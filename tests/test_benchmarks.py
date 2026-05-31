from __future__ import annotations

import json
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from glass.synthetic.generator import generate_synthetic_dataset
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
    assert payload["input_light_frame_count"] == 2
    assert payload["frame_count"] + payload["quality_gate_rejected_frames"] == 2
    assert payload["quality_gate_enforced"] is True
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
        "--catalog-similarity-top-k",
        "4",
    )

    payload = json.loads(out.read_text(encoding="utf-8"))
    diff = payload["direct_output_diff_gpu_matrix_minus_astroalign_apply_on_common_valid_pixels"]
    fit_diff = payload["direct_output_diff_gpu_similarity_fit_minus_astroalign_apply_on_common_valid_pixels"]
    catalog_similarity_diff = payload[
        "direct_output_diff_gpu_catalog_similarity_minus_astroalign_apply_on_common_valid_pixels"
    ]
    valid_pixels = payload["valid_pixels"]
    fit = payload["glass_cuda_similarity_fit_from_astroalign_matches"]
    matrix_metrics = payload["glass_cuda_matrix_metrics_from_astroalign"]
    catalog_similarity = payload["glass_cuda_catalog_similarity"]
    catalog_similarity_matrix_metrics = payload["glass_cuda_catalog_similarity_matrix_metrics"]
    catalog_similarity_agreement = payload["catalog_similarity_agreement_vs_astroalign"]
    catalog_similarity_pixel_refined = payload["glass_cuda_catalog_similarity_pixel_refined"]

    assert payload["astroalign"]["matched_control_points"] > 0
    assert payload["glass_cuda_matrix_warp_from_astroalign"]["coverage_pixels"] > 0
    assert fit["fit_model"] == "matched_pair_similarity_cuda"
    assert fit["fit_status"] == "ok"
    assert fit["valid_pairs"] == payload["astroalign"]["matched_control_points"]
    assert fit["fit_rms_px"] < 0.1
    assert fit["coverage_pixels"] > 0
    assert matrix_metrics["model"] == "matrix_alignment_metrics_cuda"
    assert matrix_metrics["valid_pixels"] > 0
    assert matrix_metrics["rms"] is not None
    assert matrix_metrics["ncc"] is not None
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
    assert catalog_similarity["top_k"] == 4
    assert len(catalog_similarity["top_candidates"]) == 4
    assert catalog_similarity_pixel_refined["seed_selection_model"] == "catalog_topk_star_guarded_pixel_metric"
    assert catalog_similarity_pixel_refined["seed_count"] == 5
    assert len(catalog_similarity_pixel_refined["seed_metrics"]) == 5
    assert catalog_similarity_pixel_refined["selected_seed_rank"] >= 0
    assert catalog_similarity_pixel_refined["star_guard"]["selection_key"]
    assert catalog_similarity_matrix_metrics["model"] == "matrix_alignment_metrics_cuda"
    assert catalog_similarity_matrix_metrics["valid_pixels"] > 0
    assert catalog_similarity_matrix_metrics["rms"] is not None
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


def test_star_guarded_seed_selection_prefers_star_supported_seed():
    pytest.importorskip("glass_cuda")
    spec = importlib.util.spec_from_file_location(
        "compare_astroalign_gpu_alignment",
        Path("benchmarks/compare_astroalign_gpu_alignment.py"),
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    seed_metrics = [
        {
            "seed_index": 0,
            "seed_rank": 0,
            "seed_inliers": 12,
            "seed_rms_px": 1.3,
            "metrics": {"rms": 78.5},
        },
        {
            "seed_index": 1,
            "seed_rank": 1,
            "seed_inliers": 11,
            "seed_rms_px": 1.2,
            "metrics": {"rms": 77.0},
        },
    ]

    selected_index, guard = module._select_star_guarded_seed(seed_metrics, pixel_selected_index=1)

    assert selected_index == 0
    assert guard["status"] == "replaced_pixel_metric"
    assert guard["star_max_inliers"] == 12
    assert guard["pixel_selected_seed_inliers"] == 11


def test_star_guarded_seed_selection_uses_star_core_metric_with_inlier_slack():
    pytest.importorskip("glass_cuda")
    spec = importlib.util.spec_from_file_location(
        "compare_astroalign_gpu_alignment",
        Path("benchmarks/compare_astroalign_gpu_alignment.py"),
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    seed_metrics = [
        {
            "seed_index": 0,
            "seed_rank": 0,
            "seed_inliers": 15,
            "seed_rms_px": 1.2,
            "metrics": {"rms": 82.0},
            "star_core_metric": {"rms": 640.0},
        },
        {
            "seed_index": 5,
            "seed_rank": 5,
            "seed_inliers": 13,
            "seed_rms_px": 1.3,
            "metrics": {"rms": 78.0},
            "star_core_metric": {"rms": 600.0},
        },
        {
            "seed_index": 8,
            "seed_rank": 8,
            "seed_inliers": 10,
            "seed_rms_px": 1.0,
            "metrics": {"rms": 76.0},
            "star_core_metric": {"rms": 590.0},
        },
    ]

    selected_index, guard = module._select_star_guarded_seed(seed_metrics, pixel_selected_index=2)

    assert selected_index == 1
    assert guard["status"] == "replaced_pixel_metric_with_star_core_metric"
    assert guard["star_max_inliers"] == 15
    assert guard["star_min_inliers_for_core_metric"] == 13


def test_star_core_preselection_keeps_refit_and_rejects_low_inlier_trap():
    spec = importlib.util.spec_from_file_location(
        "compare_astroalign_gpu_alignment",
        Path("benchmarks/compare_astroalign_gpu_alignment.py"),
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    seed_metrics = [
        {
            "seed_index": 0,
            "seed_rank": 0,
            "seed_inliers": 12,
            "seed_rms_px": 1.4,
            "star_core_metric": {"rms": 800.0},
        },
        {
            "seed_index": 1,
            "seed_rank": 1,
            "seed_inliers": 12,
            "seed_rms_px": 1.2,
            "star_core_metric": {"rms": 600.0},
        },
        {
            "seed_index": 2,
            "seed_rank": 2,
            "seed_inliers": 11,
            "seed_rms_px": 1.1,
            "star_core_metric": {"rms": 590.0},
        },
        {
            "seed_index": 3,
            "seed_rank": 3,
            "seed_inliers": 9,
            "seed_rms_px": 0.8,
            "star_core_metric": {"rms": 100.0},
        },
        {
            "seed_index": 4,
            "seed_rank": 4,
            "seed_inliers": 10,
            "seed_rms_px": 1.0,
            "star_core_metric": {"rms": 610.0},
        },
    ]

    selected_indices, summary = module._select_star_core_preselected_seed_indices(seed_metrics, max_count=3)

    assert selected_indices == [0, 1, 2]
    assert summary["enabled"]
    assert summary["star_max_inliers"] == 12
    assert summary["star_min_inliers_for_core_metric"] == 10
    assert summary["selected_seed_count"] == 3
