# Compilation mode, support OS-specific options
# nuitka-project: --mode=standalone
# nuitka-project: --enable-plugin=pyqt6
# nuitka-project: --include-package=pycubeview
# nuitka-project: --include-package=cmap.data
# nuitka-project: --include-package-data=cmap

# For Local Testing
# nuitka-project: --jobs=8
# nuitka-project: --lto=no
# nuitka-project: --nofollow-import-to=*.tests
# nuitka-project: --nofollow-import-to=scipy.__check_build
# nuitka-project: --nofollow-import-to=scipy._build_utils
# nuitka-project: --nofollow-import-to=scipy.cluster
# nuitka-project: --nofollow-import-to=scipy.constants
# nuitka-project: --nofollow-import-to=scipy.fft
# nuitka-project: --nofollow-import-to=scipy.integrate
# nuitka-project: --nofollow-import-to=scipy.io
# nuitka-project: --nofollow-import-to=scipy.interpolate
# nuitka-project: --nofollow-import-to=scipy.linalg
# nuitka-project: --nofollow-import-to=scipy.ndimage
# nuitka-project: --nofollow-import-to=scipy.optimize
# nuitka-project: --nofollow-import-to=scipy.signal
# nuitka-project: --nofollow-import-to=scipy.sparse
# nuitka-project: --nofollow-import-to=scipy.stats
# nuitka-project: --nofollow-import-to=scipy.special

# PyQt6 Imports
from PyQt6.QtWidgets import QApplication

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
