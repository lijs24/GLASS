from __future__ import annotations

from pathlib import Path

import numpy as np

import glass.engine.resident_cuda as resident_cuda
from glass.cpu.integration import weighted_integrate_stack
from glass.engine.resident_cuda import _load_or_build_matching_masters
from glass.io.fits_fast import SimpleFitsImageSpec
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
        lambda: (_ for _ in ()).throw(
            AssertionError("resident CUDA mean availability should not be probed when master rejection is active")
        ),
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
    assert stats["cache_builder"] == "resident_stack_engine_resident_cuda_policy_master_cache_v2"
    assert stats["tile_stack_mode"] == "stack_engine_cpu"
    assert stats["stack_engine_fallback_reason"] == (
        "resident_hardened_winsorized_requires_winsorized_sigma_rejection"
    )
    assert stats["stack_engine_enabled"] is True
    assert stats["master_rejection_requested"] == "minmax"
    assert stats["master_rejection_applied"] == "minmax"
    assert stats["master_rejection_dispatch_reason"] == (
        "resident_master_cache_applied_policy_with_cpu_stack_engine"
    )
    assert stats["flat_normalization"]["normalization_stage"] == "master_after_stack"
    assert dark_exposure == 120.0
    assert np.allclose(bias, 11.5)
    assert np.allclose(dark, 91.5)
    assert np.allclose(flat, 1.0)
    assert stats["stack_engine_metrics"]["bias"]["rejection"] == "minmax"
    assert stats["stack_engine_metrics"]["bias"]["master_rejection_applied"] == "minmax"
    assert stats["stack_engine_metrics"]["bias"]["resident_master_cache_builder_dispatch"] == (
        "cpu_stack_engine_tiled_rejection"
    )
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
    assert cached_stats["cache_hit_load_mode"] == "npy_mmap_readonly"
    assert isinstance(cached_bias, np.memmap)
    assert isinstance(cached_dark, np.memmap)
    assert isinstance(cached_flat, np.memmap)
    assert np.allclose(cached_bias, bias)
    assert np.allclose(cached_dark, dark)
    assert np.allclose(cached_flat, flat)


