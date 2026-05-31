from __future__ import annotations

from pathlib import Path

import numpy as np

from glass.engine.contracts import DQFlag
from glass.io.fits_io import write_fits_data
from glass.report.dq_map_verify import summarize_dq_map_pixels


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
