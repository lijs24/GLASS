from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np

from glass.cpu.integration import weighted_integrate_stack
from glass.engine.contracts import (
    CombinePolicy,
    DQMask,
    OutputMapPolicy,
    RejectionPolicy,
    StackRequest,
    TileWindow,
)
from glass.engine.rejection import RESIDENT_WINSORIZED_SIGMA_HARDENED_FRAME_LIMIT
from glass.engine.stack_engine import CPUStackEngine
from glass.io.json_io import write_json
from glass.models import now_iso


def _difference_stats(actual: np.ndarray, expected: np.ndarray) -> dict[str, float]:
    diff = np.asarray(actual, dtype=np.float32) - np.asarray(expected, dtype=np.float32)
    finite = np.isfinite(diff)
    if not np.any(finite):
        return {"max_abs": float("nan"), "rms": float("nan"), "p99_abs": float("nan")}
    values = diff[finite].astype(np.float64)
    abs_values = np.abs(values)
    return {
        "max_abs": float(np.max(abs_values)),
        "rms": float(np.sqrt(np.mean(values * values))),
        "p99_abs": float(np.percentile(abs_values, 99.0)),
    }


def _synthetic_stack(frame_count: int, height: int, width: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(int(seed))
    yy, xx = np.indices((height, width), dtype=np.float32)
    base = np.float32(100.0) + np.float32(0.03) * xx + np.float32(0.05) * yy
    frames = []
    for index in range(frame_count):
        transparency = np.float32(1.0 + 0.002 * ((index % 7) - 3))
        background = np.float32(0.04 * ((index % 5) - 2))
        noise = rng.normal(0.0, 0.15 + 0.01 * (index % 4), size=(height, width)).astype(np.float32)
        frame = base * transparency + background + noise
        if index % 5 == 0:
            frame[(index * 3) % height, (index * 7) % width] += np.float32(35.0 + index)
        if index % 7 == 0:
            frame[(index * 5 + 1) % height, (index * 11 + 2) % width] -= np.float32(32.0 + index)
        frames.append(frame.astype(np.float32))
    weights = (np.float32(1.0) + np.float32(0.1) * np.sin(np.arange(frame_count, dtype=np.float32))).astype(
        np.float32
    )
    return np.stack(frames, axis=0), weights


def _timed_cpu_baseline(
    stack: np.ndarray,
    weights: np.ndarray,
    *,
    low_sigma: float,
    high_sigma: float,
) -> tuple[tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray], float]:
    start = perf_counter()
    result = weighted_integrate_stack(
        stack,
        weights=weights,
        rejection="winsorized_sigma",
        low_sigma=low_sigma,
        high_sigma=high_sigma,
    )
    return result, perf_counter() - start


@dataclass(slots=True)
class _ArrayImageSource:
    frame_id: str
    data: np.ndarray

    @property
    def path(self) -> str:
        return f"synthetic://resident-overlimit/{self.frame_id}"

    @property
    def width(self) -> int:
        return int(self.data.shape[1])

    @property
    def height(self) -> int:
        return int(self.data.shape[0])

    @property
    def channels(self) -> int:
        return 1

    @property
    def dtype(self) -> str:
        return str(self.data.dtype)

    @property
    def metadata(self) -> dict[str, Any]:
        return {"frame_id": self.frame_id, "source": "synthetic_resident_overlimit"}

    def read_tile(self, window: TileWindow, dtype: Any = np.float32) -> np.ndarray:
        y_slice, x_slice = window.as_slices()
        return np.asarray(self.data[y_slice, x_slice], dtype=dtype)

    def read_mask_tile(self, window: TileWindow) -> DQMask:
        return DQMask.empty(window.shape)


