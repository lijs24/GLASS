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


def _tile_index(payload: dict[str, Any]) -> int | None:
    value = payload.get("index")
    if value is None:
        return None
    return int(value)


def _tile_pack_by_index(tile_pack: dict[str, Any]) -> dict[int, dict[str, Any]]:
    tiles = tile_pack.get("tiles")
    if not isinstance(tiles, list):
        return {}
    result: dict[int, dict[str, Any]] = {}
    for tile in tiles:
        if not isinstance(tile, dict):
            continue
        index = _tile_index(tile)
        if index is not None:
            result[index] = tile
    return result


def _glass_scale(tile_pack: dict[str, Any], explicit: float | None) -> float:
    if explicit is not None:
        return float(explicit)
    transform = tile_pack.get("candidate_transform")
    if isinstance(transform, dict):
        value = _float_or_none(transform.get("scale"))
        if value is not None:
            return value
    return 1.0


def _residual_value(tile: dict[str, Any], residual_stat: str) -> float | None:
    if residual_stat == "signed_mean":
        signed = tile.get("signed_diff_stats")
        if isinstance(signed, dict):
            return _float_or_none(signed.get("mean"))
        return None
    if residual_stat == "tail_signed_mean":
        source = tile.get("source_top_tile")
        if isinstance(source, dict):
            return _float_or_none(source.get("tail_signed_mean"))
        return None
    raise ValueError("residual_stat must be signed_mean or tail_signed_mean")


def _action_from_multiplier(multiplier: float) -> str:
    if multiplier > 1.000001:
        return "boost"
    if multiplier < 0.999999:
        return "downweight"
    return "hold"


def _reduction_fraction(before: float, after: float) -> float | None:
    before_abs = abs(float(before))
    if before_abs <= 0.0:
        return None
    return float((before_abs - abs(float(after))) / before_abs)


