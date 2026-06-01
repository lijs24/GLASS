from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glass.io.json_io import read_json
from glass.report.resident_sweep import (
    build_resident_sweep_variants,
    load_resident_run_summary,
    parse_int_grid,
    parse_mode_grid,
    variant_run_args,
    write_resident_sweep_summary,
)

_SWEEP_MANAGED_RUN_OPTIONS = {
    "--plan": 1,
    "--out": 1,
    "--backend": 1,
    "--until-stage": 1,
    "--memory-mode": 1,
    "--resident-prefetch-frames": 1,
    "--resident-prefetch-workers": 1,
    "--resident-prefetch-refill-mode": 1,
    "--resident-h2d-mode": 1,
    "--resident-calibration-batch-frames": 1,
    "--resident-calibration-streams": 1,
    "--resident-calibration-wave-frames": 1,
    "--resident-calibration-release-mode": 1,
}


def _split_command(value: str | None) -> list[str]:
    if value is None or value.strip() == "":
        return [sys.executable, "-m", "glass.cli"]
    return value.split()


def _split_common_run_args(value: str | None) -> list[str]:
    if value is None or value.strip() == "":
        return []
    return [part.strip("\"'") for part in shlex.split(value, posix=False)]


def _parse_optional_int_grid(value: str | None) -> list[int | None]:
    if value is None or value.strip() == "":
        return [None]
    parsed: list[int | None] = []
    for raw in value.split(","):
        item = str(raw).strip()
        if item in {"", "inherit"}:
            candidate = None
        else:
            numeric = int(item)
            if numeric <= 0:
                raise ValueError("optional integer grids must contain positive values or inherit")
            candidate = numeric
        if candidate not in parsed:
            parsed.append(candidate)
    return parsed


def _parse_optional_float_grid(value: str | None) -> list[float | None]:
    if value is None or value.strip() == "":
        return [None]
    parsed: list[float | None] = []
    for raw in value.split(","):
        item = str(raw).strip()
        if item in {"", "inherit"}:
            candidate = None
        else:
            numeric = float(item)
            if numeric < 0:
                raise ValueError("optional float grids must contain non-negative values or inherit")
            candidate = numeric
        if candidate not in parsed:
            parsed.append(candidate)
    return parsed


def _parse_fast_coarse_modes(value: str | None) -> list[str]:
    modes = parse_mode_grid(value, default=["inherit"])
    allowed = {"inherit", "off", "on"}
    invalid = [mode for mode in modes if mode not in allowed]
    if invalid:
        raise ValueError("triangle fast-coarse modes must be inherit, off, or on")
    return modes


def _common_run_args_from_command_file(path: Path) -> tuple[list[str], dict[str, Any]]:
    tokens = _split_common_run_args(path.read_text(encoding="utf-8"))
    try:
        run_index = tokens.index("run")
    except ValueError as exc:
        raise ValueError(f"baseline command file does not contain a glass run command: {path}") from exc

    imported: list[str] = []
    filtered: list[dict[str, Any]] = []
    source_args = tokens[run_index + 1 :]
    index = 0
    while index < len(source_args):
        token = source_args[index]
        value_count = _SWEEP_MANAGED_RUN_OPTIONS.get(token)
        if value_count is not None:
            filtered.append(
                {
                    "option": token,
                    "value_count": value_count,
                    "values": source_args[index + 1 : index + 1 + value_count],
                }
            )
            index += value_count + 1
            continue
        imported.append(token)
        index += 1
    return imported, {
        "source_command_path": str(path),
        "source_arg_count": len(source_args),
        "imported_arg_count": len(imported),
        "filtered_token_count": sum(1 + int(item["value_count"]) for item in filtered),
        "filtered_managed_options": sorted({str(item["option"]) for item in filtered}),
    }


def _variant_command(
    *,
    glass_command: list[str],
    plan: Path,
    run_dir: Path,
    common_run_args: list[str],
    variant: dict[str, Any],
) -> list[str]:
    return [
        *glass_command,
        "run",
        "--plan",
        str(plan),
        "--out",
        str(run_dir),
        "--backend",
        "cuda",
        "--until-stage",
        "integration",
        "--memory-mode",
        "resident",
        *common_run_args,
        *variant_run_args(variant),
    ]


