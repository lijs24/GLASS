from __future__ import annotations

from typing import Any

import numpy as np

from glass.engine.contracts import RejectionPolicy


CPU_WINSORIZED_SIGMA_SCALE_ESTIMATOR = "median_iqr_winsorized_standard_deviation_scale"
RESIDENT_WINSORIZED_SIGMA_AUTO_MODE = "auto"
RESIDENT_WINSORIZED_SIGMA_FAST_APPROX_MODE = "fast_approx"
RESIDENT_WINSORIZED_SIGMA_HARDENED_MODE = "hardened_cpu_parity"
RESIDENT_WINSORIZED_SIGMA_HARDENED_FRAME_LIMIT = 256
RESIDENT_WINSORIZED_SIGMA_HARDENED_NATIVE_FRAME_LIMIT = RESIDENT_WINSORIZED_SIGMA_HARDENED_FRAME_LIMIT
RESIDENT_WINSORIZED_SIGMA_AUTO_HARDENED_FRAME_LIMIT = RESIDENT_WINSORIZED_SIGMA_HARDENED_FRAME_LIMIT
RESIDENT_WINSORIZED_SIGMA_AUTO_COVERAGE_GUARD_FRAME_THRESHOLD = 64
RESIDENT_WINSORIZED_SIGMA_AUTO_COVERAGE_GUARD_MAX_FRACTION = 0.015
RESIDENT_WINSORIZED_SIGMA_ALGORITHM = "two_stage_winsorized_mean_std_rejection_approximation"
RESIDENT_WINSORIZED_SIGMA_SCALE_ESTIMATOR = "mean_std_two_stage_winsorized"
RESIDENT_WINSORIZED_SIGMA_PARITY_STATUS = "known_non_parity_pending_cuda_update"
RESIDENT_WINSORIZED_SIGMA_HARDENED_ALGORITHM = "median_iqr_winsorized_sigma_cuda_resident_prototype"
RESIDENT_WINSORIZED_SIGMA_HARDENED_SEGMENTED_ALGORITHM = (
    "median_iqr_winsorized_sigma_cpu_stack_engine_resident_tile_download"
)
RESIDENT_WINSORIZED_SIGMA_HARDENED_PARITY_STATUS = "cpu_baseline_parity_passed_gate_261"
RESIDENT_WINSORIZED_SIGMA_NATIVE_CUDA_ROUTE = "native_cuda_resident_stack"
RESIDENT_WINSORIZED_SIGMA_SEGMENTED_CPU_ROUTE = "cpu_stack_engine_segmented_resident_download"


def center_and_scale(
    stack: np.ndarray,
    valid: np.ndarray,
    *,
    method: str,
    low_sigma: float,
    high_sigma: float,
) -> tuple[np.ndarray, np.ndarray]:
    if method == "winsorized_sigma" and _all_valid_finite(stack, valid):
        return _winsorized_sigma_all_valid(
            stack,
            low_sigma=low_sigma,
            high_sigma=high_sigma,
        )

    masked = np.where(valid, stack, np.nan)
    if method in {"sigma", "sigma_clip"}:
        center = np.nanmedian(masked, axis=0)
        scale = np.nanstd(masked, axis=0)
    elif method in {"mad", "median_sigma"}:
        center = np.nanmedian(masked, axis=0)
        deviation = np.abs(masked - center[None, :, :])
        scale = np.float32(1.4826) * np.nanmedian(deviation, axis=0)
    elif method == "winsorized_sigma":
        first_center = np.nanmedian(masked, axis=0)
        first_scale = _iqr_scale(masked)
        fallback_scale = np.nanstd(masked, axis=0)
        first_scale = np.where(first_scale > 0, first_scale, fallback_scale)
        low = first_center - np.float32(low_sigma) * first_scale
        high = first_center + np.float32(high_sigma) * first_scale
        winsorized = np.where(valid, np.clip(stack, low[None, :, :], high[None, :, :]), np.nan)
        center = np.nanmean(winsorized, axis=0)
        scale = np.nanstd(winsorized, axis=0)
        scale = np.where(scale > 0, scale, first_scale)
    else:
        raise ValueError(f"unsupported rejection statistics method: {method}")
    return np.nan_to_num(center, nan=0.0).astype(np.float32), np.nan_to_num(
        scale, nan=0.0
    ).astype(np.float32)


def center_and_scale_for_policy(
    stack: np.ndarray, valid: np.ndarray, policy: RejectionPolicy
) -> tuple[np.ndarray, np.ndarray]:
    return center_and_scale(
        stack,
        valid,
        method=policy.method,
        low_sigma=policy.low_sigma,
        high_sigma=policy.high_sigma,
    )


