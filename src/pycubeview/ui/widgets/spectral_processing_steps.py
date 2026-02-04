# Built-Ins
from typing import Literal, TypeAlias

# PySide6 Imports
from PySide6.QtWidgets import QWidget

# Local Imports
from .measurement_processor import (
    MeasurementProcessor,
    StepConfig,
)
from .processing_parameter_widgets import (
    ParameterWidget,
    FloatSlider,
    IntSlider,
    OptionBox,
)
from pycubeview.custom_types import SpectralProcessingStepLiteral

OutlierRemovalParams: TypeAlias = Literal["sigma_threshold"]
FilteringParams: TypeAlias = Literal["method", "filter_width"]
ContRemParams: TypeAlias = Literal["method"]


class OutlierRemoval(StepConfig):

    def __init__(
        self,
        step_list: list[OutlierRemovalParams],
        widget_list: list[ParameterWidget],
        parent: QWidget | None,
    ):
        param_widgets: dict[str, ParameterWidget] = {
            k: v for k, v in zip(step_list, widget_list)
        }
        super().__init__(param_widgets, parent)


class Filtering(StepConfig):
    def __init__(
        self,
        step_list: list[FilteringParams],
        widget_list: list[ParameterWidget],
        parent: QWidget | None,
    ):
        param_widgets: dict[str, ParameterWidget] = {
            k: v for k, v in zip(step_list, widget_list)
        }
        super().__init__(param_widgets, parent)


class ContinuumRemoval(StepConfig):
    def __init__(
        self,
        step_list: list[ContRemParams],
        widget_list: list[ParameterWidget],
        parent: QWidget | None,
    ):
        param_widgets: dict[str, ParameterWidget] = {
            k: v for k, v in zip(step_list, widget_list)
        }
        super().__init__(param_widgets, parent)


def get_spectral_processing_steps(
    processor: MeasurementProcessor,
) -> list[tuple[SpectralProcessingStepLiteral, StepConfig]]:
    outlier_widgets: list[ParameterWidget] = [
        FloatSlider((0, 4), "Sigma Threshold", processor)
    ]
    filtering_widgets: list[ParameterWidget] = [
        OptionBox(["box_filter"], processor),
        IntSlider((0, 15), "Filter Width", processor),
    ]
    contrem_config: list[ParameterWidget] = [
        OptionBox(["double_line"], processor)
    ]
    return [
        (
            "OUTLIER_REMOVAL",
            OutlierRemoval(["sigma_threshold"], outlier_widgets, processor),
        ),
        (
            "FILTERING",
            Filtering(
                ["method", "filter_width"], filtering_widgets, processor
            ),
        ),
        (
            "CONTINUUM_REMOVAL",
            ContinuumRemoval(["method"], contrem_config, processor),
        ),
    ]
