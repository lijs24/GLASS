from __future__ import annotations

import numpy as np

from gpwbpp.cpu.local_norm import (
    apply_grid_normalization,
    apply_tile_normalization,
    estimate_grid_normalization_mean_std,
    estimate_tile_normalization_mean_std,
)
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


def test_gpu_local_norm_apply_grid_matches_cpu():
    module = cuda_module_or_skip()
    data = np.arange(63, dtype=np.float32).reshape(7, 9)
    scales = np.array([[1.0, 1.5], [0.75, 2.0]], dtype=np.float32)
    offsets = np.array([[0.0, 3.0], [-2.0, 7.0]], dtype=np.float32)

    gpu = module.local_norm_apply_grid_f32(data, scales, offsets, 4, 5)
    cpu = apply_grid_normalization(data, scales, offsets, tile_height=4, tile_width=5)

    assert np.allclose(gpu, cpu, atol=1.0e-5)


def test_gpu_local_norm_grid_estimate_cpu_apply_matches_reference_tiles():
    module = cuda_module_or_skip()
    yy, xx = np.indices((8, 10), dtype=np.float32)
    data = 5.0 + xx * 0.3 + yy * 1.2
    reference = data.copy()
    reference[:4, :5] = data[:4, :5] * 1.4 + 8.0
    reference[:4, 5:] = data[:4, 5:] * 0.8 - 1.0
    reference[4:, :5] = data[4:, :5] * 1.1 + 2.0
    reference[4:, 5:] = data[4:, 5:] * 0.6 + 14.0
    model = estimate_grid_normalization_mean_std(data, reference, tile_height=4, tile_width=5)

    gpu = module.local_norm_apply_grid_f32(data, model["scales"], model["offsets"], 4, 5)

    for y0, y1 in [(0, 4), (4, 8)]:
        for x0, x1 in [(0, 5), (5, 10)]:
            assert np.allclose(np.mean(gpu[y0:y1, x0:x1]), np.mean(reference[y0:y1, x0:x1]), atol=1.0e-5)
            assert np.allclose(np.std(gpu[y0:y1, x0:x1]), np.std(reference[y0:y1, x0:x1]), atol=1.0e-5)
