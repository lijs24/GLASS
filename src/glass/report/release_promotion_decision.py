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


def build_release_promotion_decision(
    *,
    acceptance_audit: str | Path,
    stack_engine_contract: str | Path | None = None,
    pipeline_contract: str | Path | None = None,
    runtime_compare: str | Path | None = None,
    repeat_preflight: str | Path | None = None,
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
    speedup_summary = acceptance.get("speedup_summary") if isinstance(acceptance.get("speedup_summary"), dict) else {}
    speedup = _number(speedup_summary.get("speedup_vs_wbpp"))
    required_speedup = float(min_speedup if min_speedup is not None else speedup_summary.get("min_speedup") or 2.0)
    pipeline_release_status = _release_evidence_status(acceptance, "pipeline_contract")
    stack_release_status = _release_evidence_status(acceptance, "stack_engine_default_promotion")
    runtime_ready, runtime_evidence = _runtime_compare_ready(
        runtime,
        min_runtime_runs=min_runtime_runs,
        max_elapsed_ratio_vs_best=max_elapsed_ratio_vs_best,
        ignore_warmup_runs=ignore_warmup_runs,
    )
    preflight_evidence = _preflight_evidence(preflight)

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
    release_blocking_names = {
        "acceptance_audit_passed",
        "speedup_threshold",
        "pipeline_release_evidence_passed",
        "stack_engine_release_evidence_passed",
        "stack_engine_default_ready",
        "stack_engine_scope_all",
    }
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
        },
        "speedup": {"actual": speedup, "required_min": required_speedup},
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
