from pathlib import Path
from typing import TypeAlias, Literal, TypeGuard
from enum import Enum, auto, StrEnum

PathLike: TypeAlias = Path | str

MeasurementFileTypes: TypeAlias = Literal[".wvl", ".hdr", ".txt", ".csv"]
measurement_file_types: list[MeasurementFileTypes] = [
    ".wvl",
    ".hdr",
    ".txt",
    ".csv",
]


def is_valid_measurement_file(value: str) -> TypeGuard[MeasurementFileTypes]:
    return value in measurement_file_types


CubeFileTypes: TypeAlias = Literal[
    ".spcub", ".geospcub", ".bsq", ".bil", ".img", ".tif"
]
cube_file_types: list[CubeFileTypes] = [
    ".spcub",
    ".geospcub",
    ".bsq",
    ".bil",
    ".img",
    ".tif",
]


def is_valid_cube_file(value: str) -> TypeGuard[CubeFileTypes]:
    return value in cube_file_types


class WidgetMode(Enum):
    COLLECT = auto()
    EDIT = auto()
    LASSO = auto()
    LINE = auto()


SaveMode: TypeAlias = Literal["Group", "Individual"]
save_modes: list[SaveMode] = ["Group", "Individual"]


def is_valid_save_mode(value: str) -> TypeGuard[SaveMode]:
    return value in save_modes


class SpectralProcessingStep(StrEnum):
    OUTLIER_REMOVAL = "OUTLIER_REMOVAL"
    FILTERING = "FILTERING"
    CONTINUUM_REMOVAL = "CONTINUUM_REMOVAL"


SpectralProcessingStepLiteral: TypeAlias = Literal[
    "OUTLIER_REMOVAL", "FILTERING", "CONTINUUM_REMOVAL"
]
