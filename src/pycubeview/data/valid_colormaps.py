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
    "tol:muted_alt",
]

SEQUENTIAL_COLOR_MAPS: tuple[str, ...] = (
    "crameri:hawaii",
    "crameri:batlow",
    "crameri:lipari",
    "crameri:tokyo",
    "seaborn:rocket",
    "colorbrewer:BuGn",
    "crameri:grayc",
    "matlab:gray",
)

SequentialColorMap: TypeAlias = Literal[
    "crameri:hawaii",
    "crameri:batlow",
    "crameri:lipari",
    "crameri:tokyo",
    "seaborn:rocket",
    "colorbrewer:BuGn",
    "crameri:grayc",
    "matlab:gray",
]
