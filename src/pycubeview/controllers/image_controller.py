# Local Imports
from .base_controller import BaseController
from pycubeview.ui.widgets.image_display import ImageDisplay
from pycubeview.ui.widgets.lasso_selector import LassoSelector
from pycubeview.interaction_filters import (
    is_ctrl_left_click,
    is_regular_left_click,
)
from pycubeview.custom_types import WidgetMode
from pycubeview.global_app_state import AppState
from pycubeview.data_transfer_classes import ImageClickData, ImageScatterPoint
from pycubeview.models.selection_model import SelectionModel

# PySide6 Imports
from PySide6.QtCore import Slot


class ImageController(BaseController):
    def __init__(
        self,
        global_state: AppState,
        selection_model: SelectionModel,
        image_display: ImageDisplay,
    ) -> None:
        self._img_disp = image_display
        self._lasso = LassoSelector(self._img_disp)
        self.scatter_cache: list[ImageScatterPoint] = []
        self.selection_model = selection_model
        super().__init__(global_state)

    def _build_actions(self) -> None:
        return

    def _install_actions(self) -> None:
        return

    def _connect_signals(self) -> None:
        self._img_disp.pixel_clicked.connect(self.try_to_start_lasso)
        self._img_disp.pixel_double_clicked.connect(self.try_to_finish_lasso)
        self._img_disp.pixel_clicked.connect(self.print_coordinate)
        self._img_disp.point_plotted.connect(self.add_point_to_cache)
        self.selection_model.cache_reset.connect(self.reset_cache)

    @Slot(ImageClickData)
    def print_coordinate(self, click_data: ImageClickData) -> None:
        if not is_regular_left_click(click_data):
            return
        if not self.app_state.widget_mode == WidgetMode.COLLECT:
            return
        print(f"Point Clicked: {click_data.x_int}, {click_data.y_int}")

    @Slot(ImageClickData)
    def try_to_start_lasso(self, click_data: ImageClickData) -> None:
        if not is_ctrl_left_click(click_data):
            return
        if self.app_state.widget_mode == WidgetMode.LASSO:
            return
        self.app_state.widget_mode = WidgetMode.LASSO
        self._lasso.start_lasso(click_data)

    @Slot(ImageClickData)
    def try_to_finish_lasso(self, click_data: ImageClickData) -> None:
        if not is_ctrl_left_click(click_data):
            return
        if self.app_state.widget_mode == WidgetMode.COLLECT:
            return
        self.app_state.widget_mode = WidgetMode.COLLECT
        self._lasso.finish_lasso()

    @Slot(ImageScatterPoint)
    def add_point_to_cache(self, scatter: ImageScatterPoint) -> None:
        self.scatter_cache.append(scatter)
        self.selection_model.image_point_added()

    def reset_cache(self) -> None:
        for i in self.scatter_cache:
            self._img_disp.pg_image_view.getView().removeItem(
                i.scatter_plot_item
            )
        self.scatter_cache = []
