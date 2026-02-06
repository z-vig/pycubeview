# Local Imports
from .base_controller import BaseController
from .image_controller import ImageController
from .measurement_controller import MeasurementController
from pycubeview.interaction_filters import is_regular_left_click
from pycubeview.custom_types import WidgetMode
from pycubeview.global_app_state import AppState
from pycubeview.data_transfer_classes import (
    ImageClickData,
    Measurement,
    LassoData,
)

# PySide6 Imports
from PySide6.QtCore import Slot


class LinkController(BaseController):
    def __init__(
        self,
        global_state: AppState,
        image_controller: ImageController,
        measurement_controller: MeasurementController,
    ) -> None:
        self._img_ctrl = image_controller
        self._meas_ctrl = measurement_controller
        self._img = image_controller._img_disp
        self._meas = measurement_controller._meas
        super().__init__(global_state)

    def _build_actions(self) -> None:
        return

    def _install_actions(self) -> None:
        return

    def _connect_signals(self) -> None:
        self._img_ctrl.lasso_plotted.connect(self._on_lasso_plotted)
        self._img.pixel_clicked.connect(self._on_pixel_select)
        self._meas.measurement_added.connect(self._on_measurement_added)
        self._meas.measurement_deleted.connect(self._on_measurement_deleted)

    @Slot(LassoData)
    def _on_lasso_plotted(self, lasso_data: LassoData):
        xpixels = lasso_data.lasso_pixels[:, 0]
        ypixels = lasso_data.lasso_pixels[:, 1]
        self._meas.add_measurement(
            x_pixels=xpixels, y_pixels=ypixels, id=lasso_data.id
        )

    @Slot(ImageClickData)
    def _on_pixel_select(self, click_data: ImageClickData) -> None:
        if not is_regular_left_click(click_data):
            return
        if self.app_state.widget_mode != WidgetMode.COLLECT:
            return
        self._meas.add_measurement(y=click_data.y_int, x=click_data.x_int)

    @Slot(Measurement)
    def _on_measurement_added(self, measurement: Measurement) -> None:
        print(f"Measurement Added to {self._img.name}")
        self._img.plot_point(
            x=measurement.pixel_x,
            y=measurement.pixel_y,
            color=measurement.color,
            identifier=measurement.id,
        )

    @Slot(Measurement)
    def _on_measurement_deleted(self, measurement: Measurement) -> None:
        self._img.delete_point(measurement.id)
