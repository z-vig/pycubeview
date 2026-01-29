# Local Imports
from .base_controller import BaseController
from pycubeview.cubeview_protocols import ImageDisplayProtocol

# PySide6 Imports
from PySide6.QtCore import Slot


class ImageController(BaseController):
    def __init__(self, image_display: ImageDisplayProtocol) -> None:
        self._img_disp = image_display
        super().__init__()

    def _build_actions(self) -> None:
        return

    def _install_actions(self) -> None:
        return

    def _connect_signals(self) -> None:
        getattr(self._img_disp, "pixel_clicked").connect(self.print_coordinate)

    @Slot(int, int)
    def print_coordinate(self, y: int, x: int) -> None:
        print(y, x)
