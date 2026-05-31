from __future__ import annotations

import gc
import hashlib
import json
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np

from glass.cpu.registration import estimate_translation_phase_correlation, translation_matrix
from glass.cpu.master_frames import image_stats, make_master_bias, make_master_dark, make_master_flat
from glass.engine.contracts import DQFlag, DQMask
from glass.engine.dq import dq_provenance_summary_from_resident
from glass.io.fits_io import FitsImageReader, read_fits_data, write_fits_data
from glass.io.json_io import read_json, write_json
from glass.models import CalibrationPolicy, PipelineArtifact, RegistrationResult, RunState, now_iso


_AUTO_STAR_THRESHOLD_SIGMAS = (0.75, 1.0, 1.25, 1.5, 2.0, 3.0)
_RESIDENT_OUTPUT_MAP_POLICIES = {"audit", "science", "minimal"}


def _cuda_module_required():
    import glass_cuda

    if not glass_cuda.cuda_available() or not hasattr(glass_cuda, "ResidentCalibratedStack"):
        raise RuntimeError("resident CUDA mode requires the native ResidentCalibratedStack backend")
    return glass_cuda


def _policy_from_plan(plan: dict[str, Any]) -> CalibrationPolicy:
    raw = plan.get("calibration_plan", {}).get("calibration_policy", {})
    allowed = set(CalibrationPolicy.__dataclass_fields__.keys())
    return CalibrationPolicy(**{key: value for key, value in raw.items() if key in allowed})


def _frame_map(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {frame["id"]: frame for frame in plan.get("frames", [])}


def _frames_by_type(plan: dict[str, Any], frame_type: str) -> list[dict[str, Any]]:
    return [frame for frame in plan.get("frames", []) if frame.get("frame_type") == frame_type]


def _paths_for_records(records: list[dict[str, Any]]) -> list[Path]:
    return [Path(str(frame["path"])) for frame in records]


def _same_shape(frame: dict[str, Any], height: int, width: int) -> bool:
    return int(frame.get("height") or 0) == height and int(frame.get("width") or 0) == width


def _safe_filter_name(value: str | None) -> str:
    text = value or "unknown"
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in text)


def _memory_estimate(frame_count: int, height: int, width: int, master_count: int = 3) -> dict[str, Any]:
    frame_bytes = int(height) * int(width) * 4
    calibrated_stack = frame_count * frame_bytes
    reusable_raw = frame_bytes
    masters = master_count * frame_bytes
    integration_outputs = 2 * frame_bytes
    weights = frame_count * 4
    estimated_peak = calibrated_stack + reusable_raw + masters + integration_outputs + weights
    return {
        "frame_bytes": frame_bytes,
        "frame_mib": frame_bytes / (1024**2),
        "calibrated_stack_bytes": calibrated_stack,
        "calibrated_stack_gib": calibrated_stack / (1024**3),
        "resident_base_bytes": calibrated_stack + reusable_raw + masters,
        "resident_base_gib": (calibrated_stack + reusable_raw + masters) / (1024**3),
        "integration_temporary_bytes": integration_outputs + weights,
        "integration_temporary_gib": (integration_outputs + weights) / (1024**3),
        "estimated_peak_bytes": estimated_peak,
        "estimated_peak_gib": estimated_peak / (1024**3),
    }


def _timing_summary(values: list[float]) -> dict[str, float]:
    if not values:
        return {"total": 0.0, "mean": 0.0, "min": 0.0, "max": 0.0}
    data = np.asarray(values, dtype=np.float64)
    return {
        "total": float(np.sum(data)),
        "mean": float(np.mean(data)),
        "min": float(np.min(data)),
        "max": float(np.max(data)),
    }


def _add_elapsed(buckets: dict[str, float], key: str, elapsed: float) -> None:
    buckets[key] = float(buckets.get(key, 0.0) + float(elapsed))


def _read_light_timed(path: str | Path, output: np.ndarray | None = None) -> tuple[np.ndarray, dict[str, float]]:
    total_start = perf_counter()
    open_start = perf_counter()
    with FitsImageReader(path) as reader:
        open_elapsed = perf_counter() - open_start
        materialize_start = perf_counter()
        if output is None:
            data = reader.read_full(dtype=np.float32)
        else:
            data = reader.read_full_into(output)
        materialize_elapsed = perf_counter() - materialize_start
    total_elapsed = perf_counter() - total_start
    return data, {
        "total": total_elapsed,
        "fits_open": open_elapsed,
        "fits_materialize_decode": materialize_elapsed,
    }


class _LightPrefetcher:
    def __init__(
        self,
        light_frames: list[dict[str, Any]],
        depth: int,
        workers: int = 1,
        pinned_ring: bool = False,
        height: int | None = None,
        width: int | None = None,
    ):
        self.light_frames = light_frames
        self.depth = max(0, int(depth))
        self.workers = max(1, int(workers))
        self.pinned_ring = bool(pinned_ring and self.depth > 0)
        self.height = height
        self.width = width
        self.executor: ThreadPoolExecutor | None = None
        self.pending: dict[int, Future[tuple[np.ndarray, dict[str, float]]]] = {}
        self.pinned_slots: list[np.ndarray] = []
        self.free_slots: list[int] = []
        self.inflight_slots: dict[int, int] = {}
        self.next_submit = 0

    def __enter__(self) -> "_LightPrefetcher":
        if self.depth > 0:
            if self.pinned_ring:
                if self.height is None or self.width is None:
                    raise ValueError("pinned resident prefetch requires image height and width")
                glass_cuda = _cuda_module_required()
                self.pinned_slots = [
                    glass_cuda.host_pinned_empty_f32(int(self.height), int(self.width))
                    for _ in range(self.depth)
                ]
                self.free_slots = list(range(len(self.pinned_slots)))
            self.executor = ThreadPoolExecutor(
                max_workers=self.workers,
                thread_name_prefix="glass-light-prefetch",
            )
            self._fill()
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        if self.executor is not None:
            self.executor.shutdown(wait=True, cancel_futures=True)
            self.executor = None

    def _fill(self) -> None:
        if self.executor is None:
            return
        while self.next_submit < len(self.light_frames) and len(self.pending) < self.depth:
            slot: np.ndarray | None = None
            slot_id: int | None = None
            if self.pinned_ring:
                if not self.free_slots:
                    return
                slot_id = self.free_slots.pop()
                slot = self.pinned_slots[slot_id]
            frame = self.light_frames[self.next_submit]
            self.pending[self.next_submit] = self.executor.submit(_read_light_timed, frame["path"], slot)
            if slot_id is not None:
                self.inflight_slots[self.next_submit] = slot_id
            self.next_submit += 1

    def result(self, index: int) -> tuple[np.ndarray, dict[str, float], float]:
        if self.executor is None:
            data, read_profile = _read_light_timed(self.light_frames[index]["path"])
            return data, read_profile, read_profile["total"]
        future = self.pending.pop(index)
        wait_start = perf_counter()
        data, read_profile = future.result()
        wait_elapsed = perf_counter() - wait_start
        if not self.pinned_ring:
            self._fill()
        return data, read_profile, wait_elapsed

    def release(self, index: int) -> None:
        if not self.pinned_ring:
            return
        slot_id = self.inflight_slots.pop(index, None)
        if slot_id is None:
            return
        self.free_slots.append(slot_id)
        self._fill()

    @property
    def host_pinned_bytes(self) -> int:
        if not self.pinned_slots:
            return 0
        return int(sum(slot.nbytes for slot in self.pinned_slots))


def _grid_local_norm_coefficients(stats: dict[str, Any], eps: float = 1.0e-6) -> dict[str, Any]:
    source_mean = np.asarray(stats["source_mean"], dtype=np.float32)
    source_std = np.asarray(stats["source_std"], dtype=np.float32)
    reference_mean = np.asarray(stats["reference_mean"], dtype=np.float32)
    reference_std = np.asarray(stats["reference_std"], dtype=np.float32)
    valid_pixels = np.asarray(stats["valid_pixels"], dtype=np.uint64)
    scales = np.ones_like(source_mean, dtype=np.float32)
    offsets = np.zeros_like(source_mean, dtype=np.float32)
    statuses: list[list[str]] = []
    empty_tiles = 0
    offset_only_tiles = 0
    ok_tiles = 0
    for row in range(source_mean.shape[0]):
        status_row: list[str] = []
        for col in range(source_mean.shape[1]):
            if int(valid_pixels[row, col]) == 0:
                empty_tiles += 1
                status_row.append("empty")
                continue
            if float(source_std[row, col]) <= eps or float(reference_std[row, col]) <= eps:
                offset_only_tiles += 1
                offsets[row, col] = np.float32(reference_mean[row, col] - source_mean[row, col])
                status_row.append("offset_only")
                continue
            scale = np.float32(reference_std[row, col] / source_std[row, col])
            scales[row, col] = scale
            offsets[row, col] = np.float32(reference_mean[row, col] - source_mean[row, col] * scale)
            ok_tiles += 1
            status_row.append("ok")
        statuses.append(status_row)
    active = valid_pixels > 0
    active_scales = scales[active]
    active_offsets = offsets[active]
    return {
        "scales": scales,
        "offsets": offsets,
        "valid_pixels": valid_pixels,
        "statuses": statuses,
        "empty_tiles": empty_tiles,
        "offset_only_tiles": offset_only_tiles,
        "ok_tiles": ok_tiles,
        "scale_mean": float(np.mean(active_scales)) if active_scales.size else 1.0,
        "scale_min": float(np.min(active_scales)) if active_scales.size else 1.0,
        "scale_max": float(np.max(active_scales)) if active_scales.size else 1.0,
        "offset_mean": float(np.mean(active_offsets)) if active_offsets.size else 0.0,
        "offset_min": float(np.min(active_offsets)) if active_offsets.size else 0.0,
        "offset_max": float(np.max(active_offsets)) if active_offsets.size else 0.0,
        "valid_pixel_total": int(np.sum(valid_pixels, dtype=np.uint64)),
    }


def _simple_snr_weight_from_stats(stats: dict[str, Any], eps: float = 1.0e-6) -> float:
    if int(stats.get("valid_pixels") or 0) <= 0:
        return 0.0
    std = float(stats.get("std") or 0.0)
    mean = abs(float(stats.get("mean") or 0.0))
    if std <= eps:
        return 1.0 / eps
    return max(mean / std, eps)


