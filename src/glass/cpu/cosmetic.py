from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from glass.cpu.star_detect import Star, detect_stars
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
    metrics: dict[str, object]


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


def star_protection_mask(
    shape: tuple[int, int],
    stars: Sequence[Star],
    radius_px: float = 3.0,
    *,
    min_pixels: int = 3,
    max_sharpness: float = 0.95,
) -> np.ndarray:
    """Return pixels protected by plausible star catalog entries.

    Single-pixel hot defects can also be local maxima. The shape guards keep
    catalog protection limited to objects with a small footprint, not isolated
    one-sample spikes.
    """

    height, width = int(shape[0]), int(shape[1])
    protected = np.zeros((height, width), dtype=bool)
    radius = max(0.0, float(radius_px))
    if height <= 0 or width <= 0 or radius <= 0.0:
        return protected
    radius_sq = radius * radius
    for star in stars:
        if int(star.npix) < int(min_pixels):
            continue
        if star.sharpness is not None and float(star.sharpness) > float(max_sharpness):
            continue
        cx = float(star.x)
        cy = float(star.y)
        if not np.isfinite(cx) or not np.isfinite(cy):
            continue
        x0 = max(0, int(np.floor(cx - radius)))
        x1 = min(width, int(np.ceil(cx + radius)) + 1)
        y0 = max(0, int(np.floor(cy - radius)))
        y1 = min(height, int(np.ceil(cy + radius)) + 1)
        if x1 <= x0 or y1 <= y0:
            continue
        yy, xx = np.ogrid[y0:y1, x0:x1]
        protected[y0:y1, x0:x1] |= (xx - cx) * (xx - cx) + (yy - cy) * (yy - cy) <= radius_sq
    return protected


def detect_star_protected_cosmetic_defects(
    data: np.ndarray,
    hot_sigma: float = 8.0,
    cold_sigma: float = 8.0,
    structure_sigma: float = 1.5,
    min_neighbor_support: int = 2,
    *,
    star_threshold_sigma: float = 5.0,
    star_max_candidates: int = 500,
    star_protection_radius_px: float = 3.0,
    star_min_pixels: int = 3,
    star_max_sharpness: float = 0.95,
    stars: Sequence[Star] | None = None,
) -> CosmeticCorrectionResult:
    """Detect isolated defects while protecting catalog-like stellar cores.

    The underlying isolated detector remains the first line of defense. This
    wrapper adds a catalog-shaped veto for compact, under-sampled stars whose
    cores might otherwise look like isolated outliers.
    """

    image = np.asarray(data, dtype=np.float32)
    isolated = detect_isolated_cosmetic_defects(
        image,
        hot_sigma=hot_sigma,
        cold_sigma=cold_sigma,
        structure_sigma=structure_sigma,
        min_neighbor_support=min_neighbor_support,
    )
    catalog = list(stars) if stars is not None else detect_stars(
        image,
        threshold_sigma=float(star_threshold_sigma),
        max_stars=int(star_max_candidates),
        min_separation_px=max(2.0, float(star_protection_radius_px) * 0.5),
    )
    protected = star_protection_mask(
        image.shape,
        catalog,
        radius_px=star_protection_radius_px,
        min_pixels=star_min_pixels,
        max_sharpness=star_max_sharpness,
    )
    dq_bits = isolated.dq_mask.data.copy()
    hot_bits = (dq_bits & np.uint32(int(DQFlag.HOT_PIXEL))) != 0
    cold_bits = (dq_bits & np.uint32(int(DQFlag.COLD_PIXEL))) != 0
    corrected_bits = (dq_bits & np.uint32(int(DQFlag.COSMETIC_CORRECTED))) != 0
    protected_hot = protected & hot_bits
    protected_cold = protected & cold_bits
    protected_corrected = protected & corrected_bits
    protected_cosmetic = protected_hot | protected_cold | protected_corrected
    if np.any(protected_cosmetic):
        clear_bits = np.uint32(
            int(DQFlag.HOT_PIXEL) | int(DQFlag.COLD_PIXEL) | int(DQFlag.COSMETIC_CORRECTED)
        )
        keep_bits = np.uint32(0xFFFFFFFF ^ int(clear_bits))
        dq_bits[protected_cosmetic] &= keep_bits

    out = isolated.data.copy()
    out[protected_cosmetic] = image[protected_cosmetic]
    metrics = dict(isolated.metrics)
    metrics.update(
        {
            "star_protection_enabled": True,
            "star_detector": "glass.cpu.star_detect.detect_stars",
            "star_count": int(len(catalog)),
            "star_protection_radius_px": float(star_protection_radius_px),
            "star_min_pixels": int(star_min_pixels),
            "star_max_sharpness": float(star_max_sharpness),
            "star_protected_pixels": int(np.count_nonzero(protected)),
            "star_protected_hot_pixels": int(np.count_nonzero(protected_hot)),
            "star_protected_cold_pixels": int(np.count_nonzero(protected_cold)),
            "star_protected_cosmetic_pixels": int(np.count_nonzero(protected_cosmetic)),
            "isolated_hot_pixels_before_star_protection": int(isolated.metrics.get("hot_pixels", 0)),
            "isolated_cold_pixels_before_star_protection": int(isolated.metrics.get("cold_pixels", 0)),
            "hot_pixels": int(np.count_nonzero((dq_bits & np.uint32(int(DQFlag.HOT_PIXEL))) != 0)),
            "cold_pixels": int(np.count_nonzero((dq_bits & np.uint32(int(DQFlag.COLD_PIXEL))) != 0)),
        }
    )
    return CosmeticCorrectionResult(
        data=out.astype(np.float32),
        dq_mask=DQMask(dq_bits),
        metrics=metrics,
    )
