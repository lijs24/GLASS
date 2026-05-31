"""Compatibility API for the optional native CUDA backend.

This module keeps the public `glass_cuda` import path stable on CPU-only
installations. It reports visible NVIDIA devices through `nvidia-smi` when
available, but `cuda_available()` remains false until a real native CUDA
extension is built and loaded. Numeric helpers use CPU fallbacks only for smoke
testing the API surface; they are not advertised as GPU kernels.
"""

from __future__ import annotations

from dataclasses import asdict
import importlib
import shutil
import subprocess
from typing import Any

import numpy as np

from glass.cpu.calibration import calibrate_light
from glass.models import CalibrationPolicy


_NATIVE_ATTEMPTED = False
_NATIVE_MODULE = None
_NATIVE_IMPORT_ERROR: str | None = None


def _native():
    global _NATIVE_ATTEMPTED, _NATIVE_MODULE, _NATIVE_IMPORT_ERROR
    if _NATIVE_ATTEMPTED:
        return _NATIVE_MODULE
    _NATIVE_ATTEMPTED = True
    try:
        _NATIVE_MODULE = importlib.import_module("_glass_cuda_native")
        _NATIVE_IMPORT_ERROR = None
    except Exception as exc:
        _NATIVE_MODULE = None
        _NATIVE_IMPORT_ERROR = f"{type(exc).__name__}: {exc}"
        return None
    return _NATIVE_MODULE


def native_import_error() -> str | None:
    _native()
    return _NATIVE_IMPORT_ERROR


def native_extension_loaded() -> bool:
    return _native() is not None


def cuda_available() -> bool:
    native = _native()
    if native is None:
        return False
    return bool(native.cuda_available())


def _run_nvidia_smi() -> list[str]:
    if shutil.which("nvidia-smi") is None:
        return []
    command = [
        "nvidia-smi",
        "--query-gpu=index,name,compute_cap,memory.total,driver_version",
        "--format=csv,noheader,nounits",
    ]
    try:
        completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=5)
    except Exception:
        return []
    if completed.returncode != 0:
        return []
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def _nvidia_smi_devices() -> list[dict[str, Any]]:
    devices: list[dict[str, Any]] = []
    for line in _run_nvidia_smi():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 5:
            continue
        index, name, compute_capability, memory_total_mib, driver_version = parts[:5]
        try:
            device_id = int(index)
        except ValueError:
            device_id = len(devices)
        try:
            memory_total = int(float(memory_total_mib))
        except ValueError:
            memory_total = None
        devices.append(
            {
                "device_id": device_id,
                "name": name,
                "compute_capability": compute_capability,
                "memory_total_mib": memory_total,
                "driver_version": driver_version,
                "native_backend": False,
                "available_to_glass": False,
            }
        )
    return devices


def _normalize_matrix_refinement_result(result: dict[str, Any]) -> dict[str, Any]:
    seed_results = []
    for seed in list(result.get("seed_results", [])):
        seed_result = dict(seed)
        seed_result["seed_index"] = int(seed_result["seed_index"])
        seed_result["matrix"] = np.asarray(seed_result["matrix"], dtype=np.float32).tolist()
        seed_result["dx_correction"] = float(seed_result["dx_correction"])
        seed_result["dy_correction"] = float(seed_result["dy_correction"])
        seed_result["metrics"] = dict(seed_result["metrics"])
        seed_result["coarse_candidates"] = int(seed_result["coarse_candidates"])
        seed_result["fine_candidates"] = int(seed_result["fine_candidates"])
        seed_results.append(seed_result)
    normalized = {
        "matrix": np.asarray(result["matrix"], dtype=np.float32).tolist(),
        "dx_correction": float(result["dx_correction"]),
        "dy_correction": float(result["dy_correction"]),
        "metrics": dict(result["metrics"]),
        "selected_index": int(result["selected_index"]),
        "seed_count": int(result["seed_count"]),
        "seed_results": seed_results,
        "coarse_candidates_per_seed": int(result["coarse_candidates_per_seed"]),
        "search_radius_px": float(result["search_radius_px"]),
        "coarse_step_px": float(result["coarse_step_px"]),
        "fine_radius_px": float(result["fine_radius_px"]),
        "fine_step_px": float(result["fine_step_px"]),
        "coarse_sample_stride": int(result["coarse_sample_stride"]),
        "final_sample_stride": int(result["final_sample_stride"]),
        "reference_index": int(result["reference_index"]),
        "moving_index": int(result["moving_index"]),
        "model": str(result.get("model", "resident_cuda_matrix_metric_translation_multi_seed_refine_grid")),
    }
    if "batch_index" in result:
        normalized["batch_index"] = int(result["batch_index"])
    if "batch_count" in result:
        normalized["batch_count"] = int(result["batch_count"])
    if "batch_model" in result:
        normalized["batch_model"] = str(result["batch_model"])
    if "batch_metric_mode" in result:
        normalized["batch_metric_mode"] = str(result["batch_metric_mode"])
    if "metric_workload_model" in result:
        normalized["metric_workload_model"] = str(result["metric_workload_model"])
    if "workspace_mode" in result:
        normalized["workspace_mode"] = str(result["workspace_mode"])
    for key in (
        "batch_metric_kernel_launches",
        "coarse_total_candidates",
        "fine_total_candidates",
        "coarse_sampled_pixels_per_candidate",
        "fine_sampled_pixels_per_candidate",
        "coarse_metric_sample_evaluations",
        "fine_metric_sample_evaluations",
        "workspace_candidate_capacity",
        "workspace_bytes",
    ):
        if key in result:
            normalized[key] = int(result[key])
    for key in (
        "coarse_metric_s",
        "fine_metric_s",
        "coarse_metric_megasamples_per_s",
        "fine_metric_megasamples_per_s",
        "native_coarse_total_s",
        "native_fine_total_s",
    ):
        if key in result:
            normalized[key] = float(result[key])
    return normalized


def list_devices() -> list[dict[str, Any]]:
    native = _native()
    smi_devices = _nvidia_smi_devices()
    if native is not None:
        try:
            native_devices = [dict(device) for device in native.list_devices()]
            smi_by_id = {device.get("device_id"): device for device in smi_devices}
            for device in native_devices:
                smi = smi_by_id.get(device.get("device_id"))
                if smi is None:
                    continue
                for key in ("driver_version", "compute_capability", "memory_total_mib", "name"):
                    value = device.get(key)
                    if value in (None, "", "unknown"):
                        device[key] = smi.get(key)
            return native_devices
        except Exception:
            pass
    return smi_devices


def get_device_info(device_id: int) -> dict[str, Any]:
    native = _native()
    if native is not None:
        return dict(native.get_device_info(device_id))
    for device in list_devices():
        if device["device_id"] == device_id:
            return device
    raise RuntimeError(f"CUDA device {device_id} is not visible to glass_cuda")


def host_pinned_empty_f32(height: int, width: int) -> np.ndarray:
    native = _native()
    if native is None or not hasattr(native, "host_pinned_empty_f32"):
        raise RuntimeError("native CUDA backend with host_pinned_empty_f32 is not available")
    return np.asarray(native.host_pinned_empty_f32(int(height), int(width)), dtype=np.float32)


def smoke_add_f32(a: Any, b: Any) -> np.ndarray:
    native = _native()
    if native is not None:
        return np.asarray(native.smoke_add_f32(a, b), dtype=np.float32)
    return np.asarray(a, dtype=np.float32) + np.asarray(b, dtype=np.float32)


def reduce_mean_tile_f32(tile: Any) -> float:
    native = _native()
    if native is not None:
        return float(native.reduce_mean_tile_f32(tile))
    return float(np.mean(np.asarray(tile, dtype=np.float32)))


def _policy_from_mapping(policy: Any) -> CalibrationPolicy:
    if isinstance(policy, CalibrationPolicy):
        return policy
    if hasattr(policy, "__dataclass_fields__"):
        return CalibrationPolicy(**asdict(policy))
    if isinstance(policy, dict):
        allowed = set(CalibrationPolicy.__dataclass_fields__.keys())
        return CalibrationPolicy(**{key: value for key, value in policy.items() if key in allowed})
    return CalibrationPolicy()


def _policy_payload(policy: Any | None) -> dict[str, Any] | None:
    if policy is None:
        return None
    if isinstance(policy, CalibrationPolicy):
        return asdict(policy)
    if hasattr(policy, "__dataclass_fields__"):
        return asdict(policy)
    if isinstance(policy, dict):
        return dict(policy)
    return asdict(_policy_from_mapping(policy))


def _as_f32_c(value: Any) -> np.ndarray:
    return np.ascontiguousarray(np.asarray(value, dtype=np.float32))


def calibrate_tile_f32(
    light: Any,
    bias: Any | None,
    dark: Any | None,
    flat: Any | None,
    light_exposure_s: float,
    dark_exposure_s: float | None,
    policy: Any | None = None,
) -> np.ndarray:
    native = _native()
    if native is not None:
        return np.asarray(
            native.calibrate_tile_f32(
                light,
                bias,
                dark,
                flat,
                light_exposure_s,
                dark_exposure_s,
                _policy_payload(policy),
            ),
            dtype=np.float32,
        )
    return calibrate_light(
        np.asarray(light, dtype=np.float32),
        None if bias is None else np.asarray(bias, dtype=np.float32),
        None if dark is None else np.asarray(dark, dtype=np.float32),
        None if flat is None else np.asarray(flat, dtype=np.float32),
        light_exposure_s,
        dark_exposure_s,
        _policy_from_mapping(policy),
    )


def integrate_accumulate_mean_tile_f32(
    frame_tile: Any,
    weight_tile: Any,
    sum_tile: Any,
    weight_sum_tile: Any,
) -> tuple[np.ndarray, np.ndarray]:
    native = _native()
    if native is not None and hasattr(native, "integrate_accumulate_mean_tile_f32"):
        sums, weight_sums = native.integrate_accumulate_mean_tile_f32(
            frame_tile, weight_tile, sum_tile, weight_sum_tile
        )
        return np.asarray(sums, dtype=np.float32), np.asarray(weight_sums, dtype=np.float32)
    frame = np.asarray(frame_tile, dtype=np.float32)
    weight = np.asarray(weight_tile, dtype=np.float32)
    sums = np.asarray(sum_tile, dtype=np.float32).copy()
    weight_sums = np.asarray(weight_sum_tile, dtype=np.float32).copy()
    sums += frame * weight
    weight_sums += weight
    return sums, weight_sums


def mean_stack_tiles_f32(stack: Any) -> np.ndarray:
    native = _native()
    if native is not None:
        return np.asarray(native.mean_stack_tiles_f32(stack), dtype=np.float32)
    return np.mean(np.asarray(stack, dtype=np.float32), axis=0).astype(np.float32)


def warp_translation_f32(data: Any, dx: float, dy: float, fill: float = 0.0) -> tuple[np.ndarray, np.ndarray]:
    native = _native()
    if native is not None:
        warped, coverage = native.warp_translation_f32(data, dx, dy, fill)
        return np.asarray(warped, dtype=np.float32), np.asarray(coverage, dtype=np.float32)
    image = np.asarray(data, dtype=np.float32)
    out = np.full_like(image, fill, dtype=np.float32)
    coverage = np.zeros_like(image, dtype=np.float32)
    ix = int(round(dx))
    iy = int(round(dy))
    h, w = image.shape
    src_x0 = max(0, -ix)
    src_x1 = min(w, w - ix)
    dst_x0 = max(0, ix)
    dst_x1 = min(w, w + ix)
    src_y0 = max(0, -iy)
    src_y1 = min(h, h - iy)
    dst_y0 = max(0, iy)
    dst_y1 = min(h, h + iy)
    if src_x0 < src_x1 and src_y0 < src_y1:
        out[dst_y0:dst_y1, dst_x0:dst_x1] = image[src_y0:src_y1, src_x0:src_x1]
        coverage[dst_y0:dst_y1, dst_x0:dst_x1] = 1.0
    return out, coverage


def warp_translation_bilinear_f32(data: Any, dx: float, dy: float, fill: float = 0.0) -> tuple[np.ndarray, np.ndarray]:
    native = _native()
    if native is not None and hasattr(native, "warp_translation_bilinear_f32"):
        warped, coverage = native.warp_translation_bilinear_f32(data, float(dx), float(dy), float(fill))
        return np.asarray(warped, dtype=np.float32), np.asarray(coverage, dtype=np.float32)

    image = np.asarray(data, dtype=np.float32)
    h, w = image.shape
    out = np.full_like(image, fill, dtype=np.float32)
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
            out[y, x] = top * (1.0 - ty) + bottom * ty
            coverage[y, x] = 1.0
    return out, coverage


def warp_matrix_bilinear_f32(data: Any, matrix: Any, fill: float = 0.0) -> tuple[np.ndarray, np.ndarray]:
    native = _native()
    if native is not None and hasattr(native, "warp_matrix_bilinear_f32"):
        warped, coverage = native.warp_matrix_bilinear_f32(data, matrix, float(fill))
        return np.asarray(warped, dtype=np.float32), np.asarray(coverage, dtype=np.float32)

    image = np.asarray(data, dtype=np.float32)
    transform = np.asarray(matrix, dtype=np.float64)
    if transform.shape != (3, 3):
        raise ValueError(f"matrix must have shape (3, 3), got {transform.shape}")
    inverse = np.linalg.inv(transform)
    h, w = image.shape
    out = np.full_like(image, fill, dtype=np.float32)
    coverage = np.zeros_like(image, dtype=np.float32)
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
            out[y, x] = top * (1.0 - ty) + bottom * ty
            coverage[y, x] = 1.0
    return out, coverage


def _sinc(value: float) -> float:
    if abs(value) < 1.0e-6:
        return 1.0
    pix = float(np.pi) * float(value)
    return float(np.sin(pix) / pix)


def _lanczos3_weight(value: float) -> float:
    if abs(value) >= 3.0:
        return 0.0
    return _sinc(value) * _sinc(value / 3.0)


def warp_matrix_lanczos3_f32(
    data: Any,
    matrix: Any,
    fill: float = np.nan,
    clamping_threshold: float = -1.0,
) -> tuple[np.ndarray, np.ndarray]:
    native = _native()
    if native is not None and hasattr(native, "warp_matrix_lanczos3_f32"):
        warped, coverage = native.warp_matrix_lanczos3_f32(
            data,
            matrix,
            float(fill),
            float(clamping_threshold),
        )
        return np.asarray(warped, dtype=np.float32), np.asarray(coverage, dtype=np.float32)

    image = np.asarray(data, dtype=np.float32)
    transform = np.asarray(matrix, dtype=np.float64)
    if transform.shape != (3, 3):
        raise ValueError(f"matrix must have shape (3, 3), got {transform.shape}")
    inverse = np.linalg.inv(transform)
    h, w = image.shape
    out = np.full_like(image, fill, dtype=np.float32)
    coverage = np.zeros_like(image, dtype=np.float32)
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
            local_values: list[float] = []
            for yy in range(y0 - 2, y0 + 4):
                wy = _lanczos3_weight(sy - float(yy))
                for xx in range(x0 - 2, x0 + 4):
                    value = float(image[yy, xx])
                    if not np.isfinite(value):
                        continue
                    weight = wy * _lanczos3_weight(sx - float(xx))
                    weighted_sum += value * weight
                    weight_sum += weight
                    local_values.append(value)
            if abs(weight_sum) <= 1.0e-12:
                continue
            value = weighted_sum / weight_sum
            if clamping_threshold >= 0.0 and local_values:
                local_min = min(local_values)
                local_max = max(local_values)
                local_range = local_max - local_min
                value = min(
                    local_max + float(clamping_threshold) * local_range,
                    max(local_min - float(clamping_threshold) * local_range, value),
                )
            out[y, x] = np.float32(value)
            coverage[y, x] = 1.0
    return out, coverage


