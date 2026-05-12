from __future__ import annotations

import numpy as np

from gpwbpp.engine.warp import warp_registered_frames
from gpwbpp.io.fits_io import read_fits_data, write_fits_data
from gpwbpp.io.json_io import write_json


def _warp_matrix_bilinear_reference(
    data: np.ndarray,
    matrix: list[list[float]],
    fill: float = 0.0,
) -> tuple[np.ndarray, np.ndarray]:
    image = np.asarray(data, dtype=np.float32)
    h, w = image.shape
    output = np.full_like(image, fill, dtype=np.float32)
    coverage = np.zeros_like(image, dtype=np.float32)
    inverse = np.linalg.inv(np.asarray(matrix, dtype=np.float64))
    for y in range(h):
        for x in range(w):
            source = inverse @ np.asarray([x, y, 1.0], dtype=np.float64)
            if abs(source[2]) <= 1.0e-12:
                continue
            sx = float(source[0] / source[2])
            sy = float(source[1] / source[2])
            if sx < 0.0 or sx > float(w - 1) or sy < 0.0 or sy > float(h - 1):
                continue
            x0 = int(np.floor(sx))
            y0 = int(np.floor(sy))
            x1 = min(x0 + 1, w - 1)
            y1 = min(y0 + 1, h - 1)
            tx = np.float32(sx - x0)
            ty = np.float32(sy - y0)
            top = image[y0, x0] * (1.0 - tx) + image[y0, x1] * tx
            bottom = image[y1, x0] * (1.0 - tx) + image[y1, x1] * tx
            output[y, x] = top * (1.0 - ty) + bottom * ty
            coverage[y, x] = 1.0
    return output, coverage


def test_warp_registered_frames_uses_matrix_bilinear_for_fractional_translation(tmp_path):
    run = tmp_path / "run"
    source_path = run / "calibrated" / "light.fits"
    data = np.arange(36, dtype=np.float32).reshape(6, 6)
    matrix = [[1.0, 0.0, 1.25], [0.0, 1.0, -0.5], [0.0, 0.0, 1.0]]
    write_fits_data(source_path, data)
    write_json(
        run / "calibration_artifacts.json",
        {"schema_version": 1, "calibrated_lights": [{"frame_id": "L001", "path": str(source_path)}]},
    )
    write_json(
        run / "registration_results.json",
        {
            "schema_version": 1,
            "registration_results": [
                {
                    "frame_id": "L001",
                    "status": "ok",
                    "matrix": matrix,
                    "warnings": [],
                }
            ],
        },
    )

    result = warp_registered_frames(run, tile_size=3)
    row = result["warp_results"][0]
    registered = read_fits_data(row["registered_path"])
    coverage = read_fits_data(row["coverage_path"])
    expected, expected_coverage = _warp_matrix_bilinear_reference(data, matrix)

    assert row["warp_model"] == "matrix_bilinear"
    assert row["tile_count"] == 4
    assert np.allclose(registered, expected, atol=1.0e-6)
    assert np.array_equal(coverage, expected_coverage)


def test_warp_registered_frames_preserves_integer_translation_fast_path(tmp_path):
    run = tmp_path / "run"
    source_path = run / "calibrated" / "light.fits"
    data = np.arange(25, dtype=np.float32).reshape(5, 5)
    matrix = [[1.0, 0.0, 1.0], [0.0, 1.0, -2.0], [0.0, 0.0, 1.0]]
    write_fits_data(source_path, data)
    write_json(
        run / "calibration_artifacts.json",
        {"schema_version": 1, "calibrated_lights": [{"frame_id": "L001", "path": str(source_path)}]},
    )
    write_json(
        run / "registration_results.json",
        {
            "schema_version": 1,
            "registration_results": [
                {
                    "frame_id": "L001",
                    "status": "ok",
                    "matrix": matrix,
                    "warnings": [],
                }
            ],
        },
    )

    result = warp_registered_frames(run, tile_size=3)

    assert result["warp_results"][0]["warp_model"] == "integer_translation_nearest"
