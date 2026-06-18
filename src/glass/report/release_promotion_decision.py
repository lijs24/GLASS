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
        if not isinstance(accounting, dict):
            continue
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
                "required": bool(accounting.get("required")),
                "verified": bool(accounting.get("verified")),
                "ok": bool(accounting.get("ok")),
                "map_rejected_sample_sum": accounting.get("map_rejected_sample_sum"),
                "source_counts": accounting.get("source_counts") or [],
                "failed_matches": failed_matches,
            }
        )

    failed_items = [row for row in rows if not row.get("ok")]
    check_present = check_passed is not None
    if check_present:
        status = "passed" if check_passed else "failed"
    elif rows:
        status = "passed" if not failed_items else "failed"
    else:
        status = "not_available"
    return {
        "schema_version": 1,
        "status": status,
        "check_name": check_name,
        "check_present": check_present,
        "check_passed": check_passed,
        "pixel_verification_enabled": bool(pixel_verification.get("enabled")),
        "accounted_output_count": len(rows),
        "required_count": sum(1 for row in rows if row.get("required")),
        "verified_count": sum(1 for row in rows if row.get("verified")),
        "failed_count": len(failed_items),
        "failed_items": failed_items,
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
        status = "passed" if not failed_items else "failed"
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
        "sample_accounting_closure": sample_accounting_closure,
        "sample_accounting_closure_status": sample_accounting_closure.get("status"),
        "sample_accounting_closure_failed_count": sample_accounting_closure.get(
            "failed_count"
        ),
        "sample_accounting_closure_present_count": sample_accounting_closure.get(
            "present_count"
        ),
        "checks": checks,
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
            pipeline_handoff["checks"].get("integration_rejection_sample_counts_match_maps") is True
            and pipeline_handoff.get("rejection_sample_accounting_status") == "passed",
            {
                "check": pipeline_handoff["checks"].get(
                    "integration_rejection_sample_counts_match_maps"
                ),
                "status": pipeline_handoff.get("rejection_sample_accounting_status"),
                "failed_count": pipeline_handoff.get("rejection_sample_accounting_failed_count"),
                "failed_items": (
                    pipeline_handoff.get("rejection_sample_accounting") or {}
                ).get("failed_items"),
            },
        ),
        _check(
            "pipeline_sample_accounting_closure_passed",
            pipeline_handoff["checks"].get("integration_sample_accounting_closure") is True
            and pipeline_handoff.get("sample_accounting_closure_status") == "passed",
            {
                "check": pipeline_handoff["checks"].get(
                    "integration_sample_accounting_closure"
                ),
                "status": pipeline_handoff.get("sample_accounting_closure_status"),
                "present_count": pipeline_handoff.get(
                    "sample_accounting_closure_present_count"
                ),
                "failed_count": pipeline_handoff.get("sample_accounting_closure_failed_count"),
                "failed_items": (
                    pipeline_handoff.get("sample_accounting_closure") or {}
                ).get("failed_items"),
            },
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
    release_blocking_names = {
        "acceptance_audit_passed",
        "speedup_threshold",
        "pipeline_release_evidence_passed",
        "pipeline_handoff_evidence_present",
        "pipeline_integration_dq_contract_passed",
        "pipeline_result_contracts_passed",
        "pipeline_pixel_verification_enabled",
        "pipeline_pixel_verification_passed",
        "pipeline_rejection_sample_accounting_passed",
        "pipeline_sample_accounting_closure_passed",
        "stack_engine_release_evidence_passed",
        "stack_engine_default_ready",
        "stack_engine_scope_all",
    }
    if stack_engine_publication_audit is not None:
        release_blocking_names.add("stack_engine_publication_runtime_default_passed")
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
        "stack_engine_publication_runtime_default": publication_runtime_default,
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
    publication = (
        payload.get("stack_engine_publication_runtime_default")
        if isinstance(payload.get("stack_engine_publication_runtime_default"), dict)
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
            f"- Sample accounting closure: `{pipeline.get('sample_accounting_closure_status')}`",
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
