from __future__ import annotations

from dataclasses import is_dataclass
from pathlib import Path
from typing import Any

from glass.io.json_io import read_json, write_json
from glass.models import now_iso, to_jsonable


RESIDENT_STAGE_LEDGER_SCHEMA_VERSION = 1

RESIDENT_STAGE_ARTIFACTS: dict[str, tuple[str, ...]] = {
    "resident_reference_scout": ("resident_reference_scout.json",),
    "resident_reference_health": ("resident_reference_health.json",),
    "resident_reference_admission": ("resident_reference_admission.json",),
    "resident_memory_admission": ("resident_memory_admission.json",),
    "resident_source_dq_strategy": ("resident_source_dq_strategy.json",),
    "resident_source_dq_cache_calibration": ("calibration_artifacts.json",),
    "resident_calibration_integration": (
        "calibration_artifacts.json",
        "frame_quality.json",
        "integration_results.json",
        "registration_results.json",
        "resident_artifacts.json",
        "resident_result_contract.json",
    ),
    "resident_calibration": (
        "calibration_artifacts.json",
        "resident_calibration_contract.json",
    ),
    "resident_reentry_boundary": ("resident_reentry_boundary.json",),
    "resident_registration": (
        "registration_results.json",
        "resident_registration_quality.json",
    ),
    "resident_local_normalization": ("local_norm_results.json",),
    "resident_integration": (
        "integration_results.json",
        "resident_artifacts.json",
        "resident_result_contract.json",
        "frame_accounting.json",
    ),
    "resident_registration_health": ("resident_registration_health.json",),
    "local_norm_contract": ("local_norm_contract.json",),
    "pipeline_contract": ("pipeline_contract.json",),
    "stack_engine_contract": ("stack_engine_contract.json",),
    "warp_quality_contract": ("warp_quality_contract.json",),
    "resident_mainline_framework": ("resident_mainline_framework.json",),
}

RESIDENT_STAGE_ORDER: tuple[str, ...] = tuple(RESIDENT_STAGE_ARTIFACTS)


def _read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = read_json(path)
    return payload if isinstance(payload, dict) else {}


def _dict_from_state(state: Any, run: Path) -> dict[str, Any]:
    if state is None:
        return _read_json_if_exists(run / "run_state.json")
    if isinstance(state, dict):
        return state
    if is_dataclass(state):
        payload = to_jsonable(state)
        return payload if isinstance(payload, dict) else {}
    return {}


def _dict_from_timing(timing: Any, run: Path) -> dict[str, Any]:
    if timing is None:
        return _read_json_if_exists(run / "run_timing.json")
    return timing if isinstance(timing, dict) else {}


def _timing_by_stage(timing: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = timing.get("stages") if isinstance(timing.get("stages"), list) else []
    by_stage: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        stage = row.get("stage")
        if isinstance(stage, str) and stage:
            by_stage[stage] = row
    return by_stage


def _state_completed_stages(state: dict[str, Any]) -> set[str]:
    completed = state.get("completed_stages")
    if not isinstance(completed, list):
        return set()
    return {str(stage) for stage in completed if str(stage)}


def _artifact_rows(run: Path, stage: str, started: bool) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for relative_path in RESIDENT_STAGE_ARTIFACTS.get(stage, ()):
        path = run / relative_path
        rows.append(
            {
                "stage": stage,
                "path": str(path),
                "relative_path": relative_path,
                "exists": path.exists(),
                "required_for_resume": bool(started),
            }
        )
    return rows


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
    return any(stage.startswith("resident_") for stage in stages)


def build_resident_stage_ledger(
    run_dir: str | Path,
    *,
    state: Any = None,
    timing: dict[str, Any] | None = None,
) -> dict[str, Any]:
    run = Path(run_dir)
    state_payload = _dict_from_state(state, run)
    timing_payload = _dict_from_timing(timing, run)
    timing_rows = _timing_by_stage(timing_payload)
    completed_stages = _state_completed_stages(state_payload)
    failed_stage = state_payload.get("failed_stage")
    resident_run = (
        timing_payload.get("memory_mode") == "resident"
        or any(stage.startswith("resident_") for stage in timing_rows)
        or _state_mentions_resident(state_payload)
    )
    stage_names = list(RESIDENT_STAGE_ORDER)
    for stage in list(timing_rows) + sorted(completed_stages):
        if stage.startswith("resident_") and stage not in stage_names:
            stage_names.append(stage)

    stage_rows: list[dict[str, Any]] = []
    expected_artifacts: list[dict[str, Any]] = []
    missing_artifacts: list[dict[str, Any]] = []
    for index, stage in enumerate(stage_names):
        timing_row = timing_rows.get(stage, {})
        timing_status = timing_row.get("status")
        started = stage in completed_stages or stage in timing_rows
        artifacts = _artifact_rows(run, stage, started)
        required = [row for row in artifacts if row["required_for_resume"]]
        missing = [row for row in required if not row["exists"]]
        if failed_stage == stage or timing_status == "failed":
            status = "failed"
        elif started and missing:
            status = "incomplete"
        elif started:
            status = "complete"
        else:
            status = "not_started"
        resume_action = (
            "rerun_or_repair_required"
            if status in {"failed", "incomplete"}
            else "skip_if_requested"
            if status == "complete"
            else "not_started"
        )
        expected_artifacts.extend(required)
        missing_artifacts.extend(missing)
        stage_rows.append(
            {
                "order": index,
                "stage": stage,
                "status": status,
                "started": started,
                "completed_in_state": stage in completed_stages,
                "timing_status": timing_status,
                "elapsed_s": timing_row.get("elapsed_s"),
                "resume_action": resume_action,
                "expected_artifacts": artifacts,
                "missing_artifacts": missing,
            }
        )

    integration_complete = (run / "integration_results.json").exists() and (
        "resident_integration" in completed_stages
        or "resident_calibration_integration" in timing_rows
        or state_payload.get("current_stage") in {"integration", "report"}
        or "integration" in completed_stages
    )
    can_noop_resume = bool(
        resident_run
        and not failed_stage
        and integration_complete
        and not missing_artifacts
    )
    return {
        "schema_version": RESIDENT_STAGE_LEDGER_SCHEMA_VERSION,
        "artifact_type": "resident_stage_ledger",
        "created_at": now_iso(),
        "run": str(run),
        "resident_run": resident_run,
        "summary": {
            "stage_count": len(stage_rows),
            "started_stage_count": sum(1 for row in stage_rows if row["started"]),
            "complete_stage_count": sum(1 for row in stage_rows if row["status"] == "complete"),
            "incomplete_stage_count": sum(1 for row in stage_rows if row["status"] == "incomplete"),
            "failed_stage_count": sum(1 for row in stage_rows if row["status"] == "failed"),
            "expected_artifact_count": len(expected_artifacts),
            "missing_artifact_count": len(missing_artifacts),
            "integration_complete": integration_complete,
            "can_noop_resume": can_noop_resume,
            "failed_stage": failed_stage,
            "memory_mode": timing_payload.get("memory_mode"),
        },
        "stages": stage_rows,
        "expected_artifacts": expected_artifacts,
        "missing_artifacts": missing_artifacts,
    }


def write_resident_stage_ledger(
    run_dir: str | Path,
    *,
    state: Any = None,
    timing: dict[str, Any] | None = None,
) -> Path:
    run = Path(run_dir)
    path = run / "resident_stage_ledger.json"
    write_json(path, build_resident_stage_ledger(run, state=state, timing=timing))
    return path
