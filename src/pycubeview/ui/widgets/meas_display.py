# Local Imports
from pycubeview.data.valid_colormaps import QualitativeColorMap
from pycubeview.data_transfer_classes import Measurement

# Dependencies
import pyqtgraph as pg  # type: ignore
import numpy as np
import cmap

# PySide6 Imports
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal


class BaseMeasurementAxisDisplay(QWidget):

    def __init__(
        self,
        measurement_name: str,
        parent: QWidget | None = None,
        measurement_cmap: QualitativeColorMap = "colorbrewer:Dark2",
    ) -> None:
        super().__init__(parent)
        # ---- Adding attributes and properties ----
        self.name = measurement_name
        self.cmap = cmap.Colormap(measurement_cmap)
        self.plotted_count: int = 0
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
    measurement_added = Signal(Measurement)

    def __init__(
        self, measurement_name: str, parent: QWidget | None = None
    ) -> None:
        super().__init__(measurement_name, parent)

    def add_measurement(self, y: int, x: int) -> None:
        if self.plotted_count >= 8:
            print("Max Number of Spectra Plotted. Save and Reset to continue.")
            return
        measurement = self.cube[y, x, :]
        measurement_color = self.cmap(self.plotted_count)
        plot_item = pg.PlotDataItem(
            self.meas_lbl,
            measurement,
            pen=pg.mkPen(color=measurement_color.hex),
            clickable=True,
        )
        self.pg_plot.addItem(plot_item)

        meas = Measurement(
            pixel_y=y,
            pixel_x=x,
            name=f"Measurement{self.plotted_count + 1}",
            color=measurement_color,
            plot_data_item=plot_item,
        )

        self.measurement_added.emit(meas)

        self.plotted_count += 1
