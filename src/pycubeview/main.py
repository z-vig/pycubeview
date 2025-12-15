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
