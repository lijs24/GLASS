from __future__ import annotations

import numpy as np

from tests.conftest import cuda_module_or_skip


def test_cuda_smoke_add():
    module = cuda_module_or_skip()
    a = np.array([1, 2, 3], dtype=np.float32)
    b = np.array([4, 5, 6], dtype=np.float32)
    assert np.allclose(module.smoke_add_f32(a, b), a + b)

