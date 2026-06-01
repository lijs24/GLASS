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


def _source_tile_signed_stats(tile: dict[str, Any]) -> dict[str, Any]:
    source = tile.get("source_top_tile")
    signed = tile.get("signed_diff_stats")
    return {
        "signed_diff_mean": _float_or_none(signed.get("mean")) if isinstance(signed, dict) else None,
        "signed_diff_rms": _float_or_none(signed.get("rms")) if isinstance(signed, dict) else None,
        "tail_signed_mean": _float_or_none(source.get("tail_signed_mean")) if isinstance(source, dict) else None,
        "tail_pixels": int(source.get("tail_pixels")) if isinstance(source, dict) and source.get("tail_pixels") is not None else None,
        "negative_tail_pixels": int(source.get("negative_tail_pixels"))
        if isinstance(source, dict) and source.get("negative_tail_pixels") is not None
        else None,
        "positive_tail_pixels": int(source.get("positive_tail_pixels"))
        if isinstance(source, dict) and source.get("positive_tail_pixels") is not None
        else None,
    }


def _proposal_multiplier(proposal: dict[str, Any]) -> float:
    direct = _float_or_none(proposal.get("proposed_multiplier"))
    if direct is not None:
        return direct
    rows = proposal.get("frame_multipliers")
    values: list[float] = []
    if isinstance(rows, dict):
        values = [float(value) for value in rows.values()]
    elif isinstance(rows, list):
        for row in rows:
            if isinstance(row, dict) and row.get("multiplier") is not None:
                values.append(float(row["multiplier"]))
    if not values:
        raise ValueError("frame-weight proposal has no proposed_multiplier or frame multipliers")
    finite = [value for value in values if np.isfinite(value)]
    if not finite:
        raise ValueError("frame-weight proposal multipliers are not finite")
    return float(np.median(np.asarray(finite, dtype=np.float64)))


def _moves_toward_reference(signed_diff: float | None, predicted_delta: float | None) -> bool | None:
    if signed_diff is None or predicted_delta is None:
        return None
    if signed_diff == 0.0 or predicted_delta == 0.0:
        return None
    return bool(float(signed_diff) * float(predicted_delta) < 0.0)


