from __future__ import annotations

from pathlib import Path
import sys

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.windows_github_release_plan import build_windows_github_release_plan


def _manifest(path: Path, *, zip_paths: dict[str, Path], source: str = "abc1234") -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "artifact_type": "windows_release_manifest",
            "status": "release_manifest_ready",
            "passed": True,
            "failed_checks": [],
            "packages": [
                {
                    "label": label,
                    "zip_path": str(zip_path),
                    "exists": True,
                    "size_bytes": zip_path.stat().st_size,
                    "sha256": f"{index:064x}",
                    "source_stamp": source,
                }
                for index, (label, zip_path) in enumerate(zip_paths.items(), start=1)
            ],
        },
    )


def _phase2_status(
    path: Path,
    *,
    passed: bool = True,
    gate: int = 204,
    sample_accounting_closure_ready: bool | None = None,
    stack_engine_ready: bool | None = None,
    stack_engine_gap_count: int = 0,
) -> None:
    accounting_passed = passed
    sample_closure_passed = (
        passed
        if sample_accounting_closure_ready is None
        else sample_accounting_closure_ready
    )
    stack_ready = passed if stack_engine_ready is None else stack_engine_ready
    stack_check_passed = stack_ready and stack_engine_gap_count == 0
    stack_recommendation = (
        "stack_engine_default_ready"
        if stack_check_passed
        else "stack_engine_contract_gaps_remain"
    )
    write_json(
        path,
        {
            "schema_version": 1,
            "artifact_type": "glass_phase2_status",
            "status": "green" if passed else "attention_required",
            "passed": passed,
            "latest_checkpoint": {"gate": gate, "status": "green" if passed else "failed", "green": passed},
            "checks": [
                {
                    "name": "stack_engine_default_contract_ready",
                    "passed": stack_check_passed,
                }
            ],
            "acceptance_audit": {
                "status": "passed" if passed else "failed",
                "native_guardrails_bundle_status": "present",
                "resident_result_contract_source": "run_default",
                "resident_result_contract_run_default": True,
                "resident_result_contract_json": "C:/glass_runs/run/resident_result_contract.json",
                "resident_native_calibration_artifact": True,
                "resident_calibration_master_count": 3,
                "resident_calibrated_light_count": 200,
                "resident_registration_fastpath_status": "present",
                "resident_registration_fastpath_contract_status": "passed",
                "resident_registration_fastpath_mode": "similarity_cuda_triangle",
                "triangle_descriptor_fit_batch": True,
                "triangle_descriptor_fit_batch_mode": "native_batch_shared_reference_device",
                "triangle_descriptor_fit_device_reuse": {
                    "reference": True,
                    "moving": True,
                    "output": True,
                },
                "triangle_pixel_refine_batch": True,
                "triangle_pixel_refine_batch_metric_mode": "flattened_frame_candidate_grid",
                "triangle_warp_batch": True,
                "triangle_warp_batch_mode": "native_matrix_lanczos3_frames",
                "triangle_warp_batch_frame_count": 188,
                "resident_warp_copy_mode": "default_stream_async_device_to_device",
                "resident_warp_scratch_bytes": 493209636,
                "resident_registration_fastpath_contract_check_count": 24,
                "resident_registration_fastpath_contract_failed_check_count": 0,
                "resident_registration_fastpath": {
                    "status": "present",
                    "contract_status": "passed",
                    "mode": "similarity_cuda_triangle",
                    "triangle_descriptor_fit_batch": True,
                    "triangle_descriptor_fit_batch_mode": "native_batch_shared_reference_device",
                    "triangle_descriptor_fit_device_reuse": {
                        "reference": True,
                        "moving": True,
                        "output": True,
                    },
                    "triangle_pixel_refine_batch": True,
                    "triangle_pixel_refine_batch_metric_mode": "flattened_frame_candidate_grid",
                    "triangle_warp_batch": True,
                    "triangle_warp_batch_mode": "native_matrix_lanczos3_frames",
                    "triangle_warp_batch_frame_count": 188,
                    "resident_warp_copy_mode": "default_stream_async_device_to_device",
                    "resident_warp_scratch_bytes": 493209636,
                    "contract_check_count": 24,
                    "contract_failed_check_count": 0,
                },
                "native_guardrails_bundle": {
                    "status": "present",
                    "resident_result_contract_source": "run_default",
                    "resident_result_contract_run_default": True,
                    "resident_native_calibration_artifact": True,
                    "resident_calibration_master_count": 3,
                    "resident_calibrated_light_count": 200,
                },
            },
            "stack_engine_contract": {
                "audit_type": "stack_engine_default_contract",
                "status": "passed" if stack_check_passed else "failed",
                "passed": stack_check_passed,
                "scope": "all",
                "default_promotion_ready": stack_check_passed,
                "default_promotion_status": "ready" if stack_check_passed else "blocked",
                "adoption_recommendation": stack_recommendation,
                "default_promotion_recommendation": stack_recommendation,
                "adoption_phase2_stack_engine_default_gap_count": stack_engine_gap_count,
                "default_promotion_phase2_stack_engine_default_gap_count": (
                    stack_engine_gap_count
                ),
                "default_promotion_blocker_count": 0 if stack_check_passed else 1,
                "default_promotion_blockers": []
                if stack_check_passed
                else [
                    {
                        "name": "phase2_stack_engine_default_gaps",
                        "gap_count": stack_engine_gap_count,
                    }
                ],
            },
            "pipeline_contract": {
                "status": "passed" if passed else "failed",
                "passed": passed,
                "failed_check_count": 0 if passed else 1,
                "integration_output_count": 1,
                "integration_map_count": 6,
                "integration_dq_contract": passed,
                "integration_stack_result_contract": passed,
                "integration_resident_result_contract": passed,
                "pixel_verification_enabled": True,
                "integration_dq_map_pixels_match_summary": passed,
                "integration_coverage_map_pixels_match_dq": passed,
                "integration_rejection_map_pixels_match_dq": passed,
                "integration_rejection_sample_counts_match_maps": accounting_passed,
                "rejection_sample_accounting_status": "passed" if accounting_passed else "failed",
                "rejection_sample_accounting_failed_count": 0 if accounting_passed else 1,
                "integration_sample_accounting_closure": sample_closure_passed,
                "sample_accounting_closure": {
                    "status": "passed" if sample_closure_passed else "failed",
                    "check_present": True,
                    "present_count": 1,
                    "failed_count": 0 if sample_closure_passed else 1,
                    "failed_items": []
                    if sample_closure_passed
                    else [{"output_id": "master_H", "reason": "sample_closure_drift"}],
                },
                "sample_accounting_closure_status": "passed"
                if sample_closure_passed
                else "failed",
                "sample_accounting_closure_present_count": 1,
                "sample_accounting_closure_failed_count": 0 if sample_closure_passed else 1,
            },
            "release_decision": {
                "status": "default_change_ready" if passed else "release_candidate_ready",
                "recommendation": "promote_default_candidate"
                if passed
                else "repeat_benchmark_before_default_change",
                "release_candidate_ready": passed,
                "default_change_ready": passed,
                "speedup_actual": 58.0,
                "runtime_repeat_run_count": 3,
                "runtime_repeat_best_label": "repeat02",
                "runtime_repeat_best_elapsed_s": 22.6,
                "runtime_repeat_elapsed_ratio_vs_best": 1.053,
                "runtime_repeat_max_elapsed_ratio_vs_best": 1.25,
            },
        },
    )


