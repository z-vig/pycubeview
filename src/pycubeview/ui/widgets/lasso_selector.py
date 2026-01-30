# Built-Ins
import math
from dataclasses import dataclass

# Dependencies
import pyqtgraph as pg  # type: ignore
from pyqtgraph.GraphicsScene.mouseEvents import MouseClickEvent  # type: ignore
import numpy as np
from shapely.geometry import Polygon, Point
from alphashape import alphashape  # type: ignore

# Local Imports
from .image_display import ImageDisplay

# PySide6 Imports
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Qt, Signal, QPointF


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

    vertices: np.ndarray
    lasso_pixels: np.ndarray
    lasso_mask: np.ndarray


class LassoSelector(QWidget):
    lasso_finished = Signal(LassoData)

    def __init__(self, parent: ImageDisplay):
        self.imdisp = parent
        self._drawing: bool = False
        self.lasso = pg.PolyLineROI(
            [[0, 0]],
            closed=True,
            pen=pg.mkPen("r", width=2),
            movable=False,
            removable=False,
        )
        self.imdisp.pg_image_view.getView().addItem(self.lasso)
        self.lasso.setVisible(False)
        super().__init__(parent)

    def on_roi_click(self, mouse_event: MouseClickEvent):
        mods = QApplication.keyboardModifiers()
        pos = mouse_event.scenePos()
        view_pos = self.imdisp.pg_image_view.getView().mapSceneToView(pos)
        if mods == Qt.KeyboardModifier.ControlModifier:
            print("ROI CLICK")
            if not self._drawing:
                self.start_lasso([[view_pos.x(), view_pos.y()]])
            else:
                if mouse_event.double():
                    self.finish_lasso()

    def start_lasso(self, pos):
        self._drawing = True
        self.lasso.clearPoints()
        self.lasso.setPoints(pos)
        self.lasso.setVisible(True)

    def lasso_movement(self, pos: QPointF):
        if not self._drawing:
            return
        view_pos = self.imdisp.pg_image_view.getView().mapSceneToView(pos)
        pts = self.lasso.getState()["points"]
        pts.append([view_pos.x(), view_pos.y()])
        self.lasso.setPoints(pts)
        for h in self.lasso.handles:
            h["item"].setVisible(False)

    def finish_lasso(self) -> None:
        self._drawing = False
        point_list = self.lasso.getState()["points"]
        self.lasso.setVisible(False)
        vertices = np.empty((len(point_list), 2))
        for n, pt in enumerate(point_list):
            vertices[n, :] = (pt.x(), pt.y())
        poly = Polygon(vertices)
        x_pts = np.asarray([i[0] for i in vertices])
        y_pts = np.asarray([i[1] for i in vertices])
        x_slice = slice(x_pts.min(), x_pts.max())
        y_slice = slice(y_pts.min(), y_pts.max())

        x_sample, y_sample = np.mgrid[x_slice, y_slice]
        pt_list = [
            (i, j) for i, j in zip(x_sample.flatten(), y_sample.flatten())
        ]
        in_x = []
        in_y = []
        for i in pt_list:
            if poly.contains(Point(i)):
                in_x.append(math.floor(i[0]))
                in_y.append(math.floor(i[1]))
        in_x_arr = np.asarray(in_x).astype(int)
        in_y_arr = np.asarray(in_y).astype(int)
        in_array = np.stack([in_x_arr, in_y_arr], axis=1)
        in_pts: list[tuple[float, float]] = [
            (i, j) for i, j in zip(in_x, in_y)
        ]

        new_poly = alphashape(points=in_pts, alpha=0.9)  # type: ignore
        x_verts = np.asarray(new_poly.exterior.xy[0])  # type: ignore
        y_verts = np.asarray(new_poly.exterior.xy[1])  # type: ignore
        xy_verts = np.concatenate([x_verts[:, None], y_verts[:, None]], axis=1)

        lasso_mask = np.zeros(self.imdisp.image_size, dtype=bool)
        lasso_mask[in_y_arr, in_x_arr] = True

        data = LassoData(
            vertices=xy_verts, lasso_pixels=in_array, lasso_mask=lasso_mask
        )

        self.lasso_finished.emit(data)
