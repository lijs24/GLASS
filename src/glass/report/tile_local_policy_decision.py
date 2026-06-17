from __future__ import annotations

from pathlib import Path
from typing import Any

from glass.io.json_io import read_json, write_json
from glass.models import now_iso


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _fraction(numerator: Any, denominator: Any) -> float | None:
    try:
        den = int(denominator)
        if den <= 0:
            return None
        return float(int(numerator or 0) / den)
    except (TypeError, ValueError):
        return None


def _load_object(path: str | Path, expected_type: str | None = None) -> dict[str, Any]:
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"JSON artifact must be an object: {path}")
    if expected_type is not None and payload.get("artifact_type") != expected_type:
        raise ValueError(f"expected {expected_type} artifact at {path}, got {payload.get('artifact_type')}")
    return payload


def _check(name: str, passed: bool, evidence: dict[str, Any], note: str = "") -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "evidence": evidence, "note": note}


def _verification_candidate(
    path: str | Path,
    *,
    min_signed_fraction: float,
    min_rms_fraction: float,
    min_mean_abs_fraction: float,
    require_aggregate_mean_abs: bool,
    require_aggregate_rms: bool,
) -> dict[str, Any]:
    payload = _load_object(path, "tile_local_apply_verification")
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    tile_count = int(summary.get("tile_count") or 0)
    signed_fraction = _fraction(summary.get("signed_mean_improved_tiles"), tile_count)
    rms_fraction = _fraction(summary.get("rms_improved_tiles"), tile_count)
    mean_abs_fraction = _fraction(summary.get("mean_abs_improved_tiles"), tile_count)
    mean_abs_delta = _float_or_none(summary.get("mean_abs_delta"))
    rms_delta = _float_or_none(summary.get("mean_rms_delta"))
    checks = [
        _check("verification_has_tiles", tile_count > 0, {"tile_count": tile_count}),
        _check(
            "signed_mean_improvement_fraction",
            signed_fraction is not None and signed_fraction >= float(min_signed_fraction),
            {"actual": signed_fraction, "required_min": float(min_signed_fraction)},
        ),
        _check(
            "rms_improvement_fraction",
            rms_fraction is not None and rms_fraction >= float(min_rms_fraction),
            {"actual": rms_fraction, "required_min": float(min_rms_fraction)},
        ),
        _check(
            "mean_abs_improvement_fraction",
            mean_abs_fraction is not None and mean_abs_fraction >= float(min_mean_abs_fraction),
            {"actual": mean_abs_fraction, "required_min": float(min_mean_abs_fraction)},
        ),
    ]
    if require_aggregate_mean_abs:
        checks.append(
            _check(
                "aggregate_mean_abs_improves",
                mean_abs_delta is not None and mean_abs_delta < 0.0,
                {"actual_delta": mean_abs_delta, "required": "< 0"},
            )
        )
    if require_aggregate_rms:
        checks.append(
            _check(
                "aggregate_rms_improves",
                rms_delta is not None and rms_delta < 0.0,
                {"actual_delta": rms_delta, "required": "< 0"},
            )
        )
    passed = all(item["passed"] for item in checks)
    score = 0.0
    score += float(signed_fraction or 0.0) * 1000.0
    score += float(rms_fraction or 0.0) * 500.0
    score += float(mean_abs_fraction or 0.0) * 100.0
    if mean_abs_delta is not None:
        score += max(0.0, -mean_abs_delta) * 1_000_000.0
    if rms_delta is not None:
        score += max(0.0, -rms_delta) * 1_000_000.0
    return {
        "verification": str(path),
        "replay": payload.get("replay"),
        "candidate": payload.get("candidate"),
        "baseline": payload.get("baseline"),
        "reference": payload.get("reference"),
        "tile_count": tile_count,
        "signed_mean_improved_fraction": signed_fraction,
        "rms_improved_fraction": rms_fraction,
        "mean_abs_improved_fraction": mean_abs_fraction,
        "mean_abs_delta": mean_abs_delta,
        "mean_rms_delta": rms_delta,
        "verification_status": summary.get("status"),
        "verification_recommendation": summary.get("recommendation"),
        "checks": checks,
        "passed": passed,
        "score": score,
    }


def _artifact_pass_check(path: str | Path | None, *, name: str, status_key: str = "status") -> dict[str, Any] | None:
    if path is None:
        return None
    payload = _load_object(path)
    status = payload.get(status_key)
    passed = payload.get("passed")
    if passed is None and isinstance(payload.get("summary"), dict):
        passed = payload["summary"].get("passed")
    if passed is None:
        passed = status == "passed"
    return _check(
        name,
        bool(passed),
        {"path": str(path), "status": status, "passed": passed},
    )


