# Dependencies
import numpy as np
import pyqtgraph as pg  # type: ignore
import cmap

# Local Imports
from pycubeview.data.valid_colormaps import SequentialColorMap
from pycubeview.data_transfer_classes import (
    ImageClickData,
    ImageScatterPoint,
    CursorTracker,
    PixelValue,
)

# Relative Imports
from pycubeview.validators.image_display_validators import (
    ImageViewConfig,
    _validate_image_data,
    _validate_pixel,
)

# PySide6 Imports
from PySide6.QtWidgets import QWidget, QVBoxLayout, QApplication
from PySide6.QtCore import Signal, QTimer, QPointF, Qt
from PySide6.QtGui import QMouseEvent


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
        self.pg_image_view = pg.ImageView(parent=self, name=display_name)
        self._vbox = self.pg_image_view.getView()

        # ---- Setting Cursor ----
        self._vbox.setCursor(Qt.CursorShape.CrossCursor)

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
    data_tracking = Signal(CursorTracker)

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
        self.setMouseTracking(True)

        # Connecting INTERAL ONLY signals
        self._vbox.scene().sigMouseMoved.connect(self._on_mouse_moved)

    def plot_point(self, *, y: int, x: int, color: cmap.Color) -> None:
        scatter = pg.ScatterPlotItem(
            x=[x + 0.5],
            y=[y + 0.5],
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

    def _get_pixel_value(
        self, x: int, y: int, *, img_arg: np.ndarray | None = None
    ) -> PixelValue:
        img: np.ndarray
        if img_arg is None:
            _img = self.pg_image_view.getImageItem().image  # axes flipped
            if _img is not None:
                img = _img
            else:
                raise ValueError("Invalid Image.")
        else:
            img = img_arg

        if img.ndim == 2:
            return PixelValue(v=img[x, y], pixel_type="single")
        elif img.ndim == 3:
            return PixelValue(
                r=img[x, y, 0],
                g=img[x, y, 1],
                b=img[x, y, 2],
                pixel_type="rgb",
            )
        else:
            raise ValueError("Invalid Image Dimensions.")

    def _on_mouse_moved(self, pos: QPointF) -> None:
        if not self._vbox.sceneBoundingRect().contains(pos):
            return
        data_position = self._vbox.mapSceneToView(pos)
        x = data_position.x()
        y = data_position.y()
        xint = int(x)
        yint = int(y)
        _img = self.pg_image_view.getImageItem().image
        if _img is not None:
            img = _img
        else:
            raise ValueError("InvalidImage")
        if _validate_pixel(y, x, np.transpose(img, (1, 0)), quiet=True):
            val: PixelValue = self._get_pixel_value(xint, yint, img_arg=img)
            ctrack = CursorTracker(
                x_exact=x,
                y_exact=y,
                x_int=xint,
                y_int=yint,
                value=val,
            )
            self.data_tracking.emit(ctrack)
        else:
            self.data_tracking.emit(
                CursorTracker(
                    x_exact=x,
                    y_exact=y,
                    x_int=xint,
                    y_int=yint,
                    value=PixelValue.null(),
                )
            )

    def _to_data_coords(self, event: QMouseEvent) -> QPointF:
        widget_coords: QPointF = event.position()
        imview_coords = self.pg_image_view.mapFromParent(widget_coords)
        data_coords: QPointF = self._vbox.mapSceneToView(imview_coords)
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
