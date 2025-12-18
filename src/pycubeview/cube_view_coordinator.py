from __future__ import annotations

"""
Coordinator Class for CubeViewWindow, which seperates UI event handling from
the main window class, help with testability and reusability.
"""

# Dependencies
from PySide6.QtGui import QColor, QPolygonF, QBrush
from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QGraphicsPolygonItem
import pyqtgraph as pg  # type: ignore
import numpy as np

# Type-Checking Help
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .cube_view_window import CubeViewWindow


class CubeViewCoordinator:
    """
    Coordinates signals and state between CubeViewWindow components.
    """

    def __init__(self, window: CubeViewWindow):
        self.window = window

    # -------------------------------------------------
    # Helper methods: color management & cache helpers
    # -------------------------------------------------
    def _next_qual_color(self) -> QColor:
        """Return next qualitative QColor and advance the cycle.

        Raises
        ------
        UserWarning
            When the qualitative colormap has been exhausted (wrap-around).
        """
        pos = self.window.state.color_cycle_pos
        c = self.window.qcmap(pos).rgba8
        qcol = QColor(c.r, c.g, c.b, int(c.a * 255))
        # advance
        pos += 1
        if pos == self.window.n_qcolors:
            # wrap and warn
            self.window.state.color_cycle_pos = 0
            raise UserWarning(
                "Number of spectra have exceeded the length of the "
                "qualitative colormap. Consider saving and clearing "
                "spectra before continuing."
            )
        self.window.state.color_cycle_pos = pos
        return qcol

    def _cache_spectrum_set(
        self, name: str, plot: pg.PlotDataItem, err: pg.ErrorBarItem
    ) -> None:
        """Set spectrum cache entry and refresh UI hints."""
        self.window.state.spectrum_cache[name] = (plot, err)
        self._update_cache_status()

    def _cache_spectrum_remove(self, name: str) -> None:
        """Remove spectrum cache entry and refresh UI hints."""
        if name in self.window.state.spectrum_cache:
            del self.window.state.spectrum_cache[name]
        self._update_cache_status()

    def _update_cache_status(self) -> None:
        """Update menu/tooltips reflecting current spectrum cache size."""
        n_cached = len(self.window.state.spectrum_cache)
        self.window.clear_spectra.setStatusTip(
            f"Clear {n_cached} spectra from memory."
        )
        self.window.save_spectra.setStatusTip(
            f"Save {n_cached} spectra currently in memory."
        )

    def on_pixel_picked(self, y: int, x: int):
        """
        Handle single pixel selection from image picker.

        Adds the spectrum at the selected pixel to the spectral display
        with the next available color from the qualitative colormap.
        Cycles through colors and warns when the colormap is exhausted.

        Parameters
        ----------
        y : int
            Row index of selected pixel.
        x : int
            Column index of selected pixel.
        """
        # Request next qualitative color (also advances cycle)
        next_color: QColor = self._next_qual_color()
        # Add the spectrum to the display and get the saved spectrum object
        spectrum_save = self.window.spectral_display.add_spectrum(
            (y, x), color=next_color
        )
        # Initialize polygon cache entry as None (single pixel, no polygon)
        self.window.polygon_cache[spectrum_save.name] = None

    def on_roi_finished(self, in_coords: np.ndarray, verts: np.ndarray):
        """
        Handle lasso/polygon ROI selection from image picker.

        Creates a colored polygon overlay on the image and adds the mean
        spectrum of all pixels within the ROI to the spectral display.

        Parameters
        ----------
        in_coords : np.ndarray
            Array of (y, x) coordinates of pixels within the ROI.
        verts : np.ndarray
            Array of (y, x) vertices defining the polygon boundary.
            Shape: (n_vertices, 2)
        """
        # Get next color from qualitative colormap for this ROI
        next_color: QColor = self._next_qual_color()
        # Add group (mean spectrum) to spectral display
        group_save = self.window.spectral_display.add_group(
            in_coords, single_color=next_color
        )
        # Create polygon graphics item from ROI vertices
        pts = [QPointF(*verts[n, :]) for n in range(verts.shape[0])]
        poly = QPolygonF(pts)
        poly_item = QGraphicsPolygonItem(poly)
        # Set polygon styling: black outline with semi-transparent fill
        poly_item.setPen(pg.mkPen("k", width=2))
        next_color.setAlphaF(0.4)
        poly_item.setBrush(QBrush(next_color))

        # Cache the polygon item for later removal if needed
        self.window.polygon_cache[group_save.name] = poly_item

        # Add polygon to the image view
        self.window.img_picker.imview.getView().addItem(poly_item)

    def cache_spectrum(
        self, plot: pg.PlotDataItem, err: pg.ErrorBarItem
    ) -> None:
        """
        Cache newly added spectrum for later operations.

        When a new spectrum is added to the display, this function caches
        it and updates status bar information about the number of spectra
        in memory.

        Parameters
        ----------
        plot : pg.PlotDataItem
            The spectral plot item that was added.
        err : pg.ErrorBarItem
            The error bar item associated with the plot.
        """
        name = plot.name()
        if name is None:
            return
        # Delegate to helper that also updates UI hints
        self._cache_spectrum_set(name, plot, err)

    def update_cache(
        self,
        plot: pg.PlotDataItem,
        err: pg.ErrorBarItem,
        old_name: str,
        new_name: str,
    ):
        """
        Update cached spectrum when its name changes.

        Handles renaming of cached spectra, updating both the spectrum
        cache and the associated polygon cache to maintain consistency.

        Parameters
        ----------
        plot : pg.PlotDataItem
            The spectral plot item being renamed.
        err : pg.ErrorBarItem
            The error bar item associated with the plot.
        old_name : str
            Previous name of the spectrum.
        new_name : str
            New name for the spectrum.
        """
        # Update spectrum cache with new name (reuse helpers)
        if old_name in self.window.state.spectrum_cache:
            del self.window.state.spectrum_cache[old_name]
        self._cache_spectrum_set(new_name, plot, err)
        # Maintain polygon cache entry under new name
        self.window.polygon_cache[new_name] = self.window.polygon_cache.pop(
            old_name
        )
        # Update saved spectra to use new name
        for spec in self.window.spectral_display.save_cache:
            if spec.name == old_name:
                spec.name = new_name

    def remove_spectrum(self, name: str):
        """
        Remove a spectrum and its associated polygon from all displays.

        Handles cleanup when a spectrum is deleted from the spectral
        display, including removal of the associated polygon overlay from
        the image.

        Parameters
        ----------
        name : str
            Name/identifier of the spectrum to remove.
        """
        # Remove the polygon overlay from the image view if it exists
        poly = self.window.polygon_cache.get(name)
        if poly is not None:
            self.window.img_picker.imview.getView().removeItem(poly)

        # Remove from caches using helper
        if name in self.window.polygon_cache:
            del self.window.polygon_cache[name]
        self._cache_spectrum_remove(name)

    def open_aux_window(self):
        """Show the auxiliary spectral display window."""
        self.window.aux_spec_display.show()

    def intercept_line_roi(self, coords: np.ndarray):
        """
        Handle line ROI updates from the image picker.

        When the user adjusts a line ROI, this function extracts spectra
        from all pixels along the line, displays them in the auxiliary
        window, and creates a scatter plot overlay on the image showing
        the ROI positions.

        Parameters
        ----------
        coords : np.ndarray
            Array of (y, x) coordinates along the line ROI.
            Shape: (n_pixels, 2)
        """
        # Clear previous line ROI spectra from auxiliary display
        for i in self.window.state.line_roi_cache:
            self.window.aux_spec_display.display_widget.spec_plot.removeItem(i)
        # Add new spectra from line ROI pixels
        self.window.aux_spec_display.display_widget.add_group(
            coords, display_mean=False, cache_all=True
        )
        # Create a color gradient for the scatter plot points
        brush_list = []
        ncolors = coords.shape[0]
        # Use sequential colormap to create gradient from line start to end
        cmap_lut = self.window.scmap.lut(ncolors) * 255
        for i in range(ncolors):
            c = pg.mkColor(tuple(cmap_lut[i, :]))
            brush_list.append(pg.mkBrush(color=c))
        # Create scatter plot with gradient colors
        # Add 0.5 offset to center points on pixels
        scatter_plot = pg.ScatterPlotItem(
            pos=coords + 0.5, brush=brush_list, pen=pg.mkPen((0, 0, 0, 0))
        )
        # Remove old scatter plot if it exists
        if self.window.state.line_roi_scatter_plot.getData()[0].size > 0:
            self.window.img_picker.imview.getView().removeItem(
                self.window.state.line_roi_scatter_plot
            )
        # Add new scatter plot to image view
        self.window.img_picker.imview.getView().addItem(scatter_plot)
        self.window.state.line_roi_scatter_plot = scatter_plot

    def cache_line_roi(self, plot_list: list[pg.PlotDataItem]):
        """
        Cache the line ROI spectral plots for later retrieval.

        Parameters
        ----------
        plot_list : list[pg.PlotDataItem]
            List of spectral plot items extracted from the line ROI.
        """
        self.window.state.line_roi_cache = plot_list

    def close_aux_window(self):
        """
        Clean up when the auxiliary spectral window is closed.

        Removes all line ROI visualizations from the image and auxiliary
        display.
        """
        # Remove scatter plot from image view
        self.window.img_picker.imview.getView().removeItem(
            self.window.state.line_roi_scatter_plot
        )
        # Reset scatter plot to empty item
        self.window.state.line_roi_scatter_plot = pg.ScatterPlotItem()
        # Remove spectral plots from auxiliary window
        for i in self.window.state.line_roi_cache:
            self.window.aux_spec_display.display_widget.spec_plot.removeItem(i)
        # Reset the line ROI tool in the image picker
        self.window.img_picker.close_line_roi()

    def update_base_dir(self):
        """
        Update the base directory across all widgets when it changes.

        Propagates base directory changes to the spectral display and
        auxiliary display, and updates the menu tooltip.
        """
        # Update base directory for file dialogs in spectral displays
        self.window.spectral_display.base_data_dir = (
            self.window.state.base_data_dir
        )
        self.window.aux_spec_display.display_widget.base_data_dir = (
            self.window.state.base_data_dir
        )
        # Update menu tooltip to show current directory
        self.window.set_data_directory.setStatusTip(
            "Sets the base directory for all data open and save menus."
            f" Current: {self.window.state.base_data_dir}"
        )
