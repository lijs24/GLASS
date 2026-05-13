from __future__ import annotations

import argparse
import importlib.util
import platform
import sys
from time import perf_counter
from pathlib import Path

from rich.console import Console

from glass.capabilities import capability_report
from glass.engine.integration import integrate_registered_frames
from glass.engine.local_norm import local_normalize_registered_frames
from glass.engine.pipeline import initialize_run, run_calibration_stages
from glass.engine.quality import measure_calibrated_quality
from glass.engine.registration import register_calibrated_frames
from glass.engine.resident_cuda import run_resident_calibration_integration
from glass.engine.warp import warp_registered_frames
from glass.engine.resume import resume_summary
from glass.engine.state import write_run_state
from glass.io.json_io import read_json, write_json
from glass.metadata.scanner import scan_tree
from glass.planner.plan_builder import build_processing_plan
from glass.planner.subset import build_subset_manifest
from glass.report.blackbox_package import create_blackbox_package, finalize_blackbox_package
from glass.report.compare_report import compare_fits, write_compare_report
from glass.report.html_report import write_html_report
from glass.report.acceptance_audit import build_acceptance_audit, write_acceptance_audit
from glass.report.speedup_report import summarize_wbpp_speedup, write_speedup_summary
from glass.report.wbpp_history import read_fastintegration_history
from glass.synthetic.generator import generate_synthetic_dataset
from glass.models import now_iso

console = Console()


def _read_json_if_exists(path: Path):
    return read_json(path) if path.exists() else None


def _local_norm_override_from_arg(value: str) -> bool | None:
    if value == "on":
        return True
    if value == "off":
        return False
    return None


def _new_timing(command: str, backend: str | None = None, tile_size: int | None = None) -> dict:
    return {
        "schema_version": 1,
        "command": command,
        "created_at": now_iso(),
        "backend": backend,
        "tile_size": tile_size,
        "stages": [],
        "total_elapsed_s": 0.0,
    }


def _write_timing(run: Path, timing: dict) -> None:
    timing["total_elapsed_s"] = float(sum(float(item.get("elapsed_s") or 0.0) for item in timing["stages"]))
    write_json(run / "run_timing.json", timing)


def _timed_stage(run: Path, timing: dict, stage: str, fn):
    record = {"stage": stage, "started_at": now_iso(), "status": "running"}
    start = perf_counter()
    try:
        result = fn()
    except Exception as exc:
        record["status"] = "failed"
        record["elapsed_s"] = perf_counter() - start
        record["error"] = str(exc)
        timing["stages"].append(record)
        _write_timing(run, timing)
        raise
    record["status"] = "ok"
    record["elapsed_s"] = perf_counter() - start
    timing["stages"].append(record)
    _write_timing(run, timing)
    return result


def _write_run_report(run: Path, report_path: Path, manifest_path: Path, plan_path: Path) -> None:
    write_html_report(
        report_path,
        manifest=_read_json_if_exists(manifest_path),
        plan=_read_json_if_exists(plan_path),
        quality=_read_json_if_exists(run / "frame_quality.json"),
        registration=_read_json_if_exists(run / "registration_results.json"),
        local_norm=_read_json_if_exists(run / "local_norm_results.json"),
        integration=_read_json_if_exists(run / "integration_results.json"),
        timing=_read_json_if_exists(run / "run_timing.json"),
        resident=_read_json_if_exists(run / "resident_artifacts.json"),
    )


def _seed_run_inputs(run: Path, plan_path: str | Path) -> None:
    run.mkdir(parents=True, exist_ok=True)
    plan = read_json(plan_path)
    write_json(run / "processing_plan.json", plan)
    manifest_path = plan.get("manifest_path")
    if manifest_path and Path(manifest_path).exists():
        write_json(run / "manifest.json", read_json(manifest_path))


def _run_full_pipeline(
    plan_path: Path,
    out: Path,
    backend: str,
    tile_size: int,
    local_normalization: str,
    integration_weighting: str,
    integration_rejection: str,
    registration_method: str = "auto",
    timing: dict | None = None,
):
    timing = timing or _new_timing("run", backend, tile_size)
    state = _timed_stage(
        out,
        timing,
        "calibration",
        lambda: run_calibration_stages(plan_path, out, backend=backend, tile_size=tile_size),
    )
    _timed_stage(out, timing, "quality", lambda: measure_calibrated_quality(out, tile_size=tile_size))
    state.completed_stages.append("quality")
    state.current_stage = "quality"
    _timed_stage(
        out,
        timing,
        "registration",
        lambda: register_calibrated_frames(out, tile_size=tile_size, method=registration_method),
    )
    state.completed_stages.append("registration")
    state.current_stage = "registration"
    _timed_stage(out, timing, "warp", lambda: warp_registered_frames(out, tile_size=tile_size))
    state.completed_stages.append("warp")
    state.current_stage = "warp"
    _timed_stage(
        out,
        timing,
        "local_normalization",
        lambda: local_normalize_registered_frames(
            out,
            plan_path=plan_path,
            backend=backend,
            tile_size=tile_size,
            enabled_override=_local_norm_override_from_arg(local_normalization),
        ),
    )
    state.completed_stages.append("local_normalization")
    state.current_stage = "local_normalization"
    _timed_stage(
        out,
        timing,
        "integration",
        lambda: integrate_registered_frames(
            out,
            plan_path=plan_path,
            backend=backend,
            tile_size=tile_size,
            weighting_override=integration_weighting,
            rejection_override=integration_rejection,
        ),
    )
    state.completed_stages.append("integration")
    state.current_stage = "integration"
    return state


