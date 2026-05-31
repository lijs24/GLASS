from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

import numpy as np

from glass.engine.contracts import DQFlag, DQMask, ImageSource, RejectionPolicy, StackRequest, TileWindow
from glass.gpu.tile_scheduler import iter_tiles


@dataclass(slots=True)
class StackEngineResult:
    master: np.ndarray
    weight_map: np.ndarray | None = None
    coverage_map: np.ndarray | None = None
    low_rejection_map: np.ndarray | None = None
    high_rejection_map: np.ndarray | None = None
    variance_map: np.ndarray | None = None
    dq_mask: DQMask | None = None
    metrics: dict[str, float | int | str] = field(default_factory=dict)


class CPUStackEngine:
    """Reference tiled stack engine for Phase 2 algorithm work."""

    def __init__(self, tile_size: int = 512):
        if tile_size <= 0:
            raise ValueError("tile_size must be positive")
        self.tile_size = int(tile_size)

    def stack(self, request: StackRequest, sources: Mapping[str, ImageSource]) -> StackEngineResult:
        ordered_sources = [sources[frame_id] for frame_id in request.frame_ids]
        width, height = self._validate_sources(request, ordered_sources)

        master = np.zeros((height, width), dtype=np.float32)
        weight_map = (
            np.zeros((height, width), dtype=np.float32) if request.output_maps.weight else None
        )
        coverage_map = (
            np.zeros((height, width), dtype=np.float32) if request.output_maps.coverage else None
        )
        low_rejection_map = (
            np.zeros((height, width), dtype=np.float32) if request.output_maps.low_rejection else None
        )
        high_rejection_map = (
            np.zeros((height, width), dtype=np.float32) if request.output_maps.high_rejection else None
        )
        variance_map = (
            np.zeros((height, width), dtype=np.float32) if request.output_maps.variance else None
        )
        dq_mask = DQMask.empty((height, width)) if request.output_maps.dq else None

        frame_weights = self._frame_weights(request)
        accumulator_dtype = np.float64 if request.combine.accumulator_dtype == "float64" else np.float32

        rejected_low_total = 0
        rejected_high_total = 0
        valid_total = 0

        for tile in iter_tiles(width, height, self.tile_size):
            window = TileWindow(tile.y0, tile.y1, tile.x0, tile.x1)
            stack, valid = self._read_stack_tile(ordered_sources, window)
            valid, low, high = _apply_rejection(stack, valid, request.rejection)
            tile_master, tile_weight, tile_coverage, tile_variance = _combine_tile(
                stack,
                valid,
                frame_weights,
                method=request.combine.method,
                accumulator_dtype=accumulator_dtype,
            )
            y_slice, x_slice = window.as_slices()
            master[y_slice, x_slice] = tile_master
            if weight_map is not None:
                weight_map[y_slice, x_slice] = tile_weight
            if coverage_map is not None:
                coverage_map[y_slice, x_slice] = tile_coverage
            if low_rejection_map is not None:
                low_rejection_map[y_slice, x_slice] = low
            if high_rejection_map is not None:
                high_rejection_map[y_slice, x_slice] = high
            if variance_map is not None:
                variance_map[y_slice, x_slice] = tile_variance
            if dq_mask is not None:
                dq_tile = DQMask.empty(window.shape)
                dq_tile.mark(DQFlag.NO_DATA, tile_coverage <= 0)
                dq_tile.mark(DQFlag.LOW_REJECTED, low > 0)
                dq_tile.mark(DQFlag.HIGH_REJECTED, high > 0)
                dq_mask.data[y_slice, x_slice] = dq_tile.data

            rejected_low_total += int(np.sum(low))
            rejected_high_total += int(np.sum(high))
            valid_total += int(np.sum(tile_coverage))

        return StackEngineResult(
            master=master,
            weight_map=weight_map,
            coverage_map=coverage_map,
            low_rejection_map=low_rejection_map,
            high_rejection_map=high_rejection_map,
            variance_map=variance_map,
            dq_mask=dq_mask,
            metrics={
                "frame_count": len(request.frame_ids),
                "width": width,
                "height": height,
                "combine": request.combine.method,
                "rejection": request.rejection.method,
                "valid_samples": valid_total,
                "low_rejected": rejected_low_total,
                "high_rejected": rejected_high_total,
            },
        )

    def _validate_sources(self, request: StackRequest, sources: list[ImageSource]) -> tuple[int, int]:
        if len(sources) != len(request.frame_ids):
            raise ValueError("source count does not match request frame count")
        width = int(sources[0].width)
        height = int(sources[0].height)
        if width <= 0 or height <= 0:
            raise ValueError("image sources must expose positive width and height")
        for frame_id, source in zip(request.frame_ids, sources, strict=True):
            if int(source.width) != width or int(source.height) != height:
                raise ValueError(
                    f"shape mismatch for {frame_id}: "
                    f"{source.width}x{source.height} != {width}x{height}"
                )
        return width, height

    def _frame_weights(self, request: StackRequest) -> np.ndarray:
        weights = np.array([float(request.weights.get(fid, 1.0)) for fid in request.frame_ids])
        weights = np.where(np.isfinite(weights) & (weights > 0), weights, 0.0)
        return weights.astype(np.float32)

    def _read_stack_tile(
        self, sources: list[ImageSource], window: TileWindow
    ) -> tuple[np.ndarray, np.ndarray]:
        tiles: list[np.ndarray] = []
        valid_masks: list[np.ndarray] = []
        for source in sources:
            tile = np.asarray(source.read_tile(window, dtype=np.float32), dtype=np.float32)
            if tile.shape != window.shape:
                raise ValueError(f"source returned tile shape {tile.shape}, expected {window.shape}")
            dq = source.read_mask_tile(window)
            tiles.append(tile)
            valid_masks.append(np.isfinite(tile) & (dq.data == 0))
        return np.stack(tiles, axis=0), np.stack(valid_masks, axis=0)


