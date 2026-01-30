# Local Imports
from .base_controller import BaseController
from pycubeview.ui.widgets.image_display import ImageDisplay, ImageClickData
from pycubeview.ui.widgets.lasso_selector import LassoSelector

# PySide6 Imports
from PySide6.QtCore import Slot


class ImageController(BaseController):
    def __init__(self, image_display: ImageDisplay) -> None:
        self._img_disp = image_display
        self._lasso = LassoSelector(self._img_disp)
        super().__init__()

    def _build_actions(self) -> None:
        return

    def _install_actions(self) -> None:
        return

    def _connect_signals(self) -> None:
        self._img_disp.pixel_clicked.connect(self.roi_click)
        self._img_disp.pixel_clicked.connect(self.print_coordinate)
        self._img_disp.pg_image_view.scene.sigMouseMoved.connect(  # type: ignore  # noqa
            self._lasso.lasso_movement
        )

    @Slot(ImageClickData)
    def print_coordinate(self, click_data: ImageClickData) -> None:
        print(click_data.y_exact, click_data.x_exact)

    @Slot(ImageClickData)
    def roi_click(self, click_data: ImageClickData) -> None:
        self._lasso.on_roi_click(click_data.click_event)
