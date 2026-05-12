from __future__ import annotations

import numpy as np

from gpwbpp.cpu.calibration import calibrate_light
from gpwbpp.models import CalibrationPolicy


def test_calibrate_light_dark_includes_bias_semantics():
    light = np.full((4, 4), 1200.0, dtype=np.float32)
    bias = np.full((4, 4), 100.0, dtype=np.float32)
    dark_includes_bias = np.full((4, 4), 120.0, dtype=np.float32)
    flat = np.ones((4, 4), dtype=np.float32) * 2.0
    policy = CalibrationPolicy(master_dark_includes_bias=True, dark_scaling_enabled=False)
    calibrated = calibrate_light(light, bias, dark_includes_bias, flat, 60.0, 60.0, policy)
    assert np.allclose(calibrated, 540.0)


def test_calibrate_light_dark_excludes_bias_semantics():
    light = np.full((4, 4), 1200.0, dtype=np.float32)
    bias = np.full((4, 4), 100.0, dtype=np.float32)
    dark_excludes_bias = np.full((4, 4), 20.0, dtype=np.float32)
    flat = np.ones((4, 4), dtype=np.float32) * 2.0
    policy = CalibrationPolicy(master_dark_includes_bias=False, dark_scaling_enabled=False)
    calibrated = calibrate_light(light, bias, dark_excludes_bias, flat, 60.0, 60.0, policy)
    assert np.allclose(calibrated, 540.0)

