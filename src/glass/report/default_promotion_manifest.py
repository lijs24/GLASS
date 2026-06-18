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


def _read_json_object_if_exists(path: str | Path | None) -> tuple[dict[str, Any], bool, str | None]:
    if path is None:
        return {}, False, None
    target = Path(str(path))
    if not target.exists():
        return {}, False, None
    try:
        return _read_json_object(target), True, None
    except (OSError, ValueError) as exc:
        return {}, True, str(exc)


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


def _path_value(value: Any) -> str | None:
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
    runtime_default = (
        pipeline.get("stack_engine_runtime_default")
        if isinstance(pipeline.get("stack_engine_runtime_default"), dict)
        else {}
    )
    resident_result = (
        pipeline.get("resident_result_contract")
        if isinstance(pipeline.get("resident_result_contract"), dict)
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
        "resident_result_contract": resident_result,
        "integration_resident_result_contract_status": pipeline.get(
            "integration_resident_result_contract_status",
            resident_result.get("status"),
        ),
        "integration_resident_result_contract_check_present": pipeline.get(
            "integration_resident_result_contract_check_present",
            resident_result.get("check_present"),
        ),
        "integration_resident_result_contract_check_passed": pipeline.get(
            "integration_resident_result_contract_check_passed",
            resident_result.get("check_passed"),
        ),
        "integration_resident_result_contract_required_count": pipeline.get(
            "integration_resident_result_contract_required_count",
            resident_result.get("required_count"),
        ),
        "integration_resident_result_contract_failed_count": pipeline.get(
            "integration_resident_result_contract_failed_count",
            resident_result.get("failed_count"),
        ),
        "integration_resident_result_contract_failed_check_count": pipeline.get(
            "integration_resident_result_contract_failed_check_count",
            resident_result.get("failed_check_count"),
        ),
        "integration_resident_result_contract_failed_checks": pipeline.get(
            "integration_resident_result_contract_failed_checks",
            resident_result.get("failed_checks") or [],
        ),
        "integration_resident_result_contract_failed_items": pipeline.get(
            "integration_resident_result_contract_failed_items",
            resident_result.get("failed_items") or [],
        ),
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
        "stack_engine_runtime_default": runtime_default,
        "stack_engine_runtime_default_status": pipeline.get(
            "stack_engine_runtime_default_status",
            runtime_default.get("status"),
        ),
        "stack_engine_runtime_default_check_present": pipeline.get(
            "stack_engine_runtime_default_check_present",
            runtime_default.get("check_present"),
        ),
        "stack_engine_runtime_default_check_passed": pipeline.get(
            "stack_engine_runtime_default_check_passed",
            runtime_default.get("check_passed"),
        ),
        "stack_engine_runtime_default_master_count": runtime_default.get(
            "master_count"
        ),
        "stack_engine_runtime_default_legacy_master_count": pipeline.get(
            "stack_engine_runtime_default_legacy_master_count",
            runtime_default.get("legacy_master_count"),
        ),
        "stack_engine_runtime_default_failed_master_count": pipeline.get(
            "stack_engine_runtime_default_failed_master_count",
            runtime_default.get("failed_master_count"),
        ),
        "stack_engine_runtime_default_failed_output_count": pipeline.get(
            "stack_engine_runtime_default_failed_output_count",
            runtime_default.get("failed_output_count"),
        ),
        "stack_engine_runtime_default_explicit_cuda_fast_path_count": pipeline.get(
            "stack_engine_runtime_default_explicit_cuda_fast_path_count",
            runtime_default.get("explicit_cuda_fast_path_count"),
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


def _decision_check_passed(decision: dict[str, Any], name: str) -> bool | None:
    checks = decision.get("checks") if isinstance(decision.get("checks"), list) else []
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


def _quality_metrics_compare_summary(phase2: dict[str, Any]) -> dict[str, Any]:
    compare = (
        phase2.get("quality_metrics_compare")
        if isinstance(phase2.get("quality_metrics_compare"), dict)
        else {}
    )
    phase2_check = _phase2_check_passed(phase2, "quality_metrics_compare_passed")
    present = bool(compare)
    ready = (
        True
        if not present
        else compare.get("passed") is True and phase2_check is True
    )
    return {
        "present": present,
        "ready": ready,
        "status": compare.get("status"),
        "passed": compare.get("passed"),
        "phase2_check_passed": phase2_check,
        "check_count": compare.get("check_count"),
        "failed_check_count": compare.get("failed_check_count"),
        "failed_checks": compare.get("failed_checks") or [],
        "baseline_metric_count": compare.get("baseline_metric_count"),
        "candidate_metric_count": compare.get("candidate_metric_count"),
        "metric_row_count": compare.get("metric_row_count"),
        "threshold_failure_count": compare.get("threshold_failure_count"),
        "threshold_failures": compare.get("threshold_failures") or [],
        "path": compare.get("path"),
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


def _resident_result_contract_summary(
    phase2: dict[str, Any],
    pipeline: dict[str, Any],
) -> dict[str, Any]:
    resident = (
        pipeline.get("resident_result_contract")
        if isinstance(pipeline.get("resident_result_contract"), dict)
        else {}
    )
    phase2_check = _phase2_check_passed(
        phase2,
        "pipeline_resident_result_contract_passed",
    )
    status = pipeline.get(
        "integration_resident_result_contract_status",
        resident.get("status"),
    )
    check_present = pipeline.get(
        "integration_resident_result_contract_check_present",
        resident.get("check_present"),
    )
    check_passed = pipeline.get(
        "integration_resident_result_contract_check_passed",
        resident.get("check_passed"),
    )
    required_count = _int_value(
        pipeline.get(
            "integration_resident_result_contract_required_count",
            resident.get("required_count"),
        )
    )
    failed_count = _int_value(
        pipeline.get(
            "integration_resident_result_contract_failed_count",
            resident.get("failed_count"),
        )
    )
    failed_check_count = _int_value(
        pipeline.get(
            "integration_resident_result_contract_failed_check_count",
            resident.get("failed_check_count"),
        )
    )
    failed_checks = pipeline.get(
        "integration_resident_result_contract_failed_checks",
        resident.get("failed_checks") or [],
    )
    if not isinstance(failed_checks, list):
        failed_checks = []
    failed_items = pipeline.get(
        "integration_resident_result_contract_failed_items",
        resident.get("failed_items") or [],
    )
    if not isinstance(failed_items, list):
        failed_items = []
    ready = (
        bool(resident)
        and pipeline.get("integration_resident_result_contract") is True
        and status == "passed"
        and check_present is True
        and check_passed is True
        and phase2_check is True
        and required_count is not None
        and required_count > 0
        and failed_count == 0
        and failed_check_count == 0
    )
    return {
        "present": bool(resident),
        "ready": ready,
        "status": status,
        "top_level_check": pipeline.get("integration_resident_result_contract"),
        "check_present": check_present,
        "check_passed": check_passed,
        "phase2_check_passed": phase2_check,
        "required_count": required_count,
        "failed_count": failed_count,
        "failed_check_count": failed_check_count,
        "failed_checks": [str(item) for item in failed_checks],
        "failed_items": failed_items,
    }


def _stack_engine_runtime_default_summary(
    phase2: dict[str, Any],
    pipeline: dict[str, Any],
) -> dict[str, Any]:
    acceptance = (
        phase2.get("acceptance_audit")
        if isinstance(phase2.get("acceptance_audit"), dict)
        else {}
    )
    acceptance_runtime = (
        acceptance.get("pipeline_stack_engine_runtime_default")
        if isinstance(acceptance.get("pipeline_stack_engine_runtime_default"), dict)
        else {}
    )
    pipeline_runtime = (
        pipeline.get("stack_engine_runtime_default")
        if isinstance(pipeline.get("stack_engine_runtime_default"), dict)
        else {}
    )
    acceptance_status = acceptance.get(
        "pipeline_stack_engine_runtime_default_status",
        acceptance_runtime.get("status"),
    )
    acceptance_check_present = acceptance.get(
        "pipeline_stack_engine_runtime_default_check_present",
        acceptance_runtime.get("check_present"),
    )
    acceptance_check_passed = acceptance.get(
        "pipeline_stack_engine_runtime_default_check_passed",
        acceptance_runtime.get("check_passed"),
    )
    acceptance_phase2_check = _phase2_check_passed(
        phase2,
        "acceptance_pipeline_stack_engine_runtime_default_passed",
    )
    pipeline_status = pipeline.get(
        "stack_engine_runtime_default_status",
        pipeline_runtime.get("status"),
    )
    pipeline_check_present = pipeline.get(
        "stack_engine_runtime_default_check_present",
        pipeline_runtime.get("check_present"),
    )
    pipeline_check_passed = pipeline.get(
        "stack_engine_runtime_default_check_passed",
        pipeline_runtime.get("check_passed"),
    )
    pipeline_phase2_check = _phase2_check_passed(
        phase2,
        "pipeline_stack_engine_runtime_default_passed",
    )
    acceptance_legacy_master_count = _int_value(
        acceptance.get(
            "pipeline_stack_engine_runtime_default_legacy_master_count",
            acceptance_runtime.get("legacy_master_count"),
        )
    )
    acceptance_failed_master_count = _int_value(
        acceptance.get(
            "pipeline_stack_engine_runtime_default_failed_master_count",
            acceptance_runtime.get("failed_master_count"),
        )
    )
    acceptance_failed_output_count = _int_value(
        acceptance.get(
            "pipeline_stack_engine_runtime_default_failed_output_count",
            acceptance_runtime.get("failed_output_count"),
        )
    )
    pipeline_legacy_master_count = _int_value(
        pipeline.get(
            "stack_engine_runtime_default_legacy_master_count",
            pipeline_runtime.get("legacy_master_count"),
        )
    )
    pipeline_failed_master_count = _int_value(
        pipeline.get(
            "stack_engine_runtime_default_failed_master_count",
            pipeline_runtime.get("failed_master_count"),
        )
    )
    pipeline_failed_output_count = _int_value(
        pipeline.get(
            "stack_engine_runtime_default_failed_output_count",
            pipeline_runtime.get("failed_output_count"),
        )
    )
    ready = (
        acceptance_status == "passed"
        and acceptance_check_present is True
        and acceptance_check_passed is True
        and acceptance_phase2_check is True
        and acceptance_legacy_master_count == 0
        and acceptance_failed_master_count == 0
        and acceptance_failed_output_count == 0
        and pipeline_status == "passed"
        and pipeline_check_present is True
        and pipeline_check_passed is True
        and pipeline_phase2_check is True
        and pipeline_legacy_master_count == 0
        and pipeline_failed_master_count == 0
        and pipeline_failed_output_count == 0
    )
    return {
        "present": bool(acceptance_runtime or pipeline_runtime),
        "ready": ready,
        "acceptance_status": acceptance_status,
        "acceptance_check_present": acceptance_check_present,
        "acceptance_check_passed": acceptance_check_passed,
        "acceptance_phase2_check_passed": acceptance_phase2_check,
        "acceptance_master_count": acceptance.get(
            "pipeline_stack_engine_runtime_default_master_count",
            acceptance_runtime.get("master_count"),
        ),
        "acceptance_legacy_master_count": acceptance_legacy_master_count,
        "acceptance_failed_master_count": acceptance_failed_master_count,
        "acceptance_failed_output_count": acceptance_failed_output_count,
        "acceptance_explicit_cuda_fast_path_count": acceptance.get(
            "pipeline_stack_engine_runtime_default_explicit_cuda_fast_path_count",
            acceptance_runtime.get("explicit_cuda_fast_path_count"),
        ),
        "acceptance_failed_masters": acceptance_runtime.get("failed_masters") or [],
        "acceptance_failed_outputs": acceptance_runtime.get("failed_outputs") or [],
        "pipeline_status": pipeline_status,
        "pipeline_check_present": pipeline_check_present,
        "pipeline_check_passed": pipeline_check_passed,
        "pipeline_phase2_check_passed": pipeline_phase2_check,
        "pipeline_master_count": pipeline.get(
            "stack_engine_runtime_default_master_count",
            pipeline_runtime.get("master_count"),
        ),
        "pipeline_legacy_master_count": pipeline_legacy_master_count,
        "pipeline_failed_master_count": pipeline_failed_master_count,
        "pipeline_failed_output_count": pipeline_failed_output_count,
        "pipeline_explicit_cuda_fast_path_count": pipeline.get(
            "stack_engine_runtime_default_explicit_cuda_fast_path_count",
            pipeline_runtime.get("explicit_cuda_fast_path_count"),
        ),
        "pipeline_failed_masters": pipeline_runtime.get("failed_masters") or [],
        "pipeline_failed_outputs": pipeline_runtime.get("failed_outputs") or [],
    }


def _check_prefix_summary(payload: dict[str, Any], prefix: str) -> dict[str, Any]:
    rows = [
        row
        for row in payload.get("checks") or []
        if isinstance(row, dict) and str(row.get("name", "")).startswith(prefix)
    ]
    failed = [str(row.get("name")) for row in rows if row.get("passed") is not True]
    return {
        "check_count": len(rows),
        "failed_check_count": len(failed),
        "failed_checks": failed,
        "passed": bool(rows) and not failed,
    }


def _runtime_default_direct_evidence_summary(
    decision: dict[str, Any],
    phase2: dict[str, Any],
) -> dict[str, Any]:
    decision_inputs = decision.get("inputs") if isinstance(decision.get("inputs"), dict) else {}
    phase2_pipeline = (
        phase2.get("pipeline_contract")
        if isinstance(phase2.get("pipeline_contract"), dict)
        else {}
    )
    acceptance_path = _path_value(decision_inputs.get("acceptance_audit"))
    pipeline_path = _path_value(decision_inputs.get("pipeline_contract") or phase2_pipeline.get("path"))
    acceptance_payload, acceptance_exists, acceptance_read_error = _read_json_object_if_exists(
        acceptance_path
    )
    pipeline_payload, pipeline_exists, pipeline_read_error = _read_json_object_if_exists(
        pipeline_path
    )
    fastpath = (
        acceptance_payload.get("resident_registration_fastpath")
        if isinstance(acceptance_payload.get("resident_registration_fastpath"), dict)
        else {}
    )
    fastpath_checks = _check_prefix_summary(
        acceptance_payload,
        "contract_resident_registration_fastpath",
    )
    pipeline_artifacts = (
        pipeline_payload.get("artifacts")
        if isinstance(pipeline_payload.get("artifacts"), dict)
        else {}
    )
    calibration_artifact = (
        pipeline_artifacts.get("calibration")
        if isinstance(pipeline_artifacts.get("calibration"), dict)
        else {}
    )
    pipeline_calibration = (
        pipeline_payload.get("calibration")
        if isinstance(pipeline_payload.get("calibration"), dict)
        else {}
    )
    resident_light_count = _int_value(
        pipeline_calibration.get(
            "calibrated_light_count",
            phase2_pipeline.get("resident_calibrated_light_count"),
        )
    )
    resident_native_calibration_artifact = (
        phase2_pipeline.get("resident_native_calibration_artifact")
        if phase2_pipeline.get("resident_native_calibration_artifact") is not None
        else any(
            isinstance(row, dict) and row.get("resident") is True
            for row in pipeline_calibration.get("calibrated_lights") or []
        )
    )
    acceptance_direct = (
        acceptance_exists
        and acceptance_read_error is None
        and fastpath.get("source") == "explicit_resident_artifacts_json"
        and fastpath.get("available") is True
        and fastpath.get("exists") is True
        and fastpath_checks.get("passed") is True
    )
    pipeline_direct = (
        pipeline_exists
        and pipeline_read_error is None
        and calibration_artifact.get("source") == "resident_artifacts_json_fallback"
        and calibration_artifact.get("exists") is True
        and calibration_artifact.get("generated_for_pipeline_contract") is True
        and calibration_artifact.get("path_exists") is False
        and resident_native_calibration_artifact is True
        and resident_light_count is not None
        and resident_light_count > 0
    )
    return {
        "present": bool(acceptance_path or pipeline_path),
        "ready": acceptance_direct and pipeline_direct,
        "decision_inputs_present": bool(decision_inputs),
        "acceptance_audit_path": acceptance_path,
        "acceptance_audit_exists": acceptance_exists,
        "acceptance_audit_read_error": acceptance_read_error,
        "acceptance_fastpath_source": fastpath.get("source"),
        "acceptance_fastpath_artifact_path": fastpath.get("path"),
        "acceptance_fastpath_available": fastpath.get("available"),
        "acceptance_fastpath_exists": fastpath.get("exists"),
        "acceptance_fastpath_check_count": fastpath_checks.get("check_count"),
        "acceptance_fastpath_failed_check_count": fastpath_checks.get(
            "failed_check_count"
        ),
        "acceptance_fastpath_failed_checks": fastpath_checks.get("failed_checks"),
        "acceptance_direct_fastpath": acceptance_direct,
        "pipeline_contract_path": pipeline_path,
        "pipeline_contract_exists": pipeline_exists,
        "pipeline_contract_read_error": pipeline_read_error,
        "pipeline_calibration_artifact_source": calibration_artifact.get("source"),
        "pipeline_calibration_artifact_exists": calibration_artifact.get("exists"),
        "pipeline_calibration_artifact_generated_for_contract": (
            calibration_artifact.get("generated_for_pipeline_contract")
        ),
        "pipeline_calibration_artifact_path_exists": calibration_artifact.get(
            "path_exists"
        ),
        "pipeline_calibration_artifact_path": calibration_artifact.get("path"),
        "pipeline_resident_native_calibration_artifact": (
            resident_native_calibration_artifact
        ),
        "pipeline_resident_calibrated_light_count": resident_light_count,
        "pipeline_direct_resident_calibration": pipeline_direct,
    }


def _resident_registration_fastpath_release_handoff_summary(
    decision: dict[str, Any],
    phase2: dict[str, Any],
) -> dict[str, Any]:
    raw = (
        decision.get("resident_registration_fastpath_handoff")
        if isinstance(decision.get("resident_registration_fastpath_handoff"), dict)
        else {}
    )
    phase2_decision = (
        phase2.get("release_decision")
        if isinstance(phase2.get("release_decision"), dict)
        else {}
    )
    phase2_handoff = (
        phase2_decision.get("resident_registration_fastpath_handoff")
        if isinstance(
            phase2_decision.get("resident_registration_fastpath_handoff"),
            dict,
        )
        else {}
    )
    raw_check = _decision_check_passed(
        decision, "resident_registration_fastpath_handoff"
    )
    phase2_check = _phase2_check_passed(
        phase2, "release_decision_resident_fastpath_handoff_ready"
    )
    raw_failed_count = _int_value(raw.get("failed_check_count"))
    phase2_failed_count = _int_value(phase2_handoff.get("failed_check_count"))
    raw_ready = (
        bool(raw)
        and raw.get("status") == "passed"
        and raw.get("ready") is True
        and raw.get("required_by_benchmark_contract") is True
        and raw_check is True
        and raw_failed_count == 0
    )
    phase2_ready = (
        bool(phase2_handoff)
        and phase2_handoff.get("status") == "passed"
        and phase2_handoff.get("ready") is True
        and phase2_handoff.get("required_by_benchmark_contract") is True
        and phase2_check is True
        and phase2_failed_count == 0
    )
    agreement = (
        raw.get("status") == phase2_handoff.get("status")
        and raw.get("ready") == phase2_handoff.get("ready")
        and raw.get("required_by_benchmark_contract")
        == phase2_handoff.get("required_by_benchmark_contract")
        and raw.get("resident_registration_mode")
        == phase2_handoff.get("resident_registration_mode")
        and raw.get("passed_check_count") == phase2_handoff.get("passed_check_count")
        and raw_failed_count == phase2_failed_count
    )
    return {
        "present": bool(raw) or bool(phase2_handoff),
        "ready": raw_ready and phase2_ready and agreement,
        "raw_ready": raw_ready,
        "phase2_ready": phase2_ready,
        "agreement": agreement,
        "decision_check_passed": raw_check,
        "phase2_check_passed": phase2_check,
        "raw_status": raw.get("status"),
        "phase2_status": phase2_handoff.get("status"),
        "raw_required": raw.get("required_by_benchmark_contract"),
        "phase2_required": phase2_handoff.get("required_by_benchmark_contract"),
        "raw_source": raw.get("source"),
        "phase2_source": phase2_handoff.get("source"),
        "raw_path": raw.get("path"),
        "phase2_path": phase2_handoff.get("path"),
        "raw_mode": raw.get("resident_registration_mode"),
        "phase2_mode": phase2_handoff.get("resident_registration_mode"),
        "raw_descriptor_fit_batch_mode": raw.get("descriptor_fit_batch_mode"),
        "phase2_descriptor_fit_batch_mode": phase2_handoff.get(
            "descriptor_fit_batch_mode"
        ),
        "raw_pixel_refine_batch_mode": raw.get("pixel_refine_batch_mode"),
        "phase2_pixel_refine_batch_mode": phase2_handoff.get(
            "pixel_refine_batch_mode"
        ),
        "raw_triangle_warp_batch_mode": raw.get("triangle_warp_batch_mode"),
        "phase2_triangle_warp_batch_mode": phase2_handoff.get(
            "triangle_warp_batch_mode"
        ),
        "raw_triangle_warp_batch_frame_count": raw.get(
            "triangle_warp_batch_frame_count"
        ),
        "phase2_triangle_warp_batch_frame_count": phase2_handoff.get(
            "triangle_warp_batch_frame_count"
        ),
        "raw_warp_copy_mode": raw.get("warp_copy_mode"),
        "phase2_warp_copy_mode": phase2_handoff.get("warp_copy_mode"),
        "raw_passed_check_count": _int_value(raw.get("passed_check_count")),
        "phase2_passed_check_count": _int_value(
            phase2_handoff.get("passed_check_count")
        ),
        "raw_failed_check_count": raw_failed_count,
        "phase2_failed_check_count": phase2_failed_count,
        "raw_failed_checks": raw.get("failed_checks") or [],
        "phase2_failed_checks": phase2_handoff.get("failed_checks") or [],
        "raw_failed_acceptance_checks": raw.get("failed_acceptance_checks") or [],
        "phase2_failed_acceptance_checks": (
            phase2_handoff.get("failed_acceptance_checks") or []
        ),
    }


def _release_decision_direct_runtime_publication_guard(
    decision: dict[str, Any],
    *,
    min_resident_lights: int,
) -> dict[str, Any]:
    direct = (
        decision.get("stack_engine_publication_direct_runtime_evidence")
        if isinstance(
            decision.get("stack_engine_publication_direct_runtime_evidence"),
            dict,
        )
        else {}
    )
    check_passed = _decision_check_passed(
        decision,
        "stack_engine_publication_direct_runtime_evidence_passed",
    )
    raw_matrix_lights = _int_value(direct.get("raw_matrix_pipeline_resident_lights"))
    raw_default_lights = _int_value(
        direct.get("raw_default_promotion_pipeline_resident_lights")
    )
    phase2_matrix_lights = _int_value(
        direct.get("phase2_matrix_pipeline_resident_lights")
    )
    phase2_default_lights = _int_value(
        direct.get("phase2_default_promotion_pipeline_resident_lights")
    )
    source_ready = (
        direct.get("raw_source_ready") is True
        and direct.get("phase2_source_ready") is True
        and direct.get("raw_matrix_acceptance_source")
        == "explicit_resident_artifacts_json"
        and direct.get("raw_default_promotion_acceptance_source")
        == "explicit_resident_artifacts_json"
        and direct.get("phase2_matrix_acceptance_source")
        == "explicit_resident_artifacts_json"
        and direct.get("phase2_default_promotion_acceptance_source")
        == "explicit_resident_artifacts_json"
        and direct.get("raw_matrix_pipeline_calibration_source")
        == "resident_artifacts_json_fallback"
        and direct.get("raw_default_promotion_pipeline_calibration_source")
        == "resident_artifacts_json_fallback"
        and direct.get("phase2_matrix_pipeline_calibration_source")
        == "resident_artifacts_json_fallback"
        and direct.get("phase2_default_promotion_pipeline_calibration_source")
        == "resident_artifacts_json_fallback"
    )
    count_ready = (
        direct.get("raw_count_ready") is True
        and direct.get("phase2_count_ready") is True
        and _int_value(direct.get("raw_matrix_acceptance_check_count")) is not None
        and _int_value(direct.get("raw_matrix_acceptance_check_count")) > 0
        and _int_value(direct.get("raw_default_promotion_acceptance_check_count"))
        is not None
        and _int_value(direct.get("raw_default_promotion_acceptance_check_count"))
        > 0
        and _int_value(direct.get("phase2_matrix_acceptance_check_count"))
        is not None
        and _int_value(direct.get("phase2_matrix_acceptance_check_count")) > 0
        and _int_value(direct.get("phase2_default_promotion_acceptance_check_count"))
        is not None
        and _int_value(direct.get("phase2_default_promotion_acceptance_check_count"))
        > 0
        and raw_matrix_lights is not None
        and raw_matrix_lights >= int(min_resident_lights)
        and raw_default_lights is not None
        and raw_default_lights >= int(min_resident_lights)
        and phase2_matrix_lights is not None
        and phase2_matrix_lights >= int(min_resident_lights)
        and phase2_default_lights is not None
        and phase2_default_lights >= int(min_resident_lights)
    )
    leaf_ready = (
        direct.get("raw_leaf_checks_ready") is True
        and direct.get("phase2_leaf_checks_ready") is True
    )
    ready = (
        bool(direct)
        and check_passed is True
        and direct.get("ready") is True
        and direct.get("checks_passed") is True
        and source_ready
        and count_ready
        and leaf_ready
    )
    return {
        "present": bool(direct),
        "ready": ready,
        "decision_check_passed": check_passed,
        "status": direct.get("status"),
        "passed": direct.get("passed"),
        "checks_passed": direct.get("checks_passed"),
        "source_ready": source_ready,
        "count_ready": count_ready,
        "leaf_checks_ready": leaf_ready,
        "raw_ready": direct.get("raw_ready"),
        "phase2_ready": direct.get("phase2_ready"),
        "phase2_check_passed": direct.get("phase2_check_passed"),
        "raw_matrix_acceptance_source": direct.get("raw_matrix_acceptance_source"),
        "raw_default_promotion_acceptance_source": direct.get(
            "raw_default_promotion_acceptance_source"
        ),
        "phase2_matrix_acceptance_source": direct.get(
            "phase2_matrix_acceptance_source"
        ),
        "phase2_default_promotion_acceptance_source": direct.get(
            "phase2_default_promotion_acceptance_source"
        ),
        "raw_matrix_acceptance_check_count": _int_value(
            direct.get("raw_matrix_acceptance_check_count")
        ),
        "raw_default_promotion_acceptance_check_count": _int_value(
            direct.get("raw_default_promotion_acceptance_check_count")
        ),
        "phase2_matrix_acceptance_check_count": _int_value(
            direct.get("phase2_matrix_acceptance_check_count")
        ),
        "phase2_default_promotion_acceptance_check_count": _int_value(
            direct.get("phase2_default_promotion_acceptance_check_count")
        ),
        "raw_matrix_pipeline_calibration_source": direct.get(
            "raw_matrix_pipeline_calibration_source"
        ),
        "raw_default_promotion_pipeline_calibration_source": direct.get(
            "raw_default_promotion_pipeline_calibration_source"
        ),
        "phase2_matrix_pipeline_calibration_source": direct.get(
            "phase2_matrix_pipeline_calibration_source"
        ),
        "phase2_default_promotion_pipeline_calibration_source": direct.get(
            "phase2_default_promotion_pipeline_calibration_source"
        ),
        "raw_matrix_pipeline_resident_lights": raw_matrix_lights,
        "raw_default_promotion_pipeline_resident_lights": raw_default_lights,
        "phase2_matrix_pipeline_resident_lights": phase2_matrix_lights,
        "phase2_default_promotion_pipeline_resident_lights": phase2_default_lights,
        "required_min_resident_lights": int(min_resident_lights),
    }


def _release_decision_quality_compare_publication_guard(
    decision: dict[str, Any],
) -> dict[str, Any]:
    quality = (
        decision.get("stack_engine_publication_quality_metrics_compare")
        if isinstance(
            decision.get("stack_engine_publication_quality_metrics_compare"),
            dict,
        )
        else {}
    )
    check_passed = _decision_check_passed(
        decision,
        "stack_engine_publication_quality_metrics_compare_passed",
    )
    present = bool(quality)
    compatible_missing = not present or quality.get("compatible_missing") is True
    quality_compare_present = quality.get("quality_compare_present") is True
    raw_ready = quality.get("raw_ready") is True
    phase2_ready = quality.get("phase2_ready") is True
    decision_check_ready = check_passed is True or (
        check_passed is None and compatible_missing and not quality_compare_present
    )
    checks_ready = quality.get("checks_passed") is True or compatible_missing
    layers_ready = (
        not quality_compare_present
        or (
            quality.get("raw_present") is True
            and quality.get("phase2_present") is True
            and raw_ready
            and phase2_ready
        )
    )
    ready = not present or (
        quality.get("ready") is True
        and decision_check_ready
        and checks_ready
        and layers_ready
    )
    return {
        "present": present,
        "ready": ready,
        "decision_check_passed": check_passed,
        "status": quality.get("status"),
        "passed": quality.get("passed"),
        "checks_passed": quality.get("checks_passed"),
        "compatible_missing": compatible_missing,
        "quality_compare_present": quality_compare_present,
        "decision_check_ready": decision_check_ready,
        "checks_ready": checks_ready,
        "layers_ready": layers_ready,
        "raw_present": quality.get("raw_present"),
        "raw_ready": quality.get("raw_ready"),
        "raw_matrix_status": quality.get("raw_matrix_status"),
        "raw_matrix_failed_check_count": quality.get(
            "raw_matrix_failed_check_count"
        ),
        "raw_default_promotion_status": quality.get(
            "raw_default_promotion_status"
        ),
        "raw_default_promotion_failed_check_count": quality.get(
            "raw_default_promotion_failed_check_count"
        ),
        "phase2_present": quality.get("phase2_present"),
        "phase2_ready": quality.get("phase2_ready"),
        "phase2_check_passed": quality.get("phase2_check_passed"),
        "phase2_matrix_status": quality.get("phase2_matrix_status"),
        "phase2_matrix_failed_check_count": quality.get(
            "phase2_matrix_failed_check_count"
        ),
        "phase2_default_promotion_status": quality.get(
            "phase2_default_promotion_status"
        ),
        "phase2_default_promotion_failed_check_count": quality.get(
            "phase2_default_promotion_failed_check_count"
        ),
        "failed_checks": quality.get("failed_checks") or [],
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
    release_resident_winsorized = (
        decision.get("pipeline_resident_winsorized_semantics_release")
        if isinstance(decision.get("pipeline_resident_winsorized_semantics_release"), dict)
        else {}
    )
    stack_engine = _stack_engine_summary(phase2)
    default_route = _default_route_acceptance_summary(phase2)
    quality_metrics_compare = _quality_metrics_compare_summary(phase2)
    resident_winsorized_sweep = _resident_winsorized_sweep_summary(phase2)
    publication_audit = _publication_audit_summary(phase2)
    integration_engine_policy = _integration_engine_policy_summary(phase2, pipeline)
    resident_result_contract = _resident_result_contract_summary(phase2, pipeline)
    stack_engine_runtime_default = _stack_engine_runtime_default_summary(
        phase2,
        pipeline,
    )
    runtime_default_direct_evidence = _runtime_default_direct_evidence_summary(
        decision,
        phase2,
    )
    resident_fastpath_release_handoff = (
        _resident_registration_fastpath_release_handoff_summary(
            decision,
            phase2,
        )
    )
    release_direct_publication_guard = (
        _release_decision_direct_runtime_publication_guard(
            decision,
            min_resident_lights=min_resident_lights,
        )
    )
    release_quality_publication_guard = (
        _release_decision_quality_compare_publication_guard(decision)
    )
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
            "release_decision_direct_runtime_publication_guard_passed",
            release_direct_publication_guard.get("ready") is True,
            release_direct_publication_guard,
        ),
        _check(
            "release_decision_quality_compare_publication_guard_passed",
            release_quality_publication_guard.get("ready") is True,
            release_quality_publication_guard,
            note="Required when the release decision supplies StackEngine publication quality compare evidence.",
        ),
        _check(
            "resident_registration_fastpath_release_handoff_ready",
            resident_fastpath_release_handoff.get("ready") is True,
            resident_fastpath_release_handoff,
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
            "quality_metrics_compare_handoff_passed",
            quality_metrics_compare.get("ready") is True,
            quality_metrics_compare,
            note="Required only when Phase2 status supplies quality-metrics-compare evidence.",
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
            "pipeline_resident_result_contract_handoff_passed",
            resident_result_contract.get("ready") is True,
            resident_result_contract,
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
            "acceptance_stack_engine_runtime_default_handoff_passed",
            stack_engine_runtime_default.get("acceptance_status") == "passed"
            and stack_engine_runtime_default.get("acceptance_check_present") is True
            and stack_engine_runtime_default.get("acceptance_check_passed") is True
            and stack_engine_runtime_default.get("acceptance_phase2_check_passed")
            is True
            and stack_engine_runtime_default.get("acceptance_legacy_master_count")
            == 0
            and stack_engine_runtime_default.get("acceptance_failed_master_count")
            == 0
            and stack_engine_runtime_default.get("acceptance_failed_output_count")
            == 0,
            {
                "status": stack_engine_runtime_default.get("acceptance_status"),
                "check_present": stack_engine_runtime_default.get(
                    "acceptance_check_present"
                ),
                "check_passed": stack_engine_runtime_default.get(
                    "acceptance_check_passed"
                ),
                "phase2_check_passed": stack_engine_runtime_default.get(
                    "acceptance_phase2_check_passed"
                ),
                "master_count": stack_engine_runtime_default.get(
                    "acceptance_master_count"
                ),
                "legacy_master_count": stack_engine_runtime_default.get(
                    "acceptance_legacy_master_count"
                ),
                "failed_master_count": stack_engine_runtime_default.get(
                    "acceptance_failed_master_count"
                ),
                "failed_output_count": stack_engine_runtime_default.get(
                    "acceptance_failed_output_count"
                ),
                "explicit_cuda_fast_path_count": stack_engine_runtime_default.get(
                    "acceptance_explicit_cuda_fast_path_count"
                ),
                "failed_masters": stack_engine_runtime_default.get(
                    "acceptance_failed_masters"
                ),
                "failed_outputs": stack_engine_runtime_default.get(
                    "acceptance_failed_outputs"
                ),
            },
        ),
        _check(
            "pipeline_stack_engine_runtime_default_handoff_passed",
            stack_engine_runtime_default.get("pipeline_status") == "passed"
            and stack_engine_runtime_default.get("pipeline_check_present") is True
            and stack_engine_runtime_default.get("pipeline_check_passed") is True
            and stack_engine_runtime_default.get("pipeline_phase2_check_passed")
            is True
            and stack_engine_runtime_default.get("pipeline_legacy_master_count") == 0
            and stack_engine_runtime_default.get("pipeline_failed_master_count") == 0
            and stack_engine_runtime_default.get("pipeline_failed_output_count") == 0,
            {
                "status": stack_engine_runtime_default.get("pipeline_status"),
                "check_present": stack_engine_runtime_default.get(
                    "pipeline_check_present"
                ),
                "check_passed": stack_engine_runtime_default.get(
                    "pipeline_check_passed"
                ),
                "phase2_check_passed": stack_engine_runtime_default.get(
                    "pipeline_phase2_check_passed"
                ),
                "master_count": stack_engine_runtime_default.get(
                    "pipeline_master_count"
                ),
                "legacy_master_count": stack_engine_runtime_default.get(
                    "pipeline_legacy_master_count"
                ),
                "failed_master_count": stack_engine_runtime_default.get(
                    "pipeline_failed_master_count"
                ),
                "failed_output_count": stack_engine_runtime_default.get(
                    "pipeline_failed_output_count"
                ),
                "explicit_cuda_fast_path_count": stack_engine_runtime_default.get(
                    "pipeline_explicit_cuda_fast_path_count"
                ),
                "failed_masters": stack_engine_runtime_default.get(
                    "pipeline_failed_masters"
                ),
                "failed_outputs": stack_engine_runtime_default.get(
                    "pipeline_failed_outputs"
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
            "resident_winsorized_semantics": release_resident_winsorized,
            "direct_runtime_publication_guard": release_direct_publication_guard,
            "quality_compare_publication_guard": release_quality_publication_guard,
        },
        "phase2_status": {
            "status": phase2.get("status"),
            "passed": phase2.get("passed"),
            "latest_checkpoint": latest_checkpoint,
            "release_decision": phase2_decision,
        },
        "runtime_repeat": runtime,
        "default_route_acceptance": default_route,
        "quality_metrics_compare": quality_metrics_compare,
        "pipeline_contract": pipeline,
        "integration_engine_policy": integration_engine_policy,
        "resident_result_contract": resident_result_contract,
        "stack_engine_runtime_default": stack_engine_runtime_default,
        "runtime_default_direct_evidence": runtime_default_direct_evidence,
        "resident_registration_fastpath_release_handoff": (
            resident_fastpath_release_handoff
        ),
        "release_decision_direct_runtime_publication_guard": (
            release_direct_publication_guard
        ),
        "release_decision_quality_compare_publication_guard": (
            release_quality_publication_guard
        ),
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
    quality_metrics_compare = payload.get("quality_metrics_compare") or {}
    pipeline = payload.get("pipeline_contract") or {}
    integration_engine_policy = payload.get("integration_engine_policy") or {}
    resident_result_contract = payload.get("resident_result_contract") or {}
    stack_engine_runtime_default = payload.get("stack_engine_runtime_default") or {}
    runtime_default_direct_evidence = (
        payload.get("runtime_default_direct_evidence") or {}
    )
    release_direct_publication_guard = (
        payload.get("release_decision_direct_runtime_publication_guard") or {}
    )
    release_quality_publication_guard = (
        payload.get("release_decision_quality_compare_publication_guard") or {}
    )
    resident_fastpath_release_handoff = (
        payload.get("resident_registration_fastpath_release_handoff") or {}
    )
    stack_engine = payload.get("stack_engine_contract") or {}
    resident_winsorized_sweep = payload.get("resident_winsorized_sweep_audit") or {}
    release_decision = payload.get("release_decision") or {}
    release_resident_winsorized = (
        release_decision.get("resident_winsorized_semantics")
        if isinstance(release_decision.get("resident_winsorized_semantics"), dict)
        else {}
    )
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
        (
            "- Quality metrics compare: "
            f"present=`{quality_metrics_compare.get('present')}` "
            f"ready=`{quality_metrics_compare.get('ready')}` "
            f"status=`{quality_metrics_compare.get('status')}` "
            f"phase2=`{quality_metrics_compare.get('phase2_check_passed')}` "
            f"failed-checks=`{quality_metrics_compare.get('failed_checks')}`"
        ),
        f"- Rejection sample accounting: `{pipeline.get('rejection_sample_accounting_status')}`",
        f"- Sample accounting closure: `{pipeline.get('sample_accounting_closure_status')}`",
        (
            "- Resident result contract: "
            f"ready=`{resident_result_contract.get('ready')}` "
            f"status=`{resident_result_contract.get('status')}` "
            f"check=`{resident_result_contract.get('check_passed')}` "
            f"phase2=`{resident_result_contract.get('phase2_check_passed')}` "
            f"required=`{resident_result_contract.get('required_count')}` "
            f"failed=`{resident_result_contract.get('failed_count')}` "
            f"failed-checks=`{resident_result_contract.get('failed_checks')}`"
        ),
        (
            "- Release resident winsorized semantics: "
            f"`{release_resident_winsorized.get('status')}` "
            f"required=`{release_resident_winsorized.get('required_count')}` "
            f"legacy-completions=`{release_resident_winsorized.get('legacy_completion_count')}`"
        ),
        f"- Acceptance integration engine policy: `{integration_engine_policy.get('acceptance_status')}`",
        f"- Pipeline integration engine policy: `{integration_engine_policy.get('pipeline_status')}`",
        (
            "- Integration engine policy ready: "
            f"`{integration_engine_policy.get('ready')}`"
        ),
        (
            "- Acceptance StackEngine runtime default: "
            f"`{stack_engine_runtime_default.get('acceptance_status')}` "
            f"check=`{stack_engine_runtime_default.get('acceptance_check_passed')}` "
            f"legacy=`{stack_engine_runtime_default.get('acceptance_legacy_master_count')}` "
            "failed-masters="
            f"`{stack_engine_runtime_default.get('acceptance_failed_master_count')}` "
            "failed-outputs="
            f"`{stack_engine_runtime_default.get('acceptance_failed_output_count')}`"
        ),
        (
            "- Pipeline StackEngine runtime default: "
            f"`{stack_engine_runtime_default.get('pipeline_status')}` "
            f"check=`{stack_engine_runtime_default.get('pipeline_check_passed')}` "
            f"legacy=`{stack_engine_runtime_default.get('pipeline_legacy_master_count')}` "
            "failed-masters="
            f"`{stack_engine_runtime_default.get('pipeline_failed_master_count')}` "
            "failed-outputs="
            f"`{stack_engine_runtime_default.get('pipeline_failed_output_count')}`"
        ),
        (
            "- StackEngine runtime default ready: "
            f"`{stack_engine_runtime_default.get('ready')}`"
        ),
        (
            "- Direct runtime evidence: "
            f"ready=`{runtime_default_direct_evidence.get('ready')}` "
            f"acceptance-source=`{runtime_default_direct_evidence.get('acceptance_fastpath_source')}` "
            "pipeline-calibration-source="
            f"`{runtime_default_direct_evidence.get('pipeline_calibration_artifact_source')}`"
        ),
        (
            "- Release direct publication guard: "
            f"ready=`{release_direct_publication_guard.get('ready')}` "
            f"check=`{release_direct_publication_guard.get('decision_check_passed')}` "
            f"source-ready=`{release_direct_publication_guard.get('source_ready')}` "
            f"count-ready=`{release_direct_publication_guard.get('count_ready')}`"
        ),
        (
            "- Release direct publication sources: "
            "raw-acceptance="
            f"`{release_direct_publication_guard.get('raw_matrix_acceptance_source')}` "
            "raw-calibration="
            f"`{release_direct_publication_guard.get('raw_matrix_pipeline_calibration_source')}` "
            "raw-lights="
            f"`{release_direct_publication_guard.get('raw_matrix_pipeline_resident_lights')}`"
        ),
        (
            "- Release quality compare publication guard: "
            f"ready=`{release_quality_publication_guard.get('ready')}` "
            f"check=`{release_quality_publication_guard.get('decision_check_passed')}` "
            f"quality-present=`{release_quality_publication_guard.get('quality_compare_present')}` "
            f"compatible-missing=`{release_quality_publication_guard.get('compatible_missing')}`"
        ),
        (
            "- Release quality compare sources: "
            f"raw=`{release_quality_publication_guard.get('raw_matrix_status')}` "
            f"phase2=`{release_quality_publication_guard.get('phase2_matrix_status')}` "
            "raw-failed="
            f"`{release_quality_publication_guard.get('raw_matrix_failed_check_count')}` "
            "phase2-failed="
            f"`{release_quality_publication_guard.get('phase2_matrix_failed_check_count')}`"
        ),
        (
            "- Resident fastpath release handoff: "
            f"ready=`{resident_fastpath_release_handoff.get('ready')}` "
            f"raw=`{resident_fastpath_release_handoff.get('raw_status')}` "
            f"phase2=`{resident_fastpath_release_handoff.get('phase2_status')}` "
            f"agreement=`{resident_fastpath_release_handoff.get('agreement')}` "
            f"checks=`{resident_fastpath_release_handoff.get('raw_passed_check_count')}`"
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
