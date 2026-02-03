# Built-Ins
from typing import Protocol, Any, runtime_checkable, Optional
from collections.abc import Callable
from pathlib import Path

# Local Imports
from pycubeview.custom_types import CubeFileTypes
from pycubeview.ui.status_indicator import BaseStatusIndicator
from pycubeview.ui.widgets.image_display import ImageDisplay
from pycubeview.ui.widgets.meas_display import MeasurementAxisDisplay
from pycubeview.global_app_state import AppState

# Dependencies
import numpy as np
import pyqtgraph as pg  # type: ignore
import cmap

# PySide6 Imports
from PySide6.QtWidgets import QWidget, QMenu, QStatusBar


class SignalProtocol(Protocol):
    def connect(self, slot: Callable[..., Any]) -> None: ...


class CubeViewMainWindowProtocol(Protocol):
    image_display_added: Any  # Signal(ImageDisplay)
    measurement_display_added: Any  # Signal(MeasurementDisplay)
    link_displays: Any  # Signal(ImageDisplay, MeasurementDisplay)
    central_widget: QWidget
    image_displays: dict[str, ImageDisplay]
    meas_displays: dict[str, MeasurementAxisDisplay]
    file_menu: QMenu
    image_menu: QMenu
    meas_menu: QMenu
    status_bar: QStatusBar
    geo_indicator: BaseStatusIndicator

    def add_image_display(self, arr: np.ndarray) -> None: ...
    def add_meas_display(self, arr: np.ndarray, lbls: np.ndarray) -> None: ...
    def reset_docks(self) -> None: ...


class ImageDisplayProtocol(Protocol):
    pixel_clicked: SignalProtocol
    data_tracking: SignalProtocol
    sigMouseMoved: SignalProtocol
    pg_image_view: pg.ImageView
    display_colormap: cmap.Colormap
    name: str

    @property
    def image_data(self) -> np.ndarray: ...
    @image_data.setter
    def image_data(self, value: np.ndarray) -> None: ...
    @property
    def image_size(self) -> np.ndarray: ...

    def plot_point(self, x: int, y: int, color: cmap.Color) -> None: ...


@runtime_checkable
class MeasurementAxisDisplayProtocol(Protocol):
    measurement_added: Any
    max_plotted: SignalProtocol
    pg_plot: pg.PlotWidget
    plotted_count: int

    @property
    def name(self) -> str: ...
    @name.setter
    def name(self, value: str) -> None: ...
    @property
    def cube(self) -> np.ndarray: ...
    @cube.setter
    def cube(self, value: np.ndarray) -> None: ...
    @property
    def meas_lbl(self) -> np.ndarray: ...
    @meas_lbl.setter
    def meas_lbl(self, value: np.ndarray) -> None: ...

    def add_measurement(
        self,
        *,
        y: int | None = None,
        x: int | None = None,
        x_pixels: Optional[np.ndarray] = None,
        y_pixels: Optional[np.ndarray] = None,
        vertices: Optional[np.ndarray] = None,
    ) -> None: ...
    def reset_cache(self) -> None: ...
    def save_spectral_cache(self) -> None: ...
    def set_plot_name(self) -> None: ...


class AppStateHandler(Protocol):
    app_state: AppState

    def set_base_fp(self, *, fp: Path | None = None) -> None: ...


class FileHandler(Protocol):
    def open_image(
        self, *, set_image: bool = True, fp: Path | None = None
    ) -> tuple[Path | None, CubeFileTypes | None]: ...
    def open_meas(self) -> np.ndarray | None: ...
    def open_cube(self, *, fp: Path | None = None) -> None: ...
    def reset_data(self) -> None: ...


class MeasurementHandler(Protocol):
    def reset_cache(self) -> None: ...
