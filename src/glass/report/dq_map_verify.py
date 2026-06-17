from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from glass.engine.contracts import DQFlag
from glass.io.fits_io import FitsImageReader


def _flag_value(flag_name: str) -> int | None:
    if flag_name == "valid":
        return 0
    try:
        return int(DQFlag[flag_name.upper()])
    except KeyError:
        return None


def summarize_dq_map_pixels(
    path: str | Path,
    *,
    flags: list[str] | tuple[str, ...] | None = None,
    tile_size: int = 2048,
) -> dict[str, Any]:
    """Summarize a DQ FITS map by tiled reads.

    DQ maps are bitfields. `valid` counts pixels whose bitfield is exactly zero;
    every other requested flag counts pixels where that bit is set.
    """

    requested_flags = list(flags) if flags is not None else [
        "valid",
        "no_data",
        "warp_edge",
        "low_rejected",
        "high_rejected",
    ]
    clean_flags: list[str] = []
    flag_bits: dict[str, int | None] = {}
    for flag in requested_flags:
        name = str(flag).lower()
        if name in clean_flags:
            continue
        clean_flags.append(name)
        flag_bits[name] = _flag_value(name)

    counts = {name: 0 for name in clean_flags}
    unknown_flags = [name for name, bit in flag_bits.items() if bit is None]
    target = Path(path)
    with FitsImageReader(target) as reader:
        height, width = reader.shape
        step = max(1, int(tile_size))
        for y0 in range(0, height, step):
            y1 = min(height, y0 + step)
            for x0 in range(0, width, step):
                x1 = min(width, x0 + step)
                tile = reader.read_tile(y0, y1, x0, x1, dtype=np.float32)
                values = np.asarray(tile, dtype=np.uint32)
                for name, bit in flag_bits.items():
                    if bit is None:
                        continue
                    if bit == 0:
                        counts[name] += int(np.count_nonzero(values == 0))
                    else:
                        counts[name] += int(np.count_nonzero((values & np.uint32(bit)) != 0))

    return {
        "schema_version": 1,
        "path": str(target),
        "width": int(width),
        "height": int(height),
        "total_pixels": int(width) * int(height),
        "tile_size": max(1, int(tile_size)),
        "counts": counts,
        "flag_bits": flag_bits,
        "unknown_flags": unknown_flags,
    }


def summarize_count_map_pixels(
    path: str | Path,
    *,
    tile_size: int = 2048,
    positive_threshold: float = 0.0,
) -> dict[str, Any]:
    """Summarize a scalar count/coverage FITS map by tiled reads."""

    target = Path(path)
    finite_pixels = 0
    nonfinite_pixels = 0
    positive_pixels = 0
    zero_or_less_pixels = 0
    negative_pixels = 0
    fractional_pixels = 0
    value_sum = 0.0
    min_value: float | None = None
    max_value: float | None = None
    with FitsImageReader(target) as reader:
        height, width = reader.shape
        step = max(1, int(tile_size))
        for y0 in range(0, height, step):
            y1 = min(height, y0 + step)
            for x0 in range(0, width, step):
                x1 = min(width, x0 + step)
                tile = reader.read_tile(y0, y1, x0, x1, dtype=np.float32)
                finite = np.isfinite(tile)
                finite_count = int(np.count_nonzero(finite))
                finite_pixels += finite_count
                nonfinite_pixels += int(tile.size - finite_count)
                if not finite_count:
                    continue
                values = tile[finite]
                positive = values > np.float32(positive_threshold)
                positive_pixels += int(np.count_nonzero(positive))
                zero_or_less_pixels += int(np.count_nonzero(~positive))
                negative_pixels += int(np.count_nonzero(values < 0.0))
                fractional_pixels += int(np.count_nonzero(np.abs(values - np.rint(values)) > 1.0e-3))
                value_sum += float(np.sum(values, dtype=np.float64))
                tile_min = float(np.min(values))
                tile_max = float(np.max(values))
                min_value = tile_min if min_value is None else min(min_value, tile_min)
                max_value = tile_max if max_value is None else max(max_value, tile_max)

    return {
        "schema_version": 1,
        "path": str(target),
        "width": int(width),
        "height": int(height),
        "total_pixels": int(width) * int(height),
        "tile_size": max(1, int(tile_size)),
        "positive_threshold": float(positive_threshold),
        "finite_pixels": finite_pixels,
        "nonfinite_pixels": nonfinite_pixels,
        "positive_pixels": positive_pixels,
        "zero_or_less_pixels": zero_or_less_pixels,
        "negative_pixels": negative_pixels,
        "fractional_pixels": fractional_pixels,
        "sum": value_sum,
        "rounded_sum": int(round(value_sum)),
        "min": min_value,
        "max": max_value,
    }
