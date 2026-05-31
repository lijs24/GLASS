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
