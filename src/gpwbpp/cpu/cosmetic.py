from __future__ import annotations

import numpy as np


def replace_hot_pixels(data: np.ndarray, threshold_sigma: float = 8.0) -> np.ndarray:
    median = float(np.median(data))
    sigma = float(np.std(data))
    out = data.copy()
    out[out > median + threshold_sigma * sigma] = median
    return out

