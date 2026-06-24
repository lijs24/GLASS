from __future__ import annotations

import numpy as np

from glass.cpu.integration import mean_integrate, sigma_clip_integrate, weighted_integrate_stack
from glass.engine.integration import _quality_weights
from glass.io.json_io import write_json


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


def test_weighted_integrate_stack_winsorized_sigma_uses_hardened_low_sample_baseline():
    stack = np.stack([np.ones((2, 2), dtype=np.float32) for _ in range(3)] + [np.ones((2, 2), dtype=np.float32) * 12])

    sigma_master, _, sigma_cov, _, sigma_high = weighted_integrate_stack(
        stack,
        rejection="sigma_clip",
        low_sigma=2.4,
        high_sigma=2.4,
    )
    winsorized_master, winsorized_weight, winsorized_cov, winsorized_low, winsorized_high = weighted_integrate_stack(
        stack,
        rejection="winsorized_sigma",
        low_sigma=2.4,
        high_sigma=2.4,
    )

    assert np.allclose(sigma_master, 3.75)
    assert np.all(sigma_cov == 4)
    assert np.sum(sigma_high) == 0
    assert np.allclose(winsorized_master, 1.0)
    assert np.all(winsorized_weight == 3)
    assert np.all(winsorized_cov == 3)
    assert np.sum(winsorized_low) == 0
    assert np.sum(winsorized_high) == 4


def test_weighted_integrate_stack_rejection_guard_cancels_excessive_rejection():
    stack = np.stack([np.ones((2, 2), dtype=np.float32) for _ in range(3)] + [np.ones((2, 2), dtype=np.float32) * 12])

    master, weight, cov, low, high = weighted_integrate_stack(
        stack,
        rejection="winsorized_sigma",
        low_sigma=2.4,
        high_sigma=2.4,
        max_reject_fraction=0.05,
    )

    assert np.allclose(master, 3.75)
    assert np.all(weight == 4)
    assert np.all(cov == 4)
    assert np.sum(low) == 0
    assert np.sum(high) == 0


def test_quality_weight_modes_are_normalized(tmp_path):
    write_json(
        tmp_path / "frame_quality.json",
        {
            "frame_quality": [
                {"frame_id": "A", "snr": 20.0, "quality_score": 10.0, "weight": 10.0},
                {"frame_id": "B", "snr": 10.0, "quality_score": 5.0, "weight": 5.0},
                {"frame_id": "C", "snr": 5.0, "quality_score": 1.0, "noise_sigma": 4.0, "background_rms": 4.0},
                {"frame_id": "D", "snr": 5.0, "quality_score": 1.0, "noise_sigma": 2.0, "background_rms": 2.0},
            ]
        },
    )
    records = [{"frame_id": "A"}, {"frame_id": "B"}]
    variance_records = [{"frame_id": "C"}, {"frame_id": "D"}]

    simple = _quality_weights(tmp_path, records, "simple_snr")
    combined = _quality_weights(tmp_path, records, "combined")
    variance_aware = _quality_weights(tmp_path, variance_records, "variance_aware")

    assert simple["A"] > simple["B"]
    assert combined["A"] > combined["B"]
    assert variance_aware["D"] > variance_aware["C"]
    assert np.isclose(variance_aware["D"] / variance_aware["C"], 4.0)
    assert np.isclose(np.median(list(simple.values())), 1.0)
    assert np.isclose(np.median(list(combined.values())), 1.0)
    assert np.isclose(np.median(list(variance_aware.values())), 1.0)
