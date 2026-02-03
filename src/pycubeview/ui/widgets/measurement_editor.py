# Local Imports
from PySide6.QtGui import QCloseEvent
from pycubeview.data_transfer_classes import Measurement

# Dependencies
import pyqtgraph as pg  # type: ignore

# PySide6 Imports
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
)


class MeasurementEditor(QWidget):
    name_changed = Signal(Measurement, str)
    deleted = Signal(Measurement)
    closed = Signal()

    def __init__(
        self, editable_measurement: Measurement, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.edit_meas = editable_measurement
        self.edit_meas.plot_data_item.setPen(pg.mkPen(color="red"))

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Spectrum Name:"))

        self.line_edit = QLineEdit()
        self.line_edit.setMaxLength(80)
        self.line_edit.setPlaceholderText(self.edit_meas.name)
        self.line_edit.returnPressed.connect(self.change_name)

        layout.addWidget(self.line_edit)

        delete_button = QPushButton("Delete Spectrum")
        delete_button.pressed.connect(self.delete_measurement)

        layout.addWidget(delete_button)

        self.setLayout(layout)
        self.setWindowTitle("Measurement Editor")

        self.show()

    def change_name(self):
        self.close()
        self.name_changed.emit(self.edit_meas, self.line_edit.text())

    def delete_measurement(self):
        self.close()
        self.deleted.emit(self.edit_meas)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.edit_meas.plot_data_item.setPen(
            pg.mkPen(color=self.edit_meas.color.hex)
        )
        self.closed.emit()
        return super().closeEvent(event)
