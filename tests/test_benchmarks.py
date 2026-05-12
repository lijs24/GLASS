from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from gpwbpp.synthetic.generator import generate_synthetic_dataset
from tests.conftest import cuda_module_or_skip


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


def test_compare_astroalign_gpu_alignment_records_direct_diff(tmp_path: Path):
    pytest.importorskip("astroalign")
    cuda_module_or_skip()
    out = tmp_path / "astroalign_vs_gpu.json"

    _run(
        "benchmarks/compare_astroalign_gpu_alignment.py",
        "--out",
        str(out),
        "--width",
        "96",
        "--height",
        "96",
        "--synthetic-dx",
        "4",
        "--synthetic-dy",
        "-3",
        "--max-shift",
        "8",
        "--catalog-stars",
        "32",
        "--catalog-threshold-sigma",
        "4",
        "--catalog-grid-cols",
        "4",
        "--catalog-grid-rows",
        "4",
        "--catalog-prior-radius",
        "4",
    )

    payload = json.loads(out.read_text(encoding="utf-8"))
    diff = payload["direct_output_diff_gpu_matrix_minus_astroalign_apply_on_common_valid_pixels"]
    valid_pixels = payload["valid_pixels"]

    assert payload["astroalign"]["matched_control_points"] > 0
    assert payload["gpwbpp_cuda_matrix_warp_from_astroalign"]["coverage_pixels"] > 0
    assert valid_pixels["common"] == diff["valid_pixels"]
    assert diff["valid_pixels"] > 0
    assert diff["median_abs_diff"] is not None
    assert diff["rms_diff"] is not None
    assert payload["resident_matrix_device_speedup_vs_astroalign_apply_transform"] is not None
