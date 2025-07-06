import eventlet
eventlet.monkey_patch()

from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, send, emit
from flask_cors import CORS
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="eventlet",
    logger=True,
    engineio_logger=True
)

users = {
    os.getenv("USER1_PHONE"): {
        "password": os.getenv("USER1_PASSWORD"),
        "username": os.getenv("USER1_USERNAME")
    },
    os.getenv("USER2_PHONE"): {
        "password": os.getenv("USER2_PASSWORD"),
        "username": os.getenv("USER2_USERNAME")
    }
}

connected_users = {}

@app.route('/')
def home():
    return "Flask Backend Chat App is running."

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 200

    data = request.json
    phone = str(data.get('phone'))
    password = data.get('password')

    if not phone or not password:
        return jsonify({'success': False, 'message': 'Phone and password required'}), 400

    user = users.get(phone)
    if user and user['password'] == password:
        return jsonify({'success': True, 'message': 'Login successful', 'username': user['username']})
    else:
        return jsonify({'success': False, 'message': 'Invalid phone or password'}), 401

@socketio.on('connect')
def handle_connect():
    print(f"A user connected with session ID: {request.sid}")

@socketio.on('join')
def handle_join(data):
    username = data.get('username')
    if not username:
        print("Join event missing username. Ignoring.")
        return

    print(f"{username} joined")
    connected_users[request.sid] = username
    timestamp = datetime.now().strftime("%H:%M:%S")
    send({'user': '💬 Chat Genie', 'text': f'🔔 {username} joined the chat', 'time': timestamp}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    username = connected_users.pop(request.sid, None)
    if username:
        print(f"{username} disconnected")
        timestamp = datetime.now().strftime("%H:%M:%S")
        send({'user': '💬 Chat Genie', 'text': f'❌ {username} left the chat', 'time': timestamp}, broadcast=True)
    else:
        print(f"Disconnected session {request.sid} had no associated username.")

@socketio.on('message')
def handle_message(data):
    username = data.get('user')
    if not username:
        print("Message event missing username. Ignoring.")
        return

    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"{username} said: {data['text']} at {timestamp}")

    reply_to = data.get('replyTo')

    message_data = {
        'user': username,
        'text': data['text'],
        'time': timestamp,
        'replyTo': reply_to
    }

    send(message_data, broadcast=True) # type: ignore

@socketio.on('typing')
def handle_typing(data):
    username = data.get('username')
    if not username:
        print("Typing event missing username. Ignoring.")
        return

    print(f"{username} is typing...")
    emit('typing', {'user': username}, broadcast=True, include_self=False)

@socketio.on('file')
def handle_file(data):
    username = data.get('user')
    if not username:
        print("File event missing username. Ignoring.")
        return

    timestamp = datetime.now().strftime("%H:%M:%S")
    data['time'] = timestamp
    print(f"File received from {username}: {data.get('fileName')}")
    emit('file', data, broadcast=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
