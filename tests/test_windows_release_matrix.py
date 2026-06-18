from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.gpu.compatibility import recommend_windows_cuda_packages
from glass.io.json_io import read_json, write_json
from glass.report.windows_release_matrix import build_windows_release_matrix


def _blackwell_doctor(path: Path) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "product": "GLASS",
            "cuda": {
                "wrapper_importable": True,
                "native_extension_loaded": True,
                "cuda_available": True,
                "probe_skipped": False,
                "devices": [
                    {
                        "device_id": 0,
                        "name": "NVIDIA RTX PRO 6000 Blackwell Workstation Edition",
                        "compute_capability": "12.0",
                        "memory_total_mib": 97886,
                        "driver_version": "596.21",
                    }
                ],
            },
            "windows_cuda_packages": recommend_windows_cuda_packages(
                [
                    {
                        "device_id": 0,
                        "name": "NVIDIA RTX PRO 6000 Blackwell Workstation Edition",
                        "compute_capability": "12.0",
                        "driver_version": "596.21",
                    }
                ]
            ),
        },
    )


def _cpu_only_doctor(path: Path) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "product": "GLASS",
            "cuda": {
                "wrapper_importable": False,
                "native_extension_loaded": False,
                "cuda_available": False,
                "probe_skipped": False,
                "devices": [],
            },
            "windows_cuda_packages": recommend_windows_cuda_packages([]),
        },
    )


def _release_decision(path: Path, *, ready: bool = True) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "artifact_type": "release_promotion_decision",
            "status": "default_change_ready" if ready else "release_candidate_ready",
            "release_candidate_ready": True,
            "default_change_ready": ready,
            "recommendation": "promote_default_candidate" if ready else "repeat_benchmark_before_default_change",
            "runtime_repeat": {
                "present": True,
                "run_count": 3,
                "considered_run_count": 3,
                "elapsed_ratio_vs_best": 1.0140343433372492,
                "recommendation": "best_observed:repeat02",
            },
        },
    )


def _acceptance(path: Path) -> None:
    write_json(path, {"schema_version": 1, "status": "passed", "passed": True})


