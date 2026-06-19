from __future__ import annotations

import numpy as np

from glass.engine.contracts import DQFlag
from glass.engine.resident_source_dq import (
    build_resident_source_dq_execution_group,
    build_resident_source_dq_summary,
    combine_source_invalid_masks,
    source_invalid_mask_from_array,
    source_invalid_mask_from_dq_mask,
    source_invalid_mask_from_sidecar_path,
    summarize_resident_source_dq_execution_groups,
)
from glass.io.fits_io import write_fits_data


def test_source_invalid_mask_from_array_accounts_nonfinite_samples_without_dq_flags():
    data = np.array([[1.0, np.nan], [np.inf, 4.0]], dtype=np.float32)

    mask, info = source_invalid_mask_from_array(data, height=2, width=2)

    assert mask is not None
    assert mask.tolist() == [[0, 1], [1, 0]]
    assert info["invalid_samples"] == 2
    assert info["flagged_samples"] == 0
    assert info["nonfinite_samples"] == 2
    assert info["flag_counts"] == {}


def test_source_invalid_mask_from_dq_mask_preserves_flag_counts():
    dq = np.zeros((2, 3), dtype=np.uint32)
    dq[0, 1] = np.uint32(int(DQFlag.HOT_PIXEL))
    dq[1, 2] = np.uint32(int(DQFlag.NO_DATA) | int(DQFlag.SATURATED))

    mask, info = source_invalid_mask_from_dq_mask(dq, height=2, width=3)

    assert mask is not None
    assert mask.tolist() == [[0, 1, 0], [0, 0, 1]]
    assert info["invalid_samples"] == 2
    assert info["flagged_samples"] == 2
    assert info["nonfinite_samples"] == 0
    assert info["flag_counts"]["hot_pixel"] == 1
    assert info["flag_counts"]["no_data"] == 1
    assert info["flag_counts"]["saturated"] == 1


def test_source_invalid_mask_from_sidecar_path_reads_fits_dq_bits(tmp_path):
    dq = np.zeros((2, 3), dtype=np.float32)
    dq[0, 1] = float(int(DQFlag.HOT_PIXEL))
    dq[1, 0] = float(int(DQFlag.NO_DATA) | int(DQFlag.SATURATED))
    dq[1, 2] = np.nan
    sidecar = tmp_path / "source_dq.fits"
    write_fits_data(sidecar, dq)

    mask, info = source_invalid_mask_from_sidecar_path(sidecar, height=2, width=3)

    assert mask is not None
    assert mask.tolist() == [[0, 1, 0], [1, 0, 1]]
    assert info["source_model"] == "dq_sidecar_fits"
    assert info["sidecar_path"] == str(sidecar)
    assert info["invalid_samples"] == 3
    assert info["flagged_samples"] == 3
    assert info["nonfinite_samples"] == 0
    assert info["flag_counts"]["hot_pixel"] == 1
    assert info["flag_counts"]["saturated"] == 1
    assert info["flag_counts"]["no_data"] == 2


def test_combine_source_invalid_masks_uses_union_without_double_counting():
    data = np.array([[1.0, np.nan], [3.0, 4.0]], dtype=np.float32)
    dq = np.zeros((2, 2), dtype=np.uint32)
    dq[0, 1] = np.uint32(int(DQFlag.NO_DATA))
    dq[1, 0] = np.uint32(int(DQFlag.HOT_PIXEL))

    mask, info = combine_source_invalid_masks(
        [
            source_invalid_mask_from_array(data, height=2, width=2),
            source_invalid_mask_from_dq_mask(dq, height=2, width=2),
        ],
        height=2,
        width=2,
    )

    assert mask is not None
    assert mask.tolist() == [[0, 1], [1, 0]]
    assert info["invalid_samples"] == 2
    assert info["flagged_samples"] == 2
    assert info["nonfinite_samples"] == 1
    assert info["flag_counts"]["no_data"] == 1
    assert info["flag_counts"]["hot_pixel"] == 1


def test_resident_source_dq_summary_matches_stackengine_input_sample_closure():
    rows = [
        {
            "frame_id": "f0",
            "status": "no_invalid_samples",
            "source": "test",
            "invalid_samples": 0,
            "flagged_samples": 0,
            "nonfinite_samples": 0,
            "flag_counts": {},
            "applied": False,
        },
        {
            "frame_id": "f1",
            "status": "applied",
            "source": "test",
            "invalid_samples": 2,
            "flagged_samples": 2,
            "nonfinite_samples": 0,
            "flag_counts": {"hot_pixel": 1, "no_data": 1},
            "applied": True,
        },
    ]

    summary = build_resident_source_dq_summary(rows, frame_count=2, height=2, width=3)

    assert summary["input_samples"] == 12
    assert summary["input_valid_samples_before_rejection"] == 10
    assert summary["input_invalid_samples_before_rejection"] == 2
    assert summary["input_flagged_samples"] == 2
    assert summary["input_nonfinite_samples"] == 0
    assert summary["source_dq_flag_counts"] == {"hot_pixel": 1, "no_data": 1}
    assert summary["passed"] is True


def test_resident_source_dq_execution_group_proves_streaming_route_without_cache():
    summary = build_resident_source_dq_summary(
        [
            {
                "frame_id": "f0",
                "status": "no_invalid_samples",
                "source": "test",
                "invalid_samples": 0,
                "flagged_samples": 0,
                "nonfinite_samples": 0,
                "flag_counts": {},
                "applied": False,
            },
            {
                "frame_id": "f1",
                "status": "applied",
                "source": "test",
                "invalid_samples": 2,
                "flagged_samples": 2,
                "nonfinite_samples": 0,
                "flag_counts": {"hot_pixel": 2},
                "applied": True,
            },
        ],
        frame_count=2,
        height=4,
        width=5,
    )

    group = build_resident_source_dq_execution_group(
        summary,
        filter_name="H",
        frame_count=2,
        height=4,
        width=5,
        resident_calibration_batch_frames=3,
    )
    aggregate = summarize_resident_source_dq_execution_groups([group])

    assert group["passed"] is True
    assert group["execution_route"] == "resident_in_memory_mask_streaming"
    assert group["materializes_calibrated_dq_cache"] is False
    assert group["streaming_memory"]["estimated_per_frame_mask_bytes"] == 20
    assert group["streaming_memory"]["estimated_batch_mask_bytes"] == 60
    assert aggregate["passed"] is True
    assert aggregate["materializes_calibrated_dq_cache"] is False
    assert aggregate["estimated_peak_batch_mask_bytes"] == 60
