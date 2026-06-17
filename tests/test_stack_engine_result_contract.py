from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from glass.engine.contracts import CombinePolicy, DQFlag, DQMask, OutputMapPolicy, RejectionPolicy, StackRequest, TileWindow
from glass.engine.stack_contract import build_stack_engine_result_contract
from glass.engine.stack_engine import CPUStackEngine, StackEngineResult


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

    def __post_init__(self) -> None:
        self.data = np.asarray(self.data, dtype=np.float32)
        self.height, self.width = self.data.shape
        self.dq = np.zeros_like(self.data, dtype=np.uint32) if self.dq is None else np.asarray(self.dq, dtype=np.uint32)

    def read_tile(self, window: TileWindow, dtype: Any = np.float32) -> np.ndarray:
        return np.asarray(self.data[window.as_slices()], dtype=dtype)

    def read_mask_tile(self, window: TileWindow) -> DQMask:
        return DQMask(np.asarray(self.dq[window.as_slices()], dtype=np.uint32).copy())


def _sources(frames: list[np.ndarray], dq: list[np.ndarray] | None = None) -> dict[str, ArrayImageSource]:
    masks = dq or [None] * len(frames)
    return {f"f{i}": ArrayImageSource(frame, mask) for i, (frame, mask) in enumerate(zip(frames, masks))}


def _request(
    frame_count: int,
    *,
    combine: CombinePolicy | None = None,
    maps: OutputMapPolicy | None = None,
    rejection: RejectionPolicy | None = None,
) -> StackRequest:
    return StackRequest(
        frame_ids=tuple(f"f{i}" for i in range(frame_count)),
        source_kind="light",
        combine=combine or CombinePolicy(),
        rejection=rejection or RejectionPolicy(),
        output_maps=maps or OutputMapPolicy(variance=True, dq=True),
    )


def test_stack_engine_result_contract_is_embedded_and_passes() -> None:
    frames = [
        np.ones((3, 4), dtype=np.float32),
        np.ones((3, 4), dtype=np.float32) * 3.0,
    ]
    dq = np.zeros((3, 4), dtype=np.uint32)
    dq[0, 0] = int(DQFlag.NO_DATA)
    request = _request(
        len(frames),
        combine=CombinePolicy(method="weighted_mean"),
        maps=OutputMapPolicy(coverage=True, weight=True, low_rejection=True, high_rejection=True, dq=True),
    )

    result = CPUStackEngine(tile_size=2).stack(request, _sources(frames, [np.zeros_like(dq), dq]))

    contract = result.dq_provenance["result_contract"]
    assert contract["passed"] is True
    assert result.metrics["result_contract_passed"] is True
    checks = {item["name"]: item for item in contract["checks"]}
    assert checks["requested_maps_present"]["passed"] is True
    assert checks["coverage_zero_matches_dq_no_data"]["passed"] is True
    assert checks["coverage_sum_matches_metrics"]["passed"] is True
    assert checks["input_samples_match_request_shape"]["evidence"]["expected_input_samples"] == 24


def test_stack_engine_result_contract_detects_dq_provenance_drift() -> None:
    frames = [
        np.ones((2, 2), dtype=np.float32),
        np.ones((2, 2), dtype=np.float32) * 2.0,
    ]
    request = _request(len(frames), maps=OutputMapPolicy(coverage=True, dq=True))
    result = CPUStackEngine(tile_size=1).stack(request, _sources(frames))
    result.dq_provenance["output_dq_summary"] = {"valid": 0, "no_data": 4}

    contract = build_stack_engine_result_contract(result, request=request)

    assert contract["passed"] is False
    checks = {item["name"]: item for item in contract["checks"]}
    assert checks["dq_summary_matches_provenance"]["passed"] is False


def test_stack_engine_result_contract_detects_missing_requested_maps() -> None:
    request = StackRequest(
        frame_ids=("a", "b"),
        source_kind="light",
        output_maps=OutputMapPolicy(coverage=True, weight=True, low_rejection=False, high_rejection=False, dq=True),
    )
    result = StackEngineResult(
        master=np.zeros((2, 3), dtype=np.float32),
        weight_map=None,
        coverage_map=None,
        dq_mask=None,
        dq_provenance={"input_samples": 12, "output_dq_summary": {}},
        metrics={"valid_samples": 0},
    )

    contract = build_stack_engine_result_contract(result, request=request)

    assert contract["passed"] is False
    checks = {item["name"]: item for item in contract["checks"]}
    assert checks["requested_maps_present"]["passed"] is False
    assert checks["requested_maps_present"]["evidence"]["missing"] == ["coverage", "dq", "weight"]


