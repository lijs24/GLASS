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


def _translation_ncc_score(reference: np.ndarray, moving: np.ndarray, dx: int, dy: int) -> float:
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
) -> dict[str, Any]:
    """Estimate an integer translation that warps ``moving`` onto ``reference``.

    The native CUDA path scores every integer shift with normalized cross-correlation
    and selects the best candidate on device. The CPU fallback is intentionally small
    and exists only to keep the API importable on CPU-only machines.
    """

    if max_shift_y is None:
        max_shift_y = max_shift_x
    native = _native()
    if native is not None and hasattr(native, "estimate_translation_search_f32"):
        result = dict(
            native.estimate_translation_search_f32(
                reference,
                moving,
                int(max_shift_x),
                int(max_shift_y),
            )
        )
        return {
            "dx": int(result["dx"]),
            "dy": int(result["dy"]),
            "score": float(result["score"]),
            "search_count": int(result["search_count"]),
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
            score = _translation_ncc_score(ref, mov, dx, dy)
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
        "model": "translation_integer_ncc_cpu_fallback",
    }


def _catalog_translation_vote(
    reference_x: np.ndarray,
    reference_y: np.ndarray,
    moving_x: np.ndarray,
    moving_y: np.ndarray,
    tolerance_px: float,
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
    tolerance2 = np.float32(tolerance_px) * np.float32(tolerance_px)
    best_index = 0
    best_score = -1
    for i, (candidate_dx, candidate_dy) in enumerate(zip(dx, dy, strict=True)):
        ddx = dx - candidate_dx
        ddy = dy - candidate_dy
        score = int(np.sum((ddx * ddx + ddy * ddy) <= tolerance2))
        if score > best_score:
            best_index = i
            best_score = score
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
) -> dict[str, Any]:
    """Estimate translation from two star coordinate catalogs.

    The CUDA path forms all reference/moving pair offsets, scores each offset
    by nearby pair-offset votes, and returns the highest-vote translation.
    """

    native = _native()
    if native is not None and hasattr(native, "estimate_translation_from_catalogs_f32"):
        result = dict(
            native.estimate_translation_from_catalogs_f32(
                np.ascontiguousarray(np.asarray(reference_x, dtype=np.float32).reshape(-1)),
                np.ascontiguousarray(np.asarray(reference_y, dtype=np.float32).reshape(-1)),
                np.ascontiguousarray(np.asarray(moving_x, dtype=np.float32).reshape(-1)),
                np.ascontiguousarray(np.asarray(moving_y, dtype=np.float32).reshape(-1)),
                float(tolerance_px),
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
            "model": str(result.get("model", "catalog_pair_offset_translation")),
        }

    return _catalog_translation_vote(
        np.asarray(reference_x, dtype=np.float32),
        np.asarray(reference_y, dtype=np.float32),
        np.asarray(moving_x, dtype=np.float32),
        np.asarray(moving_y, dtype=np.float32),
        tolerance_px,
    )


def local_norm_apply_f32(data: Any, scale: float, offset: float) -> np.ndarray:
    native = _native()
    if native is not None and hasattr(native, "local_norm_apply_f32"):
        return np.asarray(native.local_norm_apply_f32(data, float(scale), float(offset)), dtype=np.float32)
    image = np.asarray(data, dtype=np.float32)
    return (image * np.float32(scale) + np.float32(offset)).astype(np.float32)


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
