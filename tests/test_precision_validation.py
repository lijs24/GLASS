from __future__ import annotations

import numpy as np

from gpwbpp.models import CalibrationPolicy
from gpwbpp.validation.precision import calibrate_light_f64, finite_error_stats


def test_finite_error_stats_reports_small_float32_roundoff():
    reference = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    candidate = reference.astype(np.float32)
    stats = finite_error_stats(candidate, reference)
    assert stats["finite_pixels"] == 3
    assert stats["max_abs"] < 1.0e-6
    assert stats["relative_rmse"] < 1.0e-6


def test_calibrate_light_f64_preserves_float64_reference_math():
    light = np.array([[1000.25, 1001.5]], dtype=np.float64)
    dark = np.array([[100.125, 100.25]], dtype=np.float64)
    flat = np.array([[0.99, 1.01]], dtype=np.float64)
    out = calibrate_light_f64(
        light,
        master_bias=None,
        master_dark=dark,
        master_flat=flat,
        light_exposure_s=600.0,
        dark_exposure_s=600.0,
        policy=CalibrationPolicy(master_dark_includes_bias=True),
    )
    expected = (light - dark) / flat
    assert out.dtype == np.float64
    assert np.allclose(out, expected)
