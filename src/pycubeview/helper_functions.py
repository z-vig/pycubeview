"""
A set of helper functions to make using PyCubeView more user-friendly.
"""

# Dependencies
import numpy as np

# PySide6 Imports
from PySide6.QtWidgets import QApplication

# Local Imports
from .cube_view_window import CubeViewWindow


def open_cubeview(
    wvl_data: np.ndarray | str | None = None,
    image_data: np.ndarray | str | None = None,
    cube_data: np.ndarray | str | None = None,
    base_dir: str | None = None,
):
    """Starts a CubeView GUI App from the current working directory."""
    app = QApplication([])
    main = CubeViewWindow(wvl_data, image_data, cube_data, base_dir)
    main.show()
    app.exec()
