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
import glass.engine.stack_engine as stack_engine_module
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


def test_cpu_stack_engine_mean_no_rejection_fast_path_avoids_np_stack(monkeypatch):
    frames = [
        np.ones((4, 5), dtype=np.float32),
        np.ones((4, 5), dtype=np.float32) * 3.0,
        np.ones((4, 5), dtype=np.float32) * 5.0,
    ]

    def fail_stack(*args, **kwargs):
        raise AssertionError("mean/no-rejection StackEngine path should stream without np.stack")

    monkeypatch.setattr(np, "stack", fail_stack)
    result = CPUStackEngine(tile_size=2).stack(_request(len(frames)), _sources(frames))

    assert np.allclose(result.master, 3.0)
    assert np.all(result.coverage_map == 3)
    assert result.metrics["execution_path"] == "streaming_mean_no_rejection"
    assert result.dq_provenance["execution_path"] == "streaming_mean_no_rejection"
    assert result.dq_provenance["result_contract"]["passed"] is True


def test_cpu_stack_engine_full_frame_mean_hint_avoids_tile_iterator(monkeypatch):
    @dataclass(slots=True)
    class FiniteOnlySource(ArrayImageSource):
        mask_from_finite_only: bool = True

        def read_mask_tile(self, window: TileWindow) -> DQMask:
            raise AssertionError("finite-only full-frame source should not allocate a DQ mask")

    frames = [
        np.ones((3, 4), dtype=np.float32),
        np.ones((3, 4), dtype=np.float32) * 5.0,
    ]
    sources = {f"f{i}": FiniteOnlySource(frame) for i, frame in enumerate(frames)}

    def fail_iter_tiles(*args, **kwargs):
        raise AssertionError("full-frame mean hint should not use tiled iteration")

    monkeypatch.setattr(stack_engine_module, "iter_tiles", fail_iter_tiles)
    request = StackRequest(
        frame_ids=("f0", "f1"),
        source_kind="bias",
        combine=CombinePolicy(method="mean", accumulator_dtype="float64"),
        rejection=RejectionPolicy(method="none", iterations=0, min_samples=1),
        output_maps=OutputMapPolicy(
            coverage=False,
            weight=False,
            variance=False,
            low_rejection=False,
            high_rejection=False,
            dq=False,
        ),
        metadata={"full_frame_fast_path": True},
    )

    result = CPUStackEngine(tile_size=1).stack(request, sources)

    assert np.allclose(result.master, 3.0)
    assert result.coverage_map is None
    assert result.weight_map is None
    assert result.dq_mask is None
    assert result.metrics["execution_path"] == "full_frame_mean_no_rejection"
    assert result.dq_provenance["execution_path"] == "full_frame_mean_no_rejection"
    assert result.dq_provenance["input_samples"] == 24
    assert result.dq_provenance["input_valid_samples_before_rejection"] == 24
    assert result.dq_provenance["result_contract"]["passed"] is True


def test_cpu_stack_engine_streaming_mean_tracks_dq_and_nonfinite_samples():
    frames = [
        np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32),
        np.array([[5.0, np.nan], [7.0, 8.0]], dtype=np.float32),
    ]
    dq = np.zeros((2, 2), dtype=np.uint32)
    dq[1, 0] = int(DQFlag.HOT_PIXEL)
    request = _request(
        len(frames),
        combine=CombinePolicy(method="weighted_mean", accumulator_dtype="float64"),
        weights={"f0": 1.0, "f1": 3.0},
    )

    result = CPUStackEngine(tile_size=1).stack(request, _sources(frames, [np.zeros_like(dq), dq]))

    assert result.master[0, 0] == pytest.approx(4.0)
    assert result.master[0, 1] == pytest.approx(2.0)
    assert result.master[1, 0] == pytest.approx(3.0)
    assert result.master[1, 1] == pytest.approx(7.0)
    assert result.weight_map[1, 0] == pytest.approx(1.0)
    assert result.coverage_map[1, 0] == pytest.approx(1.0)
    assert result.dq_provenance["input_samples"] == 8
    assert result.dq_provenance["input_valid_samples_before_rejection"] == 6
    assert result.dq_provenance["input_invalid_samples_before_rejection"] == 2
    assert result.dq_provenance["input_flagged_samples"] == 1
    assert result.dq_provenance["input_nonfinite_samples"] == 1
    assert result.dq_provenance["input_dq_flag_counts"]["hot_pixel"] == 1
    assert result.dq_provenance["result_contract"]["passed"] is True


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


