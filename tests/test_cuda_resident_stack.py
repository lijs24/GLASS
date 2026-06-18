from __future__ import annotations

from dataclasses import asdict

import numpy as np

from glass.cpu.calibration import calibrate_light
from glass.cpu.integration import weighted_integrate_stack
from glass.cpu.warp import warp_translation
from glass.engine.resident_cuda import _output_diagnostics
from glass.models import CalibrationPolicy
from tests.conftest import cuda_module_or_skip


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


def _resident_star_field() -> np.ndarray:
    image = np.zeros((96, 112), dtype=np.float32)
    yy, xx = np.indices(image.shape, dtype=np.float32)
    for x, y, flux in [
        (12, 17, 100.0),
        (30, 42, 220.0),
        (71, 15, 160.0),
        (88, 63, 180.0),
        (45, 79, 250.0),
        (19, 86, 130.0),
        (101, 33, 145.0),
    ]:
        image += flux * np.exp(-(((xx - x) ** 2 + (yy - y) ** 2) / (2.0 * 1.4**2)))
    image += 10.0 + 0.01 * xx + 0.02 * yy
    return image.astype(np.float32)


def test_resident_output_diagnostics_reports_range_and_clipping():
    data = np.array([[-1.0, 0.0, 0.5], [1.5, 70000.0, np.nan]], dtype=np.float32)
    weight = np.array([[1, 1, 1], [1, 1, 0]], dtype=np.float32)

    diagnostics = _output_diagnostics(data, weight)

    assert diagnostics["total_pixels"] == 6
    assert diagnostics["finite_pixels"] == 5
    assert diagnostics["nonfinite_pixels"] == 1
    assert diagnostics["statistics"]["min"] == -1.0
    assert diagnostics["statistics"]["max"] == 70000.0
    assert diagnostics["normalization_probe"]["method"] == "diagnostic_only_p0_1_to_p99_9"
    assert diagnostics["clipping_probe"]["lt_0_count"] == 1
    assert diagnostics["clipping_probe"]["gt_1_count"] == 2
    assert diagnostics["clipping_probe"]["gt_65535_count"] == 1
    assert diagnostics["clipping_probe"]["zero_weight_pixels"] == 1


def test_resident_stack_calibrates_and_integrates_like_cpu():
    module = cuda_module_or_skip()
    if not hasattr(module, "ResidentCalibratedStack"):
        raise AssertionError("ResidentCalibratedStack is missing from glass_cuda")

    lights = [
        np.full((4, 5), 1000 + index * 10, dtype=np.float32)
        for index in range(3)
    ]
    bias = np.full((4, 5), 100, dtype=np.float32)
    dark = np.full((4, 5), 120, dtype=np.float32)
    flat = np.full((4, 5), 2, dtype=np.float32)
    policy = CalibrationPolicy(master_dark_includes_bias=True, dark_scaling_enabled=False)

    stack = module.ResidentCalibratedStack(len(lights), 4, 5)
    stack.set_calibration_masters(bias=bias, dark=dark, flat=flat)
    for index, light in enumerate(lights):
        stack.calibrate_frame(index, light, 60.0, 60.0, asdict(policy))

    cpu_frames = [
        calibrate_light(light, bias, dark, flat, 60.0, 60.0, policy)
        for light in lights
    ]
    cpu_master = np.mean(np.stack(cpu_frames, axis=0), axis=0).astype(np.float32)
    master, weight_map = stack.integrate_mean()

    assert stack.loaded_count == len(lights)
    assert stack.bytes_allocated >= len(lights) * 4 * 5 * 4
    assert np.allclose(master, cpu_master, rtol=1e-5, atol=1e-5)
    assert np.allclose(weight_map, np.full((4, 5), len(lights), dtype=np.float32))


def test_resident_stack_tile_local_mean_matches_cpu_reference():
    module = cuda_module_or_skip()
    if not hasattr(module, "ResidentCalibratedStack"):
        raise AssertionError("ResidentCalibratedStack is missing from glass_cuda")

    yy, xx = np.indices((5, 6), dtype=np.float32)
    frames = [
        (10.0 + xx).astype(np.float32),
        (20.0 + yy * 2.0).astype(np.float32),
        (30.0 + xx * 0.25 + yy * 0.5).astype(np.float32),
    ]
    frames[1][2, 3] = np.nan
    weights = np.array([1.0, 1.0, 0.5], dtype=np.float32)
    target_mask = np.array([0, 1, 0], dtype=np.uint8)
    tile_extents = np.array([[1, 1, 5, 4]], dtype=np.int32)
    tile_multipliers = np.array([2.0], dtype=np.float32)

    stack = module.ResidentCalibratedStack(len(frames), 5, 6)
    for index, frame in enumerate(frames):
        stack.upload_calibrated_frame(index, frame)

    master, weight_map, timing = stack.integrate_tile_local_mean(
        target_mask,
        tile_extents,
        tile_multipliers,
        weights,
    )

    expected_sum = np.zeros((5, 6), dtype=np.float32)
    expected_weight = np.zeros((5, 6), dtype=np.float32)
    for frame_index, frame in enumerate(frames):
        effective = np.full((5, 6), weights[frame_index], dtype=np.float32)
        if target_mask[frame_index]:
            effective[1:4, 1:5] *= tile_multipliers[0]
        valid = np.isfinite(frame) & np.isfinite(effective) & (effective > 0.0)
        expected_sum[valid] += frame[valid] * effective[valid]
        expected_weight[valid] += effective[valid]
    expected_master = np.zeros((5, 6), dtype=np.float32)
    valid_weight = expected_weight > 0.0
    expected_master[valid_weight] = expected_sum[valid_weight] / expected_weight[valid_weight]
    unweighted_master, unweighted_weight = stack.integrate_mean(weights)

    assert timing["timing_model"] == "native_resident_tile_local_weighted_mean_one_sync"
    assert timing["rejection"] == "none"
    assert timing["modifies_resident_stack"] is False
    assert timing["target_frame_count"] == 1
    assert timing["tile_count"] == 1
    assert np.allclose(master, expected_master, rtol=1e-6, atol=1e-6)
    assert np.allclose(weight_map, expected_weight, rtol=1e-6, atol=1e-6)
    assert not np.allclose(master[1:4, 1:5], unweighted_master[1:4, 1:5])
    assert np.allclose(weight_map[0, 0], unweighted_weight[0, 0], rtol=1e-6, atol=1e-6)


