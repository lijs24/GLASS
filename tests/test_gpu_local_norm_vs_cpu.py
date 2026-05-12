from __future__ import annotations

import numpy as np

from gpwbpp.cpu.local_norm import apply_tile_normalization, estimate_tile_normalization_mean_std
from tests.conftest import cuda_module_or_skip


def test_gpu_local_norm_apply_matches_cpu():
    module = cuda_module_or_skip()
    data = np.arange(36, dtype=np.float32).reshape(6, 6)
    scale = 1.75
    offset = -3.5
    gpu = module.local_norm_apply_f32(data, scale, offset)
    cpu = apply_tile_normalization(data, scale, offset)
    assert np.allclose(gpu, cpu)


def test_gpu_local_norm_pair_stats_matches_cpu_mean_std():
    module = cuda_module_or_skip()
    data = np.arange(36, dtype=np.float32).reshape(6, 6)
    reference = data * 1.25 + 11.0
    data[0, 0] = np.nan
    reference[5, 5] = np.nan
    gpu_stats = module.local_norm_pair_stats_f32(data, reference)
    cpu_stats = estimate_tile_normalization_mean_std(data, reference)
    assert gpu_stats["stats_backend"] == "cuda"
    assert gpu_stats["valid_pixels"] == cpu_stats["valid_pixels"]
    assert np.isclose(gpu_stats["source_mean"], cpu_stats["source_mean"], atol=1.0e-5)
    assert np.isclose(gpu_stats["reference_mean"], cpu_stats["reference_mean"], atol=1.0e-5)
    assert np.isclose(gpu_stats["source_std"], cpu_stats["source_std"], atol=1.0e-5)
    assert np.isclose(gpu_stats["reference_std"], cpu_stats["reference_std"], atol=1.0e-5)


def test_gpu_local_norm_estimate_apply_mean_std_matches_cpu_masked():
    module = cuda_module_or_skip()
    yy, xx = np.indices((8, 9), dtype=np.float32)
    data = 3.0 + xx + yy * 2.0
    reference = data * 0.75 + 5.0
    mask = np.ones_like(data, dtype=bool)
    mask[:2, :3] = False
    gpu, stats = module.local_norm_estimate_apply_mean_std_f32(data, reference, mask)
    cpu_stats = estimate_tile_normalization_mean_std(data, reference, mask)
    cpu = apply_tile_normalization(data, cpu_stats["scale"], cpu_stats["offset"], mask)
    assert stats["stats_backend"] == "cuda"
    assert stats["status"] == "ok"
    assert np.allclose(gpu, cpu, atol=1.0e-5)
    assert np.allclose(gpu[~mask], data[~mask])
