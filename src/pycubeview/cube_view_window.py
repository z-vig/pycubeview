"""
Main window module for CubeView application.

This module provides the primary UI framework for visualizing and interacting
with hyperspectral image cubes, managing spectral data display, and
coordinating user interactions across multiple display windows.
"""

# Built-Ins
from typing import Optional
from pathlib import Path

# PySide6 Imports
from PySide6 import QtWidgets as qtw

# Dependencies
from pyqtgraph.dockarea import Dock, DockArea  # type: ignore
import numpy as np
import spectralio as sio
import cmap

# Local Imports
from .cube_view_coordinator import CubeViewCoordinator
from .base_window import BaseWindow
from .image_display_widget import ImagePickerWidget
from .spectral_display_widget import SpectralDisplayWidget
from .line_roi_window import LineRoiWindow
from .file_opening_utils import open_cube, open_wvl
from .util_classes import PixelValue
from .valid_colormaps import QualitativeColorMap, SequentialColorMap


class CubeViewWindow(BaseWindow):
    """
    Main application window for cube visualization and analysis.

    This window provides an integrated interface for viewing cube-like image
    data, selecting pixels/regions of interest (ROIs) via the image picker,
    and displaying corresponding dimensional information. It coordinates
    interactions between the image display, spectral display, and auxiliary
    spectral viewing windows through a comprehensive signal/slot system.

    Parameters
    ----------
    wvl : Optional[np.ndarray | str], default=None
        Wavelength array or path to wavelength file. If None, no wavelength
        data is loaded initially.
    image_data : Optional[np.ndarray | str], default=None
        Image data (single band or RGB) as numpy array or path to image file.
        If None, no image is loaded initially.
    cube_data : Optional[np.ndarray | str], default=None
        Hyperspectral cube data (3D array) or path to cube file.
        If None, no cube data is loaded initially.
    base_dir : Optional[str], default=None
        Base directory for file dialogs. Used as the default location when
        opening or saving files.
    qual_color_map : QualitativeColorMap, default="colorbrewer:Dark2"
        Colormap for distinguishing multiple spectra/ROIs. Should have
        sufficient colors for expected number of simultaneous spectra.
    sequential_color_map : SequentialColorMap, default="crameri:hawaii"
        Colormap for line ROI display gradients and continuous data
        visualization.

    Attributes
    ----------
    qcmap : cmap.Colormap
        Qualitative colormap instance for spectrum differentiation.
    n_qcolors : int
        Number of colors available in the qualitative colormap.
    scmap : cmap.Colormap
        Sequential colormap instance for gradient displays.
    polygon_cache : dict[str, qtw.QGraphicsPolygonItem | None]
        Stores polygon graphics items for lasso-drawn ROIs, keyed by spectrum
        name.
    img_picker : ImagePickerWidget
        Widget for image display and pixel/ROI selection.
    imview_dock : Dock
        Docking widget containing the image viewer.
    spectral_display : SpectralDisplayWidget
        Widget for displaying spectral data of selected pixels.
    spec_dock : Dock
        Docking widget containing the spectral display.
    aux_spec_display : LineRoiWindow
        Auxiliary window for viewing spectral data extracted along line ROIs.
    """

    def __init__(
        self,
        wvl: Optional[np.ndarray | str] = None,
        image_data: Optional[np.ndarray | str] = None,
        cube_data: Optional[np.ndarray | str] = None,
        base_dir: Optional[str] = None,
        qual_color_map: QualitativeColorMap = "colorbrewer:Dark2",
        sequential_color_map: SequentialColorMap = "crameri:hawaii",
    ) -> None:
        """
        Initialize the CubeViewWindow with optional data and configuration.

        Parameters
        ----------
        wvl : Optional[np.ndarray | str], default=None
            Wavelength array or path to wavelength file.
        image_data : Optional[np.ndarray | str], default=None
            Image data (2D array) or path to image file.
        cube_data : Optional[np.ndarray | str], default=None
            Cube data (3D array) or path to cube file.
        base_dir : Optional[str], default=None
            Base directory for file operations.
        qual_color_map : QualitativeColorMap, default="colorbrewer:Dark2"
            Named colormap for spectrum differentiation.
        sequential_color_map : SequentialColorMap, default="crameri:hawaii"
            Named colormap for line ROI gradients.
        """
        super().__init__()

        # ---- Initialize colormaps ----
        # Qualitative colormap for distinguishing multiple spectra
        self.qcmap = cmap.Colormap(qual_color_map)
        self.n_qcolors = len(self.qcmap.color_stops)
        # Sequential colormap for gradient visualizations (e.g., line ROIs)
        self.scmap = cmap.Colormap(sequential_color_map)

        # Cache for polygon graphics items associated with lasso-drawn ROIs.
        # Maps spectrum/group name -> QGraphicsPolygonItem (or None for point
        # selections)
        self.polygon_cache: dict[str, qtw.QGraphicsPolygonItem | None] = {}

        # ---- Set up dock area layout ----
        dock_area = DockArea()
        self.setCentralWidget(dock_area)

        # ---- Image Display Dock ----
        # Top dock area for the image viewer and pixel/ROI selection tools
        self.imview_dock = Dock(name="Image Window")
        dock_area.addDock(self.imview_dock, "top")

        self.img_picker = ImagePickerWidget()
        self.imview_dock.addWidget(self.img_picker)

        # ---- Spectral Display Dock ----
        # Bottom dock area for displaying spectral data of selected pixels
        self.spec_dock = Dock(name="Spectral Display Window")
        dock_area.addDock(self.spec_dock, "bottom")

        self.spectral_display = SpectralDisplayWidget()
        self.spec_dock.addWidget(self.spectral_display)

        # ---- Connect menu actions ----
        # Wire up the menu bar actions to their corresponding handler slots
        self.open_display.triggered.connect(self.load_image)
        self.open_cube.triggered.connect(self.load_cube)
        self.clear_spectra.triggered.connect(self.empty_cache)
        self.save_spectra.triggered.connect(self.spectral_display.save_plot)
        self.link_geodata_action.triggered.connect(self.link_geodata)
        self.show_errorbars.toggled.connect(
            self.spectral_display.toggle_errorbars
        )

        # ---- Auxiliary Spectral Window ----
        # Separate window for viewing spectra extracted along line ROIs
        self.aux_spec_display = LineRoiWindow()
        self.aux_spec_display.setWindowTitle("Line ROI Spectral Display")

        # ---- Connecting Signals from Coordinator ----
        self.coord = CubeViewCoordinator(self)

        # ---- Connect Image Picker signals ----
        # Pixel selection, ROI drawing, and line ROI interactions
        self.img_picker.pixel_picked.connect(self.coord.on_pixel_picked)
        self.img_picker.lasso_finished.connect(self.coord.on_roi_finished)
        self.img_picker.line_roi_started.connect(self.coord.open_aux_window)
        self.img_picker.line_roi_updated.connect(self.coord.intercept_line_roi)

        # ---- Connect Spectral Display signals ----
        # Spectrum caching and cache management
        self.spectral_display.data_added.connect(self.coord.cache_spectrum)
        self.spectral_display.data_updated.connect(self.coord.update_cache)
        self.spectral_display.data_removed.connect(self.coord.remove_spectrum)

        # ---- Connect Auxiliary Spectral Display signals ----
        # Coordination between line ROI window and main image
        self.aux_spec_display.updated.connect(self.img_picker.update_line_roi)
        self.aux_spec_display.closed.connect(self.coord.close_aux_window)
        self.aux_spec_display.display_widget.bulk_data_added.connect(
            self.coord.cache_line_roi
        )

        # ---- Connect Base Window signals ----
        # Base directory updates
        self.base_data_dir_updated.connect(self.coord.update_base_dir)
        if base_dir is not None:
            self.state.base_data_dir = Path(base_dir)
            self.base_data_dir_updated.emit()

        # ---- Connect Status Bar updates ----
        def cursor_message(x: float, y: float, val: PixelValue) -> None:
            """
            Update status bar with current cursor position and pixel value.

            Parameters
            ----------
            x : float
                X coordinate in image space.
            y : float
                Y coordinate in image space.
            val : PixelValue
                The value(s) at the cursor location (single value or RGB).
            """
            # Special values (-999) indicate cursor left the image
            if x == -999 and y == -999 and val == -999:
                self.status_bar.clearMessage()
                return
            # Format message based on pixel type (single band or RGB)
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

        # ---- Load initial data if provided ----
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
        """
        Load an image file via file dialog and display it.

        Presents a file dialog for the user to select an image file, then loads
        and displays it using the set_image method.

        Notes
        -----
        Supports spectral cube files (.spcub, .geospcub) and rasterio-
        compatible formats (.bsq, .img, .tif).
        """
        fp_str, fp_type = qtw.QFileDialog.getOpenFileName(
            caption="Select Image Data",
            filter=(
                "Spectral Cube Files (*.spcub *.geospcub);;"
                "Rasterio-Compatible Files (*.bsq *.img *.tif)"
            ),
            dir=str(self.state.base_data_dir),
        )
        # User cancelled the dialog
        if fp_str == "":
            return
        fp = Path(fp_str)
        arr, _ = open_cube(fp)
        self.set_image(arr)

    def load_cube(self) -> None:
        """
        Load a hyperspectral cube and its associated wavelength data.

        Presents file dialogs for the user to select cube and wavelength data.
        For cube files with embedded wavelength data (.spcub, .geospcub), the
        wavelength is extracted automatically. For other formats, the user is
        prompted to select a separate wavelength file.

        Notes
        -----
        Supports:
        - .spcub and .geospcub files (with built-in wavelength)
        - Rasterio-compatible formats (.bsq, .img, .tif) requiring separate
        wavelength
        - Wavelength files: .wvl, .hdr (ENVI headers), .txt, .csv
        """
        cube_fp_str, fp_type = qtw.QFileDialog.getOpenFileName(
            caption="Select Cube Data",
            filter=(
                "Spectral Cube Files (*.spcub *.geospcub);;"
                "Rasterio-Compatible Files (*.bsq *.img *.tif)"
            ),
            dir=str(self.state.base_data_dir),
        )
        # User cancelled the dialog
        if cube_fp_str == "":
            return
        cube_fp = Path(cube_fp_str)
        arr, suff = open_cube(cube_fp)

        # Extract wavelength based on file format
        if suff == ".spcub":
            wvl = sio.read_spec3D(cube_fp, kind="spcub").wavelength.asarray()
        elif suff == ".geospcub":
            wvl = sio.read_spec3D(
                cube_fp, kind="geospcub"
            ).wavelength.asarray()
        else:
            # For other formats, prompt user to select wavelength file
            wvl_fp_str, fp_type = qtw.QFileDialog.getOpenFileName(
                caption="Select Wavelength (or other context) Data",
                filter=(
                    "Wavelength File (*.wvl);;ENVI Header File (*.hdr);;"
                    "Text-Based Files (*.txt *.csv)"
                ),
                dir=str(self.state.base_data_dir),
            )
            wvl_fp = Path(wvl_fp_str)
            wvl = open_wvl(wvl_fp)

        self.set_cube(wvl, arr)

    def set_image(self, data: np.ndarray) -> None:
        """
        Set and display the image data in the image picker widget.

        Updates both the image display and the window size based on image
        dimensions.

        Parameters
        ----------
        data : np.ndarray
            The image data to display. Can be 2D (grayscale) or 3D
            (RGB/multi-band).
        """
        self.img_picker.set_image(data)
        self.set_window_size(data)

    def set_cube(self, wvl: np.ndarray, data: np.ndarray) -> None:
        """
        Set hyperspectral cube data and enable spectral analysis.

        Propagates the cube data to all spectral display widgets and marks the
        cube as attached in the application state.

        Parameters
        ----------
        wvl : np.ndarray
            Wavelength array for the spectral dimension. Length should match
            the spectral axis of the cube data.
        data : np.ndarray
            3D hyperspectral cube data with shape (height, width, n_bands).
        """
        self.spectral_display.set_cube(wvl, data)
        self.aux_spec_display.display_widget.set_cube(wvl, data)
        self.state.cube_attached = True
        self.cube_indicator.toggle()

    def empty_cache(self) -> None:
        """
        Clear all cached spectra from memory and remove them from all displays.

        Removes all spectral plots, error bars, and polygon overlays. Resets
        the color cycle counter and the polygon cache. This does not affect
        saved data.
        """
        # Remove each cached spectrum and its error bars from the spectral
        # display
        for plot, err in self.state.spectrum_cache.values():
            self.spectral_display.spec_plot.removeItem(plot)
            self.spectral_display.spec_plot.removeItem(err)
            self.spectral_display.spec_legend.removeItem(plot)
        # Remove polygon overlays from the image display
        for poly in self.polygon_cache.values():
            if poly is None:
                continue
            self.img_picker.imview.getView().removeItem(poly)
        # Emit signal to reset plot (e.g., clear axis scaling)
        self.spectral_display.plot_reset.emit()
        # Reset all caches and state
        self.polygon_cache = {}
        self.state.spectrum_cache = {}
        self.state.color_cycle_pos = 0

    def link_geodata(self) -> None:
        """
        Link geolocation data from a file for spatial reference.

        Presents a file dialog for the user to select a geodata file, then
        links it to the spectral display for spatial context. Updates the UI
        to indicate that geodata is attached.

        Notes
        -----
        Geodata files must have the .geodata extension.
        """
        geodata_fp_str, fp_type = qtw.QFileDialog.getOpenFileName(
            caption="Select Geodata File",
            filter="Geodata File (*.geodata)",
            dir=str(self.state.base_data_dir),
        )
        # User cancelled the dialog
        if geodata_fp_str == "":
            return
        geodata_fp = Path(geodata_fp_str)
        # Update menu tooltip to show current geodata source
        self.link_geodata_action.setStatusTip(
            "Link Geolocation Data from a file. (Currently linked "
            f"from {geodata_fp})"
        )
        # Link geodata in the spectral display
        self.spectral_display.link_geodata(Path(geodata_fp))
        # Update state and UI indicator
        self.state.geodata_attached = True
        self.geo_indicator.toggle()
