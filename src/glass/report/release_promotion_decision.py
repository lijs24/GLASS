from __future__ import annotations

from pathlib import Path
from typing import Any

from glass.io.json_io import read_json, write_json
from glass.models import now_iso


def _read_json_object(path: str | Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"JSON artifact must be an object: {path}")
    return payload


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


def _release_evidence_status(acceptance: dict[str, Any], key: str) -> str | None:
    evidence = acceptance.get("release_contract_evidence")
    if not isinstance(evidence, dict):
        return None
    item = evidence.get(key)
    if not isinstance(item, dict):
        return None
    return None if item.get("status") is None else str(item.get("status"))


def _stack_default_ready(acceptance: dict[str, Any], stack_contract: dict[str, Any]) -> bool:
    promotion = stack_contract.get("default_promotion") if isinstance(stack_contract.get("default_promotion"), dict) else {}
    if promotion.get("ready") is True:
        return True
    evidence = acceptance.get("release_contract_evidence")
    stack_evidence = (
        evidence.get("stack_engine_default_promotion")
        if isinstance(evidence, dict) and isinstance(evidence.get("stack_engine_default_promotion"), dict)
        else {}
    )
    return stack_evidence.get("default_promotion_ready") is True


def _stack_default_scope(acceptance: dict[str, Any], stack_contract: dict[str, Any]) -> str | None:
    if stack_contract.get("scope") is not None:
        return str(stack_contract.get("scope"))
    evidence = acceptance.get("release_contract_evidence")
    stack_evidence = (
        evidence.get("stack_engine_default_promotion")
        if isinstance(evidence, dict) and isinstance(evidence.get("stack_engine_default_promotion"), dict)
        else {}
    )
    scope = stack_evidence.get("stack_engine_contract_scope")
    return None if scope is None else str(scope)