def _timed_cpu_stack_engine_baseline(
    stack: np.ndarray,
    weights: np.ndarray,
    *,
    low_sigma: float,
    high_sigma: float,
    min_samples: int,
    max_reject_fraction: float,
    tile_size: int,
) -> tuple[tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray], dict[str, Any], float]:
    frame_ids = tuple(f"frame_{index:04d}" for index in range(int(stack.shape[0])))
    sources = {
        frame_id: _ArrayImageSource(frame_id=frame_id, data=np.asarray(stack[index], dtype=np.float32))
        for index, frame_id in enumerate(frame_ids)
    }
    request = StackRequest(
        frame_ids=frame_ids,
        source_kind="light",
        combine=CombinePolicy(method="weighted_mean", accumulator_dtype="float64"),
        rejection=RejectionPolicy(
            method="winsorized_sigma",
            iterations=1,
            low_sigma=float(low_sigma),
            high_sigma=float(high_sigma),
            min_samples=int(min_samples),
            max_reject_fraction=float(max_reject_fraction),
        ),
        output_maps=OutputMapPolicy(
            coverage=True,
            weight=True,
            variance=False,
            low_rejection=True,
            high_rejection=True,
            dq=False,
        ),
        weights={frame_id: float(weights[index]) for index, frame_id in enumerate(frame_ids)},
        metadata={
            "baseline": "CPUStackEngine",
            "tile_size": int(tile_size),
            "source": "resident_winsorized_overlimit_benchmark",
        },
    )
    engine = CPUStackEngine(tile_size=tile_size)
    start = perf_counter()
    result = engine.stack(request, sources)
    elapsed = perf_counter() - start
    maps = (
        result.master,
        np.zeros_like(result.master, dtype=np.float32)
        if result.weight_map is None
        else result.weight_map,
        np.zeros_like(result.master, dtype=np.float32)
        if result.coverage_map is None
        else result.coverage_map,
        np.zeros_like(result.master, dtype=np.float32)
        if result.low_rejection_map is None
        else result.low_rejection_map,
        np.zeros_like(result.master, dtype=np.float32)
        if result.high_rejection_map is None
        else result.high_rejection_map,
    )
    provenance = {
        "metrics": dict(result.metrics),
        "dq_provenance": dict(result.dq_provenance),
    }
    return maps, provenance, elapsed


@contextmanager
def _temporary_env(name: str, value: str):
    previous = os.environ.get(name)
    os.environ[name] = value
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = previous


def _timed_fast_cuda(
    resident_stack: Any,
    weights: np.ndarray,
    *,
    low_sigma: float,
    high_sigma: float,
) -> tuple[tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray], dict[str, Any]]:
    start = perf_counter()
    result = resident_stack.integrate_sigma_clip(weights, low_sigma, high_sigma, True)
    elapsed = perf_counter() - start
    return result, {
        "schema_version": 1,
        "timing_model": "python_native_resident_fast_winsorized_sigma_one_sync",
        "native_method": "ResidentCalibratedStack.integrate_sigma_clip",
        "rejection": "winsorized_sigma",
        "resident_winsorized_mode": "fast_approx",
        "frame_count": int(resident_stack.frame_count),
        "height": int(resident_stack.height),
        "width": int(resident_stack.width),
        "pixel_count": int(resident_stack.height * resident_stack.width),
        "low_sigma": float(low_sigma),
        "high_sigma": float(high_sigma),
        "includes_device_sync_and_download": True,
        "total_s": float(elapsed),
    }


