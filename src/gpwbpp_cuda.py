from __future__ import annotations

"""Compatibility API for the optional native CUDA backend.

This module keeps the public `gpwbpp_cuda` import path stable on CPU-only
installations. It reports visible NVIDIA devices through `nvidia-smi` when
available, but `cuda_available()` remains false until a real native CUDA
extension is built and loaded. Numeric helpers use CPU fallbacks only for smoke
testing the API surface; they are not advertised as GPU kernels.
"""

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


def local_norm_apply_f32(data: Any, scale: float, offset: float) -> np.ndarray:
    native = _native()
    if native is not None and hasattr(native, "local_norm_apply_f32"):
        return np.asarray(native.local_norm_apply_f32(data, float(scale), float(offset)), dtype=np.float32)
    image = np.asarray(data, dtype=np.float32)
    return (image * np.float32(scale) + np.float32(offset)).astype(np.float32)


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
