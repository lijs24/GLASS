from __future__ import annotations

import numpy as np

from tests.conftest import cuda_module_or_skip


def test_gpu_integration_accumulator_matches_cpu():
    module = cuda_module_or_skip()
    frame = np.arange(16, dtype=np.float32).reshape(4, 4)
    weight = np.ones((4, 4), dtype=np.float32) * 2
    sums = np.ones((4, 4), dtype=np.float32)
    weight_sums = np.ones((4, 4), dtype=np.float32) * 3
    gpu_sum, gpu_weight = module.integrate_accumulate_mean_tile_f32(frame, weight, sums, weight_sums)
    assert np.allclose(gpu_sum, sums + frame * weight)
    assert np.allclose(gpu_weight, weight_sums + weight)
