from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.phase2_status import build_phase2_status, build_phase2_status_compare


def _write_checkpoint(path: Path, *, gate: int, status: str = "green") -> Path:
    target = path / f"s2_gate_{gate}_status.md"
    target.write_text(
        "\n".join(
            [
                f"# S2-Gate {gate} Status",
                "",
                f"- Gate: S2-Gate {gate}",
                "- Scope: fixture checkpoint",
                f"- Status: {status}",
                "- Date: 2026-06-18",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return target


def _write_acceptance(path: Path) -> None:
    write_json(
        path,
        {
            "status": "passed",
            "passed": True,
            "benchmark_contract": {"name": "fixture_contract"},
            "frame_type_counts": {"light": 200, "bias": 20, "dark": 20, "flat": 20},
            "contract_bundle_schema": {"status": "passed"},
            "native_guardrails_bundle": {
                "status": "present",
                "bundle_status": "passed",
                "resident_result_contract_source": "run_default",
                "resident_result_contract_run_default": True,
                "resident_result_contract_json": "C:/glass_runs/run/resident_result_contract.json",
                "resident_native_calibration_artifact": True,
                "resident_calibration_master_count": 3,
                "resident_calibrated_light_count": 200,
            },
            "resident_registration_fastpath": {
                "exists": True,
                "available": True,
                "artifact_count": 1,
                "path": "C:/glass_runs/run/resident_registration_fastpath.json",
                "resident_registration": {
                    "mode": "similarity_cuda_triangle",
                    "triangle_descriptor_fit_batch": True,
                    "triangle_descriptor_fit_batch_mode": "native_batch_shared_reference_device",
                    "triangle_descriptor_fit_reference_device_reuse": True,
                    "triangle_descriptor_fit_moving_device_reuse": True,
                    "triangle_descriptor_fit_output_device_reuse": True,
                    "triangle_pixel_refine_batch": True,
                    "triangle_pixel_refine_batch_metric_mode": "flattened_frame_candidate_grid",
                    "triangle_warp_batch": True,
                    "triangle_warp_batch_mode": "native_matrix_lanczos3_frames",
                    "triangle_warp_batch_frame_count": 188,
                },
                "artifact": {
                    "resident_warp_copy_mode": "default_stream_async_device_to_device",
                    "resident_warp_scratch_bytes": 493209636,
                },
                "resident_io_pipeline": {
                    "warp_copy_mode": "default_stream_async_device_to_device",
                    "warp_scratch_bytes": 493209636,
                },
            },
            "resident_contracts": {
                "calibration": {"passed": True},
                "result": {"passed": True},
            },
            "checks": [
                {"name": "contract_resident_registration_fastpath_present", "passed": True},
                {
                    "name": "contract_resident_registration_fastpath_true:descriptor_batch",
                    "passed": True,
                },
            ],
            "speedup_summary": {
                "speedup_vs_wbpp": 58.0,
                "glass": {"weighted_frame_count": 193},
                "comparison": {
                    "rms_diff": 0.001,
                    "abs_diff_p99": 0.002,
                    "coverage_fraction": 0.957,
                },
            },
        },
    )


def _write_pipeline_contract(path: Path, *, passed: bool = True) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "audit_type": "pipeline_invariant_contract",
            "status": "passed" if passed else "failed",
            "passed": passed,
            "checks": [
                {"name": "integration_output_maps_available", "passed": passed},
                {"name": "integration_dq_contract", "passed": passed},
                {"name": "integration_stack_result_contract", "passed": passed},
                {"name": "integration_resident_result_contract", "passed": passed},
                {"name": "integration_dq_map_pixels_match_summary", "passed": passed},
                {"name": "integration_coverage_map_pixels_match_dq", "passed": passed},
                {"name": "integration_rejection_map_pixels_match_dq", "passed": passed},
            ],
            "calibration": {
                "master_count": 3,
                "calibrated_light_count": 200,
                "resident_native_calibration_artifact": True,
                "resident_calibrated_light_count": 200,
            },
            "integration": {
                "outputs": [{"item": "H"}],
                "maps": [
                    {"item": "H", "map": "master"},
                    {"item": "H", "map": "coverage"},
                    {"item": "H", "map": "dq"},
                ],
            },
            "pixel_verification": {
                "enabled": True,
                "tile_size": 256,
                "tolerance_pixels": 0,
                "integration_outputs": [],
            },
        },
    )


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
            "speedup": {"actual": 58.0, "required_min": 2.0},
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
            "pipeline_handoff": {
                "source": "explicit_pipeline_contract",
                "status": "passed",
                "passed": True,
                "pixel_verification_enabled": True,
            },
        },
    )


