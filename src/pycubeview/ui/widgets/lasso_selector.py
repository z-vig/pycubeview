# Built-Ins
import math

# Dependencies
import pyqtgraph as pg  # type: ignore
import numpy as np
from shapely.geometry import Polygon, Point
from alphashape import alphashape  # type: ignore

# Local Imports
from .image_display import ImageDisplay
from pycubeview.data_transfer_classes import ImageClickData, LassoData

# PySide6 Imports
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal, QPointF


class LassoSelector(QWidget):
    lasso_started = Signal()
    lasso_finished = Signal(LassoData)

    def __init__(self, img_display: ImageDisplay):
        self.imdisp = img_display
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
        super().__init__()

    def start_lasso(self, click_data: ImageClickData):
        if not self._drawing:
            print("Starting Lasso...")
            pos = [[click_data.x_exact, click_data.y_exact]]
            self._drawing = True
            self.lasso.clearPoints()
            self.lasso.setPoints(pos)
            self.lasso.setVisible(True)
            self.lasso_started.emit()

    def lasso_movement(self, pos: QPointF) -> None:
        if not self._drawing:
            return
        data_coords = self.imdisp._vbox.mapSceneToView(pos)
        pts = self.lasso.getState()["points"]
        pts.append([data_coords.x(), data_coords.y()])
        self.lasso.setPoints(pts)
        if len(self.lasso.handles) % 50 == 0:
            print(self.lasso.handles[-1]["pos"])
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
