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
    "light_h2d_calibrate_store",
    "resident_registration_warp",
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
    total_elapsed = _number(timing_payload.get("total_elapsed_s"))
    if total_elapsed is None:
        total_elapsed = _number(timing.get("total"))
    return {
        "label": label,
        "run": str(root),
        "run_exists": root.exists(),
        "total_elapsed_s": total_elapsed,
        "timing_s": {key: _number(timing.get(key)) for key in TIMING_KEYS},
        "resident_io_pipeline": {key: io_pipeline.get(key) for key in IO_KEYS},
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
    if slow_due_to_read_wait:
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
        "| rank | label | elapsed s | read wait s | worker read s | h2d+cal s | registration s | output s |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for rank, row in enumerate(payload.get("ranked_runs", []), start=1):
        timing = row.get("timing_s", {})
        lines.append(
            "| "
            f"{rank} | {row.get('label')} | {row.get('total_elapsed_s')} | "
            f"{timing.get('light_read_wait_wall')} | {timing.get('light_read_worker_cumulative')} | "
            f"{timing.get('light_h2d_calibrate_store')} | {timing.get('resident_registration_warp')} | "
            f"{timing.get('output_write')} |"
        )
    lines.extend(["", "## Comparisons", ""])
    for comparison in payload.get("comparisons", []):
        read_wait = comparison.get("timing_delta", {}).get("light_read_wait_wall", {})
        lines.append(
            "- "
            f"`{comparison.get('candidate_label')}` / `{comparison.get('baseline_label')}`: "
            f"elapsed ratio `{comparison.get('elapsed_ratio')}`, "
            f"read-wait ratio `{read_wait.get('ratio')}`"
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
