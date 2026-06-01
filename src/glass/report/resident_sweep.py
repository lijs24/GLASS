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
) -> list[dict[str, Any]]:
    variants: list[dict[str, Any]] = []
    for prefetch_frame_count in prefetch_frames:
        for prefetch_worker_count in prefetch_workers:
            for batch_frame_count in batch_frames:
                for stream_count in streams:
                    for wave_frame_count in wave_frames:
                        for release_mode in release_modes:
                            for refill_mode in refill_modes:
                                if wave_frame_count > batch_frame_count:
                                    continue
                                refill_suffix = "" if str(refill_mode) == "immediate" else f"_rf{refill_mode}"
                                variant_id = (
                                    f"pf{prefetch_frame_count}_pw{prefetch_worker_count}_"
                                    f"b{batch_frame_count}_s{stream_count}_w{wave_frame_count}_{release_mode}"
                                    f"{refill_suffix}"
                                )
                                variants.append(
                                    {
                                        "variant_id": variant_id,
                                        "prefetch_frames": int(prefetch_frame_count),
                                        "prefetch_workers": int(prefetch_worker_count),
                                        "batch_frames": int(batch_frame_count),
                                        "streams": int(stream_count),
                                        "wave_frames": int(wave_frame_count),
                                        "release_mode": str(release_mode),
                                        "refill_mode": str(refill_mode),
                                    }
                                )
    return variants


def variant_run_args(variant: dict[str, Any]) -> list[str]:
    return [
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
        "input_light_frames": int(frame_accounting_summary.get("input_light_frames", 0) or 0),
        "active_light_frames": int(frame_accounting_summary.get("integrated_frames", 0) or 0),
        "zero_weight_frames": int(frame_accounting_summary.get("zero_weight_frames", 0) or 0),
    }
    return summary


def rank_resident_sweep_summaries(
    summaries: Iterable[dict[str, Any]], *, baseline_total_s: float | None = None
) -> list[dict[str, Any]]:
    ranked = []
    for summary in summaries:
        item = dict(summary)
        total = item.get("total_elapsed_s")
        item["speedup_vs_baseline"] = (
            None if baseline_total_s is None or total in (None, 0) else float(baseline_total_s) / float(total)
        )
        ranked.append(item)
    ranked.sort(
        key=lambda item: (
            item.get("status") != "completed",
            (item.get("guardrails") or {}).get("passed") is False,
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
) -> dict[str, Any]:
    out_path = Path(out)
    ranked = rank_resident_sweep_summaries(summaries, baseline_total_s=baseline_total_s)
    guardrail_records = [
        run.get("guardrails") or {}
        for run in ranked
        if isinstance(run.get("guardrails"), dict) and (run.get("guardrails") or {}).get("status") != "disabled"
    ]
    best_variant = ranked[0] if ranked and ranked[0].get("status") == "completed" else None
    if best_variant and (best_variant.get("guardrails") or {}).get("passed") is False:
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
    lines.extend(
        [
            "",
            "| Rank | Status | Variant | Total s | Speedup vs baseline | Timeout s | Guardrails | Read wait s | "
            "Native cal s | Blocked slots | Callback waves | Release batches | Active frames | Zero-weight |",
            "| ---: | --- | --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for run in payload["runs"]:
        total = _format_float(run.get("total_elapsed_s"))
        speedup = _format_float(run.get("speedup_vs_baseline"))
        timeout = _format_float(run.get("timeout_s"))
        read_wait = _format_float(run.get("light_read_wait_wall_s"))
        native_cal = _format_float(run.get("native_calibration_total_s"))
        guardrails = run.get("guardrails") if isinstance(run.get("guardrails"), dict) else {}
        guardrail_status = str(guardrails.get("status") or "")
        lines.append(
            "| "
            f"{run.get('rank', '')} | "
            f"{run.get('status', '')} | "
            f"`{run.get('variant_id', '')}` | "
            f"{total} | {speedup} | {timeout} | {guardrail_status} | {read_wait} | {native_cal} | "
            f"{run.get('prefetch_blocked_no_slot_count', '')} | "
            f"{run.get('callback_wave_count', '')} | "
            f"{run.get('prefetch_release_batch_count', '')} | "
            f"{run.get('active_light_frames', '')} | "
            f"{run.get('zero_weight_frames', '')} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _format_float(value: Any) -> str:
    if value is None:
        return ""
    return f"{float(value):.6f}"
