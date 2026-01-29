# Built-Ins
from dataclasses import dataclass, field
from typing import Optional, Generic, TypeVar

# Local Imports
from pycubeview.cubeview_protocols import FileHandler, AppStateHandler

# PySide 6 Imports
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QWidget

T = TypeVar("T")


@dataclass
class ActionSpec(Generic[T]):
    text: str
    callback_name: str
    shortcut: Optional[str] = None
    _action: Optional[QAction] = None

    def build(self, parent: QWidget, receiver: T) -> QAction:
        if self._action is None:
            action = QAction(self.text, parent)
            if self.shortcut is not None:
                action.setShortcut(self.shortcut)

            callback = getattr(receiver, self.callback_name)

            action.triggered.connect(callback)
            self._action = action
        return self._action


@dataclass
class ActionCatalog:
    set_base_fp: ActionSpec[AppStateHandler] = field(
        default_factory=lambda: ActionSpec[AppStateHandler](
            text="Set Base Directory", callback_name="set_base_fp"
        )
    )
    open_image: ActionSpec[FileHandler] = field(
        default_factory=lambda: ActionSpec[FileHandler](
            text="Open New Display Image", callback_name="open_image"
        )
    )
    open_cube: ActionSpec[FileHandler] = field(
        default_factory=lambda: ActionSpec[FileHandler](
            text="Open New Data Cube", callback_name="open_cube"
        )
    )
    reset_data: ActionSpec[FileHandler] = field(
        default_factory=lambda: ActionSpec[FileHandler](
            text="Reset Data", callback_name="reset_data"
        )
    )
