from __future__ import annotations

import numpy as np
import pytest

from glass.cpu.registration import (
    estimate_astroalign_transform,
    estimate_star_transform,
    estimate_triangle_asterism_transform,
    estimate_translation,
    estimate_translation_phase_correlation,
)
from glass.cpu.star_detect import detect_stars
from glass.cpu.star_detect import Star
from glass.engine.registration import _registration_preview
from glass.engine.registration import register_calibrated_frames
from glass.io.fits_io import write_fits_data
from glass.io.json_io import write_json


def _star_field(shape: tuple[int, int] = (96, 112)) -> np.ndarray:
    image = np.full(shape, 10.0, dtype=np.float32)
    yy, xx = np.indices(shape, dtype=np.float32)
    for x, y, flux in [
        (12, 17, 100.0),
        (30, 42, 220.0),
        (71, 15, 160.0),
        (88, 63, 180.0),
        (45, 79, 250.0),
        (19, 86, 130.0),
        (101, 33, 145.0),
        (53, 55, 190.0),
    ]:
        image += flux * np.exp(-(((xx - x) ** 2 + (yy - y) ** 2) / (2.0 * 1.4**2)))
    return image.astype(np.float32)


def _shift_image(data: np.ndarray, dx: int, dy: int) -> np.ndarray:
    output = np.zeros_like(data, dtype=np.float32)
    h, w = data.shape
    src_x0 = max(0, -dx)
    src_x1 = min(w, w - dx)
    dst_x0 = max(0, dx)
    dst_x1 = min(w, w + dx)
    src_y0 = max(0, -dy)
    src_y1 = min(h, h - dy)
    dst_y0 = max(0, dy)
    dst_y1 = min(h, h + dy)
    if src_x0 < src_x1 and src_y0 < src_y1:
        output[dst_y0:dst_y1, dst_x0:dst_x1] = data[src_y0:src_y1, src_x0:src_x1]
    return output


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


def test_estimate_triangle_asterism_transform_similarity_with_outlier():
    import math

    points = np.array(
        [(10, 10), (20, 10), (10, 25), (30, 30), (5, 35), (35, 5), (25, 18), (14, 32)],
        dtype=np.float64,
    )
    reference = [Star(float(x), float(y), 1000.0 - i) for i, (x, y) in enumerate(points)]
    angle = math.radians(-7.0)
    scale = 0.98
    linear = scale * np.array(
        [[math.cos(angle), -math.sin(angle)], [math.sin(angle), math.cos(angle)]],
        dtype=np.float64,
    )
    translation = np.array([-4.0, 3.0], dtype=np.float64)
    moving_points = (points - translation) @ np.linalg.inv(linear).T
    moving = [Star(float(x), float(y), 1000.0 - i) for i, (x, y) in enumerate(moving_points)]
    moving.append(Star(100.0, 100.0, 1.0))

    result = estimate_triangle_asterism_transform(
        reference,
        moving,
        "similarity",
        min_inliers=8,
        tolerance_px=0.5,
        neighbors=5,
        descriptor_radius=0.1,
    )

    assert result.status == "ok"
    assert result.inliers == 8
    assert result.rms_px < 1.0e-5
    assert np.allclose(np.asarray(result.matrix)[:2, :2], linear, atol=1.0e-6)
    assert np.allclose(np.asarray(result.matrix)[:2, 2], translation, atol=1.0e-6)
    assert any("triangle_asterism_descriptor_matches" in warning for warning in result.warnings)


def test_estimate_star_transform_homography_model():
    points = np.array(
        [
            (10, 10),
            (20, 10),
            (10, 25),
            (30, 30),
            (5, 35),
            (35, 5),
            (25, 18),
            (14, 32),
            (45, 20),
            (40, 40),
        ],
        dtype=np.float64,
    )
    matrix = np.array(
        [[1.01, 0.02, 2.0], [-0.01, 0.99, -3.0], [0.0001, -0.00008, 1.0]],
        dtype=np.float64,
    )
    inverse = np.linalg.inv(matrix)
    homogeneous = np.hstack([points, np.ones((points.shape[0], 1), dtype=np.float64)])
    moving_h = homogeneous @ inverse.T
    moving_points = moving_h[:, :2] / moving_h[:, 2:3]
    reference = [Star(float(x), float(y), 1000.0 - i) for i, (x, y) in enumerate(points)]
    moving = [Star(float(x), float(y), 1000.0 - i) for i, (x, y) in enumerate(moving_points)]

    result = estimate_star_transform(reference, moving, "homography", min_inliers=8, tolerance_px=0.75)

    assert result.status == "ok"
    assert result.inliers >= 8
    assert result.rms_px < 1.0e-4
    estimated = np.asarray(result.matrix, dtype=np.float64)
    estimated = estimated / estimated[2, 2]
    expected = matrix / matrix[2, 2]
    assert np.allclose(estimated, expected, atol=1.0e-5)
    assert any("homography model" in warning for warning in result.warnings)


