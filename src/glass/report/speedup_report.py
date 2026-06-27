from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from glass.io.json_io import write_json


def _read_json_lenient(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def _first_output(integration: dict[str, Any]) -> dict[str, Any]:
    outputs = integration.get("outputs") or []
    return outputs[0] if outputs and isinstance(outputs[0], dict) else {}


def _first_artifact(resident: dict[str, Any]) -> dict[str, Any]:
    artifacts = resident.get("artifacts") or []
    return artifacts[0] if artifacts and isinstance(artifacts[0], dict) else {}


def _selected_keys(payload: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    return {key: payload.get(key) for key in keys if key in payload}


def _weight_counts(integration: dict[str, Any]) -> dict[str, int]:
    weights = integration.get("frame_weights") or {}
    if not isinstance(weights, dict):
        return {"weighted_frame_count": 0, "zero_weight_frame_count": 0}
    active = 0
    zero = 0
    for value in weights.values():
        try:
            weight = float(value)
        except (TypeError, ValueError):
            continue
        if weight > 0.0:
            active += 1
        else:
            zero += 1
    return {"weighted_frame_count": active, "zero_weight_frame_count": zero}


def _load_glass_run(run: str | Path) -> dict[str, Any]:
    root = Path(run)
    timing = _read_json_lenient(root / "run_timing.json")
    integration_path = root / "integration_results.json"
    integration = _read_json_lenient(integration_path) if integration_path.exists() else {}
    resident_path = root / "resident_artifacts.json"
    resident = _read_json_lenient(resident_path) if resident_path.exists() else {}
    resident_master_cache_path = root / "resident_master_cache.json"
    resident_master_cache = (
        _read_json_lenient(resident_master_cache_path) if resident_master_cache_path.exists() else {}
    )
    output = _first_output(integration)
    artifact = _first_artifact(resident)
    memory_estimate = artifact.get("memory_estimate") if isinstance(artifact.get("memory_estimate"), dict) else {}
    artifact_cache = (
        artifact.get("resident_master_cache") if isinstance(artifact.get("resident_master_cache"), dict) else {}
    )
    cache_summary = (
        resident_master_cache.get("summary")
        if isinstance(resident_master_cache.get("summary"), dict)
        else artifact_cache.get("summary")
        if isinstance(artifact_cache.get("summary"), dict)
        else {}
    )
    timing_s = artifact.get("timing_s") if isinstance(artifact.get("timing_s"), dict) else {}
    io_pipeline = (
        artifact.get("resident_io_pipeline") if isinstance(artifact.get("resident_io_pipeline"), dict) else {}
    )
    weight_counts = _weight_counts(integration)
    elapsed = timing.get("total_elapsed_s")
    if elapsed is None:
        elapsed = sum(float(stage.get("elapsed_s") or 0.0) for stage in timing.get("stages", []))
    stages = []
    for stage in timing.get("stages", []):
        if not isinstance(stage, dict):
            continue
        stages.append(
            {
                "stage": stage.get("stage"),
                "elapsed_s": stage.get("elapsed_s"),
                "status": stage.get("status"),
            }
        )
    return {
        "run": str(root),
        "elapsed_s": float(elapsed),
        "command": timing.get("command"),
        "backend": output.get("backend") or timing.get("backend"),
        "memory_mode": output.get("memory_mode") or timing.get("memory_mode"),
        "frame_count": output.get("frame_count"),
        **weight_counts,
        "master_path": output.get("master_path"),
        "weighting": integration.get("weighting") or output.get("weighting"),
        "rejection": integration.get("rejection") or output.get("rejection"),
        "resident_device": (resident.get("device") or {}).get("name"),
        "resident_estimated_peak_gib": output.get("estimated_peak_gib")
        or memory_estimate.get("estimated_peak_gib"),
        "resident_master_cache": _selected_keys(
            cache_summary,
            ["cache_hit_count", "cache_miss_count", "cache_scope_counts", "set_count", "total_required_bytes"],
        ),
        "resident_io": _selected_keys(
            io_pipeline,
            [
                "fits_read_mode_effective",
                "fits_header_spec_cache_frame_count",
                "fits_header_spec_cache_hit_count",
                "prefetch_frames",
                "prefetch_workers",
                "calibration_fetch_batch_frames",
                "calibration_fetch_batch_limit_source",
            ],
        ),
        "resident_timing_s": _selected_keys(
            timing_s,
            [
                "light_read_upload_calibrate",
                "light_read_wait_wall",
                "light_read_worker_cumulative",
                "light_read_overlap_saved",
                "resident_registration_warp",
                "resident_integration",
                "output_write",
                "master_build_or_load",
                "resident_local_normalization",
            ],
        ),
        "run_stages": stages,
    }


def _load_wbpp_result(path: str | Path) -> dict[str, Any]:
    payload = _read_json_lenient(path)
    return {
        "result_path": str(path),
        "elapsed_s": float(payload["elapsed_s"]),
        "dataset": payload.get("dataset"),
        "reported_wbpp_time": payload.get("reported_wbpp_time"),
        "output_dir": payload.get("output_dir"),
        "final_master_files": payload.get("final_master_files", []),
        "clean_room_note": payload.get("clean_room_note"),
    }


def _load_wbpp_history(path: str | Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    payload = _read_json_lenient(path)
    time_payload = payload.get("time") if isinstance(payload.get("time"), dict) else {}
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    parameters = payload.get("parameters") if isinstance(payload.get("parameters"), dict) else {}
    span = time_payload.get("span")
    return {
        "history_path": str(path),
        "history_class": payload.get("history_class"),
        "elapsed_s": float(span) if span is not None else None,
        "target_count": summary.get("target_count"),
        "accepted_count": summary.get("accepted_count"),
        "failed_count": summary.get("failed_count"),
        "failed_target_image_names": summary.get("failed_target_image_names", []),
        "reference_image": payload.get("reference_image") or (payload.get("source") if payload.get("source") else None),
        "parameters": _selected_keys(
            parameters,
            [
                "pixelInterpolation",
                "rejectionAlgorithm",
                "rejectionEnabled",
                "sigmaHigh",
                "sigmaLow",
                "brightThreshold",
                "clampingThreshold",
                "descriptorsPerStar",
            ],
        ),
    }


def _load_compare(path: str | Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    payload = _read_json_lenient(path)
    timing = payload.get("timing", {}) if isinstance(payload.get("timing"), dict) else {}
    region = payload.get("comparison_region", {}) if isinstance(payload.get("comparison_region"), dict) else {}
    return {
        "path": str(path),
        "shape_match": payload.get("shape_match"),
        "rms_diff": payload.get("rms_diff"),
        "abs_diff_p50": payload.get("abs_diff_p50"),
        "abs_diff_p90": payload.get("abs_diff_p90"),
        "abs_diff_p99": payload.get("abs_diff_p99"),
        "abs_diff_p999": payload.get("abs_diff_p999"),
        "relative_rms_diff": payload.get("relative_rms_diff"),
        "coverage_fraction": region.get("coverage_fraction"),
        "compared_pixels": region.get("compared_pixels"),
        "full_frame_rms_diff": (payload.get("full_frame_stats") or {}).get("rms_diff")
        if isinstance(payload.get("full_frame_stats"), dict)
        else None,
        "full_frame_abs_diff_p99": (payload.get("full_frame_stats") or {}).get("abs_diff_p99")
        if isinstance(payload.get("full_frame_stats"), dict)
        else None,
        "compare_speedup_vs_reference": timing.get("speedup_vs_reference"),
    }


def _speedup(reference_s: float | None, glass_s: float | None) -> float | None:
    if reference_s is None or glass_s is None or glass_s <= 0:
        return None
    return reference_s / glass_s


def _stage_timing_comparison(
    glass: dict[str, Any],
    wbpp: dict[str, Any],
    wbpp_history: dict[str, Any] | None,
) -> dict[str, Any]:
    resident = glass.get("resident_timing_s") or {}
    glass_alignment_stack = sum(
        float(resident.get(key) or 0.0)
        for key in ["resident_registration_warp", "resident_local_normalization", "resident_integration"]
    )
    wbpp_history_elapsed = wbpp_history.get("elapsed_s") if wbpp_history else None
    paired = [
        {
            "stage": "total_pipeline_blackbox",
            "glass_s": glass.get("elapsed_s"),
            "wbpp_s": wbpp.get("elapsed_s"),
            "speedup_vs_wbpp": _speedup(wbpp.get("elapsed_s"), glass.get("elapsed_s")),
            "note": "End-to-end command timing for GLASS and user-generated WBPP black-box result.",
        },
        {
            "stage": "alignment_ln_integration_estimate",
            "glass_s": glass_alignment_stack,
            "wbpp_s": wbpp_history_elapsed,
            "speedup_vs_wbpp": _speedup(wbpp_history_elapsed, glass_alignment_stack),
            "note": (
                "GLASS sums resident registration/warp, local normalization, and integration components. "
                "WBPP uses the user-generated FastIntegration ProcessingHistory span when available."
            ),
        },
    ]
    return {
        "glass_run_stages": glass.get("run_stages", []),
        "glass_resident_components_s": resident,
        "wbpp_blackbox_stages": [
            {"stage": "total_pipeline_blackbox", "elapsed_s": wbpp.get("elapsed_s")},
            {
                "stage": "fastintegration_processing_history",
                "elapsed_s": wbpp_history_elapsed,
                "history_class": wbpp_history.get("history_class") if wbpp_history else None,
                "accepted_count": wbpp_history.get("accepted_count") if wbpp_history else None,
                "failed_count": wbpp_history.get("failed_count") if wbpp_history else None,
            },
        ],
        "paired_stage_estimates": paired,
    }


def summarize_wbpp_speedup(
    glass_run: str | Path,
    wbpp_result: str | Path,
    *,
    compare_json: str | Path | None = None,
    wbpp_history: str | Path | None = None,
    min_speedup: float = 1.25,
) -> dict[str, Any]:
    gp = _load_glass_run(glass_run)
    wbpp = _load_wbpp_result(wbpp_result)
    history = _load_wbpp_history(wbpp_history)
    if history is not None:
        wbpp["fastintegration_history"] = history
    speedup = wbpp["elapsed_s"] / gp["elapsed_s"] if gp["elapsed_s"] > 0 else None
    summary = {
        "schema_version": 1,
        "glass": gp,
        "wbpp_blackbox": wbpp,
        "stage_timing_comparison": _stage_timing_comparison(gp, wbpp, history),
        "speedup_vs_wbpp": speedup,
        "glass_faster": speedup is not None and speedup > 1.0,
        "meets_min_speedup": speedup is not None and speedup >= float(min_speedup),
        "min_speedup": float(min_speedup),
        "comparison": _load_compare(compare_json),
        "clean_room": {
            "status": "compliant",
            "note": (
                "This summary uses GLASS artifacts and user-generated PixInsight/WBPP black-box timing/output "
                "metadata only. It does not use PixInsight/WBPP implementation source."
            ),
        },
    }
    return summary


def write_speedup_markdown(path: str | Path, summary: dict[str, Any]) -> None:
    gp = summary["glass"]
    wbpp = summary["wbpp_blackbox"]
    comparison = summary.get("comparison") or {}
    cache = gp.get("resident_master_cache") or {}
    resident_timing = gp.get("resident_timing_s") or {}
    resident_io = gp.get("resident_io") or {}
    stage_timing = summary.get("stage_timing_comparison") or {}
    paired_stages = stage_timing.get("paired_stage_estimates") or []
    wbpp_history = (wbpp.get("fastintegration_history") or {}) if isinstance(wbpp, dict) else {}
    lines = [
        "# GLASS vs WBPP Speedup Summary",
        "",
        f"- GLASS elapsed: {gp['elapsed_s']:.3f} s",
        f"- WBPP elapsed: {wbpp['elapsed_s']:.3f} s",
        f"- Speedup: {summary['speedup_vs_wbpp']:.3f}x",
        f"- Meets threshold ({summary['min_speedup']:.3f}x): {summary['meets_min_speedup']}",
        f"- GLASS backend: {gp.get('backend')}",
        f"- GLASS memory mode: {gp.get('memory_mode')}",
        f"- Planned frame count: {gp.get('frame_count')}",
        f"- Active weighted frames: {gp.get('weighted_frame_count')}",
        f"- Zero-weight frames: {gp.get('zero_weight_frame_count')}",
        f"- Resident device: {gp.get('resident_device')}",
        f"- Resident peak VRAM estimate: {gp.get('resident_estimated_peak_gib')} GiB",
        f"- Master cache hits/misses: {cache.get('cache_hit_count')}/{cache.get('cache_miss_count')}",
        f"- FITS read mode: {resident_io.get('fits_read_mode_effective')}",
        f"- WBPP dataset: {wbpp.get('dataset')}",
        "",
        "## Resident Timing",
        "",
        f"- Light read/upload/calibrate: {resident_timing.get('light_read_upload_calibrate')} s",
        f"- Registration/warp: {resident_timing.get('resident_registration_warp')} s",
        f"- Local normalization: {resident_timing.get('resident_local_normalization')} s",
        f"- Integration: {resident_timing.get('resident_integration')} s",
        f"- Output write: {resident_timing.get('output_write')} s",
        f"- WBPP FastIntegration ProcessingHistory: {wbpp_history.get('elapsed_s')} s",
        "",
        "## Stage Timing Comparison",
        "",
        "| Stage | GLASS s | WBPP s | Speedup |",
        "| --- | ---: | ---: | ---: |",
    ]
    for stage in paired_stages:
        speedup = stage.get("speedup_vs_wbpp")
        lines.append(
            "| "
            + str(stage.get("stage"))
            + " | "
            + str(stage.get("glass_s"))
            + " | "
            + str(stage.get("wbpp_s"))
            + " | "
            + (f"{speedup:.3f}x" if isinstance(speedup, (int, float)) else "n/a")
            + " |"
        )
    lines.extend(
        [
        "",
        "## Image Comparison",
        "",
        f"- Shape match: {comparison.get('shape_match')}",
        f"- RMS diff: {comparison.get('rms_diff')}",
        f"- abs diff p99: {comparison.get('abs_diff_p99')}",
        f"- coverage fraction: {comparison.get('coverage_fraction')}",
        f"- compared pixels: {comparison.get('compared_pixels')}",
        f"- compare timing speedup: {comparison.get('compare_speedup_vs_reference')}",
        "",
        "## Clean-room",
        "",
        f"- {summary['clean_room']['note']}",
        "",
        ]
    )
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines), encoding="utf-8")


def write_speedup_summary(
    out_json: str | Path,
    summary: dict[str, Any],
    markdown: str | Path | None = None,
) -> None:
    write_json(out_json, summary)
    if markdown is not None:
        write_speedup_markdown(markdown, summary)
