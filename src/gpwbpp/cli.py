from __future__ import annotations

import argparse
from pathlib import Path

from rich.console import Console

from gpwbpp.capabilities import capability_report
from gpwbpp.engine.pipeline import initialize_run, run_calibration_stages
from gpwbpp.engine.quality import measure_calibrated_quality
from gpwbpp.engine.registration import register_calibrated_frames
from gpwbpp.engine.resume import resume_summary
from gpwbpp.engine.state import write_run_state
from gpwbpp.io.json_io import read_json, write_json
from gpwbpp.metadata.scanner import scan_tree
from gpwbpp.planner.plan_builder import build_processing_plan
from gpwbpp.report.compare_report import compare_fits, write_compare_report
from gpwbpp.report.html_report import write_html_report
from gpwbpp.synthetic.generator import generate_synthetic_dataset

console = Console()


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


def cmd_report(args: argparse.Namespace) -> int:
    run = Path(args.run)
    manifest_path = Path(args.manifest) if args.manifest else run / "manifest.json"
    plan_path = Path(args.plan) if args.plan else run / "processing_plan.json"
    manifest = read_json(manifest_path) if manifest_path.exists() else None
    plan = read_json(plan_path) if plan_path.exists() else None
    quality_path = run / "frame_quality.json"
    registration_path = run / "registration_results.json"
    quality = read_json(quality_path) if quality_path.exists() else None
    registration = read_json(registration_path) if registration_path.exists() else None
    write_html_report(args.out, manifest=manifest, plan=plan, quality=quality, registration=registration)
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
    manifest = scan_tree(args.root)
    write_json(manifest_path, manifest)
    plan = build_processing_plan(manifest, manifest_path)
    write_json(plan_path, plan)
    state = initialize_run(out)
    state.completed_stages.extend(["scan", "plan", "report"])
    state.current_stage = "report"
    write_run_state(out, state)
    write_html_report(report_path, manifest=manifest, plan=read_json(plan_path))
    console.print(f"Audit complete: {out}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    capabilities = capability_report()
    if args.backend == "cuda" and not capabilities["cuda_available"]:
        raise SystemExit("CUDA backend requested but native CUDA backend is unavailable.")
    implemented_stages = {
        "master_calibration",
        "light_calibration",
        "calibration",
        "quality",
        "registration",
    }
    if args.until_stage not in implemented_stages:
        if args.allow_partial:
            console.print("Only calibration stages are implemented; initializing partial run state.")
        else:
            raise SystemExit(
                "Current gated runner supports --until-stage calibration, quality, or registration only. "
                "Use --allow-partial to write a diagnostic run_state without executing later stages."
            )
    if args.until_stage in implemented_stages:
        state = run_calibration_stages(args.plan, args.out, backend=args.backend, tile_size=args.tile_size)
        if args.until_stage in {"quality", "registration"}:
            measure_calibrated_quality(args.out)
            state.completed_stages.append("quality")
            state.current_stage = "quality"
        if args.until_stage == "registration":
            register_calibrated_frames(args.out)
            state.completed_stages.append("registration")
            state.current_stage = "registration"
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
    console.print(resume_summary(args.run))
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    comparison = compare_fits(args.gpwbpp, args.reference)
    write_json(Path(args.out).with_suffix(".json"), comparison)
    write_compare_report(args.out, comparison)
    console.print(f"Wrote compare report: {args.out}")
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

    run = sub.add_parser("run", help="execute the gated pipeline")
    run.add_argument("--plan", required=True)
    run.add_argument("--out", required=True)
    run.add_argument("--backend", choices=["cpu", "cuda", "auto"], default="auto")
    run.add_argument("--vram-budget-gb", type=float)
    run.add_argument("--ram-budget-gb", type=float)
    run.add_argument("--until-stage")
    run.add_argument("--tile-size", type=int, default=512)
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
    audit.set_defaults(func=cmd_audit)

    compare = sub.add_parser("compare", help="compare GPWBPP output to a black-box reference")
    compare.add_argument("--gpwbpp", required=True)
    compare.add_argument("--reference", required=True)
    compare.add_argument("--out", required=True)
    compare.set_defaults(func=cmd_compare)

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
