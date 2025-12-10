# Built-Ins
from functools import partial

# PyQt6 Imports
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import pyqtSignal

# Dependencies
import pyqtgraph as pg  # type: ignore
import numpy as np
import cmap

# Local Imports
from .spectrum_edit_window import SpectrumEditWindow
from .valid_colormaps import SequentialColorMap


class SpectralDisplayWidget(QWidget):
    """
    Widget for displaying spectral (or other cube) data.

    Methods
    -------
    set_cube
        Sets the spectral (or other) cube for the plot to display from.
    add_spectrum
        Adds data from the current cube at  `coord` to the plot.
    add_group
        Adds a group of data and emits either a data_added or a bulk_data_added
        signal.
    edit_spectrum
        Edits the spectrum input as an argument.
    handle_reset
        Handles a plot reset signal.


    Signals
    -------
    data_added
        Emits when data is added to the plot"
            - (plot: PlotDataItem, err: ErrorBarItem)
    data_updated
        Emits when data on the plot is updated:
            - (plot: PlotDataItem, err: ErrorBarItem, old_name: str,
            new_name: str)
    data_removed
        Emits when data on the plot is removed from the plot.
            - (name: str)
    bulk_data_added
        Emits when more than one plot data item is added at a time.
            - (plot_list: list[PlotDataItem])
    plot_reset
        Emits when the plot is entirely cleared or reset.
            - (None)
    """

    data_added = pyqtSignal(pg.PlotDataItem, pg.ErrorBarItem)
    data_updated = pyqtSignal(pg.PlotDataItem, pg.ErrorBarItem, str, str)
    data_removed = pyqtSignal(str)
    bulk_data_added = pyqtSignal(list)
    plot_reset = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()

        self.spec_plot = pg.PlotWidget()
        self.spec_legend = self.spec_plot.addLegend()

        self.wvl = np.empty((0, 0, 0), dtype=np.float32)
        self.cube = np.empty((0, 0, 0), dtype=np.float32)
        self._count = 0
        self._editing = False

        layout = QVBoxLayout()
        layout.addWidget(self.spec_plot)
        self.setLayout(layout)

        self.plot_reset.connect(self.handle_reset)

    def set_cube(self, wvl: np.ndarray, data: np.ndarray) -> None:
        if data.ndim != 3:
            return
        self.wvl = wvl
        self.cube = data.astype(np.float32)

    def add_spectrum(
        self,
        coord: tuple[int, int],
        color: pg.Color = pg.Color((200, 200, 200)),
    ) -> str:
        self._count += 1
        spectrum = self.cube[*coord, :]
        spec_item = pg.PlotDataItem(
            self.wvl,
            spectrum,
            pen=pg.mkPen(color=color, width=1),
            clickable=True,
            name=f"SPECTRUM_{self._count:02d}",
        )
        print(type(spec_item.opts["pen"]))
        errbars = pg.ErrorBarItem(x=self.wvl, y=spectrum, height=0)
        errbars.setVisible(False)

        self.spec_plot.addItem(spec_item)
        self.data_added.emit(spec_item, errbars)

        spec_item.sigClicked.connect(
            partial(self.edit_spectrum, spec_item, errbars)
        )

        name = spec_item.name()
        if name is not None:
            return name
        else:
            raise ValueError(f"Spectrum name ({name}) is invalid")

    def add_group(
        self,
        coords: np.ndarray,
        display_mean: bool = True,
        single_color: pg.Color = pg.Color((200, 200, 200)),
        color_map: SequentialColorMap = "crameri:hawaii",
    ) -> str:
        self._count += 1
        if coords.ndim != 2:
            raise ValueError("Group Coordinate Array is the wrong size")
        if coords.shape[1] != 2:
            raise ValueError("Group Coordinate Array is the wrong size")

        spec_array = self.cube[coords[:, 1], coords[:, 0], :]
        mean_spectrum = np.mean(spec_array, axis=0)
        err_spectrum = np.std(spec_array, axis=0, ddof=1)
        spec_item = pg.PlotDataItem(
            self.wvl,
            mean_spectrum,
            pen=pg.mkPen(color=single_color, width=1),
            clickable=True,
            name=f"SPECTRUM_{self._count:02d}",
        )
        if display_mean:
            errbars = pg.ErrorBarItem(
                x=self.wvl, y=mean_spectrum, height=2 * err_spectrum, beam=10
            )

            self.spec_plot.addItem(spec_item)
            self.spec_plot.addItem(errbars)
            self.data_added.emit(spec_item, errbars)

            spec_item.sigClicked.connect(
                partial(self.edit_spectrum, spec_item, errbars)
            )

        else:
            self.spec_legend.setVisible(False)
            spec_list: list[pg.PlotDataItem] = []
            base_cmap = cmap.Colormap(color_map)
            ncolors = spec_array.shape[0]
            cmap_lut = base_cmap.lut(ncolors) * 255
            for i in range(ncolors):
                c = pg.mkColor(tuple(cmap_lut[i, :]))
                _spec = pg.PlotDataItem(
                    self.wvl,
                    spec_array[i, :],
                    pen=pg.mkPen(color=c, width=1),
                    clickable=False,
                    name=f"{spec_item.name()}_{i:04d}",
                )
                self.spec_plot.addItem(_spec)
                spec_list.append(_spec)
            self.bulk_data_added.emit(spec_list)

        name = spec_item.name()
        if name is not None:
            return name
        else:
            raise ValueError("Group Name is None")

    def edit_spectrum(self, plot: pg.PlotDataItem, err: pg.ErrorBarItem):
        if self._editing:
            print(
                "Close the current spectrum edit window to edit another"
                " spectrum."
            )
            return
        self._editing = True
        current_color = plot.opts["pen"]
        _pen = pg.mkPen({"color": "red"})
        plot.setPen(_pen)

        self.edit_win = SpectrumEditWindow(plot)
        self.edit_win.show()

        def rename_spectrum(old_name: str, new_name: str):
            self.spec_legend.removeItem(plot)
            self.spec_legend.addItem(plot, plot.name())
            self.data_updated.emit(plot, err, old_name, new_name)

        self.edit_win.name_changed.connect(rename_spectrum)

        def delete_spectrum():
            # self.state.current_spectra.remove(plot_curve)
            self.spec_plot.removeItem(plot)
            if err is not None:
                self.spec_plot.removeItem(err)
            self.edit_win.close()
            self._editing = False
            self.data_removed.emit(plot.name())

        self.edit_win.spectrum_deleted.connect(delete_spectrum)

        def close_window():
            self.edit_win.close()
            _pen = pg.mkPen(current_color)
            plot.setPen(_pen)
            self._editing = False

        self.edit_win.closed.connect(close_window)

    def handle_reset(self):
        self._count = 0
