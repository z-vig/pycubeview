# Local Imports
from .base_controller import BaseController
from pycubeview.ui.widgets.image_display import ImageClickData
from pycubeview.cubeview_protocols import (
    ImageDisplayProtocol,
    MeasurementAxisDisplayProtocol,
)

# PySide6 Imports
from PySide6.QtCore import Slot


class LinkController(BaseController):
    def __init__(
        self,
        image_display: ImageDisplayProtocol,
        measurement_display: MeasurementAxisDisplayProtocol,
    ) -> None:
        self._img = image_display
        self._meas = measurement_display
        super().__init__()

    def _build_actions(self) -> None:
        return

    def _install_actions(self) -> None:
        return

    def _connect_signals(self) -> None:
        self._img.pixel_clicked.connect(self._on_pixel_select)

    @Slot(ImageClickData)
    def _on_pixel_select(self, click_data: ImageClickData):
        self._meas.add_measurement(click_data.y_int, click_data.x_int)