def build_resident_winsorized_benchmark(
    *,
    frame_count: int = 16,
    height: int = 32,
    width: int = 32,
    seed: int = 12345,
    low_sigma: float = 3.0,
    high_sigma: float = 3.0,
    tolerance_rms: float = 2.0e-5,
    tolerance_max_abs: float = 2.0e-4,
) -> dict[str, Any]:
    if frame_count <= 0 or height <= 0 or width <= 0:
        raise ValueError("frame_count, height, and width must be positive")
    if frame_count > RESIDENT_WINSORIZED_SIGMA_HARDENED_FRAME_LIMIT:
        raise ValueError(
            "resident hardened winsorized benchmark frame_count must be at most "
            f"{RESIDENT_WINSORIZED_SIGMA_HARDENED_FRAME_LIMIT}"
        )
    stack, weights = _synthetic_stack(frame_count, height, width, seed)
    cpu_result, cpu_elapsed = _timed_cpu_baseline(
        stack,
        weights,
        low_sigma=low_sigma,
        high_sigma=high_sigma,
    )

    try:
        import glass_cuda
    except Exception as exc:  # pragma: no cover - import diagnostics are environment-specific
        return _unavailable_payload(
            frame_count=frame_count,
            height=height,
            width=width,
            seed=seed,
            low_sigma=low_sigma,
            high_sigma=high_sigma,
            cpu_elapsed=cpu_elapsed,
            reason=f"{type(exc).__name__}: {exc}",
        )

    if not glass_cuda.cuda_available() or not hasattr(glass_cuda, "ResidentCalibratedStack"):
        return _unavailable_payload(
            frame_count=frame_count,
            height=height,
            width=width,
            seed=seed,
            low_sigma=low_sigma,
            high_sigma=high_sigma,
            cpu_elapsed=cpu_elapsed,
            reason="native CUDA ResidentCalibratedStack is unavailable",
        )

    resident_stack = glass_cuda.ResidentCalibratedStack(frame_count, height, width)
    for index, frame in enumerate(stack):
        resident_stack.upload_calibrated_frame(index, frame)
    fast_result, fast_timing = _timed_fast_cuda(
        resident_stack,
        weights,
        low_sigma=low_sigma,
        high_sigma=high_sigma,
    )
    hardened_result = resident_stack.integrate_hardened_winsorized_sigma_timed(
        weights,
        low_sigma,
        high_sigma,
    )
    hardened_maps = hardened_result[:5]
    hardened_timing = hardened_result[5]

    cpu_master, cpu_weight, cpu_coverage, cpu_low, cpu_high = cpu_result
    fast_master, fast_weight, fast_coverage, fast_low, fast_high = fast_result
    hard_master, hard_weight, hard_coverage, hard_low, hard_high = hardened_maps
    hard_master_stats = _difference_stats(hard_master, cpu_master)
    hard_weight_stats = _difference_stats(hard_weight, cpu_weight)
    hard_coverage_stats = _difference_stats(hard_coverage, cpu_coverage)
    hard_low_stats = _difference_stats(hard_low, cpu_low)
    hard_high_stats = _difference_stats(hard_high, cpu_high)
    fast_master_stats = _difference_stats(fast_master, cpu_master)

    checks = [
        _check("cuda_available", True, {"cuda_available": True}),
        _check("hardened_frame_limit_ok", frame_count <= RESIDENT_WINSORIZED_SIGMA_HARDENED_FRAME_LIMIT, {
            "frame_count": frame_count,
            "limit": RESIDENT_WINSORIZED_SIGMA_HARDENED_FRAME_LIMIT,
        }),
        _check(
            "hardened_master_rms_within_tolerance",
            hard_master_stats["rms"] <= tolerance_rms,
            {"actual": hard_master_stats["rms"], "required_max": tolerance_rms},
        ),
        _check(
            "hardened_master_max_abs_within_tolerance",
            hard_master_stats["max_abs"] <= tolerance_max_abs,
            {"actual": hard_master_stats["max_abs"], "required_max": tolerance_max_abs},
        ),
        _check("hardened_weight_map_matches_cpu", hard_weight_stats["max_abs"] <= tolerance_max_abs, hard_weight_stats),
        _check("hardened_coverage_map_matches_cpu", hard_coverage_stats["max_abs"] <= tolerance_max_abs, hard_coverage_stats),
        _check("hardened_low_rejection_map_matches_cpu", hard_low_stats["max_abs"] <= tolerance_max_abs, hard_low_stats),
        _check("hardened_high_rejection_map_matches_cpu", hard_high_stats["max_abs"] <= tolerance_max_abs, hard_high_stats),
    ]
    failed = [item for item in checks if not item.get("passed")]
    return {
        "schema_version": 1,
        "artifact_type": "resident_winsorized_benchmark",
        "created_at": now_iso(),
        "status": "passed" if not failed else "failed",
        "passed": not failed,
        "config": {
            "frame_count": int(frame_count),
            "height": int(height),
            "width": int(width),
            "seed": int(seed),
            "low_sigma": float(low_sigma),
            "high_sigma": float(high_sigma),
            "hardened_frame_limit": RESIDENT_WINSORIZED_SIGMA_HARDENED_FRAME_LIMIT,
            "tolerance_rms": float(tolerance_rms),
            "tolerance_max_abs": float(tolerance_max_abs),
        },
        "timing_s": {
            "cpu_baseline": float(cpu_elapsed),
            "cuda_fast_approx": float(fast_timing["total_s"]),
            "cuda_hardened": float(hardened_timing["total_s"]),
        },
        "cuda_fast_approx_timing": fast_timing,
        "cuda_hardened_timing": hardened_timing,
        "comparisons": {
            "hardened_vs_cpu": {
                "master": hard_master_stats,
                "weight": hard_weight_stats,
                "coverage": hard_coverage_stats,
                "low_rejection": hard_low_stats,
                "high_rejection": hard_high_stats,
            },
            "fast_approx_vs_cpu": {
                "master": fast_master_stats,
                "note": "fast approximation is measured for attribution and is not required to match CPU parity",
            },
        },
        "checks": checks,
        "failed_checks": [str(item.get("name")) for item in failed],
        "limitations": [
            "Synthetic microbenchmark only; it does not replace the 200-light benchmark.",
            "CPU timing is a local baseline for this small stack and is not a throughput claim.",
            "Fast approximation is included for timing and difference context, not as a parity requirement.",
        ],
    }


