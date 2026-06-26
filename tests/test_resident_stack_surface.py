from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from glass.engine.contracts import DQFlag, DQMask
import glass.engine.resident_stack_surface as resident_stack_surface
from glass.engine.resident_stack_surface import (
    build_resident_integration_stack_surface_contract,
    build_resident_master_stack_surface_contract,
)


def test_resident_integration_stack_surface_contract_closes_dq_and_rejection_maps() -> None:
    master = np.array([[10.0, 12.0], [0.0, 14.0]], dtype=np.float32)
    weight = np.array([[2.0, 2.0], [0.0, 2.0]], dtype=np.float32)
    coverage = np.array([[2.0, 1.0], [0.0, 2.0]], dtype=np.float32)
    low = np.array([[0.0, 1.0], [0.0, 0.0]], dtype=np.float32)
    high = np.zeros((2, 2), dtype=np.float32)
    dq = DQMask.empty((2, 2))
    dq.mark(DQFlag.NO_DATA, coverage <= 0)
    dq.mark(DQFlag.LOW_REJECTED, low > 0)
    dq_summary = dq.summary()

    contract = build_resident_integration_stack_surface_contract(
        filter_name="H",
        frame_ids=["light_001", "light_002"],
        master=master,
        weight_map=weight,
        coverage_map=coverage,
        low_rejection_map=low,
        high_rejection_map=high,
        dq_map=dq.data,
        dq_summary=dq_summary,
        dq_provenance_summary={
            "active_frame_count": 2,
            "post_rejection_pixels": 3,
            "valid_samples_after_rejection": 5,
            "rejected_samples": 1,
            "output_dq_summary": dq_summary,
            "sample_accounting_closure": {
                "status": "passed",
                "input_valid_samples_before_rejection": 6,
                "valid_samples_after_rejection": 5,
                "rejected_samples": 1,
                "valid_rejection_match": True,
            },
        },
        output_map_policy={
            "available": ["master", "weight", "coverage", "low_rejection", "high_rejection", "dq"],
            "written": ["master", "weight", "coverage", "low_rejection", "high_rejection", "dq"],
            "skipped": [],
        },
        rejection="winsorized_sigma",
        low_sigma=3.0,
        high_sigma=3.0,
        weights=[1.0, 1.0],
        grouping_key="H",
        dispatch="stack",
        map_paths={"master": "master_H.fits"},
    )

    assert contract["passed"] is True
    assert contract["stack_request"]["frame_ids"] == ["light_001", "light_002"]
    assert contract["stack_request"]["source_kind"] == "light"
    assert contract["stack_request"]["output_maps"]["coverage"] is True
    checks = {item["name"]: item for item in contract["checks"]}
    assert checks["coverage_zero_matches_dq_no_data"]["passed"] is True
    assert checks["active_frame_count_matches_positive_weights"]["passed"] is True
    assert checks["coverage_max_within_active_frame_count"]["passed"] is True
    assert checks["coverage_positive_pixels_match_post_rejection_pixels"]["passed"] is True
    assert checks["weight_positive_pixels_match_post_rejection_pixels"]["passed"] is True
    assert checks["low_rejection_pixels_match_dq"]["passed"] is True
    assert checks["rejection_sample_sum_matches_provenance"]["passed"] is True


