# Built-Ins
from typing import Optional
from functools import partial
from uuid import UUID, uuid4

# Local Imports
from pycubeview.data.valid_colormaps import QualitativeColorMap
from pycubeview.data_transfer_classes import Measurement
from .measurement_editor import MeasurementEditor

# Dependencies
import pyqtgraph as pg  # type: ignore
from pyqtgraph.GraphicsScene.mouseEvents import MouseClickEvent as PGClick  # type: ignore  # noqa
import numpy as np
import cmap

# PySide6 Imports
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal


class BaseMeasurementAxisDisplay(QWidget):

    def __init__(
        self,
        measurement_unit: str,
        parent: QWidget | None = None,
        measurement_cmap: QualitativeColorMap = "colorbrewer:Dark2",
    ) -> None:
        super().__init__(parent)
        # ---- Adding attributes and properties ----
        self.id: UUID = uuid4()
        self.cmap = cmap.Colormap(measurement_cmap)
        self.plotted_count: int = 0
        self._cube: np.ndarray | None = None
        self._meas_lbl: np.ndarray | None = None
        self._editing: bool = False

        # ---- Initializing Widgets ----
        self.pg_plot = pg.PlotWidget()
        plot_item = self.pg_plot.plotItem
        if plot_item is None:
            raise ValueError("Invalid Plot Initialization.")
        plot_item.getAxis(name="bottom").setLabel(measurement_unit)
        self.pg_legend: pg.LegendItem = self.pg_plot.addLegend()

        # ---- Setting up Layout ----
        layout = QVBoxLayout()
        layout.addWidget(self.pg_plot)
        self.setLayout(layout)

        # ---- Setting Plot Name ----
        self._name = ""

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        item = self.pg_plot.getPlotItem()
        if item is None:
            return
        item.setTitle(value)
        self._name = value

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
    measurement_deleted = Signal(Measurement)
    measurement_changed = Signal(Measurement, Measurement)  # Old, New
    max_plotted = Signal()

    def __init__(
        self,
        measurement_unit: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(measurement_unit, parent)

    def add_measurement(
        self,
        *,
        y: int | None = None,
        x: int | None = None,
        x_pixels: Optional[np.ndarray] = None,
        y_pixels: Optional[np.ndarray] = None,
        new_meas: Optional[Measurement] = None,
        id: Optional[UUID] = None,
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

        if new_meas is not None:
            self.pg_plot.addItem(new_meas.plot_data_item)
            self.pg_plot.addItem(new_meas.plot_data_errorbars)
            new_meas.plot_data_item.sigClicked.connect(
                partial(self.edit_measurement, measurement=new_meas)
            )
            self.measurement_added.emit(new_meas)
            self.plotted_count += 1
            return

        measurement_color = self.cmap(self.plotted_count)
        measurement_name = f"Measurement{self.plotted_count + 1}"
        measurement_id: UUID
        if id is None:
            measurement_id = uuid4()
        else:
            measurement_id = id

        # Point measurement
        if y is not None and x is not None:
            measurement = self.cube[y, x, :]
            plot_item = pg.PlotDataItem(
                self.meas_lbl,
                measurement,
                pen=pg.mkPen(color=measurement_color.hex),
                clickable=True,
                name=measurement_name,
            )
            errorbar_item = pg.ErrorBarItem(x=[], y=[])
            errorbar_item.setVisible(False)
            meas = Measurement(
                id=measurement_id,
                name=measurement_name,
                type="Point",
                pixel_y=y,
                pixel_x=x,
                yvalues=measurement,
                xvalues=self.meas_lbl,
                color=measurement_color,
                plot_data_item=plot_item,
                plot_data_errorbars=errorbar_item,
            )

            plot_item.sigClicked.connect(
                partial(self.edit_measurement, measurement=meas)
            )
            self.pg_plot.addItem(plot_item)

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
                name=measurement_name,
            )
            errorbar_item = pg.ErrorBarItem(
                x=self.meas_lbl,
                y=roi_mean,
                height=2 * roi_err,
                beam=10,
                pen=pg.mkPen(color=measurement_color.hex),
            )

            meas = Measurement(
                id=measurement_id,
                name=measurement_name,
                type="Group",
                color=measurement_color,
                pixel_x=int(np.mean(x_pixels)),
                pixel_y=int(np.mean(y_pixels)),
                yvalues=roi_mean,
                xvalues=self.meas_lbl,
                plot_data_item=plot_item,
                plot_data_errorbars=errorbar_item,
                x_pixels=x_pixels,
                y_pixels=y_pixels,
            )

            plot_item.sigClicked.connect(
                partial(self.edit_measurement, measurement=meas)
            )
            self.pg_plot.addItem(plot_item)
            self.pg_plot.addItem(errorbar_item)
        else:
            raise ValueError(
                "Invalid arguments for add_measurement(): supply either (y, x)"
                " for point measurements or (x_pixels, y_pixels) for ROI."
            )

        self.measurement_added.emit(meas)
        self.plotted_count += 1

    def delete_measurement(self, meas: Measurement):
        self.plotted_count -= 1
        self.pg_plot.removeItem(meas.plot_data_item)
        self.pg_plot.removeItem(meas.plot_data_errorbars)
        self.measurement_deleted.emit(meas)

    def change_measurement_name(self, meas: Measurement, name: str):
        self.delete_measurement(meas)
        meas.plot_data_item.opts["name"] = name
        new_meas = meas.change_name(name)
        self.add_measurement(new_meas=new_meas)
        self.measurement_changed.emit(meas, new_meas)

    def edit_measurement(
        self,
        _curve_item: pg.PlotCurveItem,
        _mouse_click: PGClick,
        *,
        measurement: Measurement,
    ) -> None:
        if self._editing:
            print(
                "Close the current spectrum edit window to edit another"
                " spectrum."
            )
            return
        self._editing = True
        print(f"EDIT WINDOW OPENED FOR: {measurement.name}")
        self.edit_win = MeasurementEditor(measurement)
        self.edit_win.deleted.connect(self.delete_measurement)
        self.edit_win.name_changed.connect(self.change_measurement_name)
        self.edit_win.closed.connect(self.toggle_editing)

    def toggle_editing(self):
        self._editing = not self._editing