def matrix_alignment_metrics_f32(
    reference: Any,
    moving: Any,
    matrix: Any,
    sample_stride: int = 1,
) -> dict[str, Any]:
    """Score a moving-to-reference transform with GPU pixel metrics when available."""

    if sample_stride <= 0:
        raise ValueError("sample_stride must be positive")
    native = _native()
    if native is not None and hasattr(native, "matrix_alignment_metrics_f32"):
        result = dict(native.matrix_alignment_metrics_f32(reference, moving, matrix, int(sample_stride)))
        return {
            "valid_pixels": int(result["valid_pixels"]),
            "sampled_pixels": int(result["sampled_pixels"]),
            "sample_stride": int(result["sample_stride"]),
            "rms": float(result["rms"]),
            "mean_abs_diff": float(result["mean_abs_diff"]),
            "ncc": float(result["ncc"]),
            "model": str(result.get("model", "matrix_alignment_metrics_cuda")),
        }

    ref = np.asarray(reference, dtype=np.float32)
    mov = np.asarray(moving, dtype=np.float32)
    if ref.shape != mov.shape:
        raise ValueError("reference and moving must have the same shape")
    warped, coverage = warp_matrix_bilinear_f32(mov, matrix, 0.0)
    stride = max(1, int(sample_stride))
    ref_sample = ref[::stride, ::stride].astype(np.float64, copy=False)
    warped_sample = warped[::stride, ::stride].astype(np.float64, copy=False)
    coverage_sample = coverage[::stride, ::stride] > 0.0
    valid = coverage_sample & np.isfinite(ref_sample) & np.isfinite(warped_sample)
    valid_pixels = int(np.sum(valid))
    sampled_pixels = int(ref_sample.size)
    if valid_pixels == 0:
        rms = float("nan")
        mean_abs_diff = float("nan")
        ncc = float("nan")
    else:
        ref_valid = ref_sample[valid]
        warped_valid = warped_sample[valid]
        diff = warped_valid - ref_valid
        rms = float(np.sqrt(np.mean(diff * diff)))
        mean_abs_diff = float(np.mean(np.abs(diff)))
        if valid_pixels <= 1:
            ncc = float("nan")
        else:
            ref_centered = ref_valid - float(np.mean(ref_valid))
            warped_centered = warped_valid - float(np.mean(warped_valid))
            denom = float(np.sqrt(np.sum(ref_centered * ref_centered) * np.sum(warped_centered * warped_centered)))
            ncc = float(np.sum(ref_centered * warped_centered) / denom) if denom > 0.0 else float("nan")
    return {
        "valid_pixels": valid_pixels,
        "sampled_pixels": sampled_pixels,
        "sample_stride": stride,
        "rms": rms,
        "mean_abs_diff": mean_abs_diff,
        "ncc": ncc,
        "model": "matrix_alignment_metrics_cpu_fallback",
    }


def refine_matrix_translation_with_metrics_f32(
    reference: Any,
    moving: Any,
    matrix: Any,
    search_radius_px: float = 1.0,
    coarse_step_px: float = 0.25,
    fine_radius_px: float = 0.25,
    fine_step_px: float = 0.0625,
    coarse_sample_stride: int = 4,
    final_sample_stride: int = 1,
) -> dict[str, Any]:
    """Refine matrix translation terms with a native CUDA candidate grid when available."""

    if search_radius_px < 0.0:
        raise ValueError("search_radius_px must be non-negative")
    if coarse_step_px <= 0.0:
        raise ValueError("coarse_step_px must be positive")
    if fine_radius_px < 0.0:
        raise ValueError("fine_radius_px must be non-negative")
    if fine_step_px <= 0.0:
        raise ValueError("fine_step_px must be positive")
    if coarse_sample_stride <= 0 or final_sample_stride <= 0:
        raise ValueError("sample strides must be positive")

    native = _native()
    if native is not None and hasattr(native, "refine_matrix_translation_with_metrics_f32"):
        result = dict(
            native.refine_matrix_translation_with_metrics_f32(
                reference,
                moving,
                matrix,
                float(search_radius_px),
                float(coarse_step_px),
                float(fine_radius_px),
                float(fine_step_px),
                int(coarse_sample_stride),
                int(final_sample_stride),
            )
        )
        result["matrix"] = np.asarray(result["matrix"], dtype=np.float32).tolist()
        result["dx_correction"] = float(result["dx_correction"])
        result["dy_correction"] = float(result["dy_correction"])
        result["metrics"] = dict(result["metrics"])
        result["coarse_candidates"] = int(result["coarse_candidates"])
        result["fine_candidates"] = int(result["fine_candidates"])
        result["search_radius_px"] = float(result["search_radius_px"])
        result["coarse_step_px"] = float(result["coarse_step_px"])
        result["fine_radius_px"] = float(result["fine_radius_px"])
        result["fine_step_px"] = float(result["fine_step_px"])
        result["coarse_sample_stride"] = int(result["coarse_sample_stride"])
        result["final_sample_stride"] = int(result["final_sample_stride"])
        result["model"] = str(result.get("model", "cuda_matrix_metric_translation_refine_grid"))
        return result

    base = np.asarray(matrix, dtype=np.float32).reshape(3, 3)

    def score(dx: float, dy: float, stride: int) -> tuple[tuple[float, float], dict[str, Any], np.ndarray]:
        candidate = np.array(base, copy=True)
        candidate[0, 2] += np.float32(dx)
        candidate[1, 2] += np.float32(dy)
        metrics = matrix_alignment_metrics_f32(reference, moving, candidate, sample_stride=int(stride))
        return (float(metrics["rms"]), -float(metrics["ncc"])), metrics, candidate

    coarse_offsets = np.arange(
        -float(search_radius_px),
        float(search_radius_px) + float(coarse_step_px) * 0.5,
        float(coarse_step_px),
        dtype=np.float32,
    )
    best_key: tuple[float, float] | None = None
    best_dx = 0.0
    best_dy = 0.0
    best_metrics: dict[str, Any] | None = None
    best_matrix = np.array(base, copy=True)
    coarse_candidates = 0
    for dx in coarse_offsets:
        for dy in coarse_offsets:
            key, metrics, candidate = score(float(dx), float(dy), coarse_sample_stride)
            coarse_candidates += 1
            if best_key is None or key < best_key:
                best_key = key
                best_dx = float(dx)
                best_dy = float(dy)
                best_metrics = metrics
                best_matrix = candidate

    fine_candidates = 0
    if fine_radius_px > 0.0:
        fine_x = np.arange(
            best_dx - float(fine_radius_px),
            best_dx + float(fine_radius_px) + float(fine_step_px) * 0.5,
            float(fine_step_px),
            dtype=np.float32,
        )
        fine_y = np.arange(
            best_dy - float(fine_radius_px),
            best_dy + float(fine_radius_px) + float(fine_step_px) * 0.5,
            float(fine_step_px),
            dtype=np.float32,
        )
        best_key = None
        for dx in fine_x:
            for dy in fine_y:
                key, metrics, candidate = score(float(dx), float(dy), final_sample_stride)
                fine_candidates += 1
                if best_key is None or key < best_key:
                    best_key = key
                    best_dx = float(dx)
                    best_dy = float(dy)
                    best_metrics = metrics
                    best_matrix = candidate
    elif final_sample_stride != coarse_sample_stride:
        _key, best_metrics, best_matrix = score(best_dx, best_dy, final_sample_stride)

    assert best_metrics is not None
    return {
        "matrix": best_matrix.astype(np.float32).tolist(),
        "dx_correction": best_dx,
        "dy_correction": best_dy,
        "metrics": best_metrics,
        "coarse_candidates": coarse_candidates,
        "fine_candidates": fine_candidates,
        "search_radius_px": float(search_radius_px),
        "coarse_step_px": float(coarse_step_px),
        "fine_radius_px": float(fine_radius_px),
        "fine_step_px": float(fine_step_px),
        "coarse_sample_stride": int(coarse_sample_stride),
        "final_sample_stride": int(final_sample_stride),
        "model": "cuda_matrix_metric_translation_refine_loop_fallback",
    }


def refine_matrix_translation_candidates_with_metrics_f32(
    reference: Any,
    moving: Any,
    matrices: Any,
    search_radius_px: float = 1.0,
    coarse_step_px: float = 0.25,
    fine_radius_px: float = 0.25,
    fine_step_px: float = 0.0625,
    coarse_sample_stride: int = 4,
    final_sample_stride: int = 1,
) -> dict[str, Any]:
    """Refine multiple seed matrices while uploading image data only once when native CUDA is available."""

    if search_radius_px < 0.0:
        raise ValueError("search_radius_px must be non-negative")
    if coarse_step_px <= 0.0:
        raise ValueError("coarse_step_px must be positive")
    if fine_radius_px < 0.0:
        raise ValueError("fine_radius_px must be non-negative")
    if fine_step_px <= 0.0:
        raise ValueError("fine_step_px must be positive")
    if coarse_sample_stride <= 0 or final_sample_stride <= 0:
        raise ValueError("sample strides must be positive")
    matrix_array = np.asarray(matrices, dtype=np.float32)
    if matrix_array.shape == (3, 3):
        matrix_array = matrix_array.reshape(1, 3, 3)
    if matrix_array.ndim != 3 or matrix_array.shape[1:] != (3, 3):
        raise ValueError("matrices must have shape (N, 3, 3) or (3, 3)")
    if matrix_array.shape[0] == 0:
        raise ValueError("matrices must contain at least one matrix")

    native = _native()
    if native is not None and hasattr(native, "refine_matrix_translation_candidates_with_metrics_f32"):
        result = dict(
            native.refine_matrix_translation_candidates_with_metrics_f32(
                reference,
                moving,
                np.ascontiguousarray(matrix_array, dtype=np.float32),
                float(search_radius_px),
                float(coarse_step_px),
                float(fine_radius_px),
                float(fine_step_px),
                int(coarse_sample_stride),
                int(final_sample_stride),
            )
        )
        seed_results = []
        for seed in list(result.get("seed_results", [])):
            seed_result = dict(seed)
            seed_result["seed_index"] = int(seed_result["seed_index"])
            seed_result["matrix"] = np.asarray(seed_result["matrix"], dtype=np.float32).tolist()
            seed_result["dx_correction"] = float(seed_result["dx_correction"])
            seed_result["dy_correction"] = float(seed_result["dy_correction"])
            seed_result["metrics"] = dict(seed_result["metrics"])
            seed_result["coarse_candidates"] = int(seed_result["coarse_candidates"])
            seed_result["fine_candidates"] = int(seed_result["fine_candidates"])
            seed_results.append(seed_result)
        return {
            "matrix": np.asarray(result["matrix"], dtype=np.float32).tolist(),
            "dx_correction": float(result["dx_correction"]),
            "dy_correction": float(result["dy_correction"]),
            "metrics": dict(result["metrics"]),
            "selected_index": int(result["selected_index"]),
            "seed_count": int(result["seed_count"]),
            "seed_results": seed_results,
            "coarse_candidates_per_seed": int(result["coarse_candidates_per_seed"]),
            "search_radius_px": float(result["search_radius_px"]),
            "coarse_step_px": float(result["coarse_step_px"]),
            "fine_radius_px": float(result["fine_radius_px"]),
            "fine_step_px": float(result["fine_step_px"]),
            "coarse_sample_stride": int(result["coarse_sample_stride"]),
            "final_sample_stride": int(result["final_sample_stride"]),
            "model": str(result.get("model", "cuda_matrix_metric_translation_multi_seed_refine_grid")),
        }

    best_key: tuple[float, float] | None = None
    best_result: dict[str, Any] | None = None
    seed_results: list[dict[str, Any]] = []
    for seed_index, seed_matrix in enumerate(matrix_array):
        result = refine_matrix_translation_with_metrics_f32(
            reference,
            moving,
            seed_matrix,
            search_radius_px=search_radius_px,
            coarse_step_px=coarse_step_px,
            fine_radius_px=fine_radius_px,
            fine_step_px=fine_step_px,
            coarse_sample_stride=coarse_sample_stride,
            final_sample_stride=final_sample_stride,
        )
        metrics = dict(result["metrics"])
        rms = float(metrics.get("rms", float("inf")))
        ncc = float(metrics.get("ncc", float("-inf")))
        key = (rms if np.isfinite(rms) else float("inf"), -ncc if np.isfinite(ncc) else float("inf"))
        seed_result = {
            "seed_index": int(seed_index),
            "matrix": result["matrix"],
            "dx_correction": float(result["dx_correction"]),
            "dy_correction": float(result["dy_correction"]),
            "metrics": metrics,
            "coarse_candidates": int(result["coarse_candidates"]),
            "fine_candidates": int(result["fine_candidates"]),
        }
        seed_results.append(seed_result)
        if best_key is None or key < best_key:
            best_key = key
            best_result = {**result, "selected_index": int(seed_index)}
    assert best_result is not None
    return {
        "matrix": best_result["matrix"],
        "dx_correction": float(best_result["dx_correction"]),
        "dy_correction": float(best_result["dy_correction"]),
        "metrics": dict(best_result["metrics"]),
        "selected_index": int(best_result["selected_index"]),
        "seed_count": int(matrix_array.shape[0]),
        "seed_results": seed_results,
        "coarse_candidates_per_seed": int(seed_results[0]["coarse_candidates"]),
        "search_radius_px": float(search_radius_px),
        "coarse_step_px": float(coarse_step_px),
        "fine_radius_px": float(fine_radius_px),
        "fine_step_px": float(fine_step_px),
        "coarse_sample_stride": int(coarse_sample_stride),
        "final_sample_stride": int(final_sample_stride),
        "model": "cuda_matrix_metric_translation_multi_seed_refine_loop_fallback",
    }


def _translation_ncc_score(
    reference: np.ndarray,
    moving: np.ndarray,
    dx: int,
    dy: int,
    sample_stride: int = 1,
) -> float:
    h, w = reference.shape
    src_x0 = max(0, -dx)
    src_x1 = min(w, w - dx)
    dst_x0 = max(0, dx)
    dst_x1 = min(w, w + dx)
    src_y0 = max(0, -dy)
    src_y1 = min(h, h - dy)
    dst_y0 = max(0, dy)
    dst_y1 = min(h, h + dy)
    if src_x0 >= src_x1 or src_y0 >= src_y1:
        return float("-inf")
    ref = reference[dst_y0:dst_y1, dst_x0:dst_x1].astype(np.float64, copy=False)
    mov = moving[src_y0:src_y1, src_x0:src_x1].astype(np.float64, copy=False)
    stride = max(1, int(sample_stride))
    if stride > 1:
        ref = ref[::stride, ::stride]
        mov = mov[::stride, ::stride]
    valid = np.isfinite(ref) & np.isfinite(mov)
    if int(np.sum(valid)) <= 1:
        return float("-inf")
    ref = ref[valid]
    mov = mov[valid]
    ref = ref - float(np.mean(ref))
    mov = mov - float(np.mean(mov))
    denom = float(np.sqrt(np.sum(ref * ref) * np.sum(mov * mov)))
    if denom <= 0.0:
        return float("-inf")
    return float(np.sum(ref * mov) / denom)


