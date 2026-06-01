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


def test_bench_resident_prefetch_sweep_dry_run_outputs_matrix(tmp_path: Path):
    plan = tmp_path / "processing_plan.json"
    plan.write_text('{"frames": []}\n', encoding="utf-8")
    out = tmp_path / "resident_sweep"

    _run(
        "benchmarks/bench_resident_prefetch_sweep.py",
        "--plan",
        str(plan),
        "--out",
        str(out),
        "--prefetch-frames",
        "16,32",
        "--prefetch-workers",
        "8",
        "--batch-frames",
        "8",
        "--streams",
        "4",
        "--wave-frames",
        "2,4",
        "--release-modes",
        "callback_queue",
        "--baseline-total-seconds",
        "12.2",
        "--common-run-args",
        "--resident-output-maps minimal",
        "--guardrails",
        "--guardrails-pixel-verify",
        "--guardrails-pixel-verify-tile-size",
        "128",
        "--frame-gate-expected-input-light-frames",
        "200",
        "--frame-gate-expected-active-light-frames",
        "193",
        "--frame-gate-expected-zero-weight-frames",
        "7",
        "--dry-run",
    )

    payload = json.loads((out / "resident_prefetch_sweep_summary.json").read_text(encoding="utf-8"))
    analysis = json.loads((out / "resident_prefetch_sweep_analysis.json").read_text(encoding="utf-8"))
    markdown = (out / "resident_prefetch_sweep_summary.md").read_text(encoding="utf-8")
    analysis_markdown = (out / "resident_prefetch_sweep_analysis.md").read_text(encoding="utf-8")
    assert payload["benchmark"] == "resident_prefetch_sweep"
    assert payload["dry_run"] is True
    assert analysis["benchmark"] == "resident_prefetch_sweep"
    assert analysis["completed_count"] == 0
    assert analysis["frame_gate_enabled"] is True
    assert "Resident Prefetch Sweep Analysis" in analysis_markdown
    assert payload["variant_count"] == 4
    assert payload["best_variant"] is None
    assert {variant["variant_id"] for variant in payload["variants"]} == {
        "pf16_pw8_b8_s4_w2_callback_queue",
        "pf16_pw8_b8_s4_w4_callback_queue",
        "pf32_pw8_b8_s4_w2_callback_queue",
        "pf32_pw8_b8_s4_w4_callback_queue",
    }
    assert all(run["status"] == "dry_run" for run in payload["runs"])
    assert payload["guardrails"]["enabled"] is True
    assert payload["guardrails"]["planned_count"] == 4
    assert payload["frame_gate"]["enabled"] is True
    assert payload["frame_gate"]["planned_count"] == 4
    assert len([command for command in payload["commands"] if command["kind"] == "run"]) == 4
    assert len([command for command in payload["commands"] if command["kind"] == "guardrails"]) == 4
    assert "--resident-output-maps" in payload["commands"][0]["command"]
    assert "--resident-prefetch-refill-mode" in payload["commands"][0]["command"]
    guardrail_command = next(command["command"] for command in payload["commands"] if command["kind"] == "guardrails")
    assert "guardrails" in guardrail_command
    assert "--pixel-verify" in guardrail_command
    assert "--pixel-verify-tile-size" in guardrail_command
    assert "Resident Prefetch Sweep" in markdown
    assert "Guardrails" in markdown
    assert "Frame gate" in markdown


