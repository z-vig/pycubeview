# flake8: noqa

from pathlib import Path

# Dependencies
import arguably

# PySide6 Imports
from PySide6.QtWidgets import QApplication

# Local Imports
from pycubeview.ui.main_cubeview_window import CubeViewMainWindow
from pycubeview.controllers.main_controller import MainController


@arguably.command
def cubeview():
    app = QApplication([])

    main = CubeViewMainWindow()
    controller = MainController(main)

    base_fp = Path(
        "D:/moon_data/m3/Gruithuisen_Region/Gruithuisen_Mosaics_New/global_mode/"
    )
    controller.file.set_base_fp(fp=base_fp)
    controller.file.open_image(fp=Path(base_fp, "M3G_GDOMES_RFL.geospcub"))
    controller.file.open_cube(fp=Path(base_fp, "M3G_GDOMES_RFL.geospcub"))

    main.show()
    app.exec()


def main():
    arguably.run()
