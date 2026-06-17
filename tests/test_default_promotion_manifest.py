from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.gpu.compatibility import recommend_windows_cuda_packages
from glass.io.json_io import read_json, write_json
from glass.report.default_promotion_manifest import build_default_promotion_manifest


def _write_release_decision(path: Path, *, ready: bool = True) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "artifact_type": "release_promotion_decision",
            "status": "default_change_ready" if ready else "release_candidate_ready",
            "passed": True,
            "release_candidate_ready": True,
            "default_change_ready": ready,
            "recommendation": "promote_default_candidate"
            if ready
            else "repeat_benchmark_before_default_change",
            "speedup": {"actual": 58.1, "required_min": 2.0},
            "runtime_repeat": {
                "present": True,
                "run_count": 3,
                "considered_run_count": 3,
                "best_label": "repeat02",
                "best_elapsed_s": 22.6,
                "slowest_elapsed_s": 23.8,
                "elapsed_ratio_vs_best": 1.053,
                "max_elapsed_ratio_vs_best": 1.25,
                "recommendation": "best_observed:repeat02",
            },
        },
    )


def _write_phase2_status(
    path: Path,
    decision: Path,
    *,
    ready: bool = True,
    include_default_route: bool = True,
    default_route_ready: bool = True,
    rejection_sample_accounting_ready: bool = True,
) -> None:
    pipeline_ready = ready and rejection_sample_accounting_ready
    payload = {
        "schema_version": 1,
        "artifact_type": "glass_phase2_status",
        "status": "green" if pipeline_ready else "attention_required",
        "passed": pipeline_ready,
        "latest_checkpoint": {
            "gate": 236,
            "status": "green" if ready else "failed",
            "green": ready,
        },
        "release_decision": {
            "artifact_type": "release_promotion_decision",
            "path": str(decision),
            "status": "default_change_ready" if ready else "release_candidate_ready",
            "passed": True,
            "release_candidate_ready": True,
            "default_change_ready": ready,
            "recommendation": "promote_default_candidate"
            if ready
            else "repeat_benchmark_before_default_change",
            "runtime_repeat_present": True,
            "runtime_repeat_considered_run_count": 3,
            "runtime_repeat_elapsed_ratio_vs_best": 1.053,
        },
        "pipeline_contract": {
            "audit_type": "pipeline_invariant_contract",
            "status": "passed" if rejection_sample_accounting_ready else "failed",
            "passed": rejection_sample_accounting_ready,
            "check_count": 15,
            "failed_check_count": 0 if rejection_sample_accounting_ready else 1,
            "failed_checks": []
            if rejection_sample_accounting_ready
            else ["integration_rejection_sample_counts_match_maps"],
            "integration_output_count": 1,
            "integration_map_count": 6,
            "integration_dq_contract": True,
            "integration_stack_result_contract": True,
            "integration_resident_result_contract": True,
            "integration_dq_map_pixels_match_summary": True,
            "integration_coverage_map_pixels_match_dq": True,
            "integration_rejection_map_pixels_match_dq": True,
            "integration_rejection_sample_counts_match_maps": rejection_sample_accounting_ready,
            "rejection_sample_accounting": {
                "status": "passed" if rejection_sample_accounting_ready else "failed",
                "check_present": True,
                "check_passed": rejection_sample_accounting_ready,
                "failed_count": 0 if rejection_sample_accounting_ready else 1,
                "failed_items": []
                if rejection_sample_accounting_ready
                else [
                    {
                        "item": "H",
                        "map_rejected_sample_sum": 7,
                        "source_counts": [
                            {
                                "name": "dq_coverage_provenance.rejected_sample_count",
                                "count": 6,
                            }
                        ],
                    }
                ],
            },
            "rejection_sample_accounting_status": "passed"
            if rejection_sample_accounting_ready
            else "failed",
            "rejection_sample_accounting_failed_count": 0
            if rejection_sample_accounting_ready
            else 1,
            "pixel_verification_enabled": True,
            "pixel_verification_tile_size": 2048,
            "resident_native_calibration_artifact": True,
            "resident_calibrated_light_count": 200,
        },
    }
    if include_default_route:
        payload["default_route_acceptance"] = {
            "path": "C:/glass_runs/run/default_route_acceptance.json",
            "status": "passed" if default_route_ready else "failed",
            "passed": default_route_ready,
            "acceptance_passed": default_route_ready,
            "benchmark_contract": {"name": "default_route_fixture_contract"},
            "speedup_vs_reference": 28.75,
            "active_frames": 193,
            "route_contract_passed": default_route_ready,
            "route_check_count": 4 if default_route_ready else 2,
            "route_failed_checks": []
            if default_route_ready
            else ["contract_required_command_token:--backend cuda"],
        }
    write_json(path, payload)