def test_resident_matching_master_cache_can_use_resident_cuda_hardened_winsorized_builder(
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

        def integrate_hardened_winsorized_sigma_timed(
            self,
            weights=None,
            low_sigma: float = 3.0,
            high_sigma: float = 3.0,
        ):
            stack = np.stack([frame for frame in self.frames if frame is not None], axis=0)
            master, weight, coverage, low, high = weighted_integrate_stack(
                stack,
                weights=weights,
                rejection="winsorized_sigma",
                low_sigma=low_sigma,
                high_sigma=high_sigma,
            )
            return master, weight, coverage, low, high, {
                "native_method": "ResidentCalibratedStack.integrate_hardened_winsorized_sigma",
                "resident_winsorized_mode": "hardened_cpu_parity",
                "total_s": 0.01,
            }

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

    monkeypatch.setattr(resident_cuda, "_resident_master_cuda_mean_available", lambda: (True, ""))
    monkeypatch.setattr(resident_cuda, "read_simple_fits_image_native_direct_timed", fake_native_read)
    monkeypatch.setattr("glass_cuda.ResidentCalibratedStack", FakeResidentCalibratedStack)

    bias_ids = _write_constant_frames(tmp_path, "B", [10.0, 10.0, 10.0, 1000.0], exposure_s=0.0)
    dark_ids = _write_constant_frames(tmp_path, "D", [100.0, 102.0, 104.0, 1000.0], exposure_s=120.0)
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
        "B": {"group_id": "B", "group_type": "bias", "frames": bias_ids, "shape": shape},
        "D": {"group_id": "D", "group_type": "dark", "frames": dark_ids, "shape": shape},
        "F": {"group_id": "F", "group_type": "flat", "frames": flat_ids, "shape": shape},
    }
    policy = CalibrationPolicy(
        master_dark_includes_bias=False,
        flat_normalization="median",
        flat_floor=0.05,
        master_rejection="winsorized_sigma",
        master_rejection_low_sigma=1.0,
        master_rejection_high_sigma=1.0,
        master_rejection_iterations=1,
        master_rejection_min_samples=3,
        master_rejection_max_fraction=0.5,
    )

    bias, dark, flat, stats, dark_exposure = _load_or_build_matching_masters(
        tmp_path / "run_cuda_winsor",
        "H",
        4,
        4,
        frames,
        groups,
        "B",
        "D",
        "F",
        policy,
        master_cache_dir=tmp_path / "shared_cuda_winsor_cache",
    )

    expected_bias = weighted_integrate_stack(
        np.stack([np.full((4, 4), value, dtype=np.float32) for value in [10.0, 10.0, 10.0, 1000.0]]),
        rejection="winsorized_sigma",
        low_sigma=1.0,
        high_sigma=1.0,
    )[0]
    expected_dark_raw = weighted_integrate_stack(
        np.stack([np.full((4, 4), value, dtype=np.float32) for value in [100.0, 102.0, 104.0, 1000.0]]),
        rejection="winsorized_sigma",
        low_sigma=1.0,
        high_sigma=1.0,
    )[0]

    assert len(FakeResidentCalibratedStack.instances) == 3
    assert stats["cache_hit"] is False
    assert stats["tile_stack_mode"] == "stack_engine_cuda_hardened_winsorized"
    assert stats["stack_engine_fallback_reason"] is None
    assert stats["cache_builder"] == "resident_stack_engine_resident_cuda_policy_master_cache_v2"
    assert stats["master_rejection_applied"] == "winsorized_sigma"
    assert stats["master_rejection_dispatch_reason"] == (
        "resident_master_cache_applied_policy_with_resident_cuda_hardened_winsorized"
    )
    bias_metrics = stats["stack_engine_metrics"]["bias"]
    assert bias_metrics["execution_path"] == "resident_cuda_hardened_winsorized_sigma"
    assert bias_metrics["resident_master_cache_builder_dispatch"] == (
        "resident_cuda_native_direct_hardened_winsorized"
    )
    assert bias_metrics["resident_winsorized_mode"] == "hardened_cpu_parity"
    assert bias_metrics["resident_hardened_policy_guard"]["triggered_pixels"] == 0
    assert bias_metrics["result_contract_passed"] is True
    assert stats["dq_provenance_summary"]["bias"]["engine"] == "stack_engine_cuda_hardened_winsorized"
    assert stats["dq_provenance_summary"]["bias"]["sample_accounting_closure"]["status"] == "passed"
    assert dark_exposure == 120.0
    assert np.allclose(bias, expected_bias)
    assert np.allclose(dark, expected_dark_raw - expected_bias)
    assert np.allclose(np.median(flat), 1.0)


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
    policy = CalibrationPolicy(
        master_dark_includes_bias=False,
        flat_normalization="median",
        flat_floor=0.05,
        master_rejection="none",
        master_rejection_iterations=0,
    )

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
    assert stats["cache_builder"] == "resident_stack_engine_resident_cuda_policy_master_cache_v2"
    assert stats["stack_engine_metrics"]["bias"]["execution_path"] == "resident_cuda_mean_no_rejection"
    assert stats["stack_engine_metrics"]["bias"]["resident_master_cache_builder_dispatch"] == (
        "resident_cuda_native_direct_mean"
    )
    assert stats["stack_engine_metrics"]["bias"]["resident_master_cache_builder"] == (
        "ResidentCalibratedStack.integrate_mean"
    )
    assert stats["stack_engine_metrics"]["bias"]["master_rejection_applied"] == "none"
    assert stats["stack_engine_metrics"]["bias"]["fits_backend_counts"] == {"fake_native_direct_simple": 2}
    assert stats["dq_provenance_summary"]["bias"]["engine"] == "stack_engine_cuda_mean"
    assert stats["dq_provenance_summary"]["bias"]["sample_accounting_closure"]["status"] == "passed"
    assert dark_exposure == 120.0
    assert np.allclose(bias, 11.0)
    assert np.allclose(dark, 91.0)
    assert np.allclose(flat, 1.0)


