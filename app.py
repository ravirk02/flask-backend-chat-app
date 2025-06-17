import eventlet
eventlet.monkey_patch()  # 🟢 Must be FIRST

from flask import Flask, request, jsonify
from flask_socketio import SocketIO, send, emit
from flask import send_from_directory

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
    async_mode="eventlet",  # explicitly mention this
    logger=True,            # helpful for debugging
    engineio_logger=True
)

# In-memory user store: phone -> password
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

# @socketio.on('message')
# def handle_message(data):
#     timestamp = datetime.now().strftime("%H:%M:%S")
#     print(f"{data['user']} said: {data['text']} at {timestamp}")
#     data['time'] = timestamp
#     send(data, broadcast=True)
@socketio.on('message')
def handle_message(data):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"{data['user']} said: {data['text']} at {timestamp}")

    # Optional: handle replyTo field
    reply_to = data.get('replyTo')  # could be None or a dict with original message info

    message_data = {
        'user': data['user'],
        'text': data['text'],
        'time': timestamp,
        'replyTo': reply_to  # include this only if it exists
    }

    send(message_data, broadcast=True)

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
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)

