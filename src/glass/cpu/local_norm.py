from __future__ import annotations

from typing import Any

import numpy as np


def match_global_background(data: np.ndarray, reference: np.ndarray) -> np.ndarray:
    src = np.asarray(data, dtype=np.float32)
    ref = np.asarray(reference, dtype=np.float32)
    src_std = float(np.std(src)) or 1.0
    return ((src - float(np.median(src))) / src_std * float(np.std(ref)) + float(np.median(ref))).astype(
        np.float32
    )


def estimate_tile_normalization(
    data: np.ndarray,
    reference: np.ndarray,
    valid_mask: np.ndarray | None = None,
    eps: float = 1.0e-6,
) -> dict[str, Any]:
    src = np.asarray(data, dtype=np.float32)
    ref = np.asarray(reference, dtype=np.float32)
    if src.shape != ref.shape:
        raise ValueError("data and reference tiles must have the same shape")
    if valid_mask is None:
        mask = np.isfinite(src) & np.isfinite(ref)
    else:
        mask = np.asarray(valid_mask, dtype=bool) & np.isfinite(src) & np.isfinite(ref)
    valid = int(np.count_nonzero(mask))
    if valid == 0:
        return {
            "scale": 1.0,
            "offset": 0.0,
            "source_median": None,
            "reference_median": None,
            "source_std": None,
            "reference_std": None,
            "valid_pixels": 0,
            "status": "empty",
        }
    src_values = src[mask]
    ref_values = ref[mask]
    src_median = float(np.median(src_values))
    ref_median = float(np.median(ref_values))
    src_std = float(np.std(src_values))
    ref_std = float(np.std(ref_values))
    if src_std <= eps or ref_std <= eps:
        scale = 1.0
        offset = ref_median - src_median
        status = "offset_only"
    else:
        scale = ref_std / src_std
        offset = ref_median - src_median * scale
        status = "ok"
    return {
        "scale": float(scale),
        "offset": float(offset),
        "source_median": src_median,
        "reference_median": ref_median,
        "source_std": src_std,
        "reference_std": ref_std,
        "valid_pixels": valid,
        "status": status,
    }


def estimate_tile_normalization_mean_std(
    data: np.ndarray,
    reference: np.ndarray,
    valid_mask: np.ndarray | None = None,
    eps: float = 1.0e-6,
) -> dict[str, Any]:
    src = np.asarray(data, dtype=np.float32)
    ref = np.asarray(reference, dtype=np.float32)
    if src.shape != ref.shape:
        raise ValueError("data and reference tiles must have the same shape")
    if valid_mask is None:
        mask = np.isfinite(src) & np.isfinite(ref)
    else:
        mask = np.asarray(valid_mask, dtype=bool) & np.isfinite(src) & np.isfinite(ref)
    valid = int(np.count_nonzero(mask))
    if valid == 0:
        return {
            "scale": 1.0,
            "offset": 0.0,
            "source_mean": None,
            "reference_mean": None,
            "source_std": None,
            "reference_std": None,
            "valid_pixels": 0,
            "status": "empty",
        }
    src_values = src[mask]
    ref_values = ref[mask]
    src_mean = float(np.mean(src_values))
    ref_mean = float(np.mean(ref_values))
    src_std = float(np.std(src_values))
    ref_std = float(np.std(ref_values))
    if src_std <= eps or ref_std <= eps:
        scale = 1.0
        offset = ref_mean - src_mean
        status = "offset_only"
    else:
        scale = ref_std / src_std
        offset = ref_mean - src_mean * scale
        status = "ok"
    return {
        "scale": float(scale),
        "offset": float(offset),
        "source_mean": src_mean,
        "reference_mean": ref_mean,
        "source_std": src_std,
        "reference_std": ref_std,
        "valid_pixels": valid,
        "status": status,
    }


def apply_tile_normalization(
    data: np.ndarray,
    scale: float,
    offset: float,
    valid_mask: np.ndarray | None = None,
) -> np.ndarray:
    src = np.asarray(data, dtype=np.float32)
    out = src.copy()
    if valid_mask is None:
        return (src * np.float32(scale) + np.float32(offset)).astype(np.float32)
    mask = np.asarray(valid_mask, dtype=bool)
    out[mask] = src[mask] * np.float32(scale) + np.float32(offset)
    return out.astype(np.float32)


