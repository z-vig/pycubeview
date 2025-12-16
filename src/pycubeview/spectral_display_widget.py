# Built-Ins
from functools import partial
from pathlib import Path

# PyQt6 Imports
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFileDialog
from PyQt6.QtGui import QAction
from PyQt6.QtCore import pyqtSignal

# Dependencies
import pyqtgraph as pg  # type: ignore
import numpy as np
import cmap
import spectralio as sio
from spectralio.geospatial_models import PointModel

# Local Imports
from .spectrum_edit_window import SpectrumEditWindow
from .valid_colormaps import SequentialColorMap
from .text_input_widget import TextInputDialog


class SpectralDisplayWidget(QWidget):
    """
    Widget for displaying spectral (or other cube) data.

    Methods
    -------
    set_cube
        Sets the spectral (or other) cube for the plot to display from.
    add_spectrum
        Adds data from the current cube at  `coord` to the plot.
    add_group
        Adds a group of data and emits either a data_added or a bulk_data_added
        signal.
    edit_spectrum
        Edits the spectrum input as an argument.
    handle_reset
        Handles a plot reset signal.


    Signals
    -------
    data_added
        Emits when data is added to the plot"
            - (plot: PlotDataItem, err: ErrorBarItem)
    data_updated
        Emits when data on the plot is updated:
            - (plot: PlotDataItem, err: ErrorBarItem, old_name: str,
            new_name: str)
    data_removed
        Emits when data on the plot is removed from the plot.
            - (name: str)
    bulk_data_added
        Emits when more than one plot data item is added at a time.
            - (plot_list: list[PlotDataItem])
    plot_reset
        Emits when the plot is entirely cleared or reset.
            - (None)
    """

    data_added = pyqtSignal(pg.PlotDataItem, pg.ErrorBarItem)
    data_updated = pyqtSignal(pg.PlotDataItem, pg.ErrorBarItem, str, str)
    data_removed = pyqtSignal(str)
    geodata_linked = pyqtSignal()
    bulk_data_added = pyqtSignal(list)
    plot_reset = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()

        self.spec_plot = pg.PlotWidget()
        item = self.spec_plot.getPlotItem()
        if item is None:
            return
        self.current_plot_name: str = "Spectral Group"
        item.setTitle(self.current_plot_name)
        self.spec_legend = self.spec_plot.addLegend()

        self.base_data_dir: Path = Path.cwd()
        self.geodata_fp: Path | None = None

        self.save_cache: list[sio.PointSpectrum1D | sio.SpectrumGroup] = []

        self.wvl = np.empty((0), dtype=np.float32)
        self.cube = np.empty((0, 0, 0), dtype=np.float32)
        self._count = 0
        self._editing = False

        layout = QVBoxLayout()
        layout.addWidget(self.spec_plot)
        self.setLayout(layout)

        # ---- Adding Actions to Right-Click Context Menu ----
        menu = item.getViewBox().menu
        if menu is not None:
            self.plot_name_action = QAction("Set Plot Name", self)
            menu.addAction(self.plot_name_action)

        # ---- Connecting Signals ----
        self.plot_reset.connect(self.handle_reset)

        # ---- Connecting Menu Actions ----
        self.plot_name_action.triggered.connect(self.set_plot_name)

    def link_geodata(self, geodata_fp: Path) -> None:
        self.geodata_fp = Path(geodata_fp)
        self.geodata_linked.emit()

    def set_cube(self, wvl: np.ndarray, data: np.ndarray) -> None:
        if data.ndim != 3:
            return
        self.wvl = wvl
        self.cube = data.astype(np.float32)

    def add_spectrum(
        self,
        coord: tuple[int, int],
        color: pg.Color = pg.Color((200, 200, 200)),
    ) -> sio.PointSpectrum1D:
        current_save = sio.PointSpectrum1D.from_pixel_coord(
            0, 0, spec1d=sio.Spectrum1D.empty()
        )
        self._count += 1
        spectrum = self.cube[*coord, :]
        spec_name = f"SPECTRUM_{self._count:02d}"
        spec_item = pg.PlotDataItem(
            self.wvl,
            spectrum,
            pen=pg.mkPen(color=color, width=1),
            clickable=True,
            name=spec_name,
        )

        current_save.name = spec_name
        current_save.spectrum = list(spectrum)
        current_save.wavelength = sio.WvlModel.default_bbl(
            list(self.wvl.astype(float)), "um"
        )
        current_save.pixel.x = coord[1]
        current_save.pixel.y = coord[0]

        errbars = pg.ErrorBarItem(x=self.wvl, y=spectrum, height=0)
        errbars.setVisible(False)

        self.spec_plot.addItem(spec_item)
        self.data_added.emit(spec_item, errbars)

        spec_item.sigClicked.connect(
            partial(self.edit_spectrum, spec_item, errbars)
        )

        self.save_cache.append(current_save)

        return current_save

    def add_group(
        self,
        coords: np.ndarray,
        display_mean: bool = True,
        single_color: pg.Color = pg.Color((200, 200, 200)),
        color_map: SequentialColorMap = "crameri:hawaii",
        cache_all: bool = False,
    ) -> sio.SpectrumGroup:
        current_save = sio.SpectrumGroup.empty()
        self._count += 1
        if coords.ndim != 2:
            raise ValueError("Group Coordinate Array is the wrong size")
        if coords.shape[1] != 2:
            raise ValueError("Group Coordinate Array is the wrong size")

        spec_array = self.cube[coords[:, 1], coords[:, 0], :]
        mean_spectrum = np.mean(spec_array, axis=0)
        err_spectrum = np.std(spec_array, axis=0, ddof=1)
        spec_name = f"SPECTRUM_{self._count:02d}"
        spec_item = pg.PlotDataItem(
            self.wvl,
            mean_spectrum,
            pen=pg.mkPen(color=single_color, width=1),
            clickable=True,
            name=spec_name,
        )

        _wvl = sio.WvlModel.default_bbl(list(self.wvl.astype(float)), "um")
        spectra_list: list[sio.PointSpectrum1D] = [
            sio.PointSpectrum1D(
                name=f"{spec_name}_{i:04d}",
                spectrum=list(spec_array[i, :].astype(float)),
                wavelength=_wvl,
                pixel=PointModel(x=coords[i, 0], y=coords[i, 1]),
            )
            for i in range(spec_array.shape[0])
        ]
        spectra_pts_list = [
            (coords[n, 0], coords[n, 1]) for n in range(coords.shape[0])
        ]
        current_save.name = spec_name
        current_save.spectra = spectra_list
        current_save.spectra_pts = spectra_pts_list
        current_save.wavelength = _wvl
        current_save.resolve_polygon()

        if display_mean:
            errbars = pg.ErrorBarItem(
                x=self.wvl, y=mean_spectrum, height=2 * err_spectrum, beam=10
            )

            self.spec_plot.addItem(spec_item)
            self.spec_plot.addItem(errbars)
            self.data_added.emit(spec_item, errbars)

            spec_item.sigClicked.connect(
                partial(self.edit_spectrum, spec_item, errbars)
            )

            self.save_cache.append(current_save)

        else:
            self.spec_legend.setVisible(False)
            spec_list: list[pg.PlotDataItem] = []
            base_cmap = cmap.Colormap(color_map)
            ncolors = spec_array.shape[0]
            cmap_lut = base_cmap.lut(ncolors) * 255
            for i in range(ncolors):
                c = pg.mkColor(tuple(cmap_lut[i, :]))
                _spec = pg.PlotDataItem(
                    self.wvl,
                    spec_array[i, :],
                    pen=pg.mkPen(color=c, width=1),
                    clickable=False,
                    name=f"{spec_item.name()}_{i:04d}",
                )
                self.spec_plot.addItem(_spec)
                spec_list.append(_spec)
            self.bulk_data_added.emit(spec_list)

            if cache_all:
                for obj in spectra_list:
                    self.save_cache.append(obj)
            else:
                self.save_cache.append(current_save)

        return current_save

    def edit_spectrum(self, plot: pg.PlotDataItem, err: pg.ErrorBarItem):
        if self._editing:
            print(
                "Close the current spectrum edit window to edit another"
                " spectrum."
            )
            return
        self._editing = True
        current_color = plot.opts["pen"]
        _pen = pg.mkPen({"color": "red"})
        plot.setPen(_pen)

        self.edit_win = SpectrumEditWindow(plot)
        self.edit_win.show()

        def rename_spectrum(old_name: str, new_name: str):
            self.spec_legend.removeItem(plot)
            self.spec_legend.addItem(plot, plot.name())
            self.data_updated.emit(plot, err, old_name, new_name)

        self.edit_win.name_changed.connect(rename_spectrum)

        def delete_spectrum():
            # self.state.current_spectra.remove(plot_curve)
            self.spec_plot.removeItem(plot)
            if err is not None:
                self.spec_plot.removeItem(err)
            self.edit_win.close()
            self._editing = False
            self.data_removed.emit(plot.name())
            for i in self.save_cache:
                if i.name == plot.name():
                    self.save_cache.remove(i)

        self.edit_win.spectrum_deleted.connect(delete_spectrum)

        def close_window():
            self.edit_win.close()
            _pen = pg.mkPen(current_color)
            plot.setPen(_pen)
            self._editing = False

        self.edit_win.closed.connect(close_window)

    def handle_reset(self):
        self.save_cache = []
        self._count = 0

    def save_plot(self) -> None:
        qt_save_dir = QFileDialog.getExistingDirectory(
            caption="Select Save Directory", directory=str(self.base_data_dir)
        )
        if qt_save_dir == "":
            return
        save_dir = Path(qt_save_dir)
        pt_list: list[sio.GeoSpectrum1D] = []
        poly_list: list[sio.SpectrumGroup] = []
        geodata_obj: sio.BaseGeolocationModel | None = None
        if self.geodata_fp is not None:
            geodata_obj = sio.read_geodata(self.geodata_fp)

        for save in self.save_cache:
            save_path = Path(save_dir, save.name)
            sio.write_from_object(save, save_path)

            if isinstance(save, sio.PointSpectrum1D):
                if geodata_obj is not None:
                    geosave = sio.GeoSpectrum1D.from_point_spec(
                        geodata_obj, save
                    )
                    pt_list.append(geosave)

            elif isinstance(save, sio.SpectrumGroup):
                poly_list.append(save)

        if self.geodata_fp is not None:
            group_name = self.current_plot_name.lower().replace(" ", "_")
            shp_file_dir = Path(save_dir, f"{group_name}.shapes")
            if not shp_file_dir.exists():
                shp_file_dir.mkdir()
            if len(pt_list) > 0:
                sio.make_points(
                    pt_list, Path(shp_file_dir, f"{group_name}_points.shp")
                )
            if len(poly_list) > 0:
                sio.make_polygons(
                    poly_list,
                    self.geodata_fp,
                    Path(shp_file_dir, f"{group_name}_areas.shp"),
                )

    def set_plot_name(self) -> None:
        dialog = TextInputDialog()
        item = self.spec_plot.getPlotItem()
        if item is None:
            return
        if dialog.exec():
            txt = dialog.text
            if txt is None:
                return
            self.current_plot_name = txt
            item.setTitle(txt)
