from typing import Optional
from PySide6.QtWidgets import QLabel, QMainWindow, QStatusBar
from PySide6.QtCore import QObject


class BaseStatusIndicator(QObject):
    """A small helper that displays a simple indicator QLabel
    inside a QMainWindow's status bar.

    The indicator label is either provided or created. It will be parented
    to the status bar and added as a permanent or transient widget.
    """

    def __init__(
        self,
        parent: QMainWindow,
        name: str,
        indicator_label: Optional[QLabel] = None,
        starting_state: bool = False,
        permanent: bool = True,
        symbol: str = "⬤",
    ) -> None:
        super().__init__(parent)
        self._parent = parent
        self.name = name
        self.active: bool = starting_state

        # Create label if none provided
        if indicator_label is None:
            self.icon = QLabel(symbol)
        else:
            self.icon = indicator_label

        # Parent the label to the status bar so it is not a top-level window
        status_bar: QStatusBar = self._parent.statusBar()
        self.icon.setParent(status_bar)

        # Add the label to the status bar (permanent by default)
        if permanent:
            status_bar.addPermanentWidget(self.icon)
        else:
            status_bar.addWidget(self.icon)

        self.update_indicator()

    def toggle(self):
        self.active = not self.active
        self.update_indicator()

    def update_indicator(self):
        self.icon.setVisible(self.active)

    def remove(self) -> None:
        """Remove the indicator from the status bar and clean up its widget."""
        try:
            status_bar: QStatusBar = self._parent.statusBar()
            status_bar.removeWidget(self.icon)
        except Exception:
            pass
        self.icon.setParent(None)
        self.icon.deleteLater()

    def __del__(self):
        try:
            self.remove()
        except Exception:
            pass
