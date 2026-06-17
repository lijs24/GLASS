from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from glass.io.json_io import read_json, write_json
from glass.models import now_iso


def _load_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = read_json(path)
    return payload if isinstance(payload, dict) else {}


def _check(name: str, passed: bool, evidence: dict[str, Any], note: str = "") -> dict[str, Any]:
    return {
        "name": name,
        "passed": bool(passed),
        "evidence": evidence,
        "note": note,
    }


def _artifact_path_exists(path_value: Any, run_root: Path) -> bool:
    if not path_value:
        return False
    path = Path(str(path_value))
    if path.is_absolute():
        return path.exists()
    return path.exists() or (run_root / path).exists()


def _summary_is_stack_engine(summary: Any, *, stage: str | None = None) -> bool:
    if not isinstance(summary, dict):
        return False
    if summary.get("source_schema") != "stack_engine_dq_provenance":
        return False
    if summary.get("engine") != "stack_engine_cpu":
        return False
    if stage is not None and summary.get("stage") != stage:
        return False
    return True


def _positive_int(value: Any) -> bool:
    try:
        return int(value) > 0
    except (TypeError, ValueError):
        return False


def _finite_float(value: Any) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(numeric):
        return None
    return numeric


def _master_stats_contract(payload: dict[str, Any]) -> dict[str, Any]:
    stats = payload.get("stats") if isinstance(payload.get("stats"), dict) else {}
    required = ("min", "max", "mean", "median", "std")
    values = {key: _finite_float(stats.get(key)) for key in required}
    missing = [key for key in required if key not in stats]
    nonfinite = [key for key, value in values.items() if value is None and key in stats]
    bounds_ok = False
    if all(values[key] is not None for key in ("min", "max", "mean", "median")):
        minimum = float(values["min"])
        maximum = float(values["max"])
        mean = float(values["mean"])
        median = float(values["median"])
        bounds_ok = minimum <= mean <= maximum and minimum <= median <= maximum
    std_ok = values["std"] is not None and float(values["std"]) >= 0.0
    passed = not missing and not nonfinite and bounds_ok and std_ok
    return {
        "passed": passed,
        "required_keys": list(required),
        "missing_keys": missing,
        "nonfinite_keys": nonfinite,
        "bounds_ok": bounds_ok,
        "std_nonnegative": std_ok,
        "stats": {key: stats.get(key) for key in required if key in stats},
    }


def _master_semantics_contract(payload: dict[str, Any]) -> dict[str, Any]:
    master_type = str(payload.get("type") or "")
    checks: list[dict[str, Any]] = [
        _check(
            "type_recorded",
            master_type in {"bias", "dark", "flat"},
            {"type": payload.get("type"), "allowed": ["bias", "dark", "flat"]},
        ),
        _check(
            "tile_size_recorded",
            _positive_int(payload.get("tile_size")),
            {"tile_size": payload.get("tile_size")},
        ),
        _check(
            "master_rejection_recorded",
            bool(payload.get("master_rejection")),
            {"master_rejection": payload.get("master_rejection")},
        ),
    ]
    if master_type == "dark":
        checks.extend(
            [
                _check(
                    "dark_bias_semantics_recorded",
                    isinstance(payload.get("master_dark_includes_bias"), bool),
                    {"master_dark_includes_bias": payload.get("master_dark_includes_bias")},
                ),
                _check(
                    "dark_source_bias_subtraction_recorded",
                    isinstance(payload.get("bias_subtracted_from_source"), bool),
                    {"bias_subtracted_from_source": payload.get("bias_subtracted_from_source")},
                ),
            ]
        )
    elif master_type == "flat":
        per_flat = payload.get("per_flat_normalization")
        checks.extend(
            [
                _check(
                    "flat_normalization_recorded",
                    payload.get("normalization") in {"mean", "median"},
                    {"normalization": payload.get("normalization")},
                ),
                _check(
                    "flat_normalization_stage_recorded",
                    payload.get("normalization_stage") == "per_flat",
                    {"normalization_stage": payload.get("normalization_stage")},
                ),
                _check(
                    "flat_floor_recorded",
                    _finite_float(payload.get("flat_floor")) is not None,
                    {"flat_floor": payload.get("flat_floor")},
                ),
                _check(
                    "per_flat_normalization_recorded",
                    isinstance(per_flat, list) and bool(per_flat),
                    {
                        "count": len(per_flat) if isinstance(per_flat, list) else None,
                    },
                ),
            ]
        )
    passed = all(item["passed"] for item in checks)
    return {
        "passed": passed,
        "master_type": master_type or None,
        "failed_checks": [item["name"] for item in checks if not item["passed"]],
        "checks": checks,
    }


