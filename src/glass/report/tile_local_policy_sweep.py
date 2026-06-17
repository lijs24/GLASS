from __future__ import annotations

from pathlib import Path
from typing import Any

from glass.io.json_io import read_json, write_json
from glass.models import now_iso


def _load_decision(path: str | Path) -> dict[str, Any]:
    payload = read_json(path)
    if not isinstance(payload, dict) or payload.get("artifact_type") != "tile_local_policy_decision":
        raise ValueError(f"expected tile_local_policy_decision artifact: {path}")
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    candidates = payload.get("candidates") if isinstance(payload.get("candidates"), list) else []
    top_candidate = candidates[0] if candidates and isinstance(candidates[0], dict) else {}
    return {
        "path": str(path),
        "accepted": bool(summary.get("accepted")),
        "status": summary.get("status"),
        "recommendation": summary.get("recommendation"),
        "top_score": float(summary.get("top_score") or 0.0),
        "top_verification": summary.get("top_verification"),
        "failed_reasons": summary.get("failed_reasons") or [],
        "tile_count": top_candidate.get("tile_count"),
        "signed_mean_improved_fraction": top_candidate.get("signed_mean_improved_fraction"),
        "rms_improved_fraction": top_candidate.get("rms_improved_fraction"),
        "mean_abs_improved_fraction": top_candidate.get("mean_abs_improved_fraction"),
        "mean_abs_delta": top_candidate.get("mean_abs_delta"),
        "mean_rms_delta": top_candidate.get("mean_rms_delta"),
        "verification": top_candidate.get("verification"),
        "replay": top_candidate.get("replay"),
        "candidate": top_candidate.get("candidate"),
    }


def build_tile_local_policy_sweep(
    decisions: list[str | Path],
) -> dict[str, Any]:
    if not decisions:
        raise ValueError("at least one policy decision artifact is required")
    rows = [_load_decision(path) for path in decisions]
    rows.sort(key=lambda row: (bool(row.get("accepted")), float(row.get("top_score") or 0.0)), reverse=True)
    accepted = [row for row in rows if row.get("accepted")]
    top = rows[0]
    return {
        "schema_version": 1,
        "artifact_type": "tile_local_policy_sweep_summary",
        "created_at": now_iso(),
        "summary": {
            "decision_count": len(rows),
            "accepted_decision_count": len(accepted),
            "rejected_decision_count": len(rows) - len(accepted),
            "top_decision": top.get("path"),
            "top_score": top.get("top_score"),
            "top_tile_count": top.get("tile_count"),
            "status": "accepted_candidate_available" if accepted else "no_accepted_candidate",
            "recommendation": "run_broader_measured_sweep" if accepted else "hold_tile_local_policy",
        },
        "decisions": rows,
        "limitations": [
            "This sweep summary ranks measured policy-decision artifacts only.",
            "It does not run new image processing and does not enable tile-local apply by default.",
        ],
    }


def write_tile_local_policy_sweep(
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
        "# Tile-Local Policy Sweep Summary",
        "",
        f"- Status: `{summary.get('status')}`",
        f"- Recommendation: `{summary.get('recommendation')}`",
        f"- Accepted decisions: `{summary.get('accepted_decision_count')}` / `{summary.get('decision_count')}`",
        f"- Top decision: `{summary.get('top_decision')}`",
        f"- Top score: `{summary.get('top_score')}`",
        "",
        "| rank | accepted | score | tiles | signed fraction | rms fraction | mean abs delta | rms delta |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for index, row in enumerate(payload.get("decisions") or [], start=1):
        if not isinstance(row, dict):
            continue
        lines.append(
            "| {rank} | {accepted} | {score} | {tiles} | {signed} | {rms} | {mean_abs} | {rms_delta} |".format(
                rank=index,
                accepted=row.get("accepted"),
                score=row.get("top_score"),
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
