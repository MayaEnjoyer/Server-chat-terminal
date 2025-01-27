import os
import sys
import socket
import threading
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QFileDialog,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QComboBox,
    QTextBrowser,
    QListWidget
)
from PyQt5.QtCore import Qt, QUrl, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QDesktopServices, QIcon


class ChatClient:
    pass


class UsernameDialog(QDialog):
    def __init__(self):
        super().__init__()

        icon_path = os.path.join(getattr(sys, '_MEIPASS', '.'), 'icon.png')
        self.setWindowIcon(QIcon(icon_path))

        self.setWindowTitle("Enter username")
        self.setFixedSize(400, 200)
        self.setStyleSheet("background-color: #ecf0f1; font-size: 14px;")
        self.username = None
        self.layout = QVBoxLayout()
        self.title = QLabel("Welcome to the chat!")
        self.title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        self.title.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.title)
        self.form_layout = QGridLayout()
        self.label = QLabel('Name:')
        self.label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.label.setStyleSheet("font-size: 16px;")
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Enter your name...")
        self.input_field.setStyleSheet(
            "font-size: 16px; padding: 10px; border: 1px solid #bdc3c7; border-radius: 5px;"
        )
        self.form_layout.addWidget(self.label, 0, 0)
        self.form_layout.addWidget(self.input_field, 0, 1)
        self.layout.addLayout(self.form_layout)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Ok).setText('Accept')
        self.buttons.button(QDialogButtonBox.Cancel).setText('Cancel')
        self.buttons.button(QDialogButtonBox.Ok).setStyleSheet(
            "background-color: #3498db; color: white; padding: 5px; border-radius: 5px;"
        )
        self.buttons.button(QDialogButtonBox.Cancel).setStyleSheet(
            "background-color: #e74c3c; color: white; padding: 5px; border-radius: 5px;"
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)
        self.setLayout(self.layout)

    def get_username(self):
        if self.exec_() == QDialog.Accepted:
            self.username = self.input_field.text().strip()
            if not self.username:
                self.username = f"Users{datetime.now().strftime('%H%M%S')}"
        else:
            sys.exit()
        return self.username

    class ChatClient(QWidget):
        colorReceived = pyqtSignal(str)
        roomsReceived = pyqtSignal(list)
        appendLogSignal = pyqtSignal(str, str)
        switchRoomSignal = pyqtSignal(str)
        updateDisplaySignal = pyqtSignal(str)
        userListSignal = pyqtSignal(str, list)
        historySignal = pyqtSignal(str, str)

    def __int__(self):
        super().__int__()
        self.buttons.accepted
        self.username = None
        self.color = '#000000'
        self.rooms = []
        self.current_room = None
        self.room_logs = {}
        self.cline_socked = None
        self.receive_thread = None
        self.pending_file = None
        self.buffer = ''
        self.init_ui()

        self.colorReceived.connect(self.on_color_reseived)
        self.roomsReseived.connect(self.on_rooms_reseived)
        self.appendLogSignal.connect(self.on_append_log)
        self.updateDisplaySignal.connect(self.on_update_display)
        self.switchRoomSignal.connect(self.on_switch_signal)
        self.userListSignal.connect(self.on_userlist_received)
        self.historySignal.connect(self.on_history_received)


    def init_ui(self):
        icon_path = os.path.join(getattr(sys, '_MEIPASS', '.'), 'icon.png')
        self.setWindowIcon(QIcon(icon_path))

        self.setWindowTitle("Chat Client")
        self.setGeometry(300, 150, 800, 700)
        self.layout = QHBoxLayout()
        self.main_layout = QVBoxLayout()
        self.header_layout = QHBoxLayout()
        self.header_label = QLabel("Welcome to the chat", self)
        self.header_label.setAlignment(Qt.AlignCenter)
        self.header_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        self.header_layout.addWidget(self.header_label)
        self.room_box = QComboBox()
        self.room_box.setStyleSheet("font-size:14px; padding:5px;")
        self.room_box.currentIndexChanged.connect(self.user_switch_room_request)
        self.header_layout.addWidget(self.room_box)
        self.main_layout.addLayout(self.header_layout)
        self.chat_display = QTextBrowser()
        self.chat_display.setReadOnly(True)
        self.chat_display.anchorClicked.connect(self.open_link)
        self.chat_display.setStyleSheet(
            "background-color: #ecf0f1; font-size: 16px; padding: 10px; border-radius: 5px;"
        )
        self.main_layout.addWidget(self.chat_display)
        self.message_input_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Enter your message...")
        self.message_input.setStyleSheet(
            "font-size: 16px; padding: 10px; border: 1px solid #bdc3c7; border-radius: 5px;"
        )
        self.message_input.returnPressed.connect(self.send_message)
        self.message_input_layout.addWidget(self.message_input)
        self.send_button = QPushButton('Send')
        self.send_button.setStyleSheet(
            "background-color: #3498db; color: white; font-size: 16px; padding: 10px; border-radius: 5px;"
        )
        self.send_button.clicked.connect(self.send_message)
        self.message_input_layout.addWidget(self.send_button)
        self.file_button = QPushButton("Send files")
        self.file_button.setStyleSheet(
            "background-color: #9b59b6; color: white; font-size: 16px; padding: 10px; border-radius: 5px;"
        )
        self.file_button.clicked.connect(self.send_file)
        self.message_input_layout.addWidget(self.file_button)
        self.main_layout.addLayout(self.message_input_layout)
        self.footer = QLabel("Developed by Hubar", self)
        self.footer.setAlignment(Qt.AlignCenter)
        self.footer.setStyleSheet("font-size: 12px; color: #7f8c8d;")
        self.main_layout.addWidget(self.footer)
        self.user_list = QListWidget()
        self.user_list.setStyleSheet("font-size:14px; border:1px solid #bdc3c7;")
        self.layout.addLayout(self.main_layout, stretch=3)
        self.layout.addWidget(self.user_list, stretch=1)
        self.setLayout(self.layout)

    def open_link(self, url: QUrl):
        QDesktopServices.openUrl(url)

    def load_username(self):
        if os.path.exists('username.txt'):
                with open('username.txt', 'r', encoding='utf-8') as f:
                    name = f.read().strip()
                    if name:
                        return name
        return None

    def save_username(self, username):
        with open('username.txt', 'w', encoding='utf-8') as f:
                f.write(username)

