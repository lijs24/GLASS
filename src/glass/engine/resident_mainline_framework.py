from __future__ import annotations

from pathlib import Path
from typing import Any

from glass.io.json_io import read_json, write_json
from glass.report.phase2_mainline_audit import build_phase2_mainline_audit


DEFAULT_RESIDENT_MAINLINE_FRAMEWORK_GATE = "warn"
DEFAULT_RESIDENT_MAINLINE_FRAMEWORK_SCOPE = "default"


def _int_or_none(value: Any) -> int | None:
    try:
        return None if value is None else int(value)
    except (TypeError, ValueError):
        return None


def _json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = read_json(path)
    return payload if isinstance(payload, dict) else {}


def _sum_group_count_maps(groups: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for group in groups:
        values = group.get(key)
        if not isinstance(values, dict):
            continue
        for name, value in values.items():
            counts[str(name)] = counts.get(str(name), 0) + int(value or 0)
    return dict(sorted(counts.items()))


def _check(name: str, passed: bool, evidence: dict[str, Any], note: str = "") -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "evidence": evidence, "note": note}


def _source_dq_summary(run: Path) -> dict[str, Any]:
    path = run / "resident_source_dq_execution.json"
    payload = _json_if_exists(path)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    groups_raw = payload.get("groups") if isinstance(payload.get("groups"), list) else []
    groups = [group for group in groups_raw if isinstance(group, dict)]
    source_dq_flag_counts = summary.get("source_dq_flag_counts")
    if not isinstance(source_dq_flag_counts, dict):
        source_dq_flag_counts = _sum_group_count_maps(groups, "source_dq_flag_counts")
    source_counts = summary.get("source_counts")
    if not isinstance(source_counts, dict):
        source_counts = _sum_group_count_maps(groups, "source_counts")
    sidecar_source_counts = summary.get("sidecar_source_counts")
    if not isinstance(sidecar_source_counts, dict):
        sidecar_source_counts = _sum_group_count_maps(groups, "sidecar_source_counts")
    return {
        "path": str(path),
        "exists": path.exists(),
        "status": summary.get("status") or payload.get("status"),
        "passed": summary.get("passed") if "passed" in summary else payload.get("passed"),
        "frame_count": _int_or_none(summary.get("frame_count")),
        "active_frame_count": _int_or_none(summary.get("active_frame_count")),
        "input_invalid_samples_before_rejection": _int_or_none(
            summary.get("input_invalid_samples_before_rejection")
        ),
        "applied_invalid_samples": _int_or_none(summary.get("applied_invalid_samples")),
        "all_frame_input_invalid_samples_before_frame_mask": _int_or_none(
            summary.get("all_frame_input_invalid_samples_before_frame_mask")
        ),
        "all_frame_applied_invalid_samples": _int_or_none(
            summary.get("all_frame_applied_invalid_samples")
        ),
        "input_flagged_samples": _int_or_none(summary.get("input_flagged_samples")),
        "input_nonfinite_samples": _int_or_none(summary.get("input_nonfinite_samples")),
        "source_dq_flag_counts": dict(source_dq_flag_counts),
        "source_counts": dict(source_counts),
        "sidecar_source_counts": dict(sidecar_source_counts),
        "execution_routes": (
            list(summary.get("execution_routes"))
            if isinstance(summary.get("execution_routes"), list)
            else []
        ),
    }


def _threshold_met(value: int | None, minimum: int) -> bool:
    if int(minimum) <= 0:
        return True
    return value is not None and int(value) >= int(minimum)


def _source_dq_checks(
    source_dq: dict[str, Any],
    *,
    min_source_dq_invalid_samples: int,
    min_source_dq_applied_samples: int,
) -> list[dict[str, Any]]:
    source_dq_required = (
        int(min_source_dq_invalid_samples) > 0 or int(min_source_dq_applied_samples) > 0
    )
    return [
        _check(
            "resident_source_dq_present_when_required",
            bool(source_dq.get("exists")) or not source_dq_required,
            {
                "required": source_dq_required,
                "path": source_dq.get("path"),
                "exists": source_dq.get("exists"),
            },
        ),
        _check(
            "resident_source_dq_passed_when_required",
            source_dq.get("passed") is True or not source_dq_required,
            {
                "required": source_dq_required,
                "status": source_dq.get("status"),
                "passed": source_dq.get("passed"),
            },
        ),
        _check(
            "resident_source_dq_invalid_threshold_met",
            _threshold_met(
                source_dq.get("input_invalid_samples_before_rejection"),
                min_source_dq_invalid_samples,
            ),
            {
                "actual": source_dq.get("input_invalid_samples_before_rejection"),
                "required_min": int(min_source_dq_invalid_samples),
                "source": "resident_source_dq_execution.summary",
            },
        ),
        _check(
            "resident_source_dq_applied_threshold_met",
            _threshold_met(
                source_dq.get("applied_invalid_samples"),
                min_source_dq_applied_samples,
            ),
            {
                "actual": source_dq.get("applied_invalid_samples"),
                "required_min": int(min_source_dq_applied_samples),
                "source": "resident_source_dq_execution.summary",
            },
        ),
    ]


