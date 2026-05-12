from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmarks.common import add_common_args, run_timed, write_result
from gpwbpp.engine.pipeline import run_calibration_stages
from gpwbpp.io.json_io import read_json, write_json
from gpwbpp.metadata.scanner import scan_tree
from gpwbpp.planner.plan_builder import build_processing_plan
from gpwbpp.synthetic.generator import generate_synthetic_dataset


def main() -> int:
    parser = argparse.ArgumentParser()
    add_common_args(parser)
    args = parser.parse_args()
    root = Path(args.out).with_suffix("") / "source"
    run = Path(args.out).with_suffix("") / "run"
    generate_synthetic_dataset(root, frames=args.frames, width=args.width, height=args.height, known_shift=True)
    manifest = scan_tree(root)
    plan = build_processing_plan(manifest, root / "manifest.json")
    plan_path = run / "processing_plan.json"
    write_json(plan_path, plan)
    _, elapsed, peak_ram = run_timed(
        lambda: run_calibration_stages(plan_path, run, backend="cpu", tile_size=args.tile_size)
    )
    artifacts = read_json(run / "calibration_artifacts.json")
    write_result(
        args.out,
        name="cpu_calibration",
        frame_count=len(artifacts.get("calibrated_lights", [])),
        width=args.width,
        height=args.height,
        backend="cpu",
        elapsed_s=elapsed,
        peak_ram_mb=peak_ram,
        output_path=run,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
