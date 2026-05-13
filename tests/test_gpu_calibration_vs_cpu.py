from __future__ import annotations

import numpy as np
from dataclasses import asdict

from glass.cpu.calibration import calibrate_light
from glass.models import CalibrationPolicy
from tests.conftest import cuda_module_or_skip


def test_gpu_calibration_matches_cpu():
    module = cuda_module_or_skip()
    assert module.native_extension_loaded() is True
    light = np.full((8, 8), 1200, dtype=np.float32)
    bias = np.full((8, 8), 100, dtype=np.float32)
    dark = np.full((8, 8), 120, dtype=np.float32)
    flat = np.full((8, 8), 2, dtype=np.float32)
    policy = CalibrationPolicy(master_dark_includes_bias=True, dark_scaling_enabled=False)
    cpu = calibrate_light(light, bias, dark, flat, 60, 60, policy)
    gpu = module.calibrate_tile_f32(light, bias, dark, flat, 60, 60, asdict(policy))
    assert np.allclose(gpu, cpu, rtol=1e-5, atol=1e-5)


def test_gpu_calibration_dark_excludes_bias_and_scaling_matches_cpu():
    module = cuda_module_or_skip()
    light = np.full((8, 8), 1220, dtype=np.float32)
    bias = np.full((8, 8), 100, dtype=np.float32)
    dark = np.full((8, 8), 10, dtype=np.float32)
    flat = np.full((8, 8), 2, dtype=np.float32)
    policy = CalibrationPolicy(master_dark_includes_bias=False, dark_scaling_enabled=True)
    cpu = calibrate_light(light, bias, dark, flat, 120, 60, policy)
    gpu = module.calibrate_tile_f32(light, bias, dark, flat, 120, 60, asdict(policy))
    assert np.allclose(gpu, cpu, rtol=1e-5, atol=1e-5)


def test_gpu_calibration_flat_floor_and_pedestal_matches_cpu():
    module = cuda_module_or_skip()
    light = np.full((4, 4), 12, dtype=np.float32)
    flat = np.zeros((4, 4), dtype=np.float32)
    policy = CalibrationPolicy(flat_floor=2.0, pedestal=1.5)
    cpu = calibrate_light(light, None, None, flat, 60, None, policy)
    gpu = module.calibrate_tile_f32(light, None, None, flat, 60, None, asdict(policy))
    assert np.allclose(gpu, cpu, rtol=1e-5, atol=1e-5)
