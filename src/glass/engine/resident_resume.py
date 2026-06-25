from __future__ import annotations

from pathlib import Path
from typing import Any

from glass.io.json_io import read_json, write_json
from glass.models import now_iso


RESIDENT_RESUME_PREFLIGHT_SCHEMA_VERSION = 1

_STAGE_OUTPUTS: dict[str, tuple[str, ...]] = {
    "resident_reference_scout": ("resident_reference_scout.json",),
    "resident_reference_health": ("resident_reference_health.json",),
    "resident_reference_admission": ("resident_reference_admission.json",),
    "resident_memory_admission": ("resident_memory_admission.json",),
    "resident_calibration_integration": (
        "calibration_artifacts.json",
        "frame_quality.json",
        "integration_results.json",
        "registration_results.json",
        "resident_artifacts.json",
        "resident_result_contract.json",
    ),
    "resident_registration_health": ("resident_registration_health.json",),
    "local_norm_contract": ("local_norm_contract.json",),
    "pipeline_contract": ("pipeline_contract.json",),
    "stack_engine_contract": ("stack_engine_contract.json",),
    "warp_quality_contract": ("warp_quality_contract.json",),
    "resident_mainline_framework": ("resident_mainline_framework.json",),
}


def _read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = read_json(path)
    return payload if isinstance(payload, dict) else {}


def _stage_names_from_timing(timing: dict[str, Any]) -> list[str]:
    stages = timing.get("stages") if isinstance(timing.get("stages"), list) else []
    names: list[str] = []
    for row in stages:
        if not isinstance(row, dict):
            continue
        if row.get("status") != "ok":
            continue
        stage = row.get("stage")
        if isinstance(stage, str) and stage:
            names.append(stage)
    return names


def _state_mentions_resident(state: dict[str, Any]) -> bool:
    stages: list[str] = []
    for key in ("current_stage", "failed_stage"):
        value = state.get(key)
        if isinstance(value, str):
            stages.append(value)
    completed = state.get("completed_stages")
    if isinstance(completed, list):
        stages.extend(str(item) for item in completed)
    artifacts = state.get("artifacts")
    if isinstance(artifacts, list):
        for artifact in artifacts:
            if isinstance(artifact, dict):
                stages.append(str(artifact.get("stage") or ""))
    return any(stage.startswith("resident_") or stage == "resident_calibration_integration" for stage in stages)


def is_resident_run(run_dir: str | Path) -> bool:
    run = Path(run_dir)
    timing = _read_json_if_exists(run / "run_timing.json")
    if timing.get("memory_mode") == "resident":
        return True
    if any(str(stage).startswith("resident_") for stage in _stage_names_from_timing(timing)):
        return True
    state = _read_json_if_exists(run / "run_state.json")
    return _state_mentions_resident(state)


def build_resident_resume_preflight(run_dir: str | Path) -> dict[str, Any]:
    run = Path(run_dir)
    timing = _read_json_if_exists(run / "run_timing.json")
    state = _read_json_if_exists(run / "run_state.json")
    resident = is_resident_run(run)
    completed_stage_names = _stage_names_from_timing(timing)
    expected_rows: list[dict[str, Any]] = []
    for stage in completed_stage_names:
        for relative_path in _STAGE_OUTPUTS.get(stage, ()):
            path = run / relative_path
            expected_rows.append(
                {
                    "stage": stage,
                    "path": str(path),
                    "exists": path.exists(),
                    "required_for_resume": True,
                }
            )
    missing = [row for row in expected_rows if not row["exists"]]
    integration_complete = (run / "integration_results.json").exists() and (
        "resident_calibration_integration" in completed_stage_names
        or state.get("current_stage") in {"integration", "report"}
        or "integration" in state.get("completed_stages", [])
    )
    failed_stage = state.get("failed_stage")
    if not resident:
        action = "not_resident_run"
        passed = True
        reason = "run is not a resident CUDA run"
    elif failed_stage:
        action = "blocked_failed_resident_run"
        passed = False
        reason = f"run_state failed_stage is {failed_stage}"
    elif not integration_complete:
        action = "blocked_incomplete_resident_run"
        passed = False
        reason = "resident CUDA run is incomplete; CPU/tile resume fallback is not safe"
    elif missing:
        action = "blocked_missing_resident_artifacts"
        passed = False
        reason = "completed resident stages are missing required artifacts"
    else:
        action = "noop_complete"
        passed = True
        reason = "resident CUDA run already has complete integration artifacts"
    return {
        "schema_version": RESIDENT_RESUME_PREFLIGHT_SCHEMA_VERSION,
        "artifact_type": "resident_resume_preflight",
        "created_at": now_iso(),
        "run": str(run),
        "resident_run": resident,
        "passed": passed,
        "resume_action": action,
        "reason": reason,
        "summary": {
            "completed_stage_count": len(completed_stage_names),
            "expected_artifact_count": len(expected_rows),
            "missing_artifact_count": len(missing),
            "integration_complete": integration_complete,
            "failed_stage": failed_stage,
            "memory_mode": timing.get("memory_mode"),
        },
        "completed_stages_from_timing": completed_stage_names,
        "expected_artifacts": expected_rows,
        "missing_artifacts": missing,
    }


def write_resident_resume_preflight(run_dir: str | Path) -> Path:
    run = Path(run_dir)
    path = run / "resident_resume_preflight.json"
    write_json(path, build_resident_resume_preflight(run))
    return path

