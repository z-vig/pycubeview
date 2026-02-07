# Local Imports
from pycubeview.global_app_state import AppState
from pycubeview.actions import ActionCatalog

# PySide6 Imports
from PySide6.QtCore import QObject


class BaseController(QObject):
    def __init__(self, global_state: AppState) -> None:
        super().__init__()
        self.cat = ActionCatalog()
        self.app_state = global_state
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
