from __future__ import annotations

import argparse
import json
import subprocess
import time
import tracemalloc
from pathlib import Path
from typing import Any, Callable

from gpwbpp.capabilities import capability_report


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--out", required=True)
    parser.add_argument("--frames", type=int, default=4)
    parser.add_argument("--width", type=int, default=64)
    parser.add_argument("--height", type=int, default=64)
    parser.add_argument("--tile-size", type=int, default=32)


def run_timed(fn: Callable[[], Any]) -> tuple[Any, float, float]:
    tracemalloc.start()
    start = time.perf_counter()
    result = fn()
    elapsed = time.perf_counter() - start
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return result, elapsed, peak / (1024 * 1024)


def vram_mib() -> int | None:
    try:
        import gpwbpp_cuda

        devices = gpwbpp_cuda.list_devices()
    except Exception:
        return None
    if not devices:
        return None
    value = devices[0].get("memory_total_mib")
    return int(value) if value is not None else None


def nvidia_used_memory_mib() -> int | None:
    try:
        completed = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=memory.used",
                "--format=csv,noheader,nounits",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return None
    if completed.returncode != 0:
        return None
    first = completed.stdout.splitlines()[0].strip() if completed.stdout.splitlines() else ""
    try:
        return int(float(first))
    except ValueError:
        return None


def write_result(
    out: str | Path,
    *,
    name: str,
    frame_count: int,
    width: int,
    height: int,
    backend: str,
    elapsed_s: float,
    peak_ram_mb: float | None,
    output_path: str | Path,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    total_pixels = int(frame_count) * int(width) * int(height)
    throughput = None if elapsed_s <= 0 else total_pixels / elapsed_s / 1_000_000
    payload: dict[str, Any] = {
        "benchmark": name,
        "frame_count": int(frame_count),
        "image_shape": [int(height), int(width)],
        "total_pixels": total_pixels,
        "backend": backend,
        "elapsed_s": float(elapsed_s),
        "peak_ram_mb": peak_ram_mb,
        "peak_vram_mb": nvidia_used_memory_mib(),
        "vram_total_mib": vram_mib(),
        "throughput_mpix_s": throughput,
        "output_path": str(output_path),
    }
    if extra:
        payload.update(extra)
    target = Path(out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload
