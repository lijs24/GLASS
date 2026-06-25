from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

from glass.cpu.metrics import combined_quality_weight, summarize_stars
from glass.cpu.star_detect import detect_stars, robust_background
from glass.io.fits_io import FitsImageReader
from glass.io.json_io import read_json, write_json
from glass.models import FrameQuality, now_iso, to_jsonable


DEFAULT_REFERENCE_SCOUT_SAMPLE_STRIDE = 8
DEFAULT_REFERENCE_SCOUT_SAMPLE_SIDE = 768
DEFAULT_REFERENCE_SCOUT_MAX_FRAMES = 64
DEFAULT_REFERENCE_SCOUT_THRESHOLD_SIGMA = 5.0
DEFAULT_REFERENCE_SCOUT_MAX_STARS = 300
DEFAULT_REFERENCE_SCOUT_BACKEND = "auto"
AUTO_REFERENCE_SCOUT_GUARD_MIN_CPU_STAR_RATIO = 0.85
AUTO_REFERENCE_SCOUT_GUARD_MAX_CPU_RANK_FRACTION = 0.25


def _plan_light_frames(plan: dict[str, Any]) -> list[dict[str, Any]]:
    frames = [dict(frame) for frame in plan.get("frames", []) if isinstance(frame, dict)]
    by_id = {str(frame.get("id")): frame for frame in frames if frame.get("id") is not None}
    ordered: list[dict[str, Any]] = []
    seen: set[str] = set()
    for light_plan in plan.get("light_plans", []):
        if not isinstance(light_plan, dict):
            continue
        for frame_id in light_plan.get("frames", []):
            key = str(frame_id)
            frame = by_id.get(key)
            if frame is not None and key not in seen:
                ordered.append(frame)
                seen.add(key)
    if ordered:
        return ordered
    return [frame for frame in frames if str(frame.get("frame_type", "")).lower() == "light"]


def _frame_header_value(frame: dict[str, Any], *keys: str) -> Any | None:
    summary = frame.get("header_summary", {})
    if isinstance(summary, dict):
        for key in keys:
            for candidate in (key, key.upper(), key.lower()):
                if candidate in summary:
                    return summary[candidate]
    for key in keys:
        for candidate in (key, key.upper(), key.lower()):
            if candidate in frame:
                return frame[candidate]
    return None


