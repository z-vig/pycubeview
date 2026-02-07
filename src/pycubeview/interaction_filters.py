from pycubeview.data_transfer_classes import ImageClickData

from PySide6.QtCore import Qt


def is_regular_left_click(click: ImageClickData) -> bool:
    if (
        click.button == Qt.MouseButton.LeftButton
        and click.modifiers == Qt.KeyboardModifier.NoModifier
    ):
        return True
    return False


def is_ctrl_left_click(click: ImageClickData) -> bool:
    if (
        click.button == Qt.MouseButton.LeftButton
        and click.modifiers == Qt.KeyboardModifier.ControlModifier
    ):
        return True
    return False
