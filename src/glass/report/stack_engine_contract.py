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
        family == "stack_engine_cpu"
        and bool(record.get("contract_ok"))
        and result_contract_passed
        and not fallback
    )
    if stack_engine_contract_ready:
        gap_reason = ""
    elif family == "cuda_resident_stack":
        gap_reason = "resident_cuda_surface"
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
