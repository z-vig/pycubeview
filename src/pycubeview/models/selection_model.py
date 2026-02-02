# PySide6 Imports
from PySide6.QtCore import QObject, Signal


class SelectionModel(QObject):
    cache_reset = Signal()
    measurement_picked = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.n_meas_plots: int = 0
        self.n_image_points: int = 0

    def meas_plot_added(self):
        self.n_meas_plots += 1

    def image_point_added(self):
        self.n_image_points += 1

    def initiate_reset(self):
        self.n_image_points = 0
        self.n_meas_plots = 0
        self.cache_reset.emit()
