from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmarks.common import run_timed, write_result
from gpwbpp.metadata.scanner import scan_tree


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    manifest, elapsed, peak_ram = run_timed(lambda: scan_tree(args.root))
    summary = manifest.get("summary", {})
    shape = next(iter(summary.get("shape", {"0x0": 0})), "0x0")
    width, height = (int(v) for v in shape.split("x")) if "x" in shape else (0, 0)
    write_result(
        args.out,
        name="scan",
        frame_count=int(summary.get("count", 0)),
        width=width,
        height=height,
        backend="metadata",
        elapsed_s=elapsed,
        peak_ram_mb=peak_ram,
        output_path=args.root,
        extra={"summary": summary},
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