def build_tile_local_policy_proposal(
    contribution: str | Path,
    *,
    tile_pack: str | Path | None = None,
    target_group: str = "focus",
    residual_stat: str = "signed_mean",
    min_multiplier: float = 0.0,
    max_multiplier: float = 2.0,
    glass_scale: float | None = None,
) -> dict[str, Any]:
    if target_group not in {"focus", "control"}:
        raise ValueError("target_group must be focus or control")
    if residual_stat not in {"signed_mean", "tail_signed_mean"}:
        raise ValueError("residual_stat must be signed_mean or tail_signed_mean")
    if min_multiplier < 0.0:
        raise ValueError("min_multiplier must be non-negative")
    if max_multiplier < min_multiplier:
        raise ValueError("max_multiplier must be >= min_multiplier")
    contribution_payload = read_json(contribution)
    tile_pack_path = Path(tile_pack or contribution_payload.get("tile_pack_json") or "")
    tile_pack_payload = read_json(tile_pack_path) if str(tile_pack_path) else {"tiles": []}
    scale = _glass_scale(tile_pack_payload, glass_scale)
    residual_tiles = _tile_pack_by_index(tile_pack_payload)
    rows: list[dict[str, Any]] = []
    for tile in contribution_payload.get("tiles", []):
        if not isinstance(tile, dict):
            continue
        tile_index = _tile_index(tile)
        if tile_index is None:
            continue
        residual_tile = residual_tiles.get(tile_index, {})
        residual = _residual_value(residual_tile, residual_stat)
        summary = tile.get(f"{target_group}_summary")
        contribution_adu = (
            _summary_mean(summary, "tile_normalized_delta_contribution_sum")
            if isinstance(summary, dict)
            else None
        )
        contribution_reference = None if contribution_adu is None else float(contribution_adu) * scale
        if residual is None or contribution_reference is None or abs(contribution_reference) <= 0.0:
            multiplier = 1.0
            unconstrained = None
            predicted_delta = 0.0
            after = residual
            action = "insufficient_signal"
            clamped = False
            moves_toward = None
        else:
            unconstrained = 1.0 - float(residual) / float(contribution_reference)
            multiplier = float(np.clip(unconstrained, float(min_multiplier), float(max_multiplier)))
            predicted_delta = (multiplier - 1.0) * float(contribution_reference)
            after = float(residual) + predicted_delta
            action = _action_from_multiplier(multiplier)
            clamped = bool(abs(multiplier - unconstrained) > 1.0e-9)
            moves_toward = bool(abs(after) < abs(float(residual)))
        rows.append(
            {
                "tile_index": tile_index,
                "extent": tile.get("extent"),
                "target_group": target_group,
                "residual_stat": residual_stat,
                "signed_residual_reference_units": residual,
                "group_contribution_adu": contribution_adu,
                "group_contribution_reference_units": contribution_reference,
                "unconstrained_multiplier": unconstrained,
                "multiplier": multiplier,
                "action": action,
                "clamped": clamped,
                "predicted_delta_reference_units": predicted_delta,
                "predicted_signed_residual_after": after,
                "moves_toward_reference": moves_toward,
                "residual_reduction_fraction": None
                if residual is None or after is None
                else _reduction_fraction(float(residual), float(after)),
            }
        )
    known = [row for row in rows if row.get("moves_toward_reference") is not None]
    toward_count = sum(1 for row in known if row.get("moves_toward_reference") is True)
    away_count = sum(1 for row in known if row.get("moves_toward_reference") is False)
    before_abs = np.asarray(
        [abs(float(row["signed_residual_reference_units"])) for row in known],
        dtype=np.float64,
    )
    after_abs = np.asarray(
        [abs(float(row["predicted_signed_residual_after"])) for row in known],
        dtype=np.float64,
    )
    recommendation = (
        "tile_local_policy_candidate"
        if known and toward_count == len(known) and float(np.mean(after_abs)) < float(np.mean(before_abs))
        else "not_promotable"
    )
    return {
        "schema_version": 1,
        "artifact_type": "tile_local_policy_proposal",
        "created_at": now_iso(),
        "contribution": str(contribution),
        "tile_pack": str(tile_pack_path) if str(tile_pack_path) else None,
        "target_group": target_group,
        "residual_stat": residual_stat,
        "glass_scale": float(scale),
        "min_multiplier": float(min_multiplier),
        "max_multiplier": float(max_multiplier),
        "tile_count": len(rows),
        "summary": {
            "known_direction_tiles": len(known),
            "moves_toward_reference": toward_count,
            "moves_away_from_reference": away_count,
            "boost_tiles": sum(1 for row in rows if row.get("action") == "boost"),
            "downweight_tiles": sum(1 for row in rows if row.get("action") == "downweight"),
            "hold_tiles": sum(1 for row in rows if row.get("action") == "hold"),
            "clamped_tiles": sum(1 for row in rows if row.get("clamped") is True),
            "mean_abs_residual_before": None if before_abs.size == 0 else float(np.mean(before_abs)),
            "mean_abs_residual_after": None if after_abs.size == 0 else float(np.mean(after_abs)),
            "recommendation": recommendation,
        },
        "tiles": rows,
        "limitations": [
            "This is a tile-local proposal artifact; it does not modify integration output.",
            "The estimate uses tile-level residual and contribution means, not per-pixel native integration weights.",
            "Multipliers above 1 are boost proposals and require a future tile-local integration implementation before use.",
        ],
    }


def write_tile_local_policy_proposal(
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
        "# Tile-Local Policy Proposal",
        "",
        f"- Contribution: `{payload.get('contribution')}`",
        f"- Tile pack: `{payload.get('tile_pack')}`",
        f"- Target group: `{payload.get('target_group')}`",
        f"- Residual stat: `{payload.get('residual_stat')}`",
        f"- Recommendation: `{summary.get('recommendation')}`",
        f"- Toward / away: `{summary.get('moves_toward_reference')}` / `{summary.get('moves_away_from_reference')}`",
        f"- Mean abs residual before / after: `{summary.get('mean_abs_residual_before')}` / `{summary.get('mean_abs_residual_after')}`",
        "",
        "| tile | action | multiplier | residual before | predicted after | reduction | clamped |",
        "| ---: | --- | ---: | ---: | ---: | ---: | :---: |",
    ]
    for row in payload.get("tiles", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            "| {tile} | {action} | {multiplier} | {before} | {after} | {reduction} | {clamped} |".format(
                tile=row.get("tile_index"),
                action=row.get("action"),
                multiplier=row.get("multiplier"),
                before=row.get("signed_residual_reference_units"),
                after=row.get("predicted_signed_residual_after"),
                reduction=row.get("residual_reduction_fraction"),
                clamped=row.get("clamped"),
            )
        )
    lines.extend(["", "## Limitations", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
