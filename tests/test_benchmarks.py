from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from gpwbpp.synthetic.generator import generate_synthetic_dataset


def _run(script: str, *args: str) -> None:
    subprocess.run([sys.executable, script, *args], check=True)


def test_bench_scan_outputs_required_fields(tmp_path: Path):
    data = tmp_path / "data"
    out = tmp_path / "scan.json"
    generate_synthetic_dataset(data, frames=2, width=16, height=12)
    _run("benchmarks/bench_scan.py", "--root", str(data), "--out", str(out))
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["benchmark"] == "scan"
    assert payload["frame_count"] > 0
    assert payload["total_pixels"] > 0
    assert "throughput_mpix_s" in payload


def test_bench_end_to_end_cpu_outputs_required_fields(tmp_path: Path):
    out = tmp_path / "end_to_end.json"
    _run(
        "benchmarks/bench_end_to_end.py",
        "--out",
        str(out),
        "--frames",
        "2",
        "--width",
        "16",
        "--height",
        "16",
        "--tile-size",
        "8",
        "--backend",
        "cpu",
    )
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["benchmark"] == "end_to_end"
    assert payload["frame_count"] == 2
    assert payload["backend"] == "cpu"
    assert Path(payload["master_path"]).exists()
