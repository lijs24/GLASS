from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmarks.common import add_common_args, run_timed, write_result
from glass.cli import main as glass_main
from glass.io.json_io import read_json


def main() -> int:
    parser = argparse.ArgumentParser()
    add_common_args(parser)
    args = parser.parse_args()
    base = Path(args.out).with_suffix("")
    source = base / "source"
    audit = base / "audit"
    glass_main(
        [
            "synthetic",
            "--out",
            str(source),
            "--frames",
            str(args.frames),
            "--width",
            str(args.width),
            "--height",
            str(args.height),
            "--known-shift",
        ]
    )
    _, elapsed, peak_ram = run_timed(
        lambda: glass_main(
            [
                "audit",
                "--root",
                str(source),
                "--out",
                str(audit),
                "--backend",
                "cuda",
                "--tile-size",
                str(args.tile_size),
                "--integration-rejection",
                "none",
            ]
        )
    )
    integration = read_json(audit / "integration_results.json")
    output = integration["outputs"][0]
    write_result(
        args.out,
        name="gpu_integration",
        frame_count=int(output["frame_count"]),
        width=args.width,
        height=args.height,
        backend=str(output["backend"]),
        elapsed_s=elapsed,
        peak_ram_mb=peak_ram,
        output_path=output["master_path"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
