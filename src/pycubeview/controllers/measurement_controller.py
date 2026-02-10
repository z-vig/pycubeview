# Built-Ins
from pathlib import Path
from copy import copy

# Local Imports
from .base_controller import BaseController
from pycubeview.ui.widgets.measurement_processor import MeasurementProcessor
from pycubeview.ui.widgets.meas_display import MeasurementAxisDisplay
from pycubeview.data_transfer_classes import Measurement
from pycubeview.global_app_state import AppState
from pycubeview.services.process_measurements import (
    spectral_processing,
    ProcessingFlag,
)
from pycubeview.services.save_spectral_cache import save_spectral_cache
from pycubeview.ui.widgets.spectral_processing_steps import (
    get_spectral_processing_steps,
)

# Dependencies
import spectralio as sio

# PySide6 Imports
from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import QFileDialog, QInputDialog
from PySide6.QtGui import QAction


class MeasurementController(BaseController):
    cache_reset = Signal()
    added_to_cache = Signal(Measurement)

    def __init__(
        self,
        global_state: AppState,
        meas_display: MeasurementAxisDisplay,
    ) -> None:
        self._meas = meas_display
        self.measurement_cache: list[Measurement] = []
        self._unprocessed_cache: list[Measurement] = []
        super().__init__(global_state)

        # ---- Processor AddOn ----
        self.processor = MeasurementProcessor(self._meas)
        self.processor.hide()

        steps = get_spectral_processing_steps(self.processor)
        self._step_cfg_list = []
        for step_name, step_config in steps:
            self._step_cfg_list.append(step_config)
            self.processor.add_step(step_name, step_config)
        self.processor.processing_update.connect(self.on_processing_update)

    def _build_actions(self) -> None:
        self.reset_cache_action = self.cat.reset_cache.build(self._meas, self)
        self.set_plot_name_action = self.cat.set_plot_name.build(
            self._meas, self
        )
        self.save_spectral_cache_action = self.cat.save_spectral_cache.build(
            self._meas, self
        )
        self.open_processor_action = self.cat.open_processor.build(
            self._meas, self
        )
        self.toggle_errorbars_action = QAction("Show Errorbars", self._meas)
        self.toggle_errorbars_action.setCheckable(True)
        self.toggle_errorbars_action.toggled.connect(self.toggle_error_bars)
        self.toggle_errorbars_action.setChecked(True)

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
        menu.addAction(self.set_plot_name_action)
        menu.addAction(self.save_spectral_cache_action)
        menu.addAction(self.open_processor_action)
        menu.addAction(self.toggle_errorbars_action)

    def _connect_signals(self) -> None:
        self._meas.measurement_added.connect(self.on_adding_measurement)
        self._meas.measurement_deleted.connect(self.on_deleting_measurement)

    @Slot(Measurement)
    def on_adding_measurement(self, meas: Measurement) -> None:
        self.measurement_cache.append(meas)
        self._unprocessed_cache.append(meas)
        self.processor.run_processing()
        self.added_to_cache.emit(meas)
        print(
            f"Measurement Added: {meas.name}, {meas.id},"
            f" total: {len(self.measurement_cache)}"
        )
        if meas.plot_data_errorbars is None:
            return
        if not self.toggle_errorbars_action.isChecked():
            meas.plot_data_errorbars.hide()

    @Slot(Measurement)
    def on_deleting_measurement(self, meas: Measurement):
        self.measurement_cache.remove(meas)
        self._unprocessed_cache.remove(meas)
        print(
            f"Measurement Deleted: {meas.name}, {meas.id},"
            f" total: {len(self.measurement_cache)}"
        )

    def on_processing_update(self, flags: list[ProcessingFlag]):
        for i in self.measurement_cache:
            processed_spec = spectral_processing(
                measurement=i, processing_flags=flags
            )
            x, _ = i.plot_data_item.getData()
            i.plot_data_item.setData(x=x, y=processed_spec.spectrum)
            if i.plot_data_errorbars is not None:
                i.plot_data_errorbars.setData(x=x, y=processed_spec.spectrum)
                if not self.toggle_errorbars_action.isChecked():
                    i.plot_data_errorbars.hide()

    def reset_cache(self) -> None:
        print(f"Items in Cache: {len(self.measurement_cache)}")
        to_be_removed = copy(self.measurement_cache)
        for meas in to_be_removed:
            print(meas.name)
            self._meas.delete_measurement(meas)
        self.measurement_cache = []
        self._unprocessed_cache = []
        self._meas.cmap.reset()

    def set_plot_name(self) -> None:
        new_title, ok = QInputDialog.getText(
            self._meas, "Set Plot Title", f"{self._meas.name}"  # type: ignore
        )
        if ok:
            self._meas.name = new_title

    def save_spectral_cache(self) -> None:
        """Open file dialog and save spectral measurements to disk."""
        # Get save directory from user
        qt_fp = QFileDialog.getExistingDirectory(
            caption="Select Base Directory",
            dir=str(self.app_state.base_fp),
        )
        if qt_fp == "":
            return None

        save_dir = Path(qt_fp)

        # Build wavelength model from measurement display
        wvl = sio.WvlModel.fromarray(self._meas.meas_lbl, "nm")

        # Delegate to service layer
        save_spectral_cache(
            self.measurement_cache,
            save_dir,
            wvl,
            self.app_state.geodata,
            self._meas.name,
            self._meas.cube,
            self.app_state.save_mode,
        )

    def open_processor(self) -> None:
        self.processor.show()

    def toggle_error_bars(self) -> None:
        _state = self.toggle_errorbars_action.isChecked()

        for i in self.measurement_cache:
            if i.plot_data_errorbars is not None:
                if not _state:
                    i.plot_data_errorbars.hide()
                else:
                    i.plot_data_errorbars.show()
