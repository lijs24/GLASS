from __future__ import annotations

import numpy as np

from glass.engine.contracts import DQFlag
from glass.engine.resident_source_dq import (
    build_resident_source_dq_summary,
    source_invalid_mask_from_array,
    source_invalid_mask_from_dq_mask,
)


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
