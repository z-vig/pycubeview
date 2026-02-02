# Built-Ins
from typing import Optional

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
        measurement_unit: str,
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
        plot_item = self.pg_plot.plotItem
        if plot_item is None:
            raise ValueError("Invalid Plot Initialization.")
        plot_item.getAxis(name="bottom").setLabel(measurement_unit)

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
    max_plotted = Signal()

    def __init__(
        self,
        measurement_name: str,
        measurement_unit: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(measurement_name, measurement_unit, parent)

    def add_measurement(
        self,
        *,
        y: int | None = None,
        x: int | None = None,
        x_pixels: Optional[np.ndarray] = None,
        y_pixels: Optional[np.ndarray] = None,
    ) -> None:
        """
        Add a measurement to the plot.

        - Point measurement: provide both `y` and `x` (ints).
        - ROI measurement: provide both `x_pixels` and `y_pixels` (1D ndarrays
        of ints).
        """
        if self.plotted_count >= 8:
            print("Max Number of Spectra Plotted. Save and Reset to continue.")
            self.max_plotted.emit()
            return

        measurement_color = self.cmap(self.plotted_count)

        # Point measurement
        if y is not None and x is not None:
            measurement = self.cube[y, x, :]
            plot_item = pg.PlotDataItem(
                self.meas_lbl,
                measurement,
                pen=pg.mkPen(color=measurement_color.hex),
                clickable=True,
            )
            self.pg_plot.addItem(plot_item)
            errorbar_item = pg.ErrorBarItem(x=[], y=[])
            errorbar_item.setVisible(False)

            meas = Measurement(
                pixel_y=y,
                pixel_x=x,
                name=f"Measurement{self.plotted_count + 1}",
                color=measurement_color,
                plot_data_item=plot_item,
                plot_data_errorbars=errorbar_item,
            )

        # ROI measurement
        elif x_pixels is not None and y_pixels is not None:
            x_pixels = np.asarray(x_pixels, dtype=int)
            y_pixels = np.asarray(y_pixels, dtype=int)

            # gather pixel spectra and average across pixels
            roi_data = self.cube[np.ix_(y_pixels, x_pixels)]
            pixels = roi_data.reshape(-1, roi_data.shape[-1])
            roi_mean = np.mean(pixels, axis=0)
            roi_err = np.std(pixels, axis=0, ddof=1)

            plot_item = pg.PlotDataItem(
                self.meas_lbl,
                roi_mean,
                pen=pg.mkPen(color=measurement_color.hex),
                clickable=True,
            )
            self.pg_plot.addItem(plot_item)

            errorbar_item = pg.ErrorBarItem(
                x=self.meas_lbl, y=roi_mean, height=2 * roi_err, beam=10
            )
            self.pg_plot.addItem(errorbar_item)

            meas = Measurement(
                color=measurement_color,
                pixel_x=int(np.mean(x_pixels)),
                pixel_y=int(np.mean(y_pixels)),
                name=f"Measurement{self.plotted_count + 1}",
                plot_data_item=plot_item,
                plot_data_errorbars=errorbar_item,
            )
        else:
            raise ValueError(
                "Invalid arguments for add_measurement(): supply either (y, x)"
                " for point measurements or (x_pixels, y_pixels) for ROI."
            )

        self.measurement_added.emit(meas)
        self.plotted_count += 1
