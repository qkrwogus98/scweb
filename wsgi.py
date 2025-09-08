from flask.helpers import get_debug_flag
from flask_socketio import SocketIO, emit, join_room, leave_room
from fieldy import create_app
from kafka import KafkaConsumer
import json
from werkzeug.middleware.proxy_fix import ProxyFix
from flask import request, redirect
import logging
from dotenv import load_dotenv
import os
import traceback
from flask import jsonify
from datetime import datetime, timezone
from collections import defaultdict

load_dotenv()

# Load the debug flag to determine the environment
FLASK_ENV = get_debug_flag()
app = create_app(FLASK_ENV)
debug = os.getenv('DEBUG', 'False').lower() == 'true'

# 수정: async_mode를 threading으로 변경하고 추가 설정
socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    async_mode="threading",  # gevent 대신 threading 사용
    logger=True,  # 디버깅을 위한 로깅 활성화
    engineio_logger=True,  # Engine.IO 로깅도 활성화
    ping_timeout=60,  # 핑 타임아웃 증가
    ping_interval=25  # 핑 간격 설정
)

listeners = {}
active_clients = defaultdict(int)
client_topics = {}
topic_bounds = {}

def create_kafka_consumer(topic):
    return KafkaConsumer(
        topic,
        bootstrap_servers='localhost:9092',
        value_deserializer=lambda v: json.loads(v.decode('utf-8')),
        auto_offset_reset='earliest',
        group_id=f'webapp-{topic}'
    )

# Middleware to redirect HTTP to HTTPS
@app.before_request
def before_request():
    if (
        not request.is_secure
        and not debug
        and request.host not in ("localhost", "127.0.0.1")
    ):
        url = request.url.replace("http://", "https://", 1)
        return redirect(url, code=301)

def kafka_listener(topic):
    print(f"listener for {topic} is starting")
    consumer = create_kafka_consumer(topic)
    try:
        for message in consumer:
            data = message.value
            if data.get('type') == 'meta':
                start_iso = data.get('start')
                end_iso = data.get('end')
                try:
                    bounds = {}
                    if start_iso:
                        start_dt = datetime.fromisoformat(start_iso)
                        bounds['start'] = start_dt.replace(tzinfo=timezone.utc).isoformat()
                    if end_iso:
                        end_dt = datetime.fromisoformat(end_iso)
                        bounds['end'] = end_dt.replace(tzinfo=timezone.utc).isoformat()
                    topic_bounds[topic] = bounds
                    socketio.emit('timeline_bounds', bounds, room=topic)                
                except ValueError:
                    pass
                socketio.sleep(0)
                continue
            raw_date = data.get('Date')
            if raw_date:
                try:
                    dt = datetime.fromisoformat(raw_date)
                    data['Date'] = dt.replace(tzinfo=timezone.utc).isoformat()
                except ValueError:
                    pass
            socketio.emit('data', data, room=topic)
            socketio.sleep(0)
            if active_clients[topic] == 0:
                print(f"closing kafka listener for {topic}")
                break
        consumer.close()
    except Exception as e:
        logging.error(f"Kafka listener encountered an error: {e}")
    finally:
        listeners.pop(topic,None)

@app.errorhandler(500)
def internal_error(error):
    print(f"500 Error: {error}")
    print(f"Traceback: {traceback.format_exc()}")
    return jsonify({'error': str(error)}), 500

@socketio.on('connect')
def handle_connect():
    print("socket connected")
    topic = request.args.get('topic', 'data_topic')
    client_topics[request.sid] = topic
    join_room(topic)
    active_clients[topic] += 1
    print("current active clients for", topic, ":", active_clients[topic])

    if topic not in listeners:
        listeners[topic] = socketio.start_background_task(kafka_listener, topic)
    emit('status', {'status': 'connected'})

    bounds = topic_bounds.get(topic)
    if bounds:
        emit('timeline_bounds', bounds)

@socketio.on('disconnect')
def handle_disconnect():
    topic = client_topics.pop(request.sid, 'data_topic')
    leave_room(topic)
    active_clients[topic] -= 1
    print("current active clients for", topic, ":", active_clients[topic])
    emit('status', {'status': 'disconnected'})

# 디버깅을 위한 추가 이벤트 핸들러
@socketio.on('error')
def error_handler(e):
    print(f"Socket.IO error: {e}")

if __name__ == "__main__":
    print("server is running :)")
    # Ensure Flask sees HTTPS connections correctly when behind a proxy

    # Run the Flask-SocketIO app without SSL (SSL will be handled by Nginx)
    server_ip = os.getenv('SERVER_IP')
    port = int(os.getenv('PORT'))

    if not debug:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    print(f"Starting server on {server_ip}:{port}")
    print(f"Debug mode: {debug}")
    
    socketio.run(
        app,
        host=server_ip,
        port=port,
        debug=debug,
        use_reloader=False  # 리로더 비활성화로 안정성 향상
    )