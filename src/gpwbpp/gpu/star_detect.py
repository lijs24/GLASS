from __future__ import annotations

from typing import Any

import numpy as np

from gpwbpp.cpu.star_detect import detect_stars


def star_local_max_mask(data: Any, threshold: float) -> np.ndarray:
    import gpwbpp_cuda

    return gpwbpp_cuda.star_local_max_mask_f32(data, threshold)


def star_candidates(data: Any, threshold: float, max_candidates: int = 4096) -> dict[str, Any]:
    import gpwbpp_cuda

    return gpwbpp_cuda.star_candidates_f32(data, threshold, max_candidates)


def star_top_candidates(data: Any, threshold: float, max_candidates: int = 4096) -> dict[str, Any]:
    import gpwbpp_cuda

    return gpwbpp_cuda.star_top_candidates_f32(data, threshold, max_candidates)


__all__ = ["detect_stars", "star_candidates", "star_local_max_mask", "star_top_candidates"]
