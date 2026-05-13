from __future__ import annotations

from dataclasses import asdict

import numpy as np

from gpwbpp.cpu.calibration import calibrate_light
from gpwbpp.cpu.warp import warp_translation
from gpwbpp.engine.resident_cuda import _output_diagnostics
from gpwbpp.models import CalibrationPolicy
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
        raise AssertionError("ResidentCalibratedStack is missing from gpwbpp_cuda")

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
        raise AssertionError("ResidentCalibratedStack.apply_grid_normalization_frame is missing from gpwbpp_cuda")

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
        raise AssertionError("ResidentCalibratedStack.frame_pair_grid_stats is missing from gpwbpp_cuda")

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
        raise AssertionError("ResidentCalibratedStack.apply_translation_frame is missing from gpwbpp_cuda")

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
        raise AssertionError("ResidentCalibratedStack.integrate_sigma_clip is missing from gpwbpp_cuda")

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


def test_resident_stack_winsorized_sigma_matches_cpu_reference():
    module = cuda_module_or_skip()
    if not hasattr(module, "ResidentCalibratedStack") or not hasattr(
        module.ResidentCalibratedStack, "integrate_sigma_clip"
    ):
        raise AssertionError("ResidentCalibratedStack.integrate_sigma_clip is missing from gpwbpp_cuda")

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