def estimate_translation_search_f32(
    reference: Any,
    moving: Any,
    max_shift_x: int,
    max_shift_y: int | None = None,
    sample_stride: int = 1,
) -> dict[str, Any]:
    """Estimate an integer translation that warps ``moving`` onto ``reference``.

    The native CUDA path scores every integer shift with normalized cross-correlation
    and selects the best candidate on device. The CPU fallback is intentionally small
    and exists only to keep the API importable on CPU-only machines.
    """

    if max_shift_y is None:
        max_shift_y = max_shift_x
    if sample_stride <= 0:
        raise ValueError("sample_stride must be positive")
    native = _native()
    if native is not None and hasattr(native, "estimate_translation_search_f32"):
        result = dict(
            native.estimate_translation_search_f32(
                reference,
                moving,
                int(max_shift_x),
                int(max_shift_y),
                int(sample_stride),
            )
        )
        return {
            "dx": int(result["dx"]),
            "dy": int(result["dy"]),
            "score": float(result["score"]),
            "search_count": int(result["search_count"]),
            "sample_stride": int(result.get("sample_stride", sample_stride)),
            "model": str(result.get("model", "translation_integer_ncc")),
        }

    ref = np.asarray(reference, dtype=np.float32)
    mov = np.asarray(moving, dtype=np.float32)
    if ref.shape != mov.shape:
        raise ValueError(f"shape mismatch for registration: {ref.shape} != {mov.shape}")
    best_dx = 0
    best_dy = 0
    best_score = float("-inf")
    search_count = 0
    for dy in range(-int(max_shift_y), int(max_shift_y) + 1):
        for dx in range(-int(max_shift_x), int(max_shift_x) + 1):
            score = _translation_ncc_score(ref, mov, dx, dy, sample_stride)
            search_count += 1
            if score > best_score:
                best_dx = dx
                best_dy = dy
                best_score = score
    return {
        "dx": best_dx,
        "dy": best_dy,
        "score": best_score,
        "search_count": search_count,
        "sample_stride": int(sample_stride),
        "model": "translation_integer_ncc_cpu_fallback",
    }


def _translation_bilinear_ncc_score(
    reference: np.ndarray,
    moving: np.ndarray,
    dx: float,
    dy: float,
    sample_stride: int = 1,
) -> float:
    h, w = reference.shape
    ref_values: list[float] = []
    mov_values: list[float] = []
    stride = max(1, int(sample_stride))
    for y in range(0, h, stride):
        sy = float(y) - float(dy)
        if sy < 0.0 or sy > float(h - 1):
            continue
        y0 = int(np.floor(sy))
        y1 = min(y0 + 1, h - 1)
        ty = np.float32(sy - y0)
        for x in range(0, w, stride):
            sx = float(x) - float(dx)
            if sx < 0.0 or sx > float(w - 1):
                continue
            x0 = int(np.floor(sx))
            x1 = min(x0 + 1, w - 1)
            tx = np.float32(sx - x0)
            top = moving[y0, x0] * (1.0 - tx) + moving[y0, x1] * tx
            bottom = moving[y1, x0] * (1.0 - tx) + moving[y1, x1] * tx
            r = float(reference[y, x])
            m = float(top * (1.0 - ty) + bottom * ty)
            if np.isfinite(r) and np.isfinite(m):
                ref_values.append(r)
                mov_values.append(m)
    if len(ref_values) <= 1:
        return float("-inf")
    ref = np.asarray(ref_values, dtype=np.float64)
    mov = np.asarray(mov_values, dtype=np.float64)
    ref = ref - float(np.mean(ref))
    mov = mov - float(np.mean(mov))
    denom = float(np.sqrt(np.sum(ref * ref) * np.sum(mov * mov)))
    if denom <= 0.0:
        return float("-inf")
    return float(np.sum(ref * mov) / denom)


def estimate_translation_subpixel_ncc_f32(
    reference: Any,
    moving: Any,
    center_dx: float,
    center_dy: float,
    radius_steps: int,
    step: float,
    sample_stride: int = 1,
) -> dict[str, Any]:
    if sample_stride <= 0:
        raise ValueError("sample_stride must be positive")
    native = _native()
    if native is not None and hasattr(native, "estimate_translation_subpixel_ncc_f32"):
        result = dict(
            native.estimate_translation_subpixel_ncc_f32(
                reference,
                moving,
                float(center_dx),
                float(center_dy),
                int(radius_steps),
                float(step),
                int(sample_stride),
            )
        )
        return {
            "dx": float(result["dx"]),
            "dy": float(result["dy"]),
            "score": float(result["score"]),
            "candidate_count": int(result["candidate_count"]),
            "center_dx": float(result["center_dx"]),
            "center_dy": float(result["center_dy"]),
            "radius_steps": int(result["radius_steps"]),
            "step": float(result["step"]),
            "sample_stride": int(result.get("sample_stride", sample_stride)),
            "model": str(result.get("model", "translation_subpixel_ncc")),
        }

    if radius_steps < 0:
        raise ValueError("radius_steps must be non-negative")
    if step <= 0.0:
        raise ValueError("step must be positive")
    ref = np.asarray(reference, dtype=np.float32)
    mov = np.asarray(moving, dtype=np.float32)
    if ref.shape != mov.shape:
        raise ValueError(f"shape mismatch for registration: {ref.shape} != {mov.shape}")
    best_dx = float(center_dx)
    best_dy = float(center_dy)
    best_score = float("-inf")
    candidate_count = 0
    for oy in range(-int(radius_steps), int(radius_steps) + 1):
        for ox in range(-int(radius_steps), int(radius_steps) + 1):
            dx = float(center_dx) + ox * float(step)
            dy = float(center_dy) + oy * float(step)
            score = _translation_bilinear_ncc_score(ref, mov, dx, dy, sample_stride)
            candidate_count += 1
            if score > best_score:
                best_dx = dx
                best_dy = dy
                best_score = score
    return {
        "dx": best_dx,
        "dy": best_dy,
        "score": best_score,
        "candidate_count": candidate_count,
        "center_dx": float(center_dx),
        "center_dy": float(center_dy),
        "radius_steps": int(radius_steps),
        "step": float(step),
        "sample_stride": int(sample_stride),
        "model": "translation_subpixel_ncc_cpu_fallback",
    }


def _catalog_translation_vote(
    reference_x: np.ndarray,
    reference_y: np.ndarray,
    moving_x: np.ndarray,
    moving_y: np.ndarray,
    tolerance_px: float,
    max_abs_dx: float | None = None,
    max_abs_dy: float | None = None,
    prior_dx: float | None = None,
    prior_dy: float | None = None,
    prior_radius_px: float | None = None,
) -> dict[str, Any]:
    ref_x = np.asarray(reference_x, dtype=np.float32).reshape(-1)
    ref_y = np.asarray(reference_y, dtype=np.float32).reshape(-1)
    mov_x = np.asarray(moving_x, dtype=np.float32).reshape(-1)
    mov_y = np.asarray(moving_y, dtype=np.float32).reshape(-1)
    if ref_x.shape != ref_y.shape or mov_x.shape != mov_y.shape:
        raise ValueError("catalog x/y coordinate arrays must have matching shapes")
    if len(ref_x) == 0 or len(mov_x) == 0:
        raise ValueError("catalogs must be non-empty")
    dx = (ref_x[:, None] - mov_x[None, :]).reshape(-1)
    dy = (ref_y[:, None] - mov_y[None, :]).reshape(-1)
    if max_abs_dx is not None:
        max_abs_dx = float(max_abs_dx)
    if max_abs_dy is None:
        max_abs_dy = max_abs_dx
    else:
        max_abs_dy = float(max_abs_dy)
    valid_candidates = np.ones(dx.shape, dtype=bool)
    if max_abs_dx is not None and max_abs_dx >= 0.0:
        valid_candidates &= np.abs(dx) <= np.float32(max_abs_dx)
    if max_abs_dy is not None and max_abs_dy >= 0.0:
        valid_candidates &= np.abs(dy) <= np.float32(max_abs_dy)
    if prior_radius_px is not None and prior_radius_px >= 0.0:
        if prior_dx is None or prior_dy is None:
            raise ValueError("prior_dx and prior_dy are required when prior_radius_px is set")
        valid_candidates &= (dx - np.float32(prior_dx)) ** 2 + (dy - np.float32(prior_dy)) ** 2 <= np.float32(
            prior_radius_px
        ) ** 2
    tolerance2 = np.float32(tolerance_px) * np.float32(tolerance_px)
    best_index = 0
    best_score = -1
    for i, (candidate_dx, candidate_dy) in enumerate(zip(dx, dy, strict=True)):
        if not valid_candidates[i]:
            continue
        ddx = dx - candidate_dx
        ddy = dy - candidate_dy
        score = int(np.sum(valid_candidates & ((ddx * ddx + ddy * ddy) <= tolerance2)))
        if score > best_score:
            best_index = i
            best_score = score
    if best_score < 0:
        return {
            "dx": 0.0,
            "dy": 0.0,
            "inliers": 0,
            "refined_dx": 0.0,
            "refined_dy": 0.0,
            "mutual_inliers": 0,
            "rms_px": float("nan"),
            "candidate_count": int(len(dx)),
            "reference_count": int(len(ref_x)),
            "moving_count": int(len(mov_x)),
            "tolerance_px": float(tolerance_px),
            "max_abs_dx": None if max_abs_dx is None else float(max_abs_dx),
            "max_abs_dy": None if max_abs_dy is None else float(max_abs_dy),
            "prior_dx": None if prior_dx is None else float(prior_dx),
            "prior_dy": None if prior_dy is None else float(prior_dy),
            "prior_radius_px": None if prior_radius_px is None else float(prior_radius_px),
            "model": "catalog_pair_offset_translation_cpu_fallback",
        }
    refined = _refine_catalog_translation(ref_x, ref_y, mov_x, mov_y, float(dx[best_index]), float(dy[best_index]), tolerance_px)
    return {
        "dx": float(dx[best_index]),
        "dy": float(dy[best_index]),
        "inliers": int(best_score),
        **refined,
        "candidate_count": int(len(dx)),
        "reference_count": int(len(ref_x)),
        "moving_count": int(len(mov_x)),
        "tolerance_px": float(tolerance_px),
        "max_abs_dx": None if max_abs_dx is None else float(max_abs_dx),
        "max_abs_dy": None if max_abs_dy is None else float(max_abs_dy),
        "prior_dx": None if prior_dx is None else float(prior_dx),
        "prior_dy": None if prior_dy is None else float(prior_dy),
        "prior_radius_px": None if prior_radius_px is None else float(prior_radius_px),
        "model": "catalog_pair_offset_translation_cpu_fallback",
    }


def _refine_catalog_translation(
    reference_x: np.ndarray,
    reference_y: np.ndarray,
    moving_x: np.ndarray,
    moving_y: np.ndarray,
    dx: float,
    dy: float,
    tolerance_px: float,
) -> dict[str, Any]:
    tolerance2 = float(tolerance_px) * float(tolerance_px)
    moving_best_reference: list[int] = []
    for mx, my in zip(moving_x, moving_y, strict=True):
        tx = float(mx) + dx
        ty = float(my) + dy
        distances = (reference_x - tx) ** 2 + (reference_y - ty) ** 2
        index = int(np.argmin(distances))
        moving_best_reference.append(index if float(distances[index]) <= tolerance2 else -1)

    reference_best_moving: list[int] = []
    for rx, ry in zip(reference_x, reference_y, strict=True):
        tx = moving_x + np.float32(dx)
        ty = moving_y + np.float32(dy)
        distances = (tx - rx) ** 2 + (ty - ry) ** 2
        index = int(np.argmin(distances))
        reference_best_moving.append(index if float(distances[index]) <= tolerance2 else -1)

    deltas: list[tuple[float, float]] = []
    for moving_index, reference_index in enumerate(moving_best_reference):
        if reference_index < 0 or reference_best_moving[reference_index] != moving_index:
            continue
        deltas.append(
            (
                float(reference_x[reference_index] - moving_x[moving_index]),
                float(reference_y[reference_index] - moving_y[moving_index]),
            )
        )
    if not deltas:
        return {
            "refined_dx": float(dx),
            "refined_dy": float(dy),
            "mutual_inliers": 0,
            "rms_px": float("nan"),
        }
    delta_array = np.asarray(deltas, dtype=np.float32)
    refined_dx = float(np.mean(delta_array[:, 0]))
    refined_dy = float(np.mean(delta_array[:, 1]))
    residuals = delta_array - np.asarray([refined_dx, refined_dy], dtype=np.float32)
    rms_px = float(np.sqrt(np.mean(np.sum(residuals * residuals, axis=1))))
    return {
        "refined_dx": refined_dx,
        "refined_dy": refined_dy,
        "mutual_inliers": len(deltas),
        "rms_px": rms_px,
    }


def estimate_translation_from_catalogs_f32(
    reference_x: Any,
    reference_y: Any,
    moving_x: Any,
    moving_y: Any,
    tolerance_px: float = 1.0,
    max_abs_dx: float | None = None,
    max_abs_dy: float | None = None,
    prior_dx: float | None = None,
    prior_dy: float | None = None,
    prior_radius_px: float | None = None,
) -> dict[str, Any]:
    """Estimate translation from two star coordinate catalogs.

    The CUDA path forms all reference/moving pair offsets, scores each offset
    by nearby pair-offset votes, and returns the highest-vote translation.
    """

    native_max_abs_dx = -1.0 if max_abs_dx is None else float(max_abs_dx)
    native_max_abs_dy = -1.0 if max_abs_dy is None else float(max_abs_dy)
    native_prior_dx = 0.0 if prior_dx is None else float(prior_dx)
    native_prior_dy = 0.0 if prior_dy is None else float(prior_dy)
    native_prior_radius_px = -1.0 if prior_radius_px is None else float(prior_radius_px)
    native = _native()
    if native is not None and hasattr(native, "estimate_translation_from_catalogs_f32"):
        result = dict(
            native.estimate_translation_from_catalogs_f32(
                np.ascontiguousarray(np.asarray(reference_x, dtype=np.float32).reshape(-1)),
                np.ascontiguousarray(np.asarray(reference_y, dtype=np.float32).reshape(-1)),
                np.ascontiguousarray(np.asarray(moving_x, dtype=np.float32).reshape(-1)),
                np.ascontiguousarray(np.asarray(moving_y, dtype=np.float32).reshape(-1)),
                float(tolerance_px),
                native_max_abs_dx,
                native_max_abs_dy,
                native_prior_dx,
                native_prior_dy,
                native_prior_radius_px,
            )
        )
        return {
            "dx": float(result["dx"]),
            "dy": float(result["dy"]),
            "inliers": int(result["inliers"]),
            "refined_dx": float(result["refined_dx"]),
            "refined_dy": float(result["refined_dy"]),
            "mutual_inliers": int(result["mutual_inliers"]),
            "rms_px": float(result["rms_px"]),
            "candidate_count": int(result["candidate_count"]),
            "reference_count": int(result["reference_count"]),
            "moving_count": int(result["moving_count"]),
            "tolerance_px": float(result["tolerance_px"]),
            "max_abs_dx": float(result["max_abs_dx"]),
            "max_abs_dy": float(result["max_abs_dy"]),
            "prior_dx": float(result["prior_dx"]),
            "prior_dy": float(result["prior_dy"]),
            "prior_radius_px": float(result["prior_radius_px"]),
            "model": str(result.get("model", "catalog_pair_offset_translation")),
        }

    return _catalog_translation_vote(
        np.asarray(reference_x, dtype=np.float32),
        np.asarray(reference_y, dtype=np.float32),
        np.asarray(moving_x, dtype=np.float32),
        np.asarray(moving_y, dtype=np.float32),
        tolerance_px,
        max_abs_dx,
        max_abs_dy,
        prior_dx,
        prior_dy,
        prior_radius_px,
    )