def rejection_scale_estimator(method: str | RejectionPolicy) -> str:
    method_name = method.method if isinstance(method, RejectionPolicy) else str(method)
    if method_name == "none":
        return "none"
    if method_name in {"sigma", "sigma_clip"}:
        return "median_center_standard_deviation_scale"
    if method_name in {"mad", "median_sigma"}:
        return "median_center_mad_scale"
    if method_name == "winsorized_sigma":
        return CPU_WINSORIZED_SIGMA_SCALE_ESTIMATOR
    if method_name == "percentile":
        return "percentile_thresholds"
    if method_name == "minmax":
        return "minmax_extrema"
    return "unknown"


def resident_rejection_descriptor(
    method: str,
    low_sigma: float,
    high_sigma: float,
    *,
    min_samples: int = 3,
    max_reject_fraction: float = 0.5,
    max_reject_fraction_source: str | None = None,
    max_reject_fraction_resolution: dict[str, Any] | None = None,
    resident_winsorized_mode: str = RESIDENT_WINSORIZED_SIGMA_FAST_APPROX_MODE,
    requested_resident_winsorized_mode: str | None = None,
    resident_winsorized_resolution_reason: str | None = None,
    hardened_execution_route: str | None = None,
) -> dict[str, Any]:
    descriptor: dict[str, Any] = {
        "mode": str(method),
        "low_sigma": float(low_sigma),
        "high_sigma": float(high_sigma),
        "min_samples": int(min_samples),
        "max_reject_fraction": float(max_reject_fraction),
    }
    if max_reject_fraction_source is not None:
        descriptor["max_reject_fraction_source"] = str(max_reject_fraction_source)
    if max_reject_fraction_resolution is not None:
        descriptor["max_reject_fraction_resolution"] = max_reject_fraction_resolution
    if method == "winsorized_sigma":
        if resident_winsorized_mode == RESIDENT_WINSORIZED_SIGMA_HARDENED_MODE:
            route = hardened_execution_route or RESIDENT_WINSORIZED_SIGMA_NATIVE_CUDA_ROUTE
            algorithm = (
                RESIDENT_WINSORIZED_SIGMA_HARDENED_SEGMENTED_ALGORITHM
                if route == RESIDENT_WINSORIZED_SIGMA_SEGMENTED_CPU_ROUTE
                else RESIDENT_WINSORIZED_SIGMA_HARDENED_ALGORITHM
            )
            descriptor.update(
                {
                    "resident_winsorized_mode": RESIDENT_WINSORIZED_SIGMA_HARDENED_MODE,
                    "requested_resident_winsorized_mode": (
                        requested_resident_winsorized_mode or resident_winsorized_mode
                    ),
                    "resident_winsorized_resolution_reason": resident_winsorized_resolution_reason,
                    "algorithm": algorithm,
                    "hardened_execution_route": route,
                    "scale_estimator": CPU_WINSORIZED_SIGMA_SCALE_ESTIMATOR,
                    "cpu_baseline_scale_estimator": CPU_WINSORIZED_SIGMA_SCALE_ESTIMATOR,
                    "cpu_baseline_parity": True,
                    "parity_status": RESIDENT_WINSORIZED_SIGMA_HARDENED_PARITY_STATUS,
                    "approximation": False,
                    "frame_limit": RESIDENT_WINSORIZED_SIGMA_HARDENED_FRAME_LIMIT,
                    "native_frame_limit": RESIDENT_WINSORIZED_SIGMA_HARDENED_NATIVE_FRAME_LIMIT,
                    "segmented_cpu_fallback": route == RESIDENT_WINSORIZED_SIGMA_SEGMENTED_CPU_ROUTE,
                }
            )
            return descriptor
        if resident_winsorized_mode != RESIDENT_WINSORIZED_SIGMA_FAST_APPROX_MODE:
            raise ValueError(
                "resident_winsorized_mode must be fast_approx or hardened_cpu_parity"
            )
        descriptor.update(
            {
                "resident_winsorized_mode": RESIDENT_WINSORIZED_SIGMA_FAST_APPROX_MODE,
                "requested_resident_winsorized_mode": (
                    requested_resident_winsorized_mode or resident_winsorized_mode
                ),
                "resident_winsorized_resolution_reason": resident_winsorized_resolution_reason,
                "algorithm": RESIDENT_WINSORIZED_SIGMA_ALGORITHM,
                "scale_estimator": RESIDENT_WINSORIZED_SIGMA_SCALE_ESTIMATOR,
                "cpu_baseline_scale_estimator": CPU_WINSORIZED_SIGMA_SCALE_ESTIMATOR,
                "cpu_baseline_parity": False,
                "parity_status": RESIDENT_WINSORIZED_SIGMA_PARITY_STATUS,
                "approximation": True,
            }
        )
    elif method == "sigma_clip":
        descriptor.update(
            {
                "algorithm": "two_pass_mean_std_clip",
                "scale_estimator": "mean_std_two_pass",
                "cpu_baseline_scale_estimator": rejection_scale_estimator("sigma_clip"),
                "cpu_baseline_parity": False,
                "parity_status": "known_non_parity_pending_cuda_update",
                "approximation": True,
            }
        )
    else:
        descriptor.update(
            {
                "algorithm": "none",
                "scale_estimator": "none",
                "cpu_baseline_scale_estimator": rejection_scale_estimator(method),
                "cpu_baseline_parity": method == "none",
                "parity_status": "not_applicable" if method == "none" else "unknown",
                "approximation": False,
            }
        )
    return descriptor


