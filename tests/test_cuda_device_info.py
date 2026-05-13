from __future__ import annotations

from tests.conftest import cuda_api_module


def test_cuda_device_info():
    module = cuda_api_module()
    devices = module.list_devices()
    assert isinstance(devices, list)
    if devices:
        info = module.get_device_info(0)
        assert "name" in info
        assert "available_to_glass" in info