def _similarity_from_pairs_cpu(
    reference_x: Any,
    reference_y: Any,
    moving_x: Any,
    moving_y: Any,
) -> dict[str, Any]:
    ref_x = np.asarray(reference_x, dtype=np.float64).reshape(-1)
    ref_y = np.asarray(reference_y, dtype=np.float64).reshape(-1)
    mov_x = np.asarray(moving_x, dtype=np.float64).reshape(-1)
    mov_y = np.asarray(moving_y, dtype=np.float64).reshape(-1)
    if ref_x.shape != ref_y.shape or ref_x.shape != mov_x.shape or ref_x.shape != mov_y.shape:
        raise ValueError("matched coordinate arrays must have matching shapes")
    finite = np.isfinite(ref_x) & np.isfinite(ref_y) & np.isfinite(mov_x) & np.isfinite(mov_y)
    ref_x = ref_x[finite]
    ref_y = ref_y[finite]
    mov_x = mov_x[finite]
    mov_y = mov_y[finite]
    input_pairs = int(np.asarray(reference_x).reshape(-1).size)
    valid_pairs = int(ref_x.size)
    identity = np.eye(3, dtype=np.float32)
    if valid_pairs < 2:
        return {
            "matrix": identity.tolist(),
            "scale": 1.0,
            "rotation_rad": 0.0,
            "rms_px": float("nan"),
            "valid_pairs": valid_pairs,
            "input_pairs": input_pairs,
            "status": "failed",
            "status_code": 1,
            "model": "matched_pair_similarity_cpu_fallback",
        }

    mean_mx = float(np.mean(mov_x))
    mean_my = float(np.mean(mov_y))
    mean_rx = float(np.mean(ref_x))
    mean_ry = float(np.mean(ref_y))
    cx = mov_x - mean_mx
    cy = mov_y - mean_my
    ux = ref_x - mean_rx
    uy = ref_y - mean_ry
    denominator = float(np.sum(cx * cx + cy * cy))
    if denominator <= 1.0e-20:
        return {
            "matrix": identity.tolist(),
            "scale": 1.0,
            "rotation_rad": 0.0,
            "rms_px": float("nan"),
            "valid_pairs": valid_pairs,
            "input_pairs": input_pairs,
            "status": "failed",
            "status_code": 2,
            "model": "matched_pair_similarity_cpu_fallback",
        }
    a = float(np.sum(cx * ux + cy * uy) / denominator)
    b = float(np.sum(cx * uy - cy * ux) / denominator)
    tx = mean_rx - (a * mean_mx - b * mean_my)
    ty = mean_ry - (b * mean_mx + a * mean_my)
    matrix = np.asarray([[a, -b, tx], [b, a, ty], [0.0, 0.0, 1.0]], dtype=np.float32)
    transformed_x = a * mov_x - b * mov_y + tx
    transformed_y = b * mov_x + a * mov_y + ty
    residual = (transformed_x - ref_x) ** 2 + (transformed_y - ref_y) ** 2
    return {
        "matrix": matrix.tolist(),
        "scale": float(np.sqrt(a * a + b * b)),
        "rotation_rad": float(np.arctan2(b, a)),
        "rms_px": float(np.sqrt(np.mean(residual))),
        "valid_pairs": valid_pairs,
        "input_pairs": input_pairs,
        "status": "ok",
        "status_code": 0,
        "model": "matched_pair_similarity_cpu_fallback",
    }


def estimate_similarity_from_pairs_f32(
    reference_x: Any,
    reference_y: Any,
    moving_x: Any,
    moving_y: Any,
) -> dict[str, Any]:
    """Estimate a 2D similarity matrix from matched moving/reference star pairs.

    This primitive assumes the matching step has already produced one-to-one
    coordinate arrays. It fits the matrix that maps moving points onto reference
    points and is intended as a CUDA building block for future GPU star matching.
    """

    native = _native()
    if native is not None and hasattr(native, "estimate_similarity_from_pairs_f32"):
        result = dict(
            native.estimate_similarity_from_pairs_f32(
                np.ascontiguousarray(np.asarray(reference_x, dtype=np.float32).reshape(-1)),
                np.ascontiguousarray(np.asarray(reference_y, dtype=np.float32).reshape(-1)),
                np.ascontiguousarray(np.asarray(moving_x, dtype=np.float32).reshape(-1)),
                np.ascontiguousarray(np.asarray(moving_y, dtype=np.float32).reshape(-1)),
            )
        )
        return {
            "matrix": np.asarray(result["matrix"], dtype=np.float32).tolist(),
            "scale": float(result["scale"]),
            "rotation_rad": float(result["rotation_rad"]),
            "rms_px": float(result["rms_px"]),
            "valid_pairs": int(result["valid_pairs"]),
            "input_pairs": int(result["input_pairs"]),
            "status": str(result["status"]),
            "status_code": int(result["status_code"]),
            "model": str(result.get("model", "matched_pair_similarity_cuda")),
        }
    return _similarity_from_pairs_cpu(reference_x, reference_y, moving_x, moving_y)


def _similarity_matrix_from_two_pairs(
    reference_a: np.ndarray,
    reference_b: np.ndarray,
    moving_a: np.ndarray,
    moving_b: np.ndarray,
    min_pair_distance: float,
) -> np.ndarray | None:
    moving_vector = moving_b - moving_a
    reference_vector = reference_b - reference_a
    moving_distance2 = float(np.dot(moving_vector, moving_vector))
    reference_distance2 = float(np.dot(reference_vector, reference_vector))
    minimum = float(min_pair_distance) * float(min_pair_distance)
    if moving_distance2 <= minimum or reference_distance2 <= minimum:
        return None
    a = float(np.dot(moving_vector, reference_vector) / moving_distance2)
    b = float((moving_vector[0] * reference_vector[1] - moving_vector[1] * reference_vector[0]) / moving_distance2)
    tx = float(reference_a[0] - (a * moving_a[0] - b * moving_a[1]))
    ty = float(reference_a[1] - (b * moving_a[0] + a * moving_a[1]))
    return np.asarray([[a, -b, tx], [b, a, ty], [0.0, 0.0, 1.0]], dtype=np.float32)


def _score_similarity_catalog_matrix(
    matrix: np.ndarray,
    reference: np.ndarray,
    moving: np.ndarray,
    tolerance_px: float,
) -> tuple[int, float]:
    tolerance2 = float(tolerance_px) * float(tolerance_px)
    inliers = 0
    residual_sum = 0.0
    for point in moving:
        if not np.all(np.isfinite(point)):
            continue
        transformed = np.asarray(
            [
                matrix[0, 0] * point[0] + matrix[0, 1] * point[1] + matrix[0, 2],
                matrix[1, 0] * point[0] + matrix[1, 1] * point[1] + matrix[1, 2],
            ],
            dtype=np.float32,
        )
        finite_reference = reference[np.all(np.isfinite(reference), axis=1)]
        if finite_reference.size == 0:
            continue
        distances = np.sum((finite_reference - transformed) ** 2, axis=1)
        best = float(np.min(distances))
        if best <= tolerance2:
            inliers += 1
            residual_sum += best
    rms = float(np.sqrt(residual_sum / inliers)) if inliers else float("nan")
    return inliers, rms


def _similarity_from_catalogs_cpu(
    reference_x: Any,
    reference_y: Any,
    moving_x: Any,
    moving_y: Any,
    tolerance_px: float,
    min_pair_distance: float,
    prior_dx: float | None = None,
    prior_dy: float | None = None,
    prior_radius_px: float | None = None,
    min_scale: float | None = None,
    max_scale: float | None = None,
    max_abs_rotation_rad: float | None = None,
) -> dict[str, Any]:
    reference = np.column_stack(
        [np.asarray(reference_x, dtype=np.float32).reshape(-1), np.asarray(reference_y, dtype=np.float32).reshape(-1)]
    )
    moving = np.column_stack(
        [np.asarray(moving_x, dtype=np.float32).reshape(-1), np.asarray(moving_y, dtype=np.float32).reshape(-1)]
    )
    if len(reference) < 2 or len(moving) < 2:
        raise ValueError("similarity catalog estimation requires at least two stars per catalog")
    best_matrix = np.eye(3, dtype=np.float32)
    best_inliers = -1
    best_rms = float("inf")
    best_index = -1
    candidate_count = 0
    for reference_a_index, reference_a in enumerate(reference):
        for reference_b_index, reference_b in enumerate(reference):
            if reference_a_index == reference_b_index:
                continue
            for moving_a_index, moving_a in enumerate(moving):
                for moving_b_index, moving_b in enumerate(moving):
                    if moving_a_index == moving_b_index:
                        continue
                    candidate_count += 1
                    matrix = _similarity_matrix_from_two_pairs(
                        reference_a,
                        reference_b,
                        moving_a,
                        moving_b,
                        min_pair_distance,
                    )
                    if matrix is None:
                        continue
                    a = float(matrix[0, 0])
                    b = float(matrix[1, 0])
                    scale = float(np.sqrt(a * a + b * b))
                    rotation = float(np.arctan2(b, a))
                    if min_scale is not None and scale < float(min_scale):
                        continue
                    if max_scale is not None and scale > float(max_scale):
                        continue
                    if max_abs_rotation_rad is not None and abs(rotation) > float(max_abs_rotation_rad):
                        continue
                    if prior_radius_px is not None and prior_radius_px >= 0.0:
                        dx_error = float(matrix[0, 2]) - float(0.0 if prior_dx is None else prior_dx)
                        dy_error = float(matrix[1, 2]) - float(0.0 if prior_dy is None else prior_dy)
                        if dx_error * dx_error + dy_error * dy_error > float(prior_radius_px) ** 2:
                            continue
                    inliers, rms = _score_similarity_catalog_matrix(matrix, reference, moving, tolerance_px)
                    if inliers > best_inliers or (inliers == best_inliers and rms < best_rms):
                        best_matrix = matrix
                        best_inliers = inliers
                        best_rms = rms
                        best_index = candidate_count - 1
    a = float(best_matrix[0, 0])
    b = float(best_matrix[1, 0])
    return {
        "matrix": best_matrix.tolist(),
        "scale": float(np.sqrt(a * a + b * b)),
        "rotation_rad": float(np.arctan2(b, a)),
        "rms_px": best_rms if np.isfinite(best_rms) else float("nan"),
        "inliers": max(0, int(best_inliers)),
        "refined_inliers": max(0, int(best_inliers)),
        "refit_status": "not_run",
        "refit_status_code": -1,
        "refit_rms_px": best_rms if np.isfinite(best_rms) else float("nan"),
        "best_candidate_index": int(best_index),
        "candidate_count": int(candidate_count),
        "reference_count": int(len(reference)),
        "moving_count": int(len(moving)),
        "tolerance_px": float(tolerance_px),
        "min_pair_distance": float(min_pair_distance),
        "prior_dx": None if prior_dx is None else float(prior_dx),
        "prior_dy": None if prior_dy is None else float(prior_dy),
        "prior_radius_px": None if prior_radius_px is None else float(prior_radius_px),
        "min_scale": None if min_scale is None else float(min_scale),
        "max_scale": None if max_scale is None else float(max_scale),
        "max_abs_rotation_rad": None if max_abs_rotation_rad is None else float(max_abs_rotation_rad),
        "status": "ok" if best_inliers > 0 else "failed",
        "model": "catalog_pair_similarity_cpu_fallback",
    }


def estimate_similarity_from_catalogs_f32(
    reference_x: Any,
    reference_y: Any,
    moving_x: Any,
    moving_y: Any,
    tolerance_px: float = 2.0,
    min_pair_distance: float = 2.0,
    prior_dx: float | None = None,
    prior_dy: float | None = None,
    prior_radius_px: float | None = None,
    min_scale: float | None = None,
    max_scale: float | None = None,
    max_abs_rotation_rad: float | None = None,
    top_k: int = 0,
) -> dict[str, Any]:
    """Estimate a similarity transform directly from two bounded star catalogs.

    This is a clean-room, bounded brute-force seed matcher: it forms ordered
    two-star pair correspondences, fits a candidate similarity transform, scores
    transformed moving stars against the reference catalog, and returns the
    highest-inlier matrix. It is intended for compact GPU catalogs, not
    unbounded all-star lists.
    """

    native = _native()
    if native is not None and hasattr(native, "estimate_similarity_from_catalogs_f32"):
        result = dict(
            native.estimate_similarity_from_catalogs_f32(
                np.ascontiguousarray(np.asarray(reference_x, dtype=np.float32).reshape(-1)),
                np.ascontiguousarray(np.asarray(reference_y, dtype=np.float32).reshape(-1)),
                np.ascontiguousarray(np.asarray(moving_x, dtype=np.float32).reshape(-1)),
                np.ascontiguousarray(np.asarray(moving_y, dtype=np.float32).reshape(-1)),
                float(tolerance_px),
                float(min_pair_distance),
                float(0.0 if prior_dx is None else prior_dx),
                float(0.0 if prior_dy is None else prior_dy),
                float(-1.0 if prior_radius_px is None else prior_radius_px),
                float(0.0 if min_scale is None else min_scale),
                float(np.finfo(np.float32).max if max_scale is None else max_scale),
                float(-1.0 if max_abs_rotation_rad is None else max_abs_rotation_rad),
                int(top_k),
            )
        )
        top_candidates = [
            {
                "candidate_index": int(candidate["candidate_index"]),
                "inliers": int(candidate["inliers"]),
                "rms_px": float(candidate["rms_px"]),
                "matrix": np.asarray(candidate["matrix"], dtype=np.float32).tolist(),
                "scale": float(candidate["scale"]),
                "rotation_rad": float(candidate["rotation_rad"]),
            }
            for candidate in list(result.get("top_candidates", []))
        ]
        return {
            "matrix": np.asarray(result["matrix"], dtype=np.float32).tolist(),
            "scale": float(result["scale"]),
            "rotation_rad": float(result["rotation_rad"]),
            "rms_px": float(result["rms_px"]),
            "inliers": int(result["inliers"]),
            "refined_inliers": int(result.get("refined_inliers", result["inliers"])),
            "refit_status": str(result.get("refit_status", "not_run")),
            "refit_status_code": int(result.get("refit_status_code", -1)),
            "refit_rms_px": float(result.get("refit_rms_px", result["rms_px"])),
            "best_candidate_index": int(result["best_candidate_index"]),
            "candidate_count": int(result["candidate_count"]),
            "reference_count": int(result["reference_count"]),
            "moving_count": int(result["moving_count"]),
            "tolerance_px": float(result["tolerance_px"]),
            "min_pair_distance": float(result["min_pair_distance"]),
            "prior_dx": float(result["prior_dx"]),
            "prior_dy": float(result["prior_dy"]),
            "prior_radius_px": float(result["prior_radius_px"]),
            "min_scale": float(result["min_scale"]),
            "max_scale": float(result["max_scale"]),
            "max_abs_rotation_rad": float(result["max_abs_rotation_rad"]),
            "top_k": int(result.get("top_k", top_k)),
            "top_candidates": top_candidates,
            "status": str(result["status"]),
            "model": str(result.get("model", "catalog_pair_similarity_cuda")),
        }
    result = _similarity_from_catalogs_cpu(
        reference_x,
        reference_y,
        moving_x,
        moving_y,
        tolerance_px,
        min_pair_distance,
        prior_dx,
        prior_dy,
        prior_radius_px,
        min_scale,
        max_scale,
        max_abs_rotation_rad,
    )
    result["top_k"] = int(top_k)
    result["top_candidates"] = [
        {
            "candidate_index": int(result.get("best_candidate_index", 0)),
            "inliers": int(result.get("inliers", 0)),
            "rms_px": float(result.get("rms_px", float("nan"))),
            "matrix": result["matrix"],
            "scale": float(result.get("scale", float("nan"))),
            "rotation_rad": float(result.get("rotation_rad", float("nan"))),
        }
    ] if int(top_k) > 0 and result.get("status") == "ok" else []
    return result


