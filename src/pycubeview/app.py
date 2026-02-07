# flake8: noqa

# nuitka-project: --mode=standalone
# nuitka-project: --enable-plugin=pyside6
# nuitka-project: --output-filename=cubeview

# Including data and packages
# nuitka-project: --include-package=pycubeview
# nuitka-project: --include-package=cmap.data
# nuitka-project: --include-package-data=cmap
# nuitka-project: --include-package=rasterio
# nuitka-project: --include-package-data=rasterio
# nuitka-project: --include-module=PySide6.QtOpenGL
# nuitka-project: --include-data-dir=src/pycubeview/icons=resources/icons

# Speedup Options
# nuitka-project: --assume-yes-for-downloads
# nuitka-project: --output-dir=dist
# nuitka-project: --jobs=2
# nuitka-project: --lto=no
# nuitka-project: --nofollow-import-to=*.tests

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

    main.show()
    app.exec()


def main():
    arguably.run()