def test_bench_resident_prefetch_sweep_records_variant_timeout(tmp_path: Path):
    plan = tmp_path / "processing_plan.json"
    plan.write_text('{"frames": []}\n', encoding="utf-8")
    sleeper = tmp_path / "sleepy_glass.py"
    sleeper.write_text("import time\n\ntime.sleep(2)\n", encoding="utf-8")
    out = tmp_path / "resident_sweep_timeout"

    _run(
        "benchmarks/bench_resident_prefetch_sweep.py",
        "--plan",
        str(plan),
        "--out",
        str(out),
        "--glass-command",
        f"{sys.executable} {sleeper}",
        "--prefetch-frames",
        "16",
        "--prefetch-workers",
        "8",
        "--batch-frames",
        "8",
        "--streams",
        "4",
        "--wave-frames",
        "2",
        "--release-modes",
        "callback_queue",
        "--guardrails",
        "--max-variant-seconds",
        "0.05",
    )

    payload = json.loads((out / "resident_prefetch_sweep_summary.json").read_text(encoding="utf-8"))
    runs = payload["runs"]
    assert len(runs) == 1
    assert runs[0]["status"] == "timeout"
    assert runs[0]["timeout_s"] == 0.05
    assert runs[0]["guardrails"]["status"] == "skipped_run_failed"
    assert runs[0]["guardrails"]["passed"] is False
    assert payload["best_variant"] is None
    assert payload["guardrails"]["failed_count"] == 1


def test_bench_resident_prefetch_sweep_imports_baseline_run_command(tmp_path: Path):
    plan = tmp_path / "processing_plan.json"
    plan.write_text('{"frames": []}\n', encoding="utf-8")
    baseline_command = tmp_path / "run_command.txt"
    baseline_command.write_text(
        "glass run "
        f"--plan {tmp_path / 'old_plan.json'} "
        f"--out {tmp_path / 'old_run'} "
        "--backend cuda --until-stage integration --memory-mode resident "
        "--resident-master-cache-dir C:\\glass_runs\\cache "
        "--resident-registration similarity_cuda_triangle "
        "--resident-warp-interpolation bilinear "
        "--reference-frame-id F000196 "
        "--resident-star-threshold 350 "
        "--resident-output-maps audit "
        "--flat-floor 0.05 "
        "--exclude-frame-id LIGHT_H_0100 "
        "--resident-prefetch-frames 99 "
        "--resident-prefetch-workers 77 "
        "--resident-h2d-mode pinned_ring "
        "--resident-calibration-batch-frames 66 "
        "--resident-calibration-streams 55 "
        "--resident-calibration-wave-frames 44 "
        "--resident-calibration-release-mode synchronized\n",
        encoding="utf-8",
    )
    out = tmp_path / "resident_sweep_import"

    _run(
        "benchmarks/bench_resident_prefetch_sweep.py",
        "--plan",
        str(plan),
        "--out",
        str(out),
        "--common-run-args-from-command",
        str(baseline_command),
        "--prefetch-frames",
        "16",
        "--prefetch-workers",
        "8",
        "--batch-frames",
        "8",
        "--streams",
        "4",
        "--wave-frames",
        "2",
        "--release-modes",
        "callback_queue",
        "--dry-run",
    )

    payload = json.loads((out / "resident_prefetch_sweep_summary.json").read_text(encoding="utf-8"))
    markdown = (out / "resident_prefetch_sweep_summary.md").read_text(encoding="utf-8")
    command = next(item["command"] for item in payload["commands"] if item["kind"] == "run")
    common_run_args = payload["common_run_args"]
    assert common_run_args["source"] == "command_file"
    assert common_run_args["source_command_path"] == str(baseline_command)
    assert common_run_args["imported_arg_count"] > 0
    assert common_run_args["filtered_token_count"] > 0
    assert "--plan" in common_run_args["filtered_managed_options"]
    assert "--out" in common_run_args["filtered_managed_options"]
    assert "--resident-prefetch-frames" in common_run_args["filtered_managed_options"]
    assert "Imported command" in markdown
    assert command[command.index("--plan") + 1] == str(plan)
    assert command[command.index("--out") + 1] == str(out / "pf16_pw8_b8_s4_w2_callback_queue")
    assert command[command.index("--resident-prefetch-frames") + 1] == "16"
    assert command[command.index("--resident-prefetch-workers") + 1] == "8"
    assert command[command.index("--resident-calibration-batch-frames") + 1] == "8"
    assert command[command.index("--resident-calibration-streams") + 1] == "4"
    assert command[command.index("--resident-calibration-wave-frames") + 1] == "2"
    assert command[command.index("--resident-calibration-release-mode") + 1] == "callback_queue"
    assert "--reference-frame-id" in command
    assert command[command.index("--reference-frame-id") + 1] == "F000196"
    assert "--exclude-frame-id" in command
    assert "LIGHT_H_0100" in command
    assert "--resident-output-maps" in command
    assert command[command.index("--resident-output-maps") + 1] == "audit"
    assert "99" not in command
    assert "77" not in command
    assert "66" not in command


