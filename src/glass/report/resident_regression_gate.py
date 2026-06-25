from __future__ import annotations

from pathlib import Path
from typing import Any

from glass.io.json_io import read_json, write_json
from glass.models import now_iso
from glass.report.resident_determinism import build_resident_determinism_audit
from glass.report.resident_runtime_compare import build_resident_runtime_compare


def _json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = read_json(path)
    return payload if isinstance(payload, dict) else {}


def _check(name: str, passed: bool, evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "evidence": evidence or {}}


def _payload_passed(payload: dict[str, Any]) -> bool:
    if payload.get("passed") is True:
        return True
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    if summary.get("passed") is True:
        return True
    return str(payload.get("status") or "").lower() == "passed"


def _contract_check(run: Path, filename: str, name: str, *, required: bool) -> dict[str, Any]:
    path = run / filename
    payload = _json_if_exists(path)
    exists = bool(payload)
    passed = _payload_passed(payload)
    return _check(
        name,
        (not required and not exists) or (exists and passed),
        {
            "path": str(path),
            "required": required,
            "exists": exists,
            "payload_passed": passed if exists else None,
            "status": payload.get("status"),
        },
    )


def _frame_mask_summary(run: Path) -> dict[str, Any]:
    payload = _json_if_exists(run / "resident_frame_masks.json")
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    return summary if isinstance(summary, dict) else {}


def _number(value: Any) -> float | None:
    try:
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None


