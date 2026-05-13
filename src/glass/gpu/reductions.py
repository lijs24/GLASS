from __future__ import annotations

import numpy as np


def reduce_mean_tile_f32(tile: np.ndarray) -> float:
    return float(np.mean(np.asarray(tile, dtype=np.float32)))

