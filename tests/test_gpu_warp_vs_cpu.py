from __future__ import annotations

import numpy as np

from glass.cpu.warp import warp_translation
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


def _warp_matrix_bilinear_cpu(
    data: np.ndarray,
    matrix: np.ndarray,
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
            if abs(float(source[2])) <= 1.0e-12:
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


def _sinc(value: float) -> float:
    if abs(value) < 1.0e-6:
        return 1.0
    pix = np.pi * value
    return float(np.sin(pix) / pix)


def _lanczos3_weight(value: float) -> float:
    if abs(value) >= 3.0:
        return 0.0
    return _sinc(value) * _sinc(value / 3.0)


def _warp_matrix_lanczos3_cpu(
    data: np.ndarray,
    matrix: np.ndarray,
    fill: float = 0.0,
    clamping_threshold: float = -1.0,
) -> tuple[np.ndarray, np.ndarray]:
    image = np.asarray(data, dtype=np.float32)
    h, w = image.shape
    output = np.full_like(image, fill, dtype=np.float32)
    coverage = np.zeros_like(image, dtype=np.float32)
    inverse = np.linalg.inv(np.asarray(matrix, dtype=np.float64))
    for y in range(h):
        for x in range(w):
            source = inverse @ np.asarray([x, y, 1.0], dtype=np.float64)
            if abs(float(source[2])) <= 1.0e-12:
                continue
            sx = float(source[0] / source[2])
            sy = float(source[1] / source[2])
            if sx < 2.0 or sx >= float(w - 3) or sy < 2.0 or sy >= float(h - 3):
                continue
            x0 = int(np.floor(sx))
            y0 = int(np.floor(sy))
            weighted_sum = 0.0
            weight_sum = 0.0
            values: list[float] = []
            for yy in range(y0 - 2, y0 + 4):
                wy = _lanczos3_weight(sy - float(yy))
                for xx in range(x0 - 2, x0 + 4):
                    value = float(image[yy, xx])
                    if not np.isfinite(value):
                        continue
                    weight = wy * _lanczos3_weight(sx - float(xx))
                    weighted_sum += value * weight
                    weight_sum += weight
                    values.append(value)
            if abs(weight_sum) <= 1.0e-12:
                continue
            value = weighted_sum / weight_sum
            if clamping_threshold >= 0.0 and values:
                local_min = min(values)
                local_max = max(values)
                local_range = local_max - local_min
                value = min(
                    local_max + clamping_threshold * local_range,
                    max(local_min - clamping_threshold * local_range, value),
                )
            output[y, x] = np.float32(value)
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
        raise AssertionError("warp_translation_bilinear_f32 is missing from glass_cuda")

    data = np.arange(36, dtype=np.float32).reshape(6, 6)
    gpu, gpu_coverage = module.warp_translation_bilinear_f32(data, 1.25, -0.5, -1.0)
    expected, expected_coverage = _warp_translation_bilinear_cpu(data, 1.25, -0.5, -1.0)

    assert np.allclose(gpu, expected, atol=1.0e-6)
    assert np.array_equal(gpu_coverage, expected_coverage)


def test_gpu_warp_matrix_bilinear_matches_cpu_reference():
    module = cuda_module_or_skip()
    if not hasattr(module, "warp_matrix_bilinear_f32"):
        raise AssertionError("warp_matrix_bilinear_f32 is missing from glass_cuda")

    data = np.arange(49, dtype=np.float32).reshape(7, 7)
    angle = np.deg2rad(3.0)
    matrix = np.array(
        [
            [np.cos(angle), -np.sin(angle), 1.2],
            [np.sin(angle), np.cos(angle), -0.4],
            [0.0, 0.0, 1.0],
        ],
        dtype=np.float32,
    )
    gpu, gpu_coverage = module.warp_matrix_bilinear_f32(data, matrix, -1.0)
    expected, expected_coverage = _warp_matrix_bilinear_cpu(data, matrix, -1.0)

    assert np.allclose(gpu, expected, atol=1.0e-5)
    assert np.array_equal(gpu_coverage, expected_coverage)


def test_gpu_warp_matrix_lanczos3_matches_cpu_reference():
    module = cuda_module_or_skip()
    if not hasattr(module, "warp_matrix_lanczos3_f32"):
        raise AssertionError("warp_matrix_lanczos3_f32 is missing from glass_cuda")

    yy, xx = np.indices((12, 13), dtype=np.float32)
    data = 0.2 * xx + 0.4 * yy
    data[:, 7:] += 5.0
    angle = np.deg2rad(1.0)
    matrix = np.array(
        [
            [np.cos(angle), -np.sin(angle), 0.35],
            [np.sin(angle), np.cos(angle), -0.25],
            [0.0, 0.0, 1.0],
        ],
        dtype=np.float32,
    )
    gpu, gpu_coverage = module.warp_matrix_lanczos3_f32(data, matrix, -1.0, 0.30)
    expected, expected_coverage = _warp_matrix_lanczos3_cpu(data, matrix, -1.0, 0.30)

    assert np.allclose(gpu, expected, atol=3.0e-5)
    assert np.array_equal(gpu_coverage, expected_coverage)


def test_resident_stack_matrix_bilinear_warp_matches_cpu_reference():
    module = cuda_module_or_skip()
    if not hasattr(module.ResidentCalibratedStack, "apply_matrix_bilinear_frame"):
        raise AssertionError("ResidentCalibratedStack.apply_matrix_bilinear_frame is missing")

    data = np.arange(36, dtype=np.float32).reshape(6, 6)
    matrix = np.array([[1.0, 0.0, 1.25], [0.0, 1.0, -0.5], [0.0, 0.0, 1.0]], dtype=np.float32)
    stack = module.ResidentCalibratedStack(1, data.shape[0], data.shape[1])
    stack.upload_calibrated_frame(0, data)
    stack.apply_matrix_bilinear_frame(0, matrix, np.nan)
    warped, weight_map = stack.integrate_mean()
    expected, expected_coverage = _warp_matrix_bilinear_cpu(data, matrix, np.nan)
    valid = expected_coverage > 0

    assert np.allclose(warped[valid], expected[valid], atol=1.0e-5)
    assert np.all(warped[~valid] == 0.0)
    assert np.array_equal(weight_map, expected_coverage)


def test_resident_stack_matrix_lanczos3_warp_matches_cpu_reference():
    module = cuda_module_or_skip()
    if not hasattr(module.ResidentCalibratedStack, "apply_matrix_lanczos3_frame"):
        raise AssertionError("ResidentCalibratedStack.apply_matrix_lanczos3_frame is missing")

    yy, xx = np.indices((12, 13), dtype=np.float32)
    data = np.sin(xx * 0.3) + np.cos(yy * 0.2)
    matrix = np.array([[1.0, 0.0, 0.4], [0.0, 1.0, -0.35], [0.0, 0.0, 1.0]], dtype=np.float32)
    stack = module.ResidentCalibratedStack(1, data.shape[0], data.shape[1])
    stack.upload_calibrated_frame(0, data)
    stack.apply_matrix_lanczos3_frame(0, matrix, np.nan, 0.30)
    warped, weight_map = stack.integrate_mean()
    expected, expected_coverage = _warp_matrix_lanczos3_cpu(data, matrix, np.nan, 0.30)
    valid = expected_coverage > 0

    assert np.allclose(warped[valid], expected[valid], atol=3.0e-5)
    assert np.all(warped[~valid] == 0.0)
    assert np.array_equal(weight_map, expected_coverage)


def test_resident_stack_matrix_bilinear_batch_warp_matches_cpu_reference():
    module = cuda_module_or_skip()
    if not hasattr(module.ResidentCalibratedStack, "apply_matrix_bilinear_frames"):
        raise AssertionError("ResidentCalibratedStack.apply_matrix_bilinear_frames is missing")

    data0 = np.arange(64, dtype=np.float32).reshape(8, 8)
    data1 = np.flipud(data0) + np.float32(3.5)
    angle0 = np.deg2rad(2.0)
    angle1 = np.deg2rad(-1.5)
    matrices = np.asarray(
        [
            [
                [np.cos(angle0), -np.sin(angle0), 0.75],
                [np.sin(angle0), np.cos(angle0), -0.35],
                [0.0, 0.0, 1.0],
            ],
            [
                [np.cos(angle1), -np.sin(angle1), -0.45],
                [np.sin(angle1), np.cos(angle1), 0.60],
                [0.0, 0.0, 1.0],
            ],
        ],
        dtype=np.float32,
    )
    stack = module.ResidentCalibratedStack(2, data0.shape[0], data0.shape[1])
    stack.upload_calibrated_frame(0, data0)
    stack.upload_calibrated_frame(1, data1)

    timing = stack.apply_matrix_bilinear_frames([0, 1], matrices, np.nan, dispatch="chunked")
    warped, weight_map = stack.integrate_mean()
    expected0, coverage0 = _warp_matrix_bilinear_cpu(data0, matrices[0], np.nan)
    expected1, coverage1 = _warp_matrix_bilinear_cpu(data1, matrices[1], np.nan)
    expected_weight = coverage0 + coverage1
    expected_sum = np.where(coverage0 > 0, expected0, 0.0) + np.where(
        coverage1 > 0,
        expected1,
        0.0,
    )
    expected = np.divide(
        expected_sum,
        expected_weight,
        out=np.zeros_like(expected_sum, dtype=np.float32),
        where=expected_weight > 0,
    )

    assert timing["timing_model"] == "native_chunked_batch_warp_scatter_one_sync"
    assert timing["frame_count"] == 2
    assert timing["interpolation"] == "bilinear"
    assert timing["inverse_upload_mode"] == "chunked_device_batch"
    assert timing["batch_chunk_frames"] >= 1
    assert timing["batch_chunk_count"] == 1
    assert timing["batch_workspace_bytes"] >= timing["batch_output_bytes"]
    assert timing["batch_output_bytes"] >= 2 * data0.size * 4
    assert timing["batch_coverage_bytes"] >= 2 * data0.size
    assert timing["index_upload_s"] >= 0.0
    assert timing["inverse_prepare_s"] >= 0.0
    assert timing["inverse_batch_alloc_s"] >= 0.0
    assert timing["inverse_batch_bytes"] == 2 * 9 * 4
    assert timing["inverse_upload_s"] >= 0.0
    assert timing["kernel_enqueue_s"] >= 0.0
    assert timing["coverage_reduce_enqueue_s"] >= 0.0
    assert timing["scatter_enqueue_s"] >= 0.0
    assert timing["warp_kernel_launches"] == 1
    assert timing["coverage_reduce_kernel_launches"] == 1
    assert timing["scatter_kernel_launches"] == 1
    assert timing["device_copy_enqueue_s"] >= 0.0
    assert timing["sync_s"] >= 0.0
    assert timing["total_s"] >= timing["kernel_enqueue_s"]
    assert np.allclose(warped, expected, atol=1.0e-5)
    assert np.array_equal(weight_map, expected_weight)


def test_resident_stack_matrix_bilinear_batch_default_dispatch_is_loop():
    module = cuda_module_or_skip()
    data = np.arange(36, dtype=np.float32).reshape(6, 6)
    matrix = np.array(
        [
            [1.0, 0.0, 0.35],
            [0.0, 1.0, -0.25],
            [0.0, 0.0, 1.0],
        ],
        dtype=np.float32,
    )
    stack = module.ResidentCalibratedStack(1, *data.shape)
    stack.upload_calibrated_frame(0, data)

    timing = stack.apply_matrix_bilinear_frames([0], matrix[None, :, :], np.nan)

    assert timing["timing_model"] == "native_loop_batched_inverse_one_sync"
    assert timing["inverse_upload_mode"] == "single_device_batch"
    assert timing["frame_count"] == 1


def test_resident_stack_matrix_bilinear_batch_respects_max_chunk_capacity():
    module = cuda_module_or_skip()
    if not hasattr(module.ResidentCalibratedStack, "apply_matrix_bilinear_frames"):
        raise AssertionError("ResidentCalibratedStack.apply_matrix_bilinear_frames is missing")

    base = np.arange(64, dtype=np.float32).reshape(8, 8)
    frames = [(base + np.float32(index * 7)).astype(np.float32) for index in range(5)]
    matrices = np.asarray(
        [
            [[1.0, 0.0, 0.10 * index], [0.0, 1.0, -0.05 * index], [0.0, 0.0, 1.0]]
            for index in range(5)
        ],
        dtype=np.float32,
    )
    stack = module.ResidentCalibratedStack(len(frames), frames[0].shape[0], frames[0].shape[1])
    for index, frame in enumerate(frames):
        stack.upload_calibrated_frame(index, frame)

    timing = stack.apply_matrix_bilinear_frames(
        list(range(len(frames))),
        matrices,
        np.nan,
        dispatch="chunked",
        max_chunk_capacity_frames=2,
    )
    warped, weight_map = stack.integrate_mean()
    expected_sum = np.zeros_like(frames[0], dtype=np.float32)
    expected_weight = np.zeros_like(frames[0], dtype=np.float32)
    for frame, matrix in zip(frames, matrices, strict=True):
        warped_frame, coverage = _warp_matrix_bilinear_cpu(frame, matrix, np.nan)
        expected_sum += np.where(coverage > 0, warped_frame, 0.0)
        expected_weight += coverage
    expected = np.divide(
        expected_sum,
        expected_weight,
        out=np.zeros_like(expected_sum, dtype=np.float32),
        where=expected_weight > 0,
    )

    assert timing["timing_model"] == "native_chunked_batch_warp_scatter_one_sync"
    assert timing["batch_capacity_source"] == "explicit_max_chunk_capacity"
    assert timing["batch_max_chunk_capacity_frames"] == 2
    assert timing["batch_chunk_frames"] == 2
    assert timing["batch_chunk_count"] == 3
    assert timing["chunk_metadata_upload_mode"] == "single_device_batch_reused_by_chunks"
    assert timing["index_upload_count"] == 1
    assert timing["inverse_upload_count"] == 1
    assert timing["inverse_batch_bytes"] == len(frames) * 9 * 4
    assert timing["warp_kernel_launches"] == 3
    assert timing["coverage_reduce_kernel_launches"] == 3
    assert timing["scatter_kernel_launches"] == 3
    assert timing["batch_output_bytes"] == 2 * frames[0].size * 4
    assert timing["batch_coverage_bytes"] == 2 * frames[0].size
    assert timing["batch_workspace_bytes"] == (
        timing["batch_output_bytes"]
        + timing["batch_coverage_bytes"]
        + len(frames) * 9 * 4
        + len(frames) * 8
    )
    assert np.allclose(warped, expected, atol=1.0e-5)
    assert np.array_equal(weight_map, expected_weight)


def test_resident_stack_matrix_lanczos3_batch_warp_matches_cpu_reference():
    module = cuda_module_or_skip()
    if not hasattr(module.ResidentCalibratedStack, "apply_matrix_lanczos3_frames"):
        raise AssertionError("ResidentCalibratedStack.apply_matrix_lanczos3_frames is missing")

    yy, xx = np.indices((14, 15), dtype=np.float32)
    data0 = np.sin(xx * 0.17) + np.cos(yy * 0.11) + 0.02 * xx
    data1 = np.cos(xx * 0.13) - np.sin(yy * 0.19) + 0.01 * yy
    angle0 = np.deg2rad(0.75)
    angle1 = np.deg2rad(-0.50)
    matrices = np.asarray(
        [
            [
                [np.cos(angle0), -np.sin(angle0), 0.20],
                [np.sin(angle0), np.cos(angle0), -0.15],
                [0.0, 0.0, 1.0],
            ],
            [
                [np.cos(angle1), -np.sin(angle1), -0.25],
                [np.sin(angle1), np.cos(angle1), 0.18],
                [0.0, 0.0, 1.0],
            ],
        ],
        dtype=np.float32,
    )
    stack = module.ResidentCalibratedStack(2, data0.shape[0], data0.shape[1])
    stack.upload_calibrated_frame(0, data0)
    stack.upload_calibrated_frame(1, data1)

    timing = stack.apply_matrix_lanczos3_frames([0, 1], matrices, np.nan, 0.30, dispatch="chunked")
    warped, weight_map = stack.integrate_mean()
    expected0, coverage0 = _warp_matrix_lanczos3_cpu(data0, matrices[0], np.nan, 0.30)
    expected1, coverage1 = _warp_matrix_lanczos3_cpu(data1, matrices[1], np.nan, 0.30)
    expected_weight = coverage0 + coverage1
    expected_sum = np.where(coverage0 > 0, expected0, 0.0) + np.where(
        coverage1 > 0,
        expected1,
        0.0,
    )
    expected = np.divide(
        expected_sum,
        expected_weight,
        out=np.zeros_like(expected_sum, dtype=np.float32),
        where=expected_weight > 0,
    )

    assert timing["timing_model"] == "native_chunked_batch_warp_scatter_one_sync"
    assert timing["frame_count"] == 2
    assert timing["interpolation"] == "lanczos3"
    assert timing["inverse_upload_mode"] == "chunked_device_batch"
    assert timing["batch_chunk_frames"] >= 1
    assert timing["batch_chunk_count"] == 1
    assert timing["batch_workspace_bytes"] >= timing["batch_output_bytes"]
    assert timing["batch_output_bytes"] >= 2 * data0.size * 4
    assert timing["batch_coverage_bytes"] >= 2 * data0.size
    assert timing["index_upload_s"] >= 0.0
    assert timing["inverse_prepare_s"] >= 0.0
    assert timing["inverse_batch_alloc_s"] >= 0.0
    assert timing["inverse_batch_bytes"] == 2 * 9 * 4
    assert timing["inverse_upload_s"] >= 0.0
    assert timing["kernel_enqueue_s"] >= 0.0
    assert timing["coverage_reduce_enqueue_s"] >= 0.0
    assert timing["scatter_enqueue_s"] >= 0.0
    assert timing["warp_kernel_launches"] == 1
    assert timing["coverage_reduce_kernel_launches"] == 1
    assert timing["scatter_kernel_launches"] == 1
    assert timing["device_copy_enqueue_s"] >= 0.0
    assert timing["sync_s"] >= 0.0
    assert timing["total_s"] >= timing["kernel_enqueue_s"]
    assert np.allclose(warped, expected, atol=3.0e-5)
    assert np.array_equal(weight_map, expected_weight)


def test_resident_stack_matrix_lanczos3_batch_respects_max_chunk_capacity():
    module = cuda_module_or_skip()
    if not hasattr(module.ResidentCalibratedStack, "apply_matrix_lanczos3_frames"):
        raise AssertionError("ResidentCalibratedStack.apply_matrix_lanczos3_frames is missing")

    yy, xx = np.indices((10, 11), dtype=np.float32)
    frames = [
        (np.sin(xx * (0.11 + index * 0.01)) + np.cos(yy * 0.13) + index).astype(
            np.float32
        )
        for index in range(5)
    ]
    matrices = np.asarray(
        [
            [[1.0, 0.0, 0.04 * index], [0.0, 1.0, -0.03 * index], [0.0, 0.0, 1.0]]
            for index in range(5)
        ],
        dtype=np.float32,
    )
    stack = module.ResidentCalibratedStack(len(frames), frames[0].shape[0], frames[0].shape[1])
    for index, frame in enumerate(frames):
        stack.upload_calibrated_frame(index, frame)

    timing = stack.apply_matrix_lanczos3_frames(
        list(range(len(frames))),
        matrices,
        np.nan,
        0.30,
        dispatch="chunked",
        max_chunk_capacity_frames=2,
    )
    warped, weight_map = stack.integrate_mean()
    expected_sum = np.zeros_like(frames[0], dtype=np.float32)
    expected_weight = np.zeros_like(frames[0], dtype=np.float32)
    for frame, matrix in zip(frames, matrices, strict=True):
        warped_frame, coverage = _warp_matrix_lanczos3_cpu(frame, matrix, np.nan, 0.30)
        expected_sum += np.where(coverage > 0, warped_frame, 0.0)
        expected_weight += coverage
    expected = np.divide(
        expected_sum,
        expected_weight,
        out=np.zeros_like(expected_sum, dtype=np.float32),
        where=expected_weight > 0,
    )

    assert timing["timing_model"] == "native_chunked_batch_warp_scatter_one_sync"
    assert timing["batch_capacity_source"] == "explicit_max_chunk_capacity"
    assert timing["batch_max_chunk_capacity_frames"] == 2
    assert timing["batch_chunk_frames"] == 2
    assert timing["batch_chunk_count"] == 3
    assert timing["chunk_metadata_upload_mode"] == "single_device_batch_reused_by_chunks"
    assert timing["index_upload_count"] == 1
    assert timing["inverse_upload_count"] == 1
    assert timing["inverse_batch_bytes"] == len(frames) * 9 * 4
    assert timing["warp_kernel_launches"] == 3
    assert timing["coverage_reduce_kernel_launches"] == 3
    assert timing["scatter_kernel_launches"] == 3
    assert timing["batch_output_bytes"] == 2 * frames[0].size * 4
    assert timing["batch_coverage_bytes"] == 2 * frames[0].size
    assert timing["batch_workspace_bytes"] == (
        timing["batch_output_bytes"]
        + timing["batch_coverage_bytes"]
        + len(frames) * 9 * 4
        + len(frames) * 8
    )
    assert np.allclose(warped, expected, atol=3.0e-5)
    assert np.array_equal(weight_map, expected_weight)


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