def test_resident_integration_stack_surface_contract_reuses_precomputed_stats(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    master = np.array([[10.0, 12.0], [0.0, 14.0]], dtype=np.float32)
    weight = np.array([[2.0, 2.0], [0.0, 2.0]], dtype=np.float32)
    coverage = np.array([[2.0, 1.0], [0.0, 2.0]], dtype=np.float32)
    low = np.array([[0.0, 1.0], [0.0, 0.0]], dtype=np.float32)
    high = np.zeros((2, 2), dtype=np.float32)
    dq = DQMask.empty((2, 2))
    dq.mark(DQFlag.NO_DATA, coverage <= 0)
    dq.mark(DQFlag.LOW_REJECTED, low > 0)
    dq_summary = dq.summary()

    def fail_finite_stats(value: object) -> dict[str, object]:
        raise AssertionError(f"unexpected full finite scan for {type(value)!r}")

    monkeypatch.setattr(resident_stack_surface, "_finite_stats", fail_finite_stats)
    precomputed = {
        "master": {
            "present": True,
            "shape": [2, 2],
            "dtype": "float32",
            "finite_pixels": 4,
            "nonfinite_pixels": 0,
            "stats_source": "test_precomputed",
        },
        "weight": {
            "present": True,
            "shape": [2, 2],
            "dtype": "float32",
            "finite_pixels": 4,
            "nonfinite_pixels": 0,
            "positive_pixels": 3,
            "zero_or_less_pixels": 1,
            "stats_source": "test_precomputed",
        },
        "coverage": {
            "present": True,
            "shape": [2, 2],
            "dtype": "float32",
            "finite_pixels": 4,
            "nonfinite_pixels": 0,
            "rounded_sum": 5,
            "positive_pixels": 3,
            "zero_or_less_pixels": 1,
            "negative_pixels": 0,
            "fractional_pixels": 0,
            "max": 2.0,
            "stats_source": "test_precomputed",
        },
        "low_rejection": {
            "present": True,
            "shape": [2, 2],
            "dtype": "float32",
            "finite_pixels": 4,
            "nonfinite_pixels": 0,
            "rounded_sum": 1,
            "positive_pixels": 1,
            "zero_or_less_pixels": 3,
            "negative_pixels": 0,
            "fractional_pixels": 0,
            "stats_source": "test_precomputed",
        },
        "high_rejection": {
            "present": True,
            "shape": [2, 2],
            "dtype": "float32",
            "finite_pixels": 4,
            "nonfinite_pixels": 0,
            "rounded_sum": 0,
            "positive_pixels": 0,
            "zero_or_less_pixels": 4,
            "negative_pixels": 0,
            "fractional_pixels": 0,
            "stats_source": "test_precomputed",
        },
        "dq": {
            "present": True,
            "shape": [2, 2],
            "dtype": "uint32",
            "finite_pixels": 4,
            "nonfinite_pixels": 0,
            "positive_pixels": 2,
            "zero_or_less_pixels": 2,
            "negative_pixels": 0,
            "fractional_pixels": 0,
            "stats_source": "test_precomputed",
        },
    }

    contract = build_resident_integration_stack_surface_contract(
        filter_name="H",
        frame_ids=["light_001", "light_002"],
        master=master,
        weight_map=weight,
        coverage_map=coverage,
        low_rejection_map=low,
        high_rejection_map=high,
        dq_map=dq.data,
        dq_summary=dq_summary,
        dq_provenance_summary={
            "active_frame_count": 2,
            "post_rejection_pixels": 3,
            "valid_samples_after_rejection": 5,
            "rejected_samples": 1,
            "sample_accounting_closure": {
                "status": "passed",
                "valid_samples_after_rejection": 5,
                "rejected_samples": 1,
                "valid_rejection_match": True,
            },
        },
        output_map_policy={
            "available": ["master", "weight", "coverage", "low_rejection", "high_rejection", "dq"],
            "written": ["master", "weight", "coverage", "low_rejection", "high_rejection", "dq"],
            "skipped": [],
        },
        rejection="winsorized_sigma",
        low_sigma=3.0,
        high_sigma=3.0,
        weights=[1.0, 1.0],
        grouping_key="H",
        dispatch="stack",
        precomputed_map_stats=precomputed,
        trust_precomputed_dq_summary=True,
    )

    assert contract["passed"] is True
    checks = {item["name"]: item for item in contract["checks"]}
    assert checks["dq_summary_matches_dq_map"]["evidence"]["source"] == "trusted_precomputed_dq_summary"
    assert checks["active_frame_count_matches_positive_weights"]["passed"] is True
    assert checks["coverage_positive_pixels_match_post_rejection_pixels"]["passed"] is True
    assert checks["weight_positive_pixels_match_post_rejection_pixels"]["passed"] is True
    maps = {row["map"]: row for row in contract["stack_result"]["maps"]}
    assert maps["coverage"]["stats"]["stats_source"] == "test_precomputed"


def test_resident_integration_stack_surface_contract_blocks_active_coverage_drift() -> None:
    master = np.ones((2, 2), dtype=np.float32)
    weight = np.array([[2.0, 2.0], [0.0, 2.0]], dtype=np.float32)
    coverage = np.array([[3.0, 1.0], [0.0, 2.0]], dtype=np.float32)
    low = np.zeros((2, 2), dtype=np.float32)
    high = np.zeros((2, 2), dtype=np.float32)
    dq = DQMask.empty((2, 2))
    dq.mark(DQFlag.NO_DATA, coverage <= 0)
    dq_summary = dq.summary()

    contract = build_resident_integration_stack_surface_contract(
        filter_name="H",
        frame_ids=["light_001", "light_002"],
        master=master,
        weight_map=weight,
        coverage_map=coverage,
        low_rejection_map=low,
        high_rejection_map=high,
        dq_map=dq.data,
        dq_summary=dq_summary,
        dq_provenance_summary={
            "active_frame_count": 1,
            "post_rejection_pixels": 4,
            "valid_samples_after_rejection": 6,
            "rejected_samples": 0,
            "sample_accounting_closure": {
                "status": "passed",
                "input_valid_samples_before_rejection": 6,
                "valid_samples_after_rejection": 6,
                "rejected_samples": 0,
                "valid_rejection_match": True,
            },
        },
        output_map_policy={
            "available": ["master", "weight", "coverage", "low_rejection", "high_rejection", "dq"],
            "written": ["master", "weight", "coverage", "low_rejection", "high_rejection", "dq"],
            "skipped": [],
        },
        rejection="none",
        low_sigma=3.0,
        high_sigma=3.0,
        weights=[1.0, 1.0],
        grouping_key="H",
        dispatch="stack",
    )

    checks = {item["name"]: item for item in contract["checks"]}
    assert contract["passed"] is False
    assert checks["active_frame_count_matches_positive_weights"]["passed"] is False
    assert checks["coverage_max_within_active_frame_count"]["passed"] is False
    assert checks["coverage_positive_pixels_match_post_rejection_pixels"]["passed"] is False
    assert checks["weight_positive_pixels_match_post_rejection_pixels"]["passed"] is False


def test_resident_master_stack_surface_contract_records_source_frame_ids(tmp_path: Path) -> None:
    master_path = tmp_path / "master_bias.npy"
    np.save(master_path, np.zeros((2, 2), dtype=np.float32))

    contract = build_resident_master_stack_surface_contract(
        name="resident_bias_H_set1",
        master_type="bias",
        path=str(master_path),
        stats={"min": 0.0, "max": 1.0, "mean": 0.5, "median": 0.5, "std": 0.1},
        frame_ids=["bias_001", "bias_002"],
        frame_count=2,
        shape={"height": 2, "width": 2},
        policy={"master_rejection": "none"},
    )

    assert contract["passed"] is True
    assert contract["surface"] == "master_calibration"
    assert contract["stack_request"]["source_kind"] == "bias"
    assert contract["stack_request"]["frame_ids"] == ["bias_001", "bias_002"]
