from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from glass.io.json_io import read_json, write_json
from glass.models import now_iso
from glass.report.resident_active_coverage_contract import (
    build_resident_active_coverage_contract_state,
)
from glass.report.resident_runtime_compare import build_resident_runtime_compare


TRACKED_INTEGRATION_PATTERNS = (
    "resident_master_*.fits",
    "resident_weight_map_*.fits",
    "resident_coverage_map_*.fits",
    "resident_low_rejection_map_*.fits",
    "resident_high_rejection_map_*.fits",
    "resident_dq_map_*.fits",
)

DEFAULT_COMPONENT_RATIO_BUDGETS = {
    "light_read_upload_calibrate": 1.05,
    "resident_registration_warp": 1.50,
    "resident_local_normalization": 1.50,
    "resident_integration": 1.25,
    "output_write": 2.00,
}


def _number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = read_json(path)
    return payload if isinstance(payload, dict) else {}


def _first_resident_artifact(run: Path) -> dict[str, Any]:
    payload = _read_json_if_exists(run / "resident_artifacts.json")
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        return {}
    first = artifacts[0]
    return first if isinstance(first, dict) else {}


def _component_rows(run: Path) -> list[dict[str, Any]]:
    payload = _read_json_if_exists(run / "resident_component_timing.json")
    rows = payload.get("components")
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def _component_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    normalized: list[dict[str, Any]] = []
    for row in rows:
        elapsed = _number(row.get("elapsed_s"))
        normalized.append(
            {
                "component": row.get("component"),
                "elapsed_s": elapsed,
                "status": row.get("status"),
                "required": bool(row.get("required")),
            }
        )
    ranked = sorted(
        normalized,
        key=lambda row: float("-inf") if row.get("elapsed_s") is None else float(row["elapsed_s"]),
        reverse=True,
    )
    return {
        "components": normalized,
        "ranked_components": ranked,
        "largest_component": ranked[0] if ranked else None,
    }


def _frame_summary_from_contracts(run: Path) -> dict[str, Any]:
    for name in (
        "resident_registration_runtime_contract",
        "resident_result_contract",
        "pipeline_contract",
    ):
        payload = _read_json_if_exists(run / f"{name}.json")
        summary = payload.get("summary")
        if not isinstance(summary, dict):
            continue
        active = summary.get("active_frame_count") or summary.get("active_frames")
        frame_count = summary.get("frame_count") or summary.get("input_light_frames")
        masked = summary.get("masked_frame_count") or summary.get("masked_frames")
        if active is None:
            continue
        if frame_count is None and masked is not None:
            frame_count = int(active) + int(masked)
        if masked is None and frame_count is not None:
            masked = max(0, int(frame_count) - int(active))
        return {
            "source": f"{name}.json",
            "frame_count": int(frame_count) if frame_count is not None else None,
            "active_frame_count": int(active),
            "masked_frame_count": int(masked) if masked is not None else None,
        }
    return {}


def _contract_status(run: Path) -> dict[str, Any]:
    contracts: dict[str, dict[str, Any]] = {}
    for name in (
        "pipeline_contract",
        "resident_result_contract",
        "stack_engine_contract",
        "local_norm_contract",
        "warp_quality_contract",
    ):
        payload = _read_json_if_exists(run / f"{name}.json")
        if payload:
            contracts[name] = {
                "present": True,
                "passed": bool(
                    payload.get("passed")
                    or payload.get("ready")
                    or payload.get("phase2_check_passed")
                    or payload.get("status") == "passed"
                ),
                "status": payload.get("status"),
            }
        else:
            contracts[name] = {"present": False, "passed": None, "status": None}
    return contracts