def test_estimate_astroalign_transform_translation_like_similarity():
    pytest.importorskip("astroalign")
    reference = _star_field()
    moving = _shift_image(reference, 4, -3)

    result = estimate_astroalign_transform(reference, moving, max_control_points=50, detection_sigma=3, min_area=3)

    assert result.status == "ok"
    assert result.transform_model == "similarity"
    assert result.inliers >= 6
    assert result.rms_px < 0.1
    assert abs(result.matrix[0][2] + 4.0) < 0.1
    assert abs(result.matrix[1][2] - 3.0) < 0.1
    assert any("astroalign" in warning for warning in result.warnings)


def test_triangle_asterism_transform_agrees_with_astroalign_on_star_field():
    pytest.importorskip("astroalign")
    reference_image = _star_field()
    moving_image = _shift_image(reference_image, 4, -3)
    reference_stars = detect_stars(reference_image, threshold_sigma=3, max_stars=50)
    moving_stars = detect_stars(moving_image, threshold_sigma=3, max_stars=50)

    result = estimate_triangle_asterism_transform(
        reference_stars,
        moving_stars,
        "similarity",
        min_inliers=6,
        tolerance_px=0.5,
        neighbors=5,
        descriptor_radius=0.1,
    )
    astroalign_result = estimate_astroalign_transform(
        reference_image,
        moving_image,
        max_control_points=50,
        detection_sigma=3,
        min_area=3,
    )

    assert result.status == "ok"
    assert result.inliers >= 6
    assert result.rms_px < 0.1
    assert abs(result.matrix[0][2] - astroalign_result.matrix[0][2]) < 0.25
    assert abs(result.matrix[1][2] - astroalign_result.matrix[1][2]) < 0.25


def test_register_calibrated_frames_can_use_astroalign_backend(tmp_path):
    pytest.importorskip("astroalign")
    reference = _star_field()
    moving = _shift_image(reference, 4, -3)
    run = tmp_path / "run"
    cache = run / "calibrated_cache"
    cache.mkdir(parents=True)
    ref_path = cache / "ref.fits"
    moving_path = cache / "moving.fits"
    write_fits_data(ref_path, reference)
    write_fits_data(moving_path, moving)
    write_json(
        run / "calibration_artifacts.json",
        {
            "schema_version": 1,
            "calibrated_lights": [
                {"frame_id": "ref", "path": str(ref_path)},
                {"frame_id": "moving", "path": str(moving_path)},
            ],
        },
    )
    write_json(
        run / "frame_quality.json",
        {
            "schema_version": 1,
            "reference_frame_id": "ref",
            "frame_quality": [
                {"frame_id": "ref", "background_median": 10.0, "background_rms": 1.0, "star_count": 8},
                {"frame_id": "moving", "background_median": 10.0, "background_rms": 1.0, "star_count": 8},
            ],
        },
    )
    write_json(
        run / "processing_plan.json",
        {
            "schema_version": 1,
            "registration_policy": {
                "transform_model": "similarity",
                "astroalign_detection_sigma": 3,
                "astroalign_min_area": 3,
            },
        },
    )

    payload = register_calibrated_frames(run, tile_size=64, preview_max_dimension=256, method="astroalign")
    moving_result = next(item for item in payload["registration_results"] if item["frame_id"] == "moving")

    assert payload["method"] == "astroalign"
    assert payload["transform_model"] == "similarity"
    assert payload["astroalign"]["license"] == "MIT"
    assert moving_result["status"] == "ok"
    assert moving_result["registration_solution_source"] == "open_source_astroalign_preview"
    assert abs(moving_result["matrix"][0][2] + 4.0) < 0.1
    assert abs(moving_result["matrix"][1][2] - 3.0) < 0.1
    assert any("astroalign" in warning for warning in moving_result["warnings"])


