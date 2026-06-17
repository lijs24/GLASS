from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import numpy as np

from glass.io.json_io import read_json, write_json
from glass.models import now_iso
from glass.report.compare_tile_attribution import _float_or_none
from glass.report.tile_local_policy import (
    _action_from_multiplier,
    _glass_scale,
    _reduction_fraction,
    _residual_value,
    _saturation_summary,
    _tile_index,
    _tile_pack_by_index,
)

_FRAME_SUFFIX_RE = re.compile(r"^(.*?)(\d+)$")


def _frame_sort_key(frame_id: str) -> tuple[str, int, str]:
    match = _FRAME_SUFFIX_RE.match(str(frame_id))
    if match is None:
        return (str(frame_id), -1, str(frame_id))
    return (match.group(1), int(match.group(2)), str(frame_id))


def _frame_windows(frame_ids: list[str], *, window_sizes: list[int], stride: int) -> list[dict[str, Any]]:
    if stride <= 0:
        raise ValueError("stride must be positive")
    ordered = sorted(set(str(frame_id) for frame_id in frame_ids), key=_frame_sort_key)
    windows: list[dict[str, Any]] = []
    seen: set[tuple[str, ...]] = set()
    for window_size in sorted(set(int(value) for value in window_sizes)):
        if window_size <= 0:
            raise ValueError("window sizes must be positive")
        if window_size > len(ordered):
            continue
        for start in range(0, len(ordered) - window_size + 1, stride):
            selected = tuple(ordered[start : start + window_size])
            if selected in seen:
                continue
            seen.add(selected)
            candidate_id = selected[0] if len(selected) == 1 else f"{selected[0]}-{selected[-1]}"
            windows.append(
                {
                    "candidate_id": candidate_id,
                    "frame_ids": list(selected),
                    "window_size": window_size,
                    "start_index": start,
                }
            )
    return windows


def _tile_frame_contributions(contribution_tile: dict[str, Any]) -> dict[str, float]:
    result: dict[str, float] = {}
    frames = contribution_tile.get("top_frames")
    if not isinstance(frames, list):
        return result
    for frame in frames:
        if not isinstance(frame, dict):
            continue
        frame_id = frame.get("frame_id")
        if frame_id is None:
            continue
        value = _float_or_none(frame.get("normalized_delta_contribution_mean"))
        if value is None:
            continue
        result[str(frame_id)] = float(value)
    return result


