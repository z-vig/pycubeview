# Dependencies
import arguably

# PyQt6 Imports
from PyQt6.QtWidgets import QApplication

# Local Imports
from .spectral_viewing_window import CubeViewWindow


@arguably.command
def cubeview():
    app = QApplication([])

    # For Quick Dev
    main = CubeViewWindow(
        wvl="D:/moon_data/m3/M3G.wvl",
        image_data="D:/moon_data/m3/Gruithuisen_Region/Gruithuisen_Mosaics/global_mode/M3G_GDOMES_RFL.geospcub",  # noqa
        cube_data="D:/moon_data/m3/Gruithuisen_Region/Gruithuisen_Mosaics/global_mode/M3G_GDOMES_RFL.geospcub",  # noqa
    )

    # main = CubeViewWindow()
    main.show()
    app.exec()


def main():
    arguably.run()
