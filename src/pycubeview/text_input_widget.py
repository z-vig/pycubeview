from PySide6.QtWidgets import QDialog, QLineEdit, QVBoxLayout


class TextInputDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enter Text")
        self.text = None

        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText("Type and press Enter")
        self.line_edit.returnPressed.connect(self.handle_return)

        layout = QVBoxLayout()
        layout.addWidget(self.line_edit)
        self.setLayout(layout)

    def handle_return(self):
        self.text = self.line_edit.text()
        self.accept()  # Closes the dialog
