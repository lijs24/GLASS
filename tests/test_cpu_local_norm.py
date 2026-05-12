from __future__ import annotations

import numpy as np

from gpwbpp.cpu.local_norm import apply_tile_normalization, estimate_tile_normalization


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
