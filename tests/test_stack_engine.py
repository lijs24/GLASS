from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from glass.engine.contracts import (
    CombinePolicy,
    DQFlag,
    DQMask,
    OutputMapPolicy,
    RejectionPolicy,
    StackRequest,
    TileWindow,
)
from glass.engine.stack_engine import CPUStackEngine


@dataclass(slots=True)
class ArrayImageSource:
    data: np.ndarray
    dq: np.ndarray | None = None
    path: Path | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    width: int = 0
    height: int = 0
    channels: int = 1
    dtype: str = "float32"

    def __post_init__(self):
        self.data = np.asarray(self.data, dtype=np.float32)
        self.height, self.width = self.data.shape
        if self.dq is None:
            self.dq = np.zeros_like(self.data, dtype=np.uint32)
        else:
            self.dq = np.asarray(self.dq, dtype=np.uint32)

    def read_tile(self, window: TileWindow, dtype: Any = np.float32) -> np.ndarray:
        return np.asarray(self.data[window.as_slices()], dtype=dtype)

    def read_mask_tile(self, window: TileWindow) -> DQMask:
        return DQMask(np.asarray(self.dq[window.as_slices()], dtype=np.uint32).copy())


def _sources(frames: list[np.ndarray], dq: list[np.ndarray] | None = None) -> dict[str, ArrayImageSource]:
    masks = dq or [None] * len(frames)
    return {f"f{i}": ArrayImageSource(frame, mask) for i, (frame, mask) in enumerate(zip(frames, masks))}


def _request(
    frame_count: int,
    combine: CombinePolicy | None = None,
    rejection: RejectionPolicy | None = None,
    maps: OutputMapPolicy | None = None,
    weights: dict[str, float] | None = None,
) -> StackRequest:
    return StackRequest(
        frame_ids=tuple(f"f{i}" for i in range(frame_count)),
        source_kind="light",
        combine=combine or CombinePolicy(),
        rejection=rejection or RejectionPolicy(),
        output_maps=maps or OutputMapPolicy(variance=True, dq=True),
        weights=weights or {},
    )


def test_cpu_stack_engine_tiled_matches_full_frame_mean():
    rng = np.random.default_rng(42)
    frames = [rng.normal(loc=i, scale=0.5, size=(13, 17)).astype(np.float32) for i in range(4)]
    request = _request(len(frames))
    sources = _sources(frames)

    full = CPUStackEngine(tile_size=64).stack(request, sources)
    tiled = CPUStackEngine(tile_size=5).stack(request, sources)

    assert np.allclose(tiled.master, full.master)
    assert np.allclose(tiled.weight_map, full.weight_map)
    assert np.allclose(tiled.coverage_map, full.coverage_map)
    assert np.allclose(tiled.variance_map, full.variance_map)
    assert tiled.metrics["valid_samples"] == full.metrics["valid_samples"]


def test_cpu_stack_engine_weighted_mean_consumes_dq_masks():
    frames = [
        np.ones((3, 3), dtype=np.float32),
        np.ones((3, 3), dtype=np.float32) * 3,
    ]
    dq = np.zeros((3, 3), dtype=np.uint32)
    dq[0, 0] = int(DQFlag.NO_DATA)
    request = _request(
        len(frames),
        combine=CombinePolicy(method="weighted_mean", accumulator_dtype="float64"),
        weights={"f0": 1.0, "f1": 3.0},
    )

    result = CPUStackEngine(tile_size=2).stack(request, _sources(frames, [np.zeros_like(dq), dq]))

    assert result.master[0, 0] == pytest.approx(1.0)
    assert np.allclose(result.master[1:, 1:], 2.5)
    assert result.weight_map[0, 0] == pytest.approx(1.0)
    assert result.coverage_map[0, 0] == pytest.approx(1.0)
    assert result.dq_mask is not None
    assert result.dq_mask.count(DQFlag.NO_DATA) == 0


def test_cpu_stack_engine_median_combine():
    frames = [
        np.ones((4, 4), dtype=np.float32),
        np.ones((4, 4), dtype=np.float32) * 100,
        np.ones((4, 4), dtype=np.float32) * 3,
    ]
    request = _request(len(frames), combine=CombinePolicy(method="median"))

    result = CPUStackEngine(tile_size=3).stack(request, _sources(frames))

    assert np.allclose(result.master, 3.0)
    assert np.all(result.coverage_map == 3)


@pytest.mark.parametrize("method", ["sigma", "winsorized_sigma"])
def test_cpu_stack_engine_rejects_high_outlier(method):
    frames = [np.ones((5, 6), dtype=np.float32) for _ in range(4)]
    frames.append(np.ones((5, 6), dtype=np.float32) * 100)
    request = _request(
        len(frames),
        rejection=RejectionPolicy(method=method, high_sigma=1.0, max_reject_fraction=0.5),
    )

    result = CPUStackEngine(tile_size=4).stack(request, _sources(frames))

    assert np.allclose(result.master, 1.0)
    assert np.all(result.coverage_map == 4)
    assert np.sum(result.low_rejection_map) == 0
    assert np.sum(result.high_rejection_map) == 30
    assert result.dq_mask is not None
    assert result.dq_mask.count(DQFlag.HIGH_REJECTED) == 30


def test_cpu_stack_engine_minmax_rejection_keeps_middle_samples():
    frames = [
        np.ones((2, 2), dtype=np.float32),
        np.ones((2, 2), dtype=np.float32) * 2,
        np.ones((2, 2), dtype=np.float32) * 3,
        np.ones((2, 2), dtype=np.float32) * 100,
    ]
    request = _request(
        len(frames),
        rejection=RejectionPolicy(method="minmax", min_samples=2, max_reject_fraction=0.5),
    )

    result = CPUStackEngine(tile_size=1).stack(request, _sources(frames))

    assert np.allclose(result.master, 2.5)
    assert np.all(result.coverage_map == 2)
    assert np.sum(result.low_rejection_map) == 4
    assert np.sum(result.high_rejection_map) == 4


def test_cpu_stack_engine_rejects_shape_mismatch():
    sources = _sources(
        [
            np.ones((2, 2), dtype=np.float32),
            np.ones((2, 3), dtype=np.float32),
        ]
    )

    with pytest.raises(ValueError, match="shape mismatch"):
        CPUStackEngine(tile_size=2).stack(_request(2), sources)
