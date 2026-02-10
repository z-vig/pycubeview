# Local Imports
from pycubeview.ui.widgets.image_display import ImageDisplay
from pycubeview.ui.widgets.meas_display import MeasurementAxisDisplay
from .status_indicator import BaseStatusIndicator

# Dependencies
import numpy as np

# PySide6 Imports
from PySide6.QtWidgets import QMainWindow, QDockWidget, QWidget, QMenu
from PySide6.QtCore import Qt, Signal

PKG_VERSION = "1.1.0"


class CubeViewMainWindow(QMainWindow):
    image_display_added = Signal(ImageDisplay)
    measurement_display_added = Signal(MeasurementAxisDisplay)
    link_displays = Signal(ImageDisplay, MeasurementAxisDisplay)
    follow_img_display = Signal(ImageDisplay, ImageDisplay)  # Follower, Leader
    follow_meas_display = Signal(
        MeasurementAxisDisplay, MeasurementAxisDisplay
    )  # Follower, Leader

    def __init__(self) -> None:
        # Superclass initialization
        super().__init__()
        self.central_widget = self.centralWidget()
        self.image_displays: dict[str, ImageDisplay] = {}
        self.meas_displays: dict[str, MeasurementAxisDisplay] = {}

        self._image_docks: list[QDockWidget] = []
        self._meas_docks: list[QDockWidget] = []

        # Configuring Menus
        self.file_menu = self.menuBar().addMenu("File")
        self.image_menu = self.menuBar().addMenu("Image")
        self.meas_menu = self.menuBar().addMenu("Measurement")
        self.save_mode_menu = QMenu("Save Mode", self)
        self.meas_menu.addMenu(self.save_mode_menu)

        # Setting StatusBar
        self.status_bar = self.statusBar()
        self.setStatusBar(self.status_bar)

        # Status Indicators
        self.geo_indicator = BaseStatusIndicator(self, "Geo")
        self.geo_indicator.icon.setStatusTip("Geo data has been loaded.")

        # Window Settings
        self.setWindowTitle(f"CubeView v{PKG_VERSION}")
        self._set_window_size()

    def _set_window_size(self, image: np.ndarray | None = None) -> None:
        """Set the window size based on the image dimensions."""
        if image is not None:
            if image.shape[0] > image.shape[1]:
                self.resize(600, 800)  # Portrait
            elif image.shape[1] > image.shape[0]:
                self.resize(800, 600)  # Landscape
            else:
                self.resize(600, 600)  # Square
        else:
            self.resize(600, 600)

    def add_image_display(self, arr: np.ndarray) -> None:
        num_id = len(self.image_displays) + 1
        imdisp = ImageDisplay()
        imdisp.name = f"ImageDisplay{num_id}"
        imdisp.image_data = arr
        self.image_displays.update({imdisp.name: imdisp})
        dock = self._configure_dock_widget(
            imdisp,
            dock_name=f"Image{num_id}",
            dock_area=Qt.DockWidgetArea.LeftDockWidgetArea,
        )

        self.image_display_added.emit(imdisp)
        self._image_docks.append(dock)

        if len(self._image_docks) > 1:
            self.tabifyDockWidget(self._image_docks[0], dock)

        if (len(self.meas_displays) == 1) and (len(self.image_displays) == 1):
            self.link_displays.emit(
                self.image_displays[imdisp.name],
                list(self.meas_displays.values())[0],
            )

        # Automatically follows the first "Base" Image Display
        if len(self.image_displays) > 1:
            self.follow_img_display.emit(
                self.image_displays[imdisp.name],
                list(self.image_displays.values())[0],
            )

    def add_meas_display(
        self,
        arr: np.ndarray,
        lbls: np.ndarray,
        lbl_unit: str = "Wavelength (nm)",
    ) -> None:
        num_id = len(self.meas_displays) + 1
        meas = MeasurementAxisDisplay(lbl_unit)
        meas.name = f"MeasurementDisplay{num_id}"
        meas.cube = arr
        meas.meas_lbl = lbls
        self.meas_displays[meas.name] = meas
        dock = self._configure_dock_widget(
            meas,
            dock_name=f"Plot{num_id}",
            dock_area=Qt.DockWidgetArea.LeftDockWidgetArea,
        )

        self.measurement_display_added.emit(meas)
        self._meas_docks.append(dock)

        if len(self._meas_docks) > 1:
            self.tabifyDockWidget(self._meas_docks[0], dock)

        if (len(self.meas_displays) == 1) and (len(self.image_displays) > 0):
            self.link_displays.emit(
                list(self.image_displays.values())[0],
                self.meas_displays[meas.name],
            )

        if len(self.meas_displays) > 1:
            self.follow_meas_display.emit(
                self.meas_displays[meas.name],
                list(self.meas_displays.values())[0],
            )

    def _configure_dock_widget(
        self,
        inner_widget: QWidget,
        dock_name: str,
        dock_area: Qt.DockWidgetArea,
    ) -> QDockWidget:
        dock = QDockWidget(dock_name, self)
        dock.setWidget(inner_widget)
        dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea
            | Qt.DockWidgetArea.RightDockWidgetArea
            | Qt.DockWidgetArea.TopDockWidgetArea
            | Qt.DockWidgetArea.BottomDockWidgetArea
        )
        self.addDockWidget(dock_area, dock)

        dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
        )

        return dock

    def reset_docks(self) -> None:
        """Remove and delete all dock widgets and clear internal registries."""
        # Remove docks from both image and measurement lists
        for dock_list in (self._image_docks, self._meas_docks):
            for dock in list(dock_list):
                # Try to undock from the main window (no-op if already removed)
                try:
                    self.removeDockWidget(dock)
                except Exception:
                    pass

                # Deletion of the inner widget to avoid leaks
                widget = dock.widget()
                if widget is not None:
                    widget.setParent(None)
                    widget.deleteLater()

                # Close and delete the dock itself
                try:
                    dock.close()
                except Exception:
                    pass
                dock.setParent(None)
                dock.deleteLater()

            dock_list.clear()

        # Clear tracked display registries
        self.image_displays.clear()
        self.meas_displays.clear()
