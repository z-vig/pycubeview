# Local Imports
from pycubeview.global_app_state import AppState

# PySide6 Imports
from PySide6.QtCore import QObject


class BaseController(QObject):
    def __init__(self) -> None:
        self.app_state = AppState()
        self._build_actions()
        self._install_actions()
        self._connect_signals()
        return

    def _build_actions(self) -> None:
        raise NotImplementedError("_build_actions is not implemented.")

    def _connect_signals(self) -> None:
        raise NotImplementedError("_connect_signals is not implemented.")

    def _install_actions(self) -> None:
        raise NotImplementedError("_install_actions is not implemented.")
