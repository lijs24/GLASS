from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from glass.io.json_io import read_json, write_json
from glass.models import now_iso
from glass.report.compare_tile_attribution import _float_or_none, _stats
from glass.report.tile_local_policy import _residual_value, _tile_index, _tile_pack_by_index


def _stat_mean(payload: dict[str, Any] | None) -> float | None:
    if not isinstance(payload, dict):
        return None
    return _float_or_none(payload.get("mean"))


def _nested_float(payload: dict[str, Any], *keys: str) -> float | None:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return _float_or_none(current)


def _finite(values: list[float | None]) -> np.ndarray:
    return np.asarray([value for value in values if value is not None], dtype=np.float64)


def _top_candidate_with_tiles(frame_family_search: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(frame_family_search, dict):
        return None
    top = frame_family_search.get("top_candidate")
    if not isinstance(top, dict):
        return None
    top_id = top.get("candidate_id")
    for candidate in frame_family_search.get("candidates", []):
        if isinstance(candidate, dict) and candidate.get("candidate_id") == top_id:
            merged = {**top, **candidate}
            if "summary" not in candidate and isinstance(top.get("summary"), dict):
                merged["summary"] = top["summary"]
            return merged
    return top


def _tiles_by_tile_index(candidate: dict[str, Any] | None) -> dict[int, dict[str, Any]]:
    result: dict[int, dict[str, Any]] = {}
    if not isinstance(candidate, dict):
        return result
    for tile in candidate.get("tiles", []):
        if not isinstance(tile, dict):
            continue
        tile_index = tile.get("tile_index")
        if tile_index is None:
            continue
        result[int(tile_index)] = tile
    return result


def build_tile_local_residual_source_audit(
    contribution: str | Path,
    *,
    tile_pack: str | Path | None = None,
    frame_family_search: str | Path | None = None,
    residual_stat: str = "tail_signed_mean",
    high_rejection_excess_threshold: float = 0.01,
    min_coverage_fraction: float = 0.95,
) -> dict[str, Any]:
    if residual_stat not in {"signed_mean", "tail_signed_mean"}:
        raise ValueError("residual_stat must be signed_mean or tail_signed_mean")
    if high_rejection_excess_threshold < 0.0:
        raise ValueError("high_rejection_excess_threshold must be non-negative")
    if not 0.0 <= min_coverage_fraction <= 1.0:
        raise ValueError("min_coverage_fraction must be in [0, 1]")
    contribution_payload = read_json(contribution)
    tile_pack_path = Path(tile_pack or contribution_payload.get("tile_pack_json") or "")
    tile_pack_payload = read_json(tile_pack_path) if str(tile_pack_path) else {"tiles": []}
    residual_tiles = _tile_pack_by_index(tile_pack_payload)
    frame_search_payload = read_json(frame_family_search) if frame_family_search else None
    top_candidate = _top_candidate_with_tiles(frame_search_payload)
    top_candidate_tiles = _tiles_by_tile_index(top_candidate)
    selected_frame_count = int(contribution_payload.get("selected_frame_count") or 0)

    rows: list[dict[str, Any]] = []
    for tile in contribution_payload.get("tiles", []):
        if not isinstance(tile, dict):
            continue
        tile_index = _tile_index(tile)
        if tile_index is None:
            continue
        residual_tile = residual_tiles.get(tile_index, {})
        residual = _residual_value(residual_tile, residual_stat)
        coverage_mean = _stat_mean(tile.get("diagnostic_coverage_map_stats"))
        coverage_fraction_mean = None
        if coverage_mean is not None and selected_frame_count > 0:
            coverage_fraction_mean = float(coverage_mean / selected_frame_count)
        high_map_mean = _stat_mean(tile.get("diagnostic_high_rejection_map_stats"))
        low_map_mean = _stat_mean(tile.get("diagnostic_low_rejection_map_stats"))
        frame_family_tile = top_candidate_tiles.get(tile_index, {})
        high_delta = _nested_float(tile, "focus_vs_control", "high_rejected_fraction", "focus_minus_control")
        rejected_delta = _nested_float(tile, "focus_vs_control", "rejected_fraction", "focus_minus_control")
        contribution_delta = _nested_float(
            tile,
            "focus_vs_control",
            "tile_normalized_delta_contribution_sum",
            "focus_minus_control",
        )
        rows.append(
            {
                "tile_index": tile_index,
                "extent": tile.get("extent") or residual_tile.get("extent"),
                "signed_residual_reference_units": residual,
                "tail_pixels": residual_tile.get("tail_pixels"),
                "tail_fraction_of_valid": _float_or_none(residual_tile.get("tail_fraction_of_valid")),
                "coverage_fraction_mean": coverage_fraction_mean,
                "coverage_mean": coverage_mean,
                "high_rejection_map_mean": high_map_mean,
                "low_rejection_map_mean": low_map_mean,
                "high_minus_low_rejection_map_mean": None
                if high_map_mean is None or low_map_mean is None
                else float(high_map_mean - low_map_mean),
                "focus_high_rejected_fraction_minus_control": high_delta,
                "focus_rejected_fraction_minus_control": rejected_delta,
                "focus_contribution_sum_minus_control": contribution_delta,
                "diagnostic_master_delta_to_master_mean": _stat_mean(tile.get("diagnostic_master_delta_to_master")),
                "top_frame_family_candidate": None if top_candidate is None else top_candidate.get("candidate_id"),
                "top_frame_family_residual_reduction_fraction": _float_or_none(
                    frame_family_tile.get("residual_reduction_fraction")
                ),
                "top_frame_family_group_contribution_adu": _float_or_none(
                    frame_family_tile.get("group_contribution_adu")
                ),
                "top_frame_family_multiplier": _float_or_none(frame_family_tile.get("multiplier")),
                "coverage_below_threshold": bool(
                    coverage_fraction_mean is not None and coverage_fraction_mean < min_coverage_fraction
                ),
                "focus_high_rejection_excess": bool(
                    high_delta is not None and high_delta > high_rejection_excess_threshold
                ),
            }
        )

    top_summary = top_candidate.get("summary") if isinstance(top_candidate, dict) else {}
    total_before = _float_or_none(top_summary.get("total_abs_residual_before")) if isinstance(top_summary, dict) else None
    total_reduction = (
        _float_or_none(top_summary.get("total_abs_residual_reduction")) if isinstance(top_summary, dict) else None
    )
    explained_fraction = None
    if total_before is not None and total_before > 0.0 and total_reduction is not None:
        explained_fraction = float(total_reduction / total_before)
    coverage_low_count = sum(1 for row in rows if row.get("coverage_below_threshold") is True)
    high_excess_count = sum(1 for row in rows if row.get("focus_high_rejection_excess") is True)
    if rows and coverage_low_count > 0:
        recommendation = "inspect_coverage_or_valid_masks"
    elif rows and high_excess_count >= max(1, len(rows) // 2) and (explained_fraction is None or explained_fraction < 0.05):
        recommendation = "prioritize_rejection_registration_diagnostics"
    elif explained_fraction is not None and explained_fraction >= 0.05:
        recommendation = "bounded_frame_family_apply_candidate"
    else:
        recommendation = "continue_residual_source_search"
    signed_residual_abs = [
        None if (value := _float_or_none(row.get("signed_residual_reference_units"))) is None else abs(float(value))
        for row in rows
    ]

    return {
        "schema_version": 1,
        "artifact_type": "tile_local_residual_source_audit",
        "created_at": now_iso(),
        "contribution": str(contribution),
        "tile_pack": str(tile_pack_path) if str(tile_pack_path) else None,
        "frame_family_search": str(frame_family_search) if frame_family_search else None,
        "residual_stat": residual_stat,
        "selected_frame_count": selected_frame_count,
        "tile_count": len(rows),
        "thresholds": {
            "high_rejection_excess_threshold": float(high_rejection_excess_threshold),
            "min_coverage_fraction": float(min_coverage_fraction),
        },
        "summary": {
            "recommendation": recommendation,
            "coverage_below_threshold_tiles": coverage_low_count,
            "focus_high_rejection_excess_tiles": high_excess_count,
            "top_frame_family_candidate": None if top_candidate is None else top_candidate.get("candidate_id"),
            "top_frame_family_total_abs_residual_before": total_before,
            "top_frame_family_total_abs_residual_reduction": total_reduction,
            "top_frame_family_explained_fraction": explained_fraction,
            "signed_residual_abs_stats": _stats(_finite(signed_residual_abs)),
            "coverage_fraction_mean_stats": _stats(_finite([_float_or_none(row.get("coverage_fraction_mean")) for row in rows])),
            "high_rejection_map_mean_stats": _stats(_finite([_float_or_none(row.get("high_rejection_map_mean")) for row in rows])),
            "low_rejection_map_mean_stats": _stats(_finite([_float_or_none(row.get("low_rejection_map_mean")) for row in rows])),
            "focus_high_rejection_excess_stats": _stats(
                _finite([_float_or_none(row.get("focus_high_rejected_fraction_minus_control")) for row in rows])
            ),
            "top_frame_family_residual_reduction_fraction_stats": _stats(
                _finite([_float_or_none(row.get("top_frame_family_residual_reduction_fraction")) for row in rows])
            ),
        },
        "tiles": rows,
        "limitations": [
            "This audit consumes GLASS JSON diagnostics only and does not read image pixels.",
            "It highlights likely residual-source families but does not prove causality.",
            "Frame-family explanation is based on bounded tile-level contribution summaries, not a native per-pixel solve.",
        ],
    }


def write_tile_local_residual_source_audit(
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
        "# Tile-Local Residual Source Audit",
        "",
        f"- Contribution: `{payload.get('contribution')}`",
        f"- Tile pack: `{payload.get('tile_pack')}`",
        f"- Frame-family search: `{payload.get('frame_family_search')}`",
        f"- Recommendation: `{summary.get('recommendation')}`",
        f"- Coverage-below-threshold tiles: `{summary.get('coverage_below_threshold_tiles')}`",
        f"- Focus high-rejection-excess tiles: `{summary.get('focus_high_rejection_excess_tiles')}`",
        f"- Top frame-family explained fraction: `{summary.get('top_frame_family_explained_fraction')}`",
        "",
        "| tile | residual | coverage frac | high rej mean | low rej mean | focus high rej delta | top family reduction |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload.get("tiles", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            "| {tile} | {residual} | {coverage} | {high} | {low} | {delta} | {reduction} |".format(
                tile=row.get("tile_index"),
                residual=row.get("signed_residual_reference_units"),
                coverage=row.get("coverage_fraction_mean"),
                high=row.get("high_rejection_map_mean"),
                low=row.get("low_rejection_map_mean"),
                delta=row.get("focus_high_rejected_fraction_minus_control"),
                reduction=row.get("top_frame_family_residual_reduction_fraction"),
            )
        )
    lines.extend(["", "## Limitations", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
