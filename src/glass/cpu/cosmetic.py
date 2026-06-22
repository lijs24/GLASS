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


def _global_robust_location_scale(image: np.ndarray) -> tuple[np.ndarray, float, float]:
    finite = image[np.isfinite(image)]
    if finite.size == 0:
        return finite, 0.0, 0.0
    median = float(np.median(finite))
    mad = float(np.median(np.abs(finite - np.float32(median))))
    sigma = 1.4826 * mad if mad > 0 else float(np.std(finite))
    if sigma <= 0:
        sigma = 1.0
    return finite, median, float(sigma)


def _eight_neighbors(image: np.ndarray) -> np.ndarray:
    padded = np.pad(image, 1, mode="edge")
    return np.stack(
        [
            padded[0:-2, 0:-2],
            padded[0:-2, 1:-1],
            padded[0:-2, 2:],
            padded[1:-1, 0:-2],
            padded[1:-1, 2:],
            padded[2:, 0:-2],
            padded[2:, 1:-1],
            padded[2:, 2:],
        ],
        axis=0,
    ).astype(np.float32, copy=False)


def detect_isolated_cosmetic_defects(
    data: np.ndarray,
    hot_sigma: float = 8.0,
    cold_sigma: float = 8.0,
    structure_sigma: float = 1.5,
    min_neighbor_support: int = 2,
) -> CosmeticCorrectionResult:
    """Detect isolated cosmetic defects while protecting star-like structure.

    This CPU baseline is intentionally conservative for light-frame source-DQ:
    a hot/cold candidate must be a strong global and local outlier, and it must
    lack enough same-sign support in the 8-neighborhood. Compact stars usually
    have bright neighboring pixels, so their cores are not treated as isolated
    hot pixels by this model.
    """

    image = np.asarray(data, dtype=np.float32)
    finite, median, sigma = _global_robust_location_scale(image)
    if finite.size == 0:
        return CosmeticCorrectionResult(
            data=image.copy(),
            dq_mask=DQMask.empty(image.shape).mark(DQFlag.NO_DATA),
            metrics={
                "median": 0.0,
                "sigma": 0.0,
                "hot_pixels": 0,
                "cold_pixels": 0,
                "candidate_hot_pixels": 0,
                "candidate_cold_pixels": 0,
                "protected_hot_pixels": 0,
                "protected_cold_pixels": 0,
                "structure_sigma": float(structure_sigma),
                "min_neighbor_support": int(min_neighbor_support),
            },
        )

    finite_mask = np.isfinite(image)
    invalid = ~finite_mask
    neighbors = _eight_neighbors(image)
    finite_neighbors = np.where(np.isfinite(neighbors), neighbors, np.nan)
    local_median = np.nanmedian(finite_neighbors, axis=0).astype(np.float32)
    local_median = np.where(np.isfinite(local_median), local_median, np.float32(median))

    hot_limit = np.float32(median + float(hot_sigma) * sigma)
    cold_limit = np.float32(median - float(cold_sigma) * sigma)
    hot_delta = np.float32(float(hot_sigma) * sigma)
    cold_delta = np.float32(float(cold_sigma) * sigma)
    hot_candidates = finite_mask & (image > hot_limit) & ((image - local_median) > hot_delta)
    cold_candidates = finite_mask & (image < cold_limit) & ((local_median - image) > cold_delta)

    support_sigma = max(0.0, float(structure_sigma))
    hot_support_limit = np.float32(median + support_sigma * sigma)
    cold_support_limit = np.float32(median - support_sigma * sigma)
    hot_support = np.count_nonzero(finite_neighbors > hot_support_limit, axis=0)
    cold_support = np.count_nonzero(finite_neighbors < cold_support_limit, axis=0)
    support_required = max(0, int(min_neighbor_support))
    hot = hot_candidates & (hot_support < support_required)
    cold = cold_candidates & (cold_support < support_required)
    protected_hot = hot_candidates & ~hot
    protected_cold = cold_candidates & ~cold

    replace = (hot | cold) & ~invalid
    out = image.copy()
    out[replace] = local_median[replace]
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
            "candidate_hot_pixels": int(np.count_nonzero(hot_candidates)),
            "candidate_cold_pixels": int(np.count_nonzero(cold_candidates)),
            "protected_hot_pixels": int(np.count_nonzero(protected_hot)),
            "protected_cold_pixels": int(np.count_nonzero(protected_cold)),
            "structure_sigma": float(structure_sigma),
            "min_neighbor_support": int(min_neighbor_support),
        },
    )
