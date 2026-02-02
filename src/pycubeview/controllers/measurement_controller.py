# Local Imports
from .base_controller import BaseController
from pycubeview.cubeview_protocols import MeasurementAxisDisplayProtocol
from pycubeview.data_transfer_classes import Measurement
from pycubeview.global_app_state import AppState
from pycubeview.models.selection_model import SelectionModel

# PySide6 Imports
from PySide6.QtCore import Signal


class MeasurementController(BaseController):
    cache_reset = Signal()

    def __init__(
        self,
        global_state: AppState,
        selection_model: SelectionModel,
        meas_display: MeasurementAxisDisplayProtocol,
    ) -> None:
        self._meas = meas_display
        self.measurement_cache: list[Measurement] = []
        self.selection_model = selection_model
        super().__init__(global_state)

    def _build_actions(self) -> None:
        self.reset_cache_action = self.cat.reset_cache.build(self._meas, self)

    def _install_actions(self) -> None:
        item = self._meas.pg_plot.getPlotItem()
        if item is None:
            return

        vb = item.getViewBox()
        if vb is None:
            return

        menu = vb.menu
        if menu is None:
            return

        menu.addAction(self.reset_cache_action)

    def _connect_signals(self) -> None:
        self._meas.measurement_added.connect(self.on_adding_measurement)

    def on_adding_measurement(self, meas: Measurement):
        print(f"Measurement Added: {meas.name}, {meas.id}")
        self.selection_model.meas_plot_added()
        self.measurement_cache.append(meas)

    def reset_cache(self):
        self._meas.plotted_count = 0
        for meas in self.measurement_cache:
            self._meas.pg_plot.removeItem(meas.plot_data_item)
        self.measurement_cache = []
        self.selection_model.initiate_reset()