def _phase2_compare(path: Path, *, passed: bool = True, baseline_gate: int = 203, candidate_gate: int = 204) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "artifact_type": "glass_phase2_status_compare",
            "status": "passed" if passed else "regressed",
            "passed": passed,
            "baseline": {"latest_gate": baseline_gate},
            "candidate": {"latest_gate": candidate_gate},
        },
    )


def _release_direct_publication_guard(
    *,
    ready: bool = True,
    top_level: bool = False,
    acceptance_source: str = "explicit_resident_artifacts_json",
    calibration_source: str = "resident_artifacts_json_fallback",
    resident_lights: int = 200,
) -> dict[str, object]:
    source_ready = (
        ready
        and acceptance_source == "explicit_resident_artifacts_json"
        and calibration_source == "resident_artifacts_json_fallback"
    )
    count_ready = ready and resident_lights >= 200
    if top_level:
        return {
            "present": True,
            "ready": ready and source_ready and count_ready,
            "decision_check_passed": ready,
            "checks_passed": ready,
            "source_ready": source_ready,
            "count_ready": count_ready,
            "raw_leaf_checks_ready": ready,
            "phase2_leaf_checks_ready": ready,
            "raw_acceptance_source": acceptance_source,
            "phase2_acceptance_source": acceptance_source,
            "raw_calibration_source": calibration_source,
            "phase2_calibration_source": calibration_source,
            "raw_resident_lights": resident_lights if ready else 0,
            "raw_default_promotion_resident_lights": resident_lights if ready else 0,
            "phase2_resident_lights": resident_lights if ready else 0,
            "phase2_default_promotion_resident_lights": resident_lights
            if ready
            else 0,
            "required_min_resident_lights": 200,
        }
    return {
        "present": True,
        "ready": ready and source_ready and count_ready,
        "decision_check_passed": ready,
        "checks_passed": ready,
        "source_ready": source_ready,
        "count_ready": count_ready,
        "leaf_checks_ready": ready,
        "raw_ready": ready,
        "phase2_ready": ready,
        "phase2_check_passed": ready,
        "raw_matrix_acceptance_source": acceptance_source,
        "raw_default_promotion_acceptance_source": acceptance_source,
        "phase2_matrix_acceptance_source": acceptance_source,
        "phase2_default_promotion_acceptance_source": acceptance_source,
        "raw_matrix_acceptance_check_count": 24 if ready else 0,
        "raw_default_promotion_acceptance_check_count": 24 if ready else 0,
        "phase2_matrix_acceptance_check_count": 24 if ready else 0,
        "phase2_default_promotion_acceptance_check_count": 24 if ready else 0,
        "raw_matrix_pipeline_calibration_source": calibration_source,
        "raw_default_promotion_pipeline_calibration_source": calibration_source,
        "phase2_matrix_pipeline_calibration_source": calibration_source,
        "phase2_default_promotion_pipeline_calibration_source": calibration_source,
        "raw_matrix_pipeline_resident_lights": resident_lights if ready else 0,
        "raw_default_promotion_pipeline_resident_lights": resident_lights
        if ready
        else 0,
        "phase2_matrix_pipeline_resident_lights": resident_lights if ready else 0,
        "phase2_default_promotion_pipeline_resident_lights": resident_lights
        if ready
        else 0,
        "required_min_resident_lights": 200,
    }


