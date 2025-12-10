from typing import Literal, TypeAlias

QUALITATIVE_COLOR_MAPS: tuple[str, ...] = (
    "colorbrewer:Dark2",
    "colorbrewer:Accent",
    "colorbrewer:Set2",
)

QualitativeColorMap: TypeAlias = Literal[
    "colorbrewer:Dark2",
    "colorbrewer:Accent",
    "colorbrewer:Set2",
    "seaborn:tab10_colorblind",
]

SEQUENTIAL_COLOR_MAPS: tuple[str, ...] = (
    "crameri:hawaii",
    "crameri:batlow",
    "crameri:lipari",
    "crameri:tokyo",
    "seaborn:rocket",
)

SequentialColorMap: TypeAlias = Literal[
    "crameri:hawaii",
    "crameri:batlow",
    "crameri:lipari",
    "crameri:tokyo",
    "seaborn:rocket",
]
