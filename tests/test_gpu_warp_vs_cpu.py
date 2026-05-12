from __future__ import annotations

import numpy as np

from gpwbpp.cpu.warp import warp_translation
from tests.conftest import cuda_module_or_skip


def _warp_translation_bilinear_cpu(data: np.ndarray, dx: float, dy: float, fill: float = 0.0) -> tuple[np.ndarray, np.ndarray]:
    image = np.asarray(data, dtype=np.float32)
    h, w = image.shape
    output = np.full_like(image, fill, dtype=np.float32)
    coverage = np.zeros_like(image, dtype=np.float32)
    for y in range(h):
        sy = float(y) - float(dy)
        if sy < 0.0 or sy > float(h - 1):
            continue
        y0 = int(np.floor(sy))
        y1 = min(y0 + 1, h - 1)
        ty = np.float32(sy - y0)
        for x in range(w):
            sx = float(x) - float(dx)
            if sx < 0.0 or sx > float(w - 1):
                continue
            x0 = int(np.floor(sx))
            x1 = min(x0 + 1, w - 1)
            tx = np.float32(sx - x0)
            top = image[y0, x0] * (1.0 - tx) + image[y0, x1] * tx
            bottom = image[y1, x0] * (1.0 - tx) + image[y1, x1] * tx
            output[y, x] = top * (1.0 - ty) + bottom * ty
            coverage[y, x] = 1.0
    return output, coverage


def test_gpu_warp_translation_matches_cpu():
    module = cuda_module_or_skip()
    data = np.arange(25, dtype=np.float32).reshape(5, 5)
    gpu, coverage = module.warp_translation_f32(data, 1, -2, 0.0)
    cpu = warp_translation(data, 1, -2, 0.0)
    assert np.allclose(gpu, cpu)
    assert coverage.shape == data.shape
    assert np.sum(coverage) == 12


def test_gpu_warp_translation_bilinear_matches_cpu_reference():
    module = cuda_module_or_skip()
    if not hasattr(module, "warp_translation_bilinear_f32"):
        raise AssertionError("warp_translation_bilinear_f32 is missing from gpwbpp_cuda")

    data = np.arange(36, dtype=np.float32).reshape(6, 6)
    gpu, gpu_coverage = module.warp_translation_bilinear_f32(data, 1.25, -0.5, -1.0)
    expected, expected_coverage = _warp_translation_bilinear_cpu(data, 1.25, -0.5, -1.0)

    assert np.allclose(gpu, expected, atol=1.0e-6)
    assert np.array_equal(gpu_coverage, expected_coverage)


def test_gpu_catalog_refined_translation_drives_bilinear_warp():
    module = cuda_module_or_skip()
    reference = np.zeros((64, 64), dtype=np.float32)
    stars = np.array(
        [
            (12.25, 14.50, 150.0),
            (24.00, 20.75, 230.0),
            (41.50, 18.25, 180.0),
            (16.75, 42.00, 130.0),
            (49.25, 45.50, 210.0),
            (35.50, 33.25, 170.0),
        ],
        dtype=np.float32,
    )
    yy, xx = np.indices(reference.shape, dtype=np.float32)
    for x, y, flux in stars:
        reference += flux * np.exp(-(((xx - x) ** 2 + (yy - y) ** 2) / (2.0 * 1.2**2)))

    true_delta = np.array([2.25, -1.5], dtype=np.float32)
    moving, _moving_coverage = _warp_translation_bilinear_cpu(reference, -float(true_delta[0]), -float(true_delta[1]), 0.0)
    moving_stars = stars[:, :2] - true_delta
    result = module.estimate_translation_from_catalogs_f32(
        stars[:, 0],
        stars[:, 1],
        moving_stars[:, 0],
        moving_stars[:, 1],
        0.2,
    )

    aligned, coverage = module.warp_translation_bilinear_f32(
        moving,
        result["refined_dx"],
        result["refined_dy"],
        0.0,
    )
    valid = coverage > 0.0
    before = float(np.sqrt(np.mean((moving[valid] - reference[valid]) ** 2)))
    after = float(np.sqrt(np.mean((aligned[valid] - reference[valid]) ** 2)))

    assert abs(result["refined_dx"] - float(true_delta[0])) < 1.0e-5
    assert abs(result["refined_dy"] - float(true_delta[1])) < 1.0e-5
    assert result["mutual_inliers"] == len(stars)
    assert after < before * 0.5
