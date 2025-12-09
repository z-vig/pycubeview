# Built-Ins
from typing import Literal
from dataclasses import dataclass


@dataclass
class PixelValue:
    v: int = 0
    r: int = 0
    g: int = 0
    b: int = 0
    pixel_type: Literal["single"] | Literal["rgb"] = "single"

    @classmethod
    def null(cls) -> "PixelValue":
        return cls(-999, -999, -999, -999)
