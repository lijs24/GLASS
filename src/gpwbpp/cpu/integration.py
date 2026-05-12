from __future__ import annotations

import numpy as np


def mean_integrate(frames: list[np.ndarray], weights: list[float] | None = None) -> tuple[np.ndarray, np.ndarray]:
    if not frames:
        raise ValueError("cannot integrate an empty frame list")
    weights = weights or [1.0] * len(frames)
    acc = np.zeros_like(frames[0], dtype=np.float64)
    weight_sum = np.zeros_like(frames[0], dtype=np.float64)
    for frame, weight in zip(frames, weights, strict=True):
        acc += np.asarray(frame, dtype=np.float64) * float(weight)
        weight_sum += float(weight)
    master = np.divide(acc, weight_sum, out=np.zeros_like(acc), where=weight_sum != 0).astype(np.float32)
    return master, weight_sum.astype(np.float32)


def sigma_clip_integrate(
    frames: list[np.ndarray], low_sigma: float = 3.0, high_sigma: float = 3.0
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    stack = np.stack([np.asarray(frame, dtype=np.float32) for frame in frames], axis=0)
    median = np.median(stack, axis=0)
    std = np.std(stack, axis=0)
    low = stack < (median - low_sigma * std)
    high = stack > (median + high_sigma * std)
    mask = ~(low | high)
    coverage = np.sum(mask, axis=0).astype(np.float32)
    clipped = np.where(mask, stack, np.nan)
    master = np.nanmean(clipped, axis=0).astype(np.float32)
    master = np.where(np.isfinite(master), master, median).astype(np.float32)
    return master, np.sum(low, axis=0).astype(np.float32), np.sum(high, axis=0).astype(np.float32)

