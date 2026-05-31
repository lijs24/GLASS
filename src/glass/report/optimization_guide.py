from __future__ import annotations

from pathlib import Path
from typing import Any

from glass.report.speedup_report import _read_json_lenient


def _numeric(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _load_resident_artifact(glass_run: str | Path | None) -> dict[str, Any]:
    if glass_run is None:
        return {}
    path = Path(glass_run) / "resident_artifacts.json"
    if not path.exists():
        return {}
    payload = _read_json_lenient(path)
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        return {}
    first = artifacts[0]
    return first if isinstance(first, dict) else {}


def _resident_timing_from_payload(resident: dict[str, Any] | None) -> dict[str, Any]:
    artifacts = (resident or {}).get("artifacts")
    if isinstance(artifacts, list) and artifacts:
        first = artifacts[0]
        if isinstance(first, dict) and isinstance(first.get("timing_s"), dict):
            return first["timing_s"]
    if isinstance((resident or {}).get("timing_s"), dict):
        return (resident or {})["timing_s"]
    return {}


def _stage_rows_from_performance(performance_regression: dict[str, Any] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in (performance_regression or {}).get("items") or []:
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "stage": item.get("stage"),
                "actual_key": item.get("actual_key", item.get("stage")),
                "actual_s": _numeric(item.get("actual_s")),
                "baseline_s": _numeric(item.get("baseline_s")),
                "delta_s": _numeric(item.get("delta_s")),
                "factor": _numeric(item.get("factor")),
                "status": item.get("status"),
                "timing_kind": item.get("timing_kind"),
                "note": item.get("note"),
            }
        )
    return rows


def _stage_rows_from_resident_timing(timing: dict[str, Any]) -> list[dict[str, Any]]:
    preferred = [
        "master_build_or_load",
        "light_read_upload_calibrate",
        "light_read_wait_wall",
        "light_read_worker_cumulative",
        "light_h2d_calibrate_store",
        "resident_registration_warp",
        "resident_registration_component_accounted",
        "resident_weighting",
        "resident_local_normalization",
        "resident_integration",
        "output_write",
        "gc",
    ]
    rows: list[dict[str, Any]] = []
    for stage in preferred:
        actual = _numeric(timing.get(stage))
        if actual is None:
            continue
        rows.append(
            {
                "stage": stage,
                "actual_key": stage,
                "actual_s": actual,
                "baseline_s": None,
                "delta_s": None,
                "factor": None,
                "status": "current_only",
                "timing_kind": "worker_cumulative" if "cumulative" in stage else "wall_or_stage",
                "note": "",
            }
        )
    return rows