def get_username(self):
    stored_name = self.load_username()
    if stored_name:
        self.username = stored_name
    else:
        dialog = UsernameDialog()
        self.username = dialog.get_username()
        self.save_username(self.username)

def connect_to_server(self, host, port):
    self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        self.client_socket.connect((host, port))
        self.client_socket.send(f"USERNAME:{self.username}\n".encode('utf-8'))
        self.receive_thread = threading.Thread(
            target=self.receive_messages, daemon=True
        )
        self.receive_thread.start()
        self.appendLogSignal.emit('general', "Connection to server successful!")
    except Exception as e:
        self.appendLogSignal.emit('general', f"Failed to connect: {e}")
        self.updateDisplaySignal.emit('general')

def append_to_log(self, room, message):
    if room not in self.room_logs:
        self.room_logs[room] = ''
    self.room_logs[room] += message + '<br>'

@pyqtSlot(str, str)
def on_append_log(self, room, html_message):
    self.append_to_log(room, html_message)

def update_chat_display(self, room):
    if room in self.room_logs:
        self.chat_display.setHtml(self.room_logs[room])
    else:
        self.chat_display.setHtml('')

@pyqtSlot(str)
def on_update_display(self, room):
    self.update_chat_display(room)

def receive_file_data(self, filesize):
    file_data = b''
    received = 0
    while received < filesize:
        chunk = self.client_socket.recv(min(4096, filesize - received))
        if not chunk:
            break
        file_data += chunk
        received += len(chunk)
    return file_data

