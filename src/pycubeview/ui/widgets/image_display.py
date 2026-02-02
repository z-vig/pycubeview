# Dependencies
import numpy as np
import pyqtgraph as pg  # type: ignore
import cmap

# Local Imports
from pycubeview.data.valid_colormaps import SequentialColorMap
from pycubeview.data_transfer_classes import ImageClickData, ImageScatterPoint

# Relative Imports
from pycubeview.validators.image_display_validators import (
    ImageViewConfig,
    _validate_image_data,
    _validate_pixel,
)

# PySide6 Imports
from PySide6.QtWidgets import QWidget, QVBoxLayout, QApplication
from PySide6.QtCore import Signal, QTimer, QPointF
from PySide6.QtGui import QMouseEvent, QCursor, QPixmap


class BaseImageDisplay(QWidget):
    def __init__(
        self,
        display_name: str,
        parent: QWidget | None = None,
        image_cmap: SequentialColorMap = "matlab:gray",
    ):
        super().__init__(parent)
        # ---- Adding Attributes ----
        self.name = display_name
        self.display_colormap = cmap.Colormap(image_cmap)
        self._image_data: np.ndarray | None = None

        # ---- Initializing Widgets ----
        self.pg_image_view = pg.ImageView(name=display_name)

        # ---- Setting up layout ----
        layout = QVBoxLayout(self)
        layout.addWidget(self.pg_image_view)
        self.setLayout(layout)

    @property
    def image_data(self) -> np.ndarray:
        if self._image_data is None:
            raise RuntimeError("Image Data has not been set.")
        return self._image_data

    @image_data.setter
    def image_data(self, value: np.ndarray) -> None:
        self._image_data = value
        # Validates ndims and size of image data and returns config settings
        imview_config = _validate_image_data(self.image_data)

        # Uses config settings for setImage
        self.pg_image_view.setImage(
            value,
            axes=imview_config["axes"],
            levelMode=imview_config["levelMode"],
        )

        # Sets the colormap based on the config settings.
        self._set_imview_colormap(imview_config)

        # Resets color limits to scale correctly.
        self.reset_levels(1, 99)

    @property
    def image_size(self) -> tuple[int, int]:
        return (self.image_data.shape[0], self.image_data.shape[1])

    def _set_imview_colormap(
        self,
        imview_config: ImageViewConfig,
    ):
        """
        Sets the colormap based on the type of image determined from
        `_validate_image_data`.
        """
        if imview_config["levelMode"] == "mono":
            if imview_config["desc"] == "meas":
                self.pg_image_view.setColorMap(
                    self.display_colormap.to_pyqtgraph()
                )
                self.pg_image_view.setCurrentIndex(0)
            elif imview_config["desc"] == "flat":
                self.pg_image_view.getImageItem().setColorMap(
                    self.display_colormap.to_pyqtgraph()
                )

    def reset_levels(
        self, low_percentile: float, high_percentile: float
    ) -> None:
        # Setting levels
        img = self.pg_image_view.image
        pct_range = [low_percentile, high_percentile]
        if img is None:
            return
        if img.ndim == 3:
            if img.shape[-1] > 3:
                lo, hi = np.percentile(
                    img[np.isfinite(img[:, :, 0]), 0], pct_range
                )
                self.pg_image_view.setLevels(min=lo, max=hi)
            elif img.shape[-1] == 3:
                rgb_lohi = []
                for i in range(img.shape[-1]):
                    rgb_lohi.append(
                        np.percentile(
                            img[np.isfinite(img[:, :, i]), i],
                            [0.2, 99.8],
                        )
                    )
                self.pg_image_view.setLevels(rgba=rgb_lohi)
        else:
            return


class ImageDisplay(BaseImageDisplay):
    pixel_clicked = Signal(ImageClickData)
    pixel_double_clicked = Signal(ImageClickData)
    point_plotted = Signal(ImageScatterPoint)

    def __init__(
        self,
        display_name: str,
        parent: QWidget | None = None,
        image_cmap: SequentialColorMap = "matlab:gray",
    ):
        super().__init__(display_name, parent, image_cmap)
        self._click_timer = QTimer(self)
        self._click_timer.setSingleShot(True)
        self._click_timer.timeout.connect(self._emit_single_click)

    def plot_point(self, *, y: int, x: int, color: cmap.Color) -> None:
        scatter = pg.ScatterPlotItem(
            x=[x],
            y=[y],
            pen=pg.mkPen(None),
            brush=pg.mkBrush(color=color.hex),
            size=10,
        )
        self.pg_image_view.getView().addItem(scatter)
        scatter_pt = ImageScatterPoint(
            x=x, y=y, color=color, scatter_plot_item=scatter
        )
        self.point_plotted.emit(scatter_pt)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.click_data = self._process_click(event)
        self._click_timer.start(QApplication.doubleClickInterval())

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        self._click_timer.stop()
        self._emit_double_click()

    def _just_the_tip(self, event: QMouseEvent) -> QPointF:
        """
        Gets the position of the mouse tip, rather than the center.
        """
        cursor = QCursor()
        pixmap: QPixmap = cursor.pixmap()
        hotspot = cursor.hotSpot()

        if pixmap.isNull():
            return event.position()

        tip_offset = QPointF(-hotspot.x(), -hotspot.y())

        return event.position() + tip_offset

    def _to_data_coords(self, event: QMouseEvent) -> QPointF:
        widget_coords: QPointF = self._just_the_tip(event)
        scene_coords: QPointF = self.pg_image_view.getView().mapToScene(
            widget_coords
        )
        view_box: pg.ViewBox = self.pg_image_view.getView()  # type: ignore # noqa
        data_coords: QPointF = view_box.mapSceneToView(scene_coords)
        return data_coords

    def _process_click(self, event: QMouseEvent) -> ImageClickData | None:
        pos = self._to_data_coords(event)
        x = pos.x()
        y = pos.y()
        img: np.ndarray = self.pg_image_view.image  # type: ignore
        if img is None:
            return None
        if _validate_pixel(y, x, img):
            print(f"{x:.2f}, {y:.2f}, {int(x)}, {int(y)}")
            return ImageClickData(
                x_exact=x,
                y_exact=y,
                x_int=int(x),
                y_int=int(y),
                button=event.button(),
                modifiers=event.modifiers(),
            )

        else:
            return None

    def _emit_single_click(self) -> None:
        if self.click_data is None:
            return
        self.pixel_clicked.emit(self.click_data)

    def _emit_double_click(self) -> None:
        if self.click_data is None:
            return
        self.pixel_double_clicked.emit(self.click_data)
