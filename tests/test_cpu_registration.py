from __future__ import annotations

import numpy as np

from gpwbpp.cpu.registration import estimate_translation, estimate_translation_phase_correlation
from gpwbpp.cpu.star_detect import Star
from gpwbpp.engine.registration import _registration_preview
from gpwbpp.io.fits_io import write_fits_data


def test_estimate_translation_from_star_lists():
    reference = [Star(10, 10, 100), Star(20, 20, 90), Star(30, 12, 80)]
    moving = [Star(8, 13, 100), Star(18, 23, 90), Star(28, 15, 80)]
    dx, dy = estimate_translation(reference, moving)
    assert dx == 2.0
    assert dy == -3.0


def test_phase_correlation_translation():
    reference = np.zeros((32, 32), dtype=np.float32)
    reference[10:13, 14:17] = 10
    moving = np.roll(np.roll(reference, 3, axis=1), -2, axis=0)
    dx, dy = estimate_translation_phase_correlation(reference, moving)
    assert dx == -3.0
    assert dy == 2.0


def test_registration_preview_streams_block_means(tmp_path):
    data = np.arange(64, dtype=np.float32).reshape(8, 8)
    path = tmp_path / "preview.fits"
    write_fits_data(path, data)

    preview, scale, tile_count = _registration_preview(path, tile_size=3, max_dimension=4)

    expected = data.reshape(4, 2, 4, 2).mean(axis=(1, 3))
    assert scale == 2
    assert tile_count > 1
    assert np.allclose(preview, expected)