def _inline_cosmetic_cuda_source_dq_checks(source_dq: dict[str, Any]) -> list[dict[str, Any]]:
    source_counts = (
        dict(source_dq.get("source_counts")) if isinstance(source_dq.get("source_counts"), dict) else {}
    )
    execution_routes = [
        str(route) for route in source_dq.get("execution_routes") or [] if route is not None
    ]
    inline_sources = [
        source
        for source in source_counts
        if "cosmetic_cuda" in str(source) and "resident" in str(source)
    ]
    route_matches = [
        route for route in execution_routes if "resident_in_memory_mask_streaming" in route
    ]
    return [
        _check(
            "resident_inline_cosmetic_cuda_source_present",
            bool(inline_sources),
            {
                "source_counts": source_counts,
                "matched_sources": inline_sources,
            },
            "Inline cosmetic CUDA scope must prove source-DQ came from the resident CUDA detector, not a sidecar.",
        ),
        _check(
            "resident_inline_cosmetic_cuda_streaming_route",
            bool(route_matches),
            {
                "execution_routes": execution_routes,
                "matched_routes": route_matches,
            },
            "Inline cosmetic CUDA source-DQ must still flow through resident in-memory mask streaming.",
        ),
    ]


def _stack_engine_summary(run: Path) -> dict[str, Any]:
    path = run / "stack_engine_contract.json"
    payload = _json_if_exists(path)
    adoption = payload.get("adoption") if isinstance(payload.get("adoption"), dict) else {}
    promotion = (
        payload.get("default_promotion")
        if isinstance(payload.get("default_promotion"), dict)
        else {}
    )
    ledger = (
        promotion.get("pipeline_contract_dq_ledger")
        if isinstance(promotion.get("pipeline_contract_dq_ledger"), dict)
        else payload.get("pipeline_contract_dq_ledger")
        if isinstance(payload.get("pipeline_contract_dq_ledger"), dict)
        else {}
    )
    blocker_count = _int_or_none(promotion.get("blocker_count"))
    blockers = promotion.get("blockers") if isinstance(promotion.get("blockers"), list) else []
    return {
        "path": str(path),
        "exists": path.exists(),
        "status": payload.get("status"),
        "passed": payload.get("passed"),
        "audit_type": payload.get("audit_type") or payload.get("artifact_type"),
        "scope": payload.get("scope"),
        "expected_integration_engine": payload.get("expected_integration_engine"),
        "default_promotion_ready": promotion.get("ready"),
        "default_promotion_status": promotion.get("status"),
        "default_promotion_blocker_count": blocker_count,
        "default_promotion_blockers": blockers,
        "recommendation": promotion.get("recommendation") or adoption.get("recommendation"),
        "surface_count": _int_or_none(promotion.get("surface_count") or adoption.get("surface_count")),
        "calibration_surface_count": _int_or_none(promotion.get("calibration_surface_count")),
        "integration_surface_count": _int_or_none(promotion.get("integration_surface_count")),
        "resident_surface_count": _int_or_none(promotion.get("resident_surface_count")),
        "contract_ready_count": _int_or_none(adoption.get("contract_ready_count")),
        "phase2_stack_engine_default_gap_count": _int_or_none(
            promotion.get("phase2_stack_engine_default_gap_count")
            if "phase2_stack_engine_default_gap_count" in promotion
            else adoption.get("phase2_stack_engine_default_gap_count")
        ),
        "pipeline_contract_dq_ledger_ready": promotion.get(
            "pipeline_contract_dq_ledger_ready"
        )
        if "pipeline_contract_dq_ledger_ready" in promotion
        else ledger.get("ready"),
        "pipeline_contract_dq_ledger_required": promotion.get(
            "pipeline_contract_dq_ledger_required"
        )
        if "pipeline_contract_dq_ledger_required" in promotion
        else ledger.get("required"),
        "pipeline_contract_dq_ledger_status": ledger.get("status"),
        "pipeline_contract_dq_ledger_expected_rows": _int_or_none(ledger.get("expected_rows")),
        "pipeline_contract_dq_ledger_accounting_rows": _int_or_none(
            ledger.get("accounting_rows")
        ),
        "pipeline_contract_dq_ledger_failed_checks": (
            list(ledger.get("failed_checks"))
            if isinstance(ledger.get("failed_checks"), list)
            else []
        ),
        "failed_checks": (
            list(payload.get("failed_checks"))
            if isinstance(payload.get("failed_checks"), list)
            else []
        ),
    }


