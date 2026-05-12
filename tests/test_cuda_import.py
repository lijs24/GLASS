from __future__ import annotations

from tests.conftest import cuda_module_or_skip


def test_cuda_import_available_when_built():
    module = cuda_module_or_skip()
    assert module.cuda_available() is True