def triangle_asterism_descriptors_f32(
    x: Any,
    y: Any,
    max_stars: int = 80,
    neighbors: int = 5,
    max_descriptors: int = 1200,
) -> dict[str, Any]:
    """Generate local triangle asterism descriptors from a compact star catalog."""

    if max_stars < 0:
        raise ValueError("max_stars must be non-negative")
    if max_descriptors < 0:
        raise ValueError("max_descriptors must be non-negative")
    native = _native()
    x_array = np.ascontiguousarray(np.asarray(x, dtype=np.float32).reshape(-1))
    y_array = np.ascontiguousarray(np.asarray(y, dtype=np.float32).reshape(-1))
    if x_array.shape != y_array.shape:
        raise ValueError("catalog coordinate arrays must have the same shape")
    if native is not None and hasattr(native, "triangle_asterism_descriptors_f32"):
        result = dict(
            native.triangle_asterism_descriptors_f32(
                x_array,
                y_array,
                int(max_stars),
                int(neighbors),
                int(max_descriptors),
            )
        )
        return {
            "count": int(result["count"]),
            "raw_count": int(result["raw_count"]),
            "max_stars": int(result["max_stars"]),
            "neighbors": int(result["neighbors"]),
            "descriptors": np.asarray(result["descriptors"], dtype=np.float32),
            "indices": np.asarray(result["indices"], dtype=np.int32),
            "areas": np.asarray(result["areas"], dtype=np.float32),
            "model": str(result.get("model", "triangle_asterism_descriptors_cuda")),
        }

    from glass.cpu.registration import _local_triangle_descriptors

    points = np.column_stack([x_array, y_array]).astype(np.float64, copy=False)
    descriptors = _local_triangle_descriptors(
        points,
        max_points=int(max_stars),
        neighbors=int(neighbors),
        max_descriptors=int(max_descriptors),
    )
    descriptor_array = np.asarray([item[0] for item in descriptors], dtype=np.float32).reshape(-1, 2)
    index_array = np.asarray([item[1] for item in descriptors], dtype=np.int32).reshape(-1, 3)
    area_array = np.asarray([item[2] for item in descriptors], dtype=np.float32)
    neighbor_count = min(len(points[: int(max_stars)]), max(3, int(neighbors)))
    raw_count = (
        len(points[: int(max_stars)]) * neighbor_count * (neighbor_count - 1) * (neighbor_count - 2) // 6
        if len(points[: int(max_stars)]) >= 3
        else 0
    )
    return {
        "count": int(len(descriptors)),
        "raw_count": int(raw_count),
        "max_stars": int(max_stars),
        "neighbors": int(neighbor_count),
        "descriptors": descriptor_array,
        "indices": index_array,
        "areas": area_array,
        "model": "triangle_asterism_descriptors_cpu_fallback",
    }


def _normalize_triangle_similarity_result(result: dict[str, Any]) -> dict[str, Any]:
    normalized = {
        "matrix": np.asarray(result["matrix"], dtype=np.float32).tolist(),
        "scale": float(result["scale"]),
        "rotation_rad": float(result["rotation_rad"]),
        "rms_px": float(result["rms_px"]),
        "inliers": int(result["inliers"]),
        "best_candidate_index": int(result["best_candidate_index"]),
        "candidate_count": int(result["candidate_count"]),
        "reference_count": int(result["reference_count"]),
        "moving_count": int(result["moving_count"]),
        "reference_descriptor_count": int(result["reference_descriptor_count"]),
        "moving_descriptor_count": int(result["moving_descriptor_count"]),
        "tolerance_px": float(result["tolerance_px"]),
        "descriptor_radius": float(result["descriptor_radius"]),
        "status": str(result["status"]),
        "model": str(result.get("model", "triangle_descriptor_similarity_cuda")),
    }
    if "best_reduction_mode" in result:
        normalized["best_reduction_mode"] = str(result["best_reduction_mode"])
    if "batch_index" in result:
        normalized["batch_index"] = int(result["batch_index"])
    if "batch_count" in result:
        normalized["batch_count"] = int(result["batch_count"])
    if "batch_model" in result:
        normalized["batch_model"] = str(result["batch_model"])
    if "reference_device_reuse" in result:
        normalized["reference_device_reuse"] = bool(result["reference_device_reuse"])
    if "reference_device_bytes" in result:
        normalized["reference_device_bytes"] = int(result["reference_device_bytes"])
    if "moving_device_reuse" in result:
        normalized["moving_device_reuse"] = bool(result["moving_device_reuse"])
    if "moving_device_bytes" in result:
        normalized["moving_device_bytes"] = int(result["moving_device_bytes"])
    if "output_device_reuse" in result:
        normalized["output_device_reuse"] = bool(result["output_device_reuse"])
    if "output_device_bytes" in result:
        normalized["output_device_bytes"] = int(result["output_device_bytes"])
    if "batch_timing_model" in result:
        normalized["batch_timing_model"] = str(result["batch_timing_model"])
    for key in (
        "batch_host_prepare_s",
        "batch_reference_alloc_s",
        "batch_reference_upload_s",
        "batch_workspace_alloc_s",
        "batch_frame_moving_upload_s",
        "batch_frame_kernel_sync_s",
        "batch_frame_output_download_s",
        "batch_frame_total_s",
        "batch_total_elapsed_s_at_result",
    ):
        if key in result:
            normalized[key] = float(result[key])
    return normalized


def estimate_similarity_from_triangle_descriptors_f32(
    reference_x: Any,
    reference_y: Any,
    moving_x: Any,
    moving_y: Any,
    reference_descriptors: Any,
    reference_indices: Any,
    moving_descriptors: Any,
    moving_indices: Any,
    tolerance_px: float = 2.0,
    descriptor_radius: float = 0.1,
) -> dict[str, Any]:
    """Estimate a similarity transform from matched triangle descriptor candidates."""

    if tolerance_px < 0.0:
        raise ValueError("tolerance_px must be non-negative")
    if descriptor_radius < 0.0:
        raise ValueError("descriptor_radius must be non-negative")
    ref_x = np.ascontiguousarray(np.asarray(reference_x, dtype=np.float32).reshape(-1))
    ref_y = np.ascontiguousarray(np.asarray(reference_y, dtype=np.float32).reshape(-1))
    mov_x = np.ascontiguousarray(np.asarray(moving_x, dtype=np.float32).reshape(-1))
    mov_y = np.ascontiguousarray(np.asarray(moving_y, dtype=np.float32).reshape(-1))
    ref_desc = np.ascontiguousarray(np.asarray(reference_descriptors, dtype=np.float32).reshape(-1, 2))
    mov_desc = np.ascontiguousarray(np.asarray(moving_descriptors, dtype=np.float32).reshape(-1, 2))
    ref_idx = np.ascontiguousarray(np.asarray(reference_indices, dtype=np.int32).reshape(-1, 3))
    mov_idx = np.ascontiguousarray(np.asarray(moving_indices, dtype=np.int32).reshape(-1, 3))
    if ref_x.shape != ref_y.shape or mov_x.shape != mov_y.shape:
        raise ValueError("catalog coordinate arrays must have matching x/y shapes")
    if ref_desc.shape[0] != ref_idx.shape[0] or mov_desc.shape[0] != mov_idx.shape[0]:
        raise ValueError("descriptor and index row counts must match")

    native = _native()
    if native is not None and hasattr(native, "estimate_similarity_from_triangle_descriptors_f32"):
        result = dict(
            native.estimate_similarity_from_triangle_descriptors_f32(
                ref_x,
                ref_y,
                mov_x,
                mov_y,
                ref_desc,
                ref_idx,
                mov_desc,
                mov_idx,
                float(tolerance_px),
                float(descriptor_radius),
            )
        )
        return _normalize_triangle_similarity_result(result)

    from glass.cpu.registration import _fit_similarity_matrix, _score_matrix

    reference = np.column_stack([ref_x, ref_y]).astype(np.float64, copy=False)
    moving = np.column_stack([mov_x, mov_y]).astype(np.float64, copy=False)
    best_matrix = np.eye(3, dtype=np.float64)
    best_pairs: list[tuple[int, int]] = []
    best_rms = float("inf")
    best_index = -1
    candidate_index = 0
    radius = float(descriptor_radius)
    for reference_descriptor_index, reference_descriptor in enumerate(ref_desc):
        for moving_descriptor_index, moving_descriptor in enumerate(mov_desc):
            if float(np.linalg.norm(reference_descriptor - moving_descriptor)) > radius:
                candidate_index += 2
                continue
            moving_triangle = moving[mov_idx[moving_descriptor_index]]
            reference_triangle = reference[ref_idx[reference_descriptor_index]]
            for ordered_reference_triangle in (reference_triangle, reference_triangle[[1, 0, 2]]):
                try:
                    matrix = _fit_similarity_matrix(moving_triangle, ordered_reference_triangle)
                except ValueError:
                    candidate_index += 1
                    continue
                pairs, rms = _score_matrix(reference, moving, matrix, float(tolerance_px))
                if len(pairs) > len(best_pairs) or (len(pairs) == len(best_pairs) and rms < best_rms):
                    best_matrix = matrix
                    best_pairs = pairs
                    best_rms = rms
                    best_index = candidate_index
                candidate_index += 1
    a = float(best_matrix[0, 0])
    b = float(best_matrix[1, 0])
    return {
        "matrix": best_matrix.astype(np.float32).tolist(),
        "scale": float(np.sqrt(a * a + b * b)),
        "rotation_rad": float(np.arctan2(b, a)),
        "rms_px": float(best_rms) if np.isfinite(best_rms) else float("nan"),
        "inliers": int(len(best_pairs)),
        "best_candidate_index": int(best_index),
        "candidate_count": int(ref_desc.shape[0] * mov_desc.shape[0] * 2),
        "reference_count": int(len(reference)),
        "moving_count": int(len(moving)),
        "reference_descriptor_count": int(ref_desc.shape[0]),
        "moving_descriptor_count": int(mov_desc.shape[0]),
        "tolerance_px": float(tolerance_px),
        "descriptor_radius": float(descriptor_radius),
        "status": "ok" if best_pairs else "failed",
        "model": "triangle_descriptor_similarity_cpu_fallback",
    }


def estimate_similarity_from_triangle_descriptors_batch_f32(
    reference_x: Any,
    reference_y: Any,
    reference_descriptors: Any,
    reference_indices: Any,
    moving_x_list: list[Any],
    moving_y_list: list[Any],
    moving_descriptors_list: list[Any],
    moving_indices_list: list[Any],
    tolerance_px: float = 2.0,
    descriptor_radius: float = 0.1,
) -> list[dict[str, Any]]:
    """Batch triangle descriptor similarity fits against one shared reference catalog."""

    if tolerance_px < 0.0:
        raise ValueError("tolerance_px must be non-negative")
    if descriptor_radius < 0.0:
        raise ValueError("descriptor_radius must be non-negative")
    lengths = {
        len(moving_x_list),
        len(moving_y_list),
        len(moving_descriptors_list),
        len(moving_indices_list),
    }
    if len(lengths) != 1:
        raise ValueError("moving batch lists must have the same length")
    if not moving_x_list:
        return []

    ref_x = np.ascontiguousarray(np.asarray(reference_x, dtype=np.float32).reshape(-1))
    ref_y = np.ascontiguousarray(np.asarray(reference_y, dtype=np.float32).reshape(-1))
    ref_desc = np.ascontiguousarray(np.asarray(reference_descriptors, dtype=np.float32).reshape(-1, 2))
    ref_idx = np.ascontiguousarray(np.asarray(reference_indices, dtype=np.int32).reshape(-1, 3))
    mov_xs = [
        np.ascontiguousarray(np.asarray(item, dtype=np.float32).reshape(-1))
        for item in moving_x_list
    ]
    mov_ys = [
        np.ascontiguousarray(np.asarray(item, dtype=np.float32).reshape(-1))
        for item in moving_y_list
    ]
    mov_descs = [
        np.ascontiguousarray(np.asarray(item, dtype=np.float32).reshape(-1, 2))
        for item in moving_descriptors_list
    ]
    mov_indices = [
        np.ascontiguousarray(np.asarray(item, dtype=np.int32).reshape(-1, 3))
        for item in moving_indices_list
    ]

    native = _native()
    if native is not None and hasattr(native, "estimate_similarity_from_triangle_descriptors_batch_f32"):
        results = native.estimate_similarity_from_triangle_descriptors_batch_f32(
            ref_x,
            ref_y,
            ref_desc,
            ref_idx,
            mov_xs,
            mov_ys,
            mov_descs,
            mov_indices,
            float(tolerance_px),
            float(descriptor_radius),
        )
        return [_normalize_triangle_similarity_result(dict(result)) for result in list(results)]

    output = []
    batch_count = len(mov_xs)
    for batch_index, (mov_x, mov_y, mov_desc, mov_idx) in enumerate(
        zip(mov_xs, mov_ys, mov_descs, mov_indices, strict=True)
    ):
        result = estimate_similarity_from_triangle_descriptors_f32(
            ref_x,
            ref_y,
            mov_x,
            mov_y,
            ref_desc,
            ref_idx,
            mov_desc,
            mov_idx,
            tolerance_px=tolerance_px,
            descriptor_radius=descriptor_radius,
        )
        result["batch_index"] = int(batch_index)
        result["batch_count"] = int(batch_count)
        result["batch_model"] = "triangle_descriptor_similarity_cpu_batch_fallback"
        output.append(result)
    return output


def local_norm_apply_f32(data: Any, scale: float, offset: float) -> np.ndarray:
    native = _native()
    if native is not None and hasattr(native, "local_norm_apply_f32"):
        return np.asarray(native.local_norm_apply_f32(data, float(scale), float(offset)), dtype=np.float32)
    image = np.asarray(data, dtype=np.float32)
    return (image * np.float32(scale) + np.float32(offset)).astype(np.float32)


def local_norm_apply_grid_f32(
    data: Any,
    scales: Any,
    offsets: Any,
    tile_height: int,
    tile_width: int,
) -> np.ndarray:
    image = np.asarray(data, dtype=np.float32)
    scale_grid = np.asarray(scales, dtype=np.float32)
    offset_grid = np.asarray(offsets, dtype=np.float32)
    if image.ndim != 2:
        raise ValueError("data must have shape (height, width)")
    if scale_grid.shape != offset_grid.shape:
        raise ValueError("scales and offsets must have the same shape")
    if tile_height <= 0 or tile_width <= 0:
        raise ValueError("tile dimensions must be positive")
    expected_shape = (
        int(np.ceil(image.shape[0] / int(tile_height))),
        int(np.ceil(image.shape[1] / int(tile_width))),
    )
    if scale_grid.shape != expected_shape:
        raise ValueError("coefficient grid shape does not match data shape and tile dimensions")
    native = _native()
    if native is not None and hasattr(native, "local_norm_apply_grid_f32"):
        return np.asarray(
            native.local_norm_apply_grid_f32(image, scale_grid, offset_grid, int(tile_height), int(tile_width)),
            dtype=np.float32,
        )
    out = np.empty_like(image, dtype=np.float32)
    for gy in range(scale_grid.shape[0]):
        y0 = gy * int(tile_height)
        y1 = min(image.shape[0], y0 + int(tile_height))
        for gx in range(scale_grid.shape[1]):
            x0 = gx * int(tile_width)
            x1 = min(image.shape[1], x0 + int(tile_width))
            out[y0:y1, x0:x1] = image[y0:y1, x0:x1] * scale_grid[gy, gx] + offset_grid[gy, gx]
    return out


