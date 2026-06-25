from __future__ import annotations

from pathlib import Path
from typing import Any

from glass.io.json_io import read_json, write_json
from glass.models import now_iso


TIMING_KEYS = [
    "master_build_or_load",
    "light_read_upload_calibrate",
    "light_read_wait_wall",
    "light_read_worker_cumulative",
    "light_read_supply_consumer_wait_wall",
    "light_read_supply_worker_cumulative",
    "light_read_supply_file_read",
    "light_read_supply_overlap_saved",
    "light_h2d_calibrate_store",
    "resident_registration_warp",
    "resident_local_normalization",
    "resident_integration",
    "output_write",
    "gc",
]

IO_KEYS = [
    "prefetch_frames",
    "prefetch_workers",
    "prefetch_refill_mode",
    "h2d_mode",
    "calibration_batch_requested_frames",
    "calibration_batch_requested_streams",
    "calibration_wave_requested_frames",
    "calibration_release_mode_requested",
    "calibration_release_mode_effective",
]


IO_OVERLAP_KEYS = [
    "read_supply_model",
    "read_supply_effective_backend",
    "read_supply_worker_cumulative_s",
    "read_supply_file_read_cumulative_s",
    "read_supply_consumer_wait_wall_s",
    "read_supply_overlap_saved_s",
    "read_supply_worker_to_wall_ratio",
    "read_supply_overlap_efficiency",
]


