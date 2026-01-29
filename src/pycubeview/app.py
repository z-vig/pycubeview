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
        "D:/moon_data/m3/Gruithuisen_Region/Gruithuisen_Mosaics/global_mode/"
    )
    controller.file.set_base_fp(fp=base_fp)
    # controller.file.open_image(fp=Path(base_fp, "M3G_GDOMES_RFL.geospcub"))

    # For Quick Dev
    # main = CubeViewWindow(
    #     wvl="D:/moon_data/m3/M3G.wvl",
    #     image_data="D:/moon_data/m3/Gruithuisen_Region/Gruithuisen_Mosaics/global_mode/M3G_GDOMES_RFL.geospcub",
    #     cube_data="D:/moon_data/m3/Gruithuisen_Region/Gruithuisen_Mosaics/global_mode/M3G_GDOMES_RFL.geospcub",
    #     base_dir="D:/moon_data/m3/Gruithuisen_Region/Gruithuisen_Mosaics/",
    # )
    # main = CubeViewWindow(
    #     base_dir="D:/moon_data/m3/Gruithuisen_Region/Gruithuisen_Mosaics/",
    # )

    # main = CubeViewWindow()
    main.show()
    app.exec()


def main():
    arguably.run()
