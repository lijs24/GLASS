from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(slots=True)
class Star:
    x: float
    y: float
    flux: float
    peak: float = 0.0
    fwhm_px: float | None = None
    eccentricity: float | None = None
    snr: float | None = None
    sharpness: float | None = None
    npix: int = 0


@dataclass(slots=True)
class BackgroundStats:
    median: float
    rms: float
    mad: float
    noise: float


def robust_background(data: np.ndarray) -> BackgroundStats:
    image = np.asarray(data, dtype=np.float32)
    finite = image[np.isfinite(image)]
    if finite.size == 0:
        return BackgroundStats(median=0.0, rms=0.0, mad=0.0, noise=1.0)
    median = float(np.median(finite))
    rms = float(np.std(finite))
    mad = float(np.median(np.abs(finite - median)))
    noise = float(1.4826 * mad)
    if noise <= 0.0:
        noise = rms
    if noise <= 0.0:
        noise = 1.0
    return BackgroundStats(median=median, rms=rms, mad=mad, noise=noise)


def _measure_candidate(
    image: np.ndarray,
    x: int,
    y: int,
    background: float,
    noise: float,
    window_radius: int,
    origin_x: int,
    origin_y: int,
) -> Star | None:
    h, w = image.shape
    y0 = max(0, y - window_radius)
    y1 = min(h, y + window_radius + 1)
    x0 = max(0, x - window_radius)
    x1 = min(w, x + window_radius + 1)
    patch = image[y0:y1, x0:x1]
    finite = np.isfinite(patch)
    if not np.any(finite):
        return None
    weights = np.where(finite, np.maximum(patch - np.float32(background), 0.0), 0.0)
    flux = float(np.sum(weights, dtype=np.float64))
    if flux <= 0.0:
        return None
    yy, xx = np.mgrid[y0:y1, x0:x1]
    centroid_x = float(np.sum(xx * weights, dtype=np.float64) / flux)
    centroid_y = float(np.sum(yy * weights, dtype=np.float64) / flux)
    dx = xx - centroid_x
    dy = yy - centroid_y
    mxx = float(np.sum(dx * dx * weights, dtype=np.float64) / flux)
    myy = float(np.sum(dy * dy * weights, dtype=np.float64) / flux)
    mxy = float(np.sum(dx * dy * weights, dtype=np.float64) / flux)
    trace = max(mxx + myy, 0.0)
    determinant_term = max((mxx - myy) * (mxx - myy) + 4.0 * mxy * mxy, 0.0)
    root = float(np.sqrt(determinant_term))
    major_var = max((trace + root) / 2.0, 0.0)
    minor_var = max((trace - root) / 2.0, 0.0)
    mean_sigma = float(np.sqrt(max((major_var + minor_var) / 2.0, 0.0)))
    fwhm = 2.354820045 * mean_sigma if mean_sigma > 0.0 else None
    eccentricity = None
    if major_var > 0.0:
        eccentricity = float(np.sqrt(max(0.0, 1.0 - minor_var / major_var)))
    peak = float(max(float(image[y, x]) - background, 0.0))
    npix = int(np.count_nonzero(weights > 0.0))
    snr = flux / max(float(noise) * np.sqrt(max(npix, 1)), 1.0e-6)
    sharpness = peak / max(flux, 1.0e-6)
    return Star(
        x=centroid_x + float(origin_x),
        y=centroid_y + float(origin_y),
        flux=flux,
        peak=peak,
        fwhm_px=None if fwhm is None else float(fwhm),
        eccentricity=eccentricity,
        snr=float(snr),
        sharpness=float(sharpness),
        npix=npix,
    )


def _dedupe_stars(stars: list[Star], min_separation_px: float) -> list[Star]:
    if min_separation_px <= 0.0 or len(stars) <= 1:
        return stars
    kept: list[Star] = []
    min_sep_sq = float(min_separation_px * min_separation_px)
    for star in sorted(stars, key=lambda item: item.flux, reverse=True):
        duplicate = False
        for other in kept:
            dx = star.x - other.x
            dy = star.y - other.y
            if dx * dx + dy * dy < min_sep_sq:
                duplicate = True
                break
        if not duplicate:
            kept.append(star)
    return kept


def detect_stars(
    data: np.ndarray,
    threshold_sigma: float = 5.0,
    max_stars: int = 500,
    *,
    background: float | None = None,
    noise: float | None = None,
    window_radius: int = 4,
    min_separation_px: float = 2.0,
    origin_x: int = 0,
    origin_y: int = 0,
) -> list[Star]:
    image = np.asarray(data, dtype=np.float32)
    stats = robust_background(image)
    median = stats.median if background is None else float(background)
    sigma = stats.noise if noise is None else float(noise)
    threshold = median + threshold_sigma * max(sigma, 1.0e-6)
    stars: list[Star] = []
    h, w = image.shape
    if h < 3 or w < 3:
        return []
    core = image[1:-1, 1:-1]
    finite = np.isfinite(core)
    mask = finite & (core > threshold)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            neighbor = image[1 + dy : h - 1 + dy, 1 + dx : w - 1 + dx]
            mask &= core >= neighbor
    ys, xs = np.nonzero(mask)
    radius = max(1, int(window_radius))
    for local_y, local_x in zip(ys, xs, strict=True):
        star = _measure_candidate(
            image,
            int(local_x + 1),
            int(local_y + 1),
            median,
            sigma,
            radius,
            int(origin_x),
            int(origin_y),
        )
        if star is not None:
            stars.append(star)
    stars = _dedupe_stars(stars, float(min_separation_px))
    stars.sort(key=lambda star: star.flux, reverse=True)
    return stars[:max_stars]