def rejection_policy_provenance(policy: RejectionPolicy) -> dict[str, Any]:
    provenance: dict[str, Any] = {
        "method": policy.method,
        "iterations": int(policy.iterations),
        "low_sigma": float(policy.low_sigma),
        "high_sigma": float(policy.high_sigma),
        "min_samples": int(policy.min_samples),
        "max_reject_fraction": float(policy.max_reject_fraction),
        "scale_estimator": rejection_scale_estimator(policy),
    }
    if policy.method == "winsorized_sigma":
        provenance["winsorized"] = True
        provenance["winsorization_center"] = "nanmedian"
        provenance["winsorization_scale"] = "iqr_sigma_with_standard_deviation_fallback"
        provenance["final_center"] = "nanmean_after_winsorization"
        provenance["final_scale"] = "nanstd_after_winsorization"
    return provenance


def _iqr_scale(masked: np.ndarray) -> np.ndarray:
    q25 = np.nanpercentile(masked, 25.0, axis=0)
    q75 = np.nanpercentile(masked, 75.0, axis=0)
    return ((q75 - q25) / np.float32(1.349)).astype(np.float32)


def _all_valid_finite(stack: np.ndarray, valid: np.ndarray) -> bool:
    return bool(np.all(valid)) and bool(np.all(np.isfinite(stack)))


def _winsorized_sigma_all_valid(
    stack: np.ndarray,
    *,
    low_sigma: float,
    high_sigma: float,
) -> tuple[np.ndarray, np.ndarray]:
    data = np.asarray(stack, dtype=np.float32)
    sorted_stack = np.sort(data, axis=0)
    first_center = _percentile_from_sorted(sorted_stack, 50.0)
    q25 = _percentile_from_sorted(sorted_stack, 25.0)
    q75 = _percentile_from_sorted(sorted_stack, 75.0)
    first_scale = ((q75 - q25) / np.float32(1.349)).astype(np.float32)
    fallback_scale = np.std(data, axis=0, dtype=np.float64).astype(np.float32)
    first_scale = np.where(first_scale > 0, first_scale, fallback_scale)
    low = first_center - np.float32(low_sigma) * first_scale
    high = first_center + np.float32(high_sigma) * first_scale
    winsorized = np.clip(data, low[None, :, :], high[None, :, :])
    center = np.mean(winsorized, axis=0, dtype=np.float64).astype(np.float32)
    scale = np.std(winsorized, axis=0, dtype=np.float64).astype(np.float32)
    scale = np.where(scale > 0, scale, first_scale)
    return center.astype(np.float32), scale.astype(np.float32)


def _percentile_from_sorted(sorted_stack: np.ndarray, percentile: float) -> np.ndarray:
    frame_count = int(sorted_stack.shape[0])
    if frame_count <= 0:
        raise ValueError("cannot compute percentile of an empty stack")
    if frame_count == 1:
        return np.asarray(sorted_stack[0], dtype=np.float32)
    position = (np.float32(percentile) / np.float32(100.0)) * np.float32(frame_count - 1)
    lower = int(np.floor(position))
    upper = int(np.ceil(position))
    fraction = np.float32(position - lower)
    lower_values = np.asarray(sorted_stack[lower], dtype=np.float32)
    if upper == lower:
        return lower_values
    upper_values = np.asarray(sorted_stack[upper], dtype=np.float32)
    return (lower_values + (upper_values - lower_values) * fraction).astype(np.float32)
