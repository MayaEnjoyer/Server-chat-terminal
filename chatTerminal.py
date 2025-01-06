class UsernameDialog(QDialog):
    def __init__(self):
        super().__init__()

        icon_path = os.path.join(getattr(sys, '_MEIPASS', '.'), 'icon.png')
        self.setWindowIcon(QIcon(icon_path))


