# Built-Ins
from typing import Optional
from tkinter.filedialog import askopenfilename

# PyQt6 Imports
from PyQt6 import QtWidgets as qtw
from PyQt6 import QtGui
from PyQt6 import QtCore

# Dependencies
from pyqtgraph.dockarea import Dock, DockArea  # type: ignore
import numpy as np
import pyqtgraph as pg  # type: ignore
import spectralio as sio
import cmap

# Local Imports
from .base_window import BaseWindow
from .image_display_widget import ImagePickerWidget
from .spectral_display_widget import SpectralDisplayWidget
from .line_roi_window import LineRoiWindow
from .file_opening_utils import open_cube, open_wvl
from .util_classes import PixelValue
from .valid_colormaps import QualitativeColorMap, SequentialColorMap


class CubeViewWindow(BaseWindow):
    def __init__(
        self,
        wvl: Optional[np.ndarray | str] = None,
        image_data: Optional[np.ndarray | str] = None,
        cube_data: Optional[np.ndarray | str] = None,
        qualitative_color_map: QualitativeColorMap = "colorbrewer:Dark2",
        sequential_color_map: SequentialColorMap = "crameri:hawaii",
    ) -> None:
        super().__init__()

        self.qcmap = cmap.Colormap(qualitative_color_map)
        self.n_qcolors = len(self.qcmap.color_stops)
        self.scmap = cmap.Colormap(sequential_color_map)

        self.polygon_cache: dict[str, qtw.QGraphicsPolygonItem | None] = {}

        dock_area = DockArea()
        self.setCentralWidget(dock_area)

        # ---- Connecting menu actions to slots ----
        self.open_display.triggered.connect(self.load_image)
        self.open_cube.triggered.connect(self.load_cube)
        self.clear_spectra.triggered.connect(self.empty_cache)

        # ---- Image Dock ----
        self.imview_dock = Dock(name="Image Window")
        dock_area.addDock(self.imview_dock, "top")

        self.img_picker = ImagePickerWidget()
        self.imview_dock.addWidget(self.img_picker)

        # ---- Spectral Display Dock ----
        self.spec_dock = Dock(name="Spectral Display Window")
        dock_area.addDock(self.spec_dock, "bottom")

        self.spectral_display = SpectralDisplayWidget()
        self.spec_dock.addWidget(self.spectral_display)

        # ---- Auxillary Spectral Viewing Window ----
        self.aux_spec_display = LineRoiWindow()

        # ---- Linking Image and Spectral Display ----
        def intercept_pixel_coord(y: int, x: int):
            spectrum_name = self.spectral_display.add_spectrum(
                (y, x),
                color=self.qcmap[self.state.color_cycle_pos],  # type: ignore
            )
            self.polygon_cache[spectrum_name] = None
            self.state.color_cycle_pos += 1
            if self.state.color_cycle_pos == self.n_qcolors:
                self.state.color_cycle_pos = 0
                raise UserWarning(
                    "Number of spectra have exceeded the length of the"
                    "qualitative colormap. Consider saving and clearing"
                    "spectra before continuing."
                )

        def cache_spectrum(
            plot: pg.PlotDataItem, err: pg.ErrorBarItem
        ) -> None:
            name = plot.name()
            if name is None:
                return
            self.state.spectrum_cache[name] = (plot, err)
            n_cached = len(self.state.spectrum_cache)
            self.clear_spectra.setStatusTip(
                f"Clear {n_cached} spectra from memory."
            )
            self.save_spectra.setStatusTip(
                f"Save {n_cached} spectra currently in memory."
            )

        def update_cache(
            plot: pg.PlotDataItem,
            err: pg.ErrorBarItem,
            old_name: str,
            new_name: str,
        ):
            del self.state.spectrum_cache[old_name]
            self.state.spectrum_cache[new_name] = (plot, err)
            self.polygon_cache[new_name] = self.polygon_cache.pop(old_name)

        def intercept_roi(in_coords: np.ndarray, verts: np.ndarray):
            group_name = self.spectral_display.add_group(
                in_coords,
                single_color=self.qcmap[self.state.color_cycle_pos],  # type: ignore  # noqa
            )
            pts = [QtCore.QPointF(*verts[n, :]) for n in range(verts.shape[0])]
            poly = QtGui.QPolygonF(pts)
            poly_item = qtw.QGraphicsPolygonItem(poly)
            poly_item.setPen(pg.mkPen("k", width=2))
            poly_item.setBrush(QtGui.QBrush(QtGui.QColor(255, 0, 0, 30)))
            self.polygon_cache[group_name] = poly_item
            self.img_picker.imview.getView().addItem(poly_item)
            self.state.color_cycle_pos += 1
            if self.state.color_cycle_pos == self.n_qcolors:
                self.state.color_cycle_pos = 0
                raise UserWarning(
                    "Number of spectra have exceeded the length of the"
                    "qualitative colormap. Consider saving and clearing"
                    "spectra before continuing."
                )

        def remove_spectrum(name):
            poly = self.polygon_cache[name]
            if poly is not None:
                self.img_picker.imview.getView().removeItem(poly)

            del self.polygon_cache[name]
            del self.state.spectrum_cache[name]

            self.clear_spectra.setStatusTip(
                f"Clear {len(self.state.spectrum_cache)} spectra from memory."
            )
            self.save_spectra.setStatusTip(
                f"Save {len(self.state.spectrum_cache)} spectra currently in"
                " memory"
            )

        def open_aux_window():
            self.aux_spec_display.show()

        def intercept_line_roi(coords: np.ndarray):
            for i in self.state.line_roi_cache:
                self.aux_spec_display.display_widget.spec_plot.removeItem(i)
            self.aux_spec_display.display_widget.add_group(
                coords, display_mean=False
            )
            brush_list = []
            ncolors = coords.shape[0]
            print("NColors: ", ncolors)
            cmap_lut = self.scmap.lut(ncolors) * 255
            for i in range(ncolors):
                c = pg.mkColor(tuple(cmap_lut[i, :]))
                brush_list.append(pg.mkBrush(color=c))
            scatter_plot = pg.ScatterPlotItem(
                pos=coords, brush=brush_list, pen=pg.mkPen((0, 0, 0, 0))
            )
            self.img_picker.imview.getView().removeItem(
                self.state.line_roi_scatter_plot
            )
            self.img_picker.imview.getView().addItem(scatter_plot)
            self.state.line_roi_scatter_plot = scatter_plot

        def cache_line_roi(plot_list: list[pg.PlotDataItem]):
            self.state.line_roi_cache = plot_list

        def close_aux_window():
            self.img_picker.line_roi.setVisible(False)

        # Image Picker Connections
        self.img_picker.pixel_picked.connect(intercept_pixel_coord)
        self.img_picker.lasso_finished.connect(intercept_roi)
        self.img_picker.line_roi_started.connect(open_aux_window)
        self.img_picker.line_roi_updated.connect(intercept_line_roi)

        # Spectral Display Connections
        self.spectral_display.data_added.connect(cache_spectrum)
        self.spectral_display.data_updated.connect(update_cache)
        self.spectral_display.data_removed.connect(remove_spectrum)

        # Aux Spectral Display Connections
        self.aux_spec_display.updated.connect(self.img_picker.update_line_roi)
        self.aux_spec_display.closed.connect(close_aux_window)
        self.aux_spec_display.display_widget.bulk_data_added.connect(
            cache_line_roi
        )

        # Status Bar Connections
        def cursor_message(x: float, y: float, val: PixelValue) -> None:
            if x == -999 and y == -999 and val == -999:
                self.status_bar.clearMessage()
                return
            if val.pixel_type == "single":
                self.status_bar.showMessage(
                    f"x={x:.1f}   y={y:.1f}   value={val.v:.5f}"
                )
            elif val.pixel_type == "rgb":
                self.status_bar.showMessage(
                    f"x={x:.1f}   y={y:.1f}   r={val.r:.2f}  g={val.g:.2f} "
                    f"b={val.b:.2f}"
                )

        self.img_picker.mouse_moved.connect(cursor_message)

        if isinstance(image_data, np.ndarray):
            self.set_window_size(image_data)
            self.set_image(image_data)
        else:
            self.resize(600, 600)

        if isinstance(wvl, np.ndarray) and isinstance(cube_data, np.ndarray):
            self.set_cube(wvl, cube_data)

        if isinstance(image_data, str):
            arr, _ = open_cube(image_data)
            self.set_image(arr)

        if isinstance(wvl, str) and isinstance(cube_data, str):
            arr, _ = open_cube(cube_data)
            wvl_arr = open_wvl(wvl)
            self.set_cube(wvl_arr, arr)

    def load_image(self) -> None:
        fp = askopenfilename(
            title="Select Image Data",
            filetypes=[
                ("Spectral Cube Files", [".spcub", ".geospcub"]),
                ("Rasterio-Compatible Files", [".bsq", ".img", ".tif"]),
            ],
        )
        arr, _ = open_cube(fp)
        self.set_image(arr)

    def load_cube(self) -> None:
        cube_fp = askopenfilename(
            title="Select Cube Data",
            filetypes=[
                ("Spectral Cube Files", [".spcub", ".geospcub"]),
                ("Rasterio-Compatible Files", [".bsq", ".img", ".tif"]),
            ],
        )
        arr, suff = open_cube(cube_fp)
        if suff == ".spcub":
            wvl = sio.read_spec3D(cube_fp, kind="spcub").wavelength.asarray()
        elif suff == ".geospcub":
            wvl = sio.read_spec3D(
                cube_fp, kind="geospcub"
            ).wavelength.asarray()
        else:
            wvl_fp = askopenfilename(
                title="Select Wavelength (or other context) Data",
                filetypes=[
                    ("Wavelength File", [".wvl"]),
                    ("ENVI Header File", [".hdr"]),
                    ("Text-Based Files", [".txt", ".csv"]),
                ],
            )
            wvl = open_wvl(wvl_fp)

        self.set_cube(wvl, arr)

    def set_image(self, data: np.ndarray) -> None:
        self.img_picker.set_image(data)
        self.set_window_size(data)

    def set_cube(self, wvl: np.ndarray, data: np.ndarray) -> None:
        self.spectral_display.set_cube(wvl, data)
        self.aux_spec_display.display_widget.set_cube(wvl, data)

    def empty_cache(self) -> None:
        for plot, err in self.state.spectrum_cache.values():
            self.spectral_display.spec_plot.removeItem(plot)
            self.spectral_display.spec_plot.removeItem(err)
            self.spectral_display.spec_legend.removeItem(plot)
        for poly in self.polygon_cache.values():
            if poly is None:
                continue
            self.img_picker.imview.getView().removeItem(poly)
        self.spectral_display.plot_reset.emit()
