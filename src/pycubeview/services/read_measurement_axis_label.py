"""
Measurement Axis Reading Utilities

This module provides a centralized, type-safe dispatch for opening measurement
axis label files. These labels represent how to interpret the measurement axis
of a cube.

Supported File Types
--------------------
- .wvl
- .hdr
- .txt
- .csv
"""

# Built-Ins
from pathlib import Path
from typing import Protocol
import re

# Dependencies
import numpy as np
import spectralio as sio

# Local Imports
from pycubeview.custom_types import (
    MeasurementFileTypes,
    is_valid_measurement_file,
)


# ---- Handling Wavelength Data Files ----
class MeasHandler(Protocol):
    """
    Protocol for handling measurement label files.
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
    wvl_pattern = re.compile(r"wavelength\s*=\s*\{([^}]*)\}")
    with open(path, "r") as f:
        file_contents = f.read()
    result = re.findall(wvl_pattern, file_contents)
    if len(result) == 0:
        raise OSError("Unable to open .hdr file. Is there a wavelength field?")
    vals = np.asarray([float(i) for i in result[0].split(",")])
    return vals


def open_txt_file(path: Path) -> np.ndarray:
    """
    Read a .txt file. Measurement values should be seperated by commas.
    """
    with open(path, "r") as f:
        contents = f.read()
    vals = contents.split(",")
    if vals[-1] == " ":
        vals = vals[:-1]
    return np.asarray([float(i) for i in vals])


def open_csv_file(
    path: Path, measurement_column_label: str = "wavelength"
) -> np.ndarray:
    """
    Opens a csv file where there is one row of headers and at least one is
    the column label provided. Make sure there are no spaces around the commas!
    """
    if path.stat().st_size == 0:
        raise ValueError(f"File is empty. {path}")
    arr = np.loadtxt(path, delimiter=",", dtype=str)
    if arr.ndim == 1:
        arr = arr[:, None]
    idx = np.argwhere(np.char.lower(arr[0, :]) == measurement_column_label)
    if idx.size == 0:
        raise ValueError("No measurement column exists.")
    if idx.size > 1:
        raise ValueError("Multiple measurement columns exist.")
    return arr[1:, idx[0][0]].astype(float)


# Mapping from lowercase string file extensions to handler functions.
MEAS_HANDLERS: dict[MeasurementFileTypes, MeasHandler] = {
    ".wvl": open_wvl_file,
    ".hdr": open_hdr_file,
    ".txt": open_txt_file,
    ".csv": open_csv_file,
}


def open_meas(path: str | Path) -> np.ndarray:
    """
    Open a file that stores measurement axis label information.

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

    _suffix = path.suffix.lower()
    if is_valid_measurement_file(_suffix):
        suffix: MeasurementFileTypes = _suffix
    else:
        raise ValueError(f"Invalid file type: {_suffix}")

    handler = MEAS_HANDLERS.get(suffix)

    if handler is None:
        raise ValueError(f"Unsupported file type: {suffix}")

    return handler(path)