def _default_promotion(
    path: Path,
    *,
    ready: bool = True,
    rejection_sample_accounting_ready: bool = True,
    sample_accounting_closure_ready: bool = True,
    include_stack_engine_contract: bool = True,
    stack_engine_ready: bool = True,
    stack_engine_gap_count: int = 0,
    include_resident_winsorized_sweep: bool = True,
    resident_winsorized_sweep_ready: bool = True,
    resident_winsorized_sweep_required_frame_ready: bool = True,
    resident_winsorized_sweep_check_count: int = 27,
) -> None:
    manifest_ready = (
        ready
        and rejection_sample_accounting_ready
        and sample_accounting_closure_ready
        and (stack_engine_ready if include_stack_engine_contract else True)
        and (
            resident_winsorized_sweep_ready
            and resident_winsorized_sweep_required_frame_ready
            if include_resident_winsorized_sweep
            else True
        )
    )
    stack_recommendation = (
        "stack_engine_default_ready"
        if stack_engine_ready and stack_engine_gap_count == 0
        else "stack_engine_contract_gaps_remain"
    )
    payload = {
            "schema_version": 1,
            "artifact_type": "default_promotion_manifest",
            "status": "default_promotion_ready" if manifest_ready else "blocked",
            "passed": manifest_ready,
            "default_change_ready": manifest_ready,
            "recommendation": "promote_resident_cuda_default"
            if manifest_ready
            else "fix_default_blockers",
            "default_candidate": {
                "memory_mode": "resident",
                "fallback_memory_mode": "tile",
                "resident_runtime_preset": "throughput-v1",
                "integration_engine": "cuda_resident_stack",
            },
            "default_route_acceptance": {
                "present": True,
                "status": "passed" if ready else "failed",
                "passed": ready,
                "route_contract_passed": ready,
                "route_check_count": 4 if ready else 2,
                "speedup_vs_reference": 28.75,
            },
            "pipeline_contract": {
                "status": "passed" if manifest_ready else "failed",
                "passed": manifest_ready,
                "integration_rejection_sample_counts_match_maps": rejection_sample_accounting_ready,
                "integration_sample_accounting_closure": sample_accounting_closure_ready,
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
                "sample_accounting_closure": {
                    "status": "passed" if sample_accounting_closure_ready else "failed",
                    "check_present": True,
                    "check_passed": sample_accounting_closure_ready,
                    "present_count": 1,
                    "failed_count": 0 if sample_accounting_closure_ready else 1,
                    "failed_items": []
                    if sample_accounting_closure_ready
                    else [
                        {
                            "item": "H",
                            "input_valid_samples_before_rejection": 9,
                            "valid_samples_after_rejection": 6,
                            "rejected_samples": 2,
                        }
                    ],
                },
                "sample_accounting_closure_status": "passed"
                if sample_accounting_closure_ready
                else "failed",
                "sample_accounting_closure_present_count": 1,
                "sample_accounting_closure_failed_count": 0
                if sample_accounting_closure_ready
                else 1,
            },
        }
    if include_stack_engine_contract:
        payload["stack_engine_contract"] = {
            "present": True,
            "ready": stack_engine_ready,
            "phase2_check_passed": stack_engine_ready,
            "status": "passed",
            "passed": True,
            "scope": "all",
            "adoption_recommendation": stack_recommendation,
            "default_promotion_phase2_stack_engine_default_gap_count": (
                stack_engine_gap_count
            ),
            "default_promotion_blocker_count": 0 if stack_engine_ready else 1,
            "default_promotion_blockers": []
            if stack_engine_ready
            else [
                {
                    "name": "phase2_stack_engine_default_gaps",
                    "gap_count": stack_engine_gap_count,
                }
            ],
        }
    if include_resident_winsorized_sweep:
        payload["resident_winsorized_sweep_audit"] = {
            "present": True,
            "path": "runs/checkpoints/s2_gate_269_resident_winsorized_sweep_audit.json",
            "status": "passed" if resident_winsorized_sweep_ready else "failed",
            "passed": resident_winsorized_sweep_ready,
            "phase2_check_passed": resident_winsorized_sweep_ready,
            "contract_name": "s2_gate_269_default_resident_winsorized_sweep",
            "sweep_path": "runs/checkpoints/s2_gate_268_resident_winsorized_sweep.json",
            "check_count": resident_winsorized_sweep_check_count,
            "failed_check_count": 0 if resident_winsorized_sweep_ready else 1,
            "failed_checks": []
            if resident_winsorized_sweep_ready
            else ["frame_200_hardened_master_rms_within_contract"],
            "frame_counts": [8, 32, 128, 200],
            "run_count": 4,
            "required_frame_count": 200,
            "required_frame_count_passed": resident_winsorized_sweep_required_frame_ready,
            "required_frame_master_rms": 2.3e-5,
            "required_frame_master_max_abs": 6.1e-5,
            "required_frame_cuda_hardened_s": 0.0012,
        }
    write_json(path, payload)


def test_windows_release_matrix_passes_blackwell_default(tmp_path: Path):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    acceptance = tmp_path / "acceptance.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision)
    _acceptance(acceptance)
    _default_promotion(default_promotion)

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        acceptance_audit_json=acceptance,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item["passed"] for item in payload["checks"]}
    assert payload["passed"] is True
    assert payload["status"] == "release_matrix_ready"
    assert payload["current_machine"]["primary_package"] == "cuda13"
    assert payload["default_promotion_manifest"]["status"] == "default_promotion_ready"
    assert payload["default_runtime"]["resident_runtime_preset"] == "throughput-v1"
    assert checks["default_promotion_manifest_present"] is True
    assert checks["default_promotion_manifest_ready"] is True
    assert checks["default_promotion_default_route_passed"] is True
    assert checks["default_promotion_rejection_sample_accounting_passed"] is True
    assert checks["default_promotion_sample_accounting_closure_passed"] is True
    assert checks["default_promotion_stack_engine_contract_ready"] is True
    assert checks["default_promotion_resident_winsorized_sweep_audit_passed"] is True
    assert checks["default_promotion_resident_winsorized_required_frame_passed"] is True
    assert checks["default_promotion_resident_winsorized_sweep_check_count"] is True
    assert payload["default_promotion_manifest"][
        "resident_winsorized_sweep_required_frame_count"
    ] == 200
    assert checks["required_cuda_package_compatible:cuda13"] is True
    assert checks["required_cuda_package_compatible:cuda12"] is True
    assert checks["required_cuda_package_compatible:cuda11"] is True
    assert [row["label"] for row in payload["packages"]] == ["cuda11", "cuda12", "cuda13", "cpu"]


