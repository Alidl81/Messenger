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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  
    socketio.run(app, debug=True)