def build_tile_local_policy_decision(
    verifications: list[str | Path],
    *,
    apply_experiment: str | Path | None = None,
    acceptance_audit: str | Path | None = None,
    min_signed_fraction: float = 1.0,
    min_rms_fraction: float = 1.0,
    min_mean_abs_fraction: float = 0.0,
    require_aggregate_mean_abs: bool = True,
    require_aggregate_rms: bool = True,
) -> dict[str, Any]:
    if not verifications:
        raise ValueError("at least one verification artifact is required")
    candidates = [
        _verification_candidate(
            path,
            min_signed_fraction=min_signed_fraction,
            min_rms_fraction=min_rms_fraction,
            min_mean_abs_fraction=min_mean_abs_fraction,
            require_aggregate_mean_abs=require_aggregate_mean_abs,
            require_aggregate_rms=require_aggregate_rms,
        )
        for path in verifications
    ]
    candidates.sort(key=lambda row: (bool(row.get("passed")), float(row.get("score") or 0.0)), reverse=True)
    global_checks: list[dict[str, Any]] = []
    for maybe_check in [
        _artifact_pass_check(apply_experiment, name="apply_experiment_passed"),
        _artifact_pass_check(acceptance_audit, name="acceptance_audit_passed"),
    ]:
        if maybe_check is not None:
            global_checks.append(maybe_check)

    top = candidates[0]
    accepted = bool(top.get("passed")) and all(item["passed"] for item in global_checks)
    failed_reasons = [check["name"] for check in global_checks if not check["passed"]]
    failed_reasons.extend(
        f"top_verification:{check['name']}" for check in top.get("checks", []) if not check.get("passed")
    )
    return {
        "schema_version": 1,
        "artifact_type": "tile_local_policy_decision",
        "created_at": now_iso(),
        "summary": {
            "status": "accepted" if accepted else "rejected",
            "accepted": accepted,
            "candidate_count": len(candidates),
            "accepted_candidate_count": sum(1 for row in candidates if row.get("passed")),
            "top_verification": top.get("verification"),
            "top_score": top.get("score"),
            "failed_reasons": failed_reasons,
            "recommendation": "promote_measured_subset_to_sweep_candidate" if accepted else "hold_policy_subset",
        },
        "thresholds": {
            "min_signed_fraction": float(min_signed_fraction),
            "min_rms_fraction": float(min_rms_fraction),
            "min_mean_abs_fraction": float(min_mean_abs_fraction),
            "require_aggregate_mean_abs": bool(require_aggregate_mean_abs),
            "require_aggregate_rms": bool(require_aggregate_rms),
        },
        "apply_experiment": None if apply_experiment is None else str(apply_experiment),
        "acceptance_audit": None if acceptance_audit is None else str(acceptance_audit),
        "global_checks": global_checks,
        "candidates": candidates,
        "limitations": [
            "This decision ranks measured tile-local verification artifacts and related audits.",
            "It does not mutate pipeline outputs and does not enable tile-local apply by default.",
            "The accepted subset remains a sweep candidate until broader measured validation exists.",
        ],
    }


def write_tile_local_policy_decision(
    out: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(out, payload)
    if markdown is None:
        return
    target = Path(markdown)
    target.parent.mkdir(parents=True, exist_ok=True)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    lines = [
        "# Tile-Local Policy Decision",
        "",
        f"- Status: `{summary.get('status')}`",
        f"- Recommendation: `{summary.get('recommendation')}`",
        f"- Top verification: `{summary.get('top_verification')}`",
        f"- Top score: `{summary.get('top_score')}`",
        f"- Failed reasons: `{summary.get('failed_reasons')}`",
        "",
        "## Candidates",
        "",
        "| rank | passed | score | tiles | signed fraction | rms fraction | mean abs delta | rms delta |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for index, row in enumerate(payload.get("candidates") or [], start=1):
        if not isinstance(row, dict):
            continue
        lines.append(
            "| {rank} | {passed} | {score} | {tiles} | {signed} | {rms} | {mean_abs} | {rms_delta} |".format(
                rank=index,
                passed=row.get("passed"),
                score=row.get("score"),
                tiles=row.get("tile_count"),
                signed=row.get("signed_mean_improved_fraction"),
                rms=row.get("rms_improved_fraction"),
                mean_abs=row.get("mean_abs_delta"),
                rms_delta=row.get("mean_rms_delta"),
            )
        )
    lines.extend(["", "## Limitations", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
