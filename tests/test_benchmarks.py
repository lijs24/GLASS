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
        "--catalog-nms-scan-stars",
        "64",
        "--catalog-nms-min-separation",
        "4",
        "--catalog-prior-radius",
        "4",
        "--catalog-min-inliers",
        "4",
    )

    payload = json.loads(out.read_text(encoding="utf-8"))
    diff = payload["direct_output_diff_gpu_matrix_minus_astroalign_apply_on_common_valid_pixels"]
    fit_diff = payload["direct_output_diff_gpu_similarity_fit_minus_astroalign_apply_on_common_valid_pixels"]
    catalog_similarity_diff = payload[
        "direct_output_diff_gpu_catalog_similarity_minus_astroalign_apply_on_common_valid_pixels"
    ]
    valid_pixels = payload["valid_pixels"]
    fit = payload["gpwbpp_cuda_similarity_fit_from_astroalign_matches"]
    catalog_similarity = payload["gpwbpp_cuda_catalog_similarity"]
    catalog_similarity_agreement = payload["catalog_similarity_agreement_vs_astroalign"]

    assert payload["astroalign"]["matched_control_points"] > 0
    assert payload["gpwbpp_cuda_matrix_warp_from_astroalign"]["coverage_pixels"] > 0
    assert fit["fit_model"] == "matched_pair_similarity_cuda"
    assert fit["fit_status"] == "ok"
    assert fit["valid_pairs"] == payload["astroalign"]["matched_control_points"]
    assert fit["fit_rms_px"] < 0.1
    assert fit["coverage_pixels"] > 0
    assert valid_pixels["common"] == diff["valid_pixels"]
    assert valid_pixels["common_similarity_fit"] == fit_diff["valid_pixels"]
    assert valid_pixels["common_catalog_similarity"] == catalog_similarity_diff["valid_pixels"]
    assert diff["valid_pixels"] > 0
    assert fit_diff["valid_pixels"] > 0
    assert catalog_similarity_diff["valid_pixels"] > 0
    assert diff["median_abs_diff"] is not None
    assert fit_diff["median_abs_diff"] is not None
    assert catalog_similarity_diff["median_abs_diff"] is not None
    assert diff["rms_diff"] is not None
    assert fit_diff["rms_diff"] is not None
    assert catalog_similarity_diff["rms_diff"] is not None
    assert payload["gpu_similarity_fit_plus_warp_speedup_vs_astroalign_apply_transform"] is not None
    assert payload["gpu_similarity_matrix_max_abs_delta_vs_astroalign"] < 0.02
    assert catalog_similarity["fit_model"] == "catalog_pair_similarity_cuda"
    assert catalog_similarity["fit_status"] == "ok"
    assert catalog_similarity["accepted"]
    assert catalog_similarity_agreement["passed"]
    assert catalog_similarity_agreement["translation_delta_px"] <= catalog_similarity_agreement["criteria"][
        "translation_delta_px_max"
    ]
    assert catalog_similarity_agreement["output_rms_diff"] <= catalog_similarity_agreement["criteria"][
        "output_rms_diff_max"
    ]
    assert catalog_similarity["coverage_pixels"] > 0
    assert payload["catalog_similarity_speedup_vs_astroalign"] is not None
    assert payload["resident_matrix_device_speedup_vs_astroalign_apply_transform"] is not None
