# PyQt6 Imports
from PyQt6 import QtWidgets as qtw
from PyQt6.QtCore import pyqtSignal

# Local Imports
from .spectral_display_widget import SpectralDisplayWidget


class LineRoiWindow(qtw.QWidget):
    updated = pyqtSignal()
    closed = pyqtSignal()

    def __init__(self):
        super().__init__()

        layout = qtw.QVBoxLayout()

        self.display_widget = SpectralDisplayWidget()
        self.update_button = qtw.QPushButton(text="Update Plot")

        self.update_button.clicked.connect(self.update_plot)

        layout.addWidget(self.display_widget)
        layout.addWidget(self.update_button)

        self.setLayout(layout)
        self.setWindowTitle("Linear ROI Display")

    def update_plot(self, _pushed: bool) -> None:
        self.updated.emit()

    def closeEvent(self, a0):
        self.closed.emit()
        if a0 is not None:
            a0.accept()
