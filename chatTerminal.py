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