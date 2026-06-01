from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from glass.io.json_io import read_json, write_json


def parse_int_grid(value: str | None, *, default: Iterable[int]) -> list[int]:
    raw_values = list(default) if value is None or value.strip() == "" else value.split(",")
    parsed: list[int] = []
    for raw in raw_values:
        item = int(str(raw).strip())
        if item <= 0:
            raise ValueError("resident sweep integer grids must contain positive values")
        if item not in parsed:
            parsed.append(item)
    return parsed


def parse_mode_grid(value: str | None, *, default: Iterable[str]) -> list[str]:
    raw_values = list(default) if value is None or value.strip() == "" else value.split(",")
    parsed: list[str] = []
    for raw in raw_values:
        item = str(raw).strip()
        if not item:
            raise ValueError("resident sweep mode grids cannot contain empty values")
        if item not in parsed:
            parsed.append(item)
    return parsed


def build_resident_sweep_variants(
    *,
    prefetch_frames: Iterable[int],
    prefetch_workers: Iterable[int],
    batch_frames: Iterable[int],
    streams: Iterable[int],
    wave_frames: Iterable[int],
    release_modes: Iterable[str],
    refill_modes: Iterable[str] = ("immediate",),
    triangle_fast_coarse_modes: Iterable[str] = ("inherit",),
    triangle_coarse_strides: Iterable[int | None] = (None,),
    triangle_final_strides: Iterable[int | None] = (None,),
    star_max_candidates: Iterable[int | None] = (None,),
    star_grid_cols: Iterable[int | None] = (None,),
    star_grid_rows: Iterable[int | None] = (None,),
    triangle_grid_top_per_cell: Iterable[int | None] = (None,),
    triangle_nms_scan_candidates: Iterable[int | None] = (None,),
    triangle_nms_min_separation_px: Iterable[float | None] = (None,),
) -> list[dict[str, Any]]:
    variants: list[dict[str, Any]] = []
    for prefetch_frame_count in prefetch_frames:
        for prefetch_worker_count in prefetch_workers:
            for batch_frame_count in batch_frames:
                for stream_count in streams:
                    for wave_frame_count in wave_frames:
                        for release_mode in release_modes:
                            for refill_mode in refill_modes:
                                for fast_coarse_mode in triangle_fast_coarse_modes:
                                    for coarse_stride in triangle_coarse_strides:
                                        for final_stride in triangle_final_strides:
                                            for max_candidates in star_max_candidates:
                                                for grid_cols in star_grid_cols:
                                                    for grid_rows in star_grid_rows:
                                                        for top_per_cell in triangle_grid_top_per_cell:
                                                            for nms_scan in triangle_nms_scan_candidates:
                                                                for nms_sep in triangle_nms_min_separation_px:
                                                                    if wave_frame_count > batch_frame_count:
                                                                        continue
                                                                    if (grid_cols is None) != (grid_rows is None):
                                                                        continue
                                                                    refill_suffix = (
                                                                        ""
                                                                        if str(refill_mode) == "immediate"
                                                                        else f"_rf{refill_mode}"
                                                                    )
                                                                    registration_suffix = _registration_variant_suffix(
                                                                        fast_coarse_mode=fast_coarse_mode,
                                                                        coarse_stride=coarse_stride,
                                                                        final_stride=final_stride,
                                                                        max_candidates=max_candidates,
                                                                        grid_cols=grid_cols,
                                                                        grid_rows=grid_rows,
                                                                        top_per_cell=top_per_cell,
                                                                        nms_scan=nms_scan,
                                                                        nms_sep=nms_sep,
                                                                    )
                                                                    variant_id = (
                                                                        f"pf{prefetch_frame_count}_"
                                                                        f"pw{prefetch_worker_count}_"
                                                                        f"b{batch_frame_count}_s{stream_count}_"
                                                                        f"w{wave_frame_count}_{release_mode}"
                                                                        f"{refill_suffix}{registration_suffix}"
                                                                    )
                                                                    variant = {
                                                                        "variant_id": variant_id,
                                                                        "prefetch_frames": int(prefetch_frame_count),
                                                                        "prefetch_workers": int(prefetch_worker_count),
                                                                        "batch_frames": int(batch_frame_count),
                                                                        "streams": int(stream_count),
                                                                        "wave_frames": int(wave_frame_count),
                                                                        "release_mode": str(release_mode),
                                                                        "refill_mode": str(refill_mode),
                                                                    }
                                                                    _attach_registration_variant_fields(
                                                                        variant,
                                                                        fast_coarse_mode=fast_coarse_mode,
                                                                        coarse_stride=coarse_stride,
                                                                        final_stride=final_stride,
                                                                        max_candidates=max_candidates,
                                                                        grid_cols=grid_cols,
                                                                        grid_rows=grid_rows,
                                                                        top_per_cell=top_per_cell,
                                                                        nms_scan=nms_scan,
                                                                        nms_sep=nms_sep,
                                                                    )
                                                                    variants.append(variant)
    return variants


