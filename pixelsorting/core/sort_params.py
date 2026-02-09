from dataclasses import dataclass, field
from enum import Enum


class SortDirection(Enum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class SortKey(Enum):
    BRIGHTNESS = "brightness"
    HUE = "hue"
    SATURATION = "saturation"
    INTENSITY = "intensity"
    MINIMUM = "minimum"
    RED = "red"
    GREEN = "green"
    BLUE = "blue"


class IntervalMode(Enum):
    THRESHOLD = "threshold"
    RANDOM = "random"
    EDGES = "edges"
    WAVES = "waves"
    NONE = "none"


@dataclass
class SortParams:
    direction: SortDirection = SortDirection.HORIZONTAL
    angle: float = 0.0
    sort_key: SortKey = SortKey.BRIGHTNESS
    interval_mode: IntervalMode = IntervalMode.THRESHOLD
    lower_threshold: float = 0.25
    upper_threshold: float = 0.8
    pixel_size: int = 1
    span_min: int = 1
    span_max: int = 0  # 0 = unlimited
    jitter: int = 0
    reverse: bool = False

    def copy(self) -> "SortParams":
        return SortParams(
            direction=self.direction,
            angle=self.angle,
            sort_key=self.sort_key,
            interval_mode=self.interval_mode,
            lower_threshold=self.lower_threshold,
            upper_threshold=self.upper_threshold,
            pixel_size=self.pixel_size,
            span_min=self.span_min,
            span_max=self.span_max,
            jitter=self.jitter,
            reverse=self.reverse,
        )
