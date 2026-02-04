# Built-Ins
from typing import Any

# PySide6 Imports
from PySide6.QtCore import Slot, Signal, Qt
from PySide6.QtWidgets import (
    QWidget,
    QSlider,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QSizePolicy,
)


class ParameterWidget(QWidget):
    parameter_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

    @property
    def value(self) -> Any:
        raise NotImplementedError(
            "Each ParameterWidget must implement get_parameter."
        )


class FloatSlider(ParameterWidget):
    def __init__(
        self,
        slider_range: tuple[float, float],
        slider_unit: str,
        parent: QWidget | None,
    ) -> None:
        super().__init__(parent)

        self.slider = QSlider()
        self.slider.setOrientation(Qt.Orientation.Horizontal)

        self.lbl = QLabel(f"{slider_unit}: {self.slider.value()/100}")
        self.lbl.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred
        )
        self.lbl.setMinimumWidth(200)
        self.unit = slider_unit

        layout = QVBoxLayout(self)
        layout.addWidget(self.lbl)
        layout.addWidget(self.slider)

        self.slider.setRange(
            int(slider_range[0] * 100), int(slider_range[1] * 100)
        )
        self.slider.setSingleStep(1)

        self.slider.valueChanged.connect(self._on_slider)
        self.slider.valueChanged.connect(
            lambda _: self.parameter_changed.emit()
        )

    @Slot(int)
    def _on_slider(self, value: int):
        self.lbl.setText(f"{self.unit}: {value/100}")

    @property
    def value(self) -> float:
        return self.slider.value() / 100


class IntSlider(ParameterWidget):
    def __init__(
        self,
        slider_range: tuple[int, int],
        slider_unit: str,
        parent: QWidget | None,
    ) -> None:
        super().__init__(parent)

        self.slider = QSlider()
        self.slider.setOrientation(Qt.Orientation.Horizontal)

        self.lbl = QLabel(f"{slider_unit}: {self.slider.value()}")
        self.lbl.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred
        )
        self.lbl.setMinimumWidth(200)
        self.unit = slider_unit

        layout = QVBoxLayout(self)
        layout.addWidget(self.lbl)
        layout.addWidget(self.slider)

        self.slider.setRange(slider_range[0], slider_range[1])
        self.slider.setSingleStep(1)

        self.slider.valueChanged.connect(self._on_slider)
        self.slider.valueChanged.connect(
            lambda _: self.parameter_changed.emit()
        )

    @Slot(int)
    def _on_slider(self, value: int):
        self.lbl.setText(f"{self.unit}: {value}")

    @property
    def value(self) -> float:
        return self.slider.value()


class OptionBox(ParameterWidget):
    def __init__(self, options: list[str], parent: QWidget | None) -> None:
        super().__init__(parent)

        self.mode = QComboBox()
        self.mode.addItems(options)

        layout = QVBoxLayout(self)
        layout.addWidget(self.mode)

        self.mode.currentTextChanged.connect(
            lambda _: self.parameter_changed.emit()
        )

    @property
    def value(self) -> str:
        return self.mode.currentText()
