from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from tests.conftest import cuda_module_or_skip


def test_cli_scan_plan_report_audit_smoke(small_fits_dataset, tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    report = tmp_path / "report.html"
    audit = tmp_path / "audit"
    assert main(["scan", "--root", str(small_fits_dataset), "--out", str(manifest)]) == 0
    assert manifest.exists()
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    assert plan.exists()
    assert main(["report", "--run", str(tmp_path), "--out", str(report)]) == 0
    assert report.exists()
    assert main(["audit", "--root", str(small_fits_dataset), "--out", str(audit), "--backend", "cpu"]) == 0
    assert (audit / "manifest.json").exists()
    assert (audit / "processing_plan.json").exists()
    assert (audit / "report.html").exists()
    run_command = (audit / "run_command.txt").read_text(encoding="utf-8")
    assert "glass audit" in run_command
    assert "--backend cpu" in run_command


def test_cli_audit_resident_cuda_smoke(small_fits_dataset, tmp_path: Path):
    cuda_module_or_skip()
    audit = tmp_path / "resident_audit"

    assert main(
        [
            "audit",
            "--root",
            str(small_fits_dataset),
            "--out",
            str(audit),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--local-normalization",
            "off",
            "--integration-weighting",
            "none",
            "--integration-rejection",
            "none",
            "--resident-registration",
            "off",
            "--resident-registration-max-shift",
            "9",
            "--resident-ncc-sample-stride",
            "2",
            "--resident-ncc-fallback-score-threshold",
            "0.5",
            "--resident-subpixel-radius-steps",
            "3",
            "--resident-subpixel-step",
            "0.4",
            "--resident-star-threshold",
            "12",
            "--resident-star-max-candidates",
            "11",
            "--resident-star-tolerance-px",
            "1.25",
            "--resident-star-grid-cols",
            "2",
            "--resident-star-grid-rows",
            "3",
            "--resident-star-catalog-deterministic",
            "--resident-star-prior",
            "ncc",
            "--resident-star-prior-radius-px",
            "2.5",
            "--resident-star-core-preselect-top-k",
            "4",
        ]
    ) == 0

    state = read_json(audit / "run_state.json")
    timing = read_json(audit / "run_timing.json")
    integration = read_json(audit / "integration_results.json")
    resident = read_json(audit / "resident_artifacts.json")
    resident_registration = resident["artifacts"][0]["resident_registration"]
    assert (audit / "manifest.json").exists()
    assert (audit / "processing_plan.json").exists()
    assert (audit / "resident_artifacts.json").exists()
    assert (audit / "report.html").exists()
    assert state["current_stage"] == "report"
    assert "resident_integration" in state["completed_stages"]
    assert timing["memory_mode"] == "resident"
    assert integration["source_stage"] == "resident_calibrated_stack"
    assert resident_registration["max_shift"] == 9
    assert resident_registration["ncc_sample_stride"] == 2
    assert resident_registration["ncc_fallback_score_threshold"] == 0.5
    assert resident_registration["subpixel_radius_steps"] == 3
    assert resident_registration["subpixel_step"] == 0.4
    assert resident_registration["star_threshold"] == 12
    assert resident_registration["star_max_candidates"] == 11
    assert resident_registration["star_tolerance_px"] == 1.25
    assert resident_registration["star_grid_cols"] == 2
    assert resident_registration["star_grid_rows"] == 3
    assert resident_registration["star_catalog_deterministic"] is True
    assert resident_registration["star_prior"] == "ncc"
    assert resident_registration["star_prior_radius_px"] == 2.5
    assert resident_registration["star_core_preselect_top_k"] == 4


def test_cli_help_commands():
    for command in [
        "doctor",
        "scan",
        "plan",
        "subset",
        "run",
        "resume",
        "audit",
        "compare",
        "speedup-summary",
        "acceptance-audit",
        "resident-determinism",
        "stack-engine-contract",
        "pipeline-contract",
        "guardrails",
        "blackbox-package",
        "blackbox-finalize",
        "blackbox-history",
        "synthetic",
    ]:
        try:
            main([command, "--help"])
        except SystemExit as exc:
            assert exc.code == 0


def test_cli_guardrails_generates_contracts_and_report(small_fits_dataset, tmp_path: Path):
    run = tmp_path / "run"
    out_dir = tmp_path / "guardrails"
    assert main(["audit", "--root", str(small_fits_dataset), "--out", str(run), "--backend", "cpu", "--tile-size", "8"]) == 0

    assert (
        main(
            [
                "guardrails",
                "--run",
                str(run),
                "--out-dir",
                str(out_dir),
                "--expected-integration-engine",
                "stack_engine_cpu",
                "--pixel-verify",
                "--pixel-verify-tile-size",
                "8",
            ]
        )
        == 0
    )

    summary = read_json(out_dir / "guardrails_summary.json")
    stack_contract = read_json(out_dir / "stack_engine_contract.json")
    pipeline_contract = read_json(out_dir / "pipeline_contract.json")
    assert summary["passed"] is True
    assert summary["pixel_verify"] is True
    assert stack_contract["passed"] is True
    assert pipeline_contract["passed"] is True
    assert (out_dir / "stack_engine_contract.md").exists()
    assert (out_dir / "pipeline_contract.md").exists()
    assert (out_dir / "report.html").exists()
    html = (out_dir / "report.html").read_text(encoding="utf-8")
    assert "StackEngine contract audit" in html
    assert "Pipeline contract audit" in html
    assert "pixel_verification" in html


def test_cli_doctor_cpu_only_success(tmp_path: Path):
    out = tmp_path / "doctor.json"
    assert main(["doctor", "--allow-cpu-only", "--json", str(out)]) == 0
    payload = read_json(out)
    assert payload["product"] == "GLASS"
    assert payload["full_name"] == "GPU-Accelerated Lightframe Alignment and Stacking System"
    assert "cuda" in payload
    assert "capabilities" in payload
    assert "windows_cuda_packages" in payload
    assert "ordered_try_list" in payload["windows_cuda_packages"]


def test_cli_report_includes_resident_artifacts(tmp_path: Path):
    run = tmp_path / "run"
    run.mkdir()
    integration_dir = run / "integration"
    integration_dir.mkdir()
    for name in [
        "resident_master_H.fits",
        "resident_weight_map_H.fits",
        "resident_coverage_map_H.fits",
        "resident_dq_map_H.fits",
    ]:
        (integration_dir / name).write_text("placeholder", encoding="utf-8")
    write_json(
        run / "resident_artifacts.json",
        {
            "backend": "cuda_resident_stack",
            "device": {"name": "Test GPU"},
            "artifacts": [
                {
                    "filter": "H",
                    "frame_ids": ["F1", "F2"],
                    "master_stats": {"bias_count": 1, "dark_count": 1, "flat_count": 1},
                    "memory_estimate": {"resident_base_gib": 1.25, "estimated_peak_gib": 1.75},
                    "resident_io_pipeline": {"prefetch_frames": 2, "prefetch_workers": 1},
                    "resident_registration": {
                        "mode": "similarity_cuda_triangle",
                        "warp_interpolation": "lanczos3",
                        "warp_coverage": {
                            "available": True,
                            "active_frame_count": 2,
                            "frame_count": 2,
                            "frame_count_matches_active": True,
                            "warped_frame_count": 1,
                            "full_frame_count": 1,
                            "native_source": "ResidentCalibratedStack warp coverage accumulator",
                            "statistics": {"min": 1.0, "max": 2.0, "mean": 1.75},
                        },
                    },
                    "resident_local_normalization": {"mode": "resident_grid_mean_std"},
                    "resident_integration_weighting": {"mode": "simple_snr"},
                    "integration_rejection": {"mode": "winsorized_sigma"},
                    "master_path": "integration/resident_master_H.fits",
                    "weight_map_path": "integration/resident_weight_map_H.fits",
                    "coverage_map_path": "integration/resident_coverage_map_H.fits",
                    "low_rejection_map_path": None,
                    "high_rejection_map_path": None,
                    "dq_map_path": "integration/resident_dq_map_H.fits",
                    "output_map_policy": {
                        "mode": "science",
                        "available": ["master", "weight", "dq", "coverage", "low_rejection", "high_rejection"],
                        "written": ["master", "weight", "dq", "coverage"],
                        "skipped": ["low_rejection", "high_rejection"],
                        "description": "science keeps comparison maps and skips rejection count FITS files",
                    },
                    "output_write": {
                        "breakdown_s": {"master": 0.125, "weight": 0.25, "coverage": 0.375, "dq": 0.5},
                        "mode": "threaded",
                        "workers": 4,
                    },
                    "output_write_storage": {
                        "master": {"dtype": "float32", "estimated_data_bytes": 1048576},
                        "weight": {"dtype": "float32", "estimated_data_bytes": 2097152},
                        "coverage": {"dtype": "int16", "estimated_data_bytes": 524288},
                        "dq": {"dtype": "int16", "estimated_data_bytes": 524288},
                    },
                    "output_diagnostics": {
                        "total_pixels": 4,
                        "finite_pixels": 4,
                        "nonfinite_pixels": 0,
                        "statistics": {"mean": 0.25, "p50": 0.2, "std": 0.1, "min": 0.0, "max": 1.0},
                        "clipping_probe": {
                            "lt_0_count": 0,
                            "gt_1_count": 0,
                            "gt_65535_count": 0,
                            "positive_weight_pixels": 4,
                            "zero_weight_pixels": 0,
                        },
                        "normalization_probe": {
                            "method": "diagnostic_only_p0_1_to_p99_9",
                            "scale": 1.5,
                            "offset": -0.1,
                            "black": 0.0,
                            "white": 1.0,
                        },
                    },
                    "dq_provenance_summary": {
                        "schema_version": 1,
                        "source_schema": "resident_dq_coverage_provenance",
                        "stage": "integration",
                        "item": "H",
                        "engine": "cuda_resident_stack",
                        "active_frame_count": 2,
                        "zero_coverage_pixels": 0,
                        "partial_coverage_pixels": 1,
                        "valid_pixels": 3,
                        "no_data_pixels": 0,
                        "warp_edge_pixels": 1,
                    },
                    "timing_s": {
                        "light_read_upload_calibrate": 2.0,
                        "light_read_decode": 1.0,
                        "light_read_decode_worker": 1.25,
                        "light_h2d_calibrate_store": 0.75,
                        "resident_registration_warp": 0.5,
                        "resident_registration_component_accounted": 0.4,
                        "resident_registration_orchestration": 0.1,
                        "light_loop_unaccounted": 0.25,
                        "resident_weighting": 0.1,
                        "resident_local_normalization": 0.2,
                        "resident_integration": 0.25,
                        "output_write": 0.5,
                    },
                }
            ],
        },
    )
    write_json(
        run / "integration_results.json",
        {
            "source_stage": "resident_calibrated_stack",
            "outputs": [
                {
                    "filter": "H",
                    "dq_map_path": "dq.fits",
                    "dq_summary": {"valid": 3, "warp_edge": 1, "no_data": 0},
                    "geometric_warp_coverage": {
                        "available": True,
                        "frame_count": 2,
                        "frame_count_matches_active": True,
                    },
                    "dq_coverage_provenance": {
                        "available": True,
                        "active_frame_count": 2,
                        "source_terms": ["post_rejection_coverage", "geometric_warp_coverage"],
                        "geometric_warp_coverage_frame_count": 2,
                        "geometric_frame_count_matches_active": True,
                        "geometric_warp_coverage": {"min": 1.0, "max": 2.0, "mean": 1.75},
                        "geometric_zero_pixels": 0,
                        "geometric_partial_pixels": 1,
                        "geometric_full_pixels": 3,
                        "partial_edge_inference": "available_from_geometric_warp_coverage",
                    },
                    "dq_provenance_summary": {
                        "schema_version": 1,
                        "source_schema": "resident_dq_coverage_provenance",
                        "stage": "integration",
                        "item": "H",
                        "engine": "cuda_resident_stack",
                        "active_frame_count": 2,
                        "zero_coverage_pixels": 0,
                        "partial_coverage_pixels": 1,
                        "valid_pixels": 3,
                        "no_data_pixels": 0,
                        "warp_edge_pixels": 1,
                    },
                    "output_map_policy": {
                        "mode": "science",
                        "available": ["master", "weight", "dq", "coverage"],
                        "written": ["master", "weight", "dq", "coverage"],
                        "skipped": [],
                    },
                }
            ],
        },
    )
    write_json(
        run / "fixture_compare.json",
        {
            "shape_match": True,
            "rms_diff": 0.001,
            "abs_diff_p99": 0.004,
            "timing": {
                "glass_time_seconds": 10.0,
                "reference_time_seconds": 250.0,
                "speedup_vs_reference": 25.0,
            },
            "comparison_region": {"coverage_fraction": 0.97, "compared_pixels": 12345},
        },
    )
    write_json(
        run / "fixture_acceptance_audit.json",
        {
            "status": "passed",
            "passed": True,
            "benchmark_contract": {"name": "fixture_contract", "schema_version": 1},
            "frame_type_counts": {"light": 200, "bias": 20, "dark": 20, "flat": 20},
            "checks": [
                {"name": "minimum_speedup", "passed": True},
                {"name": "maximum_rms_diff", "passed": True},
            ],
            "speedup_summary": {
                "speedup_vs_wbpp": 25.0,
                "glass": {"elapsed_s": 10.0, "weighted_frame_count": 2, "zero_weight_frame_count": 0},
                "wbpp_blackbox": {"elapsed_s": 250.0},
                "comparison": {
                    "shape_match": True,
                    "rms_diff": 0.001,
                    "abs_diff_p99": 0.004,
                    "coverage_fraction": 0.97,
                    "compared_pixels": 12345,
                },
            },
            "summary": {
                "output_numerical_drift_count": 1,
                "output_numerical_drift_max_relative_rms": 0.011916,
            },
            "output_numerical_drifts": [
                {
                    "key": "H:200:F000061:F000260",
                    "field": "master_path",
                    "drift": {
                        "available": True,
                        "joint_finite_pixels": 61651200,
                        "nonfinite_mismatch_pixels": 0,
                        "mean_signed": 0.000111721,
                        "mean_abs": 0.642260,
                        "median_abs": 0.417107,
                        "rms": 3.751400,
                        "p95_abs": 1.489120,
                        "p99_abs": 3.408920,
                        "max_abs": 1836.101562,
                        "baseline_std": 314.820862,
                        "candidate_std": 314.730194,
                        "relative_rms_to_baseline_std": 0.011916,
                    },
                }
            ],
        },
    )
    report = tmp_path / "resident_report.html"
    assert main(["report", "--run", str(run), "--out", str(report)]) == 0
    html = report.read_text(encoding="utf-8")
    assert "Report navigation" in html
    assert '<nav class="report-toc"' in html
    assert 'class="section-anchor"' in html
    assert 'href="#benchmark-comparison"' in html
    assert 'id="benchmark-comparison"' in html
    assert 'href="#optimization-guidance"' in html
    assert 'id="optimization-guidance"' in html
    assert 'href="#resident-output-maps"' in html
    assert 'id="resident-output-maps"' in html
    assert 'href="#acceptance-check-failures"' in html
    assert 'id="acceptance-check-failures"' in html
    assert 'href="#output-numerical-drift"' in html
    assert 'id="output-numerical-drift"' in html
    assert "Benchmark comparison" in html
    assert "Optimization guidance" in html
    assert "I/O + upload + calibration overlap" in html
    assert "Resident registration/warp batching" in html
    assert "Acceptance check failures" in html
    assert "Output numerical drift" in html
    assert "H:200:F000061:F000260" in html
    assert "relative_rms_to_baseline_std" in html
    assert "0.011916" in html
    assert "3.7514" in html
    assert "Only failed acceptance-audit checks" in html
    assert "fixture_contract" in html
    assert "fixture_compare.json" in html
    assert "fixture_acceptance_audit.json" in html
    assert "25.0" in html
    assert "0.97" in html
    assert "12345" in html
    assert "Resident CUDA summary" in html
    assert "cuda_resident_stack" in html
    assert "Test GPU" in html
    assert "estimated_peak_gib" in html
    assert "prefetch_frames" in html
    assert "read_decode_s" in html
    assert "read_decode_worker_s" in html
    assert "h2d_calibrate_store_s" in html
    assert "registration_warp_s" in html
    assert "registration_accounted_s" in html
    assert "registration_orchestration_s" in html
    assert "similarity_cuda_triangle" in html
    assert "lanczos3" in html
    assert "resident_grid_mean_std" in html
    assert "simple_snr" in html
    assert "winsorized_sigma" in html
    assert "Output map policy" in html
    assert "science" in html
    assert "master, weight, dq, coverage" in html
    assert "low_rejection, high_rejection" in html
    assert "Resident output maps" in html
    assert "integration/resident_master_H.fits" in html
    assert "resident_weight_map_H.fits" in html
    assert "estimated_mib" in html
    assert "float32" in html
    assert "int16" in html
    assert "0.125" in html
    assert "skipped" in html
    assert "Output diagnostics" in html
    assert "normalization_scale" in html
    assert "1.5" in html
    assert "gt_65535_count" in html
    assert "clipping_probe" not in html
    assert "output_diagnostics" not in html
    assert "Geometric warp coverage" in html
    assert "DQ provenance contract" in html
    assert "resident_dq_coverage_provenance" in html
    assert "available_from_geometric_warp_coverage" in html
    assert "geometric_partial_pixels" in html
    assert "ResidentCalibratedStack warp coverage accumulator" in html


def test_cli_report_lists_failed_acceptance_checks(tmp_path: Path):
    run = tmp_path / "run"
    run.mkdir()
    write_json(run / "run_timing.json", {"command": "run", "backend": "cuda", "total_elapsed_s": 12.0, "stages": []})
    write_json(run / "integration_results.json", {"outputs": [], "frame_weights": {}})
    write_json(
        run / "failure_compare.json",
        {
            "shape_match": True,
            "rms_diff": 0.25,
            "abs_diff_p99": 0.5,
            "timing": {"glass_time_seconds": 12.0, "reference_time_seconds": 120.0, "speedup_vs_reference": 10.0},
            "comparison_region": {"coverage_fraction": 0.8, "compared_pixels": 99},
        },
    )
    write_json(
        run / "failure_acceptance_audit.json",
        {
            "status": "failed",
            "passed": False,
            "benchmark_contract": {"name": "failure_contract"},
            "frame_type_counts": {"light": 200, "bias": 20, "dark": 20, "flat": 20},
            "checks": [
                {
                    "name": "maximum_rms_diff",
                    "passed": False,
                    "evidence": {"actual": 0.25, "required_max": 0.01, "source": "compare"},
                    "note": "RMS exceeded benchmark contract",
                },
                {
                    "name": "minimum_speedup",
                    "passed": True,
                    "evidence": {"actual": 10.0, "required": 2.0},
                },
            ],
            "speedup_summary": {
                "speedup_vs_wbpp": 10.0,
                "glass": {"elapsed_s": 12.0, "weighted_frame_count": 190, "zero_weight_frame_count": 10},
                "wbpp_blackbox": {"elapsed_s": 120.0},
                "comparison": {"shape_match": True, "rms_diff": 0.25, "abs_diff_p99": 0.5, "coverage_fraction": 0.8},
            },
        },
    )

    report = tmp_path / "failure_report.html"
    assert main(["report", "--run", str(run), "--out", str(report)]) == 0
    html = report.read_text(encoding="utf-8")

    assert "Benchmark comparison" in html
    assert "failure_contract" in html
    assert "checks_failed" in html
    assert "Acceptance check failures" in html
    assert "maximum_rms_diff" in html
    assert "RMS exceeded benchmark contract" in html
    assert "0.25" in html
    assert "0.01" in html
    assert "source=compare" in html
    assert "minimum_speedup" not in html


def test_cli_report_summarizes_stack_engine_contract(tmp_path: Path):
    run = tmp_path / "run"
    run.mkdir()
    write_json(
        run / "stack_engine_contract.json",
        {
            "audit_type": "stack_engine_default_contract",
            "status": "failed",
            "passed": False,
            "scope": "all",
            "expected_integration_engine": "stack_engine_cpu",
            "checks": [
                {
                    "name": "calibration_masters_use_stack_engine",
                    "passed": False,
                    "note": "fixture legacy fallback",
                    "evidence": {"master_count": 1, "failed": ["bias_bad"]},
                },
                {
                    "name": "integration_outputs_use:stack_engine_cpu",
                    "passed": True,
                    "evidence": {"output_count": 1, "failed": []},
                },
            ],
            "calibration": {
                "master_count": 1,
                "masters": [
                    {
                        "name": "bias_bad",
                        "type": "bias",
                        "tile_stack_mode": "legacy_streaming_accumulator",
                        "contract_ok": False,
                        "has_dq_provenance": False,
                        "summary_source_schema": None,
                        "fallback_reason": "fixture fallback",
                    }
                ],
            },
            "integration": {
                "output_count": 1,
                "outputs": [
                    {
                        "index": 0,
                        "filter": "H",
                        "tile_stack_mode": "stack_engine_cpu",
                        "summary_engine": "stack_engine_cpu",
                        "summary_source_schema": "stack_engine_dq_provenance",
                        "contract_ok": True,
                        "has_stack_engine_dq_provenance": True,
                        "expected_engine": "stack_engine_cpu",
                    }
                ],
            },
        },
    )

    report = tmp_path / "stack_contract_report.html"
    assert main(["report", "--run", str(run), "--out", str(report)]) == 0
    html = report.read_text(encoding="utf-8")

    assert "StackEngine contract audit" in html
    assert "stack_engine_contract.json" in html
    assert "calibration_masters_use_stack_engine" in html
    assert "fixture legacy fallback" in html
    assert "bias_bad" in html
    assert "legacy_streaming_accumulator" in html
    assert "integration_outputs_use:stack_engine_cpu" not in html


def test_cli_report_summarizes_pipeline_contract(tmp_path: Path):
    run = tmp_path / "run"
    run.mkdir()
    write_json(
        run / "pipeline_contract.json",
        {
            "audit_type": "pipeline_invariant_contract",
            "status": "failed",
            "passed": False,
            "artifacts": {
                "warp": {"exists": True, "path": "warp_results.json"},
                "local_norm": {"exists": True, "path": "local_norm_results.json"},
                "integration": {"exists": True, "path": "integration_results.json"},
            },
            "checks": [
                {
                    "name": "integration_output_maps_available",
                    "passed": False,
                    "note": "fixture missing coverage",
                    "evidence": {"map_count": 2, "failed": ["H:coverage"]},
                },
                {
                    "name": "integration_artifact_exists",
                    "passed": True,
                    "evidence": {"path": "integration_results.json"},
                },
            ],
            "integration": {
                "maps": [
                    {
                        "surface": "integration",
                        "item": "H",
                        "map": "coverage",
                        "exists": False,
                        "required": True,
                        "policy_skipped": False,
                        "ok": False,
                        "path": None,
                    }
                ]
            },
            "pixel_verification": {
                "enabled": True,
                "tile_size": 32,
                "tolerance_pixels": 0,
                "integration_outputs": [
                    {
                        "item": "H",
                        "dq": {
                            "status": "verified",
                            "ok": False,
                            "path": "integration/dq_H.fits",
                            "summary_matches": {
                                "valid": {"actual": 41, "summary": 42, "delta": -1, "passed": False}
                            },
                        },
                        "count_maps": {
                            "coverage": {
                                "status": "verified",
                                "ok": False,
                                "summary_match": {
                                    "no_data": {"actual": 2, "summary": 1, "delta": 1, "passed": False}
                                },
                            },
                            "low_rejection": {
                                "status": "verified",
                                "ok": True,
                                "summary_match": {
                                    "low_rejected": {"actual": 5, "summary": 5, "delta": 0, "passed": True}
                                },
                            },
                            "high_rejection": {"status": "not_required", "ok": True},
                        },
                    }
                ],
            },
            "local_normalization": {
                "outputs": [
                    {
                        "frame_id": "F1",
                        "enabled": True,
                        "status": "ok",
                        "crop_box_recorded": True,
                        "normalized_path_exists": True,
                        "coverage_path_exists": True,
                        "dq_mask_path_exists": True,
                        "coefficient_grid_exists": True,
                        "contract_ok": True,
                    }
                ]
            },
            "warp": {
                "outputs": [
                    {
                        "frame_id": "F1",
                        "interpolation": "bilinear",
                        "registered_path_exists": True,
                        "coverage_path_exists": True,
                        "dq_mask_path_exists": True,
                        "dq_summary_has_valid": True,
                        "contract_ok": True,
                    }
                ],
                "skipped_frames": [],
            },
        },
    )

    report = tmp_path / "pipeline_contract_report.html"
    assert main(["report", "--run", str(run), "--out", str(report)]) == 0
    html = report.read_text(encoding="utf-8")

    assert "Pipeline contract audit" in html
    assert "pipeline_contract.json" in html
    assert "integration_output_maps_available" in html
    assert "fixture missing coverage" in html
    assert "H:coverage" in html
    assert "pixel_verification" in html
    assert "integration/dq_H.fits" in html
    assert "low_rejected" in html
    assert "<td>-1</td>" in html
    assert "<td>5</td><td>5</td><td>0</td><td>True</td>" in html
    assert "local-normalization" in html
    assert "bilinear" in html
    assert "integration_artifact_exists" not in html


def test_cli_report_limits_large_audit_tables(tmp_path: Path):
    run = tmp_path / "run"
    run.mkdir()
    frames = [
        {
            "id": f"frame_{index:04d}",
            "path": f"lights/frame_{index:04d}.fits",
            "frame_type": "light",
        }
        for index in range(205)
    ]
    quality_rows = [
        {
            "frame_id": f"quality_{index:04d}",
            "star_count": 20,
            "background_rms": 1.0,
            "weight": 1.0,
        }
        for index in range(202)
    ]
    write_json(run / "manifest.json", {"frames": frames, "summary": {"count": len(frames)}})
    write_json(
        run / "frame_quality.json",
        {
            "frame_quality": quality_rows,
            "reference_frame_id": "quality_0000",
            "star_detector": "fixture_detector",
            "weight_source": "fixture_weight",
        },
    )

    report = tmp_path / "large_table_report.html"
    assert main(["report", "--run", str(run), "--out", str(report)]) == 0
    html = report.read_text(encoding="utf-8")

    assert "Showing first 200 of 205 input frames" in html
    assert "Full details remain in <code>manifest.json</code>" in html
    assert "frame_0199" in html
    assert "frame_0200" not in html
    assert "Showing first 200 of 202 frame quality rows" in html
    assert "Full details remain in <code>frame_quality.json</code>" in html
    assert "quality_0199" in html
    assert "quality_0200" not in html