def _doctor_payload() -> dict:
    return {
        "recommendation": "cuda",
        "cuda": {
            "wrapper_importable": True,
            "native_extension_loaded": True,
            "cuda_available": True,
            "devices": [
                {
                    "device_id": 0,
                    "name": "Fixture GPU",
                    "compute_capability": "12.0",
                    "memory_total_mib": 97886,
                    "driver_version": "596.21",
                }
            ],
        },
        "windows_cuda_packages": {"ordered_try_list": ["cuda13", "cuda12", "cuda11", "cpu"]},
    }


def _status_payload(
    *,
    gate: int = 203,
    status: str = "green",
    checkpoint_green: bool = True,
    acceptance_passed: bool = True,
    acceptance_status: str = "passed",
    cuda_available: bool = True,
    release_status: str = "release_manifest_ready",
    github_status: str = "release_plan_ready",
    pipeline_passed: bool = True,
    pipeline_dq_contract: bool = True,
    pixel_verification: bool = True,
    default_change_ready: bool = True,
    release_recommendation: str = "promote_default_candidate",
) -> dict:
    return {
        "schema_version": 1,
        "artifact_type": "glass_phase2_status",
        "status": status,
        "passed": status == "green",
        "latest_checkpoint": {
            "gate": gate,
            "status": "green" if checkpoint_green else "failed",
            "green": checkpoint_green,
        },
        "acceptance_audit": {"status": acceptance_status, "passed": acceptance_passed},
        "doctor": {"cuda_available": cuda_available},
        "release_manifest": {"status": release_status},
        "github_release_plan": {"status": github_status},
        "pipeline_contract": {
            "status": "passed" if pipeline_passed else "failed",
            "passed": pipeline_passed,
            "integration_dq_contract": pipeline_dq_contract,
            "pixel_verification_enabled": pixel_verification,
        },
        "release_decision": {
            "status": "default_change_ready" if default_change_ready else "release_candidate_ready",
            "default_change_ready": default_change_ready,
            "recommendation": release_recommendation,
        },
        "checks": [],
    }