def _registration_variant_suffix(
    *,
    fast_coarse_mode: str,
    coarse_stride: int | None,
    final_stride: int | None,
    max_candidates: int | None,
    grid_cols: int | None,
    grid_rows: int | None,
    top_per_cell: int | None,
    nms_scan: int | None,
    nms_sep: float | None,
) -> str:
    parts: list[str] = []
    if str(fast_coarse_mode) != "inherit":
        parts.append("fcfast" if str(fast_coarse_mode) == "on" else "fcbase")
    if coarse_stride is not None:
        parts.append(f"cs{int(coarse_stride)}")
    if final_stride is not None:
        parts.append(f"fs{int(final_stride)}")
    if max_candidates is not None:
        parts.append(f"sm{int(max_candidates)}")
    if grid_cols is not None and grid_rows is not None:
        parts.append(f"g{int(grid_cols)}x{int(grid_rows)}")
    if top_per_cell is not None:
        parts.append(f"gt{int(top_per_cell)}")
    if nms_scan is not None:
        parts.append(f"ns{int(nms_scan)}")
    if nms_sep is not None:
        parts.append("sep" + _variant_float_token(float(nms_sep)))
    return "" if not parts else "_" + "_".join(parts)


def _attach_registration_variant_fields(
    variant: dict[str, Any],
    *,
    fast_coarse_mode: str,
    coarse_stride: int | None,
    final_stride: int | None,
    max_candidates: int | None,
    grid_cols: int | None,
    grid_rows: int | None,
    top_per_cell: int | None,
    nms_scan: int | None,
    nms_sep: float | None,
) -> None:
    if str(fast_coarse_mode) != "inherit":
        variant["triangle_fast_coarse"] = str(fast_coarse_mode) == "on"
    if coarse_stride is not None:
        variant["triangle_coarse_stride"] = int(coarse_stride)
    if final_stride is not None:
        variant["triangle_final_stride"] = int(final_stride)
    if max_candidates is not None:
        variant["star_max_candidates"] = int(max_candidates)
    if grid_cols is not None and grid_rows is not None:
        variant["star_grid_cols"] = int(grid_cols)
        variant["star_grid_rows"] = int(grid_rows)
    if top_per_cell is not None:
        variant["triangle_grid_top_per_cell"] = int(top_per_cell)
    if nms_scan is not None:
        variant["triangle_nms_scan_candidates"] = int(nms_scan)
    if nms_sep is not None:
        variant["triangle_nms_min_separation_px"] = float(nms_sep)


def variant_run_args(variant: dict[str, Any]) -> list[str]:
    args = [
        "--resident-prefetch-frames",
        str(int(variant["prefetch_frames"])),
        "--resident-prefetch-workers",
        str(int(variant["prefetch_workers"])),
        "--resident-prefetch-refill-mode",
        str(variant.get("refill_mode", "immediate")),
        "--resident-h2d-mode",
        "pinned_ring",
        "--resident-calibration-batch-frames",
        str(int(variant["batch_frames"])),
        "--resident-calibration-streams",
        str(int(variant["streams"])),
        "--resident-calibration-wave-frames",
        str(int(variant["wave_frames"])),
        "--resident-calibration-release-mode",
        str(variant["release_mode"]),
    ]
    if "triangle_coarse_stride" in variant:
        args.extend(["--resident-triangle-pixel-refine-coarse-stride", str(int(variant["triangle_coarse_stride"]))])
    if "triangle_final_stride" in variant:
        args.extend(["--resident-triangle-pixel-refine-final-stride", str(int(variant["triangle_final_stride"]))])
    if variant.get("triangle_fast_coarse") is True:
        args.append("--resident-triangle-pixel-refine-fast-coarse")
    if "star_max_candidates" in variant:
        args.extend(["--resident-star-max-candidates", str(int(variant["star_max_candidates"]))])
    if "star_grid_cols" in variant and "star_grid_rows" in variant:
        args.extend(["--resident-star-grid-cols", str(int(variant["star_grid_cols"]))])
        args.extend(["--resident-star-grid-rows", str(int(variant["star_grid_rows"]))])
    if "triangle_grid_top_per_cell" in variant:
        args.extend(
            ["--resident-triangle-grid-top-per-cell", str(int(variant["triangle_grid_top_per_cell"]))]
        )
    if "triangle_nms_scan_candidates" in variant:
        args.extend(
            ["--resident-triangle-nms-scan-candidates", str(int(variant["triangle_nms_scan_candidates"]))]
        )
    if "triangle_nms_min_separation_px" in variant:
        args.extend(
            [
                "--resident-triangle-nms-min-separation-px",
                str(float(variant["triangle_nms_min_separation_px"])),
            ]
        )
    return args


def _variant_float_token(value: float) -> str:
    return f"{value:g}".replace("-", "m").replace(".", "p")


