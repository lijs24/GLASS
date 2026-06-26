from __future__ import annotations

from pathlib import Path

import numpy as np

from glass.cpu.master_frames import make_master_bias as make_master_bias_cpu
import glass.gpu.master_frames as master_frames_module
from glass.gpu.master_frames import (
    make_master_bias,
    make_master_dark,
    make_master_flat,
    mean_stack_paths_tile_streaming,
)
from glass.synthetic.generator import generate_synthetic_dataset
from tests.conftest import cuda_module_or_skip


def test_mean_stack_streaming_accumulator_without_cuda_stack(tmp_path: Path, monkeypatch):
    out = tmp_path / "synthetic"
    generate_synthetic_dataset(out, frames=4, width=32, height=24)
    bias_paths = sorted((out / "bias").glob("*.fits"))
    cpu = make_master_bias_cpu(bias_paths)

    monkeypatch.setattr(master_frames_module, "_native_module", lambda: None)

    def fail_stack(*args, **kwargs):
        raise AssertionError("mean stack helper should not build a 3D tile stack")

    monkeypatch.setattr(np, "stack", fail_stack)
    streaming = mean_stack_paths_tile_streaming(bias_paths, tile_size=11)
    assert np.allclose(streaming.data, cpu.data, rtol=1e-5, atol=1e-5)
    assert streaming.engine == "cpu_tile_streaming_mean_fallback"
    assert streaming.metrics is not None
    assert streaming.metrics["cuda_native_available"] is False
    assert streaming.metrics["cuda_accumulator_used"] is False
    assert streaming.metrics["tile_count"] > 1
    assert streaming.dq_provenance is not None
    assert streaming.dq_provenance["engine"] == "cpu_tile_streaming_mean_fallback"
    assert streaming.dq_mask is None


def test_mean_stack_streaming_accumulator_reports_fake_native_usage(tmp_path: Path, monkeypatch):
    out = tmp_path / "synthetic"
    generate_synthetic_dataset(out, frames=3, width=20, height=16)
    bias_paths = sorted((out / "bias").glob("*.fits"))
    cpu = make_master_bias_cpu(bias_paths)

    class FakeNative:
        def __init__(self) -> None:
            self.calls = 0

        def integrate_accumulate_mean_tile_f32(self, frame_tile, weight_tile, sum_tile, weight_sum_tile):
            self.calls += 1
            return sum_tile + frame_tile * weight_tile, weight_sum_tile + weight_tile

    fake_native = FakeNative()
    monkeypatch.setattr(master_frames_module, "_native_module", lambda: fake_native)

    streaming = mean_stack_paths_tile_streaming(bias_paths, tile_size=7)

    assert fake_native.calls > 0
    assert np.allclose(streaming.data, cpu.data, rtol=1e-5, atol=1e-5)
    assert streaming.engine == "cuda_tile_streaming_mean"
    assert streaming.metrics is not None
    assert streaming.metrics["cuda_native_available"] is True
    assert streaming.metrics["cuda_accumulator_used"] is True
    assert streaming.metrics["public_helper"] == "glass.gpu.master_frames.mean_stack_paths_tile_streaming"
    assert streaming.dq_provenance is not None
    assert streaming.dq_provenance["execution_path"] == "gpu_master_tile_streaming_mean"


def test_gpu_mean_stack_matches_cpu(tmp_path: Path):
    cuda_module_or_skip()
    out = tmp_path / "synthetic"
    generate_synthetic_dataset(out, frames=4, width=32, height=24)
    bias_paths = sorted((out / "bias").glob("*.fits"))
    cpu = make_master_bias_cpu(bias_paths)
    gpu = mean_stack_paths_tile_streaming(bias_paths, tile_size=11)
    assert np.allclose(gpu.data, cpu.data, rtol=1e-5, atol=1e-5)


def test_gpu_master_bias_dark_flat_match_cpu_shape_and_stats(tmp_path: Path):
    cuda_module_or_skip()
    out = tmp_path / "synthetic"
    generate_synthetic_dataset(out, frames=4, width=32, height=24)
    bias_paths = sorted((out / "bias").glob("*.fits"))
    dark_paths = sorted((out / "dark").glob("*.fits"))
    flat_paths = sorted((out / "flat").glob("*.fits"))
    bias = make_master_bias(bias_paths, tile_size=13)
    dark = make_master_dark(dark_paths, master_bias=bias.data, tile_size=13)
    flat = make_master_flat(flat_paths, master_bias=bias.data, tile_size=13)
    assert bias.data.shape == (24, 32)
    assert dark.data.shape == (24, 32)
    assert flat.data.shape == (24, 32)
    assert bias.engine == "cuda_tile_streaming_mean"
    assert dark.engine == "cuda_tile_streaming_mean"
    assert flat.engine == "cuda_tile_streaming_mean"
    assert bias.metrics is not None
    assert dark.metrics is not None
    assert flat.metrics is not None
    assert bias.metrics["master_postprocess_operation"] == "bias_mean"
    assert dark.metrics["master_postprocess_operation"] == "dark_mean_minus_master_bias"
    assert flat.metrics["master_postprocess_operation"] == "flat_mean_calibrated_normalized"
    assert 0.98 < flat.stats["median"] < 1.02