def _pipeline_contract_source(acceptance: dict[str, Any], pipeline_contract: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    if pipeline_contract:
        return "explicit_pipeline_contract", pipeline_contract
    embedded = acceptance.get("pipeline_contract")
    if isinstance(embedded, dict) and embedded:
        return "acceptance_pipeline_contract", embedded
    return "missing", {}


def _pipeline_contract_check_state(pipeline: dict[str, Any], name: str) -> bool | None:
    checks = pipeline.get("checks") if isinstance(pipeline.get("checks"), list) else []
    for item in checks:
        if isinstance(item, dict) and item.get("name") == name:
            return bool(item.get("passed"))

    check_names = {str(item) for item in pipeline.get("check_names") or []}
    failed_checks = {str(item) for item in pipeline.get("failed_checks") or []}
    if name in check_names:
        return name not in failed_checks
    return None


def _acceptance_check_state(acceptance: dict[str, Any], name: str) -> bool | None:
    checks = acceptance.get("checks") if isinstance(acceptance.get("checks"), list) else []
    for item in checks:
        if isinstance(item, dict) and item.get("name") == name:
            return bool(item.get("passed"))
    return None


def _acceptance_check_prefix_summary(
    acceptance: dict[str, Any], prefix: str
) -> dict[str, Any]:
    checks = acceptance.get("checks") if isinstance(acceptance.get("checks"), list) else []
    rows: list[dict[str, Any]] = []
    for item in checks:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if name is not None and str(name).startswith(prefix):
            rows.append(item)
    failed = [str(item.get("name")) for item in rows if item.get("passed") is not True]
    return {
        "check_count": len(rows),
        "failed_check_count": len(failed),
        "failed_checks": failed,
        "passed": bool(rows) and not failed,
        "checks": {str(item.get("name")): bool(item.get("passed")) for item in rows},
    }


def _warp_quality_handoff_evidence(acceptance: dict[str, Any]) -> dict[str, Any]:
    contract = (
        acceptance.get("warp_quality_contract")
        if isinstance(acceptance.get("warp_quality_contract"), dict)
        else {}
    )
    acceptance_checks = {
        name: _acceptance_check_state(acceptance, name)
        for name in (
            "warp_quality_contract_present",
            "warp_quality_contract_type",
            "warp_quality_contract_passed",
        )
    }
    present = bool(contract) or any(value is not None for value in acceptance_checks.values())
    failed_acceptance_checks = [
        name for name, value in acceptance_checks.items() if value is False
    ]
    if not present:
        status = "not_available"
        ready = True
    elif (
        contract.get("exists") is not False
        and contract.get("artifact_type") == "warp_quality_contract"
        and contract.get("passed") is True
        and not failed_acceptance_checks
    ):
        status = "passed"
        ready = True
    else:
        status = "failed"
        ready = False
    return {
        "schema_version": 1,
        "source": "acceptance_audit",
        "present": present,
        "status": status,
        "ready": ready,
        "path": contract.get("path"),
        "exists": contract.get("exists"),
        "artifact_type": contract.get("artifact_type"),
        "contract_status": contract.get("status"),
        "contract_passed": contract.get("passed"),
        "check_count": contract.get("check_count"),
        "output_count": contract.get("output_count"),
        "failed_checks": contract.get("failed_checks") or [],
        "acceptance_checks": acceptance_checks,
        "failed_acceptance_checks": failed_acceptance_checks,
    }


def _resident_registration_fastpath_handoff_evidence(
    acceptance: dict[str, Any]
) -> dict[str, Any]:
    release_evidence = (
        acceptance.get("release_contract_evidence")
        if isinstance(acceptance.get("release_contract_evidence"), dict)
        else {}
    )
    contract_evidence = (
        release_evidence.get("resident_registration_fastpath")
        if isinstance(release_evidence.get("resident_registration_fastpath"), dict)
        else {}
    )
    top_level = (
        acceptance.get("resident_registration_fastpath")
        if isinstance(acceptance.get("resident_registration_fastpath"), dict)
        else {}
    )
    source = contract_evidence if contract_evidence else top_level
    check_summary = _acceptance_check_prefix_summary(
        acceptance, "contract_resident_registration_fastpath"
    )
    present = bool(contract_evidence) or bool(top_level) or check_summary["check_count"] > 0
    required = bool(
        contract_evidence.get(
            "required_by_benchmark_contract",
            top_level.get("required_by_benchmark_contract", False),
        )
    ) or check_summary["check_count"] > 0
    failed_check_count = _int_value(source.get("failed_check_count"))
    if failed_check_count is None:
        failed_check_count = int(check_summary["failed_check_count"])
    passed_check_count = _int_value(source.get("passed_check_count"))
    if passed_check_count is None and check_summary["check_count"]:
        passed_check_count = int(check_summary["check_count"]) - int(
            check_summary["failed_check_count"]
        )
    failed_checks = source.get("failed_checks")
    if not isinstance(failed_checks, list):
        failed_checks = check_summary["failed_checks"]
    status_value = source.get("status")
    status_text = None if status_value is None else str(status_value)
    source_passed = (
        status_text == "passed"
        and source.get("available") is not False
        and source.get("exists") is not False
        and failed_check_count == 0
    )
    checks_passed = check_summary["passed"] or check_summary["check_count"] == 0
    if not present:
        status = "not_available"
        ready = True
    elif not required:
        status = status_text or "not_required"
        ready = True
    elif source_passed and checks_passed:
        status = "passed"
        ready = True
    else:
        status = "failed"
        ready = False
    return {
        "schema_version": 1,
        "source": source.get("source"),
        "present": present,
        "status": status,
        "ready": ready,
        "required_by_benchmark_contract": required,
        "path": source.get("path"),
        "exists": source.get("exists"),
        "available": source.get("available"),
        "resident_registration_mode": source.get(
            "resident_registration_mode", source.get("mode")
        ),
        "descriptor_fit_batch_mode": source.get(
            "descriptor_fit_batch_mode",
            source.get("triangle_descriptor_fit_batch_mode"),
        ),
        "pixel_refine_batch_mode": source.get(
            "pixel_refine_batch_mode",
            source.get("triangle_pixel_refine_batch_mode"),
        ),
        "triangle_warp_batch_mode": source.get("triangle_warp_batch_mode"),
        "triangle_warp_batch_frame_count": source.get(
            "triangle_warp_batch_frame_count"
        ),
        "warp_copy_mode": source.get(
            "warp_copy_mode",
            source.get("resident_warp_copy_mode")
            or source.get("resident_io_pipeline_warp_copy_mode"),
        ),
        "passed_check_count": passed_check_count,
        "failed_check_count": failed_check_count,
        "failed_checks": failed_checks,
        "acceptance_check_count": check_summary["check_count"],
        "failed_acceptance_checks": check_summary["failed_checks"],
        "acceptance_checks": check_summary["checks"],
    }


def _pipeline_rejection_sample_accounting(pipeline: dict[str, Any]) -> dict[str, Any]:
    embedded = pipeline.get("rejection_sample_accounting")
    if isinstance(embedded, dict) and embedded:
        return dict(embedded)

    check_name = "integration_rejection_sample_counts_match_maps"
    check_passed = _pipeline_contract_check_state(pipeline, check_name)
    pixel_verification = (
        pipeline.get("pixel_verification")
        if isinstance(pipeline.get("pixel_verification"), dict)
        else {}
    )
    integration_outputs = pixel_verification.get("integration_outputs")
    if not isinstance(integration_outputs, list):
        integration_outputs = []

    rows: list[dict[str, Any]] = []
    for output in integration_outputs:
        if not isinstance(output, dict):
            continue
        accounting = output.get("rejection_sample_accounting")
        if isinstance(accounting, dict):
            failed_matches = [
                {
                    "source": match.get("source"),
                    "actual": match.get("actual"),
                    "summary": match.get("summary"),
                    "delta": match.get("delta"),
                }
                for match in accounting.get("source_matches") or []
                if isinstance(match, dict) and not match.get("passed")
            ]
            rows.append(
                {
                    "item": output.get("item"),
                    "status": accounting.get("status"),
                    "accounting_present": True,
                    "required": bool(accounting.get("required")),
                    "verified": bool(accounting.get("verified")),
                    "ok": bool(accounting.get("ok")),
                    "map_rejected_sample_sum": accounting.get("map_rejected_sample_sum"),
                    "source_counts": accounting.get("source_counts") or [],
                    "failed_matches": failed_matches,
                }
            )
            continue

        count_maps = output.get("count_maps") if isinstance(output.get("count_maps"), dict) else {}
        required_maps: list[str] = []
        verified_maps: list[str] = []
        for map_name in ("low_rejection", "high_rejection"):
            row = count_maps.get(map_name) if isinstance(count_maps.get(map_name), dict) else {}
            if row.get("required") is True:
                required_maps.append(map_name)
            if row.get("verified") is True:
                verified_maps.append(map_name)
        required = bool(required_maps)
        rows.append(
            {
                "item": output.get("item"),
                "status": "missing_required" if required else "not_required",
                "accounting_present": False,
                "required": required,
                "verified": False,
                "ok": not required,
                "map_rejected_sample_sum": None,
                "source_counts": [],
                "failed_matches": [],
                "required_maps": required_maps,
                "verified_maps": verified_maps,
            }
        )

    failed_items = [row for row in rows if row.get("required") and not row.get("ok")]
    check_present = check_passed is not None
    if check_present:
        status = "passed" if check_passed and not failed_items else "failed"
    elif rows:
        status = "failed" if failed_items else "not_required"
    else:
        status = "not_available"
    return {
        "schema_version": 1,
        "status": status,
        "check_name": check_name,
        "check_present": check_present,
        "check_passed": check_passed,
        "pixel_verification_enabled": bool(pixel_verification.get("enabled")),
        "output_count": len(integration_outputs),
        "accounted_output_count": sum(1 for row in rows if row.get("accounting_present")),
        "required_count": sum(1 for row in rows if row.get("required")),
        "verified_count": sum(1 for row in rows if row.get("verified")),
        "failed_count": len(failed_items),
        "failed_items": failed_items,
        "rows": rows,
    }


def _pipeline_sample_accounting_closure(pipeline: dict[str, Any]) -> dict[str, Any]:
    embedded = pipeline.get("sample_accounting_closure")
    if isinstance(embedded, dict) and embedded:
        return dict(embedded)

    check_name = "integration_sample_accounting_closure"
    check_passed = _pipeline_contract_check_state(pipeline, check_name)
    integration = pipeline.get("integration") if isinstance(pipeline.get("integration"), dict) else {}
    integration_outputs = integration.get("outputs")
    if not isinstance(integration_outputs, list):
        integration_outputs = []

    rows: list[dict[str, Any]] = []
    for output in integration_outputs:
        if not isinstance(output, dict):
            continue
        closure = output.get("sample_accounting_closure")
        if not isinstance(closure, dict):
            rows.append(
                {
                    "item": output.get("item"),
                    "status": "missing",
                    "present": False,
                    "required": False,
                    "passed": True,
                    "input_total_match": None,
                    "valid_rejection_match": None,
                    "input_samples": None,
                    "input_valid_samples_before_rejection": None,
                    "input_invalid_samples_before_rejection": None,
                    "valid_samples_after_rejection": None,
                    "rejected_samples": None,
                    "semantics": None,
                }
            )
            continue
        rows.append(
            {
                "item": output.get("item"),
                "status": closure.get("status"),
                "present": bool(closure.get("present")),
                "required": bool(closure.get("required")),
                "passed": bool(closure.get("passed")),
                "input_total_match": closure.get("input_total_match"),
                "valid_rejection_match": closure.get("valid_rejection_match"),
                "input_samples": closure.get("input_samples"),
                "input_valid_samples_before_rejection": closure.get(
                    "input_valid_samples_before_rejection"
                ),
                "input_invalid_samples_before_rejection": closure.get(
                    "input_invalid_samples_before_rejection"
                ),
                "valid_samples_after_rejection": closure.get("valid_samples_after_rejection"),
                "rejected_samples": closure.get("rejected_samples"),
                "semantics": closure.get("semantics"),
            }
        )

    failed_items = [row for row in rows if not row.get("passed")]
    check_present = check_passed is not None
    if check_present:
        status = "passed" if check_passed else "failed"
    elif rows:
        status = "passed" if any(row.get("present") for row in rows) and not failed_items else "not_available"
    else:
        status = "not_available"
    return {
        "schema_version": 1,
        "status": status,
        "check_name": check_name,
        "check_present": check_present,
        "check_passed": check_passed,
        "output_count": len(integration_outputs),
        "present_count": sum(1 for row in rows if row.get("present")),
        "required_count": sum(1 for row in rows if row.get("required")),
        "failed_count": len(failed_items),
        "failed_items": failed_items,
        "rows": rows,
    }


def _zero_count(value: Any) -> bool:
    numeric = _int_value(value)
    return numeric is not None and numeric == 0


def _release_sample_scope_ready(
    *,
    status: Any,
    check_passed: Any,
    required_count: Any,
    failed_count: Any,
) -> bool:
    if check_passed is not True:
        return False
    if failed_count not in (None, 0):
        return False
    if status == "passed":
        return True
    return status == "not_required" and _zero_count(required_count)


def _rejection_sample_release_evidence(pipeline_handoff: dict[str, Any]) -> dict[str, Any]:
    accounting = (
        pipeline_handoff.get("rejection_sample_accounting")
        if isinstance(pipeline_handoff.get("rejection_sample_accounting"), dict)
        else {}
    )
    check = pipeline_handoff["checks"].get("integration_rejection_sample_counts_match_maps")
    status = pipeline_handoff.get("rejection_sample_accounting_status")
    required_count = accounting.get("required_count")
    failed_count = accounting.get("failed_count")
    ready = _release_sample_scope_ready(
        status=status,
        check_passed=check,
        required_count=required_count,
        failed_count=failed_count,
    )
    return {
        "ready": ready,
        "check": check,
        "status": status,
        "check_present": accounting.get("check_present"),
        "required_count": required_count,
        "verified_count": accounting.get("verified_count"),
        "accounted_output_count": accounting.get("accounted_output_count"),
        "failed_count": failed_count,
        "failed_items": accounting.get("failed_items"),
        "scope": "required" if _int_value(required_count) else "not_required",
    }


def _sample_closure_release_evidence(pipeline_handoff: dict[str, Any]) -> dict[str, Any]:
    closure = (
        pipeline_handoff.get("sample_accounting_closure")
        if isinstance(pipeline_handoff.get("sample_accounting_closure"), dict)
        else {}
    )
    check = pipeline_handoff["checks"].get("integration_sample_accounting_closure")
    status = pipeline_handoff.get("sample_accounting_closure_status")
    required_count = closure.get("required_count")
    if required_count is None and _int_value(closure.get("present_count")):
        required_count = closure.get("present_count")
    failed_count = closure.get("failed_count")
    ready = _release_sample_scope_ready(
        status=status,
        check_passed=check,
        required_count=required_count,
        failed_count=failed_count,
    )
    return {
        "ready": ready,
        "check": check,
        "status": status,
        "check_present": closure.get("check_present"),
        "present_count": closure.get("present_count"),
        "required_count": required_count,
        "failed_count": failed_count,
        "failed_items": closure.get("failed_items"),
        "scope": "required" if _int_value(required_count) else "not_required",
    }


def _pipeline_handoff_evidence(
    acceptance: dict[str, Any],
    pipeline_contract: dict[str, Any],
) -> dict[str, Any]:
    source, pipeline = _pipeline_contract_source(acceptance, pipeline_contract)
    integration = pipeline.get("integration") if isinstance(pipeline.get("integration"), dict) else {}
    pixel_verification = (
        pipeline.get("pixel_verification")
        if isinstance(pipeline.get("pixel_verification"), dict)
        else {}
    )
    checks = {
        name: _pipeline_contract_check_state(pipeline, name)
        for name in (
            "integration_dq_contract",
            "integration_stack_result_contract",
            "integration_resident_result_contract",
            "integration_dq_map_pixels_match_summary",
            "integration_coverage_map_pixels_match_dq",
            "integration_rejection_map_pixels_match_dq",
            "integration_rejection_sample_counts_match_maps",
            "integration_sample_accounting_closure",
        )
    }
    rejection_sample_accounting = _pipeline_rejection_sample_accounting(pipeline)
    sample_accounting_closure = _pipeline_sample_accounting_closure(pipeline)
    resident_winsorized_semantics = _resident_winsorized_semantics_evidence(pipeline)
    return {
        "source": source,
        "present": bool(pipeline),
        "audit_type": pipeline.get("audit_type"),
        "status": pipeline.get("status"),
        "passed": pipeline.get("passed"),
        "check_count": len(pipeline.get("checks") or []) or _int_value(pipeline.get("check_count")),
        "failed_checks": list(pipeline.get("failed_checks") or []),
        "integration_output_count": len(integration.get("outputs") or []),
        "integration_map_count": len(integration.get("maps") or []),
        "pixel_verification_enabled": pixel_verification.get("enabled"),
        "pixel_verification_tile_size": pixel_verification.get("tile_size"),
        "rejection_sample_accounting": rejection_sample_accounting,
        "rejection_sample_accounting_status": rejection_sample_accounting.get("status"),
        "rejection_sample_accounting_failed_count": rejection_sample_accounting.get(
            "failed_count"
        ),
        "rejection_sample_accounting_required_count": rejection_sample_accounting.get(
            "required_count"
        ),
        "rejection_sample_accounting_verified_count": rejection_sample_accounting.get(
            "verified_count"
        ),
        "sample_accounting_closure": sample_accounting_closure,
        "sample_accounting_closure_status": sample_accounting_closure.get("status"),
        "sample_accounting_closure_failed_count": sample_accounting_closure.get(
            "failed_count"
        ),
        "sample_accounting_closure_present_count": sample_accounting_closure.get(
            "present_count"
        ),
        "sample_accounting_closure_required_count": sample_accounting_closure.get(
            "required_count"
        ),
        "resident_winsorized_semantics": resident_winsorized_semantics,
        "resident_winsorized_semantics_status": resident_winsorized_semantics.get(
            "status"
        ),
        "resident_winsorized_semantics_required_count": (
            resident_winsorized_semantics.get("required_count")
        ),
        "resident_winsorized_semantics_legacy_completion_count": (
            resident_winsorized_semantics.get("legacy_completion_count")
        ),
        "checks": checks,
    }


def _resident_winsorized_semantics_evidence(pipeline: dict[str, Any]) -> dict[str, Any]:
    integration = pipeline.get("integration") if isinstance(pipeline.get("integration"), dict) else {}
    outputs = integration.get("outputs")
    if not isinstance(outputs, list):
        outputs = []
    rows: list[dict[str, Any]] = []
    for output in outputs:
        if not isinstance(output, dict):
            continue
        resident_contract = (
            output.get("resident_result_contract")
            if isinstance(output.get("resident_result_contract"), dict)
            else {}
        )
        contract = (
            resident_contract.get("contract")
            if isinstance(resident_contract.get("contract"), dict)
            else {}
        )
        semantics = (
            contract.get("rejection_semantics")
            if isinstance(contract.get("rejection_semantics"), dict)
            else {}
        )
        if not semantics:
            continue
        descriptor = (
            semantics.get("descriptor")
            if isinstance(semantics.get("descriptor"), dict)
            else {}
        )
        rows.append(
            {
                "item": output.get("item"),
                "required": bool(semantics.get("required")),
                "present": bool(semantics.get("present")),
                "passed": bool(semantics.get("passed")),
                "status": semantics.get("status"),
                "rejection": semantics.get("rejection"),
                "descriptor_source": semantics.get("descriptor_source"),
                "integration_results_descriptor_present": semantics.get(
                    "integration_results_descriptor_present"
                ),
                "resident_artifacts_descriptor_present": semantics.get(
                    "resident_artifacts_descriptor_present"
                ),
                "legacy_completion_applied": semantics.get("legacy_completion_applied"),
                "legacy_completion_source": semantics.get("legacy_completion_source"),
                "resident_winsorized_mode": descriptor.get("resident_winsorized_mode"),
                "algorithm": descriptor.get("algorithm"),
                "scale_estimator": descriptor.get("scale_estimator"),
                "cpu_baseline_parity": descriptor.get("cpu_baseline_parity"),
                "parity_status": descriptor.get("parity_status"),
                "approximation": descriptor.get("approximation"),
            }
        )

    required_rows = [row for row in rows if row.get("required")]
    failed_rows = [row for row in required_rows if row.get("passed") is not True]
    legacy_completed = [row for row in required_rows if row.get("legacy_completion_applied") is True]
    if required_rows:
        status = "passed" if not failed_rows else "failed"
    elif rows:
        status = "not_required"
    else:
        status = "not_available"
    return {
        "schema_version": 1,
        "status": status,
        "ready": status in {"passed", "not_required", "not_available"},
        "scope": "sparse_or_not_supplied" if status == "not_available" else status,
        "output_count": len(rows),
        "required_count": len(required_rows),
        "failed_count": len(failed_rows),
        "legacy_completion_count": len(legacy_completed),
        "descriptor_sources": sorted(
            {
                str(row.get("descriptor_source"))
                for row in rows
                if row.get("descriptor_source") is not None
            }
        ),
        "failed_items": failed_rows,
        "rows": rows,
    }


def _runtime_compare_ready(
    runtime_compare: dict[str, Any],
    *,
    min_runtime_runs: int,
    max_elapsed_ratio_vs_best: float,
    ignore_warmup_runs: int,
) -> tuple[bool, dict[str, Any]]:
    if not runtime_compare:
        return False, {"present": False}
    summary = runtime_compare.get("summary") if isinstance(runtime_compare.get("summary"), dict) else {}
    runs = runtime_compare.get("runs") if isinstance(runtime_compare.get("runs"), list) else []
    ranked = runtime_compare.get("ranked_runs") if isinstance(runtime_compare.get("ranked_runs"), list) else []
    recommendation = str(summary.get("recommendation") or "")
    run_count = int(summary.get("run_count") or len(runs))
    warmup_count = max(0, int(ignore_warmup_runs))
    ignored_runs = [row for row in runs[:warmup_count] if isinstance(row, dict)]
    considered_runs = [row for row in runs[warmup_count:] if isinstance(row, dict)]
    if considered_runs:
        considered_ranked = sorted(
            considered_runs,
            key=lambda row: (
                float("inf") if _number(row.get("total_elapsed_s")) is None else float(row["total_elapsed_s"]),
                str(row.get("label")),
            ),
        )
        best_elapsed = _number(considered_ranked[0].get("total_elapsed_s"))
        best_label = considered_ranked[0].get("label")
    else:
        considered_ranked = []
        best_elapsed = None
        best_label = None
    elapsed_values = [
        value
        for value in (_number(row.get("total_elapsed_s")) for row in considered_runs if isinstance(row, dict))
        if value is not None
    ]
    slowest_elapsed = max(elapsed_values) if elapsed_values else None
    ratio_vs_best = (
        None
        if best_elapsed in (None, 0.0) or slowest_elapsed is None
        else float(slowest_elapsed) / float(best_elapsed)
    )
    unstable_recommendations = {
        "missing_timing",
        "no_runs",
        "repeat_with_warm_cache_or_dedicated_io_window",
    }
    ready = (
        len(considered_runs) >= int(min_runtime_runs)
        and bool(considered_ranked or ranked)
        and recommendation not in unstable_recommendations
        and ratio_vs_best is not None
        and ratio_vs_best <= float(max_elapsed_ratio_vs_best)
    )
    return ready, {
        "present": True,
        "run_count": run_count,
        "considered_run_count": len(considered_runs),
        "ignored_warmup_run_count": len(ignored_runs),
        "ignored_warmup_labels": [row.get("label") for row in ignored_runs],
        "required_min_runtime_runs": int(min_runtime_runs),
        "recommendation": recommendation,
        "best_label": best_label or summary.get("best_label"),
        "best_elapsed_s": best_elapsed,
        "slowest_elapsed_s": slowest_elapsed,
        "elapsed_ratio_vs_best": ratio_vs_best,
        "max_elapsed_ratio_vs_best": float(max_elapsed_ratio_vs_best),
    }


def _preflight_evidence(preflight: dict[str, Any]) -> dict[str, Any]:
    if not preflight:
        return {"present": False, "ready_to_execute": None, "recommendation": None}
    gpu = preflight.get("gpu") if isinstance(preflight.get("gpu"), dict) else {}
    return {
        "present": True,
        "ready_to_execute": preflight.get("ready_to_execute"),
        "recommendation": preflight.get("recommendation"),
        "gpu_status": gpu.get("status"),
        "gpu_reason": gpu.get("reason"),
        "gpu_utilization_percent": gpu.get("utilization_percent"),
        "gpu_free_mib": gpu.get("free_mib"),
    }


_PUBLICATION_RUNTIME_DEFAULT_CHECKS = (
    "publish_preflight_stack_engine_runtime_default_ready",
    "phase2_publish_preflight_stack_engine_runtime_default_ready",
    "phase2_publish_preflight_stack_engine_runtime_default_matches_publish_preflight",
)


_PUBLICATION_DIRECT_RUNTIME_CHECKS = (
    "publish_preflight_direct_runtime_evidence_ready",
    "phase2_publish_preflight_direct_runtime_evidence_ready",
    "phase2_publish_preflight_direct_runtime_evidence_matches_publish_preflight",
)

_PUBLICATION_QUALITY_COMPARE_CHECKS = (
    "publish_preflight_quality_metrics_compare_ready",
    "phase2_publish_preflight_quality_metrics_compare_ready",
    "phase2_publish_preflight_quality_metrics_compare_matches_publish_preflight",
)

_PUBLICATION_RELEASE_QUALITY_GUARD_CHECKS = (
    "publish_preflight_release_quality_publication_guard_ready",
    "phase2_publish_preflight_release_quality_publication_guard_ready",
    (
        "phase2_publish_preflight_release_quality_publication_guard_"
        "matches_publish_preflight"
    ),
)

_PUBLICATION_RELEASE_QUALITY_GUARD_FINAL_FIELDS = (
    "release_matrix_check",
    "release_matrix_default_check",
    "release_default_promotion_check",
    "release_matrix_default_match_check",
    "release_matrix_manifest_match_check",
)

_PUBLICATION_RELEASE_QUALITY_GUARD_LEGACY_FINAL_EVIDENCE_FIELDS = (
    "matrix_final_checks_ready",
    "matrix_final_checks_match",
    "matrix_raw_final_checks_ready",
    "matrix_phase2_final_checks_ready",
    "matrix_default_final_checks_ready",
    "matrix_default_final_checks_match",
    "matrix_default_raw_final_checks_ready",
    "matrix_default_phase2_final_checks_ready",
    "default_promotion_final_checks_ready",
    "default_promotion_final_checks_match",
    "default_promotion_raw_final_checks_ready",
    "default_promotion_phase2_final_checks_ready",
)

_PUBLICATION_RELEASE_QUALITY_GUARD_FINAL_EVIDENCE_DETAIL_FIELDS = (
    "matrix_final_evidence_ready",
    "matrix_final_evidence_match",
    "matrix_raw_final_evidence_ready",
    "matrix_phase2_final_evidence_ready",
    "matrix_default_final_evidence_ready",
    "matrix_default_final_evidence_match",
    "matrix_default_raw_final_evidence_ready",
    "matrix_default_phase2_final_evidence_ready",
    "default_promotion_final_evidence_ready",
    "default_promotion_final_evidence_match",
    "default_promotion_raw_final_evidence_ready",
    "default_promotion_phase2_final_evidence_ready",
)

_PUBLICATION_RELEASE_QUALITY_GUARD_FINAL_EVIDENCE_FIELDS = (
    *_PUBLICATION_RELEASE_QUALITY_GUARD_LEGACY_FINAL_EVIDENCE_FIELDS,
    *_PUBLICATION_RELEASE_QUALITY_GUARD_FINAL_EVIDENCE_DETAIL_FIELDS,
)

_PUBLICATION_RELEASE_QUALITY_GUARD_FINAL_EVIDENCE_PREFIXES = (
    "matrix",
    "matrix_default",
    "default_promotion",
)

_DIRECT_RUNTIME_ACCEPTANCE_SOURCE = "explicit_resident_artifacts_json"
_DIRECT_RUNTIME_PIPELINE_CALIBRATION_SOURCE = "resident_artifacts_json_fallback"
_DIRECT_RUNTIME_MIN_RESIDENT_LIGHTS = 200


def _publication_release_quality_final_evidence_present(
    layer: dict[str, Any],
) -> bool:
    return any(
        layer.get(field) is not None
        for field in _PUBLICATION_RELEASE_QUALITY_GUARD_FINAL_EVIDENCE_FIELDS
    )


def _publication_release_quality_legacy_final_evidence_present(
    layer: dict[str, Any],
) -> bool:
    return any(
        layer.get(field) is not None
        for field in _PUBLICATION_RELEASE_QUALITY_GUARD_LEGACY_FINAL_EVIDENCE_FIELDS
    )


def _publication_release_quality_final_evidence_detail_present(
    layer: dict[str, Any],
) -> bool:
    return any(
        layer.get(field) is not None
        for field in _PUBLICATION_RELEASE_QUALITY_GUARD_FINAL_EVIDENCE_DETAIL_FIELDS
    )


def _publication_release_quality_final_evidence_prefix_ready(
    layer: dict[str, Any],
    *,
    prefix: str,
    ready_suffix: str,
    match_suffix: str,
    raw_ready_suffix: str,
    phase2_ready_suffix: str,
) -> bool:
    final_ready = layer.get(f"{prefix}_{ready_suffix}")
    final_match = layer.get(f"{prefix}_{match_suffix}")
    raw_ready = layer.get(f"{prefix}_{raw_ready_suffix}")
    phase2_ready = layer.get(f"{prefix}_{phase2_ready_suffix}")
    if (
        final_ready is None
        and final_match is None
        and raw_ready is None
        and phase2_ready is None
    ):
        return False
    compatible_missing = (
        final_ready is True
        and final_match is True
        and raw_ready is None
        and phase2_ready is None
    )
    return compatible_missing or (
        final_ready is True
        and final_match is True
        and raw_ready is True
        and phase2_ready is True
    )


def _publication_release_quality_legacy_final_evidence_prefix_ready(
    layer: dict[str, Any],
    *,
    prefix: str,
) -> bool:
    return _publication_release_quality_final_evidence_prefix_ready(
        layer,
        prefix=prefix,
        ready_suffix="final_checks_ready",
        match_suffix="final_checks_match",
        raw_ready_suffix="raw_final_checks_ready",
        phase2_ready_suffix="phase2_final_checks_ready",
    )


def _publication_release_quality_final_evidence_detail_prefix_ready(
    layer: dict[str, Any],
    *,
    prefix: str,
) -> bool:
    return _publication_release_quality_final_evidence_prefix_ready(
        layer,
        prefix=prefix,
        ready_suffix="final_evidence_ready",
        match_suffix="final_evidence_match",
        raw_ready_suffix="raw_final_evidence_ready",
        phase2_ready_suffix="phase2_final_evidence_ready",
    )


def _publication_release_quality_legacy_final_evidence_ready(
    layer: dict[str, Any],
) -> bool:
    return _publication_release_quality_legacy_final_evidence_present(layer) and all(
        _publication_release_quality_legacy_final_evidence_prefix_ready(
            layer,
            prefix=prefix,
        )
        for prefix in _PUBLICATION_RELEASE_QUALITY_GUARD_FINAL_EVIDENCE_PREFIXES
    )


def _publication_release_quality_final_evidence_detail_ready(
    layer: dict[str, Any],
) -> bool:
    return _publication_release_quality_final_evidence_detail_present(layer) and all(
        _publication_release_quality_final_evidence_detail_prefix_ready(
            layer,
            prefix=prefix,
        )
        for prefix in _PUBLICATION_RELEASE_QUALITY_GUARD_FINAL_EVIDENCE_PREFIXES
    )


def _publication_release_quality_final_evidence_ready(
    layer: dict[str, Any],
) -> bool:
    if not _publication_release_quality_final_evidence_present(layer):
        return True
    if _publication_release_quality_final_evidence_detail_present(layer):
        return _publication_release_quality_final_evidence_detail_ready(
            layer
        )
    return _publication_release_quality_legacy_final_evidence_ready(
        layer
    )


def _publication_audit_runtime_default_evidence(
    publication_audit: dict[str, Any],
) -> dict[str, Any]:
    if not publication_audit:
        return {"present": False, "status": None, "passed": None}
    checks = {
        name: _pipeline_contract_check_state(publication_audit, name)
        for name in _PUBLICATION_RUNTIME_DEFAULT_CHECKS
    }
    layers = (
        publication_audit.get("layers")
        if isinstance(publication_audit.get("layers"), dict)
        else {}
    )
    raw_layer = (
        layers.get("publish_preflight_stack_engine_runtime_default")
        if isinstance(layers.get("publish_preflight_stack_engine_runtime_default"), dict)
        else {}
    )
    phase2_layer = (
        layers.get("phase2_publish_preflight_stack_engine_runtime_default")
        if isinstance(
            layers.get("phase2_publish_preflight_stack_engine_runtime_default"),
            dict,
        )
        else {}
    )
    checks_passed = all(value is True for value in checks.values())
    return {
        "present": True,
        "artifact_type": publication_audit.get("artifact_type"),
        "status": publication_audit.get("status"),
        "passed": publication_audit.get("passed"),
        "recommendation": publication_audit.get("recommendation"),
        "failed_checks": publication_audit.get("failed_checks") or [],
        "checks": checks,
        "checks_passed": checks_passed,
        "raw_ready": raw_layer.get("ready"),
        "raw_matrix_status": raw_layer.get("matrix_acceptance_status"),
        "raw_pipeline_status": raw_layer.get("matrix_pipeline_status"),
        "raw_legacy_master_count": raw_layer.get("matrix_acceptance_legacy_master_count"),
        "raw_failed_output_count": raw_layer.get("matrix_pipeline_failed_output_count"),
        "phase2_ready": phase2_layer.get("ready"),
        "phase2_check_passed": phase2_layer.get("phase2_check_passed"),
        "phase2_matrix_status": phase2_layer.get("matrix_acceptance_status"),
        "phase2_pipeline_status": phase2_layer.get("matrix_pipeline_status"),
        "phase2_legacy_master_count": phase2_layer.get(
            "matrix_acceptance_legacy_master_count"
        ),
        "phase2_failed_output_count": phase2_layer.get(
            "matrix_pipeline_failed_output_count"
        ),
    }


def _publication_audit_direct_runtime_evidence(
    publication_audit: dict[str, Any],
) -> dict[str, Any]:
    if not publication_audit:
        return {"present": False, "status": None, "passed": None}
    checks = {
        name: _pipeline_contract_check_state(publication_audit, name)
        for name in _PUBLICATION_DIRECT_RUNTIME_CHECKS
    }
    layers = (
        publication_audit.get("layers")
        if isinstance(publication_audit.get("layers"), dict)
        else {}
    )
    raw_layer = (
        layers.get("publish_preflight_direct_runtime_evidence")
        if isinstance(layers.get("publish_preflight_direct_runtime_evidence"), dict)
        else {}
    )
    phase2_layer = (
        layers.get("phase2_publish_preflight_direct_runtime_evidence")
        if isinstance(layers.get("phase2_publish_preflight_direct_runtime_evidence"), dict)
        else {}
    )
    checks_passed = all(value is True for value in checks.values())
    raw_matrix_lights = _int_value(raw_layer.get("matrix_pipeline_resident_lights"))
    raw_default_lights = _int_value(
        raw_layer.get("default_promotion_pipeline_resident_lights")
    )
    phase2_matrix_lights = _int_value(phase2_layer.get("matrix_pipeline_resident_lights"))
    phase2_default_lights = _int_value(
        phase2_layer.get("default_promotion_pipeline_resident_lights")
    )
    raw_source_ready = (
        raw_layer.get("matrix_acceptance_source") == _DIRECT_RUNTIME_ACCEPTANCE_SOURCE
        and raw_layer.get("default_promotion_acceptance_source")
        == _DIRECT_RUNTIME_ACCEPTANCE_SOURCE
        and raw_layer.get("matrix_pipeline_calibration_source")
        == _DIRECT_RUNTIME_PIPELINE_CALIBRATION_SOURCE
        and raw_layer.get("default_promotion_pipeline_calibration_source")
        == _DIRECT_RUNTIME_PIPELINE_CALIBRATION_SOURCE
    )
    phase2_source_ready = (
        phase2_layer.get("matrix_acceptance_source") == _DIRECT_RUNTIME_ACCEPTANCE_SOURCE
        and phase2_layer.get("default_promotion_acceptance_source")
        == _DIRECT_RUNTIME_ACCEPTANCE_SOURCE
        and phase2_layer.get("matrix_pipeline_calibration_source")
        == _DIRECT_RUNTIME_PIPELINE_CALIBRATION_SOURCE
        and phase2_layer.get("default_promotion_pipeline_calibration_source")
        == _DIRECT_RUNTIME_PIPELINE_CALIBRATION_SOURCE
    )
    raw_count_ready = (
        _int_value(raw_layer.get("matrix_acceptance_check_count")) is not None
        and _int_value(raw_layer.get("matrix_acceptance_check_count")) > 0
        and _int_value(raw_layer.get("default_promotion_acceptance_check_count"))
        is not None
        and _int_value(raw_layer.get("default_promotion_acceptance_check_count")) > 0
        and raw_matrix_lights is not None
        and raw_matrix_lights >= _DIRECT_RUNTIME_MIN_RESIDENT_LIGHTS
        and raw_default_lights is not None
        and raw_default_lights >= _DIRECT_RUNTIME_MIN_RESIDENT_LIGHTS
    )
    phase2_count_ready = (
        _int_value(phase2_layer.get("matrix_acceptance_check_count")) is not None
        and _int_value(phase2_layer.get("matrix_acceptance_check_count")) > 0
        and _int_value(phase2_layer.get("default_promotion_acceptance_check_count"))
        is not None
        and _int_value(phase2_layer.get("default_promotion_acceptance_check_count")) > 0
        and phase2_matrix_lights is not None
        and phase2_matrix_lights >= _DIRECT_RUNTIME_MIN_RESIDENT_LIGHTS
        and phase2_default_lights is not None
        and phase2_default_lights >= _DIRECT_RUNTIME_MIN_RESIDENT_LIGHTS
    )
    raw_leaf_checks_ready = (
        raw_layer.get("matrix_acceptance_passed") is True
        and raw_layer.get("matrix_pipeline_passed") is True
        and raw_layer.get("default_promotion_acceptance_passed") is True
        and raw_layer.get("default_promotion_pipeline_passed") is True
        and raw_layer.get("matches_default_promotion") is True
    )
    phase2_leaf_checks_ready = (
        phase2_layer.get("matrix_acceptance_passed") is True
        and phase2_layer.get("matrix_pipeline_passed") is True
        and phase2_layer.get("default_promotion_acceptance_passed") is True
        and phase2_layer.get("default_promotion_pipeline_passed") is True
        and phase2_layer.get("matches_default_promotion") is True
        and phase2_layer.get("phase2_check_passed") is True
    )
    ready = (
        publication_audit.get("status") == "passed"
        and publication_audit.get("passed") is True
        and checks_passed
        and raw_layer.get("ready") is True
        and phase2_layer.get("ready") is True
        and raw_source_ready
        and phase2_source_ready
        and raw_count_ready
        and phase2_count_ready
        and raw_leaf_checks_ready
        and phase2_leaf_checks_ready
    )
    return {
        "present": True,
        "artifact_type": publication_audit.get("artifact_type"),
        "status": publication_audit.get("status"),
        "passed": publication_audit.get("passed"),
        "recommendation": publication_audit.get("recommendation"),
        "failed_checks": publication_audit.get("failed_checks") or [],
        "checks": checks,
        "checks_passed": checks_passed,
        "ready": ready,
        "raw_ready": raw_layer.get("ready"),
        "raw_matrix_acceptance_source": raw_layer.get("matrix_acceptance_source"),
        "raw_default_promotion_acceptance_source": raw_layer.get(
            "default_promotion_acceptance_source"
        ),
        "raw_matrix_acceptance_check_count": raw_layer.get(
            "matrix_acceptance_check_count"
        ),
        "raw_default_promotion_acceptance_check_count": raw_layer.get(
            "default_promotion_acceptance_check_count"
        ),
        "raw_matrix_pipeline_calibration_source": raw_layer.get(
            "matrix_pipeline_calibration_source"
        ),
        "raw_default_promotion_pipeline_calibration_source": raw_layer.get(
            "default_promotion_pipeline_calibration_source"
        ),
        "raw_matrix_pipeline_resident_lights": raw_matrix_lights,
        "raw_default_promotion_pipeline_resident_lights": raw_default_lights,
        "raw_source_ready": raw_source_ready,
        "raw_count_ready": raw_count_ready,
        "raw_leaf_checks_ready": raw_leaf_checks_ready,
        "phase2_ready": phase2_layer.get("ready"),
        "phase2_check_passed": phase2_layer.get("phase2_check_passed"),
        "phase2_matrix_acceptance_source": phase2_layer.get(
            "matrix_acceptance_source"
        ),
        "phase2_default_promotion_acceptance_source": phase2_layer.get(
            "default_promotion_acceptance_source"
        ),
        "phase2_matrix_acceptance_check_count": phase2_layer.get(
            "matrix_acceptance_check_count"
        ),
        "phase2_default_promotion_acceptance_check_count": phase2_layer.get(
            "default_promotion_acceptance_check_count"
        ),
        "phase2_matrix_pipeline_calibration_source": phase2_layer.get(
            "matrix_pipeline_calibration_source"
        ),
        "phase2_default_promotion_pipeline_calibration_source": phase2_layer.get(
            "default_promotion_pipeline_calibration_source"
        ),
        "phase2_matrix_pipeline_resident_lights": phase2_matrix_lights,
        "phase2_default_promotion_pipeline_resident_lights": phase2_default_lights,
        "phase2_source_ready": phase2_source_ready,
        "phase2_count_ready": phase2_count_ready,
        "phase2_leaf_checks_ready": phase2_leaf_checks_ready,
    }


def _publication_audit_quality_compare_evidence(
    publication_audit: dict[str, Any],
) -> dict[str, Any]:
    if not publication_audit:
        return {
            "present": False,
            "status": None,
            "passed": None,
            "ready": None,
            "quality_compare_present": False,
        }
    checks = {
        name: _pipeline_contract_check_state(publication_audit, name)
        for name in _PUBLICATION_QUALITY_COMPARE_CHECKS
    }
    layers = (
        publication_audit.get("layers")
        if isinstance(publication_audit.get("layers"), dict)
        else {}
    )
    raw_layer = (
        layers.get("publish_preflight_quality_metrics_compare")
        if isinstance(layers.get("publish_preflight_quality_metrics_compare"), dict)
        else {}
    )
    phase2_layer = (
        layers.get("phase2_publish_preflight_quality_metrics_compare")
        if isinstance(
            layers.get("phase2_publish_preflight_quality_metrics_compare"),
            dict,
        )
        else {}
    )
    checks_seen = any(value is not None for value in checks.values())
    compatible_missing = not raw_layer and not phase2_layer and not checks_seen
    checks_passed = compatible_missing or all(value is True for value in checks.values())
    raw_present = raw_layer.get("present")
    phase2_present = phase2_layer.get("present")
    quality_compare_present = raw_present is True or phase2_present is True
    quality_compare_absent = raw_present is False and phase2_present is False
    raw_ready = raw_layer.get("ready") is True
    phase2_ready = phase2_layer.get("ready") is True
    layers_ready = (
        compatible_missing
        or (quality_compare_absent and raw_ready and phase2_ready)
        or (raw_present is True and phase2_present is True and raw_ready and phase2_ready)
    )
    ready = compatible_missing or (
        publication_audit.get("status") == "passed"
        and publication_audit.get("passed") is True
        and checks_passed
        and layers_ready
    )
    return {
        "present": True,
        "artifact_type": publication_audit.get("artifact_type"),
        "status": publication_audit.get("status"),
        "passed": publication_audit.get("passed"),
        "recommendation": publication_audit.get("recommendation"),
        "failed_checks": publication_audit.get("failed_checks") or [],
        "checks": checks,
        "checks_passed": checks_passed,
        "ready": ready,
        "compatible_missing": compatible_missing,
        "quality_compare_present": quality_compare_present,
        "raw_present": raw_present,
        "raw_ready": raw_layer.get("ready"),
        "raw_matrix_present": raw_layer.get("matrix_present"),
        "raw_matrix_ready": raw_layer.get("matrix_ready"),
        "raw_matrix_status": raw_layer.get("matrix_status"),
        "raw_matrix_failed_check_count": raw_layer.get("matrix_failed_check_count"),
        "raw_default_promotion_present": raw_layer.get(
            "default_promotion_present"
        ),
        "raw_default_promotion_ready": raw_layer.get("default_promotion_ready"),
        "raw_default_promotion_status": raw_layer.get("default_promotion_status"),
        "raw_default_promotion_failed_check_count": raw_layer.get(
            "default_promotion_failed_check_count"
        ),
        "raw_matrix_handoff_passed": raw_layer.get("matrix_handoff_passed"),
        "raw_default_promotion_handoff_passed": raw_layer.get(
            "default_promotion_handoff_passed"
        ),
        "raw_matches_default_promotion": raw_layer.get("matches_default_promotion"),
        "phase2_present": phase2_present,
        "phase2_ready": phase2_layer.get("ready"),
        "phase2_check_passed": phase2_layer.get("phase2_check_passed"),
        "phase2_matrix_present": phase2_layer.get("matrix_present"),
        "phase2_matrix_ready": phase2_layer.get("matrix_ready"),
        "phase2_matrix_status": phase2_layer.get("matrix_status"),
        "phase2_matrix_failed_check_count": phase2_layer.get(
            "matrix_failed_check_count"
        ),
        "phase2_default_promotion_present": phase2_layer.get(
            "default_promotion_present"
        ),
        "phase2_default_promotion_ready": phase2_layer.get(
            "default_promotion_ready"
        ),
        "phase2_default_promotion_status": phase2_layer.get(
            "default_promotion_status"
        ),
        "phase2_default_promotion_failed_check_count": phase2_layer.get(
            "default_promotion_failed_check_count"
        ),
        "phase2_matrix_handoff_passed": phase2_layer.get("matrix_handoff_passed"),
        "phase2_default_promotion_handoff_passed": phase2_layer.get(
            "default_promotion_handoff_passed"
        ),
        "phase2_matches_default_promotion": phase2_layer.get(
            "matches_default_promotion"
        ),
    }


def _publication_audit_release_quality_guard_evidence(
    publication_audit: dict[str, Any],
) -> dict[str, Any]:
    if not publication_audit:
        return {
            "present": False,
            "status": None,
            "passed": None,
            "ready": None,
            "release_quality_guard_present": False,
        }
    checks = {
        name: _pipeline_contract_check_state(publication_audit, name)
        for name in _PUBLICATION_RELEASE_QUALITY_GUARD_CHECKS
    }
    layers = (
        publication_audit.get("layers")
        if isinstance(publication_audit.get("layers"), dict)
        else {}
    )
    raw_layer = (
        layers.get("publish_preflight_release_quality_publication_guard")
        if isinstance(
            layers.get("publish_preflight_release_quality_publication_guard"),
            dict,
        )
        else {}
    )
    phase2_layer = (
        layers.get("phase2_publish_preflight_release_quality_publication_guard")
        if isinstance(
            layers.get("phase2_publish_preflight_release_quality_publication_guard"),
            dict,
        )
        else {}
    )
    checks_seen = any(value is not None for value in checks.values())
    compatible_missing = not raw_layer and not phase2_layer and not checks_seen
    checks_passed = compatible_missing or all(value is True for value in checks.values())
    raw_present = raw_layer.get("present")
    phase2_present = phase2_layer.get("present")
    guard_present = raw_present is True or phase2_present is True
    guard_absent = raw_present is False and phase2_present is False
    raw_ready = raw_layer.get("ready") is True
    phase2_ready = phase2_layer.get("ready") is True
    raw_final_present = any(
        raw_layer.get(field) is not None
        for field in _PUBLICATION_RELEASE_QUALITY_GUARD_FINAL_FIELDS
    )
    phase2_final_present = any(
        phase2_layer.get(field) is not None
        for field in _PUBLICATION_RELEASE_QUALITY_GUARD_FINAL_FIELDS
    )
    final_checks_compatible_missing = not raw_final_present and not phase2_final_present
    raw_final_checks_ready = not raw_final_present or all(
        raw_layer.get(field) is True
        for field in _PUBLICATION_RELEASE_QUALITY_GUARD_FINAL_FIELDS
    )
    phase2_final_checks_ready = not phase2_final_present or all(
        phase2_layer.get(field) is True
        for field in _PUBLICATION_RELEASE_QUALITY_GUARD_FINAL_FIELDS
    )
    final_checks_match = raw_final_present == phase2_final_present and all(
        raw_layer.get(field) == phase2_layer.get(field)
        for field in _PUBLICATION_RELEASE_QUALITY_GUARD_FINAL_FIELDS
    )
    final_checks_ready = (
        final_checks_compatible_missing
        or (
            raw_final_present
            and phase2_final_present
            and raw_final_checks_ready
            and phase2_final_checks_ready
            and final_checks_match
        )
    )
    raw_final_evidence_present = _publication_release_quality_final_evidence_present(
        raw_layer
    )
    phase2_final_evidence_present = (
        _publication_release_quality_final_evidence_present(phase2_layer)
    )
    final_evidence_compatible_missing = (
        not raw_final_evidence_present and not phase2_final_evidence_present
    )
    raw_final_evidence_ready = (
        not raw_final_evidence_present
        or _publication_release_quality_final_evidence_ready(raw_layer)
    )
    phase2_final_evidence_ready = (
        not phase2_final_evidence_present
        or _publication_release_quality_final_evidence_ready(phase2_layer)
    )
    final_evidence_match = (
        raw_final_evidence_present == phase2_final_evidence_present
        and all(
            raw_layer.get(field) == phase2_layer.get(field)
            for field in _PUBLICATION_RELEASE_QUALITY_GUARD_FINAL_EVIDENCE_FIELDS
        )
    )
    final_evidence_ready = (
        final_evidence_compatible_missing
        or (
            raw_final_evidence_present
            and phase2_final_evidence_present
            and raw_final_evidence_ready
            and phase2_final_evidence_ready
            and final_evidence_match
        )
    )
    layers_ready = (
        compatible_missing
        or (guard_absent and raw_ready and phase2_ready)
        or (
            raw_present is True
            and phase2_present is True
            and raw_ready
            and phase2_ready
            and final_checks_ready
            and final_evidence_ready
        )
    )
    ready = compatible_missing or (
        publication_audit.get("status") == "passed"
        and publication_audit.get("passed") is True
        and checks_passed
        and layers_ready
    )
    return {
        "present": True,
        "artifact_type": publication_audit.get("artifact_type"),
        "status": publication_audit.get("status"),
        "passed": publication_audit.get("passed"),
        "recommendation": publication_audit.get("recommendation"),
        "failed_checks": publication_audit.get("failed_checks") or [],
        "checks": checks,
        "checks_passed": checks_passed,
        "ready": ready,
        "compatible_missing": compatible_missing,
        "release_quality_guard_present": guard_present,
        "final_checks_compatible_missing": final_checks_compatible_missing,
        "final_checks_ready": final_checks_ready,
        "final_checks_match": final_checks_match,
        "raw_final_checks_present": raw_final_present,
        "raw_final_checks_ready": raw_final_checks_ready,
        "phase2_final_checks_present": phase2_final_present,
        "phase2_final_checks_ready": phase2_final_checks_ready,
        "final_evidence_compatible_missing": final_evidence_compatible_missing,
        "final_evidence_ready": final_evidence_ready,
        "final_evidence_match": final_evidence_match,
        "raw_final_evidence_present": raw_final_evidence_present,
        "raw_final_evidence_ready": raw_final_evidence_ready,
        "phase2_final_evidence_present": phase2_final_evidence_present,
        "phase2_final_evidence_ready": phase2_final_evidence_ready,
        "raw_present": raw_present,
        "raw_ready": raw_layer.get("ready"),
        "raw_matrix_present": raw_layer.get("matrix_present"),
        "raw_matrix_ready": raw_layer.get("matrix_ready"),
        "raw_matrix_check_passed": raw_layer.get("matrix_check_passed"),
        "raw_matrix_layers_ready": raw_layer.get("matrix_layers_ready"),
        "raw_matrix_raw_status": raw_layer.get("matrix_raw_status"),
        "raw_matrix_phase2_status": raw_layer.get("matrix_phase2_status"),
        "raw_matrix_default_ready": raw_layer.get("matrix_default_ready"),
        "raw_matrix_default_raw_status": raw_layer.get("matrix_default_raw_status"),
        "raw_matrix_default_phase2_status": raw_layer.get(
            "matrix_default_phase2_status"
        ),
        "raw_default_promotion_present": raw_layer.get("default_promotion_present"),
        "raw_default_promotion_ready": raw_layer.get("default_promotion_ready"),
        "raw_default_promotion_check_passed": raw_layer.get(
            "default_promotion_check_passed"
        ),
        "raw_default_promotion_layers_ready": raw_layer.get(
            "default_promotion_layers_ready"
        ),
        "raw_default_promotion_raw_status": raw_layer.get(
            "default_promotion_raw_status"
        ),
        "raw_default_promotion_phase2_status": raw_layer.get(
            "default_promotion_phase2_status"
        ),
        "raw_matrix_check": raw_layer.get("matrix_check"),
        "raw_matrix_default_check": raw_layer.get("matrix_default_check"),
        "raw_default_promotion_check": raw_layer.get("default_promotion_check"),
        "raw_matrix_default_match_check": raw_layer.get(
            "matrix_default_match_check"
        ),
        "raw_matrix_manifest_match_check": raw_layer.get(
            "matrix_manifest_match_check"
        ),
        "raw_release_matrix_check": raw_layer.get("release_matrix_check"),
        "raw_release_matrix_default_check": raw_layer.get(
            "release_matrix_default_check"
        ),
        "raw_release_default_promotion_check": raw_layer.get(
            "release_default_promotion_check"
        ),
        "raw_release_matrix_default_match_check": raw_layer.get(
            "release_matrix_default_match_check"
        ),
        "raw_release_matrix_manifest_match_check": raw_layer.get(
            "release_matrix_manifest_match_check"
        ),
        "phase2_present": phase2_present,
        "phase2_ready": phase2_layer.get("ready"),
        "phase2_check_passed": phase2_layer.get("phase2_check_passed"),
        "phase2_matrix_present": phase2_layer.get("matrix_present"),
        "phase2_matrix_ready": phase2_layer.get("matrix_ready"),
        "phase2_matrix_check_passed": phase2_layer.get("matrix_check_passed"),
        "phase2_matrix_layers_ready": phase2_layer.get("matrix_layers_ready"),
        "phase2_matrix_raw_status": phase2_layer.get("matrix_raw_status"),
        "phase2_matrix_phase2_status": phase2_layer.get("matrix_phase2_status"),
        "phase2_matrix_default_ready": phase2_layer.get("matrix_default_ready"),
        "phase2_matrix_default_raw_status": phase2_layer.get(
            "matrix_default_raw_status"
        ),
        "phase2_matrix_default_phase2_status": phase2_layer.get(
            "matrix_default_phase2_status"
        ),
        "phase2_default_promotion_present": phase2_layer.get(
            "default_promotion_present"
        ),
        "phase2_default_promotion_ready": phase2_layer.get(
            "default_promotion_ready"
        ),
        "phase2_default_promotion_check_passed": phase2_layer.get(
            "default_promotion_check_passed"
        ),
        "phase2_default_promotion_layers_ready": phase2_layer.get(
            "default_promotion_layers_ready"
        ),
        "phase2_default_promotion_raw_status": phase2_layer.get(
            "default_promotion_raw_status"
        ),
        "phase2_default_promotion_phase2_status": phase2_layer.get(
            "default_promotion_phase2_status"
        ),
        "phase2_matrix_check": phase2_layer.get("matrix_check"),
        "phase2_matrix_default_check": phase2_layer.get("matrix_default_check"),
        "phase2_default_promotion_check": phase2_layer.get(
            "default_promotion_check"
        ),
        "phase2_matrix_default_match_check": phase2_layer.get(
            "matrix_default_match_check"
        ),
        "phase2_matrix_manifest_match_check": phase2_layer.get(
            "matrix_manifest_match_check"
        ),
        "phase2_release_matrix_check": phase2_layer.get("release_matrix_check"),
        "phase2_release_matrix_default_check": phase2_layer.get(
            "release_matrix_default_check"
        ),
        "phase2_release_default_promotion_check": phase2_layer.get(
            "release_default_promotion_check"
        ),
        "phase2_release_matrix_default_match_check": phase2_layer.get(
            "release_matrix_default_match_check"
        ),
        "phase2_release_matrix_manifest_match_check": phase2_layer.get(
            "release_matrix_manifest_match_check"
        ),
        **{
            f"raw_{field}": raw_layer.get(field)
            for field in _PUBLICATION_RELEASE_QUALITY_GUARD_FINAL_EVIDENCE_FIELDS
        },
        **{
            f"phase2_{field}": phase2_layer.get(field)
            for field in _PUBLICATION_RELEASE_QUALITY_GUARD_FINAL_EVIDENCE_FIELDS
        },
    }


def build_release_promotion_decision(
    *,
    acceptance_audit: str | Path,
    stack_engine_contract: str | Path | None = None,
    pipeline_contract: str | Path | None = None,
    runtime_compare: str | Path | None = None,
    repeat_preflight: str | Path | None = None,
    stack_engine_publication_audit: str | Path | None = None,
    min_speedup: float | None = None,
    min_runtime_runs: int = 2,
    max_elapsed_ratio_vs_best: float = 1.25,
    ignore_warmup_runs: int = 0,
) -> dict[str, Any]:
    acceptance = _read_json_object(acceptance_audit)
    stack_contract = _read_json_object(stack_engine_contract)
    pipeline = _read_json_object(pipeline_contract)
    runtime = _read_json_object(runtime_compare)
    preflight = _read_json_object(repeat_preflight)
    publication_audit = _read_json_object(stack_engine_publication_audit)
    speedup_summary = acceptance.get("speedup_summary") if isinstance(acceptance.get("speedup_summary"), dict) else {}
    speedup = _number(speedup_summary.get("speedup_vs_wbpp"))
    required_speedup = float(min_speedup if min_speedup is not None else speedup_summary.get("min_speedup") or 2.0)
    pipeline_release_status = _release_evidence_status(acceptance, "pipeline_contract")
    stack_release_status = _release_evidence_status(acceptance, "stack_engine_default_promotion")
    pipeline_handoff = _pipeline_handoff_evidence(acceptance, pipeline)
    runtime_ready, runtime_evidence = _runtime_compare_ready(
        runtime,
        min_runtime_runs=min_runtime_runs,
        max_elapsed_ratio_vs_best=max_elapsed_ratio_vs_best,
        ignore_warmup_runs=ignore_warmup_runs,
    )
    preflight_evidence = _preflight_evidence(preflight)
    publication_runtime_default = _publication_audit_runtime_default_evidence(
        publication_audit
    )
    publication_direct_runtime = _publication_audit_direct_runtime_evidence(
        publication_audit
    )
    publication_quality_compare = _publication_audit_quality_compare_evidence(
        publication_audit
    )
    publication_release_quality_guard = (
        _publication_audit_release_quality_guard_evidence(publication_audit)
    )
    rejection_sample_release = _rejection_sample_release_evidence(pipeline_handoff)
    sample_closure_release = _sample_closure_release_evidence(pipeline_handoff)
    resident_winsorized_semantics = (
        pipeline_handoff.get("resident_winsorized_semantics")
        if isinstance(pipeline_handoff.get("resident_winsorized_semantics"), dict)
        else {}
    )
    warp_quality_handoff = _warp_quality_handoff_evidence(acceptance)
    resident_fastpath_handoff = _resident_registration_fastpath_handoff_evidence(
        acceptance
    )

    checks = [
        _check(
            "acceptance_audit_passed",
            acceptance.get("passed") is True,
            {"status": acceptance.get("status"), "path": str(acceptance_audit)},
        ),
        _check(
            "speedup_threshold",
            speedup is not None and speedup >= required_speedup,
            {"actual": speedup, "required_min": required_speedup},
        ),
        _check(
            "pipeline_release_evidence_passed",
            pipeline_release_status == "passed" or pipeline.get("passed") is True,
            {
                "release_evidence_status": pipeline_release_status,
                "pipeline_contract_passed": pipeline.get("passed"),
                "pipeline_contract_status": pipeline.get("status"),
            },
        ),
        _check(
            "pipeline_handoff_evidence_present",
            pipeline_handoff["present"]
            and pipeline_handoff.get("audit_type") == "pipeline_invariant_contract",
            {
                "source": pipeline_handoff.get("source"),
                "audit_type": pipeline_handoff.get("audit_type"),
                "status": pipeline_handoff.get("status"),
            },
        ),
        _check(
            "pipeline_integration_dq_contract_passed",
            pipeline_handoff["checks"].get("integration_dq_contract") is True,
            {
                "source": pipeline_handoff.get("source"),
                "check": pipeline_handoff["checks"].get("integration_dq_contract"),
                "integration_output_count": pipeline_handoff.get("integration_output_count"),
                "integration_map_count": pipeline_handoff.get("integration_map_count"),
            },
        ),
        _check(
            "pipeline_result_contracts_passed",
            pipeline_handoff["checks"].get("integration_stack_result_contract") is True
            and pipeline_handoff["checks"].get("integration_resident_result_contract") is True,
            {
                "stack_result_contract": pipeline_handoff["checks"].get(
                    "integration_stack_result_contract"
                ),
                "resident_result_contract": pipeline_handoff["checks"].get(
                    "integration_resident_result_contract"
                ),
            },
        ),
        _check(
            "pipeline_resident_winsorized_semantics_handoff",
            resident_winsorized_semantics.get("ready") is True,
            resident_winsorized_semantics,
            "Resident winsorized outputs must preserve explicit or same-run backfilled semantics in the pipeline contract.",
        ),
        _check(
            "pipeline_pixel_verification_enabled",
            pipeline_handoff.get("pixel_verification_enabled") is True,
            {
                "enabled": pipeline_handoff.get("pixel_verification_enabled"),
                "tile_size": pipeline_handoff.get("pixel_verification_tile_size"),
            },
        ),
        _check(
            "pipeline_pixel_verification_passed",
            pipeline_handoff["checks"].get("integration_dq_map_pixels_match_summary") is True
            and pipeline_handoff["checks"].get("integration_coverage_map_pixels_match_dq") is True
            and pipeline_handoff["checks"].get("integration_rejection_map_pixels_match_dq") is True,
            {
                "dq_pixels": pipeline_handoff["checks"].get(
                    "integration_dq_map_pixels_match_summary"
                ),
                "coverage_pixels": pipeline_handoff["checks"].get(
                    "integration_coverage_map_pixels_match_dq"
                ),
                "rejection_pixels": pipeline_handoff["checks"].get(
                    "integration_rejection_map_pixels_match_dq"
                ),
            },
        ),
        _check(
            "pipeline_rejection_sample_accounting_passed",
            bool(rejection_sample_release["ready"]),
            rejection_sample_release,
            "Release requires the pipeline contract to prove rejection sample accounting passed, or explicitly prove it was not required.",
        ),
        _check(
            "pipeline_sample_accounting_closure_passed",
            bool(sample_closure_release["ready"]),
            sample_closure_release,
            "Release requires the pipeline contract to prove sample-closure evidence passed, or explicitly prove it was not required.",
        ),
        _check(
            "warp_quality_contract_handoff",
            bool(warp_quality_handoff["ready"]),
            warp_quality_handoff,
            "Release requires attached warp-quality acceptance evidence to be present, typed, and passing.",
        ),
        _check(
            "resident_registration_fastpath_handoff",
            bool(resident_fastpath_handoff["ready"]),
            resident_fastpath_handoff,
            "Release requires resident registration fast-path acceptance evidence to pass when the benchmark contract requires it.",
        ),
        _check(
            "stack_engine_release_evidence_passed",
            stack_release_status == "passed" or stack_contract.get("passed") is True,
            {
                "release_evidence_status": stack_release_status,
                "stack_engine_contract_passed": stack_contract.get("passed"),
                "stack_engine_contract_status": stack_contract.get("status"),
            },
        ),
        _check(
            "stack_engine_default_ready",
            _stack_default_ready(acceptance, stack_contract),
            {
                "acceptance_release_status": stack_release_status,
                "contract_default_ready": (stack_contract.get("default_promotion") or {}).get("ready")
                if isinstance(stack_contract.get("default_promotion"), dict)
                else None,
            },
        ),
        _check(
            "stack_engine_scope_all",
            _stack_default_scope(acceptance, stack_contract) == "all",
            {"actual": _stack_default_scope(acceptance, stack_contract), "required": "all"},
        ),
        _check(
            "runtime_repeat_evidence_ready",
            runtime_ready,
            runtime_evidence,
            "Default changes require at least two stable runtime observations; release-candidate status can pass without this.",
        ),
    ]
    if stack_engine_publication_audit is not None:
        checks.append(
            _check(
                "stack_engine_publication_runtime_default_passed",
                publication_runtime_default.get("status") == "passed"
                and publication_runtime_default.get("passed") is True
                and publication_runtime_default.get("checks_passed") is True
                and publication_runtime_default.get("raw_ready") is True
                and publication_runtime_default.get("phase2_ready") is True
                and publication_runtime_default.get("phase2_check_passed") is True,
                publication_runtime_default,
            )
        )
        checks.append(
            _check(
                "stack_engine_publication_direct_runtime_evidence_passed",
                publication_direct_runtime.get("ready") is True,
                publication_direct_runtime,
            )
        )
        checks.append(
            _check(
                "stack_engine_publication_quality_metrics_compare_passed",
                publication_quality_compare.get("ready") is True,
                publication_quality_compare,
            )
        )
        checks.append(
            _check(
                "stack_engine_publication_release_quality_guard_passed",
                publication_release_quality_guard.get("ready") is True,
                publication_release_quality_guard,
            )
        )
    release_blocking_names = {
        "acceptance_audit_passed",
        "speedup_threshold",
        "pipeline_release_evidence_passed",
        "pipeline_handoff_evidence_present",
        "pipeline_integration_dq_contract_passed",
        "pipeline_result_contracts_passed",
        "pipeline_resident_winsorized_semantics_handoff",
        "pipeline_pixel_verification_enabled",
        "pipeline_pixel_verification_passed",
        "pipeline_rejection_sample_accounting_passed",
        "pipeline_sample_accounting_closure_passed",
        "warp_quality_contract_handoff",
        "resident_registration_fastpath_handoff",
        "stack_engine_release_evidence_passed",
        "stack_engine_default_ready",
        "stack_engine_scope_all",
    }
    if stack_engine_publication_audit is not None:
        release_blocking_names.add("stack_engine_publication_runtime_default_passed")
        release_blocking_names.add(
            "stack_engine_publication_direct_runtime_evidence_passed"
        )
        release_blocking_names.add(
            "stack_engine_publication_quality_metrics_compare_passed"
        )
        release_blocking_names.add(
            "stack_engine_publication_release_quality_guard_passed"
        )
    release_candidate_ready = all(
        item["passed"] for item in checks if str(item.get("name")) in release_blocking_names
    )
    default_change_ready = release_candidate_ready and runtime_ready
    if not release_candidate_ready:
        recommendation = "fix_release_blockers"
    elif not runtime_ready:
        if preflight_evidence.get("recommendation") == "wait_for_controlled_window":
            recommendation = "wait_for_controlled_window"
        else:
            recommendation = "repeat_benchmark_before_default_change"
    else:
        recommendation = "promote_default_candidate"
    status = (
        "default_change_ready"
        if default_change_ready
        else "release_candidate_ready"
        if release_candidate_ready
        else "blocked"
    )
    return {
        "schema_version": 1,
        "artifact_type": "release_promotion_decision",
        "created_at": now_iso(),
        "status": status,
        "passed": release_candidate_ready,
        "release_candidate_ready": release_candidate_ready,
        "default_change_ready": default_change_ready,
        "recommendation": recommendation,
        "inputs": {
            "acceptance_audit": str(acceptance_audit),
            "stack_engine_contract": None if stack_engine_contract is None else str(stack_engine_contract),
            "pipeline_contract": None if pipeline_contract is None else str(pipeline_contract),
            "runtime_compare": None if runtime_compare is None else str(runtime_compare),
            "repeat_preflight": None if repeat_preflight is None else str(repeat_preflight),
            "stack_engine_publication_audit": None
            if stack_engine_publication_audit is None
            else str(stack_engine_publication_audit),
        },
        "speedup": {"actual": speedup, "required_min": required_speedup},
        "pipeline_handoff": pipeline_handoff,
        "pipeline_rejection_sample_release": rejection_sample_release,
        "pipeline_sample_closure_release": sample_closure_release,
        "pipeline_resident_winsorized_semantics_release": resident_winsorized_semantics,
        "warp_quality_handoff": warp_quality_handoff,
        "resident_registration_fastpath_handoff": resident_fastpath_handoff,
        "stack_engine_publication_runtime_default": publication_runtime_default,
        "stack_engine_publication_direct_runtime_evidence": publication_direct_runtime,
        "stack_engine_publication_quality_metrics_compare": publication_quality_compare,
        "stack_engine_publication_release_quality_guard": (
            publication_release_quality_guard
        ),
        "runtime_repeat": runtime_evidence,
        "repeat_preflight": preflight_evidence,
        "checks": checks,
        "limitations": [
            "This decision artifact does not change GLASS defaults.",
            "Release-candidate readiness is based on supplied acceptance and contract artifacts.",
            "Default-change readiness additionally requires stable repeat/runtime evidence.",
        ],
    }


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# GLASS Release Promotion Decision",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Recommendation: `{payload.get('recommendation')}`",
        f"- Release candidate ready: `{payload.get('release_candidate_ready')}`",
        f"- Default change ready: `{payload.get('default_change_ready')}`",
        f"- Speedup: `{(payload.get('speedup') or {}).get('actual')}`",
        "",
        "## Checks",
        "",
    ]
    for item in payload.get("checks") or []:
        marker = "PASS" if item.get("passed") else "FAIL"
        lines.append(f"- {marker}: `{item.get('name')}` - {item.get('evidence')}")
    runtime = payload.get("runtime_repeat") if isinstance(payload.get("runtime_repeat"), dict) else {}
    pipeline = payload.get("pipeline_handoff") if isinstance(payload.get("pipeline_handoff"), dict) else {}
    rejection_sample = (
        payload.get("pipeline_rejection_sample_release")
        if isinstance(payload.get("pipeline_rejection_sample_release"), dict)
        else {}
    )
    sample_closure = (
        payload.get("pipeline_sample_closure_release")
        if isinstance(payload.get("pipeline_sample_closure_release"), dict)
        else {}
    )
    resident_winsorized = (
        payload.get("pipeline_resident_winsorized_semantics_release")
        if isinstance(payload.get("pipeline_resident_winsorized_semantics_release"), dict)
        else {}
    )
    warp_quality = (
        payload.get("warp_quality_handoff")
        if isinstance(payload.get("warp_quality_handoff"), dict)
        else {}
    )
    resident_fastpath = (
        payload.get("resident_registration_fastpath_handoff")
        if isinstance(payload.get("resident_registration_fastpath_handoff"), dict)
        else {}
    )
    publication = (
        payload.get("stack_engine_publication_runtime_default")
        if isinstance(payload.get("stack_engine_publication_runtime_default"), dict)
        else {}
    )
    publication_direct = (
        payload.get("stack_engine_publication_direct_runtime_evidence")
        if isinstance(
            payload.get("stack_engine_publication_direct_runtime_evidence"),
            dict,
        )
        else {}
    )
    publication_quality = (
        payload.get("stack_engine_publication_quality_metrics_compare")
        if isinstance(
            payload.get("stack_engine_publication_quality_metrics_compare"),
            dict,
        )
        else {}
    )
    publication_release_quality = (
        payload.get("stack_engine_publication_release_quality_guard")
        if isinstance(
            payload.get("stack_engine_publication_release_quality_guard"),
            dict,
        )
        else {}
    )
    lines.extend(
        [
            "",
            "## Pipeline DQ Handoff",
            "",
            f"- Source: `{pipeline.get('source')}`",
            f"- Status: `{pipeline.get('status')}`",
            f"- Passed: `{pipeline.get('passed')}`",
            f"- Integration outputs: `{pipeline.get('integration_output_count')}`",
            f"- Integration maps: `{pipeline.get('integration_map_count')}`",
            f"- Pixel verification enabled: `{pipeline.get('pixel_verification_enabled')}`",
            f"- Rejection sample accounting: `{pipeline.get('rejection_sample_accounting_status')}`",
            f"- Rejection sample release scope: `{rejection_sample.get('scope')}`, ready `{rejection_sample.get('ready')}`, required `{rejection_sample.get('required_count')}`, verified `{rejection_sample.get('verified_count')}`",
            f"- Sample accounting closure: `{pipeline.get('sample_accounting_closure_status')}`",
            f"- Sample closure release scope: `{sample_closure.get('scope')}`, ready `{sample_closure.get('ready')}`, required `{sample_closure.get('required_count')}`, present `{sample_closure.get('present_count')}`",
            f"- Resident winsorized semantics: `{resident_winsorized.get('status')}`, ready `{resident_winsorized.get('ready')}`, required `{resident_winsorized.get('required_count')}`, legacy completions `{resident_winsorized.get('legacy_completion_count')}`",
            f"- Resident winsorized descriptor sources: `{resident_winsorized.get('descriptor_sources')}`",
            "",
        ]
    )
    lines.extend(
        [
            "",
            "## Resident Registration Fastpath Handoff",
            "",
            f"- Present: `{resident_fastpath.get('present')}`",
            f"- Status: `{resident_fastpath.get('status')}`",
            f"- Ready: `{resident_fastpath.get('ready')}`",
            f"- Required: `{resident_fastpath.get('required_by_benchmark_contract')}`",
            f"- Source: `{resident_fastpath.get('source')}`",
            f"- Path: `{resident_fastpath.get('path')}`",
            f"- Mode: `{resident_fastpath.get('resident_registration_mode')}`",
            f"- Descriptor batch: `{resident_fastpath.get('descriptor_fit_batch_mode')}`",
            f"- Pixel refine batch: `{resident_fastpath.get('pixel_refine_batch_mode')}`",
            f"- Triangle warp batch: `{resident_fastpath.get('triangle_warp_batch_mode')}`",
            f"- Triangle warp batch frames: `{resident_fastpath.get('triangle_warp_batch_frame_count')}`",
            f"- Warp copy mode: `{resident_fastpath.get('warp_copy_mode')}`",
            f"- Checks passed: `{resident_fastpath.get('passed_check_count')}`",
            f"- Checks failed: `{resident_fastpath.get('failed_check_count')}`",
            f"- Failed checks: `{resident_fastpath.get('failed_checks')}`",
            f"- Failed acceptance checks: `{resident_fastpath.get('failed_acceptance_checks')}`",
            "",
        ]
    )
    lines.extend(
        [
            "",
            "## Warp Quality Handoff",
            "",
            f"- Present: `{warp_quality.get('present')}`",
            f"- Status: `{warp_quality.get('status')}`",
            f"- Ready: `{warp_quality.get('ready')}`",
            f"- Contract passed: `{warp_quality.get('contract_passed')}`",
            f"- Output count: `{warp_quality.get('output_count')}`",
            f"- Failed checks: `{warp_quality.get('failed_checks')}`",
            f"- Failed acceptance checks: `{warp_quality.get('failed_acceptance_checks')}`",
            f"- Path: `{warp_quality.get('path')}`",
            "",
        ]
    )
    lines.extend(
        [
            "",
            "## StackEngine Publication Runtime Default",
            "",
            f"- Present: `{publication.get('present')}`",
            f"- Status: `{publication.get('status')}`",
            f"- Passed: `{publication.get('passed')}`",
            f"- Checks passed: `{publication.get('checks_passed')}`",
            f"- Raw ready: `{publication.get('raw_ready')}`",
            f"- Phase2 ready: `{publication.get('phase2_ready')}`",
            f"- Phase2 check: `{publication.get('phase2_check_passed')}`",
            f"- Raw drift: legacy=`{publication.get('raw_legacy_master_count')}` failed_outputs=`{publication.get('raw_failed_output_count')}`",
            f"- Phase2 drift: legacy=`{publication.get('phase2_legacy_master_count')}` failed_outputs=`{publication.get('phase2_failed_output_count')}`",
            f"- Direct runtime ready: `{publication_direct.get('ready')}`",
            f"- Direct runtime checks passed: `{publication_direct.get('checks_passed')}`",
            f"- Direct runtime raw source: acceptance=`{publication_direct.get('raw_matrix_acceptance_source')}` calibration=`{publication_direct.get('raw_matrix_pipeline_calibration_source')}` lights=`{publication_direct.get('raw_matrix_pipeline_resident_lights')}`",
            f"- Direct runtime Phase2 source: acceptance=`{publication_direct.get('phase2_matrix_acceptance_source')}` calibration=`{publication_direct.get('phase2_matrix_pipeline_calibration_source')}` lights=`{publication_direct.get('phase2_matrix_pipeline_resident_lights')}`",
            f"- Quality compare ready: `{publication_quality.get('ready')}`",
            f"- Quality compare present: `{publication_quality.get('quality_compare_present')}`",
            f"- Quality compare checks passed: `{publication_quality.get('checks_passed')}`",
            f"- Quality compare raw: present=`{publication_quality.get('raw_present')}` status=`{publication_quality.get('raw_matrix_status')}` failed_checks=`{publication_quality.get('raw_matrix_failed_check_count')}`",
            f"- Quality compare Phase2: present=`{publication_quality.get('phase2_present')}` status=`{publication_quality.get('phase2_matrix_status')}` failed_checks=`{publication_quality.get('phase2_matrix_failed_check_count')}`",
            f"- Release quality guard ready: `{publication_release_quality.get('ready')}`",
            f"- Release quality guard present: `{publication_release_quality.get('release_quality_guard_present')}`",
            f"- Release quality final checks ready: `{publication_release_quality.get('final_checks_ready')}`",
            f"- Release quality final checks match: `{publication_release_quality.get('final_checks_match')}`",
            f"- Release quality final evidence ready: `{publication_release_quality.get('final_evidence_ready')}`",
            f"- Release quality final evidence match: `{publication_release_quality.get('final_evidence_match')}`",
            f"- Release quality raw final: present=`{publication_release_quality.get('raw_final_checks_present')}` matrix=`{publication_release_quality.get('raw_release_matrix_check')}` manifest=`{publication_release_quality.get('raw_release_matrix_manifest_match_check')}`",
            f"- Release quality Phase2 final: present=`{publication_release_quality.get('phase2_final_checks_present')}` matrix=`{publication_release_quality.get('phase2_release_matrix_check')}` manifest=`{publication_release_quality.get('phase2_release_matrix_manifest_match_check')}`",
            f"- Release quality raw final evidence: present=`{publication_release_quality.get('raw_final_evidence_present')}` matrix=`{publication_release_quality.get('raw_matrix_final_checks_ready')}` phase2=`{publication_release_quality.get('raw_matrix_phase2_final_checks_ready')}`",
            f"- Release quality Phase2 final evidence: present=`{publication_release_quality.get('phase2_final_evidence_present')}` matrix=`{publication_release_quality.get('phase2_matrix_final_checks_ready')}` phase2=`{publication_release_quality.get('phase2_matrix_phase2_final_checks_ready')}`",
            f"- Release quality raw final evidence detail: matrix=`{publication_release_quality.get('raw_matrix_final_evidence_ready')}` phase2=`{publication_release_quality.get('raw_matrix_phase2_final_evidence_ready')}`",
            f"- Release quality Phase2 final evidence detail: matrix=`{publication_release_quality.get('phase2_matrix_final_evidence_ready')}` phase2=`{publication_release_quality.get('phase2_matrix_phase2_final_evidence_ready')}`",
            "",
        ]
    )
    lines.extend(
        [
            "",
            "## Runtime Repeat Evidence",
            "",
            f"- Present: `{runtime.get('present')}`",
            f"- Run count: `{runtime.get('run_count')}`",
            f"- Recommendation: `{runtime.get('recommendation')}`",
            f"- Ratio vs best: `{runtime.get('elapsed_ratio_vs_best')}`",
            "",
        ]
    )
    return "\n".join(lines)


def write_release_promotion_decision(
    out: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(out, payload)
    if markdown is not None:
        Path(markdown).parent.mkdir(parents=True, exist_ok=True)
        Path(markdown).write_text(_markdown(payload), encoding="utf-8")
