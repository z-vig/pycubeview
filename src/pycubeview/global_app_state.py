# Built-Ins
from pathlib import Path
from dataclasses import dataclass
from pycubeview.custom_types import WidgetMode


@dataclass
class AppState:
    base_fp: Path = Path.home()
    current_image_size: tuple[int, int] = (0, 0)
    widget_mode: WidgetMode = WidgetMode.COLLECT