def build_resident_winsorized_overlimit_benchmark(
    *,
    frame_count: int = RESIDENT_WINSORIZED_SIGMA_HARDENED_FRAME_LIMIT + 33,
    height: int = 32,
    width: int = 32,
    seed: int = 627,
    low_sigma: float = 3.0,
    high_sigma: float = 3.0,
    min_samples: int = 3,
    max_reject_fraction: float = 0.5,
    tile_size: int = 16,
    tolerance_rms: float = 2.0e-5,
    tolerance_max_abs: float = 2.0e-4,
    inject_nan: bool = True,
) -> dict[str, Any]:
    if frame_count <= RESIDENT_WINSORIZED_SIGMA_HARDENED_FRAME_LIMIT:
        raise ValueError(
            "resident over-limit winsorized benchmark frame_count must be greater than "
            f"{RESIDENT_WINSORIZED_SIGMA_HARDENED_FRAME_LIMIT}"
        )
    if height <= 0 or width <= 0 or tile_size <= 0:
        raise ValueError("height, width, and tile_size must be positive")
    if min_samples < 1:
        raise ValueError("min_samples must be at least 1")
    if not 0.0 <= float(max_reject_fraction) <= 1.0:
        raise ValueError("max_reject_fraction must be between 0 and 1")

    stack, weights = _synthetic_stack(frame_count, height, width, seed)
    if inject_nan:
        stack[8 % frame_count, 3 % height, 4 % width] = np.nan
        if height >= 5 and width >= 6:
            stack[frame_count // 3, 4, 5] = np.nan

    cpu_result, cpu_provenance, cpu_elapsed = _timed_cpu_stack_engine_baseline(
        stack,
        weights,
        low_sigma=low_sigma,
        high_sigma=high_sigma,
        min_samples=min_samples,
        max_reject_fraction=max_reject_fraction,
        tile_size=tile_size,
    )

    try:
        import glass_cuda
    except Exception as exc:  # pragma: no cover - import diagnostics are environment-specific
        return _overlimit_unavailable_payload(
            frame_count=frame_count,
            height=height,
            width=width,
            seed=seed,
            low_sigma=low_sigma,
            high_sigma=high_sigma,
            min_samples=min_samples,
            max_reject_fraction=max_reject_fraction,
            tile_size=tile_size,
            tolerance_rms=tolerance_rms,
            tolerance_max_abs=tolerance_max_abs,
            inject_nan=inject_nan,
            cpu_elapsed=cpu_elapsed,
            cpu_provenance=cpu_provenance,
            reason=f"{type(exc).__name__}: {exc}",
        )

    if not glass_cuda.cuda_available() or not hasattr(glass_cuda, "ResidentCalibratedStack"):
        return _overlimit_unavailable_payload(
            frame_count=frame_count,
            height=height,
            width=width,
            seed=seed,
            low_sigma=low_sigma,
            high_sigma=high_sigma,
            min_samples=min_samples,
            max_reject_fraction=max_reject_fraction,
            tile_size=tile_size,
            tolerance_rms=tolerance_rms,
            tolerance_max_abs=tolerance_max_abs,
            inject_nan=inject_nan,
            cpu_elapsed=cpu_elapsed,
            cpu_provenance=cpu_provenance,
            reason="native CUDA ResidentCalibratedStack is unavailable",
        )

    resident_stack = glass_cuda.ResidentCalibratedStack(frame_count, height, width)
    upload_start = perf_counter()
    for index, frame in enumerate(stack):
        resident_stack.upload_calibrated_frame(index, frame)
    upload_elapsed = perf_counter() - upload_start

    with _temporary_env("GLASS_CUDA_RADIX_SELECT_WINSORIZED", "1"):
        cuda_result = resident_stack.integrate_hardened_winsorized_sigma_timed(
            weights,
            low_sigma,
            high_sigma,
            min_samples=int(min_samples),
            max_reject_fraction=float(max_reject_fraction),
            count_map_dtype="uint16",
        )
    cuda_maps = cuda_result[:5]
    cuda_timing = cuda_result[5]
    native_profile = cuda_timing.get("native_profile", {}) if isinstance(cuda_timing, dict) else {}

    cpu_master, cpu_weight, cpu_coverage, cpu_low, cpu_high = cpu_result
    cuda_master, cuda_weight, cuda_coverage, cuda_low, cuda_high = cuda_maps
    comparisons = {
        "radix_select_vs_cpu_stack_engine": {
            "master": _difference_stats(cuda_master, cpu_master),
            "weight": _difference_stats(cuda_weight, cpu_weight),
            "coverage": _difference_stats(cuda_coverage, cpu_coverage),
            "low_rejection": _difference_stats(cuda_low, cpu_low),
            "high_rejection": _difference_stats(cuda_high, cpu_high),
        }
    }
    map_stats = comparisons["radix_select_vs_cpu_stack_engine"]
    selector = str(cuda_timing.get("native_kernel_capacity_selector", ""))
    radix_enabled = bool(native_profile.get("radix_select_enabled"))
    checks = [
        _check("frame_count_exceeds_hardened_limit", True, {
            "frame_count": int(frame_count),
            "hardened_frame_limit": RESIDENT_WINSORIZED_SIGMA_HARDENED_FRAME_LIMIT,
        }),
        _check("cuda_available", True, {"cuda_available": True}),
        _check(
            "radix_select_enabled",
            radix_enabled,
            {"native_profile.radix_select_enabled": native_profile.get("radix_select_enabled")},
        ),
        _check(
            "radix_select_selector_used",
            selector == "radix_select_unbounded_positive_samples",
            {"native_kernel_capacity_selector": selector},
        ),
        _check(
            "radix_master_rms_within_tolerance",
            map_stats["master"]["rms"] <= tolerance_rms,
            {"actual": map_stats["master"]["rms"], "required_max": tolerance_rms},
        ),
        _check(
            "radix_master_max_abs_within_tolerance",
            map_stats["master"]["max_abs"] <= tolerance_max_abs,
            {"actual": map_stats["master"]["max_abs"], "required_max": tolerance_max_abs},
        ),
        _check("radix_weight_map_matches_cpu", map_stats["weight"]["max_abs"] <= tolerance_max_abs, map_stats["weight"]),
        _check("radix_coverage_map_matches_cpu", map_stats["coverage"]["max_abs"] <= tolerance_max_abs, map_stats["coverage"]),
        _check(
            "radix_low_rejection_map_matches_cpu",
            map_stats["low_rejection"]["max_abs"] <= tolerance_max_abs,
            map_stats["low_rejection"],
        ),
        _check(
            "radix_high_rejection_map_matches_cpu",
            map_stats["high_rejection"]["max_abs"] <= tolerance_max_abs,
            map_stats["high_rejection"],
        ),
    ]
    failed = [item for item in checks if not item.get("passed")]
    samples = int(frame_count) * int(height) * int(width)
    cuda_total_with_upload = float(upload_elapsed) + float(cuda_timing.get("total_s", 0.0))
    cpu_mpix_s = (samples / 1.0e6 / cpu_elapsed) if cpu_elapsed > 0 else None
    cuda_mpix_s = (
        samples / 1.0e6 / float(cuda_timing.get("total_s", 0.0))
        if float(cuda_timing.get("total_s", 0.0)) > 0
        else None
    )
    cuda_total_mpix_s = (samples / 1.0e6 / cuda_total_with_upload) if cuda_total_with_upload > 0 else None
    return {
        "schema_version": 1,
        "artifact_type": "resident_winsorized_overlimit_benchmark",
        "created_at": now_iso(),
        "status": "passed" if not failed else "failed",
        "passed": not failed,
        "config": {
            "frame_count": int(frame_count),
            "height": int(height),
            "width": int(width),
            "seed": int(seed),
            "low_sigma": float(low_sigma),
            "high_sigma": float(high_sigma),
            "min_samples": int(min_samples),
            "max_reject_fraction": float(max_reject_fraction),
            "tile_size": int(tile_size),
            "hardened_frame_limit": RESIDENT_WINSORIZED_SIGMA_HARDENED_FRAME_LIMIT,
            "radix_select_env": "GLASS_CUDA_RADIX_SELECT_WINSORIZED=1",
            "count_map_dtype": "uint16",
            "inject_nan": bool(inject_nan),
            "tolerance_rms": float(tolerance_rms),
            "tolerance_max_abs": float(tolerance_max_abs),
        },
        "timing_s": {
            "cpu_stack_engine": float(cpu_elapsed),
            "cuda_upload": float(upload_elapsed),
            "cuda_radix_select": float(cuda_timing.get("total_s", 0.0)),
            "cuda_total_with_upload": float(cuda_total_with_upload),
        },
        "throughput": {
            "pixels": int(height) * int(width),
            "samples": samples,
            "cpu_stack_engine_mpix_s": None if cpu_mpix_s is None else float(cpu_mpix_s),
            "cuda_radix_select_mpix_s": None if cuda_mpix_s is None else float(cuda_mpix_s),
            "cuda_total_with_upload_mpix_s": None if cuda_total_mpix_s is None else float(cuda_total_mpix_s),
        },
        "speedup_vs_cpu_stack_engine": {
            "excluding_upload": (
                float(cpu_elapsed) / float(cuda_timing.get("total_s", 0.0))
                if float(cuda_timing.get("total_s", 0.0)) > 0
                else None
            ),
            "including_upload": float(cpu_elapsed) / cuda_total_with_upload if cuda_total_with_upload > 0 else None,
        },
        "cpu_stack_engine_baseline": cpu_provenance,
        "cuda_radix_timing": cuda_timing,
        "comparisons": comparisons,
        "checks": checks,
        "failed_checks": [str(item.get("name")) for item in failed],
        "limitations": [
            "Synthetic over-limit benchmark only; it does not replace the real 200-light regression.",
            "This gate validates the opt-in radix-select resident path against the tiled CPUStackEngine baseline.",
            "The default production path is unchanged by this artifact.",
        ],
    }


def _check(name: str, passed: bool, evidence: dict[str, Any], note: str = "") -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "evidence": evidence, "note": note}


