from PyQt6.QtWidgets import QLabel


class BaseStatusIndicator:
    def __init__(
        self,
        name: str,
        indicator_label: QLabel,
        starting_state: bool = False,
    ) -> None:
        self.name = name
        self.active: bool = starting_state
        self.icon = indicator_label

        self.update_indicator()

    def toggle(self):
        self.active = not self.active
        self.update_indicator()

    def update_indicator(self):
        self.icon.setVisible(self.active)