def _normal_orientation_text(value: Any | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    if not text:
        return None
    if text in {"e", "east", "pier east", "east side", "east-of-pier"}:
        return "east"
    if text in {"w", "west", "pier west", "west side", "west-of-pier"}:
        return "west"
    return text.replace(" ", "_")


def _rotation_bucket(value: Any | None) -> str | None:
    if value is None:
        return None
    try:
        return f"{round(float(value), 1):.1f}"
    except (TypeError, ValueError):
        text = str(value).strip()
        return text or None


def _frame_orientation_key(frame: dict[str, Any]) -> tuple[str, str]:
    pierside = _normal_orientation_text(_frame_header_value(frame, "PIERSIDE", "PIER_SIDE"))
    rotation = _rotation_bucket(_frame_header_value(frame, "OBJCTROT", "ROTANGLE", "CROTA2"))
    return (pierside or "unknown", rotation or "unknown")


def _dominant_orientation_key(light_frames: list[dict[str, Any]]) -> tuple[str, str] | None:
    counts = Counter(_frame_orientation_key(frame) for frame in light_frames)
    known_counts = Counter({key: count for key, count in counts.items() if key != ("unknown", "unknown")})
    if not known_counts:
        return None
    return known_counts.most_common(1)[0][0]


def _reference_selection_key(row: dict[str, Any]) -> tuple[int, float, float, float, float]:
    return (
        int(row.get("star_count") or 0),
        float(row.get("quality_score") or row.get("weight") or 0.0),
        -float(row.get("fwhm_px") if row.get("fwhm_px") is not None else 999.0),
        -float(row.get("eccentricity") if row.get("eccentricity") is not None else 1.0),
        -float(row.get("background_rms") or 0.0),
    )


def _sampled_light_frames(light_frames: list[dict[str, Any]], max_frames: int) -> list[dict[str, Any]]:
    limit = int(max_frames)
    if limit <= 0 or len(light_frames) <= limit:
        return light_frames
    if limit == 1:
        return [light_frames[len(light_frames) // 2]]
    indices = np.linspace(0, len(light_frames) - 1, num=limit, dtype=np.int64)
    selected: list[dict[str, Any]] = []
    seen: set[int] = set()
    for index in indices:
        i = int(index)
        if i not in seen:
            selected.append(light_frames[i])
            seen.add(i)
    return selected


def _cuda_catalog_available() -> tuple[bool, str]:
    try:
        import glass_cuda
    except Exception as exc:
        return False, f"import_failed:{type(exc).__name__}: {exc}"
    if not getattr(glass_cuda, "cuda_available", lambda: False)():
        return False, "cuda_unavailable"
    if not hasattr(glass_cuda, "star_grid_top_nms_candidates_f32"):
        return False, "missing_star_grid_top_nms_candidates_f32"
    return True, "available"


def _resolve_catalog_backend(requested: str) -> tuple[str, dict[str, Any]]:
    mode = str(requested or DEFAULT_REFERENCE_SCOUT_BACKEND)
    if mode not in {"auto", "cpu", "cuda"}:
        raise ValueError("resident reference scout backend must be auto, cpu, or cuda")
    available, reason = _cuda_catalog_available()
    if mode == "cpu":
        return "cpu", {"requested": mode, "effective": "cpu", "cuda_status": reason}
    if mode == "cuda":
        if not available:
            raise RuntimeError(f"resident reference scout CUDA backend requested but unavailable: {reason}")
        return "cuda", {"requested": mode, "effective": "cuda", "cuda_status": reason}
    if available:
        return (
            "cuda",
            {
                "requested": mode,
                "effective": "cuda",
                "cuda_status": reason,
                "reason": "cuda_reference_scout_auto_candidate_pending_cpu_guard",
                "fallback": "cpu",
            },
        )
    return "cpu", {"requested": mode, "effective": "cpu", "cuda_status": reason}


def _cuda_catalog_metrics(
    sample: np.ndarray,
    *,
    median: float,
    noise: float,
    threshold_sigma: float,
    max_stars: int,
) -> tuple[dict[str, float | None], float, dict[str, float], int, dict[str, Any]]:
    import glass_cuda

    threshold = float(median) + float(threshold_sigma) * max(float(noise), 1.0e-6)
    height, width = sample.shape
    grid_cols = max(1, min(16, int(np.ceil(width / 64.0))))
    grid_rows = max(1, min(12, int(np.ceil(height / 64.0))))
    min_separation = max(2.0, float(min(height, width)) / 32.0)
    catalog = glass_cuda.star_grid_top_nms_candidates_f32(
        sample,
        threshold,
        grid_cols,
        grid_rows,
        4,
        int(max_stars),
        min_separation,
    )
    stored_count = int(catalog.get("stored_count") or 0)
    flux = np.asarray(catalog.get("flux", []), dtype=np.float32)
    peak_snr_values = np.maximum(flux - np.float32(median), 0.0) / np.float32(max(float(noise), 1.0e-6))
    finite_snr = peak_snr_values[np.isfinite(peak_snr_values)]
    peak_snr = float(np.median(finite_snr)) if finite_snr.size else 0.0
    star_metrics = {
        "fwhm_median_px": None,
        "fwhm_iqr_px": None,
        "eccentricity_median": None,
        "star_snr_median": peak_snr,
        "star_flux_median": None if flux.size == 0 else float(np.median(flux)),
    }
    weight, components = combined_quality_weight(
        star_count=stored_count,
        star_snr=peak_snr,
        fwhm_px=None,
        eccentricity=None,
        background_rms=float(noise),
        saturation_fraction=0.0,
    )
    diagnostics = {
        "catalog_model": "cuda_grid_top_nms_candidates_f32",
        "threshold": threshold,
        "threshold_sigma": float(threshold_sigma),
        "grid_cols": grid_cols,
        "grid_rows": grid_rows,
        "candidates_per_cell": 4,
        "max_output_candidates": int(max_stars),
        "min_separation_px": min_separation,
        "detected_count": int(catalog.get("count") or 0),
        "stored_count": stored_count,
        "catalog_sort_mode": str(catalog.get("catalog_sort_mode", "unavailable")),
        "catalog_topk_mode": str(catalog.get("catalog_topk_mode", "unavailable")),
    }
    return star_metrics, weight, components, stored_count, diagnostics


def _cpu_star_metrics(
    sample: np.ndarray,
    *,
    median: float,
    noise: float,
    threshold_sigma: float,
    max_stars: int,
) -> tuple[dict[str, float | None], float, dict[str, float], int, dict[str, Any]]:
    stars = detect_stars(
        sample,
        threshold_sigma=float(threshold_sigma),
        max_stars=int(max_stars),
        background=median,
        noise=noise,
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
        background_rms=float(noise),
        saturation_fraction=0.0,
    )
    diagnostics = {
        "catalog_model": "cpu_robust_local_maximum_moments_v1",
        "detected_count": len(stars),
        "stored_count": len(stars),
    }
    return star_metrics, weight, components, len(stars), diagnostics


def _scout_frame_quality(
    frame: dict[str, Any],
    *,
    sample_stride: int,
    sample_side: int,
    threshold_sigma: float,
    max_stars: int,
    catalog_backend: str,
) -> dict[str, Any]:
    path = Path(str(frame["path"]))
    warnings: list[str] = []
    with FitsImageReader(path) as reader:
        side = max(1, int(sample_side))
        crop_width = min(int(reader.width), side)
        crop_height = min(int(reader.height), side)
        x0 = max(0, (int(reader.width) - crop_width) // 2)
        y0 = max(0, (int(reader.height) - crop_height) // 2)
        crop = reader.read_tile(y0, y0 + crop_height, x0, x0 + crop_width)
        sample = crop[:: max(1, int(sample_stride)), :: max(1, int(sample_stride))]
        full_shape = [int(reader.height), int(reader.width)]
    finite = sample[np.isfinite(sample)]
    stats = robust_background(sample)
    mean = float(np.mean(finite, dtype=np.float64)) if finite.size else 0.0
    if catalog_backend == "cuda":
        star_metrics, weight, components, star_count, catalog_diagnostics = _cuda_catalog_metrics(
            sample,
            median=stats.median,
            noise=stats.noise,
            threshold_sigma=threshold_sigma,
            max_stars=max_stars,
        )
        star_detector = "cuda_grid_top_nms_candidates_f32_sampled_raw"
        weight_source = "resident_reference_scout_cuda_catalog_raw_sample_v1"
    else:
        star_metrics, weight, components, star_count, catalog_diagnostics = _cpu_star_metrics(
            sample,
            median=stats.median,
            noise=stats.noise,
            threshold_sigma=threshold_sigma,
            max_stars=max_stars,
        )
        star_detector = "robust_local_maximum_moments_v1_sampled_raw"
        weight_source = "resident_reference_scout_raw_sample_v1"
    snr = float(star_metrics["star_snr_median"] or 0.0)
    if star_count <= 0:
        warnings.append("no stars detected in sampled raw light")
    quality = FrameQuality(
        frame_id=str(frame.get("id")),
        filter=frame.get("filter"),
        background_median=stats.median,
        background_rms=stats.rms,
        star_count=star_count,
        fwhm_px=star_metrics["fwhm_median_px"],
        eccentricity=star_metrics["eccentricity_median"],
        snr=snr,
        weight=weight,
        warnings=warnings,
        background_mean=mean,
        background_mad=stats.mad,
        noise_mad=stats.noise,
        saturation_fraction=0.0,
        quality_score=weight,
        weight_source=weight_source,
        weight_components=components,
        star_metrics=star_metrics,
    )
    row = to_jsonable(quality)
    row.update(
        {
            "metric_source": "resident_reference_scout_raw_light_sample_v1",
            "source_path": str(path),
            "orientation_key": list(_frame_orientation_key(frame)),
            "sample_stride": int(sample_stride),
            "sample_side": int(sample_side),
            "sample_origin_xy": [int(x0), int(y0)],
            "sample_shape": [int(sample.shape[0]), int(sample.shape[1])],
            "full_shape": full_shape,
            "sample_pixel_count": int(finite.size),
            "reference_candidate": bool(star_count > 0),
            "star_detector": star_detector,
            "catalog_backend": catalog_backend,
            "catalog_diagnostics": catalog_diagnostics,
        }
    )
    return row


def _collect_scout_rows(
    scouted_frames: list[dict[str, Any]],
    *,
    sample_stride: int,
    sample_side: int,
    threshold_sigma: float,
    max_stars: int,
    catalog_backend: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    row_errors: list[dict[str, Any]] = []
    for frame in scouted_frames:
        try:
            rows.append(
                _scout_frame_quality(
                    frame,
                    sample_stride=max(1, int(sample_stride)),
                    sample_side=max(1, int(sample_side)),
                    threshold_sigma=float(threshold_sigma),
                    max_stars=max(1, int(max_stars)),
                    catalog_backend=catalog_backend,
                )
            )
        except Exception as exc:
            row_errors.append(
                {
                    "frame_id": str(frame.get("id")),
                    "path": str(frame.get("path")),
                    "error": str(exc),
                }
            )
    return rows, row_errors


def _select_reference(
    rows: list[dict[str, Any]],
    *,
    dominant_orientation: tuple[str, str] | None,
) -> dict[str, Any]:
    candidates = [row for row in rows if row.get("reference_candidate")]
    fallback_used = False
    if not candidates:
        candidates = rows
        fallback_used = True
    orientation_constraint_applied = False
    orientation_constraint_fallback = False
    if dominant_orientation is not None and candidates:
        orientation_rows = [
            row for row in candidates if tuple(row.get("orientation_key") or []) == tuple(dominant_orientation)
        ]
        if orientation_rows:
            candidates = orientation_rows
            orientation_constraint_applied = True
        else:
            orientation_constraint_fallback = True
    if not candidates:
        raise ValueError("resident reference scout could not read any light frame")

    ranked = sorted(candidates, key=_reference_selection_key, reverse=True)
    return {
        "reference": ranked[0],
        "ranked_candidates": ranked,
        "reference_selection_fallback": fallback_used,
        "orientation_constraint_applied": orientation_constraint_applied,
        "orientation_constraint_fallback": orientation_constraint_fallback,
    }


def _guard_top_candidates(rows: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for rank, row in enumerate(rows[: max(0, int(limit))], start=1):
        result.append(
            {
                "rank": rank,
                "frame_id": row.get("frame_id"),
                "star_count": row.get("star_count"),
                "quality_score": row.get("quality_score"),
                "background_rms": row.get("background_rms"),
            }
        )
    return result


def _auto_cuda_cpu_guard(
    *,
    cuda_selection: dict[str, Any],
    cpu_selection: dict[str, Any],
) -> dict[str, Any]:
    cuda_reference = cuda_selection["reference"]
    cpu_reference = cpu_selection["reference"]
    cpu_ranked = list(cpu_selection.get("ranked_candidates") or [])
    cuda_ranked = list(cuda_selection.get("ranked_candidates") or [])
    cuda_reference_id = str(cuda_reference.get("frame_id") or "")
    selected_cpu_row = next((row for row in cpu_ranked if str(row.get("frame_id") or "") == cuda_reference_id), None)
    selected_rank = cpu_ranked.index(selected_cpu_row) + 1 if selected_cpu_row in cpu_ranked else None
    rank_fraction = (
        (float(selected_rank) - 1.0) / float(max(len(cpu_ranked) - 1, 1))
        if selected_rank is not None and cpu_ranked
        else None
    )
    selected_star_count = int(selected_cpu_row.get("star_count") or 0) if selected_cpu_row is not None else 0
    cpu_reference_star_count = int(cpu_reference.get("star_count") or 0)
    star_ratio = (
        float(selected_star_count) / float(cpu_reference_star_count)
        if cpu_reference_star_count > 0
        else (1.0 if selected_star_count > 0 else 0.0)
    )
    passed = (
        selected_cpu_row is not None
        and star_ratio >= AUTO_REFERENCE_SCOUT_GUARD_MIN_CPU_STAR_RATIO
        and rank_fraction is not None
        and rank_fraction <= AUTO_REFERENCE_SCOUT_GUARD_MAX_CPU_RANK_FRACTION
    )
    return {
        "status": "passed" if passed else "fallback_to_cpu",
        "passed": passed,
        "cuda_reference_frame_id": cuda_reference_id,
        "cpu_reference_frame_id": str(cpu_reference.get("frame_id") or ""),
        "selected_cpu_rank": selected_rank,
        "cpu_measured_frame_count": len(cpu_ranked),
        "selected_cpu_star_count": selected_star_count,
        "cpu_reference_star_count": cpu_reference_star_count,
        "selected_cpu_star_ratio": star_ratio,
        "selected_cpu_rank_fraction": rank_fraction,
        "min_cpu_star_ratio": AUTO_REFERENCE_SCOUT_GUARD_MIN_CPU_STAR_RATIO,
        "max_cpu_rank_fraction": AUTO_REFERENCE_SCOUT_GUARD_MAX_CPU_RANK_FRACTION,
        "cuda_top_candidates": _guard_top_candidates(cuda_ranked),
        "cpu_top_candidates": _guard_top_candidates(cpu_ranked),
    }


def build_resident_reference_scout(
    plan_path: str | Path,
    run_dir: str | Path,
    *,
    sample_stride: int = DEFAULT_REFERENCE_SCOUT_SAMPLE_STRIDE,
    sample_side: int = DEFAULT_REFERENCE_SCOUT_SAMPLE_SIDE,
    max_frames: int = DEFAULT_REFERENCE_SCOUT_MAX_FRAMES,
    threshold_sigma: float = DEFAULT_REFERENCE_SCOUT_THRESHOLD_SIGMA,
    max_stars: int = DEFAULT_REFERENCE_SCOUT_MAX_STARS,
    catalog_backend: str = DEFAULT_REFERENCE_SCOUT_BACKEND,
) -> dict[str, Any]:
    plan = read_json(plan_path)
    if not isinstance(plan, dict):
        raise ValueError(f"processing plan is not a JSON object: {plan_path}")
    light_frames = _plan_light_frames(plan)
    if not light_frames:
        raise ValueError("resident reference scout requires at least one light frame in the processing plan")
    dominant_orientation = _dominant_orientation_key(light_frames)
    scouted_frames = _sampled_light_frames(light_frames, max_frames=max_frames)
    backend, backend_resolution = _resolve_catalog_backend(catalog_backend)
    rows, row_errors = _collect_scout_rows(
        scouted_frames,
        sample_stride=max(1, int(sample_stride)),
        sample_side=max(1, int(sample_side)),
        threshold_sigma=float(threshold_sigma),
        max_stars=max(1, int(max_stars)),
        catalog_backend=backend,
    )
    auto_guard: dict[str, Any] | None = None
    try:
        selection = _select_reference(rows, dominant_orientation=dominant_orientation)
    except ValueError:
        if str(catalog_backend or DEFAULT_REFERENCE_SCOUT_BACKEND) != "auto" or backend != "cuda":
            raise
        cpu_rows, cpu_errors = _collect_scout_rows(
            scouted_frames,
            sample_stride=max(1, int(sample_stride)),
            sample_side=max(1, int(sample_side)),
            threshold_sigma=float(threshold_sigma),
            max_stars=max(1, int(max_stars)),
            catalog_backend="cpu",
        )
        selection = _select_reference(cpu_rows, dominant_orientation=dominant_orientation)
        auto_guard = {
            "status": "cuda_candidate_unavailable",
            "passed": False,
            "cuda_error_count": len(row_errors),
            "cpu_error_count": len(cpu_errors),
            "cpu_reference_frame_id": str(selection["reference"].get("frame_id") or ""),
        }
        backend = "cpu"
        rows = cpu_rows
        row_errors = cpu_errors
        backend_resolution = {
            **backend_resolution,
            "effective": "cpu",
            "attempted": "cuda",
            "reason": "cuda_reference_scout_auto_cuda_candidate_failed_cpu_fallback",
        }
    if str(catalog_backend or DEFAULT_REFERENCE_SCOUT_BACKEND) == "auto" and backend == "cuda":
        cpu_rows, cpu_errors = _collect_scout_rows(
            scouted_frames,
            sample_stride=max(1, int(sample_stride)),
            sample_side=max(1, int(sample_side)),
            threshold_sigma=float(threshold_sigma),
            max_stars=max(1, int(max_stars)),
            catalog_backend="cpu",
        )
        try:
            cpu_selection = _select_reference(cpu_rows, dominant_orientation=dominant_orientation)
        except ValueError:
            auto_guard = {
                "status": "cpu_guard_unavailable",
                "passed": False,
                "cuda_reference_frame_id": str(selection["reference"].get("frame_id") or ""),
                "cpu_error_count": len(cpu_errors),
            }
        else:
            auto_guard = _auto_cuda_cpu_guard(cuda_selection=selection, cpu_selection=cpu_selection)
            if not auto_guard["passed"]:
                backend = "cpu"
                rows = cpu_rows
                row_errors = cpu_errors
                selection = cpu_selection
                backend_resolution = {
                    **backend_resolution,
                    "effective": "cpu",
                    "attempted": "cuda",
                    "reason": "cuda_reference_scout_auto_cpu_guard_fallback",
                }
            else:
                backend_resolution = {
                    **backend_resolution,
                    "effective": "cuda",
                    "attempted": "cuda",
                    "reason": "cuda_reference_scout_auto_cpu_guard_passed",
                }
    if auto_guard is not None:
        backend_resolution = {**backend_resolution, "cpu_guard": auto_guard}

    reference = selection["reference"]
    fallback_used = bool(selection["reference_selection_fallback"])
    orientation_constraint_applied = bool(selection["orientation_constraint_applied"])
    orientation_constraint_fallback = bool(selection["orientation_constraint_fallback"])
    created_at = now_iso()
    payload = {
        "schema_version": 1,
        "artifact_type": "resident_reference_scout",
        "created_at": created_at,
        "metric_source": "resident_reference_scout_raw_light_sample_v1",
        "sample_stride": max(1, int(sample_stride)),
        "sample_side": max(1, int(sample_side)),
        "max_frames": int(max_frames),
        "threshold_sigma": float(threshold_sigma),
        "max_stars": max(1, int(max_stars)),
        "catalog_backend_requested": str(catalog_backend),
        "catalog_backend": backend,
        "catalog_backend_resolution": backend_resolution,
        "frame_count": len(light_frames),
        "scouted_frame_count": len(scouted_frames),
        "dominant_orientation_key": None if dominant_orientation is None else list(dominant_orientation),
        "orientation_constraint_applied": orientation_constraint_applied,
        "orientation_constraint_fallback": orientation_constraint_fallback,
        "measured_frame_count": len(rows),
        "error_count": len(row_errors),
        "frame_quality": rows,
        "errors": row_errors,
        "reference_frame_id": str(reference["frame_id"]),
        "reference_selection": (
            "raw sampled light scout; prefer the dominant PIERSIDE/rotation orientation when known, "
            "then max star_count, max combined sample quality, min FWHM/eccentricity/background_rms"
        ),
        "reference_selection_fallback": fallback_used,
        "clean_room_note": (
            "Project-defined raw-light reference scout using GLASS FITS reading and star metrics; "
            "it does not inspect external implementation source."
        ),
    }
    return payload


def write_resident_reference_scout(
    plan_path: str | Path,
    run_dir: str | Path,
    *,
    sample_stride: int = DEFAULT_REFERENCE_SCOUT_SAMPLE_STRIDE,
    sample_side: int = DEFAULT_REFERENCE_SCOUT_SAMPLE_SIDE,
    max_frames: int = DEFAULT_REFERENCE_SCOUT_MAX_FRAMES,
    threshold_sigma: float = DEFAULT_REFERENCE_SCOUT_THRESHOLD_SIGMA,
    max_stars: int = DEFAULT_REFERENCE_SCOUT_MAX_STARS,
    catalog_backend: str = DEFAULT_REFERENCE_SCOUT_BACKEND,
) -> Path:
    run = Path(run_dir)
    payload = build_resident_reference_scout(
        plan_path,
        run,
        sample_stride=sample_stride,
        sample_side=sample_side,
        max_frames=max_frames,
        threshold_sigma=threshold_sigma,
        max_stars=max_stars,
        catalog_backend=catalog_backend,
    )
    scout_path = run / "resident_reference_scout.json"
    quality_path = run / "frame_quality.json"
    write_json(scout_path, payload)
    quality_payload = dict(payload)
    quality_payload["artifact_type"] = "frame_quality"
    quality_payload["metric_source"] = "resident_reference_scout_raw_light_sample_v1"
    quality_payload["source_artifact"] = str(scout_path)
    write_json(quality_path, quality_payload)
    return scout_path
