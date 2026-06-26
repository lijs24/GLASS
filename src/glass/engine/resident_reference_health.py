from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np

from glass.cpu.calibration import calibrate_light
from glass.cpu.metrics import combined_quality_weight, summarize_stars
from glass.cpu.star_detect import detect_stars, robust_background
from glass.engine.resident_reference_scout import build_resident_reference_scout
from glass.io.fits_io import FitsImageReader
from glass.io.json_io import read_json
from glass.models import CalibrationPolicy
from glass.models import now_iso


DEFAULT_RESIDENT_REFERENCE_HEALTH_GATE = "auto"
DEFAULT_RESIDENT_REFERENCE_HEALTH_MIN_CPU_STAR_RATIO = 0.85
DEFAULT_RESIDENT_REFERENCE_HEALTH_MAX_CPU_RANK_FRACTION = 0.25
DEFAULT_RESIDENT_REFERENCE_HEALTH_CALIBRATED_MIN_STAR_RATIO = 0.75
DEFAULT_RESIDENT_REFERENCE_HEALTH_CALIBRATED_MAX_RANK_FRACTION = 0.25
DEFAULT_RESIDENT_REFERENCE_HEALTH_CUDA_CALIBRATED_MIN_STAR_RATIO = 0.75
DEFAULT_RESIDENT_REFERENCE_HEALTH_CUDA_CALIBRATED_MAX_RANK_FRACTION = 0.25
DEFAULT_RESIDENT_REFERENCE_HEALTH_PHASE = "auto"

_SUPPORTED_ACTIONS = {"auto", "off", "warn", "fail"}
_SUPPORTED_PHASES = {"auto", "pre", "post"}


def resolve_resident_reference_health_action(
    requested_action: str,
    *,
    scout_backend: str,
) -> str:
    action = str(requested_action or DEFAULT_RESIDENT_REFERENCE_HEALTH_GATE).lower()
    if action not in _SUPPORTED_ACTIONS:
        raise ValueError("resident reference health gate must be auto, off, warn, or fail")
    if action != "auto":
        return action
    return "fail" if str(scout_backend or "").lower() == "cuda" else "off"


def resident_reference_health_action_backend(scout: dict[str, Any]) -> str:
    backend = str(scout.get("catalog_backend") or "")
    resolution = scout.get("catalog_backend_resolution")
    if isinstance(resolution, dict) and str(resolution.get("attempted") or "").lower() == "cuda":
        return "cuda"
    return backend


def resolve_resident_reference_health_phase(
    requested_phase: str,
    *,
    scout: dict[str, Any] | None,
    requested_action: str = DEFAULT_RESIDENT_REFERENCE_HEALTH_GATE,
) -> str:
    phase = str(requested_phase or DEFAULT_RESIDENT_REFERENCE_HEALTH_PHASE).lower()
    if phase not in _SUPPORTED_PHASES:
        raise ValueError("resident reference health phase must be auto, pre, or post")
    if phase != "auto":
        return phase
    if not isinstance(scout, dict):
        return "pre"
    health_backend = resident_reference_health_action_backend(scout)
    action = resolve_resident_reference_health_action(requested_action, scout_backend=health_backend)
    if action == "off":
        return "pre"
    backend = str(scout.get("catalog_backend") or "").lower()
    resolution = scout.get("catalog_backend_resolution")
    attempted = str(resolution.get("attempted") or "").lower() if isinstance(resolution, dict) else ""
    reason = str(resolution.get("reason") or "").lower() if isinstance(resolution, dict) else ""
    cpu_guard = resolution.get("cpu_guard") if isinstance(resolution, dict) else None
    has_cpu_guard = isinstance(cpu_guard, dict)
    auto_cuda_cpu_fallback = (
        backend == "cpu"
        and health_backend.lower() == "cuda"
        and attempted == "cuda"
        and (reason == "cuda_reference_scout_auto_cpu_guard_fallback" or has_cpu_guard)
        and bool(_frame_quality_rows(scout))
        and bool(scout.get("reference_frame_id"))
    )
    return "post" if auto_cuda_cpu_fallback else "pre"


def _selection_key(row: dict[str, Any]) -> tuple[int, float, float, float, float]:
    return (
        int(row.get("star_count") or 0),
        float(row.get("quality_score") or row.get("weight") or 0.0),
        -float(row.get("fwhm_px") if row.get("fwhm_px") is not None else 999.0),
        -float(row.get("eccentricity") if row.get("eccentricity") is not None else 1.0),
        -float(row.get("background_rms") or 0.0),
    )


def _frame_quality_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = payload.get("frame_quality") if isinstance(payload.get("frame_quality"), list) else []
    return [row for row in rows if isinstance(row, dict)]


