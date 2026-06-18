from __future__ import annotations

from typing import Any

import numpy as np

from glass.engine.contracts import RejectionPolicy


CPU_WINSORIZED_SIGMA_SCALE_ESTIMATOR = "median_iqr_winsorized_standard_deviation_scale"
RESIDENT_WINSORIZED_SIGMA_FAST_APPROX_MODE = "fast_approx"
RESIDENT_WINSORIZED_SIGMA_HARDENED_MODE = "hardened_cpu_parity"
RESIDENT_WINSORIZED_SIGMA_ALGORITHM = "two_stage_winsorized_mean_std_rejection_approximation"
RESIDENT_WINSORIZED_SIGMA_SCALE_ESTIMATOR = "mean_std_two_stage_winsorized"
RESIDENT_WINSORIZED_SIGMA_PARITY_STATUS = "known_non_parity_pending_cuda_update"
RESIDENT_WINSORIZED_SIGMA_HARDENED_ALGORITHM = "median_iqr_winsorized_sigma_cuda_resident_prototype"
RESIDENT_WINSORIZED_SIGMA_HARDENED_PARITY_STATUS = "cpu_baseline_parity_passed_gate_261"


def center_and_scale(
    stack: np.ndarray,
    valid: np.ndarray,
    *,
    method: str,
    low_sigma: float,
    high_sigma: float,
) -> tuple[np.ndarray, np.ndarray]:
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
    resident_winsorized_mode: str = RESIDENT_WINSORIZED_SIGMA_FAST_APPROX_MODE,
) -> dict[str, Any]:
    descriptor: dict[str, Any] = {
        "mode": str(method),
        "low_sigma": float(low_sigma),
        "high_sigma": float(high_sigma),
    }
    if method == "winsorized_sigma":
        if resident_winsorized_mode == RESIDENT_WINSORIZED_SIGMA_HARDENED_MODE:
            descriptor.update(
                {
                    "resident_winsorized_mode": RESIDENT_WINSORIZED_SIGMA_HARDENED_MODE,
                    "algorithm": RESIDENT_WINSORIZED_SIGMA_HARDENED_ALGORITHM,
                    "scale_estimator": CPU_WINSORIZED_SIGMA_SCALE_ESTIMATOR,
                    "cpu_baseline_scale_estimator": CPU_WINSORIZED_SIGMA_SCALE_ESTIMATOR,
                    "cpu_baseline_parity": True,
                    "parity_status": RESIDENT_WINSORIZED_SIGMA_HARDENED_PARITY_STATUS,
                    "approximation": False,
                    "frame_limit": 256,
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
