# Built-Ins
from uuid import UUID, uuid4
from dataclasses import dataclass, field

# Dependencies
import cmap
import pyqtgraph as pg  # type: ignore


# PySide6 Imports
from PySide6.QtCore import Qt


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


@dataclass(eq=True, frozen=True)
class Measurement:
    pixel_x: int
    pixel_y: int
    name: str
    plot_data_item: pg.PlotDataItem
    color: cmap.Color
    id: UUID = field(default_factory=uuid4)
