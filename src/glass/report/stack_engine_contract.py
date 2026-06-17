from __future__ import annotations

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


def _result_contract_passed(provenance: Any) -> bool:
    if not isinstance(provenance, dict):
        return False
    contract = provenance.get("result_contract")
    return isinstance(contract, dict) and bool(contract.get("passed"))


def _master_record(name: str, payload: dict[str, Any], run_root: Path) -> dict[str, Any]:
    path_value = payload.get("path")
    path = Path(str(path_value)) if path_value else None
    exists = False
    if path is not None:
        exists = path.exists() if path.is_absolute() else (run_root / path).exists()
    provenance = payload.get("stack_engine_dq_provenance")
    summary = payload.get("dq_provenance_summary")
    return {
        "name": name,
        "type": payload.get("type"),
        "path": path_value,
        "path_exists": exists,
        "tile_stack_mode": payload.get("tile_stack_mode"),
        "stack_engine_enabled": bool(payload.get("stack_engine_enabled")),
        "fallback_reason": payload.get("stack_engine_fallback_reason"),
        "has_dq_provenance": isinstance(provenance, dict),
        "input_samples": provenance.get("input_samples") if isinstance(provenance, dict) else None,
        "result_contract_passed": _result_contract_passed(provenance),
        "summary_source_schema": summary.get("source_schema") if isinstance(summary, dict) else None,
        "summary_engine": summary.get("engine") if isinstance(summary, dict) else None,
        "summary_stage": summary.get("stage") if isinstance(summary, dict) else None,
        "contract_ok": (
            bool(payload.get("stack_engine_enabled"))
            and str(payload.get("tile_stack_mode") or "").startswith("stack_engine_cpu")
            and not payload.get("stack_engine_fallback_reason")
            and isinstance(provenance, dict)
            and _positive_int(provenance.get("input_samples"))
            and _result_contract_passed(provenance)
            and _summary_is_stack_engine(summary, stage="master_calibration")
        ),
    }


def _integration_record(index: int, payload: dict[str, Any], expected_engine: str) -> dict[str, Any]:
    provenance = payload.get("stack_engine_dq_provenance")
    summary = payload.get("dq_provenance_summary")
    stack_engine_ok = (
        bool(payload.get("stack_engine_enabled"))
        and payload.get("tile_stack_mode") == "stack_engine_cpu"
        and isinstance(provenance, dict)
        and _positive_int(provenance.get("input_samples"))
        and _result_contract_passed(provenance)
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
        "result_contract_passed": _result_contract_passed(provenance),
        "summary_source_schema": summary.get("source_schema") if isinstance(summary, dict) else None,
        "summary_engine": summary.get("engine") if isinstance(summary, dict) else None,
        "summary_stage": summary.get("stage") if isinstance(summary, dict) else None,
        "expected_engine": expected_engine,
        "contract_ok": contract_ok,
    }


def build_stack_engine_contract_audit(
    run_dir: str | Path,
    *,
    scope: str = "all",
    expected_integration_engine: str = "stack_engine_cpu",
) -> dict[str, Any]:
    run_root = Path(run_dir)
    calibration_path = run_root / "calibration_artifacts.json"
    integration_path = run_root / "integration_results.json"
    calibration = _load_json_object(calibration_path)
    integration = _load_json_object(integration_path)
    checks: list[dict[str, Any]] = []

    include_calibration = scope in {"all", "calibration"}
    include_integration = scope in {"all", "integration"}
    masters: list[dict[str, Any]] = []
    integration_records: list[dict[str, Any]] = []

    if include_calibration:
        master_payloads = calibration.get("masters") if isinstance(calibration.get("masters"), dict) else {}
        masters = [_master_record(str(name), payload, run_root) for name, payload in master_payloads.items()]
        checks.extend(
            [
                _check(
                    "calibration_artifact_exists",
                    calibration_path.exists(),
                    {"path": str(calibration_path)},
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
            ]
        )

    if include_integration:
        outputs = integration.get("outputs") if isinstance(integration.get("outputs"), list) else []
        integration_records = [
            _integration_record(index, payload, expected_integration_engine)
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

    passed = all(item["passed"] for item in checks)
    return {
        "schema_version": 1,
        "audit_type": "stack_engine_default_contract",
        "created_at": now_iso(),
        "run_dir": str(run_root),
        "scope": scope,
        "expected_integration_engine": expected_integration_engine,
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
    }


def write_stack_engine_contract_markdown(path: str | Path, audit: dict[str, Any]) -> None:
    lines = [
        "# GLASS StackEngine Default Contract Audit",
        "",
        f"- Status: {audit['status']}",
        f"- Run: `{audit['run_dir']}`",
        f"- Scope: `{audit['scope']}`",
        f"- Expected integration engine: `{audit['expected_integration_engine']}`",
        "",
        "## Checks",
        "",
    ]
    for item in audit.get("checks") or []:
        marker = "PASS" if item.get("passed") else "FAIL"
        lines.append(f"- {marker}: `{item.get('name')}` - {item.get('evidence')}")
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
