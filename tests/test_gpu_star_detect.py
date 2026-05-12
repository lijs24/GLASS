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