def _release_matrix(
    path: Path,
    *,
    labels: list[str],
    ready: bool = True,
    rejection_sample_accounting_ready: bool = True,
    sample_accounting_closure_ready: bool = True,
    include_stack_engine_contract: bool = True,
    stack_engine_ready: bool = True,
    stack_engine_gap_count: int = 0,
    include_release_direct_guard: bool = True,
    release_direct_guard_ready: bool = True,
    default_release_direct_guard_ready: bool = True,
    release_direct_acceptance_source: str = "explicit_resident_artifacts_json",
) -> None:
    ordered_try_list = labels if "cpu" in labels else [*labels, "cpu"]
    stack_ready = stack_engine_ready and stack_engine_gap_count == 0
    matrix_ready = (
        ready
        and rejection_sample_accounting_ready
        and sample_accounting_closure_ready
        and (stack_ready if include_stack_engine_contract else True)
    )
    stack_recommendation = (
        "stack_engine_default_ready"
        if stack_ready
        else "stack_engine_contract_gaps_remain"
    )
    stack_contract = {
        "present": True,
        "ready": stack_ready,
        "phase2_check_passed": stack_ready,
        "status": "passed" if stack_ready else "failed",
        "passed": stack_ready,
        "scope": "all",
        "adoption_recommendation": stack_recommendation,
        "default_promotion_phase2_stack_engine_default_gap_count": (
            stack_engine_gap_count
        ),
        "default_promotion_blocker_count": 0 if stack_ready else 1,
        "default_promotion_blockers": []
        if stack_ready
        else [
            {
                "name": "phase2_stack_engine_default_gaps",
                "gap_count": stack_engine_gap_count,
            }
        ],
    }
    default_promotion = {
        "status": "default_promotion_ready" if matrix_ready else "blocked",
        "passed": matrix_ready,
        "default_change_ready": matrix_ready,
        "default_route_passed": ready,
        "default_route_route_contract_passed": ready,
        "default_route_route_check_count": 4 if ready else 2,
        "default_route_speedup_vs_reference": 28.75,
        "integration_rejection_sample_counts_match_maps": rejection_sample_accounting_ready,
        "rejection_sample_accounting_status": "passed"
        if rejection_sample_accounting_ready
        else "failed",
        "rejection_sample_accounting_failed_count": 0
        if rejection_sample_accounting_ready
        else 1,
        "integration_sample_accounting_closure": sample_accounting_closure_ready,
        "sample_accounting_closure": {
            "status": "passed" if sample_accounting_closure_ready else "failed",
            "check_present": True,
            "present_count": 1,
            "failed_count": 0 if sample_accounting_closure_ready else 1,
            "failed_items": []
            if sample_accounting_closure_ready
            else [{"output_id": "master_H", "reason": "sample_closure_drift"}],
        },
        "sample_accounting_closure_status": "passed"
        if sample_accounting_closure_ready
        else "failed",
        "sample_accounting_closure_present_count": 1,
        "sample_accounting_closure_failed_count": 0
        if sample_accounting_closure_ready
        else 1,
    }
    release_direct_guard = _release_direct_publication_guard(
        ready=release_direct_guard_ready,
        top_level=True,
        acceptance_source=release_direct_acceptance_source,
    )
    default_release_direct_guard = _release_direct_publication_guard(
        ready=default_release_direct_guard_ready,
        acceptance_source=release_direct_acceptance_source,
    )
    if include_release_direct_guard:
        default_promotion.update(
            {
                "release_decision_direct_runtime_publication_guard": (
                    default_release_direct_guard
                ),
                "release_decision_direct_runtime_publication_guard_present": (
                    default_release_direct_guard["present"]
                ),
                "release_decision_direct_runtime_publication_guard_ready": (
                    default_release_direct_guard["ready"]
                ),
                "release_decision_direct_runtime_publication_guard_check_passed": (
                    default_release_direct_guard["decision_check_passed"]
                ),
                "release_decision_direct_runtime_publication_guard_source_ready": (
                    default_release_direct_guard["source_ready"]
                ),
                "release_decision_direct_runtime_publication_guard_count_ready": (
                    default_release_direct_guard["count_ready"]
                ),
                "release_decision_direct_runtime_publication_guard_leaf_checks_ready": (
                    default_release_direct_guard["leaf_checks_ready"]
                ),
                "release_decision_direct_runtime_publication_guard_raw_acceptance_source": (
                    default_release_direct_guard["raw_matrix_acceptance_source"]
                ),
                "release_decision_direct_runtime_publication_guard_raw_calibration_source": (
                    default_release_direct_guard[
                        "raw_matrix_pipeline_calibration_source"
                    ]
                ),
                "release_decision_direct_runtime_publication_guard_raw_resident_lights": (
                    default_release_direct_guard[
                        "raw_matrix_pipeline_resident_lights"
                    ]
                ),
            }
        )
    if include_stack_engine_contract:
        default_promotion.update(
            {
                "stack_engine_contract": stack_contract,
                "stack_engine_contract_present": True,
                "stack_engine_contract_ready": stack_ready,
                "stack_engine_contract_phase2_check_passed": stack_ready,
                "stack_engine_contract_status": stack_contract["status"],
                "stack_engine_contract_passed": stack_ready,
                "stack_engine_contract_scope": "all",
                "stack_engine_contract_adoption_recommendation": stack_recommendation,
                "stack_engine_contract_default_gap_count": stack_engine_gap_count,
                "stack_engine_contract_blocker_count": 0 if stack_ready else 1,
                "stack_engine_contract_blockers": stack_contract[
                    "default_promotion_blockers"
                ],
            }
        )
    payload = {
            "schema_version": 1,
            "artifact_type": "windows_release_matrix",
            "status": "release_matrix_ready" if matrix_ready else "blocked",
            "passed": matrix_ready,
            "recommendation": "publish_windows_cuda_matrix"
            if matrix_ready
            else "fix_release_matrix_blockers",
            "current_machine": {
                "primary_package": labels[0] if labels else None,
                "ordered_try_list": ordered_try_list,
                "cuda_available": "cpu" not in labels[:1],
                "native_extension_loaded": "cpu" not in labels[:1],
            },
            "default_promotion_manifest": default_promotion,
            "packages": [
                {
                    "label": label,
                    "release_artifact": f"GLASS-Portable-win64-{label}.zip",
                    "compatible": True,
                }
                for label in labels
            ],
            "failed_checks": []
            if matrix_ready
            else ["default_promotion_manifest_ready"],
        }
    if include_release_direct_guard:
        payload["release_decision_direct_runtime_publication_guard"] = (
            release_direct_guard
        )
    write_json(path, payload)