def _cpu_crosscheck_from_scout_if_reusable(
    scout: dict[str, Any],
    *,
    scout_path: Path,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    rows = _frame_quality_rows(scout)
    backend = str(scout.get("catalog_backend") or "").lower()
    reference_frame_id = str(scout.get("reference_frame_id") or "")
    if backend != "cpu":
        return None, {
            "used": False,
            "reason": "scout_backend_not_cpu",
            "scout_backend": backend,
            "source_artifact": str(scout_path),
        }
    if not rows:
        return None, {
            "used": False,
            "reason": "scout_has_no_frame_quality_rows",
            "scout_backend": backend,
            "source_artifact": str(scout_path),
        }
    if not reference_frame_id:
        return None, {
            "used": False,
            "reason": "scout_missing_reference_frame_id",
            "scout_backend": backend,
            "source_artifact": str(scout_path),
            "row_count": len(rows),
        }
    reusable = dict(scout)
    reusable["artifact_type"] = "resident_reference_health_reused_cpu_crosscheck"
    reusable["reuse_source_artifact_type"] = scout.get("artifact_type")
    reusable["reuse_source_path"] = str(scout_path)
    return reusable, {
        "used": True,
        "reason": "scout_cpu_frame_quality_reused",
        "scout_backend": backend,
        "source_artifact": str(scout_path),
        "row_count": len(rows),
        "reference_frame_id": reference_frame_id,
        "catalog_backend_requested": scout.get("catalog_backend_requested"),
        "catalog_backend_resolution": scout.get("catalog_backend_resolution"),
    }


def _plan_frames_by_id(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    frames = plan.get("frames") if isinstance(plan.get("frames"), list) else []
    return {
        str(frame.get("id")): frame
        for frame in frames
        if isinstance(frame, dict) and frame.get("id") is not None
    }


def _shape_from_stats(stats: dict[str, Any]) -> tuple[int | None, int | None]:
    shape = stats.get("shape") if isinstance(stats.get("shape"), dict) else {}
    try:
        height = int(shape.get("height"))
        width = int(shape.get("width"))
    except (TypeError, ValueError):
        return None, None
    return height, width


def _candidate_master_cache_sets(
    master_cache_dir: str | Path | None,
    *,
    filter_name: str | None,
    shape: tuple[int, int] | None,
) -> list[dict[str, Any]]:
    if master_cache_dir is None:
        return []
    cache_dir = Path(master_cache_dir)
    if not cache_dir.exists():
        return []
    candidates: list[dict[str, Any]] = []
    for stats_path in sorted(cache_dir.glob("*_master_stats.json")):
        try:
            stats = read_json(stats_path)
        except Exception:
            continue
        if not isinstance(stats, dict):
            continue
        stats_filter = None if stats.get("filter") is None else str(stats.get("filter"))
        if filter_name is not None and stats_filter not in {None, str(filter_name)}:
            continue
        stats_height, stats_width = _shape_from_stats(stats)
        if shape is not None and (stats_height, stats_width) != shape:
            continue
        cache_key = str(stats.get("cache_key") or "")
        if not cache_key:
            continue
        set_dir = Path(str(stats.get("cache_dir") or cache_dir))
        files = {
            "bias": set_dir / f"{cache_key}_master_bias.npy",
            "dark": set_dir / f"{cache_key}_master_dark.npy",
            "flat": set_dir / f"{cache_key}_master_flat.npy",
        }
        if not all(path.exists() for path in files.values()):
            continue
        candidates.append(
            {
                "stats_path": str(stats_path),
                "stats": stats,
                "cache_dir": str(set_dir),
                "cache_key": cache_key,
                "files": {key: str(path) for key, path in files.items()},
            }
        )
    return candidates


def _load_master_arrays(cache_set: dict[str, Any]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    files = cache_set.get("files") if isinstance(cache_set.get("files"), dict) else {}
    return (
        np.load(str(files["bias"]), mmap_mode="r"),
        np.load(str(files["dark"]), mmap_mode="r"),
        np.load(str(files["flat"]), mmap_mode="r"),
    )


def _sample_cache_stats(sample_input_cache: dict[Any, Any] | None) -> dict[str, Any]:
    if sample_input_cache is None:
        return {
            "enabled": False,
            "hits": 0,
            "misses": 0,
            "stored_samples": 0,
            "stored_bytes": 0,
            "strategy": "disabled",
        }
    stats = sample_input_cache.setdefault(
        "_stats",
        {
            "enabled": True,
            "hits": 0,
            "misses": 0,
            "stored_samples": 0,
            "stored_bytes": 0,
            "strategy": "strided_light_bias_dark_flat_input_reuse",
        },
    )
    return stats if isinstance(stats, dict) else {}


def _sample_input_cache_key(
    scout_row: dict[str, Any],
    *,
    frame: dict[str, Any],
    x0: int,
    y0: int,
    sample_side: int,
    stride: int,
) -> tuple[str, str, int, int, int, int]:
    return (
        str(scout_row.get("frame_id")),
        str(frame.get("path")),
        int(x0),
        int(y0),
        int(sample_side),
        int(stride),
    )


def _strided_sample_inputs(
    scout_row: dict[str, Any],
    *,
    frame: dict[str, Any],
    master_bias: np.ndarray,
    master_dark: np.ndarray,
    master_flat: np.ndarray,
    sample_input_cache: dict[Any, Any] | None = None,
) -> dict[str, Any]:
    origin = scout_row.get("sample_origin_xy") if isinstance(scout_row.get("sample_origin_xy"), list) else [0, 0]
    sample_shape = scout_row.get("sample_shape") if isinstance(scout_row.get("sample_shape"), list) else [1, 1]
    stride = max(1, int(scout_row.get("sample_stride") or 1))
    sample_side = max(1, int(scout_row.get("sample_side") or max(sample_shape)))
    x0 = int(origin[0])
    y0 = int(origin[1])
    key = _sample_input_cache_key(
        scout_row,
        frame=frame,
        x0=x0,
        y0=y0,
        sample_side=sample_side,
        stride=stride,
    )
    stats = _sample_cache_stats(sample_input_cache)
    if sample_input_cache is not None and key in sample_input_cache:
        stats["hits"] = int(stats.get("hits") or 0) + 1
        cached = sample_input_cache[key]
        return dict(cached) if isinstance(cached, dict) else cached

    path = Path(str(frame["path"]))
    with FitsImageReader(path) as reader:
        crop_width = min(int(reader.width) - x0, sample_side)
        crop_height = min(int(reader.height) - y0, sample_side)
        light = reader.read_tile(y0, y0 + crop_height, x0, x0 + crop_width)
    sample_slice = (slice(None, None, stride), slice(None, None, stride))
    record = {
        "frame_id": str(scout_row.get("frame_id")),
        "source_path": str(path),
        "x0": x0,
        "y0": y0,
        "stride": stride,
        "sample_side": sample_side,
        "light": np.ascontiguousarray(light[sample_slice], dtype=np.float32),
        "bias": np.ascontiguousarray(
            master_bias[y0 : y0 + crop_height, x0 : x0 + crop_width][sample_slice],
            dtype=np.float32,
        ),
        "dark": np.ascontiguousarray(
            master_dark[y0 : y0 + crop_height, x0 : x0 + crop_width][sample_slice],
            dtype=np.float32,
        ),
        "flat": np.ascontiguousarray(
            master_flat[y0 : y0 + crop_height, x0 : x0 + crop_width][sample_slice],
            dtype=np.float32,
        ),
    }
    if sample_input_cache is not None:
        stored_bytes = sum(
            int(record[name].nbytes)
            for name in ("light", "bias", "dark", "flat")
            if isinstance(record.get(name), np.ndarray)
        )
        stats["misses"] = int(stats.get("misses") or 0) + 1
        stats["stored_samples"] = int(stats.get("stored_samples") or 0) + 1
        stats["stored_bytes"] = int(stats.get("stored_bytes") or 0) + stored_bytes
        sample_input_cache[key] = record
    return dict(record)


def _cuda_reference_health_available() -> tuple[bool, str]:
    try:
        import glass_cuda
    except Exception as exc:
        return False, f"import_failed:{type(exc).__name__}: {exc}"
    if not getattr(glass_cuda, "cuda_available", lambda: False)():
        return False, "cuda_unavailable"
    if not hasattr(glass_cuda, "calibrate_tile_f32"):
        return False, "missing_calibrate_tile_f32"
    if not hasattr(glass_cuda, "star_grid_top_nms_candidates_f32"):
        return False, "missing_star_grid_top_nms_candidates_f32"
    return True, "available"


def _calibration_policy(plan: dict[str, Any], *, flat_floor: float | None, cache_stats: dict[str, Any]) -> CalibrationPolicy:
    calibration_plan = plan.get("calibration_plan") if isinstance(plan.get("calibration_plan"), dict) else {}
    policy_payload = (
        calibration_plan.get("calibration_policy")
        if isinstance(calibration_plan.get("calibration_policy"), dict)
        else {}
    )
    policy = CalibrationPolicy(**policy_payload)
    if flat_floor is not None:
        policy.flat_floor = float(flat_floor)
    else:
        flat_norm = cache_stats.get("flat_normalization") if isinstance(cache_stats.get("flat_normalization"), dict) else {}
        if flat_norm.get("flat_floor") is not None:
            policy.flat_floor = float(flat_norm["flat_floor"])
    if cache_stats.get("master_dark_includes_bias") is not None:
        policy.master_dark_includes_bias = bool(cache_stats.get("master_dark_includes_bias"))
    return policy


def _calibrated_crosscheck_row(
    scout_row: dict[str, Any],
    *,
    frame: dict[str, Any],
    master_bias: np.ndarray,
    master_dark: np.ndarray,
    master_flat: np.ndarray,
    dark_exposure_s: float | None,
    policy: CalibrationPolicy,
    threshold_sigma: float,
    max_stars: int,
    sample_input_cache: dict[Any, Any] | None = None,
) -> dict[str, Any]:
    inputs = _strided_sample_inputs(
        scout_row,
        frame=frame,
        master_bias=master_bias,
        master_dark=master_dark,
        master_flat=master_flat,
        sample_input_cache=sample_input_cache,
    )
    calibrated = calibrate_light(
        inputs["light"],
        inputs["bias"],
        inputs["dark"],
        inputs["flat"],
        float(frame.get("exposure_s") or 0.0),
        dark_exposure_s,
        policy,
    )
    stats = robust_background(calibrated)
    stars = detect_stars(
        calibrated,
        threshold_sigma=float(threshold_sigma),
        max_stars=int(max_stars),
        background=stats.median,
        noise=stats.noise,
        window_radius=2,
        min_separation_px=2.0,
    )
    star_metrics = summarize_stars(stars)
    snr = float(star_metrics["star_snr_median"] or 0.0)
    weight, components = combined_quality_weight(
        star_count=len(stars),
        star_snr=snr,
        fwhm_px=star_metrics["fwhm_median_px"],
        eccentricity=star_metrics["eccentricity_median"],
        background_rms=stats.rms,
        saturation_fraction=0.0,
    )
    return {
        "frame_id": str(scout_row.get("frame_id")),
        "source_path": str(inputs["source_path"]),
        "metric_source": "resident_reference_health_calibrated_sample_v1",
        "star_count": len(stars),
        "quality_score": weight,
        "weight_components": components,
        "background_median": stats.median,
        "background_rms": stats.rms,
        "background_mad": stats.mad,
        "noise_mad": stats.noise,
        "snr": snr,
        "fwhm_px": star_metrics["fwhm_median_px"],
        "eccentricity": star_metrics["eccentricity_median"],
        "star_metrics": star_metrics,
        "sample_origin_xy": [int(inputs["x0"]), int(inputs["y0"])],
        "sample_shape": [int(calibrated.shape[0]), int(calibrated.shape[1])],
        "sample_stride": int(inputs["stride"]),
        "sample_side": int(inputs["sample_side"]),
    }


def _cuda_calibrated_crosscheck_row(
    scout_row: dict[str, Any],
    *,
    frame: dict[str, Any],
    master_bias: np.ndarray,
    master_dark: np.ndarray,
    master_flat: np.ndarray,
    dark_exposure_s: float | None,
    policy: CalibrationPolicy,
    threshold_sigma: float,
    max_stars: int,
    sample_input_cache: dict[Any, Any] | None = None,
) -> dict[str, Any]:
    import glass_cuda

    inputs = _strided_sample_inputs(
        scout_row,
        frame=frame,
        master_bias=master_bias,
        master_dark=master_dark,
        master_flat=master_flat,
        sample_input_cache=sample_input_cache,
    )
    calibrated = np.asarray(
        glass_cuda.calibrate_tile_f32(
            inputs["light"],
            inputs["bias"],
            inputs["dark"],
            inputs["flat"],
            float(frame.get("exposure_s") or 0.0),
            dark_exposure_s,
            asdict(policy),
        ),
        dtype=np.float32,
    )
    stats = robust_background(calibrated)
    threshold = float(stats.median) + float(threshold_sigma) * max(float(stats.noise), 1.0e-6)
    height, width = calibrated.shape
    grid_cols = max(1, min(16, int(np.ceil(width / 64.0))))
    grid_rows = max(1, min(12, int(np.ceil(height / 64.0))))
    min_separation = max(2.0, float(min(height, width)) / 32.0)
    catalog = glass_cuda.star_grid_top_nms_candidates_f32(
        calibrated,
        threshold,
        grid_cols,
        grid_rows,
        4,
        int(max_stars),
        min_separation,
    )
    stored_count = int(catalog.get("stored_count") or 0)
    detected_count = int(catalog.get("count") or 0)
    flux = np.asarray(catalog.get("flux", []), dtype=np.float32)
    finite_flux = flux[np.isfinite(flux)]
    peak_snr_values = np.maximum(finite_flux - np.float32(stats.median), 0.0) / np.float32(
        max(float(stats.noise), 1.0e-6)
    )
    peak_snr_values = peak_snr_values[np.isfinite(peak_snr_values)]
    peak_snr = float(np.median(peak_snr_values)) if peak_snr_values.size else 0.0
    flux_median = float(np.median(finite_flux)) if finite_flux.size else 0.0
    weight, components = combined_quality_weight(
        star_count=stored_count,
        star_snr=peak_snr,
        fwhm_px=None,
        eccentricity=None,
        background_rms=stats.rms,
        saturation_fraction=0.0,
    )
    return {
        "frame_id": str(scout_row.get("frame_id")),
        "source_path": str(inputs["source_path"]),
        "metric_source": "resident_reference_health_cuda_calibrated_sample_v1",
        "star_count": stored_count,
        "detected_count": detected_count,
        "quality_score": weight,
        "weight_components": components,
        "background_median": stats.median,
        "background_rms": stats.rms,
        "background_mad": stats.mad,
        "noise_mad": stats.noise,
        "snr": peak_snr,
        "fwhm_px": None,
        "eccentricity": None,
        "flux_median": flux_median,
        "threshold": threshold,
        "catalog_diagnostics": {
            "catalog_model": "cuda_calibrate_tile_f32_then_star_grid_top_nms_candidates_f32",
            "grid_cols": grid_cols,
            "grid_rows": grid_rows,
            "candidates_per_cell": 4,
            "max_output_candidates": int(max_stars),
            "min_separation_px": min_separation,
            "catalog_sort_mode": str(catalog.get("catalog_sort_mode", "unavailable")),
            "catalog_topk_mode": str(catalog.get("catalog_topk_mode", "unavailable")),
        },
        "sample_origin_xy": [int(inputs["x0"]), int(inputs["y0"])],
        "sample_shape": [int(calibrated.shape[0]), int(calibrated.shape[1])],
        "sample_stride": int(inputs["stride"]),
        "sample_side": int(inputs["sample_side"]),
    }


def _calibrated_crosscheck(
    plan: dict[str, Any],
    scout: dict[str, Any],
    *,
    master_cache_dir: str | Path | None,
    flat_floor: float | None,
    reference_frame_id: str,
    min_star_ratio: float,
    max_rank_fraction: float,
    enabled: bool,
    sample_input_cache: dict[Any, Any] | None = None,
) -> dict[str, Any]:
    scout_rows = _frame_quality_rows(scout)
    frames_by_id = _plan_frames_by_id(plan)
    first_row = scout_rows[0] if scout_rows else {}
    first_frame = frames_by_id.get(str(first_row.get("frame_id")))
    shape_value = first_row.get("full_shape") if isinstance(first_row.get("full_shape"), list) else None
    shape = (int(shape_value[0]), int(shape_value[1])) if shape_value and len(shape_value) >= 2 else None
    filter_name = None if first_frame is None or first_frame.get("filter") is None else str(first_frame.get("filter"))
    cache_sets = _candidate_master_cache_sets(master_cache_dir, filter_name=filter_name, shape=shape)
    if not cache_sets:
        return {
            "status": "unavailable",
            "available": False,
            "reason": "matching_resident_master_cache_not_found",
            "master_cache_dir": None if master_cache_dir is None else str(master_cache_dir),
            "filter": filter_name,
            "shape": None if shape is None else {"height": shape[0], "width": shape[1]},
            "checks": [],
            "failed_checks": [],
        }
    cache_set = cache_sets[0]
    stats = cache_set["stats"]
    master_bias, master_dark, master_flat = _load_master_arrays(cache_set)
    policy = _calibration_policy(plan, flat_floor=flat_floor, cache_stats=stats)
    dark_exposure = None if stats.get("dark_exposure_s") is None else float(stats.get("dark_exposure_s"))
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for scout_row in scout_rows:
        frame = frames_by_id.get(str(scout_row.get("frame_id")))
        if frame is None:
            errors.append({"frame_id": scout_row.get("frame_id"), "error": "missing_frame_in_plan"})
            continue
        try:
            rows.append(
                _calibrated_crosscheck_row(
                    scout_row,
                    frame=frame,
                    master_bias=master_bias,
                    master_dark=master_dark,
                    master_flat=master_flat,
                    dark_exposure_s=dark_exposure,
                    policy=policy,
                    threshold_sigma=float(scout.get("threshold_sigma") or 5.0),
                    max_stars=int(scout.get("max_stars") or 300),
                    sample_input_cache=sample_input_cache,
                )
            )
        except Exception as exc:
            errors.append({"frame_id": scout_row.get("frame_id"), "error": str(exc)})
    ranked = sorted(rows, key=_selection_key, reverse=True)
    calibrated_reference_frame_id = str(ranked[0]["frame_id"]) if ranked else ""
    selected_row = next((row for row in ranked if str(row.get("frame_id")) == reference_frame_id), None)
    reference_row = next((row for row in ranked if str(row.get("frame_id")) == calibrated_reference_frame_id), None)
    selected_rank = ranked.index(selected_row) + 1 if selected_row in ranked else None
    rank_fraction = (
        (float(selected_rank) - 1.0) / float(max(len(ranked) - 1, 1))
        if selected_rank is not None and ranked
        else None
    )
    selected_star_count = int(selected_row.get("star_count") or 0) if selected_row is not None else 0
    reference_star_count = int(reference_row.get("star_count") or 0) if reference_row is not None else 0
    star_ratio = (
        float(selected_star_count) / float(reference_star_count)
        if reference_star_count > 0
        else (1.0 if selected_star_count > 0 else 0.0)
    )
    checks = [
        {
            "name": "calibrated_crosscheck_measured_frames",
            "passed": bool(rows),
            "evidence": {"measured_frame_count": len(rows), "error_count": len(errors)},
        },
        {
            "name": "selected_reference_present_in_calibrated_crosscheck",
            "passed": selected_row is not None,
            "evidence": {"reference_frame_id": reference_frame_id, "present": selected_row is not None},
        },
        {
            "name": "selected_reference_calibrated_star_ratio",
            "passed": not enabled or star_ratio >= float(min_star_ratio),
            "evidence": {
                "selected_calibrated_star_count": selected_star_count,
                "calibrated_reference_star_count": reference_star_count,
                "star_ratio": star_ratio,
                "min_star_ratio": float(min_star_ratio),
            },
        },
        {
            "name": "selected_reference_calibrated_rank_fraction",
            "passed": not enabled
            or (rank_fraction is not None and rank_fraction <= float(max_rank_fraction)),
            "evidence": {
                "selected_calibrated_rank": selected_rank,
                "calibrated_measured_frame_count": len(ranked),
                "rank_fraction": rank_fraction,
                "max_rank_fraction": float(max_rank_fraction),
            },
        },
    ]
    raw_passed = all(item["passed"] for item in checks)
    cache_stats = _sample_cache_stats(sample_input_cache)
    return {
        "status": "passed" if raw_passed else "failed",
        "available": True,
        "passed": raw_passed,
        "sample_input_cache": dict(cache_stats),
        "master_cache": {
            "cache_dir": cache_set.get("cache_dir"),
            "cache_key": cache_set.get("cache_key"),
            "stats_path": cache_set.get("stats_path"),
            "filter": stats.get("filter"),
            "shape": stats.get("shape"),
            "flat_floor": float(policy.flat_floor),
            "dark_exposure_s": dark_exposure,
            "master_dark_includes_bias": bool(policy.master_dark_includes_bias),
        },
        "summary": {
            "reference_frame_id": reference_frame_id,
            "calibrated_reference_frame_id": calibrated_reference_frame_id,
            "selected_calibrated_rank": selected_rank,
            "calibrated_measured_frame_count": len(ranked),
            "selected_calibrated_star_count": selected_star_count,
            "calibrated_reference_star_count": reference_star_count,
            "selected_calibrated_star_ratio": star_ratio,
            "selected_calibrated_rank_fraction": rank_fraction,
        },
        "top_reference_candidates": [
            {
                "frame_id": row.get("frame_id"),
                "star_count": row.get("star_count"),
                "quality_score": row.get("quality_score"),
                "fwhm_px": row.get("fwhm_px"),
                "eccentricity": row.get("eccentricity"),
                "background_rms": row.get("background_rms"),
            }
            for row in ranked[:10]
        ],
        "checks": checks,
        "failed_checks": [item["name"] for item in checks if not item["passed"]],
        "error_count": len(errors),
        "errors": errors[:25],
    }


def _cuda_calibrated_crosscheck(
    plan: dict[str, Any],
    scout: dict[str, Any],
    *,
    master_cache_dir: str | Path | None,
    flat_floor: float | None,
    reference_frame_id: str,
    min_star_ratio: float,
    max_rank_fraction: float,
    sample_input_cache: dict[Any, Any] | None = None,
) -> dict[str, Any]:
    available, reason = _cuda_reference_health_available()
    if not available:
        return {
            "status": "unavailable",
            "available": False,
            "reason": reason,
            "checks": [],
            "failed_checks": [],
        }
    scout_rows = _frame_quality_rows(scout)
    frames_by_id = _plan_frames_by_id(plan)
    first_row = scout_rows[0] if scout_rows else {}
    first_frame = frames_by_id.get(str(first_row.get("frame_id")))
    shape_value = first_row.get("full_shape") if isinstance(first_row.get("full_shape"), list) else None
    shape = (int(shape_value[0]), int(shape_value[1])) if shape_value and len(shape_value) >= 2 else None
    filter_name = None if first_frame is None or first_frame.get("filter") is None else str(first_frame.get("filter"))
    cache_sets = _candidate_master_cache_sets(master_cache_dir, filter_name=filter_name, shape=shape)
    if not cache_sets:
        return {
            "status": "unavailable",
            "available": False,
            "reason": "matching_resident_master_cache_not_found",
            "master_cache_dir": None if master_cache_dir is None else str(master_cache_dir),
            "filter": filter_name,
            "shape": None if shape is None else {"height": shape[0], "width": shape[1]},
            "checks": [],
            "failed_checks": [],
        }
    cache_set = cache_sets[0]
    stats = cache_set["stats"]
    master_bias, master_dark, master_flat = _load_master_arrays(cache_set)
    policy = _calibration_policy(plan, flat_floor=flat_floor, cache_stats=stats)
    dark_exposure = None if stats.get("dark_exposure_s") is None else float(stats.get("dark_exposure_s"))
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for scout_row in scout_rows:
        frame = frames_by_id.get(str(scout_row.get("frame_id")))
        if frame is None:
            errors.append({"frame_id": scout_row.get("frame_id"), "error": "missing_frame_in_plan"})
            continue
        try:
            rows.append(
                _cuda_calibrated_crosscheck_row(
                    scout_row,
                    frame=frame,
                    master_bias=master_bias,
                    master_dark=master_dark,
                    master_flat=master_flat,
                    dark_exposure_s=dark_exposure,
                    policy=policy,
                    threshold_sigma=float(scout.get("threshold_sigma") or 5.0),
                    max_stars=int(scout.get("max_stars") or 300),
                    sample_input_cache=sample_input_cache,
                )
            )
        except Exception as exc:
            errors.append({"frame_id": scout_row.get("frame_id"), "error": str(exc)})
    ranked = sorted(
        rows,
        key=lambda row: (
            int(row.get("star_count") or 0),
            float(row.get("flux_median") or 0.0),
            float(row.get("quality_score") or 0.0),
            -float(row.get("background_rms") or 0.0),
        ),
        reverse=True,
    )
    cuda_reference_frame_id = str(ranked[0]["frame_id"]) if ranked else ""
    selected_row = next((row for row in ranked if str(row.get("frame_id")) == reference_frame_id), None)
    reference_row = next((row for row in ranked if str(row.get("frame_id")) == cuda_reference_frame_id), None)
    selected_rank = ranked.index(selected_row) + 1 if selected_row in ranked else None
    rank_fraction = (
        (float(selected_rank) - 1.0) / float(max(len(ranked) - 1, 1))
        if selected_rank is not None and ranked
        else None
    )
    selected_star_count = int(selected_row.get("star_count") or 0) if selected_row is not None else 0
    reference_star_count = int(reference_row.get("star_count") or 0) if reference_row is not None else 0
    star_ratio = (
        float(selected_star_count) / float(reference_star_count)
        if reference_star_count > 0
        else (1.0 if selected_star_count > 0 else 0.0)
    )
    checks = [
        {
            "name": "cuda_calibrated_crosscheck_measured_frames",
            "passed": bool(rows),
            "evidence": {"measured_frame_count": len(rows), "error_count": len(errors)},
        },
        {
            "name": "selected_reference_present_in_cuda_calibrated_crosscheck",
            "passed": selected_row is not None,
            "evidence": {"reference_frame_id": reference_frame_id, "present": selected_row is not None},
        },
        {
            "name": "selected_reference_cuda_calibrated_star_ratio",
            "passed": star_ratio >= float(min_star_ratio),
            "evidence": {
                "selected_cuda_calibrated_star_count": selected_star_count,
                "cuda_calibrated_reference_star_count": reference_star_count,
                "star_ratio": star_ratio,
                "min_star_ratio": float(min_star_ratio),
            },
        },
        {
            "name": "selected_reference_cuda_calibrated_rank_fraction",
            "passed": rank_fraction is not None and rank_fraction <= float(max_rank_fraction),
            "evidence": {
                "selected_cuda_calibrated_rank": selected_rank,
                "cuda_calibrated_measured_frame_count": len(ranked),
                "rank_fraction": rank_fraction,
                "max_rank_fraction": float(max_rank_fraction),
            },
        },
    ]
    raw_passed = all(item["passed"] for item in checks)
    return {
        "status": "passed" if raw_passed else "failed",
        "available": True,
        "passed": raw_passed,
        "enforced": False,
        "sample_input_cache": dict(_sample_cache_stats(sample_input_cache)),
        "master_cache": {
            "cache_dir": cache_set.get("cache_dir"),
            "cache_key": cache_set.get("cache_key"),
            "stats_path": cache_set.get("stats_path"),
            "filter": stats.get("filter"),
            "shape": stats.get("shape"),
            "flat_floor": float(policy.flat_floor),
            "dark_exposure_s": dark_exposure,
            "master_dark_includes_bias": bool(policy.master_dark_includes_bias),
        },
        "summary": {
            "reference_frame_id": reference_frame_id,
            "cuda_calibrated_reference_frame_id": cuda_reference_frame_id,
            "selected_cuda_calibrated_rank": selected_rank,
            "cuda_calibrated_measured_frame_count": len(ranked),
            "selected_cuda_calibrated_star_count": selected_star_count,
            "cuda_calibrated_reference_star_count": reference_star_count,
            "selected_cuda_calibrated_star_ratio": star_ratio,
            "selected_cuda_calibrated_rank_fraction": rank_fraction,
        },
        "top_reference_candidates": [
            {
                "frame_id": row.get("frame_id"),
                "star_count": row.get("star_count"),
                "detected_count": row.get("detected_count"),
                "quality_score": row.get("quality_score"),
                "flux_median": row.get("flux_median"),
                "background_rms": row.get("background_rms"),
            }
            for row in ranked[:10]
        ],
        "checks": checks,
        "failed_checks": [item["name"] for item in checks if not item["passed"]],
        "error_count": len(errors),
        "errors": errors[:25],
    }


def _json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = read_json(path)
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _registration_decision_by_id(registration_quality: dict[str, Any]) -> dict[str, dict[str, Any]]:
    decisions = (
        registration_quality.get("decisions")
        if isinstance(registration_quality.get("decisions"), list)
        else []
    )
    return {
        str(item.get("frame_id")): item
        for item in decisions
        if isinstance(item, dict) and item.get("frame_id") is not None
    }


def build_resident_reference_post_health(
    run_dir: str | Path,
    *,
    requested_action: str = DEFAULT_RESIDENT_REFERENCE_HEALTH_GATE,
    requested_phase: str = DEFAULT_RESIDENT_REFERENCE_HEALTH_PHASE,
    min_cpu_star_ratio: float = DEFAULT_RESIDENT_REFERENCE_HEALTH_MIN_CPU_STAR_RATIO,
    max_cpu_rank_fraction: float = DEFAULT_RESIDENT_REFERENCE_HEALTH_MAX_CPU_RANK_FRACTION,
) -> dict[str, Any]:
    if float(min_cpu_star_ratio) < 0.0:
        raise ValueError("resident reference health min CPU star ratio must be non-negative")
    if not 0.0 <= float(max_cpu_rank_fraction) <= 1.0:
        raise ValueError("resident reference health max CPU rank fraction must be in [0, 1]")

    run = Path(run_dir)
    scout_path = run / "resident_reference_scout.json"
    registration_quality_path = run / "resident_registration_quality.json"
    frame_masks_path = run / "resident_frame_masks.json"
    created_at = now_iso()

    scout = _json_if_exists(scout_path)
    health_action_backend = resident_reference_health_action_backend(scout) if scout else ""
    action = resolve_resident_reference_health_action(requested_action, scout_backend=health_action_backend)
    phase = resolve_resident_reference_health_phase(
        requested_phase,
        scout=scout,
        requested_action=requested_action,
    )
    enabled = action in {"warn", "fail"}
    reference_frame_id = str(scout.get("reference_frame_id") or "") if scout else ""
    scout_backend = str(scout.get("catalog_backend") or "") if scout else ""

    cpu_crosscheck, cpu_crosscheck_reuse = _cpu_crosscheck_from_scout_if_reusable(
        scout,
        scout_path=scout_path,
    ) if scout else (None, {
        "used": False,
        "reason": "resident_reference_scout_missing",
        "source_artifact": str(scout_path),
    })
    cpu_rows = _frame_quality_rows(cpu_crosscheck or {})
    ranked = sorted(cpu_rows, key=_selection_key, reverse=True)
    cpu_reference_frame_id = str((cpu_crosscheck or {}).get("reference_frame_id") or "")
    selected_cpu_row = next((row for row in ranked if str(row.get("frame_id")) == reference_frame_id), None)
    cpu_reference_row = next((row for row in ranked if str(row.get("frame_id")) == cpu_reference_frame_id), None)
    selected_rank = ranked.index(selected_cpu_row) + 1 if selected_cpu_row in ranked else None
    rank_fraction = (
        (float(selected_rank) - 1.0) / float(max(len(ranked) - 1, 1))
        if selected_rank is not None and ranked
        else None
    )
    selected_star_count = int(selected_cpu_row.get("star_count") or 0) if selected_cpu_row is not None else 0
    cpu_reference_star_count = int(cpu_reference_row.get("star_count") or 0) if cpu_reference_row is not None else 0
    star_ratio = (
        float(selected_star_count) / float(cpu_reference_star_count)
        if cpu_reference_star_count > 0
        else (1.0 if selected_star_count > 0 else 0.0)
    )

    registration_quality = _json_if_exists(registration_quality_path)
    registration_summary = (
        registration_quality.get("summary")
        if isinstance(registration_quality.get("summary"), dict)
        else {}
    )
    decision = _registration_decision_by_id(registration_quality).get(reference_frame_id)
    final_status = str(decision.get("final_status") or "") if isinstance(decision, dict) else ""
    decision_status = str(decision.get("decision_status") or "") if isinstance(decision, dict) else ""
    accepted = bool(decision.get("accepted")) if isinstance(decision, dict) else False
    registration_reference_ok = (
        isinstance(decision, dict)
        and final_status in {"reference", "ok"}
        and decision_status in {"reference", "accepted"}
        and accepted
    )

    frame_masks = _json_if_exists(frame_masks_path)
    frame_mask_summary = (
        frame_masks.get("summary") if isinstance(frame_masks.get("summary"), dict) else {}
    )
    active_ids = {
        str(item)
        for item in frame_mask_summary.get("active_frame_ids", [])
        if item is not None
    } if isinstance(frame_mask_summary.get("active_frame_ids"), list) else set()
    masked_ids = {
        str(item)
        for item in frame_mask_summary.get("masked_frame_ids", [])
        if item is not None
    } if isinstance(frame_mask_summary.get("masked_frame_ids"), list) else set()
    reference_active = reference_frame_id in active_ids if active_ids else registration_reference_ok
    reference_masked = reference_frame_id in masked_ids

    checks = [
        {
            "name": "resident_reference_scout_present",
            "passed": bool(scout),
            "evidence": {"path": str(scout_path), "exists": bool(scout)},
        },
        {
            "name": "reference_frame_id_recorded",
            "passed": bool(reference_frame_id),
            "evidence": {"reference_frame_id": reference_frame_id},
        },
        {
            "name": "post_resident_cpu_scout_rows_reused",
            "passed": bool(cpu_crosscheck_reuse.get("used")),
            "evidence": cpu_crosscheck_reuse,
        },
        {
            "name": "selected_reference_present_in_cpu_crosscheck",
            "passed": selected_cpu_row is not None,
            "evidence": {"reference_frame_id": reference_frame_id, "present": selected_cpu_row is not None},
        },
        {
            "name": "selected_reference_cpu_star_ratio",
            "passed": not enabled or star_ratio >= float(min_cpu_star_ratio),
            "evidence": {
                "selected_cpu_star_count": selected_star_count,
                "cpu_reference_star_count": cpu_reference_star_count,
                "star_ratio": star_ratio,
                "min_cpu_star_ratio": float(min_cpu_star_ratio),
            },
        },
        {
            "name": "selected_reference_cpu_rank_fraction",
            "passed": not enabled
            or (rank_fraction is not None and rank_fraction <= float(max_cpu_rank_fraction)),
            "evidence": {
                "selected_cpu_rank": selected_rank,
                "cpu_measured_frame_count": len(ranked),
                "rank_fraction": rank_fraction,
                "max_cpu_rank_fraction": float(max_cpu_rank_fraction),
            },
        },
        {
            "name": "resident_registration_quality_present",
            "passed": bool(registration_quality),
            "evidence": {"path": str(registration_quality_path), "exists": bool(registration_quality)},
        },
        {
            "name": "selected_reference_present_in_registration_quality",
            "passed": isinstance(decision, dict),
            "evidence": {"reference_frame_id": reference_frame_id, "present": isinstance(decision, dict)},
        },
        {
            "name": "selected_reference_not_excluded_by_registration_quality",
            "passed": not enabled or registration_reference_ok,
            "evidence": {
                "reference_frame_id": reference_frame_id,
                "decision_status": decision_status,
                "final_status": final_status,
                "accepted": accepted,
            },
        },
        {
            "name": "resident_frame_mask_contract_passed",
            "passed": not frame_mask_summary or frame_mask_summary.get("passed") is True,
            "evidence": {
                "path": str(frame_masks_path),
                "exists": bool(frame_masks),
                "passed": frame_mask_summary.get("passed"),
            },
        },
        {
            "name": "selected_reference_active_after_frame_masks",
            "passed": not enabled or (reference_active and not reference_masked),
            "evidence": {
                "reference_frame_id": reference_frame_id,
                "active": reference_active,
                "masked": reference_masked,
                "active_frame_count": frame_mask_summary.get("active_frame_count"),
                "masked_frame_count": frame_mask_summary.get("masked_frame_count"),
            },
        },
    ]
    raw_passed = all(item["passed"] for item in checks)
    passed = raw_passed or action == "warn"
    status = "disabled" if action == "off" else ("passed" if raw_passed else "warning" if action == "warn" else "failed")
    failed_checks = [item["name"] for item in checks if not item["passed"]]
    return {
        "schema_version": 1,
        "artifact_type": "resident_reference_health",
        "created_at": created_at,
        "run_dir": str(run),
        "scout_path": str(scout_path),
        "scout_backend": scout_backend,
        "health_action_backend": health_action_backend,
        "requested_action": str(requested_action or DEFAULT_RESIDENT_REFERENCE_HEALTH_GATE).lower(),
        "effective_action": action,
        "requested_phase": str(requested_phase or DEFAULT_RESIDENT_REFERENCE_HEALTH_PHASE).lower(),
        "effective_phase": phase,
        "health_model": "post_resident_artifact_reuse",
        "status": status,
        "passed": passed,
        "blocking": action == "fail" and not raw_passed,
        "thresholds": {
            "min_cpu_star_ratio": float(min_cpu_star_ratio),
            "max_cpu_rank_fraction": float(max_cpu_rank_fraction),
        },
        "summary": {
            "reference_frame_id": reference_frame_id,
            "cpu_reference_frame_id": cpu_reference_frame_id,
            "selected_cpu_rank": selected_rank,
            "cpu_measured_frame_count": len(ranked),
            "selected_cpu_star_count": selected_star_count,
            "cpu_reference_star_count": cpu_reference_star_count,
            "selected_cpu_star_ratio": star_ratio,
            "selected_cpu_rank_fraction": rank_fraction,
            "cpu_crosscheck_reused": bool(cpu_crosscheck_reuse.get("used")),
            "post_resident_artifact_reused": True,
            "post_resident_reuse_available": raw_passed,
            "calibrated_available": False,
            "cuda_calibrated_available": False,
            "reference_registration_decision_status": decision_status or None,
            "reference_registration_final_status": final_status or None,
            "reference_registration_accepted": accepted,
            "reference_active_after_frame_masks": reference_active,
            "reference_masked_after_frame_masks": reference_masked,
            "registration_quality_frame_count": registration_summary.get("frame_count"),
            "registration_quality_summary": registration_summary,
        },
        "cpu_crosscheck": {
            "artifact_type": (cpu_crosscheck or {}).get("artifact_type"),
            "catalog_backend": (cpu_crosscheck or {}).get("catalog_backend"),
            "reference_frame_id": cpu_reference_frame_id,
            "dominant_orientation_key": (cpu_crosscheck or {}).get("dominant_orientation_key"),
            "orientation_constraint_applied": (cpu_crosscheck or {}).get("orientation_constraint_applied"),
            "measured_frame_count": len(cpu_rows),
            "reuse": cpu_crosscheck_reuse,
            "top_reference_candidates": [
                {
                    "frame_id": row.get("frame_id"),
                    "star_count": row.get("star_count"),
                    "quality_score": row.get("quality_score"),
                    "fwhm_px": row.get("fwhm_px"),
                    "eccentricity": row.get("eccentricity"),
                    "background_rms": row.get("background_rms"),
                }
                for row in ranked[:10]
            ],
        },
        "post_resident_crosscheck": {
            "registration_quality_path": str(registration_quality_path),
            "frame_masks_path": str(frame_masks_path),
            "reference_decision": decision if isinstance(decision, dict) else None,
            "frame_mask_summary": frame_mask_summary,
        },
        "calibrated_crosscheck": {
            "status": "replaced_by_post_resident_artifact_reuse",
            "available": False,
            "reason": "post_resident_reference_health_uses_registration_quality_and_frame_masks",
            "checks": [],
            "failed_checks": [],
        },
        "cuda_calibrated_crosscheck": {
            "status": "replaced_by_post_resident_artifact_reuse",
            "available": False,
            "reason": "post_resident_reference_health_uses_registration_quality_and_frame_masks",
            "checks": [],
            "failed_checks": [],
        },
        "checks": checks,
        "effective_checks": checks,
        "failed_checks": failed_checks,
        "recommended_actions": [
            "inspect resident_reference_scout.json",
            "inspect resident_registration_quality.json",
            "rerun with --resident-reference-health-phase pre for pre-compute calibrated sampling",
            "provide --reference-frame-id for an explicit reference",
        ],
        "clean_room_note": (
            "Project-defined post-resident reference health over GLASS-owned scout, "
            "registration quality, and frame-mask artifacts."
        ),
    }


def build_resident_reference_health(
    plan_path: str | Path,
    run_dir: str | Path,
    *,
    requested_action: str = DEFAULT_RESIDENT_REFERENCE_HEALTH_GATE,
    min_cpu_star_ratio: float = DEFAULT_RESIDENT_REFERENCE_HEALTH_MIN_CPU_STAR_RATIO,
    max_cpu_rank_fraction: float = DEFAULT_RESIDENT_REFERENCE_HEALTH_MAX_CPU_RANK_FRACTION,
    calibrated_min_star_ratio: float = DEFAULT_RESIDENT_REFERENCE_HEALTH_CALIBRATED_MIN_STAR_RATIO,
    calibrated_max_rank_fraction: float = DEFAULT_RESIDENT_REFERENCE_HEALTH_CALIBRATED_MAX_RANK_FRACTION,
    cuda_calibrated_min_star_ratio: float = DEFAULT_RESIDENT_REFERENCE_HEALTH_CUDA_CALIBRATED_MIN_STAR_RATIO,
    cuda_calibrated_max_rank_fraction: float = DEFAULT_RESIDENT_REFERENCE_HEALTH_CUDA_CALIBRATED_MAX_RANK_FRACTION,
    master_cache_dir: str | Path | None = None,
    flat_floor: float | None = None,
) -> dict[str, Any]:
    if float(min_cpu_star_ratio) < 0.0:
        raise ValueError("resident reference health min CPU star ratio must be non-negative")
    if not 0.0 <= float(max_cpu_rank_fraction) <= 1.0:
        raise ValueError("resident reference health max CPU rank fraction must be in [0, 1]")
    if float(calibrated_min_star_ratio) < 0.0:
        raise ValueError("resident reference health calibrated min star ratio must be non-negative")
    if not 0.0 <= float(calibrated_max_rank_fraction) <= 1.0:
        raise ValueError("resident reference health calibrated max rank fraction must be in [0, 1]")
    if float(cuda_calibrated_min_star_ratio) < 0.0:
        raise ValueError("resident reference health CUDA calibrated min star ratio must be non-negative")
    if not 0.0 <= float(cuda_calibrated_max_rank_fraction) <= 1.0:
        raise ValueError("resident reference health CUDA calibrated max rank fraction must be in [0, 1]")

    run = Path(run_dir)
    scout_path = run / "resident_reference_scout.json"
    created_at = now_iso()
    if not scout_path.exists():
        action = resolve_resident_reference_health_action(requested_action, scout_backend="")
        passed = action == "off"
        checks = [
            {
                "name": "resident_reference_scout_present",
                "passed": passed,
                "evidence": {"path": str(scout_path), "exists": False, "action": action},
            }
        ]
        return {
            "schema_version": 1,
            "artifact_type": "resident_reference_health",
            "created_at": created_at,
            "run_dir": str(run),
            "scout_path": str(scout_path),
            "status": "disabled" if action == "off" else "failed",
            "passed": passed,
            "blocking": action == "fail" and not passed,
            "requested_action": str(requested_action or DEFAULT_RESIDENT_REFERENCE_HEALTH_GATE).lower(),
            "effective_action": action,
            "checks": checks,
            "failed_checks": [item["name"] for item in checks if not item["passed"]],
            "summary": {},
        }

    scout = read_json(scout_path)
    if not isinstance(scout, dict):
        raise ValueError(f"resident reference scout is not a JSON object: {scout_path}")
    plan = read_json(plan_path)
    if not isinstance(plan, dict):
        raise ValueError(f"processing plan is not a JSON object: {plan_path}")
    scout_backend = str(scout.get("catalog_backend") or "")
    health_action_backend = resident_reference_health_action_backend(scout)
    action = resolve_resident_reference_health_action(requested_action, scout_backend=health_action_backend)
    enabled = action in {"warn", "fail"}
    reference_frame_id = str(scout.get("reference_frame_id") or "")
    cpu_crosscheck, cpu_crosscheck_reuse = _cpu_crosscheck_from_scout_if_reusable(scout, scout_path=scout_path)
    if cpu_crosscheck is None:
        cpu_crosscheck = build_resident_reference_scout(
            plan_path,
            run,
            sample_stride=int(scout.get("sample_stride") or 1),
            sample_side=int(scout.get("sample_side") or 1),
            max_frames=int(scout.get("max_frames") or 0),
            threshold_sigma=float(scout.get("threshold_sigma") or 5.0),
            max_stars=int(scout.get("max_stars") or 300),
            catalog_backend="cpu",
        )
        cpu_crosscheck_reuse = {
            **cpu_crosscheck_reuse,
            "fallback_measured": True,
            "fallback_artifact_type": cpu_crosscheck.get("artifact_type"),
            "fallback_measured_frame_count": len(_frame_quality_rows(cpu_crosscheck)),
        }
    cpu_rows = _frame_quality_rows(cpu_crosscheck)
    ranked = sorted(cpu_rows, key=_selection_key, reverse=True)
    cpu_reference_frame_id = str(cpu_crosscheck.get("reference_frame_id") or "")
    selected_cpu_row = next((row for row in ranked if str(row.get("frame_id")) == reference_frame_id), None)
    cpu_reference_row = next((row for row in ranked if str(row.get("frame_id")) == cpu_reference_frame_id), None)
    selected_rank = ranked.index(selected_cpu_row) + 1 if selected_cpu_row in ranked else None
    rank_fraction = (
        (float(selected_rank) - 1.0) / float(max(len(ranked) - 1, 1))
        if selected_rank is not None and ranked
        else None
    )
    selected_star_count = int(selected_cpu_row.get("star_count") or 0) if selected_cpu_row is not None else 0
    cpu_reference_star_count = int(cpu_reference_row.get("star_count") or 0) if cpu_reference_row is not None else 0
    star_ratio = (
        float(selected_star_count) / float(cpu_reference_star_count)
        if cpu_reference_star_count > 0
        else (1.0 if selected_star_count > 0 else 0.0)
    )

    checks = [
        {
            "name": "resident_reference_scout_present",
            "passed": True,
            "evidence": {"path": str(scout_path), "exists": True, "scout_backend": scout_backend},
        },
        {
            "name": "reference_frame_id_recorded",
            "passed": bool(reference_frame_id),
            "evidence": {"reference_frame_id": reference_frame_id},
        },
        {
            "name": "cpu_crosscheck_measured_frames",
            "passed": bool(cpu_rows),
            "evidence": {"measured_frame_count": len(cpu_rows)},
        },
        {
            "name": "selected_reference_present_in_cpu_crosscheck",
            "passed": selected_cpu_row is not None,
            "evidence": {"reference_frame_id": reference_frame_id, "present": selected_cpu_row is not None},
        },
        {
            "name": "selected_reference_cpu_star_ratio",
            "passed": not enabled or star_ratio >= float(min_cpu_star_ratio),
            "evidence": {
                "selected_cpu_star_count": selected_star_count,
                "cpu_reference_star_count": cpu_reference_star_count,
                "star_ratio": star_ratio,
                "min_cpu_star_ratio": float(min_cpu_star_ratio),
            },
        },
        {
            "name": "selected_reference_cpu_rank_fraction",
            "passed": not enabled
            or (rank_fraction is not None and rank_fraction <= float(max_cpu_rank_fraction)),
            "evidence": {
                "selected_cpu_rank": selected_rank,
                "cpu_measured_frame_count": len(ranked),
                "rank_fraction": rank_fraction,
                "max_cpu_rank_fraction": float(max_cpu_rank_fraction),
            },
        },
    ]
    cuda_health_available, cuda_health_reason = _cuda_reference_health_available()
    sample_input_cache: dict[Any, Any] | None = (
        {"_stats": _sample_cache_stats({})} if cuda_health_available else None
    )
    if sample_input_cache is not None:
        sample_input_cache["_stats"]["availability_reason"] = cuda_health_reason
    calibrated = _calibrated_crosscheck(
        plan,
        scout,
        master_cache_dir=master_cache_dir,
        flat_floor=flat_floor,
        reference_frame_id=reference_frame_id,
        min_star_ratio=float(calibrated_min_star_ratio),
        max_rank_fraction=float(calibrated_max_rank_fraction),
        enabled=enabled,
        sample_input_cache=sample_input_cache,
    )
    cuda_calibrated = _cuda_calibrated_crosscheck(
        plan,
        scout,
        master_cache_dir=master_cache_dir,
        flat_floor=flat_floor,
        reference_frame_id=reference_frame_id,
        min_star_ratio=float(cuda_calibrated_min_star_ratio),
        max_rank_fraction=float(cuda_calibrated_max_rank_fraction),
        sample_input_cache=sample_input_cache,
    )
    calibrated_checks = calibrated.get("checks") if isinstance(calibrated.get("checks"), list) else []
    effective_checks = list(checks)
    if calibrated.get("available"):
        effective_checks.extend(item for item in calibrated_checks if isinstance(item, dict))
    raw_passed = all(item["passed"] for item in effective_checks)
    passed = raw_passed or action == "warn"
    status = "disabled" if action == "off" else ("passed" if raw_passed else "warning" if action == "warn" else "failed")
    failed_checks = [item["name"] for item in effective_checks if not item["passed"]]
    return {
        "schema_version": 1,
        "artifact_type": "resident_reference_health",
        "created_at": created_at,
        "run_dir": str(run),
        "scout_path": str(scout_path),
        "scout_backend": scout_backend,
        "health_action_backend": health_action_backend,
        "requested_action": str(requested_action or DEFAULT_RESIDENT_REFERENCE_HEALTH_GATE).lower(),
        "effective_action": action,
        "status": status,
        "passed": passed,
        "blocking": action == "fail" and not raw_passed,
        "thresholds": {
            "min_cpu_star_ratio": float(min_cpu_star_ratio),
            "max_cpu_rank_fraction": float(max_cpu_rank_fraction),
            "calibrated_min_star_ratio": float(calibrated_min_star_ratio),
            "calibrated_max_rank_fraction": float(calibrated_max_rank_fraction),
            "cuda_calibrated_min_star_ratio": float(cuda_calibrated_min_star_ratio),
            "cuda_calibrated_max_rank_fraction": float(cuda_calibrated_max_rank_fraction),
        },
        "summary": {
            "reference_frame_id": reference_frame_id,
            "cpu_reference_frame_id": cpu_reference_frame_id,
            "selected_cpu_rank": selected_rank,
            "cpu_measured_frame_count": len(ranked),
            "selected_cpu_star_count": selected_star_count,
            "cpu_reference_star_count": cpu_reference_star_count,
            "selected_cpu_star_ratio": star_ratio,
            "selected_cpu_rank_fraction": rank_fraction,
            "cpu_crosscheck_reused": bool(cpu_crosscheck_reuse.get("used")),
            "calibrated_available": bool(calibrated.get("available")),
            "calibrated_reference_frame_id": (
                calibrated.get("summary", {}).get("calibrated_reference_frame_id")
                if isinstance(calibrated.get("summary"), dict)
                else None
            ),
            "selected_calibrated_star_ratio": (
                calibrated.get("summary", {}).get("selected_calibrated_star_ratio")
                if isinstance(calibrated.get("summary"), dict)
                else None
            ),
            "selected_calibrated_rank_fraction": (
                calibrated.get("summary", {}).get("selected_calibrated_rank_fraction")
                if isinstance(calibrated.get("summary"), dict)
                else None
            ),
            "cuda_calibrated_available": bool(cuda_calibrated.get("available")),
            "sample_input_cache_enabled": bool(sample_input_cache is not None),
            "sample_input_cache_hits": (
                _sample_cache_stats(sample_input_cache).get("hits")
                if sample_input_cache is not None
                else 0
            ),
            "sample_input_cache_misses": (
                _sample_cache_stats(sample_input_cache).get("misses")
                if sample_input_cache is not None
                else 0
            ),
            "sample_input_cache_stored_bytes": (
                _sample_cache_stats(sample_input_cache).get("stored_bytes")
                if sample_input_cache is not None
                else 0
            ),
            "cuda_calibrated_reference_frame_id": (
                cuda_calibrated.get("summary", {}).get("cuda_calibrated_reference_frame_id")
                if isinstance(cuda_calibrated.get("summary"), dict)
                else None
            ),
            "selected_cuda_calibrated_star_ratio": (
                cuda_calibrated.get("summary", {}).get("selected_cuda_calibrated_star_ratio")
                if isinstance(cuda_calibrated.get("summary"), dict)
                else None
            ),
            "selected_cuda_calibrated_rank_fraction": (
                cuda_calibrated.get("summary", {}).get("selected_cuda_calibrated_rank_fraction")
                if isinstance(cuda_calibrated.get("summary"), dict)
                else None
            ),
        },
        "cpu_crosscheck": {
            "artifact_type": cpu_crosscheck.get("artifact_type"),
            "catalog_backend": cpu_crosscheck.get("catalog_backend"),
            "reference_frame_id": cpu_reference_frame_id,
            "dominant_orientation_key": cpu_crosscheck.get("dominant_orientation_key"),
            "orientation_constraint_applied": cpu_crosscheck.get("orientation_constraint_applied"),
            "measured_frame_count": len(cpu_rows),
            "reuse": cpu_crosscheck_reuse,
            "top_reference_candidates": [
                {
                    "frame_id": row.get("frame_id"),
                    "star_count": row.get("star_count"),
                    "quality_score": row.get("quality_score"),
                    "fwhm_px": row.get("fwhm_px"),
                    "eccentricity": row.get("eccentricity"),
                    "background_rms": row.get("background_rms"),
                }
                for row in ranked[:10]
            ],
        },
        "calibrated_crosscheck": calibrated,
        "cuda_calibrated_crosscheck": cuda_calibrated,
        "checks": checks,
        "effective_checks": effective_checks,
        "failed_checks": failed_checks,
        "recommended_actions": [
            "use the default CPU resident reference scout",
            "choose an explicit --reference-frame-id that passes CPU cross-check",
            "keep --resident-reference-health-gate warn/off only for diagnostic CUDA scout experiments",
        ],
        "clean_room_note": (
            "Project-defined cross-check over GLASS raw-light scout artifacts and GLASS CPU star metrics; "
            "it does not inspect external implementation source."
        ),
    }
