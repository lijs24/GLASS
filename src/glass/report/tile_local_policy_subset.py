from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from glass.io.json_io import read_json, write_json
from glass.models import now_iso
from glass.report.compare_tile_attribution import _float_or_none, _stats


def _tile_index(tile: dict[str, Any]) -> int:
    value = tile.get("tile_index", tile.get("index"))
    if value is None:
        raise ValueError("tile row is missing tile_index")
    return int(value)


def _validated_extent(tile: dict[str, Any]) -> dict[str, int]:
    extent = tile.get("extent")
    if not isinstance(extent, dict):
        raise ValueError(f"tile {_tile_index(tile)} is missing extent")
    try:
        checked = {
            "x0": int(extent["x0"]),
            "y0": int(extent["y0"]),
            "x1": int(extent["x1"]),
            "y1": int(extent["y1"]),
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"tile {_tile_index(tile)} has an invalid extent") from exc
    if checked["x1"] <= checked["x0"] or checked["y1"] <= checked["y0"]:
        raise ValueError(f"tile {_tile_index(tile)} extent must be a positive rectangle")
    return checked


def _rectangles_overlap(left: dict[str, int], right: dict[str, int]) -> bool:
    return max(left["x0"], right["x0"]) < min(left["x1"], right["x1"]) and max(left["y0"], right["y0"]) < min(
        left["y1"],
        right["y1"],
    )


def _finite(values: list[float | None]) -> np.ndarray:
    return np.asarray([value for value in values if value is not None], dtype=np.float64)


def _score(tile: dict[str, Any], strategy: str) -> tuple[float, int]:
    tile_id = _tile_index(tile)
    if strategy == "tile_index":
        return (-float(tile_id), -tile_id)
    if strategy == "residual_reduction":
        reduction = _float_or_none(tile.get("residual_reduction_fraction"))
        return (float(reduction or 0.0), -tile_id)
    if strategy == "canonical_delta_abs":
        delta = _float_or_none(tile.get("canonical_delta_contribution_adu"))
        return (abs(float(delta or 0.0)), -tile_id)
    raise ValueError(f"unsupported tile-local subset strategy: {strategy}")


def _replay_summary(tiles: list[dict[str, Any]]) -> dict[str, Any]:
    known = [
        tile
        for tile in tiles
        if _float_or_none(tile.get("signed_residual_reference_units_before")) is not None
        and _float_or_none(tile.get("signed_residual_reference_units_after")) is not None
    ]
    before_abs = _finite([abs(float(tile["signed_residual_reference_units_before"])) for tile in known])
    after_abs = _finite([abs(float(tile["signed_residual_reference_units_after"])) for tile in known])
    reductions = _finite([_float_or_none(tile.get("residual_reduction_fraction")) for tile in known])
    toward_count = sum(1 for tile in known if tile.get("moves_toward_reference") is True)
    away_count = sum(1 for tile in known if tile.get("moves_toward_reference") is False)
    mean_before = None if before_abs.size == 0 else float(np.mean(before_abs))
    mean_after = None if after_abs.size == 0 else float(np.mean(after_abs))
    recommendation = (
        "tile_local_replay_promising"
        if known and toward_count == len(known) and mean_before is not None and mean_after is not None and mean_after < mean_before
        else "not_promotable"
    )
    return {
        "known_direction_tiles": len(known),
        "moves_toward_reference": toward_count,
        "moves_away_from_reference": away_count,
        "boost_tiles": sum(1 for tile in tiles if tile.get("action") == "boost"),
        "downweight_tiles": sum(1 for tile in tiles if tile.get("action") == "downweight"),
        "hold_tiles": sum(1 for tile in tiles if tile.get("action") == "hold"),
        "clamped_tiles": sum(1 for tile in tiles if tile.get("clamped") is True),
        "mean_abs_residual_before": mean_before,
        "mean_abs_residual_after": mean_after,
        "mean_residual_reduction_fraction": None if reductions.size == 0 else float(np.mean(reductions)),
        "multiplier_stats": _stats(_finite([_float_or_none(tile.get("multiplier")) for tile in tiles])),
        "canonical_delta_contribution_adu_stats": _stats(
            _finite([_float_or_none(tile.get("canonical_delta_contribution_adu")) for tile in tiles])
        ),
        "per_frame_delta_minus_canonical_delta_adu_stats": _stats(
            _finite([_float_or_none(tile.get("per_frame_delta_minus_canonical_delta_adu")) for tile in tiles])
        ),
        "recommendation": recommendation,
    }


