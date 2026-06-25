from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import numpy as np

from glass.cpu.cosmetic import detect_isolated_cosmetic_defects
from glass.engine.contracts import DQFlag, DQMask
from glass.io.fits_io import read_fits_data


def _empty_flag_counts() -> dict[str, int]:
    return {flag.name.lower(): 0 for flag in DQFlag if flag != DQFlag.VALID}


def _dq_flag_counts(data: np.ndarray) -> dict[str, int]:
    counts = _empty_flag_counts()
    bits = np.asarray(data, dtype=np.uint32)
    for flag in DQFlag:
        if flag == DQFlag.VALID:
            continue
        counts[flag.name.lower()] = int(np.count_nonzero((bits & np.uint32(int(flag))) != 0))
    return counts


def source_invalid_mask_from_array(
    data: Any,
    *,
    height: int,
    width: int,
) -> tuple[np.ndarray | None, dict[str, Any]]:
    """Build a source-DQ invalid mask from a resident input array.

    Resident CUDA kernels already treat NaN samples as invalid. This helper
    gives finite DQ flags the same route by turning invalid source samples into
    NaN before integration. Raw byte FITS payloads are reported as unsupported
    for mask extraction here because their compatibility guard implies integer
    samples without NaN payload values.
    """

    shape = (int(height), int(width))
    array = np.asarray(data)
    if array.shape != shape:
        return None, {
            "supported": False,
            "reason": "source_array_shape_not_image",
            "shape": list(array.shape),
            "expected_shape": list(shape),
            "invalid_samples": 0,
        }
    if not np.issubdtype(array.dtype, np.floating):
        return None, {
            "supported": False,
            "reason": "source_array_not_floating",
            "shape": list(array.shape),
            "dtype": str(array.dtype),
            "invalid_samples": 0,
        }

    invalid = ~np.isfinite(array)
    invalid_count = int(np.count_nonzero(invalid))
    return invalid.astype(np.uint8, copy=False), {
        "supported": True,
        "reason": "",
        "shape": list(array.shape),
        "dtype": str(array.dtype),
        "invalid_samples": invalid_count,
        "flagged_samples": 0,
        "nonfinite_samples": invalid_count,
        "flag_counts": {},
        "source_model": "nonfinite_source_samples",
    }


def source_invalid_mask_from_inline_cosmetic(
    data: Any,
    *,
    height: int,
    width: int,
    hot_sigma: float = 8.0,
    cold_sigma: float = 8.0,
) -> tuple[np.ndarray | None, dict[str, Any]]:
    """Build an in-memory source-DQ mask with the CPU cosmetic detector.

    This helper intentionally returns only the invalid-sample mask. Resident
    CUDA applies the mask to the calibrated stack as NaN samples; it does not
    replace cosmetic defects with synthetic values.
    """

    shape = (int(height), int(width))
    array = np.asarray(data)
    if array.shape != shape:
        return None, {
            "supported": False,
            "reason": "inline_cosmetic_source_shape_not_image",
            "shape": list(array.shape),
            "expected_shape": list(shape),
            "invalid_samples": 0,
            "flag_counts": {},
            "source_model": "inline_structure_cosmetic_source_dq",
        }
    if not np.issubdtype(array.dtype, np.number):
        return None, {
            "supported": False,
            "reason": "inline_cosmetic_source_not_numeric",
            "shape": list(array.shape),
            "dtype": str(array.dtype),
            "invalid_samples": 0,
            "flag_counts": {},
            "source_model": "inline_structure_cosmetic_source_dq",
        }

    result = detect_isolated_cosmetic_defects(
        np.asarray(array, dtype=np.float32),
        hot_sigma=float(hot_sigma),
        cold_sigma=float(cold_sigma),
    )
    invalid_mask, info = source_invalid_mask_from_dq_mask(result.dq_mask, height=height, width=width)
    info.update(
        {
            "source_model": "inline_structure_cosmetic_source_dq",
            "inline_source_dq": True,
            "inline_source_dq_detector": "glass.cpu.cosmetic.detect_isolated_cosmetic_defects",
            "inline_source_dq_applies_replacement": False,
            "hot_sigma": float(hot_sigma),
            "cold_sigma": float(cold_sigma),
            "cosmetic_metrics": dict(result.metrics),
        }
    )
    return invalid_mask, info


def inline_cosmetic_thresholds_from_array(
    data: Any,
    *,
    height: int,
    width: int,
    hot_sigma: float = 8.0,
    cold_sigma: float = 8.0,
) -> dict[str, Any]:
    """Compute scalar cosmetic thresholds for resident CUDA application.

    This is intentionally not a CPU mask generator. CPU computes only the
    median/MAD-derived thresholds used by the existing cosmetic baseline; the
    per-pixel hot/cold/nonfinite detection and invalid-sample application run
    inside the resident CUDA stack.
    """

    shape = (int(height), int(width))
    array = np.asarray(data)
    if array.shape != shape:
        return {
            "supported": False,
            "reason": "inline_cosmetic_cuda_source_shape_not_image",
            "shape": list(array.shape),
            "expected_shape": list(shape),
            "invalid_samples": 0,
            "flag_counts": {},
            "source_model": "inline_structure_cosmetic_cuda_thresholds",
        }
    if not np.issubdtype(array.dtype, np.number):
        return {
            "supported": False,
            "reason": "inline_cosmetic_cuda_source_not_numeric",
            "shape": list(array.shape),
            "dtype": str(array.dtype),
            "invalid_samples": 0,
            "flag_counts": {},
            "source_model": "inline_structure_cosmetic_cuda_thresholds",
        }

    image = np.asarray(array, dtype=np.float32)
    finite = image[np.isfinite(image)]
    if finite.size == 0:
        median = 0.0
        sigma = 0.0
        low_threshold = float("-inf")
        high_threshold = float("inf")
    else:
        median = float(np.median(finite))
        mad = float(np.median(np.abs(finite - np.float32(median))))
        sigma = 1.4826 * mad if mad > 0 else float(np.std(finite))
        if sigma <= 0:
            sigma = 1.0
        low_threshold = float(np.float32(median - float(cold_sigma) * sigma))
        high_threshold = float(np.float32(median + float(hot_sigma) * sigma))

    return {
        "supported": True,
        "reason": "",
        "shape": list(image.shape),
        "dtype": str(image.dtype),
        "invalid_samples": 0,
        "flagged_samples": 0,
        "nonfinite_samples": 0,
        "flag_counts": {},
        "source_model": "inline_structure_cosmetic_cuda_thresholds",
        "inline_source_dq": True,
        "inline_source_dq_detector": "ResidentCalibratedStack.apply_isolated_cosmetic_threshold_mask_frame",
        "inline_source_dq_applies_replacement": False,
        "detector_execution": "cuda_isolated_threshold_apply",
        "threshold_source": "cpu_median_mad_scalar",
        "hot_sigma": float(hot_sigma),
        "cold_sigma": float(cold_sigma),
        "low_threshold": low_threshold,
        "high_threshold": high_threshold,
        "structure_sigma": 1.5,
        "min_neighbor_support": 2,
        "cosmetic_metrics": {
            "median": median,
            "sigma": float(sigma),
            "hot_pixels": None,
            "cold_pixels": None,
            "candidate_hot_pixels": None,
            "candidate_cold_pixels": None,
            "protected_hot_pixels": None,
            "protected_cold_pixels": None,
            "structure_sigma": 1.5,
            "min_neighbor_support": 2,
        },
    }