def _number(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result


def _load_first_resident_artifact(run: Path) -> dict[str, Any]:
    path = run / "resident_artifacts.json"
    if not path.exists():
        return {}
    payload = read_json(path)
    artifacts = payload.get("artifacts") if isinstance(payload, dict) else None
    if not isinstance(artifacts, list) or not artifacts:
        return {}
    first = artifacts[0]
    return first if isinstance(first, dict) else {}


def _read_supply_from_artifact(
    timing: dict[str, Any],
    io_pipeline: dict[str, Any],
    io_overlap: dict[str, Any],
) -> dict[str, float | None]:
    wall = _number(timing.get("light_read_upload_calibrate"))
    worker = _number(io_overlap.get("read_supply_worker_cumulative_s"))
    file_read = _number(io_overlap.get("read_supply_file_read_cumulative_s"))
    wait = _number(io_overlap.get("read_supply_consumer_wait_wall_s"))
    hidden = _number(io_overlap.get("read_supply_overlap_saved_s"))
    if worker is None and io_pipeline.get("native_completion_calibration_enabled"):
        worker = _number(io_pipeline.get("native_path_calibration_total_s"))
        file_read = _number(io_pipeline.get("native_path_calibration_file_read_s"))
        slot_wait = _number(io_pipeline.get("native_completion_calibration_slot_reuse_wait_s")) or 0.0
        fill_wait = (
            _number(io_pipeline.get("native_completion_calibration_consumer_wave_fill_wait_s"))
            or 0.0
        )
        wait = slot_wait + fill_wait
        hidden = None if worker is None or wall is None else max(0.0, worker - wall)
    if worker is None:
        worker = _number(timing.get("light_read_worker_cumulative"))
    if wait is None:
        wait = _number(timing.get("light_read_wait_wall"))
    if hidden is None and worker is not None and wall is not None:
        hidden = max(0.0, worker - wall)
    return {
        "light_read_supply_consumer_wait_wall": wait,
        "light_read_supply_worker_cumulative": worker,
        "light_read_supply_file_read": file_read,
        "light_read_supply_overlap_saved": hidden,
    }


def _io_overlap_row(
    timing: dict[str, Any],
    io_pipeline: dict[str, Any],
    io_overlap: dict[str, Any],
    read_supply: dict[str, float | None],
) -> dict[str, Any]:
    row = {key: io_overlap.get(key) for key in IO_OVERLAP_KEYS}
    if row.get("read_supply_model") is None and io_pipeline.get(
        "native_completion_calibration_enabled"
    ):
        row["read_supply_model"] = "native_completion_calibration"
    if row.get("read_supply_effective_backend") is None:
        row["read_supply_effective_backend"] = io_pipeline.get(
            "native_path_calibration_read_backend"
        )
    field_map = {
        "read_supply_worker_cumulative_s": "light_read_supply_worker_cumulative",
        "read_supply_file_read_cumulative_s": "light_read_supply_file_read",
        "read_supply_consumer_wait_wall_s": "light_read_supply_consumer_wait_wall",
        "read_supply_overlap_saved_s": "light_read_supply_overlap_saved",
    }
    for overlap_key, timing_key in field_map.items():
        if row.get(overlap_key) is None:
            row[overlap_key] = read_supply.get(timing_key)
    worker = _number(row.get("read_supply_worker_cumulative_s"))
    wall = _number(timing.get("light_read_upload_calibrate"))
    hidden = _number(row.get("read_supply_overlap_saved_s"))
    if row.get("read_supply_worker_to_wall_ratio") is None and worker not in (None, 0.0):
        row["read_supply_worker_to_wall_ratio"] = (
            None if wall in (None, 0.0) else float(worker) / float(wall)
        )
    if row.get("read_supply_overlap_efficiency") is None and worker not in (None, 0.0):
        row["read_supply_overlap_efficiency"] = (
            None if hidden is None else float(hidden) / float(worker)
        )
    return row


def _run_row(label: str, run: str | Path) -> dict[str, Any]:
    root = Path(run)
    timing_payload = read_json(root / "run_timing.json") if (root / "run_timing.json").exists() else {}
    artifact = _load_first_resident_artifact(root)
    timing = artifact.get("timing_s") if isinstance(artifact.get("timing_s"), dict) else {}
    io_pipeline = (
        artifact.get("resident_io_pipeline")
        if isinstance(artifact.get("resident_io_pipeline"), dict)
        else {}
    )
    io_overlap = (
        artifact.get("resident_io_overlap")
        if isinstance(artifact.get("resident_io_overlap"), dict)
        else {}
    )
    total_elapsed = _number(timing_payload.get("total_elapsed_s"))
    if total_elapsed is None:
        total_elapsed = _number(timing.get("total"))
    timing_row = {key: _number(timing.get(key)) for key in TIMING_KEYS}
    read_supply = _read_supply_from_artifact(timing, io_pipeline, io_overlap)
    for key, value in read_supply.items():
        if timing_row.get(key) is None:
            timing_row[key] = value
    return {
        "label": label,
        "run": str(root),
        "run_exists": root.exists(),
        "total_elapsed_s": total_elapsed,
        "timing_s": timing_row,
        "resident_io_pipeline": {key: io_pipeline.get(key) for key in IO_KEYS},
        "resident_io_overlap": _io_overlap_row(
            timing,
            io_pipeline,
            io_overlap,
            read_supply,
        ),
    }


def _delta(candidate: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    candidate_elapsed = _number(candidate.get("total_elapsed_s"))
    baseline_elapsed = _number(baseline.get("total_elapsed_s"))
    timing_delta: dict[str, Any] = {}
    for key in TIMING_KEYS:
        c_value = _number(candidate.get("timing_s", {}).get(key))
        b_value = _number(baseline.get("timing_s", {}).get(key))
        timing_delta[key] = {
            "candidate_s": c_value,
            "baseline_s": b_value,
            "delta_s": None if c_value is None or b_value is None else c_value - b_value,
            "ratio": None if c_value is None or b_value in (None, 0.0) else c_value / b_value,
        }
    return {
        "candidate_label": candidate["label"],
        "baseline_label": baseline["label"],
        "elapsed_delta_s": None
        if candidate_elapsed is None or baseline_elapsed is None
        else candidate_elapsed - baseline_elapsed,
        "elapsed_ratio": None
        if candidate_elapsed is None or baseline_elapsed in (None, 0.0)
        else candidate_elapsed / baseline_elapsed,
        "timing_delta": timing_delta,
    }


def _recommendation(rows: list[dict[str, Any]], comparisons: list[dict[str, Any]]) -> str:
    if not rows:
        return "no_runs"
    best = min(
        (row for row in rows if row.get("total_elapsed_s") is not None),
        key=lambda row: float(row["total_elapsed_s"]),
        default=None,
    )
    if best is None:
        return "missing_timing"
    slow_due_to_read_wait = any(
        (comparison.get("timing_delta", {}).get("light_read_wait_wall", {}).get("ratio") or 0.0) > 1.5
        for comparison in comparisons
    )
    slow_due_to_supply_wait = any(
        (
            comparison.get("timing_delta", {})
            .get("light_read_supply_consumer_wait_wall", {})
            .get("ratio")
            or 0.0
        )
        > 1.5
        for comparison in comparisons
    )
    if slow_due_to_read_wait or slow_due_to_supply_wait:
        return "repeat_with_warm_cache_or_dedicated_io_window"
    return f"best_observed:{best['label']}"


def build_resident_runtime_compare(
    runs: list[tuple[str, str | Path]],
    *,
    baseline_label: str | None = None,
) -> dict[str, Any]:
    rows = [_run_row(label, path) for label, path in runs]
    if baseline_label is None and rows:
        baseline = rows[0]
    else:
        matches = [row for row in rows if row["label"] == baseline_label]
        if not matches:
            raise ValueError(f"baseline label is not present in runs: {baseline_label}")
        baseline = matches[0]
    comparisons = [_delta(row, baseline) for row in rows if row is not baseline]
    ranked = sorted(
        rows,
        key=lambda row: (
            float("inf") if row.get("total_elapsed_s") is None else float(row["total_elapsed_s"]),
            row["label"],
        ),
    )
    return {
        "schema_version": 1,
        "artifact_type": "resident_runtime_compare",
        "created_at": now_iso(),
        "baseline_label": baseline["label"] if rows else None,
        "runs": rows,
        "ranked_runs": ranked,
        "comparisons": comparisons,
        "summary": {
            "run_count": len(rows),
            "best_label": ranked[0]["label"] if ranked else None,
            "best_elapsed_s": ranked[0].get("total_elapsed_s") if ranked else None,
            "recommendation": _recommendation(rows, comparisons),
        },
    }


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Resident Runtime Compare",
        "",
        f"- Baseline: `{payload.get('baseline_label')}`",
        f"- Best: `{payload.get('summary', {}).get('best_label')}`",
        f"- Recommendation: `{payload.get('summary', {}).get('recommendation')}`",
        "",
        "## Runs",
        "",
        "| rank | label | elapsed s | read wait s | supply worker s | supply hidden s | h2d+cal s | registration s | LN s | output s |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for rank, row in enumerate(payload.get("ranked_runs", []), start=1):
        timing = row.get("timing_s", {})
        lines.append(
            "| "
            f"{rank} | {row.get('label')} | {row.get('total_elapsed_s')} | "
            f"{timing.get('light_read_wait_wall')} | "
            f"{timing.get('light_read_supply_worker_cumulative')} | "
            f"{timing.get('light_read_supply_overlap_saved')} | "
            f"{timing.get('light_h2d_calibrate_store')} | {timing.get('resident_registration_warp')} | "
            f"{timing.get('resident_local_normalization')} | {timing.get('output_write')} |"
        )
    lines.extend(["", "## Comparisons", ""])
    for comparison in payload.get("comparisons", []):
        read_wait = comparison.get("timing_delta", {}).get("light_read_wait_wall", {})
        supply_worker = comparison.get("timing_delta", {}).get(
            "light_read_supply_worker_cumulative",
            {},
        )
        lines.append(
            "- "
            f"`{comparison.get('candidate_label')}` / `{comparison.get('baseline_label')}`: "
            f"elapsed ratio `{comparison.get('elapsed_ratio')}`, "
            f"read-wait ratio `{read_wait.get('ratio')}`, "
            f"supply-worker ratio `{supply_worker.get('ratio')}`"
        )
    lines.append("")
    return "\n".join(lines)


def write_resident_runtime_compare(
    out: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(out, payload)
    if markdown is not None:
        Path(markdown).write_text(_markdown(payload), encoding="utf-8")
