from __future__ import annotations

import numpy as np

from gpwbpp.cpu.local_norm import apply_tile_normalization
from tests.conftest import cuda_module_or_skip


def test_gpu_local_norm_apply_matches_cpu():
    module = cuda_module_or_skip()
    data = np.arange(36, dtype=np.float32).reshape(6, 6)
    scale = 1.75
    offset = -3.5
    gpu = module.local_norm_apply_f32(data, scale, offset)
    cpu = apply_tile_normalization(data, scale, offset)
    assert np.allclose(gpu, cpu)
