"""Compatibility API for the optional native CUDA backend.

This module keeps the public `gpwbpp_cuda` import path stable on CPU-only
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

from gpwbpp.cpu.calibration import calibrate_light
from gpwbpp.models import CalibrationPolicy


def _native():
    try:
        return importlib.import_module("_gpwbpp_cuda_native")
    except Exception:
        return None


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


def list_devices() -> list[dict[str, Any]]:
    native = _native()
    if native is not None:
        try:
            return list(native.list_devices())
        except Exception:
            pass
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
                "available_to_gpwbpp": False,
            }
        )
    return devices


def get_device_info(device_id: int) -> dict[str, Any]:
    native = _native()
    if native is not None:
        return dict(native.get_device_info(device_id))
    for device in list_devices():
        if device["device_id"] == device_id:
            return device
    raise RuntimeError(f"CUDA device {device_id} is not visible to gpwbpp_cuda")


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
            )
        )
        return {
            "matrix": np.asarray(result["matrix"], dtype=np.float32).tolist(),
            "scale": float(result["scale"]),
            "rotation_rad": float(result["rotation_rad"]),
            "rms_px": float(result["rms_px"]),
            "inliers": int(result["inliers"]),
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
            "status": str(result["status"]),
            "model": str(result.get("model", "catalog_pair_similarity_cuda")),
        }
    return _similarity_from_catalogs_cpu(
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


def local_norm_apply_f32(data: Any, scale: float, offset: float) -> np.ndarray:
    native = _native()
    if native is not None and hasattr(native, "local_norm_apply_f32"):
        return np.asarray(native.local_norm_apply_f32(data, float(scale), float(offset)), dtype=np.float32)
    image = np.asarray(data, dtype=np.float32)
    return (image * np.float32(scale) + np.float32(offset)).astype(np.float32)


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

    def apply_global_normalization_frame(self, index: int, scale: float, offset: float) -> None:
        if not hasattr(self._impl, "apply_global_normalization_frame"):
            raise RuntimeError("native ResidentCalibratedStack.apply_global_normalization_frame is not available")
        self._impl.apply_global_normalization_frame(int(index), float(scale), float(offset))

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