def test_register_calibrated_frames_can_override_reference_by_stem(tmp_path):
    reference = _star_field()
    moving = _shift_image(reference, 4, -3)
    run = tmp_path / "run"
    cache = run / "calibrated_cache"
    cache.mkdir(parents=True)
    auto_ref_path = cache / "auto_ref.fits"
    user_ref_path = cache / "user_ref.fits"
    moving_path = cache / "moving.fits"
    write_fits_data(auto_ref_path, moving)
    write_fits_data(user_ref_path, reference)
    write_fits_data(moving_path, moving)
    write_json(
        run / "calibration_artifacts.json",
        {
            "schema_version": 1,
            "calibrated_lights": [
                {"frame_id": "auto_ref", "path": str(auto_ref_path)},
                {"frame_id": "user_ref", "path": str(user_ref_path)},
                {"frame_id": "moving", "path": str(moving_path)},
            ],
        },
    )
    write_json(
        run / "frame_quality.json",
        {
            "schema_version": 1,
            "reference_frame_id": "auto_ref",
            "frame_quality": [
                {"frame_id": "auto_ref", "background_median": 10.0, "background_rms": 1.0, "star_count": 8},
                {"frame_id": "user_ref", "background_median": 10.0, "background_rms": 1.0, "star_count": 8},
                {"frame_id": "moving", "background_median": 10.0, "background_rms": 1.0, "star_count": 8},
            ],
        },
    )
    write_json(
        run / "processing_plan.json",
        {
            "schema_version": 1,
            "registration_policy": {},
            "frames": [
                {"id": "auto_ref", "path": str(auto_ref_path)},
                {"id": "user_ref", "path": str(tmp_path / "originals" / "LIGHT_H_USER_REF.fits")},
                {"id": "moving", "path": str(moving_path)},
            ],
        },
    )

    payload = register_calibrated_frames(
        run,
        tile_size=64,
        preview_max_dimension=256,
        method="auto",
        reference_frame_id="LIGHT_H_USER_REF",
    )

    assert payload["reference_frame_id"] == "user_ref"
    assert payload["quality_reference_frame_id"] == "auto_ref"
    assert payload["requested_reference_frame_id"] == "LIGHT_H_USER_REF"
    user_ref = next(item for item in payload["registration_results"] if item["frame_id"] == "user_ref")
    moving_result = next(item for item in payload["registration_results"] if item["frame_id"] == "moving")
    assert user_ref["status"] == "reference"
    assert moving_result["status"] == "ok"


def test_register_calibrated_frames_records_astroalign_failure(tmp_path, monkeypatch):
    import glass.engine.registration as registration_module

    reference = _star_field()
    moving = np.zeros_like(reference)
    run = tmp_path / "run"
    cache = run / "calibrated_cache"
    cache.mkdir(parents=True)
    ref_path = cache / "ref.fits"
    moving_path = cache / "moving.fits"
    write_fits_data(ref_path, reference)
    write_fits_data(moving_path, moving)
    write_json(
        run / "calibration_artifacts.json",
        {
            "schema_version": 1,
            "calibrated_lights": [
                {"frame_id": "ref", "path": str(ref_path)},
                {"frame_id": "moving", "path": str(moving_path)},
            ],
        },
    )
    write_json(
        run / "frame_quality.json",
        {
            "schema_version": 1,
            "reference_frame_id": "ref",
            "frame_quality": [
                {"frame_id": "ref", "background_median": 10.0, "background_rms": 1.0, "star_count": 8},
                {"frame_id": "moving", "background_median": 0.0, "background_rms": 1.0, "star_count": 0},
            ],
        },
    )
    write_json(run / "processing_plan.json", {"schema_version": 1, "registration_policy": {}})

    def fail_astroalign(*args, **kwargs):
        raise RuntimeError("synthetic astroalign failure")

    monkeypatch.setattr(registration_module, "estimate_astroalign_transform", fail_astroalign)

    payload = register_calibrated_frames(run, tile_size=64, preview_max_dimension=256, method="astroalign")
    moving_result = next(item for item in payload["registration_results"] if item["frame_id"] == "moving")

    assert moving_result["status"] == "failed"
    assert moving_result["registration_solution_source"] == "open_source_astroalign_preview"
    assert moving_result["matrix"] == [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    assert any("synthetic astroalign failure" in warning for warning in moving_result["warnings"])


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
    from glass.engine.registration import FitsImageReader

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
