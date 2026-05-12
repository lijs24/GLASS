from __future__ import annotations

import numpy as np

from gpwbpp.cpu.star_detect import Star


def estimate_translation(reference: list[Star], moving: list[Star]) -> tuple[float, float]:
    if not reference or not moving:
        raise ValueError("cannot estimate translation without stars")
    n = min(len(reference), len(moving), 30)
    ref = np.array([(s.x, s.y) for s in reference[:n]], dtype=np.float32)
    mov = np.array([(s.x, s.y) for s in moving[:n]], dtype=np.float32)
    delta = np.median(ref - mov, axis=0)
    return float(delta[0]), float(delta[1])


def translation_matrix(dx: float, dy: float) -> list[list[float]]:
    return [[1.0, 0.0, dx], [0.0, 1.0, dy], [0.0, 0.0, 1.0]]

