from __future__ import annotations

import numpy as np
import pytest

from glass.engine.resident_source_dq import (
    apply_resident_source_invalid_mask,
    build_resident_source_dq_execution_group,
    build_resident_source_dq_summary,
    validate_resident_source_dq_execution_group,
)


class _FakeResidentStack:
    def __init__(self) -> None:
        self.applied_masks: list[tuple[int, np.ndarray]] = []

    def apply_invalid_mask_frame(self, frame_index: int, invalid_mask: np.ndarray) -> dict[str, object]:
        mask = np.asarray(invalid_mask, dtype=np.uint8)
        self.applied_masks.append((int(frame_index), mask.copy()))
        return {
            "native_method": "FakeResidentStack.apply_invalid_mask_frame",
            "invalid_samples": int(np.count_nonzero(mask)),
        }


def test_source_dq_sidecar_is_contractually_visible_before_registration_catalog() -> None:
    stack = _FakeResidentStack()
    invalid = np.zeros((4, 4), dtype=np.uint8)
    invalid[1, 2] = 1

    row = apply_resident_source_invalid_mask(
        stack,
        frame_index=3,
        frame_id="light_003",
        invalid_mask=invalid,
        mask_info={
            "supported": True,
            "reason": "",
            "invalid_samples": 1,
            "flagged_samples": 1,
            "nonfinite_samples": 0,
            "flag_counts": {"hot_pixel": 1},
            "source_model": "source_dq_sidecar",
            "sidecar_paths": ["light_003_dq.fits"],
        },
        source="resident_calibrated_batch_input",
    )

    summary = build_resident_source_dq_summary([row], frame_count=4, height=4, width=4)
    group = build_resident_source_dq_execution_group(
        summary,
        filter_name="H",
        frame_count=4,
        height=4,
        width=4,
        resident_calibration_batch_frames=2,
    )

    validate_resident_source_dq_execution_group(group)
    assert stack.applied_masks[0][0] == 3
    assert row["application_order"] == "calibration_pre_registration"
    assert row["registration_catalog_visible"] is True
    assert row["registration_catalog_visibility_required"] is True
    assert summary["pre_registration_catalog_visible_invalid_samples"] == 1
    assert summary["required_invalid_samples_not_visible_to_registration_catalog"] == 0
    assert group["application_order_counts"] == {"calibration_pre_registration": 1}
    assert group["registration_catalog_visibility_counts"] == {
        "pre_registration_catalog_visible": 1
    }
    assert any(
        check["name"] == "non_inline_source_dq_visible_to_registration_catalog"
        and check["passed"] is True
        for check in group["checks"]
    )


def test_deferred_inline_cosmetic_cuda_is_not_required_to_feed_registration_catalog() -> None:
    row = {
        "schema_version": 1,
        "frame_id": "light_001",
        "frame_index": 1,
        "source": "resident_post_registration_pre_warp_cosmetic_cuda",
        "application_order": "post_registration_pre_warp",
        "registration_catalog_visibility": "post_registration_deferred_not_catalog_visible",
        "registration_catalog_visible": False,
        "registration_catalog_visibility_required": False,
        "supported": True,
        "status": "applied",
        "applied": True,
        "invalid_samples": 2,
        "flagged_samples": 2,
        "nonfinite_samples": 0,
        "flag_counts": {"hot_pixel": 2},
        "source_model": "inline_structure_cosmetic_cuda_thresholds",
        "inline_source_dq": True,
        "native_method": "ResidentCalibratedStack.apply_isolated_cosmetic_threshold_mask_frames",
    }

    summary = build_resident_source_dq_summary([row], frame_count=2, height=4, width=4)
    group = build_resident_source_dq_execution_group(
        summary,
        filter_name="H",
        frame_count=2,
        height=4,
        width=4,
    )

    validate_resident_source_dq_execution_group(group)
    assert summary["post_registration_deferred_invalid_samples"] == 2
    assert summary["required_invalid_samples_not_visible_to_registration_catalog"] == 0
    assert group["application_order_counts"] == {"post_registration_pre_warp": 1}
    assert group["registration_catalog_visibility_counts"] == {"not_catalog_visible": 1}


def test_required_source_dq_after_registration_fails_execution_contract() -> None:
    row = {
        "schema_version": 1,
        "frame_id": "light_002",
        "frame_index": 2,
        "source": "resident_post_registration_pre_warp_sidecar",
        "application_order": "post_registration_pre_warp",
        "registration_catalog_visibility": "post_registration_deferred_not_catalog_visible",
        "registration_catalog_visible": False,
        "registration_catalog_visibility_required": True,
        "supported": True,
        "status": "applied",
        "applied": True,
        "invalid_samples": 1,
        "flagged_samples": 1,
        "nonfinite_samples": 0,
        "flag_counts": {"hot_pixel": 1},
        "source_model": "source_dq_sidecar",
        "native_method": "ResidentCalibratedStack.apply_invalid_mask_frame",
    }

    summary = build_resident_source_dq_summary([row], frame_count=2, height=4, width=4)
    group = build_resident_source_dq_execution_group(
        summary,
        filter_name="H",
        frame_count=2,
        height=4,
        width=4,
    )

    assert group["passed"] is False
    assert group["required_invalid_samples_not_visible_to_registration_catalog"] == 1
    with pytest.raises(RuntimeError, match="non_inline_source_dq_visible_to_registration_catalog"):
        validate_resident_source_dq_execution_group(group)
