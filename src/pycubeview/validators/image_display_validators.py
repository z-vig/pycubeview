# Built-Ins
from typing import TypedDict, Literal, TypeAlias

# Dependencies
import numpy as np


class ColorAxesOrder(TypedDict):
    x: int
    y: int
    c: int


class MeasurementAxesOrder(TypedDict):
    x: int
    y: int
    t: int


class FlatImageAxesOrder(TypedDict):
    x: int
    y: int


AxesOrder: TypeAlias = (
    ColorAxesOrder | MeasurementAxesOrder | FlatImageAxesOrder
)


class ImageViewConfig(TypedDict):
    axes: AxesOrder
    levelMode: Literal["rgba", "mono"]
    desc: Literal["rgb", "meas", "flat"]


def _validate_image_data(arr: np.ndarray) -> ImageViewConfig:
    """
    Validates the number of array dimensions and size of the last dimension,
    which is interpretted as the measurement dimension.

    Parameters
    ----------
    arr: np.ndarray
        Array to validate.

    Returns
    -------
    imview_config: ImageViewConfig
        Configuration options to be passed to the setImage method of
        pg.ImageView instance.
    """
    if arr.ndim == 3:
        if arr.shape[-1] == 3:
            return ImageViewConfig(
                axes={"y": 0, "x": 1, "c": 2}, levelMode="rgba", desc="rgb"
            )
        elif arr.shape[-1] > 3:
            return ImageViewConfig(
                axes={"y": 0, "x": 1, "t": 2}, levelMode="mono", desc="meas"
            )
        else:
            raise ValueError(
                f"Array has invalid measurement axis size: {arr.shape[-1]}."
            )
    elif arr.ndim == 2:
        return ImageViewConfig(
            axes={"y": 0, "x": 1}, levelMode="mono", desc="flat"
        )
    else:
        raise ValueError(f"Array has invalid number of dimensions: {arr.ndim}")


def _validate_pixel(
    y: float | int, x: float | int, img: np.ndarray, quiet: bool = False
) -> bool:
    if y < 0 or y > img.shape[0]:
        if not quiet:
            print(f"Out of Image Bounds. ({x}, {y})")
        return False
    if x < 0 or x > img.shape[1]:
        if not quiet:
            print(f"Out of Image Bounds. ({x}, {y})")
        return False
    return True
