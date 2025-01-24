import sys
import json
import websocket
import threading
import requests
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QTextEdit, QLabel, QLineEdit, QMessageBox, QStackedWidget
from PyQt5.QtCore import Qt

# Server Details
SERVER_URL = "http://MessengerServer.pythonanywhere.com"
WS_URL = "http://messengerserver.pythonanywhere.com/socket.io/?EIO=3&transport=polling"



class LoginRegisterPage(QWidget):
    """Login & Registration Page"""

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.label = QLabel("Login / Register")
        self.label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(self.label, alignment=Qt.AlignCenter)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter Username")
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        self.login_button = QPushButton("Login")
        self.login_button.setStyleSheet("background-color: #2a9d8f; color: white;")
        self.login_button.clicked.connect(self.login)
        layout.addWidget(self.login_button)

        self.register_button = QPushButton("Register")
        self.register_button.setStyleSheet("background-color: #f4a261; color: white;")
        self.register_button.clicked.connect(self.register)
        layout.addWidget(self.register_button)

        self.setLayout(layout)

    def login(self):
        """Handle login"""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "Error", "Username and Password required!")
            return

        response = requests.post(f"{SERVER_URL}/login", json={"username": username, "password": password})
        if response.status_code == 200:
            token = response.json().get("token")
            self.parent.token = token
            self.parent.username = username
            self.parent.chat_page.connect_websocket()
            self.parent.stack.setCurrentWidget(self.parent.chat_page)
        else:
            QMessageBox.warning(self, "Error", "Invalid Credentials!")

    def register(self):
        """Handle registration"""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "Error", "Username and Password required!")
            return

        response = requests.post(f"{SERVER_URL}/register", json={"username": username, "password": password})
        if response.status_code == 201:
            QMessageBox.information(self, "Success", "Registration successful! Please login.")
        else:
            QMessageBox.warning(self, "Error", "Username already exists!")


class ChatPage(QWidget):
    """Main Chat Page"""

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.username = None
        self.current_recipient = None
        self.ws = None
        self.init_ui()

    def init_ui(self):
        """Setup chat UI"""
        layout = QHBoxLayout(self)

        # Sidebar for users
        self.user_list = QListWidget()
        self.user_list.setMaximumWidth(180)
        self.user_list.setStyleSheet("background-color: #333; color: white;")
        self.user_list.itemClicked.connect(self.select_user)

        # Chat area
        chat_layout = QVBoxLayout()
        self.chat_label = QLabel("Global Chat")
        self.chat_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 5px;")
        self.message_list = QListWidget()
        self.message_list.setStyleSheet("background-color: #444; color: white;")

        self.message_input = QTextEdit()
        self.message_input.setMaximumHeight(50)
        self.message_input.setStyleSheet("background-color: #555; color: white;")
        self.send_button = QPushButton("Send")
        self.send_button.setStyleSheet("background-color: #2a9d8f; color: white;")
        self.send_button.clicked.connect(self.send_message)

        chat_layout.addWidget(self.chat_label)
        chat_layout.addWidget(self.message_list)
        chat_layout.addWidget(self.message_input)
        chat_layout.addWidget(self.send_button)

        layout.addWidget(self.user_list)
        layout.addLayout(chat_layout)

    def connect_websocket(self):
        """Connect to WebSocket"""
        self.ws = websocket.WebSocketApp(
        WS_URL,
        on_message=self.on_message,
        on_close=self.on_close,
        on_open=self.on_open
        )
        # Start the WebSocket connection in a separate thread
        threading.Thread(target=self.ws.run_forever, daemon=True).start()

    def on_open(self, ws):
        """WebSocket Opened"""
        self.ws.send(json.dumps({"event": "join", "username": self.parent.username, "room": "global"}))
        self.fetch_users()

    def on_message(self, ws, message):
        """Receive message"""
        try:
            data = json.loads(message)
            sender = data.get("sender", "Unknown")
            content = data.get("content", "")

            if sender and content:
                self.message_list.addItem(f"{sender}: {content}")
        except Exception as e:
            print("Error processing message:", e)

    def on_close(self, ws, status, msg):
        """WebSocket Disconnected"""
        self.message_list.addItem("⚠️ Disconnected. Reconnecting...")
        threading.Timer(5, self.connect_websocket).start()

    def send_message(self):
        """Send message"""
        message = self.message_input.toPlainText().strip()
        if not message:
            return

        if not self.ws or not self.ws.sock or not self.ws.sock.connected:
            self.message_list.addItem("⚠️ Not connected to server!")
            return

        recipient = self.current_recipient if self.current_recipient else None
        payload = {"sender": self.parent.username, "recipient": recipient, "content": message}

        try:
            self.ws.send(json.dumps(payload))
            self.message_list.addItem(f"You: {message}")
            self.message_input.clear()
        except Exception as e:
            self.message_list.addItem(f"⚠️ Error sending message: {e}")

    def select_user(self, item):
        """Select user for private chat"""
        selected_user = item.text()
        if selected_user == self.parent.username:
            return

        self.current_recipient = selected_user
        self.chat_label.setText(f"Private Chat with {selected_user}")
        self.message_list.clear()
        self.ws.send(json.dumps({"event": "join", "username": self.parent.username, "room": selected_user}))

    def fetch_users(self):
        """Fetch online users"""
        response = requests.get(f"{SERVER_URL}/online_users")
        if response.status_code == 200:
            users = response.json()
            self.user_list.clear()
            for user in users:
                self.user_list.addItem(user["username"])


class MessengerApp(QWidget):
    """Main Application"""

    def __init__(self):
        super().__init__()
        self.token = None
        self.username = None
        self.init_ui()

    def init_ui(self):
        """Setup main application"""
        self.stack = QStackedWidget()

        self.login_page = LoginRegisterPage(self)
        self.chat_page = ChatPage(self)

        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.chat_page)

        layout = QVBoxLayout()
        layout.addWidget(self.stack)
        self.setLayout(layout)

        self.setWindowTitle("Messenger")
        self.resize(600, 500)

        self.stack.setCurrentWidget(self.login_page)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MessengerApp()
    window.show()
    sys.exit(app.exec_())