def _positive_or_unknown(value: int | None) -> bool:
    return value is not None and value > 0


def _zero_or_none(value: int | None) -> bool:
    return value in (0, None)


def _stack_engine_checks(stack_engine: dict[str, Any]) -> list[dict[str, Any]]:
    surface_coverage_passed = (
        _positive_or_unknown(stack_engine.get("surface_count"))
        and _positive_or_unknown(stack_engine.get("calibration_surface_count"))
        and _positive_or_unknown(stack_engine.get("integration_surface_count"))
    )
    dq_ledger_required = stack_engine.get("pipeline_contract_dq_ledger_required") is True
    dq_ledger_ready = stack_engine.get("pipeline_contract_dq_ledger_ready") is True
    return [
        _check(
            "stack_engine_contract_present",
            bool(stack_engine.get("exists")),
            {
                "path": stack_engine.get("path"),
                "exists": stack_engine.get("exists"),
            },
        ),
        _check(
            "stack_engine_contract_passed",
            stack_engine.get("passed") is True,
            {
                "status": stack_engine.get("status"),
                "passed": stack_engine.get("passed"),
                "failed_checks": stack_engine.get("failed_checks"),
            },
        ),
        _check(
            "stack_engine_default_promotion_ready",
            stack_engine.get("default_promotion_ready") is True,
            {
                "ready": stack_engine.get("default_promotion_ready"),
                "status": stack_engine.get("default_promotion_status"),
                "blocker_count": stack_engine.get("default_promotion_blocker_count"),
                "blockers": stack_engine.get("default_promotion_blockers"),
                "recommendation": stack_engine.get("recommendation"),
            },
            "Resident mainline strict runs must prove StackEngine default readiness, not just write a contract file.",
        ),
        _check(
            "stack_engine_default_gap_count_zero",
            _zero_or_none(stack_engine.get("phase2_stack_engine_default_gap_count")),
            {
                "gap_count": stack_engine.get("phase2_stack_engine_default_gap_count"),
                "recommendation": stack_engine.get("recommendation"),
            },
        ),
        _check(
            "stack_engine_surface_coverage_present",
            surface_coverage_passed,
            {
                "surface_count": stack_engine.get("surface_count"),
                "calibration_surface_count": stack_engine.get("calibration_surface_count"),
                "integration_surface_count": stack_engine.get("integration_surface_count"),
                "resident_surface_count": stack_engine.get("resident_surface_count"),
                "contract_ready_count": stack_engine.get("contract_ready_count"),
            },
        ),
        _check(
            "stack_engine_pipeline_dq_ledger_ready",
            dq_ledger_ready if dq_ledger_required else True,
            {
                "required": dq_ledger_required,
                "ready": stack_engine.get("pipeline_contract_dq_ledger_ready"),
                "status": stack_engine.get("pipeline_contract_dq_ledger_status"),
                "expected_rows": stack_engine.get("pipeline_contract_dq_ledger_expected_rows"),
                "accounting_rows": stack_engine.get("pipeline_contract_dq_ledger_accounting_rows"),
                "failed_checks": stack_engine.get("pipeline_contract_dq_ledger_failed_checks"),
            },
            "Resident StackEngine surfaces require the pipeline DQ ledger to be ready.",
        ),
    ]


