from __future__ import annotations

import numpy as np

from tests.conftest import cuda_module_or_skip


def _cpu_local_max_mask(data: np.ndarray, threshold: float) -> np.ndarray:
    image = np.asarray(data, dtype=np.float32)
    h, w = image.shape
    mask = np.zeros((h, w), dtype=np.uint8)
    if h < 3 or w < 3:
        return mask
    core = image[1:-1, 1:-1]
    candidate = np.isfinite(core) & (core > np.float32(threshold))
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            candidate &= core >= image[1 + dy : h - 1 + dy, 1 + dx : w - 1 + dx]
    mask[1:-1, 1:-1] = candidate.astype(np.uint8)
    return mask


def test_gpu_star_local_max_mask_matches_cpu():
    module = cuda_module_or_skip()
    if not hasattr(module, "star_local_max_mask_f32"):
        raise AssertionError("star_local_max_mask_f32 is missing from gpwbpp_cuda")

    image = np.zeros((8, 9), dtype=np.float32)
    image[2, 3] = 10.0
    image[5, 6] = 20.0
    image[1, 1] = 4.0
    image[4, 4] = np.nan
    image[0, 3] = 100.0

    gpu = module.star_local_max_mask_f32(image, 5.0)
    expected = _cpu_local_max_mask(image, 5.0)

    assert gpu.dtype == np.uint8
    assert np.array_equal(gpu, expected)
    assert int(np.sum(gpu)) == 2


def test_resident_stack_star_local_max_mask_uses_device_frame():
    module = cuda_module_or_skip()
    if not hasattr(module, "ResidentCalibratedStack"):
        raise AssertionError("ResidentCalibratedStack is missing from gpwbpp_cuda")

    image = np.zeros((6, 7), dtype=np.float32)
    image[2, 2] = 11.0
    image[3, 5] = 12.0
    stack = module.ResidentCalibratedStack(1, 6, 7)
    stack.upload_calibrated_frame(0, image)

    gpu = stack.star_local_max_mask(0, 5.0)
    expected = _cpu_local_max_mask(image, 5.0)

    assert np.array_equal(gpu, expected)
    assert int(np.sum(gpu)) == 2


def test_gpu_star_candidates_compacts_local_maxima():
    module = cuda_module_or_skip()
    if not hasattr(module, "star_candidates_f32"):
        raise AssertionError("star_candidates_f32 is missing from gpwbpp_cuda")

    image = np.zeros((7, 8), dtype=np.float32)
    image[2, 2] = 11.0
    image[4, 5] = 20.0
    image[1, 6] = 9.0

    result = module.star_candidates_f32(image, 5.0, 8)
    coords = {(int(x), int(y), float(f)) for x, y, f in zip(result["x"], result["y"], result["flux"], strict=True)}

    assert result["count"] == 3
    assert result["stored_count"] == 3
    assert coords == {(2, 2, 11.0), (5, 4, 20.0), (6, 1, 9.0)}


def test_resident_stack_star_candidates_from_device_frame():
    module = cuda_module_or_skip()
    image = np.zeros((7, 8), dtype=np.float32)
    image[2, 2] = 11.0
    image[4, 5] = 20.0
    image[1, 6] = 9.0
    stack = module.ResidentCalibratedStack(1, 7, 8)
    stack.upload_calibrated_frame(0, image)

    result = stack.star_candidates(0, 5.0, 2)
    coords = {(int(x), int(y)) for x, y in zip(result["x"], result["y"], strict=True)}

    assert result["count"] == 3
    assert result["stored_count"] == 2
    assert coords.issubset({(2, 2), (5, 4), (6, 1)})


def test_gpu_star_top_candidates_sorts_by_flux_and_caps():
    module = cuda_module_or_skip()
    if not hasattr(module, "star_top_candidates_f32"):
        raise AssertionError("star_top_candidates_f32 is missing from gpwbpp_cuda")

    image = np.zeros((9, 10), dtype=np.float32)
    image[2, 2] = 11.0
    image[4, 5] = 20.0
    image[1, 6] = 9.0
    image[7, 3] = 17.0

    result = module.star_top_candidates_f32(image, 5.0, 3)

    assert result["count"] == 4
    assert result["stored_count"] == 3
    assert np.array_equal(result["flux"], np.array([20.0, 17.0, 11.0], dtype=np.float32))
    assert [(int(x), int(y)) for x, y in zip(result["x"], result["y"], strict=True)] == [
        (5, 4),
        (3, 7),
        (2, 2),
    ]


def test_gpu_star_grid_candidates_keeps_brightest_per_cell():
    module = cuda_module_or_skip()
    if not hasattr(module, "star_grid_candidates_f32"):
        raise AssertionError("star_grid_candidates_f32 is missing from gpwbpp_cuda")

    image = np.zeros((8, 8), dtype=np.float32)
    image[1, 1] = 9.0
    image[3, 2] = 15.0
    image[1, 6] = 12.0
    image[6, 2] = 18.0
    image[6, 6] = 7.0

    result = module.star_grid_candidates_f32(image, 5.0, 2, 2)

    assert result["count"] == 5
    assert result["stored_count"] == 4
    assert np.array_equal(result["flux"], np.array([18.0, 15.0, 12.0, 7.0], dtype=np.float32))
    assert [(int(x), int(y)) for x, y in zip(result["x"], result["y"], strict=True)] == [
        (2, 6),
        (2, 3),
        (6, 1),
        (6, 6),
    ]
    assert result["grid_cols"] == 2
    assert result["grid_rows"] == 2


def test_resident_stack_star_top_candidates_from_device_frame():
    module = cuda_module_or_skip()
    image = np.zeros((9, 10), dtype=np.float32)
    image[2, 2] = 11.0
    image[4, 5] = 20.0
    image[1, 6] = 9.0
    image[7, 3] = 17.0
    stack = module.ResidentCalibratedStack(1, 9, 10)
    stack.upload_calibrated_frame(0, image)

    result = stack.star_top_candidates(0, 5.0, 2)

    assert result["count"] == 4
    assert result["stored_count"] == 2
    assert np.array_equal(result["flux"], np.array([20.0, 17.0], dtype=np.float32))
    assert [(int(x), int(y)) for x, y in zip(result["x"], result["y"], strict=True)] == [
        (5, 4),
        (3, 7),
    ]