def test_resident_matching_master_cache_prefers_raw_u16_gpu_decode(
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

        def calibrate_frames_fits_u16be_bzero_host_async_multistream_callback_release_timed(
            self,
            indices,
            raw_lights,
            light_exposures_s,
            dark_exposures_s,
            stream_count: int,
            wave_frames: int,
            release_callback,
            policy=None,
        ):
            del light_exposures_s, dark_exposures_s, policy
            raw_h2d_bytes = 0
            for index, raw in zip(indices, raw_lights, strict=True):
                raw_array = np.asarray(raw, dtype=np.uint8)
                raw_h2d_bytes += int(raw_array.nbytes)
                bits = np.frombuffer(raw_array.tobytes(), dtype=">u2")
                values = (bits ^ np.uint16(0x8000)).astype(np.float32).reshape(self.height, self.width)
                self.frames[int(index)] = values
            release_callback(list(indices))
            return {
                "source_sample_format": "fits_bitpix16_bzero32768_big_endian",
                "raw_h2d_bytes": raw_h2d_bytes,
                "float32_host_bytes_avoided": raw_h2d_bytes * 2,
                "requested_stream_count": int(stream_count),
                "stream_count": int(stream_count),
                "requested_wave_frames": int(wave_frames),
                "wave_frames": int(wave_frames),
                "frame_count": len(list(indices)),
                "total_s": 0.01,
            }

        def integrate_mean(self):
            stack = np.stack([frame for frame in self.frames if frame is not None], axis=0)
            finite = np.isfinite(stack)
            sums = np.where(finite, stack, 0.0).sum(axis=0, dtype=np.float64)
            weight = finite.sum(axis=0, dtype=np.float32)
            master = np.divide(sums, weight, out=np.zeros_like(sums), where=weight > 0).astype(np.float32)
            return master, weight.astype(np.float32)

    raw_values: dict[str, float] = {}

    def write_raw_named(prefix: str, values: list[float]) -> list[str]:
        frame_ids: list[str] = []
        for index, value in enumerate(values):
            frame_id = f"{prefix}{index}"
            frame_ids.append(frame_id)
            path = tmp_path / f"{frame_id}.fits"
            path.write_bytes(b"raw placeholder")
            raw_values[str(path)] = float(value)
        return frame_ids

    def fake_spec(path):
        return SimpleFitsImageSpec(
            path=Path(path),
            bitpix=16,
            width=4,
            height=4,
            data_offset=0,
            dtype=np.dtype(">i2"),
            bscale=1.0,
            bzero=32768.0,
            blank=None,
        )

    def fake_raw_read(path, output=None, spec=None):
        value = int(raw_values[str(Path(path))])
        bits = np.full(16, value ^ 0x8000, dtype=">u2")
        raw = bits.view(np.uint8).copy()
        if output is not None:
            output[...] = raw
            raw = output
        return raw, {
            "fits_reader_backend": "native_u16be_raw",
            "fits_native_file_read_s": 0.001,
            "fits_native_decode_s": 0.0,
            "fits_native_total_s": 0.001,
            "fits_native_bytes_read": int(raw.nbytes),
        }

    monkeypatch.setattr(resident_cuda, "_resident_master_cuda_mean_available", lambda: (True, ""))
    monkeypatch.setattr(resident_cuda, "simple_fits_image_spec", fake_spec)
    monkeypatch.setattr(resident_cuda, "read_simple_fits_u16be_raw_timed", fake_raw_read)
    monkeypatch.setattr(
        resident_cuda,
        "read_simple_fits_image_native_direct_timed",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("raw path should not use native-direct float read")),
    )
    monkeypatch.setattr("glass_cuda.ResidentCalibratedStack", FakeResidentCalibratedStack)

    bias_ids = write_raw_named("B", [10.0, 12.0])
    dark_ids = write_raw_named("D", [100.0, 104.0])
    flat_ids = write_raw_named("F", [100.0, 120.0])
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
    policy = CalibrationPolicy(
        master_dark_includes_bias=False,
        flat_normalization="median",
        flat_floor=0.05,
        master_rejection="none",
        master_rejection_iterations=0,
    )

    bias, dark, flat, stats, dark_exposure = _load_or_build_matching_masters(
        tmp_path / "run_raw",
        "H",
        4,
        4,
        frames,
        groups,
        "B",
        "D",
        "F",
        policy,
        master_cache_dir=tmp_path / "shared_raw_cache",
    )

    assert len(FakeResidentCalibratedStack.instances) == 3
    assert stats["tile_stack_mode"] == "stack_engine_cuda_mean"
    assert stats["cache_builder"] == "resident_stack_engine_resident_cuda_policy_master_cache_v2"
    assert stats["stack_engine_metrics"]["bias"]["resident_master_cache_builder_dispatch"] == (
        "resident_cuda_raw_u16_mean"
    )
    assert stats["stack_engine_metrics"]["bias"]["raw_u16_gpu_decode_enabled"] is True
    assert stats["stack_engine_metrics"]["bias"]["raw_h2d_bytes"] == 64
    assert stats["stack_engine_metrics"]["bias"]["raw_float32_host_bytes_avoided"] == 128
    assert stats["stack_engine_metrics"]["bias"]["fits_backend_counts"] == {"native_u16be_raw": 2}
    assert stats["dq_provenance_summary"]["bias"]["engine"] == "stack_engine_cuda_mean"
    assert stats["dq_provenance_summary"]["bias"]["sample_accounting_closure"]["status"] == "passed"
    assert dark_exposure == 120.0
    assert np.allclose(bias, 11.0)
    assert np.allclose(dark, 91.0)
    assert np.allclose(flat, 1.0)
