from PySide6 import QtWidgets as qtw
from PySide6.QtCore import Signal
from pyqtgraph.graphicsItems.PlotDataItem import PlotDataItem  # type: ignore


class SpectrumEditWindow(qtw.QWidget):
    name_changed = Signal(str, str)
    spectrum_deleted = Signal()
    closed = Signal()

    def __init__(self, edit_spec: PlotDataItem):
        super().__init__()

        self.edit_spec = edit_spec
        layout = qtw.QVBoxLayout()

        layout.addWidget(qtw.QLabel("Spectrum Name:"))

        self.line_edit_widget = qtw.QLineEdit()
        self.line_edit_widget.setMaxLength(80)
        self.line_edit_widget.setPlaceholderText(f"{self.edit_spec.name()}")
        self.line_edit_widget.returnPressed.connect(self.set_spectrum_name)

        layout.addWidget(self.line_edit_widget)

        delete_button = qtw.QPushButton("Delete Spectrum")
        delete_button.pressed.connect(self.delete_spectrum)
        layout.addWidget(delete_button)

        self.setLayout(layout)
        self.setWindowTitle("Spectrum Editor")

    def set_spectrum_name(self):
        new_name = self.line_edit_widget.text()
        old_name = self.edit_spec.opts["name"]
        self.edit_spec.opts["name"] = new_name
        self.name_changed.emit(old_name, new_name)

    def delete_spectrum(self):
        self.spectrum_deleted.emit()

    def closeEvent(self, event):
        self.closed.emit()
        if event is not None:
            event.accept()