def build_tile_local_policy_subset(
    replay: str | Path,
    *,
    strategy: str = "canonical_delta_abs",
    max_tiles: int = 0,
) -> dict[str, Any]:
    payload = read_json(replay)
    if not isinstance(payload, dict) or payload.get("artifact_type") != "tile_local_policy_replay":
        raise ValueError("replay must be a tile_local_policy_replay artifact")
    tiles = payload.get("tiles")
    if not isinstance(tiles, list) or not tiles:
        raise ValueError("replay must contain at least one tile")
    checked_tiles = [dict(tile) for tile in tiles if isinstance(tile, dict)]
    if len(checked_tiles) != len(tiles):
        raise ValueError("replay tiles must be JSON objects")
    for tile in checked_tiles:
        _validated_extent(tile)

    selected: list[dict[str, Any]] = []
    selected_extents: list[tuple[int, dict[str, int]]] = []
    dropped_overlap: list[dict[str, Any]] = []
    dropped_limit: list[int] = []
    max_selected = int(max_tiles)
    for tile in sorted(checked_tiles, key=lambda row: _score(row, strategy), reverse=True):
        tile_id = _tile_index(tile)
        if max_selected > 0 and len(selected) >= max_selected:
            dropped_limit.append(tile_id)
            continue
        extent = _validated_extent(tile)
        overlaps = [other_id for other_id, other_extent in selected_extents if _rectangles_overlap(extent, other_extent)]
        if overlaps:
            dropped_overlap.append({"tile_index": tile_id, "overlaps_with": overlaps, "extent": extent})
            continue
        selected.append(tile)
        selected_extents.append((tile_id, extent))

    if not selected:
        raise ValueError("tile-local subset selected no non-overlapping tiles")
    selected.sort(key=_tile_index)
    subset = dict(payload)
    subset.update(
        {
            "created_at": now_iso(),
            "source_replay": str(replay),
            "subset_strategy": strategy,
            "subset_max_tiles": max_selected,
            "original_tile_count": len(checked_tiles),
            "tile_count": len(selected),
            "tiles": selected,
            "summary": _replay_summary(selected),
            "dropped_overlap_tiles": dropped_overlap,
            "dropped_limit_tiles": dropped_limit,
            "limitations": [
                "This artifact is a non-overlapping subset of a tile-local replay contract.",
                "Selection is greedy by the requested strategy and is intended for bounded native apply experiments.",
                "It does not prove a global tile-local policy is safe.",
            ],
        }
    )
    return subset


def write_tile_local_policy_subset(
    out: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(out, payload)
    if markdown is None:
        return
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    target = Path(markdown)
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Tile-Local Policy Subset",
        "",
        f"- Source replay: `{payload.get('source_replay')}`",
        f"- Strategy: `{payload.get('subset_strategy')}`",
        f"- Original tiles: `{payload.get('original_tile_count')}`",
        f"- Selected tiles: `{payload.get('tile_count')}`",
        f"- Dropped overlap tiles: `{len(payload.get('dropped_overlap_tiles') or [])}`",
        f"- Dropped limit tiles: `{len(payload.get('dropped_limit_tiles') or [])}`",
        f"- Recommendation: `{summary.get('recommendation')}`",
        f"- Mean abs residual before / after: `{summary.get('mean_abs_residual_before')}` / `{summary.get('mean_abs_residual_after')}`",
        "",
        "| tile | action | multiplier | extent | residual before | residual after |",
        "| ---: | --- | ---: | --- | ---: | ---: |",
    ]
    for tile in payload.get("tiles", []):
        if not isinstance(tile, dict):
            continue
        lines.append(
            "| {tile} | {action} | {multiplier} | {extent} | {before} | {after} |".format(
                tile=_tile_index(tile),
                action=tile.get("action"),
                multiplier=tile.get("multiplier"),
                extent=tile.get("extent"),
                before=tile.get("signed_residual_reference_units_before"),
                after=tile.get("signed_residual_reference_units_after"),
            )
        )
    lines.extend(["", "## Dropped Overlaps", ""])
    for row in payload.get("dropped_overlap_tiles") or []:
        lines.append(f"- tile `{row.get('tile_index')}` overlaps with `{row.get('overlaps_with')}`")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
