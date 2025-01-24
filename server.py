from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO, join_room, leave_room, send, emit
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import jwt

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = '96278fbe9fd9c3c498040d653c964d9b'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://admin:74fvcopI26GwyF29DJNqYt1N0vcIvKnJ@dpg-cu9t04bqf0us73c4p480-a:5432/messengerdb_os0s'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///messenger.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB limit

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    online = db.Column(db.Boolean, default=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(50), nullable=False)
    recipient = db.Column(db.String(50), nullable=True)  # Null for global chat
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Routes

@app.route('/', methods=['GET'])
def index():
    return "This server made by ChiToProject Team for Messenger"
    

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data['username']
    password = data['password']

    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']

    user = User.query.filter_by(username=username).first()
    if user and bcrypt.check_password_hash(user.password, password):
        token = jwt.encode({'username': username}, app.config['SECRET_KEY'], algorithm='HS256')
        user.online = True
        db.session.commit()
        return jsonify({'token': token}), 200

    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/logout', methods=['POST'])
def logout():
    token = request.headers.get('Authorization').split()[1]
    try:
        decoded = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user = User.query.filter_by(username=decoded['username']).first()
        user.online = False
        db.session.commit()
        return jsonify({'message': 'Logged out successfully'}), 200
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401

@app.route('/users', methods=['GET'])
def get_users():
    """Returns all users and their online status."""
    users = User.query.all()
    return jsonify([{'username': user.username, 'online': user.online} for user in users])

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    return jsonify({'message': 'File uploaded successfully', 'filename': filename}), 200

# WebSocket Events
@socketio.on('connect')
def handle_connect():
    print("Client connected")

@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")

@socketio.on('join')
def handle_join(data):
    """Handles user joining a chat room."""
    username = data['username']
    room = data['room']
    join_room(room)
    emit('message', {'sender': 'Server', 'content': f'{username} has joined the chat.'}, to=room)

@socketio.on('leave')
def handle_leave(data):
    """Handles user leaving a chat room."""
    username = data['username']
    room = data['room']
    leave_room(room)
    emit('message', {'sender': 'Server', 'content': f'{username} has left the chat.'}, to=room)

@socketio.on('send_message')
def handle_message(data):
    """Handles receiving and broadcasting messages."""
    sender = data['sender']
    recipient = data.get('recipient')  # If None, it's a global chat
    content = data['content']

    # Save message to database
    new_message = Message(sender=sender, recipient=recipient, content=content)
    db.session.add(new_message)
    db.session.commit()

    if recipient:  
        # Private chat (send only to recipient)
        emit('message', {'sender': sender, 'content': content}, room=recipient)
    else:
        # Global chat (broadcast to everyone)
        emit('message', {'sender': sender, 'content': content}, broadcast=True)

@socketio.on('typing')
def handle_typing(data):
    """Handles 'typing...' indicators."""
    sender = data['sender']
    recipient = data['recipient']
    emit('typing', {'sender': sender}, room=recipient)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  
    socketio.run(app, debug=True)
