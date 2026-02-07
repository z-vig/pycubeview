# Built-Ins
from pathlib import Path

# Local Imports
from .base_controller import BaseController
from pycubeview.ui.widgets.measurement_processor import MeasurementProcessor
from pycubeview.ui.widgets.meas_display import MeasurementAxisDisplay
from pycubeview.data_transfer_classes import Measurement
from pycubeview.global_app_state import AppState
from pycubeview.models.selection_model import SelectionModel
from pycubeview.services.process_measurements import (
    spectral_processing,
    ProcessingFlag,
)
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
        selection_model: SelectionModel,
        meas_display: MeasurementAxisDisplay,
    ) -> None:
        self._meas = meas_display
        self.measurement_cache: list[Measurement] = []
        self._unprocessed_cache: list[Measurement] = []
        self.selection_model = selection_model
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
        self.selection_model.meas_plot_added()
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
        self.selection_model.meas_plot_removed()
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
        self._meas.plotted_count = 0
        for meas in self.measurement_cache:
            self._meas.pg_plot.removeItem(meas.plot_data_item)
            self._meas.pg_plot.removeItem(meas.plot_data_errorbars)
        self.measurement_cache = []
        self.selection_model.initiate_reset()

    def set_plot_name(self) -> None:
        new_title, ok = QInputDialog.getText(
            self._meas, "Set Plot Title", f"{self._meas.name}"  # type: ignore
        )
        if ok:
            self._meas.name = new_title

    def save_spectral_cache(self) -> None:
        # Setting Save Directory
        qt_fp = QFileDialog.getExistingDirectory(
            caption="Select Base Directory",
            dir=str(self.app_state.base_fp),
        )
        if qt_fp == "":
            return None
        save_dir = Path(qt_fp)

        # Getting WvlModel object from measurement display.
        wvl = sio.WvlModel.fromarray(self._meas.meas_lbl, "nm")

        # Setting up save bins
        point_saves: list[sio.PointSpectrum1D] = []
        group_saves: list[sio.SpectrumGroup] = []

        # Saving .spec and .specgrp files.
        for meas in self.measurement_cache:
            save_path = Path(save_dir, meas.name)
            if meas.type == "Point":
                _spec = sio.Spectrum1D(
                    name=meas.name,
                    spectrum=list(meas.yvalues),
                    wavelength=sio.WvlModel.fromarray(
                        self._meas.meas_lbl, "nm"
                    ),
                    bbl_applied=True,
                )
                spec = sio.PointSpectrum1D.from_pixel_coord(
                    x=meas.pixel_x, y=meas.pixel_y, spec1d=_spec
                )
                sio.write_from_object(spec, save_path)
                point_saves.append(spec)
            elif meas.type == "Group":
                if (meas.x_pixels is None) or (meas.y_pixels is None):
                    continue
                spec_list: list[sio.PointSpectrum1D] = []
                spec_points: list[tuple[int, int]] = []
                for n in range(meas.x_pixels.size):
                    x = meas.x_pixels[n]
                    y = meas.y_pixels[n]
                    _spec = sio.Spectrum1D(
                        name=meas.name,
                        spectrum=list(self._meas.cube[y, x, :]),
                        wavelength=wvl,
                        bbl_applied=True,
                    )
                    spec = sio.PointSpectrum1D.from_pixel_coord(
                        x=x, y=y, spec1d=_spec
                    )
                    spec_list.append(spec)
                    spec_points.append((x, y))

                spec_grp = sio.SpectrumGroup(
                    name=meas.name,
                    spectra=spec_list,
                    spectra_pts=spec_points,
                    wavelength=wvl,
                )
                sio.write_from_object(spec_grp, save_path)
                group_saves.append(spec_grp)

        # Saving shapefiles, if geodata is set.
        if self.app_state.geodata is None:
            return

        geoloc = sio.read_geodata(self.app_state.geodata)
        shp_file_dir = Path(save_dir, f"{self._meas.name}.shapes")
        if not shp_file_dir.exists():
            shp_file_dir.mkdir()
        if len(point_saves) > 0:
            geo_point_saves = [
                sio.GeoSpectrum1D.from_point_spec(geoloc, i)
                for i in point_saves
            ]
            sio.make_points(
                geo_point_saves,
                Path(shp_file_dir, f"{self._meas.name}_points.shp"),
            )
        if len(group_saves) > 0:
            sio.make_polygons(
                group_saves,
                self.app_state.geodata,
                Path(shp_file_dir, f"{self._meas.name}_areas.shp"),
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
