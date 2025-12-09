"""
File Opening Utilities

This module provides a centralized, type-safe dispatch for opening three
categories of files for the operation ofthe SpecView GUI.

Supported File Types
--------------------


Available Helper Functions::

    from pathlib import Path

    wvl = open_wvl(Path("wvlvals.wvl"))
    img = open_cube(Path("cube.geospcub"))

"""

# Built-Ins
from pathlib import Path
from typing import Protocol
from dataclasses import dataclass

# Dependencies
import numpy as np
import rasterio as rio  # type: ignore
import spectralio as sio
import re
import pandas as pd


# ---- Handling Wavelength Data Files ----


class WvlHandler(Protocol):
    """
    Protocol for handling wavelength (or other context data) files.
    """

    def __call__(self, path: Path) -> np.ndarray: ...

    """
    Handle a file at the given path.

    Parameters
    ----------
    path: Path
        Path to an existing file whose suffix is one of the following

        - .wvl
        - .hdr
        - .txt
        - .csv

    Returns
    -------
    wvl_array: np.ndarray
        A 1D numpy array that holds the wavelength values.

    Raises
    ------
    OSError
        If the file cannot be read.
    """


def open_wvl_file(path: Path) -> np.ndarray:
    """Reads .wvl files using `spectralio`"""
    wvl = sio.read_wvl(path)
    return wvl.asarray()


def open_hdr_file(path: Path) -> np.ndarray:
    """Read an ENVI .hdr file"""
    wvl_pattern = re.compile(r"wavelength\s=\s\{([^}]*)\}")
    with open(path, "r") as f:
        file_contents = f.read()
    result = re.findall(wvl_pattern, file_contents)
    if len(result) == 0:
        raise OSError("Unable to open .hdr file. Is there a wavelength field?")
    vals = np.asarray([float(i) for i in result[0].split(",")])
    return vals


def open_txt_file(path: Path) -> np.ndarray:
    """
    Read a .txt file. Wavelength values should be seperated by commas.
    """
    with open(path, "r") as f:
        contents = f.read()
    vals = contents.split(",")
    if vals[-1] == " ":
        vals = vals[:-1]
    return np.asarray([float(i) for i in vals])


def open_csv_file(path: Path) -> np.ndarray:
    """
    Opens a csv file where there is one row of headers and at least one is
    "wavelength". Make sure there are no spaces around the commas!
    """
    df = pd.read_csv(path)
    wvl_col_idx = [i.lower() for i in df.columns.to_list()].index("wavelength")
    wvl = df.iloc[:, wvl_col_idx].to_numpy()
    return wvl


# Mapping from lowercase string file extensions to handler functions.
WVL_HANDLERS: dict[str, WvlHandler] = {
    ".wvl": open_wvl_file,
    ".hdr": open_hdr_file,
    ".txt": open_txt_file,
    ".csv": open_csv_file,
}


def open_wvl(path: str | Path) -> np.ndarray:
    """
    Open a file that stores wavelength information.

    This function inspects the files extension name and passes it to the
    appropriate handler for that file type.

    Parameters
    ----------
    path: str or Path
        Path to file containing wavelength data that is to be opened.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    ValueError
        If the file does not have a valid extension.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    suffix = path.suffix.lower()

    handler = WVL_HANDLERS.get(suffix)

    if handler is None:
        raise ValueError(f"Unsupported file type: {suffix}")

    return handler(path)


# ---- Handling Cube Data Files ----
@dataclass
class CubeAxisOrder:
    """
    Holds information for orienting spectral data cubes.

    Parameters
    ----------
    x: int
        Axis index for the horizontal image direction.
    y: int
        Axis index for the vertical image direction.
    b: int
        Axis index for the spectral band (or other context data) direction.
    """

    x: int
    y: int
    b: int


class CubeHandler(Protocol):
    """
    Protocol for handling cube data files.
    """

    def __call__(self, path: Path, axis_map: dict[str, int]) -> np.ndarray: ...

    """
    Handle a file at the given path.

    Parameters
    ----------
    path: Path
        Path to an existing file whose suffix is one of the following

        - .spcub
        - .geospcub
        - .bsq
        - .img
        - .tif



    Returns
    -------
    cube_array: np.ndarray
        A 3D numpy array where axis 0 is the vertical image dimension, axis 1
        is the horizontal image dimension and axis 2 is the wavelength (or
        other context data) dimension.

    Raises
    ------
    OSError
        If the file cannot be read.
    """


def open_spcub_cube(path: Path, axis_map: dict[str, int]) -> np.ndarray:
    """
    Read .spcub or .geospcub files using `spectralio`
    """
    cub_obj: sio.Spectrum3D
    if path.suffix.lower() == ".geospcub":
        cub_obj = sio.read_spec3D(path, kind="geospcub")
    elif path.suffix.lower() == ".spcub":
        cub_obj = sio.read_spec3D(path, kind="spcub")
    else:
        raise ValueError(
            "Invalid File Type passed to `open_spcub_file()`: "
            f"{path.suffix.lower()}"
        )
    return cub_obj.load_raster(bbl=True)


def open_rasterio_cube(path: Path, axis_map: dict[str, int]) -> np.ndarray:
    """
    Reads any rasterio-compatible file type.
    """
    try:
        axis_order_obj = CubeAxisOrder(**axis_map)
    except TypeError:
        raise TypeError(
            "Invalid axis_order dictionary with keys: "
            f"{list(axis_map.keys())}. The keys should be ['x', 'y', 'b']"
            " for the horizontal, vertical and spectral (or other) dimension,"
            " respectively."
        )

    with rio.open(path, "r") as f:
        cube_array = f.read()
    transpose_order = (axis_order_obj.y, axis_order_obj.x, axis_order_obj.b)
    cube_array = np.transpose(cube_array, transpose_order)
    return cube_array


# Mapping from lowercase file extension to handler function.
CUBE_HANDLERS: dict[str, CubeHandler] = {
    ".spcub": open_spcub_cube,
    ".geospcub": open_spcub_cube,
    ".bsq": open_rasterio_cube,
    ".img": open_rasterio_cube,
    ".tif": open_rasterio_cube,
}


def open_cube(
    path: str | Path, axis_map: dict[str, int] = {"x": 2, "y": 1, "b": 0}
) -> tuple[np.ndarray, str]:
    """
    Open a file that stores spectral (or other) cube-based information.

    This function inspects the files extension name and passes it to the
    appropriate handler for that file type.

    Parameters
    ----------
    path: str or Path
        Path to file containing wavelength data that is to be opened.

    Returns
    -------
    cube_array: np.ndarray
        3D Array of spectral cube data.
    file_suffix: str
        Lowercase suffix of the file name.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    ValueError
        If the file does not have a valid extension.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    suffix = path.suffix.lower()

    handler = CUBE_HANDLERS.get(suffix)

    if handler is None:
        raise ValueError(f"Unsupported file type: {suffix}")

    return (handler(path, axis_map), suffix)
