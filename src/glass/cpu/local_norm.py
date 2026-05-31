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


def fill_invalid_coefficient_grid(
    values: np.ndarray,
    valid_mask: np.ndarray,
    default: float,
) -> np.ndarray:
    grid = np.asarray(values, dtype=np.float32)
    valid = np.asarray(valid_mask, dtype=bool)
    if grid.shape != valid.shape:
        raise ValueError("values and valid_mask must have the same shape")
    out = grid.copy()
    valid_positions = np.argwhere(valid)
    if len(valid_positions) == 0:
        out[...] = np.float32(default)
        return out
    invalid_positions = np.argwhere(~valid)
    for y, x in invalid_positions:
        distances = np.sum((valid_positions - np.array([y, x])) ** 2, axis=1)
        nearest_y, nearest_x = valid_positions[int(np.argmin(distances))]
        out[y, x] = grid[nearest_y, nearest_x]
    return out


def _grid_centers(length: int, tile_length: int, grid_count: int) -> np.ndarray:
    if length <= 0:
        raise ValueError("image dimensions must be positive")
    if tile_length <= 0:
        raise ValueError("tile dimensions must be positive")
    centers = np.empty(grid_count, dtype=np.float32)
    for index in range(grid_count):
        start = index * tile_length
        end = min(length, start + tile_length)
        centers[index] = np.float32((start + end - 1) * 0.5)
    return centers


def interpolate_coefficient_grid_slice(
    values: np.ndarray,
    height: int,
    width: int,
    tile_height: int,
    tile_width: int,
    y0: int,
    y1: int,
    x0: int,
    x1: int,
) -> np.ndarray:
    grid = np.asarray(values, dtype=np.float32)
    if grid.ndim != 2:
        raise ValueError("coefficient grid must be two-dimensional")
    grid_rows, grid_cols = grid.shape
    expected_shape = (int(np.ceil(height / tile_height)), int(np.ceil(width / tile_width)))
    if grid.shape != expected_shape:
        raise ValueError("coefficient grid shape does not match image shape and tile dimensions")
    if not (0 <= y0 < y1 <= height and 0 <= x0 < x1 <= width):
        raise ValueError("slice bounds must be inside the image")
    if grid_rows == 1 and grid_cols == 1:
        return np.full((y1 - y0, x1 - x0), grid[0, 0], dtype=np.float32)

    x_centers = _grid_centers(width, tile_width, grid_cols)
    y_centers = _grid_centers(height, tile_height, grid_rows)
    x_coords = np.arange(x0, x1, dtype=np.float32)
    y_coords = np.arange(y0, y1, dtype=np.float32)

    if grid_cols == 1:
        along_x = np.repeat(grid[:, :1], len(x_coords), axis=1)
    else:
        along_x = np.vstack([np.interp(x_coords, x_centers, row).astype(np.float32) for row in grid])
    if grid_rows == 1:
        return np.repeat(along_x, len(y_coords), axis=0).astype(np.float32)

    out = np.empty((len(y_coords), len(x_coords)), dtype=np.float32)
    for x_index in range(len(x_coords)):
        out[:, x_index] = np.interp(y_coords, y_centers, along_x[:, x_index]).astype(np.float32)
    return out


def interpolate_coefficient_grid(
    values: np.ndarray,
    height: int,
    width: int,
    tile_height: int,
    tile_width: int,
) -> np.ndarray:
    return interpolate_coefficient_grid_slice(
        values,
        height,
        width,
        tile_height,
        tile_width,
        0,
        int(height),
        0,
        int(width),
    )


def apply_coefficient_fields(
    data: np.ndarray,
    scale_field: np.ndarray,
    offset_field: np.ndarray,
    valid_mask: np.ndarray | None = None,
) -> np.ndarray:
    src = np.asarray(data, dtype=np.float32)
    scale = np.asarray(scale_field, dtype=np.float32)
    offset = np.asarray(offset_field, dtype=np.float32)
    if src.shape != scale.shape or src.shape != offset.shape:
        raise ValueError("data, scale_field, and offset_field must have the same shape")
    out = src.copy()
    transformed = src * scale + offset
    if valid_mask is None:
        return transformed.astype(np.float32)
    mask = np.asarray(valid_mask, dtype=bool)
    if mask.shape != src.shape:
        raise ValueError("valid_mask must match data shape")
    out[mask] = transformed[mask]
    return out.astype(np.float32)


def summarize_residuals(residuals: np.ndarray, valid_mask: np.ndarray | None = None) -> dict[str, Any]:
    values = np.asarray(residuals, dtype=np.float32)
    mask = np.isfinite(values)
    if valid_mask is not None:
        mask &= np.asarray(valid_mask, dtype=bool)
    count = int(np.count_nonzero(mask))
    if count == 0:
        return {
            "valid_pixels": 0,
            "mean": None,
            "median": None,
            "rms": None,
            "mad": None,
            "p95_abs": None,
            "max_abs": None,
        }
    finite = values[mask].astype(np.float64)
    median = float(np.median(finite))
    abs_values = np.abs(finite)
    return {
        "valid_pixels": count,
        "mean": float(np.mean(finite)),
        "median": median,
        "rms": float(np.sqrt(np.mean(finite * finite))),
        "mad": float(np.median(np.abs(finite - median))),
        "p95_abs": float(np.percentile(abs_values, 95)),
        "max_abs": float(np.max(abs_values)),
    }


def normalize_grid_continuous_mean_std(
    data: np.ndarray,
    reference: np.ndarray,
    tile_height: int,
    tile_width: int,
    valid_mask: np.ndarray | None = None,
    eps: float = 1.0e-6,
) -> tuple[np.ndarray, dict[str, Any]]:
    src = np.asarray(data, dtype=np.float32)
    ref = np.asarray(reference, dtype=np.float32)
    model = estimate_grid_normalization_mean_std(src, ref, tile_height, tile_width, valid_mask, eps)
    valid_grid = np.asarray(model["valid_pixels"]) > 0
    scale_grid = fill_invalid_coefficient_grid(model["scales"], valid_grid, default=1.0)
    offset_grid = fill_invalid_coefficient_grid(model["offsets"], valid_grid, default=0.0)
    scale_field = interpolate_coefficient_grid(scale_grid, src.shape[0], src.shape[1], tile_height, tile_width)
    offset_field = interpolate_coefficient_grid(offset_grid, src.shape[0], src.shape[1], tile_height, tile_width)
    out = apply_coefficient_fields(src, scale_field, offset_field, valid_mask)
    residual_mask = np.isfinite(out) & np.isfinite(ref)
    if valid_mask is not None:
        residual_mask &= np.asarray(valid_mask, dtype=bool)
    residual_summary = summarize_residuals(out - ref, residual_mask)
    model.update(
        {
            "model": "continuous_grid_mean_std_v1",
            "coefficient_field_model": "bilinear_tile_center_v1",
            "interpolation": "bilinear_tile_center",
            "raw_scales": np.asarray(model["scales"], dtype=np.float32),
            "raw_offsets": np.asarray(model["offsets"], dtype=np.float32),
            "scales": scale_grid,
            "offsets": offset_grid,
            "empty_tiles_filled": int(np.count_nonzero(~valid_grid)),
            "scale_field": scale_field,
            "offset_field": offset_field,
            "residual_summary": residual_summary,
        }
    )
    return out, model


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
