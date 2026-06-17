from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from glass.io.json_io import read_json, write_json
from glass.models import now_iso


def _float(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if np.isfinite(number) else default


def _extent_from_row(row: dict[str, Any]) -> dict[str, int]:
    if isinstance(row.get("extent"), dict):
        raw = row["extent"]
    else:
        raw = row
    try:
        extent = {
            "x0": int(raw["x0"]),
            "y0": int(raw["y0"]),
            "x1": int(raw["x1"]),
            "y1": int(raw["y1"]),
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"tile row has invalid extent: {row}") from exc
    if extent["x1"] <= extent["x0"] or extent["y1"] <= extent["y0"]:
        raise ValueError(f"tile extent must be positive: {extent}")
    return extent


def _overlaps(left: dict[str, int], right: dict[str, int]) -> bool:
    return max(left["x0"], right["x0"]) < min(left["x1"], right["x1"]) and max(left["y0"], right["y0"]) < min(
        left["y1"],
        right["y1"],
    )


def _area(extent: dict[str, int]) -> int:
    return int((extent["x1"] - extent["x0"]) * (extent["y1"] - extent["y0"]))


def _overlap_area(left: dict[str, int], right: dict[str, int]) -> int:
    width = max(0, min(left["x1"], right["x1"]) - max(left["x0"], right["x0"]))
    height = max(0, min(left["y1"], right["y1"]) - max(left["y0"], right["y0"]))
    return int(width * height)


def _known_extents(paths: list[str | Path] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths or []:
        payload = read_json(path)
        tiles = payload.get("tiles") if isinstance(payload, dict) else None
        if not isinstance(tiles, list):
            raise ValueError(f"known tile pack has no tiles list: {path}")
        for index, tile in enumerate(tiles):
            if not isinstance(tile, dict):
                continue
            extent = _extent_from_row(tile)
            rows.append(
                {
                    "known_tile_pack": str(path),
                    "known_tile_index": int(tile.get("index", index)),
                    "extent": extent,
                }
            )
    return rows


def _score(row: dict[str, Any], prefer: str) -> float:
    if prefer == "tail_pixels":
        return _float(row.get("tail_pixels"))
    if prefer == "tail_fraction":
        return _float(row.get("tail_fraction_of_valid"))
    if prefer == "tail_abs_mean":
        return _float(row.get("tail_abs_mean"))
    if prefer == "tail_abs_max":
        return _float(row.get("tail_abs_max"))
    raise ValueError(f"unsupported residual tile ranking: {prefer}")


def _candidate_from_top_tile(
    *,
    audit_path: str | Path,
    audit: dict[str, Any],
    row: dict[str, Any],
    source_index: int,
    prefer: str,
    known: list[dict[str, Any]],
) -> dict[str, Any]:
    extent = _extent_from_row(row)
    known_overlaps = []
    for known_row in known:
        overlap = _overlap_area(extent, known_row["extent"])
        if overlap <= 0:
            continue
        known_overlaps.append(
            {
                "known_tile_pack": known_row["known_tile_pack"],
                "known_tile_index": known_row["known_tile_index"],
                "overlap_area": overlap,
                "overlap_fraction_of_candidate": float(overlap / _area(extent)),
            }
        )
    score = _score(row, prefer)
    return {
        "source_audit": str(audit_path),
        "source_tile_index": source_index,
        "extent": extent,
        "score": score,
        "score_basis": prefer,
        "tail_pixels": int(row.get("tail_pixels") or 0),
        "valid_pixels": int(row.get("valid_pixels") or 0),
        "tail_fraction_of_valid": _float(row.get("tail_fraction_of_valid")),
        "tail_abs_mean": _float(row.get("tail_abs_mean")),
        "tail_abs_max": _float(row.get("tail_abs_max")),
        "tail_signed_mean": _float(row.get("tail_signed_mean")),
        "negative_tail_pixels": int(row.get("negative_tail_pixels") or 0),
        "positive_tail_pixels": int(row.get("positive_tail_pixels") or 0),
        "source_glass": audit.get("glass"),
        "source_reference": audit.get("reference"),
        "source_coverage_map": audit.get("coverage_map"),
        "source_top_tile": row,
        "known_overlap_count": len(known_overlaps),
        "known_overlaps": known_overlaps,
    }


def build_residual_tile_candidates(
    outlier_audits: list[str | Path],
    *,
    known_tile_packs: list[str | Path] | None = None,
    max_tiles: int = 16,
    min_tail_pixels: int = 1,
    min_tail_fraction: float = 0.0,
    prefer: str = "tail_pixels",
    drop_overlaps: bool = True,
    known_overlap_mode: str = "include",
) -> dict[str, Any]:
    if not outlier_audits:
        raise ValueError("at least one compare outlier audit is required")
    if max_tiles <= 0:
        raise ValueError("max_tiles must be positive")
    if min_tail_pixels < 0:
        raise ValueError("min_tail_pixels must be non-negative")
    if min_tail_fraction < 0.0:
        raise ValueError("min_tail_fraction must be non-negative")
    if known_overlap_mode not in {"include", "exclude", "only"}:
        raise ValueError(f"unsupported known overlap mode: {known_overlap_mode}")
    known = _known_extents(known_tile_packs)
    candidates: list[dict[str, Any]] = []
    source_summaries: list[dict[str, Any]] = []
    filtered_known_overlap = 0
    for audit_path in outlier_audits:
        audit = read_json(audit_path)
        if not isinstance(audit, dict) or audit.get("audit_type") != "compare_outlier_audit":
            raise ValueError(f"expected compare_outlier_audit artifact: {audit_path}")
        if audit.get("status") != "completed":
            raise ValueError(f"compare outlier audit is not completed: {audit_path}")
        top_tiles = audit.get("top_tiles")
        if not isinstance(top_tiles, list) or not top_tiles:
            raise ValueError(f"compare outlier audit has no top_tiles: {audit_path}")
        kept = 0
        for index, row in enumerate(top_tiles):
            if not isinstance(row, dict):
                continue
            if int(row.get("tail_pixels") or 0) < int(min_tail_pixels):
                continue
            if _float(row.get("tail_fraction_of_valid")) < float(min_tail_fraction):
                continue
            candidate = _candidate_from_top_tile(
                audit_path=audit_path,
                audit=audit,
                row=row,
                source_index=index,
                prefer=prefer,
                known=known,
            )
            has_known_overlap = int(candidate.get("known_overlap_count") or 0) > 0
            if known_overlap_mode == "exclude" and has_known_overlap:
                filtered_known_overlap += 1
                continue
            if known_overlap_mode == "only" and not has_known_overlap:
                filtered_known_overlap += 1
                continue
            candidates.append(candidate)
            kept += 1
        source_summaries.append(
            {
                "path": str(audit_path),
                "top_tile_count": len(top_tiles),
                "candidate_count_after_filters": kept,
                "recommendation": (audit.get("recommendation") or {}).get("status")
                if isinstance(audit.get("recommendation"), dict)
                else None,
                "target_exceedance_pixels": (audit.get("target_exceedance") or {}).get("pixels")
                if isinstance(audit.get("target_exceedance"), dict)
                else None,
            }
        )
    candidates.sort(
        key=lambda row: (
            float(row.get("score") or 0.0),
            int(row.get("tail_pixels") or 0),
            float(row.get("tail_abs_max") or 0.0),
            -int(row.get("source_tile_index") or 0),
        ),
        reverse=True,
    )
    selected: list[dict[str, Any]] = []
    dropped_overlap: list[dict[str, Any]] = []
    dropped_limit: list[dict[str, Any]] = []
    for row in candidates:
        overlaps_with = [
            int(existing["index"])
            for existing in selected
            if _overlaps(row["extent"], existing["extent"])
        ]
        if drop_overlaps and overlaps_with:
            dropped_overlap.append(
                {
                    "source_audit": row["source_audit"],
                    "source_tile_index": row["source_tile_index"],
                    "extent": row["extent"],
                    "overlaps_with_selected": overlaps_with,
                    "score": row["score"],
                }
            )
            continue
        if len(selected) >= int(max_tiles):
            dropped_limit.append(
                {
                    "source_audit": row["source_audit"],
                    "source_tile_index": row["source_tile_index"],
                    "extent": row["extent"],
                    "score": row["score"],
                }
            )
            continue
        row = dict(row)
        row["index"] = len(selected)
        selected.append(row)
    known_selected = sum(1 for row in selected if int(row.get("known_overlap_count") or 0) > 0)
    return {
        "schema_version": 1,
        "artifact_type": "residual_tile_candidates",
        "created_at": now_iso(),
        "outlier_audits": [str(path) for path in outlier_audits],
        "known_tile_packs": [str(path) for path in known_tile_packs or []],
        "selection_policy": {
            "max_tiles": int(max_tiles),
            "min_tail_pixels": int(min_tail_pixels),
            "min_tail_fraction": float(min_tail_fraction),
            "prefer": prefer,
            "drop_overlaps": bool(drop_overlaps),
            "known_overlap_mode": known_overlap_mode,
        },
        "summary": {
            "source_count": len(outlier_audits),
            "raw_candidate_count": len(candidates),
            "selected_tile_count": len(selected),
            "selected_known_overlap_count": known_selected,
            "selected_new_region_count": len(selected) - known_selected,
            "filtered_known_overlap_count": filtered_known_overlap,
            "dropped_overlap_count": len(dropped_overlap),
            "dropped_limit_count": len(dropped_limit),
            "top_score": selected[0].get("score") if selected else None,
            "recommendation": "capture_resident_contributions_for_selected_tiles" if selected else "no_candidate_tiles",
        },
        "source_summaries": source_summaries,
        "tile_count": len(selected),
        "tiles": selected,
        "dropped_overlap_tiles": dropped_overlap,
        "dropped_limit_tiles": dropped_limit,
        "limitations": [
            "This artifact ranks residual tiles from existing compare-outlier audits.",
            "It does not read image pixels, run registration, or change pipeline defaults.",
            "Known-overlap flags are diagnostic; a selected known-overlap tile can still be useful for regression comparison.",
        ],
    }


def write_residual_tile_candidates(
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
        "# Residual Tile Candidates",
        "",
        f"- Recommendation: `{summary.get('recommendation')}`",
        f"- Sources: `{summary.get('source_count')}`",
        f"- Raw candidates: `{summary.get('raw_candidate_count')}`",
        f"- Selected tiles: `{summary.get('selected_tile_count')}`",
        f"- New regions: `{summary.get('selected_new_region_count')}`",
        f"- Known overlaps: `{summary.get('selected_known_overlap_count')}`",
        f"- Dropped overlaps: `{summary.get('dropped_overlap_count')}`",
        "",
        "| rank | source tile | score | tail pixels | tail fraction | signed mean | known overlaps | extent |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for tile in payload.get("tiles") or []:
        if not isinstance(tile, dict):
            continue
        lines.append(
            "| {rank} | {source}#{tile_index} | {score} | {tail_pixels} | {tail_fraction} | {signed} | {known} | {extent} |".format(
                rank=tile.get("index"),
                source=Path(str(tile.get("source_audit"))).name,
                tile_index=tile.get("source_tile_index"),
                score=tile.get("score"),
                tail_pixels=tile.get("tail_pixels"),
                tail_fraction=tile.get("tail_fraction_of_valid"),
                signed=tile.get("tail_signed_mean"),
                known=tile.get("known_overlap_count"),
                extent=tile.get("extent"),
            )
        )
    lines.extend(["", "## Source Summaries", ""])
    for source in payload.get("source_summaries") or []:
        if isinstance(source, dict):
            lines.append(
                "- `{path}`: candidates `{count}` / top tiles `{top}`, target exceedance `{target}`".format(
                    path=source.get("path"),
                    count=source.get("candidate_count_after_filters"),
                    top=source.get("top_tile_count"),
                    target=source.get("target_exceedance_pixels"),
                )
            )
    lines.extend(["", "## Limitations", ""])
    for item in payload.get("limitations") or []:
        lines.append(f"- {item}")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
