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
        raise AssertionError("star_local_max_mask_f32 is missing from glass_cuda")

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
        raise AssertionError("ResidentCalibratedStack is missing from glass_cuda")

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
        raise AssertionError("star_candidates_f32 is missing from glass_cuda")

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
        raise AssertionError("star_top_candidates_f32 is missing from glass_cuda")

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
        raise AssertionError("star_grid_candidates_f32 is missing from glass_cuda")

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


def test_resident_stack_star_top_nms_candidates_from_device_frame():
    module = cuda_module_or_skip()
    image = np.zeros((32, 32), dtype=np.float32)
    image[8, 8] = 50.0
    image[9, 9] = 49.0
    image[24, 24] = 45.0
    stack = module.ResidentCalibratedStack(1, 32, 32)
    stack.upload_calibrated_frame(0, image)

    result = stack.star_top_nms_candidates(0, 10.0, 8, 4, 4.0)
    points = {(int(x), int(y)) for x, y in zip(result["x"], result["y"], strict=True)}

    assert result["count"] == 2
    assert result["stored_count"] == 2
    assert points == {(8, 8), (24, 24)}


def test_resident_stack_star_grid_top_nms_candidates_from_device_frame():
    module = cuda_module_or_skip()
    image = np.zeros((32, 32), dtype=np.float32)
    image[6, 6] = 50.0
    image[7, 7] = 49.0
    image[24, 6] = 48.0
    image[6, 24] = 47.0
    image[24, 24] = 46.0
    stack = module.ResidentCalibratedStack(1, 32, 32)
    stack.upload_calibrated_frame(0, image)

    result = stack.star_grid_top_nms_candidates(0, 10.0, 2, 2, 2, 4, 4.0)
    points = {(int(x), int(y)) for x, y in zip(result["x"], result["y"], strict=True)}

    assert result["count"] == 4
    assert result["stored_count"] == 4
    assert points == {(6, 6), (24, 6), (6, 24), (24, 24)}


def test_resident_stack_star_grid_top_nms_candidates_batch_matches_single_calls():
    module = cuda_module_or_skip()
    if not hasattr(module.ResidentCalibratedStack, "star_grid_top_nms_candidates_batch"):
        raise AssertionError("ResidentCalibratedStack.star_grid_top_nms_candidates_batch is missing")

    first = np.zeros((32, 32), dtype=np.float32)
    first[6, 6] = 50.0
    first[7, 7] = 49.0
    first[24, 6] = 48.0
    first[6, 24] = 47.0
    second = np.zeros((32, 32), dtype=np.float32)
    second[5, 5] = 60.0
    second[20, 8] = 42.0
    second[9, 23] = 41.0
    second[22, 22] = 40.0

    stack = module.ResidentCalibratedStack(2, 32, 32)
    stack.upload_calibrated_frame(0, first)
    stack.upload_calibrated_frame(1, second)

    batch = list(stack.star_grid_top_nms_candidates_batch([0, 1], 10.0, 2, 2, 2, 4, 4.0))
    singles = [
        stack.star_grid_top_nms_candidates(0, 10.0, 2, 2, 2, 4, 4.0),
        stack.star_grid_top_nms_candidates(1, 10.0, 2, 2, 2, 4, 4.0),
    ]

    assert len(batch) == 2
    for expected_index, batch_item, single_item in zip(range(2), batch, singles, strict=True):
        assert int(batch_item["frame_index"]) == expected_index
        assert int(batch_item["count"]) == int(single_item["count"])
        assert int(batch_item["stored_count"]) == int(single_item["stored_count"])
        assert np.array_equal(batch_item["x"], single_item["x"])
        assert np.array_equal(batch_item["y"], single_item["y"])
        assert np.array_equal(batch_item["flux"], single_item["flux"])


def test_gpu_star_top_candidate_selectors_are_repeatable_under_contention():
    module = cuda_module_or_skip()
    required = [
        "star_top_candidates_f32",
        "star_top_nms_candidates_f32",
        "star_grid_top_nms_candidates_f32",
    ]
    for name in required:
        if not hasattr(module, name):
            raise AssertionError(f"{name} is missing from glass_cuda")

    rng = np.random.default_rng(20260513)
    image = rng.normal(0.0, 0.01, size=(192, 192)).astype(np.float32)
    for index in range(900):
        x = 2 + (index * 37) % 188
        y = 2 + (index * 53) % 188
        image[y, x] = np.float32(1000.0 + index)
    threshold = 100.0

    selectors = [
        lambda: module.star_top_candidates_f32(image, threshold, 64),
        lambda: module.star_top_nms_candidates_f32(image, threshold, 256, 64, 8.0),
        lambda: module.star_grid_top_nms_candidates_f32(image, threshold, 12, 12, 4, 64, 8.0),
    ]

    for selector in selectors:
        first = selector()
        first_catalog = np.column_stack([first["x"], first["y"], first["flux"]])
        for _ in range(4):
            current = selector()
            current_catalog = np.column_stack([current["x"], current["y"], current["flux"]])
            assert np.array_equal(current_catalog, first_catalog)