def test_windows_release_matrix_blocks_cpu_only_cuda_release(tmp_path: Path):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    _cpu_only_doctor(doctor)
    _release_decision(decision)

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
    )

    checks = {item["name"]: item["passed"] for item in payload["checks"]}
    assert payload["passed"] is False
    assert checks["cuda_available_for_release_machine"] is False
    assert checks["required_cuda_package_compatible:cuda13"] is False
    assert payload["recommendation"] == "fix_release_matrix_blockers"


def test_windows_release_matrix_blocks_missing_default_promotion_manifest(tmp_path: Path):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    _blackwell_doctor(doctor)
    _release_decision(decision)

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item["passed"] for item in payload["checks"]}
    assert payload["passed"] is False
    assert checks["default_promotion_manifest_present"] is False
    assert checks["default_promotion_manifest_ready"] is False
    assert checks["default_promotion_default_route_passed"] is False


def test_windows_release_matrix_blocks_failed_default_promotion_manifest(tmp_path: Path):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision)
    _default_promotion(default_promotion, ready=False)

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item["passed"] for item in payload["checks"]}
    assert payload["passed"] is False
    assert checks["default_promotion_manifest_present"] is True
    assert checks["default_promotion_manifest_ready"] is False
    assert checks["default_promotion_default_route_passed"] is False
    assert checks["default_promotion_rejection_sample_accounting_passed"] is True
    assert checks["default_promotion_sample_accounting_closure_passed"] is True
    assert checks["default_promotion_stack_engine_contract_ready"] is True


def test_windows_release_matrix_blocks_rejection_sample_accounting_drift(tmp_path: Path):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision)
    _default_promotion(default_promotion, rejection_sample_accounting_ready=False)

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert checks["default_promotion_manifest_present"]["passed"] is True
    assert checks["default_promotion_manifest_ready"]["passed"] is False
    assert checks["default_promotion_rejection_sample_accounting_passed"]["passed"] is False
    assert checks["default_promotion_rejection_sample_accounting_passed"]["evidence"] == {
        "pipeline_contract_status": "failed",
        "pipeline_contract_passed": False,
        "check": False,
        "status": "failed",
        "failed_count": 1,
        "failed_items": [
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
    }


def test_windows_release_matrix_blocks_sample_accounting_closure_drift(tmp_path: Path):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision)
    _default_promotion(default_promotion, sample_accounting_closure_ready=False)

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert checks["default_promotion_manifest_present"]["passed"] is True
    assert checks["default_promotion_manifest_ready"]["passed"] is False
    assert checks["default_promotion_sample_accounting_closure_passed"]["passed"] is False
    assert checks["default_promotion_sample_accounting_closure_passed"]["evidence"] == {
        "pipeline_contract_status": "failed",
        "pipeline_contract_passed": False,
        "check": False,
        "status": "failed",
        "present_count": 1,
        "failed_count": 1,
        "failed_items": [
            {
                "item": "H",
                "input_valid_samples_before_rejection": 9,
                "valid_samples_after_rejection": 6,
                "rejected_samples": 2,
            }
        ],
    }


def test_windows_release_matrix_blocks_missing_stack_engine_contract(tmp_path: Path):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision)
    _default_promotion(default_promotion, include_stack_engine_contract=False)

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert checks["default_promotion_manifest_ready"]["passed"] is True
    assert checks["default_promotion_stack_engine_contract_ready"]["passed"] is False
    assert checks["default_promotion_stack_engine_contract_ready"]["evidence"] == {
        "present": None,
        "ready": None,
        "phase2_check_passed": None,
        "status": None,
        "passed": None,
        "scope": None,
        "adoption_recommendation": None,
        "default_gap_count": None,
        "blocker_count": None,
        "blockers": [],
    }


