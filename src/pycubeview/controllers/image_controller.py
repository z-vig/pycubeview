# Built-Ins
from uuid import UUID

# Dependencies
import pyqtgraph as pg  # type: ignore

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
from pycubeview.data_transfer_classes import (
    ImageClickData,
    ImageScatterPoint,
    LassoData,
)
from pycubeview.models.selection_model import SelectionModel

# PySide6 Imports
from PySide6.QtCore import Slot, QPointF, Signal
from PySide6.QtGui import QPolygonF
from PySide6.QtWidgets import QGraphicsPolygonItem


class ImageController(BaseController):
    lasso_plotted = Signal(LassoData)

    def __init__(
        self,
        global_state: AppState,
        selection_model: SelectionModel,
        image_display: ImageDisplay,
    ) -> None:
        self._img_disp = image_display
        self._lasso = LassoSelector(self._img_disp)
        self.scatter_cache: list[ImageScatterPoint] = []
        self.poly_cache: dict[UUID, QGraphicsPolygonItem] = {}
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
        self._img_disp.point_deleted.connect(self.remove_point_from_cache)
        self.selection_model.cache_reset.connect(self.reset_cache)
        self._img_disp._vbox.scene().sigMouseMoved.connect(
            self._lasso.lasso_movement
        )
        self._lasso.lasso_finished.connect(self.plot_lasso_polygon)

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

    @Slot(UUID)
    def remove_point_from_cache(self, id: UUID) -> None:
        for i in self.scatter_cache:
            if i.id == id:
                self._img_disp._vbox.removeItem(i.scatter_plot_item)
        for poly_id, poly_obj in self.poly_cache.items():
            if poly_id == id:
                self._img_disp._vbox.removeItem(poly_obj)

    def reset_cache(self) -> None:
        for i in self.scatter_cache:
            self._img_disp._vbox.removeItem(i.scatter_plot_item)
        for j in self.poly_cache:
            self._img_disp._vbox.removeItem(j)
        self.scatter_cache = []
        self.poly_cache = {}

    @Slot(LassoData)
    def plot_lasso_polygon(self, lasso_data: LassoData) -> None:
        pts = [
            QPointF(*lasso_data.vertices[n, :])
            for n in range(lasso_data.vertices.shape[0])
        ]
        poly = QPolygonF(pts)
        poly_item = QGraphicsPolygonItem(poly)
        poly_item.setPen(pg.mkPen("k", width=2))

        self.poly_cache[lasso_data.id] = poly_item
        self._img_disp._vbox.addItem(poly_item)
        self.lasso_plotted.emit(lasso_data)