def local_norm_pair_stats_f32(data: Any, reference: Any) -> dict[str, Any]:
    src = np.asarray(data, dtype=np.float32)
    ref = np.asarray(reference, dtype=np.float32)
    if src.shape != ref.shape:
        raise ValueError(f"shape mismatch for local norm pair stats: {src.shape} != {ref.shape}")
    native = _native()
    if native is not None and hasattr(native, "local_norm_pair_stats_f32"):
        result = dict(native.local_norm_pair_stats_f32(src, ref))
        result["stats_backend"] = "cuda"
        return result
    mask = np.isfinite(src) & np.isfinite(ref)
    valid = int(np.count_nonzero(mask))
    if valid == 0:
        return {
            "valid_pixels": 0,
            "total_pixels": int(src.size),
            "source_mean": None,
            "reference_mean": None,
            "source_std": None,
            "reference_std": None,
            "model": "cpu_pair_mean_std",
            "stats_backend": "cpu_fallback",
        }
    src_values = src[mask]
    ref_values = ref[mask]
    return {
        "valid_pixels": valid,
        "total_pixels": int(src.size),
        "source_mean": float(np.mean(src_values)),
        "reference_mean": float(np.mean(ref_values)),
        "source_std": float(np.std(src_values)),
        "reference_std": float(np.std(ref_values)),
        "model": "cpu_pair_mean_std",
        "stats_backend": "cpu_fallback",
    }


def local_norm_estimate_apply_mean_std_f32(
    data: Any,
    reference: Any,
    valid_mask: Any | None = None,
    eps: float = 1.0e-6,
) -> tuple[np.ndarray, dict[str, Any]]:
    src = np.asarray(data, dtype=np.float32)
    ref = np.asarray(reference, dtype=np.float32)
    if src.shape != ref.shape:
        raise ValueError(f"shape mismatch for local norm: {src.shape} != {ref.shape}")
    if valid_mask is None:
        mask = np.isfinite(src) & np.isfinite(ref)
        stats_src = src
        stats_ref = ref
    else:
        mask = np.asarray(valid_mask, dtype=bool) & np.isfinite(src) & np.isfinite(ref)
        stats_src = src.copy()
        stats_ref = ref.copy()
        stats_src[~mask] = np.nan
        stats_ref[~mask] = np.nan
    stats = local_norm_pair_stats_f32(stats_src, stats_ref)
    valid = int(stats["valid_pixels"])
    if valid == 0:
        scale = 1.0
        offset = 0.0
        status = "empty"
    else:
        source_mean = float(stats["source_mean"])
        reference_mean = float(stats["reference_mean"])
        source_std = float(stats["source_std"])
        reference_std = float(stats["reference_std"])
        if source_std <= float(eps) or reference_std <= float(eps):
            scale = 1.0
            offset = reference_mean - source_mean
            status = "offset_only"
        else:
            scale = reference_std / source_std
            offset = reference_mean - source_mean * scale
            status = "ok"
    out = local_norm_apply_f32(src, scale, offset)
    if valid_mask is not None:
        out = np.asarray(out, dtype=np.float32).copy()
        out[~mask] = src[~mask]
    stats.update(
        {
            "scale": float(scale),
            "offset": float(offset),
            "status": status,
            "apply_backend": "cuda" if native_extension_loaded() else "cpu_fallback",
            "model": f"{stats.get('model', 'pair_mean_std')}_apply",
        }
    )
    return np.asarray(out, dtype=np.float32), stats


def star_local_max_mask_f32(data: Any, threshold: float) -> np.ndarray:
    native = _native()
    if native is not None and hasattr(native, "star_local_max_mask_f32"):
        return np.asarray(native.star_local_max_mask_f32(data, float(threshold)), dtype=np.uint8)
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


def star_candidates_f32(data: Any, threshold: float, max_candidates: int = 4096) -> dict[str, Any]:
    native = _native()
    if native is not None and hasattr(native, "star_candidates_f32"):
        result = dict(native.star_candidates_f32(data, float(threshold), int(max_candidates)))
        return {
            "count": int(result["count"]),
            "stored_count": int(result["stored_count"]),
            "x": np.asarray(result["x"], dtype=np.float32),
            "y": np.asarray(result["y"], dtype=np.float32),
            "flux": np.asarray(result["flux"], dtype=np.float32),
        }
    mask = star_local_max_mask_f32(data, threshold)
    ys, xs = np.nonzero(mask)
    image = np.asarray(data, dtype=np.float32)
    flux = image[ys, xs].astype(np.float32)
    order = np.argsort(-flux, kind="stable")
    stored = order[: int(max_candidates)]
    return {
        "count": int(len(xs)),
        "stored_count": int(len(stored)),
        "x": xs[stored].astype(np.float32),
        "y": ys[stored].astype(np.float32),
        "flux": flux[stored].astype(np.float32),
    }


def star_top_candidates_f32(data: Any, threshold: float, max_candidates: int = 4096) -> dict[str, Any]:
    native = _native()
    if native is not None and hasattr(native, "star_top_candidates_f32"):
        result = dict(native.star_top_candidates_f32(data, float(threshold), int(max_candidates)))
        return {
            "count": int(result["count"]),
            "stored_count": int(result["stored_count"]),
            "x": np.asarray(result["x"], dtype=np.float32),
            "y": np.asarray(result["y"], dtype=np.float32),
            "flux": np.asarray(result["flux"], dtype=np.float32),
        }

    mask = star_local_max_mask_f32(data, threshold)
    ys, xs = np.nonzero(mask)
    image = np.asarray(data, dtype=np.float32)
    flux = image[ys, xs].astype(np.float32)
    order = np.argsort(-flux, kind="stable")
    stored = order[: int(max_candidates)]
    return {
        "count": int(len(xs)),
        "stored_count": int(len(stored)),
        "x": xs[stored].astype(np.float32),
        "y": ys[stored].astype(np.float32),
        "flux": flux[stored].astype(np.float32),
    }


def star_top_nms_candidates_f32(
    data: Any,
    threshold: float,
    scan_candidates: int = 4096,
    max_output_candidates: int = 64,
    min_separation_px: float = 32.0,
) -> dict[str, Any]:
    native = _native()
    if native is not None and hasattr(native, "star_top_nms_candidates_f32"):
        result = dict(
            native.star_top_nms_candidates_f32(
                data,
                float(threshold),
                int(scan_candidates),
                int(max_output_candidates),
                float(min_separation_px),
            )
        )
        return {
            "count": int(result["count"]),
            "stored_count": int(result["stored_count"]),
            "scan_candidates": int(result["scan_candidates"]),
            "max_output_candidates": int(result["max_output_candidates"]),
            "min_separation_px": float(result["min_separation_px"]),
            "x": np.asarray(result["x"], dtype=np.float32),
            "y": np.asarray(result["y"], dtype=np.float32),
            "flux": np.asarray(result["flux"], dtype=np.float32),
        }

    top = star_top_candidates_f32(data, threshold, int(scan_candidates))
    xs = np.asarray(top["x"], dtype=np.float32)
    ys = np.asarray(top["y"], dtype=np.float32)
    flux = np.asarray(top["flux"], dtype=np.float32)
    selected: list[int] = []
    min_separation2 = float(min_separation_px) * float(min_separation_px)
    for i, (x, y) in enumerate(zip(xs, ys, strict=True)):
        if len(selected) >= int(max_output_candidates):
            break
        if not np.isfinite(x) or not np.isfinite(y):
            continue
        keep = True
        for j in selected:
            dx = float(x - xs[j])
            dy = float(y - ys[j])
            if dx * dx + dy * dy < min_separation2:
                keep = False
                break
        if keep:
            selected.append(i)
    selected_array = np.asarray(selected, dtype=np.int64)
    return {
        "count": int(top["count"]),
        "stored_count": int(len(selected)),
        "scan_candidates": int(scan_candidates),
        "max_output_candidates": int(max_output_candidates),
        "min_separation_px": float(min_separation_px),
        "x": xs[selected_array].astype(np.float32),
        "y": ys[selected_array].astype(np.float32),
        "flux": flux[selected_array].astype(np.float32),
    }


