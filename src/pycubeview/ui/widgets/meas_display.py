# Dependencies
import pyqtgraph as pg  # type: ignore
import numpy as np

# PySide6 Imports
from PySide6.QtWidgets import QWidget, QVBoxLayout


class BaseMeasurementAxisDisplay(QWidget):
    def __init__(
        self, measurement_name: str, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        # ---- Adding attributes and properties ----
        self.name = measurement_name
        self._cube: np.ndarray | None = None
        self._meas_lbl: np.ndarray | None = None

        # ---- Initializing Widgets ----
        self.pg_plot = pg.PlotWidget()

        # ---- Setting up Layout ----
        layout = QVBoxLayout()
        layout.addWidget(self.pg_plot)
        self.setLayout(layout)

    @property
    def cube(self) -> np.ndarray:
        if self._cube is None:
            raise RuntimeError("Cube Data has not been set.")
        return self._cube

    @cube.setter
    def cube(self, value: np.ndarray):
        self._cube = value

    @property
    def meas_lbl(self) -> np.ndarray:
        if self._meas_lbl is None:
            raise RuntimeError("Measurement Labels have not been set.")
        return self._meas_lbl

    @meas_lbl.setter
    def meas_lbl(self, value: np.ndarray):
        self._meas_lbl = value


class MeasurementAxisDisplay(BaseMeasurementAxisDisplay):
    def __init__(
        self, measurement_name: str, parent: QWidget | None = None
    ) -> None:
        super().__init__(measurement_name, parent)

    def add_measurement(self, y: int, x: int):
        measurement = self.cube[y, x, :]
        plot_item = pg.PlotDataItem(self.meas_lbl, measurement, clickable=True)
        self.pg_plot.addItem(plot_item)
