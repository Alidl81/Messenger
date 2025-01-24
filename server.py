from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

# تنظیمات دیتابیس (PostgreSQL)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://admin:your_password@your_host:5432/messengerdb_os0s'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'

# ایجاد شیء SQLAlchemy و Bcrypt
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# تعریف مدل User
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    online = db.Column(db.Boolean, default=False)

# تعریف مدل Message
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(50), nullable=False)
    recipient = db.Column(db.String(50), nullable=True)  # Null برای چت عمومی
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# روت اصلی
@app.route('/')
def hello_world():
    return 'Hello, World!'

# هنگام راه‌اندازی سرور، جداول را ایجاد می‌کنیم
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # این خط جداول را در دیتابیس ایجاد می‌کند
    socketio.run(app, debug=True)