def star_grid_top_nms_candidates_f32(
    data: Any,
    threshold: float,
    grid_cols: int = 16,
    grid_rows: int = 12,
    candidates_per_cell: int = 4,
    max_output_candidates: int = 64,
    min_separation_px: float = 32.0,
) -> dict[str, Any]:
    native = _native()
    if native is not None and hasattr(native, "star_grid_top_nms_candidates_f32"):
        result = dict(
            native.star_grid_top_nms_candidates_f32(
                data,
                float(threshold),
                int(grid_cols),
                int(grid_rows),
                int(candidates_per_cell),
                int(max_output_candidates),
                float(min_separation_px),
            )
        )
        return {
            "count": int(result["count"]),
            "stored_count": int(result["stored_count"]),
            "grid_cols": int(result["grid_cols"]),
            "grid_rows": int(result["grid_rows"]),
            "candidates_per_cell": int(result["candidates_per_cell"]),
            "grid_capacity": int(result["grid_capacity"]),
            "max_output_candidates": int(result["max_output_candidates"]),
            "min_separation_px": float(result["min_separation_px"]),
            "catalog_sort_mode": str(result.get("catalog_sort_mode", "unavailable")),
            "catalog_topk_mode": str(result.get("catalog_topk_mode", "unavailable")),
            "x": np.asarray(result["x"], dtype=np.float32),
            "y": np.asarray(result["y"], dtype=np.float32),
            "flux": np.asarray(result["flux"], dtype=np.float32),
        }

    if grid_cols <= 0 or grid_rows <= 0 or candidates_per_cell <= 0 or max_output_candidates <= 0:
        raise ValueError("grid dimensions and candidate counts must be positive")
    mask = star_local_max_mask_f32(data, threshold)
    ys, xs = np.nonzero(mask)
    image = np.asarray(data, dtype=np.float32)
    flux = image[ys, xs].astype(np.float32)
    cell_count = int(grid_cols) * int(grid_rows)
    capacity = cell_count * int(candidates_per_cell)
    per_cell: list[list[int]] = [[] for _ in range(cell_count)]
    h, w = image.shape
    order = np.argsort(-flux, kind="stable")
    for source_index in order:
        x = int(xs[source_index])
        y = int(ys[source_index])
        cell_x = min((x * int(grid_cols)) // w, int(grid_cols) - 1)
        cell_y = min((y * int(grid_rows)) // h, int(grid_rows) - 1)
        cell_index = cell_y * int(grid_cols) + cell_x
        if len(per_cell[cell_index]) < int(candidates_per_cell):
            per_cell[cell_index].append(int(source_index))
    compact_indices = [idx for cell in per_cell for idx in cell]
    compact_indices.sort(key=lambda idx: float(flux[idx]), reverse=True)
    selected: list[int] = []
    min_separation2 = float(min_separation_px) * float(min_separation_px)
    for idx in compact_indices:
        if len(selected) >= int(max_output_candidates):
            break
        x = float(xs[idx])
        y = float(ys[idx])
        keep = True
        for kept in selected:
            dx = x - float(xs[kept])
            dy = y - float(ys[kept])
            if dx * dx + dy * dy < min_separation2:
                keep = False
                break
        if keep:
            selected.append(idx)
    selected_array = np.asarray(selected, dtype=np.int64)
    return {
        "count": int(len(xs)),
        "stored_count": int(len(selected)),
        "grid_cols": int(grid_cols),
        "grid_rows": int(grid_rows),
        "candidates_per_cell": int(candidates_per_cell),
        "grid_capacity": int(capacity),
        "max_output_candidates": int(max_output_candidates),
        "min_separation_px": float(min_separation_px),
        "catalog_sort_mode": "python_stable_sort",
        "catalog_topk_mode": "python_per_cell_sort",
        "x": xs[selected_array].astype(np.float32),
        "y": ys[selected_array].astype(np.float32),
        "flux": flux[selected_array].astype(np.float32),
    }


def star_grid_candidates_f32(data: Any, threshold: float, grid_cols: int = 8, grid_rows: int = 8) -> dict[str, Any]:
    native = _native()
    if native is not None and hasattr(native, "star_grid_candidates_f32"):
        result = dict(native.star_grid_candidates_f32(data, float(threshold), int(grid_cols), int(grid_rows)))
        return {
            "count": int(result["count"]),
            "stored_count": int(result["stored_count"]),
            "x": np.asarray(result["x"], dtype=np.float32),
            "y": np.asarray(result["y"], dtype=np.float32),
            "flux": np.asarray(result["flux"], dtype=np.float32),
            "grid_cols": int(result["grid_cols"]),
            "grid_rows": int(result["grid_rows"]),
        }

    if grid_cols <= 0 or grid_rows <= 0:
        raise ValueError("grid dimensions must be positive")
    mask = star_local_max_mask_f32(data, threshold)
    ys, xs = np.nonzero(mask)
    image = np.asarray(data, dtype=np.float32)
    flux = image[ys, xs].astype(np.float32)
    cell_count = int(grid_cols) * int(grid_rows)
    best_x = np.zeros(cell_count, dtype=np.float32)
    best_y = np.zeros(cell_count, dtype=np.float32)
    best_flux = np.full(cell_count, -np.inf, dtype=np.float32)
    h, w = image.shape
    for x, y, value in zip(xs, ys, flux, strict=True):
        cell_x = min((int(x) * int(grid_cols)) // w, int(grid_cols) - 1)
        cell_y = min((int(y) * int(grid_rows)) // h, int(grid_rows) - 1)
        cell_index = cell_y * int(grid_cols) + cell_x
        if value > best_flux[cell_index]:
            best_x[cell_index] = np.float32(x)
            best_y[cell_index] = np.float32(y)
            best_flux[cell_index] = value
    valid = np.isfinite(best_flux)
    order = np.argsort(-best_flux[valid], kind="stable")
    return {
        "count": int(len(xs)),
        "stored_count": int(np.sum(valid)),
        "x": best_x[valid][order].astype(np.float32),
        "y": best_y[valid][order].astype(np.float32),
        "flux": best_flux[valid][order].astype(np.float32),
        "grid_cols": int(grid_cols),
        "grid_rows": int(grid_rows),
    }


class ResidentCalibratedStack:
    """VRAM-resident calibrated-frame stack for high-memory benchmark paths.

    The object keeps one reusable raw-light buffer, optional master calibration
    frames, and a calibrated frame stack on the device. Raw inputs are uploaded
    one at a time and are not retained after each calibration kernel completes.
    """

    def __init__(self, frame_count: int, height: int, width: int):
        native = _native()
        if native is None or not hasattr(native, "ResidentCalibratedStack"):
            raise RuntimeError("native CUDA backend with ResidentCalibratedStack is not available")
        self._impl = native.ResidentCalibratedStack(int(frame_count), int(height), int(width))

    @property
    def frame_count(self) -> int:
        return int(self._impl.frame_count)

    @property
    def height(self) -> int:
        return int(self._impl.height)

    @property
    def width(self) -> int:
        return int(self._impl.width)

    @property
    def pixels_per_frame(self) -> int:
        return int(self._impl.pixels_per_frame)

    @property
    def loaded_count(self) -> int:
        return int(self._impl.loaded_count)

    @property
    def bytes_allocated(self) -> int:
        return int(self._impl.bytes_allocated)

    @property
    def warp_scratch_bytes(self) -> int:
        if not hasattr(self._impl, "warp_scratch_bytes"):
            return 0
        return int(self._impl.warp_scratch_bytes)

    @property
    def warp_copy_mode(self) -> str:
        if not hasattr(self._impl, "warp_copy_mode"):
            return "legacy_synchronous_device_to_device"
        return str(self._impl.warp_copy_mode)

    @property
    def host_pinned_bytes(self) -> int:
        if not hasattr(self._impl, "host_pinned_bytes"):
            return 0
        return int(self._impl.host_pinned_bytes)

    @property
    def warp_coverage_frame_count(self) -> int:
        if not hasattr(self._impl, "warp_coverage_frame_count"):
            return 0
        return int(self._impl.warp_coverage_frame_count)

    def set_calibration_masters(
        self,
        bias: Any | None = None,
        dark: Any | None = None,
        flat: Any | None = None,
    ) -> None:
        self._impl.set_calibration_masters(
            None if bias is None else _as_f32_c(bias),
            None if dark is None else _as_f32_c(dark),
            None if flat is None else _as_f32_c(flat),
        )

    def reset_warp_coverage(self) -> None:
        if not hasattr(self._impl, "reset_warp_coverage"):
            raise RuntimeError("native ResidentCalibratedStack.reset_warp_coverage is not available")
        self._impl.reset_warp_coverage()

    def accumulate_full_warp_coverage_frame(self) -> None:
        if not hasattr(self._impl, "accumulate_full_warp_coverage_frame"):
            raise RuntimeError(
                "native ResidentCalibratedStack.accumulate_full_warp_coverage_frame is not available"
            )
        self._impl.accumulate_full_warp_coverage_frame()

    def warp_coverage_map(self) -> np.ndarray:
        if not hasattr(self._impl, "warp_coverage_map"):
            raise RuntimeError("native ResidentCalibratedStack.warp_coverage_map is not available")
        return np.asarray(self._impl.warp_coverage_map(), dtype=np.float32)

    def upload_calibrated_frame(self, index: int, frame: Any) -> None:
        self._impl.upload_calibrated_frame(int(index), _as_f32_c(frame))

    def calibrate_frame(
        self,
        index: int,
        light: Any,
        light_exposure_s: float,
        dark_exposure_s: float | None,
        policy: Any | None = None,
    ) -> None:
        self._impl.calibrate_frame(
            int(index),
            _as_f32_c(light),
            float(light_exposure_s),
            None if dark_exposure_s is None else float(dark_exposure_s),
            _policy_payload(policy),
        )

    def calibrate_frame_timed(
        self,
        index: int,
        light: Any,
        light_exposure_s: float,
        dark_exposure_s: float | None,
        policy: Any | None = None,
    ) -> dict[str, Any]:
        if not hasattr(self._impl, "calibrate_frame_timed"):
            self.calibrate_frame(index, light, light_exposure_s, dark_exposure_s, policy)
            return {
                "schema_version": 1,
                "h2d_mode": "pageable",
                "host_copy_s": 0.0,
                "h2d_s": 0.0,
                "calibrate_store_s": 0.0,
                "total_s": 0.0,
                "host_pinned_bytes": self.host_pinned_bytes,
            }
        result = self._impl.calibrate_frame_timed(
            int(index),
            _as_f32_c(light),
            float(light_exposure_s),
            None if dark_exposure_s is None else float(dark_exposure_s),
            _policy_payload(policy),
        )
        return dict(result)

    def calibrate_frame_pinned_async(
        self,
        index: int,
        light: Any,
        light_exposure_s: float,
        dark_exposure_s: float | None,
        policy: Any | None = None,
    ) -> None:
        if not hasattr(self._impl, "calibrate_frame_pinned_async"):
            raise RuntimeError("native ResidentCalibratedStack.calibrate_frame_pinned_async is not available")
        self._impl.calibrate_frame_pinned_async(
            int(index),
            _as_f32_c(light),
            float(light_exposure_s),
            None if dark_exposure_s is None else float(dark_exposure_s),
            _policy_payload(policy),
        )

    def calibrate_frame_pinned_async_timed(
        self,
        index: int,
        light: Any,
        light_exposure_s: float,
        dark_exposure_s: float | None,
        policy: Any | None = None,
    ) -> dict[str, Any]:
        if not hasattr(self._impl, "calibrate_frame_pinned_async_timed"):
            raise RuntimeError("native ResidentCalibratedStack.calibrate_frame_pinned_async_timed is not available")
        result = self._impl.calibrate_frame_pinned_async_timed(
            int(index),
            _as_f32_c(light),
            float(light_exposure_s),
            None if dark_exposure_s is None else float(dark_exposure_s),
            _policy_payload(policy),
        )
        return dict(result)

    def calibrate_frame_host_async_timed(
        self,
        index: int,
        light: Any,
        light_exposure_s: float,
        dark_exposure_s: float | None,
        policy: Any | None = None,
    ) -> dict[str, Any]:
        if not hasattr(self._impl, "calibrate_frame_host_async_timed"):
            raise RuntimeError("native ResidentCalibratedStack.calibrate_frame_host_async_timed is not available")
        result = self._impl.calibrate_frame_host_async_timed(
            int(index),
            _as_f32_c(light),
            float(light_exposure_s),
            None if dark_exposure_s is None else float(dark_exposure_s),
            _policy_payload(policy),
        )
        return dict(result)

    def apply_translation_frame(self, index: int, dx: int, dy: int, fill: float = np.nan) -> None:
        if not hasattr(self._impl, "apply_translation_frame"):
            raise RuntimeError("native ResidentCalibratedStack.apply_translation_frame is not available")
        self._impl.apply_translation_frame(int(index), int(dx), int(dy), float(fill))

    def apply_translation_bilinear_frame(self, index: int, dx: float, dy: float, fill: float = np.nan) -> None:
        if not hasattr(self._impl, "apply_translation_bilinear_frame"):
            raise RuntimeError("native ResidentCalibratedStack.apply_translation_bilinear_frame is not available")
        self._impl.apply_translation_bilinear_frame(int(index), float(dx), float(dy), float(fill))

    def apply_matrix_bilinear_frame(self, index: int, matrix: Any, fill: float = np.nan) -> None:
        if not hasattr(self._impl, "apply_matrix_bilinear_frame"):
            raise RuntimeError("native ResidentCalibratedStack.apply_matrix_bilinear_frame is not available")
        self._impl.apply_matrix_bilinear_frame(int(index), np.asarray(matrix, dtype=np.float32), float(fill))

    def apply_matrix_bilinear_frames(
        self,
        indices: Any,
        matrices: Any,
        fill: float = np.nan,
    ) -> dict[str, Any]:
        if not hasattr(self._impl, "apply_matrix_bilinear_frames"):
            raise RuntimeError("native ResidentCalibratedStack.apply_matrix_bilinear_frames is not available")
        result = self._impl.apply_matrix_bilinear_frames(
            np.asarray(indices, dtype=np.int64),
            np.asarray(matrices, dtype=np.float32),
            float(fill),
        )
        return dict(result)

    def apply_matrix_lanczos3_frame(
        self,
        index: int,
        matrix: Any,
        fill: float = np.nan,
        clamping_threshold: float = -1.0,
    ) -> None:
        if not hasattr(self._impl, "apply_matrix_lanczos3_frame"):
            raise RuntimeError("native ResidentCalibratedStack.apply_matrix_lanczos3_frame is not available")
        self._impl.apply_matrix_lanczos3_frame(
            int(index),
            np.asarray(matrix, dtype=np.float32),
            float(fill),
            float(clamping_threshold),
        )

    def apply_matrix_lanczos3_frames(
        self,
        indices: Any,
        matrices: Any,
        fill: float = np.nan,
        clamping_threshold: float = -1.0,
    ) -> dict[str, Any]:
        if not hasattr(self._impl, "apply_matrix_lanczos3_frames"):
            raise RuntimeError("native ResidentCalibratedStack.apply_matrix_lanczos3_frames is not available")
        result = self._impl.apply_matrix_lanczos3_frames(
            np.asarray(indices, dtype=np.int64),
            np.asarray(matrices, dtype=np.float32),
            float(fill),
            float(clamping_threshold),
        )
        return dict(result)

    def matrix_alignment_metrics_to_reference(
        self,
        reference_index: int,
        moving_index: int,
        matrix: Any,
        sample_stride: int = 1,
    ) -> dict[str, Any]:
        if not hasattr(self._impl, "matrix_alignment_metrics_to_reference"):
            raise RuntimeError(
                "native ResidentCalibratedStack.matrix_alignment_metrics_to_reference is not available"
            )
        if sample_stride <= 0:
            raise ValueError("sample_stride must be positive")
        result = dict(
            self._impl.matrix_alignment_metrics_to_reference(
                int(reference_index),
                int(moving_index),
                np.asarray(matrix, dtype=np.float32),
                int(sample_stride),
            )
        )
        return {
            "valid_pixels": int(result["valid_pixels"]),
            "sampled_pixels": int(result["sampled_pixels"]),
            "sample_stride": int(result["sample_stride"]),
            "rms": float(result["rms"]),
            "mean_abs_diff": float(result["mean_abs_diff"]),
            "ncc": float(result["ncc"]),
            "reference_index": int(result["reference_index"]),
            "moving_index": int(result["moving_index"]),
            "model": str(result.get("model", "resident_matrix_alignment_metrics_cuda")),
        }

    def star_core_metrics_candidates_to_reference(
        self,
        reference_index: int,
        moving_index: int,
        matrices: Any,
        threshold: float,
    ) -> dict[str, Any]:
        if not hasattr(self._impl, "star_core_metrics_candidates_to_reference"):
            raise RuntimeError(
                "native ResidentCalibratedStack.star_core_metrics_candidates_to_reference is not available"
            )
        if not np.isfinite(float(threshold)):
            raise ValueError("threshold must be finite")
        matrix_array = np.asarray(matrices, dtype=np.float32)
        if matrix_array.shape == (3, 3):
            matrix_array = matrix_array.reshape(1, 3, 3)
        if matrix_array.ndim != 3 or matrix_array.shape[1:] != (3, 3):
            raise ValueError("matrices must have shape (N, 3, 3) or (3, 3)")
        if matrix_array.shape[0] == 0:
            raise ValueError("matrices must contain at least one matrix")
        result = dict(
            self._impl.star_core_metrics_candidates_to_reference(
                int(reference_index),
                int(moving_index),
                np.ascontiguousarray(matrix_array),
                float(threshold),
            )
        )
        candidate_metrics = []
        for item in result["candidate_metrics"]:
            raw = dict(item)
            metrics = dict(raw["metrics"])
            candidate_metrics.append(
                {
                    "seed_index": int(raw["seed_index"]),
                    "metrics": {
                        "valid_pixels": int(metrics["valid_pixels"]),
                        "sampled_pixels": int(metrics["sampled_pixels"]),
                        "sample_stride": int(metrics["sample_stride"]),
                        "rms": float(metrics["rms"]),
                        "mean_abs_diff": float(metrics["mean_abs_diff"]),
                        "ncc": float(metrics["ncc"]),
                        "model": str(metrics.get("model", "resident_star_core_bilinear_metric_cuda_candidate")),
                    },
                }
            )
        return {
            "candidate_count": int(result["candidate_count"]),
            "threshold": float(result["threshold"]),
            "sampled_pixels": int(result["sampled_pixels"]),
            "candidate_metrics": candidate_metrics,
            "reference_index": int(result["reference_index"]),
            "moving_index": int(result["moving_index"]),
            "model": str(result.get("model", "resident_star_core_bilinear_metric_cuda")),
        }

    def refine_matrix_translation_candidates_to_reference(
        self,
        reference_index: int,
        moving_index: int,
        matrices: Any,
        search_radius_px: float = 1.0,
        coarse_step_px: float = 0.25,
        fine_radius_px: float = 0.25,
        fine_step_px: float = 0.0625,
        coarse_sample_stride: int = 4,
        final_sample_stride: int = 1,
    ) -> dict[str, Any]:
        if not hasattr(self._impl, "refine_matrix_translation_candidates_to_reference"):
            raise RuntimeError(
                "native ResidentCalibratedStack.refine_matrix_translation_candidates_to_reference is not available"
            )
        if search_radius_px < 0.0:
            raise ValueError("search_radius_px must be non-negative")
        if coarse_step_px <= 0.0:
            raise ValueError("coarse_step_px must be positive")
        if fine_radius_px < 0.0:
            raise ValueError("fine_radius_px must be non-negative")
        if fine_step_px <= 0.0:
            raise ValueError("fine_step_px must be positive")
        if coarse_sample_stride <= 0 or final_sample_stride <= 0:
            raise ValueError("sample strides must be positive")
        matrix_array = np.asarray(matrices, dtype=np.float32)
        if matrix_array.shape == (3, 3):
            matrix_array = matrix_array.reshape(1, 3, 3)
        if matrix_array.ndim != 3 or matrix_array.shape[1:] != (3, 3):
            raise ValueError("matrices must have shape (N, 3, 3) or (3, 3)")
        if matrix_array.shape[0] == 0:
            raise ValueError("matrices must contain at least one matrix")

        result = dict(
            self._impl.refine_matrix_translation_candidates_to_reference(
                int(reference_index),
                int(moving_index),
                np.ascontiguousarray(matrix_array, dtype=np.float32),
                float(search_radius_px),
                float(coarse_step_px),
                float(fine_radius_px),
                float(fine_step_px),
                int(coarse_sample_stride),
                int(final_sample_stride),
            )
        )
        return _normalize_matrix_refinement_result(result)

    def refine_matrix_translation_candidates_batch_to_reference(
        self,
        reference_index: int,
        moving_indices: list[int] | np.ndarray,
        matrices: Any,
        search_radius_px: float = 1.0,
        coarse_step_px: float = 0.25,
        fine_radius_px: float = 0.25,
        fine_step_px: float = 0.0625,
        coarse_sample_stride: int = 4,
        final_sample_stride: int = 1,
    ) -> list[dict[str, Any]]:
        if not hasattr(self._impl, "refine_matrix_translation_candidates_batch_to_reference"):
            return [
                self.refine_matrix_translation_candidates_to_reference(
                    reference_index,
                    int(moving_index),
                    np.asarray([matrix], dtype=np.float32),
                    search_radius_px,
                    coarse_step_px,
                    fine_radius_px,
                    fine_step_px,
                    coarse_sample_stride,
                    final_sample_stride,
                )
                for moving_index, matrix in zip(list(moving_indices), np.asarray(matrices, dtype=np.float32), strict=True)
            ]
        moving_index_list = [int(item) for item in list(moving_indices)]
        matrix_array = np.asarray(matrices, dtype=np.float32)
        if matrix_array.ndim != 3 or matrix_array.shape[1:] != (3, 3):
            raise ValueError("batch matrices must have shape (N, 3, 3)")
        if matrix_array.shape[0] != len(moving_index_list):
            raise ValueError("batch matrices must contain one matrix per moving index")
        if search_radius_px < 0.0:
            raise ValueError("search_radius_px must be non-negative")
        if coarse_step_px <= 0.0:
            raise ValueError("coarse_step_px must be positive")
        if fine_radius_px < 0.0:
            raise ValueError("fine_radius_px must be non-negative")
        if fine_step_px <= 0.0:
            raise ValueError("fine_step_px must be positive")
        if coarse_sample_stride <= 0 or final_sample_stride <= 0:
            raise ValueError("sample strides must be positive")
        if not moving_index_list:
            return []
        results = self._impl.refine_matrix_translation_candidates_batch_to_reference(
            int(reference_index),
            moving_index_list,
            np.ascontiguousarray(matrix_array, dtype=np.float32),
            float(search_radius_px),
            float(coarse_step_px),
            float(fine_radius_px),
            float(fine_step_px),
            int(coarse_sample_stride),
            int(final_sample_stride),
        )
        return [_normalize_matrix_refinement_result(dict(result)) for result in list(results)]

    def estimate_translation_to_reference(
        self,
        reference_index: int,
        moving_index: int,
        max_shift_x: int,
        max_shift_y: int | None = None,
        sample_stride: int = 1,
    ) -> dict[str, Any]:
        if not hasattr(self._impl, "estimate_translation_to_reference"):
            raise RuntimeError("native ResidentCalibratedStack.estimate_translation_to_reference is not available")
        if sample_stride <= 0:
            raise ValueError("sample_stride must be positive")
        result = dict(
            self._impl.estimate_translation_to_reference(
                int(reference_index),
                int(moving_index),
                int(max_shift_x),
                int(max_shift_x if max_shift_y is None else max_shift_y),
                int(sample_stride),
            )
        )
        return {
            "dx": int(result["dx"]),
            "dy": int(result["dy"]),
            "score": float(result["score"]),
            "search_count": int(result["search_count"]),
            "sample_stride": int(result.get("sample_stride", sample_stride)),
            "reference_index": int(result["reference_index"]),
            "moving_index": int(result["moving_index"]),
            "model": str(result["model"]),
        }

    def estimate_translation_subpixel_to_reference(
        self,
        reference_index: int,
        moving_index: int,
        center_dx: float,
        center_dy: float,
        radius_steps: int,
        step: float,
        sample_stride: int = 1,
    ) -> dict[str, Any]:
        if not hasattr(self._impl, "estimate_translation_subpixel_to_reference"):
            raise RuntimeError(
                "native ResidentCalibratedStack.estimate_translation_subpixel_to_reference is not available"
            )
        if sample_stride <= 0:
            raise ValueError("sample_stride must be positive")
        result = dict(
            self._impl.estimate_translation_subpixel_to_reference(
                int(reference_index),
                int(moving_index),
                float(center_dx),
                float(center_dy),
                int(radius_steps),
                float(step),
                int(sample_stride),
            )
        )
        return {
            "dx": float(result["dx"]),
            "dy": float(result["dy"]),
            "score": float(result["score"]),
            "candidate_count": int(result["candidate_count"]),
            "center_dx": float(result["center_dx"]),
            "center_dy": float(result["center_dy"]),
            "radius_steps": int(result["radius_steps"]),
            "step": float(result["step"]),
            "sample_stride": int(result.get("sample_stride", sample_stride)),
            "reference_index": int(result["reference_index"]),
            "moving_index": int(result["moving_index"]),
            "model": str(result["model"]),
        }

    def frame_global_stats(self, index: int) -> dict[str, Any]:
        if not hasattr(self._impl, "frame_global_stats"):
            raise RuntimeError("native ResidentCalibratedStack.frame_global_stats is not available")
        result = dict(self._impl.frame_global_stats(int(index)))
        return {
            "mean": float(result["mean"]),
            "std": float(result["std"]),
            "valid_pixels": int(result["valid_pixels"]),
            "total_pixels": int(result["total_pixels"]),
            "nonfinite_pixels": int(result["nonfinite_pixels"]),
            "model": str(result["model"]),
        }

    def frame_pair_grid_stats(
        self,
        reference_index: int,
        source_index: int,
        tile_height: int,
        tile_width: int,
    ) -> dict[str, Any]:
        if not hasattr(self._impl, "frame_pair_grid_stats"):
            raise RuntimeError("native ResidentCalibratedStack.frame_pair_grid_stats is not available")
        result = dict(
            self._impl.frame_pair_grid_stats(
                int(reference_index),
                int(source_index),
                int(tile_height),
                int(tile_width),
            )
        )
        return {
            "source_mean": np.asarray(result["source_mean"], dtype=np.float32),
            "source_std": np.asarray(result["source_std"], dtype=np.float32),
            "reference_mean": np.asarray(result["reference_mean"], dtype=np.float32),
            "reference_std": np.asarray(result["reference_std"], dtype=np.float32),
            "valid_pixels": np.asarray(result["valid_pixels"], dtype=np.uint64),
            "grid_rows": int(result["grid_rows"]),
            "grid_cols": int(result["grid_cols"]),
            "tile_height": int(result["tile_height"]),
            "tile_width": int(result["tile_width"]),
            "valid_pixel_total": int(result["valid_pixel_total"]),
            "model": str(result["model"]),
        }

    def apply_global_normalization_frame(self, index: int, scale: float, offset: float) -> None:
        if not hasattr(self._impl, "apply_global_normalization_frame"):
            raise RuntimeError("native ResidentCalibratedStack.apply_global_normalization_frame is not available")
        self._impl.apply_global_normalization_frame(int(index), float(scale), float(offset))

    def apply_grid_normalization_frame(
        self,
        index: int,
        scales: Any,
        offsets: Any,
        tile_height: int,
        tile_width: int,
    ) -> None:
        if not hasattr(self._impl, "apply_grid_normalization_frame"):
            raise RuntimeError("native ResidentCalibratedStack.apply_grid_normalization_frame is not available")
        scale_grid = np.asarray(scales, dtype=np.float32)
        offset_grid = np.asarray(offsets, dtype=np.float32)
        self._impl.apply_grid_normalization_frame(
            int(index),
            scale_grid,
            offset_grid,
            int(tile_height),
            int(tile_width),
        )

    def star_local_max_mask(self, index: int, threshold: float) -> np.ndarray:
        if not hasattr(self._impl, "star_local_max_mask"):
            raise RuntimeError("native ResidentCalibratedStack.star_local_max_mask is not available")
        return np.asarray(self._impl.star_local_max_mask(int(index), float(threshold)), dtype=np.uint8)

    def star_candidates(self, index: int, threshold: float, max_candidates: int = 4096) -> dict[str, Any]:
        if not hasattr(self._impl, "star_candidates"):
            raise RuntimeError("native ResidentCalibratedStack.star_candidates is not available")
        result = dict(self._impl.star_candidates(int(index), float(threshold), int(max_candidates)))
        return {
            "count": int(result["count"]),
            "stored_count": int(result["stored_count"]),
            "x": np.asarray(result["x"], dtype=np.float32),
            "y": np.asarray(result["y"], dtype=np.float32),
            "flux": np.asarray(result["flux"], dtype=np.float32),
        }

    def star_top_candidates(self, index: int, threshold: float, max_candidates: int = 4096) -> dict[str, Any]:
        if not hasattr(self._impl, "star_top_candidates"):
            raise RuntimeError("native ResidentCalibratedStack.star_top_candidates is not available")
        result = dict(self._impl.star_top_candidates(int(index), float(threshold), int(max_candidates)))
        return {
            "count": int(result["count"]),
            "stored_count": int(result["stored_count"]),
            "x": np.asarray(result["x"], dtype=np.float32),
            "y": np.asarray(result["y"], dtype=np.float32),
            "flux": np.asarray(result["flux"], dtype=np.float32),
        }

    def star_top_nms_candidates(
        self,
        index: int,
        threshold: float,
        scan_candidates: int,
        max_output_candidates: int,
        min_separation_px: float,
    ) -> dict[str, Any]:
        if not hasattr(self._impl, "star_top_nms_candidates"):
            raise RuntimeError("native ResidentCalibratedStack.star_top_nms_candidates is not available")
        result = dict(
            self._impl.star_top_nms_candidates(
                int(index),
                float(threshold),
                int(scan_candidates),
                int(max_output_candidates),
                float(min_separation_px),
            )
        )
        return {
            "count": int(result["count"]),
            "stored_count": int(result["stored_count"]),
            "scan_candidates": int(result["scan_candidates"]),
            "max_output_candidates": int(result["max_output_candidates"]),
            "min_separation_px": float(result["min_separation_px"]),
            "x": np.asarray(result["x"], dtype=np.float32),
            "y": np.asarray(result["y"], dtype=np.float32),
            "flux": np.asarray(result["flux"], dtype=np.float32),
        }

    def star_grid_top_nms_candidates(
        self,
        index: int,
        threshold: float,
        grid_cols: int,
        grid_rows: int,
        candidates_per_cell: int,
        max_output_candidates: int,
        min_separation_px: float,
        deterministic: bool = False,
    ) -> dict[str, Any]:
        method_name = (
            "star_grid_top_nms_candidates_deterministic"
            if deterministic
            else "star_grid_top_nms_candidates"
        )
        if not hasattr(self._impl, method_name):
            raise RuntimeError(f"native ResidentCalibratedStack.{method_name} is not available")
        method = getattr(self._impl, method_name)
        result = dict(
            method(
                int(index),
                float(threshold),
                int(grid_cols),
                int(grid_rows),
                int(candidates_per_cell),
                int(max_output_candidates),
                float(min_separation_px),
            )
        )
        return {
            "count": int(result["count"]),
            "stored_count": int(result["stored_count"]),
            "grid_cols": int(result["grid_cols"]),
            "grid_rows": int(result["grid_rows"]),
            "candidates_per_cell": int(result["candidates_per_cell"]),
            "max_output_candidates": int(result["max_output_candidates"]),
            "min_separation_px": float(result["min_separation_px"]),
            "catalog_sort_mode": str(result.get("catalog_sort_mode", "unavailable")),
            "catalog_topk_mode": str(result.get("catalog_topk_mode", "unavailable")),
            "x": np.asarray(result["x"], dtype=np.float32),
            "y": np.asarray(result["y"], dtype=np.float32),
            "flux": np.asarray(result["flux"], dtype=np.float32),
        }

    def star_grid_top_nms_candidates_batch(
        self,
        indices: list[int] | tuple[int, ...],
        threshold: float,
        grid_cols: int,
        grid_rows: int,
        candidates_per_cell: int,
        max_output_candidates: int,
        min_separation_px: float,
        deterministic: bool = False,
    ) -> list[dict[str, Any]]:
        method_name = (
            "star_grid_top_nms_candidates_batch_deterministic"
            if deterministic
            else "star_grid_top_nms_candidates_batch"
        )
        if not hasattr(self._impl, method_name):
            raise RuntimeError(f"native ResidentCalibratedStack.{method_name} is not available")
        method = getattr(self._impl, method_name)
        results = method(
            [int(index) for index in indices],
            float(threshold),
            int(grid_cols),
            int(grid_rows),
            int(candidates_per_cell),
            int(max_output_candidates),
            float(min_separation_px),
        )
        catalogs: list[dict[str, Any]] = []
        for item in results:
            result = dict(item)
            catalogs.append(
                {
                    "frame_index": int(result["frame_index"]),
                    "count": int(result["count"]),
                    "stored_count": int(result["stored_count"]),
                    "grid_cols": int(result["grid_cols"]),
                    "grid_rows": int(result["grid_rows"]),
                    "candidates_per_cell": int(result["candidates_per_cell"]),
                    "max_output_candidates": int(result["max_output_candidates"]),
                    "min_separation_px": float(result["min_separation_px"]),
                    "catalog_sort_mode": str(result.get("catalog_sort_mode", "unavailable")),
                    "catalog_topk_mode": str(result.get("catalog_topk_mode", "unavailable")),
                    "catalog_timing_model": str(
                        result.get("catalog_timing_model", "unavailable")
                    ),
                    "catalog_enqueue_s": float(result.get("catalog_enqueue_s", 0.0) or 0.0),
                    "catalog_sync_s": float(result.get("catalog_sync_s", 0.0) or 0.0),
                    "catalog_count_download_s": float(
                        result.get("catalog_count_download_s", 0.0) or 0.0
                    ),
                    "catalog_output_download_s": float(
                        result.get("catalog_output_download_s", 0.0) or 0.0
                    ),
                    "catalog_native_s": float(result.get("catalog_native_s", 0.0) or 0.0),
                    "x": np.asarray(result["x"], dtype=np.float32),
                    "y": np.asarray(result["y"], dtype=np.float32),
                    "flux": np.asarray(result["flux"], dtype=np.float32),
                }
            )
        return catalogs

    def estimate_translation_from_stars_to_reference(
        self,
        reference_index: int,
        moving_index: int,
        threshold: float,
        max_candidates: int = 64,
        tolerance_px: float = 1.0,
        max_abs_dx: float = -1.0,
        max_abs_dy: float | None = None,
        prior_dx: float = 0.0,
        prior_dy: float = 0.0,
        prior_radius_px: float = -1.0,
        grid_cols: int = 0,
        grid_rows: int = 0,
    ) -> dict[str, Any]:
        if not hasattr(self._impl, "estimate_translation_from_stars_to_reference"):
            raise RuntimeError(
                "native ResidentCalibratedStack.estimate_translation_from_stars_to_reference is not available"
            )
        if max_abs_dy is None:
            max_abs_dy = max_abs_dx
        result = dict(
            self._impl.estimate_translation_from_stars_to_reference(
                int(reference_index),
                int(moving_index),
                float(threshold),
                int(max_candidates),
                float(tolerance_px),
                float(max_abs_dx),
                float(max_abs_dy),
                float(prior_dx),
                float(prior_dy),
                float(prior_radius_px),
                int(grid_cols),
                int(grid_rows),
            )
        )
        return {
            "dx": float(result["dx"]),
            "dy": float(result["dy"]),
            "inliers": int(result["inliers"]),
            "refined_dx": float(result["refined_dx"]),
            "refined_dy": float(result["refined_dy"]),
            "mutual_inliers": int(result["mutual_inliers"]),
            "rms_px": float(result["rms_px"]),
            "candidate_count": int(result["candidate_count"]),
            "reference_count": int(result["reference_count"]),
            "moving_count": int(result["moving_count"]),
            "reference_total_count": int(result["reference_total_count"]),
            "moving_total_count": int(result["moving_total_count"]),
            "threshold": float(result["threshold"]),
            "max_candidates": int(result["max_candidates"]),
            "catalog_capacity": int(result["catalog_capacity"]),
            "candidate_selection": str(result["candidate_selection"]),
            "grid_cols": int(result["grid_cols"]),
            "grid_rows": int(result["grid_rows"]),
            "tolerance_px": float(result["tolerance_px"]),
            "max_abs_dx": float(result["max_abs_dx"]),
            "max_abs_dy": float(result["max_abs_dy"]),
            "prior_dx": float(result["prior_dx"]),
            "prior_dy": float(result["prior_dy"]),
            "prior_radius_px": float(result["prior_radius_px"]),
            "reference_index": int(result["reference_index"]),
            "moving_index": int(result["moving_index"]),
            "model": str(result["model"]),
        }

    def integrate_mean(self, weights: Any | None = None) -> tuple[np.ndarray, np.ndarray]:
        master, weight_map = self._impl.integrate_mean(
            None if weights is None else _as_f32_c(weights).reshape((self.frame_count,))
        )
        return np.asarray(master, dtype=np.float32), np.asarray(weight_map, dtype=np.float32)

    def integrate_sigma_clip(
        self,
        weights: Any | None = None,
        low_sigma: float = 3.0,
        high_sigma: float = 3.0,
        winsorize: bool = True,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        if not hasattr(self._impl, "integrate_sigma_clip"):
            raise RuntimeError("native ResidentCalibratedStack.integrate_sigma_clip is not available")
        master, weight_map, coverage, low_reject, high_reject = self._impl.integrate_sigma_clip(
            None if weights is None else _as_f32_c(weights).reshape((self.frame_count,)),
            float(low_sigma),
            float(high_sigma),
            bool(winsorize),
        )
        return (
            np.asarray(master, dtype=np.float32),
            np.asarray(weight_map, dtype=np.float32),
            np.asarray(coverage, dtype=np.float32),
            np.asarray(low_reject, dtype=np.float32),
            np.asarray(high_reject, dtype=np.float32),
        )
