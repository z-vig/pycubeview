# Built-Ins
from typing import Mapping

# Local Imports
from .meas_display import MeasurementAxisDisplay
from pycubeview.services.process_measurements import ProcessingFlag
from .processing_parameter_widgets import ParameterWidget

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


class StepConfig(QWidget):
    config_changed = Signal()

    def __init__(
        self,
        param_widgets: Mapping[str, ParameterWidget],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.widget_map = param_widgets

        layout = QFormLayout(self)
        self._widget_list = []
        for name, widget in self.widget_map.items():
            print(f"    {name} added.")
            widget.parameter_changed.connect(self.config_changed.emit)
            layout.addRow(name, widget)
            self._widget_list.append(widget)


class MeasurementProcessor(QDialog):
    processing_update = Signal(list)

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

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(self._tree)
        self.splitter.addWidget(self._stack)

        layout = QVBoxLayout(self)
        layout.addWidget(self.splitter)
        layout.addWidget(buttons)

        self._tree.currentItemChanged.connect(self._on_step_changed)
        self._tree.itemChanged.connect(self.run_processing)

        self.setWindowTitle("Processing Options")

    def add_step(self, name: str, config_widget: StepConfig) -> None:
        item = QTreeWidgetItem([name])
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(0, Qt.CheckState.Unchecked)

        print(f"STEP ADDED: {name}")
        config_widget.config_changed.connect(self.run_processing)

        self._tree.addTopLevelItem(item)
        self._stack.addWidget(config_widget)

        self._steps.append(item)
        self._configs.append(config_widget)

    def _on_step_changed(
        self,
        current: QTreeWidgetItem,
    ) -> None:
        if current is None:
            return

        index = self._tree.indexOfTopLevelItem(current)
        if index >= 0:
            self._stack.setCurrentIndex(index)

    def run_processing(self) -> None:
        flags: list[ProcessingFlag] = []
        for i, j in zip(self._steps, self._configs):
            if i.checkState(0) == Qt.CheckState.Unchecked:
                continue
            step_name = i.text(0)
            config_dict = {k: v.value for k, v in j.widget_map.items()}
            flags.append(ProcessingFlag(step=step_name, config=config_dict))

        self.processing_update.emit(flags)