def _frame_index_alignment_status(run: Path) -> dict[str, Any]:
    payload = _read_json_if_exists(run / "resident_frame_masks.json")
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    alignment = summary.get("frame_index_alignment_contract")
    if not payload:
        return {
            "present": False,
            "checked": False,
            "passed": False,
            "status": "missing_resident_frame_masks",
            "path": str(run / "resident_frame_masks.json"),
        }
    if not isinstance(alignment, dict):
        return {
            "present": True,
            "checked": False,
            "passed": False,
            "status": "missing_frame_index_alignment_contract",
            "path": str(run / "resident_frame_masks.json"),
        }
    checked = bool(alignment.get("checked"))
    passed = bool(alignment.get("passed"))
    return {
        "present": True,
        "checked": checked,
        "passed": checked and passed,
        "status": "passed" if checked and passed else "failed",
        "path": str(run / "resident_frame_masks.json"),
        "weight_mismatch_frame_count": int(alignment.get("weight_mismatch_frame_count") or 0),
        "weight_missing_frame_count": int(alignment.get("weight_missing_frame_count") or 0),
        "weight_mismatch_frame_ids": alignment.get("weight_mismatch_frame_ids") or [],
        "weight_missing_frame_ids": alignment.get("weight_missing_frame_ids") or [],
    }


def _active_frame_summary(run: Path) -> dict[str, Any]:
    contract_summary = _frame_summary_from_contracts(run)
    artifact = _first_resident_artifact(run)
    source = "resident_artifacts.json"
    candidates = [
        artifact.get("dq_provenance_summary"),
        artifact.get("source_dq_summary"),
    ]
    for candidate in candidates:
        if isinstance(candidate, dict):
            active = candidate.get("active_frame_count")
            frame_count = candidate.get("frame_count") or contract_summary.get("frame_count")
            masked = candidate.get("masked_frame_count") or contract_summary.get("masked_frame_count")
            if active is not None:
                if frame_count is None and masked is not None:
                    frame_count = int(active) + int(masked)
                if masked is None and frame_count is not None:
                    masked = max(0, int(frame_count) - int(active))
                return {
                    "source": source,
                    "frame_count": int(frame_count) if frame_count is not None else None,
                    "active_frame_count": int(active),
                    "masked_frame_count": int(masked) if masked is not None else None,
                }
    weights = artifact.get("weights")
    if isinstance(weights, list):
        active = sum(1 for value in weights if _number(value) not in (None, 0.0))
        return {
            "source": source,
            "frame_count": len(weights),
            "active_frame_count": active,
            "masked_frame_count": len(weights) - active,
        }
    if contract_summary:
        return contract_summary
    return {
        "source": "unavailable",
        "frame_count": None,
        "active_frame_count": None,
        "masked_frame_count": None,
    }


