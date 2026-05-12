from __future__ import annotations

import argparse
import json
from pathlib import Path


def placeholder_benchmark(name: str) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    result = {
        "frame_count": 0,
        "image_shape": None,
        "total_pixels": 0,
        "backend": name,
        "elapsed_s": 0.0,
        "peak_ram_mb": None,
        "peak_vram_mb": None,
        "throughput_mpix_s": None,
        "output_path": args.out,
        "capability": "placeholder until corresponding gate is implemented",
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0

