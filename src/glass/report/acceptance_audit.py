from __future__ import annotations

from pathlib import Path
from typing import Any

from glass.io.json_io import write_json
from glass.report.benchmark_contract import (
    build_benchmark_contract_checks,
    build_benchmark_performance_diagnostics,
    collect_dq_provenance_records,
    collect_frame_accounting_record,
    load_benchmark_contract,
)
from glass.report.optimization_guide import build_optimization_guidance
from glass.report.speedup_report import _read_json_lenient, summarize_wbpp_speedup


def _frame_type_counts(manifest: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {"light": 0, "bias": 0, "dark": 0, "flat": 0}
    for frame in manifest.get("frames") or []:
        frame_type = str(frame.get("frame_type") or "unknown").lower()
        counts[frame_type] = counts.get(frame_type, 0) + 1
    return counts


def _numeric(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _check(name: str, passed: bool, evidence: dict[str, Any], note: str = "") -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "evidence": evidence, "note": note}


def _contract_bundle_paths(
    contract_bundle_json: str | Path | None,
    *,
    pipeline_contract_json: str | Path | None,
    stack_engine_contract_json: str | Path | None,
) -> tuple[str | Path | None, str | Path | None, dict[str, Any] | None]:
    if contract_bundle_json is None:
        return pipeline_contract_json, stack_engine_contract_json, None
    bundle_path = Path(contract_bundle_json)
    bundle_payload = _read_json_lenient(bundle_path) if bundle_path.exists() else {}
    artifact_map = (
        bundle_payload.get("artifacts")
        if isinstance(bundle_payload.get("artifacts"), dict)
        else {}
    )
    argument_map = (
        bundle_payload.get("acceptance_audit_argument_map")
        if isinstance(bundle_payload.get("acceptance_audit_argument_map"), dict)
        else {}
    )
    bundle_pipeline = artifact_map.get("pipeline_contract") or argument_map.get("pipeline_contract_json")
    bundle_stack = artifact_map.get("stack_engine_contract") or argument_map.get("stack_engine_contract_json")
    bundle_resident_calibration = (
        artifact_map.get("resident_calibration_contract")
        or bundle_payload.get("resident_calibration_contract_json")
    )
    bundle_resident_result = (
        artifact_map.get("resident_result_contract")
        or bundle_payload.get("resident_result_contract_json")
    )
    resolved_pipeline = pipeline_contract_json if pipeline_contract_json is not None else bundle_pipeline
    resolved_stack = stack_engine_contract_json if stack_engine_contract_json is not None else bundle_stack
    bundle = {
        "path": str(bundle_path),
        "exists": bundle_path.exists(),
        "schema_version": bundle_payload.get("schema_version"),
        "artifact_type": bundle_payload.get("artifact_type"),
        "status": bundle_payload.get("status"),
        "passed": bundle_payload.get("passed"),
        "purpose": bundle_payload.get("purpose"),
        "artifact_keys": sorted(str(key) for key in artifact_map),
        "argument_map_keys": sorted(str(key) for key in argument_map),
        "acceptance_audit_argument_count": len(bundle_payload.get("acceptance_audit_arguments") or [])
        if isinstance(bundle_payload.get("acceptance_audit_arguments"), list)
        else 0,
        "pipeline_contract_json": None if resolved_pipeline is None else str(resolved_pipeline),
        "stack_engine_contract_json": None if resolved_stack is None else str(resolved_stack),
        "resident_calibration_contract_json": None
        if bundle_resident_calibration is None
        else str(bundle_resident_calibration),
        "resident_result_contract_json": None if bundle_resident_result is None else str(bundle_resident_result),
        "resident_calibration_contract_attached": bundle_payload.get("resident_calibration_contract_attached"),
        "resident_result_contract_attached": bundle_payload.get("resident_result_contract_attached"),
        "explicit_pipeline_contract_overrode_bundle": pipeline_contract_json is not None,
        "explicit_stack_engine_contract_overrode_bundle": stack_engine_contract_json is not None,
        "checks": bundle_payload.get("checks") if isinstance(bundle_payload.get("checks"), list) else [],
    }
    return resolved_pipeline, resolved_stack, bundle


def _contract_bundle_schema_audit(
    contract_bundle: dict[str, Any] | None,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    if contract_bundle is None:
        return None, []
    artifact_keys = {str(key) for key in contract_bundle.get("artifact_keys") or []}
    argument_map_keys = {str(key) for key in contract_bundle.get("argument_map_keys") or []}
    required_artifacts = {"guardrails_summary", "pipeline_contract", "stack_engine_contract"}
    required_argument_map = {"pipeline_contract_json", "stack_engine_contract_json"}
    missing_artifacts = sorted(required_artifacts - artifact_keys)
    missing_argument_map = sorted(required_argument_map - argument_map_keys)
    record = {
        "schema_version": contract_bundle.get("schema_version"),
        "required_schema_version": 1,
        "purpose": contract_bundle.get("purpose"),
        "required_purpose": "acceptance_audit_contract_inputs",
        "artifact_keys": sorted(artifact_keys),
        "missing_required_artifacts": missing_artifacts,
        "argument_map_keys": sorted(argument_map_keys),
        "missing_required_argument_map_keys": missing_argument_map,
    }
    checks = [
        _check(
            "contract_bundle_schema_version",
            contract_bundle.get("schema_version") == 1,
            {
                "actual": contract_bundle.get("schema_version"),
                "required": 1,
            },
        ),
        _check(
            "contract_bundle_purpose",
            contract_bundle.get("purpose") == "acceptance_audit_contract_inputs",
            {
                "actual": contract_bundle.get("purpose"),
                "required": "acceptance_audit_contract_inputs",
            },
        ),
        _check(
            "contract_bundle_required_artifacts",
            not missing_artifacts,
            {
                "required": sorted(required_artifacts),
                "missing": missing_artifacts,
                "actual": sorted(artifact_keys),
            },
        ),
        _check(
            "contract_bundle_argument_map",
            not missing_argument_map,
            {
                "required": sorted(required_argument_map),
                "missing": missing_argument_map,
                "actual": sorted(argument_map_keys),
            },
        ),
    ]
    record["passed"] = all(item["passed"] for item in checks)
    record["status"] = "passed" if record["passed"] else "failed"
    return record, checks


def _contract_attachment_audit(
    *,
    contract_bundle: dict[str, Any] | None,
    label: str,
    path_key: str,
    attached_key: str,
    expected_artifact_type: str,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    if contract_bundle is None:
        return None, []
    path_value = contract_bundle.get(path_key)
    declared_attached = bool(contract_bundle.get(attached_key)) or path_value is not None
    if not declared_attached:
        return None, []

    path = Path(str(path_value)) if path_value else None
    exists = bool(path and path.exists())
    payload = _read_json_lenient(path) if path is not None and exists else {}
    contract_checks = [item for item in payload.get("checks") or [] if isinstance(item, dict)]
    failed_checks = [item.get("name") for item in contract_checks if not item.get("passed")]
    output_count = payload.get("output_count")
    if output_count is None and isinstance(payload.get("outputs"), list):
        output_count = len(payload["outputs"])
    record = {
        "path": None if path is None else str(path),
        "exists": exists,
        "artifact_type": payload.get("artifact_type"),
        "audit_type": payload.get("audit_type"),
        "status": payload.get("status"),
        "passed": payload.get("passed"),
        "output_count": output_count,
        "check_count": len(contract_checks),
        "failed_checks": failed_checks,
    }
    checks = [
        _check(
            f"{label}_present",
            exists,
            {"path": record["path"], "exists": exists},
        ),
        _check(
            f"{label}_type",
            payload.get("artifact_type") == expected_artifact_type,
            {
                "path": record["path"],
                "artifact_type": payload.get("artifact_type"),
                "required": expected_artifact_type,
            },
        ),
        _check(
            f"{label}_passed",
            payload.get("passed") is True,
            {
                "status": payload.get("status"),
                "failed_checks": failed_checks,
            },
        ),
    ]
    return record, checks


def _pipeline_contract_release_evidence(
    *,
    checks: list[dict[str, Any]],
    pipeline_contract: dict[str, Any] | None,
    contract_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    pipeline_checks = [
        item
        for item in checks
        if str(item.get("name", "")).startswith(("pipeline_contract_", "contract_pipeline_contract"))
    ]
    failed_checks = [str(item.get("name")) for item in pipeline_checks if not item.get("passed")]
    if pipeline_checks:
        status = "passed" if not failed_checks else "failed"
    else:
        status = "not_requested"
    contract_requirements = (contract_payload or {}).get("pipeline_contract")
    return {
        "status": status,
        "required_by_benchmark_contract": isinstance(contract_requirements, dict)
        and bool(contract_requirements),
        "pipeline_contract_path": None if pipeline_contract is None else pipeline_contract.get("path"),
        "pipeline_contract_audit_type": None if pipeline_contract is None else pipeline_contract.get("audit_type"),
        "pipeline_contract_status": None if pipeline_contract is None else pipeline_contract.get("status"),
        "pipeline_contract_passed": None if pipeline_contract is None else pipeline_contract.get("passed"),
        "pipeline_contract_check_count": 0 if pipeline_contract is None else pipeline_contract.get("check_count", 0),
        "direct_check_count": sum(1 for item in pipeline_checks if str(item.get("name", "")).startswith("pipeline_")),
        "benchmark_check_count": sum(
            1 for item in pipeline_checks if str(item.get("name", "")).startswith("contract_pipeline_")
        ),
        "passed_check_count": sum(1 for item in pipeline_checks if item.get("passed")),
        "failed_check_count": len(failed_checks),
        "failed_checks": failed_checks,
        "checks": pipeline_checks,
    }


def _stack_engine_default_promotion_release_evidence(
    *,
    checks: list[dict[str, Any]],
    stack_engine_contract: dict[str, Any] | None,
    contract_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    stack_checks = [
        item
        for item in checks
        if str(item.get("name", "")).startswith(
            ("stack_engine_contract_", "contract_stack_engine_default_promotion")
        )
    ]
    failed_checks = [str(item.get("name")) for item in stack_checks if not item.get("passed")]
    if stack_checks:
        status = "passed" if not failed_checks else "failed"
    else:
        status = "not_requested"
    requirements = (contract_payload or {}).get("stack_engine_default_promotion")
    promotion = (stack_engine_contract or {}).get("default_promotion") or {}
    adoption = (stack_engine_contract or {}).get("adoption") or {}
    return {
        "status": status,
        "required_by_benchmark_contract": isinstance(requirements, dict) and bool(requirements),
        "stack_engine_contract_path": None if stack_engine_contract is None else stack_engine_contract.get("path"),
        "stack_engine_contract_audit_type": None
        if stack_engine_contract is None
        else stack_engine_contract.get("audit_type"),
        "stack_engine_contract_status": None if stack_engine_contract is None else stack_engine_contract.get("status"),
        "stack_engine_contract_passed": None if stack_engine_contract is None else stack_engine_contract.get("passed"),
        "stack_engine_contract_scope": None if stack_engine_contract is None else stack_engine_contract.get("scope"),
        "default_promotion_ready": promotion.get("ready"),
        "default_promotion_status": promotion.get("status"),
        "default_promotion_gap_count": promotion.get("phase2_stack_engine_default_gap_count"),
        "default_promotion_blocker_count": promotion.get("blocker_count"),
        "adoption_recommendation": adoption.get("recommendation"),
        "direct_check_count": sum(1 for item in stack_checks if str(item.get("name", "")).startswith("stack_engine_")),
        "benchmark_check_count": sum(
            1 for item in stack_checks if str(item.get("name", "")).startswith("contract_stack_engine_")
        ),
        "passed_check_count": sum(1 for item in stack_checks if item.get("passed")),
        "failed_check_count": len(failed_checks),
        "failed_checks": failed_checks,
        "checks": stack_checks,
    }


def build_acceptance_audit(
    *,
    manifest_path: str | Path,
    glass_run: str | Path,
    wbpp_result: str | Path,
    compare_json: str | Path,
    min_lights: int = 200,
    min_bias: int = 20,
    min_dark: int = 20,
    min_flat: int = 20,
    min_active_frames: int = 1,
    min_speedup: float = 2.0,
    min_coverage_fraction: float = 0.95,
    max_rms_diff: float | None = 0.01,
    max_abs_diff_p99: float | None = 0.01,
    benchmark_contract: str | Path | None = None,
    resident_determinism_json: str | Path | None = None,
    contract_bundle_json: str | Path | None = None,
    pipeline_contract_json: str | Path | None = None,
    stack_engine_contract_json: str | Path | None = None,
) -> dict[str, Any]:
    pipeline_contract_json, stack_engine_contract_json, contract_bundle = _contract_bundle_paths(
        contract_bundle_json,
        pipeline_contract_json=pipeline_contract_json,
        stack_engine_contract_json=stack_engine_contract_json,
    )
    manifest = _read_json_lenient(manifest_path)
    speedup = summarize_wbpp_speedup(
        glass_run,
        wbpp_result,
        compare_json=compare_json,
        min_speedup=min_speedup,
    )
    counts = _frame_type_counts(manifest)
    compare_payload = _read_json_lenient(compare_json)
    comparison = speedup.get("comparison") or {}
    gp = speedup["glass"]

    rms = _numeric(comparison.get("rms_diff"))
    p99 = _numeric(comparison.get("abs_diff_p99"))
    coverage = _numeric(comparison.get("coverage_fraction"))
    active_frames = int(gp.get("weighted_frame_count") or 0)

    checks = [
        _check(
            "minimum_light_frames",
            counts.get("light", 0) >= int(min_lights),
            {"actual": counts.get("light", 0), "required": int(min_lights)},
        ),
        _check(
            "minimum_bias_frames",
            counts.get("bias", 0) >= int(min_bias),
            {"actual": counts.get("bias", 0), "required": int(min_bias)},
        ),
        _check(
            "minimum_dark_frames",
            counts.get("dark", 0) >= int(min_dark),
            {"actual": counts.get("dark", 0), "required": int(min_dark)},
        ),
        _check(
            "minimum_flat_frames",
            counts.get("flat", 0) >= int(min_flat),
            {"actual": counts.get("flat", 0), "required": int(min_flat)},
        ),
        _check(
            "minimum_active_frames",
            active_frames >= int(min_active_frames),
            {"actual": active_frames, "required": int(min_active_frames)},
        ),
        _check(
            "minimum_speedup",
            bool(speedup.get("meets_min_speedup")),
            {"actual": speedup.get("speedup_vs_wbpp"), "required": float(min_speedup)},
        ),
        _check(
            "shape_match",
            comparison.get("shape_match") is True,
            {"actual": comparison.get("shape_match"), "required": True},
        ),
        _check(
            "minimum_coverage_fraction",
            coverage is not None and coverage >= float(min_coverage_fraction),
            {"actual": coverage, "required": float(min_coverage_fraction)},
        ),
    ]

    if max_rms_diff is not None:
        checks.append(
            _check(
                "maximum_rms_diff",
                rms is not None and rms <= float(max_rms_diff),
                {"actual": rms, "required_max": float(max_rms_diff)},
            )
        )
    if max_abs_diff_p99 is not None:
        checks.append(
            _check(
                "maximum_abs_diff_p99",
                p99 is not None and p99 <= float(max_abs_diff_p99),
                {"actual": p99, "required_max": float(max_abs_diff_p99)},
            )
        )

    if contract_bundle is not None:
        checks.extend(
            [
                _check(
                    "contract_bundle_present",
                    bool(contract_bundle.get("exists")),
                    {"path": contract_bundle.get("path"), "exists": contract_bundle.get("exists")},
                ),
                _check(
                    "contract_bundle_type",
                    contract_bundle.get("artifact_type") == "glass_acceptance_contract_bundle",
                    {
                        "path": contract_bundle.get("path"),
                        "artifact_type": contract_bundle.get("artifact_type"),
                        "required": "glass_acceptance_contract_bundle",
                    },
                ),
            ]
        )

    contract_bundle_schema, contract_bundle_schema_checks = _contract_bundle_schema_audit(contract_bundle)
    checks.extend(contract_bundle_schema_checks)

    resident_calibration_contract, resident_calibration_checks = _contract_attachment_audit(
        contract_bundle=contract_bundle,
        label="resident_calibration_contract",
        path_key="resident_calibration_contract_json",
        attached_key="resident_calibration_contract_attached",
        expected_artifact_type="resident_cuda_calibration_contract",
    )
    resident_result_contract, resident_result_checks = _contract_attachment_audit(
        contract_bundle=contract_bundle,
        label="resident_result_contract",
        path_key="resident_result_contract_json",
        attached_key="resident_result_contract_attached",
        expected_artifact_type="resident_cuda_result_contract",
    )
    checks.extend(resident_calibration_checks)
    checks.extend(resident_result_checks)

    pipeline_contract_path = Path(pipeline_contract_json) if pipeline_contract_json is not None else None
    pipeline_contract_payload = (
        _read_json_lenient(pipeline_contract_path)
        if pipeline_contract_path is not None and pipeline_contract_path.exists()
        else {}
    )
    pipeline_contract = None
    if pipeline_contract_path is not None:
        contract_checks = [
            item for item in pipeline_contract_payload.get("checks") or [] if isinstance(item, dict)
        ]
        check_names = [
            str(item.get("name")) for item in contract_checks if item.get("name") is not None
        ]
        failed_checks = [
            item.get("name")
            for item in contract_checks
            if not item.get("passed")
        ]
        pipeline_contract = {
            "path": str(pipeline_contract_path),
            "audit_type": pipeline_contract_payload.get("audit_type"),
            "status": pipeline_contract_payload.get("status"),
            "passed": pipeline_contract_payload.get("passed"),
            "check_count": len(contract_checks),
            "check_names": check_names,
            "failed_checks": failed_checks,
            "integration": pipeline_contract_payload.get("integration") or {},
            "pixel_verification": pipeline_contract_payload.get("pixel_verification") or {},
        }
        checks.extend(
            [
                _check(
                    "pipeline_contract_present",
                    pipeline_contract_path.exists()
                    and pipeline_contract_payload.get("audit_type") == "pipeline_invariant_contract",
                    {
                        "path": str(pipeline_contract_path),
                        "exists": pipeline_contract_path.exists(),
                        "audit_type": pipeline_contract_payload.get("audit_type"),
                    },
                ),
                _check(
                    "pipeline_contract_passed",
                    pipeline_contract_payload.get("passed") is True,
                    {
                        "status": pipeline_contract_payload.get("status"),
                        "failed_checks": failed_checks,
                    },
                ),
            ]
        )

    stack_engine_contract_path = (
        Path(stack_engine_contract_json) if stack_engine_contract_json is not None else None
    )
    stack_engine_contract_payload = (
        _read_json_lenient(stack_engine_contract_path)
        if stack_engine_contract_path is not None and stack_engine_contract_path.exists()
        else {}
    )
    stack_engine_contract = None
    if stack_engine_contract_path is not None:
        contract_checks = [
            item for item in stack_engine_contract_payload.get("checks") or [] if isinstance(item, dict)
        ]
        check_names = [
            str(item.get("name")) for item in contract_checks if item.get("name") is not None
        ]
        failed_checks = [
            item.get("name")
            for item in contract_checks
            if not item.get("passed")
        ]
        stack_engine_contract = {
            "path": str(stack_engine_contract_path),
            "audit_type": stack_engine_contract_payload.get("audit_type"),
            "status": stack_engine_contract_payload.get("status"),
            "passed": stack_engine_contract_payload.get("passed"),
            "scope": stack_engine_contract_payload.get("scope"),
            "expected_integration_engine": stack_engine_contract_payload.get("expected_integration_engine"),
            "check_count": len(contract_checks),
            "check_names": check_names,
            "failed_checks": failed_checks,
            "adoption": stack_engine_contract_payload.get("adoption") or {},
            "default_promotion": stack_engine_contract_payload.get("default_promotion") or {},
        }
        checks.extend(
            [
                _check(
                    "stack_engine_contract_present",
                    stack_engine_contract_path.exists()
                    and stack_engine_contract_payload.get("audit_type") == "stack_engine_default_contract",
                    {
                        "path": str(stack_engine_contract_path),
                        "exists": stack_engine_contract_path.exists(),
                        "audit_type": stack_engine_contract_payload.get("audit_type"),
                    },
                ),
                _check(
                    "stack_engine_contract_passed",
                    stack_engine_contract_payload.get("passed") is True,
                    {
                        "status": stack_engine_contract_payload.get("status"),
                        "failed_checks": failed_checks,
                    },
                ),
            ]
        )

    contract_payload: dict[str, Any] | None = None
    if benchmark_contract is not None:
        contract_payload = load_benchmark_contract(benchmark_contract)
    resident_determinism_payload = (
        _read_json_lenient(resident_determinism_json) if resident_determinism_json is not None else {}
    )
    resident_determinism_summary = (
        resident_determinism_payload.get("summary")
        if isinstance(resident_determinism_payload.get("summary"), dict)
        else {}
    )
    output_numerical_drifts = (
        resident_determinism_payload.get("output_numerical_drifts")
        if isinstance(resident_determinism_payload.get("output_numerical_drifts"), list)
        else []
    )
    resident_determinism = None
    if resident_determinism_payload:
        resident_determinism = {
            "path": str(resident_determinism_json),
            "audit_type": resident_determinism_payload.get("audit_type"),
            "strict_passed": resident_determinism_summary.get("passed"),
            "summary": resident_determinism_summary,
            "timing": resident_determinism_payload.get("timing") or {},
            "output_numerical_drift_count": len(output_numerical_drifts),
            "output_numerical_drift_max_relative_rms": resident_determinism_summary.get(
                "output_numerical_drift_max_relative_rms"
            ),
        }
    performance_regression: dict[str, Any] | None = None
    dq_provenance_records = collect_dq_provenance_records(
        glass_run,
        dq_contract=(contract_payload or {}).get("dq_provenance"),
    )
    frame_accounting_record = collect_frame_accounting_record(glass_run)
    if benchmark_contract is not None:
        checks.extend(
            build_benchmark_contract_checks(
                contract_payload,
                glass_run=glass_run,
                speedup_summary=speedup,
                compare_payload=compare_payload,
                frame_type_counts=counts,
                dq_provenance_records=dq_provenance_records,
                frame_accounting_record=frame_accounting_record,
                resident_determinism=resident_determinism,
                output_numerical_drifts=output_numerical_drifts,
                pipeline_contract=pipeline_contract,
                stack_engine_contract=stack_engine_contract,
            )
        )
        performance_regression = build_benchmark_performance_diagnostics(
            contract_payload,
            glass_run=glass_run,
        )
    optimization_guidance = build_optimization_guidance(
        performance_regression=performance_regression,
        frame_accounting=frame_accounting_record,
        glass_run=glass_run,
    )
    release_contract_evidence = {
        "pipeline_contract": _pipeline_contract_release_evidence(
            checks=checks,
            pipeline_contract=pipeline_contract,
            contract_payload=contract_payload,
        ),
        "stack_engine_default_promotion": _stack_engine_default_promotion_release_evidence(
            checks=checks,
            stack_engine_contract=stack_engine_contract,
            contract_payload=contract_payload,
        ),
    }

    passed = all(item["passed"] for item in checks)
    return {
        "schema_version": 1,
        "status": "passed" if passed else "failed",
        "passed": passed,
        "manifest_path": str(manifest_path),
        "glass_run": str(glass_run),
        "wbpp_result": str(wbpp_result),
        "compare_json": str(compare_json),
        "benchmark_contract": None
        if benchmark_contract is None
        else {
            "path": str(benchmark_contract),
            "name": contract_payload.get("name") if contract_payload else None,
            "schema_version": contract_payload.get("schema_version") if contract_payload else None,
        },
        "frame_type_counts": counts,
        "checks": checks,
        "performance_regression": performance_regression,
        "optimization_guidance": optimization_guidance,
        "dq_provenance": {
            "schema_version": 1,
            "record_count": len(dq_provenance_records),
            "records": dq_provenance_records,
            "contract": (contract_payload or {}).get("dq_provenance") if contract_payload else None,
        },
        "frame_accounting": frame_accounting_record,
        "resident_determinism": resident_determinism,
        "contract_bundle": contract_bundle,
        "contract_bundle_schema": contract_bundle_schema,
        "resident_contracts": {
            "calibration": resident_calibration_contract,
            "result": resident_result_contract,
        },
        "pipeline_contract": pipeline_contract,
        "stack_engine_contract": stack_engine_contract,
        "release_contract_evidence": release_contract_evidence,
        "output_numerical_drifts": output_numerical_drifts,
        "speedup_summary": speedup,
        "clean_room": {
            "status": "compliant",
            "note": (
                "Acceptance audit consumes GLASS artifacts and user-generated PixInsight/WBPP "
                "black-box timing/output metadata only."
            ),
        },
    }


def write_acceptance_audit_markdown(path: str | Path, audit: dict[str, Any]) -> None:
    speedup = audit["speedup_summary"]
    comparison = speedup.get("comparison") or {}
    lines = [
        "# GLASS Acceptance Audit",
        "",
        f"- Status: {audit['status']}",
        f"- Benchmark contract: {(audit.get('benchmark_contract') or {}).get('name')}",
        f"- Contract bundle: {(audit.get('contract_bundle') or {}).get('status')}",
        f"- Pipeline contract: {(audit.get('pipeline_contract') or {}).get('status')}",
        f"- StackEngine contract: {(audit.get('stack_engine_contract') or {}).get('status')}",
        f"- DQ provenance records: {(audit.get('dq_provenance') or {}).get('record_count')}",
        f"- Frame accounting artifact: {(audit.get('frame_accounting') or {}).get('path')}",
        f"- Speedup vs WBPP: {speedup.get('speedup_vs_wbpp')}",
        f"- Frame counts: {audit.get('frame_type_counts')}",
        f"- Shape match: {comparison.get('shape_match')}",
        f"- RMS diff: {comparison.get('rms_diff')}",
        f"- abs diff p99: {comparison.get('abs_diff_p99')}",
        f"- Coverage fraction: {comparison.get('coverage_fraction')}",
        "",
        "## Checks",
        "",
    ]
    release_evidence = (
        (audit.get("release_contract_evidence") or {}).get("pipeline_contract")
        if isinstance(audit.get("release_contract_evidence"), dict)
        else None
    )
    if release_evidence:
        lines.extend(
            [
                "## Pipeline Contract Evidence",
                "",
                f"- Status: {release_evidence.get('status')}",
                f"- Required by benchmark contract: {release_evidence.get('required_by_benchmark_contract')}",
                f"- Pipeline contract path: {release_evidence.get('pipeline_contract_path')}",
                f"- Pipeline contract audit type: {release_evidence.get('pipeline_contract_audit_type')}",
                f"- Pipeline contract passed: {release_evidence.get('pipeline_contract_passed')}",
                f"- Pipeline contract checks: {release_evidence.get('pipeline_contract_check_count')}",
                f"- Acceptance pipeline checks passed: {release_evidence.get('passed_check_count')}",
                f"- Acceptance pipeline checks failed: {release_evidence.get('failed_check_count')}",
                f"- Failed pipeline checks: {release_evidence.get('failed_checks')}",
                "",
            ]
        )
        for item in release_evidence.get("checks") or []:
            marker = "PASS" if item.get("passed") else "FAIL"
            lines.append(f"- {marker}: {item.get('name')} - {item.get('evidence')}")
        lines.append("")
    stack_release_evidence = (
        (audit.get("release_contract_evidence") or {}).get("stack_engine_default_promotion")
        if isinstance(audit.get("release_contract_evidence"), dict)
        else None
    )
    if stack_release_evidence:
        lines.extend(
            [
                "## StackEngine Default Promotion Evidence",
                "",
                f"- Status: {stack_release_evidence.get('status')}",
                f"- Required by benchmark contract: {stack_release_evidence.get('required_by_benchmark_contract')}",
                f"- StackEngine contract path: {stack_release_evidence.get('stack_engine_contract_path')}",
                f"- StackEngine contract audit type: {stack_release_evidence.get('stack_engine_contract_audit_type')}",
                f"- StackEngine contract passed: {stack_release_evidence.get('stack_engine_contract_passed')}",
                f"- StackEngine contract scope: {stack_release_evidence.get('stack_engine_contract_scope')}",
                f"- Default promotion ready: {stack_release_evidence.get('default_promotion_ready')}",
                f"- Default promotion status: {stack_release_evidence.get('default_promotion_status')}",
                f"- Default promotion gaps: {stack_release_evidence.get('default_promotion_gap_count')}",
                f"- Default promotion blockers: {stack_release_evidence.get('default_promotion_blocker_count')}",
                f"- Adoption recommendation: {stack_release_evidence.get('adoption_recommendation')}",
                f"- Acceptance StackEngine checks passed: {stack_release_evidence.get('passed_check_count')}",
                f"- Acceptance StackEngine checks failed: {stack_release_evidence.get('failed_check_count')}",
                f"- Failed StackEngine checks: {stack_release_evidence.get('failed_checks')}",
                "",
            ]
        )
        for item in stack_release_evidence.get("checks") or []:
            marker = "PASS" if item.get("passed") else "FAIL"
            lines.append(f"- {marker}: {item.get('name')} - {item.get('evidence')}")
        lines.append("")
    bundle_schema = audit.get("contract_bundle_schema") if isinstance(audit.get("contract_bundle_schema"), dict) else {}
    if bundle_schema:
        lines.extend(["## Contract Bundle Schema", ""])
        lines.append(f"- Status: {bundle_schema.get('status')}")
        lines.append(
            f"- Schema version: {bundle_schema.get('schema_version')} "
            f"(required {bundle_schema.get('required_schema_version')})"
        )
        lines.append(
            f"- Purpose: {bundle_schema.get('purpose')} "
            f"(required {bundle_schema.get('required_purpose')})"
        )
        lines.append(f"- Artifact keys: {bundle_schema.get('artifact_keys')}")
        lines.append(f"- Missing artifacts: {bundle_schema.get('missing_required_artifacts')}")
        lines.append(f"- Argument map keys: {bundle_schema.get('argument_map_keys')}")
        lines.append(f"- Missing argument map keys: {bundle_schema.get('missing_required_argument_map_keys')}")
        lines.append("")
    resident_contracts = audit.get("resident_contracts") if isinstance(audit.get("resident_contracts"), dict) else {}
    resident_rows = [
        (name, payload)
        for name, payload in resident_contracts.items()
        if isinstance(payload, dict)
    ]
    if resident_rows:
        lines.extend(["## Resident Bundle Contracts", ""])
        for name, payload in resident_rows:
            lines.append(
                "- "
                f"{name}: status={payload.get('status')} passed={payload.get('passed')} "
                f"type={payload.get('artifact_type')} checks={payload.get('check_count')} "
                f"path={payload.get('path')}"
            )
            failed = payload.get("failed_checks")
            if failed:
                lines.append(f"  failed_checks={failed}")
        lines.append("")
    for item in audit["checks"]:
        marker = "PASS" if item["passed"] else "FAIL"
        lines.append(f"- {marker}: {item['name']} - {item['evidence']}")
    dq = audit.get("dq_provenance") or {}
    if dq.get("records"):
        lines.extend(["", "## DQ Provenance", ""])
        for record in dq.get("records") or []:
            summary = record.get("summary") or {}
            verification = record.get("dq_map_pixel_verification") or {}
            output_maps = record.get("output_count_map_verification") or {}
            lines.append(
                "- "
                f"{record.get('source_file')}[{record.get('index')}] "
                f"schema={summary.get('source_schema')} engine={summary.get('engine')} "
                f"stage={summary.get('stage')} item={summary.get('item')} "
                f"dq_map_exists={record.get('dq_map_exists')} "
                f"legacy_normalized={record.get('normalized_from_legacy')} "
                f"pixel_verification={verification.get('status')} "
                f"coverage_verification={(output_maps.get('coverage') or {}).get('status')}"
            )
    accounting = audit.get("frame_accounting") or {}
    if accounting:
        summary = accounting.get("summary") or {}
        exception_summary = accounting.get("exception_summary") or {}
        exceptions = accounting.get("exception_frames") if isinstance(accounting.get("exception_frames"), list) else []
        weights = accounting.get("integration_weight_counts") or {}
        registration = accounting.get("registration_counts") or {}
        lines.extend(["", "## Frame Accounting", ""])
        lines.append(f"- Exists: {accounting.get('exists')}")
        lines.append(f"- Input lights: {summary.get('input_light_frames')}")
        lines.append(f"- Integrated frames: {summary.get('integrated_frames')}")
        lines.append(f"- Zero-weight frames: {summary.get('zero_weight_frames')}")
        lines.append(f"- Final status counts: {summary.get('final_status_counts')}")
        lines.append(f"- Exception summary: {exception_summary}")
        lines.append(f"- Integration weight counts: {weights}")
        lines.append(f"- Registration counts: {registration}")
        for item in exceptions[:12]:
            lines.append(
                "- Exception frame: "
                f"{item.get('frame_id')} status={item.get('final_status')} "
                f"stage={item.get('primary_stage')} reason={item.get('primary_reason')}"
            )
    regression = audit.get("performance_regression")
    if regression:
        lines.extend(["", "## Performance Regression Diagnostics", ""])
        lines.append(f"- Status: {regression.get('status')}")
        worst = regression.get("worst_regression") or {}
        if worst:
            lines.append(
                "- Worst stage: "
                f"{worst.get('stage')} actual={worst.get('actual_s')}s "
                f"baseline={worst.get('baseline_s')}s factor={worst.get('factor')}"
            )
        for item in (regression.get("items") or [])[:8]:
            lines.append(
                "- "
                f"{item.get('status')}: {item.get('stage')} "
                f"actual={item.get('actual_s')}s baseline={item.get('baseline_s')}s "
                f"delta={item.get('delta_s')}s factor={item.get('factor')}"
            )
    resident_determinism = audit.get("resident_determinism") or {}
    if resident_determinism:
        summary = resident_determinism.get("summary") or {}
        lines.extend(["", "## Resident Determinism", ""])
        lines.append(f"- Source: {resident_determinism.get('path')}")
        lines.append(f"- Strict passed: {resident_determinism.get('strict_passed')}")
        lines.append(f"- Output differences: {summary.get('output_difference_count')}")
        lines.append(f"- Output numerical drifts: {resident_determinism.get('output_numerical_drift_count')}")
        lines.append(
            "- Max relative output RMS drift: "
            f"{resident_determinism.get('output_numerical_drift_max_relative_rms')}"
        )
        for item in (audit.get("output_numerical_drifts") or [])[:8]:
            drift = item.get("drift") if isinstance(item.get("drift"), dict) else {}
            lines.append(
                "- Output drift: "
                f"{item.get('key')} {item.get('field')} "
                f"rms={drift.get('rms')} mean_abs={drift.get('mean_abs')} "
                f"relative_rms={drift.get('relative_rms_to_baseline_std')}"
            )
    guidance = audit.get("optimization_guidance") or {}
    targets = guidance.get("targets") if isinstance(guidance.get("targets"), list) else []
    if targets:
        exception_context = guidance.get("exception_context") or {}
        lines.extend(["", "## Optimization Guidance", ""])
        lines.append(f"- Primary target: {guidance.get('primary_target')}")
        lines.append(f"- Exception context: {exception_context}")
        for target in targets[:4]:
            lines.append(
                "- "
                f"#{target.get('rank')} {target.get('label')} "
                f"stage={target.get('primary_stage')} current={target.get('current_s')}s "
                f"baseline={target.get('baseline_s')}s factor={target.get('factor')} "
                f"action={target.get('next_action')}"
            )
    lines.extend(["", "## Clean-room", "", f"- {audit['clean_room']['note']}", ""])
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines), encoding="utf-8")


def write_acceptance_audit(
    out_json: str | Path,
    audit: dict[str, Any],
    markdown: str | Path | None = None,
) -> None:
    write_json(out_json, audit)
    if markdown is not None:
        write_acceptance_audit_markdown(markdown, audit)
