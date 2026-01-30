# Dependencies
import spectralio as sio
import numpy as np

# Local Imports
from pycubeview.custom_types import Path, CubeFileTypes
from pycubeview.cubeview_protocols import CubeViewMainWindowProtocol
from .base_controller import BaseController
import pycubeview.services.read_cube as read_cube
import pycubeview.services.read_measurement_axis_label as read_lbl

# PySide6 Imports
from PySide6.QtWidgets import QFileDialog


class FileController(BaseController):
    def __init__(self, window: CubeViewMainWindowProtocol):
        self._window = window
        super().__init__()

    def _build_actions(self):
        self.base_fp_action = self.cat.set_base_fp.build(
            self._window.central_widget, self
        )
        self.open_cube_action = self.cat.open_cube.build(
            self._window.central_widget, self
        )
        self.open_image_action = self.cat.open_image.build(
            self._window.central_widget, self
        )
        self.reset_data_action = self.cat.reset_data.build(
            self._window.central_widget, self
        )

    def _install_actions(self) -> None:
        self._window.meas_menu.addAction(self.open_cube_action)
        self._window.image_menu.addAction(self.open_image_action)
        self._window.file_menu.addAction(self.base_fp_action)
        self._window.file_menu.addAction(self.reset_data_action)

    def _connect_signals(self) -> None:
        return

    def _open_cube_dialog(self) -> Path | None:
        cube_fp_str, fp_type = QFileDialog.getOpenFileName(
            caption="Select Cube Data",
            filter=(
                "Spectral Cube Files (*.spcub *.geospcub);;"
                "Rasterio-Compatible Files (*.bsq *.img *.tif)"
            ),
            dir=str(self.app_state.base_fp),
        )

        if cube_fp_str == "":
            return None

        return Path(cube_fp_str)

    def _open_meas_dialog(self) -> Path | None:
        wvl_fp_str, fp_type = QFileDialog.getOpenFileName(
            caption="Select Wavelength (or other context) Data",
            filter=(
                "Wavelength File (*.wvl);;ENVI Header File (*.hdr);;"
                "Text-Based Files (*.txt *.csv)"
            ),
            dir=str(self.app_state.base_fp),
        )
        if wvl_fp_str == "":
            return None
        return Path(wvl_fp_str)

    def open_image(
        self,
        *,
        set_image: bool = True,
        fp: Path | None = None,
    ) -> tuple[Path | None, CubeFileTypes | None]:
        if fp is None:
            newfp = self._open_cube_dialog()
            if not newfp:
                return (None, None)
        else:
            newfp = fp
        arr, suffix = read_cube.open_cube(newfp)
        imsize = (arr.shape[0], arr.shape[1])
        if set_image and self._check_imsize(imsize):
            self._window.add_image_display(arr)
        return newfp, suffix

    def open_meas(self) -> np.ndarray | None:
        fp = self._open_meas_dialog()
        if fp is None:
            return None
        arr = read_lbl.open_meas(fp)
        return arr

    def open_cube(self, *, fp: Path | None = None) -> None:
        fp, suffix = self.open_image(set_image=False, fp=fp)
        if fp is None or suffix is None:
            return None
        if suffix in (".spcub", ".geospcub"):
            if suffix == ".spcub":
                cube = sio.read_spec3D(fp, kind="spcub")
            elif suffix == ".geospcub":
                cube = sio.read_spec3D(fp, kind="geospcub")
            else:
                raise ValueError(f"Invalid file type: {suffix}")

            arr = cube.load_raster()
            imsize = (arr.shape[0], arr.shape[1])
            if self._check_imsize(imsize):
                self._window.add_meas_display(arr, cube.wavelength.asarray())
        else:
            arr, _ = read_cube.open_cube(fp)
            imsize = (arr.shape[0], arr.shape[1])
            lbl = self.open_meas()
            if lbl is None:
                return None
            if self._check_imsize(imsize):
                self._window.add_meas_display(arr, lbl)

    def set_base_fp(self, *, fp: Path | None = None) -> None:
        if fp is None:
            newfp = QFileDialog.getExistingDirectory(
                caption="Select Base Directory",
                dir=str(self.app_state.base_fp),
            )
            if not newfp:
                return None
        else:
            newfp = str(fp)
        self.app_state.base_fp = Path(newfp)
        return None

    def reset_data(self) -> None:
        self._window.reset_docks()

    def _check_imsize(self, new_imsize: tuple[int, int]) -> bool:
        if self.app_state.current_image_size == (0, 0):
            self.app_state.current_image_size = new_imsize
            return True
        elif self.app_state.current_image_size != new_imsize:
            print(
                "Selected dataset does not have the same pixel dimensions "
                "as your first dataset."
            )
            return False
        return True
