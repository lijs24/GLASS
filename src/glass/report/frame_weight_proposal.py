from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from glass.io.json_io import read_json, write_json
from glass.models import now_iso
from glass.report.compare_tile_attribution import _float_or_none


def _summary_mean(summary: dict[str, Any], key: str) -> float | None:
    value = summary.get(key)
    if not isinstance(value, dict):
        return None
    return _float_or_none(value.get("mean"))


def _clip_multiplier(value: float, *, min_multiplier: float, max_multiplier: float) -> float:
    return float(np.clip(float(value), float(min_multiplier), float(max_multiplier)))


def build_frame_weight_proposal(
    integration_audit: str | Path,
    *,
    method: str = "control_ratio",
    min_multiplier: float = 0.05,
    max_multiplier: float = 1.0,
    target_group: str = "focus",
    reason: str | None = None,
) -> dict[str, Any]:
    if method != "control_ratio":
        raise ValueError("frame weight proposal method must be control_ratio")
    if target_group != "focus":
        raise ValueError("frame weight proposal target_group must be focus")
    if min_multiplier < 0.0 or min_multiplier > 1.0:
        raise ValueError("min_multiplier must be in [0, 1]")
    if max_multiplier < 0.0 or max_multiplier > 1.0 or max_multiplier < min_multiplier:
        raise ValueError("max_multiplier must be in [0, 1] and >= min_multiplier")
    audit = read_json(integration_audit)
    focus_ids = [str(item) for item in audit.get("focus_ids", [])]
    if not focus_ids:
        raise ValueError("integration audit has no focus_ids")
    focus_summary = audit.get("focus_summary") if isinstance(audit.get("focus_summary"), dict) else {}
    control_summary = audit.get("control_summary") if isinstance(audit.get("control_summary"), dict) else {}
    focus_contribution = _summary_mean(focus_summary, "tile_normalized_delta_contribution_sum")
    control_contribution = _summary_mean(control_summary, "tile_normalized_delta_contribution_sum")
    if focus_contribution is None or control_contribution is None:
        raise ValueError("integration audit is missing focus/control contribution summary means")
    if focus_contribution <= 0.0:
        multiplier = 1.0
        status = "no_positive_focus_contribution"
    else:
        multiplier = _clip_multiplier(
            max(0.0, control_contribution) / focus_contribution,
            min_multiplier=float(min_multiplier),
            max_multiplier=float(max_multiplier),
        )
        status = "proposed" if multiplier < 1.0 else "no_downweight"
    proposal_reason = reason or (
        "localized contribution control-ratio proposal from compare-tile-integration audit"
    )
    rows = [
        {
            "frame_id": frame_id,
            "multiplier": multiplier,
            "target_group": target_group,
            "reason": proposal_reason,
            "source_audit": str(integration_audit),
            "method": method,
            "status": status,
        }
        for frame_id in focus_ids
    ]
    return {
        "schema_version": 1,
        "artifact_type": "frame_weight_proposal",
        "created_at": now_iso(),
        "source_integration_audit": str(integration_audit),
        "method": method,
        "target_group": target_group,
        "status": status,
        "min_multiplier": float(min_multiplier),
        "max_multiplier": float(max_multiplier),
        "focus_contribution_mean": float(focus_contribution),
        "control_contribution_mean": float(control_contribution),
        "proposed_multiplier": float(multiplier),
        "focus_ids": focus_ids,
        "control_ids": [str(item) for item in audit.get("control_ids", [])],
        "frame_multipliers": rows,
        "limitations": [
            "This proposal is an explicit experiment artifact, not a default weighting policy.",
            "It is derived from localized diagnostic contribution summaries and must be benchmarked before promotion.",
        ],
    }


def write_frame_weight_proposal(
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
    lines = [
        "# Frame Weight Proposal",
        "",
        f"- Source audit: `{payload.get('source_integration_audit')}`",
        f"- Method: `{payload.get('method')}`",
        f"- Target group: `{payload.get('target_group')}`",
        f"- Status: `{payload.get('status')}`",
        f"- Focus contribution mean: `{payload.get('focus_contribution_mean')}`",
        f"- Control contribution mean: `{payload.get('control_contribution_mean')}`",
        f"- Proposed multiplier: `{payload.get('proposed_multiplier')}`",
        "",
        "| frame | multiplier | reason |",
        "| --- | ---: | --- |",
    ]
    for row in payload.get("frame_multipliers", []):
        if not isinstance(row, dict):
            continue
        lines.append(f"| {row.get('frame_id')} | {row.get('multiplier')} | {row.get('reason')} |")
    lines.extend(["", "## Limitations", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
