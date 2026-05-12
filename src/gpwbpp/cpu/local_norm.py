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