def _apply_rejection(
    stack: np.ndarray, valid: np.ndarray, policy: RejectionPolicy
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    low = np.zeros(stack.shape[1:], dtype=np.float32)
    high = np.zeros(stack.shape[1:], dtype=np.float32)
    if policy.method == "none" or policy.iterations == 0:
        return valid, low, high

    working_valid = valid.copy()
    iterations = max(1, int(policy.iterations))
    for _ in range(iterations):
        reject_low, reject_high = _rejection_pass(stack, working_valid, policy)
        rejected = reject_low | reject_high
        if not np.any(rejected):
            break
        remaining = np.sum(working_valid & ~rejected, axis=0)
        total = np.sum(working_valid, axis=0)
        rejected_fraction = np.divide(
            np.sum(rejected, axis=0),
            np.maximum(total, 1),
            out=np.zeros_like(total, dtype=np.float32),
            where=total > 0,
        )
        allowed = (remaining >= policy.min_samples) & (rejected_fraction <= policy.max_reject_fraction)
        reject_low &= allowed[None, :, :]
        reject_high &= allowed[None, :, :]
        rejected = reject_low | reject_high
        low += np.sum(reject_low, axis=0).astype(np.float32)
        high += np.sum(reject_high, axis=0).astype(np.float32)
        working_valid &= ~rejected
    return working_valid, low, high


def _rejection_pass(
    stack: np.ndarray, valid: np.ndarray, policy: RejectionPolicy
) -> tuple[np.ndarray, np.ndarray]:
    if policy.method == "minmax":
        return _minmax_rejection(stack, valid)
    if policy.method == "percentile":
        return _percentile_rejection(stack, valid, policy)
    if policy.method in {"sigma", "mad", "median_sigma", "winsorized_sigma"}:
        center, scale = _center_and_scale(stack, valid, policy)
        low_threshold = center - np.float32(policy.low_sigma) * scale
        high_threshold = center + np.float32(policy.high_sigma) * scale
        usable = valid & np.isfinite(scale)[None, :, :] & (scale[None, :, :] > 0)
        return usable & (stack < low_threshold[None, :, :]), usable & (
            stack > high_threshold[None, :, :]
        )
    raise ValueError(f"unsupported rejection method: {policy.method}")


def _center_and_scale(
    stack: np.ndarray, valid: np.ndarray, policy: RejectionPolicy
) -> tuple[np.ndarray, np.ndarray]:
    masked = np.where(valid, stack, np.nan)
    if policy.method == "sigma":
        center = np.nanmedian(masked, axis=0)
        scale = np.nanstd(masked, axis=0)
    elif policy.method in {"mad", "median_sigma"}:
        center = np.nanmedian(masked, axis=0)
        deviation = np.abs(masked - center[None, :, :])
        scale = np.float32(1.4826) * np.nanmedian(deviation, axis=0)
    else:
        first_center = np.nanmean(masked, axis=0)
        first_scale = np.nanstd(masked, axis=0)
        low = first_center - np.float32(policy.low_sigma) * first_scale
        high = first_center + np.float32(policy.high_sigma) * first_scale
        winsorized = np.where(valid, np.clip(stack, low[None, :, :], high[None, :, :]), np.nan)
        center = np.nanmean(winsorized, axis=0)
        scale = np.nanstd(winsorized, axis=0)
    return np.nan_to_num(center, nan=0.0).astype(np.float32), np.nan_to_num(
        scale, nan=0.0
    ).astype(np.float32)


def _minmax_rejection(stack: np.ndarray, valid: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    masked = np.where(valid, stack, np.nan)
    low_value = np.nanmin(masked, axis=0)
    high_value = np.nanmax(masked, axis=0)
    low = valid & (stack == low_value[None, :, :])
    high = valid & (stack == high_value[None, :, :])
    same_value = low_value == high_value
    low[:, same_value] = False
    high[:, same_value] = False
    return low, high


def _percentile_rejection(
    stack: np.ndarray, valid: np.ndarray, policy: RejectionPolicy
) -> tuple[np.ndarray, np.ndarray]:
    masked = np.where(valid, stack, np.nan)
    low_percentile = float(np.clip(policy.low_sigma, 0.0, 49.0))
    high_percentile = float(np.clip(100.0 - policy.high_sigma, 51.0, 100.0))
    low_value = np.nanpercentile(masked, low_percentile, axis=0)
    high_value = np.nanpercentile(masked, high_percentile, axis=0)
    return valid & (stack < low_value[None, :, :]), valid & (stack > high_value[None, :, :])


def _combine_tile(
    stack: np.ndarray,
    valid: np.ndarray,
    frame_weights: np.ndarray,
    method: str,
    accumulator_dtype: type[np.floating],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    coverage = np.sum(valid, axis=0).astype(np.float32)
    if method == "median":
        masked = np.where(valid, stack, np.nan)
        master = np.nanmedian(masked, axis=0)
        weight = coverage
    elif method == "sum":
        master = np.sum(np.where(valid, stack, 0.0).astype(accumulator_dtype), axis=0)
        weight = coverage
    elif method in {"mean", "weighted_mean"}:
        weights = np.ones_like(frame_weights) if method == "mean" else frame_weights
        effective_weights = np.where(valid, weights[:, None, None], 0.0).astype(accumulator_dtype)
        weighted = np.where(valid, stack, 0.0).astype(accumulator_dtype) * effective_weights
        weight = np.sum(effective_weights, axis=0)
        master = np.divide(
            np.sum(weighted, axis=0),
            weight,
            out=np.zeros_like(weight, dtype=accumulator_dtype),
            where=weight > 0,
        )
    else:
        raise ValueError(f"unsupported combine method: {method}")

    masked = np.where(valid, stack, np.nan)
    variance = np.nanvar(masked, axis=0)
    master = np.where(np.isfinite(master), master, 0.0)
    variance = np.where(np.isfinite(variance), variance, 0.0)
    return (
        master.astype(np.float32),
        weight.astype(np.float32),
        coverage,
        variance.astype(np.float32),
    )