def estimate_grid_normalization_mean_std(
    data: np.ndarray,
    reference: np.ndarray,
    tile_height: int,
    tile_width: int,
    valid_mask: np.ndarray | None = None,
    eps: float = 1.0e-6,
) -> dict[str, Any]:
    src = np.asarray(data, dtype=np.float32)
    ref = np.asarray(reference, dtype=np.float32)
    if src.shape != ref.shape:
        raise ValueError("data and reference must have the same shape")
    if tile_height <= 0 or tile_width <= 0:
        raise ValueError("tile dimensions must be positive")
    mask = None if valid_mask is None else np.asarray(valid_mask, dtype=bool)
    if mask is not None and mask.shape != src.shape:
        raise ValueError("valid_mask must match data shape")
    height, width = src.shape
    grid_rows = int(np.ceil(height / tile_height))
    grid_cols = int(np.ceil(width / tile_width))
    scales = np.ones((grid_rows, grid_cols), dtype=np.float32)
    offsets = np.zeros((grid_rows, grid_cols), dtype=np.float32)
    statuses: list[list[str]] = []
    valid_pixels = np.zeros((grid_rows, grid_cols), dtype=np.int64)
    for gy in range(grid_rows):
        row_statuses: list[str] = []
        y0 = gy * tile_height
        y1 = min(height, y0 + tile_height)
        for gx in range(grid_cols):
            x0 = gx * tile_width
            x1 = min(width, x0 + tile_width)
            tile_mask = None if mask is None else mask[y0:y1, x0:x1]
            stats = estimate_tile_normalization_mean_std(
                src[y0:y1, x0:x1],
                ref[y0:y1, x0:x1],
                valid_mask=tile_mask,
                eps=eps,
            )
            scales[gy, gx] = np.float32(stats["scale"])
            offsets[gy, gx] = np.float32(stats["offset"])
            row_statuses.append(str(stats["status"]))
            valid_pixels[gy, gx] = int(stats["valid_pixels"])
        statuses.append(row_statuses)
    return {
        "tile_height": int(tile_height),
        "tile_width": int(tile_width),
        "grid_rows": grid_rows,
        "grid_cols": grid_cols,
        "scales": scales,
        "offsets": offsets,
        "statuses": statuses,
        "valid_pixels": valid_pixels,
        "model": "grid_mean_std_piecewise",
    }


def apply_grid_normalization(
    data: np.ndarray,
    scales: np.ndarray,
    offsets: np.ndarray,
    tile_height: int,
    tile_width: int,
) -> np.ndarray:
    src = np.asarray(data, dtype=np.float32)
    scale_grid = np.asarray(scales, dtype=np.float32)
    offset_grid = np.asarray(offsets, dtype=np.float32)
    if scale_grid.shape != offset_grid.shape:
        raise ValueError("scales and offsets must have the same shape")
    if tile_height <= 0 or tile_width <= 0:
        raise ValueError("tile dimensions must be positive")
    height, width = src.shape
    expected_shape = (int(np.ceil(height / tile_height)), int(np.ceil(width / tile_width)))
    if scale_grid.shape != expected_shape:
        raise ValueError("coefficient grid shape does not match data shape and tile dimensions")
    out = np.empty_like(src, dtype=np.float32)
    for gy in range(scale_grid.shape[0]):
        y0 = gy * tile_height
        y1 = min(height, y0 + tile_height)
        for gx in range(scale_grid.shape[1]):
            x0 = gx * tile_width
            x1 = min(width, x0 + tile_width)
            out[y0:y1, x0:x1] = src[y0:y1, x0:x1] * scale_grid[gy, gx] + offset_grid[gy, gx]
    return out


def normalize_grid_mean_std(
    data: np.ndarray,
    reference: np.ndarray,
    tile_height: int,
    tile_width: int,
    valid_mask: np.ndarray | None = None,
    eps: float = 1.0e-6,
) -> tuple[np.ndarray, dict[str, Any]]:
    model = estimate_grid_normalization_mean_std(data, reference, tile_height, tile_width, valid_mask, eps)
    out = apply_grid_normalization(data, model["scales"], model["offsets"], tile_height, tile_width)
    return out, model
