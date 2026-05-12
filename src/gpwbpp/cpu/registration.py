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


def estimate_translation_phase_correlation(reference: np.ndarray, moving: np.ndarray) -> tuple[float, float]:
    ref = np.asarray(reference, dtype=np.float32)
    mov = np.asarray(moving, dtype=np.float32)
    if ref.shape != mov.shape:
        raise ValueError(f"shape mismatch for registration: {ref.shape} != {mov.shape}")
    ref = ref - float(np.mean(ref))
    mov = mov - float(np.mean(mov))
    cross_power = np.fft.fft2(ref) * np.conj(np.fft.fft2(mov))
    denom = np.abs(cross_power)
    cross_power = np.divide(cross_power, denom, out=np.zeros_like(cross_power), where=denom > 0)
    corr = np.fft.ifft2(cross_power)
    y, x = np.unravel_index(np.argmax(np.abs(corr)), corr.shape)
    height, width = ref.shape
    if x > width // 2:
        x -= width
    if y > height // 2:
        y -= height
    return float(x), float(y)
