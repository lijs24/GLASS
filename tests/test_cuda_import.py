from __future__ import annotations

from tests.conftest import cuda_api_module


def test_cuda_import_api_available():
    module = cuda_api_module()
    assert isinstance(module.cuda_available(), bool)
    assert hasattr(module, "list_devices")
    assert hasattr(module, "smoke_add_f32")
