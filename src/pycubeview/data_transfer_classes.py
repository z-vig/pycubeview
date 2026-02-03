# Built-Ins
from uuid import UUID
from dataclasses import dataclass, field, replace
from typing import Literal, Optional

# Dependencies
import cmap
import pyqtgraph as pg  # type: ignore
import numpy as np

# PySide6 Imports
from PySide6.QtCore import Qt


@dataclass
class PixelValue:
    v: float = 0.0
    r: float = 0.0
    g: float = 0.0
    b: float = 0.0
    pixel_type: Literal["single", "rgb"] = "single"

    @classmethod
    def null(cls) -> "PixelValue":
        return cls(-999.0, -999.0, -999.0, -999.0)


@dataclass
class CursorTracker:
    x_exact: float
    y_exact: float
    x_int: int
    y_int: int
    value: PixelValue = field(default_factory=PixelValue.null)


@dataclass
class ImageClickData:
    x_exact: float
    y_exact: float
    x_int: int
    y_int: int
    button: Qt.MouseButton
    modifiers: Qt.KeyboardModifier


@dataclass
class ImageScatterPoint:
    x: int
    y: int
    color: cmap.Color
    scatter_plot_item: pg.ScatterPlotItem
    id: UUID


@dataclass(eq=True, frozen=True)
class Measurement:
    """
    Holds all information about a measurement. If there measurement is of a
    single point, `plot_data_errorbars`, `x_pixels` and `y_pixels` will be
    None. If the measurement is of multiple points, pixel_x and pixel_y will
    represent the centroid of the measurement.

    Attributes
    ----------
    name: str
        The name of the measurement.
    type: str
        Type of measurement. Either Point or Group.
    color: cmap.Color
        The color assigned to the measurement.
    pixel_x: int
        The x coordinate of the measurement in pixel space or the centroid x.
    pixel_y: int
        The y coordinate of the measurement in pixel space or the centroid y.
    yvalues: np.ndarray
        The values of the measurement, or the mean of a group.
    xvalues: np.ndarray
        Measurement label values.
    plot_data_item: pg.PlotDataItem
        The plot item containing the measurement data.
    plot_data_errorbars: Optional[pg.ErrorBarItem]
        The error bar item for the measurement. None if single point.
    x_pixels: Optional[np.ndarray]
        The x coordinates of all pixels in the measurement. None if single
        point.
    y_pixels: Optional[np.ndarray]
        The y coordinates of all pixels in the measurement. None if single
        point.
    vertices: Optional[np.ndarray]
        2-column array where the first column is the x values and the second
        is the y values of all the vertices enclosed by the Group.
    id: UUID
        A unique identifier for the measurement.
    """

    id: UUID
    name: str
    type: Literal["Group", "Point"]
    color: cmap.Color
    pixel_x: int
    pixel_y: int
    yvalues: np.ndarray
    xvalues: np.ndarray
    plot_data_item: pg.PlotDataItem
    plot_data_errorbars: Optional[pg.ErrorBarItem] = None
    x_pixels: Optional[np.ndarray] = None
    y_pixels: Optional[np.ndarray] = None

    def change_name(self, name: str) -> "Measurement":
        new_plot_data_item = pg.PlotDataItem(
            x=self.xvalues,
            y=self.yvalues,
            pen=pg.mkPen(color=self.color.hex),
            clickable=True,
            name=name,
        )
        return replace(self, name=name, plot_data_item=new_plot_data_item)


@dataclass
class LassoData:
    """
    Contains data from the lasso selection.

    Attributes
    ----------
    vertices: np.ndarray
        A 2D array with 2 columns. The first is the x coordinates and the
        second is the y coordinates of the vertices of the lasso.
    lasso_pixels: np.ndarray
        2D array with 2 columns. The first is all of the x coordinates and the
        second is all of the y coordinates of the pixels within the lasso.
    lasso_mask: np.ndarray
        2D array with pixel dimensions where all True values are in the lasso.
    """

    id: UUID
    vertices: np.ndarray
    lasso_pixels: np.ndarray
    lasso_mask: np.ndarray
