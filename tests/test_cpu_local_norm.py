from __future__ import annotations

import numpy as np

from gpwbpp.cpu.local_norm import (
    apply_grid_normalization,
    apply_tile_normalization,
    estimate_tile_normalization,
    estimate_tile_normalization_mean_std,
    normalize_grid_mean_std,
)


def test_estimate_tile_normalization_matches_reference_stats():
    data = np.arange(16, dtype=np.float32).reshape(4, 4)
    reference = data * 2.0 + 10.0
    stats = estimate_tile_normalization(data, reference)
    out = apply_tile_normalization(data, stats["scale"], stats["offset"])
    assert stats["status"] == "ok"
    assert np.allclose(np.median(out), np.median(reference), atol=1.0e-5)
    assert np.allclose(np.std(out), np.std(reference), atol=1.0e-5)


def test_estimate_tile_normalization_honors_valid_mask():
    data = np.ones((4, 4), dtype=np.float32) * 5
    reference = np.ones((4, 4), dtype=np.float32) * 9
    mask = np.zeros((4, 4), dtype=bool)
    mask[1:3, 1:3] = True
    stats = estimate_tile_normalization(data, reference, mask)
    out = apply_tile_normalization(data, stats["scale"], stats["offset"], mask)
    assert stats["status"] == "offset_only"
    assert stats["valid_pixels"] == 4
    assert np.allclose(out[mask], 9)
    assert np.allclose(out[~mask], 5)


def test_estimate_tile_normalization_mean_std_honors_valid_mask():
    data = np.arange(16, dtype=np.float32).reshape(4, 4)
    reference = data * 1.5 + 8.0
    mask = np.zeros((4, 4), dtype=bool)
    mask[:, 1:4] = True
    stats = estimate_tile_normalization_mean_std(data, reference, mask)
    out = apply_tile_normalization(data, stats["scale"], stats["offset"], mask)
    assert stats["status"] == "ok"
    assert stats["valid_pixels"] == 12
    assert np.allclose(np.mean(out[mask]), np.mean(reference[mask]), atol=1.0e-5)
    assert np.allclose(np.std(out[mask]), np.std(reference[mask]), atol=1.0e-5)
    assert np.allclose(out[~mask], data[~mask])


def test_grid_normalization_mean_std_matches_reference_tiles():
    yy, xx = np.indices((7, 9), dtype=np.float32)
    data = 10.0 + xx + yy * 0.5
    reference = data.copy()
    reference[:4, :5] = reference[:4, :5] * 1.5 + 7.0
    reference[:4, 5:] = reference[:4, 5:] * 0.75 - 3.0
    reference[4:, :5] = reference[4:, :5] * 1.2 + 2.0
    reference[4:, 5:] = reference[4:, 5:] * 0.9 + 11.0

    out, model = normalize_grid_mean_std(data, reference, tile_height=4, tile_width=5)

    assert model["grid_rows"] == 2
    assert model["grid_cols"] == 2
    for y0, y1 in [(0, 4), (4, 7)]:
        for x0, x1 in [(0, 5), (5, 9)]:
            assert np.allclose(np.mean(out[y0:y1, x0:x1]), np.mean(reference[y0:y1, x0:x1]), atol=1.0e-5)
            assert np.allclose(np.std(out[y0:y1, x0:x1]), np.std(reference[y0:y1, x0:x1]), atol=1.0e-5)


def test_apply_grid_normalization_uses_edge_tiles():
    data = np.arange(15, dtype=np.float32).reshape(3, 5)
    scales = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    offsets = np.array([[0.0, 10.0], [20.0, 30.0]], dtype=np.float32)
    out = apply_grid_normalization(data, scales, offsets, tile_height=2, tile_width=3)

    assert np.allclose(out[:2, :3], data[:2, :3])
    assert np.allclose(out[:2, 3:], data[:2, 3:] * 2.0 + 10.0)
    assert np.allclose(out[2:, :3], data[2:, :3] * 3.0 + 20.0)
    assert np.allclose(out[2:, 3:], data[2:, 3:] * 4.0 + 30.0)
