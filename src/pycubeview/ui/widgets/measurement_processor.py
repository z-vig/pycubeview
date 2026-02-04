# Built-Ins
from typing import Any

# Local Imports
from .meas_display import MeasurementAxisDisplay
from pycubeview.data_transfer_classes import Measurement
from pycubeview.cubeview_protocols import MeasurementProcessorFunction
from pycubeview.services.process_measurements import ProcessingFlag

# PySide6 Imports
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QDialog,
    QTreeWidget,
    QTreeWidgetItem,
    QStackedWidget,
    QSplitter,
    QVBoxLayout,
    QDialogButtonBox,
    QFormLayout,
)


class ParameterWidget(QWidget):
    parameter_changed = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

    def on_parameter_change(self, value: Any):
        raise NotImplementedError(
            "Each ParameterWidget must implement on_parameter_change."
        )

    def get_parmeter(self) -> Any:
        raise NotImplementedError(
            "Each ParameterWidget must implement get_parameter."
        )


class StepConfig(QWidget):
    def __init__(
        self,
        param_widgets: dict[str, ParameterWidget],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.widgets = param_widgets

        layout = QFormLayout(self)
        for name, widget in param_widgets.items():
            self._widget = widget
            layout.addRow(name, self._widget)


class MeasurementProcessor(QDialog):
    def __init__(
        self, meas_disp: MeasurementAxisDisplay, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._meas = meas_disp

        self._steps: list[QTreeWidgetItem] = []
        self._configs: list[StepConfig] = []

        self._tree = QTreeWidget()
        self._tree.setHeaderLabel("Processing Steps")

        self._stack = QStackedWidget()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._tree)
        splitter.addWidget(self._stack)

        layout = QVBoxLayout(self)
        layout.addWidget(splitter)
        layout.addWidget(buttons)

        self._tree.currentItemChanged.connect(self._on_step_changed)

        self.setWindowTitle("Processing Options")

    def add_step(self, name: str, config_widget: QWidget) -> None:
        item = QTreeWidgetItem([name])
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(0, Qt.CheckState.Checked)

        self._tree.addTopLevelItem(item)
        self._stack.addWidget(config_widget)

    def _on_step_changed(
        self,
        current: QTreeWidgetItem,
    ) -> None:
        if current is None:
            return

        index = self._tree.indexOfTopLevelItem(current)
        if index >= 0:
            self._stack.setCurrentIndex(index)

    def run_processing(
        self,
        meas: Measurement,
        processing_function: MeasurementProcessorFunction,
    ):
        flags: list[ProcessingFlag] = []
        for i, j in zip(self._steps, self._configs):
            step_name = i.text(0)
            config_dict = {k: v.get_parmeter() for k, v in j.widgets.items()}
            flags.append(ProcessingFlag(step=step_name, config=config_dict))

        processing_function(measurement=meas, processing_flags=flags)


# gain = QDoubleSpinBox()
# gain.setRange(0.0, 10.0)
# gain.setValue(1.0)

# mode = QComboBox()
# mode.addItems(["fast", "balanced", "accurate"])

# level = LabeledSlider(self)
# level.slider.setOrientation(Qt.Orientation.Horizontal)
# level.slider.setRange(0, self._meas.meas_lbl.size // 2)

# config1 = StepConfig({"Gain": gain})
# config2 = StepConfig({"Options": mode, "Level": level})

# self.add_step("Step1", config1)
# self.add_step("Step2", config2)