def test_bench_resident_prefetch_sweep_imports_frame_gate_contract(tmp_path: Path):
    plan = tmp_path / "processing_plan.json"
    plan.write_text('{"frames": []}\n', encoding="utf-8")
    contract = tmp_path / "contract.json"
    contract.write_text(
        json.dumps(
            {
                "name": "fixture_contract",
                "frame_accounting": {
                    "required_input_light_frames": 200,
                    "required_integrated_frames": 193,
                    "required_zero_weight_frames": 7,
                    "min_integrated_frames": 190,
                },
            }
        ),
        encoding="utf-8",
    )
    out = tmp_path / "resident_sweep_contract"

    _run(
        "benchmarks/bench_resident_prefetch_sweep.py",
        "--plan",
        str(plan),
        "--out",
        str(out),
        "--frame-gate-from-contract",
        str(contract),
        "--prefetch-frames",
        "16",
        "--prefetch-workers",
        "8",
        "--batch-frames",
        "8",
        "--streams",
        "4",
        "--wave-frames",
        "2",
        "--release-modes",
        "callback_queue",
        "--dry-run",
    )

    payload = json.loads((out / "resident_prefetch_sweep_summary.json").read_text(encoding="utf-8"))
    markdown = (out / "resident_prefetch_sweep_summary.md").read_text(encoding="utf-8")
    policy = payload["frame_gate"]["policy"]
    provenance = payload["common_run_args"]["frame_gate_contract"]
    assert policy["expected_input_light_frames"] == 200
    assert policy["expected_active_light_frames"] == 193
    assert policy["expected_zero_weight_frames"] == 7
    assert policy["min_active_light_frames"] == 190
    assert payload["frame_gate"]["planned_count"] == 1
    assert provenance["source_contract_path"] == str(contract)
    assert provenance["contract_name"] == "fixture_contract"
    assert "expected_active_light_frames" in provenance["imported_fields"]
    assert "Frame gate contract" in markdown


def test_bench_resident_prefetch_sweep_dry_run_registration_grid(tmp_path: Path):
    plan = tmp_path / "processing_plan.json"
    plan.write_text('{"frames": []}\n', encoding="utf-8")
    out = tmp_path / "resident_sweep_registration_grid"

    _run(
        "benchmarks/bench_resident_prefetch_sweep.py",
        "--plan",
        str(plan),
        "--out",
        str(out),
        "--prefetch-frames",
        "16",
        "--prefetch-workers",
        "8",
        "--batch-frames",
        "8",
        "--streams",
        "4",
        "--wave-frames",
        "2",
        "--release-modes",
        "callback_queue",
        "--triangle-fast-coarse-modes",
        "off,on",
        "--triangle-coarse-strides",
        "4",
        "--triangle-final-strides",
        "8",
        "--star-max-candidates",
        "48",
        "--star-grid-cols",
        "8",
        "--star-grid-rows",
        "6",
        "--triangle-grid-top-per-cell",
        "2",
        "--triangle-nms-scan-candidates",
        "96",
        "--triangle-nms-min-separation-px",
        "32.5",
        "--dry-run",
    )

    payload = json.loads((out / "resident_prefetch_sweep_summary.json").read_text(encoding="utf-8"))
    assert payload["variant_count"] == 2
    assert {variant["variant_id"] for variant in payload["variants"]} == {
        "pf16_pw8_b8_s4_w2_callback_queue_fcbase_cs4_fs8_sm48_g8x6_gt2_ns96_sep32p5",
        "pf16_pw8_b8_s4_w2_callback_queue_fcfast_cs4_fs8_sm48_g8x6_gt2_ns96_sep32p5",
    }
    fast_command = next(
        item["command"]
        for item in payload["commands"]
        if item["variant_id"] == "pf16_pw8_b8_s4_w2_callback_queue_fcfast_cs4_fs8_sm48_g8x6_gt2_ns96_sep32p5"
        and item["kind"] == "run"
    )
    base_command = next(
        item["command"]
        for item in payload["commands"]
        if item["variant_id"] == "pf16_pw8_b8_s4_w2_callback_queue_fcbase_cs4_fs8_sm48_g8x6_gt2_ns96_sep32p5"
        and item["kind"] == "run"
    )
    assert "--resident-triangle-pixel-refine-fast-coarse" in fast_command
    assert "--resident-triangle-pixel-refine-fast-coarse" not in base_command
    assert fast_command[fast_command.index("--resident-triangle-pixel-refine-coarse-stride") + 1] == "4"
    assert fast_command[fast_command.index("--resident-triangle-pixel-refine-final-stride") + 1] == "8"
    assert fast_command[fast_command.index("--resident-star-max-candidates") + 1] == "48"
    assert fast_command[fast_command.index("--resident-star-grid-cols") + 1] == "8"
    assert fast_command[fast_command.index("--resident-star-grid-rows") + 1] == "6"
    assert fast_command[fast_command.index("--resident-triangle-grid-top-per-cell") + 1] == "2"
    assert fast_command[fast_command.index("--resident-triangle-nms-scan-candidates") + 1] == "96"
    assert fast_command[fast_command.index("--resident-triangle-nms-min-separation-px") + 1] == "32.5"


