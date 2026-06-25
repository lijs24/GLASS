from __future__ import annotations

from pathlib import Path
from typing import Any

from glass.io.json_io import read_json, write_json
from glass.models import now_iso


RESIDENT_COMPONENT_TIMING_SCHEMA_VERSION = 1

RESIDENT_COMPONENT_TIMING_KEYS: tuple[tuple[str, str], ...] = (
    ("light_read_upload_calibrate", "resident_light_read_upload_calibrate"),
    ("resident_registration_warp", "resident_registration_warp"),
    ("resident_local_normalization", "resident_local_normalization"),
    ("resident_integration", "resident_integration"),
    ("output_write", "resident_output_write"),
)

REQUIRED_RESIDENT_COMPONENT_TIMING_KEYS: tuple[str, ...] = (
    "light_read_upload_calibrate",
    "resident_registration_warp",
    "resident_integration",
)


def _json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = read_json(path)
    return payload if isinstance(payload, dict) else {}


def _number(value: Any) -> float | None:
    try:
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None


def _first_resident_artifact(payload: dict[str, Any]) -> dict[str, Any]:
    artifacts = payload.get("artifacts") if isinstance(payload.get("artifacts"), list) else []
    first = artifacts[0] if artifacts else {}
    return first if isinstance(first, dict) else {}


def build_resident_component_timing(
    run_dir: str | Path,
    *,
    timing: dict[str, Any] | None = None,
    resident_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    run = Path(run_dir)
    timing_payload = timing if isinstance(timing, dict) else _json_object(run / "run_timing.json")
    resident = (
        resident_payload
        if isinstance(resident_payload, dict)
        else _json_object(run / "resident_artifacts.json")
    )
    artifact = _first_resident_artifact(resident)
    timing_s = artifact.get("timing_s") if isinstance(artifact.get("timing_s"), dict) else {}

    rows: list[dict[str, Any]] = []
    for source_key, component in RESIDENT_COMPONENT_TIMING_KEYS:
        elapsed_s = _number(timing_s.get(source_key))
        required = source_key in REQUIRED_RESIDENT_COMPONENT_TIMING_KEYS
        rows.append(
            {
                "component": component,
                "source_key": source_key,
                "elapsed_s": elapsed_s,
                "status": "ok" if elapsed_s is not None else "missing",
                "required": required,
                "source_artifact": str(run / "resident_artifacts.json"),
            }
        )

    present_rows = [row for row in rows if row["elapsed_s"] is not None]
    missing_required = [
        str(row["source_key"]) for row in rows if row["required"] and row["elapsed_s"] is None
    ]
    largest = max(
        ((str(row["component"]), float(row["elapsed_s"])) for row in present_rows),
        key=lambda item: item[1],
        default=(None, None),
    )
    resident_stage_elapsed = None
    for row in timing_payload.get("stages") or []:
        if isinstance(row, dict) and row.get("stage") == "resident_calibration_integration":
            resident_stage_elapsed = _number(row.get("elapsed_s"))
            break

    passed = not missing_required and bool(present_rows)
    return {
        "schema_version": RESIDENT_COMPONENT_TIMING_SCHEMA_VERSION,
        "artifact_type": "resident_component_timing",
        "created_at": now_iso(),
        "run": str(run),
        "status": "passed" if passed else "failed",
        "passed": passed,
        "source": {
            "resident_artifacts_path": str(run / "resident_artifacts.json"),
            "run_timing_path": str(run / "run_timing.json"),
            "resident_artifacts_exists": (run / "resident_artifacts.json").exists(),
            "run_timing_exists": (run / "run_timing.json").exists(),
        },
        "summary": {
            "component_count": len(rows),
            "present_component_count": len(present_rows),
            "missing_component_count": len(rows) - len(present_rows),
            "required_component_count": len(REQUIRED_RESIDENT_COMPONENT_TIMING_KEYS),
            "missing_required_components": missing_required,
            "total_component_elapsed_s": sum(float(row["elapsed_s"]) for row in present_rows),
            "resident_calibration_integration_elapsed_s": resident_stage_elapsed,
            "largest_component": largest,
        },
        "components": rows,
    }


def materialize_resident_component_timing(
    timing: dict[str, Any],
    component_payload: dict[str, Any],
) -> dict[str, Any]:
    rows = (
        component_payload.get("components")
        if isinstance(component_payload.get("components"), list)
        else []
    )
    component_stages: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        component = row.get("component")
        source_key = row.get("source_key")
        elapsed_s = _number(row.get("elapsed_s"))
        if not isinstance(component, str) or not component:
            continue
        component_stages.append(
            {
                "component": component,
                "source_key": source_key,
                "elapsed_s": elapsed_s,
                "status": row.get("status") or ("ok" if elapsed_s is not None else "missing"),
                "required": bool(row.get("required")),
                "source_stage": "resident_calibration_integration",
                "source_artifact": "resident_artifacts.json",
            }
        )
    timing["resident_component_stages"] = component_stages
    summary = component_payload.get("summary")
    if isinstance(summary, dict):
        timing["resident_component_timing_summary"] = summary
    timing["resident_component_timing_path"] = "resident_component_timing.json"
    return timing


def write_resident_component_timing(
    run_dir: str | Path,
    *,
    timing: dict[str, Any] | None = None,
    resident_payload: dict[str, Any] | None = None,
) -> Path:
    run = Path(run_dir)
    path = run / "resident_component_timing.json"
    write_json(path, build_resident_component_timing(run, timing=timing, resident_payload=resident_payload))
    return path
