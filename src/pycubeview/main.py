# Compilation mode, support OS-specific options
# nuitka-project: --mode=standalone
# nuitka-project: --enable-plugin=pyside6
# nuitka-project: --include-package=pycubeview
# nuitka-project: --include-package=cmap.data
# nuitka-project: --include-package-data=cmap
# nuitka-project: --include-package=rasterio
# nuitka-project: --include-package-data=rasterio
# nuitka-project: --include-module=PySide6.QtOpenGL

# nuitka-project: --output-dir=dist
# nuitka-project: --jobs=2
# nuitka-project: --lto=no
# nuitka-project: --nofollow-import-to=*.tests

# PySide6 Imports
from PySide6.QtWidgets import QApplication

# Local Imports
from pycubeview.cube_view_window import CubeViewWindow


def cubeview():
    app = QApplication([])

    main = CubeViewWindow()
    main.show()
    app.exec()


def main():
    cubeview()


if __name__ == "__main__":
    main()