def _expected_tile_local_sigma(
    frames: list[np.ndarray],
    weights: np.ndarray,
    target_mask: np.ndarray,
    tile_extents: np.ndarray,
    tile_multipliers: np.ndarray,
    low_sigma: float,
    high_sigma: float,
    winsorize: bool,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    height, width = frames[0].shape
    master = np.zeros((height, width), dtype=np.float32)
    weight_map = np.zeros((height, width), dtype=np.float32)
    coverage = np.zeros((height, width), dtype=np.float32)
    low_reject = np.zeros((height, width), dtype=np.float32)
    high_reject = np.zeros((height, width), dtype=np.float32)
    stack = np.stack(frames, axis=0).astype(np.float32)
    for y in range(height):
        for x in range(width):
            tile_multiplier = 1.0
            for tile, extent in enumerate(tile_extents):
                x0, y0, x1, y1 = [int(value) for value in extent]
                if x0 <= x < x1 and y0 <= y < y1:
                    tile_multiplier = float(tile_multipliers[tile])
                    break
            effective_weights = weights.astype(np.float32).copy()
            effective_weights[target_mask.astype(bool)] *= np.float32(tile_multiplier)
            values = stack[:, y, x]
            valid = np.isfinite(values) & np.isfinite(effective_weights) & (effective_weights > 0.0)
            if not np.any(valid):
                continue
            valid_values = values[valid]
            mean = np.float32(np.mean(valid_values, dtype=np.float32))
            std = np.float32(np.sqrt(np.mean((valid_values - mean) ** 2, dtype=np.float32)))
            low_threshold = np.float32(mean - low_sigma * std)
            high_threshold = np.float32(mean + high_sigma * std)
            if winsorize:
                clipped = np.clip(valid_values, low_threshold, high_threshold).astype(np.float32)
                center = np.float32(np.mean(clipped, dtype=np.float32))
                scale = np.float32(np.sqrt(np.mean((clipped - center) ** 2, dtype=np.float32)))
                low_threshold = np.float32(center - low_sigma * scale)
                high_threshold = np.float32(center + high_sigma * scale)
            accepted_sum = np.float32(0.0)
            accepted_weight = np.float32(0.0)
            for value, weight in zip(values, effective_weights, strict=True):
                if not np.isfinite(value) or not np.isfinite(weight) or weight <= 0.0:
                    continue
                if value < low_threshold:
                    low_reject[y, x] += 1.0
                    continue
                if value > high_threshold:
                    high_reject[y, x] += 1.0
                    continue
                accepted_sum += np.float32(value * weight)
                accepted_weight += np.float32(weight)
                coverage[y, x] += 1.0
            weight_map[y, x] = accepted_weight
            if accepted_weight > 0.0:
                master[y, x] = np.float32(accepted_sum / accepted_weight)
    return master, weight_map, coverage, low_reject, high_reject


def test_resident_stack_tile_local_sigma_clip_matches_cpu_reference():
    module = cuda_module_or_skip()
    if not hasattr(module, "ResidentCalibratedStack"):
        raise AssertionError("ResidentCalibratedStack is missing from glass_cuda")

    yy, xx = np.indices((5, 6), dtype=np.float32)
    frames = [
        (10.0 + xx * 0.1).astype(np.float32),
        (12.0 + yy * 0.2).astype(np.float32),
        (50.0 + xx * 0.05).astype(np.float32),
    ]
    frames[2][0, 0] = 11.0
    frames[1][2, 3] = np.nan
    weights = np.array([1.0, 1.0, 0.5], dtype=np.float32)
    target_mask = np.array([0, 1, 0], dtype=np.uint8)
    tile_extents = np.array([[1, 1, 5, 4]], dtype=np.int32)
    tile_multipliers = np.array([2.0], dtype=np.float32)

    stack = module.ResidentCalibratedStack(len(frames), 5, 6)
    for index, frame in enumerate(frames):
        stack.upload_calibrated_frame(index, frame)

    result = stack.integrate_tile_local_sigma_clip(
        target_mask,
        tile_extents,
        tile_multipliers,
        weights,
        low_sigma=3.0,
        high_sigma=1.0,
        winsorize=True,
    )
    master, weight_map, coverage, low_reject, high_reject, timing = result
    expected = _expected_tile_local_sigma(
        frames,
        weights,
        target_mask,
        tile_extents,
        tile_multipliers,
        low_sigma=3.0,
        high_sigma=1.0,
        winsorize=True,
    )

    assert timing["timing_model"] == "native_resident_tile_local_sigma_clip_one_sync"
    assert timing["rejection"] == "winsorized_sigma"
    assert timing["target_frame_count"] == 1
    assert timing["tile_count"] == 1
    assert timing["modifies_resident_stack"] is False
    for actual, expected_map in zip(
        (master, weight_map, coverage, low_reject, high_reject),
        expected,
        strict=True,
    ):
        assert np.allclose(actual, expected_map, rtol=2e-5, atol=2e-5)


def _matrix_translation(dx: float, dy: float) -> np.ndarray:
    return np.array(
        [[1.0, 0.0, dx], [0.0, 1.0, dy], [0.0, 0.0, 1.0]],
        dtype=np.float32,
    )


def _expected_matrix_warped_mean(
    module: object,
    frames: list[np.ndarray],
    matrices: np.ndarray,
    weights: np.ndarray,
    interpolation: str,
    clamping_threshold: float = -1.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    height, width = frames[0].shape
    sums = np.zeros((height, width), dtype=np.float32)
    weight_map = np.zeros((height, width), dtype=np.float32)
    coverage = np.zeros((height, width), dtype=np.float32)
    geometric = np.zeros((height, width), dtype=np.float32)
    for frame, matrix, weight in zip(frames, matrices, weights, strict=True):
        if weight <= 0.0 or not np.isfinite(weight):
            continue
        if interpolation == "lanczos3":
            warped, footprint = module.warp_matrix_lanczos3_f32(
                frame,
                matrix,
                np.nan,
                clamping_threshold,
            )
        else:
            warped, footprint = module.warp_matrix_bilinear_f32(frame, matrix, np.nan)
        finite = np.isfinite(warped)
        geometric += (footprint > 0.5).astype(np.float32)
        coverage += finite.astype(np.float32)
        sums[finite] += warped[finite] * weight
        weight_map[finite] += weight
    master = np.zeros((height, width), dtype=np.float32)
    valid = weight_map > 0.0
    master[valid] = sums[valid] / weight_map[valid]
    return master, weight_map, coverage, geometric


def test_resident_stack_fused_matrix_warped_mean_bilinear_matches_warp_then_integrate():
    module = cuda_module_or_skip()
    if not hasattr(module, "ResidentCalibratedStack"):
        raise AssertionError("ResidentCalibratedStack is missing from glass_cuda")

    yy, xx = np.indices((12, 14), dtype=np.float32)
    frames = [
        (10.0 + xx + yy * 0.25).astype(np.float32),
        (20.0 + xx * 0.5 + yy).astype(np.float32),
        (30.0 + xx * 0.1 - yy * 0.2).astype(np.float32),
    ]
    frames[1][3, 4] = np.nan
    matrices = np.stack(
        [
            _matrix_translation(0.0, 0.0),
            _matrix_translation(1.25, -0.5),
            _matrix_translation(-2.0, 1.0),
        ],
        axis=0,
    )
    weights = np.array([1.0, 0.5, 0.0], dtype=np.float32)

    stack = module.ResidentCalibratedStack(len(frames), 12, 14)
    for index, frame in enumerate(frames):
        stack.upload_calibrated_frame(index, frame)

    master, weight_map, coverage, geometric, timing = stack.integrate_matrix_warped_mean(
        matrices,
        weights,
        interpolation="bilinear",
    )
    expected_master, expected_weight, expected_coverage, expected_geometric = _expected_matrix_warped_mean(
        module,
        frames,
        matrices,
        weights,
        "bilinear",
    )
    unwarped_master, _ = stack.integrate_mean(weights)

    assert timing["timing_model"] == "native_fused_matrix_warp_weighted_mean_one_sync"
    assert timing["interpolation"] == "bilinear"
    assert timing["rejection"] == "none"
    assert timing["avoids_stack_scatter"] is True
    assert timing["modifies_resident_stack"] is False
    assert timing["frame_count"] == len(frames)
    assert timing["output_bytes"] == 12 * 14 * 4 * 4
    assert np.allclose(master, expected_master, rtol=2e-5, atol=2e-5)
    assert np.allclose(weight_map, expected_weight, rtol=1e-6, atol=1e-6)
    assert np.allclose(coverage, expected_coverage, rtol=1e-6, atol=1e-6)
    assert np.allclose(geometric, expected_geometric, rtol=1e-6, atol=1e-6)
    assert not np.allclose(master, unwarped_master)


def test_resident_stack_fused_matrix_warped_mean_lanczos3_matches_warp_then_integrate():
    module = cuda_module_or_skip()
    if not hasattr(module, "ResidentCalibratedStack"):
        raise AssertionError("ResidentCalibratedStack is missing from glass_cuda")

    yy, xx = np.indices((20, 22), dtype=np.float32)
    frames = [
        (100.0 + np.sin(xx * 0.2) * 5.0 + yy * 0.3).astype(np.float32),
        (90.0 + np.cos(yy * 0.25) * 3.0 + xx * 0.2).astype(np.float32),
        (80.0 + xx * 0.4 - yy * 0.1).astype(np.float32),
    ]
    matrices = np.stack(
        [
            _matrix_translation(0.0, 0.0),
            _matrix_translation(0.4, -0.3),
            _matrix_translation(-0.75, 0.6),
        ],
        axis=0,
    )
    weights = np.array([1.0, 0.75, 0.25], dtype=np.float32)

    stack = module.ResidentCalibratedStack(len(frames), 20, 22)
    for index, frame in enumerate(frames):
        stack.upload_calibrated_frame(index, frame)

    master, weight_map, coverage, geometric, timing = stack.integrate_matrix_warped_mean(
        matrices,
        weights,
        interpolation="lanczos3",
        clamping_threshold=0.3,
    )
    expected_master, expected_weight, expected_coverage, expected_geometric = _expected_matrix_warped_mean(
        module,
        frames,
        matrices,
        weights,
        "lanczos3",
        clamping_threshold=0.3,
    )

    assert timing["interpolation"] == "lanczos3"
    assert timing["inverse_batch_bytes"] == len(frames) * 9 * 4
    assert timing["weights_bytes"] == len(frames) * 4
    assert np.allclose(master, expected_master, rtol=2e-5, atol=2e-5)
    assert np.allclose(weight_map, expected_weight, rtol=1e-6, atol=1e-6)
    assert np.allclose(coverage, expected_coverage, rtol=1e-6, atol=1e-6)
    assert np.allclose(geometric, expected_geometric, rtol=1e-6, atol=1e-6)


def test_resident_stack_pinned_async_calibration_matches_pageable_and_cpu():
    module = cuda_module_or_skip()
    if not hasattr(module, "ResidentCalibratedStack"):
        raise AssertionError("ResidentCalibratedStack is missing from glass_cuda")

    light = np.arange(20, dtype=np.float32).reshape(4, 5) + 1000.0
    bias = np.full((4, 5), 100, dtype=np.float32)
    dark = np.full((4, 5), 120, dtype=np.float32)
    flat = np.full((4, 5), 2, dtype=np.float32)
    policy = CalibrationPolicy(master_dark_includes_bias=True, dark_scaling_enabled=False)

    pageable = module.ResidentCalibratedStack(1, 4, 5)
    pageable.set_calibration_masters(bias=bias, dark=dark, flat=flat)
    pageable_timing = pageable.calibrate_frame_timed(0, light, 60.0, 60.0, asdict(policy))
    pageable_master, _ = pageable.integrate_mean()

    pinned = module.ResidentCalibratedStack(1, 4, 5)
    pinned.set_calibration_masters(bias=bias, dark=dark, flat=flat)
    pinned_timing = pinned.calibrate_frame_pinned_async_timed(0, light, 60.0, 60.0, asdict(policy))
    pinned_master, pinned_weight = pinned.integrate_mean()

    expected = calibrate_light(light, bias, dark, flat, 60.0, 60.0, policy)
    assert pageable_timing["h2d_mode"] == "pageable"
    assert pageable_timing["event_mode"] == "none"
    assert pinned_timing["h2d_mode"] == "pinned_async"
    assert pinned_timing["event_mode"] == "reused_stack_events"
    assert pinned_timing["host_pinned_bytes"] >= light.nbytes
    assert pinned_timing["h2d_s"] >= 0.0
    assert pinned_timing["calibrate_store_s"] >= 0.0
    assert np.allclose(pageable_master, expected, rtol=1e-5, atol=1e-5)
    assert np.allclose(pinned_master, expected, rtol=1e-5, atol=1e-5)
    assert np.allclose(pinned_master, pageable_master, rtol=1e-5, atol=1e-5)
    assert np.allclose(pinned_weight, np.ones((4, 5), dtype=np.float32))


def test_resident_stack_host_async_calibration_accepts_pinned_host_array():
    module = cuda_module_or_skip()
    if not hasattr(module, "ResidentCalibratedStack"):
        raise AssertionError("ResidentCalibratedStack is missing from glass_cuda")

    pinned_light = module.host_pinned_empty_f32(4, 5)
    pinned_light[...] = np.arange(20, dtype=np.float32).reshape(4, 5) + 1000.0
    bias = np.full((4, 5), 100, dtype=np.float32)
    dark = np.full((4, 5), 120, dtype=np.float32)
    flat = np.full((4, 5), 2, dtype=np.float32)
    policy = CalibrationPolicy(master_dark_includes_bias=True, dark_scaling_enabled=False)

    stack = module.ResidentCalibratedStack(1, 4, 5)
    stack.set_calibration_masters(bias=bias, dark=dark, flat=flat)
    timing = stack.calibrate_frame_host_async_timed(0, pinned_light, 60.0, 60.0, asdict(policy))
    master, weight = stack.integrate_mean()

    expected = calibrate_light(pinned_light, bias, dark, flat, 60.0, 60.0, policy)
    assert pinned_light.flags.c_contiguous
    assert timing["h2d_mode"] == "host_async"
    assert timing["event_mode"] == "reused_stack_events"
    assert timing["host_copy_s"] == 0.0
    assert timing["h2d_s"] >= 0.0
    assert timing["calibrate_store_s"] >= 0.0
    assert np.allclose(master, expected, rtol=1e-5, atol=1e-5)
    assert np.allclose(weight, np.ones((4, 5), dtype=np.float32))


def test_resident_stack_host_async_batch_calibration_matches_cpu():
    module = cuda_module_or_skip()
    if not hasattr(module.ResidentCalibratedStack, "calibrate_frames_host_async_timed"):
        raise AssertionError("ResidentCalibratedStack.calibrate_frames_host_async_timed is missing")

    light0 = module.host_pinned_empty_f32(4, 5)
    light1 = module.host_pinned_empty_f32(4, 5)
    light0[...] = np.arange(20, dtype=np.float32).reshape(4, 5) + 1000.0
    light1[...] = np.flipud(np.asarray(light0)) + 12.0
    bias = np.full((4, 5), 100, dtype=np.float32)
    dark = np.full((4, 5), 120, dtype=np.float32)
    flat = np.full((4, 5), 2, dtype=np.float32)
    policy = CalibrationPolicy(master_dark_includes_bias=True, dark_scaling_enabled=False)

    stack = module.ResidentCalibratedStack(2, 4, 5)
    stack.set_calibration_masters(bias=bias, dark=dark, flat=flat)
    timing = stack.calibrate_frames_host_async_timed(
        [0, 1],
        [light0, light1],
        [60.0, 60.0],
        [60.0, 60.0],
        asdict(policy),
    )
    master, weight = stack.integrate_mean()

    expected0 = calibrate_light(light0, bias, dark, flat, 60.0, 60.0, policy)
    expected1 = calibrate_light(light1, bias, dark, flat, 60.0, 60.0, policy)
    expected = np.mean(np.stack([expected0, expected1], axis=0), axis=0)
    assert timing["h2d_mode"] == "host_async_batch"
    assert timing["event_mode"] == "reused_stack_events"
    assert timing["timing_model"] == "single_stream_sequential_h2d_kernel_one_sync"
    assert timing["frame_count"] == 2
    assert timing["stream_h2d_calibrate_store_s"] >= 0.0
    assert timing["sync_s"] >= 0.0
    assert timing["total_s"] >= timing["sync_s"]
    assert np.allclose(master, expected, rtol=1e-5, atol=1e-5)
    assert np.allclose(weight, np.full((4, 5), 2.0, dtype=np.float32))


def test_resident_stack_host_async_multistream_batch_calibration_matches_cpu():
    module = cuda_module_or_skip()
    if not hasattr(module.ResidentCalibratedStack, "calibrate_frames_host_async_multistream_timed"):
        raise AssertionError("ResidentCalibratedStack.calibrate_frames_host_async_multistream_timed is missing")

    lights = []
    for offset in (1000.0, 1010.0, 1020.0):
        light = module.host_pinned_empty_f32(4, 5)
        light[...] = np.arange(20, dtype=np.float32).reshape(4, 5) + offset
        lights.append(light)
    bias = np.full((4, 5), 100, dtype=np.float32)
    dark = np.full((4, 5), 120, dtype=np.float32)
    flat = np.full((4, 5), 2, dtype=np.float32)
    policy = CalibrationPolicy(master_dark_includes_bias=True, dark_scaling_enabled=False)

    stack = module.ResidentCalibratedStack(3, 4, 5)
    stack.set_calibration_masters(bias=bias, dark=dark, flat=flat)
    timing = stack.calibrate_frames_host_async_multistream_timed(
        [0, 1, 2],
        lights,
        [60.0, 60.0, 60.0],
        [60.0, 60.0, 60.0],
        2,
        asdict(policy),
    )
    master, weight = stack.integrate_mean()

    expected_frames = [calibrate_light(light, bias, dark, flat, 60.0, 60.0, policy) for light in lights]
    expected = np.mean(np.stack(expected_frames, axis=0), axis=0)
    assert timing["h2d_mode"] == "host_async_multistream_batch"
    assert timing["event_mode"] == "reused_stack_lane_events"
    assert timing["timing_model"] == "multi_stream_lanes_one_sync"
    assert timing["requested_stream_count"] == 2
    assert timing["stream_count"] == 2
    assert timing["frame_count"] == 3
    assert timing["calibration_lane_buffer_bytes"] >= 2 * 4 * 5 * 4
    assert len(timing["lane_stream_elapsed_s"]) == 2
    assert timing["stream_h2d_calibrate_store_s"] >= 0.0
    assert timing["sync_s"] >= 0.0
    assert stack.calibration_lane_count >= 2
    assert stack.calibration_lane_buffer_bytes >= 2 * 4 * 5 * 4
    assert np.allclose(master, expected, rtol=1e-5, atol=1e-5)
    assert np.allclose(weight, np.full((4, 5), 3.0, dtype=np.float32))


def test_resident_stack_h2d_release_batch_calibration_matches_cpu():
    module = cuda_module_or_skip()
    if not hasattr(module.ResidentCalibratedStack, "calibrate_frames_host_async_multistream_h2d_release_timed"):
        raise AssertionError(
            "ResidentCalibratedStack.calibrate_frames_host_async_multistream_h2d_release_timed is missing"
        )
    if not hasattr(module.ResidentCalibratedStack, "finish_pending_calibration_timed"):
        raise AssertionError("ResidentCalibratedStack.finish_pending_calibration_timed is missing")

    lights = []
    for offset in (1000.0, 1010.0):
        light = module.host_pinned_empty_f32(4, 5)
        light[...] = np.arange(20, dtype=np.float32).reshape(4, 5) + offset
        lights.append(light)
    bias = np.full((4, 5), 100, dtype=np.float32)
    dark = np.full((4, 5), 120, dtype=np.float32)
    flat = np.full((4, 5), 2, dtype=np.float32)
    policy = CalibrationPolicy(master_dark_includes_bias=True, dark_scaling_enabled=False)

    stack = module.ResidentCalibratedStack(2, 4, 5)
    stack.set_calibration_masters(bias=bias, dark=dark, flat=flat)
    release_timing = stack.calibrate_frames_host_async_multistream_h2d_release_timed(
        [0, 1],
        lights,
        [60.0, 60.0],
        [60.0, 60.0],
        2,
        asdict(policy),
    )
    assert release_timing["h2d_mode"] == "host_async_multistream_h2d_release_batch"
    assert release_timing["event_mode"] == "reused_stack_lane_h2d_events"
    assert release_timing["timing_model"] == "multi_stream_one_frame_per_lane_h2d_release_then_wait"
    assert release_timing["host_release_safe"] is True
    assert release_timing["pending"] is True
    assert release_timing["stream_count"] == 2
    assert release_timing["frame_count"] == 2
    assert release_timing["h2d_event_sync_s"] >= 0.0
    assert release_timing["h2d_event_elapsed_s"] >= 0.0

    finish_timing = stack.finish_pending_calibration_timed()
    master, weight = stack.integrate_mean()

    expected_frames = [calibrate_light(light, bias, dark, flat, 60.0, 60.0, policy) for light in lights]
    expected = np.mean(np.stack(expected_frames, axis=0), axis=0)
    assert finish_timing["pending"] is False
    assert finish_timing["event_mode"] == "reused_stack_lane_h2d_events"
    assert finish_timing["timing_model"] == "multi_stream_one_frame_per_lane_h2d_release_then_wait"
    assert finish_timing["wait_sync_s"] >= 0.0
    assert finish_timing["stream_h2d_calibrate_store_s"] >= 0.0
    assert finish_timing["h2d_release_s"] == release_timing["h2d_release_s"]
    assert np.allclose(master, expected, rtol=1e-5, atol=1e-5)
    assert np.allclose(weight, np.full((4, 5), 2.0, dtype=np.float32))


def test_resident_stack_callback_release_queue_calibration_matches_cpu():
    module = cuda_module_or_skip()
    if not hasattr(module.ResidentCalibratedStack, "calibrate_frames_host_async_multistream_callback_release_timed"):
        raise AssertionError(
            "ResidentCalibratedStack.calibrate_frames_host_async_multistream_callback_release_timed is missing"
        )

    lights = []
    for offset in (1000.0, 1010.0, 1020.0, 1030.0):
        light = module.host_pinned_empty_f32(4, 5)
        light[...] = np.arange(20, dtype=np.float32).reshape(4, 5) + offset
        lights.append(light)
    bias = np.full((4, 5), 100, dtype=np.float32)
    dark = np.full((4, 5), 120, dtype=np.float32)
    flat = np.full((4, 5), 2, dtype=np.float32)
    policy = CalibrationPolicy(master_dark_includes_bias=True, dark_scaling_enabled=False)
    released: list[list[int]] = []

    def release_callback(indices):
        released.append([int(index) for index in indices])

    stack = module.ResidentCalibratedStack(4, 4, 5)
    stack.set_calibration_masters(bias=bias, dark=dark, flat=flat)
    timing = stack.calibrate_frames_host_async_multistream_callback_release_timed(
        [0, 1, 2, 3],
        lights,
        [60.0, 60.0, 60.0, 60.0],
        [60.0, 60.0, 60.0, 60.0],
        2,
        2,
        release_callback,
        asdict(policy),
    )
    master, weight = stack.integrate_mean()

    expected_frames = [calibrate_light(light, bias, dark, flat, 60.0, 60.0, policy) for light in lights]
    expected = np.mean(np.stack(expected_frames, axis=0), axis=0)
    assert released == [[0, 1], [2, 3]]
    assert timing["h2d_mode"] == "host_async_multistream_callback_release_batch"
    assert timing["event_mode"] == "reused_stack_lane_h2d_callback_events"
    assert timing["timing_model"] == "multi_stream_callback_release_waves_one_final_sync"
    assert timing["requested_stream_count"] == 2
    assert timing["stream_count"] == 2
    assert timing["requested_wave_frames"] == 2
    assert timing["wave_frames"] == 2
    assert timing["wave_count"] == 2
    assert timing["frame_count"] == 4
    assert timing["callback_release_count"] == 4
    assert timing["host_release_safe"] is True
    assert timing["h2d_event_sync_s"] >= 0.0
    assert timing["h2d_event_elapsed_s"] >= 0.0
    assert timing["callback_s"] >= 0.0
    assert timing["stream_h2d_calibrate_store_s"] >= 0.0
    assert timing["sync_s"] >= 0.0
    assert len(timing["lane_stream_elapsed_s"]) == 2
    assert len(timing["wave_h2d_elapsed_s"]) == 2
    assert np.allclose(master, expected, rtol=1e-5, atol=1e-5)
    assert np.allclose(weight, np.full((4, 5), 4.0, dtype=np.float32))


def test_resident_stack_weighted_mean_matches_cpu():
    module = cuda_module_or_skip()
    frames = [
        np.full((3, 3), 1, dtype=np.float32),
        np.full((3, 3), 3, dtype=np.float32),
        np.full((3, 3), 10, dtype=np.float32),
    ]
    weights = np.array([1, 2, 0.5], dtype=np.float32)

    stack = module.ResidentCalibratedStack(len(frames), 3, 3)
    for index, frame in enumerate(frames):
        stack.upload_calibrated_frame(index, frame)
    master, weight_map = stack.integrate_mean(weights)

    expected = np.average(np.stack(frames, axis=0), axis=0, weights=weights).astype(np.float32)
    assert np.allclose(master, expected, rtol=1e-5, atol=1e-5)
    assert np.allclose(weight_map, np.full((3, 3), np.sum(weights), dtype=np.float32))


def test_resident_stack_global_stats_ignore_nonfinite_pixels():
    module = cuda_module_or_skip()
    frame = np.array([[1, 2, np.nan], [4, np.inf, 6]], dtype=np.float32)
    finite = frame[np.isfinite(frame)]

    stack = module.ResidentCalibratedStack(1, 2, 3)
    stack.upload_calibrated_frame(0, frame)
    stats = stack.frame_global_stats(0)

    assert stats["model"] == "resident_global_mean_std"
    assert stats["valid_pixels"] == int(finite.size)
    assert stats["nonfinite_pixels"] == 2
    assert np.isclose(stats["mean"], float(np.mean(finite)))
    assert np.isclose(stats["std"], float(np.std(finite)))


def test_resident_stack_global_normalization_matches_reference_stats():
    module = cuda_module_or_skip()
    reference = np.array([[10, 20], [30, 40]], dtype=np.float32)
    moving = reference * np.float32(2.0) + np.float32(5.0)

    stack = module.ResidentCalibratedStack(2, 2, 2)
    stack.upload_calibrated_frame(0, reference)
    stack.upload_calibrated_frame(1, moving)
    ref_stats = stack.frame_global_stats(0)
    mov_stats = stack.frame_global_stats(1)
    scale = ref_stats["std"] / mov_stats["std"]
    offset = ref_stats["mean"] - mov_stats["mean"] * scale
    stack.apply_global_normalization_frame(1, scale, offset)
    normalized, weight_map = stack.integrate_mean(np.array([0.0, 1.0], dtype=np.float32))

    assert np.allclose(normalized, reference, rtol=1e-5, atol=1e-5)
    assert np.allclose(weight_map, np.ones_like(reference, dtype=np.float32))


def test_resident_stack_grid_normalization_matches_standalone_cuda():
    module = cuda_module_or_skip()
    if not hasattr(module.ResidentCalibratedStack, "apply_grid_normalization_frame"):
        raise AssertionError("ResidentCalibratedStack.apply_grid_normalization_frame is missing from glass_cuda")

    frame = np.arange(35, dtype=np.float32).reshape(5, 7)
    scales = np.array([[1.0, 2.0], [0.5, 1.25]], dtype=np.float32)
    offsets = np.array([[0.0, -3.0], [4.0, 10.0]], dtype=np.float32)
    expected = module.local_norm_apply_grid_f32(frame, scales, offsets, 3, 4)

    stack = module.ResidentCalibratedStack(1, frame.shape[0], frame.shape[1])
    stack.upload_calibrated_frame(0, frame)
    stack.apply_grid_normalization_frame(0, scales, offsets, 3, 4)
    normalized, weight_map = stack.integrate_mean()

    assert np.allclose(normalized, expected, rtol=1e-5, atol=1e-5)
    assert np.allclose(weight_map, np.ones_like(frame, dtype=np.float32))


def test_resident_stack_grid_stats_can_drive_in_vram_normalization():
    module = cuda_module_or_skip()
    if not hasattr(module.ResidentCalibratedStack, "frame_pair_grid_stats"):
        raise AssertionError("ResidentCalibratedStack.frame_pair_grid_stats is missing from glass_cuda")

    reference = np.arange(16, dtype=np.float32).reshape(4, 4) + np.float32(10.0)
    scales_true = np.array([[2.0, 0.5], [1.5, 3.0]], dtype=np.float32)
    offsets_true = np.array([[5.0, -2.0], [8.0, 1.0]], dtype=np.float32)
    moving = np.empty_like(reference)
    for row in range(2):
        for col in range(2):
            y0 = row * 2
            x0 = col * 2
            moving[y0 : y0 + 2, x0 : x0 + 2] = (
                reference[y0 : y0 + 2, x0 : x0 + 2] * scales_true[row, col] + offsets_true[row, col]
            )

    stack = module.ResidentCalibratedStack(2, 4, 4)
    stack.upload_calibrated_frame(0, reference)
    stack.upload_calibrated_frame(1, moving)
    stats = stack.frame_pair_grid_stats(0, 1, 2, 2)

    assert stats["model"] == "resident_grid_pair_mean_std"
    assert stats["grid_rows"] == 2
    assert stats["grid_cols"] == 2
    assert np.all(stats["valid_pixels"] == 4)

    normalization_scales = stats["reference_std"] / stats["source_std"]
    normalization_offsets = stats["reference_mean"] - stats["source_mean"] * normalization_scales
    stack.apply_grid_normalization_frame(1, normalization_scales, normalization_offsets, 2, 2)
    normalized, weight_map = stack.integrate_mean(np.array([0.0, 1.0], dtype=np.float32))

    assert np.allclose(normalized, reference, rtol=1e-5, atol=1e-5)
    assert np.allclose(weight_map, np.ones_like(reference, dtype=np.float32))


def test_resident_stack_translation_warp_uses_nan_coverage():
    module = cuda_module_or_skip()
    if not hasattr(module.ResidentCalibratedStack, "apply_translation_frame"):
        raise AssertionError("ResidentCalibratedStack.apply_translation_frame is missing from glass_cuda")

    frame = np.arange(20, dtype=np.float32).reshape(4, 5)
    stack = module.ResidentCalibratedStack(1, 4, 5)
    stack.upload_calibrated_frame(0, frame)
    stack.apply_translation_frame(0, 1, -1, np.nan)
    master, weight_map = stack.integrate_mean()

    expected = warp_translation(frame, 1, -1, fill=np.nan)
    valid = np.isfinite(expected)
    assert np.allclose(master[valid], expected[valid], rtol=1e-5, atol=1e-5)
    assert np.all(master[~valid] == 0.0)
    assert np.allclose(weight_map, valid.astype(np.float32))


def test_resident_stack_accumulates_geometric_warp_coverage():
    module = cuda_module_or_skip()
    required = [
        "reset_warp_coverage",
        "accumulate_full_warp_coverage_frame",
        "warp_coverage_map",
        "apply_translation_frame",
    ]
    missing = [name for name in required if not hasattr(module.ResidentCalibratedStack, name)]
    if missing:
        raise AssertionError(f"ResidentCalibratedStack is missing {missing}")

    frame = np.arange(20, dtype=np.float32).reshape(4, 5)
    stack = module.ResidentCalibratedStack(2, 4, 5)
    stack.upload_calibrated_frame(0, frame)
    stack.upload_calibrated_frame(1, frame)

    stack.reset_warp_coverage()
    stack.accumulate_full_warp_coverage_frame()
    stack.apply_translation_frame(1, 1, 0, np.nan)
    coverage = stack.warp_coverage_map()

    expected = np.full_like(frame, 2.0, dtype=np.float32)
    expected[:, 0] = 1.0
    assert stack.warp_coverage_frame_count == 2
    assert np.allclose(coverage, expected)


def test_resident_stack_reuses_warp_scratch_buffers():
    module = cuda_module_or_skip()
    required = [
        "apply_translation_frame",
        "apply_matrix_bilinear_frame",
        "warp_scratch_bytes",
        "warp_copy_mode",
    ]
    missing = [name for name in required if not hasattr(module.ResidentCalibratedStack, name)]
    if missing:
        raise AssertionError(f"ResidentCalibratedStack is missing {missing}")

    frame = np.arange(30, dtype=np.float32).reshape(5, 6)
    stack = module.ResidentCalibratedStack(2, 5, 6)
    stack.upload_calibrated_frame(0, frame)
    stack.upload_calibrated_frame(1, frame)

    assert stack.warp_copy_mode == "default_stream_async_device_to_device"
    assert stack.warp_scratch_bytes == 0
    before = stack.bytes_allocated
    stack.apply_translation_frame(0, 1, 0, np.nan)
    translation_scratch = stack.warp_scratch_bytes
    after_translation = stack.bytes_allocated

    assert translation_scratch == 2 * frame.nbytes
    assert after_translation == before + translation_scratch + frame.nbytes
    stack.apply_translation_frame(1, -1, 0, np.nan)
    assert stack.warp_scratch_bytes == translation_scratch
    assert stack.bytes_allocated == after_translation

    matrix = [[1.0, 0.0, 0.0], [0.0, 1.0, 1.0], [0.0, 0.0, 1.0]]
    stack.apply_matrix_bilinear_frame(1, matrix, np.nan)
    matrix_scratch = stack.warp_scratch_bytes

    assert matrix_scratch == translation_scratch + 9 * np.dtype(np.float32).itemsize
    assert stack.bytes_allocated == after_translation + 9 * np.dtype(np.float32).itemsize
    stack.apply_matrix_bilinear_frame(0, matrix, np.nan)
    assert stack.warp_scratch_bytes == matrix_scratch
    assert stack.bytes_allocated == after_translation + 9 * np.dtype(np.float32).itemsize


def test_resident_stack_grid_star_catalog_batch_reports_native_timing():
    module = cuda_module_or_skip()
    if not hasattr(module.ResidentCalibratedStack, "star_grid_top_nms_candidates_batch"):
        raise AssertionError("ResidentCalibratedStack.star_grid_top_nms_candidates_batch is missing")

    reference = _resident_star_field()
    frames = [
        reference,
        _shift_image(reference, 4, -3),
        _shift_image(reference, -2, 5),
    ]
    stack = module.ResidentCalibratedStack(len(frames), reference.shape[0], reference.shape[1])
    for index, frame in enumerate(frames):
        stack.upload_calibrated_frame(index, frame)

    batch = stack.star_grid_top_nms_candidates_batch([0, 1, 2], 30.0, 4, 4, 2, 8, 4.0)
    repeat_batch = stack.star_grid_top_nms_candidates_batch([0, 1, 2], 30.0, 4, 4, 2, 8, 4.0)
    singles = [
        stack.star_grid_top_nms_candidates(index, 30.0, 4, 4, 2, 8, 4.0)
        for index in [0, 1, 2]
    ]

    assert [item["frame_index"] for item in batch] == [0, 1, 2]
    for batch_item, repeat_item, single_item in zip(batch, repeat_batch, singles, strict=True):
        assert batch_item["catalog_timing_model"] == "per_frame_launch_sync_download"
        assert batch_item["catalog_sort_mode"] == "shared_bitonic_power2"
        assert batch_item["catalog_topk_mode"] == "strict_flux_precheck_per_cell_lock"
        assert batch_item["catalog_native_s"] >= 0.0
        assert batch_item["catalog_sync_s"] >= 0.0
        assert batch_item["catalog_output_download_s"] >= 0.0
        assert batch_item["count"] == repeat_item["count"]
        assert batch_item["stored_count"] == repeat_item["stored_count"]
        assert np.array_equal(batch_item["x"], repeat_item["x"])
        assert np.array_equal(batch_item["y"], repeat_item["y"])
        assert np.array_equal(batch_item["flux"], repeat_item["flux"])
        assert batch_item["count"] == single_item["count"]
        assert batch_item["stored_count"] == single_item["stored_count"]
        assert batch_item["catalog_sort_mode"] == single_item["catalog_sort_mode"]
        assert batch_item["catalog_topk_mode"] == single_item["catalog_topk_mode"]
        assert np.allclose(batch_item["x"], single_item["x"])
        assert np.allclose(batch_item["y"], single_item["y"])
        assert np.allclose(batch_item["flux"], single_item["flux"])

    deterministic_batch = stack.star_grid_top_nms_candidates_batch(
        [0, 1, 2],
        30.0,
        4,
        4,
        2,
        8,
        4.0,
        deterministic=True,
    )
    deterministic_repeat = stack.star_grid_top_nms_candidates_batch(
        [0, 1, 2],
        30.0,
        4,
        4,
        2,
        8,
        4.0,
        deterministic=True,
    )
    deterministic_singles = [
        stack.star_grid_top_nms_candidates(index, 30.0, 4, 4, 2, 8, 4.0, deterministic=True)
        for index in [0, 1, 2]
    ]
    for batch_item, repeat_item, single_item in zip(
        deterministic_batch,
        deterministic_repeat,
        deterministic_singles,
        strict=True,
    ):
        assert batch_item["catalog_topk_mode"] == "deterministic_parallel_per_cell"
        assert batch_item["count"] == repeat_item["count"]
        assert batch_item["stored_count"] == repeat_item["stored_count"]
        assert np.array_equal(batch_item["x"], repeat_item["x"])
        assert np.array_equal(batch_item["y"], repeat_item["y"])
        assert np.array_equal(batch_item["flux"], repeat_item["flux"])
        assert batch_item["count"] == single_item["count"]
        assert batch_item["stored_count"] == single_item["stored_count"]
        assert np.array_equal(batch_item["x"], single_item["x"])
        assert np.array_equal(batch_item["y"], single_item["y"])
        assert np.array_equal(batch_item["flux"], single_item["flux"])


def test_resident_stack_estimates_and_warps_subpixel_translation_on_device():
    module = cuda_module_or_skip()
    required = [
        "estimate_translation_to_reference",
        "estimate_translation_subpixel_to_reference",
        "apply_translation_bilinear_frame",
    ]
    missing = [name for name in required if not hasattr(module.ResidentCalibratedStack, name)]
    if missing:
        raise AssertionError(f"ResidentCalibratedStack is missing {missing}")

    image = np.zeros((64, 64), dtype=np.float32)
    yy, xx = np.indices(image.shape, dtype=np.float32)
    for x, y, flux in [
        (12.25, 14.50, 150.0),
        (24.00, 20.75, 230.0),
        (41.50, 18.25, 180.0),
        (16.75, 42.00, 130.0),
        (49.25, 45.50, 210.0),
        (35.50, 33.25, 170.0),
    ]:
        image += flux * np.exp(-(((xx - x) ** 2 + (yy - y) ** 2) / (2.0 * 1.2**2)))
    reference = (image + 10.0 + 0.01 * xx + 0.02 * yy).astype(np.float32)
    true_delta = np.array([2.25, -1.5], dtype=np.float32)
    moving, _coverage = module.warp_translation_bilinear_f32(
        reference,
        -float(true_delta[0]),
        -float(true_delta[1]),
        0.0,
    )

    stack = module.ResidentCalibratedStack(2, reference.shape[0], reference.shape[1])
    stack.upload_calibrated_frame(0, reference)
    stack.upload_calibrated_frame(1, moving)

    coarse = stack.estimate_translation_to_reference(0, 1, 4, 4)
    refined = stack.estimate_translation_subpixel_to_reference(
        0,
        1,
        float(coarse["dx"]),
        float(coarse["dy"]),
        3,
        0.25,
    )
    stack.apply_translation_bilinear_frame(1, refined["dx"], refined["dy"], np.nan)
    aligned, weight_map = stack.integrate_mean(np.array([0.0, 1.0], dtype=np.float32))

    valid = weight_map > 0.0
    valid &= (xx >= 8) & (xx < reference.shape[1] - 8) & (yy >= 8) & (yy < reference.shape[0] - 8)
    rms = float(np.sqrt(np.mean((aligned[valid] - reference[valid]) ** 2)))

    assert coarse["model"] == "resident_translation_integer_ncc"
    assert refined["model"] == "resident_translation_subpixel_ncc"
    assert abs(refined["dx"] - float(true_delta[0])) <= 0.25
    assert abs(refined["dy"] - float(true_delta[1])) <= 0.25
    assert refined["candidate_count"] == 49
    assert refined["score"] > 0.98
    assert rms < 4.0


def test_resident_stack_matrix_alignment_metrics_match_standalone_cuda():
    module = cuda_module_or_skip()
    if not hasattr(module.ResidentCalibratedStack, "matrix_alignment_metrics_to_reference"):
        raise AssertionError("ResidentCalibratedStack.matrix_alignment_metrics_to_reference is missing")

    reference = _resident_star_field()
    matrix = np.asarray([[1.0, 0.0, 2.25], [0.0, 1.0, -1.5], [0.0, 0.0, 1.0]], dtype=np.float32)
    moving, _ = module.warp_matrix_bilinear_f32(reference, np.linalg.inv(matrix).astype(np.float32), 0.0)
    stack = module.ResidentCalibratedStack(2, reference.shape[0], reference.shape[1])
    stack.upload_calibrated_frame(0, reference)
    stack.upload_calibrated_frame(1, moving)

    resident = stack.matrix_alignment_metrics_to_reference(0, 1, matrix, sample_stride=2)
    standalone = module.matrix_alignment_metrics_f32(reference, moving, matrix, sample_stride=2)
    bad = stack.matrix_alignment_metrics_to_reference(
        0,
        1,
        np.asarray([[1.0, 0.0, -1.0], [0.0, 1.0, 2.0], [0.0, 0.0, 1.0]], dtype=np.float32),
        sample_stride=2,
    )

    assert resident["model"] == "resident_matrix_alignment_metrics_cuda"
    assert resident["reference_index"] == 0
    assert resident["moving_index"] == 1
    assert resident["valid_pixels"] == standalone["valid_pixels"]
    assert resident["sampled_pixels"] == standalone["sampled_pixels"]
    assert resident["sample_stride"] == 2
    assert abs(resident["rms"] - standalone["rms"]) < 1.0e-5
    assert abs(resident["mean_abs_diff"] - standalone["mean_abs_diff"]) < 1.0e-5
    assert abs(resident["ncc"] - standalone["ncc"]) < 1.0e-6
    assert resident["rms"] < bad["rms"] * 0.5
    assert resident["ncc"] > bad["ncc"]


def test_resident_stack_batches_matrix_translation_refine():
    module = cuda_module_or_skip()
    if not hasattr(module.ResidentCalibratedStack, "refine_matrix_translation_candidates_batch_to_reference"):
        raise AssertionError(
            "ResidentCalibratedStack.refine_matrix_translation_candidates_batch_to_reference is missing"
        )

    reference = _resident_star_field()
    matrices = np.asarray(
        [
            [[1.0, 0.0, 2.25], [0.0, 1.0, -1.5], [0.0, 0.0, 1.0]],
            [[1.0, 0.0, -1.75], [0.0, 1.0, 2.0], [0.0, 0.0, 1.0]],
        ],
        dtype=np.float32,
    )
    moving_frames = [
        module.warp_matrix_bilinear_f32(reference, np.linalg.inv(matrix).astype(np.float32), 0.0)[0]
        for matrix in matrices
    ]
    stack = module.ResidentCalibratedStack(3, reference.shape[0], reference.shape[1])
    stack.upload_calibrated_frame(0, reference)
    for offset, frame in enumerate(moving_frames, start=1):
        stack.upload_calibrated_frame(offset, frame)

    batch = stack.refine_matrix_translation_candidates_batch_to_reference(
        0,
        [1, 2],
        matrices,
        search_radius_px=0.5,
        coarse_step_px=0.25,
        fine_radius_px=0.25,
        fine_step_px=0.125,
        coarse_sample_stride=2,
        final_sample_stride=2,
    )
    singles = [
        stack.refine_matrix_translation_candidates_to_reference(
            0,
            index,
            np.asarray([matrix], dtype=np.float32),
            search_radius_px=0.5,
            coarse_step_px=0.25,
            fine_radius_px=0.25,
            fine_step_px=0.125,
            coarse_sample_stride=2,
            final_sample_stride=2,
        )
        for index, matrix in zip([1, 2], matrices, strict=True)
    ]

    assert [item["moving_index"] for item in batch] == [1, 2]
    assert batch[0]["batch_model"] == "resident_cuda_matrix_metric_translation_batch_refine_grid"
    assert batch[0]["batch_count"] == 2
    assert batch[0]["batch_metric_mode"] == "flattened_frame_candidate_grid"
    assert batch[0]["batch_metric_kernel_launches"] == 2
    assert batch[0]["metric_workload_model"] == "candidate_count_x_sampled_pixels"
    assert batch[0]["coarse_total_candidates"] == batch[0]["batch_count"] * batch[0]["coarse_candidates_per_seed"]
    assert batch[0]["fine_total_candidates"] > 0
    assert batch[0]["coarse_sampled_pixels_per_candidate"] > 0
    assert batch[0]["fine_sampled_pixels_per_candidate"] > 0
    assert batch[0]["coarse_metric_sample_evaluations"] == (
        batch[0]["coarse_total_candidates"] * batch[0]["coarse_sampled_pixels_per_candidate"]
    )
    assert batch[0]["fine_metric_sample_evaluations"] == (
        batch[0]["fine_total_candidates"] * batch[0]["fine_sampled_pixels_per_candidate"]
    )
    assert batch[0]["coarse_metric_megasamples_per_s"] >= 0.0
    assert batch[0]["fine_metric_megasamples_per_s"] >= 0.0
    assert batch[0]["workspace_mode"] == "shared_flattened_candidate_metric_buffers"
    assert batch[0]["workspace_candidate_capacity"] >= batch[0]["coarse_candidates_per_seed"]
    assert batch[0]["workspace_bytes"] > 0
    for batch_result, single_result in zip(batch, singles, strict=True):
        assert batch_result["model"] == single_result["model"]
        assert batch_result["batch_metric_mode"] == "flattened_frame_candidate_grid"
        assert batch_result["batch_metric_kernel_launches"] == 2
        assert batch_result["metric_workload_model"] == "candidate_count_x_sampled_pixels"
        assert batch_result["workspace_mode"] == "shared_flattened_candidate_metric_buffers"
        assert batch_result["workspace_candidate_capacity"] >= batch_result["coarse_candidates_per_seed"]
        assert batch_result["workspace_bytes"] == batch[0]["workspace_bytes"]
        assert batch_result["coarse_metric_s"] >= 0.0
        assert batch_result["fine_metric_s"] >= 0.0
        assert batch_result["native_coarse_total_s"] >= batch_result["coarse_metric_s"]
        assert batch_result["native_fine_total_s"] >= batch_result["fine_metric_s"]
        assert np.allclose(batch_result["matrix"], single_result["matrix"], rtol=1e-6, atol=1e-6)
        assert abs(batch_result["metrics"]["ncc"] - single_result["metrics"]["ncc"]) < 1.0e-6
        assert abs(batch_result["metrics"]["rms"] - single_result["metrics"]["rms"]) < 1.0e-5


def test_resident_stack_star_catalog_registration_stays_on_device():
    module = cuda_module_or_skip()
    if not hasattr(module.ResidentCalibratedStack, "estimate_translation_from_stars_to_reference"):
        raise AssertionError("ResidentCalibratedStack.estimate_translation_from_stars_to_reference is missing")

    reference = _resident_star_field()
    moving = _shift_image(reference, 4, -3)
    stack = module.ResidentCalibratedStack(2, reference.shape[0], reference.shape[1])
    stack.upload_calibrated_frame(0, reference)
    stack.upload_calibrated_frame(1, moving)

    result = stack.estimate_translation_from_stars_to_reference(0, 1, 30.0, 16, 0.25, 8.0, 8.0)
    stack.apply_translation_bilinear_frame(1, result["refined_dx"], result["refined_dy"], np.nan)
    aligned, weight_map = stack.integrate_mean(np.array([0.0, 1.0], dtype=np.float32))

    valid = weight_map > 0.0
    rms = float(np.sqrt(np.mean((aligned[valid] - reference[valid]) ** 2)))

    assert result["model"] == "resident_star_catalog_pair_offset_translation"
    assert result["dx"] == -4.0
    assert result["dy"] == 3.0
    assert abs(result["refined_dx"] + 4.0) < 1.0e-5
    assert abs(result["refined_dy"] - 3.0) < 1.0e-5
    assert result["mutual_inliers"] >= 6
    assert result["rms_px"] == 0.0
    assert rms < 1.0e-4


def test_resident_stack_star_catalog_registration_can_use_grid_candidates():
    module = cuda_module_or_skip()
    reference = _resident_star_field()
    moving = _shift_image(reference, 4, -3)
    stack = module.ResidentCalibratedStack(2, reference.shape[0], reference.shape[1])
    stack.upload_calibrated_frame(0, reference)
    stack.upload_calibrated_frame(1, moving)

    result = stack.estimate_translation_from_stars_to_reference(
        0,
        1,
        30.0,
        16,
        0.25,
        8.0,
        8.0,
        grid_cols=4,
        grid_rows=4,
    )

    assert result["candidate_selection"] == "grid_brightest_per_cell"
    assert result["catalog_capacity"] == 16
    assert result["grid_cols"] == 4
    assert result["grid_rows"] == 4
    assert abs(result["refined_dx"] + 4.0) < 1.0e-5
    assert abs(result["refined_dy"] - 3.0) < 1.0e-5
    assert result["mutual_inliers"] >= 6


def test_resident_stack_weighted_mean_skips_zero_weight_and_nan_frames():
    module = cuda_module_or_skip()
    frames = [
        np.full((2, 2), 1, dtype=np.float32),
        np.full((2, 2), 100, dtype=np.float32),
        np.array([[3, np.nan], [3, 3]], dtype=np.float32),
    ]
    weights = np.array([1, 0, 1], dtype=np.float32)

    stack = module.ResidentCalibratedStack(len(frames), 2, 2)
    for index, frame in enumerate(frames):
        stack.upload_calibrated_frame(index, frame)
    master, weight_map = stack.integrate_mean(weights)

    assert np.allclose(master, np.array([[2, 1], [2, 2]], dtype=np.float32))
    assert np.allclose(weight_map, np.array([[2, 1], [2, 2]], dtype=np.float32))


def _mean_std_sigma_reference(
    frames: list[np.ndarray],
    low_sigma: float,
    high_sigma: float,
    winsorize: bool,
    weights: np.ndarray | None = None,
):
    stack = np.stack(frames, axis=0).astype(np.float32)
    frame_weights = np.ones((stack.shape[0],), dtype=np.float32) if weights is None else weights.astype(np.float32)
    active = frame_weights[:, None, None] > 0
    finite = np.isfinite(stack)
    stats_valid = active & finite
    count = np.sum(stats_valid, axis=0)
    safe_count = np.where(count > 0, count, 1)
    mean = np.sum(np.where(stats_valid, stack, 0.0), axis=0) / safe_count
    std = np.sqrt(np.sum(np.where(stats_valid, (stack - mean[None, :, :]) ** 2, 0.0), axis=0) / safe_count)
    if winsorize:
        first_low = mean - np.float32(low_sigma) * std
        first_high = mean + np.float32(high_sigma) * std
        winsorized = np.where(stats_valid, np.clip(stack, first_low[None, :, :], first_high[None, :, :]), 0.0)
        winsor_mean = np.sum(np.where(stats_valid, winsorized, 0.0), axis=0) / safe_count
        winsor_std = np.sqrt(
            np.sum(np.where(stats_valid, (winsorized - winsor_mean[None, :, :]) ** 2, 0.0), axis=0) / safe_count
        )
        low_threshold = winsor_mean - np.float32(low_sigma) * winsor_std
        high_threshold = winsor_mean + np.float32(high_sigma) * winsor_std
    else:
        low_threshold = mean - np.float32(low_sigma) * std
        high_threshold = mean + np.float32(high_sigma) * std
    low = stats_valid & (stack < low_threshold[None, :, :])
    high = stats_valid & (stack > high_threshold[None, :, :])
    valid = stats_valid & ~(low | high)
    weight_cube = frame_weights[:, None, None]
    weight_sum = np.sum(np.where(valid, weight_cube, 0.0), axis=0)
    master = np.divide(
        np.sum(np.where(valid, stack * weight_cube, 0.0), axis=0),
        weight_sum,
        out=np.zeros_like(mean, dtype=np.float32),
        where=weight_sum > 0,
    )
    return (
        master.astype(np.float32),
        np.sum(valid, axis=0).astype(np.float32),
        np.sum(stats_valid & low, axis=0).astype(np.float32),
        np.sum(stats_valid & high, axis=0).astype(np.float32),
    )


def test_resident_stack_sigma_clip_maps_match_cpu_reference():
    module = cuda_module_or_skip()
    if not hasattr(module, "ResidentCalibratedStack") or not hasattr(
        module.ResidentCalibratedStack, "integrate_sigma_clip"
    ):
        raise AssertionError("ResidentCalibratedStack.integrate_sigma_clip is missing from glass_cuda")

    frames = [
        np.array([[1, 5], [10, 2]], dtype=np.float32),
        np.array([[1, 6], [10, 2]], dtype=np.float32),
        np.array([[1, 7], [10, 2]], dtype=np.float32),
        np.array([[100, 8], [10, -50]], dtype=np.float32),
    ]
    stack = module.ResidentCalibratedStack(len(frames), 2, 2)
    for index, frame in enumerate(frames):
        stack.upload_calibrated_frame(index, frame)

    master, weight_map, coverage, low_reject, high_reject = stack.integrate_sigma_clip(None, 1.0, 1.0, False)
    expected_master, expected_coverage, expected_low, expected_high = _mean_std_sigma_reference(
        frames, 1.0, 1.0, False
    )

    assert np.allclose(master, expected_master, rtol=1e-5, atol=1e-5)
    assert np.allclose(weight_map, expected_coverage, rtol=1e-5, atol=1e-5)
    assert np.allclose(coverage, expected_coverage, rtol=1e-5, atol=1e-5)
    assert np.allclose(low_reject, expected_low, rtol=1e-5, atol=1e-5)
    assert np.allclose(high_reject, expected_high, rtol=1e-5, atol=1e-5)


def test_resident_stack_sigma_clip_ignores_zero_weight_frames():
    module = cuda_module_or_skip()
    frames = [
        np.full((2, 2), 1, dtype=np.float32),
        np.full((2, 2), 1, dtype=np.float32),
        np.full((2, 2), 100, dtype=np.float32),
    ]
    weights = np.array([1, 1, 0], dtype=np.float32)
    stack = module.ResidentCalibratedStack(len(frames), 2, 2)
    for index, frame in enumerate(frames):
        stack.upload_calibrated_frame(index, frame)

    master, weight_map, coverage, low_reject, high_reject = stack.integrate_sigma_clip(weights, 1.0, 1.0, False)
    expected_master, expected_coverage, expected_low, expected_high = _mean_std_sigma_reference(
        frames, 1.0, 1.0, False, weights
    )

    assert np.allclose(master, expected_master, rtol=1e-5, atol=1e-5)
    assert np.allclose(weight_map, expected_coverage, rtol=1e-5, atol=1e-5)
    assert np.allclose(coverage, expected_coverage, rtol=1e-5, atol=1e-5)
    assert np.allclose(low_reject, expected_low, rtol=1e-5, atol=1e-5)
    assert np.allclose(high_reject, expected_high, rtol=1e-5, atol=1e-5)


def test_resident_stack_winsorized_sigma_matches_mean_std_reference():
    module = cuda_module_or_skip()
    if not hasattr(module, "ResidentCalibratedStack") or not hasattr(
        module.ResidentCalibratedStack, "integrate_sigma_clip"
    ):
        raise AssertionError("ResidentCalibratedStack.integrate_sigma_clip is missing from glass_cuda")

    frames = [
        np.full((2, 2), 1, dtype=np.float32),
        np.full((2, 2), 1, dtype=np.float32),
        np.full((2, 2), 1, dtype=np.float32),
        np.full((2, 2), 100, dtype=np.float32),
    ]
    stack = module.ResidentCalibratedStack(len(frames), 2, 2)
    for index, frame in enumerate(frames):
        stack.upload_calibrated_frame(index, frame)

    master, weight_map, coverage, low_reject, high_reject = stack.integrate_sigma_clip(None, 1.0, 1.0, True)
    expected_master, expected_coverage, expected_low, expected_high = _mean_std_sigma_reference(
        frames, 1.0, 1.0, True
    )

    assert np.allclose(master, expected_master, rtol=1e-5, atol=1e-5)
    assert np.allclose(weight_map, expected_coverage, rtol=1e-5, atol=1e-5)
    assert np.allclose(coverage, expected_coverage, rtol=1e-5, atol=1e-5)
    assert np.allclose(low_reject, expected_low, rtol=1e-5, atol=1e-5)
    assert np.allclose(high_reject, expected_high, rtol=1e-5, atol=1e-5)


def test_resident_stack_hardened_winsorized_sigma_matches_cpu_baseline():
    module = cuda_module_or_skip()
    if not hasattr(module, "ResidentCalibratedStack") or not hasattr(
        module.ResidentCalibratedStack, "integrate_hardened_winsorized_sigma"
    ):
        raise AssertionError(
            "ResidentCalibratedStack.integrate_hardened_winsorized_sigma is missing from glass_cuda"
        )

    frames = [
        np.array([[1, 1], [10, 4]], dtype=np.float32),
        np.array([[1, 2], [10, 4]], dtype=np.float32),
        np.array([[1, 3], [10, 4]], dtype=np.float32),
        np.array([[12, 4], [10, 40]], dtype=np.float32),
    ]
    weights = np.array([1.0, 2.0, 1.0, 1.0], dtype=np.float32)
    resident_stack = module.ResidentCalibratedStack(len(frames), 2, 2)
    for index, frame in enumerate(frames):
        resident_stack.upload_calibrated_frame(index, frame)

    master, weight_map, coverage, low_reject, high_reject, timing = (
        resident_stack.integrate_hardened_winsorized_sigma_timed(weights, 2.4, 2.4)
    )
    expected_master, expected_weight, expected_coverage, expected_low, expected_high = (
        weighted_integrate_stack(
            np.stack(frames, axis=0),
            weights=weights,
            rejection="winsorized_sigma",
            low_sigma=2.4,
            high_sigma=2.4,
        )
    )

    assert np.allclose(master, expected_master, rtol=1e-5, atol=1e-5)
    assert np.allclose(weight_map, expected_weight, rtol=1e-5, atol=1e-5)
    assert np.allclose(coverage, expected_coverage, rtol=1e-5, atol=1e-5)
    assert np.allclose(low_reject, expected_low, rtol=1e-5, atol=1e-5)
    assert np.allclose(high_reject, expected_high, rtol=1e-5, atol=1e-5)
    assert timing["native_method"] == "ResidentCalibratedStack.integrate_hardened_winsorized_sigma"
    assert timing["resident_winsorized_mode"] == "hardened_cpu_parity"
    assert timing["frame_count"] == len(frames)
    assert timing["pixel_count"] == 4
    assert timing["total_s"] >= 0.0
    assert high_reject[0, 0] == 1
    assert high_reject[1, 1] == 1


def _expected_matrix_warped_sigma(
    module: object,
    frames: list[np.ndarray],
    matrices: np.ndarray,
    low_sigma: float,
    high_sigma: float,
    winsorize: bool,
    interpolation: str,
    weights: np.ndarray | None = None,
    clamping_threshold: float = -1.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    warped_frames: list[np.ndarray] = []
    geometric: np.ndarray | None = None
    frame_weights = (
        np.ones((len(frames),), dtype=np.float32)
        if weights is None
        else np.asarray(weights, dtype=np.float32)
    )
    for frame, matrix, weight in zip(frames, matrices, frame_weights, strict=True):
        if interpolation == "lanczos3":
            warped, footprint = module.warp_matrix_lanczos3_f32(
                frame,
                matrix,
                np.nan,
                clamping_threshold,
            )
        else:
            warped, footprint = module.warp_matrix_bilinear_f32(frame, matrix, np.nan)
        warped_frames.append(warped)
        footprint_count = ((footprint > 0.5) & (weight > 0.0) & np.isfinite(weight)).astype(np.float32)
        geometric = footprint_count if geometric is None else geometric + footprint_count
    warped_stack = module.ResidentCalibratedStack(len(warped_frames), *warped_frames[0].shape)
    for index, warped in enumerate(warped_frames):
        warped_stack.upload_calibrated_frame(index, warped)
    master, weight_map, coverage, low_reject, high_reject = warped_stack.integrate_sigma_clip(
        frame_weights,
        low_sigma,
        high_sigma,
        winsorize,
    )
    return (
        master,
        weight_map,
        coverage,
        low_reject,
        high_reject,
        np.zeros_like(master) if geometric is None else geometric,
    )


def test_resident_stack_fused_matrix_warped_sigma_bilinear_matches_warp_then_integrate():
    module = cuda_module_or_skip()
    if not hasattr(module, "ResidentCalibratedStack"):
        raise AssertionError("ResidentCalibratedStack is missing from glass_cuda")

    yy, xx = np.indices((16, 18), dtype=np.float32)
    base = (10.0 + xx * 0.7 + yy * 0.2).astype(np.float32)
    frames = [
        base,
        base + 1.0,
        base + 2.0,
        base + 80.0,
    ]
    matrices = np.stack(
        [
            _matrix_translation(0.0, 0.0),
            _matrix_translation(0.5, -0.25),
            _matrix_translation(-1.0, 0.75),
            _matrix_translation(0.25, 0.5),
        ],
        axis=0,
    )
    weights = np.ones((len(frames),), dtype=np.float32)
    stack = module.ResidentCalibratedStack(len(frames), 16, 18)
    for index, frame in enumerate(frames):
        stack.upload_calibrated_frame(index, frame)

    master, weight_map, coverage, low_reject, high_reject, geometric, timing = (
        stack.integrate_matrix_warped_sigma_clip(
            matrices,
            weights,
            interpolation="bilinear",
            low_sigma=1.0,
            high_sigma=1.0,
            winsorize=False,
        )
    )
    expected_master, expected_weight, expected_coverage, expected_low, expected_high, expected_geometric = (
        _expected_matrix_warped_sigma(
            module,
            frames,
            matrices,
            1.0,
            1.0,
            False,
            "bilinear",
            weights,
        )
    )
    unwarped_master, _ = stack.integrate_mean(weights)

    assert timing["timing_model"] == "native_fused_matrix_warp_sigma_clip_one_sync"
    assert timing["interpolation"] == "bilinear"
    assert timing["rejection"] == "sigma_clip"
    assert timing["winsorize"] is False
    assert timing["avoids_stack_scatter"] is True
    assert timing["modifies_resident_stack"] is False
    assert timing["output_bytes"] == 16 * 18 * 4 * 6
    assert np.max(high_reject) > 0.0
    assert np.allclose(master, expected_master, rtol=3e-5, atol=3e-5)
    assert np.allclose(weight_map, expected_weight, rtol=1e-6, atol=1e-6)
    assert np.allclose(coverage, expected_coverage, rtol=1e-6, atol=1e-6)
    assert np.allclose(low_reject, expected_low, rtol=1e-6, atol=1e-6)
    assert np.allclose(high_reject, expected_high, rtol=1e-6, atol=1e-6)
    assert np.allclose(geometric, expected_geometric, rtol=1e-6, atol=1e-6)
    assert not np.allclose(master, unwarped_master)


def test_resident_stack_fused_matrix_warped_winsorized_lanczos3_matches_warp_then_integrate():
    module = cuda_module_or_skip()
    if not hasattr(module, "ResidentCalibratedStack"):
        raise AssertionError("ResidentCalibratedStack is missing from glass_cuda")

    yy, xx = np.indices((22, 24), dtype=np.float32)
    base = (25.0 + np.sin(xx * 0.15) * 2.0 + yy * 0.3).astype(np.float32)
    frames = [
        base,
        base + 0.5,
        base - 0.75,
        base + 60.0,
    ]
    matrices = np.stack(
        [
            _matrix_translation(0.0, 0.0),
            _matrix_translation(0.3, -0.2),
            _matrix_translation(-0.4, 0.35),
            _matrix_translation(0.2, 0.25),
        ],
        axis=0,
    )
    weights = np.ones((len(frames),), dtype=np.float32)
    stack = module.ResidentCalibratedStack(len(frames), 22, 24)
    for index, frame in enumerate(frames):
        stack.upload_calibrated_frame(index, frame)

    master, weight_map, coverage, low_reject, high_reject, geometric, timing = (
        stack.integrate_matrix_warped_sigma_clip(
            matrices,
            weights,
            interpolation="lanczos3",
            clamping_threshold=0.3,
            low_sigma=1.0,
            high_sigma=1.0,
            winsorize=True,
        )
    )
    expected_master, expected_weight, expected_coverage, expected_low, expected_high, expected_geometric = (
        _expected_matrix_warped_sigma(
            module,
            frames,
            matrices,
            1.0,
            1.0,
            True,
            "lanczos3",
            weights,
            clamping_threshold=0.3,
        )
    )

    assert timing["interpolation"] == "lanczos3"
    assert timing["rejection"] == "winsorized_sigma"
    assert timing["winsorize"] is True
    assert timing["inverse_batch_bytes"] == len(frames) * 9 * 4
    assert np.max(high_reject) > 0.0
    assert np.allclose(master, expected_master, rtol=3e-5, atol=3e-5)
    assert np.allclose(weight_map, expected_weight, rtol=1e-6, atol=1e-6)
    assert np.allclose(coverage, expected_coverage, rtol=1e-6, atol=1e-6)
    assert np.allclose(low_reject, expected_low, rtol=1e-6, atol=1e-6)
    assert np.allclose(high_reject, expected_high, rtol=1e-6, atol=1e-6)
    assert np.allclose(geometric, expected_geometric, rtol=1e-6, atol=1e-6)
