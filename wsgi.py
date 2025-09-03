from flask.helpers import get_debug_flag
from flask_socketio import SocketIO, emit
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

active_clients = 0

def create_kafka_consumer():
    return KafkaConsumer(
        'data_topic',
        bootstrap_servers='localhost:9092',
        value_deserializer=lambda v: json.loads(v.decode('utf-8'))
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

def kafka_listener():
    print("listener is starting")
    consumer = create_kafka_consumer()
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
                    socketio.emit('timeline_bounds', bounds)
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
            socketio.emit('data', data)
            socketio.sleep(0)
            if active_clients == 0:
                print("closing kafka listener")
                break
        consumer.close()
    except Exception as e:
        logging.error(f"Kafka listener encountered an error: {e}")

@app.errorhandler(500)
def internal_error(error):
    print(f"500 Error: {error}")
    print(f"Traceback: {traceback.format_exc()}")
    return jsonify({'error': str(error)}), 500

@socketio.on('connect')
def handle_connect():
    print("socket connected")
    global active_clients
    active_clients += 1
    print("current active clients :", active_clients)

    if active_clients == 1:  # Start Kafka listener when first client connects
        socketio.start_background_task(kafka_listener)
    emit('status', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    global active_clients
    active_clients -= 1
    print("current active clients :", active_clients)
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