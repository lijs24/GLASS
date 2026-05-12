from __future__ import annotations

import numpy as np

from gpwbpp.models import CalibrationPolicy


def calibrate_light(
    light: np.ndarray,
    master_bias: np.ndarray | None,
    master_dark: np.ndarray | None,
    master_flat: np.ndarray | None,
    light_exposure_s: float,
    dark_exposure_s: float | None,
    policy: CalibrationPolicy | None = None,
) -> np.ndarray:
    policy = policy or CalibrationPolicy()
    calibrated = light.astype(np.float32, copy=True)
    if master_dark is not None:
        scale = 1.0
        if policy.dark_scaling_enabled and dark_exposure_s not in (None, 0):
            scale = float(light_exposure_s) / float(dark_exposure_s)
        calibrated = calibrated - master_dark.astype(np.float32) * scale
        if not policy.master_dark_includes_bias and master_bias is not None:
            calibrated = calibrated - master_bias.astype(np.float32)
    elif master_bias is not None:
        calibrated = calibrated - master_bias.astype(np.float32)
    if master_flat is not None:
        flat = np.maximum(master_flat.astype(np.float32), policy.flat_floor)
        calibrated = calibrated / flat
    if policy.pedestal:
        calibrated = calibrated + float(policy.pedestal)
    return calibrated.astype(np.float32)