def _stage_lookup(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for row in rows:
        for key in (row.get("stage"), row.get("actual_key")):
            if key:
                lookup[str(key)] = row
    return lookup


def _timing_value(lookup: dict[str, dict[str, Any]], names: list[str]) -> float | None:
    for name in names:
        row = lookup.get(name)
        value = _numeric((row or {}).get("actual_s"))
        if value is not None:
            return value
    return None


def _timing_row(lookup: dict[str, dict[str, Any]], names: list[str]) -> dict[str, Any]:
    for name in names:
        row = lookup.get(name)
        if row:
            return row
    return {}


def _exception_context(frame_accounting: dict[str, Any] | None) -> dict[str, Any]:
    summary = (frame_accounting or {}).get("exception_summary") or {}
    exceptions = (frame_accounting or {}).get("exception_frames")
    exception_rows = exceptions if isinstance(exceptions, list) else []
    stage_counts = summary.get("primary_stage_counts") if isinstance(summary.get("primary_stage_counts"), dict) else {}
    final_counts = summary.get("final_status_counts") if isinstance(summary.get("final_status_counts"), dict) else {}
    sample_ids = [str(item.get("frame_id")) for item in exception_rows[:8] if isinstance(item, dict)]
    count = int(summary.get("count") or len(exception_rows))
    dominant_stage = None
    if stage_counts:
        dominant_stage = max(stage_counts.items(), key=lambda item: int(item[1] or 0))[0]
    return {
        "count": count,
        "dominant_stage": dominant_stage,
        "primary_stage_counts": stage_counts,
        "final_status_counts": final_counts,
        "sample_frame_ids": sample_ids,
        "note": (
            "Exception frames explain active-frame count drift; timing priorities remain based on wall-clock stages."
            if count
            else "No rejected or zero-weight frame exceptions were recorded."
        ),
    }


def build_optimization_guidance(
    *,
    performance_regression: dict[str, Any] | None = None,
    frame_accounting: dict[str, Any] | None = None,
    resident: dict[str, Any] | None = None,
    glass_run: str | Path | None = None,
) -> dict[str, Any]:
    resident_artifact = _load_resident_artifact(glass_run)
    timing = _resident_timing_from_payload(resident) or (
        resident_artifact.get("timing_s") if isinstance(resident_artifact.get("timing_s"), dict) else {}
    )
    stage_rows = _stage_rows_from_performance(performance_regression)
    if not stage_rows:
        stage_rows = _stage_rows_from_resident_timing(timing)
    lookup = _stage_lookup(stage_rows)
    exception_context = _exception_context(frame_accounting)

    target_specs = [
        {
            "target_id": "io_upload_calibration_pipeline",
            "label": "I/O + upload + calibration overlap",
            "primary_stages": ["light_read_upload_calibrate"],
            "related_stages": [
                "light_read_wait_wall",
                "light_read_worker_cumulative",
                "light_h2d_calibrate_store",
                "light_read_decode_worker",
            ],
            "next_action": (
                "Use deeper double/multi buffering, pinned host rings, async H2D, and larger batches so GPU "
                "calibration overlaps CPU FITS decode and disk reads."
            ),
        },
        {
            "target_id": "resident_registration_warp",
            "label": "Resident registration/warp batching",
            "primary_stages": ["resident_registration_warp"],
            "related_stages": [
                "resident_registration_component_accounted",
                "resident_registration_orchestration",
            ],
            "next_action": (
                "Keep star tables, descriptors, candidate scoring, pixel refinement, and warp scheduling resident "
                "on the GPU; reduce per-frame Python orchestration and host/device synchronization."
            ),
        },
        {
            "target_id": "output_write_policy",
            "label": "Output-map write policy",
            "primary_stages": ["output_write"],
            "related_stages": [],
            "next_action": (
                "Use science/minimal map policies for speed runs and keep full audit maps for validation runs."
            ),
        },
        {
            "target_id": "resident_master_cache",
            "label": "Resident master-frame cache",
            "primary_stages": ["master_build_or_load"],
            "related_stages": [],
            "next_action": (
                "Reuse the shared resident master cache when calibration inputs and policies are unchanged."
            ),
        },
    ]

    targets: list[dict[str, Any]] = []
    for spec in target_specs:
        primary = _timing_row(lookup, spec["primary_stages"])
        current_s = _numeric(primary.get("actual_s"))
        baseline_s = _numeric(primary.get("baseline_s"))
        factor = _numeric(primary.get("factor"))
        delta_s = _numeric(primary.get("delta_s"))
        if current_s is None and baseline_s is None:
            continue
        related_names = list(spec["related_stages"])
        related = [
            {
                "stage": name,
                "actual_s": _timing_value(lookup, [name]),
            }
            for name in related_names
            if _timing_value(lookup, [name]) is not None
        ]
        score = float(current_s or 0.0)
        if str(primary.get("status")) == "regressed":
            score *= 1.25
        if str(primary.get("timing_kind")) == "worker_cumulative":
            score = 0.0
        targets.append(
            {
                "target_id": spec["target_id"],
                "label": spec["label"],
                "primary_stage": primary.get("stage") or spec["primary_stages"][0],
                "current_s": current_s,
                "baseline_s": baseline_s,
                "delta_s": delta_s,
                "factor": factor,
                "status": primary.get("status"),
                "timing_kind": primary.get("timing_kind"),
                "priority_score": score,
                "related_stages": related,
                "next_action": spec["next_action"],
            }
        )

    targets.sort(key=lambda item: float(item.get("priority_score") or 0.0), reverse=True)
    total_target_wall = sum(float(item.get("current_s") or 0.0) for item in targets if item.get("timing_kind") != "worker_cumulative")
    for rank, target in enumerate(targets, start=1):
        target["rank"] = rank
        current_s = _numeric(target.get("current_s"))
        target["share_of_selected_wall"] = (
            None if current_s is None or total_target_wall <= 0.0 else current_s / total_target_wall
        )

    stage_rows.sort(
        key=lambda item: (
            item.get("timing_kind") != "worker_cumulative",
            _numeric(item.get("actual_s")) is not None,
            float(_numeric(item.get("actual_s")) or 0.0),
        ),
        reverse=True,
    )
    return {
        "schema_version": 1,
        "primary_target": targets[0]["target_id"] if targets else None,
        "targets": targets,
        "stage_timing_rows": stage_rows,
        "exception_context": exception_context,
    }