def _compare_command(
    *,
    glass_command: list[str],
    candidate_master: str,
    reference_master: Path,
    out_html: Path,
    candidate_total_s: float | None,
    reference_total_s: float | None,
    candidate_label: str,
    reference_label: str,
    ignore_border_px: int,
    glass_scale: float | None,
    glass_offset: float | None,
    clip_low: float | None,
    clip_high: float | None,
    glass_coverage_map: str | None,
    min_coverage: float | None,
) -> list[str]:
    command = [
        *glass_command,
        "compare",
        "--glass",
        candidate_master,
        "--reference",
        str(reference_master),
        "--out",
        str(out_html),
        "--glass-label",
        candidate_label,
        "--reference-label",
        reference_label,
        "--ignore-border-px",
        str(ignore_border_px),
    ]
    if candidate_total_s is not None:
        command.extend(["--glass-time-seconds", str(candidate_total_s)])
    if reference_total_s is not None:
        command.extend(["--reference-time-seconds", str(reference_total_s)])
    if glass_scale is not None:
        command.extend(["--glass-scale", str(glass_scale)])
    if glass_offset is not None:
        command.extend(["--glass-offset", str(glass_offset)])
    if clip_low is not None:
        command.extend(["--clip-low", str(clip_low)])
    if clip_high is not None:
        command.extend(["--clip-high", str(clip_high)])
    if glass_coverage_map:
        command.extend(["--glass-coverage-map", str(glass_coverage_map)])
    if min_coverage is not None:
        command.extend(["--min-coverage", str(min_coverage)])
    return command


def _guardrails_command(
    *,
    glass_command: list[str],
    run_dir: Path,
    out_dir: Path,
    stack_scope: str,
    expected_integration_engine: str,
    pixel_verify: bool,
    pixel_verify_tile_size: int,
    pixel_tolerance: int,
) -> list[str]:
    command = [
        *glass_command,
        "guardrails",
        "--run",
        str(run_dir),
        "--out-dir",
        str(out_dir),
        "--stack-scope",
        stack_scope,
        "--expected-integration-engine",
        expected_integration_engine,
        "--pixel-verify-tile-size",
        str(pixel_verify_tile_size),
        "--pixel-tolerance",
        str(pixel_tolerance),
    ]
    if pixel_verify:
        command.append("--pixel-verify")
    return command


def _attach_guardrails_summary(summary: dict[str, Any], guardrails_dir: Path) -> None:
    guardrails_summary_path = guardrails_dir / "guardrails_summary.json"
    if not guardrails_summary_path.exists():
        summary["guardrails"] = {
            "status": "missing",
            "passed": False,
            "summary_path": str(guardrails_summary_path),
        }
        return
    guardrails = read_json(guardrails_summary_path)
    summary["guardrails"] = {
        "status": guardrails.get("status"),
        "passed": bool(guardrails.get("passed")),
        "summary_path": str(guardrails_summary_path),
        "report": (guardrails.get("artifacts") or {}).get("report"),
        "failed": [
            {"name": item.get("name"), "failed": item.get("failed")}
            for item in guardrails.get("checks") or []
            if not item.get("passed")
        ],
    }


def _run_subprocess(command: list[str], *, timeout_seconds: float | None = None) -> dict[str, Any]:
    effective_timeout = None if timeout_seconds is None or timeout_seconds <= 0 else float(timeout_seconds)
    try:
        subprocess.run(command, check=True, timeout=effective_timeout)
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "timeout",
            "passed": False,
            "timeout_s": effective_timeout,
            "error": str(exc),
        }
    except subprocess.CalledProcessError as exc:
        return {
            "status": "failed",
            "passed": False,
            "exit_code": int(exc.returncode),
            "error": str(exc),
        }
    return {"status": "completed", "passed": True}


