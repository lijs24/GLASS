from __future__ import annotations

import argparse
import json
from pathlib import Path
from time import perf_counter

from gpwbpp.metadata.scanner import scan_tree


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    start = perf_counter()
    manifest = scan_tree(args.root)
    elapsed = perf_counter() - start
    frames = manifest["summary"]["count"]
    result = {
        "frame_count": frames,
        "image_shape": manifest["summary"].get("shape", {}),
        "total_pixels": None,
        "backend": "metadata",
        "elapsed_s": elapsed,
        "peak_ram_mb": None,
        "peak_vram_mb": None,
        "throughput_mpix_s": None,
        "output_path": args.out,
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

