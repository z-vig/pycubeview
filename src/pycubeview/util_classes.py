# Built-Ins
from typing import Literal
from dataclasses import dataclass


@dataclass
class PixelValue:
    v: float = 0.0
    r: float = 0.0
    g: float = 0.0
    b: float = 0.0
    pixel_type: Literal["single"] | Literal["rgb"] = "single"

    @classmethod
    def null(cls) -> "PixelValue":
        return cls(-999.0, -999.0, -999.0, -999.0)
