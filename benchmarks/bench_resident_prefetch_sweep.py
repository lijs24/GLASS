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


def _common_run_args_from_command_file(path: Path) -> list[str]:
    tokens = _split_common_run_args(path.read_text(encoding="utf-8"))
    try:
        run_index = tokens.index("run")
    except ValueError as exc:
        raise ValueError(f"baseline command file does not contain a glass run command: {path}") from exc

    imported: list[str] = []
    source_args = tokens[run_index + 1 :]
    index = 0
    while index < len(source_args):
        token = source_args[index]
        value_count = _SWEEP_MANAGED_RUN_OPTIONS.get(token)
        if value_count is not None:
            index += value_count + 1
            continue
        imported.append(token)
        index += 1
    return imported


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
    parser.add_argument("--baseline-total-seconds", type=float)
    parser.add_argument("--reference-master", help="optional master FITS used for post-run compare reports")
    parser.add_argument("--reference-time-seconds", type=float)
    parser.add_argument("--reference-label", default="reference")
    parser.add_argument("--ignore-border-px", type=int, default=16)
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
    imported_common_run_args = (
        _common_run_args_from_command_file(Path(args.common_run_args_from_command))
        if args.common_run_args_from_command
        else []
    )
    common_run_args = [
        *imported_common_run_args,
        *_split_common_run_args(args.common_run_args),
        *args.common_run_arg,
    ]
    variants = build_resident_sweep_variants(
        prefetch_frames=parse_int_grid(args.prefetch_frames, default=[16, 24, 32]),
        prefetch_workers=parse_int_grid(args.prefetch_workers, default=[8, 12]),
        batch_frames=parse_int_grid(args.batch_frames, default=[8]),
        streams=parse_int_grid(args.streams, default=[4]),
        wave_frames=parse_int_grid(args.wave_frames, default=[2, 4]),
        release_modes=parse_mode_grid(args.release_modes, default=["callback_queue"]),
        refill_modes=parse_mode_grid(args.refill_modes, default=["immediate"]),
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
            )
            commands.append({"variant_id": variant_id, "kind": "compare", "command": compare_command})
            subprocess.run(compare_command, check=True)

    payload = write_resident_sweep_summary(
        out_dir,
        plan=plan,
        variants=variants,
        summaries=summaries,
        dry_run=args.dry_run,
        baseline_total_s=args.baseline_total_seconds,
        commands=commands,
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
