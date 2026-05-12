from __future__ import annotations

import numpy as np

from gpwbpp.cpu.integration import mean_integrate, sigma_clip_integrate


def test_mean_integrate():
    frames = [np.ones((4, 4), dtype=np.float32), np.ones((4, 4), dtype=np.float32) * 3]
    master, weight = mean_integrate(frames)
    assert np.allclose(master, 2.0)
    assert np.allclose(weight, 2.0)


def test_sigma_clip_integrate_rejects_outlier():
    frames = [np.ones((4, 4), dtype=np.float32) for _ in range(4)]
    frames.append(np.ones((4, 4), dtype=np.float32) * 100)
    master, low, high = sigma_clip_integrate(frames, high_sigma=1.0)
    assert np.allclose(master, 1.0)
    assert np.sum(low) == 0
    assert np.sum(high) > 0

