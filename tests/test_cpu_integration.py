from __future__ import annotations

import numpy as np

from gpwbpp.cpu.integration import mean_integrate, sigma_clip_integrate, weighted_integrate_stack


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


def test_weighted_integrate_stack_with_coverage():
    stack = np.stack(
        [
            np.ones((3, 3), dtype=np.float32),
            np.ones((3, 3), dtype=np.float32) * 3,
        ],
        axis=0,
    )
    coverage = np.ones_like(stack, dtype=np.float32)
    coverage[1, 0, 0] = 0
    master, weight, cov, low, high = weighted_integrate_stack(stack, coverage=coverage, weights=np.array([1, 3]))
    assert np.allclose(master[1:, 1:], 2.5)
    assert master[0, 0] == 1.0
    assert weight[0, 0] == 1.0
    assert cov[0, 0] == 1.0
    assert np.sum(low) == 0
    assert np.sum(high) == 0


def test_winsorized_sigma_outputs_rejection_maps():
    stack = np.stack([np.ones((4, 4), dtype=np.float32) for _ in range(4)] + [np.ones((4, 4), dtype=np.float32) * 9])
    master, weight, cov, low, high = weighted_integrate_stack(stack, rejection="winsorized_sigma", high_sigma=1.0)
    assert np.allclose(master, 1)
    assert np.all(weight == 4)
    assert np.all(cov == 4)
    assert np.sum(low) == 0
    assert np.sum(high) > 0