@pyqtSlot(str, str)
def on_history_received(self, room_name, history_text):
    lines = history_text.split('\n')
    self.room_logs[room_name] = ''
    for line in lines:
        line = line.strip()
        if line:
            if ':' in line:
                color, message = line.split(':', 1)
                color = color.strip()
                message = message.strip()
                msg_html = f'<span style="color:{color}">{message}</span><br>'
                self.room_logs[room_name] += msg_html
            else:
                self.room_logs[room_name] += line + '<br>'
    if room_name == self.current_room:
        self.update_chat_display(room_name)

def process_message(self, line):
        if line.startswith('COLOR:'):
            c = line.split(':', 1)[1]
            self.colorReceived.emit(c)
        elif line.startswith('ROOMS:'):
            rooms_list = line.split(':', 1)[1]
            r = rooms_list.split(',')
            self.roomsReceived.emit(r)
        elif line.startswith('FILE:'):
            filename = line.split(':', 1)[1]
            size_line = self.get_next_line()
            if size_line.startswith('FILESIZE:'):
                filesize = int(size_line.split(':', 1)[1])
                file_data = self.receive_file_data(filesize)
                local_filename = f"received_{filename}"
                with open(local_filename, 'wb') as f:
                    f.write(file_data)
                msg = f'<span style="color:#34495e">File received: <a href="file://{os.path.abspath(local_filename)}">{filename}</a></span>'
                self.appendLogSignal.emit(self.current_room, msg)
                if self.room_box.currentText() == self.current_room:
                    self.updateDisplaySignal.emit(self.current_room)
            elif line.startswith('USERLIST:'):
                parts = line.split(':', 2)
                room_name = parts[1]
                users_str = parts[2]
                users_list = users_str.split(',') if users_str else []
                self.userListSignal.emit(room_name, users_list)
            elif line.startswith('HISTORY:'):
                # HISTORY:room_name:history_text
                prefix, room_name, history_text = line.split(':', 2)
                self.historySignal.emit(room_name, history_text)
            else:
                if ":" in line:
                    color, message = line.split(':', 1)
                    color = color.strip()
                    message = message.strip()
                    msg_html = f'<span style="color:{color}">{message}</span>'
                    self.appendLogSignal.emit(self.current_room, msg_html)
                    if self.room_box.currentText() == self.current_room:
                        self.updateDisplaySignal.emit(self.current_room)

def get_next_line(self):
    while True:
        if '\n' in self.buffer:
            lines = self.buffer.split('\n')
            line = lines[0].strip()
            self.buffer = '\n'.join(lines[1:])
        return line
        data = self.client_socket.recv(1024)
        if not data:
            return ''
        self.buffer += data.decode('utf-8')

def receive_messages(self):
    while True:
        try:
            data = self.client_socket.recv(1024)
            if not data:
                break
            self.buffer += data.decode('utf-8')
            lines = self.buffer.split('\n')
            for line in lines[:-1]:
                line = line.strip()
            if line:
        self.process_message(line)
            self.buffer = lines[-1]
        except:
                break

    @pyqtSlot(str)
    def on_color_received(self, c):
        self.color = c

    @pyqtSlot(list)
    def on_rooms_received(self, r):
        self.rooms = r
        self.room_box.clear()
        self.room_box.addItems(self.rooms)
        if 'general' in self.rooms:
            self.current_room = 'general'
            idx = self.rooms.index('general')
            self.room_box.setCurrentIndex(idx)
            if 'general' not in self.room_logs:
                self.room_logs['general'] = ''
            self.updateDisplaySignal.emit('general')

    def send_message(self):
        message = self.message_input.text().strip()
        if message:
            try:
                timestamp = datetime.now().strftime('%H:%M:%S')
                formatted_message = f"[{timestamp}] {self.username}: {message}"
                self.client_socket.send((formatted_message + '\n').encode('utf-8'))
                msg_html = f'<span style="color:{self.color}">{formatted_message}</span>'
                self.appendLogSignal.emit(self.current_room, msg_html)
                self.updateDisplaySignal.emit(self.current_room)
                self.message_input.clear()
            except Exception as e:
                self.appendLogSignal.emit(self.current_room, f"Failed to send message: {e}")
                self.updateDisplaySignal.emit(self.current_room)


