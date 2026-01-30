# Local Imports
from .base_controller import BaseController
from pycubeview.cubeview_protocols import MeasurementAxisDisplayProtocol
from pycubeview.ui.widgets.meas_display import Measurement


class MeasurementController(BaseController):
    def __init__(self, meas_display: MeasurementAxisDisplayProtocol) -> None:
        self._meas = meas_display
        self.measurement_cache: list[Measurement] = []
        super().__init__()

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
        self.measurement_cache.append(meas)

    def reset_cache(self):
        self._meas.plotted_count = 0
        for meas in self.measurement_cache:
            self._meas.pg_plot.removeItem(meas.plot_data_item)