def _inline_cosmetic_threshold_info_from_stats(
    stats: dict[str, Any],
    *,
    shape: tuple[int, int],
    hot_sigma: float,
    cold_sigma: float,
    fallback_threshold_source: str,
    fallback_native_method: str,
    fallback_execution: str,
    batch_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    info = {
        "supported": True,
        "reason": "",
        "shape": list(shape),
        "dtype": "float32",
        "invalid_samples": 0,
        "flagged_samples": 0,
        "nonfinite_samples": 0,
        "flag_counts": {},
        "source_model": "inline_structure_cosmetic_cuda_thresholds",
        "inline_source_dq": True,
        "inline_source_dq_detector": "ResidentCalibratedStack.apply_isolated_cosmetic_threshold_mask_frame",
        "inline_source_dq_applies_replacement": False,
        "detector_execution": "cuda_isolated_threshold_apply",
        "threshold_source": str(stats.get("threshold_source") or fallback_threshold_source),
        "threshold_stats": stats,
        "threshold_stats_native_method": str(stats.get("native_method") or fallback_native_method),
        "threshold_stats_domain": str(stats.get("stats_domain") or "resident_calibrated_frame"),
        "threshold_stats_execution": str(stats.get("robust_stats_execution") or fallback_execution),
        "threshold_stats_materializes_host_frame": bool(stats.get("materializes_host_frame", False)),
        "threshold_stats_sample_count": int(stats.get("sample_count") or 0),
        "threshold_stats_sample_download_bytes": int(stats.get("sample_download_bytes") or 0),
        "threshold_stats_bin_count": int(stats.get("bin_count") or 0),
        "threshold_stats_histogram_download_bytes": int(stats.get("histogram_download_bytes") or 0),
        "threshold_stats_histogram_approximation": stats.get("histogram_approximation"),
        "threshold_stats_batch_reuses_device_work_buffers": stats.get(
            "batch_reuses_device_work_buffers"
        ),
        "hot_sigma": float(hot_sigma),
        "cold_sigma": float(cold_sigma),
        "low_threshold": float(stats.get("low_threshold", float("-inf"))),
        "high_threshold": float(stats.get("high_threshold", float("inf"))),
        "structure_sigma": 1.5,
        "min_neighbor_support": 2,
        "cosmetic_metrics": {
            "median": float(stats.get("median", 0.0)),
            "sigma": float(stats.get("sigma", 0.0)),
            "mad": float(stats.get("mad", 0.0)),
            "hot_pixels": None,
            "cold_pixels": None,
            "candidate_hot_pixels": None,
            "candidate_cold_pixels": None,
            "protected_hot_pixels": None,
            "protected_cold_pixels": None,
            "structure_sigma": 1.5,
            "min_neighbor_support": 2,
        },
    }
    if batch_summary:
        info.update(
            {
                "threshold_stats_batch_native_method": batch_summary.get("native_method"),
                "threshold_stats_batch_frame_count": batch_summary.get("frame_count"),
                "threshold_stats_batch_total_s": batch_summary.get("total_s"),
                "threshold_stats_batch_device_alloc_s": batch_summary.get("device_alloc_s"),
                "threshold_stats_batch_histogram_download_bytes": batch_summary.get(
                    "histogram_download_bytes"
                ),
                "threshold_stats_batch_minmax_partial_download_bytes": batch_summary.get(
                    "minmax_partial_download_bytes"
                ),
                "threshold_stats_batch_reuses_device_work_buffers": batch_summary.get(
                    "batch_reuses_device_work_buffers"
                ),
            }
        )
    return info


def inline_cosmetic_thresholds_from_resident_stack(
    stack: Any,
    *,
    frame_index: int,
    height: int,
    width: int,
    hot_sigma: float = 8.0,
    cold_sigma: float = 8.0,
    sample_limit: int = 65536,
    histogram_bins: int = 4096,
) -> dict[str, Any]:
    """Compute cosmetic thresholds from an already resident calibrated frame."""

    shape = (int(height), int(width))
    if hasattr(stack, "frame_histogram_robust_stats"):
        stats = dict(
            stack.frame_histogram_robust_stats(
                int(frame_index),
                int(histogram_bins),
                float(hot_sigma),
                float(cold_sigma),
            )
        )
    elif hasattr(stack, "frame_sampled_robust_stats"):
        stats = dict(
            stack.frame_sampled_robust_stats(
                int(frame_index),
                int(sample_limit),
                float(hot_sigma),
                float(cold_sigma),
            )
        )
    else:
        return {
            "supported": False,
            "reason": "resident_cuda_robust_threshold_stats_unavailable",
            "shape": list(shape),
            "invalid_samples": 0,
            "flag_counts": {},
            "source_model": "inline_structure_cosmetic_cuda_thresholds",
            "threshold_source": "unavailable",
        }

    fallback_threshold_source = (
        "cuda_resident_histogram_median_mad_scalar"
        if hasattr(stack, "frame_histogram_robust_stats")
        else "cuda_resident_sampled_median_mad_scalar"
    )
    return _inline_cosmetic_threshold_info_from_stats(
        stats,
        shape=shape,
        hot_sigma=hot_sigma,
        cold_sigma=cold_sigma,
        fallback_threshold_source=fallback_threshold_source,
        fallback_native_method="ResidentCalibratedStack.frame_histogram_robust_stats",
        fallback_execution="cuda_histogram_quantile_then_host_bin_scan_scalar",
    )


def inline_cosmetic_thresholds_batch_from_resident_stack(
    stack: Any,
    *,
    frame_indices: list[int],
    height: int,
    width: int,
    hot_sigma: float = 8.0,
    cold_sigma: float = 8.0,
    sample_limit: int = 65536,
    histogram_bins: int = 4096,
) -> dict[int, dict[str, Any]]:
    """Compute cosmetic thresholds for a batch of resident calibrated frames."""

    indices = [int(index) for index in frame_indices]
    if not indices:
        return {}
    shape = (int(height), int(width))
    if hasattr(stack, "frames_histogram_robust_stats"):
        batch_stats = dict(
            stack.frames_histogram_robust_stats(
                indices,
                int(histogram_bins),
                float(hot_sigma),
                float(cold_sigma),
            )
        )
        batch_summary = {key: value for key, value in batch_stats.items() if key != "frames"}
        threshold_by_index: dict[int, dict[str, Any]] = {}
        for frame_stats in list(batch_stats.get("frames") or []):
            stats = dict(frame_stats)
            frame_index = int(stats.get("frame_index"))
            threshold_by_index[frame_index] = _inline_cosmetic_threshold_info_from_stats(
                stats,
                shape=shape,
                hot_sigma=hot_sigma,
                cold_sigma=cold_sigma,
                fallback_threshold_source="cuda_resident_histogram_median_mad_scalar",
                fallback_native_method="ResidentCalibratedStack.frames_histogram_robust_stats",
                fallback_execution="cuda_histogram_quantile_batch_reused_buffers_then_host_bin_scan_scalar",
                batch_summary=batch_summary,
            )
        return threshold_by_index
    return {
        index: inline_cosmetic_thresholds_from_resident_stack(
            stack,
            frame_index=index,
            height=height,
            width=width,
            hot_sigma=hot_sigma,
            cold_sigma=cold_sigma,
            sample_limit=sample_limit,
            histogram_bins=histogram_bins,
        )
        for index in indices
    }


def source_invalid_mask_from_dq_mask(
    dq: DQMask | np.ndarray,
    *,
    height: int,
    width: int,
) -> tuple[np.ndarray | None, dict[str, Any]]:
    shape = (int(height), int(width))
    data = dq.data if isinstance(dq, DQMask) else np.asarray(dq)
    if data.shape != shape:
        return None, {
            "supported": False,
            "reason": "source_dq_shape_not_image",
            "shape": list(data.shape),
            "expected_shape": list(shape),
            "invalid_samples": 0,
            "flag_counts": {},
            "source_model": "dq_bitmask",
        }
    data_u32 = np.asarray(data, dtype=np.uint32)
    invalid = data_u32 != 0
    invalid_count = int(np.count_nonzero(invalid))
    return invalid.astype(np.uint8, copy=False), {
        "supported": True,
        "reason": "",
        "shape": list(data_u32.shape),
        "dtype": str(data_u32.dtype),
        "invalid_samples": invalid_count,
        "flagged_samples": invalid_count,
        "nonfinite_samples": 0,
        "flag_counts": _dq_flag_counts(data_u32),
        "source_model": "dq_bitmask",
    }


def _dq_bits_from_sidecar_data(data: np.ndarray) -> np.ndarray:
    array = np.asarray(data)
    finite = np.isfinite(array)
    bits = np.zeros(array.shape, dtype=np.uint32)
    if np.any(finite):
        bits[finite] = np.rint(array[finite]).astype(np.uint32, copy=False)
    if np.any(~finite):
        bits[~finite] |= np.uint32(int(DQFlag.NO_DATA))
    return bits


def source_invalid_mask_from_sidecar_path(
    path: str | Path,
    *,
    height: int,
    width: int,
) -> tuple[np.ndarray | None, dict[str, Any]]:
    sidecar_path = Path(path)
    if not sidecar_path.exists():
        raise FileNotFoundError(f"source DQ sidecar does not exist: {sidecar_path}")
    data = read_fits_data(sidecar_path, dtype=np.float32)
    bits = _dq_bits_from_sidecar_data(data)
    invalid_mask, info = source_invalid_mask_from_dq_mask(bits, height=height, width=width)
    info.update(
        {
            "source_model": "dq_sidecar_fits",
            "sidecar_path": str(sidecar_path),
            "sidecar_format": sidecar_path.suffix.lower().lstrip(".") or "unknown",
        }
    )
    return invalid_mask, info


def combine_source_invalid_masks(
    components: list[tuple[np.ndarray | None, dict[str, Any]]],
    *,
    height: int,
    width: int,
) -> tuple[np.ndarray | None, dict[str, Any]]:
    shape = (int(height), int(width))
    supported = True
    reasons: list[str] = []
    masks: list[np.ndarray] = []
    flag_counts = _empty_flag_counts()
    flagged_samples = 0
    nonfinite_samples = 0
    source_models: list[str] = []
    sidecar_paths: list[str] = []
    sidecar_sources: list[str] = []
    sidecar_plan_keys: list[str] = []
    sidecar_artifact_paths: list[str] = []
    sidecar_artifact_frame_ids: list[str] = []
    component_summaries: list[dict[str, Any]] = []
    for mask, info in components:
        info = dict(info)
        source_model = str(info.get("source_model") or "unknown")
        source_models.append(source_model)
        if info.get("sidecar_path"):
            sidecar_paths.append(str(info["sidecar_path"]))
        if info.get("sidecar_source"):
            sidecar_sources.append(str(info["sidecar_source"]))
        if info.get("sidecar_plan_key"):
            sidecar_plan_keys.append(str(info["sidecar_plan_key"]))
        if info.get("sidecar_artifact_path"):
            sidecar_artifact_paths.append(str(info["sidecar_artifact_path"]))
        if info.get("sidecar_artifact_frame_id"):
            sidecar_artifact_frame_ids.append(str(info["sidecar_artifact_frame_id"]))
        component_summaries.append(
            {
                "source_model": source_model,
                "supported": bool(info.get("supported")),
                "reason": str(info.get("reason") or ""),
                "invalid_samples": int(info.get("invalid_samples") or 0),
                "flagged_samples": int(info.get("flagged_samples") or 0),
                "nonfinite_samples": int(info.get("nonfinite_samples") or 0),
                "sidecar_path": info.get("sidecar_path"),
                "sidecar_source": info.get("sidecar_source"),
                "sidecar_plan_key": info.get("sidecar_plan_key"),
                "sidecar_artifact_path": info.get("sidecar_artifact_path"),
                "sidecar_artifact_frame_id": info.get("sidecar_artifact_frame_id"),
                "inline_source_dq": info.get("inline_source_dq"),
                "inline_source_dq_detector": info.get("inline_source_dq_detector"),
                "inline_source_dq_applies_replacement": info.get("inline_source_dq_applies_replacement"),
                "hot_sigma": info.get("hot_sigma"),
                "cold_sigma": info.get("cold_sigma"),
                "low_threshold": info.get("low_threshold"),
                "high_threshold": info.get("high_threshold"),
                "threshold_source": info.get("threshold_source"),
                "threshold_stats": info.get("threshold_stats"),
                "threshold_stats_native_method": info.get("threshold_stats_native_method"),
                "threshold_stats_domain": info.get("threshold_stats_domain"),
                "threshold_stats_execution": info.get("threshold_stats_execution"),
                "threshold_stats_materializes_host_frame": info.get(
                    "threshold_stats_materializes_host_frame"
                ),
                "threshold_stats_sample_count": info.get("threshold_stats_sample_count"),
                "threshold_stats_sample_download_bytes": info.get(
                    "threshold_stats_sample_download_bytes"
                ),
                "threshold_stats_bin_count": info.get("threshold_stats_bin_count"),
                "threshold_stats_histogram_download_bytes": info.get(
                    "threshold_stats_histogram_download_bytes"
                ),
                "threshold_stats_histogram_approximation": info.get(
                    "threshold_stats_histogram_approximation"
                ),
                "threshold_stats_batch_native_method": info.get(
                    "threshold_stats_batch_native_method"
                ),
                "threshold_stats_batch_frame_count": info.get("threshold_stats_batch_frame_count"),
                "threshold_stats_batch_total_s": info.get("threshold_stats_batch_total_s"),
                "threshold_stats_batch_device_alloc_s": info.get(
                    "threshold_stats_batch_device_alloc_s"
                ),
                "threshold_stats_batch_histogram_download_bytes": info.get(
                    "threshold_stats_batch_histogram_download_bytes"
                ),
                "threshold_stats_batch_minmax_partial_download_bytes": info.get(
                    "threshold_stats_batch_minmax_partial_download_bytes"
                ),
                "threshold_stats_batch_reuses_device_work_buffers": info.get(
                    "threshold_stats_batch_reuses_device_work_buffers"
                ),
                "detector_execution": info.get("detector_execution"),
                "cosmetic_metrics": info.get("cosmetic_metrics"),
            }
        )
        if not bool(info.get("supported")):
            reason = str(info.get("reason") or f"unsupported:{source_model}")
            if reason:
                reasons.append(reason)
            if int(info.get("invalid_samples") or 0) > 0:
                supported = False
            continue
        flagged_samples += int(info.get("flagged_samples") or 0)
        nonfinite_samples += int(info.get("nonfinite_samples") or 0)
        for flag, count in dict(info.get("flag_counts") or {}).items():
            flag_counts[str(flag)] = int(flag_counts.get(str(flag), 0)) + int(count or 0)
        if mask is not None:
            array = np.asarray(mask, dtype=np.uint8)
            if array.shape != shape:
                supported = False
                reasons.append("source_invalid_mask_shape_not_image")
            elif np.any(array != 0):
                masks.append(array)

    combined: np.ndarray | None = None
    invalid_count = 0
    if masks:
        combined_bool = np.zeros(shape, dtype=bool)
        for mask in masks:
            combined_bool |= mask != 0
        invalid_count = int(np.count_nonzero(combined_bool))
        combined = combined_bool.astype(np.uint8, copy=False)

    inline_detectors = sorted(
        {
            str(item.get("inline_source_dq_detector"))
            for item in component_summaries
            if item.get("inline_source_dq_detector")
        }
    )
    inline_replacement_modes = {
        bool(item.get("inline_source_dq_applies_replacement"))
        for item in component_summaries
        if item.get("inline_source_dq_applies_replacement") is not None
    }

    return combined, {
        "supported": supported,
        "reason": ";".join(reasons),
        "shape": list(shape),
        "invalid_samples": invalid_count,
        "flagged_samples": int(flagged_samples),
        "nonfinite_samples": int(nonfinite_samples),
        "flag_counts": {key: value for key, value in sorted(flag_counts.items()) if value},
        "source_model": "+".join(source_models) if source_models else "none",
        "component_summaries": component_summaries,
        "sidecar_paths": sidecar_paths,
        "sidecar_sources": sidecar_sources,
        "sidecar_plan_keys": sidecar_plan_keys,
        "sidecar_artifact_paths": sidecar_artifact_paths,
        "sidecar_artifact_frame_ids": sidecar_artifact_frame_ids,
        "inline_source_dq": any(
            bool(item.get("inline_source_dq")) for item in component_summaries
        ),
        "inline_source_dq_detector": inline_detectors[0]
        if len(inline_detectors) == 1
        else "+".join(inline_detectors)
        if inline_detectors
        else None,
        "inline_source_dq_applies_replacement": any(inline_replacement_modes)
        if inline_replacement_modes
        else None,
    }


def apply_resident_source_invalid_mask(
    stack: Any,
    *,
    frame_index: int,
    frame_id: str,
    invalid_mask: np.ndarray | None,
    mask_info: dict[str, Any],
    source: str,
    require_native: bool = True,
) -> dict[str, Any]:
    invalid_count = int(mask_info.get("invalid_samples") or 0)
    row: dict[str, Any] = {
        "schema_version": 1,
        "frame_id": str(frame_id),
        "frame_index": int(frame_index),
        "source": str(source),
        "application_order": "calibration_pre_registration",
        "registration_catalog_visibility": "pre_registration_catalog_visible",
        "registration_catalog_visible": True,
        "registration_catalog_visibility_required": True,
        "supported": bool(mask_info.get("supported")),
        "reason": str(mask_info.get("reason") or ""),
        "invalid_samples": invalid_count,
        "flagged_samples": int(mask_info.get("flagged_samples") or 0),
        "nonfinite_samples": int(mask_info.get("nonfinite_samples") or 0),
        "flag_counts": dict(mask_info.get("flag_counts") or {}),
        "source_model": str(mask_info.get("source_model") or source),
        "applied": False,
        "native_method": None,
    }
    for key in (
        "component_summaries",
        "sidecar_paths",
        "sidecar_sources",
        "sidecar_plan_keys",
        "sidecar_artifact_paths",
        "sidecar_artifact_frame_ids",
        "sidecar_path",
        "sidecar_format",
        "inline_source_dq",
        "inline_source_dq_detector",
        "inline_source_dq_applies_replacement",
        "threshold_source",
        "threshold_stats",
        "threshold_stats_native_method",
        "threshold_stats_domain",
        "threshold_stats_execution",
        "threshold_stats_materializes_host_frame",
        "threshold_stats_sample_count",
        "threshold_stats_sample_download_bytes",
        "threshold_stats_bin_count",
        "threshold_stats_histogram_download_bytes",
        "threshold_stats_histogram_approximation",
        "threshold_stats_batch_native_method",
        "threshold_stats_batch_frame_count",
        "threshold_stats_batch_total_s",
        "threshold_stats_batch_device_alloc_s",
        "threshold_stats_batch_histogram_download_bytes",
        "threshold_stats_batch_minmax_partial_download_bytes",
        "threshold_stats_batch_reuses_device_work_buffers",
        "detector_execution",
        "low_threshold",
        "high_threshold",
    ):
        if key in mask_info:
            row[key] = mask_info[key]
    if not row["supported"]:
        row["status"] = "unsupported_no_invalid_samples" if invalid_count == 0 else "unsupported"
        if invalid_count > 0 and require_native:
            raise RuntimeError(f"resident source-DQ mask is unsupported for {frame_id}: {row['reason']}")
        return row
    if invalid_count == 0:
        row["status"] = "no_invalid_samples"
        return row
    if invalid_mask is None:
        row["status"] = "missing_invalid_mask"
        if require_native:
            raise RuntimeError(f"resident source-DQ invalid mask is missing for {frame_id}")
        return row
    if not hasattr(stack, "apply_invalid_mask_frame"):
        row["status"] = "native_method_unavailable"
        if require_native:
            raise RuntimeError(
                "resident CUDA backend must expose apply_invalid_mask_frame "
                f"to consume source-DQ invalid samples for {frame_id}"
            )
        return row

    native = dict(stack.apply_invalid_mask_frame(int(frame_index), invalid_mask))
    row.update(
        {
            "status": "applied",
            "applied": True,
            "native_method": str(native.get("native_method") or "ResidentCalibratedStack.apply_invalid_mask_frame"),
            "native": native,
        }
    )
    return row


def apply_resident_inline_cosmetic_thresholds(
    stack: Any,
    *,
    frame_index: int,
    frame_id: str,
    threshold_info: dict[str, Any],
    source: str,
    require_native: bool = True,
    native_result: dict[str, Any] | None = None,
    native_count_result: dict[str, Any] | None = None,
    max_invalid_fraction: float | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "schema_version": 1,
        "frame_id": str(frame_id),
        "frame_index": int(frame_index),
        "source": str(source),
        "application_order": "calibration_pre_registration",
        "registration_catalog_visibility": "pre_registration_catalog_visible",
        "registration_catalog_visible": True,
        "registration_catalog_visibility_required": False,
        "supported": bool(threshold_info.get("supported")),
        "reason": str(threshold_info.get("reason") or ""),
        "invalid_samples": 0,
        "flagged_samples": 0,
        "nonfinite_samples": 0,
        "flag_counts": {},
        "source_model": str(threshold_info.get("source_model") or "inline_structure_cosmetic_cuda_thresholds"),
        "inline_source_dq": bool(threshold_info.get("inline_source_dq")),
        "inline_source_dq_detector": str(
            threshold_info.get("inline_source_dq_detector")
            or "ResidentCalibratedStack.apply_isolated_cosmetic_threshold_mask_frame"
        ),
        "inline_source_dq_applies_replacement": bool(
            threshold_info.get("inline_source_dq_applies_replacement")
        ),
        "threshold_source": str(threshold_info.get("threshold_source") or "cpu_median_mad_scalar"),
        "threshold_stats": dict(threshold_info.get("threshold_stats") or {}),
        "threshold_stats_native_method": threshold_info.get("threshold_stats_native_method"),
        "threshold_stats_domain": threshold_info.get("threshold_stats_domain"),
        "threshold_stats_execution": threshold_info.get("threshold_stats_execution"),
        "threshold_stats_materializes_host_frame": threshold_info.get("threshold_stats_materializes_host_frame"),
        "threshold_stats_sample_count": threshold_info.get("threshold_stats_sample_count"),
        "threshold_stats_sample_download_bytes": threshold_info.get("threshold_stats_sample_download_bytes"),
        "threshold_stats_bin_count": threshold_info.get("threshold_stats_bin_count"),
        "threshold_stats_histogram_download_bytes": threshold_info.get(
            "threshold_stats_histogram_download_bytes"
        ),
        "threshold_stats_histogram_approximation": threshold_info.get(
            "threshold_stats_histogram_approximation"
        ),
        "threshold_stats_batch_native_method": threshold_info.get(
            "threshold_stats_batch_native_method"
        ),
        "threshold_stats_batch_frame_count": threshold_info.get("threshold_stats_batch_frame_count"),
        "threshold_stats_batch_total_s": threshold_info.get("threshold_stats_batch_total_s"),
        "threshold_stats_batch_device_alloc_s": threshold_info.get(
            "threshold_stats_batch_device_alloc_s"
        ),
        "threshold_stats_batch_histogram_download_bytes": threshold_info.get(
            "threshold_stats_batch_histogram_download_bytes"
        ),
        "threshold_stats_batch_minmax_partial_download_bytes": threshold_info.get(
            "threshold_stats_batch_minmax_partial_download_bytes"
        ),
        "threshold_stats_batch_reuses_device_work_buffers": threshold_info.get(
            "threshold_stats_batch_reuses_device_work_buffers"
        ),
        "detector_execution": str(threshold_info.get("detector_execution") or "cuda_isolated_threshold_apply"),
        "hot_sigma": float(threshold_info.get("hot_sigma") or 0.0),
        "cold_sigma": float(threshold_info.get("cold_sigma") or 0.0),
        "low_threshold": float(threshold_info.get("low_threshold", float("-inf"))),
        "high_threshold": float(threshold_info.get("high_threshold", float("inf"))),
        "cosmetic_metrics": dict(threshold_info.get("cosmetic_metrics") or {}),
        "structure_sigma": float(threshold_info.get("structure_sigma", 1.5)),
        "min_neighbor_support": int(threshold_info.get("min_neighbor_support", 2)),
        "applied": False,
        "native_method": None,
    }
    if not row["supported"]:
        row["status"] = "unsupported_no_invalid_samples"
        return row

    metrics_for_params = dict(row["cosmetic_metrics"])
    stats_for_params = dict(row["threshold_stats"])
    threshold_median = float(metrics_for_params.get("median", stats_for_params.get("median", 0.0)) or 0.0)
    threshold_sigma = float(metrics_for_params.get("sigma", stats_for_params.get("sigma", 0.0)) or 0.0)
    use_isolated_detector = "isolated" in str(row["inline_source_dq_detector"])
    guard_enabled = max_invalid_fraction is not None and float(max_invalid_fraction) > 0.0
    if guard_enabled and native_count_result is None:
        if use_isolated_detector and hasattr(stack, "count_isolated_cosmetic_threshold_mask_frame"):
            native_count_result = dict(
                stack.count_isolated_cosmetic_threshold_mask_frame(
                    int(frame_index),
                    float(row["low_threshold"]),
                    float(row["high_threshold"]),
                    threshold_median,
                    threshold_sigma,
                    float(row["structure_sigma"]),
                    int(row["min_neighbor_support"]),
                )
            )
        elif hasattr(stack, "count_cosmetic_threshold_mask_frame"):
            native_count_result = dict(
                stack.count_cosmetic_threshold_mask_frame(
                    int(frame_index),
                    float(row["low_threshold"]),
                    float(row["high_threshold"]),
                )
            )
    if native_count_result is not None:
        count_native = dict(native_count_result)
        count_hot = int(count_native.get("hot_samples") or 0)
        count_cold = int(count_native.get("cold_samples") or 0)
        count_nonfinite = int(count_native.get("nonfinite_samples") or 0)
        count_cosmetic = int(count_native.get("cosmetic_corrected_samples") or (count_hot + count_cold))
        count_invalid = int(count_native.get("invalid_samples") or (count_cosmetic + count_nonfinite))
        count_total = max(1, int(count_native.get("total_pixels") or count_native.get("total_pixels_per_frame") or 1))
        count_fraction = float(count_invalid) / float(count_total)
        row.update(
            {
                "threshold_guard": {
                    "enabled": bool(guard_enabled),
                    "max_invalid_fraction": None
                    if max_invalid_fraction is None
                    else float(max_invalid_fraction),
                    "would_invalid_samples": int(count_invalid),
                    "would_hot_samples": int(count_hot),
                    "would_cold_samples": int(count_cold),
                    "would_nonfinite_samples": int(count_nonfinite),
                    "would_invalid_fraction": float(count_fraction),
                    "native_method": str(
                        count_native.get("native_method")
                        or "ResidentCalibratedStack.count_cosmetic_threshold_mask_frame"
                    ),
                    "detector_execution": str(
                        count_native.get("detector_execution") or "cuda_threshold_count"
                    ),
                },
                "native_count": count_native,
                "would_invalid_samples": int(count_invalid),
                "would_hot_samples": int(count_hot),
                "would_cold_samples": int(count_cold),
                "would_nonfinite_samples": int(count_nonfinite),
                "would_invalid_fraction": float(count_fraction),
            }
        )
        if guard_enabled and count_fraction > float(max_invalid_fraction):
            metrics = dict(row["cosmetic_metrics"])
            metrics["would_hot_pixels"] = count_hot
            metrics["would_cold_pixels"] = count_cold
            row.update(
                {
                    "status": "skipped_high_invalid_fraction",
                    "reason": (
                        "resident inline cosmetic threshold would invalidate "
                        f"{count_fraction:.6g} of frame samples, above "
                        f"{float(max_invalid_fraction):.6g}"
                    ),
                    "applied": False,
                    "native_method": str(
                        count_native.get("native_method")
                        or "ResidentCalibratedStack.count_cosmetic_threshold_mask_frame"
                    ),
                    "native": count_native,
                    "detector_execution": str(
                        count_native.get("detector_execution") or "cuda_threshold_count"
                    ),
                    "invalid_samples": 0,
                    "flagged_samples": 0,
                    "nonfinite_samples": 0,
                    "flag_counts": {},
                    "cosmetic_metrics": metrics,
                    "component_summaries": [
                        {
                            "source_model": row["source_model"],
                            "supported": True,
                            "reason": row["reason"],
                            "invalid_samples": 0,
                            "flagged_samples": 0,
                            "nonfinite_samples": 0,
                            "would_invalid_samples": int(count_invalid),
                            "would_invalid_fraction": float(count_fraction),
                            "inline_source_dq": True,
                            "inline_source_dq_detector": row["inline_source_dq_detector"],
                            "inline_source_dq_applies_replacement": False,
                            "hot_sigma": row["hot_sigma"],
                            "cold_sigma": row["cold_sigma"],
                            "low_threshold": row["low_threshold"],
                            "high_threshold": row["high_threshold"],
                            "threshold_source": row["threshold_source"],
                            "threshold_stats": row["threshold_stats"],
                            "structure_sigma": row["structure_sigma"],
                            "min_neighbor_support": row["min_neighbor_support"],
                            "detector_execution": row["detector_execution"],
                            "cosmetic_metrics": metrics,
                        }
                    ],
                }
            )
            return row
    required_apply_method = (
        "apply_isolated_cosmetic_threshold_mask_frame"
        if use_isolated_detector
        else "apply_cosmetic_threshold_mask_frame"
    )
    if native_result is None and not hasattr(stack, required_apply_method):
        row["status"] = "native_method_unavailable"
        if require_native:
            raise RuntimeError(
                f"resident CUDA backend must expose {required_apply_method} "
                f"to consume inline cosmetic source-DQ samples for {frame_id}"
            )
        return row

    if native_result is not None:
        native = dict(native_result)
    elif use_isolated_detector:
        native = dict(
            stack.apply_isolated_cosmetic_threshold_mask_frame(
                int(frame_index),
                float(row["low_threshold"]),
                float(row["high_threshold"]),
                threshold_median,
                threshold_sigma,
                float(row["structure_sigma"]),
                int(row["min_neighbor_support"]),
            )
        )
    else:
        native = dict(
            stack.apply_cosmetic_threshold_mask_frame(
                int(frame_index),
                float(row["low_threshold"]),
                float(row["high_threshold"]),
            )
        )
    hot = int(native.get("hot_samples") or 0)
    cold = int(native.get("cold_samples") or 0)
    nonfinite = int(native.get("nonfinite_samples") or 0)
    cosmetic = int(native.get("cosmetic_corrected_samples") or (hot + cold))
    invalid = int(native.get("invalid_samples") or (cosmetic + nonfinite))
    flag_counts = _empty_flag_counts()
    if hot:
        flag_counts["hot_pixel"] = hot
    if cold:
        flag_counts["cold_pixel"] = cold
    if nonfinite:
        flag_counts["no_data"] = nonfinite
    if cosmetic:
        flag_counts["cosmetic_corrected"] = cosmetic
    flag_counts = {key: value for key, value in flag_counts.items() if value}

    metrics = dict(row["cosmetic_metrics"])
    metrics["hot_pixels"] = hot
    metrics["cold_pixels"] = cold
    metrics["candidate_hot_pixels"] = int(native.get("candidate_hot_samples") or hot)
    metrics["candidate_cold_pixels"] = int(native.get("candidate_cold_samples") or cold)
    metrics["protected_hot_pixels"] = int(native.get("protected_hot_samples") or 0)
    metrics["protected_cold_pixels"] = int(native.get("protected_cold_samples") or 0)
    row.update(
        {
            "status": "applied" if invalid > 0 else "no_invalid_samples",
            "applied": invalid > 0,
            "native_method": str(
                native.get("native_method")
                or "ResidentCalibratedStack.apply_cosmetic_threshold_mask_frame"
            ),
            "native": native,
            "detector_execution": str(native.get("detector_execution") or row["detector_execution"]),
            "threshold_guard": row.get("threshold_guard"),
            "native_count": row.get("native_count"),
            "would_invalid_samples": row.get("would_invalid_samples"),
            "would_invalid_fraction": row.get("would_invalid_fraction"),
            "invalid_samples": invalid,
            "flagged_samples": invalid,
            "nonfinite_samples": nonfinite,
            "flag_counts": flag_counts,
            "cosmetic_metrics": metrics,
            "component_summaries": [
                {
                    "source_model": row["source_model"],
                    "supported": True,
                    "reason": "",
                    "invalid_samples": invalid,
                    "flagged_samples": invalid,
                    "nonfinite_samples": nonfinite,
                    "inline_source_dq": True,
                    "inline_source_dq_detector": row["inline_source_dq_detector"],
                    "inline_source_dq_applies_replacement": False,
                    "hot_sigma": row["hot_sigma"],
                    "cold_sigma": row["cold_sigma"],
                    "low_threshold": row["low_threshold"],
                    "high_threshold": row["high_threshold"],
                    "threshold_source": row["threshold_source"],
                    "threshold_stats": row["threshold_stats"],
                    "threshold_stats_native_method": row["threshold_stats_native_method"],
                    "threshold_stats_domain": row["threshold_stats_domain"],
                    "threshold_stats_execution": row["threshold_stats_execution"],
                    "threshold_stats_materializes_host_frame": row[
                        "threshold_stats_materializes_host_frame"
                    ],
                    "threshold_stats_sample_count": row["threshold_stats_sample_count"],
                    "threshold_stats_sample_download_bytes": row[
                        "threshold_stats_sample_download_bytes"
                    ],
                    "threshold_stats_bin_count": row["threshold_stats_bin_count"],
                    "threshold_stats_histogram_download_bytes": row[
                        "threshold_stats_histogram_download_bytes"
                    ],
                    "threshold_stats_histogram_approximation": row[
                        "threshold_stats_histogram_approximation"
                    ],
                    "threshold_stats_batch_native_method": row[
                        "threshold_stats_batch_native_method"
                    ],
                    "threshold_stats_batch_frame_count": row["threshold_stats_batch_frame_count"],
                    "threshold_stats_batch_total_s": row["threshold_stats_batch_total_s"],
                    "threshold_stats_batch_device_alloc_s": row[
                        "threshold_stats_batch_device_alloc_s"
                    ],
                    "threshold_stats_batch_histogram_download_bytes": row[
                        "threshold_stats_batch_histogram_download_bytes"
                    ],
                    "threshold_stats_batch_minmax_partial_download_bytes": row[
                        "threshold_stats_batch_minmax_partial_download_bytes"
                    ],
                    "threshold_stats_batch_reuses_device_work_buffers": row[
                        "threshold_stats_batch_reuses_device_work_buffers"
                    ],
                    "structure_sigma": row["structure_sigma"],
                    "min_neighbor_support": row["min_neighbor_support"],
                    "detector_execution": row["detector_execution"],
                    "cosmetic_metrics": metrics,
                }
            ],
        }
    )
    return row


def build_skipped_resident_inline_cosmetic_threshold_row(
    *,
    frame_index: int,
    frame_id: str,
    threshold_info: dict[str, Any],
    source: str,
    admission_policy: str,
    admission_reason: str,
) -> dict[str, Any]:
    info = dict(threshold_info)
    metrics = dict(info.get("cosmetic_metrics") or {})
    row: dict[str, Any] = {
        "schema_version": 1,
        "frame_id": str(frame_id),
        "frame_index": int(frame_index),
        "source": str(source),
        "application_order": "calibration_pre_registration",
        "registration_catalog_visibility": "pre_registration_catalog_visible",
        "registration_catalog_visible": True,
        "registration_catalog_visibility_required": False,
        "supported": bool(info.get("supported")),
        "reason": str(admission_reason),
        "invalid_samples": 0,
        "flagged_samples": 0,
        "nonfinite_samples": 0,
        "flag_counts": {},
        "source_model": str(info.get("source_model") or "inline_structure_cosmetic_cuda_thresholds"),
        "inline_source_dq": bool(info.get("inline_source_dq")),
        "inline_source_dq_detector": str(
            info.get("inline_source_dq_detector")
            or "ResidentCalibratedStack.apply_isolated_cosmetic_threshold_mask_frame"
        ),
        "inline_source_dq_applies_replacement": bool(
            info.get("inline_source_dq_applies_replacement")
        ),
        "threshold_source": str(info.get("threshold_source") or "cpu_median_mad_scalar"),
        "threshold_stats": dict(info.get("threshold_stats") or {}),
        "threshold_stats_native_method": info.get("threshold_stats_native_method"),
        "threshold_stats_domain": info.get("threshold_stats_domain"),
        "threshold_stats_execution": info.get("threshold_stats_execution"),
        "threshold_stats_materializes_host_frame": info.get("threshold_stats_materializes_host_frame"),
        "threshold_stats_sample_count": info.get("threshold_stats_sample_count"),
        "threshold_stats_sample_download_bytes": info.get("threshold_stats_sample_download_bytes"),
        "threshold_stats_bin_count": info.get("threshold_stats_bin_count"),
        "threshold_stats_histogram_download_bytes": info.get(
            "threshold_stats_histogram_download_bytes"
        ),
        "threshold_stats_histogram_approximation": info.get(
            "threshold_stats_histogram_approximation"
        ),
        "threshold_stats_batch_native_method": info.get("threshold_stats_batch_native_method"),
        "threshold_stats_batch_frame_count": info.get("threshold_stats_batch_frame_count"),
        "threshold_stats_batch_total_s": info.get("threshold_stats_batch_total_s"),
        "threshold_stats_batch_device_alloc_s": info.get("threshold_stats_batch_device_alloc_s"),
        "threshold_stats_batch_histogram_download_bytes": info.get(
            "threshold_stats_batch_histogram_download_bytes"
        ),
        "threshold_stats_batch_minmax_partial_download_bytes": info.get(
            "threshold_stats_batch_minmax_partial_download_bytes"
        ),
        "threshold_stats_batch_reuses_device_work_buffers": info.get(
            "threshold_stats_batch_reuses_device_work_buffers"
        ),
        "detector_execution": str(info.get("detector_execution") or "cuda_isolated_threshold_apply"),
        "hot_sigma": float(info.get("hot_sigma") or 0.0),
        "cold_sigma": float(info.get("cold_sigma") or 0.0),
        "low_threshold": float(info.get("low_threshold", float("-inf"))),
        "high_threshold": float(info.get("high_threshold", float("inf"))),
        "cosmetic_metrics": metrics,
        "structure_sigma": float(info.get("structure_sigma", 1.5)),
        "min_neighbor_support": int(info.get("min_neighbor_support", 2)),
        "applied": False,
        "native_method": None,
        "status": "skipped_admission_policy",
        "admission_policy": str(admission_policy),
        "admission_reason": str(admission_reason),
        "component_summaries": [
            {
                "source_model": str(info.get("source_model") or "inline_structure_cosmetic_cuda_thresholds"),
                "supported": bool(info.get("supported")),
                "reason": str(admission_reason),
                "invalid_samples": 0,
                "flagged_samples": 0,
                "nonfinite_samples": 0,
                "inline_source_dq": bool(info.get("inline_source_dq")),
                "inline_source_dq_detector": str(
                    info.get("inline_source_dq_detector")
                    or "ResidentCalibratedStack.apply_isolated_cosmetic_threshold_mask_frame"
                ),
                "inline_source_dq_applies_replacement": False,
                "hot_sigma": float(info.get("hot_sigma") or 0.0),
                "cold_sigma": float(info.get("cold_sigma") or 0.0),
                "low_threshold": float(info.get("low_threshold", float("-inf"))),
                "high_threshold": float(info.get("high_threshold", float("inf"))),
                "threshold_source": str(info.get("threshold_source") or "cpu_median_mad_scalar"),
                "threshold_stats": dict(info.get("threshold_stats") or {}),
                "structure_sigma": float(info.get("structure_sigma", 1.5)),
                "min_neighbor_support": int(info.get("min_neighbor_support", 2)),
                "detector_execution": str(
                    info.get("detector_execution") or "cuda_isolated_threshold_apply"
                ),
                "cosmetic_metrics": metrics,
                "admission_policy": str(admission_policy),
            }
        ],
    }
    return row


def apply_resident_inline_cosmetic_thresholds_batch(
    stack: Any,
    *,
    items: list[dict[str, Any]],
    source: str,
    require_native: bool = True,
    max_invalid_fraction: float | None = None,
) -> list[dict[str, Any]]:
    if not items:
        return []
    use_isolated_detector = all(
        "isolated" in str(dict(item["threshold_info"]).get("inline_source_dq_detector") or "")
        for item in items
    )
    batch_apply_method = (
        "apply_isolated_cosmetic_threshold_mask_frames"
        if use_isolated_detector
        else "apply_cosmetic_threshold_mask_frames"
    )
    batch_count_method = (
        "count_isolated_cosmetic_threshold_mask_frames"
        if use_isolated_detector
        else "count_cosmetic_threshold_mask_frames"
    )
    if not hasattr(stack, batch_apply_method):
        return [
            apply_resident_inline_cosmetic_thresholds(
                stack,
                frame_index=int(item["frame_index"]),
                frame_id=str(item["frame_id"]),
                threshold_info=dict(item["threshold_info"]),
                source=source,
                require_native=require_native,
                max_invalid_fraction=max_invalid_fraction,
            )
            for item in items
        ]

    indices = [int(item["frame_index"]) for item in items]
    low_thresholds = [float(dict(item["threshold_info"])["low_threshold"]) for item in items]
    high_thresholds = [float(dict(item["threshold_info"])["high_threshold"]) for item in items]
    medians = [
        float(
            dict(dict(item["threshold_info"]).get("cosmetic_metrics") or {}).get(
                "median",
                dict(dict(item["threshold_info"]).get("threshold_stats") or {}).get("median", 0.0),
            )
            or 0.0
        )
        for item in items
    ]
    sigmas = [
        float(
            dict(dict(item["threshold_info"]).get("cosmetic_metrics") or {}).get(
                "sigma",
                dict(dict(item["threshold_info"]).get("threshold_stats") or {}).get("sigma", 0.0),
            )
            or 0.0
        )
        for item in items
    ]
    structure_sigma = float(dict(items[0]["threshold_info"]).get("structure_sigma", 1.5))
    min_neighbor_support = int(dict(items[0]["threshold_info"]).get("min_neighbor_support", 2))
    native_count_by_index: dict[int, dict[str, Any]] = {}
    guard_enabled = max_invalid_fraction is not None and float(max_invalid_fraction) > 0.0
    if guard_enabled and hasattr(stack, batch_count_method):
        count_fn = getattr(stack, batch_count_method)
        native_count_batch = dict(
            count_fn(
                indices,
                low_thresholds,
                high_thresholds,
                medians,
                sigmas,
                structure_sigma,
                min_neighbor_support,
            )
            if use_isolated_detector
            else count_fn(indices, low_thresholds, high_thresholds)
        )
        native_count_by_index = {
            int(frame_result.get("frame_index")): dict(frame_result)
            for frame_result in list(native_count_batch.get("frames") or [])
        }
        for frame_result in native_count_by_index.values():
            frame_result.setdefault("batch_native_method", native_count_batch.get("native_method"))
            frame_result.setdefault("batch_frame_count", native_count_batch.get("frame_count"))
            frame_result.setdefault("batch_total_s", native_count_batch.get("total_s"))

    apply_items: list[dict[str, Any]] = []
    skipped_rows_by_index: dict[int, dict[str, Any]] = {}
    for item in items:
        frame_index = int(item["frame_index"])
        count_result = native_count_by_index.get(frame_index)
        if count_result is None:
            apply_items.append(item)
            continue
        count_invalid = int(
            count_result.get("invalid_samples")
            or count_result.get("cosmetic_corrected_samples")
            or 0
        )
        count_total = max(1, int(count_result.get("total_pixels") or count_result.get("total_pixels_per_frame") or 1))
        if not guard_enabled or (float(count_invalid) / float(count_total)) <= float(max_invalid_fraction):
            apply_items.append(item)
            continue
        row = apply_resident_inline_cosmetic_thresholds(
            stack,
            frame_index=frame_index,
            frame_id=str(item["frame_id"]),
            threshold_info=dict(item["threshold_info"]),
            source=source,
            require_native=require_native,
            native_count_result=count_result,
            max_invalid_fraction=max_invalid_fraction,
        )
        if row["status"] == "skipped_high_invalid_fraction":
            skipped_rows_by_index[frame_index] = row
        else:
            apply_items.append(item)

    native_batch = (
        dict(
            getattr(stack, batch_apply_method)(
                [int(item["frame_index"]) for item in apply_items],
                [float(dict(item["threshold_info"])["low_threshold"]) for item in apply_items],
                [float(dict(item["threshold_info"])["high_threshold"]) for item in apply_items],
                [
                    float(
                        dict(dict(item["threshold_info"]).get("cosmetic_metrics") or {}).get(
                            "median",
                            dict(dict(item["threshold_info"]).get("threshold_stats") or {}).get("median", 0.0),
                        )
                        or 0.0
                    )
                    for item in apply_items
                ],
                [
                    float(
                        dict(dict(item["threshold_info"]).get("cosmetic_metrics") or {}).get(
                            "sigma",
                            dict(dict(item["threshold_info"]).get("threshold_stats") or {}).get("sigma", 0.0),
                        )
                        or 0.0
                    )
                    for item in apply_items
                ],
                structure_sigma,
                min_neighbor_support,
            )
            if use_isolated_detector
            else getattr(stack, batch_apply_method)(
                [int(item["frame_index"]) for item in apply_items],
                [float(dict(item["threshold_info"])["low_threshold"]) for item in apply_items],
                [float(dict(item["threshold_info"])["high_threshold"]) for item in apply_items],
            )
        )
        if apply_items
        else {"frames": [], "native_method": f"ResidentCalibratedStack.{batch_apply_method}"}
    )
    native_by_index = {
        int(frame_result.get("frame_index")): dict(frame_result)
        for frame_result in list(native_batch.get("frames") or [])
    }
    rows: list[dict[str, Any]] = []
    for item in items:
        frame_index = int(item["frame_index"])
        skipped_row = skipped_rows_by_index.get(frame_index)
        if skipped_row is not None:
            rows.append(skipped_row)
            continue
        native_result = native_by_index.get(frame_index)
        if native_result is None:
            if require_native:
                raise RuntimeError(
                    "resident CUDA batch cosmetic threshold application did not return "
                    f"a result for frame index {frame_index}"
                )
            rows.append(
                apply_resident_inline_cosmetic_thresholds(
                    stack,
                    frame_index=frame_index,
                    frame_id=str(item["frame_id"]),
                threshold_info=dict(item["threshold_info"]),
                source=source,
                require_native=False,
                native_count_result=native_count_by_index.get(frame_index),
                max_invalid_fraction=max_invalid_fraction,
            )
            )
            continue
        native_result.setdefault("batch_native_method", native_batch.get("native_method"))
        native_result.setdefault("batch_frame_count", native_batch.get("frame_count"))
        native_result.setdefault("batch_total_s", native_batch.get("total_s"))
        rows.append(
            apply_resident_inline_cosmetic_thresholds(
                stack,
                frame_index=frame_index,
                frame_id=str(item["frame_id"]),
                threshold_info=dict(item["threshold_info"]),
                source=source,
                require_native=require_native,
                native_result=native_result,
                native_count_result=native_count_by_index.get(frame_index),
                max_invalid_fraction=max_invalid_fraction,
            )
        )
    return rows


def _source_dq_application_order(row: dict[str, Any]) -> str:
    order = row.get("application_order")
    if order is not None and str(order):
        return str(order)
    source = str(row.get("source") or "")
    if source.startswith("resident_post_registration_pre_warp"):
        return "post_registration_pre_warp"
    if source.startswith("resident_calibrated"):
        return "calibration_pre_registration"
    return "unspecified"


def _source_dq_registration_catalog_visible(row: dict[str, Any]) -> bool:
    if row.get("registration_catalog_visible") is not None:
        return bool(row.get("registration_catalog_visible"))
    return _source_dq_application_order(row) == "calibration_pre_registration"


def _source_dq_registration_catalog_visibility_required(row: dict[str, Any]) -> bool:
    if row.get("registration_catalog_visibility_required") is not None:
        return bool(row.get("registration_catalog_visibility_required"))
    return not bool(row.get("inline_source_dq"))


def build_resident_source_dq_summary(
    rows: list[dict[str, Any]],
    *,
    frame_count: int,
    height: int,
    width: int,
    active_frame_count: int | None = None,
    active_frame_ids: Iterable[str] | None = None,
    fast_skip_frame_count: int = 0,
    fast_skip_reason: str | None = None,
) -> dict[str, Any]:
    fast_skip_frame_count = max(0, int(fast_skip_frame_count))
    active_frame_id_set = (
        None if active_frame_ids is None else {str(frame_id) for frame_id in active_frame_ids}
    )

    def row_is_active(row: dict[str, Any]) -> bool:
        if active_frame_id_set is None:
            return True
        return str(row.get("frame_id")) in active_frame_id_set

    active_rows = [row for row in rows if row_is_active(row)]
    inactive_rows = [row for row in rows if not row_is_active(row)]
    total_invalid = sum(int(row.get("invalid_samples") or 0) for row in active_rows)
    total_flagged = sum(int(row.get("flagged_samples") or 0) for row in active_rows)
    total_nonfinite = sum(int(row.get("nonfinite_samples") or 0) for row in active_rows)
    total_would_invalid = sum(int(row.get("would_invalid_samples") or 0) for row in active_rows)
    all_frame_invalid = sum(int(row.get("invalid_samples") or 0) for row in rows)
    all_frame_flagged = sum(int(row.get("flagged_samples") or 0) for row in rows)
    all_frame_nonfinite = sum(int(row.get("nonfinite_samples") or 0) for row in rows)
    all_frame_would_invalid = sum(int(row.get("would_invalid_samples") or 0) for row in rows)
    inactive_invalid = sum(int(row.get("invalid_samples") or 0) for row in inactive_rows)
    applied_invalid = sum(
        int(row.get("invalid_samples") or 0) for row in active_rows if bool(row.get("applied"))
    )
    all_frame_applied_invalid = sum(
        int(row.get("invalid_samples") or 0) for row in rows if bool(row.get("applied"))
    )
    unsupported = [row for row in rows if str(row.get("status") or "").startswith("unsupported")]
    native_missing = [row for row in rows if row.get("status") == "native_method_unavailable"]
    source_counts: dict[str, int] = {}
    status_counts: dict[str, int] = {}
    sidecar_source_counts: dict[str, int] = {}
    sidecar_paths: set[str] = set()
    sidecar_artifact_paths: set[str] = set()
    native_methods: set[str] = set()
    flag_counts = _empty_flag_counts()
    application_order_counts: dict[str, int] = {}
    registration_visibility_counts: dict[str, int] = {}
    pre_registration_visible_invalid = 0
    pre_registration_visible_rows = 0
    post_registration_deferred_invalid = 0
    post_registration_deferred_rows = 0
    missing_application_order_rows = 0
    required_invalid_not_visible = 0
    for row in rows:
        source = str(row.get("source") or "unknown")
        source_counts[source] = source_counts.get(source, 0) + 1
        status = str(row.get("status") or "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
        application_order = _source_dq_application_order(row)
        application_order_counts[application_order] = application_order_counts.get(application_order, 0) + 1
        if row.get("application_order") is None:
            missing_application_order_rows += 1
        registration_visible = _source_dq_registration_catalog_visible(row)
        visibility_key = "pre_registration_catalog_visible" if registration_visible else "not_catalog_visible"
        registration_visibility_counts[visibility_key] = registration_visibility_counts.get(visibility_key, 0) + 1
        row_invalid = int(row.get("invalid_samples") or 0)
        if registration_visible:
            pre_registration_visible_rows += 1
            pre_registration_visible_invalid += row_invalid
        else:
            post_registration_deferred_rows += 1
            post_registration_deferred_invalid += row_invalid
        if (
            row_invalid > 0
            and _source_dq_registration_catalog_visibility_required(row)
            and not registration_visible
        ):
            required_invalid_not_visible += row_invalid
        if row.get("native_method"):
            native_methods.add(str(row["native_method"]))
        for sidecar_source in list(row.get("sidecar_sources") or []):
            sidecar_source = str(sidecar_source)
            sidecar_source_counts[sidecar_source] = sidecar_source_counts.get(sidecar_source, 0) + 1
        for sidecar_path in list(row.get("sidecar_paths") or []):
            sidecar_paths.add(str(sidecar_path))
        for artifact_path in list(row.get("sidecar_artifact_paths") or []):
            sidecar_artifact_paths.add(str(artifact_path))
        if row_is_active(row):
            for flag, count in dict(row.get("flag_counts") or {}).items():
                flag_counts[str(flag)] = int(flag_counts.get(str(flag), 0)) + int(count or 0)
    if fast_skip_frame_count:
        source_counts["no_source_dq_fast_skip"] = (
            source_counts.get("no_source_dq_fast_skip", 0) + fast_skip_frame_count
        )
        status_counts["no_source_dq_fast_skip"] = (
            status_counts.get("no_source_dq_fast_skip", 0) + fast_skip_frame_count
        )

    effective_frame_count = int(frame_count if active_frame_count is None else active_frame_count)
    input_samples = int(effective_frame_count) * int(height) * int(width)
    input_valid_before_rejection = max(0, input_samples - int(total_invalid))
    native_method_list = sorted(native_methods)
    summary_native_method = (
        native_method_list[0]
        if len(native_method_list) == 1
        else "mixed_resident_source_dq_methods"
        if native_method_list
        else "ResidentCalibratedStack.apply_invalid_mask_frame"
    )
    return {
        "schema_version": 1,
        "source_model": "resident_source_dq_invalid_to_nan",
        "native_method": summary_native_method,
        "native_methods": native_method_list,
        "frame_count": int(frame_count),
        "active_frame_count": int(effective_frame_count),
        "height": int(height),
        "width": int(width),
        "input_samples": int(input_samples),
        "input_valid_samples_before_rejection": int(input_valid_before_rejection),
        "input_invalid_samples_before_rejection": int(total_invalid),
        "input_would_invalid_samples_before_guard": int(total_would_invalid),
        "input_guarded_invalid_samples_skipped": int(max(0, total_would_invalid - total_invalid)),
        "input_flagged_samples": int(total_flagged),
        "input_nonfinite_samples": int(total_nonfinite),
        "all_frame_input_invalid_samples_before_frame_mask": int(all_frame_invalid),
        "all_frame_input_would_invalid_samples_before_guard": int(all_frame_would_invalid),
        "all_frame_input_flagged_samples": int(all_frame_flagged),
        "all_frame_input_nonfinite_samples": int(all_frame_nonfinite),
        "all_frame_applied_invalid_samples": int(all_frame_applied_invalid),
        "inactive_frame_input_invalid_samples_before_frame_mask": int(inactive_invalid),
        "active_frame_ids_provided": active_frame_id_set is not None,
        "source_dq_flag_counts": {key: value for key, value in sorted(flag_counts.items()) if value},
        "applied_invalid_samples": int(applied_invalid),
        "frame_with_invalid_count": int(
            sum(1 for row in active_rows if int(row.get("invalid_samples") or 0) > 0)
        ),
        "all_frame_with_invalid_count": int(
            sum(1 for row in rows if int(row.get("invalid_samples") or 0) > 0)
        ),
        "applied_frame_count": int(sum(1 for row in active_rows if bool(row.get("applied")))),
        "all_frame_applied_frame_count": int(sum(1 for row in rows if bool(row.get("applied")))),
        "unsupported_frame_count": len(unsupported),
        "native_missing_frame_count": len(native_missing),
        "fast_skip_frame_count": fast_skip_frame_count,
        "fast_skip_reason": fast_skip_reason if fast_skip_frame_count else None,
        "source_counts": dict(sorted(source_counts.items())),
        "status_counts": dict(sorted(status_counts.items())),
        "application_order_counts": dict(sorted(application_order_counts.items())),
        "registration_catalog_visibility_counts": dict(sorted(registration_visibility_counts.items())),
        "pre_registration_catalog_visible_row_count": int(pre_registration_visible_rows),
        "pre_registration_catalog_visible_invalid_samples": int(pre_registration_visible_invalid),
        "post_registration_deferred_row_count": int(post_registration_deferred_rows),
        "post_registration_deferred_invalid_samples": int(post_registration_deferred_invalid),
        "rows_missing_application_order_count": int(missing_application_order_rows),
        "required_invalid_samples_not_visible_to_registration_catalog": int(required_invalid_not_visible),
        "sidecar_source_counts": dict(sorted(sidecar_source_counts.items())),
        "sidecar_path_count": len(sidecar_paths),
        "sidecar_artifact_path_count": len(sidecar_artifact_paths),
        "sidecar_artifact_paths": sorted(sidecar_artifact_paths),
        "passed": (
            len(unsupported) == 0
            and len(native_missing) == 0
            and applied_invalid == total_invalid
            and all_frame_applied_invalid == all_frame_invalid
        ),
        "rows": rows,
        "semantics": (
            "Resident CUDA consumes source-DQ invalid samples by setting resident "
            "frame pixels to NaN before integration. Invalid samples may come from "
            "uploaded source-DQ masks or resident CUDA threshold detection; existing "
            "resident integration kernels then skip those samples before rejection, "
            "matching the CPU StackEngine valid-sample contract. Non-inline source-DQ "
            "masks are applied before resident registration catalog detection so "
            "bad pixels cannot become registration stars; inline cosmetic CUDA masks "
            "may be explicitly deferred until after registration to avoid suppressing "
            "real stellar cores."
        ),
    }


def _execution_check(name: str, passed: bool, details: dict[str, Any]) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "details": details}


def build_resident_source_dq_execution_group(
    source_dq_summary: dict[str, Any],
    *,
    filter_name: str | None,
    frame_count: int,
    height: int,
    width: int,
    resident_calibration_batch_frames: int = 1,
) -> dict[str, Any]:
    batch_frames = max(1, int(resident_calibration_batch_frames or 1))
    per_frame_mask_bytes = int(height) * int(width)
    batch_mask_bytes = per_frame_mask_bytes * batch_frames
    all_frame_mask_bytes = per_frame_mask_bytes * int(frame_count)
    input_invalid = int(source_dq_summary.get("input_invalid_samples_before_rejection") or 0)
    applied_invalid = int(source_dq_summary.get("applied_invalid_samples") or 0)
    all_frame_input_invalid = int(
        source_dq_summary.get("all_frame_input_invalid_samples_before_frame_mask", input_invalid)
        or 0
    )
    all_frame_applied_invalid = int(
        source_dq_summary.get("all_frame_applied_invalid_samples", applied_invalid) or 0
    )
    unsupported = int(source_dq_summary.get("unsupported_frame_count") or 0)
    native_missing = int(source_dq_summary.get("native_missing_frame_count") or 0)
    missing_application_order = int(source_dq_summary.get("rows_missing_application_order_count") or 0)
    required_invalid_not_visible = int(
        source_dq_summary.get("required_invalid_samples_not_visible_to_registration_catalog") or 0
    )
    summary_passed = bool(source_dq_summary.get("passed"))
    checks = [
        _execution_check(
            "source_dq_summary_passed",
            summary_passed,
            {"passed": summary_passed},
        ),
        _execution_check(
            "invalid_samples_applied",
            applied_invalid == input_invalid,
            {"applied_invalid_samples": applied_invalid, "input_invalid_samples": input_invalid},
        ),
        _execution_check(
            "all_frame_invalid_samples_applied",
            all_frame_applied_invalid == all_frame_input_invalid,
            {
                "all_frame_applied_invalid_samples": all_frame_applied_invalid,
                "all_frame_input_invalid_samples": all_frame_input_invalid,
            },
        ),
        _execution_check(
            "no_unsupported_frames",
            unsupported == 0,
            {"unsupported_frame_count": unsupported},
        ),
        _execution_check(
            "native_method_available",
            native_missing == 0,
            {"native_missing_frame_count": native_missing},
        ),
        _execution_check(
            "application_order_declared",
            missing_application_order == 0,
            {"rows_missing_application_order_count": missing_application_order},
        ),
        _execution_check(
            "non_inline_source_dq_visible_to_registration_catalog",
            required_invalid_not_visible == 0,
            {
                "required_invalid_samples_not_visible_to_registration_catalog": (
                    required_invalid_not_visible
                ),
                "pre_registration_catalog_visible_invalid_samples": int(
                    source_dq_summary.get("pre_registration_catalog_visible_invalid_samples") or 0
                ),
                "post_registration_deferred_invalid_samples": int(
                    source_dq_summary.get("post_registration_deferred_invalid_samples") or 0
                ),
            },
        ),
        _execution_check(
            "no_calibrated_dq_disk_cache_required",
            True,
            {
                "materializes_calibrated_dq_cache": False,
                "execution_route": "resident_in_memory_mask_streaming",
            },
        ),
    ]
    passed = all(item["passed"] for item in checks)
    return {
        "schema_version": 1,
        "artifact": "resident_source_dq_execution_group",
        "filter": filter_name,
        "status": "passed" if passed else "failed",
        "passed": passed,
        "execution_route": "resident_in_memory_mask_streaming",
        "native_method": source_dq_summary.get("native_method"),
        "native_methods": list(source_dq_summary.get("native_methods") or []),
        "materializes_calibrated_dq_cache": False,
        "frame_count": int(frame_count),
        "active_frame_count": int(source_dq_summary.get("active_frame_count") or frame_count),
        "height": int(height),
        "width": int(width),
        "input_samples": int(source_dq_summary.get("input_samples") or 0),
        "frame_with_invalid_count": int(source_dq_summary.get("frame_with_invalid_count") or 0),
        "all_frame_with_invalid_count": int(source_dq_summary.get("all_frame_with_invalid_count") or 0),
        "applied_frame_count": int(source_dq_summary.get("applied_frame_count") or 0),
        "all_frame_applied_frame_count": int(
            source_dq_summary.get("all_frame_applied_frame_count") or 0
        ),
        "input_invalid_samples_before_rejection": input_invalid,
        "applied_invalid_samples": applied_invalid,
        "all_frame_input_invalid_samples_before_frame_mask": all_frame_input_invalid,
        "all_frame_applied_invalid_samples": all_frame_applied_invalid,
        "inactive_frame_input_invalid_samples_before_frame_mask": int(
            source_dq_summary.get("inactive_frame_input_invalid_samples_before_frame_mask") or 0
        ),
        "active_frame_ids_provided": bool(source_dq_summary.get("active_frame_ids_provided")),
        "input_flagged_samples": int(source_dq_summary.get("input_flagged_samples") or 0),
        "input_nonfinite_samples": int(source_dq_summary.get("input_nonfinite_samples") or 0),
        "all_frame_input_flagged_samples": int(
            source_dq_summary.get("all_frame_input_flagged_samples") or 0
        ),
        "all_frame_input_nonfinite_samples": int(
            source_dq_summary.get("all_frame_input_nonfinite_samples") or 0
        ),
        "source_dq_flag_counts": dict(source_dq_summary.get("source_dq_flag_counts") or {}),
        "source_counts": dict(source_dq_summary.get("source_counts") or {}),
        "status_counts": dict(source_dq_summary.get("status_counts") or {}),
        "application_order_counts": dict(source_dq_summary.get("application_order_counts") or {}),
        "registration_catalog_visibility_counts": dict(
            source_dq_summary.get("registration_catalog_visibility_counts") or {}
        ),
        "pre_registration_catalog_visible_row_count": int(
            source_dq_summary.get("pre_registration_catalog_visible_row_count") or 0
        ),
        "pre_registration_catalog_visible_invalid_samples": int(
            source_dq_summary.get("pre_registration_catalog_visible_invalid_samples") or 0
        ),
        "post_registration_deferred_row_count": int(
            source_dq_summary.get("post_registration_deferred_row_count") or 0
        ),
        "post_registration_deferred_invalid_samples": int(
            source_dq_summary.get("post_registration_deferred_invalid_samples") or 0
        ),
        "required_invalid_samples_not_visible_to_registration_catalog": required_invalid_not_visible,
        "sidecar_source_counts": dict(source_dq_summary.get("sidecar_source_counts") or {}),
        "streaming_memory": {
            "invalid_mask_bytes_per_pixel": 1,
            "estimated_per_frame_mask_bytes": per_frame_mask_bytes,
            "batch_frames": batch_frames,
            "estimated_batch_mask_bytes": batch_mask_bytes,
            "estimated_all_frame_mask_bytes": all_frame_mask_bytes,
        },
        "checks": checks,
        "semantics": (
            "Source-DQ invalid samples are applied to resident calibrated frames in memory "
            "with resident CUDA native methods, so resident integration skips those samples "
            "without requiring a calibrated+DQ disk cache. Non-inline source-DQ masks are "
            "required to be visible before resident registration catalog detection; inline "
            "cosmetic CUDA masks may be deferred until after registration when configured."
        ),
    }


def validate_resident_source_dq_execution_group(group: dict[str, Any]) -> None:
    if not group.get("passed"):
        failed = [str(item.get("name")) for item in group.get("checks", []) if not item.get("passed")]
        raise RuntimeError(f"resident source-DQ execution contract failed: {', '.join(failed)}")


def summarize_resident_source_dq_execution_groups(groups: list[dict[str, Any]]) -> dict[str, Any]:
    failed = [str(group.get("filter") or "unknown") for group in groups if not group.get("passed")]
    return {
        "schema_version": 1,
        "passed": not failed,
        "status": "passed" if not failed else "failed",
        "group_count": len(groups),
        "failed_groups": failed,
        "frame_count": int(sum(int(group.get("frame_count") or 0) for group in groups)),
        "active_frame_count": int(sum(int(group.get("active_frame_count") or 0) for group in groups)),
        "input_samples": int(sum(int(group.get("input_samples") or 0) for group in groups)),
        "frame_with_invalid_count": int(
            sum(int(group.get("frame_with_invalid_count") or 0) for group in groups)
        ),
        "all_frame_with_invalid_count": int(
            sum(int(group.get("all_frame_with_invalid_count") or 0) for group in groups)
        ),
        "applied_frame_count": int(sum(int(group.get("applied_frame_count") or 0) for group in groups)),
        "all_frame_applied_frame_count": int(
            sum(int(group.get("all_frame_applied_frame_count") or 0) for group in groups)
        ),
        "input_invalid_samples_before_rejection": int(
            sum(int(group.get("input_invalid_samples_before_rejection") or 0) for group in groups)
        ),
        "applied_invalid_samples": int(
            sum(int(group.get("applied_invalid_samples") or 0) for group in groups)
        ),
        "all_frame_input_invalid_samples_before_frame_mask": int(
            sum(
                int(group.get("all_frame_input_invalid_samples_before_frame_mask") or 0)
                for group in groups
            )
        ),
        "all_frame_applied_invalid_samples": int(
            sum(int(group.get("all_frame_applied_invalid_samples") or 0) for group in groups)
        ),
        "inactive_frame_input_invalid_samples_before_frame_mask": int(
            sum(
                int(group.get("inactive_frame_input_invalid_samples_before_frame_mask") or 0)
                for group in groups
            )
        ),
        "materializes_calibrated_dq_cache": any(
            bool(group.get("materializes_calibrated_dq_cache")) for group in groups
        ),
        "execution_routes": sorted({str(group.get("execution_route") or "unknown") for group in groups}),
        "estimated_peak_batch_mask_bytes": int(
            max(
                (
                    int((group.get("streaming_memory") or {}).get("estimated_batch_mask_bytes") or 0)
                    for group in groups
                ),
                default=0,
            )
        ),
        "estimated_all_frame_mask_bytes": int(
            sum(
                int((group.get("streaming_memory") or {}).get("estimated_all_frame_mask_bytes") or 0)
                for group in groups
            )
        ),
    }
