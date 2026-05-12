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
    for y in range(1, h - 1):
        row = image[y]
        for x in range(1, w - 1):
            value = float(row[x])
            if value <= threshold:
                continue
            patch = image[y - 1 : y + 2, x - 1 : x + 2]
            if value < float(np.max(patch)):
                continue
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