def _failed_variant_summary(
    *,
    variant: dict[str, Any],
    variant_id: str,
    run_dir: Path,
    result: dict[str, Any],
    guardrails_dir: Path,
    guardrails_requested: bool,
) -> dict[str, Any]:
    summary = {
        "variant": variant,
        "variant_id": variant_id,
        "run_dir": str(run_dir),
        "status": result.get("status", "failed"),
        "total_elapsed_s": None,
        "error": result.get("error"),
        "exit_code": result.get("exit_code"),
        "timeout_s": result.get("timeout_s"),
    }
    if guardrails_requested:
        summary["guardrails"] = {
            "status": "skipped_run_failed",
            "passed": False,
            "out_dir": str(guardrails_dir),
            "reason": result.get("status", "failed"),
        }
    return summary


def _mark_guardrails_failed(
    summary: dict[str, Any],
    *,
    guardrails_dir: Path,
    result: dict[str, Any],
) -> None:
    summary["guardrails"] = {
        "status": result.get("status", "failed"),
        "passed": False,
        "out_dir": str(guardrails_dir),
        "error": result.get("error"),
        "exit_code": result.get("exit_code"),
        "timeout_s": result.get("timeout_s"),
    }


def _attach_compare_summary(summary: dict[str, Any], compare_json_path: Path, compare_html_path: Path) -> None:
    if not compare_json_path.exists():
        summary["compare"] = {
            "status": "missing",
            "json_path": str(compare_json_path),
            "report": str(compare_html_path),
        }
        return
    comparison = read_json(compare_json_path)
    timing = comparison.get("timing") if isinstance(comparison.get("timing"), dict) else {}
    region = comparison.get("comparison_region") if isinstance(comparison.get("comparison_region"), dict) else {}
    summary["compare"] = {
        "status": "completed",
        "json_path": str(compare_json_path),
        "report": str(compare_html_path),
        "shape_match": comparison.get("shape_match"),
        "rms_diff": comparison.get("rms_diff"),
        "relative_rms_diff": comparison.get("relative_rms_diff"),
        "abs_diff_p99": comparison.get("abs_diff_p99"),
        "max_abs_diff": comparison.get("max_abs_diff"),
        "compared_pixels": region.get("compared_pixels"),
        "coverage_fraction": region.get("coverage_fraction"),
        "min_coverage": region.get("min_coverage"),
        "speedup_vs_reference": timing.get("speedup_vs_reference"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run or dry-run a resident CUDA prefetch/batch/stream parameter sweep."
    )
    parser.add_argument("--plan", required=True, help="processing_plan.json")
    parser.add_argument("--out", required=True, help="sweep output directory")
    parser.add_argument("--glass-command", help="command prefix used to invoke GLASS; defaults to this Python")
    parser.add_argument(
        "--common-run-arg",
        action="append",
        default=[],
        help=(
            "single GLASS run argument token applied to every variant; repeat for each token. "
            "Use --common-run-arg=<token> when the token starts with --."
        ),
    )
    parser.add_argument(
        "--common-run-args",
        help="space-separated GLASS run argument string applied to every variant",
    )
    parser.add_argument(
        "--common-run-args-from-command",
        help=(
            "import shared GLASS run arguments from a previous run_command.txt; "
            "sweep-managed plan/out/backend/memory/prefetch/batch flags are filtered out"
        ),
    )
    parser.add_argument("--prefetch-frames", default="16,24,32")
    parser.add_argument("--prefetch-workers", default="8,12")
    parser.add_argument("--batch-frames", default="8")
    parser.add_argument("--streams", default="4")
    parser.add_argument("--wave-frames", default="2,4")
    parser.add_argument("--release-modes", default="callback_queue")
    parser.add_argument("--refill-modes", default="immediate")
    parser.add_argument(
        "--triangle-fast-coarse-modes",
        default="inherit",
        help="comma grid for resident triangle pixel refine fast-coarse mode: inherit,off,on",
    )
    parser.add_argument(
        "--triangle-coarse-strides",
        help="comma grid for resident triangle coarse pixel-refine stride, or inherit",
    )
    parser.add_argument(
        "--triangle-final-strides",
        help="comma grid for resident triangle final pixel-refine stride, or inherit",
    )
    parser.add_argument(
        "--star-max-candidates",
        help="comma grid for resident star max candidates, or inherit",
    )
    parser.add_argument("--star-grid-cols", help="comma grid for resident star grid column counts, or inherit")
    parser.add_argument("--star-grid-rows", help="comma grid for resident star grid row counts, or inherit")
    parser.add_argument(
        "--triangle-grid-top-per-cell",
        help="comma grid for resident triangle grid top-per-cell counts, or inherit",
    )
    parser.add_argument(
        "--triangle-nms-scan-candidates",
        help="comma grid for resident triangle non-grid NMS scan counts, or inherit",
    )
    parser.add_argument(
        "--triangle-nms-min-separation-px",
        help="comma grid for resident triangle NMS minimum separation values, or inherit",
    )
    parser.add_argument("--baseline-total-seconds", type=float)
    parser.add_argument("--reference-master", help="optional master FITS used for post-run compare reports")
    parser.add_argument("--reference-time-seconds", type=float)
    parser.add_argument("--reference-label", default="reference")
    parser.add_argument("--ignore-border-px", type=int, default=16)
    parser.add_argument("--compare-glass-scale", type=float, help="scale candidate pixels before per-variant compare")
    parser.add_argument("--compare-glass-offset", type=float, help="offset candidate pixels before per-variant compare")
    parser.add_argument("--compare-clip-low", type=float, help="clip transformed candidate pixels to this lower bound")
    parser.add_argument("--compare-clip-high", type=float, help="clip transformed candidate pixels to this upper bound")
    parser.add_argument(
        "--compare-use-candidate-coverage-map",
        action="store_true",
        help="pass each candidate resident coverage map to glass compare when available",
    )
    parser.add_argument("--compare-min-coverage", type=float, help="minimum coverage for per-variant compare metrics")
    parser.add_argument(
        "--compare-require-shape-match",
        action="store_true",
        help="require shape_match=true for a variant to pass the compare gate",
    )
    parser.add_argument("--compare-max-rms", type=float, help="maximum rms_diff for compare-gated ranking")
    parser.add_argument(
        "--compare-max-relative-rms",
        type=float,
        help="maximum relative_rms_diff for compare-gated ranking",
    )
    parser.add_argument("--compare-max-p99", type=float, help="maximum abs_diff_p99 for compare-gated ranking")
    parser.add_argument(
        "--frame-gate-expected-input-light-frames",
        type=int,
        help="exact input light frame count required for promotion ranking",
    )
    parser.add_argument(
        "--frame-gate-expected-active-light-frames",
        type=int,
        help="exact integrated/active light frame count required for promotion ranking",
    )
    parser.add_argument(
        "--frame-gate-expected-zero-weight-frames",
        type=int,
        help="exact zero-weight light frame count required for promotion ranking",
    )
    parser.add_argument(
        "--frame-gate-min-active-light-frames",
        type=int,
        help="minimum integrated/active light frame count required for promotion ranking",
    )
    parser.add_argument(
        "--guardrails",
        action="store_true",
        help="run glass guardrails for each completed variant and include pass/fail in the sweep summary",
    )
    parser.add_argument(
        "--guardrails-stack-scope",
        choices=["all", "calibration", "integration"],
        default="integration",
        help="StackEngine contract scope used by per-variant guardrails",
    )
    parser.add_argument(
        "--guardrails-expected-integration-engine",
        choices=["stack_engine_cpu", "cuda_resident_stack", "any"],
        default="cuda_resident_stack",
        help="expected integration engine used by per-variant guardrails",
    )
    parser.add_argument(
        "--guardrails-pixel-verify",
        action="store_true",
        help="enable tiled FITS pixel verification inside per-variant guardrails",
    )
    parser.add_argument("--guardrails-pixel-verify-tile-size", type=int, default=4096)
    parser.add_argument("--guardrails-pixel-tolerance", type=int, default=0)
    parser.add_argument(
        "--max-variant-seconds",
        type=float,
        help="maximum wall time for one GLASS run variant; non-positive or omitted disables the timeout",
    )
    parser.add_argument(
        "--max-guardrails-seconds",
        type=float,
        help="maximum wall time for one per-variant guardrail bundle; non-positive or omitted disables the timeout",
    )
    parser.add_argument("--dry-run", action="store_true", help="write planned commands without executing variants")
    parser.add_argument(
        "--reuse-existing",
        action="store_true",
        help="summarize existing variant directories instead of rerunning completed variants",
    )
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    plan = Path(args.plan)
    glass_command = _split_command(args.glass_command)
    imported_common_run_args: list[str] = []
    import_provenance: dict[str, Any] | None = None
    if args.common_run_args_from_command:
        imported_common_run_args, import_provenance = _common_run_args_from_command_file(
            Path(args.common_run_args_from_command)
        )
    inline_common_run_args = _split_common_run_args(args.common_run_args)
    common_run_args = [
        *imported_common_run_args,
        *inline_common_run_args,
        *args.common_run_arg,
    ]
    common_run_args_provenance = {
        "source": "command_file" if import_provenance else "inline",
        "source_command_path": (import_provenance or {}).get("source_command_path"),
        "source_arg_count": (import_provenance or {}).get("source_arg_count", 0),
        "imported_arg_count": len(imported_common_run_args),
        "inline_arg_count": len(inline_common_run_args),
        "repeated_arg_count": len(args.common_run_arg),
        "total_arg_count": len(common_run_args),
        "filtered_token_count": (import_provenance or {}).get("filtered_token_count", 0),
        "filtered_managed_options": (import_provenance or {}).get("filtered_managed_options", []),
    }
    variants = build_resident_sweep_variants(
        prefetch_frames=parse_int_grid(args.prefetch_frames, default=[16, 24, 32]),
        prefetch_workers=parse_int_grid(args.prefetch_workers, default=[8, 12]),
        batch_frames=parse_int_grid(args.batch_frames, default=[8]),
        streams=parse_int_grid(args.streams, default=[4]),
        wave_frames=parse_int_grid(args.wave_frames, default=[2, 4]),
        release_modes=parse_mode_grid(args.release_modes, default=["callback_queue"]),
        refill_modes=parse_mode_grid(args.refill_modes, default=["immediate"]),
        triangle_fast_coarse_modes=_parse_fast_coarse_modes(args.triangle_fast_coarse_modes),
        triangle_coarse_strides=_parse_optional_int_grid(args.triangle_coarse_strides),
        triangle_final_strides=_parse_optional_int_grid(args.triangle_final_strides),
        star_max_candidates=_parse_optional_int_grid(args.star_max_candidates),
        star_grid_cols=_parse_optional_int_grid(args.star_grid_cols),
        star_grid_rows=_parse_optional_int_grid(args.star_grid_rows),
        triangle_grid_top_per_cell=_parse_optional_int_grid(args.triangle_grid_top_per_cell),
        triangle_nms_scan_candidates=_parse_optional_int_grid(args.triangle_nms_scan_candidates),
        triangle_nms_min_separation_px=_parse_optional_float_grid(args.triangle_nms_min_separation_px),
    )

    summaries: list[dict[str, Any]] = []
    commands: list[dict[str, Any]] = []
    for variant in variants:
        variant_id = str(variant["variant_id"])
        run_dir = out_dir / variant_id
        run_command = _variant_command(
            glass_command=glass_command,
            plan=plan,
            run_dir=run_dir,
            common_run_args=common_run_args,
            variant=variant,
        )
        commands.append({"variant_id": variant_id, "kind": "run", "command": run_command})
        guardrails_dir = out_dir / f"guardrails_{variant_id}"
        if args.guardrails:
            guardrails_command = _guardrails_command(
                glass_command=glass_command,
                run_dir=run_dir,
                out_dir=guardrails_dir,
                stack_scope=args.guardrails_stack_scope,
                expected_integration_engine=args.guardrails_expected_integration_engine,
                pixel_verify=args.guardrails_pixel_verify,
                pixel_verify_tile_size=args.guardrails_pixel_verify_tile_size,
                pixel_tolerance=args.guardrails_pixel_tolerance,
            )
            commands.append({"variant_id": variant_id, "kind": "guardrails", "command": guardrails_command})
        if args.dry_run:
            summaries.append(
                {
                    "variant": variant,
                    "variant_id": variant_id,
                    "run_dir": str(run_dir),
                    "status": "dry_run",
                    "guardrails": {
                        "status": "planned" if args.guardrails else "disabled",
                        "passed": None,
                        "out_dir": str(guardrails_dir) if args.guardrails else None,
                    },
                }
            )
            continue
        if not (args.reuse_existing and (run_dir / "resident_artifacts.json").exists()):
            run_result = _run_subprocess(run_command, timeout_seconds=args.max_variant_seconds)
            if run_result["status"] != "completed":
                summaries.append(
                    _failed_variant_summary(
                        variant=variant,
                        variant_id=variant_id,
                        run_dir=run_dir,
                        result=run_result,
                        guardrails_dir=guardrails_dir,
                        guardrails_requested=args.guardrails,
                    )
                )
                continue
        if args.guardrails:
            guardrails_result = _run_subprocess(
                guardrails_command,
                timeout_seconds=args.max_guardrails_seconds,
            )
        else:
            guardrails_result = {"status": "disabled", "passed": None}
        summary = load_resident_run_summary(run_dir, variant=variant)
        if args.guardrails:
            if guardrails_result["status"] == "completed":
                _attach_guardrails_summary(summary, guardrails_dir)
            else:
                _mark_guardrails_failed(summary, guardrails_dir=guardrails_dir, result=guardrails_result)
        summaries.append(summary)
        if args.reference_master and summary.get("master_path"):
            compare_out = out_dir / f"compare_{variant_id}_vs_reference.html"
            candidate_coverage_map = (
                str(summary.get("coverage_map_path"))
                if args.compare_use_candidate_coverage_map and summary.get("coverage_map_path")
                else None
            )
            compare_command = _compare_command(
                glass_command=glass_command,
                candidate_master=str(summary["master_path"]),
                reference_master=Path(args.reference_master),
                out_html=compare_out,
                candidate_total_s=summary.get("total_elapsed_s"),
                reference_total_s=args.reference_time_seconds,
                candidate_label=variant_id,
                reference_label=args.reference_label,
                ignore_border_px=args.ignore_border_px,
                glass_scale=args.compare_glass_scale,
                glass_offset=args.compare_glass_offset,
                clip_low=args.compare_clip_low,
                clip_high=args.compare_clip_high,
                glass_coverage_map=candidate_coverage_map,
                min_coverage=args.compare_min_coverage,
            )
            commands.append({"variant_id": variant_id, "kind": "compare", "command": compare_command})
            subprocess.run(compare_command, check=True)
            _attach_compare_summary(summary, compare_out.with_suffix(".json"), compare_out)

    payload = write_resident_sweep_summary(
        out_dir,
        plan=plan,
        variants=variants,
        summaries=summaries,
        dry_run=args.dry_run,
        baseline_total_s=args.baseline_total_seconds,
        commands=commands,
        common_run_args=common_run_args_provenance,
        compare_gate={
            "require_shape_match": args.compare_require_shape_match,
            "max_rms_diff": args.compare_max_rms,
            "max_relative_rms_diff": args.compare_max_relative_rms,
            "max_abs_diff_p99": args.compare_max_p99,
        },
        frame_gate={
            "expected_input_light_frames": args.frame_gate_expected_input_light_frames,
            "expected_active_light_frames": args.frame_gate_expected_active_light_frames,
            "expected_zero_weight_frames": args.frame_gate_expected_zero_weight_frames,
            "min_active_light_frames": args.frame_gate_min_active_light_frames,
        },
    )
    print(f"resident prefetch sweep summary: {out_dir / 'resident_prefetch_sweep_summary.json'}")
    if payload.get("best_variant"):
        best = payload["best_variant"]
        print(f"best={best['variant_id']} total_s={best.get('total_elapsed_s')}")
    else:
        print(f"variants={len(variants)} dry_run={args.dry_run}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
