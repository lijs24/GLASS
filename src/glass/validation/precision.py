from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import re
from typing import Any

import numpy as np

from glass.cpu.calibration import calibrate_light
from glass.cpu.integration import mean_integrate
from glass.io.fits_io import FitsImageReader
from glass.models import CalibrationPolicy


_SAMPLE_FORMAT_RE = re.compile(r'sampleFormat="([^"]+)"')


def read_xisf_sample_format(path: str | Path, max_bytes: int = 4 * 1024 * 1024) -> str | None:
    data = Path(path).read_bytes()[:max_bytes]
    text = data.decode("utf-8", errors="ignore")
    match = _SAMPLE_FORMAT_RE.search(text)
    return None if match is None else match.group(1)


def finite_error_stats(candidate: np.ndarray, reference: np.ndarray) -> dict[str, float]:
    cand = np.asarray(candidate, dtype=np.float64)
    ref = np.asarray(reference, dtype=np.float64)
    mask = np.isfinite(cand) & np.isfinite(ref)
    if not np.any(mask):
        return {
            "finite_pixels": 0.0,
            "max_abs": float("nan"),
            "mean_abs": float("nan"),
            "rmse": float("nan"),
            "reference_rms": float("nan"),
            "relative_rmse": float("nan"),
        }
    diff = cand[mask] - ref[mask]
    abs_diff = np.abs(diff)
    reference_rms = float(np.sqrt(np.mean(ref[mask] * ref[mask])))
    rmse = float(np.sqrt(np.mean(diff * diff)))
    return {
        "finite_pixels": float(np.count_nonzero(mask)),
        "max_abs": float(np.max(abs_diff)),
        "mean_abs": float(np.mean(abs_diff)),
        "rmse": rmse,
        "reference_rms": reference_rms,
        "relative_rmse": float(rmse / reference_rms) if reference_rms > 0 else 0.0,
    }


def read_crop(path: str | Path, y0: int, x0: int, height: int, width: int, dtype=np.float64) -> np.ndarray:
    with FitsImageReader(path) as reader:
        y1 = min(reader.height, y0 + height)
        x1 = min(reader.width, x0 + width)
        return reader.read_tile(y0, y1, x0, x1, dtype=dtype)


def mean_crop(paths: list[str | Path], y0: int, x0: int, height: int, width: int) -> np.ndarray:
    if not paths:
        raise ValueError("cannot compute a mean crop from an empty path list")
    acc: np.ndarray | None = None
    for path in paths:
        data = read_crop(path, y0, x0, height, width, dtype=np.float64)
        if acc is None:
            acc = np.zeros_like(data, dtype=np.float64)
        acc += data
    assert acc is not None
    return acc / float(len(paths))


def make_crop_masters(
    bias_paths: list[str | Path],
    dark_paths: list[str | Path],
    flat_paths: list[str | Path],
    y0: int,
    x0: int,
    height: int,
    width: int,
    policy: CalibrationPolicy,
) -> tuple[np.ndarray | None, np.ndarray | None, np.ndarray | None]:
    master_bias = mean_crop(bias_paths, y0, x0, height, width) if bias_paths else None
    master_dark = mean_crop(dark_paths, y0, x0, height, width) if dark_paths else None
    if master_dark is not None and not policy.master_dark_includes_bias and master_bias is not None:
        master_dark = master_dark - master_bias

    master_flat = None
    if flat_paths:
        flat = mean_crop(flat_paths, y0, x0, height, width)
        if master_bias is not None:
            flat = flat - master_bias
        norm = float(np.mean(flat) if policy.flat_normalization == "mean" else np.median(flat))
        if abs(norm) < policy.flat_floor:
            raise ValueError("flat normalization is below flat_floor")
        master_flat = np.maximum(flat / norm, policy.flat_floor)
    return master_bias, master_dark, master_flat