def load_resident_run_summary(run_dir: str | Path, *, variant: dict[str, Any] | None = None) -> dict[str, Any]:
    run_path = Path(run_dir)
    timing_path = run_path / "run_timing.json"
    resident_path = run_path / "resident_artifacts.json"
    frame_accounting_path = run_path / "frame_accounting.json"

    timing = read_json(timing_path) if timing_path.exists() else {}
    resident = read_json(resident_path) if resident_path.exists() else {}
    frame_accounting = read_json(frame_accounting_path) if frame_accounting_path.exists() else {}
    frame_accounting_summary = frame_accounting.get("summary") or {}
    artifact = (resident.get("artifacts") or [{}])[0]
    artifact_timing = artifact.get("timing_s") or {}
    io_pipeline = artifact.get("resident_io_pipeline") or {}
    fine_timing = artifact.get("fine_timing") or {}
    registration_components = fine_timing.get("registration_component_seconds") or {}

    total_elapsed = timing.get("total_elapsed_s")
    if total_elapsed is None:
        stages = timing.get("stages") or []
        total_elapsed = sum(float(stage.get("elapsed_s", 0.0) or 0.0) for stage in stages)

    summary = {
        "variant": variant or {},
        "variant_id": (variant or {}).get("variant_id", run_path.name),
        "run_dir": str(run_path),
        "status": "completed" if timing_path.exists() and resident_path.exists() else "missing",
        "total_elapsed_s": None if total_elapsed is None else float(total_elapsed),
        "light_read_upload_calibrate_s": _optional_float(artifact_timing.get("light_read_upload_calibrate")),
        "light_read_wait_wall_s": _optional_float(artifact_timing.get("light_read_wait_wall")),
        "light_h2d_calibrate_store_s": _optional_float(artifact_timing.get("light_h2d_calibrate_store")),
        "native_calibration_total_s": _optional_float(io_pipeline.get("calibration_batch_native_total_s")),
        "native_calibration_sync_s": _optional_float(io_pipeline.get("calibration_batch_sync_s")),
        "resident_registration_warp_s": _optional_float(artifact_timing.get("resident_registration_warp")),
        "registration_component_accounted_s": _optional_float(
            registration_components.get("component_accounted_total")
        ),
        "registration_triangle_moving_catalog_s": _optional_float(
            registration_components.get("triangle_moving_catalog")
        ),
        "registration_triangle_descriptor_fit_s": _optional_float(
            registration_components.get("triangle_descriptor_fit")
        ),
        "registration_triangle_moving_descriptors_s": _optional_float(
            registration_components.get("triangle_moving_descriptors")
        ),
        "registration_triangle_pixel_refine_s": _optional_float(
            registration_components.get("triangle_pixel_refine")
        ),
        "registration_triangle_warp_s": _optional_float(registration_components.get("triangle_warp")),
        "registration_triangle_warp_native_batch_s": _optional_float(
            registration_components.get("triangle_warp_native_batch")
        ),
        "prefetch_blocked_no_slot_count": int(io_pipeline.get("prefetch_fill_blocked_no_slot_count", 0) or 0),
        "prefetch_release_batch_count": int(io_pipeline.get("prefetch_release_batch_count", 0) or 0),
        "prefetch_refill_mode": io_pipeline.get("prefetch_refill_mode"),
        "prefetch_release_refill_queued_submit_count": int(
            io_pipeline.get("prefetch_release_refill_queued_submit_count", 0) or 0
        ),
        "prefetch_release_refill_queued_execute_count": int(
            io_pipeline.get("prefetch_release_refill_queued_execute_count", 0) or 0
        ),
        "prefetch_release_refill_queued_coalesced_count": int(
            io_pipeline.get("prefetch_release_refill_queued_coalesced_count", 0) or 0
        ),
        "prefetch_release_refill_wait_s": float(io_pipeline.get("prefetch_release_refill_wait_s", 0.0) or 0.0),
        "prefetch_fill_call_count": int(io_pipeline.get("prefetch_fill_call_count", 0) or 0),
        "prefetch_fill_submit_count": int(io_pipeline.get("prefetch_fill_submit_count", 0) or 0),
        "callback_wave_count": int(io_pipeline.get("calibration_callback_wave_count", 0) or 0),
        "callback_release_count": int(io_pipeline.get("calibration_callback_release_count", 0) or 0),
        "calibration_batch_count": int(io_pipeline.get("calibration_batch_count", 0) or 0),
        "calibration_release_mode_effective": io_pipeline.get("calibration_release_mode_effective"),
        "master_path": artifact.get("master_path"),
        "coverage_map_path": artifact.get("coverage_map_path"),
        "input_light_frames": int(frame_accounting_summary.get("input_light_frames", 0) or 0),
        "active_light_frames": int(frame_accounting_summary.get("integrated_frames", 0) or 0),
        "zero_weight_frames": int(frame_accounting_summary.get("zero_weight_frames", 0) or 0),
    }
    return summary


