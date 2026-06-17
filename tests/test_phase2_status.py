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


def _write_default_route_acceptance(path: Path, *, route_passed: bool = True) -> None:
    write_json(
        path,
        {
            "status": "passed" if route_passed else "failed",
            "passed": route_passed,
            "benchmark_contract": {"name": "default_route_fixture_contract"},
            "speedup_summary": {
                "speedup_vs_wbpp": 28.75,
                "glass": {"weighted_frame_count": 193},
                "comparison": {
                    "rms_diff": 0.001,
                    "abs_diff_p99": 0.002,
                    "coverage_fraction": 0.97,
                },
            },
            "checks": [
                {
                    "name": "contract_required_command_token:--memory-mode resident",
                    "passed": route_passed,
                },
                {
                    "name": "contract_required_command_token:--backend cuda",
                    "passed": route_passed,
                },
                {
                    "name": (
                        "contract_required_command_token:"
                        "--resident-registration similarity_cuda_triangle"
                    ),
                    "passed": route_passed,
                },
                {
                    "name": "contract_required_command_token_group:resident_h2d_or_runtime_preset",
                    "passed": route_passed,
                },
            ],
        },
    )


def _write_pipeline_contract(
    path: Path,
    *,
    passed: bool = True,
    rejection_sample_accounting_passed: bool = True,
) -> None:
    pipeline_passed = passed and rejection_sample_accounting_passed
    write_json(
        path,
        {
            "schema_version": 1,
            "audit_type": "pipeline_invariant_contract",
            "status": "passed" if pipeline_passed else "failed",
            "passed": pipeline_passed,
            "checks": [
                {"name": "integration_output_maps_available", "passed": passed},
                {"name": "integration_dq_contract", "passed": passed},
                {"name": "integration_stack_result_contract", "passed": passed},
                {"name": "integration_resident_result_contract", "passed": passed},
                {"name": "integration_dq_map_pixels_match_summary", "passed": passed},
                {"name": "integration_coverage_map_pixels_match_dq", "passed": passed},
                {"name": "integration_rejection_map_pixels_match_dq", "passed": passed},
                {
                    "name": "integration_rejection_sample_counts_match_maps",
                    "passed": rejection_sample_accounting_passed,
                    "evidence": {
                        "verified_records": 1,
                        "required_records": 1,
                        "failed": []
                        if rejection_sample_accounting_passed
                        else [
                            {
                                "item": "H",
                                "status": "verified",
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
                },
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
                "integration_outputs": [
                    {
                        "item": "H",
                        "status": "verified",
                        "rejection_sample_accounting": {
                            "status": "verified",
                            "verified": True,
                            "ok": rejection_sample_accounting_passed,
                            "required": True,
                            "rejection": "winsorized_sigma",
                            "map_rejected_sample_sum": 6
                            if rejection_sample_accounting_passed
                            else 7,
                            "source_counts": [
                                {
                                    "name": "dq_coverage_provenance.rejected_sample_count",
                                    "count": 6,
                                },
                                {
                                    "name": "dq_provenance_summary.rejected_samples",
                                    "count": 6,
                                },
                            ],
                            "source_matches": [
                                {
                                    "source": "dq_coverage_provenance.rejected_sample_count",
                                    "actual": 6 if rejection_sample_accounting_passed else 7,
                                    "summary": 6,
                                    "delta": 0 if rejection_sample_accounting_passed else 1,
                                    "passed": rejection_sample_accounting_passed,
                                },
                                {
                                    "source": "dq_provenance_summary.rejected_samples",
                                    "actual": 6 if rejection_sample_accounting_passed else 7,
                                    "summary": 6,
                                    "delta": 0 if rejection_sample_accounting_passed else 1,
                                    "passed": rejection_sample_accounting_passed,
                                },
                            ],
                        },
                    }
                ],
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


def _write_publish_preflight(path: Path, *, ready: bool = True) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "artifact_type": "windows_publish_preflight",
            "status": "publish_preflight_ready" if ready else "blocked",
            "passed": ready,
            "recommendation": "publish_release_bundle" if ready else "fix_publish_preflight_blockers",
            "failed_checks": [] if ready else ["manifest_assets_match_github_plan"],
            "summary": {
                "release_tag": "v0.1.0-test",
                "asset_count": 4,
                "package_count": 4,
                "primary_package": "cuda13",
                "ordered_try_list": ["cuda13", "cuda12", "cuda11", "cpu"],
                "source_stamps": ["abcdef0"],
                "default_promotion_status": "default_promotion_ready" if ready else "blocked",
                "default_route_check_count": 4 if ready else 2,
                "default_route_speedup_vs_reference": 28.75,
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
    fastpath_contract_status: str = "passed",
    fastpath_contract_check_count: int = 24,
    default_route_passed: bool = True,
    default_route_contract_passed: bool = True,
    cuda_available: bool = True,
    release_status: str = "release_manifest_ready",
    github_status: str = "release_plan_ready",
    publish_preflight_status: str = "publish_preflight_ready",
    pipeline_passed: bool = True,
    pipeline_dq_contract: bool = True,
    pixel_verification: bool = True,
    pipeline_rejection_sample_check_present: bool = True,
    pipeline_rejection_sample_status: str = "passed",
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
        "acceptance_audit": {
            "status": acceptance_status,
            "passed": acceptance_passed,
            "resident_registration_fastpath_contract_status": fastpath_contract_status,
            "resident_registration_fastpath_contract_check_count": fastpath_contract_check_count,
        },
        "default_route_acceptance": {
            "status": "passed" if default_route_passed else "failed",
            "passed": default_route_passed,
            "route_contract_passed": default_route_contract_passed,
        },
        "doctor": {"cuda_available": cuda_available},
        "release_manifest": {"status": release_status},
        "github_release_plan": {"status": github_status},
        "publish_preflight": {"status": publish_preflight_status},
        "pipeline_contract": {
            "status": "passed" if pipeline_passed else "failed",
            "passed": pipeline_passed,
            "integration_dq_contract": pipeline_dq_contract,
            "pixel_verification_enabled": pixel_verification,
            "integration_rejection_sample_counts_match_maps": (
                pipeline_rejection_sample_status == "passed"
            )
            if pipeline_rejection_sample_check_present
            else None,
            "rejection_sample_accounting": {
                "status": pipeline_rejection_sample_status,
                "check_present": pipeline_rejection_sample_check_present,
                "check_passed": (pipeline_rejection_sample_status == "passed")
                if pipeline_rejection_sample_check_present
                else None,
                "failed_count": 0 if pipeline_rejection_sample_status == "passed" else 1,
            },
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
    default_route_acceptance = tmp_path / "default_route_acceptance.json"
    release = tmp_path / "release_manifest.json"
    github_plan = tmp_path / "github_release_plan.json"
    publish_preflight = tmp_path / "publish_preflight.json"
    pipeline_contract = tmp_path / "pipeline_contract.json"
    release_decision = tmp_path / "release_decision.json"
    _write_acceptance(acceptance)
    _write_default_route_acceptance(default_route_acceptance)
    _write_pipeline_contract(pipeline_contract)
    _write_release_decision(release_decision)
    _write_publish_preflight(publish_preflight)
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
        default_route_acceptance_audit=default_route_acceptance,
        release_manifest=release,
        github_release_plan=github_plan,
        publish_preflight=publish_preflight,
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
    assert payload["default_route_acceptance"]["status"] == "passed"
    assert payload["default_route_acceptance"]["passed"] is True
    assert payload["default_route_acceptance"]["route_contract_passed"] is True
    assert payload["default_route_acceptance"]["route_check_count"] == 4
    assert payload["doctor"]["primary_gpu"] == "Fixture GPU"
    assert payload["release_manifest"]["package_count"] == 4
    assert payload["github_release_plan"]["status"] == "release_plan_ready"
    assert payload["publish_preflight"]["status"] == "publish_preflight_ready"
    assert payload["publish_preflight"]["asset_count"] == 4
    assert payload["publish_preflight"]["primary_package"] == "cuda13"
    assert payload["pipeline_contract"]["status"] == "passed"
    assert payload["pipeline_contract"]["integration_dq_contract"] is True
    assert payload["pipeline_contract"]["integration_stack_result_contract"] is True
    assert payload["pipeline_contract"]["pixel_verification_enabled"] is True
    assert payload["pipeline_contract"]["integration_dq_map_pixels_match_summary"] is True
    assert payload["pipeline_contract"]["integration_rejection_sample_counts_match_maps"] is True
    assert payload["pipeline_contract"]["rejection_sample_accounting_status"] == "passed"
    assert payload["pipeline_contract"]["rejection_sample_accounting_failed_count"] == 0
    assert payload["release_decision"]["status"] == "default_change_ready"
    assert payload["release_decision"]["default_change_ready"] is True
    assert payload["release_decision"]["recommendation"] == "promote_default_candidate"
    assert payload["release_decision"]["runtime_repeat_elapsed_ratio_vs_best"] == 1.053
    checks = {item["name"]: item["passed"] for item in payload["checks"]}
    assert checks["resident_registration_fastpath_contract_passed_for_default"] is True
    assert checks["default_route_acceptance_passed"] is True
    assert checks["default_route_acceptance_route_contract_passed"] is True
    assert checks["pipeline_rejection_sample_accounting_passed"] is True
    assert checks["windows_publish_preflight_ready"] is True


def test_cli_phase2_status_writes_outputs(tmp_path: Path):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=202)
    acceptance = tmp_path / "acceptance.json"
    default_route_acceptance = tmp_path / "default_route_acceptance.json"
    out = tmp_path / "phase2_status.json"
    markdown = tmp_path / "phase2_status.md"
    pipeline_contract = tmp_path / "pipeline_contract.json"
    release_decision = tmp_path / "release_decision.json"
    publish_preflight = tmp_path / "publish_preflight.json"
    _write_acceptance(acceptance)
    _write_default_route_acceptance(default_route_acceptance)
    _write_pipeline_contract(pipeline_contract)
    _write_release_decision(release_decision)
    _write_publish_preflight(publish_preflight)

    result = main(
        [
            "phase2-status",
            "--checkpoint-dir",
            str(checkpoints),
            "--acceptance-audit",
            str(acceptance),
            "--default-route-acceptance-audit",
            str(default_route_acceptance),
            "--pipeline-contract",
            str(pipeline_contract),
            "--release-decision",
            str(release_decision),
            "--publish-preflight",
            str(publish_preflight),
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
    assert payload["default_route_acceptance"]["route_contract_passed"] is True
    assert payload["pipeline_contract"]["integration_dq_contract"] is True
    assert payload["release_decision"]["default_change_ready"] is True
    assert payload["publish_preflight"]["status"] == "publish_preflight_ready"
    text = markdown.read_text(encoding="utf-8")
    assert "GLASS Phase 2 Status" in text
    assert "Acceptance" in text
    assert "Native resident result source: run_default" in text
    assert "Native calibrated lights: 200" in text
    assert "Registration fast path: present" in text
    assert "Registration fast path contract: passed" in text
    assert "Triangle warp batch frames: 188" in text
    assert "Default Route Acceptance" in text
    assert "Route contract passed: True" in text
    assert "Pipeline Contract" in text
    assert "Integration DQ contract: True" in text
    assert "DQ pixels match summary: True" in text
    assert "Rejection sample counts match maps: True" in text
    assert "Rejection sample accounting: passed failed=0" in text
    assert "Release Decision" in text
    assert "Default change ready: True" in text
    assert "Runtime repeat ratio vs best: 1.053" in text
    assert "Windows Publish Preflight" in text
    assert "Preflight status: publish_preflight_ready" in text
    assert "Default route checks: 4" in text


def test_phase2_status_blocks_default_ready_without_fastpath_contract(tmp_path: Path):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=223)
    acceptance = tmp_path / "acceptance.json"
    pipeline_contract = tmp_path / "pipeline_contract.json"
    release_decision = tmp_path / "release_decision.json"
    _write_acceptance(acceptance)
    payload = read_json(acceptance)
    payload["checks"] = [
        item
        for item in payload["checks"]
        if not str(item.get("name") or "").startswith("contract_resident_registration_fastpath")
    ]
    write_json(acceptance, payload)
    _write_pipeline_contract(pipeline_contract)
    _write_release_decision(release_decision)

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        acceptance_audit=acceptance,
        pipeline_contract=pipeline_contract,
        release_decision=release_decision,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    assert status["status"] == "attention_required"
    fastpath_check = checks["resident_registration_fastpath_contract_passed_for_default"]
    assert fastpath_check["passed"] is False
    assert fastpath_check["evidence"]["status"] == "not_requested"
    assert fastpath_check["evidence"]["check_count"] == 0


def test_phase2_status_blocks_failed_default_route_acceptance_when_supplied(tmp_path: Path):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=224)
    acceptance = tmp_path / "acceptance.json"
    default_route_acceptance = tmp_path / "default_route_acceptance.json"
    pipeline_contract = tmp_path / "pipeline_contract.json"
    release_decision = tmp_path / "release_decision.json"
    _write_acceptance(acceptance)
    _write_default_route_acceptance(default_route_acceptance, route_passed=False)
    _write_pipeline_contract(pipeline_contract)
    _write_release_decision(release_decision)

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        acceptance_audit=acceptance,
        default_route_acceptance_audit=default_route_acceptance,
        pipeline_contract=pipeline_contract,
        release_decision=release_decision,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    assert status["status"] == "attention_required"
    assert checks["default_route_acceptance_passed"]["passed"] is False
    assert checks["default_route_acceptance_route_contract_passed"]["passed"] is False
    assert status["default_route_acceptance"]["route_failed_checks"] == [
        "contract_required_command_token:--memory-mode resident",
        "contract_required_command_token:--backend cuda",
        "contract_required_command_token:--resident-registration similarity_cuda_triangle",
        "contract_required_command_token_group:resident_h2d_or_runtime_preset",
    ]


def test_phase2_status_blocks_failed_publish_preflight_when_supplied(tmp_path: Path):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=230)
    acceptance = tmp_path / "acceptance.json"
    pipeline_contract = tmp_path / "pipeline_contract.json"
    release_decision = tmp_path / "release_decision.json"
    publish_preflight = tmp_path / "publish_preflight.json"
    _write_acceptance(acceptance)
    _write_pipeline_contract(pipeline_contract)
    _write_release_decision(release_decision)
    _write_publish_preflight(publish_preflight, ready=False)

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        acceptance_audit=acceptance,
        publish_preflight=publish_preflight,
        pipeline_contract=pipeline_contract,
        release_decision=release_decision,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    assert status["status"] == "attention_required"
    assert status["publish_preflight"]["status"] == "blocked"
    assert checks["windows_publish_preflight_ready"]["passed"] is False
    assert checks["windows_publish_preflight_ready"]["evidence"]["failed_checks"] == [
        "manifest_assets_match_github_plan"
    ]


def test_phase2_status_blocks_pipeline_rejection_sample_drift(tmp_path: Path):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=236)
    acceptance = tmp_path / "acceptance.json"
    pipeline_contract = tmp_path / "pipeline_contract.json"
    release_decision = tmp_path / "release_decision.json"
    _write_acceptance(acceptance)
    _write_pipeline_contract(pipeline_contract, rejection_sample_accounting_passed=False)
    _write_release_decision(release_decision)

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        acceptance_audit=acceptance,
        pipeline_contract=pipeline_contract,
        release_decision=release_decision,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    accounting = status["pipeline_contract"]["rejection_sample_accounting"]
    assert status["status"] == "attention_required"
    assert checks["pipeline_contract_passed"]["passed"] is False
    assert checks["pipeline_rejection_sample_accounting_passed"]["passed"] is False
    assert accounting["status"] == "failed"
    assert accounting["check_present"] is True
    assert accounting["check_passed"] is False
    assert accounting["failed_count"] == 1
    assert accounting["failed_items"][0]["map_rejected_sample_sum"] == 7
    assert accounting["failed_items"][0]["failed_matches"][0] == {
        "source": "dq_coverage_provenance.rejected_sample_count",
        "actual": 7,
        "summary": 6,
        "delta": 1,
    }


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
    assert checks["default_route_acceptance_passed_preserved"] is True
    assert checks["default_route_acceptance_route_contract_preserved"] is True
    assert checks["resident_registration_fastpath_contract_passed_preserved"] is True
    assert checks["resident_registration_fastpath_contract_check_count_preserved"] is True
    assert checks["cuda_available_preserved"] is True
    assert checks["release_manifest_ready_preserved"] is True
    assert checks["github_release_plan_ready_preserved"] is True
    assert checks["windows_publish_preflight_ready_preserved"] is True
    assert checks["pipeline_contract_passed_preserved"] is True
    assert checks["pipeline_integration_dq_contract_preserved"] is True
    assert checks["pipeline_pixel_verification_preserved"] is True
    assert checks["pipeline_rejection_sample_accounting_check_preserved"] is True
    assert checks["pipeline_rejection_sample_accounting_passed_preserved"] is True
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
            publish_preflight_status="blocked",
            pipeline_passed=False,
            pipeline_dq_contract=False,
            pixel_verification=False,
            pipeline_rejection_sample_status="failed",
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
    assert checks["default_route_acceptance_passed_preserved"] is True
    assert checks["default_route_acceptance_route_contract_preserved"] is True
    assert checks["resident_registration_fastpath_contract_passed_preserved"] is True
    assert checks["resident_registration_fastpath_contract_check_count_preserved"] is True
    assert checks["cuda_available_preserved"] is False
    assert checks["release_manifest_ready_preserved"] is False
    assert checks["github_release_plan_ready_preserved"] is False
    assert checks["windows_publish_preflight_ready_preserved"] is False
    assert checks["pipeline_contract_passed_preserved"] is False
    assert checks["pipeline_integration_dq_contract_preserved"] is False
    assert checks["pipeline_pixel_verification_preserved"] is False
    assert checks["pipeline_rejection_sample_accounting_check_preserved"] is True
    assert checks["pipeline_rejection_sample_accounting_passed_preserved"] is False
    assert checks["release_decision_default_change_ready_preserved"] is False
    assert checks["release_decision_promote_recommendation_preserved"] is False


def test_phase2_status_compare_flags_fastpath_contract_evidence_regression(tmp_path: Path):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    write_json(baseline, _status_payload(gate=221))
    write_json(
        candidate,
        _status_payload(
            gate=222,
            fastpath_contract_status="not_requested",
            fastpath_contract_check_count=0,
        ),
    )

    payload = build_phase2_status_compare(
        baseline_status=baseline,
        candidate_status=candidate,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["status"] == "regressed"
    assert checks["resident_registration_fastpath_contract_passed_preserved"]["passed"] is False
    assert checks["resident_registration_fastpath_contract_passed_preserved"]["evidence"] == {
        "baseline": "passed",
        "candidate": "not_requested",
    }
    assert checks["resident_registration_fastpath_contract_check_count_preserved"]["passed"] is False
    assert checks["resident_registration_fastpath_contract_check_count_preserved"]["evidence"] == {
        "baseline": 24,
        "candidate": 0,
    }


def test_phase2_status_compare_flags_default_route_acceptance_regression(tmp_path: Path):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    write_json(baseline, _status_payload(gate=223))
    write_json(
        candidate,
        _status_payload(
            gate=224,
            default_route_passed=False,
            default_route_contract_passed=False,
        ),
    )

    payload = build_phase2_status_compare(
        baseline_status=baseline,
        candidate_status=candidate,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["status"] == "regressed"
    assert checks["default_route_acceptance_passed_preserved"]["passed"] is False
    assert checks["default_route_acceptance_passed_preserved"]["evidence"] == {
        "baseline": True,
        "candidate": False,
    }
    assert checks["default_route_acceptance_route_contract_preserved"]["passed"] is False
    assert checks["default_route_acceptance_route_contract_preserved"]["evidence"] == {
        "baseline": True,
        "candidate": False,
    }


def test_phase2_status_compare_flags_rejection_sample_accounting_regression(tmp_path: Path):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    write_json(baseline, _status_payload(gate=235))
    write_json(
        candidate,
        _status_payload(
            gate=236,
            pipeline_rejection_sample_check_present=False,
            pipeline_rejection_sample_status="not_available",
        ),
    )

    payload = build_phase2_status_compare(
        baseline_status=baseline,
        candidate_status=candidate,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["status"] == "regressed"
    assert checks["pipeline_rejection_sample_accounting_check_preserved"]["passed"] is False
    assert checks["pipeline_rejection_sample_accounting_check_preserved"]["evidence"] == {
        "baseline": True,
        "candidate": False,
    }
    assert checks["pipeline_rejection_sample_accounting_passed_preserved"]["passed"] is False
    assert checks["pipeline_rejection_sample_accounting_passed_preserved"]["evidence"] == {
        "baseline": "passed",
        "candidate": "not_available",
    }


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
