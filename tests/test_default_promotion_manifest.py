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
    sample_accounting_closure_ready: bool = True,
    include_stack_engine_contract: bool = True,
    stack_engine_ready: bool = True,
    stack_engine_gap_count: int = 0,
    include_resident_winsorized_sweep: bool = True,
    resident_winsorized_sweep_ready: bool = True,
    resident_winsorized_sweep_required_frame_ready: bool = True,
    resident_winsorized_sweep_check_count: int = 27,
    resident_winsorized_sweep_required_frame_count: int = 200,
    include_stack_publication_audit: bool = True,
    stack_publication_audit_ready: bool = True,
    stack_publication_policy_ready: bool = True,
    stack_publication_resident_winsorized_ready: bool = True,
    include_integration_engine_policy: bool = True,
    acceptance_integration_engine_policy_ready: bool = True,
    pipeline_integration_engine_policy_ready: bool = True,
    pipeline_integration_engine_policy_check_present: bool = True,
) -> None:
    acceptance_policy_chain_ready = (
        acceptance_integration_engine_policy_ready
        if include_integration_engine_policy
        else True
    )
    pipeline_policy_chain_ready = (
        pipeline_integration_engine_policy_ready
        and pipeline_integration_engine_policy_check_present
        if include_integration_engine_policy
        else True
    )
    pipeline_ready = (
        ready
        and rejection_sample_accounting_ready
        and sample_accounting_closure_ready
        and pipeline_policy_chain_ready
    )
    phase2_ready = (
        pipeline_ready
        and acceptance_policy_chain_ready
        and (stack_engine_ready if include_stack_engine_contract else True)
        and (
            stack_publication_audit_ready
            and stack_publication_policy_ready
            and stack_publication_resident_winsorized_ready
            if include_stack_publication_audit
            else True
        )
        and (
            resident_winsorized_sweep_ready
            and resident_winsorized_sweep_required_frame_ready
            if include_resident_winsorized_sweep
            else True
        )
    )
    failed_pipeline_checks = []
    if not rejection_sample_accounting_ready:
        failed_pipeline_checks.append("integration_rejection_sample_counts_match_maps")
    if not sample_accounting_closure_ready:
        failed_pipeline_checks.append("integration_sample_accounting_closure")
    if include_integration_engine_policy and not pipeline_policy_chain_ready:
        failed_pipeline_checks.append("integration_default_engine_policy")
    stack_engine_recommendation = (
        "stack_engine_default_ready"
        if stack_engine_ready and stack_engine_gap_count == 0
        else "stack_engine_contract_gaps_remain"
    )
    payload = {
        "schema_version": 1,
        "artifact_type": "glass_phase2_status",
        "status": "green" if phase2_ready else "attention_required",
        "passed": phase2_ready,
        "latest_checkpoint": {
            "gate": 252,
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
                "status": "passed" if pipeline_ready else "failed",
            "passed": pipeline_ready,
            "check_count": 15,
            "failed_check_count": len(failed_pipeline_checks),
            "failed_checks": failed_pipeline_checks,
            "integration_output_count": 1,
            "integration_map_count": 6,
            "integration_dq_contract": True,
            "integration_stack_result_contract": True,
            "integration_resident_result_contract": True,
            "integration_dq_map_pixels_match_summary": True,
            "integration_coverage_map_pixels_match_dq": True,
            "integration_rejection_map_pixels_match_dq": True,
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
            "pixel_verification_enabled": True,
            "pixel_verification_tile_size": 2048,
            "resident_native_calibration_artifact": True,
            "resident_calibrated_light_count": 200,
        },
        "checks": [
            {
                "name": "stack_engine_default_contract_ready",
                "passed": stack_engine_ready if include_stack_engine_contract else False,
            },
        ],
    }
    if include_integration_engine_policy:
        acceptance_policy_status = (
            "passed" if acceptance_integration_engine_policy_ready else "failed"
        )
        pipeline_policy_status = (
            "passed"
            if pipeline_integration_engine_policy_ready
            else "failed"
        )
        acceptance_failed_items = (
            []
            if acceptance_integration_engine_policy_ready
            else [
                {
                    "item": "H",
                    "status": "implicit_cuda_fast_path",
                    "backend": "cuda",
                    "tile_stack_mode": "cuda_streaming_accumulator_fast_path",
                    "failures": ["cuda_fast_path_not_explicit"],
                }
            ]
        )
        pipeline_failed_items = (
            []
            if pipeline_integration_engine_policy_ready
            else [
                {
                    "item": "H",
                    "status": "implicit_cuda_fast_path",
                    "backend": "cuda",
                    "tile_stack_mode": "cuda_streaming_accumulator_fast_path",
                    "failures": ["cuda_fast_path_not_explicit"],
                }
            ]
        )
        payload["acceptance_audit"] = {
            "status": "passed" if acceptance_policy_chain_ready else "failed",
            "passed": acceptance_policy_chain_ready,
            "pipeline_integration_engine_policy_status": acceptance_policy_status,
            "pipeline_integration_engine_policy_check_present": True,
            "pipeline_integration_engine_policy_check_passed": (
                acceptance_integration_engine_policy_ready
            ),
            "pipeline_integration_engine_policy_non_resident_count": 0
            if acceptance_integration_engine_policy_ready
            else 1,
            "pipeline_integration_engine_policy_failed_count": 0
            if acceptance_integration_engine_policy_ready
            else 1,
            "pipeline_integration_engine_policy": {
                "status": acceptance_policy_status,
                "check_name": "integration_default_engine_policy",
                "check_present": True,
                "check_passed": acceptance_integration_engine_policy_ready,
                "non_resident_count": 0
                if acceptance_integration_engine_policy_ready
                else 1,
                "resident_count": 1 if acceptance_integration_engine_policy_ready else 0,
                "failed_count": 0
                if acceptance_integration_engine_policy_ready
                else 1,
                "failed_items": acceptance_failed_items,
            },
        }
        payload["pipeline_contract"].update(
            {
                "integration_default_engine_policy": (
                    pipeline_integration_engine_policy_ready
                    if pipeline_integration_engine_policy_check_present
                    else None
                ),
                "integration_engine_policy_status": pipeline_policy_status,
                "integration_engine_policy_check_present": (
                    pipeline_integration_engine_policy_check_present
                ),
                "integration_engine_policy_check_passed": (
                    pipeline_integration_engine_policy_ready
                    if pipeline_integration_engine_policy_check_present
                    else None
                ),
                "integration_engine_policy_non_resident_count": 0
                if pipeline_integration_engine_policy_ready
                else 1,
                "integration_engine_policy_failed_count": 0
                if pipeline_integration_engine_policy_ready
                else 1,
                "integration_engine_policy": {
                    "status": pipeline_policy_status,
                    "check_present": pipeline_integration_engine_policy_check_present,
                    "check_passed": pipeline_integration_engine_policy_ready
                    if pipeline_integration_engine_policy_check_present
                    else None,
                    "non_resident_count": 0
                    if pipeline_integration_engine_policy_ready
                    else 1,
                    "resident_count": 1 if pipeline_integration_engine_policy_ready else 0,
                    "failed_count": 0
                    if pipeline_integration_engine_policy_ready
                    else 1,
                    "failed_items": pipeline_failed_items,
                },
            }
        )
        payload["checks"].extend(
            [
                {
                    "name": "acceptance_pipeline_integration_engine_policy_passed",
                    "passed": acceptance_policy_chain_ready,
                },
                {
                    "name": "pipeline_integration_engine_policy_passed",
                    "passed": pipeline_policy_chain_ready,
                },
            ]
        )
    if include_resident_winsorized_sweep:
        payload["resident_winsorized_sweep_audit"] = {
            "schema_version": 1,
            "path": "C:/glass_runs/run/resident_winsorized_sweep_audit.json",
            "status": "passed" if resident_winsorized_sweep_ready else "failed",
            "passed": resident_winsorized_sweep_ready,
            "contract_name": "s2_gate_269_default_resident_winsorized_sweep",
            "contract_path": "benchmarks/resident_winsorized_sweep_contract.json",
            "sweep_path": "runs/checkpoints/s2_gate_268_resident_winsorized_sweep.json",
            "check_count": resident_winsorized_sweep_check_count,
            "failed_check_count": 0 if resident_winsorized_sweep_ready else 1,
            "failed_checks": []
            if resident_winsorized_sweep_ready
            else ["frame_200_hardened_master_rms_within_contract"],
            "frame_counts": [8, 32, 128, 200],
            "run_count": 4,
            "required_frame_count": resident_winsorized_sweep_required_frame_count,
            "required_frame_count_passed": resident_winsorized_sweep_required_frame_ready,
            "required_frame_master_rms": 2.3e-5,
            "required_frame_master_max_abs": 6.1e-5,
            "max_hardened_master_rms": 2.3e-5,
            "required_frame_cuda_hardened_s": 0.0012,
        }
        payload["checks"].append(
            {
                "name": "resident_winsorized_sweep_audit_passed",
                "passed": resident_winsorized_sweep_ready,
            }
        )
    if include_stack_engine_contract:
        payload["stack_engine_contract"] = {
            "path": "C:/glass_runs/run/stack_engine_contract.json",
            "audit_type": "stack_engine_default_contract",
            "status": "passed",
            "passed": True,
            "scope": "all",
            "expected_integration_engine": "stack_engine_cpu",
            "adoption_recommendation": stack_engine_recommendation,
            "adoption_surface_count": 4,
            "adoption_contract_ready_count": 4 - stack_engine_gap_count,
            "adoption_stack_engine_surface_count": 4 - stack_engine_gap_count,
            "adoption_cuda_resident_surface_count": 0,
            "adoption_phase2_stack_engine_default_gap_count": stack_engine_gap_count,
            "adoption_gap_surfaces": [
                {
                    "surface": "integration",
                    "item": "H",
                    "engine_family": "legacy",
                    "gap_reason": "legacy_or_unknown_engine",
                }
            ]
            if stack_engine_gap_count
            else [],
            "default_promotion_ready": stack_engine_ready,
            "default_promotion_status": "ready" if stack_engine_ready else "blocked",
            "default_promotion_recommendation": stack_engine_recommendation,
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
    if include_stack_publication_audit:
        publication_failed_checks = []
        if not stack_publication_audit_ready:
            publication_failed_checks.append("stack_engine_publication_audit_passed")
        if not stack_publication_policy_ready:
            publication_failed_checks.append(
                "stack_engine_publication_audit_policy_chain_passed"
            )
        if not stack_publication_resident_winsorized_ready:
            publication_failed_checks.append(
                "stack_engine_publication_audit_resident_winsorized_chain_passed"
            )
        payload["stack_engine_publication_audit"] = {
            "path": "C:/glass_runs/run/stack_engine_publication_audit.json",
            "status": "passed" if stack_publication_audit_ready else "blocked",
            "passed": stack_publication_audit_ready,
            "recommendation": "publication_chain_ready"
            if stack_publication_audit_ready
            else "fix_stack_engine_publication_chain",
            "check_count": 21,
            "failed_check_count": len(publication_failed_checks),
            "failed_checks": publication_failed_checks,
            "publish_preflight_integration_engine_policy": {
                "status": "publish_preflight_ready"
                if stack_publication_policy_ready
                else "blocked",
                "ready": stack_publication_policy_ready,
            },
            "phase2_publish_preflight_integration_engine_policy": {
                "status": "publish_preflight_ready"
                if stack_publication_policy_ready
                else "blocked",
                "ready": stack_publication_policy_ready,
            },
            "publish_preflight_integration_engine_policy_ready": (
                stack_publication_policy_ready
            ),
            "phase2_publish_preflight_integration_engine_policy_ready": (
                stack_publication_policy_ready
            ),
            "phase2_publish_preflight_integration_engine_policy_matches_publish_preflight": (
                stack_publication_policy_ready
            ),
            "publish_preflight_resident_winsorized_sweep": {
                "status": "publish_preflight_ready"
                if stack_publication_resident_winsorized_ready
                else "blocked",
                "ready": stack_publication_resident_winsorized_ready,
            },
            "phase2_publish_preflight_resident_winsorized_sweep": {
                "status": "publish_preflight_ready"
                if stack_publication_resident_winsorized_ready
                else "blocked",
                "ready": stack_publication_resident_winsorized_ready,
            },
            "publish_preflight_resident_winsorized_sweep_ready": (
                stack_publication_resident_winsorized_ready
            ),
            "phase2_publish_preflight_resident_winsorized_sweep_ready": (
                stack_publication_resident_winsorized_ready
            ),
            "phase2_publish_preflight_resident_winsorized_matches_publish_preflight": (
                stack_publication_resident_winsorized_ready
            ),
        }
        payload["checks"].extend(
            [
                {
                    "name": "stack_engine_publication_audit_passed",
                    "passed": stack_publication_audit_ready,
                },
                {
                    "name": "stack_engine_publication_audit_policy_chain_passed",
                    "passed": stack_publication_policy_ready,
                },
                {
                    "name": "stack_engine_publication_audit_resident_winsorized_chain_passed",
                    "passed": stack_publication_resident_winsorized_ready,
                },
            ]
        )
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
    assert payload["stack_engine_contract"]["ready"] is True
    assert payload["stack_engine_contract"]["adoption_recommendation"] == "stack_engine_default_ready"
    assert checks["runtime_repeat_ratio_within_bound"] is True
    assert checks["default_route_acceptance_present"] is True
    assert checks["default_route_acceptance_passed"] is True
    assert checks["default_route_acceptance_route_contract_passed"] is True
    assert checks["default_route_acceptance_route_check_count"] is True
    assert checks["pipeline_pixel_maps_match_dq"] is True
    assert checks["pipeline_rejection_sample_accounting_passed"] is True
    assert checks["pipeline_sample_accounting_closure_passed"] is True
    assert checks["acceptance_integration_engine_policy_handoff_passed"] is True
    assert checks["pipeline_integration_engine_policy_default_passed"] is True
    assert payload["integration_engine_policy"]["ready"] is True
    assert payload["integration_engine_policy"]["pipeline_non_resident_count"] == 0
    assert checks["phase2_stack_engine_default_contract_ready"] is True
    assert checks["resident_winsorized_sweep_audit_passed"] is True
    assert checks["resident_winsorized_sweep_required_frame_passed"] is True
    assert checks["resident_winsorized_sweep_check_count"] is True
    assert checks["stack_engine_publication_audit_passed"] is True
    assert checks["stack_engine_publication_policy_chain_passed"] is True
    assert checks["stack_engine_publication_resident_winsorized_chain_passed"] is True
    assert payload["stack_engine_publication_audit"]["ready"] is True
    assert (
        payload["stack_engine_publication_audit"]["publish_preflight_policy_ready"]
        is True
    )
    assert payload["resident_winsorized_sweep_audit"]["required_frame_count"] == 200
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


def test_default_promotion_manifest_blocks_sample_accounting_closure_drift(
    tmp_path: Path,
) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    _write_release_decision(decision)
    _write_phase2_status(phase2, decision, sample_accounting_closure_ready=False)

    payload = build_default_promotion_manifest(
        release_decision_json=decision,
        phase2_status_json=phase2,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert "phase2_status_green" in payload["failed_checks"]
    assert "pipeline_contract_passed" in payload["failed_checks"]
    assert "pipeline_sample_accounting_closure_passed" in payload["failed_checks"]
    assert checks["pipeline_sample_accounting_closure_passed"]["evidence"] == {
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


def test_default_promotion_manifest_blocks_missing_integration_engine_policy(
    tmp_path: Path,
) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    _write_release_decision(decision)
    _write_phase2_status(
        phase2,
        decision,
        include_integration_engine_policy=False,
    )

    payload = build_default_promotion_manifest(
        release_decision_json=decision,
        phase2_status_json=phase2,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert "phase2_status_green" not in payload["failed_checks"]
    assert (
        "acceptance_integration_engine_policy_handoff_passed"
        in payload["failed_checks"]
    )
    assert (
        "pipeline_integration_engine_policy_default_passed"
        in payload["failed_checks"]
    )
    assert payload["integration_engine_policy"]["present"] is False
    assert checks["acceptance_integration_engine_policy_handoff_passed"][
        "evidence"
    ] == {
        "status": None,
        "check_present": None,
        "check_passed": None,
        "phase2_check_passed": None,
        "non_resident_count": None,
        "failed_count": None,
        "failed_items": [],
    }
    assert checks["pipeline_integration_engine_policy_default_passed"][
        "evidence"
    ]["check_present"] is None


def test_default_promotion_manifest_blocks_failed_integration_engine_policy(
    tmp_path: Path,
) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    _write_release_decision(decision)
    _write_phase2_status(
        phase2,
        decision,
        acceptance_integration_engine_policy_ready=False,
        pipeline_integration_engine_policy_ready=False,
    )

    payload = build_default_promotion_manifest(
        release_decision_json=decision,
        phase2_status_json=phase2,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert "phase2_status_green" in payload["failed_checks"]
    assert "pipeline_contract_passed" in payload["failed_checks"]
    assert (
        "acceptance_integration_engine_policy_handoff_passed"
        in payload["failed_checks"]
    )
    assert (
        "pipeline_integration_engine_policy_default_passed"
        in payload["failed_checks"]
    )
    assert payload["integration_engine_policy"]["ready"] is False
    assert checks["acceptance_integration_engine_policy_handoff_passed"][
        "evidence"
    ]["non_resident_count"] == 1
    assert checks["pipeline_integration_engine_policy_default_passed"][
        "evidence"
    ]["failed_items"][0]["failures"] == ["cuda_fast_path_not_explicit"]


def test_default_promotion_manifest_blocks_missing_stack_engine_contract(
    tmp_path: Path,
) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    _write_release_decision(decision)
    _write_phase2_status(phase2, decision, include_stack_engine_contract=False)

    payload = build_default_promotion_manifest(
        release_decision_json=decision,
        phase2_status_json=phase2,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert payload["stack_engine_contract"]["present"] is False
    assert "phase2_status_green" not in payload["failed_checks"]
    assert "phase2_stack_engine_default_contract_ready" in payload["failed_checks"]
    assert checks["phase2_stack_engine_default_contract_ready"]["evidence"] == {
        "present": False,
        "phase2_check_passed": False,
        "status": None,
        "passed": None,
        "scope": None,
        "expected_integration_engine": None,
        "adoption_recommendation": None,
        "adoption_gap_count": None,
        "default_promotion_ready": None,
        "default_promotion_status": None,
        "default_promotion_blocker_count": None,
        "default_promotion_blockers": [],
    }


def test_default_promotion_manifest_blocks_stack_engine_default_gap(
    tmp_path: Path,
) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    _write_release_decision(decision)
    _write_phase2_status(
        phase2,
        decision,
        stack_engine_ready=False,
        stack_engine_gap_count=1,
    )

    payload = build_default_promotion_manifest(
        release_decision_json=decision,
        phase2_status_json=phase2,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert payload["stack_engine_contract"]["present"] is True
    assert payload["stack_engine_contract"]["ready"] is False
    assert "phase2_status_green" in payload["failed_checks"]
    assert "phase2_stack_engine_default_contract_ready" in payload["failed_checks"]
    assert checks["phase2_stack_engine_default_contract_ready"]["evidence"][
        "adoption_gap_count"
    ] == 1
    assert checks["phase2_stack_engine_default_contract_ready"]["evidence"][
        "default_promotion_status"
    ] == "blocked"


def test_default_promotion_manifest_blocks_missing_resident_winsorized_sweep(
    tmp_path: Path,
) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    _write_release_decision(decision)
    _write_phase2_status(phase2, decision, include_resident_winsorized_sweep=False)

    payload = build_default_promotion_manifest(
        release_decision_json=decision,
        phase2_status_json=phase2,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert "phase2_status_green" not in payload["failed_checks"]
    assert "resident_winsorized_sweep_audit_passed" in payload["failed_checks"]
    assert "resident_winsorized_sweep_required_frame_passed" in payload["failed_checks"]
    assert "resident_winsorized_sweep_check_count" in payload["failed_checks"]
    assert payload["resident_winsorized_sweep_audit"]["present"] is False
    assert checks["resident_winsorized_sweep_audit_passed"]["evidence"] == {
        "present": False,
        "status": None,
        "passed": None,
        "phase2_check_passed": None,
        "failed_checks": [],
    }


def test_default_promotion_manifest_blocks_failed_resident_winsorized_sweep(
    tmp_path: Path,
) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    _write_release_decision(decision)
    _write_phase2_status(
        phase2,
        decision,
        resident_winsorized_sweep_ready=False,
        resident_winsorized_sweep_required_frame_ready=False,
        resident_winsorized_sweep_check_count=26,
    )

    payload = build_default_promotion_manifest(
        release_decision_json=decision,
        phase2_status_json=phase2,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert "phase2_status_green" in payload["failed_checks"]
    assert "resident_winsorized_sweep_audit_passed" in payload["failed_checks"]
    assert "resident_winsorized_sweep_required_frame_passed" in payload["failed_checks"]
    assert "resident_winsorized_sweep_check_count" in payload["failed_checks"]
    assert checks["resident_winsorized_sweep_required_frame_passed"]["evidence"] == {
        "actual_frame_count": 200,
        "required_frame_count": 200,
        "required_frame_count_passed": False,
        "required_frame_master_rms": 2.3e-05,
        "required_frame_master_max_abs": 6.1e-05,
    }


def test_default_promotion_manifest_blocks_missing_publication_audit(
    tmp_path: Path,
) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    _write_release_decision(decision)
    _write_phase2_status(
        phase2,
        decision,
        include_stack_publication_audit=False,
    )

    payload = build_default_promotion_manifest(
        release_decision_json=decision,
        phase2_status_json=phase2,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert "phase2_status_green" not in payload["failed_checks"]
    assert "stack_engine_publication_audit_passed" in payload["failed_checks"]
    assert "stack_engine_publication_policy_chain_passed" in payload["failed_checks"]
    assert (
        "stack_engine_publication_resident_winsorized_chain_passed"
        in payload["failed_checks"]
    )
    assert payload["stack_engine_publication_audit"]["present"] is False
    assert checks["stack_engine_publication_audit_passed"]["evidence"] == {
        "present": False,
        "status": None,
        "passed": None,
        "phase2_check_passed": None,
        "failed_checks": [],
    }


def test_default_promotion_manifest_blocks_failed_publication_policy_chain(
    tmp_path: Path,
) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    _write_release_decision(decision)
    _write_phase2_status(
        phase2,
        decision,
        stack_publication_audit_ready=False,
        stack_publication_policy_ready=False,
    )

    payload = build_default_promotion_manifest(
        release_decision_json=decision,
        phase2_status_json=phase2,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert "phase2_status_green" in payload["failed_checks"]
    assert "stack_engine_publication_audit_passed" in payload["failed_checks"]
    assert "stack_engine_publication_policy_chain_passed" in payload["failed_checks"]
    assert (
        "stack_engine_publication_resident_winsorized_chain_passed"
        not in payload["failed_checks"]
    )
    assert payload["stack_engine_publication_audit"]["ready"] is False
    assert checks["stack_engine_publication_policy_chain_passed"]["evidence"][
        "publish_preflight_policy_ready"
    ] is False
    assert checks["stack_engine_publication_policy_chain_passed"]["evidence"][
        "policy_agreement"
    ] is False


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
    assert "Sample accounting closure: `passed`" in markdown_text
    assert "Acceptance integration engine policy: `passed`" in markdown_text
    assert "Pipeline integration engine policy: `passed`" in markdown_text
    assert "Integration engine policy ready: `True`" in markdown_text
    assert "StackEngine Default Contract" in markdown_text
    assert "Adoption recommendation: `stack_engine_default_ready`" in markdown_text
    assert "Default promotion: `ready` ready=`True` blockers=`0`" in markdown_text
    assert "Resident Winsorized Sweep" in markdown_text
    assert "Required frame count: `200`" in markdown_text
    assert "StackEngine Publication Audit" in markdown_text
    assert "Policy chain: raw=`True` phase2=`True` agreement=`True`" in markdown_text
    assert "Resident winsorized chain: raw=`True` phase2=`True` agreement=`True`" in markdown_text
    assert "Route contract passed: `True`" in markdown_text