def test_phase2_status_summarizes_green_handoff(tmp_path: Path):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=201)
    latest = _write_checkpoint(checkpoints, gate=202)
    acceptance = tmp_path / "acceptance.json"
    release = tmp_path / "release_manifest.json"
    github_plan = tmp_path / "github_release_plan.json"
    pipeline_contract = tmp_path / "pipeline_contract.json"
    release_decision = tmp_path / "release_decision.json"
    _write_acceptance(acceptance)
    _write_pipeline_contract(pipeline_contract)
    _write_release_decision(release_decision)
    write_json(
        release,
        {
            "status": "release_manifest_ready",
            "passed": True,
            "recommendation": "ready_for_upload",
            "package_count": 4,
            "source_stamp": "abcdef0",
        },
    )
    write_json(
        github_plan,
        {
            "status": "release_plan_ready",
            "tag": "v0.1.0-test",
            "package_count": 4,
            "publication_ready": False,
            "recommendation": "authenticate_github_cli_then_run_release_command",
            "gh": {"available": True, "auth_ok": False},
            "script": {"path": "publish.ps1", "publish_default": False},
        },
    )

    payload = build_phase2_status(
        checkpoint_dir=checkpoints,
        acceptance_audit=acceptance,
        release_manifest=release,
        github_release_plan=github_plan,
        pipeline_contract=pipeline_contract,
        release_decision=release_decision,
        doctor_payload=_doctor_payload(),
    )

    assert payload["status"] == "green"
    assert payload["latest_checkpoint"]["path"] == str(latest)
    assert payload["acceptance_audit"]["speedup_vs_reference"] == 58.0
    assert payload["acceptance_audit"]["native_guardrails_bundle_status"] == "present"
    assert payload["acceptance_audit"]["resident_result_contract_source"] == "run_default"
    assert payload["acceptance_audit"]["resident_result_contract_run_default"] is True
    assert payload["acceptance_audit"]["resident_native_calibration_artifact"] is True
    assert payload["acceptance_audit"]["resident_calibrated_light_count"] == 200
    assert payload["acceptance_audit"]["resident_registration_fastpath_status"] == "present"
    assert payload["acceptance_audit"]["resident_registration_fastpath_contract_status"] == "passed"
    assert payload["acceptance_audit"]["resident_registration_fastpath_mode"] == "similarity_cuda_triangle"
    assert payload["acceptance_audit"]["triangle_descriptor_fit_batch"] is True
    assert payload["acceptance_audit"]["triangle_warp_batch_frame_count"] == 188
    assert payload["doctor"]["primary_gpu"] == "Fixture GPU"
    assert payload["release_manifest"]["package_count"] == 4
    assert payload["github_release_plan"]["status"] == "release_plan_ready"
    assert payload["pipeline_contract"]["status"] == "passed"
    assert payload["pipeline_contract"]["integration_dq_contract"] is True
    assert payload["pipeline_contract"]["integration_stack_result_contract"] is True
    assert payload["pipeline_contract"]["pixel_verification_enabled"] is True
    assert payload["pipeline_contract"]["integration_dq_map_pixels_match_summary"] is True
    assert payload["release_decision"]["status"] == "default_change_ready"
    assert payload["release_decision"]["default_change_ready"] is True
    assert payload["release_decision"]["recommendation"] == "promote_default_candidate"
    assert payload["release_decision"]["runtime_repeat_elapsed_ratio_vs_best"] == 1.053


def test_cli_phase2_status_writes_outputs(tmp_path: Path):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=202)
    acceptance = tmp_path / "acceptance.json"
    out = tmp_path / "phase2_status.json"
    markdown = tmp_path / "phase2_status.md"
    pipeline_contract = tmp_path / "pipeline_contract.json"
    release_decision = tmp_path / "release_decision.json"
    _write_acceptance(acceptance)
    _write_pipeline_contract(pipeline_contract)
    _write_release_decision(release_decision)

    result = main(
        [
            "phase2-status",
            "--checkpoint-dir",
            str(checkpoints),
            "--acceptance-audit",
            str(acceptance),
            "--pipeline-contract",
            str(pipeline_contract),
            "--release-decision",
            str(release_decision),
            "--out",
            str(out),
            "--markdown",
            str(markdown),
            "--skip-cuda-probe",
        ]
    )

    assert result == 0
    payload = read_json(out)
    assert payload["artifact_type"] == "glass_phase2_status"
    assert payload["latest_checkpoint"]["gate"] == 202
    assert payload["acceptance_audit"]["contract_bundle_schema_status"] == "passed"
    assert payload["acceptance_audit"]["resident_result_contract_source"] == "run_default"
    assert payload["pipeline_contract"]["integration_dq_contract"] is True
    assert payload["release_decision"]["default_change_ready"] is True
    text = markdown.read_text(encoding="utf-8")
    assert "GLASS Phase 2 Status" in text
    assert "Acceptance" in text
    assert "Native resident result source: run_default" in text
    assert "Native calibrated lights: 200" in text
    assert "Registration fast path: present" in text
    assert "Triangle warp batch frames: 188" in text
    assert "Pipeline Contract" in text
    assert "Integration DQ contract: True" in text
    assert "DQ pixels match summary: True" in text
    assert "Release Decision" in text
    assert "Default change ready: True" in text
    assert "Runtime repeat ratio vs best: 1.053" in text


