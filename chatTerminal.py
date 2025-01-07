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




