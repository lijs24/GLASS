from __future__ import annotations

from dataclasses import asdict

import numpy as np

from gpwbpp.cpu.calibration import calibrate_light
from gpwbpp.engine.resident_cuda import _output_diagnostics
from gpwbpp.models import CalibrationPolicy
from tests.conftest import cuda_module_or_skip


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


def _mean_std_sigma_reference(frames: list[np.ndarray], low_sigma: float, high_sigma: float, winsorize: bool):
    stack = np.stack(frames, axis=0).astype(np.float32)
    mean = np.mean(stack, axis=0)
    std = np.std(stack, axis=0)
    low_threshold = mean - np.float32(low_sigma) * std
    high_threshold = mean + np.float32(high_sigma) * std
    low = stack < low_threshold[None, :, :]
    high = stack > high_threshold[None, :, :]
    if winsorize:
        working = np.where(low, low_threshold[None, :, :], stack)
        working = np.where(high, high_threshold[None, :, :], working)
        valid = np.ones_like(stack, dtype=bool)
    else:
        working = stack
        valid = ~(low | high)
    master = np.sum(np.where(valid, working, 0.0), axis=0) / np.sum(valid, axis=0)
    return (
        master.astype(np.float32),
        np.sum(valid, axis=0).astype(np.float32),
        np.sum(low, axis=0).astype(np.float32),
        np.sum(high, axis=0).astype(np.float32),
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
    assert np.allclose(weight_map, np.full((2, 2), len(frames), dtype=np.float32))
    assert np.allclose(coverage, expected_coverage, rtol=1e-5, atol=1e-5)
    assert np.allclose(low_reject, expected_low, rtol=1e-5, atol=1e-5)
    assert np.allclose(high_reject, expected_high, rtol=1e-5, atol=1e-5)
