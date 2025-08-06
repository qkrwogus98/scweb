from flask.helpers import get_debug_flag
from flask_socketio import SocketIO, emit
from fieldy import create_app
from kafka import KafkaConsumer
import json
from werkzeug.middleware.proxy_fix import ProxyFix
from flask import request, redirect
import logging
import threading
from dotenv import load_dotenv
import os

load_dotenv()


# Load the debug flag to determine the environment
FLASK_ENV = get_debug_flag()
app = create_app(FLASK_ENV)
debug = os.getenv('DEBUG', 'False').lower() == 'true'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="gevent")
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
    if not request.is_secure and not debug:
        url = request.url.replace("http://", "https://", 1)
        return redirect(url, code=301)

def kafka_listener():
    print("listener is starting")
    consumer = create_kafka_consumer()
    try:
        for message in consumer:
            data = message.value
            socketio.emit('data', data)
            if active_clients == 0:
                print("closing kafka listener")
                break
        consumer.close()
    except Exception as e:
        logging.error(f"Kafka listener encountered an error: {e}")

@socketio.on('connect')
def handle_connect():
    print("socket connected")
    global active_clients, consumer_thread
    active_clients += 1
    print("current active clients :", active_clients)

    if active_clients == 1:  # Start Kafka listener when first client connects
        consumer_thread = threading.Thread(target=kafka_listener)
        consumer_thread.start()
    emit('status', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    global active_clients, consumer
    active_clients -= 1
    print("current active clients :", active_clients)

    emit('status', {'status': 'disconnected'})
    
if __name__ == "__main__":
    print("server is running :)")
    # Ensure Flask sees HTTPS connections correctly when behind a proxy

    # Run the Flask-SocketIO app without SSL (SSL will be handled by Nginx)
    server_ip = os.getenv('SERVER_IP')
    port = int(os.getenv('PORT'))

    if not debug:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    socketio.run(app, host=server_ip, port=5000, debug=debug)