def _unavailable_payload(
    *,
    frame_count: int,
    height: int,
    width: int,
    seed: int,
    low_sigma: float,
    high_sigma: float,
    cpu_elapsed: float,
    reason: str,
) -> dict[str, Any]:
    check = _check("cuda_available", False, {"reason": reason})
    return {
        "schema_version": 1,
        "artifact_type": "resident_winsorized_benchmark",
        "created_at": now_iso(),
        "status": "cuda_unavailable",
        "passed": False,
        "config": {
            "frame_count": int(frame_count),
            "height": int(height),
            "width": int(width),
            "seed": int(seed),
            "low_sigma": float(low_sigma),
            "high_sigma": float(high_sigma),
            "hardened_frame_limit": RESIDENT_WINSORIZED_SIGMA_HARDENED_FRAME_LIMIT,
        },
        "timing_s": {"cpu_baseline": float(cpu_elapsed)},
        "checks": [check],
        "failed_checks": [check["name"]],
        "limitations": ["CUDA was unavailable; only the CPU baseline was timed."],
    }


def _overlimit_unavailable_payload(
    *,
    frame_count: int,
    height: int,
    width: int,
    seed: int,
    low_sigma: float,
    high_sigma: float,
    min_samples: int,
    max_reject_fraction: float,
    tile_size: int,
    tolerance_rms: float,
    tolerance_max_abs: float,
    inject_nan: bool,
    cpu_elapsed: float,
    cpu_provenance: dict[str, Any],
    reason: str,
) -> dict[str, Any]:
    check = _check("cuda_available", False, {"reason": reason})
    return {
        "schema_version": 1,
        "artifact_type": "resident_winsorized_overlimit_benchmark",
        "created_at": now_iso(),
        "status": "cuda_unavailable",
        "passed": False,
        "config": {
            "frame_count": int(frame_count),
            "height": int(height),
            "width": int(width),
            "seed": int(seed),
            "low_sigma": float(low_sigma),
            "high_sigma": float(high_sigma),
            "min_samples": int(min_samples),
            "max_reject_fraction": float(max_reject_fraction),
            "tile_size": int(tile_size),
            "hardened_frame_limit": RESIDENT_WINSORIZED_SIGMA_HARDENED_FRAME_LIMIT,
            "radix_select_env": "GLASS_CUDA_RADIX_SELECT_WINSORIZED=1",
            "count_map_dtype": "uint16",
            "inject_nan": bool(inject_nan),
            "tolerance_rms": float(tolerance_rms),
            "tolerance_max_abs": float(tolerance_max_abs),
        },
        "timing_s": {"cpu_stack_engine": float(cpu_elapsed)},
        "cpu_stack_engine_baseline": cpu_provenance,
        "checks": [check],
        "failed_checks": [check["name"]],
        "limitations": ["CUDA was unavailable; only the CPUStackEngine baseline was timed."],
    }


