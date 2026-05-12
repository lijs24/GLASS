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
