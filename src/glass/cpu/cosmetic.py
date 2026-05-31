from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from glass.engine.contracts import DQFlag, DQMask


def replace_hot_pixels(data: np.ndarray, threshold_sigma: float = 8.0) -> np.ndarray:
    median = float(np.median(data))
    sigma = float(np.std(data))
    out = data.copy()
    out[out > median + threshold_sigma * sigma] = median
    return out


@dataclass(slots=True)
class CosmeticCorrectionResult:
    data: np.ndarray
    dq_mask: DQMask
    metrics: dict[str, float | int]


def correct_cosmetic_defects(
    data: np.ndarray,
    hot_sigma: float = 8.0,
    cold_sigma: float = 8.0,
) -> CosmeticCorrectionResult:
    image = np.asarray(data, dtype=np.float32)
    finite = image[np.isfinite(image)]
    if finite.size == 0:
        return CosmeticCorrectionResult(
            data=image.copy(),
            dq_mask=DQMask.empty(image.shape).mark(DQFlag.NO_DATA),
            metrics={"median": 0.0, "sigma": 0.0, "hot_pixels": 0, "cold_pixels": 0},
        )
    median = float(np.median(finite))
    mad = float(np.median(np.abs(finite - median)))
    sigma = 1.4826 * mad if mad > 0 else float(np.std(finite))
    if sigma <= 0:
        sigma = 1.0
    hot = image > np.float32(median + float(hot_sigma) * sigma)
    cold = image < np.float32(median - float(cold_sigma) * sigma)
    invalid = ~np.isfinite(image)
    out = image.copy()
    replace = (hot | cold) & ~invalid
    out[replace] = np.float32(median)
    mask = DQMask.empty(image.shape)
    mask.mark(DQFlag.NO_DATA, invalid)
    mask.mark(DQFlag.HOT_PIXEL, hot & ~invalid)
    mask.mark(DQFlag.COLD_PIXEL, cold & ~invalid)
    mask.mark(DQFlag.COSMETIC_CORRECTED, replace)
    return CosmeticCorrectionResult(
        data=out.astype(np.float32),
        dq_mask=mask,
        metrics={
            "median": median,
            "sigma": float(sigma),
            "hot_pixels": int(np.count_nonzero(hot & ~invalid)),
            "cold_pixels": int(np.count_nonzero(cold & ~invalid)),
        },
    )