def _markdown(payload: dict[str, Any]) -> str:
    timing = payload.get("timing_s", {})
    comparisons = payload.get("comparisons", {})
    hardened = comparisons.get("hardened_vs_cpu", {}) if isinstance(comparisons, dict) else {}
    fast = comparisons.get("fast_approx_vs_cpu", {}) if isinstance(comparisons, dict) else {}
    lines = [
        "# Resident Winsorized Benchmark",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Passed: `{payload.get('passed')}`",
        f"- Frames: `{payload.get('config', {}).get('frame_count')}`",
        f"- Shape: `{payload.get('config', {}).get('height')}x{payload.get('config', {}).get('width')}`",
        "",
        "## Timing",
        "",
        "| path | seconds |",
        "| --- | ---: |",
        f"| CPU baseline | {timing.get('cpu_baseline')} |",
        f"| CUDA fast approximation | {timing.get('cuda_fast_approx')} |",
        f"| CUDA hardened | {timing.get('cuda_hardened')} |",
        "",
        "## Differences",
        "",
        "| comparison | RMS | max abs | p99 abs |",
        "| --- | ---: | ---: | ---: |",
    ]
    hard_master = hardened.get("master", {}) if isinstance(hardened, dict) else {}
    fast_master = fast.get("master", {}) if isinstance(fast, dict) else {}
    lines.append(
        f"| hardened master vs CPU | {hard_master.get('rms')} | {hard_master.get('max_abs')} | {hard_master.get('p99_abs')} |"
    )
    lines.append(
        f"| fast master vs CPU | {fast_master.get('rms')} | {fast_master.get('max_abs')} | {fast_master.get('p99_abs')} |"
    )
    lines.extend(["", "## Failed Checks", ""])
    failed = payload.get("failed_checks", [])
    if failed:
        for name in failed:
            lines.append(f"- `{name}`")
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def _overlimit_markdown(payload: dict[str, Any]) -> str:
    timing = payload.get("timing_s", {})
    speedup = payload.get("speedup_vs_cpu_stack_engine", {})
    comparisons = payload.get("comparisons", {})
    radix = (
        comparisons.get("radix_select_vs_cpu_stack_engine", {})
        if isinstance(comparisons, dict)
        else {}
    )
    lines = [
        "# Resident Winsorized Over-Limit Benchmark",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Passed: `{payload.get('passed')}`",
        f"- Frames: `{payload.get('config', {}).get('frame_count')}`",
        f"- Shape: `{payload.get('config', {}).get('height')}x{payload.get('config', {}).get('width')}`",
        f"- CPU tile size: `{payload.get('config', {}).get('tile_size')}`",
        f"- Hardened frame limit: `{payload.get('config', {}).get('hardened_frame_limit')}`",
        "",
        "## Timing",
        "",
        "| path | seconds |",
        "| --- | ---: |",
        f"| CPU StackEngine tiled baseline | {timing.get('cpu_stack_engine')} |",
        f"| CUDA upload | {timing.get('cuda_upload')} |",
        f"| CUDA radix-select integration | {timing.get('cuda_radix_select')} |",
        f"| CUDA total with upload | {timing.get('cuda_total_with_upload')} |",
        "",
        "## Speedup",
        "",
        "| comparison | factor |",
        "| --- | ---: |",
        f"| CUDA radix-select excluding upload vs CPU StackEngine | {speedup.get('excluding_upload')} |",
        f"| CUDA radix-select including upload vs CPU StackEngine | {speedup.get('including_upload')} |",
        "",
        "## Differences",
        "",
        "| map | RMS | max abs | p99 abs |",
        "| --- | ---: | ---: | ---: |",
    ]
    for name in ("master", "weight", "coverage", "low_rejection", "high_rejection"):
        stats = radix.get(name, {}) if isinstance(radix, dict) else {}
        lines.append(
            f"| {name} | {stats.get('rms')} | {stats.get('max_abs')} | {stats.get('p99_abs')} |"
        )
    lines.extend(["", "## Failed Checks", ""])
    failed = payload.get("failed_checks", [])
    if failed:
        for name in failed:
            lines.append(f"- `{name}`")
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def write_resident_winsorized_benchmark(
    out: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(out, payload)
    if markdown is not None:
        Path(markdown).write_text(_markdown(payload), encoding="utf-8")


def write_resident_winsorized_overlimit_benchmark(
    out: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(out, payload)
    if markdown is not None:
        Path(markdown).write_text(_overlimit_markdown(payload), encoding="utf-8")