def build_resident_regression_gate(
    baseline_run: str | Path,
    candidate_run: str | Path,
    *,
    max_elapsed_ratio: float = 1.15,
    min_active_frame_count: int | None = None,
    max_masked_frame_count: int | None = None,
    require_pipeline_contract: bool = True,
    require_stack_engine_contract: bool = True,
    require_resident_result_contract: bool = True,
    require_resident_frame_masks: bool = True,
    require_dq_pixel_closure: bool = True,
    require_resident_dq_lifecycle: bool = True,
    require_resident_source_dq_execution: bool = True,
    require_resident_master_cache: bool = True,
) -> dict[str, Any]:
    baseline = Path(baseline_run)
    candidate = Path(candidate_run)
    determinism = build_resident_determinism_audit(baseline, candidate)
    runtime = build_resident_runtime_compare(
        [("baseline", baseline), ("candidate", candidate)],
        baseline_label="baseline",
    )
    runtime_comparison = (runtime.get("comparisons") or [{}])[0]
    elapsed_ratio = _number(runtime_comparison.get("elapsed_ratio"))
    frame_mask = _frame_mask_summary(candidate)
    active_count = frame_mask.get("active_frame_count")
    masked_count = frame_mask.get("masked_frame_count")

    checks = [
        _check("baseline_run_exists", baseline.exists(), {"path": str(baseline)}),
        _check("candidate_run_exists", candidate.exists(), {"path": str(candidate)}),
        _check(
            "resident_determinism_passed",
            determinism.get("summary", {}).get("passed") is True,
            {
                "artifact_difference_count": determinism.get("summary", {}).get("artifact_difference_count"),
                "frame_signature_difference_count": determinism.get("summary", {}).get(
                    "frame_signature_difference_count"
                ),
                "registration_difference_count": determinism.get("summary", {}).get("registration_difference_count"),
                "frame_accounting_difference_count": determinism.get("summary", {}).get(
                    "frame_accounting_difference_count"
                ),
                "output_difference_count": determinism.get("summary", {}).get("output_difference_count"),
            },
        ),
        _check(
            "runtime_within_threshold",
            elapsed_ratio is not None and elapsed_ratio <= max_elapsed_ratio,
            {
                "elapsed_ratio": elapsed_ratio,
                "max_elapsed_ratio": max_elapsed_ratio,
                "elapsed_delta_s": runtime_comparison.get("elapsed_delta_s"),
            },
        ),
        _contract_check(
            candidate,
            "pipeline_contract.json",
            "candidate_pipeline_contract_passed",
            required=require_pipeline_contract,
        ),
        _contract_check(
            candidate,
            "stack_engine_contract.json",
            "candidate_stack_engine_contract_passed",
            required=require_stack_engine_contract,
        ),
        _contract_check(
            candidate,
            "resident_result_contract.json",
            "candidate_resident_result_contract_passed",
            required=require_resident_result_contract,
        ),
        _contract_check(
            candidate,
            "resident_frame_masks.json",
            "candidate_resident_frame_masks_passed",
            required=require_resident_frame_masks,
        ),
        _contract_check(
            candidate,
            "resident_dq_pixel_closure.json",
            "candidate_dq_pixel_closure_passed",
            required=require_dq_pixel_closure,
        ),
        _contract_check(
            candidate,
            "resident_dq_lifecycle.json",
            "candidate_resident_dq_lifecycle_passed",
            required=require_resident_dq_lifecycle,
        ),
        _contract_check(
            candidate,
            "resident_source_dq_execution.json",
            "candidate_resident_source_dq_execution_passed",
            required=require_resident_source_dq_execution,
        ),
        _contract_check(
            candidate,
            "resident_master_cache.json",
            "candidate_resident_master_cache_passed",
            required=require_resident_master_cache,
        ),
    ]
    if min_active_frame_count is not None:
        checks.append(
            _check(
                "candidate_active_frame_count_at_least_min",
                isinstance(active_count, int) and active_count >= min_active_frame_count,
                {"active_frame_count": active_count, "min_active_frame_count": min_active_frame_count},
            )
        )
    if max_masked_frame_count is not None:
        checks.append(
            _check(
                "candidate_masked_frame_count_at_most_max",
                isinstance(masked_count, int) and masked_count <= max_masked_frame_count,
                {"masked_frame_count": masked_count, "max_masked_frame_count": max_masked_frame_count},
            )
        )

    failed = [item["name"] for item in checks if not item["passed"]]
    passed = not failed
    return {
        "schema_version": 1,
        "artifact_type": "resident_regression_gate",
        "created_at": now_iso(),
        "baseline_run": str(baseline),
        "candidate_run": str(candidate),
        "passed": passed,
        "status": "passed" if passed else "failed",
        "failed_checks": failed,
        "checks": checks,
        "thresholds": {
            "max_elapsed_ratio": max_elapsed_ratio,
            "min_active_frame_count": min_active_frame_count,
            "max_masked_frame_count": max_masked_frame_count,
            "require_pipeline_contract": require_pipeline_contract,
            "require_stack_engine_contract": require_stack_engine_contract,
            "require_resident_result_contract": require_resident_result_contract,
            "require_resident_frame_masks": require_resident_frame_masks,
            "require_dq_pixel_closure": require_dq_pixel_closure,
            "require_resident_dq_lifecycle": require_resident_dq_lifecycle,
            "require_resident_source_dq_execution": require_resident_source_dq_execution,
            "require_resident_master_cache": require_resident_master_cache,
        },
        "determinism_summary": determinism.get("summary", {}),
        "runtime_summary": runtime.get("summary", {}),
        "runtime_comparison": runtime_comparison,
        "candidate_frame_mask_summary": frame_mask,
    }


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Resident Regression Gate",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Baseline: `{payload.get('baseline_run')}`",
        f"- Candidate: `{payload.get('candidate_run')}`",
        f"- Failed checks: `{payload.get('failed_checks')}`",
        "",
        "## Checks",
        "",
    ]
    for check in payload.get("checks") or []:
        lines.append(f"- `{check.get('name')}`: {'PASS' if check.get('passed') else 'FAIL'}")
    lines.extend(
        [
            "",
            "## Runtime",
            "",
            f"- Candidate/baseline ratio: `{(payload.get('runtime_comparison') or {}).get('elapsed_ratio')}`",
            f"- Max allowed ratio: `{(payload.get('thresholds') or {}).get('max_elapsed_ratio')}`",
            "",
        ]
    )
    return "\n".join(lines)


def write_resident_regression_gate(
    out: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(out, payload)
    if markdown is not None:
        Path(markdown).write_text(_markdown(payload), encoding="utf-8")