def build_frame_weight_proposal_audit(
    integration_audit: str | Path,
    proposal: str | Path,
    *,
    tile_pack: str | Path | None = None,
    glass_scale: float | None = None,
) -> dict[str, Any]:
    integration = read_json(integration_audit)
    proposal_payload = read_json(proposal)
    tile_pack_path = Path(tile_pack or integration.get("tile_pack") or "")
    tile_pack_payload = read_json(tile_pack_path) if str(tile_pack_path) else {"tiles": []}
    transform = tile_pack_payload.get("candidate_transform")
    if glass_scale is None and isinstance(transform, dict):
        glass_scale = _float_or_none(transform.get("scale"))
    if glass_scale is None:
        glass_scale = 1.0
    multiplier = _proposal_multiplier(proposal_payload)
    tile_pack_by_index = {
        int(tile.get("index")): tile
        for tile in tile_pack_payload.get("tiles", [])
        if isinstance(tile, dict) and tile.get("index") is not None
    }

    rows: list[dict[str, Any]] = []
    for tile in integration.get("tiles", []):
        if not isinstance(tile, dict):
            continue
        tile_index = int(tile.get("index", len(rows)))
        focus_summary = tile.get("focus_summary") if isinstance(tile.get("focus_summary"), dict) else {}
        focus_contribution = _summary_mean(focus_summary, "tile_normalized_delta_contribution_sum")
        predicted_delta_adu = None if focus_contribution is None else (float(multiplier) - 1.0) * focus_contribution
        predicted_delta_reference_units = (
            None if predicted_delta_adu is None else float(predicted_delta_adu) * float(glass_scale)
        )
        signed_stats = _source_tile_signed_stats(tile_pack_by_index.get(tile_index, {}))
        signed_diff_mean = signed_stats["signed_diff_mean"]
        tail_signed_mean = signed_stats["tail_signed_mean"]
        mean_toward = _moves_toward_reference(signed_diff_mean, predicted_delta_reference_units)
        tail_toward = _moves_toward_reference(tail_signed_mean, predicted_delta_reference_units)
        after_mean = (
            None
            if signed_diff_mean is None or predicted_delta_reference_units is None
            else float(signed_diff_mean) + float(predicted_delta_reference_units)
        )
        after_tail = (
            None
            if tail_signed_mean is None or predicted_delta_reference_units is None
            else float(tail_signed_mean) + float(predicted_delta_reference_units)
        )
        rows.append(
            {
                "tile_index": tile_index,
                "extent": tile.get("extent"),
                "focus_contribution_mean_adu": focus_contribution,
                "proposal_multiplier": float(multiplier),
                "predicted_master_delta_adu": predicted_delta_adu,
                "glass_scale": float(glass_scale),
                "predicted_signed_delta_reference_units": predicted_delta_reference_units,
                **signed_stats,
                "moves_mean_toward_reference": mean_toward,
                "moves_tail_toward_reference": tail_toward,
                "predicted_signed_diff_mean_after": after_mean,
                "predicted_tail_signed_mean_after": after_tail,
                "abs_signed_diff_mean_before": None if signed_diff_mean is None else abs(float(signed_diff_mean)),
                "abs_signed_diff_mean_after": None if after_mean is None else abs(float(after_mean)),
                "abs_tail_signed_mean_before": None if tail_signed_mean is None else abs(float(tail_signed_mean)),
                "abs_tail_signed_mean_after": None if after_tail is None else abs(float(after_tail)),
            }
        )

    mean_known = [row for row in rows if row["moves_mean_toward_reference"] is not None]
    tail_known = [row for row in rows if row["moves_tail_toward_reference"] is not None]
    mean_toward_count = sum(1 for row in mean_known if row["moves_mean_toward_reference"])
    tail_toward_count = sum(1 for row in tail_known if row["moves_tail_toward_reference"])
    mean_away_count = len(mean_known) - mean_toward_count
    tail_away_count = len(tail_known) - tail_toward_count
    recommendation = (
        "reject_downweight_direction"
        if mean_away_count > mean_toward_count or tail_away_count > tail_toward_count
        else "directionally_promising"
    )
    return {
        "schema_version": 1,
        "artifact_type": "frame_weight_proposal_direction_audit",
        "created_at": now_iso(),
        "integration_audit": str(integration_audit),
        "frame_weight_proposal": str(proposal),
        "tile_pack": str(tile_pack_path) if str(tile_pack_path) else None,
        "proposal_method": proposal_payload.get("method"),
        "proposal_multiplier": float(multiplier),
        "focus_ids": [str(item) for item in integration.get("focus_ids", [])],
        "control_ids": [str(item) for item in integration.get("control_ids", [])],
        "tile_count": len(rows),
        "summary": {
            "mean_direction_known_tiles": len(mean_known),
            "mean_moves_toward_reference": mean_toward_count,
            "mean_moves_away_from_reference": mean_away_count,
            "tail_direction_known_tiles": len(tail_known),
            "tail_moves_toward_reference": tail_toward_count,
            "tail_moves_away_from_reference": tail_away_count,
            "recommendation": recommendation,
        },
        "tiles": rows,
        "limitations": [
            "This is a first-order direction audit, not a full reintegration.",
            "It uses tile-level focus contribution summaries and signed residual summaries, not per-pixel proposal masks.",
        ],
    }


def write_frame_weight_proposal_audit(
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
        "# Frame Weight Proposal Direction Audit",
        "",
        f"- Integration audit: `{payload.get('integration_audit')}`",
        f"- Proposal: `{payload.get('frame_weight_proposal')}`",
        f"- Proposal multiplier: `{payload.get('proposal_multiplier')}`",
        f"- Recommendation: `{summary.get('recommendation')}`",
        f"- Mean toward/away: `{summary.get('mean_moves_toward_reference')}` / `{summary.get('mean_moves_away_from_reference')}`",
        f"- Tail toward/away: `{summary.get('tail_moves_toward_reference')}` / `{summary.get('tail_moves_away_from_reference')}`",
        "",
        "| tile | signed mean | tail signed mean | predicted delta | mean toward | tail toward |",
        "| ---: | ---: | ---: | ---: | :---: | :---: |",
    ]
    for row in payload.get("tiles", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            "| {tile} | {mean} | {tail} | {delta} | {mean_toward} | {tail_toward} |".format(
                tile=row.get("tile_index"),
                mean=row.get("signed_diff_mean"),
                tail=row.get("tail_signed_mean"),
                delta=row.get("predicted_signed_delta_reference_units"),
                mean_toward=row.get("moves_mean_toward_reference"),
                tail_toward=row.get("moves_tail_toward_reference"),
            )
        )
    lines.extend(["", "## Limitations", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
