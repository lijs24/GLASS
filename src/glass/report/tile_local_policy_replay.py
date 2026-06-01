from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from glass.io.json_io import read_json, write_json
from glass.models import now_iso
from glass.report.compare_tile_attribution import _float_or_none, _stats


def _tile_index(payload: dict[str, Any], key: str = "index") -> int | None:
    value = payload.get(key)
    if value is None:
        return None
    return int(value)


def _tiles_by_index(payload: dict[str, Any], *, key: str = "index") -> dict[int, dict[str, Any]]:
    result: dict[int, dict[str, Any]] = {}
    tiles = payload.get("tiles")
    if not isinstance(tiles, list):
        return result
    for tile in tiles:
        if not isinstance(tile, dict):
            continue
        index = _tile_index(tile, key=key)
        if index is not None:
            result[index] = tile
    return result


def _group_ids(contribution: dict[str, Any], target_group: str) -> list[str]:
    key = f"{target_group}_ids"
    values = contribution.get(key)
    if not isinstance(values, list):
        return []
    return [str(value) for value in values]


def _finite(values: list[float | None]) -> np.ndarray:
    return np.asarray([value for value in values if value is not None], dtype=np.float64)


def _sum_finite(values: list[float | None]) -> float | None:
    finite = _finite(values)
    if finite.size == 0:
        return None
    return float(np.sum(finite))


def _residual_reduction_fraction(before: float | None, after: float | None) -> float | None:
    if before is None or after is None:
        return None
    before_abs = abs(float(before))
    if before_abs <= 0.0:
        return None
    return float((before_abs - abs(float(after))) / before_abs)