def test_stack_engine_result_contract_detects_rejection_dq_mismatch() -> None:
    result = StackEngineResult(
        master=np.zeros((2, 2), dtype=np.float32),
        coverage_map=np.ones((2, 2), dtype=np.float32),
        low_rejection_map=np.array([[1, 0], [0, 0]], dtype=np.float32),
        high_rejection_map=np.zeros((2, 2), dtype=np.float32),
        dq_mask=DQMask.empty((2, 2)),
        dq_provenance={
            "input_samples": 4,
            "output_coverage_zero_pixels": 0,
            "output_dq_summary": {"valid": 4},
        },
        metrics={"valid_samples": 4},
    )
    request = StackRequest(
        frame_ids=("a",),
        source_kind="light",
        output_maps=OutputMapPolicy(coverage=True, low_rejection=True, high_rejection=True, dq=True),
    )

    contract = build_stack_engine_result_contract(result, request=request)

    assert contract["passed"] is False
    checks = {item["name"]: item for item in contract["checks"]}
    assert checks["low_rejection_map_matches_dq"]["passed"] is False


def test_stack_engine_result_contract_distinguishes_rejected_samples_from_pixels() -> None:
    frames = [
        np.ones((3, 3), dtype=np.float32),
        np.ones((3, 3), dtype=np.float32),
        np.ones((3, 3), dtype=np.float32),
        np.ones((3, 3), dtype=np.float32) * 100.0,
        np.ones((3, 3), dtype=np.float32) * 101.0,
    ]
    request = _request(
        len(frames),
        rejection=RejectionPolicy(method="sigma", high_sigma=1.0, min_samples=3, max_reject_fraction=0.5),
        maps=OutputMapPolicy(coverage=True, weight=True, low_rejection=True, high_rejection=True, dq=True),
    )

    result = CPUStackEngine(tile_size=2).stack(request, _sources(frames))
    contract = result.dq_provenance["result_contract"]
    checks = {item["name"]: item for item in contract["checks"]}

    assert contract["passed"] is True
    assert np.all(result.high_rejection_map == 2)
    assert checks["high_rejection_map_matches_dq"]["evidence"]["high_rejection_pixels"] == 9
    assert checks["high_rejection_sample_sum_matches_metrics"]["evidence"]["map_rejected_sample_sum"] == 18
    assert checks["high_rejection_sample_sum_matches_metrics"]["passed"] is True
    assert checks["high_rejection_pixels_match_provenance"]["passed"] is True


def test_stack_engine_result_contract_detects_rejection_sample_metric_drift() -> None:
    dq = DQMask.empty((2, 2)).mark(DQFlag.HIGH_REJECTED, np.array([[True, False], [False, False]]))
    result = StackEngineResult(
        master=np.zeros((2, 2), dtype=np.float32),
        coverage_map=np.ones((2, 2), dtype=np.float32) * 2,
        low_rejection_map=np.zeros((2, 2), dtype=np.float32),
        high_rejection_map=np.array([[2, 0], [0, 0]], dtype=np.float32),
        dq_mask=dq,
        dq_provenance={
            "input_samples": 8,
            "output_coverage_zero_pixels": 0,
            "output_high_rejected_pixels": 1,
            "output_low_rejected_pixels": 0,
            "output_dq_summary": {"valid": 3, "high_rejected": 1},
        },
        metrics={"valid_samples": 8, "low_rejected": 0, "high_rejected": 1},
    )
    request = StackRequest(
        frame_ids=("a", "b"),
        source_kind="light",
        output_maps=OutputMapPolicy(coverage=True, low_rejection=True, high_rejection=True, dq=True),
    )

    contract = build_stack_engine_result_contract(result, request=request)
    checks = {item["name"]: item for item in contract["checks"]}

    assert contract["passed"] is False
    assert checks["high_rejection_map_matches_dq"]["passed"] is True
    assert checks["high_rejection_pixels_match_provenance"]["passed"] is True
    assert checks["high_rejection_sample_sum_matches_metrics"]["passed"] is False
    assert checks["high_rejection_sample_sum_matches_metrics"]["evidence"] == {
        "map_rejected_sample_sum": 2,
        "metrics_rejected_samples": 1,
    }
