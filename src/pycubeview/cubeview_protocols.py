# Built-Ins
from typing import Protocol
from pathlib import Path

# Local Imports
from pycubeview.custom_types import CubeFileTypes
from pycubeview.ui.widgets.image_display import ImageDisplay
from pycubeview.ui.widgets.meas_display import MeasurementAxisDisplay
from pycubeview.controllers.base_controller import AppState

# Dependencies
import numpy as np
import pyqtgraph as pg  # type: ignore
import cmap

# PySide6 Imports
from PySide6.QtWidgets import QWidget, QMenu
from PySide6.QtCore import Signal


class CubeViewMainWindowProtocol(Protocol):
    image_display_added: Signal
    measurement_display_added: Signal
    link_displays: Signal
    central_widget: QWidget
    image_displays: dict[str, ImageDisplay]
    meas_displays: dict[str, MeasurementAxisDisplay]
    file_menu: QMenu
    image_menu: QMenu
    meas_menu: QMenu

    def add_image_display(self, arr: np.ndarray) -> None: ...
    def add_meas_display(self, arr: np.ndarray, lbls: np.ndarray) -> None: ...
    def reset_docks(self) -> None: ...


class ImageDisplayProtocol(Protocol):
    pixel_clicked: Signal
    pg_image_view: pg.ImageView
    display_colormap: cmap.Colormap
    name: str

    @property
    def image_data(self) -> np.ndarray: ...
    @image_data.setter
    def image_data(self, value: np.ndarray) -> None: ...


class MeasurementAxisDisplayProtocol(Protocol):
    name: str
    pg_plot: pg.PlotWidget

    @property
    def cube(self) -> np.ndarray: ...
    @cube.setter
    def cube(self, value: np.ndarray) -> None: ...
    @property
    def meas_lbl(self) -> np.ndarray: ...
    @meas_lbl.setter
    def meas_lbl(self, value: np.ndarray) -> None: ...

    def add_measurement(self, y: int, x: int) -> None: ...


class AppStateHandler(Protocol):
    app_state: AppState

    def set_base_fp(self, *, fp: Path | None) -> None: ...


class FileHandler(Protocol):
    def open_image(self) -> tuple[Path | None, CubeFileTypes | None]: ...
    def open_meas(self) -> np.ndarray | None: ...
    def open_cube(self) -> None: ...
    def reset_data(self) -> None: ...