def _preview_scale(height: int, width: int, target_max_dim: int = 1024) -> int:
    return max(1, (max(int(height), int(width)) + int(target_max_dim) - 1) // int(target_max_dim))


def _registration_preview(image: np.ndarray, scale: int) -> np.ndarray:
    preview = np.asarray(image, dtype=np.float32)[:: int(scale), :: int(scale)]
    return np.ascontiguousarray(np.nan_to_num(preview, nan=0.0, posinf=0.0, neginf=0.0), dtype=np.float32)


def _frame_reference_tokens(frame: dict[str, Any]) -> set[str]:
    path = Path(str(frame.get("path", "")))
    return {str(frame.get("id", "")), path.name, path.stem}


def _frame_header_value(
    frame: dict[str, Any],
    key: str,
    cache: dict[tuple[str, str], Any] | None = None,
) -> Any | None:
    key_upper = str(key).upper()
    summary = frame.get("header_summary", {})
    if isinstance(summary, dict):
        for candidate in (key, key_upper, key_upper.lower()):
            if candidate in summary:
                return summary[candidate]

    path = str(frame.get("path") or "")
    if not path:
        return None
    cache_key = (path, key_upper)
    if cache is not None and cache_key in cache:
        return cache[cache_key]
    value = None
    try:
        from astropy.io import fits

        header = fits.getheader(path, 0)
        value = header.get(key_upper)
    except Exception:
        value = None
    if cache is not None:
        cache[cache_key] = value
    return value


def _normalize_pierside(value: Any | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    if not text:
        return None
    if text in {"e", "east", "pier east", "east side", "east-of-pier"}:
        return "east"
    if text in {"w", "west", "pier west", "west side", "west-of-pier"}:
        return "west"
    return text


def _resident_similarity_frame_dispatch(
    resident_star_prior: str,
    reference_frame: dict[str, Any],
    moving_frame: dict[str, Any],
    header_cache: dict[tuple[str, str], Any] | None = None,
) -> dict[str, Any]:
    if resident_star_prior != "auto_pierside":
        return {
            "prior": resident_star_prior,
            "orientation_mode": "manual",
            "reference_pierside": None,
            "moving_pierside": None,
        }

    reference_pierside = _normalize_pierside(_frame_header_value(reference_frame, "PIERSIDE", header_cache))
    moving_pierside = _normalize_pierside(_frame_header_value(moving_frame, "PIERSIDE", header_cache))
    if reference_pierside and moving_pierside:
        if reference_pierside == moving_pierside:
            return {
                "prior": "ncc",
                "orientation_mode": "pierside_same",
                "reference_pierside": reference_pierside,
                "moving_pierside": moving_pierside,
            }
        return {
            "prior": "none",
            "orientation_mode": "pierside_flipped",
            "reference_pierside": reference_pierside,
            "moving_pierside": moving_pierside,
        }
    return {
        "prior": "ncc",
        "orientation_mode": "pierside_unknown",
        "reference_pierside": reference_pierside,
        "moving_pierside": moving_pierside,
    }


def _find_reference_frame(light_frames: list[dict[str, Any]], reference_frame_id: str | None) -> dict[str, Any]:
    if reference_frame_id:
        for frame in light_frames:
            if str(reference_frame_id) in _frame_reference_tokens(frame):
                return frame
        raise ValueError(f"reference frame was not found in resident light group: {reference_frame_id}")
    return light_frames[0]


def _matches_any_token(frame: dict[str, Any], tokens: set[str]) -> bool:
    return bool(_frame_reference_tokens(frame) & tokens)


def _registration_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = payload.get("registration_results")
    if rows is None:
        rows = payload.get("results", [])
    return [dict(row) for row in rows]


def _registration_matrix(row: dict[str, Any]) -> list[list[float]]:
    matrix = np.asarray(row.get("matrix"), dtype=np.float64)
    if matrix.shape != (3, 3):
        raise ValueError(f"external registration matrix for {row.get('frame_id')} must be 3x3")
    return [[float(value) for value in line] for line in matrix]


def _matrix_is_translation(matrix: list[list[float]], atol: float = 1.0e-6) -> bool:
    m = np.asarray(matrix, dtype=np.float64)
    if m.shape != (3, 3):
        return False
    return bool(
        np.allclose(m[:2, :2], np.eye(2), atol=atol)
        and np.allclose(m[2], np.asarray([0.0, 0.0, 1.0]), atol=atol)
    )


def _float_or_nan(value: Any) -> float:
    if value is None:
        return float("nan")
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _finite_float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(result):
        return None
    return result


def _policy_int(raw: dict[str, Any], key: str, default: int) -> int:
    value = raw.get(key)
    if value is None:
        return int(default)
    return int(value)


def _policy_float(raw: dict[str, Any], key: str, default: float) -> float:
    value = raw.get(key)
    if value is None:
        return float(default)
    return float(value)


def _policy_optional_float(raw: dict[str, Any], key: str, default: float | None) -> float | None:
    value = raw.get(key)
    if value is None:
        return default
    return float(value)


def _policy_bool(raw: dict[str, Any], key: str, default: bool) -> bool:
    value = raw.get(key)
    if value is None:
        return bool(default)
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{key} must be a boolean-like value")


def _apply_resident_registration_matrix(
    stack: Any,
    index: int,
    matrix: list[list[float]],
    interpolation: str = "bilinear",
    clamping_threshold: float = -1.0,
) -> str:
    if _matrix_is_translation(matrix):
        if interpolation == "lanczos3" and hasattr(stack, "apply_matrix_lanczos3_frame"):
            stack.apply_matrix_lanczos3_frame(index, matrix, np.nan, float(clamping_threshold))
            return "matrix_lanczos3"
        stack.apply_translation_bilinear_frame(index, float(matrix[0][2]), float(matrix[1][2]), np.nan)
        return "translation_bilinear"
    if interpolation == "lanczos3":
        if not hasattr(stack, "apply_matrix_lanczos3_frame"):
            raise RuntimeError("resident CUDA backend does not expose matrix Lanczos3 warp")
        stack.apply_matrix_lanczos3_frame(index, matrix, np.nan, float(clamping_threshold))
        return "matrix_lanczos3"
    if not hasattr(stack, "apply_matrix_bilinear_frame"):
        raise RuntimeError("resident CUDA backend does not expose matrix bilinear warp")
    stack.apply_matrix_bilinear_frame(index, matrix, np.nan)
    return "matrix_bilinear"


def _output_diagnostics(data: np.ndarray, weight_map: np.ndarray | None = None) -> dict[str, Any]:
    values = np.asarray(data, dtype=np.float32)
    total_pixels = int(values.size)
    finite_mask = np.isfinite(values)
    finite = values[finite_mask]
    nonfinite_count = total_pixels - int(finite.size)
    if finite.size == 0:
        return {
            "total_pixels": total_pixels,
            "finite_pixels": 0,
            "nonfinite_pixels": nonfinite_count,
            "statistics": None,
            "normalization_probe": None,
            "clipping_probe": {
                "lt_0_count": 0,
                "gt_1_count": 0,
                "gt_65535_count": 0,
                "nonfinite_count": nonfinite_count,
            },
        }

    percentiles = {
        "p001": float(np.percentile(finite, 0.01)),
        "p01": float(np.percentile(finite, 0.1)),
        "p1": float(np.percentile(finite, 1.0)),
        "p50": float(np.percentile(finite, 50.0)),
        "p99": float(np.percentile(finite, 99.0)),
        "p999": float(np.percentile(finite, 99.9)),
        "p9999": float(np.percentile(finite, 99.99)),
    }
    minimum = float(np.min(finite))
    maximum = float(np.max(finite))
    robust_low = percentiles["p01"]
    robust_high = percentiles["p999"]
    robust_span = robust_high - robust_low
    positive_weight_count = None
    zero_weight_count = None
    if weight_map is not None:
        weights = np.asarray(weight_map, dtype=np.float32)
        positive_weight_count = int(np.count_nonzero(weights > 0))
        zero_weight_count = int(weights.size - positive_weight_count)
    clipping = {
        "lt_0_count": int(np.count_nonzero(finite < 0.0)),
        "lt_0_fraction": float(np.mean(finite < 0.0)),
        "gt_1_count": int(np.count_nonzero(finite > 1.0)),
        "gt_1_fraction": float(np.mean(finite > 1.0)),
        "gt_65535_count": int(np.count_nonzero(finite > 65535.0)),
        "gt_65535_fraction": float(np.mean(finite > 65535.0)),
        "nonfinite_count": nonfinite_count,
        "positive_weight_pixels": positive_weight_count,
        "zero_weight_pixels": zero_weight_count,
    }
    return {
        "total_pixels": total_pixels,
        "finite_pixels": int(finite.size),
        "nonfinite_pixels": nonfinite_count,
        "statistics": {
            "min": minimum,
            "max": maximum,
            "mean": float(np.mean(finite)),
            "std": float(np.std(finite)),
            **percentiles,
        },
        "normalization_probe": {
            "method": "diagnostic_only_p0_1_to_p99_9",
            "black": robust_low,
            "white": robust_high,
            "scale": float(1.0 / robust_span) if robust_span > 0 else 1.0,
            "offset": float(-robust_low),
            "would_clip_low_count": int(np.count_nonzero(finite < robust_low)),
            "would_clip_high_count": int(np.count_nonzero(finite > robust_high)),
            "would_clip_low_fraction": float(np.mean(finite < robust_low)),
            "would_clip_high_fraction": float(np.mean(finite > robust_high)),
        },
        "clipping_probe": clipping,
    }


def _count_map_dtype(frame_count: int) -> Any:
    return np.int16 if int(frame_count) <= np.iinfo(np.int16).max else np.int32


def _resident_dq_map(
    master: np.ndarray,
    weight_map: np.ndarray,
    coverage_map: np.ndarray | None,
    low_rejection_map: np.ndarray | None,
    high_rejection_map: np.ndarray | None,
    geometric_warp_coverage_map: np.ndarray | None = None,
    active_frame_count: int = 0,
) -> tuple[np.ndarray, dict[str, int]]:
    dq = np.zeros(np.asarray(master).shape, dtype=np.uint32)
    master_values = np.asarray(master, dtype=np.float32)
    weights = np.asarray(weight_map, dtype=np.float32)
    invalid = (~np.isfinite(master_values)) | (~np.isfinite(weights)) | (weights <= 0.0)
    if coverage_map is not None:
        coverage = np.asarray(coverage_map, dtype=np.float32)
        coverage_invalid = (~np.isfinite(coverage)) | (coverage <= 0.5)
        invalid |= coverage_invalid
        dq[coverage_invalid] |= np.uint32(int(DQFlag.WARP_EDGE))
    if geometric_warp_coverage_map is not None:
        geometric = np.asarray(geometric_warp_coverage_map, dtype=np.float32)
        geometric_invalid = (~np.isfinite(geometric)) | (geometric <= 0.5)
        invalid |= geometric_invalid
        dq[geometric_invalid] |= np.uint32(int(DQFlag.WARP_EDGE))
        expected_count = int(active_frame_count)
        if expected_count > 0:
            geometric_partial = (
                np.isfinite(geometric)
                & (geometric > 0.5)
                & (geometric < float(expected_count) - 0.5)
            )
            dq[geometric_partial] |= np.uint32(int(DQFlag.WARP_EDGE))
    dq[invalid] |= np.uint32(int(DQFlag.NO_DATA))
    if low_rejection_map is not None:
        low = np.asarray(low_rejection_map, dtype=np.float32)
        dq[np.isfinite(low) & (low > 0.0)] |= np.uint32(int(DQFlag.LOW_REJECTED))
    if high_rejection_map is not None:
        high = np.asarray(high_rejection_map, dtype=np.float32)
        dq[np.isfinite(high) & (high > 0.0)] |= np.uint32(int(DQFlag.HIGH_REJECTED))
    return dq, DQMask(dq).summary()


def _resident_coverage_array_stats(data: np.ndarray) -> dict[str, float | int]:
    values = np.asarray(data, dtype=np.float32)
    finite_mask = np.isfinite(values)
    finite_count = int(np.count_nonzero(finite_mask))
    if finite_count == 0:
        return {
            "finite_pixels": 0,
            "min": 0.0,
            "max": 0.0,
            "mean": 0.0,
        }
    return {
        "finite_pixels": finite_count,
        "min": float(np.nanmin(values)),
        "max": float(np.nanmax(values)),
        "mean": float(np.nanmean(values)),
    }


def _resident_dq_coverage_provenance(
    coverage_map: np.ndarray | None,
    low_rejection_map: np.ndarray | None,
    high_rejection_map: np.ndarray | None,
    active_frame_count: int,
    geometric_warp_coverage_map: np.ndarray | None = None,
    geometric_warp_coverage_frame_count: int | None = None,
) -> dict[str, Any]:
    active_count = max(0, int(active_frame_count))
    if coverage_map is None:
        provenance = {
            "available": False,
            "active_frame_count": active_count,
            "reason": "resident integration did not emit a coverage map",
        }
        if geometric_warp_coverage_map is not None:
            geometric = np.asarray(geometric_warp_coverage_map, dtype=np.float32)
            geometric_count = (
                active_count
                if geometric_warp_coverage_frame_count is None
                else max(0, int(geometric_warp_coverage_frame_count))
            )
            finite_geometric = np.isfinite(geometric)
            provenance.update(
                {
                    "geometric_warp_coverage": _resident_coverage_array_stats(geometric),
                    "geometric_warp_coverage_frame_count": geometric_count,
                    "geometric_zero_pixels": int(np.count_nonzero(finite_geometric & (geometric <= 0.5))),
                    "geometric_partial_pixels": int(
                        np.count_nonzero(
                            finite_geometric
                            & (geometric > 0.5)
                            & (geometric < float(geometric_count) - 0.5)
                        )
                        if geometric_count > 0
                        else 0
                    ),
                    "partial_edge_inference": "available_from_geometric_warp_coverage",
                }
            )
        return provenance

    post_rejection = np.asarray(coverage_map, dtype=np.float32)
    finite_pre_rejection = post_rejection.copy()
    source_terms = ["post_rejection_coverage"]
    if low_rejection_map is not None:
        finite_pre_rejection += np.nan_to_num(np.asarray(low_rejection_map, dtype=np.float32), nan=0.0)
        source_terms.append("low_rejection")
    if high_rejection_map is not None:
        finite_pre_rejection += np.nan_to_num(np.asarray(high_rejection_map, dtype=np.float32), nan=0.0)
        source_terms.append("high_rejection")
    geometric = None
    geometric_count = 0
    if geometric_warp_coverage_map is not None:
        geometric = np.asarray(geometric_warp_coverage_map, dtype=np.float32)
        geometric_count = (
            active_count
            if geometric_warp_coverage_frame_count is None
            else max(0, int(geometric_warp_coverage_frame_count))
        )
        source_terms.append("geometric_warp_coverage")

    finite_pre = np.isfinite(finite_pre_rejection)
    finite_post = np.isfinite(post_rejection)
    zero_pre = finite_pre & (finite_pre_rejection <= 0.5)
    partial_pre = (
        finite_pre
        & (finite_pre_rejection > 0.5)
        & (finite_pre_rejection < float(active_count) - 0.5)
        if active_count > 0
        else np.zeros_like(finite_pre, dtype=bool)
    )
    rejection_reduced = finite_pre & finite_post & (post_rejection < finite_pre_rejection - 0.5)
    rejected_samples = finite_pre_rejection - post_rejection
    np.maximum(rejected_samples, 0.0, out=rejected_samples)

    result: dict[str, Any] = {
        "available": True,
        "active_frame_count": active_count,
        "source_terms": source_terms,
        "post_rejection_coverage": _resident_coverage_array_stats(post_rejection),
        "finite_pre_rejection_coverage": _resident_coverage_array_stats(finite_pre_rejection),
        "zero_pre_rejection_pixels": int(np.count_nonzero(zero_pre)),
        "partial_pre_rejection_pixels": int(np.count_nonzero(partial_pre)),
        "post_rejection_zero_pixels": int(np.count_nonzero(finite_post & (post_rejection <= 0.5))),
        "rejection_reduced_pixels": int(np.count_nonzero(rejection_reduced)),
        "rejected_sample_count": float(np.nansum(rejected_samples)),
        "partial_edge_inference": "deferred",
        "note": (
            "finite_pre_rejection_coverage is coverage + low/high rejection counts. "
            "It separates rejection loss from finite contributing samples but is not yet "
            "a pure geometric warp-footprint map."
        ),
    }
    if geometric is not None:
        finite_geometric = np.isfinite(geometric)
        zero_geometric = finite_geometric & (geometric <= 0.5)
        partial_geometric = (
            finite_geometric
            & (geometric > 0.5)
            & (geometric < float(geometric_count) - 0.5)
            if geometric_count > 0
            else np.zeros_like(finite_geometric, dtype=bool)
        )
        full_geometric = (
            finite_geometric & (geometric >= float(geometric_count) - 0.5)
            if geometric_count > 0
            else np.zeros_like(finite_geometric, dtype=bool)
        )
        result.update(
            {
                "geometric_warp_coverage": _resident_coverage_array_stats(geometric),
                "geometric_warp_coverage_frame_count": geometric_count,
                "geometric_frame_count_matches_active": geometric_count == active_count,
                "geometric_zero_pixels": int(np.count_nonzero(zero_geometric)),
                "geometric_partial_pixels": int(np.count_nonzero(partial_geometric)),
                "geometric_full_pixels": int(np.count_nonzero(full_geometric)),
                "partial_edge_inference": "available_from_geometric_warp_coverage",
                "note": (
                    "geometric_warp_coverage is accumulated by the resident CUDA warp path before "
                    "sigma rejection. finite_pre_rejection_coverage remains coverage + low/high "
                    "rejection counts for rejection accounting."
                ),
            }
        )
    return result


def _resident_output_map_selection(policy: str) -> dict[str, bool]:
    if policy not in _RESIDENT_OUTPUT_MAP_POLICIES:
        raise ValueError("resident_output_maps must be audit, science, or minimal")
    return {
        "master": True,
        "weight": policy in {"audit", "science"},
        "coverage": policy in {"audit", "science"},
        "low_rejection": policy == "audit",
        "high_rejection": policy == "audit",
        "dq": policy in {"audit", "science"},
    }


def _count_map_for_write(data: np.ndarray, dtype: Any) -> np.ndarray:
    return np.rint(np.asarray(data)).astype(dtype, copy=False)


def _array_storage_bytes(data: np.ndarray, dtype: Any) -> int:
    return int(np.asarray(data).size * np.dtype(dtype).itemsize)


def _write_one_resident_output(spec: dict[str, Any]) -> tuple[str, float, dict[str, Any]]:
    name = str(spec["name"])
    dtype = spec.get("dtype", np.float32)
    data = spec["data"]
    if spec.get("round_counts"):
        data = _count_map_for_write(data, dtype)
    start = perf_counter()
    write_fits_data(spec["path"], data, spec.get("header"), dtype=dtype)
    elapsed = perf_counter() - start
    storage = {
        "dtype": np.dtype(dtype).name,
        "estimated_data_bytes": _array_storage_bytes(data, dtype),
    }
    return name, elapsed, storage


def _write_resident_outputs(
    specs: list[dict[str, Any]],
    *,
    max_workers: int | None = None,
) -> tuple[float, dict[str, float], dict[str, dict[str, Any]], int]:
    if not specs:
        return 0.0, {}, {}, 0
    worker_count = max(1, min(len(specs), int(max_workers or len(specs))))
    start = perf_counter()
    breakdown: dict[str, float] = {}
    storage: dict[str, dict[str, Any]] = {}
    if worker_count == 1:
        for spec in specs:
            name, elapsed, entry = _write_one_resident_output(spec)
            breakdown[name] = elapsed
            storage[name] = entry
    else:
        with ThreadPoolExecutor(max_workers=worker_count, thread_name_prefix="glass-output") as executor:
            futures = [executor.submit(_write_one_resident_output, spec) for spec in specs]
            for future in futures:
                name, elapsed, entry = future.result()
                breakdown[name] = elapsed
                storage[name] = entry
    return perf_counter() - start, breakdown, storage, worker_count


def _resident_star_threshold_candidates(
    stack: Any,
    reference_index: int,
    moving_index: int,
    fixed_threshold: float,
) -> tuple[list[float], str]:
    if fixed_threshold > 0.0:
        return [float(fixed_threshold)], "fixed"
    if not hasattr(stack, "frame_global_stats"):
        raise RuntimeError("resident star auto-threshold requires frame_global_stats")

    reference_stats = stack.frame_global_stats(reference_index)
    moving_stats = stack.frame_global_stats(moving_index)
    candidates: list[float] = []
    for sigma in _AUTO_STAR_THRESHOLD_SIGMAS:
        frame_thresholds: list[float] = []
        for stats in (reference_stats, moving_stats):
            if int(stats.get("valid_pixels", 0)) <= 0:
                continue
            mean = float(stats["mean"])
            std = float(stats["std"])
            if np.isfinite(mean) and np.isfinite(std) and std > 0.0:
                frame_thresholds.append(max(0.0, mean + float(sigma) * std))
        if frame_thresholds:
            candidates.append(min(frame_thresholds))
    if not candidates:
        candidates.append(30.0)

    unique: list[float] = []
    seen: set[float] = set()
    for threshold in candidates:
        rounded = round(float(threshold), 6)
        if rounded in seen:
            continue
        seen.add(rounded)
        unique.append(float(threshold))
    return unique, "auto_mean_std"


def _resident_star_registration_score(result: dict[str, Any]) -> tuple[int, float, int]:
    inliers = int(result.get("mutual_inliers", 0))
    rms = float(result.get("rms_px", float("nan")))
    finite_rms = rms if np.isfinite(rms) else float("inf")
    support = min(int(result.get("reference_count", 0)), int(result.get("moving_count", 0)))
    return inliers, -finite_rms, support


def _resident_similarity_score(result: dict[str, Any]) -> tuple[int, float, int]:
    inliers = int(result.get("refined_inliers", result.get("inliers", 0)))
    rms = float(result.get("refit_rms_px", result.get("rms_px", float("nan"))))
    finite_rms = rms if np.isfinite(rms) else float("inf")
    support = min(int(result.get("reference_count", 0)), int(result.get("moving_count", 0)))
    return inliers, -finite_rms, support


def _select_star_core_preselected_seed_indices(
    seed_metrics: list[dict[str, Any]],
    max_count: int,
) -> tuple[list[int], dict[str, Any]]:
    max_count = int(max_count)
    if max_count <= 0 or max_count >= len(seed_metrics):
        return list(range(len(seed_metrics))), {
            "enabled": False,
            "requested_top_k": max_count,
            "input_seed_count": len(seed_metrics),
            "selected_seed_count": len(seed_metrics),
            "selected_seed_indices": list(range(len(seed_metrics))),
            "selection_key": "disabled",
        }

    star_core_candidates: list[tuple[int, dict[str, Any]]] = []
    for index, seed in enumerate(seed_metrics):
        star_core_rms = _finite_float_or_none(seed.get("star_core_metric", {}).get("rms"))
        if star_core_rms is not None:
            star_core_candidates.append((index, seed))

    if not star_core_candidates:
        selected = list(range(min(max_count, len(seed_metrics))))
        return selected, {
            "enabled": True,
            "requested_top_k": max_count,
            "input_seed_count": len(seed_metrics),
            "selected_seed_count": len(selected),
            "selected_seed_indices": selected,
            "selection_key": "first_n_no_star_core_metric",
        }

    inlier_values = [
        int(seed["seed_inliers"])
        for _, seed in star_core_candidates
        if seed.get("seed_inliers") is not None
    ]
    if inlier_values:
        max_inliers = max(inlier_values)
        min_inliers = max(0, max_inliers - 2)
        eligible = [
            (index, seed)
            for index, seed in star_core_candidates
            if seed.get("seed_inliers") is None or int(seed["seed_inliers"]) >= min_inliers
        ]
    else:
        max_inliers = None
        min_inliers = None
        eligible = star_core_candidates

    def key(item: tuple[int, dict[str, Any]]) -> tuple[float, int, float, int]:
        index, seed = item
        star_core_rms = _finite_float_or_none(seed.get("star_core_metric", {}).get("rms"))
        inliers = int(seed["seed_inliers"]) if seed.get("seed_inliers") is not None else -1
        seed_rms = _finite_float_or_none(seed.get("seed_rms_px"))
        return (
            float("inf") if star_core_rms is None else star_core_rms,
            -inliers,
            float("inf") if seed_rms is None else seed_rms,
            index,
        )

    selected_set: set[int] = {0}
    for index, _seed in sorted(eligible, key=key):
        selected_set.add(index)
        if len(selected_set) >= max_count:
            break
    if len(selected_set) < max_count:
        for index, _seed in sorted(star_core_candidates, key=key):
            selected_set.add(index)
            if len(selected_set) >= max_count:
                break

    selected = sorted(selected_set)
    return selected, {
        "enabled": True,
        "requested_top_k": max_count,
        "input_seed_count": len(seed_metrics),
        "selected_seed_count": len(selected),
        "selected_seed_indices": selected,
        "star_max_inliers": None if max_inliers is None else int(max_inliers),
        "star_min_inliers_for_core_metric": None if min_inliers is None else int(min_inliers),
        "eligible_seed_count": len(eligible),
        "selection_key": "pre_refine_star_core_rms_with_two_inlier_slack",
    }


def _select_star_guarded_seed(
    seed_metrics: list[dict[str, Any]],
    pixel_selected_index: int,
) -> tuple[int, dict[str, Any]]:
    pixel_selected_index = int(pixel_selected_index)
    if pixel_selected_index < 0 or pixel_selected_index >= len(seed_metrics):
        pixel_selected_index = 0

    star_core_candidates: list[tuple[int, dict[str, Any]]] = []
    for index, seed in enumerate(seed_metrics):
        star_core_rms = _finite_float_or_none(seed.get("star_core_metric", {}).get("rms"))
        if star_core_rms is not None:
            star_core_candidates.append((index, seed))

    if star_core_candidates:
        inlier_values = [
            int(seed["seed_inliers"])
            for _, seed in star_core_candidates
            if seed.get("seed_inliers") is not None
        ]
        if inlier_values:
            max_inliers = max(inlier_values)
            min_inliers = max(0, max_inliers - 2)
            eligible = [
                (index, seed)
                for index, seed in star_core_candidates
                if seed.get("seed_inliers") is None or int(seed["seed_inliers"]) >= min_inliers
            ]
        else:
            max_inliers = None
            min_inliers = None
            eligible = star_core_candidates

        def star_core_key(item: tuple[int, dict[str, Any]]) -> tuple[float, int, float, int]:
            index, seed = item
            star_core_rms = _finite_float_or_none(seed.get("star_core_metric", {}).get("rms"))
            inliers = int(seed["seed_inliers"]) if seed.get("seed_inliers") is not None else -1
            seed_rms = _finite_float_or_none(seed.get("seed_rms_px"))
            return (
                float("inf") if star_core_rms is None else star_core_rms,
                -inliers,
                float("inf") if seed_rms is None else seed_rms,
                index,
            )

        selected_index, _selected = min(eligible, key=star_core_key)
        pixel_seed = seed_metrics[pixel_selected_index]
        return selected_index, {
            "status": "kept_star_core_metric"
            if selected_index == pixel_selected_index
            else "replaced_pixel_metric_with_star_core_metric",
            "pixel_selected_index": pixel_selected_index,
            "pixel_selected_seed_rank": int(pixel_seed.get("seed_rank", pixel_selected_index)),
            "pixel_selected_seed_inliers": pixel_seed.get("seed_inliers"),
            "pixel_selected_seed_rms_px": pixel_seed.get("seed_rms_px"),
            "selected_index": selected_index,
            "star_max_inliers": None if max_inliers is None else int(max_inliers),
            "star_min_inliers_for_core_metric": None if min_inliers is None else int(min_inliers),
            "eligible_seed_count": len(eligible),
            "selection_key": "star_core_rms_with_two_inlier_slack",
        }

    star_candidates: list[tuple[int, dict[str, Any]]] = []
    for index, seed in enumerate(seed_metrics):
        inliers = seed.get("seed_inliers")
        rms_px = _finite_float_or_none(seed.get("seed_rms_px"))
        if inliers is None or rms_px is None:
            continue
        star_candidates.append((index, seed))

    if not star_candidates:
        return pixel_selected_index, {
            "status": "pixel_metric_only_no_star_metadata",
            "pixel_selected_index": pixel_selected_index,
            "selected_index": pixel_selected_index,
            "eligible_seed_count": 0,
            "selection_key": "pixel_metric_rms",
        }

    max_inliers = max(int(seed["seed_inliers"]) for _, seed in star_candidates)
    eligible = [(index, seed) for index, seed in star_candidates if int(seed["seed_inliers"]) == max_inliers]

    def key(item: tuple[int, dict[str, Any]]) -> tuple[float, float, int]:
        index, seed = item
        metric_rms = _finite_float_or_none(seed.get("metrics", {}).get("rms"))
        seed_rms = _finite_float_or_none(seed.get("seed_rms_px"))
        return (
            float("inf") if metric_rms is None else metric_rms,
            float("inf") if seed_rms is None else seed_rms,
            index,
        )

    selected_index, _selected = min(eligible, key=key)
    pixel_seed = seed_metrics[pixel_selected_index]
    return selected_index, {
        "status": "kept_pixel_metric" if selected_index == pixel_selected_index else "replaced_pixel_metric",
        "pixel_selected_index": pixel_selected_index,
        "pixel_selected_seed_rank": int(pixel_seed.get("seed_rank", pixel_selected_index)),
        "pixel_selected_seed_inliers": pixel_seed.get("seed_inliers"),
        "pixel_selected_seed_rms_px": pixel_seed.get("seed_rms_px"),
        "selected_index": selected_index,
        "star_max_inliers": int(max_inliers),
        "eligible_seed_count": len(eligible),
        "selection_key": "max_seed_inliers_then_pixel_rms_then_seed_rms",
    }


def _annotate_resident_star_core_metrics(
    stack: Any,
    reference_index: int,
    moving_index: int,
    seed_metrics: list[dict[str, Any]],
    threshold: float,
) -> dict[str, Any]:
    matrices = np.asarray([seed["matrix"] for seed in seed_metrics], dtype=np.float32)
    t0 = perf_counter()
    result = stack.star_core_metrics_candidates_to_reference(reference_index, moving_index, matrices, float(threshold))
    elapsed = perf_counter() - t0
    candidate_metrics = list(result["candidate_metrics"])
    available_pixels = 0
    for item in candidate_metrics:
        local_seed_index = int(item["seed_index"])
        metrics = dict(item["metrics"])
        seed_metrics[local_seed_index]["star_core_metric"] = metrics
        available_pixels = max(available_pixels, int(metrics.get("valid_pixels", 0)))
    return {
        "elapsed_s": elapsed,
        "threshold": float(result["threshold"]),
        "available_pixels": int(available_pixels),
        "sampled_pixels": int(result["sampled_pixels"]),
        "candidate_count": int(result["candidate_count"]),
        "model": str(result["model"]),
    }


def _group_map(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(group["group_id"]): group for group in plan.get("groups", [])}


def _find_matching_bias_for_group(
    target_group: dict[str, Any] | None,
    groups: dict[str, dict[str, Any]],
) -> str | None:
    if target_group is None:
        return None
    for group_id, group in groups.items():
        if group.get("group_type") != "bias":
            continue
        if (
            group.get("gain") == target_group.get("gain")
            and group.get("offset") == target_group.get("offset")
            and group.get("binning") == target_group.get("binning")
            and group.get("shape") == target_group.get("shape")
        ):
            return group_id
    return None


def _records_for_group(
    group_id: str | None,
    frames: dict[str, dict[str, Any]],
    groups: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    if group_id is None or group_id not in groups:
        return []
    return [frames[frame_id] for frame_id in groups[group_id].get("frames", []) if frame_id in frames]


def _light_calibration_groups(plan: dict[str, Any]) -> dict[str, dict[str, str | None]]:
    by_frame: dict[str, dict[str, str | None]] = {}
    for light_plan in plan.get("light_plans", []):
        for frame_id in light_plan.get("frames", []):
            by_frame[str(frame_id)] = {
                "bias_group": light_plan.get("matching_bias_group"),
                "dark_group": light_plan.get("matching_dark_group"),
                "flat_group": light_plan.get("matching_flat_group"),
            }
    return by_frame


def _master_set_cache_key(
    filter_name: str | None,
    height: int,
    width: int,
    bias_group: str | None,
    dark_group: str | None,
    flat_group: str | None,
) -> str:
    return (
        f"{_safe_filter_name(filter_name)}_{width}x{height}_"
        f"bias-{bias_group or 'none'}_dark-{dark_group or 'none'}_flat-{flat_group or 'none'}"
    )


def _record_cache_token(record: dict[str, Any]) -> dict[str, Any]:
    path = Path(str(record.get("path") or ""))
    stat: dict[str, Any]
    try:
        info = path.stat()
        stat = {"size": int(info.st_size), "mtime_ns": int(info.st_mtime_ns)}
    except OSError:
        stat = {"missing": True}
    return {
        "id": record.get("id"),
        "path": str(path),
        "exposure_s": record.get("exposure_s"),
        "gain": record.get("gain"),
        "offset": record.get("offset"),
        "temperature_c": record.get("temperature_c"),
        "width": record.get("width"),
        "height": record.get("height"),
        **stat,
    }


def _master_cache_fingerprint(
    *,
    filter_name: str | None,
    height: int,
    width: int,
    bias_group: str | None,
    dark_group: str | None,
    flat_group: str | None,
    flat_bias_group: str | None,
    bias_records: list[dict[str, Any]],
    dark_records: list[dict[str, Any]],
    flat_records: list[dict[str, Any]],
    flat_bias_records: list[dict[str, Any]],
    policy: CalibrationPolicy,
) -> str:
    payload = {
        "schema_version": 1,
        "filter": filter_name,
        "shape": {"height": int(height), "width": int(width)},
        "groups": {
            "bias": bias_group,
            "dark": dark_group,
            "flat": flat_group,
            "flat_bias": flat_bias_group,
        },
        "policy": asdict(policy),
        "records": {
            "bias": [_record_cache_token(record) for record in bias_records],
            "dark": [_record_cache_token(record) for record in dark_records],
            "flat": [_record_cache_token(record) for record in flat_records],
            "flat_bias": [_record_cache_token(record) for record in flat_bias_records],
        },
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _resident_master_cache_root(run: Path, master_cache_dir: str | Path | None) -> tuple[Path, str]:
    if master_cache_dir is None:
        return run / "calib_cache" / "resident_masters", "run"
    return Path(master_cache_dir), "shared"


def _master_cache_paths(cache: Path, key: str) -> dict[str, Path]:
    return {
        "bias": cache / f"{key}_master_bias.npy",
        "dark": cache / f"{key}_master_dark.npy",
        "flat": cache / f"{key}_master_flat.npy",
        "stats": cache / f"{key}_master_stats.json",
    }


def _cached_master_files_complete(paths: dict[str, Path], stats: dict[str, Any]) -> bool:
    return (
        (int(stats.get("bias_count") or 0) <= 0 or paths["bias"].exists())
        and (int(stats.get("dark_count") or 0) <= 0 or paths["dark"].exists())
        and (int(stats.get("flat_count") or 0) <= 0 or paths["flat"].exists())
    )


def _load_or_build_matching_masters(
    run: Path,
    filter_name: str | None,
    height: int,
    width: int,
    frames: dict[str, dict[str, Any]],
    groups: dict[str, dict[str, Any]],
    bias_group: str | None,
    dark_group: str | None,
    flat_group: str | None,
    policy: CalibrationPolicy,
    master_cache_dir: str | Path | None = None,
) -> tuple[np.ndarray | None, np.ndarray | None, np.ndarray | None, dict[str, Any], float | None]:
    cache, cache_scope = _resident_master_cache_root(run, master_cache_dir)
    cache.mkdir(parents=True, exist_ok=True)
    base_key = _master_set_cache_key(filter_name, height, width, bias_group, dark_group, flat_group)
    bias_records = _records_for_group(bias_group, frames, groups)
    dark_records = _records_for_group(dark_group, frames, groups)
    flat_records = _records_for_group(flat_group, frames, groups)
    flat_group_record = groups.get(flat_group or "")
    flat_bias_group = _find_matching_bias_for_group(flat_group_record, groups)
    flat_bias_records = [] if flat_bias_group == bias_group else _records_for_group(flat_bias_group, frames, groups)
    fingerprint = _master_cache_fingerprint(
        filter_name=filter_name,
        height=height,
        width=width,
        bias_group=bias_group,
        dark_group=dark_group,
        flat_group=flat_group,
        flat_bias_group=flat_bias_group,
        bias_records=bias_records,
        dark_records=dark_records,
        flat_records=flat_records,
        flat_bias_records=flat_bias_records,
        policy=policy,
    )
    key = f"{base_key}_{fingerprint[:16]}"
    paths = _master_cache_paths(cache, key)
    stats_path = paths["stats"]
    if stats_path.exists():
        stats = read_json(stats_path)
        if stats.get("cache_fingerprint") == fingerprint and _cached_master_files_complete(paths, stats):
            stats = {**stats, "cache_hit": True, "cache_scope": cache_scope, "cache_dir": str(cache)}
            master_bias = np.load(paths["bias"]) if paths["bias"].exists() else None
            master_dark = np.load(paths["dark"]) if paths["dark"].exists() else None
            master_flat = np.load(paths["flat"]) if paths["flat"].exists() else None
            return master_bias, master_dark, master_flat, stats, stats.get("dark_exposure_s")

    master_bias = None
    bias_paths = _paths_for_records(bias_records)
    if bias_paths:
        master_bias = make_master_bias(bias_paths).data

    master_dark = None
    dark_paths = _paths_for_records(dark_records)
    if dark_paths:
        dark_bias = None if policy.master_dark_includes_bias else master_bias
        master_dark = make_master_dark(dark_paths, dark_bias).data

    master_flat = None
    flat_paths = _paths_for_records(flat_records)
    if flat_paths:
        flat_bias = master_bias
        if flat_bias_group != bias_group:
            flat_bias_paths = _paths_for_records(flat_bias_records)
            flat_bias = make_master_bias(flat_bias_paths).data if flat_bias_paths else None
        master_flat = make_master_flat(
            flat_paths,
            master_bias=flat_bias,
            normalization=policy.flat_normalization,
            flat_floor=policy.flat_floor,
        ).data

    dark_exposures = [
        float(frame["exposure_s"]) for frame in dark_records if frame.get("exposure_s") is not None
    ]
    dark_exposure = float(np.median(dark_exposures)) if dark_exposures else None
    stats = {
        "calibration_group_policy": "planner_matching_groups_per_light",
        "filter": filter_name,
        "shape": {"height": height, "width": width},
        "bias_group": bias_group,
        "dark_group": dark_group,
        "flat_group": flat_group,
        "flat_bias_group": flat_bias_group,
        "bias_count": len(bias_paths),
        "dark_count": len(dark_paths),
        "flat_count": len(flat_paths),
        "dark_exposure_s": dark_exposure,
        "bias": None if master_bias is None else image_stats(master_bias),
        "dark": None if master_dark is None else image_stats(master_dark),
        "flat": None if master_flat is None else image_stats(master_flat),
        "master_dark_includes_bias": policy.master_dark_includes_bias,
        "cache_hit": False,
        "cache_scope": cache_scope,
        "cache_dir": str(cache),
        "cache_key": key,
        "cache_base_key": base_key,
        "cache_fingerprint": fingerprint,
    }
    if master_bias is not None:
        np.save(paths["bias"], master_bias)
    if master_dark is not None:
        np.save(paths["dark"], master_dark)
    if master_flat is not None:
        np.save(paths["flat"], master_flat)
    write_json(stats_path, stats)
    return master_bias, master_dark, master_flat, stats, dark_exposure


def _load_or_build_aggregate_masters(
    run: Path,
    filter_name: str | None,
    height: int,
    width: int,
    bias_records: list[dict[str, Any]],
    dark_records: list[dict[str, Any]],
    flat_records: list[dict[str, Any]],
    policy: CalibrationPolicy,
) -> tuple[np.ndarray | None, np.ndarray | None, np.ndarray | None, dict[str, Any]]:
    cache = run / "calib_cache" / "resident_masters"
    cache.mkdir(parents=True, exist_ok=True)
    key = f"aggregate_{_safe_filter_name(filter_name)}_{width}x{height}"
    bias_path = cache / f"{key}_master_bias.npy"
    dark_path = cache / f"{key}_master_dark.npy"
    flat_path = cache / f"{key}_master_flat.npy"
    stats_path = cache / f"{key}_master_stats.json"
    if bias_path.exists() and dark_path.exists() and flat_path.exists() and stats_path.exists():
        return np.load(bias_path), np.load(dark_path), np.load(flat_path), read_json(stats_path)

    master_bias = None
    bias_paths = _paths_for_records(bias_records)
    if bias_paths:
        master_bias = make_master_bias(bias_paths).data

    master_dark = None
    dark_paths = _paths_for_records(dark_records)
    if dark_paths:
        dark_bias = None if policy.master_dark_includes_bias else master_bias
        master_dark = make_master_dark(dark_paths, dark_bias).data

    master_flat = None
    flat_paths = _paths_for_records(flat_records)
    if flat_paths:
        master_flat = make_master_flat(
            flat_paths,
            master_bias=master_bias,
            normalization=policy.flat_normalization,
            flat_floor=policy.flat_floor,
        ).data

    stats = {
        "calibration_group_policy": "aggregate_same_shape_filter_for_resident_mode",
        "filter": filter_name,
        "bias_count": len(bias_paths),
        "dark_count": len(dark_paths),
        "flat_count": len(flat_paths),
        "bias": None if master_bias is None else image_stats(master_bias),
        "dark": None if master_dark is None else image_stats(master_dark),
        "flat": None if master_flat is None else image_stats(master_flat),
        "master_dark_includes_bias": policy.master_dark_includes_bias,
    }
    if master_bias is not None:
        np.save(bias_path, master_bias)
    if master_dark is not None:
        np.save(dark_path, master_dark)
    if master_flat is not None:
        np.save(flat_path, master_flat)
    write_json(stats_path, stats)
    return master_bias, master_dark, master_flat, stats


def run_resident_calibration_integration(
    plan_path: str | Path,
    run_dir: str | Path,
    integration_weighting: str = "auto",
    integration_rejection: str = "none",
    flat_floor: float | None = None,
    resident_registration: str = "off",
    resident_registration_max_shift: int = 128,
    resident_ncc_sample_stride: int = 1,
    resident_ncc_fallback_score_threshold: float = 0.0,
    resident_subpixel_radius_steps: int = 4,
    resident_subpixel_step: float = 0.25,
    resident_star_threshold: float = 30.0,
    resident_star_max_candidates: int = 64,
    resident_star_tolerance_px: float = 1.0,
    resident_star_grid_cols: int = 0,
    resident_star_grid_rows: int = 0,
    resident_star_prior: str = "none",
    resident_star_prior_radius_px: float = 4.0,
    resident_star_core_preselect_top_k: int = 0,
    resident_triangle_pixel_refine_coarse_stride: int | None = None,
    resident_triangle_pixel_refine_final_stride: int | None = None,
    resident_registration_results: str | Path | None = None,
    resident_warp_interpolation: str = "bilinear",
    resident_warp_clamping_threshold: float = -1.0,
    reference_frame_id: str | None = None,
    exclude_frame_ids: list[str] | None = None,
    local_normalization: str = "off",
    resident_local_normalization_mode: str = "global_mean_std",
    resident_local_normalization_tile_size: int = 512,
    resident_prefetch_frames: int = 0,
    resident_prefetch_workers: int = 1,
    resident_h2d_mode: str = "pageable",
    resident_master_cache_dir: str | Path | None = None,
    resident_output_maps: str = "audit",
) -> RunState:
    if integration_rejection not in {"auto", "none", "sigma_clip", "winsorized_sigma"}:
        raise ValueError("resident CUDA mode supports rejection=none, sigma_clip, or winsorized_sigma")
    if integration_weighting not in {"auto", "none", "simple_snr"}:
        raise ValueError("resident CUDA mode supports integration weighting=none or simple_snr")
    if resident_output_maps not in _RESIDENT_OUTPUT_MAP_POLICIES:
        raise ValueError("resident_output_maps must be audit, science, or minimal")
    if resident_registration not in {
        "off",
        "translation_preview",
        "translation_ncc_subpixel",
        "translation_star_catalog",
        "similarity_cuda_catalog",
        "similarity_cuda_triangle",
        "external_matrix",
    }:
        raise ValueError(
            "resident_registration must be off, translation_preview, translation_ncc_subpixel, "
            "translation_star_catalog, similarity_cuda_catalog, similarity_cuda_triangle, or external_matrix"
        )
    if local_normalization not in {"auto", "on", "off"}:
        raise ValueError("local_normalization must be auto, on, or off")
    if resident_local_normalization_mode not in {"global_mean_std", "grid_mean_std"}:
        raise ValueError("resident_local_normalization_mode must be global_mean_std or grid_mean_std")
    if resident_local_normalization_tile_size <= 0:
        raise ValueError("resident_local_normalization_tile_size must be positive")
    if resident_registration_max_shift < 0:
        raise ValueError("resident_registration_max_shift must be non-negative")
    if resident_warp_interpolation not in {"bilinear", "lanczos3"}:
        raise ValueError("resident_warp_interpolation must be bilinear or lanczos3")
    if resident_ncc_sample_stride <= 0:
        raise ValueError("resident_ncc_sample_stride must be positive")
    if resident_ncc_fallback_score_threshold < 0.0 or resident_ncc_fallback_score_threshold > 1.0:
        raise ValueError("resident_ncc_fallback_score_threshold must be in [0, 1]")
    if resident_subpixel_radius_steps < 0:
        raise ValueError("resident_subpixel_radius_steps must be non-negative")
    if resident_subpixel_step <= 0:
        raise ValueError("resident_subpixel_step must be positive")
    if resident_star_max_candidates <= 0:
        raise ValueError("resident_star_max_candidates must be positive")
    if resident_star_tolerance_px < 0:
        raise ValueError("resident_star_tolerance_px must be non-negative")
    if resident_star_prior not in {"none", "ncc", "auto_pierside"}:
        raise ValueError("resident_star_prior must be none, ncc, or auto_pierside")
    if resident_star_prior_radius_px < 0:
        raise ValueError("resident_star_prior_radius_px must be non-negative")
    if resident_star_core_preselect_top_k < 0:
        raise ValueError("resident_star_core_preselect_top_k must be non-negative")
    if resident_triangle_pixel_refine_coarse_stride is not None and resident_triangle_pixel_refine_coarse_stride <= 0:
        raise ValueError("resident_triangle_pixel_refine_coarse_stride must be positive when provided")
    if resident_triangle_pixel_refine_final_stride is not None and resident_triangle_pixel_refine_final_stride <= 0:
        raise ValueError("resident_triangle_pixel_refine_final_stride must be positive when provided")
    if resident_prefetch_frames < 0:
        raise ValueError("resident_prefetch_frames must be non-negative")
    if resident_prefetch_workers <= 0:
        raise ValueError("resident_prefetch_workers must be positive")
    if resident_h2d_mode not in {"pageable", "pinned_async", "pinned_ring"}:
        raise ValueError("resident_h2d_mode must be one of: pageable, pinned_async, pinned_ring")
    if resident_h2d_mode == "pinned_ring" and resident_prefetch_frames <= 0:
        raise ValueError("resident_h2d_mode=pinned_ring requires resident_prefetch_frames > 0")
    if (resident_star_grid_cols > 0 or resident_star_grid_rows > 0) and (
        resident_star_grid_cols <= 0 or resident_star_grid_rows <= 0
    ):
        raise ValueError("resident star grid dimensions must both be positive")
    resident_matrix_warp_method = (
        "apply_matrix_lanczos3_frame"
        if resident_warp_interpolation == "lanczos3"
        else "apply_matrix_bilinear_frame"
    )

    cuda_module = _cuda_module_required()
    plan = read_json(plan_path)
    run = Path(run_dir)
    run.mkdir(parents=True, exist_ok=True)
    shared_master_cache_dir = None if resident_master_cache_dir is None else Path(resident_master_cache_dir)
    if shared_master_cache_dir is not None:
        shared_master_cache_dir.mkdir(parents=True, exist_ok=True)
    state = RunState(run_id=run.name or "glass-run", created_at=now_iso(), current_stage="resident_calibration")

    frames = _frame_map(plan)
    groups = _group_map(plan)
    light_calibration_groups = _light_calibration_groups(plan)
    policy = _policy_from_plan(plan)
    if flat_floor is not None:
        if flat_floor <= 0:
            raise ValueError("flat_floor override must be positive")
        policy.flat_floor = float(flat_floor)
    integration_policy = plan.get("integration_policy", {})
    registration_policy = plan.get("registration_policy", {})
    excluded_tokens = {str(item) for item in (exclude_frame_ids or []) if str(item)}
    weighting_mode = (
        str(integration_policy.get("weighting") or "none")
        if integration_weighting == "auto"
        else integration_weighting
    )
    if weighting_mode not in {"none", "simple_snr"}:
        raise ValueError("resident CUDA mode supports resolved integration weighting=none or simple_snr")
    rejection_mode = "none" if integration_rejection == "auto" else integration_rejection
    low_sigma = float(integration_policy.get("low_sigma", 3.0))
    high_sigma = float(integration_policy.get("high_sigma", 3.0))
    external_registration_path: Path | None = None
    external_registration_by_frame: dict[str, dict[str, Any]] = {}
    external_reference_frame_id: str | None = None
    if resident_registration == "external_matrix":
        external_registration_path = (
            Path(resident_registration_results) if resident_registration_results is not None else run / "registration_results.json"
        )
        if not external_registration_path.exists():
            raise ValueError(f"external resident registration results not found: {external_registration_path}")
        external_registration_payload = read_json(external_registration_path)
        external_registration_by_frame = {
            str(row.get("frame_id")): row for row in _registration_rows(external_registration_payload)
        }
        if not external_registration_by_frame:
            raise ValueError("external resident registration results contain no frame rows")
        if external_registration_payload.get("reference_frame_id") is not None:
            external_reference_frame_id = str(external_registration_payload["reference_frame_id"])
    output_dir = run / "integration"
    output_dir.mkdir(parents=True, exist_ok=True)
    header_cache: dict[tuple[str, str], Any] = {}

    resident_artifacts: list[dict[str, Any]] = []
    outputs: list[dict[str, Any]] = []
    frame_weights: dict[str, float] = {}
    registration_results: list[RegistrationResult] = []
    local_norm_groups: list[dict[str, Any]] = []

    try:
        all_lights = _frames_by_type(plan, "light")
        light_groups: dict[tuple[str | None, int, int], list[dict[str, Any]]] = {}
        for frame in all_lights:
            height = int(frame["height"])
            width = int(frame["width"])
            light_groups.setdefault((frame.get("filter"), height, width), []).append(frame)

        for (filter_name, height, width), light_frames in light_groups.items():
            height = int(light_frames[0]["height"])
            width = int(light_frames[0]["width"])
            filt = _safe_filter_name(filter_name)
            master_elapsed = 0.0
            master_stats_sets: dict[str, Any] = {}

            allocate_start = perf_counter()
            stack = cuda_module.ResidentCalibratedStack(len(light_frames), height, width)
            allocate_elapsed = perf_counter() - allocate_start
            coverage_native_stack = getattr(stack, "_impl", stack)
            resident_warp_coverage_supported = all(
                hasattr(coverage_native_stack, name)
                for name in (
                    "reset_warp_coverage",
                    "accumulate_full_warp_coverage_frame",
                    "warp_coverage_map",
                )
            )
            warped_frame_indices: set[int] = set()
            if resident_warp_coverage_supported:
                stack.reset_warp_coverage()

            registration_start = perf_counter()
            selected_reference_frame_id = reference_frame_id or external_reference_frame_id
            reference_frame = _find_reference_frame(light_frames, selected_reference_frame_id)
            reference_index = next(
                index for index, frame in enumerate(light_frames) if frame["id"] == reference_frame["id"]
            )
            reference_preview = None
            preview_scale = 1
            if resident_registration == "translation_preview":
                preview_scale = _preview_scale(height, width)
                reference_image = read_fits_data(reference_frame["path"], dtype=np.float32)
                reference_preview = _registration_preview(reference_image, preview_scale)
                del reference_image
                gc.collect()
            registration_setup_elapsed = perf_counter() - registration_start

            load_calibrate_start = perf_counter()
            per_frame_s = []
            per_frame_read_s: list[float] = []
            per_frame_read_worker_s: list[float] = []
            per_frame_fits_open_s: list[float] = []
            per_frame_fits_materialize_decode_s: list[float] = []
            per_frame_calibrate_s: list[float] = []
            per_frame_host_copy_s: list[float] = []
            per_frame_h2d_s: list[float] = []
            per_frame_calibrate_store_s: list[float] = []
            per_frame_registration_s = []
            registration_component_s: dict[str, float] = {}
            registration_during_load_elapsed = 0.0
            gc_elapsed = 0.0
            frame_weight_values: list[float] = []
            current_master_key: str | None = None
            current_dark_exposure: float | None = None
            prefetch_host_pinned_bytes = 0
            with _LightPrefetcher(
                light_frames,
                resident_prefetch_frames,
                resident_prefetch_workers,
                pinned_ring=resident_h2d_mode == "pinned_ring",
                height=height,
                width=width,
            ) as light_prefetch:
                prefetch_host_pinned_bytes = light_prefetch.host_pinned_bytes
                for index, frame in enumerate(light_frames):
                    frame_start = perf_counter()
                    calibration_groups = light_calibration_groups.get(str(frame["id"]), {})
                    bias_group = calibration_groups.get("bias_group")
                    dark_group = calibration_groups.get("dark_group")
                    flat_group = calibration_groups.get("flat_group")
                    master_key = _master_set_cache_key(
                        filter_name,
                        height,
                        width,
                        bias_group,
                        dark_group,
                        flat_group,
                    )
                    if master_key != current_master_key:
                        master_set_start = perf_counter()
                        master_bias, master_dark, master_flat, stats, dark_exposure = _load_or_build_matching_masters(
                            run,
                            filter_name,
                            height,
                            width,
                            frames,
                            groups,
                            bias_group,
                            dark_group,
                            flat_group,
                            policy,
                            master_cache_dir=shared_master_cache_dir,
                        )
                        stack.set_calibration_masters(master_bias, master_dark, master_flat)
                        master_elapsed += perf_counter() - master_set_start
                        master_stats_sets[master_key] = stats
                        current_master_key = master_key
                        current_dark_exposure = None if dark_exposure is None else float(dark_exposure)
                        del master_bias, master_dark, master_flat
                        gc_start = perf_counter()
                        gc.collect()
                        gc_elapsed += perf_counter() - gc_start
                    light, read_profile, read_wait_elapsed = light_prefetch.result(index)
                    per_frame_read_worker_s.append(float(read_profile.get("total", 0.0)))
                    per_frame_fits_open_s.append(float(read_profile.get("fits_open", 0.0)))
                    per_frame_fits_materialize_decode_s.append(
                        float(read_profile.get("fits_materialize_decode", 0.0))
                    )
                    per_frame_read_s.append(read_wait_elapsed)
                    calibrate_start = perf_counter()
                    try:
                        if resident_h2d_mode == "pinned_async":
                            calibration_timing = stack.calibrate_frame_pinned_async_timed(
                                index,
                                light,
                                float(frame.get("exposure_s") or 0.0),
                                current_dark_exposure,
                                asdict(policy),
                            )
                        elif resident_h2d_mode == "pinned_ring":
                            calibration_timing = stack.calibrate_frame_host_async_timed(
                                index,
                                light,
                                float(frame.get("exposure_s") or 0.0),
                                current_dark_exposure,
                                asdict(policy),
                            )
                        else:
                            calibration_timing = stack.calibrate_frame_timed(
                                index,
                                light,
                                float(frame.get("exposure_s") or 0.0),
                                current_dark_exposure,
                                asdict(policy),
                            )
                    finally:
                        light_prefetch.release(index)
                    per_frame_calibrate_s.append(perf_counter() - calibrate_start)
                    per_frame_host_copy_s.append(float(calibration_timing.get("host_copy_s", 0.0)))
                    per_frame_h2d_s.append(float(calibration_timing.get("h2d_s", 0.0)))
                    per_frame_calibrate_store_s.append(float(calibration_timing.get("calibrate_store_s", 0.0)))
                    frame_weight = 1.0
                    if resident_registration == "translation_preview":
                        registration_frame_start = perf_counter()
                        warnings = []
                        status = "excluded" if _matches_any_token(frame, excluded_tokens) else "ok"
                        dx = 0.0
                        dy = 0.0
                        try:
                            if status == "excluded":
                                frame_weight = 0.0
                                warnings.append("excluded by resident frame mask")
                            elif frame["id"] != reference_frame["id"]:
                                preview = _registration_preview(light, preview_scale)
                                if reference_preview is None:
                                    raise RuntimeError("reference preview is not available")
                                preview_dx, preview_dy = estimate_translation_phase_correlation(
                                    reference_preview, preview
                                )
                                dx = float(preview_dx * preview_scale)
                                dy = float(preview_dy * preview_scale)
                                stack.apply_translation_frame(index, int(round(dx)), int(round(dy)), np.nan)
                                warped_frame_indices.add(index)
                            else:
                                status = "reference"
                        except Exception as exc:
                            status = "failed"
                            frame_weight = 0.0
                            warnings.append(str(exc))
                        registration_elapsed = perf_counter() - registration_frame_start
                        registration_during_load_elapsed += registration_elapsed
                        per_frame_registration_s.append(registration_elapsed)
                        registration_results.append(
                            RegistrationResult(
                                frame_id=str(frame["id"]),
                                reference_frame_id=str(reference_frame["id"]),
                                transform_model="translation_preview",
                                matrix=translation_matrix(dx, dy),
                                matched_stars=0,
                                inliers=0 if status in {"failed", "excluded"} else 1,
                                rms_px=0.0 if status not in {"failed", "excluded"} else float("nan"),
                                status=status,
                                warnings=warnings
                                + [
                                    f"preview_scale={preview_scale}",
                                    "phase-correlation preview registration; no star-model RMS yet",
                                ],
                            )
                        )
                    per_frame_s.append(perf_counter() - frame_start)
                    if resident_registration == "off" and _matches_any_token(frame, excluded_tokens):
                        frame_weight = 0.0
                    frame_weights[frame["id"]] = frame_weight
                    frame_weight_values.append(frame_weight)
                    del light
                    if index % 10 == 9:
                        gc_start = perf_counter()
                        gc.collect()
                        gc_elapsed += perf_counter() - gc_start
            load_calibrate_elapsed = perf_counter() - load_calibrate_start

            if resident_registration == "translation_ncc_subpixel":
                for index, frame in enumerate(light_frames):
                    registration_frame_start = perf_counter()
                    warnings = []
                    status = "excluded" if _matches_any_token(frame, excluded_tokens) else "ok"
                    dx = 0.0
                    dy = 0.0
                    score = float("nan")
                    try:
                        if status == "excluded":
                            frame_weight_values[index] = 0.0
                            frame_weights[frame["id"]] = 0.0
                            warnings.append("excluded by resident frame mask")
                        elif frame["id"] == reference_frame["id"]:
                            status = "reference"
                        else:
                            coarse = stack.estimate_translation_to_reference(
                                reference_index,
                                index,
                                resident_registration_max_shift,
                                resident_registration_max_shift,
                                resident_ncc_sample_stride,
                            )
                            refined = stack.estimate_translation_subpixel_to_reference(
                                reference_index,
                                index,
                                float(coarse["dx"]),
                                float(coarse["dy"]),
                                resident_subpixel_radius_steps,
                                resident_subpixel_step,
                                resident_ncc_sample_stride,
                            )
                            fallback_used = False
                            original_refined = refined
                            original_score = float(refined["score"])
                            if (
                                resident_ncc_sample_stride > 1
                                and resident_ncc_fallback_score_threshold > 0.0
                                and original_score <= resident_ncc_fallback_score_threshold
                            ):
                                coarse = stack.estimate_translation_to_reference(
                                    reference_index,
                                    index,
                                    resident_registration_max_shift,
                                    resident_registration_max_shift,
                                    1,
                                )
                                refined = stack.estimate_translation_subpixel_to_reference(
                                    reference_index,
                                    index,
                                    float(coarse["dx"]),
                                    float(coarse["dy"]),
                                    resident_subpixel_radius_steps,
                                    resident_subpixel_step,
                                    1,
                                )
                                fallback_used = True
                            dx = float(refined["dx"])
                            dy = float(refined["dy"])
                            score = float(refined["score"])
                            stack.apply_translation_bilinear_frame(index, dx, dy, np.nan)
                            warped_frame_indices.add(index)
                            warnings.extend(
                                [
                                    f"coarse_dx={int(coarse['dx'])}",
                                    f"coarse_dy={int(coarse['dy'])}",
                                    f"coarse_score={float(coarse['score']):.6g}",
                                    f"subpixel_score={score:.6g}",
                                    f"ncc_sample_stride={resident_ncc_sample_stride}",
                                ]
                            )
                            if fallback_used:
                                warnings.extend(
                                    [
                                        "ncc_fallback_stride=1",
                                        (
                                            "ncc_fallback_reason="
                                            f"score_below_{resident_ncc_fallback_score_threshold:.6g}"
                                        ),
                                        f"ncc_original_dx={float(original_refined['dx']):.6g}",
                                        f"ncc_original_dy={float(original_refined['dy']):.6g}",
                                        f"ncc_original_score={original_score:.6g}",
                                        f"ncc_fallback_coarse_dx={int(coarse['dx'])}",
                                        f"ncc_fallback_coarse_dy={int(coarse['dy'])}",
                                        f"ncc_fallback_coarse_score={float(coarse['score']):.6g}",
                                        f"ncc_fallback_subpixel_score={score:.6g}",
                                    ]
                                )
                    except Exception as exc:
                        status = "failed"
                        frame_weight_values[index] = 0.0
                        frame_weights[frame["id"]] = 0.0
                        warnings.append(str(exc))
                    per_frame_registration_s.append(perf_counter() - registration_frame_start)
                    registration_results.append(
                        RegistrationResult(
                            frame_id=str(frame["id"]),
                            reference_frame_id=str(reference_frame["id"]),
                            transform_model="translation_ncc_subpixel",
                            matrix=translation_matrix(dx, dy),
                            matched_stars=0,
                            inliers=0 if status in {"failed", "excluded"} else 1,
                            rms_px=0.0 if status not in {"failed", "excluded"} else float("nan"),
                            status=status,
                            warnings=warnings
                            + [
                                f"max_shift={resident_registration_max_shift}",
                                f"subpixel_radius_steps={resident_subpixel_radius_steps}",
                                f"subpixel_step={resident_subpixel_step}",
                                "resident GPU NCC registration; no star-model RMS yet",
                            ],
                        )
                    )

            if resident_registration == "translation_star_catalog":
                if not hasattr(stack, "estimate_translation_from_stars_to_reference"):
                    raise RuntimeError("resident CUDA backend does not expose star-catalog registration")
                for index, frame in enumerate(light_frames):
                    registration_frame_start = perf_counter()
                    warnings = []
                    status = "excluded" if _matches_any_token(frame, excluded_tokens) else "ok"
                    dx = 0.0
                    dy = 0.0
                    inliers = 0
                    rms_px = float("nan")
                    try:
                        if status == "excluded":
                            frame_weight_values[index] = 0.0
                            frame_weights[frame["id"]] = 0.0
                            warnings.append("excluded by resident frame mask")
                        elif frame["id"] == reference_frame["id"]:
                            status = "reference"
                            inliers = 1
                            rms_px = 0.0
                        else:
                            prior_dx = 0.0
                            prior_dy = 0.0
                            prior_radius = -1.0
                            prior_warnings: list[str] = []
                            if resident_star_prior == "ncc":
                                if not hasattr(stack, "estimate_translation_to_reference") or not hasattr(
                                    stack,
                                    "estimate_translation_subpixel_to_reference",
                                ):
                                    raise RuntimeError("resident star NCC prior requires resident NCC registration")
                                coarse = stack.estimate_translation_to_reference(
                                    reference_index,
                                    index,
                                    resident_registration_max_shift,
                                    resident_registration_max_shift,
                                    resident_ncc_sample_stride,
                                )
                                refined_prior = stack.estimate_translation_subpixel_to_reference(
                                    reference_index,
                                    index,
                                    float(coarse["dx"]),
                                    float(coarse["dy"]),
                                    resident_subpixel_radius_steps,
                                    resident_subpixel_step,
                                    resident_ncc_sample_stride,
                                )
                                prior_dx = float(refined_prior["dx"])
                                prior_dy = float(refined_prior["dy"])
                                prior_radius = float(resident_star_prior_radius_px)
                                prior_warnings.extend(
                                    [
                                        "star_prior_model=ncc",
                                        f"star_prior_dx={prior_dx:.6g}",
                                        f"star_prior_dy={prior_dy:.6g}",
                                        f"star_prior_radius_px={prior_radius:.6g}",
                                        f"star_prior_coarse_score={float(coarse['score']):.6g}",
                                        f"star_prior_subpixel_score={float(refined_prior['score']):.6g}",
                                        f"star_prior_ncc_sample_stride={resident_ncc_sample_stride}",
                                    ]
                                )
                            threshold_candidates, threshold_mode = _resident_star_threshold_candidates(
                                stack,
                                reference_index,
                                index,
                                resident_star_threshold,
                            )
                            trial_results = []
                            result = None
                            for threshold in threshold_candidates:
                                trial = stack.estimate_translation_from_stars_to_reference(
                                    reference_index,
                                    index,
                                    threshold,
                                    resident_star_max_candidates,
                                    resident_star_tolerance_px,
                                    float(resident_registration_max_shift),
                                    float(resident_registration_max_shift),
                                    prior_dx,
                                    prior_dy,
                                    prior_radius,
                                    resident_star_grid_cols,
                                    resident_star_grid_rows,
                                )
                                trial_results.append(trial)
                                if result is None or _resident_star_registration_score(
                                    trial
                                ) > _resident_star_registration_score(result):
                                    result = trial
                            if result is None:
                                raise RuntimeError("resident star-catalog registration produced no threshold trials")
                            dx = float(result["refined_dx"])
                            dy = float(result["refined_dy"])
                            inliers = int(result["mutual_inliers"])
                            rms_px = float(result["rms_px"])
                            if inliers <= 0:
                                status = "failed"
                                frame_weight_values[index] = 0.0
                                frame_weights[frame["id"]] = 0.0
                                warnings.append("resident star-catalog registration found no mutual inliers")
                            else:
                                stack.apply_translation_bilinear_frame(index, dx, dy, np.nan)
                                warped_frame_indices.add(index)
                            warnings.extend(
                                [
                                    f"star_threshold_mode={threshold_mode}",
                                    f"selected_star_threshold={float(result['threshold']):.6g}",
                                    "star_threshold_candidates="
                                    + ",".join(f"{float(item):.6g}" for item in threshold_candidates),
                                    f"reference_stars={int(result['reference_count'])}",
                                    f"moving_stars={int(result['moving_count'])}",
                                    f"candidate_count={int(result['candidate_count'])}",
                                    f"candidate_selection={result['candidate_selection']}",
                                    f"raw_dx={float(result['dx']):.6g}",
                                    f"raw_dy={float(result['dy']):.6g}",
                                ]
                                + prior_warnings
                            )
                    except Exception as exc:
                        status = "failed"
                        frame_weight_values[index] = 0.0
                        frame_weights[frame["id"]] = 0.0
                        warnings.append(str(exc))
                    per_frame_registration_s.append(perf_counter() - registration_frame_start)
                    registration_results.append(
                        RegistrationResult(
                            frame_id=str(frame["id"]),
                            reference_frame_id=str(reference_frame["id"]),
                            transform_model="translation_star_catalog",
                            matrix=translation_matrix(dx, dy),
                            matched_stars=inliers,
                            inliers=inliers,
                            rms_px=rms_px,
                            status=status,
                            warnings=warnings
                            + [
                                f"max_shift={resident_registration_max_shift}",
                                f"star_max_candidates={resident_star_max_candidates}",
                                f"star_tolerance_px={resident_star_tolerance_px}",
                                "resident GPU star-catalog translation; similarity/affine not yet implemented",
                            ],
                        )
                    )

            if resident_registration == "similarity_cuda_catalog":
                required_methods = [
                    "star_top_candidates",
                    "refine_matrix_translation_candidates_to_reference",
                    resident_matrix_warp_method,
                ]
                missing_methods = [name for name in required_methods if not hasattr(stack, name)]
                if missing_methods:
                    raise RuntimeError(
                        "resident CUDA backend lacks similarity registration primitive(s): "
                        + ", ".join(missing_methods)
                    )
                if not hasattr(cuda_module, "estimate_similarity_from_catalogs_f32"):
                    raise RuntimeError("CUDA backend lacks catalog similarity fitting")

                tolerance_px = _policy_float(
                    registration_policy,
                    "cuda_catalog_tolerance_px",
                    resident_star_tolerance_px,
                )
                default_min_pair_distance = max(8.0, float(min(height, width)) / 48.0)
                min_pair_distance = _policy_float(
                    registration_policy,
                    "cuda_catalog_min_pair_distance",
                    default_min_pair_distance,
                )
                similarity_top_k = max(0, _policy_int(registration_policy, "cuda_catalog_similarity_top_k", 8))
                min_scale = _policy_optional_float(registration_policy, "cuda_catalog_min_scale", 0.995)
                max_scale = _policy_optional_float(registration_policy, "cuda_catalog_max_scale", 1.005)
                max_abs_rotation_rad = _policy_optional_float(
                    registration_policy,
                    "cuda_catalog_max_abs_rotation_rad",
                    0.01,
                )
                pierside_same_similarity_top_k = max(
                    0,
                    _policy_int(
                        registration_policy,
                        "cuda_catalog_pierside_same_similarity_top_k",
                        similarity_top_k,
                    ),
                )
                pierside_flip_similarity_top_k = max(
                    0,
                    _policy_int(
                        registration_policy,
                        "cuda_catalog_pierside_flip_similarity_top_k",
                        max(similarity_top_k, 64),
                    ),
                )
                pierside_same_max_abs_rotation_rad = _policy_optional_float(
                    registration_policy,
                    "cuda_catalog_pierside_same_max_abs_rotation_rad",
                    max_abs_rotation_rad,
                )
                pierside_flip_max_abs_rotation_rad = _policy_optional_float(
                    registration_policy,
                    "cuda_catalog_pierside_flip_max_abs_rotation_rad",
                    3.2,
                )
                refine_kwargs = {
                    "search_radius_px": _policy_float(
                        registration_policy,
                        "cuda_catalog_pixel_refine_radius",
                        1.0,
                    ),
                    "coarse_step_px": _policy_float(
                        registration_policy,
                        "cuda_catalog_pixel_refine_coarse_step",
                        0.25,
                    ),
                    "fine_radius_px": _policy_float(
                        registration_policy,
                        "cuda_catalog_pixel_refine_fine_radius",
                        0.25,
                    ),
                    "fine_step_px": _policy_float(
                        registration_policy,
                        "cuda_catalog_pixel_refine_fine_step",
                        0.0625,
                    ),
                    "coarse_sample_stride": _policy_int(
                        registration_policy,
                        "cuda_catalog_pixel_refine_coarse_stride",
                        resident_ncc_sample_stride,
                    ),
                    "final_sample_stride": _policy_int(
                        registration_policy,
                        "cuda_catalog_pixel_refine_final_stride",
                        1,
                    ),
                }
                nms_min_separation_px = _policy_float(
                    registration_policy,
                    "cuda_catalog_nms_min_separation_px",
                    max(32.0, float(min(height, width)) / 100.0),
                )
                nms_scan_candidates = _policy_int(
                    registration_policy,
                    "cuda_catalog_nms_scan_candidates",
                    max(resident_star_max_candidates, resident_star_max_candidates * 4),
                )
                grid_top_candidates_per_cell = _policy_int(
                    registration_policy,
                    "cuda_catalog_grid_top_per_cell",
                    4,
                )
                native_stack = getattr(stack, "_impl", stack)
                has_top_nms_catalog = hasattr(native_stack, "star_top_nms_candidates")
                has_grid_nms_catalog = hasattr(native_stack, "star_grid_top_nms_candidates")
                has_star_core_metrics = hasattr(native_stack, "star_core_metrics_candidates_to_reference")
                use_grid_catalog = (
                    resident_star_grid_cols > 0 and resident_star_grid_rows > 0 and has_grid_nms_catalog
                )
                star_core_preselect_top_k = max(
                    0,
                    _policy_int(
                        registration_policy,
                        "cuda_catalog_star_core_preselect_top_k",
                        resident_star_core_preselect_top_k,
                    ),
                )
                star_core_guard_enabled = _policy_bool(
                    registration_policy,
                    "cuda_catalog_star_core_guard",
                    star_core_preselect_top_k > 0,
                )
                min_pixel_ncc = _policy_optional_float(
                    registration_policy,
                    "cuda_catalog_min_pixel_ncc",
                    None,
                )
                min_selected_seed_inliers = max(
                    0,
                    _policy_int(
                        registration_policy,
                        "cuda_catalog_min_selected_seed_inliers",
                        0,
                    ),
                )
                catalog_selector = (
                    "resident_grid_top_nms"
                    if use_grid_catalog
                    else "resident_top_nms"
                    if has_top_nms_catalog
                    else "resident_top_flux"
                )

                def detect_resident_catalog(
                    frame_index: int,
                    threshold: float,
                    _stack=stack,
                ) -> dict[str, Any]:
                    if use_grid_catalog:
                        return _stack.star_grid_top_nms_candidates(
                            frame_index,
                            threshold,
                            resident_star_grid_cols,
                            resident_star_grid_rows,
                            grid_top_candidates_per_cell,
                            resident_star_max_candidates,
                            nms_min_separation_px,
                        )
                    if has_top_nms_catalog:
                        return _stack.star_top_nms_candidates(
                            frame_index,
                            threshold,
                            nms_scan_candidates,
                            resident_star_max_candidates,
                            nms_min_separation_px,
                        )
                    return _stack.star_top_candidates(frame_index, threshold, resident_star_max_candidates)

                reference_catalogs: dict[float, dict[str, Any]] = {}
                for index, frame in enumerate(light_frames):
                    registration_frame_start = perf_counter()
                    warnings = []
                    status = "excluded" if _matches_any_token(frame, excluded_tokens) else "ok"
                    matrix = translation_matrix(0.0, 0.0)
                    matched = 0
                    inliers = 0
                    rms_px = float("nan")
                    try:
                        if status == "excluded":
                            frame_weight_values[index] = 0.0
                            frame_weights[frame["id"]] = 0.0
                            warnings.append("excluded by resident frame mask")
                        elif frame["id"] == reference_frame["id"]:
                            status = "reference"
                            matched = 1
                            inliers = 1
                            rms_px = 0.0
                        else:
                            dispatch = _resident_similarity_frame_dispatch(
                                resident_star_prior,
                                reference_frame,
                                frame,
                                header_cache,
                            )
                            frame_star_prior = str(dispatch["prior"])
                            orientation_mode = str(dispatch["orientation_mode"])
                            frame_similarity_top_k = similarity_top_k
                            frame_max_abs_rotation_rad = max_abs_rotation_rad
                            if resident_star_prior == "auto_pierside":
                                if orientation_mode == "pierside_flipped":
                                    frame_similarity_top_k = pierside_flip_similarity_top_k
                                    frame_max_abs_rotation_rad = pierside_flip_max_abs_rotation_rad
                                elif orientation_mode == "pierside_same":
                                    frame_similarity_top_k = pierside_same_similarity_top_k
                                    frame_max_abs_rotation_rad = pierside_same_max_abs_rotation_rad
                            prior_dx = 0.0
                            prior_dy = 0.0
                            prior_radius = -1.0
                            prior_warnings: list[str] = []
                            prior_warnings.extend(
                                [
                                    f"similarity_prior_requested={resident_star_prior}",
                                    f"similarity_prior_effective={frame_star_prior}",
                                    f"similarity_orientation_mode={orientation_mode}",
                                    "similarity_reference_pierside="
                                    + str(dispatch.get("reference_pierside") or "unknown"),
                                    "similarity_frame_pierside="
                                    + str(dispatch.get("moving_pierside") or "unknown"),
                                    f"similarity_frame_top_k={frame_similarity_top_k}",
                                    "similarity_frame_max_abs_rotation_rad="
                                    + str(frame_max_abs_rotation_rad),
                                ]
                            )
                            if frame_star_prior == "ncc":
                                if not hasattr(stack, "estimate_translation_to_reference") or not hasattr(
                                    stack,
                                    "estimate_translation_subpixel_to_reference",
                                ):
                                    raise RuntimeError("resident similarity NCC prior requires resident NCC registration")
                                coarse = stack.estimate_translation_to_reference(
                                    reference_index,
                                    index,
                                    resident_registration_max_shift,
                                    resident_registration_max_shift,
                                    resident_ncc_sample_stride,
                                )
                                refined_prior = stack.estimate_translation_subpixel_to_reference(
                                    reference_index,
                                    index,
                                    float(coarse["dx"]),
                                    float(coarse["dy"]),
                                    resident_subpixel_radius_steps,
                                    resident_subpixel_step,
                                    resident_ncc_sample_stride,
                                )
                                prior_dx = float(refined_prior["dx"])
                                prior_dy = float(refined_prior["dy"])
                                prior_radius = float(resident_star_prior_radius_px)
                                prior_warnings.extend(
                                    [
                                        "similarity_prior_model=ncc",
                                        f"similarity_prior_dx={prior_dx:.6g}",
                                        f"similarity_prior_dy={prior_dy:.6g}",
                                        f"similarity_prior_radius_px={prior_radius:.6g}",
                                        f"similarity_prior_coarse_score={float(coarse['score']):.6g}",
                                        f"similarity_prior_subpixel_score={float(refined_prior['score']):.6g}",
                                    ]
                                )
                            else:
                                prior_warnings.append("similarity_prior_model=none")

                            threshold_candidates, threshold_mode = _resident_star_threshold_candidates(
                                stack,
                                reference_index,
                                index,
                                resident_star_threshold,
                            )
                            trial_results = []
                            selected_fit = None
                            selected_threshold = None
                            selected_reference_catalog = None
                            selected_moving_catalog = None
                            for threshold in threshold_candidates:
                                threshold_key = round(float(threshold), 6)
                                reference_catalog = reference_catalogs.get(threshold_key)
                                if reference_catalog is None:
                                    reference_catalog = detect_resident_catalog(reference_index, threshold)
                                    reference_catalogs[threshold_key] = reference_catalog
                                moving_catalog = detect_resident_catalog(index, threshold)
                                if int(reference_catalog["stored_count"]) < 2 or int(moving_catalog["stored_count"]) < 2:
                                    trial_results.append(
                                        {
                                            "threshold": float(threshold),
                                            "status": "too_few_stars",
                                            "reference_stored": int(reference_catalog["stored_count"]),
                                            "moving_stored": int(moving_catalog["stored_count"]),
                                        }
                                    )
                                    continue
                                fit = cuda_module.estimate_similarity_from_catalogs_f32(
                                    reference_catalog["x"],
                                    reference_catalog["y"],
                                    moving_catalog["x"],
                                    moving_catalog["y"],
                                    tolerance_px=tolerance_px,
                                    min_pair_distance=min_pair_distance,
                                    prior_dx=prior_dx,
                                    prior_dy=prior_dy,
                                    prior_radius_px=prior_radius,
                                    min_scale=min_scale,
                                    max_scale=max_scale,
                                    max_abs_rotation_rad=frame_max_abs_rotation_rad,
                                    top_k=frame_similarity_top_k,
                                )
                                trial_results.append(
                                    {
                                        "threshold": float(threshold),
                                        "status": str(fit.get("status", "failed")),
                                        "inliers": int(fit.get("refined_inliers", fit.get("inliers", 0))),
                                        "rms_px": _float_or_nan(fit.get("refit_rms_px", fit.get("rms_px"))),
                                        "reference_stored": int(reference_catalog["stored_count"]),
                                        "moving_stored": int(moving_catalog["stored_count"]),
                                        "top_candidate_count": len(fit.get("top_candidates", [])),
                                    }
                                )
                                if str(fit.get("status")) != "ok":
                                    continue
                                if selected_fit is None or _resident_similarity_score(fit) > _resident_similarity_score(
                                    selected_fit
                                ):
                                    selected_fit = fit
                                    selected_threshold = float(threshold)
                                    selected_reference_catalog = reference_catalog
                                    selected_moving_catalog = moving_catalog

                            if selected_fit is None:
                                status = "failed"
                                frame_weight_values[index] = 0.0
                                frame_weights[frame["id"]] = 0.0
                                warnings.append("resident similarity catalog registration found no accepted fit")
                            else:
                                seeds: list[dict[str, Any]] = [
                                    {
                                        "seed_rank": 0,
                                        "seed_source": "catalog_similarity_refit",
                                        "candidate_index": None,
                                        "inliers": int(
                                            selected_fit.get(
                                                "refined_inliers",
                                                selected_fit.get("inliers", 0),
                                            )
                                        ),
                                        "rms_px": _finite_float_or_none(
                                            selected_fit.get("refit_rms_px", selected_fit.get("rms_px"))
                                        ),
                                        "matrix": np.asarray(selected_fit["matrix"], dtype=np.float32)
                                        .reshape(3, 3)
                                        .tolist(),
                                    }
                                ]
                                for seed_rank, candidate in enumerate(selected_fit.get("top_candidates", []), start=1):
                                    seeds.append(
                                        {
                                            "seed_rank": seed_rank,
                                            "seed_source": "catalog_similarity_top_candidate",
                                            "candidate_index": int(candidate.get("candidate_index", seed_rank - 1)),
                                            "inliers": int(candidate.get("inliers", 0)),
                                            "rms_px": _finite_float_or_none(candidate.get("rms_px")),
                                            "matrix": np.asarray(candidate["matrix"], dtype=np.float32)
                                            .reshape(3, 3)
                                            .tolist(),
                                        }
                                    )
                                selected_seed_indices = list(range(len(seeds)))
                                preselection: dict[str, Any] = {
                                    "enabled": False,
                                    "requested_top_k": int(star_core_preselect_top_k),
                                    "input_seed_count": len(seeds),
                                    "selected_seed_count": len(seeds),
                                    "selected_seed_indices": selected_seed_indices,
                                    "selection_key": "disabled",
                                }
                                pre_refine_metric_summary: dict[str, Any] | None = None
                                star_core_threshold = _policy_float(
                                    registration_policy,
                                    "cuda_catalog_star_core_threshold",
                                    float(selected_threshold or threshold_candidates[0]),
                                )
                                if 0 < star_core_preselect_top_k < len(seeds):
                                    if has_star_core_metrics:
                                        prescreen_seed_metrics = [
                                            {
                                                "seed_index": seed_index,
                                                "seed_rank": int(seed["seed_rank"]),
                                                "seed_source": str(seed["seed_source"]),
                                                "candidate_index": seed["candidate_index"],
                                                "seed_inliers": seed["inliers"],
                                                "seed_rms_px": seed["rms_px"],
                                                "matrix": np.asarray(seed["matrix"], dtype=np.float32)
                                                .reshape(3, 3)
                                                .tolist(),
                                            }
                                            for seed_index, seed in enumerate(seeds)
                                        ]
                                        pre_refine_metric_summary = _annotate_resident_star_core_metrics(
                                            stack,
                                            reference_index,
                                            index,
                                            prescreen_seed_metrics,
                                            star_core_threshold,
                                        )
                                        selected_seed_indices, preselection = _select_star_core_preselected_seed_indices(
                                            prescreen_seed_metrics,
                                            star_core_preselect_top_k,
                                        )
                                    else:
                                        preselection = {
                                            **preselection,
                                            "enabled": False,
                                            "selection_key": "native_star_core_metric_unavailable",
                                        }
                                seed_matrices = [
                                    np.asarray(seeds[seed_index]["matrix"], dtype=np.float32).reshape(3, 3)
                                    for seed_index in selected_seed_indices
                                ]
                                refinement = stack.refine_matrix_translation_candidates_to_reference(
                                    reference_index,
                                    index,
                                    np.asarray(seed_matrices, dtype=np.float32),
                                    **refine_kwargs,
                                )
                                seed_metrics: list[dict[str, Any]] = []
                                for seed_result in refinement.get("seed_results", []):
                                    refine_seed_index = int(seed_result["seed_index"])
                                    seed_index = int(selected_seed_indices[refine_seed_index])
                                    seed = seeds[seed_index]
                                    seed_metrics.append(
                                        {
                                            "seed_index": seed_index,
                                            "refine_seed_index": refine_seed_index,
                                            "seed_rank": int(seed["seed_rank"]),
                                            "seed_source": str(seed["seed_source"]),
                                            "candidate_index": seed["candidate_index"],
                                            "seed_inliers": seed["inliers"],
                                            "seed_rms_px": seed["rms_px"],
                                            "dx_correction": float(seed_result["dx_correction"]),
                                            "dy_correction": float(seed_result["dy_correction"]),
                                            "metrics": dict(seed_result["metrics"]),
                                            "matrix": np.asarray(seed_result["matrix"], dtype=np.float32)
                                            .reshape(3, 3)
                                            .tolist(),
                                        }
                                    )
                                pixel_selected_index = int(refinement["selected_index"])
                                selected_metric_index = pixel_selected_index
                                star_guard = {
                                    "status": "disabled",
                                    "pixel_selected_index": pixel_selected_index,
                                    "selected_index": pixel_selected_index,
                                    "selection_key": "disabled",
                                }
                                star_core_metric_summary: dict[str, Any] | None = None
                                if star_core_guard_enabled and has_star_core_metrics and seed_metrics:
                                    star_core_metric_summary = _annotate_resident_star_core_metrics(
                                        stack,
                                        reference_index,
                                        index,
                                        seed_metrics,
                                        star_core_threshold,
                                    )
                                    selected_metric_index, star_guard = _select_star_guarded_seed(
                                        seed_metrics,
                                        pixel_selected_index,
                                    )
                                selected_seed_metric = (
                                    seed_metrics[selected_metric_index]
                                    if seed_metrics
                                    else {
                                        "seed_index": pixel_selected_index,
                                        "refine_seed_index": pixel_selected_index,
                                        "seed_rank": pixel_selected_index,
                                        "seed_source": "pixel_metric",
                                        "candidate_index": None,
                                        "seed_inliers": None,
                                        "seed_rms_px": None,
                                        "matrix": refinement["matrix"],
                                        "metrics": dict(refinement["metrics"]),
                                    }
                                )
                                matrix = np.asarray(selected_seed_metric["matrix"], dtype=np.float32).tolist()
                                matched = int(selected_fit.get("inliers", 0))
                                inliers = int(selected_fit.get("refined_inliers", matched))
                                rms_px = _float_or_nan(selected_fit.get("refit_rms_px", selected_fit.get("rms_px")))
                                selected_metrics = dict(selected_seed_metric["metrics"])
                                selected_pixel_ncc = _float_or_nan(selected_metrics.get("ncc"))
                                selected_pixel_rms = _float_or_nan(selected_metrics.get("rms"))
                                selected_seed_inliers = selected_seed_metric.get("seed_inliers")
                                quality_failures: list[str] = []
                                if min_pixel_ncc is not None and (
                                    not np.isfinite(selected_pixel_ncc) or selected_pixel_ncc < float(min_pixel_ncc)
                                ):
                                    quality_failures.append(
                                        f"pixel_ncc {selected_pixel_ncc:.6g} < {float(min_pixel_ncc):.6g}"
                                    )
                                if (
                                    min_selected_seed_inliers > 0
                                    and selected_seed_inliers is not None
                                    and int(selected_seed_inliers) < min_selected_seed_inliers
                                ):
                                    quality_failures.append(
                                        f"selected_seed_inliers {int(selected_seed_inliers)} < "
                                        f"{min_selected_seed_inliers}"
                                    )
                                if quality_failures:
                                    status = "failed"
                                    frame_weight_values[index] = 0.0
                                    frame_weights[frame["id"]] = 0.0
                                    warnings.append(
                                        "resident similarity registration failed quality gate: "
                                        + "; ".join(quality_failures)
                                    )
                                else:
                                    warp_model = _apply_resident_registration_matrix(
                                        stack,
                                        index,
                                        matrix,
                                        resident_warp_interpolation,
                                        resident_warp_clamping_threshold,
                                    )
                                    warped_frame_indices.add(index)
                                    warnings.append(f"resident_registration_application={warp_model}")
                                warnings.extend(
                                    [
                                        f"similarity_threshold_mode={threshold_mode}",
                                        f"selected_similarity_threshold={float(selected_threshold or 0.0):.6g}",
                                        "similarity_threshold_candidates="
                                        + ",".join(f"{float(item):.6g}" for item in threshold_candidates),
                                        f"reference_stars={int(selected_reference_catalog['stored_count'])}",
                                        f"moving_stars={int(selected_moving_catalog['stored_count'])}",
                                        f"similarity_top_k={int(selected_fit.get('top_k', frame_similarity_top_k))}",
                                        "similarity_max_abs_rotation_rad="
                                        + str(frame_max_abs_rotation_rad),
                                        f"similarity_top_candidate_count={len(selected_fit.get('top_candidates', []))}",
                                        f"similarity_seed_count={int(refinement['seed_count'])}",
                                        f"similarity_refined_seed_count={len(selected_seed_indices)}",
                                        f"similarity_selected_refine_seed={int(refinement['selected_index'])}",
                                        f"similarity_selected_seed={int(selected_seed_metric['seed_index'])}",
                                        f"similarity_selected_seed_rank={int(selected_seed_metric['seed_rank'])}",
                                        f"similarity_pixel_selected_seed={pixel_selected_index}",
                                        f"similarity_scale={float(selected_fit.get('scale', float('nan'))):.9g}",
                                        f"similarity_rotation_rad={float(selected_fit.get('rotation_rad', float('nan'))):.9g}",
                                        f"similarity_fit_rms_px={rms_px:.6g}",
                                        f"similarity_pixel_rms_adu={selected_pixel_rms:.6g}",
                                        f"similarity_pixel_ncc={selected_pixel_ncc:.6g}",
                                        "similarity_quality_gate_status="
                                        + ("failed" if quality_failures else "ok"),
                                        f"similarity_min_pixel_ncc={min_pixel_ncc}",
                                        f"similarity_min_selected_seed_inliers={min_selected_seed_inliers}",
                                        f"similarity_catalog_selector={catalog_selector}",
                                        f"similarity_nms_min_separation_px={nms_min_separation_px:.6g}",
                                        f"similarity_star_core_preselect_enabled={bool(preselection.get('enabled', False))}",
                                        f"similarity_star_core_preselect_requested_top_k={star_core_preselect_top_k}",
                                        f"similarity_star_core_preselect_selected_seed_count={int(preselection.get('selected_seed_count', len(selected_seed_indices)))}",
                                        "similarity_star_core_preselect_indices="
                                        + ",".join(str(int(item)) for item in preselection.get("selected_seed_indices", [])),
                                        f"similarity_star_core_guard_enabled={bool(star_core_guard_enabled and has_star_core_metrics)}",
                                        f"similarity_star_core_guard_status={star_guard['status']}",
                                        f"similarity_star_core_threshold={star_core_threshold:.6g}",
                                        "resident CUDA catalog similarity with multi-seed pixel refinement",
                                    ]
                                    + prior_warnings
                                )
                                if pre_refine_metric_summary is not None:
                                    warnings.append(
                                        "similarity_star_core_pre_refine_summary="
                                        + str(pre_refine_metric_summary)
                                    )
                                if star_core_metric_summary is not None:
                                    warnings.append(
                                        "similarity_star_core_guard_summary=" + str(star_core_metric_summary)
                                    )
                            warnings.append("similarity_trials=" + str(trial_results))
                    except Exception as exc:
                        status = "failed"
                        frame_weight_values[index] = 0.0
                        frame_weights[frame["id"]] = 0.0
                        warnings.append(str(exc))
                    per_frame_registration_s.append(perf_counter() - registration_frame_start)
                    registration_results.append(
                        RegistrationResult(
                            frame_id=str(frame["id"]),
                            reference_frame_id=str(reference_frame["id"]),
                            transform_model="similarity_cuda_catalog",
                            matrix=matrix,
                            matched_stars=matched,
                            inliers=inliers,
                            rms_px=rms_px,
                            status=status,
                            warnings=warnings
                            + [
                                f"max_shift={resident_registration_max_shift}",
                                f"star_max_candidates={resident_star_max_candidates}",
                                f"star_tolerance_px={resident_star_tolerance_px}",
                                "resident GPU similarity catalog registration",
                            ],
                        )
                    )

            if resident_registration == "similarity_cuda_triangle":
                required_methods = [
                    "star_top_candidates",
                    resident_matrix_warp_method,
                ]
                missing_methods = [name for name in required_methods if not hasattr(stack, name)]
                if missing_methods:
                    raise RuntimeError(
                        "resident CUDA backend lacks triangle registration primitive(s): "
                        + ", ".join(missing_methods)
                    )
                required_cuda = [
                    "estimate_similarity_from_triangle_descriptors_f32",
                    "triangle_asterism_descriptors_f32",
                ]
                missing_cuda = [name for name in required_cuda if not hasattr(cuda_module, name)]
                if missing_cuda:
                    raise RuntimeError(
                        "CUDA backend lacks triangle descriptor primitive(s): "
                        + ", ".join(missing_cuda)
                    )

                tolerance_px = _policy_float(
                    registration_policy,
                    "cuda_triangle_tolerance_px",
                    _policy_float(registration_policy, "cuda_catalog_tolerance_px", resident_star_tolerance_px),
                )
                descriptor_radius = _policy_float(registration_policy, "cuda_triangle_descriptor_radius", 0.1)
                descriptor_neighbors = _policy_int(registration_policy, "cuda_triangle_neighbors", 5)
                max_descriptors = _policy_int(registration_policy, "cuda_triangle_max_descriptors", 1200)
                nms_min_separation_px = _policy_float(
                    registration_policy,
                    "cuda_triangle_nms_min_separation_px",
                    _policy_float(
                        registration_policy,
                        "cuda_catalog_nms_min_separation_px",
                        max(32.0, float(min(height, width)) / 100.0),
                    ),
                )
                nms_scan_candidates = _policy_int(
                    registration_policy,
                    "cuda_triangle_nms_scan_candidates",
                    _policy_int(
                        registration_policy,
                        "cuda_catalog_nms_scan_candidates",
                        max(resident_star_max_candidates, resident_star_max_candidates * 4),
                    ),
                )
                grid_top_candidates_per_cell = _policy_int(
                    registration_policy,
                    "cuda_triangle_grid_top_per_cell",
                    _policy_int(registration_policy, "cuda_catalog_grid_top_per_cell", 4),
                )
                refine_kwargs = {
                    "search_radius_px": _policy_float(
                        registration_policy,
                        "cuda_triangle_pixel_refine_radius",
                        _policy_float(registration_policy, "cuda_catalog_pixel_refine_radius", 1.0),
                    ),
                    "coarse_step_px": _policy_float(
                        registration_policy,
                        "cuda_triangle_pixel_refine_coarse_step",
                        _policy_float(registration_policy, "cuda_catalog_pixel_refine_coarse_step", 0.25),
                    ),
                    "fine_radius_px": _policy_float(
                        registration_policy,
                        "cuda_triangle_pixel_refine_fine_radius",
                        _policy_float(registration_policy, "cuda_catalog_pixel_refine_fine_radius", 0.25),
                    ),
                    "fine_step_px": _policy_float(
                        registration_policy,
                        "cuda_triangle_pixel_refine_fine_step",
                        _policy_float(registration_policy, "cuda_catalog_pixel_refine_fine_step", 0.0625),
                    ),
                    "coarse_sample_stride": _policy_int(
                        registration_policy,
                        "cuda_triangle_pixel_refine_coarse_stride",
                        _policy_int(
                            registration_policy,
                            "cuda_catalog_pixel_refine_coarse_stride",
                            resident_ncc_sample_stride,
                        ),
                    ),
                    "final_sample_stride": _policy_int(
                        registration_policy,
                        "cuda_triangle_pixel_refine_final_stride",
                        _policy_int(registration_policy, "cuda_catalog_pixel_refine_final_stride", 1),
                    ),
                }
                if resident_triangle_pixel_refine_coarse_stride is not None:
                    refine_kwargs["coarse_sample_stride"] = int(resident_triangle_pixel_refine_coarse_stride)
                if resident_triangle_pixel_refine_final_stride is not None:
                    refine_kwargs["final_sample_stride"] = int(resident_triangle_pixel_refine_final_stride)
                min_pixel_ncc = _policy_optional_float(
                    registration_policy,
                    "cuda_triangle_min_pixel_ncc",
                    _policy_optional_float(registration_policy, "cuda_catalog_min_pixel_ncc", None),
                )
                pixel_refine_enabled = _policy_bool(registration_policy, "cuda_triangle_pixel_refine", True)
                native_stack = getattr(stack, "_impl", stack)
                has_top_nms_catalog = hasattr(native_stack, "star_top_nms_candidates")
                has_grid_nms_catalog = hasattr(native_stack, "star_grid_top_nms_candidates")
                use_grid_catalog = (
                    resident_star_grid_cols > 0 and resident_star_grid_rows > 0 and has_grid_nms_catalog
                )
                triangle_catalog_batch_enabled = bool(
                    use_grid_catalog
                    and resident_star_threshold > 0.0
                    and hasattr(native_stack, "star_grid_top_nms_candidates_batch")
                )
                triangle_catalog_batch_mode = (
                    "grid_top_nms_fixed_threshold" if triangle_catalog_batch_enabled else "off"
                )
                catalog_selector = (
                    "resident_grid_top_nms"
                    if use_grid_catalog
                    else "resident_top_nms"
                    if has_top_nms_catalog
                    else "resident_top_flux"
                )

                def detect_resident_triangle_catalog(
                    frame_index: int,
                    threshold: float,
                    _stack=stack,
                ) -> dict[str, Any]:
                    if use_grid_catalog:
                        return _stack.star_grid_top_nms_candidates(
                            frame_index,
                            threshold,
                            resident_star_grid_cols,
                            resident_star_grid_rows,
                            grid_top_candidates_per_cell,
                            resident_star_max_candidates,
                            nms_min_separation_px,
                        )
                    if has_top_nms_catalog:
                        return _stack.star_top_nms_candidates(
                            frame_index,
                            threshold,
                            nms_scan_candidates,
                            resident_star_max_candidates,
                            nms_min_separation_px,
                        )
                    return _stack.star_top_candidates(frame_index, threshold, resident_star_max_candidates)

                def triangle_descriptors(catalog: dict[str, Any]) -> dict[str, Any]:
                    return cuda_module.triangle_asterism_descriptors_f32(
                        catalog["x"],
                        catalog["y"],
                        max_stars=resident_star_max_candidates,
                        neighbors=descriptor_neighbors,
                        max_descriptors=max_descriptors,
                    )

                reference_catalogs: dict[float, dict[str, Any]] = {}
                reference_descriptors: dict[float, dict[str, Any]] = {}
                moving_catalog_batch_cache: dict[float, dict[int, dict[str, Any]]] = {}
                moving_catalog_batch_indices = [
                    frame_index
                    for frame_index, frame in enumerate(light_frames)
                    if frame_index != reference_index and not _matches_any_token(frame, excluded_tokens)
                ]

                def detect_resident_triangle_moving_catalog(
                    frame_index: int,
                    threshold: float,
                    _stack=stack,
                ) -> dict[str, Any]:
                    threshold_key = round(float(threshold), 6)
                    if triangle_catalog_batch_enabled:
                        cached_by_index = moving_catalog_batch_cache.get(threshold_key)
                        if cached_by_index is None:
                            batch_start = perf_counter()
                            batch_results = _stack.star_grid_top_nms_candidates_batch(
                                moving_catalog_batch_indices,
                                threshold,
                                resident_star_grid_cols,
                                resident_star_grid_rows,
                                grid_top_candidates_per_cell,
                                resident_star_max_candidates,
                                nms_min_separation_px,
                            )
                            _add_elapsed(
                                registration_component_s,
                                "triangle_moving_catalog_batch",
                                perf_counter() - batch_start,
                            )
                            cached_by_index = {int(item["frame_index"]): item for item in batch_results}
                            moving_catalog_batch_cache[threshold_key] = cached_by_index
                        cached_catalog = cached_by_index.get(frame_index)
                        if cached_catalog is not None:
                            return cached_catalog
                    return detect_resident_triangle_catalog(frame_index, threshold)

                for index, frame in enumerate(light_frames):
                    registration_frame_start = perf_counter()
                    warnings = []
                    status = "excluded" if _matches_any_token(frame, excluded_tokens) else "ok"
                    matrix = translation_matrix(0.0, 0.0)
                    matched = 0
                    inliers = 0
                    rms_px = float("nan")
                    try:
                        if status == "excluded":
                            frame_weight_values[index] = 0.0
                            frame_weights[frame["id"]] = 0.0
                            warnings.append("excluded by resident frame mask")
                        elif frame["id"] == reference_frame["id"]:
                            status = "reference"
                            matched = 1
                            inliers = 1
                            rms_px = 0.0
                        else:
                            threshold_start = perf_counter()
                            threshold_candidates, threshold_mode = _resident_star_threshold_candidates(
                                stack,
                                reference_index,
                                index,
                                resident_star_threshold,
                            )
                            _add_elapsed(
                                registration_component_s,
                                "triangle_threshold_select",
                                perf_counter() - threshold_start,
                            )
                            trial_results = []
                            selected_fit = None
                            selected_threshold = None
                            selected_reference_catalog = None
                            selected_moving_catalog = None
                            selected_reference_descriptors = None
                            selected_moving_descriptors = None
                            for threshold in threshold_candidates:
                                threshold_key = round(float(threshold), 6)
                                reference_catalog = reference_catalogs.get(threshold_key)
                                if reference_catalog is None:
                                    reference_catalog_start = perf_counter()
                                    reference_catalog = detect_resident_triangle_catalog(reference_index, threshold)
                                    _add_elapsed(
                                        registration_component_s,
                                        "triangle_reference_catalog",
                                        perf_counter() - reference_catalog_start,
                                    )
                                    reference_catalogs[threshold_key] = reference_catalog
                                moving_catalog_start = perf_counter()
                                moving_catalog = detect_resident_triangle_moving_catalog(index, threshold)
                                _add_elapsed(
                                    registration_component_s,
                                    "triangle_moving_catalog",
                                    perf_counter() - moving_catalog_start,
                                )
                                if int(reference_catalog["stored_count"]) < 3 or int(moving_catalog["stored_count"]) < 3:
                                    trial_results.append(
                                        {
                                            "threshold": float(threshold),
                                            "status": "too_few_stars",
                                            "reference_stored": int(reference_catalog["stored_count"]),
                                            "moving_stored": int(moving_catalog["stored_count"]),
                                        }
                                    )
                                    continue
                                reference_descriptor = reference_descriptors.get(threshold_key)
                                if reference_descriptor is None:
                                    reference_descriptor_start = perf_counter()
                                    reference_descriptor = triangle_descriptors(reference_catalog)
                                    _add_elapsed(
                                        registration_component_s,
                                        "triangle_reference_descriptors",
                                        perf_counter() - reference_descriptor_start,
                                    )
                                    reference_descriptors[threshold_key] = reference_descriptor
                                moving_descriptor_start = perf_counter()
                                moving_descriptor = triangle_descriptors(moving_catalog)
                                _add_elapsed(
                                    registration_component_s,
                                    "triangle_moving_descriptors",
                                    perf_counter() - moving_descriptor_start,
                                )
                                if (
                                    int(reference_descriptor["count"]) <= 0
                                    or int(moving_descriptor["count"]) <= 0
                                ):
                                    trial_results.append(
                                        {
                                            "threshold": float(threshold),
                                            "status": "too_few_descriptors",
                                            "reference_descriptors": int(reference_descriptor["count"]),
                                            "moving_descriptors": int(moving_descriptor["count"]),
                                        }
                                    )
                                    continue
                                fit_start = perf_counter()
                                fit = cuda_module.estimate_similarity_from_triangle_descriptors_f32(
                                    reference_catalog["x"],
                                    reference_catalog["y"],
                                    moving_catalog["x"],
                                    moving_catalog["y"],
                                    reference_descriptor["descriptors"],
                                    reference_descriptor["indices"],
                                    moving_descriptor["descriptors"],
                                    moving_descriptor["indices"],
                                    tolerance_px=tolerance_px,
                                    descriptor_radius=descriptor_radius,
                                )
                                _add_elapsed(
                                    registration_component_s,
                                    "triangle_descriptor_fit",
                                    perf_counter() - fit_start,
                                )
                                trial_results.append(
                                    {
                                        "threshold": float(threshold),
                                        "status": str(fit.get("status", "failed")),
                                        "inliers": int(fit.get("inliers", 0)),
                                        "rms_px": _float_or_nan(fit.get("rms_px")),
                                        "reference_stored": int(reference_catalog["stored_count"]),
                                        "moving_stored": int(moving_catalog["stored_count"]),
                                        "reference_descriptors": int(reference_descriptor["count"]),
                                        "moving_descriptors": int(moving_descriptor["count"]),
                                        "candidate_count": int(fit.get("candidate_count", 0)),
                                    }
                                )
                                if str(fit.get("status")) != "ok":
                                    continue
                                if selected_fit is None or _resident_similarity_score(fit) > _resident_similarity_score(
                                    selected_fit
                                ):
                                    selected_fit = fit
                                    selected_threshold = float(threshold)
                                    selected_reference_catalog = reference_catalog
                                    selected_moving_catalog = moving_catalog
                                    selected_reference_descriptors = reference_descriptor
                                    selected_moving_descriptors = moving_descriptor

                            if selected_fit is None:
                                status = "failed"
                                frame_weight_values[index] = 0.0
                                frame_weights[frame["id"]] = 0.0
                                warnings.append("resident triangle descriptor registration found no accepted fit")
                            else:
                                matrix_array = np.asarray(selected_fit["matrix"], dtype=np.float32).reshape(3, 3)
                                pixel_metrics: dict[str, Any] | None = None
                                if pixel_refine_enabled and hasattr(
                                    stack,
                                    "refine_matrix_translation_candidates_to_reference",
                                ):
                                    pixel_refine_start = perf_counter()
                                    refinement = stack.refine_matrix_translation_candidates_to_reference(
                                        reference_index,
                                        index,
                                        np.asarray([matrix_array], dtype=np.float32),
                                        **refine_kwargs,
                                    )
                                    _add_elapsed(
                                        registration_component_s,
                                        "triangle_pixel_refine",
                                        perf_counter() - pixel_refine_start,
                                    )
                                    matrix_array = np.asarray(refinement["matrix"], dtype=np.float32).reshape(3, 3)
                                    pixel_metrics = dict(refinement.get("metrics", {}))
                                matrix = matrix_array.tolist()
                                matched = int(selected_fit.get("inliers", 0))
                                inliers = matched
                                rms_px = _float_or_nan(selected_fit.get("rms_px"))
                                selected_pixel_ncc = (
                                    float("nan")
                                    if pixel_metrics is None
                                    else _float_or_nan(pixel_metrics.get("ncc"))
                                )
                                selected_pixel_rms = (
                                    float("nan")
                                    if pixel_metrics is None
                                    else _float_or_nan(pixel_metrics.get("rms"))
                                )
                                quality_failures: list[str] = []
                                if min_pixel_ncc is not None and (
                                    not np.isfinite(selected_pixel_ncc) or selected_pixel_ncc < float(min_pixel_ncc)
                                ):
                                    quality_failures.append(
                                        f"pixel_ncc {selected_pixel_ncc:.6g} < {float(min_pixel_ncc):.6g}"
                                    )
                                if quality_failures:
                                    status = "failed"
                                    frame_weight_values[index] = 0.0
                                    frame_weights[frame["id"]] = 0.0
                                    warnings.append(
                                        "resident triangle descriptor registration failed quality gate: "
                                        + "; ".join(quality_failures)
                                    )
                                else:
                                    warp_start = perf_counter()
                                    warp_model = _apply_resident_registration_matrix(
                                        stack,
                                        index,
                                        matrix,
                                        resident_warp_interpolation,
                                        resident_warp_clamping_threshold,
                                    )
                                    warped_frame_indices.add(index)
                                    _add_elapsed(
                                        registration_component_s,
                                        "triangle_warp",
                                        perf_counter() - warp_start,
                                    )
                                    warnings.append(f"resident_registration_application={warp_model}")
                                warnings.extend(
                                    [
                                        f"triangle_threshold_mode={threshold_mode}",
                                        f"selected_triangle_threshold={float(selected_threshold or 0.0):.6g}",
                                        "triangle_threshold_candidates="
                                        + ",".join(f"{float(item):.6g}" for item in threshold_candidates),
                                        f"reference_stars={int(selected_reference_catalog['stored_count'])}",
                                        f"moving_stars={int(selected_moving_catalog['stored_count'])}",
                                        f"reference_descriptors={int(selected_reference_descriptors['count'])}",
                                        f"moving_descriptors={int(selected_moving_descriptors['count'])}",
                                        f"triangle_neighbors={descriptor_neighbors}",
                                        f"triangle_max_descriptors={max_descriptors}",
                                        f"triangle_descriptor_radius={descriptor_radius:.6g}",
                                        f"triangle_candidate_count={int(selected_fit.get('candidate_count', 0))}",
                                        f"triangle_scale={float(selected_fit.get('scale', float('nan'))):.9g}",
                                        f"triangle_rotation_rad={float(selected_fit.get('rotation_rad', float('nan'))):.9g}",
                                        f"triangle_fit_rms_px={rms_px:.6g}",
                                        f"triangle_pixel_refine_enabled={pixel_refine_enabled}",
                                        f"triangle_pixel_rms_adu={selected_pixel_rms:.6g}",
                                        f"triangle_pixel_ncc={selected_pixel_ncc:.6g}",
                                        "triangle_quality_gate_status="
                                        + ("failed" if quality_failures else "ok"),
                                        f"triangle_min_pixel_ncc={min_pixel_ncc}",
                                        f"triangle_catalog_selector={catalog_selector}",
                                        f"triangle_catalog_batch={triangle_catalog_batch_mode}",
                                        f"triangle_nms_min_separation_px={nms_min_separation_px:.6g}",
                                        "resident CUDA triangle descriptor similarity",
                                    ]
                                )
                            warnings.append("triangle_trials=" + str(trial_results))
                    except Exception as exc:
                        status = "failed"
                        frame_weight_values[index] = 0.0
                        frame_weights[frame["id"]] = 0.0
                        warnings.append(str(exc))
                    registration_elapsed = perf_counter() - registration_frame_start
                    if resident_registration == "similarity_cuda_triangle":
                        _add_elapsed(registration_component_s, "triangle_frame_total", registration_elapsed)
                    per_frame_registration_s.append(registration_elapsed)
                    registration_results.append(
                        RegistrationResult(
                            frame_id=str(frame["id"]),
                            reference_frame_id=str(reference_frame["id"]),
                            transform_model="similarity_cuda_triangle",
                            matrix=matrix,
                            matched_stars=matched,
                            inliers=inliers,
                            rms_px=rms_px,
                            status=status,
                            warnings=warnings
                            + [
                                f"max_shift={resident_registration_max_shift}",
                                f"star_max_candidates={resident_star_max_candidates}",
                                f"star_tolerance_px={resident_star_tolerance_px}",
                                "resident CUDA triangle descriptor registration",
                            ],
                        )
                    )

            if resident_registration == "external_matrix":
                for index, frame in enumerate(light_frames):
                    registration_frame_start = perf_counter()
                    warnings = []
                    status = "excluded" if _matches_any_token(frame, excluded_tokens) else "ok"
                    matrix = translation_matrix(0.0, 0.0)
                    transform_model = "external_matrix"
                    matched = 0
                    inliers = 0
                    rms_px = float("nan")
                    try:
                        row = external_registration_by_frame.get(str(frame["id"]))
                        if status == "excluded":
                            frame_weight_values[index] = 0.0
                            frame_weights[frame["id"]] = 0.0
                            warnings.append("excluded by resident frame mask")
                        elif row is None:
                            status = "failed"
                            frame_weight_values[index] = 0.0
                            frame_weights[frame["id"]] = 0.0
                            warnings.append("missing external registration row")
                        else:
                            matrix = _registration_matrix(row)
                            transform_model = str(row.get("transform_model") or "external_matrix")
                            matched = int(row.get("matched_stars") or 0)
                            inliers = int(row.get("inliers") or 0)
                            rms_px = _float_or_nan(row.get("rms_px"))
                            source_status = str(row.get("status") or "failed")
                            warnings.extend(str(item) for item in row.get("warnings", []))
                            if frame["id"] == reference_frame["id"] or source_status == "reference":
                                status = "reference"
                                rms_px = 0.0 if not np.isfinite(rms_px) else rms_px
                            elif source_status != "ok":
                                status = source_status
                                frame_weight_values[index] = 0.0
                                frame_weights[frame["id"]] = 0.0
                                warnings.append(f"external registration status was {source_status}")
                            else:
                                warp_model = _apply_resident_registration_matrix(
                                    stack,
                                    index,
                                    matrix,
                                    resident_warp_interpolation,
                                    resident_warp_clamping_threshold,
                                )
                                warped_frame_indices.add(index)
                                warnings.append(f"external_registration_application={warp_model}")
                            if external_registration_path is not None:
                                warnings.append(f"external_registration_results={external_registration_path}")
                    except Exception as exc:
                        status = "failed"
                        frame_weight_values[index] = 0.0
                        frame_weights[frame["id"]] = 0.0
                        warnings.append(str(exc))
                    per_frame_registration_s.append(perf_counter() - registration_frame_start)
                    registration_results.append(
                        RegistrationResult(
                            frame_id=str(frame["id"]),
                            reference_frame_id=str(reference_frame["id"]),
                            transform_model=transform_model,
                            matrix=matrix,
                            matched_stars=matched,
                            inliers=inliers,
                            rms_px=rms_px,
                            status=status,
                            warnings=warnings
                            + [
                                "resident CUDA external matrix registration; matrices come from a prior "
                                "registration_results.json artifact",
                            ],
                        )
                    )

            weighting_start = perf_counter()
            weighting_frame_results: list[dict[str, Any]] = []
            weighting_warnings: list[str] = []
            if weighting_mode == "simple_snr":
                if not hasattr(stack, "frame_global_stats"):
                    raise RuntimeError("resident CUDA backend does not expose frame_global_stats for simple_snr")
                for index, frame in enumerate(light_frames):
                    status = "ok"
                    stats: dict[str, Any] | None = None
                    weight = float(frame_weight_values[index])
                    if frame_weight_values[index] <= 0.0:
                        status = "skipped_zero_weight"
                        weight = 0.0
                    else:
                        stats = stack.frame_global_stats(index)
                        weight = _simple_snr_weight_from_stats(stats)
                        if weight <= 0.0:
                            status = "empty"
                            weight = 0.0
                        frame_weight_values[index] = float(weight)
                        frame_weights[frame["id"]] = float(weight)
                    weighting_frame_results.append(
                        {
                            "frame_id": str(frame["id"]),
                            "weight": float(weight),
                            "status": status,
                            "source_mean": None if stats is None else float(stats["mean"]),
                            "source_std": None if stats is None else float(stats["std"]),
                            "valid_pixels": None if stats is None else int(stats["valid_pixels"]),
                        }
                    )
            else:
                weighting_frame_results = [
                    {
                        "frame_id": str(frame["id"]),
                        "weight": float(frame_weight_values[index]),
                        "status": "zero_weight" if frame_weight_values[index] <= 0.0 else "unit",
                    }
                    for index, frame in enumerate(light_frames)
                ]
            weighting_elapsed = perf_counter() - weighting_start

            local_norm_start = perf_counter()
            local_norm_policy = plan.get("local_normalization_policy", {})
            local_norm_enabled = local_normalization == "on" or (
                local_normalization == "auto" and bool(local_norm_policy.get("enabled", False))
            )
            local_norm_mode = (
                f"resident_{resident_local_normalization_mode}" if local_norm_enabled else "off"
            )
            local_norm_frame_results: list[dict[str, Any]] = []
            local_norm_warnings: list[str] = []
            if local_norm_enabled:
                if resident_local_normalization_mode == "global_mean_std":
                    if not hasattr(stack, "frame_global_stats") or not hasattr(stack, "apply_global_normalization_frame"):
                        raise RuntimeError("resident CUDA backend does not expose global local normalization")
                    reference_stats = stack.frame_global_stats(reference_index)
                    reference_mean = float(reference_stats["mean"])
                    reference_std = float(reference_stats["std"])
                else:
                    if not hasattr(stack, "frame_pair_grid_stats") or not hasattr(
                        stack, "apply_grid_normalization_frame"
                    ):
                        raise RuntimeError("resident CUDA backend does not expose grid local normalization")
                    reference_stats = None
                    reference_mean = 0.0
                    reference_std = 0.0
                eps = 1.0e-6
                if resident_local_normalization_mode == "global_mean_std":
                    local_norm_warnings.append(
                        "resident CUDA local normalization uses one global mean/std model per frame"
                    )
                for index, frame in enumerate(light_frames):
                    status = "ok"
                    warnings: list[str] = []
                    scale = 1.0
                    offset = 0.0
                    source_stats: dict[str, Any] | None = None
                    grid_coefficients: dict[str, Any] | None = None
                    if frame_weight_values[index] <= 0.0:
                        status = "skipped_zero_weight"
                        warnings.append("frame was excluded or failed registration before local normalization")
                    elif index == reference_index:
                        status = "reference"
                        source_stats = reference_stats
                    elif resident_local_normalization_mode == "global_mean_std":
                        source_stats = stack.frame_global_stats(index)
                        source_mean = float(source_stats["mean"])
                        source_std = float(source_stats["std"])
                        if int(source_stats["valid_pixels"]) == 0:
                            status = "empty"
                            frame_weight_values[index] = 0.0
                            frame_weights[frame["id"]] = 0.0
                            warnings.append("frame had no finite pixels for resident global LN")
                        elif source_std <= eps or reference_std <= eps:
                            status = "offset_only"
                            scale = 1.0
                            offset = reference_mean - source_mean
                            stack.apply_global_normalization_frame(index, scale, offset)
                        else:
                            scale = reference_std / source_std
                            offset = reference_mean - source_mean * scale
                            stack.apply_global_normalization_frame(index, scale, offset)
                    else:
                        grid_stats = stack.frame_pair_grid_stats(
                            reference_index,
                            index,
                            resident_local_normalization_tile_size,
                            resident_local_normalization_tile_size,
                        )
                        coeffs = _grid_local_norm_coefficients(grid_stats, eps=eps)
                        if coeffs["valid_pixel_total"] == 0:
                            status = "empty"
                            frame_weight_values[index] = 0.0
                            frame_weights[frame["id"]] = 0.0
                            warnings.append("frame had no finite paired pixels for resident grid LN")
                        else:
                            stack.apply_grid_normalization_frame(
                                index,
                                coeffs["scales"],
                                coeffs["offsets"],
                                resident_local_normalization_tile_size,
                                resident_local_normalization_tile_size,
                            )
                            if coeffs["empty_tiles"]:
                                status = "partial"
                                warnings.append(
                                    f"{coeffs['empty_tiles']} local-normalization tiles had no paired finite pixels"
                                )
                        scale = float(coeffs["scale_mean"])
                        offset = float(coeffs["offset_mean"])
                        grid_coefficients = {
                            "model": str(grid_stats["model"]),
                            "tile_size": resident_local_normalization_tile_size,
                            "grid_rows": int(grid_stats["grid_rows"]),
                            "grid_cols": int(grid_stats["grid_cols"]),
                            "scale_mean": float(coeffs["scale_mean"]),
                            "scale_min": float(coeffs["scale_min"]),
                            "scale_max": float(coeffs["scale_max"]),
                            "offset_mean": float(coeffs["offset_mean"]),
                            "offset_min": float(coeffs["offset_min"]),
                            "offset_max": float(coeffs["offset_max"]),
                            "valid_pixel_total": int(coeffs["valid_pixel_total"]),
                            "empty_tiles": int(coeffs["empty_tiles"]),
                            "offset_only_tiles": int(coeffs["offset_only_tiles"]),
                            "ok_tiles": int(coeffs["ok_tiles"]),
                            "scales": coeffs["scales"].tolist(),
                            "offsets": coeffs["offsets"].tolist(),
                            "valid_pixels": coeffs["valid_pixels"].astype(np.uint64).tolist(),
                            "statuses": coeffs["statuses"],
                        }
                    local_norm_frame_results.append(
                        {
                            "frame_id": str(frame["id"]),
                            "reference_frame_id": str(reference_frame["id"]),
                            "model": local_norm_mode,
                            "scale": float(scale),
                            "offset": float(offset),
                            "source_mean": None if source_stats is None else float(source_stats["mean"]),
                            "source_std": None if source_stats is None else float(source_stats["std"]),
                            "reference_mean": reference_mean,
                            "reference_std": reference_std,
                            "valid_pixels": None if source_stats is None else int(source_stats["valid_pixels"]),
                            "grid_coefficients": grid_coefficients,
                            "status": status,
                            "warnings": warnings,
                        }
                    )
            else:
                local_norm_warnings.append(
                    "resident CUDA local normalization disabled; use --local-normalization on to enable it"
                )
            local_norm_elapsed = perf_counter() - local_norm_start
            local_norm_groups.append(
                {
                    "filter": filter_name,
                    "enabled": local_norm_enabled,
                    "mode": local_norm_mode,
                    "tile_size": (
                        resident_local_normalization_tile_size
                        if resident_local_normalization_mode == "grid_mean_std" and local_norm_enabled
                        else None
                    ),
                    "reference_frame_id": str(reference_frame["id"]),
                    "reference_index": reference_index,
                    "crop_box": None,
                    "frame_results": local_norm_frame_results,
                    "timing_s": local_norm_elapsed,
                    "warnings": local_norm_warnings,
                }
            )

            geometric_warp_coverage_map = None
            geometric_warp_coverage_frame_count = 0
            if resident_warp_coverage_supported:
                for index, weight in enumerate(frame_weight_values):
                    if weight > 0.0 and index not in warped_frame_indices:
                        stack.accumulate_full_warp_coverage_frame()
                geometric_warp_coverage_frame_count = int(stack.warp_coverage_frame_count)
                geometric_warp_coverage_map = stack.warp_coverage_map()

            integrate_start = perf_counter()
            coverage_map = None
            low_rejection_map = None
            high_rejection_map = None
            weights_array = np.asarray(frame_weight_values, dtype=np.float32)
            weights_arg = None if np.all(weights_array == 1.0) else weights_array
            active_frame_count = int(np.count_nonzero(np.isfinite(weights_array) & (weights_array > 0.0)))
            if rejection_mode == "none":
                master, weight_map = stack.integrate_mean(weights_arg)
            else:
                if not hasattr(stack, "integrate_sigma_clip"):
                    raise RuntimeError("resident CUDA backend does not expose integrate_sigma_clip")
                winsorize = rejection_mode == "winsorized_sigma"
                (
                    master,
                    weight_map,
                    coverage_map,
                    low_rejection_map,
                    high_rejection_map,
                ) = stack.integrate_sigma_clip(weights_arg, low_sigma, high_sigma, winsorize)
            integrate_elapsed = perf_counter() - integrate_start
            output_diagnostics = _output_diagnostics(master, weight_map)
            output_map_selection = _resident_output_map_selection(resident_output_maps)
            master_path = output_dir / f"resident_master_{filt}.fits"
            weight_path = (
                output_dir / f"resident_weight_map_{filt}.fits" if output_map_selection["weight"] else None
            )
            coverage_path = (
                output_dir / f"resident_coverage_map_{filt}.fits"
                if coverage_map is not None and output_map_selection["coverage"]
                else None
            )
            low_rejection_path = (
                output_dir / f"resident_low_rejection_map_{filt}.fits"
                if low_rejection_map is not None and output_map_selection["low_rejection"]
                else None
            )
            high_rejection_path = (
                output_dir / f"resident_high_rejection_map_{filt}.fits"
                if high_rejection_map is not None and output_map_selection["high_rejection"]
                else None
            )
            dq_map = None
            dq_summary = None
            dq_path = output_dir / f"resident_dq_map_{filt}.fits" if output_map_selection["dq"] else None
            if output_map_selection["dq"]:
                dq_map, dq_summary = _resident_dq_map(
                    master,
                    weight_map,
                    coverage_map,
                    low_rejection_map,
                    high_rejection_map,
                    geometric_warp_coverage_map=geometric_warp_coverage_map,
                    active_frame_count=active_frame_count,
                )
            dq_coverage_provenance = _resident_dq_coverage_provenance(
                coverage_map,
                low_rejection_map,
                high_rejection_map,
                active_frame_count,
                geometric_warp_coverage_map=geometric_warp_coverage_map,
                geometric_warp_coverage_frame_count=geometric_warp_coverage_frame_count,
            )
            dq_provenance_summary = dq_provenance_summary_from_resident(
                dq_coverage_provenance,
                dq_summary,
                item=filt,
            )
            count_dtype = _count_map_dtype(len(light_frames))
            available_output_maps = ["master", "weight", "dq"]
            if coverage_map is not None:
                available_output_maps.append("coverage")
            if low_rejection_map is not None:
                available_output_maps.append("low_rejection")
            if high_rejection_map is not None:
                available_output_maps.append("high_rejection")
            output_specs: list[dict[str, Any]] = [
                {
                    "name": "master",
                    "path": master_path,
                    "data": master,
                    "header": {"IMAGETYP": "master", "FILTER": filter_name},
                    "dtype": np.float32,
                },
            ]
            if weight_path is not None:
                output_specs.append(
                    {
                        "name": "weight",
                        "path": weight_path,
                        "data": weight_map,
                        "header": {"IMAGETYP": "weight", "FILTER": filter_name},
                        "dtype": np.float32,
                    }
                )
            if dq_map is not None and dq_path is not None:
                output_specs.append(
                    {
                        "name": "dq",
                        "path": dq_path,
                        "data": dq_map,
                        "header": {
                            "IMAGETYP": "dq_mask",
                            "FILTER": filter_name,
                            "DQSTAGE": "integration",
                            "DQFLAGS": "NO_DATA,WARP_EDGE,LOW_REJECTED,HIGH_REJECTED",
                        },
                        "dtype": np.int16,
                        "round_counts": True,
                    }
                )
            if coverage_map is not None and coverage_path is not None:
                output_specs.append(
                    {
                        "name": "coverage",
                        "path": coverage_path,
                        "data": coverage_map,
                        "header": {"IMAGETYP": "coverage", "FILTER": filter_name, "DTYPE": np.dtype(count_dtype).name},
                        "dtype": count_dtype,
                        "round_counts": True,
                    }
                )
            if low_rejection_map is not None and low_rejection_path is not None:
                output_specs.append(
                    {
                        "name": "low_rejection",
                        "path": low_rejection_path,
                        "data": low_rejection_map,
                        "header": {"IMAGETYP": "rej_low", "FILTER": filter_name, "DTYPE": np.dtype(count_dtype).name},
                        "dtype": count_dtype,
                        "round_counts": True,
                    }
                )
            if high_rejection_map is not None and high_rejection_path is not None:
                output_specs.append(
                    {
                        "name": "high_rejection",
                        "path": high_rejection_path,
                        "data": high_rejection_map,
                        "header": {"IMAGETYP": "rej_high", "FILTER": filter_name, "DTYPE": np.dtype(count_dtype).name},
                        "dtype": count_dtype,
                        "round_counts": True,
                    }
                )
            written_output_maps = [str(spec["name"]) for spec in output_specs]
            skipped_output_maps = [
                name for name in available_output_maps if name not in set(written_output_maps)
            ]
            write_elapsed, write_breakdown, write_storage, output_write_workers = _write_resident_outputs(output_specs)

            first_master_stats = next(iter(master_stats_sets.values()), {})
            master_stats = {
                "calibration_group_policy": "planner_matching_groups_per_light",
                "set_count": len(master_stats_sets),
                "bias_count": first_master_stats.get("bias_count"),
                "dark_count": first_master_stats.get("dark_count"),
                "flat_count": first_master_stats.get("flat_count"),
                "sets": master_stats_sets,
            }
            memory_estimate = _memory_estimate(len(light_frames), height, width)
            read_timing = _timing_summary(per_frame_read_s)
            read_worker_timing = _timing_summary(per_frame_read_worker_s)
            fits_open_timing = _timing_summary(per_frame_fits_open_s)
            fits_materialize_decode_timing = _timing_summary(per_frame_fits_materialize_decode_s)
            calibrate_timing = _timing_summary(per_frame_calibrate_s)
            host_copy_timing = _timing_summary(per_frame_host_copy_s)
            h2d_timing = _timing_summary(per_frame_h2d_s)
            calibrate_store_timing = _timing_summary(per_frame_calibrate_store_s)
            registration_timing = _timing_summary(per_frame_registration_s)
            registration_total = registration_timing["total"]
            registration_component_total = float(
                sum(
                    value
                    for key, value in registration_component_s.items()
                    if not key.endswith("_frame_total")
                )
            )
            registration_orchestration_elapsed = max(0.0, registration_total - registration_component_total)
            registration_deferred_elapsed = max(0.0, registration_total - registration_during_load_elapsed)
            read_wait_total = read_timing["total"]
            read_worker_total = read_worker_timing["total"]
            read_overlap_saved = max(0.0, read_worker_total - read_wait_total)
            read_overlap_efficiency = (
                read_overlap_saved / read_worker_total if read_worker_total > 0.0 else None
            )
            read_wait_fraction_of_wall = (
                read_wait_total / load_calibrate_elapsed if load_calibrate_elapsed > 0.0 else None
            )
            read_worker_to_wall_ratio = (
                read_worker_total / load_calibrate_elapsed if load_calibrate_elapsed > 0.0 else None
            )
            resident_io_overlap = {
                "schema_version": 1,
                "wall_clock_stage_s": load_calibrate_elapsed,
                "consumer_read_wait_wall_s": read_wait_total,
                "worker_read_cumulative_s": read_worker_total,
                "worker_fits_open_cumulative_s": fits_open_timing["total"],
                "worker_fits_materialize_decode_cumulative_s": fits_materialize_decode_timing["total"],
                "overlap_saved_s": read_overlap_saved,
                "overlap_efficiency": read_overlap_efficiency,
                "consumer_wait_fraction_of_wall": read_wait_fraction_of_wall,
                "worker_cumulative_to_wall_ratio": read_worker_to_wall_ratio,
                "prefetch_enabled": bool(resident_prefetch_frames > 0),
                "prefetch_frames": int(resident_prefetch_frames),
                "prefetch_workers": int(resident_prefetch_workers) if resident_prefetch_frames > 0 else 0,
                "note": (
                    "worker_* values are cumulative read-thread time and can exceed wall-clock time "
                    "when prefetch overlaps FITS decode with GPU upload/calibration."
                ),
            }
            light_loop_accounted = (
                read_wait_total
                + calibrate_timing["total"]
                + registration_during_load_elapsed
                + gc_elapsed
            )
            light_loop_unaccounted = max(0.0, load_calibrate_elapsed - light_loop_accounted)
            fine_timing = {
                "schema_version": 1,
                "seconds": {
                    "light_loop_total": load_calibrate_elapsed,
                    "light_read_decode_total": read_wait_total,
                    "light_read_decode_worker_total": read_worker_total,
                    "light_fits_open_total": fits_open_timing["total"],
                    "light_fits_materialize_decode_total": fits_materialize_decode_timing["total"],
                    "light_read_overlap_saved": read_overlap_saved,
                    "light_host_copy_to_pinned_total": host_copy_timing["total"],
                    "light_h2d_total": h2d_timing["total"],
                    "light_calibrate_store_total": calibrate_store_timing["total"],
                    "light_h2d_calibrate_store_total": calibrate_timing["total"],
                    "resident_registration_warp_total": registration_total,
                    "resident_registration_warp_during_load_total": registration_during_load_elapsed,
                    "resident_registration_warp_deferred_total": registration_deferred_elapsed,
                    "gc_total": gc_elapsed,
                    "light_loop_accounted": light_loop_accounted,
                    "light_loop_unaccounted": light_loop_unaccounted,
                },
                "per_frame_seconds": {
                    "total": _timing_summary(per_frame_s),
                    "read_decode": read_timing,
                    "read_decode_worker": read_worker_timing,
                    "fits_open": fits_open_timing,
                    "fits_materialize_decode": fits_materialize_decode_timing,
                    "host_copy_to_pinned": host_copy_timing,
                    "h2d": h2d_timing,
                    "calibrate_store": calibrate_store_timing,
                    "h2d_calibrate_store": calibrate_timing,
                    "registration_warp": registration_timing,
                },
                "registration_component_seconds": {
                    **{key: float(value) for key, value in sorted(registration_component_s.items())},
                    "component_accounted_total": registration_component_total,
                    "python_orchestration_or_uninstrumented": registration_orchestration_elapsed,
                },
            }
            resident_artifacts.append(
                {
                    "filter": filter_name,
                    "frame_ids": [str(frame["id"]) for frame in light_frames],
                    "shape": {"height": height, "width": width},
                    "master_stats": master_stats,
                    "output_diagnostics": output_diagnostics,
                    "output_map_policy": {
                        "mode": resident_output_maps,
                        "available": available_output_maps,
                        "written": written_output_maps,
                        "skipped": skipped_output_maps,
                        "description": (
                            "audit writes all available diagnostic maps; science writes master, "
                            "weight, coverage, and DQ maps; minimal writes only master."
                        ),
                    },
                    "dq_map_path": None if dq_path is None else str(dq_path),
                    "dq_summary": dq_summary,
                    "dq_coverage_provenance": dq_coverage_provenance,
                    "dq_provenance_summary": dq_provenance_summary,
                    "dq_flag_bits": {
                        "no_data": int(DQFlag.NO_DATA),
                        "warp_edge": int(DQFlag.WARP_EDGE),
                        "low_rejected": int(DQFlag.LOW_REJECTED),
                        "high_rejected": int(DQFlag.HIGH_REJECTED),
                    },
                    "memory_estimate": memory_estimate,
                    "resident_bytes_allocated_after_master_upload": stack.bytes_allocated,
                    "timing_s": {
                        "master_build_or_load": master_elapsed,
                        "resident_allocate_and_master_upload": allocate_elapsed,
                        "registration_preview_setup": registration_setup_elapsed,
                        "light_read_upload_calibrate": load_calibrate_elapsed,
                        "light_read_decode": read_wait_total,
                        "light_read_wait_wall": read_wait_total,
                        "light_read_decode_worker": read_worker_total,
                        "light_read_worker_cumulative": read_worker_total,
                        "light_fits_open": fits_open_timing["total"],
                        "light_fits_open_worker_cumulative": fits_open_timing["total"],
                        "light_fits_materialize_decode": fits_materialize_decode_timing["total"],
                        "light_fits_materialize_decode_worker_cumulative": fits_materialize_decode_timing["total"],
                        "light_read_overlap_saved": read_overlap_saved,
                        "light_host_copy_to_pinned": host_copy_timing["total"],
                        "light_h2d": h2d_timing["total"],
                        "light_calibrate_store": calibrate_store_timing["total"],
                        "light_h2d_calibrate_store": calibrate_timing["total"],
                        "resident_registration_warp": registration_total,
                        "resident_registration_warp_during_load": registration_during_load_elapsed,
                        "resident_registration_warp_deferred": registration_deferred_elapsed,
                        "resident_registration_component_accounted": registration_component_total,
                        "resident_registration_orchestration": registration_orchestration_elapsed,
                        "gc": gc_elapsed,
                        "light_loop_unaccounted": light_loop_unaccounted,
                        "resident_weighting": weighting_elapsed,
                        "resident_local_normalization": local_norm_elapsed,
                        "resident_integration": integrate_elapsed,
                        "output_write": write_elapsed,
                        "per_frame_mean": fine_timing["per_frame_seconds"]["total"]["mean"],
                        "per_frame_min": fine_timing["per_frame_seconds"]["total"]["min"],
                        "per_frame_max": fine_timing["per_frame_seconds"]["total"]["max"],
                        "per_frame_read_decode_mean": read_timing["mean"],
                        "per_frame_read_decode_worker_mean": read_worker_timing["mean"],
                        "per_frame_fits_open_mean": fits_open_timing["mean"],
                        "per_frame_fits_materialize_decode_mean": fits_materialize_decode_timing["mean"],
                        "per_frame_host_copy_to_pinned_mean": host_copy_timing["mean"],
                        "per_frame_h2d_mean": h2d_timing["mean"],
                        "per_frame_calibrate_store_mean": calibrate_store_timing["mean"],
                        "per_frame_h2d_calibrate_store_mean": calibrate_timing["mean"],
                        "per_frame_registration_mean": registration_timing["mean"],
                    },
                    "output_write": {
                        "mode": "threaded" if output_write_workers > 1 else "serial",
                        "workers": output_write_workers,
                        "breakdown_s": write_breakdown,
                        "storage": write_storage,
                    },
                    "fine_timing": fine_timing,
                    "resident_io_overlap": resident_io_overlap,
                    "resident_io_pipeline": {
                        "prefetch_frames": int(resident_prefetch_frames),
                        "prefetch_workers": int(resident_prefetch_workers) if resident_prefetch_frames > 0 else 0,
                        "h2d_mode": resident_h2d_mode,
                        "master_cache_dir": str(shared_master_cache_dir) if shared_master_cache_dir is not None else None,
                        "master_cache_scope": "shared" if shared_master_cache_dir is not None else "run",
                        "host_pinned_bytes": int(
                            max(prefetch_host_pinned_bytes, int(getattr(stack, "host_pinned_bytes", 0)))
                        ),
                        "prefetch_host_pinned_bytes": int(prefetch_host_pinned_bytes),
                        "stack_host_pinned_bytes": int(getattr(stack, "host_pinned_bytes", 0)),
                    },
                    "resident_registration": {
                        "mode": resident_registration,
                        "reference_frame_id": str(reference_frame["id"]),
                        "preview_scale": preview_scale,
                        "warp_interpolation": resident_warp_interpolation,
                        "warp_clamping_threshold": resident_warp_clamping_threshold,
                        "max_shift": resident_registration_max_shift,
                        "ncc_sample_stride": resident_ncc_sample_stride,
                        "ncc_fallback_score_threshold": resident_ncc_fallback_score_threshold,
                        "subpixel_radius_steps": resident_subpixel_radius_steps,
                        "subpixel_step": resident_subpixel_step,
                        "star_threshold": resident_star_threshold,
                        "star_threshold_mode": "fixed"
                        if resident_star_threshold > 0.0
                        else "auto_mean_std",
                        "star_threshold_auto_sigmas": list(_AUTO_STAR_THRESHOLD_SIGMAS),
                        "star_max_candidates": resident_star_max_candidates,
                        "star_tolerance_px": resident_star_tolerance_px,
                        "star_grid_cols": resident_star_grid_cols,
                        "star_grid_rows": resident_star_grid_rows,
                        "star_prior": resident_star_prior,
                        "star_prior_radius_px": resident_star_prior_radius_px,
                        "pierside_same_similarity_top_k": _policy_int(
                            registration_policy,
                            "cuda_catalog_pierside_same_similarity_top_k",
                            _policy_int(registration_policy, "cuda_catalog_similarity_top_k", 8),
                        ),
                        "pierside_flip_similarity_top_k": _policy_int(
                            registration_policy,
                            "cuda_catalog_pierside_flip_similarity_top_k",
                            max(_policy_int(registration_policy, "cuda_catalog_similarity_top_k", 8), 64),
                        ),
                        "pierside_same_max_abs_rotation_rad": _policy_optional_float(
                            registration_policy,
                            "cuda_catalog_pierside_same_max_abs_rotation_rad",
                            _policy_optional_float(
                                registration_policy,
                                "cuda_catalog_max_abs_rotation_rad",
                                0.01,
                            ),
                        ),
                        "pierside_flip_max_abs_rotation_rad": _policy_optional_float(
                            registration_policy,
                            "cuda_catalog_pierside_flip_max_abs_rotation_rad",
                            3.2,
                        ),
                        "star_core_preselect_top_k": _policy_int(
                            registration_policy,
                            "cuda_catalog_star_core_preselect_top_k",
                            resident_star_core_preselect_top_k,
                        ),
                        "star_core_guard": _policy_bool(
                            registration_policy,
                            "cuda_catalog_star_core_guard",
                            _policy_int(
                                registration_policy,
                                "cuda_catalog_star_core_preselect_top_k",
                                resident_star_core_preselect_top_k,
                            )
                            > 0,
                        ),
                        "min_pixel_ncc": _policy_optional_float(
                            registration_policy,
                            "cuda_catalog_min_pixel_ncc",
                            None,
                        ),
                        "min_selected_seed_inliers": _policy_int(
                            registration_policy,
                            "cuda_catalog_min_selected_seed_inliers",
                            0,
                        ),
                        "triangle_descriptor_radius": _policy_float(
                            registration_policy,
                            "cuda_triangle_descriptor_radius",
                            0.1,
                        ),
                        "triangle_neighbors": _policy_int(
                            registration_policy,
                            "cuda_triangle_neighbors",
                            5,
                        ),
                        "triangle_max_descriptors": _policy_int(
                            registration_policy,
                            "cuda_triangle_max_descriptors",
                            1200,
                        ),
                        "triangle_pixel_refine": _policy_bool(
                            registration_policy,
                            "cuda_triangle_pixel_refine",
                            True,
                        ),
                        "triangle_catalog_batch": bool(
                            resident_registration == "similarity_cuda_triangle"
                            and triangle_catalog_batch_enabled
                        ),
                        "triangle_catalog_batch_mode": triangle_catalog_batch_mode
                        if resident_registration == "similarity_cuda_triangle"
                        else "off",
                        "triangle_pixel_refine_coarse_stride": int(refine_kwargs["coarse_sample_stride"])
                        if resident_registration == "similarity_cuda_triangle"
                        else None,
                        "triangle_pixel_refine_final_stride": int(refine_kwargs["final_sample_stride"])
                        if resident_registration == "similarity_cuda_triangle"
                        else None,
                        "triangle_min_pixel_ncc": _policy_optional_float(
                            registration_policy,
                            "cuda_triangle_min_pixel_ncc",
                            _policy_optional_float(registration_policy, "cuda_catalog_min_pixel_ncc", None),
                        ),
                        "external_registration_results_path": None
                        if external_registration_path is None
                        else str(external_registration_path),
                        "failed_frame_count": int(np.count_nonzero(weights_array == 0.0)),
                        "excluded_frame_tokens": sorted(excluded_tokens),
                        "warp_coverage": {
                            "available": bool(geometric_warp_coverage_map is not None),
                            "supported": bool(resident_warp_coverage_supported),
                            "native_source": "ResidentCalibratedStack warp coverage accumulator",
                            "frame_count": geometric_warp_coverage_frame_count,
                            "warped_frame_count": len(warped_frame_indices),
                            "full_frame_count": max(
                                0,
                                geometric_warp_coverage_frame_count - len(warped_frame_indices),
                            ),
                            "active_frame_count": active_frame_count,
                            "frame_count_matches_active": geometric_warp_coverage_frame_count == active_frame_count,
                            "statistics": None
                            if geometric_warp_coverage_map is None
                            else _resident_coverage_array_stats(geometric_warp_coverage_map),
                        },
                    },
                    "resident_local_normalization": {
                        "enabled": local_norm_enabled,
                        "mode": local_norm_mode,
                        "tile_size": (
                            resident_local_normalization_tile_size
                            if resident_local_normalization_mode == "grid_mean_std" and local_norm_enabled
                            else None
                        ),
                        "reference_frame_id": str(reference_frame["id"]),
                        "warning_count": len(local_norm_warnings),
                    },
                    "resident_integration_weighting": {
                        "mode": weighting_mode,
                        "frame_results": weighting_frame_results,
                        "timing_s": weighting_elapsed,
                        "warnings": weighting_warnings,
                    },
                    "integration_rejection": {
                        "mode": rejection_mode,
                        "low_sigma": low_sigma,
                        "high_sigma": high_sigma,
                        "algorithm": (
                            "two_stage_winsorized_mean_std_rejection_approximation"
                            if rejection_mode == "winsorized_sigma"
                            else "two_pass_mean_std_clip"
                            if rejection_mode == "sigma_clip"
                            else "none"
                        ),
                    },
                    "notes": [
                        "Raw light frames are uploaded one at a time into a reusable device buffer.",
                        "Calibrated frames remain resident in VRAM until integration completes.",
                        (
                            "Resident registration can consume external similarity/affine matrices and apply them "
                            f"with CUDA matrix {resident_warp_interpolation} warp."
                            if resident_registration == "external_matrix"
                            else "Resident registration estimated CUDA similarity matrices and applied resident matrix warp."
                            if resident_registration == "similarity_cuda_catalog"
                            else "Resident registration estimated CUDA triangle-descriptor similarity matrices and "
                            "applied resident matrix warp."
                            if resident_registration == "similarity_cuda_triangle"
                            else "Resident registration is optional and currently limited to translation."
                        ),
                        (
                            f"Resident local normalization uses {local_norm_mode}."
                            if local_norm_enabled
                            else "Local normalization was disabled for this resident run."
                        ),
                    ],
                }
            )
            outputs.append(
                {
                    "filter": filt,
                    "frame_count": len(light_frames),
                    "master_path": str(master_path),
                    "weight_map_path": None if weight_path is None else str(weight_path),
                    "coverage_map_path": None if coverage_path is None else str(coverage_path),
                    "low_rejection_map_path": None if low_rejection_path is None else str(low_rejection_path),
                    "high_rejection_map_path": None if high_rejection_path is None else str(high_rejection_path),
                    "dq_map_path": None if dq_path is None else str(dq_path),
                    "dq_summary": dq_summary,
                    "dq_coverage_provenance": dq_coverage_provenance,
                    "dq_provenance_summary": dq_provenance_summary,
                    "geometric_warp_coverage": {
                        "available": bool(geometric_warp_coverage_map is not None),
                        "frame_count": geometric_warp_coverage_frame_count,
                        "frame_count_matches_active": geometric_warp_coverage_frame_count == active_frame_count,
                    },
                    "output_map_policy": {
                        "mode": resident_output_maps,
                        "available": available_output_maps,
                        "written": written_output_maps,
                        "skipped": skipped_output_maps,
                    },
                    "backend": "cuda_resident_stack",
                    "memory_mode": "resident",
                    "rejection": rejection_mode,
                    "weighting": weighting_mode,
                    "resident_registration": resident_registration,
                    "resident_local_normalization": local_norm_mode,
                    "estimated_peak_gib": memory_estimate["estimated_peak_gib"],
                    "resident_integration_s": integrate_elapsed,
                    "output_write_storage": write_storage,
                    "output_diagnostics": output_diagnostics,
                }
            )
            del (
                stack,
                master,
                weight_map,
                coverage_map,
                low_rejection_map,
                high_rejection_map,
                dq_map,
                geometric_warp_coverage_map,
            )
            gc.collect()

        if not outputs:
            raise ValueError("resident mode found no executable light plans")

        resident_path = run / "resident_artifacts.json"
        write_json(
            resident_path,
            {
                "schema_version": 1,
                "backend": "cuda_resident_stack",
                "policy": asdict(policy),
                "artifacts": resident_artifacts,
                "device": cuda_module.get_device_info(0),
            },
        )
        if registration_results:
            matrix_warp_description = f"CUDA matrix {resident_warp_interpolation} warp"
            write_json(
                run / "registration_results.json",
                {
                    "schema_version": 1,
                    "source_stage": "resident_calibrated_stack",
                    "transform_model": resident_registration,
                    "results": registration_results,
                    "warnings": [
                        (
                            "resident registration consumed external matrices; non-translation matrices are applied "
                            f"with {matrix_warp_description}"
                            if resident_registration == "external_matrix"
                            else (
                                "resident registration estimated CUDA catalog similarity matrices and applied them "
                                f"with resident matrix {resident_warp_interpolation} warp"
                            )
                            if resident_registration == "similarity_cuda_catalog"
                            else (
                                "resident registration estimated CUDA triangle descriptor matrices and applied them "
                                f"with resident matrix {resident_warp_interpolation} warp"
                            )
                            if resident_registration == "similarity_cuda_triangle"
                            else "resident registration is translation-only in the current gate"
                        ),
                        (
                            "similarity-catalog mode records CUDA fit/refine diagnostics in warnings"
                            if resident_registration == "similarity_cuda_catalog"
                            else "triangle-descriptor mode records CUDA descriptor fit/refine diagnostics in warnings"
                            if resident_registration == "similarity_cuda_triangle"
                            else "star-catalog mode records GPU mutual-inlier diagnostics; preview/NCC modes still use "
                            "placeholder matched_stars/inliers/rms"
                            if resident_registration == "translation_star_catalog"
                            else "external_matrix mode preserves matched_stars/inliers/rms from the source artifact"
                            if resident_registration == "external_matrix"
                            else "matched_stars/inliers/rms are placeholders until star-based registration is wired in"
                        ),
                    ],
                },
            )
        local_norm_path = run / "local_norm_results.json"
        write_json(
            local_norm_path,
            {
                "schema_version": 1,
                "source_stage": "resident_calibrated_stack",
                "mode": next((group["mode"] for group in local_norm_groups if group["enabled"]), "off"),
                "enabled": any(group["enabled"] for group in local_norm_groups),
                "crop_box": None,
                "groups": local_norm_groups,
                "warnings": [
                    "resident local normalization runs before integration while frames remain in VRAM"
                ],
            },
        )
        integration_warnings: list[str] = []
        if rejection_mode == "winsorized_sigma":
            integration_warnings.append(
                "resident CUDA winsorized_sigma is currently a two-stage winsorized mean/std rejection approximation"
            )
        elif rejection_mode == "sigma_clip":
            integration_warnings.append("resident CUDA used two-pass mean/std sigma clipping")
        if weighting_mode == "simple_snr":
            integration_warnings.append("resident CUDA used frame-global mean/std simple_snr weights")
        if any(group["enabled"] for group in local_norm_groups):
            mode = next((group["mode"] for group in local_norm_groups if group["enabled"]), "unknown")
            integration_warnings.append(f"resident CUDA used {mode} local normalization before integration")
        else:
            integration_warnings.append("resident CUDA mode skipped local normalization")
        write_json(
            run / "integration_results.json",
            {
                "schema_version": 1,
                "source_stage": "resident_calibrated_stack",
                "combine": "mean",
                "weighting": weighting_mode,
                "rejection": rejection_mode,
                "low_sigma": low_sigma,
                "high_sigma": high_sigma,
                "frame_weights": frame_weights,
                "outputs": outputs,
                "excluded_frame_tokens": sorted(excluded_tokens),
                "warnings": integration_warnings,
            },
        )
        state.artifacts.append(
            PipelineArtifact(
                stage="resident_calibration_integration",
                path=str(resident_path),
                format="json",
                created_at=now_iso(),
                source_frames=list(frames.keys()),
            )
        )
        state.artifacts.append(
            PipelineArtifact(
                stage="resident_local_normalization",
                path=str(local_norm_path),
                format="json",
                created_at=now_iso(),
                source_frames=list(frames.keys()),
            )
        )
        state.completed_stages.extend(
            [
                "master_calibration",
                "resident_light_calibration",
                *(["resident_registration"] if resident_registration != "off" else []),
                *(["resident_local_normalization"] if any(group["enabled"] for group in local_norm_groups) else []),
                "resident_integration",
            ]
        )
        state.current_stage = "integration"
        state.warnings.append(
            "resident CUDA mode is a high-VRAM calibration plus integration path; "
            + (
                "external registration matrices are applied with CUDA matrix warp when requested"
                if resident_registration == "external_matrix"
                else "resident CUDA catalog similarity matrices are estimated and applied in VRAM"
                if resident_registration == "similarity_cuda_catalog"
                else "resident CUDA triangle descriptor similarity matrices are estimated and applied in VRAM"
                if resident_registration == "similarity_cuda_triangle"
                else f"registration is translation only and local normalization is {resident_local_normalization_mode}"
                " when enabled"
            )
        )
        return state
    except Exception as exc:
        state.failed_stage = state.current_stage
        state.errors.append(str(exc))
        raise
