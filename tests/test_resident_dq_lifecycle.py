from __future__ import annotations

import pytest

from glass.engine.resident_dq_lifecycle import (
    build_resident_dq_lifecycle_group,
    summarize_resident_dq_lifecycle_groups,
    validate_resident_dq_lifecycle_group,
)


def _source_group(*, active_frame_count: int = 3) -> dict:
    return {
        "artifact": "resident_source_dq_execution_group",
        "filter": "H",
        "passed": True,
        "status": "passed",
        "execution_route": "resident_in_memory_mask_streaming",
        "materializes_calibrated_dq_cache": False,
        "frame_count": 4,
        "active_frame_count": active_frame_count,
        "height": 2,
        "width": 5,
        "input_samples": active_frame_count * 10,
        "input_invalid_samples_before_rejection": 1,
        "all_frame_input_invalid_samples_before_frame_mask": 2,
    }


def _frame_mask_group() -> dict:
    return {
        "artifact": "resident_frame_mask_contract_group",
        "filter": "H",
        "summary": {
            "passed": True,
            "frame_count": 4,
            "active_frame_count": 3,
            "masked_frame_count": 1,
            "unknown_zero_weight_frame_count": 0,
        },
    }


def _pixel_closure_group() -> dict:
    return {
        "artifact": "resident_dq_pixel_closure_group",
        "filter": "H",
        "passed": True,
        "status": "passed",
        "frame_mask_active_frame_count": 3,
        "frame_mask_masked_frame_count": 1,
    }


def test_resident_dq_lifecycle_passes_complete_group() -> None:
    group = build_resident_dq_lifecycle_group(
        source_dq_execution_group=_source_group(),
        frame_mask_group=_frame_mask_group(),
        dq_pixel_closure_group=_pixel_closure_group(),
        filter_name="H",
    )

    validate_resident_dq_lifecycle_group(group)
    assert group["passed"] is True
    assert group["active_frame_count"] == 3
    assert group["masked_frame_count"] == 1
    checks = {check["name"]: check for check in group["checks"]}
    assert checks["source_active_matches_frame_mask"]["passed"] is True
    assert checks["source_input_samples_use_active_frames"]["passed"] is True


def test_resident_dq_lifecycle_rejects_active_count_drift() -> None:
    group = build_resident_dq_lifecycle_group(
        source_dq_execution_group=_source_group(active_frame_count=4),
        frame_mask_group=_frame_mask_group(),
        dq_pixel_closure_group=_pixel_closure_group(),
        filter_name="H",
    )

    assert group["passed"] is False
    with pytest.raises(RuntimeError, match="source_active_matches_frame_mask"):
        validate_resident_dq_lifecycle_group(group)


def test_resident_dq_lifecycle_summary_counts_failed_checks() -> None:
    good = build_resident_dq_lifecycle_group(
        source_dq_execution_group=_source_group(),
        frame_mask_group=_frame_mask_group(),
        dq_pixel_closure_group=_pixel_closure_group(),
    )
    bad = build_resident_dq_lifecycle_group(
        source_dq_execution_group={**_source_group(), "input_samples": 40},
        frame_mask_group=_frame_mask_group(),
        dq_pixel_closure_group=_pixel_closure_group(),
    )

    summary = summarize_resident_dq_lifecycle_groups([good, bad])

    assert summary["group_count"] == 2
    assert summary["passed_group_count"] == 1
    assert summary["failed_group_count"] == 1
    assert summary["failed_check_counts"] == {"source_input_samples_use_active_frames": 1}