def _resume_pipeline(plan_path: Path, out: Path, backend: str = "auto", tile_size: int = 512, timing: dict | None = None):
    timing = timing or _new_timing("resume", backend, tile_size)
    state = initialize_run(out)
    if (out / "calibration_artifacts.json").exists():
        state.completed_stages.extend(["master_calibration", "light_calibration"])
        state.current_stage = "calibration"
    else:
        return _run_full_pipeline(plan_path, out, backend, tile_size, "auto", "auto", "auto", "auto", timing)

    if not (out / "frame_quality.json").exists():
        _timed_stage(out, timing, "quality", lambda: measure_calibrated_quality(out, tile_size=tile_size))
    state.completed_stages.append("quality")
    state.current_stage = "quality"

    if not (out / "registration_results.json").exists():
        _timed_stage(out, timing, "registration", lambda: register_calibrated_frames(out, tile_size=tile_size))
    state.completed_stages.append("registration")
    state.current_stage = "registration"

    if not (out / "warp_results.json").exists():
        _timed_stage(out, timing, "warp", lambda: warp_registered_frames(out, tile_size=tile_size))
    state.completed_stages.append("warp")
    state.current_stage = "warp"

    if not (out / "local_norm_results.json").exists():
        _timed_stage(
            out,
            timing,
            "local_normalization",
            lambda: local_normalize_registered_frames(out, plan_path=plan_path, backend=backend, tile_size=tile_size),
        )
    state.completed_stages.append("local_normalization")
    state.current_stage = "local_normalization"

    if not (out / "integration_results.json").exists():
        _timed_stage(
            out,
            timing,
            "integration",
            lambda: integrate_registered_frames(out, plan_path=plan_path, backend=backend, tile_size=tile_size),
        )
    state.completed_stages.append("integration")
    state.current_stage = "integration"
    return state


def cmd_scan(args: argparse.Namespace) -> int:
    manifest = scan_tree(args.root)
    write_json(args.out, manifest)
    summary = manifest["summary"]
    console.print(f"Scanned {summary['count']} frame(s)")
    console.print(summary)
    return 0


def cmd_plan(args: argparse.Namespace) -> int:
    manifest = read_json(args.manifest)
    plan = build_processing_plan(manifest, args.manifest)
    write_json(args.out, plan)
    console.print(f"Wrote processing plan: {args.out}")
    console.print({"executable": plan.executable, "warnings": len(plan.global_warnings)})
    return 0


