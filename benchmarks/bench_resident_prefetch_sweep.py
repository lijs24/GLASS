from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glass.report.resident_sweep import (
    build_resident_sweep_variants,
    load_resident_run_summary,
    parse_int_grid,
    parse_mode_grid,
    variant_run_args,
    write_resident_sweep_summary,
)


def _split_command(value: str | None) -> list[str]:
    if value is None or value.strip() == "":
        return [sys.executable, "-m", "glass.cli"]
    return value.split()


def _split_common_run_args(value: str | None) -> list[str]:
    if value is None or value.strip() == "":
        return []
    return [part.strip("\"'") for part in shlex.split(value, posix=False)]


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
    common_run_args = [*_split_common_run_args(args.common_run_args), *args.common_run_arg]
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
        if args.dry_run:
            summaries.append({"variant": variant, "variant_id": variant_id, "run_dir": str(run_dir), "status": "dry_run"})
            continue
        if not (args.reuse_existing and (run_dir / "resident_artifacts.json").exists()):
            subprocess.run(run_command, check=True)
        summary = load_resident_run_summary(run_dir, variant=variant)
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
