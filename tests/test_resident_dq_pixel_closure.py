from __future__ import annotations

import pytest

from glass.engine.resident_dq_pixel_closure import (
    build_resident_dq_pixel_closure_group,
    summarize_resident_dq_pixel_closure_groups,
    validate_resident_dq_pixel_closure_group,
)


def _good_output() -> dict:
    return {
        "filter": "H",
        "frame_count": 4,
        "rejection": "winsorized_sigma",
        "dq_summary": {"valid": 8, "warp_edge": 1, "low_rejected": 2, "high_rejected": 1},
        "dq_coverage_provenance": {
            "available": True,
            "active_frame_count": 3,
            "geometric_warp_coverage_frame_count": 3,
            "geometric_frame_count_matches_active": True,
            "rejected_sample_count": 6,
            "source_terms": [
                "post_rejection_coverage",
                "low_rejection",
                "high_rejection",
                "geometric_warp_coverage",
            ],
        },
        "dq_provenance_summary": {
            "source_schema": "resident_dq_coverage_provenance",
            "active_frame_count": 3,
            "rejected_samples": 6,
            "source_terms": [
                "post_rejection_coverage",
                "low_rejection",
                "high_rejection",
                "geometric_warp_coverage",
            ],
            "output_dq_summary": {
                "valid": 8,
                "warp_edge": 1,
                "low_rejected": 2,
                "high_rejected": 1,
            },
            "sample_accounting_closure": {
                "status": "passed",
                "input_valid_samples_before_rejection": 30,
                "valid_samples_after_rejection": 24,
                "rejected_samples": 6,
                "valid_rejection_match": True,
            },
        },
        "geometric_warp_coverage": {
            "available": True,
            "frame_count": 3,
            "frame_count_matches_active": True,
        },
        "resident_frame_mask_contract": {
            "summary": {
                "active_frame_count": 3,
                "masked_frame_count": 1,
                "unknown_zero_weight_frame_count": 0,
                "passed": True,
            }
        },
    }


def _good_mask() -> dict:
    return {
        "summary": {
            "active_frame_count": 3,
            "masked_frame_count": 1,
            "unknown_zero_weight_frame_count": 0,
            "passed": True,
        }
    }


def test_resident_dq_pixel_closure_passes_complete_group() -> None:
    group = build_resident_dq_pixel_closure_group(output=_good_output(), frame_mask_contract=_good_mask())

    validate_resident_dq_pixel_closure_group(group)
    assert group["passed"] is True
    checks = {check["name"]: check for check in group["checks"]}
    assert checks["active_frame_count_matches_provenance"]["passed"] is True
    assert checks["geometric_coverage_count_matches_active"]["passed"] is True
    assert checks["sample_accounting_closure_passed"]["passed"] is True


def test_resident_dq_pixel_closure_rejects_active_count_mismatch() -> None:
    output = _good_output()
    output["dq_provenance_summary"]["active_frame_count"] = 2

    group = build_resident_dq_pixel_closure_group(output=output, frame_mask_contract=_good_mask())

    assert group["passed"] is False
    with pytest.raises(RuntimeError, match="active_frame_count_matches_provenance"):
        validate_resident_dq_pixel_closure_group(group)


def test_resident_dq_pixel_closure_rejects_rejection_sample_mismatch() -> None:
    output = _good_output()
    output["dq_coverage_provenance"]["rejected_sample_count"] = 5

    group = build_resident_dq_pixel_closure_group(output=output, frame_mask_contract=_good_mask())

    assert group["passed"] is False
    failed = [check["name"] for check in group["checks"] if not check["passed"]]
    assert "rejection_sample_count_matches" in failed


def test_resident_dq_pixel_closure_summary_counts_failed_groups() -> None:
    good = build_resident_dq_pixel_closure_group(output=_good_output(), frame_mask_contract=_good_mask())
    bad_output = _good_output()
    bad_output["geometric_warp_coverage"]["frame_count"] = 2
    bad = build_resident_dq_pixel_closure_group(output=bad_output, frame_mask_contract=_good_mask())

    summary = summarize_resident_dq_pixel_closure_groups([good, bad])

    assert summary["group_count"] == 2
    assert summary["passed_group_count"] == 1
    assert summary["failed_group_count"] == 1
    assert summary["failed_check_counts"] == {"geometric_coverage_count_matches_active": 1}