def _master_science_contract(payload: dict[str, Any], *, path_exists: bool) -> dict[str, Any]:
    stats_contract = _master_stats_contract(payload)
    semantics_contract = _master_semantics_contract(payload)
    checks = [
        _check("master_path_exists", path_exists, {"path": payload.get("path")}),
        _check("master_stats_contract", bool(stats_contract.get("passed")), stats_contract),
        _check("master_semantics_contract", bool(semantics_contract.get("passed")), semantics_contract),
    ]
    return {
        "schema_version": 1,
        "contract_type": "master_calibration_surface_contract",
        "passed": all(item["passed"] for item in checks),
        "status": "passed" if all(item["passed"] for item in checks) else "failed",
        "checks": checks,
        "stats": stats_contract,
        "semantics": semantics_contract,
    }


def build_master_calibration_surface_contract(
    payload: dict[str, Any],
    *,
    path_exists: bool,
) -> dict[str, Any]:
    """Audit the output-side science metadata for one master calibration frame."""

    return _master_science_contract(payload, path_exists=path_exists)


def _result_contract_passed(provenance: Any) -> bool:
    if not isinstance(provenance, dict):
        return False
    contract = provenance.get("result_contract")
    return isinstance(contract, dict) and bool(contract.get("passed"))


def _resident_contract_lookup(payload: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    if payload.get("artifact_type") != "resident_cuda_result_contract":
        return {}
    top_level_passed = payload.get("passed") is True
    outputs = payload.get("outputs") if isinstance(payload.get("outputs"), list) else []
    lookup: dict[tuple[str, str], dict[str, Any]] = {}
    for output in outputs:
        if not isinstance(output, dict):
            continue
        index_key = str(output.get("index"))
        filter_key = str(output.get("filter") or "")
        checks = output.get("checks") if isinstance(output.get("checks"), list) else []
        record = {
            "artifact_type": payload.get("artifact_type"),
            "top_level_passed": top_level_passed,
            "passed": top_level_passed and output.get("passed") is True,
            "status": output.get("status"),
            "check_count": len([item for item in checks if isinstance(item, dict)]),
            "active_frame_count": output.get("active_frame_count"),
            "frame_count": output.get("frame_count"),
            "contract_type": output.get("contract_type"),
        }
        lookup[("index", index_key)] = record
        if filter_key:
            lookup[("filter", filter_key)] = record
    return lookup


def _resident_contract_for_output(
    index: int,
    payload: dict[str, Any],
    lookup: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any] | None:
    by_index = lookup.get(("index", str(index)))
    if by_index is not None:
        return by_index
    filter_value = payload.get("filter")
    if filter_value is None:
        return None
    return lookup.get(("filter", str(filter_value)))


def _resident_calibration_lookup(payload: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    if payload.get("artifact_type") != "resident_cuda_calibration_contract":
        return {}
    top_level_passed = payload.get("passed") is True
    outputs = payload.get("outputs") if isinstance(payload.get("outputs"), list) else []
    lookup: dict[tuple[str, str], dict[str, Any]] = {}
    for output in outputs:
        if not isinstance(output, dict):
            continue
        index_key = str(output.get("index"))
        filter_key = str(output.get("filter") or "")
        checks = output.get("checks") if isinstance(output.get("checks"), list) else []
        record = {
            "artifact_type": payload.get("artifact_type"),
            "top_level_passed": top_level_passed,
            "passed": top_level_passed and output.get("passed") is True,
            "status": output.get("status"),
            "check_count": len([item for item in checks if isinstance(item, dict)]),
            "frame_count": output.get("frame_count"),
            "set_count": output.get("set_count"),
            "bias_count": output.get("bias_count"),
            "dark_count": output.get("dark_count"),
            "flat_count": output.get("flat_count"),
            "calibration_group_policy": output.get("calibration_group_policy"),
        }
        lookup[("index", index_key)] = record
        if filter_key:
            lookup[("filter", filter_key)] = record
    return lookup


def _resident_calibration_records(
    payload: dict[str, Any],
) -> list[dict[str, Any]]:
    if payload.get("artifact_type") != "resident_cuda_calibration_contract":
        return []
    outputs = payload.get("outputs") if isinstance(payload.get("outputs"), list) else []
    records: list[dict[str, Any]] = []
    for output in outputs:
        if not isinstance(output, dict):
            continue
        passed = payload.get("passed") is True and output.get("passed") is True
        science_contract = {
            "schema_version": 1,
            "contract_type": "resident_calibration_surface_contract",
            "passed": passed,
            "status": "passed" if passed else "failed",
            "source": "resident_cuda_calibration_contract",
            "note": (
                "Resident calibration surfaces are audited by the attached resident CUDA "
                "calibration contract; per-master CPU stats are not required here."
            ),
        }
        records.append(
            {
                "name": f"resident_calibration_{output.get('filter') or output.get('index')}",
                "type": "resident_calibration",
                "path": output.get("master_path"),
                "path_exists": output.get("master_path_exists"),
                "tile_stack_mode": "cuda_resident_stack",
                "backend": "cuda_resident_stack",
                "stack_engine_enabled": True,
                "fallback_reason": None,
                "has_dq_provenance": True,
                "input_samples": output.get("frame_count"),
                "result_contract_passed": passed,
                "resident_calibration_contract_passed": passed,
                "resident_calibration_contract_status": output.get("status"),
                "resident_calibration_contract_check_count": len(
                    [item for item in output.get("checks") or [] if isinstance(item, dict)]
                ),
                "resident_calibration_frame_count": output.get("frame_count"),
                "resident_calibration_set_count": output.get("set_count"),
                "resident_calibration_bias_count": output.get("bias_count"),
                "resident_calibration_dark_count": output.get("dark_count"),
                "resident_calibration_flat_count": output.get("flat_count"),
                "summary_source_schema": "resident_cuda_calibration_contract",
                "summary_engine": "cuda_resident_stack",
                "summary_stage": "master_calibration",
                "science_contract_ok": passed,
                "science_contract": science_contract,
                "contract_ok": passed,
            }
        )
    return records


def _master_record(name: str, payload: dict[str, Any], run_root: Path) -> dict[str, Any]:
    path_value = payload.get("path")
    exists = _artifact_path_exists(path_value, run_root)
    provenance = payload.get("stack_engine_dq_provenance")
    summary = payload.get("dq_provenance_summary")
    resident_contract = payload.get("resident_calibration_contract")
    science_contract = _master_science_contract(payload, path_exists=exists)
    science_ok = bool(science_contract.get("passed"))
    stack_result_contract_passed = _result_contract_passed(provenance)
    resident_contract_passed = (
        isinstance(resident_contract, dict)
        and resident_contract.get("artifact_type") == "resident_cuda_calibration_master_contract"
        and bool(resident_contract.get("passed"))
    )
    stack_engine_ok = (
        bool(payload.get("stack_engine_enabled"))
        and str(payload.get("tile_stack_mode") or "").startswith("stack_engine_cpu")
        and not payload.get("stack_engine_fallback_reason")
        and isinstance(provenance, dict)
        and _positive_int(provenance.get("input_samples"))
        and stack_result_contract_passed
        and _summary_is_stack_engine(summary, stage="master_calibration")
        and science_ok
    )
    resident_engine_ok = (
        bool(payload.get("stack_engine_enabled"))
        and payload.get("tile_stack_mode") == "cuda_resident_stack"
        and not payload.get("stack_engine_fallback_reason")
        and isinstance(summary, dict)
        and summary.get("engine") == "cuda_resident_stack"
        and summary.get("stage") == "master_calibration"
        and resident_contract_passed
        and science_ok
    )
    return {
        "name": name,
        "type": payload.get("type"),
        "path": path_value,
        "path_exists": exists,
        "stats_present": isinstance(payload.get("stats"), dict),
        "science_contract_ok": science_ok,
        "science_contract": science_contract,
        "tile_stack_mode": payload.get("tile_stack_mode"),
        "backend": payload.get("backend"),
        "stack_engine_enabled": bool(payload.get("stack_engine_enabled")),
        "fallback_reason": payload.get("stack_engine_fallback_reason"),
        "has_dq_provenance": isinstance(provenance, dict),
        "input_samples": provenance.get("input_samples") if isinstance(provenance, dict) else None,
        "result_contract_passed": stack_result_contract_passed or resident_contract_passed,
        "stack_result_contract_passed": stack_result_contract_passed,
        "resident_calibration_contract_passed": resident_contract_passed,
        "resident_calibration_contract_status": resident_contract.get("status")
        if isinstance(resident_contract, dict)
        else None,
        "resident_calibration_contract_check_count": len(resident_contract.get("checks") or [])
        if isinstance(resident_contract, dict)
        else None,
        "summary_source_schema": summary.get("source_schema") if isinstance(summary, dict) else None,
        "summary_engine": summary.get("engine") if isinstance(summary, dict) else None,
        "summary_stage": summary.get("stage") if isinstance(summary, dict) else None,
        "contract_ok": stack_engine_ok or resident_engine_ok,
    }


def _integration_record(
    index: int,
    payload: dict[str, Any],
    expected_engine: str,
    resident_contracts: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    provenance = payload.get("stack_engine_dq_provenance")
    summary = payload.get("dq_provenance_summary")
    resident_contract = _resident_contract_for_output(index, payload, resident_contracts)
    stack_result_contract_passed = _result_contract_passed(provenance)
    resident_result_contract_passed = bool((resident_contract or {}).get("passed"))
    stack_engine_ok = (
        bool(payload.get("stack_engine_enabled"))
        and payload.get("tile_stack_mode") == "stack_engine_cpu"
        and isinstance(provenance, dict)
        and _positive_int(provenance.get("input_samples"))
        and stack_result_contract_passed
        and _summary_is_stack_engine(summary, stage="integration")
    )
    resident_summary_ok = isinstance(summary, dict) and summary.get("engine") == "cuda_resident_stack"
    if expected_engine == "stack_engine_cpu":
        contract_ok = stack_engine_ok
    elif expected_engine == "cuda_resident_stack":
        contract_ok = resident_summary_ok
    else:
        contract_ok = stack_engine_ok or resident_summary_ok
    return {
        "index": index,
        "filter": payload.get("filter"),
        "backend": payload.get("backend"),
        "source_stage": payload.get("source_stage"),
        "tile_stack_mode": payload.get("tile_stack_mode"),
        "stack_engine_enabled": bool(payload.get("stack_engine_enabled")),
        "has_stack_engine_dq_provenance": isinstance(provenance, dict),
        "input_samples": provenance.get("input_samples") if isinstance(provenance, dict) else None,
        "result_contract_passed": stack_result_contract_passed or resident_result_contract_passed,
        "stack_result_contract_passed": stack_result_contract_passed,
        "resident_result_contract_passed": resident_result_contract_passed,
        "resident_result_contract_status": (resident_contract or {}).get("status"),
        "resident_result_contract_check_count": (resident_contract or {}).get("check_count"),
        "resident_result_contract_active_frame_count": (resident_contract or {}).get("active_frame_count"),
        "summary_source_schema": summary.get("source_schema") if isinstance(summary, dict) else None,
        "summary_engine": summary.get("engine") if isinstance(summary, dict) else None,
        "summary_stage": summary.get("stage") if isinstance(summary, dict) else None,
        "expected_engine": expected_engine,
        "contract_ok": contract_ok,
    }


def _engine_family(record: dict[str, Any]) -> str:
    mode = str(record.get("tile_stack_mode") or "")
    summary_engine = str(record.get("summary_engine") or "")
    backend = str(record.get("backend") or "")
    if mode.startswith("stack_engine_cpu") or summary_engine == "stack_engine_cpu":
        return "stack_engine_cpu"
    if summary_engine == "cuda_resident_stack" or backend == "cuda_resident_stack":
        return "cuda_resident_stack"
    if mode:
        return mode
    return "unknown"


def _adoption_surface_record(surface: str, record: dict[str, Any]) -> dict[str, Any]:
    family = _engine_family(record)
    fallback = record.get("fallback_reason")
    result_contract_passed = bool(record.get("result_contract_passed"))
    stack_engine_contract_ready = (
        family in {"stack_engine_cpu", "cuda_resident_stack"}
        and bool(record.get("contract_ok"))
        and result_contract_passed
        and not fallback
    )
    if stack_engine_contract_ready:
        gap_reason = ""
    elif family == "cuda_resident_stack":
        gap_reason = "resident_cuda_surface"
    elif not record.get("science_contract_ok") and surface == "master_calibration":
        gap_reason = "master_calibration_science_contract_failed"
    elif family == "stack_engine_cpu" and not result_contract_passed:
        gap_reason = "missing_or_failed_result_contract"
    elif fallback:
        gap_reason = "stack_engine_fallback"
    else:
        gap_reason = "legacy_or_unknown_engine"
    return {
        "surface": surface,
        "item": record.get("name", record.get("filter", record.get("index"))),
        "type": record.get("type", "light" if surface == "integration" else None),
        "engine_family": family,
        "tile_stack_mode": record.get("tile_stack_mode"),
        "summary_engine": record.get("summary_engine"),
        "stack_engine_enabled": record.get("stack_engine_enabled"),
        "result_contract_passed": record.get("result_contract_passed"),
        "stack_result_contract_passed": record.get("stack_result_contract_passed"),
        "resident_result_contract_passed": record.get("resident_result_contract_passed"),
        "resident_calibration_contract_passed": record.get("resident_calibration_contract_passed"),
        "science_contract_ok": record.get("science_contract_ok"),
        "contract_ok": record.get("contract_ok"),
        "fallback_reason": fallback,
        "stack_engine_contract_ready": stack_engine_contract_ready,
        "phase2_stack_engine_default_gap": not stack_engine_contract_ready,
        "gap_reason": gap_reason,
    }


def _build_adoption_summary(
    masters: list[dict[str, Any]],
    integration_records: list[dict[str, Any]],
) -> dict[str, Any]:
    surfaces = [
        *[_adoption_surface_record("master_calibration", record) for record in masters],
        *[_adoption_surface_record("integration", record) for record in integration_records],
    ]
    engine_counts: dict[str, int] = {}
    for surface in surfaces:
        family = str(surface.get("engine_family") or "unknown")
        engine_counts[family] = engine_counts.get(family, 0) + 1
    gap_surfaces = [surface for surface in surfaces if surface.get("phase2_stack_engine_default_gap")]
    fallback_surfaces = [surface for surface in surfaces if surface.get("fallback_reason")]
    if not surfaces:
        recommendation = "no_surfaces_to_audit"
    elif not gap_surfaces:
        recommendation = "stack_engine_default_ready"
    elif engine_counts.get("cuda_resident_stack"):
        recommendation = "resident_cuda_surfaces_remain"
    else:
        recommendation = "stack_engine_contract_gaps_remain"
    return {
        "schema_version": 1,
        "target_engine": "stack_engine_cpu",
        "surface_count": len(surfaces),
        "stack_engine_surface_count": engine_counts.get("stack_engine_cpu", 0),
        "cuda_resident_surface_count": engine_counts.get("cuda_resident_stack", 0),
        "other_surface_count": len(surfaces)
        - engine_counts.get("stack_engine_cpu", 0)
        - engine_counts.get("cuda_resident_stack", 0),
        "engine_counts": engine_counts,
        "contract_ready_count": sum(1 for surface in surfaces if surface.get("stack_engine_contract_ready")),
        "result_contract_passed_count": sum(1 for surface in surfaces if surface.get("result_contract_passed")),
        "fallback_count": len(fallback_surfaces),
        "phase2_stack_engine_default_gap_count": len(gap_surfaces),
        "gap_surfaces": [
            {
                "surface": surface.get("surface"),
                "item": surface.get("item"),
                "engine_family": surface.get("engine_family"),
                "gap_reason": surface.get("gap_reason"),
            }
            for surface in gap_surfaces
        ],
        "recommendation": recommendation,
        "surfaces": surfaces,
    }


def _build_default_promotion_summary(
    *,
    scope: str,
    checks: list[dict[str, Any]],
    masters: list[dict[str, Any]],
    integration_records: list[dict[str, Any]],
    adoption: dict[str, Any],
) -> dict[str, Any]:
    failed_checks = [item.get("name") for item in checks if not item.get("passed")]
    blockers: list[dict[str, Any]] = []
    if failed_checks:
        blockers.append(
            {
                "name": "stack_engine_contract_failed",
                "failed_checks": failed_checks,
            }
        )
    if scope != "all":
        blockers.append(
            {
                "name": "scope_not_all",
                "actual": scope,
                "required": "all",
            }
        )
    if not masters:
        blockers.append(
            {
                "name": "missing_calibration_surface",
                "actual": len(masters),
                "required_min": 1,
            }
        )
    if not integration_records:
        blockers.append(
            {
                "name": "missing_integration_surface",
                "actual": len(integration_records),
                "required_min": 1,
            }
        )
    gap_count = int(adoption.get("phase2_stack_engine_default_gap_count") or 0)
    if gap_count:
        blockers.append(
            {
                "name": "phase2_stack_engine_default_gaps",
                "gap_count": gap_count,
                "gap_surfaces": adoption.get("gap_surfaces") or [],
            }
        )
    recommendation = str(adoption.get("recommendation") or "")
    if recommendation != "stack_engine_default_ready":
        blockers.append(
            {
                "name": "adoption_recommendation_not_ready",
                "actual": recommendation,
                "required": "stack_engine_default_ready",
            }
        )
    ready = not blockers
    return {
        "schema_version": 1,
        "target_engine": adoption.get("target_engine", "stack_engine_cpu"),
        "ready": ready,
        "status": "ready" if ready else "blocked",
        "required_scope": "all",
        "actual_scope": scope,
        "surface_count": adoption.get("surface_count", 0),
        "calibration_surface_count": len(masters),
        "integration_surface_count": len(integration_records),
        "phase2_stack_engine_default_gap_count": gap_count,
        "recommendation": recommendation,
        "blocker_count": len(blockers),
        "blockers": blockers,
    }


def build_stack_engine_contract_audit(
    run_dir: str | Path,
    *,
    scope: str = "all",
    expected_integration_engine: str = "stack_engine_cpu",
    resident_result_contract: dict[str, Any] | None = None,
    resident_calibration_contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    run_root = Path(run_dir)
    calibration_path = run_root / "calibration_artifacts.json"
    integration_path = run_root / "integration_results.json"
    resident_result_contract_path = run_root / "resident_result_contract.json"
    calibration = _load_json_object(calibration_path)
    integration = _load_json_object(integration_path)
    resident_result_contract_source = "provided" if isinstance(resident_result_contract, dict) else "missing"
    if resident_result_contract is None and resident_result_contract_path.exists():
        resident_result_contract = _load_json_object(resident_result_contract_path)
        resident_result_contract_source = "run_default"
    resident_contracts = _resident_contract_lookup(resident_result_contract or {})
    resident_calibration_contracts = _resident_calibration_lookup(resident_calibration_contract or {})
    checks: list[dict[str, Any]] = []

    include_calibration = scope in {"all", "calibration"}
    include_integration = scope in {"all", "integration"}
    masters: list[dict[str, Any]] = []
    integration_records: list[dict[str, Any]] = []

    if include_calibration:
        master_payloads = calibration.get("masters") if isinstance(calibration.get("masters"), dict) else {}
        masters = [_master_record(str(name), payload, run_root) for name, payload in master_payloads.items()]
        masters.extend(_resident_calibration_records(resident_calibration_contract or {}))
        calibration_artifact_available = calibration_path.exists() or bool(resident_calibration_contracts)
        checks.extend(
            [
                _check(
                    "calibration_artifact_exists",
                    calibration_artifact_available,
                    {
                        "path": str(calibration_path),
                        "exists": calibration_path.exists(),
                        "resident_calibration_contract_attached": bool(resident_calibration_contracts),
                    },
                ),
                _check(
                    "calibration_master_records_present",
                    bool(masters),
                    {"actual": len(masters), "required_min": 1},
                ),
                _check(
                    "calibration_masters_use_stack_engine",
                    bool(masters) and all(item["contract_ok"] for item in masters),
                    {
                        "master_count": len(masters),
                        "failed": [item["name"] for item in masters if not item["contract_ok"]],
                    },
                    "All master bias/dark/flat records must use StackEngine without fallback.",
                ),
                _check(
                    "calibration_masters_science_auditable",
                    bool(masters) and all(item.get("science_contract_ok") for item in masters),
                    {
                        "master_count": len(masters),
                        "failed": [
                            {
                                "name": item["name"],
                                "type": item.get("type"),
                                "science_contract": item.get("science_contract"),
                            }
                            for item in masters
                            if not item.get("science_contract_ok")
                        ],
                    },
                    "Master calibration records must include output stats and calibration semantics.",
                ),
            ]
        )

    if include_integration:
        outputs = integration.get("outputs") if isinstance(integration.get("outputs"), list) else []
        integration_records = [
            _integration_record(index, payload, expected_integration_engine, resident_contracts)
            for index, payload in enumerate(outputs)
            if isinstance(payload, dict)
        ]
        checks.extend(
            [
                _check(
                    "integration_artifact_exists",
                    integration_path.exists(),
                    {"path": str(integration_path)},
                ),
                _check(
                    "integration_output_records_present",
                    bool(integration_records),
                    {"actual": len(integration_records), "required_min": 1},
                ),
                _check(
                    f"integration_outputs_use:{expected_integration_engine}",
                    bool(integration_records) and all(item["contract_ok"] for item in integration_records),
                    {
                        "output_count": len(integration_records),
                        "failed": [item["index"] for item in integration_records if not item["contract_ok"]],
                    },
                    "Tile/CPU light integration must use StackEngine by default; resident CUDA is explicit.",
                ),
            ]
        )

    adoption = _build_adoption_summary(masters, integration_records)
    passed = all(item["passed"] for item in checks)
    default_promotion = _build_default_promotion_summary(
        scope=scope,
        checks=checks,
        masters=masters,
        integration_records=integration_records,
        adoption=adoption,
    )
    return {
        "schema_version": 1,
        "audit_type": "stack_engine_default_contract",
        "created_at": now_iso(),
        "run_dir": str(run_root),
        "scope": scope,
        "expected_integration_engine": expected_integration_engine,
        "resident_calibration_contract_attached": bool(resident_calibration_contracts),
        "resident_result_contract_attached": bool(resident_contracts),
        "resident_result_contract_path": str(resident_result_contract_path)
        if resident_result_contract_source == "run_default"
        else None,
        "resident_result_contract_source": resident_result_contract_source
        if bool(resident_contracts)
        else "missing",
        "status": "passed" if passed else "failed",
        "passed": passed,
        "checks": checks,
        "calibration": {
            "artifact_path": str(calibration_path),
            "master_count": len(masters),
            "masters": masters,
        },
        "integration": {
            "artifact_path": str(integration_path),
            "output_count": len(integration_records),
            "outputs": integration_records,
        },
        "adoption": adoption,
        "default_promotion": default_promotion,
    }


def write_stack_engine_contract_markdown(path: str | Path, audit: dict[str, Any]) -> None:
    lines = [
        "# GLASS StackEngine Default Contract Audit",
        "",
        f"- Status: {audit['status']}",
        f"- Run: `{audit['run_dir']}`",
        f"- Scope: `{audit['scope']}`",
        f"- Expected integration engine: `{audit['expected_integration_engine']}`",
        f"- Resident calibration contract attached: `{audit.get('resident_calibration_contract_attached')}`",
        f"- Resident result contract attached: `{audit.get('resident_result_contract_attached')}`",
        f"- StackEngine adoption recommendation: `{(audit.get('adoption') or {}).get('recommendation')}`",
        f"- Phase 2 StackEngine default gaps: `{(audit.get('adoption') or {}).get('phase2_stack_engine_default_gap_count')}`",
        f"- Default promotion ready: `{(audit.get('default_promotion') or {}).get('ready')}`",
        "",
        "## Checks",
        "",
    ]
    for item in audit.get("checks") or []:
        marker = "PASS" if item.get("passed") else "FAIL"
        lines.append(f"- {marker}: `{item.get('name')}` - {item.get('evidence')}")
    adoption = audit.get("adoption") if isinstance(audit.get("adoption"), dict) else {}
    if adoption:
        lines.extend(["", "## StackEngine Adoption", ""])
        lines.append(f"- Target engine: `{adoption.get('target_engine')}`")
        lines.append(f"- Surface count: `{adoption.get('surface_count')}`")
        lines.append(f"- StackEngine surfaces: `{adoption.get('stack_engine_surface_count')}`")
        lines.append(f"- Resident CUDA surfaces: `{adoption.get('cuda_resident_surface_count')}`")
        lines.append(f"- Contract-ready surfaces: `{adoption.get('contract_ready_count')}`")
        lines.append(f"- Gap count: `{adoption.get('phase2_stack_engine_default_gap_count')}`")
        lines.append(f"- Recommendation: `{adoption.get('recommendation')}`")
        for surface in adoption.get("surfaces") or []:
            lines.append(
                "- "
                f"{surface.get('surface')}:{surface.get('item')} "
                f"engine={surface.get('engine_family')} "
                f"ready={surface.get('stack_engine_contract_ready')} "
                f"gap={surface.get('phase2_stack_engine_default_gap')} "
                f"reason={surface.get('gap_reason')}"
            )
    promotion = audit.get("default_promotion") if isinstance(audit.get("default_promotion"), dict) else {}
    if promotion:
        lines.extend(["", "## Default Promotion Guard", ""])
        lines.append(f"- Status: `{promotion.get('status')}`")
        lines.append(f"- Ready: `{promotion.get('ready')}`")
        lines.append(f"- Required scope: `{promotion.get('required_scope')}`")
        lines.append(f"- Actual scope: `{promotion.get('actual_scope')}`")
        lines.append(f"- Blocker count: `{promotion.get('blocker_count')}`")
        for blocker in promotion.get("blockers") or []:
            lines.append(f"- Blocker `{blocker.get('name')}`: {blocker}")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_stack_engine_contract_audit(
    path: str | Path,
    audit: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(path, audit)
    if markdown is not None:
        write_stack_engine_contract_markdown(markdown, audit)