def _tracked_maps(run: Path) -> dict[str, dict[str, Any]]:
    integration = run / "integration"
    maps: dict[str, dict[str, Any]] = {}
    if not integration.exists():
        return maps
    for pattern in TRACKED_INTEGRATION_PATTERNS:
        for path in sorted(integration.glob(pattern)):
            if not path.is_file():
                continue
            key = path.name
            maps[key] = {
                "path": str(path),
                "size_bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
    return maps


def _map_comparison(baseline: Path, candidate: Path) -> dict[str, Any]:
    baseline_maps = _tracked_maps(baseline)
    candidate_maps = _tracked_maps(candidate)
    candidate_pattern_counts = {
        pattern: sum(1 for name in candidate_maps if Path(name).match(pattern))
        for pattern in TRACKED_INTEGRATION_PATTERNS
    }
    candidate_missing_patterns = [
        pattern for pattern, count in candidate_pattern_counts.items() if count == 0
    ]
    all_names = sorted(set(baseline_maps) | set(candidate_maps))
    rows = []
    mismatch_count = 0
    missing_count = 0
    for name in all_names:
        b_row = baseline_maps.get(name)
        c_row = candidate_maps.get(name)
        present = b_row is not None and c_row is not None
        if not present:
            missing_count += 1
        hash_match = bool(
            present
            and b_row is not None
            and c_row is not None
            and b_row.get("sha256") == c_row.get("sha256")
            and b_row.get("size_bytes") == c_row.get("size_bytes")
        )
        if present and not hash_match:
            mismatch_count += 1
        rows.append(
            {
                "name": name,
                "baseline_present": b_row is not None,
                "candidate_present": c_row is not None,
                "size_match": bool(
                    present
                    and b_row is not None
                    and c_row is not None
                    and b_row.get("size_bytes") == c_row.get("size_bytes")
                ),
                "sha256_match": hash_match,
                "baseline": b_row,
                "candidate": c_row,
            }
        )
    compared_count = sum(1 for row in rows if row["baseline_present"] and row["candidate_present"])
    return {
        "tracked_patterns": list(TRACKED_INTEGRATION_PATTERNS),
        "baseline_map_count": len(baseline_maps),
        "candidate_map_count": len(candidate_maps),
        "candidate_pattern_counts": candidate_pattern_counts,
        "candidate_missing_patterns": candidate_missing_patterns,
        "compared_map_count": compared_count,
        "missing_map_count": missing_count,
        "mismatch_count": mismatch_count,
        "all_hashes_match": bool(rows and missing_count == 0 and mismatch_count == 0),
        "maps": rows,
    }


def _check(name: str, passed: bool, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "details": details or {}}


def _component_ratio_budget_map(
    *,
    max_component_ratio: float | None,
    component_ratio_budgets: dict[str, float] | None,
) -> dict[str, float]:
    budgets = {
        key: float(max_component_ratio)
        if max_component_ratio is not None
        else float(value)
        for key, value in DEFAULT_COMPONENT_RATIO_BUDGETS.items()
    }
    for key, value in (component_ratio_budgets or {}).items():
        budgets[str(key)] = float(value)
    invalid = {key: value for key, value in budgets.items() if value <= 0.0}
    if invalid:
        raise ValueError(f"component ratio budgets must be positive: {invalid}")
    return budgets


def _component_ratio_budget_state(
    runtime_delta: dict[str, Any],
    *,
    max_component_ratio: float | None,
    component_ratio_budgets: dict[str, float] | None,
) -> dict[str, Any]:
    budgets = _component_ratio_budget_map(
        max_component_ratio=max_component_ratio,
        component_ratio_budgets=component_ratio_budgets,
    )
    timing_delta = runtime_delta.get("timing_delta")
    timing_delta = timing_delta if isinstance(timing_delta, dict) else {}
    rows: list[dict[str, Any]] = []
    for component, budget in budgets.items():
        delta = timing_delta.get(component)
        delta = delta if isinstance(delta, dict) else {}
        ratio = _number(delta.get("ratio"))
        baseline_s = _number(delta.get("baseline_s"))
        candidate_s = _number(delta.get("candidate_s"))
        passed = ratio is not None and ratio <= float(budget)
        rows.append(
            {
                "component": component,
                "baseline_s": baseline_s,
                "candidate_s": candidate_s,
                "ratio": ratio,
                "max_ratio": float(budget),
                "passed": passed,
                "status": "passed" if passed else "failed",
            }
        )
    failed = [row for row in rows if not row["passed"]]
    present = [row for row in rows if row["ratio"] is not None]
    worst = max(
        present,
        key=lambda row: float(row["ratio"]),
        default=None,
    )
    return {
        "schema_version": 1,
        "default_budgets": DEFAULT_COMPONENT_RATIO_BUDGETS,
        "max_component_ratio": max_component_ratio,
        "component_ratio_budgets": budgets,
        "rows": rows,
        "failed_rows": failed,
        "failed_count": len(failed),
        "worst_component": worst,
        "passed": not failed,
    }


def build_phase2_mainline_ab(
    baseline_run: str | Path,
    candidate_run: str | Path,
    *,
    max_elapsed_ratio: float = 1.15,
    max_component_ratio: float | None = None,
    component_ratio_budgets: dict[str, float] | None = None,
    min_active_frame_count: int = 1,
    require_hash_match: bool = True,
) -> dict[str, Any]:
    baseline = Path(baseline_run)
    candidate = Path(candidate_run)
    runtime_compare = build_resident_runtime_compare(
        [("baseline", baseline), ("candidate", candidate)],
        baseline_label="baseline",
    )
    runtime_delta = runtime_compare.get("comparisons", [{}])[0]
    elapsed_ratio = _number(runtime_delta.get("elapsed_ratio"))
    map_comparison = _map_comparison(baseline, candidate)
    active_summary = _active_frame_summary(candidate)
    candidate_contracts = _contract_status(candidate)
    candidate_components = _component_summary(_component_rows(candidate))
    candidate_frame_index_alignment = _frame_index_alignment_status(candidate)
    candidate_active_coverage_contract = build_resident_active_coverage_contract_state(candidate)
    component_ratio_budget = _component_ratio_budget_state(
        runtime_delta,
        max_component_ratio=max_component_ratio,
        component_ratio_budgets=component_ratio_budgets,
    )

    required_contract_names = ("pipeline_contract", "resident_result_contract")
    required_contracts_pass = all(
        bool(candidate_contracts.get(name, {}).get("passed")) for name in required_contract_names
    )
    active_count = active_summary.get("active_frame_count")
    checks = [
        _check("baseline_run_exists", baseline.exists(), {"path": str(baseline)}),
        _check("candidate_run_exists", candidate.exists(), {"path": str(candidate)}),
        _check(
            "candidate_required_contracts_pass",
            required_contracts_pass,
            {
                "required": list(required_contract_names),
                "contracts": candidate_contracts,
            },
        ),
        _check(
            "elapsed_ratio_within_budget",
            elapsed_ratio is not None and elapsed_ratio <= max_elapsed_ratio,
            {"elapsed_ratio": elapsed_ratio, "max_elapsed_ratio": max_elapsed_ratio},
        ),
        _check(
            "active_frame_count_sufficient",
            active_count is not None and int(active_count) >= int(min_active_frame_count),
            {
                "active_frame_count": active_count,
                "min_active_frame_count": min_active_frame_count,
            },
        ),
        _check(
            "candidate_integration_maps_present",
            not map_comparison["candidate_missing_patterns"],
            {
                "candidate_map_count": map_comparison["candidate_map_count"],
                "required_patterns": list(TRACKED_INTEGRATION_PATTERNS),
                "missing_patterns": map_comparison["candidate_missing_patterns"],
            },
        ),
        _check(
            "candidate_frame_index_alignment_contract_pass",
            bool(candidate_frame_index_alignment.get("passed")),
            candidate_frame_index_alignment,
        ),
        _check(
            "candidate_active_coverage_stack_surface_contract",
            bool(candidate_active_coverage_contract.get("passed")),
            candidate_active_coverage_contract,
        ),
        _check(
            "component_ratios_within_budget",
            bool(component_ratio_budget.get("passed")),
            {
                "failed_count": component_ratio_budget["failed_count"],
                "failed_rows": component_ratio_budget["failed_rows"],
                "worst_component": component_ratio_budget["worst_component"],
                "budgets": component_ratio_budget["component_ratio_budgets"],
            },
        ),
    ]
    if require_hash_match:
        checks.append(
            _check(
                "tracked_integration_maps_hash_match",
                map_comparison["all_hashes_match"],
                {
                    "missing_map_count": map_comparison["missing_map_count"],
                    "mismatch_count": map_comparison["mismatch_count"],
                    "compared_map_count": map_comparison["compared_map_count"],
                },
            )
        )
    failed_checks = [item for item in checks if not item["passed"]]
    return {
        "schema_version": 1,
        "artifact_type": "phase2_mainline_ab",
        "created_at": now_iso(),
        "baseline_run": str(baseline),
        "candidate_run": str(candidate),
        "max_elapsed_ratio": max_elapsed_ratio,
        "max_component_ratio": max_component_ratio,
        "component_ratio_budgets": component_ratio_budget["component_ratio_budgets"],
        "min_active_frame_count": min_active_frame_count,
        "require_hash_match": require_hash_match,
        "runtime_compare": runtime_compare,
        "runtime_delta": runtime_delta,
        "component_ratio_budget": component_ratio_budget,
        "candidate_components": candidate_components,
        "candidate_contracts": candidate_contracts,
        "candidate_frame_index_alignment": candidate_frame_index_alignment,
        "candidate_active_coverage_contract": candidate_active_coverage_contract,
        "candidate_active_frames": active_summary,
        "map_comparison": map_comparison,
        "checks": checks,
        "failed_checks": failed_checks,
        "failed_check_count": len(failed_checks),
        "passed": not failed_checks,
        "summary": {
            "status": "passed" if not failed_checks else "failed",
            "elapsed_ratio": elapsed_ratio,
            "best_label": runtime_compare.get("summary", {}).get("best_label"),
            "candidate_active_frame_count": active_count,
            "candidate_masked_frame_count": active_summary.get("masked_frame_count"),
            "largest_component": candidate_components.get("largest_component"),
            "worst_component_ratio": (
                None
                if component_ratio_budget.get("worst_component") is None
                else component_ratio_budget["worst_component"].get("ratio")
            ),
            "worst_component_ratio_name": (
                None
                if component_ratio_budget.get("worst_component") is None
                else component_ratio_budget["worst_component"].get("component")
            ),
            "component_ratio_failed_count": component_ratio_budget["failed_count"],
            "frame_index_alignment_passed": candidate_frame_index_alignment.get("passed"),
            "frame_index_alignment_status": candidate_frame_index_alignment.get("status"),
            "active_coverage_contract_passed": candidate_active_coverage_contract.get("passed"),
            "active_coverage_contract_status": candidate_active_coverage_contract.get("status"),
            "hash_mismatch_count": map_comparison["mismatch_count"],
            "hash_missing_map_count": map_comparison["missing_map_count"],
        },
    }


def _markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {})
    largest = summary.get("largest_component") or {}
    lines = [
        "# Phase 2 Mainline A/B",
        "",
        f"- Status: `{summary.get('status')}`",
        f"- Baseline: `{payload.get('baseline_run')}`",
        f"- Candidate: `{payload.get('candidate_run')}`",
        f"- Elapsed ratio: `{summary.get('elapsed_ratio')}`",
        f"- Best label: `{summary.get('best_label')}`",
        f"- Candidate active/masked frames: `{summary.get('candidate_active_frame_count')}` / `{summary.get('candidate_masked_frame_count')}`",
        f"- Largest candidate component: `{largest.get('component')}` = `{largest.get('elapsed_s')}` s",
        f"- Worst component ratio: `{summary.get('worst_component_ratio_name')}` = `{summary.get('worst_component_ratio')}`",
        f"- Active/coverage contract: `{summary.get('active_coverage_contract_status')}`",
        f"- Hash mismatches/missing maps: `{summary.get('hash_mismatch_count')}` / `{summary.get('hash_missing_map_count')}`",
        "",
        "## Checks",
        "",
    ]
    for check in payload.get("checks", []):
        status = "PASS" if check.get("passed") else "FAIL"
        lines.append(f"- {status}: `{check.get('name')}`")
    lines.extend(["", "## Component Ratios", ""])
    lines.append("| component | baseline s | candidate s | ratio | max ratio | status |")
    lines.append("| --- | ---: | ---: | ---: | ---: | --- |")
    for row in payload.get("component_ratio_budget", {}).get("rows", []):
        lines.append(
            "| "
            f"{row.get('component')} | {row.get('baseline_s')} | {row.get('candidate_s')} | "
            f"{row.get('ratio')} | {row.get('max_ratio')} | {row.get('status')} |"
        )
    lines.append("")
    return "\n".join(lines)


def write_phase2_mainline_ab(
    out: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(out, payload)
    if markdown is not None:
        Path(markdown).write_text(_markdown(payload), encoding="utf-8")