def _selected_frame_rows(
    contribution_tile: dict[str, Any],
    *,
    frame_ids: set[str],
    multiplier: float,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    frames = contribution_tile.get("top_frames")
    if not isinstance(frames, list):
        return rows
    for frame in frames:
        if not isinstance(frame, dict):
            continue
        frame_id = str(frame.get("frame_id"))
        if frame_id not in frame_ids:
            continue
        original = _float_or_none(frame.get("normalized_delta_contribution_mean"))
        accepted_weighted_delta = _float_or_none(frame.get("accepted_weighted_delta_mean"))
        proposed = None if original is None else float(original) * float(multiplier)
        delta = None if original is None or proposed is None else float(proposed - original)
        rows.append(
            {
                "frame_id": frame_id,
                "tile_index": frame.get("tile_index", contribution_tile.get("index")),
                "integration_weight": _float_or_none(frame.get("integration_weight")),
                "accepted_pixels": int(frame.get("accepted_pixels") or 0),
                "rejected_pixels": int(frame.get("rejected_pixels") or 0),
                "accepted_fraction": _float_or_none(frame.get("accepted_fraction")),
                "accepted_weighted_delta_mean": accepted_weighted_delta,
                "original_normalized_delta_contribution_mean": original,
                "multiplier": float(multiplier),
                "proposed_normalized_delta_contribution_mean": proposed,
                "delta_normalized_delta_contribution_mean": delta,
            }
        )
    rows.sort(
        key=lambda row: abs(float(row.get("delta_normalized_delta_contribution_mean") or 0.0)),
        reverse=True,
    )
    return rows


def _tile_replay_row(
    contribution_tile: dict[str, Any],
    proposal_tile: dict[str, Any],
    *,
    frame_ids: set[str],
    target_group: str,
) -> dict[str, Any]:
    multiplier = _float_or_none(proposal_tile.get("multiplier"))
    multiplier = 1.0 if multiplier is None else multiplier
    frame_rows = _selected_frame_rows(contribution_tile, frame_ids=frame_ids, multiplier=multiplier)
    frame_original = _sum_finite(
        [_float_or_none(row.get("original_normalized_delta_contribution_mean")) for row in frame_rows]
    )
    frame_proposed = _sum_finite(
        [_float_or_none(row.get("proposed_normalized_delta_contribution_mean")) for row in frame_rows]
    )
    frame_delta = None if frame_original is None or frame_proposed is None else float(frame_proposed - frame_original)

    original_adu = _float_or_none(proposal_tile.get("group_contribution_adu"))
    proposed_adu = None if original_adu is None else float(original_adu) * float(multiplier)
    delta_adu = None if original_adu is None else (float(multiplier) - 1.0) * float(original_adu)
    original_reference = _float_or_none(proposal_tile.get("group_contribution_reference_units"))
    delta_reference = _float_or_none(proposal_tile.get("predicted_delta_reference_units"))
    proposed_reference = None if original_reference is None or delta_reference is None else original_reference + delta_reference
    before = _float_or_none(proposal_tile.get("signed_residual_reference_units"))
    after = _float_or_none(proposal_tile.get("predicted_signed_residual_after"))

    row = {
        "tile_index": _tile_index(proposal_tile, key="tile_index"),
        "extent": proposal_tile.get("extent") or contribution_tile.get("extent"),
        "target_group": target_group,
        "action": proposal_tile.get("action"),
        "multiplier": float(multiplier),
        "clamped": bool(proposal_tile.get("clamped")),
        "target_frame_count": len(frame_ids),
        "selected_frame_rows": frame_rows,
        "selected_frame_row_count": len(frame_rows),
        "canonical_original_contribution_adu": original_adu,
        "canonical_proposed_contribution_adu": proposed_adu,
        "canonical_delta_contribution_adu": delta_adu,
        "canonical_original_contribution_reference_units": original_reference,
        "canonical_proposed_contribution_reference_units": proposed_reference,
        "canonical_delta_contribution_reference_units": delta_reference,
        "per_frame_original_contribution_sum": frame_original,
        "per_frame_proposed_contribution_sum": frame_proposed,
        "per_frame_delta_contribution_sum": frame_delta,
        "per_frame_delta_minus_canonical_delta_adu": None
        if frame_delta is None or delta_adu is None
        else float(frame_delta - delta_adu),
        "signed_residual_reference_units_before": before,
        "signed_residual_reference_units_after": after,
        "moves_toward_reference": proposal_tile.get("moves_toward_reference"),
        "residual_reduction_fraction": _residual_reduction_fraction(before, after),
    }
    return row


def build_tile_local_policy_replay(
    contribution: str | Path,
    proposal: str | Path,
) -> dict[str, Any]:
    contribution_payload = read_json(contribution)
    proposal_payload = read_json(proposal)
    if proposal_payload.get("artifact_type") != "tile_local_policy_proposal":
        raise ValueError("proposal must be a tile_local_policy_proposal artifact")
    target_group = str(proposal_payload.get("target_group") or "focus")
    if target_group not in {"focus", "control"}:
        raise ValueError("proposal target_group must be focus or control")

    frame_ids = set(_group_ids(contribution_payload, target_group))
    contribution_tiles = _tiles_by_index(contribution_payload)
    proposal_tiles = _tiles_by_index(proposal_payload, key="tile_index")
    rows: list[dict[str, Any]] = []
    missing_contribution_tiles: list[int] = []
    for tile_index, proposal_tile in sorted(proposal_tiles.items()):
        contribution_tile = contribution_tiles.get(tile_index)
        if contribution_tile is None:
            missing_contribution_tiles.append(tile_index)
            continue
        rows.append(
            _tile_replay_row(
                contribution_tile,
                proposal_tile,
                frame_ids=frame_ids,
                target_group=target_group,
            )
        )

    known = [
        row
        for row in rows
        if row.get("signed_residual_reference_units_before") is not None
        and row.get("signed_residual_reference_units_after") is not None
    ]
    before_abs = _finite([abs(float(row["signed_residual_reference_units_before"])) for row in known])
    after_abs = _finite([abs(float(row["signed_residual_reference_units_after"])) for row in known])
    toward_count = sum(1 for row in known if row.get("moves_toward_reference") is True)
    away_count = sum(1 for row in known if row.get("moves_toward_reference") is False)
    mean_before = None if before_abs.size == 0 else float(np.mean(before_abs))
    mean_after = None if after_abs.size == 0 else float(np.mean(after_abs))
    reductions = _finite([_float_or_none(row.get("residual_reduction_fraction")) for row in known])
    recommendation = (
        "tile_local_replay_promising"
        if known and toward_count == len(known) and mean_before is not None and mean_after is not None and mean_after < mean_before
        else "not_promotable"
    )
    multipliers = _finite([_float_or_none(row.get("multiplier")) for row in rows])
    canonical_deltas = _finite([_float_or_none(row.get("canonical_delta_contribution_adu")) for row in rows])
    per_frame_delta_mismatches = _finite(
        [_float_or_none(row.get("per_frame_delta_minus_canonical_delta_adu")) for row in rows]
    )
    return {
        "schema_version": 1,
        "artifact_type": "tile_local_policy_replay",
        "created_at": now_iso(),
        "contribution": str(contribution),
        "proposal": str(proposal),
        "target_group": target_group,
        "residual_stat": proposal_payload.get("residual_stat"),
        "target_frame_ids": sorted(frame_ids),
        "tile_count": len(rows),
        "missing_contribution_tiles": missing_contribution_tiles,
        "summary": {
            "known_direction_tiles": len(known),
            "moves_toward_reference": toward_count,
            "moves_away_from_reference": away_count,
            "boost_tiles": sum(1 for row in rows if row.get("action") == "boost"),
            "downweight_tiles": sum(1 for row in rows if row.get("action") == "downweight"),
            "hold_tiles": sum(1 for row in rows if row.get("action") == "hold"),
            "clamped_tiles": sum(1 for row in rows if row.get("clamped") is True),
            "mean_abs_residual_before": mean_before,
            "mean_abs_residual_after": mean_after,
            "mean_residual_reduction_fraction": None if reductions.size == 0 else float(np.mean(reductions)),
            "multiplier_stats": _stats(multipliers),
            "canonical_delta_contribution_adu_stats": _stats(canonical_deltas),
            "per_frame_delta_minus_canonical_delta_adu_stats": _stats(per_frame_delta_mismatches),
            "recommendation": recommendation,
        },
        "tiles": rows,
        "limitations": [
            "This replay applies the tile-local proposal to contribution summaries only.",
            "It does not modify resident CUDA integration output and does not write image pixels.",
            "Per-frame rows come from the resident contribution artifact; the canonical contribution uses the proposal summary.",
        ],
    }


def write_tile_local_policy_replay(
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
        "# Tile-Local Policy Replay",
        "",
        f"- Contribution: `{payload.get('contribution')}`",
        f"- Proposal: `{payload.get('proposal')}`",
        f"- Target group: `{payload.get('target_group')}`",
        f"- Residual stat: `{payload.get('residual_stat')}`",
        f"- Recommendation: `{summary.get('recommendation')}`",
        f"- Toward / away: `{summary.get('moves_toward_reference')}` / `{summary.get('moves_away_from_reference')}`",
        f"- Mean abs residual before / after: `{summary.get('mean_abs_residual_before')}` / `{summary.get('mean_abs_residual_after')}`",
        "",
        "| tile | action | multiplier | canonical delta ADU | residual before | residual after | rows |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload.get("tiles", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            "| {tile} | {action} | {multiplier} | {delta} | {before} | {after} | {rows} |".format(
                tile=row.get("tile_index"),
                action=row.get("action"),
                multiplier=row.get("multiplier"),
                delta=row.get("canonical_delta_contribution_adu"),
                before=row.get("signed_residual_reference_units_before"),
                after=row.get("signed_residual_reference_units_after"),
                rows=row.get("selected_frame_row_count"),
            )
        )
    lines.extend(["", "## Limitations", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
