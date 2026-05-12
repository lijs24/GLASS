from __future__ import annotations

import numpy as np

from gpwbpp.cpu.warp import warp_translation
from tests.conftest import cuda_module_or_skip


def test_gpu_warp_translation_matches_cpu():
    module = cuda_module_or_skip()
    data = np.arange(25, dtype=np.float32).reshape(5, 5)
    gpu, coverage = module.warp_translation_f32(data, 1, -2, 0.0)
    cpu = warp_translation(data, 1, -2, 0.0)
    assert np.allclose(gpu, cpu)
    assert coverage.shape == data.shape
    assert np.sum(coverage) == 12
