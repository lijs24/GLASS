from __future__ import annotations

from tests.conftest import cuda_module_or_skip


def test_gpu_integration_placeholder():
    cuda_module_or_skip()