def test_windows_github_release_plan_records_assets(tmp_path: Path):
    zip_file = tmp_path / "GLASS-Portable-win64-cuda13.zip"
    zip_file.write_bytes(b"zip")
    manifest = tmp_path / "manifest.json"
    matrix = tmp_path / "matrix.json"
    _manifest(manifest, zip_paths={"cuda13": zip_file})
    _release_matrix(matrix, labels=["cuda13"])

    payload = build_windows_github_release_plan(
        manifest_artifact=manifest,
        tag="v0.1.0-test",
        title="Test Release",
        notes_file=tmp_path / "notes.md",
        require_same_source_stamp=True,
        windows_release_matrix=matrix,
    )

    assert payload["passed"] is True
    assert payload["publication_ready"] is True
    assert payload["assets"][0]["label"] == "cuda13"
    assert payload["release_matrix"]["status"] == "release_matrix_ready"
    assert (
        payload["release_matrix"][
            "release_decision_direct_runtime_publication_guard_ready"
        ]
        is True
    )
    assert (
        payload["release_matrix"][
            "default_promotion_release_decision_direct_runtime_publication_guard_ready"
        ]
        is True
    )
    assert "gh release create v0.1.0-test" in payload["release"]["command"]
    assert "--draft" in payload["release"]["command"]


def test_windows_github_release_plan_accepts_phase2_handoff_evidence(tmp_path: Path):
    zip_file = tmp_path / "GLASS-Portable-win64-cuda13.zip"
    zip_file.write_bytes(b"zip")
    manifest = tmp_path / "manifest.json"
    phase2_status = tmp_path / "phase2_status.json"
    phase2_compare = tmp_path / "phase2_compare.json"
    matrix = tmp_path / "matrix.json"
    _manifest(manifest, zip_paths={"cuda13": zip_file})
    _phase2_status(phase2_status, gate=204)
    _phase2_compare(phase2_compare, baseline_gate=203, candidate_gate=204)
    _release_matrix(matrix, labels=["cuda13"])

    payload = build_windows_github_release_plan(
        manifest_artifact=manifest,
        tag="v0.1.0-test",
        phase2_status=phase2_status,
        phase2_status_compare=phase2_compare,
        windows_release_matrix=matrix,
    )

    checks = {str(item["name"]): item["passed"] for item in payload["checks"]}
    assert payload["passed"] is True
    assert payload["phase2"]["status"]["latest_gate"] == 204
    assert payload["phase2"]["status"]["resident_result_contract_source"] == "run_default"
    assert payload["phase2"]["status"]["resident_result_contract_run_default"] is True
    assert payload["phase2"]["status"]["resident_native_calibration_artifact"] is True
    assert payload["phase2"]["status"]["resident_calibrated_light_count"] == 200
    assert payload["phase2"]["status"]["resident_registration_fastpath_status"] == "present"
    assert payload["phase2"]["status"]["resident_registration_fastpath_contract_status"] == "passed"
    assert payload["phase2"]["status"]["resident_registration_fastpath_mode"] == "similarity_cuda_triangle"
    assert payload["phase2"]["status"]["triangle_descriptor_fit_batch"] is True
    assert payload["phase2"]["status"]["triangle_warp_batch_frame_count"] == 188
    assert payload["phase2"]["status"]["pipeline_contract_status"] == "passed"
    assert payload["phase2"]["status"]["pipeline_integration_dq_contract"] is True
    assert payload["phase2"]["status"]["pipeline_pixel_verification_enabled"] is True
    assert payload["phase2"]["status"]["pipeline_rejection_sample_accounting_status"] == "passed"
    assert payload["phase2"]["status"]["pipeline_integration_sample_accounting_closure"] is True
    assert payload["phase2"]["status"]["pipeline_sample_accounting_closure_status"] == "passed"
    assert payload["phase2"]["status"]["stack_engine_default_contract_status"] == "passed"
    assert payload["phase2"]["status"]["stack_engine_default_contract_phase2_check_passed"] is True
    assert payload["phase2"]["status"]["stack_engine_default_contract_default_gap_count"] == 0
    assert payload["phase2"]["status"]["stack_engine_default_contract_blocker_count"] == 0
    assert payload["phase2"]["status"]["release_decision_status"] == "default_change_ready"
    assert payload["phase2"]["status"]["release_decision_default_change_ready"] is True
    assert payload["phase2"]["status"]["release_runtime_repeat_elapsed_ratio_vs_best"] == 1.053
    assert payload["phase2"]["status_compare"]["candidate_gate"] == 204
    assert payload["release_matrix"]["primary_package"] == "cuda13"
    assert payload["release_matrix"]["rejection_sample_accounting_status"] == "passed"
    assert payload["release_matrix"]["sample_accounting_closure_status"] == "passed"
    assert payload["release_matrix"]["stack_engine_contract_ready"] is True
    assert payload["release_matrix"]["stack_engine_contract_phase2_check_passed"] is True
    assert payload["release_matrix"]["stack_engine_contract_default_gap_count"] == 0
    assert checks["phase2_status_present"] is True
    assert checks["phase2_status_green"] is True
    assert checks["phase2_pipeline_rejection_sample_accounting_passed"] is True
    assert checks["phase2_pipeline_sample_accounting_closure_passed"] is True
    assert checks["phase2_stack_engine_default_contract_ready"] is True
    assert checks["phase2_status_compare_present"] is True
    assert checks["phase2_status_compare_passed"] is True
    assert checks["windows_release_matrix_ready"] is True
    assert checks["windows_release_matrix_default_route_passed"] is True
    assert checks["windows_release_matrix_rejection_sample_accounting_passed"] is True
    assert checks["windows_release_matrix_sample_accounting_closure_passed"] is True
    assert checks["windows_release_matrix_stack_engine_contract_ready"] is True
    assert (
        checks[
            "windows_release_matrix_release_decision_direct_runtime_publication_guard_passed"
        ]
        is True
    )
    assert (
        checks[
            "windows_release_matrix_default_promotion_release_decision_direct_runtime_publication_guard_passed"
        ]
        is True
    )
    assert checks["phase2_release_matrix_stack_engine_contract_agree"] is True


