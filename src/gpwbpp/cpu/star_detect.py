from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(slots=True)
class Star:
    x: float
    y: float
    flux: float


def detect_stars(data: np.ndarray, threshold_sigma: float = 5.0, max_stars: int = 500) -> list[Star]:
    image = np.asarray(data, dtype=np.float32)
    median = float(np.median(image))
    sigma = float(np.std(image))
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
    for local_y, local_x in zip(ys, xs, strict=True):
        y = int(local_y + 1)
        x = int(local_x + 1)
        patch = image[y - 1 : y + 2, x - 1 : x + 2]
        yy, xx = np.mgrid[y - 1 : y + 2, x - 1 : x + 2]
        weights = np.maximum(patch - median, 0.0)
        total = float(np.sum(weights))
        if total <= 0:
            continue
        stars.append(
            Star(
                x=float(np.sum(xx * weights) / total),
                y=float(np.sum(yy * weights) / total),
                flux=total,
            )
        )
    stars.sort(key=lambda star: star.flux, reverse=True)
    return stars[:max_stars]