def rank_resident_sweep_summaries(
    summaries: Iterable[dict[str, Any]],
    *,
    baseline_total_s: float | None = None,
    compare_gate: dict[str, Any] | None = None,
    frame_gate: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    compare_policy = _normalize_compare_gate_policy(compare_gate)
    frame_policy = _normalize_frame_gate_policy(frame_gate)
    ranked = []
    for summary in summaries:
        item = dict(summary)
        total = item.get("total_elapsed_s")
        item["speedup_vs_baseline"] = (
            None if baseline_total_s is None or total in (None, 0) else float(baseline_total_s) / float(total)
        )
        item["frame_gate"] = _evaluate_frame_gate(item, frame_policy)
        item["compare_gate"] = _evaluate_compare_gate(item, compare_policy)
        ranked.append(item)
    ranked.sort(
        key=lambda item: (
            item.get("status") != "completed",
            (item.get("guardrails") or {}).get("passed") is False,
            (item.get("frame_gate") or {}).get("passed") is False,
            (item.get("compare_gate") or {}).get("passed") is False,
            float("inf") if item.get("total_elapsed_s") is None else float(item["total_elapsed_s"]),
            int(item.get("prefetch_blocked_no_slot_count", 0) or 0),
        )
    )
    for rank, item in enumerate(ranked, start=1):
        item["rank"] = rank
    return ranked


def write_resident_sweep_summary(
    out: str | Path,
    *,
    plan: str | Path,
    variants: list[dict[str, Any]],
    summaries: list[dict[str, Any]],
    dry_run: bool,
    baseline_total_s: float | None = None,
    commands: list[dict[str, Any]] | None = None,
    common_run_args: dict[str, Any] | None = None,
    compare_gate: dict[str, Any] | None = None,
    frame_gate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out_path = Path(out)
    compare_gate_policy = _normalize_compare_gate_policy(compare_gate)
    frame_gate_policy = _normalize_frame_gate_policy(frame_gate)
    ranked = rank_resident_sweep_summaries(
        summaries,
        baseline_total_s=baseline_total_s,
        compare_gate=compare_gate_policy,
        frame_gate=frame_gate_policy,
    )
    guardrail_records = [
        run.get("guardrails") or {}
        for run in ranked
        if isinstance(run.get("guardrails"), dict) and (run.get("guardrails") or {}).get("status") != "disabled"
    ]
    frame_gate_records = [
        run.get("frame_gate") or {}
        for run in ranked
        if isinstance(run.get("frame_gate"), dict) and (run.get("frame_gate") or {}).get("status") != "disabled"
    ]
    compare_gate_records = [
        run.get("compare_gate") or {}
        for run in ranked
        if isinstance(run.get("compare_gate"), dict) and (run.get("compare_gate") or {}).get("status") != "disabled"
    ]
    best_variant = ranked[0] if ranked and ranked[0].get("status") == "completed" else None
    if best_variant and (best_variant.get("guardrails") or {}).get("passed") is False:
        best_variant = None
    if best_variant and (best_variant.get("compare_gate") or {}).get("passed") is False:
        best_variant = None
    if best_variant and (best_variant.get("frame_gate") or {}).get("passed") is False:
        best_variant = None
    payload = {
        "benchmark": "resident_prefetch_sweep",
        "schema_version": 1,
        "plan": str(plan),
        "out_dir": str(out_path),
        "dry_run": bool(dry_run),
        "variant_count": len(variants),
        "variants": variants,
        "runs": ranked,
        "best_variant": best_variant,
        "baseline_total_s": baseline_total_s,
        "guardrails": {
            "enabled": bool(guardrail_records),
            "passed_count": sum(1 for item in guardrail_records if item.get("passed") is True),
            "failed_count": sum(1 for item in guardrail_records if item.get("passed") is False),
            "planned_count": sum(1 for item in guardrail_records if item.get("status") == "planned"),
        },
        "frame_gate": {
            "enabled": bool(frame_gate_records),
            "policy": frame_gate_policy,
            "passed_count": sum(1 for item in frame_gate_records if item.get("passed") is True),
            "failed_count": sum(1 for item in frame_gate_records if item.get("passed") is False),
            "planned_count": sum(1 for item in frame_gate_records if item.get("status") == "planned"),
        },
        "compare_gate": {
            "enabled": bool(compare_gate_records),
            "policy": compare_gate_policy,
            "passed_count": sum(1 for item in compare_gate_records if item.get("passed") is True),
            "failed_count": sum(1 for item in compare_gate_records if item.get("passed") is False),
            "planned_count": sum(1 for item in compare_gate_records if item.get("status") == "planned"),
        },
        "common_run_args": common_run_args or {},
        "commands": commands or [],
    }
    write_json(out_path / "resident_prefetch_sweep_summary.json", payload)
    _write_markdown(out_path / "resident_prefetch_sweep_summary.md", payload)
    analysis = build_resident_sweep_analysis(payload)
    write_json(out_path / "resident_prefetch_sweep_analysis.json", analysis)
    _write_analysis_markdown(out_path / "resident_prefetch_sweep_analysis.md", analysis)
    return payload


def build_resident_sweep_analysis(payload: dict[str, Any]) -> dict[str, Any]:
    runs = [dict(run) for run in payload.get("runs", []) if isinstance(run, dict)]
    completed = [run for run in runs if run.get("status") == "completed"]
    guardrails_enabled = bool((payload.get("guardrails") or {}).get("enabled"))
    frame_gate_enabled = bool((payload.get("frame_gate") or {}).get("enabled"))
    compare_gate_enabled = bool((payload.get("compare_gate") or {}).get("enabled"))
    promotion_candidates = [
        run
        for run in completed
        if _run_guardrails_rankable(run, guardrails_enabled)
        and _run_frame_rankable(run, frame_gate_enabled)
        and _run_compare_rankable(run, compare_gate_enabled)
    ]
    fastest = _min_run_by(completed, "total_elapsed_s")
    lowest_catalog = _min_run_by(completed, "registration_triangle_moving_catalog_s")
    lowest_registration_warp = _min_run_by(completed, "resident_registration_warp_s")
    fastest_promotion = _min_run_by(promotion_candidates, "total_elapsed_s")
    baseline_total = _optional_float(payload.get("baseline_total_s"))
    best_variant = payload.get("best_variant") if isinstance(payload.get("best_variant"), dict) else None
    analysis = {
        "schema_version": 1,
        "benchmark": payload.get("benchmark"),
        "summary_path": str(Path(str(payload.get("out_dir", "."))) / "resident_prefetch_sweep_summary.json"),
        "variant_count": int(payload.get("variant_count", len(runs)) or 0),
        "completed_count": len(completed),
        "promotion_candidate_count": len(promotion_candidates),
        "guardrails_enabled": guardrails_enabled,
        "frame_gate_enabled": frame_gate_enabled,
        "frame_gate_policy": (payload.get("frame_gate") or {}).get("policy", {}),
        "compare_gate_enabled": compare_gate_enabled,
        "compare_gate_policy": (payload.get("compare_gate") or {}).get("policy", {}),
        "baseline_total_s": baseline_total,
        "best_variant_id": None if best_variant is None else best_variant.get("variant_id"),
        "fastest_variant": _analysis_run_record(fastest, baseline_total),
        "lowest_catalog_variant": _analysis_run_record(lowest_catalog, baseline_total),
        "lowest_registration_warp_variant": _analysis_run_record(lowest_registration_warp, baseline_total),
        "fastest_promotion_candidate": _analysis_run_record(fastest_promotion, baseline_total),
        "runs": [_analysis_run_record(run, baseline_total) for run in runs],
    }
    analysis["recommendation"] = _resident_sweep_recommendation(analysis)
    return analysis


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _run_guardrails_rankable(run: dict[str, Any], guardrails_enabled: bool) -> bool:
    if not guardrails_enabled:
        return True
    return (run.get("guardrails") or {}).get("passed") is True


def _run_compare_rankable(run: dict[str, Any], compare_gate_enabled: bool) -> bool:
    if not compare_gate_enabled:
        return True
    return (run.get("compare_gate") or {}).get("passed") is True


def _run_frame_rankable(run: dict[str, Any], frame_gate_enabled: bool) -> bool:
    if not frame_gate_enabled:
        return True
    return (run.get("frame_gate") or {}).get("passed") is True


def _min_run_by(runs: Iterable[dict[str, Any]], key: str) -> dict[str, Any] | None:
    candidates = [run for run in runs if run.get(key) is not None]
    if not candidates:
        return None
    return min(candidates, key=lambda run: float(run[key]))


def _analysis_run_record(run: dict[str, Any] | None, baseline_total_s: float | None) -> dict[str, Any] | None:
    if run is None:
        return None
    total = _optional_float(run.get("total_elapsed_s"))
    catalog = _optional_float(run.get("registration_triangle_moving_catalog_s"))
    registration_warp = _optional_float(run.get("resident_registration_warp_s"))
    compare = run.get("compare") if isinstance(run.get("compare"), dict) else {}
    compare_gate = run.get("compare_gate") if isinstance(run.get("compare_gate"), dict) else {}
    frame_gate = run.get("frame_gate") if isinstance(run.get("frame_gate"), dict) else {}
    guardrails = run.get("guardrails") if isinstance(run.get("guardrails"), dict) else {}
    return {
        "variant_id": run.get("variant_id"),
        "rank": run.get("rank"),
        "status": run.get("status"),
        "total_elapsed_s": total,
        "speedup_vs_baseline": None
        if baseline_total_s in (None, 0) or total in (None, 0)
        else float(baseline_total_s) / float(total),
        "registration_triangle_moving_catalog_s": catalog,
        "resident_registration_warp_s": registration_warp,
        "registration_triangle_pixel_refine_s": _optional_float(
            run.get("registration_triangle_pixel_refine_s")
        ),
        "registration_triangle_warp_s": _optional_float(run.get("registration_triangle_warp_s")),
        "guardrails_status": guardrails.get("status"),
        "guardrails_passed": guardrails.get("passed"),
        "frame_gate_status": frame_gate.get("status"),
        "frame_gate_passed": frame_gate.get("passed"),
        "frame_gate_reasons": frame_gate.get("reasons", []),
        "compare_gate_status": compare_gate.get("status"),
        "compare_gate_passed": compare_gate.get("passed"),
        "compare_gate_reasons": compare_gate.get("reasons", []),
        "ref_rms": compare.get("rms_diff"),
        "ref_p99": compare.get("abs_diff_p99"),
        "ref_speedup": compare.get("speedup_vs_reference"),
        "input_light_frames": run.get("input_light_frames"),
        "active_light_frames": run.get("active_light_frames"),
        "zero_weight_frames": run.get("zero_weight_frames"),
        "variant": run.get("variant", {}),
    }


def _resident_sweep_recommendation(analysis: dict[str, Any]) -> dict[str, Any]:
    fastest_promotion = analysis.get("fastest_promotion_candidate")
    lowest_catalog = analysis.get("lowest_catalog_variant")
    if fastest_promotion is not None:
        return {
            "status": "promotion_candidate_found",
            "variant_id": fastest_promotion.get("variant_id"),
            "reason": "fastest completed variant satisfying all enabled promotion gates",
        }
    if lowest_catalog is not None and lowest_catalog.get("frame_gate_passed") is False:
        return {
            "status": "candidate_blocked_by_frame_gate",
            "variant_id": lowest_catalog.get("variant_id"),
            "reason": "lowest moving-catalog time did not satisfy the frame-accounting gate",
            "frame_gate_reasons": lowest_catalog.get("frame_gate_reasons", []),
        }
    if lowest_catalog is not None and lowest_catalog.get("compare_gate_passed") is False:
        return {
            "status": "candidate_blocked_by_compare_gate",
            "variant_id": lowest_catalog.get("variant_id"),
            "reason": "lowest moving-catalog time did not satisfy the compare gate",
            "compare_gate_reasons": lowest_catalog.get("compare_gate_reasons", []),
        }
    return {
        "status": "no_promotion_candidate",
        "variant_id": None,
        "reason": "no completed variant satisfied all enabled ranking gates",
    }


def _normalize_frame_gate_policy(frame_gate: dict[str, Any] | None) -> dict[str, Any]:
    if not frame_gate:
        return {"enabled": False}
    policy = {
        "expected_input_light_frames": _optional_int(frame_gate.get("expected_input_light_frames")),
        "expected_active_light_frames": _optional_int(frame_gate.get("expected_active_light_frames")),
        "expected_zero_weight_frames": _optional_int(frame_gate.get("expected_zero_weight_frames")),
        "min_active_light_frames": _optional_int(frame_gate.get("min_active_light_frames")),
    }
    policy["enabled"] = any(value is not None for value in policy.values())
    return policy


def _normalize_compare_gate_policy(compare_gate: dict[str, Any] | None) -> dict[str, Any]:
    if not compare_gate:
        return {"enabled": False}
    policy = {
        "require_shape_match": bool(compare_gate.get("require_shape_match", False)),
        "max_rms_diff": _optional_float(compare_gate.get("max_rms_diff")),
        "max_relative_rms_diff": _optional_float(compare_gate.get("max_relative_rms_diff")),
        "max_abs_diff_p99": _optional_float(compare_gate.get("max_abs_diff_p99")),
    }
    policy["enabled"] = bool(
        policy["require_shape_match"]
        or policy["max_rms_diff"] is not None
        or policy["max_relative_rms_diff"] is not None
        or policy["max_abs_diff_p99"] is not None
    )
    return policy


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _evaluate_frame_gate(run: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    if not policy.get("enabled"):
        return {"status": "disabled", "passed": None, "policy": policy}
    if run.get("status") == "dry_run":
        return {"status": "planned", "passed": None, "policy": policy}
    reasons: list[str] = []
    _append_expected_int_gate_reason(
        reasons,
        run.get("input_light_frames"),
        policy.get("expected_input_light_frames"),
        "input_light_frames",
    )
    _append_expected_int_gate_reason(
        reasons,
        run.get("active_light_frames"),
        policy.get("expected_active_light_frames"),
        "active_light_frames",
    )
    _append_expected_int_gate_reason(
        reasons,
        run.get("zero_weight_frames"),
        policy.get("expected_zero_weight_frames"),
        "zero_weight_frames",
    )
    _append_min_int_gate_reason(
        reasons,
        run.get("active_light_frames"),
        policy.get("min_active_light_frames"),
        "active_light_frames",
    )
    return {
        "status": "failed" if reasons else "passed",
        "passed": not reasons,
        "reasons": reasons,
        "policy": policy,
    }


def _evaluate_compare_gate(run: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    if not policy.get("enabled"):
        return {"status": "disabled", "passed": None, "policy": policy}
    if run.get("status") == "dry_run":
        return {"status": "planned", "passed": None, "policy": policy}
    compare = run.get("compare") if isinstance(run.get("compare"), dict) else {}
    reasons: list[str] = []
    if compare.get("status") != "completed":
        reasons.append("compare status is not completed")
    if policy.get("require_shape_match") and compare.get("shape_match") is not True:
        reasons.append("shape_match is not true")
    _append_max_float_gate_reason(
        reasons,
        compare.get("rms_diff"),
        policy.get("max_rms_diff"),
        "rms_diff",
    )
    _append_max_float_gate_reason(
        reasons,
        compare.get("relative_rms_diff"),
        policy.get("max_relative_rms_diff"),
        "relative_rms_diff",
    )
    _append_max_float_gate_reason(
        reasons,
        compare.get("abs_diff_p99"),
        policy.get("max_abs_diff_p99"),
        "abs_diff_p99",
    )
    return {
        "status": "failed" if reasons else "passed",
        "passed": not reasons,
        "reasons": reasons,
        "policy": policy,
    }


def _append_expected_int_gate_reason(
    reasons: list[str],
    value: Any,
    expected: Any,
    name: str,
) -> None:
    if expected is None:
        return
    if value is None:
        reasons.append(f"{name} is missing")
        return
    numeric = int(value)
    required = int(expected)
    if numeric != required:
        reasons.append(f"{name} {numeric} != {required}")


def _append_min_int_gate_reason(
    reasons: list[str],
    value: Any,
    minimum: Any,
    name: str,
) -> None:
    if minimum is None:
        return
    if value is None:
        reasons.append(f"{name} is missing")
        return
    numeric = int(value)
    required = int(minimum)
    if numeric < required:
        reasons.append(f"{name} {numeric} < {required}")


def _append_max_float_gate_reason(
    reasons: list[str],
    value: Any,
    limit: Any,
    name: str,
) -> None:
    if limit is None:
        return
    if value is None:
        reasons.append(f"{name} is missing")
        return
    numeric = float(value)
    maximum = float(limit)
    if numeric > maximum:
        reasons.append(f"{name} {numeric:.6g} > {maximum:.6g}")


def _write_markdown(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Resident Prefetch Sweep",
        "",
        f"- Plan: `{payload['plan']}`",
        f"- Variants: {payload['variant_count']}",
        f"- Dry run: {payload['dry_run']}",
    ]
    if payload.get("baseline_total_s") is not None:
        lines.append(f"- Baseline total: {payload['baseline_total_s']:.6f} s")
    common_run_args = payload.get("common_run_args") if isinstance(payload.get("common_run_args"), dict) else {}
    if common_run_args:
        lines.append(f"- Common run args source: `{common_run_args.get('source')}`")
        if common_run_args.get("source_command_path"):
            lines.append(f"- Imported command: `{common_run_args['source_command_path']}`")
        frame_gate_contract = common_run_args.get("frame_gate_contract")
        if isinstance(frame_gate_contract, dict) and frame_gate_contract.get("source_contract_path"):
            lines.append(f"- Frame gate contract: `{frame_gate_contract['source_contract_path']}`")
        compare_contract = common_run_args.get("compare_contract")
        if isinstance(compare_contract, dict) and compare_contract.get("source_contract_path"):
            lines.append(f"- Compare contract: `{compare_contract['source_contract_path']}`")
        lines.append(
            "- Common run args: "
            f"{common_run_args.get('total_arg_count', 0)} total, "
            f"{common_run_args.get('imported_arg_count', 0)} imported, "
            f"{common_run_args.get('filtered_token_count', 0)} filtered"
        )
    compare_gate = payload.get("compare_gate") if isinstance(payload.get("compare_gate"), dict) else {}
    if compare_gate.get("enabled"):
        lines.append(
            "- Compare gate: "
            f"{compare_gate.get('passed_count', 0)} passed, "
            f"{compare_gate.get('failed_count', 0)} failed, "
            f"{compare_gate.get('planned_count', 0)} planned"
        )
    frame_gate = payload.get("frame_gate") if isinstance(payload.get("frame_gate"), dict) else {}
    if frame_gate.get("enabled"):
        lines.append(
            "- Frame gate: "
            f"{frame_gate.get('passed_count', 0)} passed, "
            f"{frame_gate.get('failed_count', 0)} failed, "
            f"{frame_gate.get('planned_count', 0)} planned"
        )
    lines.extend(
        [
            "",
            "| Rank | Status | Variant | Total s | Speedup vs baseline | Timeout s | Guardrails | Frame gate | Compare gate | Read wait s | "
            "Native cal s | Reg/warp s | Catalog s | Pixel refine s | Warp s | Blocked slots | Callback waves | "
            "Release batches | Active frames | Zero-weight | Ref RMS | Ref p99 | Ref speedup |",
            "| ---: | --- | --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | "
            "---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for run in payload["runs"]:
        total = _format_float(run.get("total_elapsed_s"))
        speedup = _format_float(run.get("speedup_vs_baseline"))
        timeout = _format_float(run.get("timeout_s"))
        read_wait = _format_float(run.get("light_read_wait_wall_s"))
        native_cal = _format_float(run.get("native_calibration_total_s"))
        registration_warp = _format_float(run.get("resident_registration_warp_s"))
        catalog = _format_float(run.get("registration_triangle_moving_catalog_s"))
        pixel_refine = _format_float(run.get("registration_triangle_pixel_refine_s"))
        warp = _format_float(run.get("registration_triangle_warp_s"))
        compare = run.get("compare") if isinstance(run.get("compare"), dict) else {}
        compare_rms = _format_float(compare.get("rms_diff"))
        compare_p99 = _format_float(compare.get("abs_diff_p99"))
        compare_speedup = _format_float(compare.get("speedup_vs_reference"))
        guardrails = run.get("guardrails") if isinstance(run.get("guardrails"), dict) else {}
        guardrail_status = str(guardrails.get("status") or "")
        compare_gate_status = ""
        if isinstance(run.get("compare_gate"), dict):
            compare_gate_status = str(run["compare_gate"].get("status") or "")
        frame_gate_status = ""
        if isinstance(run.get("frame_gate"), dict):
            frame_gate_status = str(run["frame_gate"].get("status") or "")
        lines.append(
            "| "
            f"{run.get('rank', '')} | "
            f"{run.get('status', '')} | "
            f"`{run.get('variant_id', '')}` | "
            f"{total} | {speedup} | {timeout} | {guardrail_status} | {frame_gate_status} | "
            f"{compare_gate_status} | "
            f"{read_wait} | {native_cal} | "
            f"{registration_warp} | {catalog} | {pixel_refine} | {warp} | "
            f"{run.get('prefetch_blocked_no_slot_count', '')} | "
            f"{run.get('callback_wave_count', '')} | "
            f"{run.get('prefetch_release_batch_count', '')} | "
            f"{run.get('active_light_frames', '')} | "
            f"{run.get('zero_weight_frames', '')} | "
            f"{compare_rms} | {compare_p99} | {compare_speedup} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_analysis_markdown(path: Path, analysis: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    recommendation = analysis.get("recommendation") if isinstance(analysis.get("recommendation"), dict) else {}
    lines = [
        "# Resident Prefetch Sweep Analysis",
        "",
        f"- Variants: {analysis.get('variant_count', 0)}",
        f"- Completed: {analysis.get('completed_count', 0)}",
        f"- Promotion candidates: {analysis.get('promotion_candidate_count', 0)}",
        f"- Recommendation: `{recommendation.get('status')}`",
    ]
    if recommendation.get("variant_id"):
        lines.append(f"- Recommendation variant: `{recommendation['variant_id']}`")
    if recommendation.get("reason"):
        lines.append(f"- Reason: {recommendation['reason']}")
    lines.extend(
        [
            "",
            "| Kind | Variant | Total s | Catalog s | Reg/warp s | Frame gate | Compare gate | Ref RMS | Ref p99 |",
            "| --- | --- | ---: | ---: | ---: | --- | --- | ---: | ---: |",
        ]
    )
    rows = [
        ("Fastest", analysis.get("fastest_variant")),
        ("Lowest catalog", analysis.get("lowest_catalog_variant")),
        ("Lowest reg/warp", analysis.get("lowest_registration_warp_variant")),
        ("Fastest promotion", analysis.get("fastest_promotion_candidate")),
    ]
    for label, row in rows:
        if not isinstance(row, dict):
            lines.append(f"| {label} |  |  |  |  |  |  |  |  |")
            continue
        lines.append(
            "| "
            f"{label} | "
            f"`{row.get('variant_id', '')}` | "
            f"{_format_float(row.get('total_elapsed_s'))} | "
            f"{_format_float(row.get('registration_triangle_moving_catalog_s'))} | "
            f"{_format_float(row.get('resident_registration_warp_s'))} | "
            f"{row.get('frame_gate_status') or ''} | "
            f"{row.get('compare_gate_status') or ''} | "
            f"{_format_float(row.get('ref_rms'))} | "
            f"{_format_float(row.get('ref_p99'))} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _format_float(value: Any) -> str:
    if value is None:
        return ""
    return f"{float(value):.6f}"