def test_cpu_stack_engine_records_dq_provenance():
    frames = [
        np.ones((2, 2), dtype=np.float32),
        np.ones((2, 2), dtype=np.float32) * 3,
    ]
    dq0 = np.zeros((2, 2), dtype=np.uint32)
    dq1 = np.zeros((2, 2), dtype=np.uint32)
    dq0[0, 0] = int(DQFlag.HOT_PIXEL)
    dq1[0, 0] = int(DQFlag.NO_DATA)
    dq0[0, 1] = int(DQFlag.SATURATED)
    frames[1][1, 0] = np.nan
    request = _request(len(frames), maps=OutputMapPolicy(coverage=True, dq=True))

    result = CPUStackEngine(tile_size=1).stack(request, _sources(frames, [dq0, dq1]))

    provenance = result.dq_provenance
    assert provenance["schema_version"] == 1
    assert provenance["input_samples"] == 8
    assert provenance["input_valid_samples_before_rejection"] == 4
    assert provenance["input_invalid_samples_before_rejection"] == 4
    assert provenance["input_flagged_samples"] == 3
    assert provenance["input_nonfinite_samples"] == 1
    assert provenance["input_dq_flag_counts"]["hot_pixel"] == 1
    assert provenance["input_dq_flag_counts"]["no_data"] == 1
    assert provenance["input_dq_flag_counts"]["saturated"] == 1
    assert provenance["output_coverage_zero_pixels"] == 1
    assert provenance["output_dq_summary"]["no_data"] == 1
    assert result.coverage_map[0, 0] == pytest.approx(0.0)
    assert result.coverage_map[0, 1] == pytest.approx(1.0)
    assert result.coverage_map[1, 0] == pytest.approx(1.0)
    assert result.metrics["input_valid_samples"] == 4
    assert result.metrics["input_invalid_samples"] == 4
    assert result.metrics["rejected_samples"] == 0


def test_cpu_stack_engine_weighted_variance_map():
    frames = [
        np.ones((2, 2), dtype=np.float32),
        np.ones((2, 2), dtype=np.float32) * 3.0,
    ]
    request = _request(
        len(frames),
        combine=CombinePolicy(method="weighted_mean", accumulator_dtype="float64"),
        weights={"f0": 1.0, "f1": 3.0},
    )

    result = CPUStackEngine(tile_size=2).stack(request, _sources(frames))

    assert np.allclose(result.master, 2.5)
    assert np.allclose(result.variance_map, 0.75)
    assert result.metrics["variance_mean"] == pytest.approx(0.75)


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


def test_cpu_stack_engine_winsorized_sigma_is_distinct_for_low_sample_outlier():
    frames = [np.ones((2, 2), dtype=np.float32) for _ in range(3)]
    frames.append(np.ones((2, 2), dtype=np.float32) * 12.0)
    rejection = RejectionPolicy(
        method="sigma",
        low_sigma=2.4,
        high_sigma=2.4,
        min_samples=3,
        max_reject_fraction=0.5,
    )
    winsorized_rejection = RejectionPolicy(
        method="winsorized_sigma",
        low_sigma=2.4,
        high_sigma=2.4,
        min_samples=3,
        max_reject_fraction=0.5,
    )

    sigma = CPUStackEngine(tile_size=1).stack(
        _request(len(frames), rejection=rejection), _sources(frames)
    )
    winsorized = CPUStackEngine(tile_size=1).stack(
        _request(len(frames), rejection=winsorized_rejection), _sources(frames)
    )

    assert np.allclose(sigma.master, 3.75)
    assert np.sum(sigma.high_rejection_map) == 0
    assert sigma.metrics["rejection_scale_estimator"] == "median_center_standard_deviation_scale"
    assert np.allclose(winsorized.master, 1.0)
    assert np.all(winsorized.coverage_map == 3)
    assert np.sum(winsorized.high_rejection_map) == 4
    assert winsorized.metrics["high_rejected"] == 4
    assert (
        winsorized.metrics["rejection_scale_estimator"]
        == "median_iqr_winsorized_standard_deviation_scale"
    )
    assert winsorized.dq_provenance["rejection_policy"]["method"] == "winsorized_sigma"
    assert winsorized.dq_provenance["rejection_policy"]["winsorized"] is True
    assert (
        winsorized.dq_provenance["rejection_policy"]["winsorization_scale"]
        == "iqr_sigma_with_standard_deviation_fallback"
    )


def test_cpu_stack_engine_invalid_input_samples_are_not_rejections():
    frames = [np.ones((2, 2), dtype=np.float32) for _ in range(5)]
    frames[-1] = np.ones((2, 2), dtype=np.float32) * 100.0
    frames[2][0, 0] = np.nan
    dq = [np.zeros((2, 2), dtype=np.uint32) for _ in frames]
    dq[1][1, 1] = int(DQFlag.HOT_PIXEL)
    request = _request(
        len(frames),
        rejection=RejectionPolicy(method="sigma", high_sigma=1.0, max_reject_fraction=0.5),
        maps=OutputMapPolicy(coverage=True, low_rejection=True, high_rejection=True, dq=True),
    )

    result = CPUStackEngine(tile_size=1).stack(request, _sources(frames, dq))
    contract = result.dq_provenance["result_contract"]
    checks = {item["name"]: item for item in contract["checks"]}

    assert contract["passed"] is True
    assert result.dq_provenance["input_samples"] == 20
    assert result.dq_provenance["input_valid_samples_before_rejection"] == 18
    assert result.dq_provenance["input_invalid_samples_before_rejection"] == 2
    assert result.metrics["valid_samples"] == 14
    assert result.metrics["high_rejected"] == 4
    assert result.metrics["low_rejected"] == 0
    assert result.metrics["valid_samples"] + result.metrics["high_rejected"] == 18
    assert checks["input_valid_samples_close_after_rejection"]["passed"] is True
    assert checks["input_valid_invalid_samples_match_total"]["passed"] is True


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
