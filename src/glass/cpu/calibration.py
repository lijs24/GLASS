from __future__ import annotations

import numpy as np

from glass.models import CalibrationPolicy


def apply_overscan_trim(
    data: np.ndarray,
    overscan_columns: int = 0,
    overscan_rows: int = 0,
    trim: bool = True,
) -> tuple[np.ndarray, dict[str, float | int | bool]]:
    image = np.asarray(data, dtype=np.float32)
    columns = max(0, int(overscan_columns))
    rows = max(0, int(overscan_rows))
    if columns == 0 and rows == 0:
        return image.astype(np.float32, copy=True), {
            "enabled": False,
            "overscan_columns": 0,
            "overscan_rows": 0,
            "trim": bool(trim),
            "level": 0.0,
        }
    samples: list[np.ndarray] = []
    if columns:
        if columns >= image.shape[1]:
            raise ValueError("overscan_columns must be smaller than image width")
        samples.append(image[:, -columns:].ravel())
    if rows:
        if rows >= image.shape[0]:
            raise ValueError("overscan_rows must be smaller than image height")
        samples.append(image[-rows:, :].ravel())
    overscan = np.concatenate(samples) if samples else np.asarray([], dtype=np.float32)
    finite = overscan[np.isfinite(overscan)]
    level = float(np.median(finite)) if finite.size else 0.0
    corrected = (image - np.float32(level)).astype(np.float32)
    if trim:
        y1 = corrected.shape[0] - rows if rows else corrected.shape[0]
        x1 = corrected.shape[1] - columns if columns else corrected.shape[1]
        corrected = corrected[:y1, :x1].copy()
    return corrected, {
        "enabled": True,
        "overscan_columns": columns,
        "overscan_rows": rows,
        "trim": bool(trim),
        "level": level,
    }


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