def test_windows_github_release_plan_blocks_failed_phase2_handoff_evidence(tmp_path: Path):
    zip_file = tmp_path / "GLASS-Portable-win64-cuda13.zip"
    zip_file.write_bytes(b"zip")
    manifest = tmp_path / "manifest.json"
    phase2_status = tmp_path / "phase2_status.json"
    phase2_compare = tmp_path / "phase2_compare.json"
    matrix = tmp_path / "matrix.json"
    _manifest(manifest, zip_paths={"cuda13": zip_file})
    _phase2_status(phase2_status, passed=False, gate=204)
    _phase2_compare(phase2_compare, passed=False, baseline_gate=204, candidate_gate=203)
    _release_matrix(matrix, labels=["cuda13", "cpu"])

    payload = build_windows_github_release_plan(
        manifest_artifact=manifest,
        tag="v0.1.0-test",
        phase2_status=phase2_status,
        phase2_status_compare=phase2_compare,
        windows_release_matrix=matrix,
    )

    checks = {str(item["name"]): item["passed"] for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["publication_ready"] is False
    assert checks["phase2_status_green"] is False
    assert checks["phase2_stack_engine_default_contract_ready"] is False
    assert checks["phase2_status_compare_passed"] is False
    assert "phase2_status_green" in payload["failed_checks"]
    assert "phase2_stack_engine_default_contract_ready" in payload["failed_checks"]
    assert "phase2_status_compare_passed" in payload["failed_checks"]


def test_windows_github_release_plan_blocks_phase2_sample_closure_drift(tmp_path: Path):
    zip_file = tmp_path / "GLASS-Portable-win64-cuda13.zip"
    zip_file.write_bytes(b"zip")
    manifest = tmp_path / "manifest.json"
    phase2_status = tmp_path / "phase2_status.json"
    matrix = tmp_path / "matrix.json"
    _manifest(manifest, zip_paths={"cuda13": zip_file})
    _phase2_status(phase2_status, sample_accounting_closure_ready=False, gate=248)
    _release_matrix(matrix, labels=["cuda13"])

    payload = build_windows_github_release_plan(
        manifest_artifact=manifest,
        tag="v0.1.0-test",
        phase2_status=phase2_status,
        windows_release_matrix=matrix,
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["publication_ready"] is False
    assert payload["phase2"]["status"]["pipeline_sample_accounting_closure_status"] == "failed"
    assert checks["phase2_pipeline_sample_accounting_closure_passed"]["passed"] is False
    assert checks["phase2_pipeline_sample_accounting_closure_passed"]["evidence"] == {
        "check": False,
        "status": "failed",
        "present_count": 1,
        "failed_count": 1,
        "failed_items": [{"output_id": "master_H", "reason": "sample_closure_drift"}],
    }


def test_windows_github_release_plan_blocks_phase2_stack_engine_contract_gap(
    tmp_path: Path,
):
    zip_file = tmp_path / "GLASS-Portable-win64-cuda13.zip"
    zip_file.write_bytes(b"zip")
    manifest = tmp_path / "manifest.json"
    phase2_status = tmp_path / "phase2_status.json"
    matrix = tmp_path / "matrix.json"
    _manifest(manifest, zip_paths={"cuda13": zip_file})
    _phase2_status(
        phase2_status,
        gate=254,
        stack_engine_ready=False,
        stack_engine_gap_count=1,
    )
    _release_matrix(matrix, labels=["cuda13"])

    payload = build_windows_github_release_plan(
        manifest_artifact=manifest,
        tag="v0.1.0-test",
        phase2_status=phase2_status,
        windows_release_matrix=matrix,
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["publication_ready"] is False
    assert payload["phase2"]["status"]["stack_engine_default_contract_status"] == "failed"
    assert checks["phase2_stack_engine_default_contract_ready"]["passed"] is False
    assert checks["phase2_stack_engine_default_contract_ready"]["evidence"] == {
        "present": True,
        "phase2_check_passed": False,
        "audit_type": "stack_engine_default_contract",
        "status": "failed",
        "passed": False,
        "scope": "all",
        "default_promotion_ready": False,
        "default_promotion_status": "blocked",
        "adoption_recommendation": "stack_engine_contract_gaps_remain",
        "default_promotion_recommendation": "stack_engine_contract_gaps_remain",
        "default_gap_count": 1,
        "blocker_count": 1,
        "blockers": [{"name": "phase2_stack_engine_default_gaps", "gap_count": 1}],
    }


def test_windows_github_release_plan_blocks_missing_windows_release_matrix(tmp_path: Path):
    zip_file = tmp_path / "GLASS-Portable-win64-cuda13.zip"
    zip_file.write_bytes(b"zip")
    manifest = tmp_path / "manifest.json"
    _manifest(manifest, zip_paths={"cuda13": zip_file})

    payload = build_windows_github_release_plan(
        manifest_artifact=manifest,
        tag="v0.1.0-test",
    )

    checks = {str(item["name"]): item["passed"] for item in payload["checks"]}
    assert payload["passed"] is False
    assert checks["windows_release_matrix_present"] is False
    assert checks["windows_release_matrix_ready"] is False
    assert "windows_release_matrix_present" in payload["failed_checks"]


def test_windows_github_release_plan_blocks_failed_windows_release_matrix(tmp_path: Path):
    zip_file = tmp_path / "GLASS-Portable-win64-cuda13.zip"
    zip_file.write_bytes(b"zip")
    manifest = tmp_path / "manifest.json"
    matrix = tmp_path / "matrix.json"
    _manifest(manifest, zip_paths={"cuda13": zip_file})
    _release_matrix(matrix, labels=["cuda13", "cpu"], ready=False)

    payload = build_windows_github_release_plan(
        manifest_artifact=manifest,
        tag="v0.1.0-test",
        windows_release_matrix=matrix,
    )

    checks = {str(item["name"]): item["passed"] for item in payload["checks"]}
    assert payload["passed"] is False
    assert checks["windows_release_matrix_present"] is True
    assert checks["windows_release_matrix_ready"] is False
    assert checks["windows_release_matrix_default_promotion_ready"] is False


def test_windows_github_release_plan_blocks_release_matrix_rejection_sample_drift(
    tmp_path: Path,
):
    zip_file = tmp_path / "GLASS-Portable-win64-cuda13.zip"
    zip_file.write_bytes(b"zip")
    manifest = tmp_path / "manifest.json"
    matrix = tmp_path / "matrix.json"
    _manifest(manifest, zip_paths={"cuda13": zip_file})
    _release_matrix(matrix, labels=["cuda13"], rejection_sample_accounting_ready=False)

    payload = build_windows_github_release_plan(
        manifest_artifact=manifest,
        tag="v0.1.0-test",
        windows_release_matrix=matrix,
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["publication_ready"] is False
    assert payload["release_matrix"]["rejection_sample_accounting_status"] == "failed"
    assert checks["windows_release_matrix_rejection_sample_accounting_passed"]["passed"] is False
    assert checks["windows_release_matrix_rejection_sample_accounting_passed"]["evidence"] == {
        "check": False,
        "status": "failed",
        "failed_count": 1,
    }


def test_windows_github_release_plan_blocks_release_matrix_sample_closure_drift(
    tmp_path: Path,
):
    zip_file = tmp_path / "GLASS-Portable-win64-cuda13.zip"
    zip_file.write_bytes(b"zip")
    manifest = tmp_path / "manifest.json"
    matrix = tmp_path / "matrix.json"
    _manifest(manifest, zip_paths={"cuda13": zip_file})
    _release_matrix(matrix, labels=["cuda13"], sample_accounting_closure_ready=False)

    payload = build_windows_github_release_plan(
        manifest_artifact=manifest,
        tag="v0.1.0-test",
        windows_release_matrix=matrix,
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["publication_ready"] is False
    assert payload["release_matrix"]["sample_accounting_closure_status"] == "failed"
    assert checks["windows_release_matrix_sample_accounting_closure_passed"]["passed"] is False
    assert checks["windows_release_matrix_sample_accounting_closure_passed"]["evidence"] == {
        "check": False,
        "status": "failed",
        "present_count": 1,
        "failed_count": 1,
        "failed_items": [{"output_id": "master_H", "reason": "sample_closure_drift"}],
    }


def test_windows_github_release_plan_blocks_missing_release_matrix_stack_engine_contract(
    tmp_path: Path,
):
    zip_file = tmp_path / "GLASS-Portable-win64-cuda13.zip"
    zip_file.write_bytes(b"zip")
    manifest = tmp_path / "manifest.json"
    matrix = tmp_path / "matrix.json"
    _manifest(manifest, zip_paths={"cuda13": zip_file})
    _release_matrix(
        matrix,
        labels=["cuda13"],
        include_stack_engine_contract=False,
    )

    payload = build_windows_github_release_plan(
        manifest_artifact=manifest,
        tag="v0.1.0-test",
        windows_release_matrix=matrix,
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["publication_ready"] is False
    assert checks["windows_release_matrix_ready"]["passed"] is True
    assert checks["windows_release_matrix_stack_engine_contract_ready"]["passed"] is False
    assert checks["windows_release_matrix_stack_engine_contract_ready"]["evidence"] == {
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


def test_windows_github_release_plan_blocks_release_matrix_stack_engine_contract_gap(
    tmp_path: Path,
):
    zip_file = tmp_path / "GLASS-Portable-win64-cuda13.zip"
    zip_file.write_bytes(b"zip")
    manifest = tmp_path / "manifest.json"
    matrix = tmp_path / "matrix.json"
    _manifest(manifest, zip_paths={"cuda13": zip_file})
    _release_matrix(
        matrix,
        labels=["cuda13"],
        stack_engine_ready=False,
        stack_engine_gap_count=1,
    )

    payload = build_windows_github_release_plan(
        manifest_artifact=manifest,
        tag="v0.1.0-test",
        windows_release_matrix=matrix,
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["publication_ready"] is False
    assert payload["release_matrix"]["stack_engine_contract_ready"] is False
    assert checks["windows_release_matrix_ready"]["passed"] is False
    assert checks["windows_release_matrix_stack_engine_contract_ready"]["passed"] is False
    assert checks["windows_release_matrix_stack_engine_contract_ready"]["evidence"][
        "default_gap_count"
    ] == 1
    assert checks["windows_release_matrix_stack_engine_contract_ready"]["evidence"][
        "blocker_count"
    ] == 1


def test_windows_github_release_plan_blocks_missing_release_matrix_direct_publication_guard(
    tmp_path: Path,
):
    zip_file = tmp_path / "GLASS-Portable-win64-cuda13.zip"
    zip_file.write_bytes(b"zip")
    manifest = tmp_path / "manifest.json"
    matrix = tmp_path / "matrix.json"
    _manifest(manifest, zip_paths={"cuda13": zip_file})
    _release_matrix(matrix, labels=["cuda13"], include_release_direct_guard=False)

    payload = build_windows_github_release_plan(
        manifest_artifact=manifest,
        tag="v0.1.0-test",
        windows_release_matrix=matrix,
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["publication_ready"] is False
    assert checks["windows_release_matrix_ready"]["passed"] is True
    assert (
        checks[
            "windows_release_matrix_release_decision_direct_runtime_publication_guard_passed"
        ]["passed"]
        is False
    )
    assert (
        checks[
            "windows_release_matrix_default_promotion_release_decision_direct_runtime_publication_guard_passed"
        ]["passed"]
        is False
    )


def test_windows_github_release_plan_blocks_stale_default_promotion_direct_publication_guard(
    tmp_path: Path,
):
    zip_file = tmp_path / "GLASS-Portable-win64-cuda13.zip"
    zip_file.write_bytes(b"zip")
    manifest = tmp_path / "manifest.json"
    matrix = tmp_path / "matrix.json"
    _manifest(manifest, zip_paths={"cuda13": zip_file})
    _release_matrix(
        matrix,
        labels=["cuda13"],
        default_release_direct_guard_ready=False,
    )

    payload = build_windows_github_release_plan(
        manifest_artifact=manifest,
        tag="v0.1.0-test",
        windows_release_matrix=matrix,
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["publication_ready"] is False
    assert (
        checks[
            "windows_release_matrix_release_decision_direct_runtime_publication_guard_passed"
        ]["passed"]
        is True
    )
    assert (
        checks[
            "windows_release_matrix_default_promotion_release_decision_direct_runtime_publication_guard_passed"
        ]["passed"]
        is False
    )
    assert (
        checks[
            "windows_release_matrix_default_promotion_release_decision_direct_runtime_publication_guard_passed"
        ]["evidence"]["resident_lights"]
        == 0
    )


def test_windows_github_release_plan_blocks_mixed_sources(tmp_path: Path):
    zip_a = tmp_path / "a.zip"
    zip_b = tmp_path / "b.zip"
    zip_a.write_bytes(b"a")
    zip_b.write_bytes(b"b")
    manifest = tmp_path / "manifest.json"
    matrix = tmp_path / "matrix.json"
    _manifest(manifest, zip_paths={"cuda13": zip_a}, source="aaa1111")
    _release_matrix(matrix, labels=["cuda13", "cpu"])
    payload = read_json(manifest)
    payload["packages"].append(
        {
            "label": "cpu",
            "zip_path": str(zip_b),
            "exists": True,
            "size_bytes": zip_b.stat().st_size,
            "sha256": "2".zfill(64),
            "source_stamp": "bbb2222",
        }
    )
    write_json(manifest, payload)

    plan = build_windows_github_release_plan(
        manifest_artifact=manifest,
        tag="v0.1.0-test",
        require_same_source_stamp=True,
        windows_release_matrix=matrix,
    )

    checks = {str(item["name"]): item["passed"] for item in plan["checks"]}
    assert plan["passed"] is False
    assert checks["same_source_stamp"] is False


def test_windows_github_release_plan_cli_writes_outputs(tmp_path: Path):
    zip_file = tmp_path / "GLASS-Portable-win64-cpu.zip"
    zip_file.write_bytes(b"cpu")
    manifest = tmp_path / "manifest.json"
    _manifest(manifest, zip_paths={"cpu": zip_file})
    out = tmp_path / "plan.json"
    markdown = tmp_path / "plan.md"
    notes = tmp_path / "notes.md"
    script = tmp_path / "publish_release.ps1"
    phase2_status = tmp_path / "phase2_status.json"
    phase2_compare = tmp_path / "phase2_compare.json"
    matrix = tmp_path / "matrix.json"
    _phase2_status(phase2_status)
    _phase2_compare(phase2_compare)
    _release_matrix(matrix, labels=["cpu"])

    result = main(
        [
            "windows-github-release-plan",
            "--manifest",
            str(manifest),
            "--tag",
            "v0.1.0-test",
            "--out",
            str(out),
            "--markdown",
            str(markdown),
            "--notes",
            str(notes),
            "--script",
            str(script),
            "--phase2-status",
            str(phase2_status),
            "--phase2-status-compare",
            str(phase2_compare),
            "--windows-release-matrix",
            str(matrix),
            "--require-same-source-stamp",
            "--fail-on-failure",
        ]
    )

    assert result == 0
    payload = read_json(out)
    assert payload["status"] == "release_plan_ready"
    assert payload["release"]["script_file"] == str(script.resolve())
    assert payload["release"]["script_default_mode"] == "dry_run_requires_publish_switch"
    markdown_text = markdown.read_text(encoding="utf-8")
    assert "GLASS Windows GitHub Release Plan" in markdown_text
    assert "Publish script" in markdown_text
    assert "Windows Release Matrix Handoff" in markdown_text
    assert "Matrix status: `release_matrix_ready`" in markdown_text
    assert "Default route contract/checks: `True`/`4`" in markdown_text
    assert "Release direct publication guard: ready=`True` check=`True`" in markdown_text
    assert "Default-promotion release direct guard: ready=`True` check=`True`" in markdown_text
    assert "StackEngine default contract: ready=`True` phase2-check=`True` gaps=`0` blockers=`0`" in markdown_text
    assert "Rejection sample accounting: `passed` failed `0`" in markdown_text
    assert "Sample accounting closure: `passed` present=`1` failed=`0`" in markdown_text
    assert "Phase 2 Handoff Preflight" in markdown_text
    assert "Native resident contract source: `run_default`" in markdown_text
    assert "Native calibrated lights: `200`" in markdown_text
    assert "Resident registration fast path: `present`" in markdown_text
    assert "Triangle warp batch: `True`" in markdown_text
    assert "Pipeline contract: `passed`" in markdown_text
    assert "Pipeline integration DQ contract: `True`" in markdown_text
    assert "Pipeline rejection sample accounting: `passed`" in markdown_text
    assert "Pipeline sample accounting closure: `passed`" in markdown_text
    assert "StackEngine default contract: `passed` check `True` gaps `0` blockers `0`" in markdown_text
    assert "Release decision: `default_change_ready`" in markdown_text
    assert "Runtime repeat ratio vs best: `1.053`" in markdown_text
    assert "Recommended Install Order" in notes.read_text(encoding="utf-8")
    notes_text = notes.read_text(encoding="utf-8")
    assert "Windows Release Matrix Evidence" in notes_text
    assert "Default route contract: `True` checks `4`" in notes_text
    assert "Release direct publication guard: ready `True` check `True`" in notes_text
    assert "Default-promotion release direct guard: ready `True` check `True`" in notes_text
    assert "StackEngine default contract: ready `True` phase2-check `True` gaps `0` blockers `0`" in notes_text
    assert "Rejection sample accounting: `passed` failed `0`" in notes_text
    assert "Sample accounting closure: `passed` present `1` failed `0`" in notes_text
    assert "Native resident contract source: `run_default`" in notes_text
    assert "calibrated lights `200`" in notes_text
    assert "Resident registration fast path: `present`" in notes_text
    assert "warp batch `True` frames `188`" in notes_text
    assert "Pipeline DQ contract: `passed` passed `True` DQ `True`" in notes_text
    assert "Pipeline pixel verification: `True`" in notes_text
    assert "Pipeline rejection sample accounting: `passed` check `True` failed `0`" in notes_text
    assert "Pipeline sample accounting closure: `passed` check `True` failed `0`" in notes_text
    assert "StackEngine default contract: `passed` check `True` gaps `0` blockers `0`" in notes_text
    assert "Default-change decision: `default_change_ready` ready `True`" in notes_text
    assert "Runtime repeat evidence: runs `3`" in notes_text
    script_text = script.read_text(encoding="utf-8")
    assert "$ExpectedTag = 'v0.1.0-test'" in script_text
    assert "$WindowsReleaseMatrixFile =" in script_text
    assert "Windows release matrix check failed" in script_text
    assert "Windows release matrix default-promotion evidence failed" in script_text
    assert "Windows release matrix rejection sample accounting failed" in script_text
    assert "Windows release matrix sample accounting closure failed" in script_text
    assert "Windows release matrix StackEngine default contract failed" in script_text
    assert "Windows release matrix release-decision direct publication guard failed" in script_text
    assert "Windows release matrix default-promotion direct publication guard failed" in script_text
    assert "$Phase2StatusFile =" in script_text
    assert "$Phase2StatusCompareFile =" in script_text
    assert "Phase 2 status check failed" in script_text
    assert "Phase 2 sample accounting closure failed" in script_text
    assert "Phase 2 StackEngine default contract failed" in script_text
    assert "Phase 2 status compare check failed" in script_text
    assert "GitHub CLI authentication check failed" in script_text
    assert "Get-FileHash -LiteralPath $asset.Path -Algorithm SHA256" in script_text
    assert "SizeBytes = 3" in script_text
    assert "Re-run this script with -Publish" in script_text
    assert "& $GhPath @releaseArgs" in script_text
    assert "GitHub release creation failed" in script_text


def test_windows_github_release_plan_auth_check_blocks_publication(tmp_path: Path):
    zip_file = tmp_path / "GLASS-Portable-win64-cpu.zip"
    zip_file.write_bytes(b"cpu")
    manifest = tmp_path / "manifest.json"
    matrix = tmp_path / "matrix.json"
    _manifest(manifest, zip_paths={"cpu": zip_file})
    _release_matrix(matrix, labels=["cpu"])

    payload = build_windows_github_release_plan(
        manifest_artifact=manifest,
        tag="v0.1.0-test",
        gh_path=sys.executable,
        check_gh=True,
        check_gh_auth=True,
        windows_release_matrix=matrix,
    )

    assert payload["passed"] is True
    assert payload["publication_ready"] is False
    assert payload["gh"]["available"] is True
    assert payload["gh"]["auth_ok"] is False
    assert payload["recommendation"] == "authenticate_github_cli_then_run_release_command"
