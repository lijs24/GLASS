from __future__ import annotations

from pathlib import Path

import numpy as np

from glass.engine.resident_cuda import _load_or_build_matching_masters
from glass.io.fits_io import write_fits_data
from glass.models import CalibrationPolicy


def _write_constant_frames(root: Path, prefix: str, values: list[float], exposure_s: float | None = None) -> list[str]:
    frame_ids: list[str] = []
    for index, value in enumerate(values):
        frame_id = f"{prefix}{index}"
        frame_ids.append(frame_id)
        write_fits_data(
            root / f"{frame_id}.fits",
            np.full((4, 4), value, dtype=np.float32),
            header={"EXPTIME": exposure_s},
        )
    return frame_ids


def test_resident_matching_master_cache_uses_stack_engine_contract(tmp_path: Path) -> None:
    bias_ids = _write_constant_frames(tmp_path, "B", [10.0, 11.0, 12.0, 1000.0], exposure_s=0.0)
    dark_ids = _write_constant_frames(tmp_path, "D", [100.0, 102.0, 104.0, 106.0], exposure_s=120.0)
    flat_ids = _write_constant_frames(tmp_path, "F", [100.0, 110.0, 120.0, 10000.0], exposure_s=1.0)
    frames = {
        frame_id: {
            "id": frame_id,
            "path": str(tmp_path / f"{frame_id}.fits"),
            "exposure_s": 120.0 if frame_id.startswith("D") else 1.0,
            "width": 4,
            "height": 4,
        }
        for frame_id in [*bias_ids, *dark_ids, *flat_ids]
    }
    shape = {"height": 4, "width": 4}
    groups = {
        "B": {
            "group_id": "B",
            "group_type": "bias",
            "frames": bias_ids,
            "gain": 100,
            "offset": 20,
            "binning": [1, 1],
            "shape": shape,
        },
        "D": {
            "group_id": "D",
            "group_type": "dark",
            "frames": dark_ids,
            "gain": 100,
            "offset": 20,
            "binning": [1, 1],
            "shape": shape,
        },
        "F": {
            "group_id": "F",
            "group_type": "flat",
            "frames": flat_ids,
            "gain": 100,
            "offset": 20,
            "binning": [1, 1],
            "shape": shape,
        },
    }
    policy = CalibrationPolicy(
        master_dark_includes_bias=False,
        master_rejection="minmax",
        master_rejection_min_samples=2,
        master_rejection_max_fraction=0.5,
        flat_normalization="median",
        flat_floor=0.05,
    )
    cache = tmp_path / "shared_cache"

    bias, dark, flat, stats, dark_exposure = _load_or_build_matching_masters(
        tmp_path / "run_a",
        "H",
        4,
        4,
        frames,
        groups,
        "B",
        "D",
        "F",
        policy,
        master_cache_dir=cache,
    )

    assert stats["cache_hit"] is False
    assert stats["cache_builder"] == "resident_stack_engine_mean_master_cache_v1"
    assert stats["tile_stack_mode"] == "stack_engine_cpu"
    assert stats["stack_engine_enabled"] is True
    assert stats["master_rejection_requested"] == "minmax"
    assert stats["master_rejection_applied"] == "none"
    assert stats["flat_normalization"]["normalization_stage"] == "master_after_stack"
    assert dark_exposure == 120.0
    assert np.allclose(bias, 258.25)
    assert np.allclose(dark, -155.25)
    assert np.allclose(flat, 1.0)
    assert stats["stack_engine_metrics"]["bias"]["rejection"] == "none"
    assert stats["stack_engine_metrics"]["bias"]["master_rejection_requested"] == "minmax"
    assert stats["stack_engine_metrics"]["bias"]["result_contract_passed"] is True
    assert stats["dq_provenance_summary"]["bias"]["source_schema"] == "stack_engine_dq_provenance"
    assert stats["dq_provenance_summary"]["bias"]["sample_accounting_closure"]["status"] == "passed"

    cached_bias, cached_dark, cached_flat, cached_stats, _dark_exposure = _load_or_build_matching_masters(
        tmp_path / "run_b",
        "H",
        4,
        4,
        frames,
        groups,
        "B",
        "D",
        "F",
        policy,
        master_cache_dir=cache,
    )

    assert cached_stats["cache_hit"] is True
    assert cached_stats["stack_engine_enabled"] is True
    assert cached_stats["cache_scope"] == "shared"
    assert np.allclose(cached_bias, bias)
    assert np.allclose(cached_dark, dark)
    assert np.allclose(cached_flat, flat)
