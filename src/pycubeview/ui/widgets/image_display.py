# Dependencies
import numpy as np
import pyqtgraph as pg  # type: ignore
from pyqtgraph.GraphicsScene.mouseEvents import MouseClickEvent  # type: ignore
import cmap

# Local Imports
from pycubeview.data.valid_colormaps import SequentialColorMap

# Relative Imports
from pycubeview.validators.image_display_validators import (
    ImageViewConfig,
    _validate_image_data,
    _validate_pixel,
)

# PySide6 Imports
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal


class BaseImageDisplay(QWidget):
    def __init__(
        self,
        parent: QWidget | None = None,
        display_name: str = "ImageDisplay",
        image_cmap: SequentialColorMap = "matlab:gray",
    ):
        super().__init__()
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
    pixel_clicked = Signal(int, int)

    def __init__(
        self,
        display_name: str,
        parent: QWidget | None = None,
        image_cmap: SequentialColorMap = "matlab:gray",
    ):
        super().__init__(parent, display_name, image_cmap)
        self.pg_image_view.scene.sigMouseClicked.connect(  # type: ignore
            self._on_pixel_clicked
        )

    def _on_pixel_clicked(self, event: MouseClickEvent):
        pos = self.pg_image_view.getView().mapSceneToView(event.pos())
        x = int(pos.x())
        y = int(pos.y())
        img = self.pg_image_view.image
        if img is None:
            return
        if _validate_pixel(y, x, img):
            self.pixel_clicked.emit(y, x)
