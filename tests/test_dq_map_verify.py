from __future__ import annotations

from pathlib import Path

import numpy as np

from glass.engine.contracts import DQFlag
from glass.io.fits_io import write_fits_data
from glass.report.dq_map_verify import summarize_count_map_pixels, summarize_dq_map_pixels


def test_summarize_dq_map_pixels_counts_bitfield_flags(tmp_path: Path):
    dq_map = tmp_path / "dq.fits"
    values = np.array(
        [
            [0, int(DQFlag.NO_DATA), int(DQFlag.WARP_EDGE)],
            [int(DQFlag.LOW_REJECTED), int(DQFlag.HIGH_REJECTED), int(DQFlag.WARP_EDGE | DQFlag.HIGH_REJECTED)],
        ],
        dtype=np.uint32,
    )
    write_fits_data(dq_map, values, dtype=np.float32)

    summary = summarize_dq_map_pixels(
        dq_map,
        flags=["valid", "no_data", "warp_edge", "low_rejected", "high_rejected"],
        tile_size=2,
    )

    assert summary["width"] == 3
    assert summary["height"] == 2
    assert summary["total_pixels"] == 6
    assert summary["counts"] == {
        "valid": 1,
        "no_data": 1,
        "warp_edge": 2,
        "low_rejected": 1,
        "high_rejected": 2,
    }
    assert summary["unknown_flags"] == []


def test_summarize_count_map_pixels_counts_positive_and_sum(tmp_path: Path):
    count_map = tmp_path / "count.fits"
    values = np.array(
        [
            [0.0, 1.0, 2.0],
            [np.nan, -1.0, 4.0],
        ],
        dtype=np.float32,
    )
    write_fits_data(count_map, values, dtype=np.float32)

    summary = summarize_count_map_pixels(count_map, tile_size=2)

    assert summary["width"] == 3
    assert summary["height"] == 2
    assert summary["total_pixels"] == 6
    assert summary["finite_pixels"] == 5
    assert summary["nonfinite_pixels"] == 1
    assert summary["positive_pixels"] == 3
    assert summary["zero_or_less_pixels"] == 2
    assert summary["sum"] == 6.0
    assert summary["rounded_sum"] == 6
    assert summary["min"] == -1.0
    assert summary["max"] == 4.0