def test_bench_resident_prefetch_sweep_compare_contract(tmp_path: Path):
    spec = importlib.util.spec_from_file_location(
        "bench_resident_prefetch_sweep",
        Path("benchmarks/bench_resident_prefetch_sweep.py"),
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    command = module._compare_command(
        glass_command=["glass"],
        candidate_master="candidate.fits",
        reference_master=tmp_path / "reference.xisf",
        out_html=tmp_path / "compare.html",
        candidate_total_s=14.5,
        reference_total_s=100.0,
        candidate_label="candidate",
        reference_label="reference",
        ignore_border_px=0,
        glass_scale=1.25,
        glass_offset=0.5,
        clip_low=0.0,
        clip_high=1.0,
        glass_coverage_map="coverage.fits",
        min_coverage=190.0,
    )
    assert "--glass-scale" in command
    assert command[command.index("--glass-scale") + 1] == "1.25"
    assert "--glass-offset" in command
    assert command[command.index("--glass-offset") + 1] == "0.5"
    assert "--clip-low" in command
    assert command[command.index("--clip-low") + 1] == "0.0"
    assert "--clip-high" in command
    assert command[command.index("--clip-high") + 1] == "1.0"
    assert "--glass-coverage-map" in command
    assert command[command.index("--glass-coverage-map") + 1] == "coverage.fits"
    assert "--min-coverage" in command
    assert command[command.index("--min-coverage") + 1] == "190.0"

    compare_html = tmp_path / "compare.html"
    compare_json = tmp_path / "compare.json"
    compare_json.write_text(
        json.dumps(
            {
                "shape_match": True,
                "rms_diff": 0.0012,
                "relative_rms_diff": 0.02,
                "abs_diff_p99": 0.0003,
                "max_abs_diff": 0.9,
                "comparison_region": {
                    "compared_pixels": 12345,
                    "coverage_fraction": 0.98,
                    "min_coverage": 190.0,
                },
                "timing": {"speedup_vs_reference": 6.9},
            }
        ),
        encoding="utf-8",
    )
    summary: dict[str, object] = {}
    module._attach_compare_summary(summary, compare_json, compare_html)

    compare = summary["compare"]
    assert compare["status"] == "completed"
    assert compare["shape_match"] is True
    assert compare["rms_diff"] == 0.0012
    assert compare["relative_rms_diff"] == 0.02
    assert compare["abs_diff_p99"] == 0.0003
    assert compare["max_abs_diff"] == 0.9
    assert compare["compared_pixels"] == 12345
    assert compare["coverage_fraction"] == 0.98
    assert compare["min_coverage"] == 190.0
    assert compare["speedup_vs_reference"] == 6.9

    missing_summary: dict[str, object] = {}
    module._attach_compare_summary(missing_summary, tmp_path / "missing.json", compare_html)
    assert missing_summary["compare"]["status"] == "missing"


def test_resident_sweep_ranking_prefers_guardrail_passed_variant(tmp_path: Path):
    from glass.report.resident_sweep import write_resident_sweep_summary

    payload = write_resident_sweep_summary(
        tmp_path,
        plan="processing_plan.json",
        variants=[],
        summaries=[
            {
                "variant_id": "fast_broken",
                "status": "completed",
                "total_elapsed_s": 10.0,
                "guardrails": {"status": "failed", "passed": False},
            },
            {
                "variant_id": "slower_green",
                "status": "completed",
                "total_elapsed_s": 11.0,
                "guardrails": {"status": "passed", "passed": True},
            },
        ],
        dry_run=False,
        baseline_total_s=22.0,
    )
    assert payload["best_variant"]["variant_id"] == "slower_green"
    assert payload["guardrails"]["passed_count"] == 1
    assert payload["guardrails"]["failed_count"] == 1


def test_resident_sweep_ranking_applies_frame_gate(tmp_path: Path):
    from glass.report.resident_sweep import write_resident_sweep_summary

    payload = write_resident_sweep_summary(
        tmp_path,
        plan="processing_plan.json",
        variants=[],
        summaries=[
            {
                "variant_id": "fast_wrong_frame_count",
                "status": "completed",
                "total_elapsed_s": 10.0,
                "registration_triangle_moving_catalog_s": 0.5,
                "guardrails": {"status": "passed", "passed": True},
                "input_light_frames": 200,
                "active_light_frames": 192,
                "zero_weight_frames": 8,
            },
            {
                "variant_id": "slower_expected_frame_count",
                "status": "completed",
                "total_elapsed_s": 11.0,
                "registration_triangle_moving_catalog_s": 0.8,
                "guardrails": {"status": "passed", "passed": True},
                "input_light_frames": 200,
                "active_light_frames": 193,
                "zero_weight_frames": 7,
            },
        ],
        dry_run=False,
        baseline_total_s=22.0,
        frame_gate={
            "expected_input_light_frames": 200,
            "expected_active_light_frames": 193,
            "expected_zero_weight_frames": 7,
            "min_active_light_frames": 193,
        },
    )

    markdown = (tmp_path / "resident_prefetch_sweep_summary.md").read_text(encoding="utf-8")
    analysis = json.loads((tmp_path / "resident_prefetch_sweep_analysis.json").read_text(encoding="utf-8"))
    runs_by_id = {run["variant_id"]: run for run in payload["runs"]}
    assert payload["best_variant"]["variant_id"] == "slower_expected_frame_count"
    assert payload["frame_gate"]["enabled"] is True
    assert payload["frame_gate"]["passed_count"] == 1
    assert payload["frame_gate"]["failed_count"] == 1
    assert runs_by_id["fast_wrong_frame_count"]["frame_gate"]["passed"] is False
    assert "active_light_frames 192 != 193" in runs_by_id["fast_wrong_frame_count"]["frame_gate"]["reasons"]
    assert "zero_weight_frames 8 != 7" in runs_by_id["fast_wrong_frame_count"]["frame_gate"]["reasons"]
    assert runs_by_id["slower_expected_frame_count"]["frame_gate"]["passed"] is True
    assert analysis["frame_gate_enabled"] is True
    assert analysis["promotion_candidate_count"] == 1
    assert analysis["fastest_promotion_candidate"]["variant_id"] == "slower_expected_frame_count"
    assert "Frame gate" in markdown

    blocked = write_resident_sweep_summary(
        tmp_path / "blocked",
        plan="processing_plan.json",
        variants=[],
        summaries=[
            {
                "variant_id": "low_catalog_wrong_frame_count",
                "status": "completed",
                "total_elapsed_s": 10.0,
                "registration_triangle_moving_catalog_s": 0.5,
                "guardrails": {"status": "passed", "passed": True},
                "input_light_frames": 200,
                "active_light_frames": 192,
                "zero_weight_frames": 8,
            }
        ],
        dry_run=False,
        baseline_total_s=22.0,
        frame_gate={
            "expected_input_light_frames": 200,
            "expected_active_light_frames": 193,
            "expected_zero_weight_frames": 7,
        },
    )
    blocked_analysis = json.loads(
        (tmp_path / "blocked" / "resident_prefetch_sweep_analysis.json").read_text(encoding="utf-8")
    )
    assert blocked["best_variant"] is None
    assert blocked_analysis["recommendation"]["status"] == "candidate_blocked_by_frame_gate"


def test_resident_sweep_ranking_applies_compare_gate(tmp_path: Path):
    from glass.report.resident_sweep import write_resident_sweep_summary

    payload = write_resident_sweep_summary(
        tmp_path,
        plan="processing_plan.json",
        variants=[],
        summaries=[
            {
                "variant_id": "fast_noisy",
                "status": "completed",
                "total_elapsed_s": 10.0,
                "guardrails": {"status": "passed", "passed": True},
                "compare": {
                    "status": "completed",
                    "shape_match": True,
                    "rms_diff": 0.0020,
                    "relative_rms_diff": 0.1,
                    "abs_diff_p99": 0.0005,
                },
            },
            {
                "variant_id": "slower_clean",
                "status": "completed",
                "total_elapsed_s": 11.0,
                "guardrails": {"status": "passed", "passed": True},
                "compare": {
                    "status": "completed",
                    "shape_match": True,
                    "rms_diff": 0.0010,
                    "relative_rms_diff": 0.05,
                    "abs_diff_p99": 0.0002,
                },
            },
        ],
        dry_run=False,
        baseline_total_s=22.0,
        compare_gate={
            "require_shape_match": True,
            "max_rms_diff": 0.0015,
            "max_abs_diff_p99": 0.0003,
        },
    )

    markdown = (tmp_path / "resident_prefetch_sweep_summary.md").read_text(encoding="utf-8")
    runs_by_id = {run["variant_id"]: run for run in payload["runs"]}
    assert payload["best_variant"]["variant_id"] == "slower_clean"
    assert payload["compare_gate"]["enabled"] is True
    assert payload["compare_gate"]["passed_count"] == 1
    assert payload["compare_gate"]["failed_count"] == 1
    assert runs_by_id["fast_noisy"]["compare_gate"]["passed"] is False
    assert "rms_diff 0.002" in runs_by_id["fast_noisy"]["compare_gate"]["reasons"][0]
    assert runs_by_id["slower_clean"]["compare_gate"]["passed"] is True
    assert "Compare gate" in markdown
    assert "failed" in markdown
    assert "passed" in markdown


def test_resident_sweep_analysis_blocks_low_catalog_variant_on_compare_gate(tmp_path: Path):
    from glass.report.resident_sweep import write_resident_sweep_summary

    payload = write_resident_sweep_summary(
        tmp_path,
        plan="processing_plan.json",
        variants=[],
        summaries=[
            {
                "variant_id": "low_catalog_noisy",
                "variant": {"triangle_grid_top_per_cell": 2},
                "status": "completed",
                "total_elapsed_s": 10.0,
                "registration_triangle_moving_catalog_s": 0.5,
                "resident_registration_warp_s": 1.6,
                "guardrails": {"status": "passed", "passed": True},
                "compare": {
                    "status": "completed",
                    "shape_match": True,
                    "rms_diff": 0.0020,
                    "abs_diff_p99": 0.0005,
                },
            },
            {
                "variant_id": "slower_clean",
                "variant": {"triangle_grid_top_per_cell": 4},
                "status": "completed",
                "total_elapsed_s": 11.0,
                "registration_triangle_moving_catalog_s": 0.9,
                "resident_registration_warp_s": 2.0,
                "guardrails": {"status": "passed", "passed": True},
                "compare": {
                    "status": "completed",
                    "shape_match": True,
                    "rms_diff": 0.0010,
                    "abs_diff_p99": 0.0002,
                },
            },
        ],
        dry_run=False,
        baseline_total_s=22.0,
        compare_gate={
            "require_shape_match": True,
            "max_rms_diff": 0.0015,
            "max_abs_diff_p99": 0.0003,
        },
    )

    analysis = json.loads((tmp_path / "resident_prefetch_sweep_analysis.json").read_text(encoding="utf-8"))
    analysis_markdown = (tmp_path / "resident_prefetch_sweep_analysis.md").read_text(encoding="utf-8")
    assert payload["best_variant"]["variant_id"] == "slower_clean"
    assert analysis["promotion_candidate_count"] == 1
    assert analysis["lowest_catalog_variant"]["variant_id"] == "low_catalog_noisy"
    assert analysis["lowest_catalog_variant"]["compare_gate_passed"] is False
    assert analysis["fastest_promotion_candidate"]["variant_id"] == "slower_clean"
    assert analysis["recommendation"]["status"] == "promotion_candidate_found"
    assert "Lowest catalog" in analysis_markdown
    assert "Fastest promotion" in analysis_markdown


def test_resident_sweep_summary_extracts_registration_components(tmp_path: Path):
    from glass.report.resident_sweep import load_resident_run_summary, write_resident_sweep_summary

    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "run_timing.json").write_text('{"total_elapsed_s": 12.5}\n', encoding="utf-8")
    (run_dir / "frame_accounting.json").write_text(
        json.dumps({"summary": {"input_light_frames": 3, "integrated_frames": 2, "zero_weight_frames": 1}}),
        encoding="utf-8",
    )
    (run_dir / "resident_artifacts.json").write_text(
        json.dumps(
            {
                "artifacts": [
                    {
                        "master_path": "master.fits",
                        "coverage_map_path": "coverage.fits",
                        "timing_s": {"resident_registration_warp": 2.4},
                        "resident_io_pipeline": {
                            "calibration_batch_native_total_s": 1.1,
                            "calibration_batch_sync_s": 0.1,
                        },
                        "fine_timing": {
                            "registration_component_seconds": {
                                "component_accounted_total": 2.4,
                                "triangle_moving_catalog": 0.7,
                                "triangle_descriptor_fit": 0.2,
                                "triangle_moving_descriptors": 0.1,
                                "triangle_pixel_refine": 0.9,
                                "triangle_warp": 0.4,
                                "triangle_warp_native_batch": 0.35,
                            }
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    summary = load_resident_run_summary(
        run_dir,
        variant={"variant_id": "pf16_pw8_b8_s4_w2_callback_queue"},
    )
    summary["compare"] = {
        "status": "completed",
        "rms_diff": 0.0012,
        "abs_diff_p99": 0.0003,
        "speedup_vs_reference": 6.9,
    }
    assert summary["coverage_map_path"] == "coverage.fits"
    assert summary["resident_registration_warp_s"] == 2.4
    assert summary["registration_component_accounted_s"] == 2.4
    assert summary["registration_triangle_moving_catalog_s"] == 0.7
    assert summary["registration_triangle_descriptor_fit_s"] == 0.2
    assert summary["registration_triangle_moving_descriptors_s"] == 0.1
    assert summary["registration_triangle_pixel_refine_s"] == 0.9
    assert summary["registration_triangle_warp_s"] == 0.4
    assert summary["registration_triangle_warp_native_batch_s"] == 0.35

    payload = write_resident_sweep_summary(
        tmp_path / "summary",
        plan="processing_plan.json",
        variants=[summary["variant"]],
        summaries=[summary],
        dry_run=False,
        baseline_total_s=25.0,
    )
    markdown = (tmp_path / "summary" / "resident_prefetch_sweep_summary.md").read_text(encoding="utf-8")
    assert payload["runs"][0]["registration_triangle_pixel_refine_s"] == 0.9
    assert payload["runs"][0]["compare"]["rms_diff"] == 0.0012
    assert "Catalog s" in markdown
    assert "Pixel refine s" in markdown
    assert "Ref RMS" in markdown
    assert "0.001200" in markdown
    assert "0.900000" in markdown
