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

    main.show()
    app.exec()


def main():
    arguably.run()
