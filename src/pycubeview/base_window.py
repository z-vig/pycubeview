# Built-ins
from dataclasses import dataclass
from pathlib import Path

# Dependencies
import pyqtgraph as pg  # type: ignore
import numpy as np

# PyQt6 Imports
from PyQt6.QtWidgets import QMainWindow, QStatusBar, QMenu, QFileDialog
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QAction

PKG_VERSION = "0.1.6"


@dataclass
class MasterGUIState:
    spectrum_cache: dict[str, tuple[pg.PlotDataItem, pg.ErrorBarItem]]
    spectrum_edit_open: bool
    line_roi_cache: list[pg.PlotDataItem]
    line_roi_scatter_plot: pg.ScatterPlotItem
    color_cycle_pos: int
    drawing: bool
    cube_attached: bool = False
    geodata_attached: bool = False
    base_data_dir: Path = Path.cwd()

    @classmethod
    def initial(cls) -> "MasterGUIState":
        return cls(
            spectrum_cache={},
            spectrum_edit_open=False,
            line_roi_cache=[],
            line_roi_scatter_plot=pg.ScatterPlotItem(),
            color_cycle_pos=0,
            drawing=False,
        )


class BaseWindow(QMainWindow):
    base_data_dir_updated = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()

        self.state = MasterGUIState.initial()

        self.open_cube = QAction("Open Spectral Cube", self)
        self.open_cube.setStatusTip("Open a new spectral cube.")

        self.open_display = QAction("Open Display", self)
        self.open_display.setStatusTip("Open new display data.")

        self.clear_spectra = QAction("Clear Spectrum Plot", self)
        self.clear_spectra.setStatusTip("Clear 0 spectra from memory.")

        self.save_spectra = QAction("Save Spectrum Plot", self)
        self.save_spectra.setStatusTip("Save 0 spectra currently in memory.")

        self.link_geodata_action = QAction("Link Geodata", self)
        self.link_geodata_action.setStatusTip(
            "Link Geolocation Data from a file. (No Geodata has been linked"
            "to the current plot)"
        )

        self.set_data_directory = QAction("Set Data Directory", self)
        self.set_data_directory.setStatusTip(
            "Sets the base directory for all data open and save menus."
            f" Current: {self.state.base_data_dir}"
        )

        menubar = self.menuBar()
        if menubar is not None:
            self.file_menu = QMenu(title="File")
            menubar.addMenu(self.file_menu)
            self.file_menu.addAction(self.set_data_directory)

            self.open_menu = QMenu(title="Open")
            menubar.addMenu(self.open_menu)
            self.open_menu.addAction(self.open_cube)
            self.open_menu.addAction(self.open_display)

            self.spectrum_menu = QMenu(title="Spectrum")
            menubar.addMenu(self.spectrum_menu)
            self.spectrum_menu.addAction(self.clear_spectra)
            self.spectrum_menu.addAction(self.save_spectra)

            self.geo_menu = QMenu(title="Geo")
            menubar.addMenu(self.geo_menu)
            self.geo_menu.addAction(self.link_geodata_action)

        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)

        self.setWindowTitle(f"CubeView v{PKG_VERSION}")

        # ---- Setting Menu Actions ----
        self.set_data_directory.triggered.connect(self.set_base_directory)

    def set_window_size(self, image: np.ndarray) -> None:
        if image.shape[0] > image.shape[1]:
            self.resize(600, 800)
        elif image.shape[1] > image.shape[0]:
            self.resize(800, 600)
        else:
            self.resize(600, 600)

    def set_base_directory(self) -> None:
        base_dir_str = QFileDialog.getExistingDirectory(
            caption="Select Data Directory.",
            directory=str(self.state.base_data_dir),
        )
        if base_dir_str == "":
            return
        self.state.base_data_dir = Path(base_dir_str)
        self.base_data_dir_updated.emit()
