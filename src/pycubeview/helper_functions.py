# Dependencies
import numpy as np

# PySide6 Imports
from PySide6.QtWidgets import QApplication

# Local Imports
from .cube_view_window import CubeViewWindow


def open_cubeview(
    image_data: np.ndarray | str | None,
    cube_data: np.ndarray | str | None,
    wvl_data: np.ndarray | str | None,
):
    app = QApplication([])
    main = CubeViewWindow(wvl_data, image_data, cube_data)
    main.show()
    app.exec()
