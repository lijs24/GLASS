from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.engine.resident_component_timing import (
    build_resident_component_timing,
    materialize_resident_component_timing,
)
from glass.engine.resident_registration_runtime_contract import (
    write_resident_registration_runtime_contract,
)
from glass.io.json_io import read_json, write_json
from glass.report.phase2_mainline_audit import build_phase2_mainline_audit


def _touch(path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("fixture", encoding="utf-8")
    return str(path)


def _write_green_run(run: Path) -> None:
    integration = run / "integration"
    maps = {
        "master_path": _touch(integration / "resident_master_H.fits"),
        "weight_map_path": _touch(integration / "resident_weight_map_H.fits"),
        "coverage_map_path": _touch(integration / "resident_coverage_map_H.fits"),
        "low_rejection_map_path": _touch(integration / "resident_low_rejection_map_H.fits"),
        "high_rejection_map_path": _touch(integration / "resident_high_rejection_map_H.fits"),
        "dq_map_path": _touch(integration / "resident_dq_map_H.fits"),
    }
    write_json(
        run / "run_timing.json",
        {
            "backend": "cuda",
            "memory_mode": "resident",
            "resident_runtime_preset": "throughput-v4-native-completion",
            "resident_registration": "similarity_cuda_triangle",
            "integration_rejection": "winsorized_sigma",
            "local_normalization": "on",
            "resident_local_normalization_mode": "grid_mean_std",
            "resident_warp_interpolation": "lanczos3",
            "resident_fits_read_mode_resolution": {"effective": "auto"},
            "resident_memory_lifecycle_path": "resident_memory_lifecycle.json",
            "resident_memory_lifecycle_summary": {
                "group_count": 1,
                "failed_group_count": 0,
                "raw_all_frames_resident": False,
                "calibrated_stack_resident": True,
                "registered_cache_materialized_on_disk": False,
                "max_estimated_calibrated_stack_bytes": 800,
                "max_estimated_peak_bytes": 1200,
            },
            "total_elapsed_s": 12.5,
            "stages": [
                {"stage": "resident_reference_scout", "elapsed_s": 1.0},
                {"stage": "resident_reference_health", "elapsed_s": 1.5},
                {"stage": "resident_calibration_integration", "elapsed_s": 9.5},
                {"stage": "pipeline_contract", "elapsed_s": 0.1},
                {"stage": "stack_engine_contract", "elapsed_s": 0.02},
                {"stage": "warp_quality_contract", "elapsed_s": 0.03},
            ],
        },
    )
    write_json(
        run / "run_state.json",
        {
            "current_stage": "integration",
            "completed_stages": [
                "resident_light_calibration",
                "resident_registration",
                "resident_local_normalization",
                "resident_integration",
            ],
            "failed_stage": None,
            "errors": [],
        },
    )
    write_json(
        run / "frame_accounting.json",
        {
            "artifact": "frame_accounting",
            "summary": {
                "input_light_frames": 200,
                "resident_frame_mask_active_frames": 193,
                "resident_frame_mask_masked_frames": 7,
                "resident_dq_lifecycle_present": True,
                "resident_dq_lifecycle_status": "passed",
                "resident_dq_lifecycle_passed": True,
                "resident_dq_lifecycle_rows": 200,
                "resident_dq_lifecycle_active_frames": 193,
                "resident_dq_lifecycle_masked_frames": 7,
                "resident_dq_lifecycle_source_input_samples": 11898681600,
                "resident_source_dq_contract_rows": 200,
            },
        },
    )
    write_json(
        run / "resident_artifacts.json",
        {
            "backend": "cuda_resident_stack",
            "artifacts": [
                {
                    **maps,
                    "timing_s": {
                        "light_read_upload_calibrate": 3.1,
                        "resident_registration_warp": 0.27,
                        "resident_local_normalization": 0.41,
                        "resident_integration": 3.28,
                        "output_write": 0.25,
                    },
                    "triangle_catalog_batch": True,
                    "triangle_descriptor_generation_batch": True,
                    "triangle_descriptor_fit_batch": True,
                    "triangle_warp_batch": True,
                    "triangle_warp_batch_mode": "native_matrix_lanczos3_frames",
                    "triangle_warp_batch_dispatch": "chunked",
                    "triangle_warp_batch_frame_count": 192,
                    "triangle_warp_batch_fallback_frame_count": 0,
                    "triangle_warp_batch_native_chunk_count": 24,
                    "triangle_warp_batch_native_chunk_frames": 8,
                    "triangle_warp_batch_native_total_s": 0.49,
                    "warp_coverage": {
                        "available": True,
                        "frame_count": 193,
                        "warped_frame_count": 192,
                    },
                }
            ],
        },
    )
    timing = read_json(run / "run_timing.json")
    component_timing = build_resident_component_timing(run, timing=timing)
    write_json(run / "resident_component_timing.json", component_timing)
    materialize_resident_component_timing(timing, component_timing)
    write_json(run / "run_timing.json", timing)
    write_json(
        run / "resident_frame_masks.json",
        {
            "summary": {
                "passed": True,
                "frame_count": 200,
                "active_frame_count": 193,
                "masked_frame_count": 7,
            }
        },
    )
    write_json(
        run / "resident_reference_health.json",
        {
            "passed": True,
            "status": "passed",
            "summary": {
                "cpu_crosscheck_reused": True,
                "calibrated_available": True,
                "cuda_calibrated_available": True,
            },
        },
    )
    write_json(
        run / "resident_dq_lifecycle.json",
        {
            "summary": {
                "passed": True,
                "status": "passed",
                "frame_count": 200,
                "active_frame_count": 193,
                "masked_frame_count": 7,
            }
        },
    )
    write_json(
        run / "resident_memory_lifecycle.json",
        {
            "artifact_type": "resident_memory_lifecycle",
            "passed": True,
            "status": "passed",
            "summary": {
                "group_count": 1,
                "failed_group_count": 0,
                "raw_all_frames_resident": False,
                "calibrated_stack_resident": True,
                "registered_cache_materialized_on_disk": False,
                "max_estimated_calibrated_stack_bytes": 800,
                "max_estimated_peak_bytes": 1200,
            },
        },
    )
    for name in (
        "resident_source_dq_execution.json",
        "resident_dq_pixel_closure.json",
        "resident_master_cache.json",
    ):
        write_json(run / name, {"summary": {"passed": True, "status": "passed"}})
    for name in (
        "pipeline_contract.json",
        "stack_engine_contract.json",
        "warp_quality_contract.json",
        "resident_result_contract.json",
        "resident_calibration_contract.json",
    ):
        write_json(run / name, {"passed": True, "status": "passed"})
    for name in (
        "integration_results.json",
        "calibration_artifacts.json",
        "frame_quality.json",
        "resident_registration_quality.json",
        "local_norm_results.json",
        "resident_reference_scout.json",
        "resident_stage_ledger.json",
    ):
        write_json(run / name, {"passed": True, "status": "passed"})
    write_json(
        run / "registration_results.json",
        {
            "results": [
                *({"frame_id": f"F{i:03d}", "status": "ok"} for i in range(1, 193)),
                {"frame_id": "F193", "status": "reference"},
                *({"frame_id": f"F{i:03d}", "status": "excluded"} for i in range(194, 201)),
            ]
        },
    )
    write_resident_registration_runtime_contract(run)


def _write_acceptance_and_compare(tmp_path: Path, run: Path) -> tuple[Path, Path]:
    compare = tmp_path / "compare.json"
    write_json(
        compare,
        {
            "shape_match": True,
            "rms_diff": 0.005,
            "abs_diff_p99": 0.002,
            "comparison_region": {"coverage_fraction": 0.975, "compared_pixels": 100},
            "full_frame_stats": {"rms_diff": 0.013, "abs_diff_p99": 0.008},
        },
    )
    acceptance = tmp_path / "acceptance.json"
    write_json(
        acceptance,
        {
            "passed": True,
            "status": "passed",
            "glass_run": str(run),
            "compare_json": str(compare),
            "speedup_summary": {
                "speedup_vs_wbpp": 87.0,
                "comparison": {
                    "shape_match": True,
                    "rms_diff": 0.005,
                    "abs_diff_p99": 0.002,
                    "coverage_fraction": 0.975,
                    "compared_pixels": 100,
                },
            },
        },
    )
    return acceptance, compare


def test_phase2_mainline_audit_passes_green_resident_run(tmp_path: Path) -> None:
    run = tmp_path / "run"
    _write_green_run(run)
    acceptance, compare = _write_acceptance_and_compare(tmp_path, run)

    audit = build_phase2_mainline_audit(
        run,
        acceptance_audit=acceptance,
        compare_json=compare,
        min_speedup=50,
        min_coverage_fraction=0.97,
        max_rms_diff=0.006,
        max_abs_diff_p99=0.003,
        require_acceptance=True,
        require_compare=True,
    )

    assert audit["passed"] is True
    assert audit["summary"]["input_light_frames"] == 200
    assert audit["summary"]["active_frames"] == 193
    assert audit["summary"]["speedup_vs_wbpp"] == 87.0
    assert audit["next_priorities"][0]["area"] == "resident calibration/integration execution"
    assert audit["next_priorities"][1]["area"] == "reference calibrated-health resident reuse"
    assert audit["next_priorities"][1]["evidence"]["cpu_crosscheck_reused"] is True
    checks = {check["name"]: check for check in audit["checks"]}
    ledger = checks["resident_stage_ledger_component_contract"]["evidence"]
    assert ledger["stage_status"]["resident_calibration"] == "complete"
    assert "resident_light_calibration" not in ledger["stage_status"]


def test_phase2_mainline_audit_fails_missing_output_map(tmp_path: Path) -> None:
    run = tmp_path / "run"
    _write_green_run(run)
    Path(read_json(run / "resident_artifacts.json")["artifacts"][0]["dq_map_path"]).unlink()

    audit = build_phase2_mainline_audit(run)

    assert audit["passed"] is False
    assert "resident_output_maps_present" in audit["failed_checks"]


def test_phase2_mainline_audit_fails_missing_component_ledger_artifact(tmp_path: Path) -> None:
    run = tmp_path / "run"
    _write_green_run(run)
    (run / "resident_calibration_contract.json").unlink()

    audit = build_phase2_mainline_audit(run)

    assert audit["passed"] is False
    assert "resident_stage_ledger_component_contract" in audit["failed_checks"]
    checks = {check["name"]: check for check in audit["checks"]}
    evidence = checks["resident_stage_ledger_component_contract"]["evidence"]
    assert evidence["summary"]["missing_artifact_count"] == 1


def test_phase2_mainline_audit_fails_missing_memory_lifecycle_artifact(
    tmp_path: Path,
) -> None:
    run = tmp_path / "run"
    _write_green_run(run)
    (run / "resident_memory_lifecycle.json").unlink()

    audit = build_phase2_mainline_audit(run)

    assert audit["passed"] is False
    assert "core_artifacts_present" in audit["failed_checks"]
    assert "resident_memory_lifecycle_contract" in audit["failed_checks"]
    checks = {check["name"]: check for check in audit["checks"]}
    evidence = checks["resident_memory_lifecycle_contract"]["evidence"]
    assert evidence["exists"] is False


def test_phase2_mainline_audit_fails_nonresident_memory_lifecycle(
    tmp_path: Path,
) -> None:
    run = tmp_path / "run"
    _write_green_run(run)
    payload = read_json(run / "resident_memory_lifecycle.json")
    payload["summary"]["calibrated_stack_resident"] = False
    write_json(run / "resident_memory_lifecycle.json", payload)

    audit = build_phase2_mainline_audit(run)

    assert audit["passed"] is False
    assert "resident_memory_lifecycle_contract" in audit["failed_checks"]
    checks = {check["name"]: check for check in audit["checks"]}
    evidence = checks["resident_memory_lifecycle_contract"]["evidence"]
    assert evidence["summary"]["calibrated_stack_resident"] is False


def test_phase2_mainline_audit_fails_missing_component_timing_artifact(tmp_path: Path) -> None:
    run = tmp_path / "run"
    _write_green_run(run)
    (run / "resident_component_timing.json").unlink()

    audit = build_phase2_mainline_audit(run)

    assert audit["passed"] is False
    assert "core_artifacts_present" in audit["failed_checks"]
    assert "timing_components_available" in audit["failed_checks"]
    checks = {check["name"]: check for check in audit["checks"]}
    evidence = checks["timing_components_available"]["evidence"]
    assert evidence["component_artifact"]["exists"] is False


def test_phase2_mainline_audit_fails_missing_required_component_timing(
    tmp_path: Path,
) -> None:
    run = tmp_path / "run"
    _write_green_run(run)
    payload = read_json(run / "resident_component_timing.json")
    for row in payload["components"]:
        if row["source_key"] == "resident_registration_warp":
            row["elapsed_s"] = None
            row["status"] = "missing"
    payload["passed"] = False
    payload["status"] = "failed"
    payload["summary"]["missing_required_components"] = ["resident_registration_warp"]
    write_json(run / "resident_component_timing.json", payload)

    audit = build_phase2_mainline_audit(run)

    assert audit["passed"] is False
    assert "timing_components_available" in audit["failed_checks"]
    checks = {check["name"]: check for check in audit["checks"]}
    evidence = checks["timing_components_available"]["evidence"]
    assert evidence["component_artifact"]["passed"] is False
    assert evidence["component_artifact"]["missing_required_components"] == [
        "resident_registration_warp"
    ]


def test_phase2_mainline_audit_cli_writes_markdown(tmp_path: Path) -> None:
    run = tmp_path / "run"
    _write_green_run(run)
    acceptance, compare = _write_acceptance_and_compare(tmp_path, run)
    out = tmp_path / "mainline.json"
    md = tmp_path / "mainline.md"

    result = main(
        [
            "phase2-mainline-audit",
            "--run",
            str(run),
            "--acceptance-audit",
            str(acceptance),
            "--compare-json",
            str(compare),
            "--out",
            str(out),
            "--markdown",
            str(md),
            "--min-speedup",
            "50",
            "--min-coverage-fraction",
            "0.97",
            "--max-rms-diff",
            "0.006",
            "--max-abs-diff-p99",
            "0.003",
            "--require-acceptance",
            "--require-compare",
            "--fail-on-not-green",
        ]
    )

    assert result == 0
    assert read_json(out)["passed"] is True
    assert "Phase 2 Mainline Audit" in md.read_text(encoding="utf-8")
