from __future__ import annotations

from typing import Any

import numpy as np

from gpwbpp.cpu.star_detect import detect_stars


def star_local_max_mask(data: Any, threshold: float) -> np.ndarray:
    import gpwbpp_cuda

    return gpwbpp_cuda.star_local_max_mask_f32(data, threshold)


__all__ = ["detect_stars", "star_local_max_mask"]
