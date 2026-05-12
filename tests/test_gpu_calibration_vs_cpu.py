from __future__ import annotations

import numpy as np
from dataclasses import asdict

from gpwbpp.cpu.calibration import calibrate_light
from gpwbpp.models import CalibrationPolicy
from tests.conftest import cuda_module_or_skip


def test_gpu_calibration_matches_cpu():
    module = cuda_module_or_skip()
    light = np.full((8, 8), 1200, dtype=np.float32)
    bias = np.full((8, 8), 100, dtype=np.float32)
    dark = np.full((8, 8), 120, dtype=np.float32)
    flat = np.full((8, 8), 2, dtype=np.float32)
    policy = CalibrationPolicy(master_dark_includes_bias=True, dark_scaling_enabled=False)
    cpu = calibrate_light(light, bias, dark, flat, 60, 60, policy)
    gpu = module.calibrate_tile_f32(light, bias, dark, flat, 60, 60, asdict(policy))
    assert np.allclose(gpu, cpu, rtol=1e-5, atol=1e-5)
