from __future__ import annotations

from pathlib import Path
from typing import Any

from glass.io.json_io import read_json, write_json
from glass.models import now_iso


def _read_json_object(path: str | Path) -> dict[str, Any]:
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"JSON artifact must be an object: {path}")
    return payload


def _read_json_object_optional(path: str | Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    return _read_json_object(path)


def _check(name: str, passed: bool, evidence: dict[str, Any], note: str = "") -> dict[str, Any]:
    return {
        "name": name,
        "passed": bool(passed),
        "evidence": evidence,
        "note": note,
    }


def _number(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_value(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _status_value(payload: dict[str, Any], *keys: str) -> Any:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _artifact_type(payload: dict[str, Any]) -> str | None:
    value = payload.get("artifact_type")
    return None if value is None else str(value)


def _same_artifact_name(left: str | Path, right: Any) -> bool:
    if right is None:
        return False
    return Path(str(left)).name == Path(str(right)).name


def _runtime_repeat_summary(decision: dict[str, Any]) -> dict[str, Any]:
    runtime = decision.get("runtime_repeat") if isinstance(decision.get("runtime_repeat"), dict) else {}
    run_count = _int_value(runtime.get("considered_run_count"))
    if run_count is None:
        run_count = _int_value(runtime.get("run_count"))
    return {
        "present": runtime.get("present"),
        "run_count": _int_value(runtime.get("run_count")),
        "considered_run_count": run_count,
        "required_min_runtime_runs": _int_value(runtime.get("required_min_runtime_runs")),
        "best_label": runtime.get("best_label"),
        "best_elapsed_s": _number(runtime.get("best_elapsed_s")),
        "slowest_elapsed_s": _number(runtime.get("slowest_elapsed_s")),
        "elapsed_ratio_vs_best": _number(runtime.get("elapsed_ratio_vs_best")),
        "max_elapsed_ratio_vs_best": _number(runtime.get("max_elapsed_ratio_vs_best")),
        "recommendation": runtime.get("recommendation"),
    }


def _doctor_summary(doctor: dict[str, Any]) -> dict[str, Any]:
    if not doctor:
        return {"present": False}
    cuda = doctor.get("cuda") if isinstance(doctor.get("cuda"), dict) else {}
    packages = (
        doctor.get("windows_cuda_packages")
        if isinstance(doctor.get("windows_cuda_packages"), dict)
        else {}
    )
    devices = cuda.get("devices") if isinstance(cuda.get("devices"), list) else []
    first_device = devices[0] if devices and isinstance(devices[0], dict) else {}
    ordered_try_list = [str(item) for item in packages.get("ordered_try_list") or []]
    package_rows = [
        {
            "label": item.get("label"),
            "toolkit": item.get("toolkit"),
            "compatible": item.get("compatible"),
            "match": item.get("match"),
            "architectures": item.get("architectures"),
        }
        for item in packages.get("packages") or []
        if isinstance(item, dict)
    ]
    return {
        "present": True,
        "schema_version": doctor.get("schema_version"),
        "recommendation": doctor.get("recommendation"),
        "cuda_available": cuda.get("cuda_available"),
        "wrapper_importable": cuda.get("wrapper_importable"),
        "native_extension_loaded": cuda.get("native_extension_loaded"),
        "probe_skipped": cuda.get("probe_skipped"),
        "device": first_device,
        "primary_package": packages.get("primary"),
        "ordered_try_list": ordered_try_list,
        "package_rows": package_rows,
        "guidance": packages.get("guidance"),
    }


def _pipeline_summary(phase2: dict[str, Any]) -> dict[str, Any]:
    pipeline = (
        phase2.get("pipeline_contract") if isinstance(phase2.get("pipeline_contract"), dict) else {}
    )
    engine_policy = (
        pipeline.get("integration_engine_policy")
        if isinstance(pipeline.get("integration_engine_policy"), dict)
        else {}
    )
    return {
        "present": bool(pipeline),
        "status": pipeline.get("status"),
        "passed": pipeline.get("passed"),
        "check_count": pipeline.get("check_count"),
        "failed_check_count": pipeline.get("failed_check_count"),
        "failed_checks": pipeline.get("failed_checks") or [],
        "integration_output_count": pipeline.get("integration_output_count"),
        "integration_map_count": pipeline.get("integration_map_count"),
        "integration_dq_contract": pipeline.get("integration_dq_contract"),
        "integration_stack_result_contract": pipeline.get("integration_stack_result_contract"),
        "integration_resident_result_contract": pipeline.get("integration_resident_result_contract"),
        "integration_dq_map_pixels_match_summary": pipeline.get(
            "integration_dq_map_pixels_match_summary"
        ),
        "integration_coverage_map_pixels_match_dq": pipeline.get(
            "integration_coverage_map_pixels_match_dq"
        ),
        "integration_rejection_map_pixels_match_dq": pipeline.get(
            "integration_rejection_map_pixels_match_dq"
        ),
        "integration_rejection_sample_counts_match_maps": pipeline.get(
            "integration_rejection_sample_counts_match_maps"
        ),
        "integration_sample_accounting_closure": pipeline.get(
            "integration_sample_accounting_closure"
        ),
        "integration_default_engine_policy": pipeline.get(
            "integration_default_engine_policy"
        ),
        "integration_engine_policy": engine_policy,
        "integration_engine_policy_status": pipeline.get(
            "integration_engine_policy_status", engine_policy.get("status")
        ),
        "integration_engine_policy_check_present": pipeline.get(
            "integration_engine_policy_check_present",
            engine_policy.get("check_present"),
        ),
        "integration_engine_policy_check_passed": pipeline.get(
            "integration_engine_policy_check_passed",
            engine_policy.get("check_passed"),
        ),
        "integration_engine_policy_non_resident_count": pipeline.get(
            "integration_engine_policy_non_resident_count",
            engine_policy.get("non_resident_count"),
        ),
        "integration_engine_policy_failed_count": pipeline.get(
            "integration_engine_policy_failed_count",
            engine_policy.get("failed_count"),
        ),
        "rejection_sample_accounting": pipeline.get("rejection_sample_accounting")
        if isinstance(pipeline.get("rejection_sample_accounting"), dict)
        else {},
        "rejection_sample_accounting_status": pipeline.get("rejection_sample_accounting_status"),
        "rejection_sample_accounting_failed_count": pipeline.get(
            "rejection_sample_accounting_failed_count"
        ),
        "sample_accounting_closure": pipeline.get("sample_accounting_closure")
        if isinstance(pipeline.get("sample_accounting_closure"), dict)
        else {},
        "sample_accounting_closure_status": pipeline.get("sample_accounting_closure_status"),
        "sample_accounting_closure_present_count": pipeline.get(
            "sample_accounting_closure_present_count"
        ),
        "sample_accounting_closure_failed_count": pipeline.get(
            "sample_accounting_closure_failed_count"
        ),
        "pixel_verification_enabled": pipeline.get("pixel_verification_enabled"),
        "pixel_verification_tile_size": pipeline.get("pixel_verification_tile_size"),
        "resident_native_calibration_artifact": pipeline.get("resident_native_calibration_artifact"),
        "resident_calibrated_light_count": pipeline.get("resident_calibrated_light_count"),
        "calibrated_light_count": pipeline.get("calibrated_light_count"),
    }


def _phase2_check_passed(phase2: dict[str, Any], name: str) -> bool | None:
    checks = phase2.get("checks") if isinstance(phase2.get("checks"), list) else []
    for item in checks:
        if isinstance(item, dict) and item.get("name") == name:
            return item.get("passed") is True
    return None


def _stack_engine_summary(phase2: dict[str, Any]) -> dict[str, Any]:
    contract = (
        phase2.get("stack_engine_contract")
        if isinstance(phase2.get("stack_engine_contract"), dict)
        else {}
    )
    phase2_check = _phase2_check_passed(phase2, "stack_engine_default_contract_ready")
    gap_count = contract.get("default_promotion_phase2_stack_engine_default_gap_count")
    if gap_count is None:
        gap_count = contract.get("adoption_phase2_stack_engine_default_gap_count")
    blocker_count = contract.get("default_promotion_blocker_count")
    blockers = (
        contract.get("default_promotion_blockers")
        if isinstance(contract.get("default_promotion_blockers"), list)
        else []
    )
    ready = (
        bool(contract)
        and contract.get("audit_type") == "stack_engine_default_contract"
        and contract.get("status") == "passed"
        and contract.get("passed") is True
        and contract.get("default_promotion_ready") is True
        and contract.get("default_promotion_status") == "ready"
        and contract.get("adoption_recommendation") == "stack_engine_default_ready"
        and contract.get("default_promotion_recommendation") == "stack_engine_default_ready"
        and _int_value(gap_count) == 0
        and _int_value(blocker_count) == 0
        and phase2_check is True
    )
    return {
        "present": bool(contract),
        "ready": ready,
        "phase2_check_passed": phase2_check,
        "path": contract.get("path"),
        "audit_type": contract.get("audit_type"),
        "status": contract.get("status"),
        "passed": contract.get("passed"),
        "scope": contract.get("scope"),
        "expected_integration_engine": contract.get("expected_integration_engine"),
        "adoption_recommendation": contract.get("adoption_recommendation"),
        "adoption_surface_count": contract.get("adoption_surface_count"),
        "adoption_contract_ready_count": contract.get("adoption_contract_ready_count"),
        "adoption_stack_engine_surface_count": contract.get(
            "adoption_stack_engine_surface_count"
        ),
        "adoption_cuda_resident_surface_count": contract.get(
            "adoption_cuda_resident_surface_count"
        ),
        "adoption_phase2_stack_engine_default_gap_count": contract.get(
            "adoption_phase2_stack_engine_default_gap_count"
        ),
        "adoption_gap_surfaces": contract.get("adoption_gap_surfaces") or [],
        "default_promotion_ready": contract.get("default_promotion_ready"),
        "default_promotion_status": contract.get("default_promotion_status"),
        "default_promotion_recommendation": contract.get(
            "default_promotion_recommendation"
        ),
        "default_promotion_phase2_stack_engine_default_gap_count": gap_count,
        "default_promotion_blocker_count": blocker_count,
        "default_promotion_blockers": blockers,
    }


def _default_route_acceptance_summary(phase2: dict[str, Any]) -> dict[str, Any]:
    default_route = (
        phase2.get("default_route_acceptance")
        if isinstance(phase2.get("default_route_acceptance"), dict)
        else {}
    )
    return {
        "present": bool(default_route),
        "path": default_route.get("path"),
        "status": default_route.get("status"),
        "passed": default_route.get("passed"),
        "acceptance_passed": default_route.get("acceptance_passed"),
        "benchmark_contract": default_route.get("benchmark_contract"),
        "speedup_vs_reference": _number(default_route.get("speedup_vs_reference")),
        "active_frames": _int_value(default_route.get("active_frames")),
        "route_contract_passed": default_route.get("route_contract_passed"),
        "route_check_count": _int_value(default_route.get("route_check_count")),
        "route_failed_checks": default_route.get("route_failed_checks") or [],
    }


def _resident_winsorized_sweep_summary(phase2: dict[str, Any]) -> dict[str, Any]:
    sweep = (
        phase2.get("resident_winsorized_sweep_audit")
        if isinstance(phase2.get("resident_winsorized_sweep_audit"), dict)
        else {}
    )
    return {
        "present": bool(sweep),
        "path": sweep.get("path"),
        "status": sweep.get("status"),
        "passed": sweep.get("passed"),
        "phase2_check_passed": _phase2_check_passed(
            phase2,
            "resident_winsorized_sweep_audit_passed",
        ),
        "contract_name": sweep.get("contract_name"),
        "sweep_path": sweep.get("sweep_path"),
        "check_count": _int_value(sweep.get("check_count")),
        "failed_check_count": _int_value(sweep.get("failed_check_count")),
        "failed_checks": sweep.get("failed_checks") or [],
        "frame_counts": sweep.get("frame_counts") or [],
        "run_count": _int_value(sweep.get("run_count")),
        "required_frame_count": _int_value(sweep.get("required_frame_count")),
        "required_frame_count_passed": sweep.get("required_frame_count_passed"),
        "required_frame_master_rms": _number(sweep.get("required_frame_master_rms")),
        "required_frame_master_max_abs": _number(
            sweep.get("required_frame_master_max_abs")
        ),
        "max_hardened_master_rms": _number(sweep.get("max_hardened_master_rms")),
        "required_frame_cuda_hardened_s": _number(
            sweep.get("required_frame_cuda_hardened_s")
        ),
    }


def _publication_audit_summary(phase2: dict[str, Any]) -> dict[str, Any]:
    audit = (
        phase2.get("stack_engine_publication_audit")
        if isinstance(phase2.get("stack_engine_publication_audit"), dict)
        else {}
    )
    policy_layer = (
        audit.get("publish_preflight_integration_engine_policy")
        if isinstance(audit.get("publish_preflight_integration_engine_policy"), dict)
        else {}
    )
    phase2_policy_layer = (
        audit.get("phase2_publish_preflight_integration_engine_policy")
        if isinstance(
            audit.get("phase2_publish_preflight_integration_engine_policy"),
            dict,
        )
        else {}
    )
    winsorized_layer = (
        audit.get("publish_preflight_resident_winsorized_sweep")
        if isinstance(audit.get("publish_preflight_resident_winsorized_sweep"), dict)
        else {}
    )
    phase2_winsorized_layer = (
        audit.get("phase2_publish_preflight_resident_winsorized_sweep")
        if isinstance(
            audit.get("phase2_publish_preflight_resident_winsorized_sweep"),
            dict,
        )
        else {}
    )
    passed_check = _phase2_check_passed(phase2, "stack_engine_publication_audit_passed")
    policy_check = _phase2_check_passed(
        phase2,
        "stack_engine_publication_audit_policy_chain_passed",
    )
    winsorized_check = _phase2_check_passed(
        phase2,
        "stack_engine_publication_audit_resident_winsorized_chain_passed",
    )
    ready = (
        bool(audit)
        and audit.get("status") == "passed"
        and audit.get("passed") is True
        and passed_check is True
        and policy_check is True
        and winsorized_check is True
        and audit.get("publish_preflight_integration_engine_policy_ready") is True
        and audit.get("phase2_publish_preflight_integration_engine_policy_ready")
        is True
        and audit.get(
            "phase2_publish_preflight_integration_engine_policy_matches_publish_preflight"
        )
        is True
        and audit.get("publish_preflight_resident_winsorized_sweep_ready") is True
        and audit.get("phase2_publish_preflight_resident_winsorized_sweep_ready")
        is True
        and audit.get(
            "phase2_publish_preflight_resident_winsorized_matches_publish_preflight"
        )
        is True
    )
    return {
        "present": bool(audit),
        "ready": ready,
        "path": audit.get("path"),
        "status": audit.get("status"),
        "passed": audit.get("passed"),
        "recommendation": audit.get("recommendation"),
        "check_count": _int_value(audit.get("check_count")),
        "failed_check_count": _int_value(audit.get("failed_check_count")),
        "failed_checks": audit.get("failed_checks") or [],
        "phase2_audit_check_passed": passed_check,
        "policy_chain_phase2_check_passed": policy_check,
        "resident_winsorized_chain_phase2_check_passed": winsorized_check,
        "publish_preflight_policy_layer": policy_layer,
        "phase2_policy_layer": phase2_policy_layer,
        "publish_preflight_policy_ready": audit.get(
            "publish_preflight_integration_engine_policy_ready"
        ),
        "phase2_policy_ready": audit.get(
            "phase2_publish_preflight_integration_engine_policy_ready"
        ),
        "policy_agreement": audit.get(
            "phase2_publish_preflight_integration_engine_policy_matches_publish_preflight"
        ),
        "publish_preflight_resident_winsorized_layer": winsorized_layer,
        "phase2_resident_winsorized_layer": phase2_winsorized_layer,
        "publish_preflight_resident_winsorized_ready": audit.get(
            "publish_preflight_resident_winsorized_sweep_ready"
        ),
        "phase2_resident_winsorized_ready": audit.get(
            "phase2_publish_preflight_resident_winsorized_sweep_ready"
        ),
        "resident_winsorized_agreement": audit.get(
            "phase2_publish_preflight_resident_winsorized_matches_publish_preflight"
        ),
    }


def _integration_engine_policy_summary(
    phase2: dict[str, Any],
    pipeline: dict[str, Any],
) -> dict[str, Any]:
    acceptance = (
        phase2.get("acceptance_audit")
        if isinstance(phase2.get("acceptance_audit"), dict)
        else {}
    )
    acceptance_policy = (
        acceptance.get("pipeline_integration_engine_policy")
        if isinstance(acceptance.get("pipeline_integration_engine_policy"), dict)
        else {}
    )
    pipeline_policy = (
        pipeline.get("integration_engine_policy")
        if isinstance(pipeline.get("integration_engine_policy"), dict)
        else {}
    )
    acceptance_status = acceptance.get(
        "pipeline_integration_engine_policy_status",
        acceptance_policy.get("status"),
    )
    acceptance_check_present = acceptance.get(
        "pipeline_integration_engine_policy_check_present",
        acceptance_policy.get("check_present"),
    )
    acceptance_check_passed = acceptance.get(
        "pipeline_integration_engine_policy_check_passed",
        acceptance_policy.get("check_passed"),
    )
    pipeline_status = pipeline.get(
        "integration_engine_policy_status",
        pipeline_policy.get("status"),
    )
    pipeline_check_present = pipeline.get(
        "integration_engine_policy_check_present",
        pipeline_policy.get("check_present"),
    )
    pipeline_check_passed = pipeline.get(
        "integration_engine_policy_check_passed",
        pipeline_policy.get("check_passed"),
    )
    acceptance_phase2_check = _phase2_check_passed(
        phase2,
        "acceptance_pipeline_integration_engine_policy_passed",
    )
    pipeline_phase2_check = _phase2_check_passed(
        phase2,
        "pipeline_integration_engine_policy_passed",
    )
    ready = (
        acceptance_status == "passed"
        and acceptance_check_present is True
        and acceptance_check_passed is True
        and acceptance_phase2_check is True
        and pipeline_status == "passed"
        and pipeline_check_present is True
        and pipeline_check_passed is True
        and pipeline_phase2_check is True
    )
    return {
        "present": bool(acceptance_policy or pipeline_policy),
        "ready": ready,
        "acceptance_status": acceptance_status,
        "acceptance_check_present": acceptance_check_present,
        "acceptance_check_passed": acceptance_check_passed,
        "acceptance_phase2_check_passed": acceptance_phase2_check,
        "acceptance_non_resident_count": acceptance.get(
            "pipeline_integration_engine_policy_non_resident_count",
            acceptance_policy.get("non_resident_count"),
        ),
        "acceptance_failed_count": acceptance.get(
            "pipeline_integration_engine_policy_failed_count",
            acceptance_policy.get("failed_count"),
        ),
        "acceptance_failed_items": acceptance_policy.get("failed_items") or [],
        "pipeline_status": pipeline_status,
        "pipeline_check_present": pipeline_check_present,
        "pipeline_check_passed": pipeline_check_passed,
        "pipeline_phase2_check_passed": pipeline_phase2_check,
        "pipeline_default_engine_policy": pipeline.get(
            "integration_default_engine_policy"
        ),
        "pipeline_non_resident_count": pipeline.get(
            "integration_engine_policy_non_resident_count",
            pipeline_policy.get("non_resident_count"),
        ),
        "pipeline_failed_count": pipeline.get(
            "integration_engine_policy_failed_count",
            pipeline_policy.get("failed_count"),
        ),
        "pipeline_failed_items": pipeline_policy.get("failed_items") or [],
    }


def build_default_promotion_manifest(
    *,
    release_decision_json: str | Path,
    phase2_status_json: str | Path,
    doctor_json: str | Path | None = None,
    default_memory_mode: str = "resident",
    fallback_memory_mode: str = "tile",
    default_runtime_preset: str = "throughput-v1",
    integration_engine: str = "cuda_resident_stack",
    min_runtime_runs: int = 2,
    max_runtime_ratio: float = 1.25,
    min_resident_lights: int = 200,
    min_resident_winsorized_sweep_checks: int = 27,
    required_resident_winsorized_sweep_frame_count: int = 200,
    require_doctor: bool = False,
) -> dict[str, Any]:
    decision = _read_json_object(release_decision_json)
    phase2 = _read_json_object(phase2_status_json)
    doctor = _read_json_object_optional(doctor_json)
    runtime = _runtime_repeat_summary(decision)
    pipeline = _pipeline_summary(phase2)
    stack_engine = _stack_engine_summary(phase2)
    default_route = _default_route_acceptance_summary(phase2)
    resident_winsorized_sweep = _resident_winsorized_sweep_summary(phase2)
    publication_audit = _publication_audit_summary(phase2)
    integration_engine_policy = _integration_engine_policy_summary(phase2, pipeline)
    doctor_info = _doctor_summary(doctor)
    phase2_decision = (
        phase2.get("release_decision") if isinstance(phase2.get("release_decision"), dict) else {}
    )
    latest_checkpoint = (
        phase2.get("latest_checkpoint")
        if isinstance(phase2.get("latest_checkpoint"), dict)
        else {}
    )
    ordered_try_list = doctor_info.get("ordered_try_list") or []
    runtime_ratio = runtime.get("elapsed_ratio_vs_best")
    considered_runs = runtime.get("considered_run_count")
    resident_light_count = _int_value(pipeline.get("resident_calibrated_light_count"))
    if resident_light_count is None:
        resident_light_count = _int_value(pipeline.get("calibrated_light_count"))

    checks = [
        _check(
            "release_decision_artifact_type",
            _artifact_type(decision) == "release_promotion_decision",
            {"actual": _artifact_type(decision), "required": "release_promotion_decision"},
        ),
        _check(
            "phase2_status_artifact_type",
            _artifact_type(phase2) == "glass_phase2_status",
            {"actual": _artifact_type(phase2), "required": "glass_phase2_status"},
        ),
        _check(
            "phase2_status_green",
            phase2.get("status") == "green" and phase2.get("passed") is True,
            {"status": phase2.get("status"), "passed": phase2.get("passed")},
        ),
        _check(
            "latest_checkpoint_green",
            latest_checkpoint.get("green") is True,
            {
                "gate": latest_checkpoint.get("gate"),
                "status": latest_checkpoint.get("status"),
                "green": latest_checkpoint.get("green"),
            },
        ),
        _check(
            "release_decision_default_change_ready",
            decision.get("default_change_ready") is True,
            {"actual": decision.get("default_change_ready"), "status": decision.get("status")},
        ),
        _check(
            "release_decision_recommends_promotion",
            decision.get("recommendation") == "promote_default_candidate",
            {"actual": decision.get("recommendation"), "required": "promote_default_candidate"},
        ),
        _check(
            "phase2_embeds_same_release_decision",
            _same_artifact_name(release_decision_json, phase2_decision.get("path")),
            {
                "input": str(release_decision_json),
                "phase2_release_decision_path": phase2_decision.get("path"),
            },
        ),
        _check(
            "phase2_release_decision_default_change_ready",
            phase2_decision.get("default_change_ready") is True,
            {"actual": phase2_decision.get("default_change_ready")},
        ),
        _check(
            "phase2_release_decision_recommends_promotion",
            phase2_decision.get("recommendation") == "promote_default_candidate",
            {
                "actual": phase2_decision.get("recommendation"),
                "required": "promote_default_candidate",
            },
        ),
        _check(
            "default_route_acceptance_present",
            default_route.get("present") is True,
            {"path": default_route.get("path"), "status": default_route.get("status")},
        ),
        _check(
            "default_route_acceptance_passed",
            default_route.get("passed") is True,
            {
                "status": default_route.get("status"),
                "passed": default_route.get("passed"),
                "acceptance_passed": default_route.get("acceptance_passed"),
            },
        ),
        _check(
            "default_route_acceptance_route_contract_passed",
            default_route.get("route_contract_passed") is True,
            {
                "route_contract_passed": default_route.get("route_contract_passed"),
                "route_failed_checks": default_route.get("route_failed_checks"),
            },
        ),
        _check(
            "default_route_acceptance_route_check_count",
            (default_route.get("route_check_count") or 0) >= 4,
            {"actual": default_route.get("route_check_count"), "required_min": 4},
        ),
        _check(
            "runtime_repeat_present",
            runtime.get("present") is True,
            {"present": runtime.get("present"), "recommendation": runtime.get("recommendation")},
        ),
        _check(
            "runtime_repeat_count",
            considered_runs is not None and considered_runs >= int(min_runtime_runs),
            {"actual": considered_runs, "required_min": int(min_runtime_runs)},
        ),
        _check(
            "runtime_repeat_ratio_within_bound",
            runtime_ratio is not None and runtime_ratio <= float(max_runtime_ratio),
            {"actual": runtime_ratio, "required_max": float(max_runtime_ratio)},
        ),
        _check(
            "pipeline_contract_passed",
            pipeline.get("passed") is True and pipeline.get("status") == "passed",
            {"status": pipeline.get("status"), "passed": pipeline.get("passed")},
        ),
        _check(
            "pipeline_dq_contract_passed",
            pipeline.get("integration_dq_contract") is True,
            {"actual": pipeline.get("integration_dq_contract")},
        ),
        _check(
            "pipeline_stack_and_resident_result_contracts_passed",
            pipeline.get("integration_stack_result_contract") is True
            and pipeline.get("integration_resident_result_contract") is True,
            {
                "stack": pipeline.get("integration_stack_result_contract"),
                "resident": pipeline.get("integration_resident_result_contract"),
            },
        ),
        _check(
            "pipeline_pixel_verification_enabled",
            pipeline.get("pixel_verification_enabled") is True,
            {
                "enabled": pipeline.get("pixel_verification_enabled"),
                "tile_size": pipeline.get("pixel_verification_tile_size"),
            },
        ),
        _check(
            "pipeline_pixel_maps_match_dq",
            pipeline.get("integration_dq_map_pixels_match_summary") is True
            and pipeline.get("integration_coverage_map_pixels_match_dq") is True
            and pipeline.get("integration_rejection_map_pixels_match_dq") is True,
            {
                "dq": pipeline.get("integration_dq_map_pixels_match_summary"),
                "coverage": pipeline.get("integration_coverage_map_pixels_match_dq"),
                "rejection": pipeline.get("integration_rejection_map_pixels_match_dq"),
            },
        ),
        _check(
            "pipeline_rejection_sample_accounting_passed",
            pipeline.get("integration_rejection_sample_counts_match_maps") is True
            and pipeline.get("rejection_sample_accounting_status") == "passed",
            {
                "check": pipeline.get("integration_rejection_sample_counts_match_maps"),
                "status": pipeline.get("rejection_sample_accounting_status"),
                "failed_count": pipeline.get("rejection_sample_accounting_failed_count"),
                "failed_items": (pipeline.get("rejection_sample_accounting") or {}).get(
                    "failed_items"
                ),
            },
        ),
        _check(
            "pipeline_sample_accounting_closure_passed",
            pipeline.get("integration_sample_accounting_closure") is True
            and pipeline.get("sample_accounting_closure_status") == "passed",
            {
                "check": pipeline.get("integration_sample_accounting_closure"),
                "status": pipeline.get("sample_accounting_closure_status"),
                "present_count": pipeline.get("sample_accounting_closure_present_count"),
                "failed_count": pipeline.get("sample_accounting_closure_failed_count"),
                "failed_items": (pipeline.get("sample_accounting_closure") or {}).get(
                    "failed_items"
                ),
            },
        ),
        _check(
            "acceptance_integration_engine_policy_handoff_passed",
            integration_engine_policy.get("acceptance_status") == "passed"
            and integration_engine_policy.get("acceptance_check_present") is True
            and integration_engine_policy.get("acceptance_check_passed") is True
            and integration_engine_policy.get("acceptance_phase2_check_passed") is True,
            {
                "status": integration_engine_policy.get("acceptance_status"),
                "check_present": integration_engine_policy.get(
                    "acceptance_check_present"
                ),
                "check_passed": integration_engine_policy.get(
                    "acceptance_check_passed"
                ),
                "phase2_check_passed": integration_engine_policy.get(
                    "acceptance_phase2_check_passed"
                ),
                "non_resident_count": integration_engine_policy.get(
                    "acceptance_non_resident_count"
                ),
                "failed_count": integration_engine_policy.get(
                    "acceptance_failed_count"
                ),
                "failed_items": integration_engine_policy.get(
                    "acceptance_failed_items"
                ),
            },
        ),
        _check(
            "pipeline_integration_engine_policy_default_passed",
            integration_engine_policy.get("pipeline_status") == "passed"
            and integration_engine_policy.get("pipeline_check_present") is True
            and integration_engine_policy.get("pipeline_check_passed") is True
            and integration_engine_policy.get("pipeline_phase2_check_passed") is True,
            {
                "status": integration_engine_policy.get("pipeline_status"),
                "check_present": integration_engine_policy.get(
                    "pipeline_check_present"
                ),
                "check_passed": integration_engine_policy.get(
                    "pipeline_check_passed"
                ),
                "phase2_check_passed": integration_engine_policy.get(
                    "pipeline_phase2_check_passed"
                ),
                "default_engine_policy": integration_engine_policy.get(
                    "pipeline_default_engine_policy"
                ),
                "non_resident_count": integration_engine_policy.get(
                    "pipeline_non_resident_count"
                ),
                "failed_count": integration_engine_policy.get(
                    "pipeline_failed_count"
                ),
                "failed_items": integration_engine_policy.get(
                    "pipeline_failed_items"
                ),
            },
        ),
        _check(
            "phase2_stack_engine_default_contract_ready",
            stack_engine.get("ready") is True,
            {
                "present": stack_engine.get("present"),
                "phase2_check_passed": stack_engine.get("phase2_check_passed"),
                "status": stack_engine.get("status"),
                "passed": stack_engine.get("passed"),
                "scope": stack_engine.get("scope"),
                "expected_integration_engine": stack_engine.get(
                    "expected_integration_engine"
                ),
                "adoption_recommendation": stack_engine.get("adoption_recommendation"),
                "adoption_gap_count": stack_engine.get(
                    "adoption_phase2_stack_engine_default_gap_count"
                ),
                "default_promotion_ready": stack_engine.get(
                    "default_promotion_ready"
                ),
                "default_promotion_status": stack_engine.get(
                    "default_promotion_status"
                ),
                "default_promotion_blocker_count": stack_engine.get(
                    "default_promotion_blocker_count"
                ),
                "default_promotion_blockers": stack_engine.get(
                    "default_promotion_blockers"
                ),
            },
        ),
        _check(
            "resident_calibration_artifact_present",
            pipeline.get("resident_native_calibration_artifact") is True,
            {"actual": pipeline.get("resident_native_calibration_artifact")},
        ),
        _check(
            "resident_light_count",
            resident_light_count is not None and resident_light_count >= int(min_resident_lights),
            {"actual": resident_light_count, "required_min": int(min_resident_lights)},
        ),
        _check(
            "resident_winsorized_sweep_audit_passed",
            resident_winsorized_sweep.get("present") is True
            and resident_winsorized_sweep.get("passed") is True
            and resident_winsorized_sweep.get("status") == "passed"
            and resident_winsorized_sweep.get("phase2_check_passed") is True,
            {
                "present": resident_winsorized_sweep.get("present"),
                "status": resident_winsorized_sweep.get("status"),
                "passed": resident_winsorized_sweep.get("passed"),
                "phase2_check_passed": resident_winsorized_sweep.get(
                    "phase2_check_passed"
                ),
                "failed_checks": resident_winsorized_sweep.get("failed_checks"),
            },
        ),
        _check(
            "resident_winsorized_sweep_required_frame_passed",
            resident_winsorized_sweep.get("required_frame_count")
            == int(required_resident_winsorized_sweep_frame_count)
            and resident_winsorized_sweep.get("required_frame_count_passed") is True,
            {
                "actual_frame_count": resident_winsorized_sweep.get(
                    "required_frame_count"
                ),
                "required_frame_count": int(
                    required_resident_winsorized_sweep_frame_count
                ),
                "required_frame_count_passed": resident_winsorized_sweep.get(
                    "required_frame_count_passed"
                ),
                "required_frame_master_rms": resident_winsorized_sweep.get(
                    "required_frame_master_rms"
                ),
                "required_frame_master_max_abs": resident_winsorized_sweep.get(
                    "required_frame_master_max_abs"
                ),
            },
        ),
        _check(
            "resident_winsorized_sweep_check_count",
            resident_winsorized_sweep.get("check_count") is not None
            and resident_winsorized_sweep.get("check_count")
            >= int(min_resident_winsorized_sweep_checks),
            {
                "actual": resident_winsorized_sweep.get("check_count"),
                "required_min": int(min_resident_winsorized_sweep_checks),
                "failed_check_count": resident_winsorized_sweep.get(
                    "failed_check_count"
                ),
            },
        ),
        _check(
            "stack_engine_publication_audit_passed",
            publication_audit.get("present") is True
            and publication_audit.get("status") == "passed"
            and publication_audit.get("passed") is True
            and publication_audit.get("phase2_audit_check_passed") is True,
            {
                "present": publication_audit.get("present"),
                "status": publication_audit.get("status"),
                "passed": publication_audit.get("passed"),
                "phase2_check_passed": publication_audit.get(
                    "phase2_audit_check_passed"
                ),
                "failed_checks": publication_audit.get("failed_checks"),
            },
        ),
        _check(
            "stack_engine_publication_policy_chain_passed",
            publication_audit.get("publish_preflight_policy_ready") is True
            and publication_audit.get("phase2_policy_ready") is True
            and publication_audit.get("policy_agreement") is True
            and publication_audit.get("policy_chain_phase2_check_passed") is True,
            {
                "publish_preflight_policy_ready": publication_audit.get(
                    "publish_preflight_policy_ready"
                ),
                "phase2_policy_ready": publication_audit.get("phase2_policy_ready"),
                "policy_agreement": publication_audit.get("policy_agreement"),
                "phase2_check_passed": publication_audit.get(
                    "policy_chain_phase2_check_passed"
                ),
                "publish_preflight_layer": publication_audit.get(
                    "publish_preflight_policy_layer"
                ),
                "phase2_layer": publication_audit.get("phase2_policy_layer"),
            },
        ),
        _check(
            "stack_engine_publication_resident_winsorized_chain_passed",
            publication_audit.get("publish_preflight_resident_winsorized_ready")
            is True
            and publication_audit.get("phase2_resident_winsorized_ready") is True
            and publication_audit.get("resident_winsorized_agreement") is True
            and publication_audit.get(
                "resident_winsorized_chain_phase2_check_passed"
            )
            is True,
            {
                "publish_preflight_resident_winsorized_ready": publication_audit.get(
                    "publish_preflight_resident_winsorized_ready"
                ),
                "phase2_resident_winsorized_ready": publication_audit.get(
                    "phase2_resident_winsorized_ready"
                ),
                "resident_winsorized_agreement": publication_audit.get(
                    "resident_winsorized_agreement"
                ),
                "phase2_check_passed": publication_audit.get(
                    "resident_winsorized_chain_phase2_check_passed"
                ),
                "publish_preflight_layer": publication_audit.get(
                    "publish_preflight_resident_winsorized_layer"
                ),
                "phase2_layer": publication_audit.get(
                    "phase2_resident_winsorized_layer"
                ),
            },
        ),
        _check(
            "default_memory_mode_candidate",
            default_memory_mode == "resident",
            {"actual": default_memory_mode, "required": "resident"},
        ),
        _check(
            "fallback_memory_mode_preserved",
            fallback_memory_mode == "tile",
            {"actual": fallback_memory_mode, "required": "tile"},
        ),
        _check(
            "default_runtime_preset_candidate",
            default_runtime_preset == "throughput-v1",
            {"actual": default_runtime_preset, "required": "throughput-v1"},
        ),
        _check(
            "integration_engine_candidate",
            integration_engine == "cuda_resident_stack",
            {"actual": integration_engine, "required": "cuda_resident_stack"},
        ),
        _check(
            "doctor_artifact_available",
            bool(doctor_info.get("present")) or not require_doctor,
            {"present": doctor_info.get("present"), "required": bool(require_doctor)},
        ),
    ]
    if doctor_info.get("present"):
        checks.extend(
            [
                _check(
                    "doctor_cuda_available",
                    doctor_info.get("cuda_available") is True,
                    {
                        "cuda_available": doctor_info.get("cuda_available"),
                        "native_extension_loaded": doctor_info.get("native_extension_loaded"),
                        "wrapper_importable": doctor_info.get("wrapper_importable"),
                    },
                ),
                _check(
                    "doctor_native_extension_loaded",
                    doctor_info.get("native_extension_loaded") is True,
                    {"actual": doctor_info.get("native_extension_loaded")},
                ),
                _check(
                    "windows_package_try_list_has_cpu_fallback",
                    "cpu" in ordered_try_list,
                    {"ordered_try_list": ordered_try_list},
                ),
                _check(
                    "windows_package_primary_present",
                    bool(doctor_info.get("primary_package")),
                    {"primary": doctor_info.get("primary_package")},
                ),
            ]
        )

    failed = [item for item in checks if not item.get("passed")]
    status = "default_promotion_ready" if not failed else "blocked"
    return {
        "schema_version": 1,
        "artifact_type": "default_promotion_manifest",
        "created_at": now_iso(),
        "status": status,
        "passed": not failed,
        "default_change_ready": not failed,
        "recommendation": "promote_resident_cuda_default" if not failed else "fix_default_blockers",
        "inputs": {
            "release_decision_json": str(release_decision_json),
            "phase2_status_json": str(phase2_status_json),
            "doctor_json": None if doctor_json is None else str(doctor_json),
        },
        "default_candidate": {
            "memory_mode": default_memory_mode,
            "fallback_memory_mode": fallback_memory_mode,
            "resident_runtime_preset": default_runtime_preset,
            "integration_engine": integration_engine,
            "cpu_only_install_preserved": True,
            "cuda_optional": True,
        },
        "release_decision": {
            "status": decision.get("status"),
            "passed": decision.get("passed"),
            "release_candidate_ready": decision.get("release_candidate_ready"),
            "default_change_ready": decision.get("default_change_ready"),
            "recommendation": decision.get("recommendation"),
            "speedup": decision.get("speedup"),
        },
        "phase2_status": {
            "status": phase2.get("status"),
            "passed": phase2.get("passed"),
            "latest_checkpoint": latest_checkpoint,
            "release_decision": phase2_decision,
        },
        "runtime_repeat": runtime,
        "default_route_acceptance": default_route,
        "pipeline_contract": pipeline,
        "integration_engine_policy": integration_engine_policy,
        "stack_engine_contract": stack_engine,
        "resident_winsorized_sweep_audit": resident_winsorized_sweep,
        "stack_engine_publication_audit": publication_audit,
        "doctor": doctor_info,
        "checks": checks,
        "failed_checks": [str(item.get("name")) for item in failed],
        "limitations": [
            "This manifest proves readiness for a default promotion; it does not change CLI defaults.",
            "The resident CUDA default candidate still requires the tile and CPU fallback paths to remain available.",
            "Runtime evidence is bounded by the supplied repeat artifacts and the current storage/GPU state.",
        ],
    }


def _markdown(payload: dict[str, Any]) -> str:
    default_candidate = payload.get("default_candidate") or {}
    runtime = payload.get("runtime_repeat") or {}
    default_route = payload.get("default_route_acceptance") or {}
    pipeline = payload.get("pipeline_contract") or {}
    integration_engine_policy = payload.get("integration_engine_policy") or {}
    stack_engine = payload.get("stack_engine_contract") or {}
    resident_winsorized_sweep = payload.get("resident_winsorized_sweep_audit") or {}
    publication_audit = payload.get("stack_engine_publication_audit") or {}
    doctor = payload.get("doctor") or {}
    device = doctor.get("device") if isinstance(doctor, dict) else {}
    lines = [
        "# GLASS Default Promotion Manifest",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Recommendation: `{payload.get('recommendation')}`",
        f"- Passed: `{payload.get('passed')}`",
        f"- Default memory mode candidate: `{default_candidate.get('memory_mode')}`",
        f"- Fallback memory mode: `{default_candidate.get('fallback_memory_mode')}`",
        f"- Runtime preset: `{default_candidate.get('resident_runtime_preset')}`",
        f"- Integration engine: `{default_candidate.get('integration_engine')}`",
        "",
        "## Runtime Evidence",
        "",
        f"- Runs: `{runtime.get('considered_run_count')}`",
        f"- Best: `{runtime.get('best_label')}` `{runtime.get('best_elapsed_s')}` s",
        f"- Slowest: `{runtime.get('slowest_elapsed_s')}` s",
        f"- Slowest/best ratio: `{runtime.get('elapsed_ratio_vs_best')}`",
        "",
        "## Default Route Evidence",
        "",
        f"- Present: `{default_route.get('present')}`",
        f"- Status: `{default_route.get('status')}`",
        f"- Passed: `{default_route.get('passed')}`",
        f"- Route contract passed: `{default_route.get('route_contract_passed')}`",
        f"- Route check count: `{default_route.get('route_check_count')}`",
        f"- Route failed checks: `{default_route.get('route_failed_checks')}`",
        f"- Speedup vs reference: `{default_route.get('speedup_vs_reference')}`",
        f"- Rejection sample accounting: `{pipeline.get('rejection_sample_accounting_status')}`",
        f"- Sample accounting closure: `{pipeline.get('sample_accounting_closure_status')}`",
        f"- Acceptance integration engine policy: `{integration_engine_policy.get('acceptance_status')}`",
        f"- Pipeline integration engine policy: `{integration_engine_policy.get('pipeline_status')}`",
        (
            "- Integration engine policy ready: "
            f"`{integration_engine_policy.get('ready')}`"
        ),
        "",
        "## StackEngine Default Contract",
        "",
        f"- Present: `{stack_engine.get('present')}`",
        f"- Status: `{stack_engine.get('status')}`",
        f"- Ready: `{stack_engine.get('ready')}`",
        f"- Phase2 check passed: `{stack_engine.get('phase2_check_passed')}`",
        f"- Scope: `{stack_engine.get('scope')}`",
        (
            "- Adoption recommendation: "
            f"`{stack_engine.get('adoption_recommendation')}`"
        ),
        (
            "- Default gap count: "
            f"`{stack_engine.get('default_promotion_phase2_stack_engine_default_gap_count')}`"
        ),
        (
            "- Default promotion: "
            f"`{stack_engine.get('default_promotion_status')}` "
            f"ready=`{stack_engine.get('default_promotion_ready')}` "
            f"blockers=`{stack_engine.get('default_promotion_blocker_count')}`"
        ),
        "",
        "## Resident Winsorized Sweep",
        "",
        f"- Present: `{resident_winsorized_sweep.get('present')}`",
        f"- Status: `{resident_winsorized_sweep.get('status')}`",
        f"- Passed: `{resident_winsorized_sweep.get('passed')}`",
        f"- Phase2 check passed: `{resident_winsorized_sweep.get('phase2_check_passed')}`",
        f"- Check count: `{resident_winsorized_sweep.get('check_count')}`",
        f"- Required frame count: `{resident_winsorized_sweep.get('required_frame_count')}`",
        (
            "- Required frame count passed: "
            f"`{resident_winsorized_sweep.get('required_frame_count_passed')}`"
        ),
        (
            "- Required frame master RMS: "
            f"`{resident_winsorized_sweep.get('required_frame_master_rms')}`"
        ),
        (
            "- Required frame hardened CUDA seconds: "
            f"`{resident_winsorized_sweep.get('required_frame_cuda_hardened_s')}`"
        ),
        "",
        "## StackEngine Publication Audit",
        "",
        f"- Present: `{publication_audit.get('present')}`",
        f"- Status: `{publication_audit.get('status')}`",
        f"- Passed: `{publication_audit.get('passed')}`",
        f"- Ready: `{publication_audit.get('ready')}`",
        (
            "- Phase2 audit check passed: "
            f"`{publication_audit.get('phase2_audit_check_passed')}`"
        ),
        f"- Failed checks: `{publication_audit.get('failed_checks')}`",
        (
            "- Policy chain: "
            f"raw=`{publication_audit.get('publish_preflight_policy_ready')}` "
            f"phase2=`{publication_audit.get('phase2_policy_ready')}` "
            f"agreement=`{publication_audit.get('policy_agreement')}` "
            "phase2-check="
            f"`{publication_audit.get('policy_chain_phase2_check_passed')}`"
        ),
        (
            "- Resident winsorized chain: "
            "raw="
            f"`{publication_audit.get('publish_preflight_resident_winsorized_ready')}` "
            "phase2="
            f"`{publication_audit.get('phase2_resident_winsorized_ready')}` "
            "agreement="
            f"`{publication_audit.get('resident_winsorized_agreement')}` "
            "phase2-check="
            f"`{publication_audit.get('resident_winsorized_chain_phase2_check_passed')}`"
        ),
        "",
        "## Release Machine",
        "",
        f"- Doctor present: `{doctor.get('present')}`",
        f"- CUDA available: `{doctor.get('cuda_available')}`",
        f"- Native extension loaded: `{doctor.get('native_extension_loaded')}`",
        f"- GPU: `{device.get('name') if isinstance(device, dict) else None}`",
        f"- Primary package: `{doctor.get('primary_package')}`",
        f"- Try order: `{', '.join(doctor.get('ordered_try_list') or [])}`",
        "",
        "## Checks",
        "",
    ]
    for item in payload.get("checks") or []:
        marker = "PASS" if item.get("passed") else "FAIL"
        lines.append(f"- {marker}: `{item.get('name')}` - {item.get('evidence')}")
    lines.append("")
    return "\n".join(lines)


def write_default_promotion_manifest(
    out: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(out, payload)
    if markdown is not None:
        target = Path(markdown)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(_markdown(payload), encoding="utf-8")
