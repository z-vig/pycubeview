# Local Imports
from pycubeview.cubeview_protocols import (
    CubeViewMainWindowProtocol,
    ImageDisplayProtocol,
    MeasurementAxisDisplayProtocol,
)
from .file_controller import FileController
from .image_controller import ImageController
from .link_controller import LinkController
from .measurement_controller import MeasurementController

# PySide6 Imports
from PySide6.QtCore import QObject, Slot


class MainController(QObject):
    def __init__(self, window: CubeViewMainWindowProtocol) -> None:
        super().__init__()
        self._window = window
        self.file = FileController(window)
        self.image_controllers: list[ImageController] = []
        self.measurement_controllers: list[MeasurementController] = []

        self._connect_signals()

    def _connect_signals(self):
        self._window.image_display_added.connect(self._on_adding_image_display)
        self._window.measurement_display_added.connect(
            self._on_adding_measurement_display
        )
        self._window.link_displays.connect(self._on_linking_displays)

    @Slot(ImageDisplayProtocol)
    def _on_adding_image_display(self, img_display: ImageDisplayProtocol):
        print("Image Display Controller Connected")
        self.image_controllers.append(ImageController(img_display))  # type: ignore  # noqa

    @Slot(MeasurementAxisDisplayProtocol)
    def _on_adding_measurement_display(
        self, meas_display: MeasurementAxisDisplayProtocol
    ):
        self.measurement_controllers.append(
            MeasurementController(meas_display)
        )

    @Slot(ImageDisplayProtocol, MeasurementAxisDisplayProtocol)
    def _on_linking_displays(
        self,
        img_display: ImageDisplayProtocol,
        meas_display: MeasurementAxisDisplayProtocol,
    ):
        print("Displays Linked")
        self.link_controller = LinkController(img_display, meas_display)
