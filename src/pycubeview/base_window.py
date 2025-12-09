# Built-ins
from dataclasses import dataclass
from importlib.metadata import version

# Dependencies
import pyqtgraph as pg  # type: ignore
import numpy as np

# PyQt6 Imports
from PyQt6.QtWidgets import QMainWindow, QStatusBar, QMenu
from PyQt6.QtGui import QAction


@dataclass
class MasterGUIState:
    spectrum_cache: dict[str, tuple[pg.PlotDataItem, pg.ErrorBarItem]]
    spectrum_edit_open: bool
    drawing: bool

    @classmethod
    def initial(cls) -> "MasterGUIState":
        return cls(
            spectrum_cache={},
            spectrum_edit_open=False,
            drawing=False,
        )


class BaseWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.state = MasterGUIState.initial()

        self.open_cube = QAction("Open Spectral Cube", self)
        self.open_cube.setStatusTip("Open a new spectral cube.")

        self.open_display = QAction("Open Display", self)
        self.open_display.setStatusTip("Open new display data.")

        self.clear_spectra = QAction("Clear Spectrum Plot", self)
        self.clear_spectra.setStatusTip("Clear 0 spectra from memory.")

        menubar = self.menuBar()
        if menubar is not None:
            self.open_menu = QMenu(title="Open")
            menubar.addMenu(self.open_menu)
            self.open_menu.addAction(self.open_cube)
            self.open_menu.addAction(self.open_display)

            self.spectrum_menu = QMenu(title="Spectrum")
            menubar.addMenu(self.spectrum_menu)
            self.spectrum_menu.addAction(self.clear_spectra)

        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)

        self.setWindowTitle(f"CubeView v{version("pycubeview")}")

    def set_window_size(self, image: np.ndarray) -> None:
        if image.shape[0] > image.shape[1]:
            self.resize(600, 800)
        elif image.shape[1] > image.shape[0]:
            self.resize(800, 600)
        else:
            self.resize(600, 600)
