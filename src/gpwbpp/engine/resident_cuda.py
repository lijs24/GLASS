from __future__ import annotations

import gc
from dataclasses import asdict
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np

from gpwbpp.cpu.registration import estimate_translation_phase_correlation, translation_matrix
from gpwbpp.cpu.master_frames import image_stats, make_master_bias, make_master_dark, make_master_flat
from gpwbpp.io.fits_io import read_fits_data, write_fits_data
from gpwbpp.io.json_io import read_json, write_json
from gpwbpp.models import CalibrationPolicy, PipelineArtifact, RegistrationResult, RunState, now_iso


_AUTO_STAR_THRESHOLD_SIGMAS = (0.75, 1.0, 1.25, 1.5, 2.0, 3.0)


def _cuda_module_required():
    import gpwbpp_cuda

    if not gpwbpp_cuda.cuda_available() or not hasattr(gpwbpp_cuda, "ResidentCalibratedStack"):
        raise RuntimeError("resident CUDA mode requires the native ResidentCalibratedStack backend")
    return gpwbpp_cuda


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


def _apply_resident_registration_matrix(stack: Any, index: int, matrix: list[list[float]]) -> str:
    if _matrix_is_translation(matrix):
        stack.apply_translation_bilinear_frame(index, float(matrix[0][2]), float(matrix[1][2]), np.nan)
        return "translation_bilinear"
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
) -> tuple[np.ndarray | None, np.ndarray | None, np.ndarray | None, dict[str, Any], float | None]:
    cache = run / "calib_cache" / "resident_masters"
    cache.mkdir(parents=True, exist_ok=True)
    key = _master_set_cache_key(filter_name, height, width, bias_group, dark_group, flat_group)
    bias_path = cache / f"{key}_master_bias.npy"
    dark_path = cache / f"{key}_master_dark.npy"
    flat_path = cache / f"{key}_master_flat.npy"
    stats_path = cache / f"{key}_master_stats.json"
    if stats_path.exists():
        stats = read_json(stats_path)
        master_bias = np.load(bias_path) if bias_path.exists() else None
        master_dark = np.load(dark_path) if dark_path.exists() else None
        master_flat = np.load(flat_path) if flat_path.exists() else None
        return master_bias, master_dark, master_flat, stats, stats.get("dark_exposure_s")

    bias_records = _records_for_group(bias_group, frames, groups)
    dark_records = _records_for_group(dark_group, frames, groups)
    flat_records = _records_for_group(flat_group, frames, groups)

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
        flat_group_record = groups.get(flat_group or "")
        flat_bias_group = _find_matching_bias_for_group(flat_group_record, groups)
        flat_bias = master_bias
        if flat_bias_group != bias_group:
            flat_bias_records = _records_for_group(flat_bias_group, frames, groups)
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
        "bias_count": len(bias_paths),
        "dark_count": len(dark_paths),
        "flat_count": len(flat_paths),
        "dark_exposure_s": dark_exposure,
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
    resident_registration_results: str | Path | None = None,
    reference_frame_id: str | None = None,
    exclude_frame_ids: list[str] | None = None,
    local_normalization: str = "off",
) -> RunState:
    if integration_rejection not in {"auto", "none", "sigma_clip", "winsorized_sigma"}:
        raise ValueError("resident CUDA mode supports rejection=none, sigma_clip, or winsorized_sigma")
    if integration_weighting not in {"auto", "none"}:
        raise ValueError("resident CUDA mode currently supports integration weighting=none only")
    if resident_registration not in {
        "off",
        "translation_preview",
        "translation_ncc_subpixel",
        "translation_star_catalog",
        "similarity_cuda_catalog",
        "external_matrix",
    }:
        raise ValueError(
            "resident_registration must be off, translation_preview, translation_ncc_subpixel, "
            "translation_star_catalog, similarity_cuda_catalog, or external_matrix"
        )
    if local_normalization not in {"auto", "on", "off"}:
        raise ValueError("local_normalization must be auto, on, or off")
    if resident_registration_max_shift < 0:
        raise ValueError("resident_registration_max_shift must be non-negative")
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
    if (resident_star_grid_cols > 0 or resident_star_grid_rows > 0) and (
        resident_star_grid_cols <= 0 or resident_star_grid_rows <= 0
    ):
        raise ValueError("resident star grid dimensions must both be positive")

    cuda_module = _cuda_module_required()
    plan = read_json(plan_path)
    run = Path(run_dir)
    run.mkdir(parents=True, exist_ok=True)
    state = RunState(run_id=run.name or "gpwbpp-run", created_at=now_iso(), current_stage="resident_calibration")

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
            per_frame_registration_s = []
            frame_weight_values: list[float] = []
            current_master_key: str | None = None
            current_dark_exposure: float | None = None
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
                    )
                    stack.set_calibration_masters(master_bias, master_dark, master_flat)
                    master_elapsed += perf_counter() - master_set_start
                    master_stats_sets[master_key] = stats
                    current_master_key = master_key
                    current_dark_exposure = None if dark_exposure is None else float(dark_exposure)
                    del master_bias, master_dark, master_flat
                    gc.collect()
                light = read_fits_data(frame["path"], dtype=np.float32)
                stack.calibrate_frame(
                    index,
                    light,
                    float(frame.get("exposure_s") or 0.0),
                    current_dark_exposure,
                    asdict(policy),
                )
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
                            preview_dx, preview_dy = estimate_translation_phase_correlation(reference_preview, preview)
                            dx = float(preview_dx * preview_scale)
                            dy = float(preview_dy * preview_scale)
                            stack.apply_translation_frame(index, int(round(dx)), int(round(dy)), np.nan)
                        else:
                            status = "reference"
                    except Exception as exc:
                        status = "failed"
                        frame_weight = 0.0
                        warnings.append(str(exc))
                    per_frame_registration_s.append(perf_counter() - registration_frame_start)
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
                    gc.collect()
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
                    "apply_matrix_bilinear_frame",
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

                def detect_resident_catalog(frame_index: int, threshold: float) -> dict[str, Any]:
                    if use_grid_catalog:
                        return stack.star_grid_top_nms_candidates(
                            frame_index,
                            threshold,
                            resident_star_grid_cols,
                            resident_star_grid_rows,
                            grid_top_candidates_per_cell,
                            resident_star_max_candidates,
                            nms_min_separation_px,
                        )
                    if has_top_nms_catalog:
                        return stack.star_top_nms_candidates(
                            frame_index,
                            threshold,
                            nms_scan_candidates,
                            resident_star_max_candidates,
                            nms_min_separation_px,
                        )
                    return stack.star_top_candidates(frame_index, threshold, resident_star_max_candidates)

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
                                    stack.apply_matrix_bilinear_frame(index, matrix, np.nan)
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
                                warp_model = _apply_resident_registration_matrix(stack, index, matrix)
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

            local_norm_start = perf_counter()
            local_norm_policy = plan.get("local_normalization_policy", {})
            local_norm_enabled = local_normalization == "on" or (
                local_normalization == "auto" and bool(local_norm_policy.get("enabled", False))
            )
            local_norm_mode = "resident_global_mean_std" if local_norm_enabled else "off"
            local_norm_frame_results: list[dict[str, Any]] = []
            local_norm_warnings: list[str] = []
            if local_norm_enabled:
                if not hasattr(stack, "frame_global_stats") or not hasattr(stack, "apply_global_normalization_frame"):
                    raise RuntimeError("resident CUDA backend does not expose global local normalization")
                reference_stats = stack.frame_global_stats(reference_index)
                reference_mean = float(reference_stats["mean"])
                reference_std = float(reference_stats["std"])
                eps = 1.0e-6
                local_norm_warnings.append(
                    "resident CUDA local normalization currently uses one global mean/std model per frame; "
                    "full tile/window LN remains a later gate"
                )
                for index, frame in enumerate(light_frames):
                    status = "ok"
                    warnings: list[str] = []
                    scale = 1.0
                    offset = 0.0
                    source_stats: dict[str, Any] | None = None
                    if frame_weight_values[index] <= 0.0:
                        status = "skipped_zero_weight"
                        warnings.append("frame was excluded or failed registration before local normalization")
                    elif index == reference_index:
                        status = "reference"
                        source_stats = reference_stats
                    else:
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
                    local_norm_frame_results.append(
                        {
                            "frame_id": str(frame["id"]),
                            "reference_frame_id": str(reference_frame["id"]),
                            "scale": float(scale),
                            "offset": float(offset),
                            "source_mean": None if source_stats is None else float(source_stats["mean"]),
                            "source_std": None if source_stats is None else float(source_stats["std"]),
                            "reference_mean": reference_mean,
                            "reference_std": reference_std,
                            "valid_pixels": None if source_stats is None else int(source_stats["valid_pixels"]),
                            "status": status,
                            "warnings": warnings,
                        }
                    )
            else:
                local_norm_warnings.append(
                    "resident CUDA local normalization disabled; use --local-normalization on for global LN"
                )
            local_norm_elapsed = perf_counter() - local_norm_start
            local_norm_groups.append(
                {
                    "filter": filter_name,
                    "enabled": local_norm_enabled,
                    "mode": local_norm_mode,
                    "reference_frame_id": str(reference_frame["id"]),
                    "reference_index": reference_index,
                    "crop_box": None,
                    "frame_results": local_norm_frame_results,
                    "timing_s": local_norm_elapsed,
                    "warnings": local_norm_warnings,
                }
            )

            integrate_start = perf_counter()
            coverage_map = None
            low_rejection_map = None
            high_rejection_map = None
            weights_array = np.asarray(frame_weight_values, dtype=np.float32)
            weights_arg = None if np.all(weights_array == 1.0) else weights_array
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
            master_path = output_dir / f"resident_master_{filt}.fits"
            weight_path = output_dir / f"resident_weight_map_{filt}.fits"
            coverage_path = output_dir / f"resident_coverage_map_{filt}.fits" if coverage_map is not None else None
            low_rejection_path = (
                output_dir / f"resident_low_rejection_map_{filt}.fits" if low_rejection_map is not None else None
            )
            high_rejection_path = (
                output_dir / f"resident_high_rejection_map_{filt}.fits" if high_rejection_map is not None else None
            )
            write_start = perf_counter()
            write_fits_data(master_path, master, {"IMAGETYP": "master", "FILTER": filter_name})
            write_fits_data(weight_path, weight_map, {"IMAGETYP": "weight", "FILTER": filter_name})
            if coverage_map is not None and coverage_path is not None:
                write_fits_data(coverage_path, coverage_map, {"IMAGETYP": "coverage", "FILTER": filter_name})
            if low_rejection_map is not None and low_rejection_path is not None:
                write_fits_data(low_rejection_path, low_rejection_map, {"IMAGETYP": "rej_low", "FILTER": filter_name})
            if high_rejection_map is not None and high_rejection_path is not None:
                write_fits_data(high_rejection_path, high_rejection_map, {"IMAGETYP": "rej_high", "FILTER": filter_name})
            write_elapsed = perf_counter() - write_start

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
            resident_artifacts.append(
                {
                    "filter": filter_name,
                    "frame_ids": [str(frame["id"]) for frame in light_frames],
                    "shape": {"height": height, "width": width},
                    "master_stats": master_stats,
                    "output_diagnostics": output_diagnostics,
                    "memory_estimate": memory_estimate,
                    "resident_bytes_allocated_after_master_upload": stack.bytes_allocated,
                    "timing_s": {
                        "master_build_or_load": master_elapsed,
                        "resident_allocate_and_master_upload": allocate_elapsed,
                        "registration_preview_setup": registration_setup_elapsed,
                        "light_read_upload_calibrate": load_calibrate_elapsed,
                        "resident_local_normalization": local_norm_elapsed,
                        "resident_integration": integrate_elapsed,
                        "output_write": write_elapsed,
                        "per_frame_mean": float(np.mean(per_frame_s)) if per_frame_s else 0.0,
                        "per_frame_min": float(np.min(per_frame_s)) if per_frame_s else 0.0,
                        "per_frame_max": float(np.max(per_frame_s)) if per_frame_s else 0.0,
                        "per_frame_registration_mean": (
                            float(np.mean(per_frame_registration_s)) if per_frame_registration_s else 0.0
                        ),
                    },
                    "resident_registration": {
                        "mode": resident_registration,
                        "reference_frame_id": str(reference_frame["id"]),
                        "preview_scale": preview_scale,
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
                        "external_registration_results_path": None
                        if external_registration_path is None
                        else str(external_registration_path),
                        "failed_frame_count": int(np.count_nonzero(weights_array == 0.0)),
                        "excluded_frame_tokens": sorted(excluded_tokens),
                    },
                    "resident_local_normalization": {
                        "enabled": local_norm_enabled,
                        "mode": local_norm_mode,
                        "reference_frame_id": str(reference_frame["id"]),
                        "warning_count": len(local_norm_warnings),
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
                            "with CUDA matrix bilinear warp."
                            if resident_registration == "external_matrix"
                            else "Resident registration estimated CUDA similarity matrices and applied resident matrix warp."
                            if resident_registration == "similarity_cuda_catalog"
                            else "Resident registration is optional and currently limited to translation."
                        ),
                        (
                            "Resident local normalization uses a global mean/std model per frame."
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
                    "weight_map_path": str(weight_path),
                    "coverage_map_path": None if coverage_path is None else str(coverage_path),
                    "low_rejection_map_path": None if low_rejection_path is None else str(low_rejection_path),
                    "high_rejection_map_path": None if high_rejection_path is None else str(high_rejection_path),
                    "backend": "cuda_resident_stack",
                    "memory_mode": "resident",
                    "rejection": rejection_mode,
                    "weighting": "none",
                    "resident_registration": resident_registration,
                    "resident_local_normalization": local_norm_mode,
                    "estimated_peak_gib": memory_estimate["estimated_peak_gib"],
                    "resident_integration_s": integrate_elapsed,
                    "output_diagnostics": output_diagnostics,
                }
            )
            del stack, master, weight_map
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
                            "with CUDA matrix bilinear warp"
                            if resident_registration == "external_matrix"
                            else (
                                "resident registration estimated CUDA catalog similarity matrices and applied them "
                                "with resident matrix bilinear warp"
                            )
                            if resident_registration == "similarity_cuda_catalog"
                            else "resident registration is translation-only in the current gate"
                        ),
                        (
                            "similarity-catalog mode records CUDA fit/refine diagnostics in warnings"
                            if resident_registration == "similarity_cuda_catalog"
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
                "mode": "resident_global_mean_std"
                if any(group["enabled"] for group in local_norm_groups)
                else "off",
                "enabled": any(group["enabled"] for group in local_norm_groups),
                "crop_box": None,
                "groups": local_norm_groups,
                "warnings": [
                    "resident global LN is an early high-VRAM capability; full tile/window LN is not claimed here"
                ],
            },
        )
        integration_warnings = [
            "resident CUDA winsorized_sigma is currently a two-stage winsorized mean/std rejection approximation",
        ]
        if any(group["enabled"] for group in local_norm_groups):
            integration_warnings.append("resident CUDA used global mean/std local normalization before integration")
        else:
            integration_warnings.append("resident CUDA mode skipped local normalization")
        write_json(
            run / "integration_results.json",
            {
                "schema_version": 1,
                "source_stage": "resident_calibrated_stack",
                "combine": "mean",
                "weighting": "none",
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
                else "registration is translation only and local normalization is global mean/std when enabled"
            )
        )
        return state
    except Exception as exc:
        state.failed_stage = state.current_stage
        state.errors.append(str(exc))
        raise
