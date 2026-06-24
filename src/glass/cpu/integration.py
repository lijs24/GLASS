from __future__ import annotations

import numpy as np

from glass.engine.rejection import center_and_scale


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
    clipped = np.where(mask, stack, np.nan)
    master = np.nanmean(clipped, axis=0).astype(np.float32)
    master = np.where(np.isfinite(master), master, median).astype(np.float32)
    return master, np.sum(low, axis=0).astype(np.float32), np.sum(high, axis=0).astype(np.float32)


def weighted_integrate_stack(
    stack: np.ndarray,
    coverage: np.ndarray | None = None,
    weights: np.ndarray | None = None,
    rejection: str = "none",
    low_sigma: float = 3.0,
    high_sigma: float = 3.0,
    min_samples: int = 3,
    max_reject_fraction: float = 0.5,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    frames = np.asarray(stack, dtype=np.float32)
    if frames.ndim != 3:
        raise ValueError("stack must have shape (frame_count, height, width)")
    if min_samples < 1:
        raise ValueError("min_samples must be at least 1")
    if not 0.0 <= max_reject_fraction <= 1.0:
        raise ValueError("max_reject_fraction must be between 0 and 1")
    frame_count, height, width = frames.shape
    if weights is None:
        frame_weights = np.ones(frame_count, dtype=np.float32)
    else:
        frame_weights = np.asarray(weights, dtype=np.float32)
        if frame_weights.shape != (frame_count,):
            raise ValueError("weights must have shape (frame_count,)")
    if coverage is None:
        valid = np.isfinite(frames)
    else:
        cov = np.asarray(coverage, dtype=np.float32)
        if cov.shape != frames.shape:
            raise ValueError("coverage must have the same shape as stack")
        valid = (cov > 0.5) & np.isfinite(frames)
    valid = valid & np.isfinite(frame_weights)[:, None, None] & (frame_weights[:, None, None] > 0)
    low_reject = np.zeros((height, width), dtype=np.float32)
    high_reject = np.zeros((height, width), dtype=np.float32)
    working = frames.copy()

    if rejection in {"sigma_clip", "winsorized_sigma"}:
        center, scale = center_and_scale(
            frames,
            valid,
            method=rejection,
            low_sigma=low_sigma,
            high_sigma=high_sigma,
        )
        low_threshold = center - np.float32(low_sigma) * scale
        high_threshold = center + np.float32(high_sigma) * scale
        low = valid & (frames < low_threshold[None, :, :])
        high = valid & (frames > high_threshold[None, :, :])
        rejected = low | high
        if np.any(rejected):
            total = np.sum(valid, axis=0)
            rejected_count = np.sum(rejected, axis=0)
            remaining = total - rejected_count
            rejected_fraction = np.divide(
                rejected_count,
                np.maximum(total, 1),
                out=np.zeros_like(total, dtype=np.float32),
                where=total > 0,
            )
            allowed = (remaining >= int(min_samples)) & (
                rejected_fraction <= np.float32(max_reject_fraction)
            )
            low &= allowed[None, :, :]
            high &= allowed[None, :, :]
        low_reject = np.sum(low, axis=0).astype(np.float32)
        high_reject = np.sum(high, axis=0).astype(np.float32)
        valid = valid & ~(low | high)
    elif rejection != "none":
        raise ValueError(f"unsupported rejection mode: {rejection}")

    w = frame_weights[:, None, None]
    effective_weights = np.where(valid, w, 0.0).astype(np.float64)
    weighted_sum = np.sum(np.where(valid, working, 0.0).astype(np.float64) * effective_weights, axis=0)
    weight_map = np.sum(effective_weights, axis=0)
    coverage_map = np.sum(valid, axis=0).astype(np.float32)
    master = np.divide(weighted_sum, weight_map, out=np.zeros_like(weighted_sum), where=weight_map > 0)
    return (
        master.astype(np.float32),
        weight_map.astype(np.float32),
        coverage_map,
        low_reject,
        high_reject,
    )
