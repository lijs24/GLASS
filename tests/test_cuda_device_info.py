from __future__ import annotations

from tests.conftest import cuda_module_or_skip


def test_cuda_device_info():
    module = cuda_module_or_skip()
    devices = module.list_devices()
    assert isinstance(devices, list)
    if devices:
        info = module.get_device_info(0)
        assert "name" in info