def build_resident_mainline_framework(
    run: str | Path,
    *,
    requested_action: str = DEFAULT_RESIDENT_MAINLINE_FRAMEWORK_GATE,
    framework_scope: str = DEFAULT_RESIDENT_MAINLINE_FRAMEWORK_SCOPE,
    min_lights: int = 1,
    min_active_frames: int = 1,
    max_masked_frames: int = 1_000_000,
    min_source_dq_invalid_samples: int = 0,
    min_source_dq_applied_samples: int = 0,
) -> dict[str, Any]:
    """Build a resident-run postcondition summary from the already written artifacts."""

    run_path = Path(run)
    action = str(requested_action or DEFAULT_RESIDENT_MAINLINE_FRAMEWORK_GATE)
    if action not in {"off", "warn", "strict"}:
        raise ValueError("requested_action must be off, warn, or strict")
    scope = str(framework_scope or DEFAULT_RESIDENT_MAINLINE_FRAMEWORK_SCOPE)
    valid_scopes = {"default", "source_dq_positive", "inline_cosmetic_cuda_positive"}
    if scope not in valid_scopes:
        raise ValueError(
            "framework_scope must be default, source_dq_positive, or inline_cosmetic_cuda_positive"
        )
    audit = build_phase2_mainline_audit(
        run_path,
        min_lights=max(0, int(min_lights)),
        min_active_frames=max(0, int(min_active_frames)),
        max_masked_frames=max(0, int(max_masked_frames)),
        require_acceptance=False,
        require_compare=False,
    )
    source_dq = _source_dq_summary(run_path)
    extra_checks = _source_dq_checks(
        source_dq,
        min_source_dq_invalid_samples=max(0, int(min_source_dq_invalid_samples)),
        min_source_dq_applied_samples=max(0, int(min_source_dq_applied_samples)),
    )
    if scope == "inline_cosmetic_cuda_positive":
        extra_checks.extend(_inline_cosmetic_cuda_source_dq_checks(source_dq))
    stack_engine = _stack_engine_summary(run_path)
    stack_engine_checks = _stack_engine_checks(stack_engine)
    audit_checks = list(audit.get("checks") or [])
    if scope in {"source_dq_positive", "inline_cosmetic_cuda_positive"}:
        relaxed = {
            "default_resident_cuda_route",
            "resident_output_maps_present",
            "resident_stage_ledger_component_contract",
        }
        audit_checks = [
            check
            for check in audit_checks
            if not (isinstance(check, dict) and check.get("name") in relaxed)
        ]
    checks = audit_checks + stack_engine_checks + extra_checks
    failed_checks = [
        str(check.get("name"))
        for check in checks
        if isinstance(check, dict) and not check.get("passed")
    ]
    passed = not failed_checks
    summary = audit.get("summary") if isinstance(audit.get("summary"), dict) else {}
    summary = {**summary, "stack_engine": stack_engine, "source_dq": source_dq}
    return {
        **audit,
        "artifact_type": "resident_mainline_framework",
        "source_artifact_type": audit.get("artifact_type"),
        "scope": "resident_run_postcondition",
        "framework_scope": scope,
        "policy": {
            "requested_action": action,
            "blocking": bool(action == "strict" and not passed),
            "framework_scope": scope,
            "min_lights": max(0, int(min_lights)),
            "min_active_frames": max(0, int(min_active_frames)),
            "max_masked_frames": max(0, int(max_masked_frames)),
            "min_source_dq_invalid_samples": max(0, int(min_source_dq_invalid_samples)),
            "min_source_dq_applied_samples": max(0, int(min_source_dq_applied_samples)),
            "acceptance_required": False,
            "compare_required": False,
        },
        "summary": summary,
        "checks": checks,
        "failed_checks": failed_checks,
        "stack_engine": stack_engine,
        "source_dq": source_dq,
        "status": "passed" if passed else "failed",
        "passed": passed,
        "blocking": bool(action == "strict" and not passed),
    }


def write_resident_mainline_framework(
    run: str | Path,
    *,
    requested_action: str = DEFAULT_RESIDENT_MAINLINE_FRAMEWORK_GATE,
    framework_scope: str = DEFAULT_RESIDENT_MAINLINE_FRAMEWORK_SCOPE,
    min_lights: int = 1,
    min_active_frames: int = 1,
    max_masked_frames: int = 1_000_000,
    min_source_dq_invalid_samples: int = 0,
    min_source_dq_applied_samples: int = 0,
    path: str | Path | None = None,
) -> Path:
    run_path = Path(run)
    out = Path(path) if path is not None else run_path / "resident_mainline_framework.json"
    payload = build_resident_mainline_framework(
        run_path,
        requested_action=requested_action,
        framework_scope=framework_scope,
        min_lights=min_lights,
        min_active_frames=min_active_frames,
        max_masked_frames=max_masked_frames,
        min_source_dq_invalid_samples=min_source_dq_invalid_samples,
        min_source_dq_applied_samples=min_source_dq_applied_samples,
    )
    write_json(out, payload)
    return out
