from flask import Flask, request, jsonify
from flask_socketio import SocketIO, send, emit
from flask_cors import CORS
from datetime import datetime
import os
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*")

# In-memory user store: phone -> password
users = {
    "8737043934": {"password": "Sunshine@2002", "username": "Shinchan"},
    "7518917530": {"password": "Shinchan@2007", "username": "Sunshine"}
}

connected_users = {}

@app.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 200

    data = request.json
    phone = data.get('phone')
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
    print("A user connected.")

@socketio.on('join')
def handle_join(data):
    username = data.get('username', 'Unknown')
    print(f"{username} joined")
    connected_users[request.sid] = username
    timestamp = datetime.now().strftime("%H:%M:%S")
    send({'user': 'System', 'text': f'🔔 {username} joined the chat', 'time': timestamp}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    username = connected_users.get(request.sid, 'Unknown')
    print(f"{username} disconnected")
    timestamp = datetime.now().strftime("%H:%M:%S")
    send({'user': 'System', 'text': f'❌ {username} left the chat', 'time': timestamp}, broadcast=True)
    connected_users.pop(request.sid, None)

@socketio.on('message')
def handle_message(data):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"{data['user']} said: {data['text']} at {timestamp}")
    data['time'] = timestamp
    send(data, broadcast=True)

@socketio.on('typing')
def handle_typing(data):
    username = data.get('username', 'Unknown')
    print(f"{username} is typing...")
    emit('typing', {'user': username}, broadcast=True, include_self=False)

@socketio.on('file')
def handle_file(data):
    timestamp = datetime.now().strftime("%H:%M:%S")
    data['time'] = timestamp
    print(f"File received from {data.get('user')}: {data.get('fileName')}")
    emit('file', data, broadcast=True)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # default to 5000 locally
    socketio.run(app, port=port, debug=True, use_reloader=False)
