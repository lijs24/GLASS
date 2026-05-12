from __future__ import annotations

import argparse
from time import perf_counter
from pathlib import Path

from rich.console import Console

from gpwbpp.capabilities import capability_report
from gpwbpp.engine.integration import integrate_registered_frames
from gpwbpp.engine.local_norm import local_normalize_registered_frames
from gpwbpp.engine.pipeline import initialize_run, run_calibration_stages
from gpwbpp.engine.quality import measure_calibrated_quality
from gpwbpp.engine.registration import register_calibrated_frames
from gpwbpp.engine.resident_cuda import run_resident_calibration_integration
from gpwbpp.engine.warp import warp_registered_frames
from gpwbpp.engine.resume import resume_summary
from gpwbpp.engine.state import write_run_state
from gpwbpp.io.json_io import read_json, write_json
from gpwbpp.metadata.scanner import scan_tree
from gpwbpp.planner.plan_builder import build_processing_plan
from gpwbpp.planner.subset import build_subset_manifest
from gpwbpp.report.blackbox_package import create_blackbox_package, finalize_blackbox_package
from gpwbpp.report.compare_report import compare_fits, write_compare_report
from gpwbpp.report.html_report import write_html_report
from gpwbpp.synthetic.generator import generate_synthetic_dataset
from gpwbpp.models import now_iso

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
    _timed_stage(out, timing, "registration", lambda: register_calibrated_frames(out, tile_size=tile_size))
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
        return _run_full_pipeline(plan_path, out, backend, tile_size, "auto", "auto", "auto", timing)

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
    manifest_path = out / "manifest.json"
    plan_path = out / "processing_plan.json"
    report_path = out / "report.html"
    timing = _new_timing("audit", args.backend, args.tile_size)
    manifest = _timed_stage(out, timing, "scan", lambda: scan_tree(args.root))
    write_json(manifest_path, manifest)
    plan = _timed_stage(out, timing, "plan", lambda: build_processing_plan(manifest, manifest_path))
    write_json(plan_path, plan)
    if plan.executable:
        state = _run_full_pipeline(
            plan_path,
            out,
            args.backend,
            args.tile_size,
            args.local_normalization,
            args.integration_weighting,
            args.integration_rejection,
            timing,
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
        if args.local_normalization == "on":
            raise SystemExit("Resident memory mode does not include materialized local normalization yet.")
        if args.integration_rejection not in {"auto", "none", "sigma_clip", "winsorized_sigma"}:
            raise SystemExit(
                "Resident memory mode currently supports --integration-rejection none, "
                "sigma_clip, or winsorized_sigma."
            )
        if args.integration_weighting not in {"auto", "none"}:
            raise SystemExit("Resident memory mode currently supports --integration-weighting none only.")
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
            lambda: run_calibration_stages(args.plan, args.out, backend=args.backend, tile_size=args.tile_size),
        )
        if args.until_stage in {"quality", "registration", "warp", "local_normalization", "integration"}:
            _timed_stage(out, timing, "quality", lambda: measure_calibrated_quality(args.out, tile_size=args.tile_size))
            state.completed_stages.append("quality")
            state.current_stage = "quality"
        if args.until_stage in {"registration", "warp", "local_normalization", "integration"}:
            _timed_stage(out, timing, "registration", lambda: register_calibrated_frames(args.out, tile_size=args.tile_size))
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
        args.gpwbpp,
        args.reference,
        gpwbpp_time_seconds=args.gpwbpp_time_seconds,
        reference_time_seconds=args.reference_time_seconds,
        gpwbpp_label=args.gpwbpp_label,
        reference_label=args.reference_label,
        gpwbpp_scale=args.gpwbpp_scale,
        gpwbpp_offset=args.gpwbpp_offset,
        clip_low=args.clip_low,
        clip_high=args.clip_high,
    )
    write_json(Path(args.out).with_suffix(".json"), comparison)
    write_compare_report(args.out, comparison)
    console.print(f"Wrote compare report: {args.out}")
    return 0


def cmd_blackbox_package(args: argparse.Namespace) -> int:
    payload = create_blackbox_package(
        args.manifest,
        args.plan,
        args.out,
        gpwbpp_run=args.gpwbpp_run,
        gpwbpp_time_seconds=args.gpwbpp_time_seconds,
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gpwbpp")
    parser.add_argument("--version", action="version", version="gpwbpp 0.1.0")
    sub = parser.add_subparsers(dest="command", required=True)

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
        "--memory-mode",
        choices=["tile", "resident"],
        default="tile",
        help="execution memory strategy; resident currently covers CUDA calibration plus mean integration",
    )
    run.add_argument("--local-normalization", choices=["auto", "on", "off"], default="auto")
    run.add_argument("--integration-weighting", choices=["auto", "none", "simple_snr"], default="auto")
    run.add_argument(
        "--integration-rejection",
        choices=["auto", "none", "sigma_clip", "winsorized_sigma"],
        default="auto",
    )
    run.add_argument("--allow-partial", action="store_true")
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
    audit.add_argument("--local-normalization", choices=["auto", "on", "off"], default="auto")
    audit.add_argument("--integration-weighting", choices=["auto", "none", "simple_snr"], default="auto")
    audit.add_argument(
        "--integration-rejection",
        choices=["auto", "none", "sigma_clip", "winsorized_sigma"],
        default="auto",
    )
    audit.set_defaults(func=cmd_audit)

    compare = sub.add_parser("compare", help="compare GPWBPP output to a black-box reference")
    compare.add_argument("--gpwbpp", required=True)
    compare.add_argument("--reference", required=True)
    compare.add_argument("--out", required=True)
    compare.add_argument("--gpwbpp-time-seconds", type=float)
    compare.add_argument("--reference-time-seconds", type=float)
    compare.add_argument("--gpwbpp-label", default="GPWBPP")
    compare.add_argument("--reference-label", default="reference")
    compare.add_argument("--gpwbpp-scale", type=float, help="scale GPWBPP pixels before comparison")
    compare.add_argument("--gpwbpp-offset", type=float, help="offset GPWBPP pixels before comparison")
    compare.add_argument("--clip-low", type=float, help="clip transformed GPWBPP pixels to this lower bound")
    compare.add_argument("--clip-high", type=float, help="clip transformed GPWBPP pixels to this upper bound")
    compare.set_defaults(func=cmd_compare)

    blackbox = sub.add_parser("blackbox-package", help="write a PixInsight/WBPP black-box handoff package")
    blackbox.add_argument("--manifest", required=True)
    blackbox.add_argument("--out", required=True)
    blackbox.add_argument("--plan")
    blackbox.add_argument("--gpwbpp-run")
    blackbox.add_argument("--gpwbpp-time-seconds", type=float)
    blackbox.add_argument("--reference-label", default="PixInsight WBPP")
    blackbox.set_defaults(func=cmd_blackbox_package)

    finalize = sub.add_parser("blackbox-finalize", help="finalize a PixInsight/WBPP black-box timing package")
    finalize.add_argument("--timing", required=True)
    finalize.add_argument("--out")
    finalize.set_defaults(func=cmd_blackbox_finalize)

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
