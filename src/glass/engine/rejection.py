from __future__ import annotations

from typing import Any

import numpy as np

from glass.engine.contracts import RejectionPolicy


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
        return "median_iqr_winsorized_standard_deviation_scale"
    if method_name == "percentile":
        return "percentile_thresholds"
    if method_name == "minmax":
        return "minmax_extrema"
    return "unknown"


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
