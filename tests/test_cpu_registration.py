from __future__ import annotations

import numpy as np

from gpwbpp.cpu.registration import (
    estimate_star_transform,
    estimate_translation,
    estimate_translation_phase_correlation,
)
from gpwbpp.cpu.star_detect import Star
from gpwbpp.engine.registration import _registration_preview
from gpwbpp.io.fits_io import write_fits_data


def test_estimate_translation_from_star_lists():
    reference = [Star(10, 10, 100), Star(20, 20, 90), Star(30, 12, 80)]
    moving = [Star(8, 13, 100), Star(18, 23, 90), Star(28, 15, 80)]
    dx, dy = estimate_translation(reference, moving)
    assert dx == 2.0
    assert dy == -3.0


def test_estimate_star_transform_translation_with_outliers():
    reference = [
        Star(10, 10, 100),
        Star(20, 10, 90),
        Star(10, 25, 80),
        Star(30, 30, 70),
        Star(5, 35, 60),
        Star(35, 5, 50),
        Star(25, 18, 40),
        Star(14, 32, 30),
    ]
    moving = [Star(star.x - 3, star.y + 2, star.flux) for star in reference]
    moving.append(Star(100, 100, 10))

    result = estimate_star_transform(reference, moving, "translation", min_inliers=6, tolerance_px=0.5)

    assert result.status == "ok"
    assert result.inliers == 8
    assert result.rms_px == 0.0
    assert abs(result.matrix[0][2] - 3.0) < 1.0e-6
    assert abs(result.matrix[1][2] + 2.0) < 1.0e-6


def test_estimate_star_transform_similarity():
    import math

    points = np.array(
        [(10, 10), (20, 10), (10, 25), (30, 30), (5, 35), (35, 5), (25, 18), (14, 32)],
        dtype=np.float64,
    )
    reference = [Star(float(x), float(y), 1000.0 - i) for i, (x, y) in enumerate(points)]
    angle = math.radians(5.0)
    scale = 1.02
    linear = scale * np.array(
        [[math.cos(angle), -math.sin(angle)], [math.sin(angle), math.cos(angle)]],
        dtype=np.float64,
    )
    translation = np.array([3.0, -2.0], dtype=np.float64)
    moving_points = (points - translation) @ np.linalg.inv(linear).T
    moving = [Star(float(x), float(y), 1000.0 - i) for i, (x, y) in enumerate(moving_points)]

    result = estimate_star_transform(reference, moving, "similarity", min_inliers=6, tolerance_px=0.5)

    assert result.status == "ok"
    assert result.inliers == 8
    assert result.rms_px < 1.0e-5
    assert np.allclose(np.asarray(result.matrix)[:2, :2], linear, atol=1.0e-6)
    assert np.allclose(np.asarray(result.matrix)[:2, 2], translation, atol=1.0e-6)


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


def test_registration_preview_uses_tiles_for_scale_one(tmp_path, monkeypatch):
    from gpwbpp.engine.registration import FitsImageReader

    data = np.arange(16, dtype=np.float32).reshape(4, 4)
    path = tmp_path / "preview_scale_one.fits"
    write_fits_data(path, data)

    def fail_read_full(self, dtype=np.float32):
        raise AssertionError("registration preview should use tile reads, not read_full")

    monkeypatch.setattr(FitsImageReader, "read_full", fail_read_full)
    preview, scale, tile_count = _registration_preview(path, tile_size=3, max_dimension=8)
    assert scale == 1
    assert tile_count == 4
    assert np.allclose(preview, data)
