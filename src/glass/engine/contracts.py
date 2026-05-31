from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntFlag
from pathlib import Path
from typing import Any, Literal, Protocol, runtime_checkable

import numpy as np


CombineMethod = Literal["mean", "median", "sum", "weighted_mean", "drizzle"]
AccumulatorDType = Literal["float32", "float64"]
RejectionMethod = Literal[
    "none",
    "minmax",
    "percentile",
    "sigma",
    "mad",
    "median_sigma",
    "winsorized_sigma",
]


@dataclass(frozen=True, slots=True)
class TileWindow:
    """Rectangular pixel window used by tiled and resident execution paths."""

    y0: int
    y1: int
    x0: int
    x1: int
    channel: int | None = None
    overlap: int = 0
    origin_y: int = 0
    origin_x: int = 0

    def __post_init__(self) -> None:
        if self.y0 < 0 or self.x0 < 0:
            raise ValueError("tile coordinates must be non-negative")
        if self.y1 <= self.y0 or self.x1 <= self.x0:
            raise ValueError("tile end coordinates must be greater than start coordinates")
        if self.overlap < 0:
            raise ValueError("tile overlap must be non-negative")
        if self.channel is not None and self.channel < 0:
            raise ValueError("tile channel must be non-negative when provided")

    @property
    def height(self) -> int:
        return self.y1 - self.y0

    @property
    def width(self) -> int:
        return self.x1 - self.x0

    @property
    def shape(self) -> tuple[int, int]:
        return self.height, self.width

    def as_slices(self) -> tuple[slice, slice]:
        return slice(self.y0, self.y1), slice(self.x0, self.x1)

    def with_overlap_clipped(self, width: int, height: int) -> "TileWindow":
        if self.overlap == 0:
            return self
        return TileWindow(
            y0=max(0, self.y0 - self.overlap),
            y1=min(int(height), self.y1 + self.overlap),
            x0=max(0, self.x0 - self.overlap),
            x1=min(int(width), self.x1 + self.overlap),
            channel=self.channel,
            overlap=0,
            origin_y=self.y0,
            origin_x=self.x0,
        )


class DQFlag(IntFlag):
    VALID = 0
    NO_DATA = 1 << 0
    SATURATED = 1 << 1
    HOT_PIXEL = 1 << 2
    COLD_PIXEL = 1 << 3
    DEAD_PIXEL = 1 << 4
    COSMETIC_CORRECTED = 1 << 5
    WARP_EDGE = 1 << 6
    LOCAL_NORMALIZATION_EXCLUDED = 1 << 7
    LOW_REJECTED = 1 << 8
    HIGH_REJECTED = 1 << 9


@dataclass(slots=True)
class DQMask:
    """Mutable data-quality bitfield for a single image tile."""

    data: np.ndarray

    def __post_init__(self) -> None:
        if self.data.dtype != np.uint32:
            self.data = np.asarray(self.data, dtype=np.uint32)

    @classmethod
    def empty(cls, shape: tuple[int, int]) -> "DQMask":
        return cls(np.zeros(shape, dtype=np.uint32))

    def copy(self) -> "DQMask":
        return DQMask(self.data.copy())

    def mark(self, flag: DQFlag, where: np.ndarray | None = None) -> "DQMask":
        flag_value = np.uint32(int(flag))
        if flag_value == 0:
            return self
        if where is None:
            self.data |= flag_value
        else:
            self.data[np.asarray(where, dtype=bool)] |= flag_value
        return self

    def has_flag(self, flag: DQFlag) -> np.ndarray:
        return (self.data & np.uint32(int(flag))) != 0

    def count(self, flag: DQFlag) -> int:
        if flag == DQFlag.VALID:
            return int(np.count_nonzero(self.data == 0))
        return int(np.count_nonzero(self.has_flag(flag)))

    def summary(self) -> dict[str, int]:
        summary = {"valid": self.count(DQFlag.VALID)}
        for flag in DQFlag:
            if flag == DQFlag.VALID:
                continue
            count = self.count(flag)
            if count:
                summary[flag.name.lower()] = count
        return summary


@runtime_checkable
class ImageSource(Protocol):
    path: Path | str | None
    width: int
    height: int
    channels: int
    dtype: str
    metadata: dict[str, Any]

    def read_tile(self, window: TileWindow, dtype: Any = np.float32) -> np.ndarray:
        ...

    def read_mask_tile(self, window: TileWindow) -> DQMask:
        ...


@dataclass(slots=True)
class TransformResult:
    tile: np.ndarray
    dq: DQMask
    metrics: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class FrameTransform(Protocol):
    name: str

    def prepare(self, frame_meta: Any, context: dict[str, Any]) -> Any:
        ...

    def apply_tile(
        self,
        tile: np.ndarray,
        window: TileWindow,
        state: Any,
        dq: DQMask | None = None,
    ) -> TransformResult:
        ...


@dataclass(frozen=True, slots=True)
class IdentityTransform:
    name: str = "identity"

    def prepare(self, frame_meta: Any, context: dict[str, Any]) -> None:
        return None

    def apply_tile(
        self,
        tile: np.ndarray,
        window: TileWindow,
        state: Any,
        dq: DQMask | None = None,
    ) -> TransformResult:
        del window, state
        mask = dq.copy() if dq is not None else DQMask.empty(tuple(tile.shape[-2:]))
        return TransformResult(tile=np.asarray(tile), dq=mask, metrics={})


@dataclass(frozen=True, slots=True)
class CombinePolicy:
    method: CombineMethod = "mean"
    accumulator_dtype: AccumulatorDType = "float32"


@dataclass(frozen=True, slots=True)
class RejectionPolicy:
    method: RejectionMethod = "none"
    iterations: int = 1
    low_sigma: float = 3.0
    high_sigma: float = 3.0
    min_samples: int = 3
    max_reject_fraction: float = 0.5

    def __post_init__(self) -> None:
        if self.iterations < 0:
            raise ValueError("rejection iterations must be non-negative")
        if self.min_samples < 1:
            raise ValueError("rejection min_samples must be at least 1")
        if not 0.0 <= self.max_reject_fraction <= 1.0:
            raise ValueError("max_reject_fraction must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class OutputMapPolicy:
    coverage: bool = True
    weight: bool = True
    variance: bool = False
    low_rejection: bool = True
    high_rejection: bool = True
    dq: bool = False


@dataclass(frozen=True, slots=True)
class StackRequest:
    frame_ids: tuple[str, ...]
    source_kind: Literal["bias", "dark", "flat", "light", "unknown"]
    combine: CombinePolicy = field(default_factory=CombinePolicy)
    rejection: RejectionPolicy = field(default_factory=RejectionPolicy)
    output_maps: OutputMapPolicy = field(default_factory=OutputMapPolicy)
    preprocess: tuple[str, ...] = ()
    normalization: str | None = None
    weights: dict[str, float] = field(default_factory=dict)
    grouping_key: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.frame_ids:
            raise ValueError("StackRequest requires at least one frame_id")