def cmd_subset(args: argparse.Namespace) -> int:
    manifest = read_json(args.manifest)
    subset = build_subset_manifest(
        manifest,
        object_name=args.object,
        filter_name=args.filter,
        exposure_s=args.exposure_s,
        light_limit=args.light_limit,
        bias_limit=args.bias_limit,
        dark_limit=args.dark_limit,
        flat_limit=args.flat_limit,
        all_compatible_calibration=args.all_compatible_calibration,
    )
    write_json(args.out, subset)
    summary = subset["summary"]
    console.print(f"Wrote subset manifest: {args.out}")
    console.print(summary)
    if args.plan_out:
        plan = build_processing_plan(subset, args.out)
        write_json(args.plan_out, plan)
        console.print(f"Wrote subset processing plan: {args.plan_out}")
        console.print({"executable": plan.executable, "warnings": len(plan.global_warnings)})
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    run = Path(args.run)
    manifest_path = Path(args.manifest) if args.manifest else run / "manifest.json"
    plan_path = Path(args.plan) if args.plan else run / "processing_plan.json"
    manifest = _read_json_if_exists(manifest_path)
    plan = _read_json_if_exists(plan_path)
    quality_path = run / "frame_quality.json"
    registration_path = run / "registration_results.json"
    local_norm_path = run / "local_norm_results.json"
    integration_path = run / "integration_results.json"
    timing_path = run / "run_timing.json"
    resident_path = run / "resident_artifacts.json"
    quality = _read_json_if_exists(quality_path)
    registration = _read_json_if_exists(registration_path)
    local_norm = _read_json_if_exists(local_norm_path)
    integration = _read_json_if_exists(integration_path)
    timing = _read_json_if_exists(timing_path)
    resident = _read_json_if_exists(resident_path)
    write_html_report(
        args.out,
        manifest=manifest,
        plan=plan,
        quality=quality,
        registration=registration,
        local_norm=local_norm,
        integration=integration,
        timing=timing,
        resident=resident,
    )
    console.print(f"Wrote report: {args.out}")
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if args.backend == "cuda" and not capability_report()["cuda_available"]:
        raise SystemExit("CUDA backend requested but unavailable; use --backend auto or cpu.")
    if args.memory_mode == "resident" and args.backend != "cuda":
        raise SystemExit("Resident audit currently requires --backend cuda.")
    manifest_path = out / "manifest.json"
    plan_path = out / "processing_plan.json"
    report_path = out / "report.html"
    timing = _new_timing("audit", args.backend, args.tile_size)
    timing["memory_mode"] = args.memory_mode
    manifest = _timed_stage(out, timing, "scan", lambda: scan_tree(args.root))
    write_json(manifest_path, manifest)
    plan = _timed_stage(out, timing, "plan", lambda: build_processing_plan(manifest, manifest_path))
    write_json(plan_path, plan)
    if plan.executable and args.memory_mode == "resident":
        state = _timed_stage(
            out,
            timing,
            "resident_calibration_integration",
            lambda: run_resident_calibration_integration(
                plan_path,
                out,
                integration_weighting=args.integration_weighting,
                integration_rejection=args.integration_rejection,
                flat_floor=args.flat_floor,
                resident_registration=args.resident_registration,
                resident_registration_max_shift=args.resident_registration_max_shift,
                resident_ncc_sample_stride=args.resident_ncc_sample_stride,
                resident_ncc_fallback_score_threshold=args.resident_ncc_fallback_score_threshold,
                resident_subpixel_radius_steps=args.resident_subpixel_radius_steps,
                resident_subpixel_step=args.resident_subpixel_step,
                resident_star_threshold=args.resident_star_threshold,
                resident_star_max_candidates=args.resident_star_max_candidates,
                resident_star_tolerance_px=args.resident_star_tolerance_px,
                resident_star_grid_cols=args.resident_star_grid_cols,
                resident_star_grid_rows=args.resident_star_grid_rows,
                resident_star_prior=args.resident_star_prior,
                resident_star_prior_radius_px=args.resident_star_prior_radius_px,
                resident_star_core_preselect_top_k=args.resident_star_core_preselect_top_k,
                resident_triangle_pixel_refine_coarse_stride=args.resident_triangle_pixel_refine_coarse_stride,
                resident_triangle_pixel_refine_final_stride=args.resident_triangle_pixel_refine_final_stride,
                resident_registration_results=args.resident_registration_results,
                resident_warp_interpolation=args.resident_warp_interpolation,
                resident_warp_clamping_threshold=args.resident_warp_clamping_threshold,
                reference_frame_id=args.reference_frame_id,
                exclude_frame_ids=args.exclude_frame_id,
                local_normalization=args.local_normalization,
                resident_local_normalization_mode=args.resident_local_normalization_mode,
                resident_local_normalization_tile_size=args.resident_local_normalization_tile_size,
                resident_prefetch_frames=args.resident_prefetch_frames,
                resident_prefetch_workers=args.resident_prefetch_workers,
                resident_h2d_mode=args.resident_h2d_mode,
            ),
        )
    elif plan.executable:
        state = _run_full_pipeline(
            plan_path,
            out,
            args.backend,
            args.tile_size,
            args.local_normalization,
            args.integration_weighting,
            args.integration_rejection,
            registration_method=args.registration_method,
            timing=timing,
        )
    else:
        state = initialize_run(out)
        state.warnings.append("processing plan is not executable; audit stopped after scan and plan")
    state.completed_stages.insert(0, "plan")
    state.completed_stages.insert(0, "scan")
    state.completed_stages.append("report")
    state.current_stage = "report"
    write_run_state(out, state)
    _timed_stage(out, timing, "report", lambda: _write_run_report(out, report_path, manifest_path, plan_path))
    console.print(f"Audit complete: {out}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    capabilities = capability_report()
    if args.backend == "cuda" and not capabilities["cuda_available"]:
        raise SystemExit("CUDA backend requested but native CUDA backend is unavailable.")
    _seed_run_inputs(Path(args.out), args.plan)
    if args.memory_mode == "resident":
        if args.backend != "cuda":
            raise SystemExit("Resident memory mode currently requires --backend cuda.")
        if args.until_stage != "integration":
            raise SystemExit("Resident memory mode currently supports --until-stage integration only.")
        if args.integration_rejection not in {"auto", "none", "sigma_clip", "winsorized_sigma"}:
            raise SystemExit(
                "Resident memory mode currently supports --integration-rejection none, "
                "sigma_clip, or winsorized_sigma."
            )
        if args.integration_weighting not in {"auto", "none", "simple_snr"}:
            raise SystemExit("Resident memory mode currently supports --integration-weighting none or simple_snr.")
        out = Path(args.out)
        timing = _new_timing("run", args.backend, None)
        timing["memory_mode"] = "resident"
        state = _timed_stage(
            out,
            timing,
            "resident_calibration_integration",
            lambda: run_resident_calibration_integration(
                args.plan,
                args.out,
                integration_weighting=args.integration_weighting,
                integration_rejection=args.integration_rejection,
                flat_floor=args.flat_floor,
                resident_registration=args.resident_registration,
                resident_registration_max_shift=args.resident_registration_max_shift,
                resident_ncc_sample_stride=args.resident_ncc_sample_stride,
                resident_ncc_fallback_score_threshold=args.resident_ncc_fallback_score_threshold,
                resident_subpixel_radius_steps=args.resident_subpixel_radius_steps,
                resident_subpixel_step=args.resident_subpixel_step,
                resident_star_threshold=args.resident_star_threshold,
                resident_star_max_candidates=args.resident_star_max_candidates,
                resident_star_tolerance_px=args.resident_star_tolerance_px,
                resident_star_grid_cols=args.resident_star_grid_cols,
                resident_star_grid_rows=args.resident_star_grid_rows,
                resident_star_prior=args.resident_star_prior,
                resident_star_prior_radius_px=args.resident_star_prior_radius_px,
                resident_star_core_preselect_top_k=args.resident_star_core_preselect_top_k,
                resident_triangle_pixel_refine_coarse_stride=args.resident_triangle_pixel_refine_coarse_stride,
                resident_triangle_pixel_refine_final_stride=args.resident_triangle_pixel_refine_final_stride,
                resident_registration_results=args.resident_registration_results,
                resident_warp_interpolation=args.resident_warp_interpolation,
                resident_warp_clamping_threshold=args.resident_warp_clamping_threshold,
                reference_frame_id=args.reference_frame_id,
                exclude_frame_ids=args.exclude_frame_id,
                local_normalization=args.local_normalization,
                resident_local_normalization_mode=args.resident_local_normalization_mode,
                resident_local_normalization_tile_size=args.resident_local_normalization_tile_size,
                resident_prefetch_frames=args.resident_prefetch_frames,
                resident_prefetch_workers=args.resident_prefetch_workers,
                resident_h2d_mode=args.resident_h2d_mode,
            ),
        )
        write_run_state(args.out, state)
        console.print(f"Resident CUDA run complete through {state.current_stage}: {args.out}")
        return 0
    implemented_stages = {
        "master_calibration",
        "light_calibration",
        "calibration",
        "quality",
        "registration",
        "warp",
        "local_normalization",
        "integration",
    }
    if args.until_stage not in implemented_stages:
        if args.allow_partial:
            console.print("Only calibration stages are implemented; initializing partial run state.")
        else:
            raise SystemExit(
                "Current gated runner supports --until-stage calibration, quality, registration, warp, "
                "local_normalization, or integration only. "
                "Use --allow-partial to write a diagnostic run_state without executing later stages."
            )
    if args.until_stage in implemented_stages:
        out = Path(args.out)
        timing = _new_timing("run", args.backend, args.tile_size)
        state = _timed_stage(
            out,
            timing,
            "calibration",
            lambda: run_calibration_stages(
                args.plan,
                args.out,
                backend=args.backend,
                tile_size=args.tile_size,
                flat_floor=args.flat_floor,
            ),
        )
        if args.until_stage in {"quality", "registration", "warp", "local_normalization", "integration"}:
            _timed_stage(out, timing, "quality", lambda: measure_calibrated_quality(args.out, tile_size=args.tile_size))
            state.completed_stages.append("quality")
            state.current_stage = "quality"
        if args.until_stage in {"registration", "warp", "local_normalization", "integration"}:
            _timed_stage(
                out,
                timing,
                "registration",
                lambda: register_calibrated_frames(
                    args.out,
                    tile_size=args.tile_size,
                    preview_max_dimension=args.registration_preview_max_dimension,
                    method=args.registration_method,
                    reference_frame_id=args.reference_frame_id,
                ),
            )
            state.completed_stages.append("registration")
            state.current_stage = "registration"
        if args.until_stage in {"warp", "local_normalization", "integration"}:
            _timed_stage(out, timing, "warp", lambda: warp_registered_frames(args.out, tile_size=args.tile_size))
            state.completed_stages.append("warp")
            state.current_stage = "warp"
        if args.until_stage in {"local_normalization", "integration"}:
            _timed_stage(
                out,
                timing,
                "local_normalization",
                lambda: local_normalize_registered_frames(
                    args.out,
                    plan_path=args.plan,
                    backend=args.backend,
                    tile_size=args.tile_size,
                    enabled_override=_local_norm_override_from_arg(args.local_normalization),
                ),
            )
            state.completed_stages.append("local_normalization")
            state.current_stage = "local_normalization"
        if args.until_stage == "integration":
            _timed_stage(
                out,
                timing,
                "integration",
                lambda: integrate_registered_frames(
                    args.out,
                    plan_path=args.plan,
                    backend=args.backend,
                    tile_size=args.tile_size,
                    weighting_override=args.integration_weighting,
                    rejection_override=args.integration_rejection,
                ),
            )
            state.completed_stages.append("integration")
            state.current_stage = "integration"
        write_run_state(args.out, state)
        console.print(f"Run complete through {state.current_stage}: {args.out}")
        return 0
    out = Path(args.out)
    state = initialize_run(out)
    state.current_stage = args.until_stage or "created"
    state.warnings.append("full pipeline execution is gated; current implementation stops after planning")
    write_run_state(out, state)
    console.print("Run state initialized. Full execution is implemented in later gates.")
    return 0


def cmd_resume(args: argparse.Namespace) -> int:
    run = Path(args.run)
    plan_path = run / "processing_plan.json"
    manifest_path = run / "manifest.json"
    if (run / "integration_results.json").exists():
        console.print(resume_summary(args.run))
        console.print("Run already has integration_results.json; no stages repeated.")
        return 0
    if plan_path.exists():
        plan = read_json(plan_path)
        if not plan.get("executable", False):
            console.print(resume_summary(args.run))
            console.print("Processing plan is not executable; nothing to resume.")
            return 0
        timing = _new_timing("resume", "auto", 512)
        state = _resume_pipeline(plan_path, run, "auto", 512, timing)
        state.completed_stages.insert(0, "plan")
        if manifest_path.exists():
            state.completed_stages.insert(0, "scan")
        state.completed_stages.append("report")
        state.current_stage = "report"
        write_run_state(run, state)
        _write_run_report(run, run / "report.html", manifest_path, plan_path)
        console.print(f"Resume complete: {run}")
        return 0
    console.print(resume_summary(args.run))
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    comparison = compare_fits(
        args.glass,
        args.reference,
        glass_time_seconds=args.glass_time_seconds,
        reference_time_seconds=args.reference_time_seconds,
        glass_label=args.glass_label,
        reference_label=args.reference_label,
        glass_scale=args.glass_scale,
        glass_offset=args.glass_offset,
        clip_low=args.clip_low,
        clip_high=args.clip_high,
        diagnostics_dir=args.diagnostics_dir,
        diagnostic_max_size=args.diagnostic_max_size,
        hotspot_tile_size=args.hotspot_tile_size,
        ignore_border_px=args.ignore_border_px,
        glass_coverage_map=args.glass_coverage_map,
        min_coverage=args.min_coverage,
    )
    write_json(Path(args.out).with_suffix(".json"), comparison)
    write_compare_report(args.out, comparison)
    console.print(f"Wrote compare report: {args.out}")
    return 0


def cmd_speedup_summary(args: argparse.Namespace) -> int:
    summary = summarize_wbpp_speedup(
        args.glass_run,
        args.wbpp_result,
        compare_json=args.compare_json,
        min_speedup=args.min_speedup,
    )
    write_speedup_summary(args.out, summary, markdown=args.markdown)
    console.print(
        {
            "speedup_vs_wbpp": summary["speedup_vs_wbpp"],
            "meets_min_speedup": summary["meets_min_speedup"],
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 0


def cmd_acceptance_audit(args: argparse.Namespace) -> int:
    audit = build_acceptance_audit(
        manifest_path=args.manifest,
        glass_run=args.glass_run,
        wbpp_result=args.wbpp_result,
        compare_json=args.compare_json,
        min_lights=args.min_lights,
        min_bias=args.min_bias,
        min_dark=args.min_dark,
        min_flat=args.min_flat,
        min_active_frames=args.min_active_frames,
        min_speedup=args.min_speedup,
        min_coverage_fraction=args.min_coverage_fraction,
        max_rms_diff=args.max_rms_diff,
        max_abs_diff_p99=args.max_abs_diff_p99,
    )
    write_acceptance_audit(args.out, audit, markdown=args.markdown)
    console.print(
        {
            "status": audit["status"],
            "speedup_vs_wbpp": audit["speedup_summary"]["speedup_vs_wbpp"],
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 0 if audit["passed"] else 2


def cmd_blackbox_package(args: argparse.Namespace) -> int:
    payload = create_blackbox_package(
        args.manifest,
        args.plan,
        args.out,
        glass_run=args.glass_run,
        glass_time_seconds=args.glass_time_seconds,
        reference_label=args.reference_label,
    )
    console.print(f"Wrote black-box package: {args.out}")
    console.print(payload)
    return 0


def cmd_blackbox_finalize(args: argparse.Namespace) -> int:
    payload = finalize_blackbox_package(args.timing, args.out)
    console.print(f"Wrote black-box finalize summary: {args.out or Path(args.timing).parent}")
    console.print(payload)
    return 0 if payload.get("status") == "complete" else 2


def cmd_blackbox_history(args: argparse.Namespace) -> int:
    payload = read_fastintegration_history(args.master, max_bytes=args.max_bytes)
    write_json(args.out, payload)
    console.print(f"Wrote WBPP FastIntegration history: {args.out}")
    console.print(payload["summary"])
    return 0


def cmd_synthetic(args: argparse.Namespace) -> int:
    generate_synthetic_dataset(
        args.out,
        frames=args.frames,
        width=args.width,
        height=args.height,
        filt=args.filter,
        known_shift=args.known_shift,
    )
    console.print(f"Wrote synthetic dataset: {args.out}")
    return 0


def _doctor_payload() -> dict:
    cuda_importable = importlib.util.find_spec("glass_cuda") is not None
    cuda_info: dict = {
        "wrapper_importable": cuda_importable,
        "native_extension_loaded": False,
        "cuda_available": False,
        "devices": [],
        "error": None,
    }
    if cuda_importable:
        try:
            import glass_cuda  # type: ignore

            cuda_info["native_extension_loaded"] = bool(
                getattr(glass_cuda, "native_extension_loaded", lambda: False)()
            )
            cuda_info["cuda_available"] = bool(getattr(glass_cuda, "cuda_available", lambda: False)())
            cuda_info["devices"] = list(getattr(glass_cuda, "list_devices", lambda: [])())
        except Exception as exc:  # pragma: no cover - environment-specific diagnostic path
            cuda_info["error"] = str(exc)
    return {
        "schema_version": 1,
        "product": "GLASS",
        "full_name": "GPU-Accelerated Lightframe Alignment and Stacking System",
        "python": {
            "version": sys.version.split()[0],
            "executable": sys.executable,
            "platform": platform.platform(),
        },
        "capabilities": capability_report(),
        "cuda": cuda_info,
        "recommendation": (
            "cuda"
            if cuda_info["cuda_available"]
            else "cpu; install a GLASS CUDA wheel and update the NVIDIA driver to enable GPU acceleration"
        ),
    }


def cmd_doctor(args: argparse.Namespace) -> int:
    payload = _doctor_payload()
    if args.json:
        write_json(args.json, payload)
        console.print(f"Wrote GLASS doctor report: {args.json}")
    console.print("GLASS Doctor")
    console.print(f"Python: {payload['python']['version']} ({payload['python']['platform']})")
    cuda = payload["cuda"]
    console.print(f"CUDA wrapper importable: {cuda['wrapper_importable']}")
    console.print(f"CUDA native extension loaded: {cuda['native_extension_loaded']}")
    console.print(f"CUDA available: {cuda['cuda_available']}")
    if cuda.get("error"):
        console.print(f"CUDA error: {cuda['error']}")
    devices = cuda.get("devices") or []
    if devices:
        for device in devices:
            name = device.get("name", "unknown")
            cc = device.get("compute_capability", device.get("major_minor", "unknown"))
            memory = device.get("memory_total_mib", device.get("total_global_mem_mib", "unknown"))
            driver = device.get("driver_version", "unknown")
            console.print(f"GPU {device.get('device_id', '?')}: {name}, cc={cc}, VRAM={memory} MiB, driver={driver}")
    else:
        console.print("GPU: none detected by GLASS")
    console.print(f"Recommendation: {payload['recommendation']}")
    return 0 if cuda["cuda_available"] or args.allow_cpu_only else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="glass")
    parser.add_argument("--version", action="version", version="glass 0.1.0")
    sub = parser.add_subparsers(dest="command", required=True)

    doctor = sub.add_parser("doctor", help="diagnose GLASS CPU/CUDA runtime availability")
    doctor.add_argument("--json", help="optional output JSON report")
    doctor.add_argument("--allow-cpu-only", action="store_true", help="return success when CUDA is unavailable")
    doctor.set_defaults(func=cmd_doctor)

    scan = sub.add_parser("scan", help="scan FITS/FIT/XISF metadata")
    scan.add_argument("--root", required=True)
    scan.add_argument("--out", required=True)
    scan.set_defaults(func=cmd_scan)

    plan = sub.add_parser("plan", help="build processing_plan.json from a manifest")
    plan.add_argument("--manifest", required=True)
    plan.add_argument("--out", required=True)
    plan.set_defaults(func=cmd_plan)

    subset = sub.add_parser("subset", help="select a small executable subset from a manifest")
    subset.add_argument("--manifest", required=True)
    subset.add_argument("--out", required=True)
    subset.add_argument("--plan-out")
    subset.add_argument("--object")
    subset.add_argument("--filter")
    subset.add_argument("--exposure-s", type=float)
    subset.add_argument("--light-limit", type=int, default=2)
    subset.add_argument("--bias-limit", type=int, default=1)
    subset.add_argument("--dark-limit", type=int, default=1)
    subset.add_argument("--flat-limit", type=int, default=1)
    subset.add_argument(
        "--all-compatible-calibration",
        action="store_true",
        help="include all compatible calibration frames, not only the planner-selected matching groups",
    )
    subset.set_defaults(func=cmd_subset)

    run = sub.add_parser("run", help="execute the gated pipeline")
    run.add_argument("--plan", required=True)
    run.add_argument("--out", required=True)
    run.add_argument("--backend", choices=["cpu", "cuda", "auto"], default="auto")
    run.add_argument("--vram-budget-gb", type=float)
    run.add_argument("--ram-budget-gb", type=float)
    run.add_argument("--until-stage")
    run.add_argument("--tile-size", type=int, default=512)
    run.add_argument(
        "--registration-method",
        choices=["auto", "star", "astroalign", "cuda_catalog", "cuda_triangle"],
        default="auto",
        help=(
            "tile-mode registration method; astroalign uses the optional open-source glass[align] backend, "
            "cuda_catalog and cuda_triangle require the native CUDA backend"
        ),
    )
    run.add_argument(
        "--registration-preview-max-dimension",
        type=int,
        default=1024,
        help="maximum preview width/height used by tile-mode streaming registration",
    )
    run.add_argument(
        "--memory-mode",
        choices=["tile", "resident"],
        default="tile",
        help="execution memory strategy; resident currently covers CUDA calibration plus integration",
    )
    run.add_argument(
        "--resident-prefetch-frames",
        type=int,
        default=0,
        help="number of light frames to prefetch into CPU RAM ahead of resident CUDA calibration",
    )
    run.add_argument(
        "--resident-prefetch-workers",
        type=int,
        default=1,
        help="worker threads used for resident light-frame CPU RAM prefetch",
    )
    run.add_argument(
        "--resident-h2d-mode",
        choices=["pageable", "pinned_async", "pinned_ring"],
        default="pageable",
        help=(
            "resident light upload mode: pageable cudaMemcpy, native pinned staging plus async H2D, "
            "or prefetch-ring pinned slots plus async H2D"
        ),
    )
    run.add_argument("--local-normalization", choices=["auto", "on", "off"], default="auto")
    run.add_argument("--integration-weighting", choices=["auto", "none", "simple_snr"], default="auto")
    run.add_argument(
        "--integration-rejection",
        choices=["auto", "none", "sigma_clip", "winsorized_sigma"],
        default="auto",
    )
    run.add_argument("--allow-partial", action="store_true")
    run.add_argument("--flat-floor", type=float, help="override calibration flat floor for this run")
    run.add_argument(
        "--resident-registration",
        choices=[
            "off",
            "translation_preview",
            "translation_ncc_subpixel",
            "translation_star_catalog",
            "similarity_cuda_catalog",
            "similarity_cuda_triangle",
            "external_matrix",
        ],
        default="off",
        help=(
            "resident CUDA registration mode; translation_preview uses downsampled phase correlation, "
            "translation_ncc_subpixel uses resident GPU NCC plus subpixel refinement, "
            "translation_star_catalog uses GPU star candidates plus pair-offset voting, "
            "similarity_cuda_catalog uses resident GPU star catalogs plus CUDA similarity refinement, "
            "similarity_cuda_triangle uses resident GPU star catalogs plus CUDA triangle descriptors, "
            "external_matrix applies matrices from a prior registration_results.json"
        ),
    )
    run.add_argument(
        "--resident-registration-results",
        help="registration_results.json to consume when --resident-registration external_matrix is selected",
    )
    run.add_argument(
        "--resident-warp-interpolation",
        choices=["bilinear", "lanczos3"],
        default="bilinear",
        help="resident CUDA matrix warp interpolation for similarity/external registration",
    )
    run.add_argument(
        "--resident-warp-clamping-threshold",
        type=float,
        default=-1.0,
        help="Lanczos3 local overshoot clamp threshold; negative disables clamping",
    )
    run.add_argument("--resident-registration-max-shift", type=int, default=128)
    run.add_argument(
        "--resident-ncc-sample-stride",
        type=int,
        default=1,
        help="sample every Nth pixel in resident GPU NCC registration; 1 keeps full-resolution scoring",
    )
    run.add_argument(
        "--resident-ncc-fallback-score-threshold",
        type=float,
        default=0.0,
        help=(
            "when resident NCC sample stride is greater than 1, rerun low-score frames at full stride 1; "
            "0 disables fallback"
        ),
    )
    run.add_argument("--resident-subpixel-radius-steps", type=int, default=4)
    run.add_argument("--resident-subpixel-step", type=float, default=0.25)
    run.add_argument(
        "--resident-star-threshold",
        type=float,
        default=30.0,
        help="fixed resident star threshold; use 0 or a negative value for GPU mean/std auto-threshold trials",
    )
    run.add_argument("--resident-star-max-candidates", type=int, default=64)
    run.add_argument("--resident-star-tolerance-px", type=float, default=1.0)
    run.add_argument("--resident-star-grid-cols", type=int, default=0)
    run.add_argument("--resident-star-grid-rows", type=int, default=0)
    run.add_argument(
        "--resident-star-prior",
        choices=["none", "ncc", "auto_pierside"],
        default="none",
        help=(
            "optional prior for resident star-catalog voting: none, ncc, or auto_pierside "
            "to use PIERSIDE metadata for same-side NCC and flipped-side wide rotation search"
        ),
    )
    run.add_argument("--resident-star-prior-radius-px", type=float, default=4.0)
    run.add_argument(
        "--resident-local-normalization-mode",
        choices=["global_mean_std", "grid_mean_std"],
        default="global_mean_std",
        help="resident CUDA LN coefficient model used when --local-normalization enables LN",
    )
    run.add_argument(
        "--resident-local-normalization-tile-size",
        type=int,
        default=512,
        help="tile size for resident grid_mean_std local normalization",
    )
    run.add_argument(
        "--resident-star-core-preselect-top-k",
        type=int,
        default=0,
        help=(
            "for resident similarity_cuda_catalog, use GPU star-core metrics to preselect this many "
            "candidate matrices before pixel refinement; 0 disables preselection"
        ),
    )
    run.add_argument(
        "--resident-triangle-pixel-refine-coarse-stride",
        type=int,
        help="override resident triangle pixel-refine coarse sample stride",
    )
    run.add_argument(
        "--resident-triangle-pixel-refine-final-stride",
        type=int,
        help="override resident triangle pixel-refine final sample stride",
    )
    run.add_argument(
        "--reference-frame-id",
        help="reference frame id, file name, or stem for registration",
    )
    run.add_argument(
        "--exclude-frame-id",
        action="append",
        default=[],
        help="frame id, file name, or stem to exclude from resident integration; can be repeated",
    )
    run.set_defaults(func=cmd_run)

    resume = sub.add_parser("resume", help="resume a run directory")
    resume.add_argument("--run", required=True)
    resume.set_defaults(func=cmd_resume)

    report = sub.add_parser("report", help="write an HTML report")
    report.add_argument("--run", required=True)
    report.add_argument("--out", required=True)
    report.add_argument("--manifest")
    report.add_argument("--plan")
    report.set_defaults(func=cmd_report)

    audit = sub.add_parser("audit", help="scan, plan, and report in one command")
    audit.add_argument("--root", required=True)
    audit.add_argument("--out", required=True)
    audit.add_argument("--backend", choices=["cpu", "cuda", "auto"], default="auto")
    audit.add_argument("--tile-size", type=int, default=512)
    audit.add_argument(
        "--memory-mode",
        choices=["tile", "resident"],
        default="tile",
        help="execution memory strategy for the run portion of audit",
    )
    audit.add_argument(
        "--resident-prefetch-frames",
        type=int,
        default=0,
        help="number of light frames to prefetch into CPU RAM ahead of resident CUDA calibration",
    )
    audit.add_argument(
        "--resident-prefetch-workers",
        type=int,
        default=1,
        help="worker threads used for resident light-frame CPU RAM prefetch",
    )
    audit.add_argument(
        "--resident-h2d-mode",
        choices=["pageable", "pinned_async", "pinned_ring"],
        default="pageable",
        help="resident light upload mode for resident audit",
    )
    audit.add_argument(
        "--registration-method",
        choices=["auto", "star", "astroalign", "cuda_catalog", "cuda_triangle"],
        default="auto",
        help="registration method passed to the gated run portion of audit",
    )
    audit.add_argument("--local-normalization", choices=["auto", "on", "off"], default="auto")
    audit.add_argument("--integration-weighting", choices=["auto", "none", "simple_snr"], default="auto")
    audit.add_argument(
        "--integration-rejection",
        choices=["auto", "none", "sigma_clip", "winsorized_sigma"],
        default="auto",
    )
    audit.add_argument("--flat-floor", type=float, help="override calibration flat floor for resident audit")
    audit.add_argument(
        "--resident-registration",
        choices=[
            "off",
            "translation_preview",
            "translation_ncc_subpixel",
            "translation_star_catalog",
            "similarity_cuda_catalog",
            "similarity_cuda_triangle",
            "external_matrix",
        ],
        default="off",
        help="resident CUDA registration mode for --memory-mode resident",
    )
    audit.add_argument(
        "--resident-registration-results",
        help="registration_results.json consumed by resident external_matrix audit",
    )
    audit.add_argument(
        "--resident-warp-interpolation",
        choices=["bilinear", "lanczos3"],
        default="bilinear",
        help="resident CUDA matrix warp interpolation for resident audit",
    )
    audit.add_argument("--resident-warp-clamping-threshold", type=float, default=-1.0)
    audit.add_argument("--resident-registration-max-shift", type=int, default=128)
    audit.add_argument("--resident-ncc-sample-stride", type=int, default=1)
    audit.add_argument("--resident-ncc-fallback-score-threshold", type=float, default=0.0)
    audit.add_argument("--resident-subpixel-radius-steps", type=int, default=4)
    audit.add_argument("--resident-subpixel-step", type=float, default=0.25)
    audit.add_argument(
        "--resident-star-threshold",
        type=float,
        default=30.0,
        help="fixed resident star threshold; use 0 or negative for GPU mean/std auto-threshold trials",
    )
    audit.add_argument("--resident-star-max-candidates", type=int, default=64)
    audit.add_argument("--resident-star-tolerance-px", type=float, default=1.0)
    audit.add_argument("--resident-star-grid-cols", type=int, default=0)
    audit.add_argument("--resident-star-grid-rows", type=int, default=0)
    audit.add_argument(
        "--resident-star-prior",
        choices=["none", "ncc", "auto_pierside"],
        default="none",
        help="optional prior for resident star-catalog voting in resident audit",
    )
    audit.add_argument("--resident-star-prior-radius-px", type=float, default=4.0)
    audit.add_argument(
        "--resident-star-core-preselect-top-k",
        type=int,
        default=0,
        help="preselect resident similarity candidates with GPU star-core metrics before pixel refinement",
    )
    audit.add_argument(
        "--resident-triangle-pixel-refine-coarse-stride",
        type=int,
        help="override resident triangle pixel-refine coarse sample stride for resident audit",
    )
    audit.add_argument(
        "--resident-triangle-pixel-refine-final-stride",
        type=int,
        help="override resident triangle pixel-refine final sample stride for resident audit",
    )
    audit.add_argument(
        "--resident-local-normalization-mode",
        choices=["global_mean_std", "grid_mean_std"],
        default="global_mean_std",
        help="resident CUDA LN coefficient model used when audit enables LN",
    )
    audit.add_argument("--resident-local-normalization-tile-size", type=int, default=512)
    audit.add_argument("--reference-frame-id")
    audit.add_argument("--exclude-frame-id", action="append", default=[])
    audit.set_defaults(func=cmd_audit)

    compare = sub.add_parser("compare", help="compare GLASS output to a black-box reference")
    compare.add_argument("--glass", required=True)
    compare.add_argument("--reference", required=True)
    compare.add_argument("--out", required=True)
    compare.add_argument("--glass-time-seconds", type=float)
    compare.add_argument("--reference-time-seconds", type=float)
    compare.add_argument("--glass-label", default="GLASS")
    compare.add_argument("--reference-label", default="reference")
    compare.add_argument("--glass-scale", type=float, help="scale GLASS pixels before comparison")
    compare.add_argument("--glass-offset", type=float, help="offset GLASS pixels before comparison")
    compare.add_argument("--clip-low", type=float, help="clip transformed GLASS pixels to this lower bound")
    compare.add_argument("--clip-high", type=float, help="clip transformed GLASS pixels to this upper bound")
    compare.add_argument("--diagnostics-dir", help="optional directory for compare preview PNGs and residual hotspots")
    compare.add_argument("--diagnostic-max-size", type=int, default=1024, help="maximum preview PNG width or height")
    compare.add_argument("--hotspot-tile-size", type=int, default=512, help="tile size for residual hotspot ranking")
    compare.add_argument("--ignore-border-px", type=int, default=0, help="ignore this many pixels on each edge for metrics")
    compare.add_argument("--glass-coverage-map", help="optional GLASS coverage map used to mask comparison metrics")
    compare.add_argument("--min-coverage", type=float, help="minimum GLASS coverage required for comparison metrics")
    compare.set_defaults(func=cmd_compare)

    speedup = sub.add_parser("speedup-summary", help="summarize GLASS timing against WBPP black-box timing")
    speedup.add_argument("--glass-run", required=True, help="GLASS run directory containing run_timing.json")
    speedup.add_argument("--wbpp-result", required=True, help="user-generated PixInsight/WBPP black-box result JSON")
    speedup.add_argument("--compare-json", help="optional GLASS compare JSON with image-difference metrics")
    speedup.add_argument("--out", required=True, help="output summary JSON")
    speedup.add_argument("--markdown", help="optional output Markdown summary")
    speedup.add_argument("--min-speedup", type=float, default=1.25)
    speedup.set_defaults(func=cmd_speedup_summary)

    acceptance = sub.add_parser(
        "acceptance-audit",
        help="verify a real GLASS/WBPP acceptance benchmark from existing artifacts",
    )
    acceptance.add_argument("--manifest", required=True, help="manifest.json used for the benchmark")
    acceptance.add_argument("--glass-run", required=True, help="GLASS run directory")
    acceptance.add_argument("--wbpp-result", required=True, help="user-generated WBPP black-box result JSON")
    acceptance.add_argument("--compare-json", required=True, help="coverage-masked or full compare JSON")
    acceptance.add_argument("--out", required=True, help="output acceptance audit JSON")
    acceptance.add_argument("--markdown", help="optional output Markdown summary")
    acceptance.add_argument("--min-lights", type=int, default=200)
    acceptance.add_argument("--min-bias", type=int, default=20)
    acceptance.add_argument("--min-dark", type=int, default=20)
    acceptance.add_argument("--min-flat", type=int, default=20)
    acceptance.add_argument("--min-active-frames", type=int, default=1)
    acceptance.add_argument("--min-speedup", type=float, default=2.0)
    acceptance.add_argument("--min-coverage-fraction", type=float, default=0.95)
    acceptance.add_argument("--max-rms-diff", type=float, default=0.01)
    acceptance.add_argument("--max-abs-diff-p99", type=float, default=0.01)
    acceptance.set_defaults(func=cmd_acceptance_audit)

    blackbox = sub.add_parser("blackbox-package", help="write a PixInsight/WBPP black-box handoff package")
    blackbox.add_argument("--manifest", required=True)
    blackbox.add_argument("--out", required=True)
    blackbox.add_argument("--plan")
    blackbox.add_argument("--glass-run")
    blackbox.add_argument("--glass-time-seconds", type=float)
    blackbox.add_argument("--reference-label", default="PixInsight WBPP")
    blackbox.set_defaults(func=cmd_blackbox_package)

    finalize = sub.add_parser("blackbox-finalize", help="finalize a PixInsight/WBPP black-box timing package")
    finalize.add_argument("--timing", required=True)
    finalize.add_argument("--out")
    finalize.set_defaults(func=cmd_blackbox_finalize)

    history = sub.add_parser(
        "blackbox-history",
        help="extract user-generated WBPP FastIntegration ProcessingHistory from a XISF master",
    )
    history.add_argument("--master", required=True)
    history.add_argument("--out", required=True)
    history.add_argument("--max-bytes", type=int, default=32 * 1024 * 1024)
    history.set_defaults(func=cmd_blackbox_history)

    synthetic = sub.add_parser("synthetic", help="generate synthetic FITS data")
    synthetic.add_argument("--out", required=True)
    synthetic.add_argument("--frames", type=int, default=20)
    synthetic.add_argument("--width", type=int, default=512)
    synthetic.add_argument("--height", type=int, default=512)
    synthetic.add_argument("--filter", default="H")
    synthetic.add_argument("--known-shift", action="store_true")
    synthetic.set_defaults(func=cmd_synthetic)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
