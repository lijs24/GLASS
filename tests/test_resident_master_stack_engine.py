from __future__ import annotations

from pathlib import Path

import numpy as np

import glass.engine.resident_cuda as resident_cuda
from glass.engine.resident_cuda import _load_or_build_matching_masters
from glass.io.fits_io import read_fits_data, write_fits_data
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


def test_resident_matching_master_cache_uses_stack_engine_contract(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        resident_cuda,
        "_resident_master_cuda_mean_available",
        lambda: (False, "unit_test_cuda_unavailable"),
    )
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
    assert stats["cache_builder"] == "resident_stack_engine_resident_cuda_mean_master_cache_v1"
    assert stats["tile_stack_mode"] == "stack_engine_cpu"
    assert stats["stack_engine_fallback_reason"] == "unit_test_cuda_unavailable"
    assert stats["stack_engine_enabled"] is True
    assert stats["master_rejection_requested"] == "minmax"
    assert stats["master_rejection_applied"] == "none"
    assert stats["flat_normalization"]["normalization_stage"] == "master_after_stack"
    assert dark_exposure == 120.0
    assert np.allclose(bias, 258.25)
    assert np.allclose(dark, -155.25)
    assert np.allclose(flat, 1.0)
    assert stats["stack_engine_metrics"]["bias"]["rejection"] == "none"
    assert stats["stack_engine_metrics"]["bias"]["execution_path"] == "full_frame_mean_no_rejection"
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


def test_resident_matching_master_cache_can_use_resident_cuda_mean_builder(
    tmp_path: Path,
    monkeypatch,
) -> None:
    class FakeResidentCalibratedStack:
        instances: list["FakeResidentCalibratedStack"] = []

        def __init__(self, frame_count: int, height: int, width: int) -> None:
            self.frame_count = int(frame_count)
            self.height = int(height)
            self.width = int(width)
            self.frames: list[np.ndarray | None] = [None] * self.frame_count
            FakeResidentCalibratedStack.instances.append(self)

        def upload_calibrated_frame(self, index: int, frame) -> None:
            arr = np.asarray(frame, dtype=np.float32)
            assert arr.shape == (self.height, self.width)
            self.frames[int(index)] = arr.copy()

        def integrate_mean(self):
            stack = np.stack([frame for frame in self.frames if frame is not None], axis=0)
            finite = np.isfinite(stack)
            sums = np.where(finite, stack, 0.0).sum(axis=0, dtype=np.float64)
            weight = finite.sum(axis=0, dtype=np.float32)
            master = np.divide(sums, weight, out=np.zeros_like(sums), where=weight > 0).astype(np.float32)
            return master, weight.astype(np.float32)

    def fake_native_read(path, dtype=np.float32, output=None):
        data = read_fits_data(path, dtype=dtype)
        if output is not None:
            output[...] = data
            data = output
        return data, {
            "fits_reader_backend": "fake_native_direct_simple",
            "fits_native_file_read_s": 0.001,
            "fits_native_decode_s": 0.002,
            "fits_native_total_s": 0.003,
            "fits_native_bytes_read": int(np.asarray(data).nbytes),
        }

    monkeypatch.setattr(
        resident_cuda,
        "_resident_master_cuda_mean_available",
        lambda: (True, ""),
    )
    monkeypatch.setattr(resident_cuda, "read_simple_fits_image_native_direct_timed", fake_native_read)
    monkeypatch.setattr("glass_cuda.ResidentCalibratedStack", FakeResidentCalibratedStack)

    bias_ids = _write_constant_frames(tmp_path, "B", [10.0, 12.0], exposure_s=0.0)
    dark_ids = _write_constant_frames(tmp_path, "D", [100.0, 104.0], exposure_s=120.0)
    flat_ids = _write_constant_frames(tmp_path, "F", [100.0, 120.0], exposure_s=1.0)
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
        "B": {"group_id": "B", "group_type": "bias", "frames": bias_ids, "shape": shape},
        "D": {"group_id": "D", "group_type": "dark", "frames": dark_ids, "shape": shape},
        "F": {"group_id": "F", "group_type": "flat", "frames": flat_ids, "shape": shape},
    }
    policy = CalibrationPolicy(master_dark_includes_bias=False, flat_normalization="median", flat_floor=0.05)

    bias, dark, flat, stats, dark_exposure = _load_or_build_matching_masters(
        tmp_path / "run_cuda",
        "H",
        4,
        4,
        frames,
        groups,
        "B",
        "D",
        "F",
        policy,
        master_cache_dir=tmp_path / "shared_cuda_cache",
    )

    assert len(FakeResidentCalibratedStack.instances) == 3
    assert stats["cache_hit"] is False
    assert stats["tile_stack_mode"] == "stack_engine_cuda_mean"
    assert stats["stack_engine_fallback_reason"] is None
    assert stats["cache_builder"] == "resident_stack_engine_resident_cuda_mean_master_cache_v1"
    assert stats["stack_engine_metrics"]["bias"]["execution_path"] == "resident_cuda_mean_no_rejection"
    assert stats["stack_engine_metrics"]["bias"]["resident_master_cache_builder"] == (
        "ResidentCalibratedStack.integrate_mean"
    )
    assert stats["stack_engine_metrics"]["bias"]["fits_backend_counts"] == {"fake_native_direct_simple": 2}
    assert stats["dq_provenance_summary"]["bias"]["engine"] == "stack_engine_cuda_mean"
    assert stats["dq_provenance_summary"]["bias"]["sample_accounting_closure"]["status"] == "passed"
    assert dark_exposure == 120.0
    assert np.allclose(bias, 11.0)
    assert np.allclose(dark, 91.0)
    assert np.allclose(flat, 1.0)
