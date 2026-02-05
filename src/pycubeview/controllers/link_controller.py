# Local Imports
from .base_controller import BaseController
from pycubeview.ui.widgets.image_display import ImageDisplay
from pycubeview.ui.widgets.meas_display import MeasurementAxisDisplay
from pycubeview.interaction_filters import is_regular_left_click
from pycubeview.custom_types import WidgetMode
from pycubeview.global_app_state import AppState
from pycubeview.data_transfer_classes import ImageClickData, Measurement

# PySide6 Imports
from PySide6.QtCore import Slot


class LinkController(BaseController):
    def __init__(
        self,
        global_state: AppState,
        image_display: ImageDisplay,
        measurement_display: MeasurementAxisDisplay,
    ) -> None:
        self._img = image_display
        self._meas = measurement_display
        super().__init__(global_state)

    def _build_actions(self) -> None:
        return

    def _install_actions(self) -> None:
        return

    def _connect_signals(self) -> None:
        self._img.pixel_clicked.connect(self._on_pixel_select)
        self._meas.measurement_added.connect(self._on_measurement_added)
        self._meas.measurement_deleted.connect(self._on_measurement_deleted)

    @Slot(ImageClickData)
    def _on_pixel_select(self, click_data: ImageClickData) -> None:
        if not is_regular_left_click(click_data):
            return
        if self.app_state.widget_mode != WidgetMode.COLLECT:
            return
        self._meas.add_measurement(y=click_data.y_int, x=click_data.x_int)

    @Slot(Measurement)
    def _on_measurement_added(self, measurement: Measurement) -> None:
        self._img.plot_point(
            x=measurement.pixel_x,
            y=measurement.pixel_y,
            color=measurement.color,
            identifier=measurement.id,
        )

    @Slot(Measurement)
    def _on_measurement_deleted(self, measurement: Measurement) -> None:
        self._img.delete_point(measurement.id)