def _write_doctor(path: Path) -> None:
    devices = [
        {
            "device_id": 0,
            "name": "NVIDIA RTX PRO 6000 Blackwell Workstation Edition",
            "compute_capability": "12.0",
            "driver_version": "596.21",
        }
    ]
    write_json(
        path,
        {
            "schema_version": 1,
            "product": "GLASS",
            "recommendation": "cuda",
            "cuda": {
                "wrapper_importable": True,
                "native_extension_loaded": True,
                "cuda_available": True,
                "probe_skipped": False,
                "devices": devices,
            },
            "windows_cuda_packages": recommend_windows_cuda_packages(devices),
        },
    )


def test_default_promotion_manifest_passes_ready_artifacts(tmp_path: Path) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    doctor = tmp_path / "doctor.json"
    _write_release_decision(decision)
    _write_phase2_status(phase2, decision)
    _write_doctor(doctor)

    payload = build_default_promotion_manifest(
        release_decision_json=decision,
        phase2_status_json=phase2,
        doctor_json=doctor,
        require_doctor=True,
        min_runtime_runs=3,
    )

    checks = {item["name"]: item["passed"] for item in payload["checks"]}
    assert payload["passed"] is True
    assert payload["status"] == "default_promotion_ready"
    assert payload["recommendation"] == "promote_resident_cuda_default"
    assert payload["default_candidate"]["memory_mode"] == "resident"
    assert payload["default_candidate"]["fallback_memory_mode"] == "tile"
    assert payload["default_route_acceptance"]["route_contract_passed"] is True
    assert checks["runtime_repeat_ratio_within_bound"] is True
    assert checks["default_route_acceptance_present"] is True
    assert checks["default_route_acceptance_passed"] is True
    assert checks["default_route_acceptance_route_contract_passed"] is True
    assert checks["default_route_acceptance_route_check_count"] is True
    assert checks["pipeline_pixel_maps_match_dq"] is True
    assert checks["pipeline_rejection_sample_accounting_passed"] is True
    assert checks["windows_package_try_list_has_cpu_fallback"] is True


def test_default_promotion_manifest_blocks_unready_release_decision(tmp_path: Path) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    _write_release_decision(decision, ready=False)
    _write_phase2_status(phase2, decision, ready=False)

    payload = build_default_promotion_manifest(
        release_decision_json=decision,
        phase2_status_json=phase2,
    )

    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert "release_decision_default_change_ready" in payload["failed_checks"]
    assert "phase2_status_green" in payload["failed_checks"]


def test_default_promotion_manifest_blocks_missing_default_route_evidence(tmp_path: Path) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    _write_release_decision(decision)
    _write_phase2_status(phase2, decision, include_default_route=False)

    payload = build_default_promotion_manifest(
        release_decision_json=decision,
        phase2_status_json=phase2,
    )

    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert "default_route_acceptance_present" in payload["failed_checks"]
    assert "default_route_acceptance_passed" in payload["failed_checks"]
    assert "default_route_acceptance_route_contract_passed" in payload["failed_checks"]
    assert "default_route_acceptance_route_check_count" in payload["failed_checks"]


def test_default_promotion_manifest_blocks_failed_default_route_evidence(tmp_path: Path) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    _write_release_decision(decision)
    _write_phase2_status(phase2, decision, default_route_ready=False)

    payload = build_default_promotion_manifest(
        release_decision_json=decision,
        phase2_status_json=phase2,
    )

    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert "default_route_acceptance_present" not in payload["failed_checks"]
    assert "default_route_acceptance_passed" in payload["failed_checks"]
    assert "default_route_acceptance_route_contract_passed" in payload["failed_checks"]
    assert "default_route_acceptance_route_check_count" in payload["failed_checks"]


def test_default_promotion_manifest_blocks_rejection_sample_accounting_drift(
    tmp_path: Path,
) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    _write_release_decision(decision)
    _write_phase2_status(phase2, decision, rejection_sample_accounting_ready=False)

    payload = build_default_promotion_manifest(
        release_decision_json=decision,
        phase2_status_json=phase2,
    )

    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert "phase2_status_green" in payload["failed_checks"]
    assert "pipeline_contract_passed" in payload["failed_checks"]
    assert "pipeline_rejection_sample_accounting_passed" in payload["failed_checks"]


def test_default_promotion_manifest_cli_writes_json_and_markdown(tmp_path: Path) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    doctor = tmp_path / "doctor.json"
    out = tmp_path / "manifest.json"
    markdown = tmp_path / "manifest.md"
    _write_release_decision(decision)
    _write_phase2_status(phase2, decision)
    _write_doctor(doctor)

    result = main(
        [
            "default-promotion-manifest",
            "--release-decision",
            str(decision),
            "--phase2-status",
            str(phase2),
            "--doctor-json",
            str(doctor),
            "--require-doctor",
            "--min-runtime-runs",
            "3",
            "--out",
            str(out),
            "--markdown",
            str(markdown),
            "--fail-on-not-ready",
        ]
    )

    assert result == 0
    payload = read_json(out)
    assert payload["passed"] is True
    markdown_text = markdown.read_text(encoding="utf-8")
    assert "Default Promotion Manifest" in markdown_text
    assert "Default Route Evidence" in markdown_text
    assert "Rejection sample accounting: `passed`" in markdown_text
    assert "Route contract passed: `True`" in markdown_text