def _candidate_tile_row(
    *,
    contribution_tile: dict[str, Any],
    residual_tile: dict[str, Any],
    frame_ids: list[str],
    residual_stat: str,
    scale: float,
    min_multiplier: float,
    max_multiplier: float,
) -> dict[str, Any]:
    frame_contributions = _tile_frame_contributions(contribution_tile)
    contribution_adu = float(sum(frame_contributions.get(frame_id, 0.0) for frame_id in frame_ids))
    contribution_reference = contribution_adu * float(scale)
    residual = _residual_value(residual_tile, residual_stat)
    if residual is None or abs(contribution_reference) <= 0.0:
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
    return {
        "tile_index": _tile_index(contribution_tile),
        "extent": contribution_tile.get("extent") or residual_tile.get("extent"),
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


def _candidate_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    known = [
        row
        for row in rows
        if row.get("signed_residual_reference_units") is not None
        and row.get("predicted_signed_residual_after") is not None
    ]
    before_abs = np.asarray([abs(float(row["signed_residual_reference_units"])) for row in known], dtype=np.float64)
    after_abs = np.asarray([abs(float(row["predicted_signed_residual_after"])) for row in known], dtype=np.float64)
    toward_count = sum(1 for row in known if row.get("moves_toward_reference") is True)
    away_count = sum(1 for row in known if row.get("moves_toward_reference") is False)
    total_before = None if before_abs.size == 0 else float(np.sum(before_abs))
    total_after = None if after_abs.size == 0 else float(np.sum(after_abs))
    total_reduction = None if total_before is None or total_after is None else float(total_before - total_after)
    summary = {
        "known_direction_tiles": len(known),
        "moves_toward_reference": toward_count,
        "moves_away_from_reference": away_count,
        "boost_tiles": sum(1 for row in rows if row.get("action") == "boost"),
        "downweight_tiles": sum(1 for row in rows if row.get("action") == "downweight"),
        "hold_tiles": sum(1 for row in rows if row.get("action") == "hold"),
        "clamped_tiles": sum(1 for row in rows if row.get("clamped") is True),
        "mean_abs_residual_before": None if before_abs.size == 0 else float(np.mean(before_abs)),
        "mean_abs_residual_after": None if after_abs.size == 0 else float(np.mean(after_abs)),
        "total_abs_residual_before": total_before,
        "total_abs_residual_after": total_after,
        "total_abs_residual_reduction": total_reduction,
    }
    summary.update(_saturation_summary(rows, len(known)))
    summary["recommendation"] = (
        "frame_family_candidate"
        if known
        and toward_count == len(known)
        and total_reduction is not None
        and total_reduction > 0.0
        else "not_promotable"
    )
    return summary


def build_tile_local_frame_family_search(
    contribution: str | Path,
    *,
    tile_pack: str | Path | None = None,
    residual_stat: str = "tail_signed_mean",
    min_multiplier: float = 0.0,
    max_multiplier: float = 2.0,
    glass_scale: float | None = None,
    window_sizes: list[int] | tuple[int, ...] = (1, 3, 5, 11),
    stride: int = 1,
    top_n: int = 20,
) -> dict[str, Any]:
    if residual_stat not in {"signed_mean", "tail_signed_mean"}:
        raise ValueError("residual_stat must be signed_mean or tail_signed_mean")
    if min_multiplier < 0.0:
        raise ValueError("min_multiplier must be non-negative")
    if max_multiplier < min_multiplier:
        raise ValueError("max_multiplier must be >= min_multiplier")
    if top_n < 0:
        raise ValueError("top_n must be non-negative")
    contribution_payload = read_json(contribution)
    tile_pack_path = Path(tile_pack or contribution_payload.get("tile_pack_json") or "")
    tile_pack_payload = read_json(tile_pack_path) if str(tile_pack_path) else {"tiles": []}
    residual_tiles = _tile_pack_by_index(tile_pack_payload)
    scale = _glass_scale(tile_pack_payload, glass_scale)

    contribution_tiles = [
        tile
        for tile in contribution_payload.get("tiles", [])
        if isinstance(tile, dict) and _tile_index(tile) in residual_tiles
    ]
    frame_ids: list[str] = []
    for tile in contribution_tiles:
        frame_ids.extend(_tile_frame_contributions(tile))
    windows = _frame_windows(frame_ids, window_sizes=list(window_sizes), stride=stride)

    candidates: list[dict[str, Any]] = []
    for window in windows:
        rows = [
            _candidate_tile_row(
                contribution_tile=tile,
                residual_tile=residual_tiles[int(_tile_index(tile))],
                frame_ids=window["frame_ids"],
                residual_stat=residual_stat,
                scale=scale,
                min_multiplier=min_multiplier,
                max_multiplier=max_multiplier,
            )
            for tile in contribution_tiles
        ]
        summary = _candidate_summary(rows)
        candidates.append(
            {
                **window,
                "summary": summary,
                "tiles": rows,
            }
        )

    candidates.sort(
        key=lambda candidate: (
            float(candidate["summary"].get("total_abs_residual_reduction") or 0.0),
            int(candidate["summary"].get("moves_toward_reference") or 0),
            -int(candidate.get("window_size") or 0),
        ),
        reverse=True,
    )
    retained = candidates if top_n == 0 else candidates[:top_n]
    top = retained[0] if retained else None
    return {
        "schema_version": 1,
        "artifact_type": "tile_local_frame_family_search",
        "created_at": now_iso(),
        "contribution": str(contribution),
        "tile_pack": str(tile_pack_path) if str(tile_pack_path) else None,
        "residual_stat": residual_stat,
        "glass_scale": float(scale),
        "min_multiplier": float(min_multiplier),
        "max_multiplier": float(max_multiplier),
        "window_sizes": [int(value) for value in window_sizes],
        "stride": int(stride),
        "candidate_count": len(candidates),
        "retained_candidate_count": len(retained),
        "tile_count": len(contribution_tiles),
        "top_candidate": None
        if top is None
        else {
            "candidate_id": top.get("candidate_id"),
            "frame_ids": top.get("frame_ids"),
            "window_size": top.get("window_size"),
            "summary": top.get("summary"),
        },
        "candidates": retained,
        "limitations": [
            "This is a summary search over resident contribution artifacts; it does not change image pixels.",
            "Candidate windows use sorted available frame ids and do not prove a physical root cause.",
            "Scores use tile-level residual and contribution means, not a native per-pixel optimization.",
        ],
    }


def write_tile_local_frame_family_search(
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
        "# Tile-Local Frame-Family Search",
        "",
        f"- Contribution: `{payload.get('contribution')}`",
        f"- Tile pack: `{payload.get('tile_pack')}`",
        f"- Residual stat: `{payload.get('residual_stat')}`",
        f"- Candidate count: `{payload.get('candidate_count')}`",
        f"- Retained candidate count: `{payload.get('retained_candidate_count')}`",
        "",
        "| rank | candidate | frames | window | total reduction | mean before | mean after | toward | clamped fraction | boost p50 | applied/required mean |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for rank, candidate in enumerate(payload.get("candidates", []), start=1):
        if not isinstance(candidate, dict):
            continue
        summary = candidate.get("summary") if isinstance(candidate.get("summary"), dict) else {}
        boost_stats = summary.get("boost_required_multiplier_stats")
        ratio_stats = summary.get("applied_to_required_boost_ratio_stats")
        boost_p50 = boost_stats.get("p50") if isinstance(boost_stats, dict) else None
        ratio_mean = ratio_stats.get("mean") if isinstance(ratio_stats, dict) else None
        lines.append(
            "| {rank} | {candidate} | {frames} | {window} | {reduction} | {before} | {after} | {toward} | {clamped} | {boost_p50} | {ratio_mean} |".format(
                rank=rank,
                candidate=candidate.get("candidate_id"),
                frames=len(candidate.get("frame_ids") or []),
                window=candidate.get("window_size"),
                reduction=summary.get("total_abs_residual_reduction"),
                before=summary.get("mean_abs_residual_before"),
                after=summary.get("mean_abs_residual_after"),
                toward=summary.get("moves_toward_reference"),
                clamped=summary.get("clamped_fraction"),
                boost_p50=boost_p50,
                ratio_mean=ratio_mean,
            )
        )
    lines.extend(["", "## Limitations", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