def calibrate_light_f64(
    light: np.ndarray,
    master_bias: np.ndarray | None,
    master_dark: np.ndarray | None,
    master_flat: np.ndarray | None,
    light_exposure_s: float,
    dark_exposure_s: float | None,
    policy: CalibrationPolicy,
) -> np.ndarray:
    calibrated = np.asarray(light, dtype=np.float64).copy()
    if master_dark is not None:
        scale = 1.0
        if policy.dark_scaling_enabled and dark_exposure_s not in (None, 0):
            scale = float(light_exposure_s) / float(dark_exposure_s)
        calibrated = calibrated - np.asarray(master_dark, dtype=np.float64) * scale
        if not policy.master_dark_includes_bias and master_bias is not None:
            calibrated = calibrated - np.asarray(master_bias, dtype=np.float64)
    elif master_bias is not None:
        calibrated = calibrated - np.asarray(master_bias, dtype=np.float64)
    if master_flat is not None:
        calibrated = calibrated / np.maximum(np.asarray(master_flat, dtype=np.float64), policy.flat_floor)
    if policy.pedestal:
        calibrated = calibrated + float(policy.pedestal)
    return calibrated


def compare_precision_on_crops(
    light_frames: list[dict[str, Any]],
    bias_paths: list[str | Path],
    dark_paths: list[str | Path],
    flat_paths: list[str | Path],
    y0: int,
    x0: int,
    height: int,
    width: int,
    dark_exposure_s: float | None,
    policy: CalibrationPolicy,
    cuda_module: Any | None = None,
) -> dict[str, Any]:
    master_bias64, master_dark64, master_flat64 = make_crop_masters(
        bias_paths, dark_paths, flat_paths, y0, x0, height, width, policy
    )
    master_bias32 = None if master_bias64 is None else master_bias64.astype(np.float32)
    master_dark32 = None if master_dark64 is None else master_dark64.astype(np.float32)
    master_flat32 = None if master_flat64 is None else master_flat64.astype(np.float32)

    f64_frames: list[np.ndarray] = []
    f32_frames: list[np.ndarray] = []
    cuda_frames: list[np.ndarray] = []
    calibration_errors: list[dict[str, Any]] = []

    for frame in light_frames:
        light64 = read_crop(frame["path"], y0, x0, height, width, dtype=np.float64)
        light_exposure = float(frame.get("exposure_s") or 0.0)
        ref64 = calibrate_light_f64(
            light64,
            master_bias64,
            master_dark64,
            master_flat64,
            light_exposure,
            dark_exposure_s,
            policy,
        )
        cpu32 = calibrate_light(
            light64.astype(np.float32),
            master_bias32,
            master_dark32,
            master_flat32,
            light_exposure,
            dark_exposure_s,
            policy,
        )
        f64_frames.append(ref64)
        f32_frames.append(cpu32)
        item: dict[str, Any] = {
            "frame_id": frame.get("id"),
            "cpu32_vs_cpu64": finite_error_stats(cpu32, ref64),
        }
        if cuda_module is not None and getattr(cuda_module, "cuda_available", lambda: False)():
            cuda32 = cuda_module.calibrate_tile_f32(
                light64.astype(np.float32),
                master_bias32,
                master_dark32,
                master_flat32,
                light_exposure,
                dark_exposure_s,
                asdict(policy),
            )
            cuda_frames.append(cuda32)
            item["cuda32_vs_cpu64"] = finite_error_stats(cuda32, ref64)
            item["cuda32_vs_cpu32"] = finite_error_stats(cuda32, cpu32)
        calibration_errors.append(item)

    master64 = np.mean(np.stack(f64_frames, axis=0), axis=0)
    master32, _ = mean_integrate(f32_frames)
    result: dict[str, Any] = {
        "crop": {"x0": x0, "y0": y0, "width": width, "height": height},
        "frame_count": len(light_frames),
        "calibration_errors": calibration_errors,
        "integration_errors": {
            "cpu32_vs_cpu64": finite_error_stats(master32, master64),
        },
    }

    if cuda_module is not None and getattr(cuda_module, "cuda_available", lambda: False)() and cuda_frames:
        stack = cuda_module.ResidentCalibratedStack(len(cuda_frames), cuda_frames[0].shape[0], cuda_frames[0].shape[1])
        for index, frame in enumerate(cuda_frames):
            stack.upload_calibrated_frame(index, frame)
        cuda_master, _ = stack.integrate_mean()
        result["integration_errors"]["cuda32_vs_cpu64"] = finite_error_stats(cuda_master, master64)
        result["integration_errors"]["cuda32_vs_cpu32"] = finite_error_stats(cuda_master, master32)

    return result