def test_windows_release_matrix_blocks_stack_engine_contract_gap(tmp_path: Path):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision)
    _default_promotion(
        default_promotion,
        stack_engine_ready=False,
        stack_engine_gap_count=1,
    )

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert checks["default_promotion_manifest_ready"]["passed"] is False
    assert checks["default_promotion_stack_engine_contract_ready"]["passed"] is False
    assert checks["default_promotion_stack_engine_contract_ready"]["evidence"][
        "default_gap_count"
    ] == 1
    assert checks["default_promotion_stack_engine_contract_ready"]["evidence"][
        "blocker_count"
    ] == 1


def test_windows_release_matrix_blocks_missing_resident_winsorized_sweep(tmp_path: Path):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision)
    _default_promotion(default_promotion, include_resident_winsorized_sweep=False)

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert checks["default_promotion_manifest_ready"]["passed"] is True
    assert checks["default_promotion_resident_winsorized_sweep_audit_passed"][
        "passed"
    ] is False
    assert checks["default_promotion_resident_winsorized_required_frame_passed"][
        "passed"
    ] is False
    assert checks["default_promotion_resident_winsorized_sweep_check_count"][
        "passed"
    ] is False
    assert checks["default_promotion_resident_winsorized_sweep_audit_passed"][
        "evidence"
    ] == {
        "present": None,
        "status": None,
        "passed": None,
        "phase2_check_passed": None,
        "failed_checks": [],
    }


def test_windows_release_matrix_blocks_failed_resident_winsorized_sweep(tmp_path: Path):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision)
    _default_promotion(
        default_promotion,
        resident_winsorized_sweep_ready=False,
        resident_winsorized_sweep_required_frame_ready=False,
        resident_winsorized_sweep_check_count=26,
    )

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert checks["default_promotion_manifest_ready"]["passed"] is False
    assert checks["default_promotion_resident_winsorized_sweep_audit_passed"][
        "passed"
    ] is False
    assert checks["default_promotion_resident_winsorized_required_frame_passed"][
        "passed"
    ] is False
    assert checks["default_promotion_resident_winsorized_sweep_check_count"][
        "passed"
    ] is False
    assert checks["default_promotion_resident_winsorized_required_frame_passed"][
        "evidence"
    ] == {
        "actual_frame_count": 200,
        "required_frame_count": 200,
        "required_frame_count_passed": False,
        "required_frame_master_rms": 2.3e-05,
        "required_frame_master_max_abs": 6.1e-05,
    }


def test_windows_release_matrix_cli_writes_json_and_markdown(tmp_path: Path):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    default_promotion = tmp_path / "default_promotion.json"
    out = tmp_path / "matrix.json"
    markdown = tmp_path / "matrix.md"
    _blackwell_doctor(doctor)
    _release_decision(decision)
    _default_promotion(default_promotion)

    result = main(
        [
            "windows-release-matrix",
            "--doctor-json",
            str(doctor),
            "--release-decision",
            str(decision),
            "--default-promotion-manifest",
            str(default_promotion),
            "--expected-primary-package",
            "cuda13",
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
    assert "GLASS Windows Release Matrix" in markdown_text
    assert "Default Promotion Manifest" in markdown_text
    assert "Default route contract/checks: `True`/`4`" in markdown_text
    assert "Rejection sample accounting: `passed` failed=`0`" in markdown_text
    assert "Sample accounting closure: `passed` present=`1` failed=`0`" in markdown_text
    assert (
        "StackEngine default contract: ready=`True` phase2-check=`True` gaps=`0` blockers=`0`"
        in markdown_text
    )
    assert (
        "Resident winsorized sweep: passed=`True` phase2-check=`True` "
        "required-frame=`200` required-pass=`True` checks=`27`"
    ) in markdown_text