def test_phase2_status_compare_passes_non_regression(tmp_path: Path):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    write_json(baseline, _status_payload(gate=203))
    write_json(candidate, _status_payload(gate=204))

    payload = build_phase2_status_compare(
        baseline_status=baseline,
        candidate_status=candidate,
    )

    checks = {item["name"]: item["passed"] for item in payload["checks"]}
    assert payload["status"] == "passed"
    assert checks["latest_checkpoint_gate_not_decreased"] is True
    assert checks["acceptance_audit_passed_preserved"] is True
    assert checks["cuda_available_preserved"] is True
    assert checks["release_manifest_ready_preserved"] is True
    assert checks["pipeline_contract_passed_preserved"] is True
    assert checks["pipeline_integration_dq_contract_preserved"] is True
    assert checks["pipeline_pixel_verification_preserved"] is True
    assert checks["release_decision_default_change_ready_preserved"] is True
    assert checks["release_decision_promote_recommendation_preserved"] is True


def test_phase2_status_compare_flags_handoff_regressions(tmp_path: Path):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    write_json(baseline, _status_payload(gate=203))
    write_json(
        candidate,
        _status_payload(
            gate=202,
            status="attention_required",
            checkpoint_green=False,
            acceptance_passed=False,
            acceptance_status="failed",
            cuda_available=False,
            release_status="failed",
            github_status="failed",
            pipeline_passed=False,
            pipeline_dq_contract=False,
            pixel_verification=False,
            default_change_ready=False,
            release_recommendation="repeat_benchmark_before_default_change",
        ),
    )

    payload = build_phase2_status_compare(
        baseline_status=baseline,
        candidate_status=candidate,
    )

    checks = {item["name"]: item["passed"] for item in payload["checks"]}
    assert payload["status"] == "regressed"
    assert checks["latest_checkpoint_gate_not_decreased"] is False
    assert checks["overall_status_green_preserved"] is False
    assert checks["latest_checkpoint_green_preserved"] is False
    assert checks["acceptance_audit_passed_preserved"] is False
    assert checks["acceptance_status_preserved"] is False
    assert checks["cuda_available_preserved"] is False
    assert checks["release_manifest_ready_preserved"] is False
    assert checks["github_release_plan_ready_preserved"] is False
    assert checks["pipeline_contract_passed_preserved"] is False
    assert checks["pipeline_integration_dq_contract_preserved"] is False
    assert checks["pipeline_pixel_verification_preserved"] is False
    assert checks["release_decision_default_change_ready_preserved"] is False
    assert checks["release_decision_promote_recommendation_preserved"] is False


def test_cli_phase2_status_compare_writes_outputs_and_returns_failure(tmp_path: Path):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    out = tmp_path / "compare.json"
    markdown = tmp_path / "compare.md"
    write_json(baseline, _status_payload(gate=203))
    write_json(candidate, _status_payload(gate=202, cuda_available=False))

    result = main(
        [
            "phase2-status-compare",
            "--baseline-status",
            str(baseline),
            "--candidate-status",
            str(candidate),
            "--out",
            str(out),
            "--markdown",
            str(markdown),
            "--fail-on-regression",
        ]
    )

    assert result == 2
    payload = read_json(out)
    assert payload["artifact_type"] == "glass_phase2_status_compare"
    assert payload["status"] == "regressed"
    text = markdown.read_text(encoding="utf-8")
    assert "GLASS Phase 2 Status Compare" in text
    assert "latest_checkpoint_gate_not_decreased" in text
