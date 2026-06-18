from __future__ import annotations

from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np

from glass.cpu.integration import weighted_integrate_stack
from glass.engine.rejection import RESIDENT_WINSORIZED_SIGMA_HARDENED_FRAME_LIMIT
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


def write_resident_winsorized_benchmark(
    out: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(out, payload)
    if markdown is not None:
        Path(markdown).write_text(_markdown(payload), encoding="utf-8")
