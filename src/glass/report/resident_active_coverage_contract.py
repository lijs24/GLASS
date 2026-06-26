from __future__ import annotations

from pathlib import Path
from typing import Any

from glass.io.json_io import read_json


REQUIRED_ACTIVE_COVERAGE_STACK_SURFACE_CHECKS = (
    "active_frame_count_matches_positive_weights",
    "coverage_max_within_active_frame_count",
    "coverage_positive_pixels_match_post_rejection_pixels",
    "weight_positive_pixels_match_post_rejection_pixels",
)


def _read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = read_json(path)
    return payload if isinstance(payload, dict) else {}


def _surface_output_state(
    output: dict[str, Any],
    *,
    index: int,
    required_checks: tuple[str, ...],
) -> dict[str, Any]:
    contract = output.get("stack_engine_surface_contract")
    if not isinstance(contract, dict):
        return {
            "index": index,
            "filter": output.get("filter"),
            "applicable": True,
            "contract_present": False,
            "contract_passed": False,
            "status": "missing_stack_engine_surface_contract",
            "required_checks": [],
            "missing_required_checks": list(required_checks),
            "failed_required_checks": list(required_checks),
            "passed": False,
        }

    stack_result = contract.get("stack_result") if isinstance(contract.get("stack_result"), dict) else {}
    maps = stack_result.get("maps") if isinstance(stack_result.get("maps"), list) else []
    maps_by_name = {
        str(item.get("map")): item
        for item in maps
        if isinstance(item, dict) and item.get("map") is not None
    }
    coverage_row = maps_by_name.get("coverage") or {}
    weight_row = maps_by_name.get("weight") or {}
    coverage_supported = bool(coverage_row.get("present") or coverage_row.get("required"))
    weight_supported = bool(weight_row.get("present") or weight_row.get("required"))
    applicable = bool(coverage_supported and weight_supported)
    if not applicable:
        return {
            "index": index,
            "filter": output.get("filter"),
            "applicable": False,
            "contract_present": True,
            "contract_type": contract.get("contract_type"),
            "contract_status": contract.get("status"),
            "contract_passed": contract.get("passed") is True,
            "status": "not_applicable_no_coverage_weight_surface",
            "map_support": {
                "coverage_present": coverage_row.get("present"),
                "coverage_required": coverage_row.get("required"),
                "weight_present": weight_row.get("present"),
                "weight_required": weight_row.get("required"),
            },
            "required_checks": [],
            "missing_required_checks": [],
            "failed_required_checks": [],
            "passed": True,
        }

    checks = contract.get("checks") if isinstance(contract.get("checks"), list) else []
    by_name = {
        str(item.get("name")): item
        for item in checks
        if isinstance(item, dict) and item.get("name") is not None
    }
    required_rows: list[dict[str, Any]] = []
    missing: list[str] = []
    failed: list[str] = []
    for name in required_checks:
        row = by_name.get(name)
        passed = bool(row and row.get("passed") is True)
        if row is None:
            missing.append(name)
        if not passed:
            failed.append(name)
        required_rows.append(
            {
                "name": name,
                "present": row is not None,
                "passed": passed,
                "evidence": {} if row is None else row.get("evidence") or row.get("details") or {},
            }
        )

    contract_passed = contract.get("passed") is True
    return {
        "index": index,
        "filter": output.get("filter"),
        "applicable": True,
        "contract_present": True,
        "contract_type": contract.get("contract_type"),
        "contract_status": contract.get("status"),
        "contract_passed": contract_passed,
        "required_checks": required_rows,
        "missing_required_checks": missing,
        "failed_required_checks": failed,
        "passed": bool(contract_passed and not failed),
    }


def build_resident_active_coverage_contract_state(
    run: str | Path,
    *,
    required_checks: tuple[str, ...] = REQUIRED_ACTIVE_COVERAGE_STACK_SURFACE_CHECKS,
) -> dict[str, Any]:
    run_root = Path(run)
    path = run_root / "integration_results.json"
    payload = _read_json_if_exists(path)
    outputs = payload.get("outputs") if isinstance(payload.get("outputs"), list) else []
    output_rows = [
        _surface_output_state(output, index=index, required_checks=required_checks)
        for index, output in enumerate(outputs)
        if isinstance(output, dict)
    ]
    failed_outputs = [row for row in output_rows if not row["passed"]]
    passed = bool(path.exists() and output_rows and not failed_outputs)
    return {
        "path": str(path),
        "exists": path.exists(),
        "required_checks": list(required_checks),
        "output_count": len(output_rows),
        "failed_output_count": len(failed_outputs),
        "outputs": output_rows,
        "passed": passed,
        "status": "passed" if passed else "failed",
    }
