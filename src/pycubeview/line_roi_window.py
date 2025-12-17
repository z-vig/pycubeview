# PySide6 Imports
from PySide6 import QtWidgets as qtw
from PySide6.QtCore import Signal
from PySide6.QtGui import QAction

# Dependencies
import pyqtgraph as pg  # type: ignore
import cmap
import numpy as np

# Local Imports
from .valid_colormaps import SequentialColorMap
from .spectral_display_widget import SpectralDisplayWidget


class LineRoiWindow(qtw.QMainWindow):
    updated = Signal()
    closed = Signal()

    def __init__(
        self,
        cmap_name: SequentialColorMap = "crameri:hawaii",
    ):
        super().__init__()

        line_roi_cmap = cmap.Colormap(cmap_name)

        layout = qtw.QVBoxLayout()

        self.display_widget = SpectralDisplayWidget()
        self.profile_widget = pg.PlotWidget()
        self.profile_plot = pg.PlotDataItem()
        self.profile_scatter = pg.ScatterPlotItem()

        self.profile_widget.addItem(self.profile_plot)
        self.profile_widget.addItem(self.profile_scatter)

        self.xdata = np.ndarray(0, dtype=np.float32)
        self.line_cmap = line_roi_cmap

        self.profile_indicator = pg.InfiniteLine(
            pos=0, pen=pg.mkPen(color="r", width=2), movable=True
        )
        self.profile_indicator.sigDragged.connect(self.update_profile)
        self.display_widget.spec_plot.addItem(self.profile_indicator)

        self.name_edit = qtw.QLineEdit(parent=self)
        self.update_button = qtw.QPushButton(text="Update Plot")

        self.update_button.clicked.connect(self.update_plot)

        self.current_display_roi: list[pg.PlotDataItem] = []
        self.current_display_roi_array: np.ndarray = np.empty((0, 0))

        layout.addWidget(self.name_edit)
        layout.addWidget(self.display_widget)
        layout.addWidget(self.profile_widget)
        layout.addWidget(self.update_button)

        main_widget = qtw.QWidget()
        main_widget.setLayout(layout)

        cbar = pg.GradientLegend([50, 50], [50, 50])
        cbar.setColorMap(line_roi_cmap.to_pyqtgraph())
        self.display_widget.spec_plot.addItem(cbar)

        # ---- Adding Toolbar ----
        toolbar = qtw.QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        # Toolbar actions
        save_action = QAction("Save All", self)
        save_action.setStatusTip(
            "Saves Linear ROI spectra one-by-one to a folder"
        )
        save_action.triggered.connect(self.display_widget.save_plot)
        toolbar.addAction(save_action)

        self.name_edit.returnPressed.connect(self.set_name)
        self.display_widget.bulk_data_added.connect(self.set_current_roi)

        self.setCentralWidget(main_widget)
        self.setWindowTitle("Linear ROI Display")

    def update_plot(self, _pushed: bool) -> None:
        self.display_widget.save_cache = []
        self.updated.emit()

    def set_current_roi(self, spec_list: list[pg.PlotDataItem]) -> None:
        self.current_display_roi = spec_list
        self.xdata = spec_list[0].xData
        _name = spec_list[0].name()
        if _name is None:
            return
        spec_plot_item = self.display_widget.spec_plot.getPlotItem()
        if spec_plot_item is None:
            return
        spec_plot_item.setTitle(_name[:-5])
        if self.xdata is None:
            return
        arr_size = (len(self.current_display_roi), self.xdata.size)
        self.current_display_roi_array = np.empty(arr_size)
        for n, i in enumerate(spec_list):
            self.current_display_roi_array[n, :] = i.yData
        mean_wvl = np.mean(self.xdata)
        self.profile_indicator.setPos(mean_wvl)

    def set_name(self):
        spec_plot_item = self.display_widget.spec_plot.getPlotItem()
        if spec_plot_item is None:
            return
        group_name = self.name_edit.text()
        spec_plot_item.setTitle(group_name)
        for n, spec in enumerate(self.display_widget.save_cache):
            spec.name = f"{group_name}_{n:04d}"

    def update_profile(self) -> None:
        pos = self.profile_indicator.getPos()
        xpos: float = pos[0]
        if self.xdata is None:
            return
        if xpos < self.xdata.min():
            self.profile_indicator.setPos(self.xdata.min())
            return
        if xpos > self.xdata.max():
            self.profile_indicator.setPos(self.xdata.max())
            return
        profile_x = np.arange(
            0, self.current_display_roi_array.shape[0], dtype=int
        )
        idx = np.argmin(np.abs(self.xdata - xpos))
        profile_y = self.current_display_roi_array[:, idx]
        self.profile_plot.setData(profile_x, profile_y)
        brush_list = []
        ncolors = profile_x.shape[0]
        cmap_lut = self.line_cmap.lut(ncolors) * 255
        for i in range(ncolors):
            c = pg.mkColor(tuple(cmap_lut[i, :]))
            brush_list.append(pg.mkBrush(color=c))
        self.profile_scatter.setData(
            x=profile_x, y=profile_y, brush=brush_list
        )
        self.profile_plot.setVisible(True)

    def closeEvent(self, a0):
        self.closed.emit()
        if a0 is not None:
            a0.accept()
