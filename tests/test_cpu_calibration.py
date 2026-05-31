from __future__ import annotations

import numpy as np

from glass.cpu.calibration import apply_overscan_trim, calibrate_light
from glass.cpu.cosmetic import correct_cosmetic_defects
from glass.engine.contracts import DQFlag
from glass.models import CalibrationPolicy


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


def test_calibrate_light_applies_pedestal_after_flat_division():
    light = np.full((2, 2), 20.0, dtype=np.float32)
    flat = np.full((2, 2), 2.0, dtype=np.float32)
    policy = CalibrationPolicy(pedestal=5.0)

    calibrated = calibrate_light(light, None, None, flat, 1.0, None, policy)

    assert np.allclose(calibrated, 15.0)


def test_apply_overscan_trim_subtracts_median_and_trims():
    data = np.array(
        [
            [10.0, 12.0, 100.0, 102.0],
            [14.0, 16.0, 104.0, 106.0],
            [99.0, 101.0, 103.0, 105.0],
        ],
        dtype=np.float32,
    )

    corrected, metrics = apply_overscan_trim(data, overscan_columns=2, overscan_rows=1, trim=True)

    assert corrected.shape == (2, 2)
    assert metrics["enabled"] is True
    assert metrics["level"] == 103.0
    assert np.allclose(corrected, np.array([[-93.0, -91.0], [-89.0, -87.0]], dtype=np.float32))


def test_cosmetic_correction_marks_hot_cold_and_corrected_pixels():
    data = np.full((5, 5), 10.0, dtype=np.float32)
    data[1, 1] = 100.0
    data[2, 3] = -100.0

    result = correct_cosmetic_defects(data, hot_sigma=2.0, cold_sigma=2.0)

    assert result.data[1, 1] == 10.0
    assert result.data[2, 3] == 10.0
    assert result.dq_mask.count(DQFlag.HOT_PIXEL) == 1
    assert result.dq_mask.count(DQFlag.COLD_PIXEL) == 1
    assert result.dq_mask.count(DQFlag.COSMETIC_CORRECTED) == 2
