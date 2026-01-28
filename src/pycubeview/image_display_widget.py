# Built-Ins
from pathlib import Path

# PySide6 Imports
from PySide6.QtWidgets import QWidget, QVBoxLayout, QApplication
from PySide6.QtGui import QAction
from PySide6.QtCore import Signal, Qt, QPointF

# Dependencies
import pyqtgraph as pg  # type: ignore
from pyqtgraph.GraphicsScene.mouseEvents import MouseClickEvent  # type: ignore
import numpy as np
from shapely.geometry import Polygon, Point
from alphashape import alphashape  # type: ignore
import math
import cmap

# Local Imports
from .valid_colormaps import SequentialColorMap
from .util_classes import PixelValue
from .utils import get_bresenham_line


class ImagePickerWidget(QWidget):
    mouse_moved = Signal(float, float, PixelValue)
    pixel_picked = Signal(int, int)
    lasso_finished = Signal(np.ndarray, np.ndarray)
    line_roi_started = Signal()
    line_roi_updated = Signal(np.ndarray)

    def __init__(
        self,
        image_cmap: SequentialColorMap = "matlab:gray",
        line_roi_cmap: SequentialColorMap = "crameri:hawaii",
    ):
        super().__init__()

        self.imcmap = cmap.Colormap(image_cmap)
        self.lrcmap = cmap.Colormap(line_roi_cmap)
        self.base_data_dir: Path = Path.cwd()

        self.imview = pg.ImageView()
        self.imview.scene.sigMouseClicked.connect(  # type: ignore
            self.pixel_select
        )
        self.imview.scene.sigMouseClicked.connect(  # type: ignore
            self.roi_click_handler
        )
        self.imview.scene.sigMouseMoved.connect(  # type: ignore
            self.lasso_movement
        )
        self.imview.scene.sigMouseMoved.connect(  # type: ignore
            self.track_cursor
        )
        self._drawing = False

        # ---- Adding blank ROI objects ----
        self.lasso = pg.PolyLineROI(
            [[0, 0]],
            closed=True,
            pen=pg.mkPen("r", width=2),
            movable=False,
            removable=False,
        )
        self.imview.getView().addItem(self.lasso)
        self.lasso.setVisible(False)

        self.line_roi = pg.LineSegmentROI(
            positions=[[0, 0], [0, 0]],
            pen=pg.mkPen("r", width=2),
            movable=True,
            removable=False,
        )
        handle_colors = [
            self.lrcmap.to_pyqtgraph()[0],
            self.lrcmap.to_pyqtgraph()[-1],
        ]
        for i, j in zip(self.line_roi.getHandles(), handle_colors):
            i.pen = pg.mkPen(color=j, width=4)
            i.update()

        self.imview.getView().addItem(self.line_roi)
        self.line_roi.setVisible(False)

        # ---- Adding to Context Menu ----
        context_menu = self.imview.getView().menu
        if context_menu is not None:
            self.open_spectral_display_action = QAction(
                "Connect New Spectral Display", self
            )
            context_menu.addAction(self.open_spectral_display_action)

        layout = QVBoxLayout()
        layout.addWidget(self.imview)
        self.setLayout(layout)

    def set_image(self, data: np.ndarray) -> None:
        # Setting imview image
        if data.ndim == 3:
            if data.shape[-1] == 3:
                _ax_interp = {"y": 0, "x": 1, "c": 2}
                self.imview.setImage(data, axes=_ax_interp, levelMode="rgba")
            elif data.shape[-1] > 3:
                _ax_interp = {"y": 0, "x": 1, "t": 2}
                self.imview.setImage(data, axes=_ax_interp, levelMode="mono")
                self.imview.setColorMap(self.imcmap.to_pyqtgraph())
                self.imview.setCurrentIndex(0)
        elif data.ndim == 2:
            _ax_interp = {"y": 0, "x": 1}
            self.imview.setImage(data, axes=_ax_interp, levelMode="mono")
            self.imview.getImageItem().setColorMap(self.imcmap.to_pyqtgraph())
            self.img = data
        else:
            print("Data is the wrong number of dimensions.")
            return
        self.reset_levels(0.2, 99.8)

    def reset_levels(
        self, low_percentile: float, high_percentile: float
    ) -> None:
        # Setting levels
        img = self.imview.image
        pct_range = [low_percentile, high_percentile]
        if img is None:
            return
        if img.ndim == 3:
            if img.shape[-1] > 3:
                lo, hi = np.percentile(
                    img[np.isfinite(img[:, :, 0]), 0], pct_range
                )
                self.imview.setLevels(min=lo, max=hi)
            elif img.shape[-1] == 3:
                rgb_lohi = []
                for i in range(img.shape[-1]):
                    rgb_lohi.append(
                        np.percentile(
                            img[np.isfinite(img[:, :, i]), i],
                            [0.2, 99.8],
                        )
                    )
                self.imview.setLevels(rgba=rgb_lohi)
        else:
            return

    def pixel_select(self, mouse_event: MouseClickEvent) -> None:
        if mouse_event.button() != Qt.MouseButton.LeftButton:
            return
        mods = QApplication.keyboardModifiers()
        if (
            mods == Qt.KeyboardModifier.ControlModifier
            or mods == Qt.KeyboardModifier.AltModifier
        ):
            return
        if self._drawing:
            return
        img = self.imview.image
        if img is None:
            return
        data_pos = self.imview.getView().mapSceneToView(mouse_event.pos())
        x = int(data_pos.x())
        y = int(data_pos.y())
        if y < 0 or y > img.shape[0]:
            print(f"Out of Image Bounds. ({x}, {y})")
            return
        if x < 0 or x > img.shape[1]:
            print(f"Out of Image Bounds. ({x}, {y})")
            return
        self.pixel_picked.emit(y, x)

    def roi_click_handler(self, mouse_event: MouseClickEvent) -> None:
        mods = QApplication.keyboardModifiers()
        pos = mouse_event.scenePos()
        view_pos = self.imview.getView().mapSceneToView(pos)
        if mods == Qt.KeyboardModifier.ControlModifier:

            if not self._drawing:
                self.start_lasso([[view_pos.x(), view_pos.y()]])
            else:
                if mouse_event.double():
                    self.finish_lasso()

        if mods == Qt.KeyboardModifier.AltModifier:
            if not self._drawing:
                self.start_line_roi([[view_pos.x(), view_pos.y()]])
            else:
                return

    def lasso_movement(self, pos: QPointF):
        if not self._drawing:
            return
        view_pos = self.imview.getView().mapSceneToView(pos)
        pts = self.lasso.getState()["points"]
        pts.append([view_pos.x(), view_pos.y()])
        self.lasso.setPoints(pts)
        for h in self.lasso.handles:
            h["item"].setVisible(False)

    def start_lasso(self, pos):
        self._drawing = True
        self.lasso.clearPoints()
        self.lasso.setPoints(pos)
        self.lasso.setVisible(True)

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

        self.lasso_finished.emit(in_array, xy_verts)

    def start_line_roi(self, pos):
        self._drawing = True
        self.line_roi.setPos(pg.Point(*pos))
        self.line_roi_started.emit()
        self.line_roi.setVisible(True)

    def update_line_roi(self) -> None:
        self._drawing = False
        (_, end_pt1), (_, end_pt2) = self.line_roi.getSceneHandlePositions()
        end_pt1 = self.imview.getView().mapSceneToView(end_pt1)
        end_pt2 = self.imview.getView().mapSceneToView(end_pt2)
        pt1_int: tuple[int, int] = (int(end_pt1.x()), int(end_pt1.y()))
        pt2_int: tuple[int, int] = (int(end_pt2.x()), int(end_pt2.y()))
        pixels = get_bresenham_line(pt1_int, pt2_int)
        coords = np.empty((len(pixels), 2), dtype=np.int32)
        for n, i in enumerate(pixels):
            coords[n, :] = i
        self.line_roi_updated.emit(coords)

    def close_line_roi(self) -> None:
        self.line_roi.setVisible(False)
        self._drawing = False

    def track_cursor(self, pos) -> None:
        view_pos = self.imview.getView().mapSceneToView(pos)
        x_float = view_pos.x()
        y_float = view_pos.y()
        x_int = int(x_float)
        y_int = int(y_float)
        img = self.imview.getImageItem().image  # axes flipped
        if img is None:
            return
        if 0 <= y_int < img.shape[1] and 0 <= x_int < img.shape[0]:
            if img.ndim == 2:
                self.mouse_moved.emit(
                    x_float,
                    y_float,
                    PixelValue(v=img[x_int, y_int], pixel_type="single"),
                )
            elif img.ndim == 3:
                self.mouse_moved.emit(
                    x_float,
                    y_float,
                    PixelValue(
                        r=img[x_int, y_int, 0],
                        g=img[x_int, y_int, 1],
                        b=img[x_int, y_int, 2],
                        pixel_type="rgb",
                    ),
                )
        else:
            self.mouse_moved.emit(-999, -999, PixelValue.null())
