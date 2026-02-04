from typing import Any
from PySide6.QtCore import Slot, Signal
from PySide6.QtWidgets import QWidget, QSlider, QVBoxLayout, QLabel, QComboBox

from .measurement_processor import (
    ParameterWidget,
    MeasurementProcessor,
    StepConfig,
)
from pycubeview.custom_types import SpectralProcessingStepLiteral


class SigmaThresholdSlider(ParameterWidget):
    def __init__(self, parent: QWidget | None) -> None:
        super().__init__(parent)

        self.lbl = QLabel()
        self.slider = QSlider()

        layout = QVBoxLayout(self)
        layout.addWidget(self.lbl)
        layout.addWidget(self.slider)

        self.slider.valueChanged.connect(self._on_slider)
        self.slider.setRange(0, 400)
        self.slider.setSingleStep(1)

    @Slot(int)
    def _on_slider(self, value: int):
        self.lbl.setText(f"Sigma Threshold: {value}")

    def on_parameter_change(self, value: Any):
        self.parameter_changed.emit(value / 100)

    def get_parmeter(self) -> Any:
        return self.slider.value() / 100


class FilterMethodBox(ParameterWidget):
    def __init__(self, parent: QWidget | None) -> None:
        super().__init__(parent)

        self.mode = QComboBox()
        self.mode.addItems(["box_filter"])

        layout = QVBoxLayout(self)
        layout.addWidget(self.mode)

        self.mode.currentTextChanged.connect(self.on_parameter_change)

    def on_parameter_change(self, value: str):
        self.parameter_changed.emit(value)

    def get_parmeter(self) -> str:
        return self.mode.currentText()


class FilterWidthSlider(ParameterWidget):
    def __init__(self, parent: QWidget | None) -> None:
        super().__init__(parent)

        self.lbl = QLabel()
        self.slider = QSlider()

        layout = QVBoxLayout(self)
        layout.addWidget(self.lbl)
        layout.addWidget(self.slider)

        self.slider.valueChanged.connect(self._on_slider)
        self.slider.setRange(0, 100)
        self.slider.setSingleStep(1)

    @Slot(int)
    def _on_slider(self, value: int):
        self.lbl.setText(f"Filter Width: {value}")

    def on_parameter_change(self, value: int):
        self.parameter_changed.emit(value)

    def get_parmeter(self) -> int:
        return self.slider.value()


class ContinuumRemovalMethodBox(ParameterWidget):
    def __init__(self, parent: QWidget | None) -> None:
        super().__init__(parent)

        self.mode = QComboBox()
        self.mode.addItems(["double_line"])

        layout = QVBoxLayout(self)
        layout.addWidget(self.mode)

        self.mode.currentTextChanged.connect(self.on_parameter_change)

    def on_parameter_change(self, value: str):
        self.parameter_changed.emit(value)

    def get_parmeter(self) -> str:
        return self.mode.currentText()


class OutlierRemoval(StepConfig):
    sigma_threshold_changed = Signal(float)

    def __init__(
        self, param_widgets: dict[str, ParameterWidget], parent: QWidget | None
    ):
        super().__init__(param_widgets, parent)

        param_widgets["sigma_threshold"].parameter_changed.connect(
            self.on_sigma_threshold_change
        )

    @Slot(float)
    def on_sigma_threshold_change(self, value: float) -> None:
        self.sigma_threshold_changed.emit(value)


class Filtering(StepConfig):
    filter_method_changed = Signal(str)
    filter_width_changed = Signal(int)

    def __init__(
        self,
        param_widgets: dict[str, ParameterWidget],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(param_widgets, parent)

        param_widgets["method"].parameter_changed.connect(
            self.on_filter_method_change
        )
        param_widgets["filter_width"].parameter_changed.connect(
            self.on_filter_width_change
        )

    @Slot(str)
    def on_filter_method_change(self, value: str) -> None:
        self.filter_method_changed.emit(value)

    @Slot(int)
    def on_filter_width_change(self, value: int) -> None:
        self.filter_width_changed.emit(value)


class ContinuumRemoval(StepConfig):
    contrem_method_changed = Signal(str)

    def __init__(
        self,
        param_widgets: dict[str, ParameterWidget],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(param_widgets, parent)

        param_widgets["method"].parameter_changed.connect(
            self.on_contrem_method_change
        )

    @Slot(str)
    def on_contrem_method_change(self, value: str):
        self.contrem_method_changed.emit(value)


def get_spectral_processing_steps(
    processor: MeasurementProcessor,
) -> list[dict[SpectralProcessingStepLiteral, StepConfig]]:
    outlier_config: dict[str, ParameterWidget] = {
        "sigma_threshold": SigmaThresholdSlider(processor)
    }
    filtering_config: dict[str, ParameterWidget] = {
        "method": FilterMethodBox(processor),
        "filter_width": FilterWidthSlider(processor),
    }
    continuum_removal_config: dict[str, ParameterWidget] = {
        "method": ContinuumRemovalMethodBox(processor)
    }
    return [
        {"OUTLIER_REMOVAL": OutlierRemoval(outlier_config, processor)},
        {"FILTERING": Filtering(filtering_config, processor)},
        {
            "CONTINUUM_REMOVAL": ContinuumRemoval(
                continuum_removal_config, processor
            )
        },
    ]
