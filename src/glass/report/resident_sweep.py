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
                                                if wave_frame_count > batch_frame_count:
                                                    continue
                                                refill_suffix = (
                                                    "" if str(refill_mode) == "immediate" else f"_rf{refill_mode}"
                                                )
                                                registration_suffix = _registration_variant_suffix(
                                                    fast_coarse_mode=fast_coarse_mode,
                                                    coarse_stride=coarse_stride,
                                                    final_stride=final_stride,
                                                    max_candidates=max_candidates,
                                                )
                                                variant_id = (
                                                    f"pf{prefetch_frame_count}_pw{prefetch_worker_count}_"
                                                    f"b{batch_frame_count}_s{stream_count}_w{wave_frame_count}_"
                                                    f"{release_mode}{refill_suffix}{registration_suffix}"
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
                                                )
                                                variants.append(variant)
    return variants


def _registration_variant_suffix(
    *,
    fast_coarse_mode: str,
    coarse_stride: int | None,
    final_stride: int | None,
    max_candidates: int | None,
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
    return "" if not parts else "_" + "_".join(parts)


def _attach_registration_variant_fields(
    variant: dict[str, Any],
    *,
    fast_coarse_mode: str,
    coarse_stride: int | None,
    final_stride: int | None,
    max_candidates: int | None,
) -> None:
    if str(fast_coarse_mode) != "inherit":
        variant["triangle_fast_coarse"] = str(fast_coarse_mode) == "on"
    if coarse_stride is not None:
        variant["triangle_coarse_stride"] = int(coarse_stride)
    if final_stride is not None:
        variant["triangle_final_stride"] = int(final_stride)
    if max_candidates is not None:
        variant["star_max_candidates"] = int(max_candidates)


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
    return args


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
) -> list[dict[str, Any]]:
    compare_policy = _normalize_compare_gate_policy(compare_gate)
    ranked = []
    for summary in summaries:
        item = dict(summary)
        total = item.get("total_elapsed_s")
        item["speedup_vs_baseline"] = (
            None if baseline_total_s is None or total in (None, 0) else float(baseline_total_s) / float(total)
        )
        item["compare_gate"] = _evaluate_compare_gate(item, compare_policy)
        ranked.append(item)
    ranked.sort(
        key=lambda item: (
            item.get("status") != "completed",
            (item.get("guardrails") or {}).get("passed") is False,
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
) -> dict[str, Any]:
    out_path = Path(out)
    compare_gate_policy = _normalize_compare_gate_policy(compare_gate)
    ranked = rank_resident_sweep_summaries(
        summaries,
        baseline_total_s=baseline_total_s,
        compare_gate=compare_gate_policy,
    )
    guardrail_records = [
        run.get("guardrails") or {}
        for run in ranked
        if isinstance(run.get("guardrails"), dict) and (run.get("guardrails") or {}).get("status") != "disabled"
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
    return payload


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


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


def _evaluate_compare_gate(run: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    if not policy.get("enabled"):
        return {"status": "disabled", "passed": None, "policy": policy}
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
            f"{compare_gate.get('failed_count', 0)} failed"
        )
    lines.extend(
        [
            "",
            "| Rank | Status | Variant | Total s | Speedup vs baseline | Timeout s | Guardrails | Compare gate | Read wait s | "
            "Native cal s | Reg/warp s | Catalog s | Pixel refine s | Warp s | Blocked slots | Callback waves | "
            "Release batches | Active frames | Zero-weight | Ref RMS | Ref p99 | Ref speedup |",
            "| ---: | --- | --- | ---: | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | "
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
        lines.append(
            "| "
            f"{run.get('rank', '')} | "
            f"{run.get('status', '')} | "
            f"`{run.get('variant_id', '')}` | "
            f"{total} | {speedup} | {timeout} | {guardrail_status} | {compare_gate_status} | "
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


def _format_float(value: Any) -> str:
    if value is None:
        return ""
    return f"{float(value):.6f}"
