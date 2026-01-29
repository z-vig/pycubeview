# Local Imports
from pycubeview.cubeview_protocols import (
    CubeViewMainWindowProtocol,
    ImageDisplayProtocol,
    MeasurementAxisDisplayProtocol,
)
from .file_controller import FileController
from .image_controller import ImageController
from .link_controller import LinkController

# PySide6 Imports
from PySide6.QtCore import QObject, Slot


class MainController(QObject):
    def __init__(self, window: CubeViewMainWindowProtocol) -> None:
        super().__init__()
        self._window = window
        self.file = FileController(window)
        self.image_controllers: list[ImageController] = []

        self._connect_signals()

    def _connect_signals(self):
        getattr(self._window, "image_display_added").connect(
            self._on_adding_image_display
        )
        getattr(self._window, "link_displays").connect(
            self._on_linking_displays
        )

    @Slot(ImageDisplayProtocol)
    def _on_adding_image_display(self, img_display: ImageDisplayProtocol):
        print("Image Display Controller Connected")
        self.image_controllers.append(ImageController(img_display))

    @Slot(ImageDisplayProtocol, MeasurementAxisDisplayProtocol)
    def _on_linking_displays(
        self,
        img_display: ImageDisplayProtocol,
        meas_display: MeasurementAxisDisplayProtocol,
    ):
        print("Displays Linked")
        self.link_controller = LinkController(img_display, meas_display)
