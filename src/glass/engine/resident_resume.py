from __future__ import annotations

from pathlib import Path
from typing import Any

from glass.io.json_io import read_json, write_json
from glass.engine.resident_stage_ledger import (
    build_resident_stage_ledger,
    write_resident_stage_ledger,
)
from glass.engine.resident_reentry_boundary import (
    build_resident_reentry_boundary,
    write_resident_reentry_boundary,
)
from glass.models import now_iso


RESIDENT_RESUME_PREFLIGHT_SCHEMA_VERSION = 1


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


def _resident_stage_started(ledger: dict[str, Any], stage: str) -> bool:
    rows = ledger.get("stages") if isinstance(ledger.get("stages"), list) else []
    for row in rows:
        if isinstance(row, dict) and row.get("stage") == stage:
            return bool(row.get("started"))
    return False


def _run_invocation(run: Path) -> dict[str, Any]:
    invocation = _read_json_if_exists(run / "run_invocation.json")
    argv = invocation.get("argv") if isinstance(invocation.get("argv"), list) else []
    return {
        "path": str(run / "run_invocation.json"),
        "exists": (run / "run_invocation.json").exists(),
        "subcommand": invocation.get("subcommand"),
        "argv": [str(item) for item in argv],
        "cwd": str(invocation.get("cwd") or ""),
    }


def _argv_option_value(argv: list[str], flag: str) -> str | None:
    for index, token in enumerate(argv):
        if token == flag and index + 1 < len(argv):
            return argv[index + 1]
        prefix = f"{flag}="
        if token.startswith(prefix):
            return token[len(prefix) :]
    return None


def _resident_reentry_candidate(run: Path, ledger: dict[str, Any], failed_stage: Any) -> dict[str, Any]:
    invocation = _run_invocation(run)
    argv = invocation["argv"] if isinstance(invocation.get("argv"), list) else []
    out_arg = _argv_option_value(argv, "--out")
    invocation_cwd = Path(str(invocation.get("cwd") or Path.cwd()))
    out_path = None if out_arg is None else Path(str(out_arg))
    resolved_out = None if out_path is None else (out_path if out_path.is_absolute() else invocation_cwd / out_path)
    integration_started = _resident_stage_started(ledger, "resident_calibration_integration")
    eligible = bool(
        invocation.get("exists")
        and invocation.get("subcommand") == "run"
        and not failed_stage
        and not integration_started
        and out_arg is not None
        and resolved_out is not None
        and resolved_out.resolve() == run.resolve()
    )
    reasons: list[str] = []
    if not invocation.get("exists"):
        reasons.append("missing_run_invocation")
    if invocation.get("subcommand") != "run":
        reasons.append("run_invocation_not_run")
    if failed_stage:
        reasons.append(f"run_state_failed_stage:{failed_stage}")
    if integration_started:
        reasons.append("resident_calibration_integration_already_started")
    if out_arg is None:
        reasons.append("run_invocation_missing_out")
    elif resolved_out is None or resolved_out.resolve() != run.resolve():
        reasons.append("run_invocation_out_mismatch")
    return {
        "eligible": eligible,
        "action": "reenter_from_run_invocation" if eligible else "blocked",
        "reasons": reasons,
        "invocation": invocation,
        "resident_calibration_integration_started": integration_started,
    }


def _boundary_by_name(boundary: dict[str, Any], name: str) -> dict[str, Any]:
    rows = boundary.get("boundaries") if isinstance(boundary.get("boundaries"), list) else []
    for row in rows:
        if isinstance(row, dict) and row.get("name") == name:
            return row
    return {}


def _resident_boundary_reentry_candidate(
    run: Path,
    boundary: dict[str, Any],
    failed_stage: Any,
) -> dict[str, Any]:
    summary = boundary.get("summary") if isinstance(boundary.get("summary"), dict) else {}
    boundary_name = summary.get("strongest_supported_boundary")
    if boundary_name not in {"resident_calibration", "resident_master_cache"}:
        boundary_name = None
    boundary_row = _boundary_by_name(boundary, str(boundary_name)) if boundary_name else {}
    invocation = _run_invocation(run)
    argv = invocation["argv"] if isinstance(invocation.get("argv"), list) else []
    out_arg = _argv_option_value(argv, "--out")
    invocation_cwd = Path(str(invocation.get("cwd") or Path.cwd()))
    out_path = None if out_arg is None else Path(str(out_arg))
    resolved_out = None if out_path is None else (out_path if out_path.is_absolute() else invocation_cwd / out_path)
    out_matches = bool(resolved_out is not None and resolved_out.resolve() == run.resolve())
    eligible = bool(
        boundary_name
        and boundary_row.get("resume_supported") is True
        and invocation.get("exists")
        and invocation.get("subcommand") == "run"
        and not failed_stage
        and out_matches
    )
    reasons: list[str] = []
    if not boundary_name:
        reasons.append("no_supported_resident_boundary")
    elif boundary_row.get("resume_supported") is not True:
        reasons.append(f"{boundary_name}_not_resume_supported")
    if not invocation.get("exists"):
        reasons.append("missing_run_invocation")
    if invocation.get("subcommand") != "run":
        reasons.append("run_invocation_not_run")
    if failed_stage:
        reasons.append(f"run_state_failed_stage:{failed_stage}")
    if out_arg is None:
        reasons.append("run_invocation_missing_out")
    elif not out_matches:
        reasons.append("run_invocation_out_mismatch")
    action = (
        "reenter_from_calibration_boundary"
        if boundary_name == "resident_calibration"
        else "reenter_from_master_cache_boundary"
        if boundary_name == "resident_master_cache"
        else "blocked"
    )
    return {
        "eligible": eligible,
        "action": action if eligible else "blocked",
        "reasons": reasons,
        "boundary_name": boundary_name,
        "boundary_action": boundary_row.get("resume_action"),
        "invocation": invocation,
    }


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
    state = _read_json_if_exists(run / "run_state.json")
    ledger = build_resident_stage_ledger(run)
    boundary = build_resident_reentry_boundary(run)
    boundary_summary = (
        boundary.get("summary") if isinstance(boundary.get("summary"), dict) else {}
    )
    summary = ledger.get("summary") if isinstance(ledger.get("summary"), dict) else {}
    resident = is_resident_run(run)
    expected_rows = (
        list(ledger.get("expected_artifacts"))
        if isinstance(ledger.get("expected_artifacts"), list)
        else []
    )
    missing = (
        list(ledger.get("missing_artifacts"))
        if isinstance(ledger.get("missing_artifacts"), list)
        else []
    )
    integration_complete = bool(summary.get("integration_complete"))
    failed_stage = state.get("failed_stage")
    reentry = _resident_reentry_candidate(run, ledger, failed_stage)
    boundary_reentry = _resident_boundary_reentry_candidate(run, boundary, failed_stage)
    if not resident:
        action = "not_resident_run"
        passed = True
        reason = "run is not a resident CUDA run"
    elif failed_stage:
        action = "blocked_failed_resident_run"
        passed = False
        reason = f"run_state failed_stage is {failed_stage}"
    elif not integration_complete and reentry["eligible"]:
        action = "reenter_from_run_invocation"
        passed = True
        reason = "resident CUDA run can re-enter from stored run invocation before calibration/integration started"
    elif (
        not integration_complete
        and _resident_stage_started(ledger, "resident_calibration_integration")
        and boundary_reentry["eligible"]
    ):
        action = str(boundary_reentry["action"])
        passed = True
        reason = (
            "resident CUDA run can re-enter from the ready "
            f"{boundary_reentry['boundary_name']} boundary using stored run invocation"
        )
    elif (
        not integration_complete
        and _resident_stage_started(ledger, "resident_calibration_integration")
        and bool(boundary_summary.get("calibration_boundary_ready"))
    ):
        action = "blocked_calibration_boundary_reentry_unavailable"
        passed = False
        reason = (
            "resident CUDA calibration/master-cache boundary is ready, but "
            "calibration-boundary reentry is unavailable for this run"
        )
    elif (
        not integration_complete
        and _resident_stage_started(ledger, "resident_calibration_integration")
        and bool(boundary_summary.get("master_cache_boundary_ready"))
    ):
        action = "blocked_master_cache_reentry_unavailable"
        passed = False
        reason = (
            "resident CUDA master-cache boundary is ready, but master-cache "
            "reentry is unavailable for this run"
        )
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
            "completed_stage_count": int(summary.get("complete_stage_count") or 0),
            "started_stage_count": int(summary.get("started_stage_count") or 0),
            "expected_artifact_count": len(expected_rows),
            "missing_artifact_count": len(missing),
            "integration_complete": integration_complete,
            "failed_stage": failed_stage,
            "memory_mode": summary.get("memory_mode"),
            "stage_ledger_can_noop_resume": bool(summary.get("can_noop_resume")),
            "reentry_eligible": bool(reentry.get("eligible")),
            "strongest_ready_boundary": boundary_summary.get("strongest_ready_boundary"),
            "calibration_boundary_ready": bool(
                boundary_summary.get("calibration_boundary_ready")
            ),
            "calibration_boundary_resume_supported": bool(
                boundary_summary.get("calibration_boundary_resume_supported")
            ),
            "boundary_reentry_eligible": bool(boundary_reentry.get("eligible")),
            "boundary_reentry_name": boundary_reentry.get("boundary_name"),
        },
        "reentry": reentry,
        "boundary_reentry": boundary_reentry,
        "resident_reentry_boundary": {
            "path": str(run / "resident_reentry_boundary.json"),
            "summary": boundary_summary,
        },
        "stage_ledger": {
            "path": str(run / "resident_stage_ledger.json"),
            "summary": summary,
        },
        "completed_stages_from_timing": [
            str(row.get("stage"))
            for row in ledger.get("stages", [])
            if isinstance(row, dict) and row.get("timing_status") == "ok"
        ],
        "expected_artifacts": expected_rows,
        "missing_artifacts": missing,
    }


def write_resident_resume_preflight(run_dir: str | Path) -> Path:
    run = Path(run_dir)
    write_resident_reentry_boundary(run)
    write_resident_stage_ledger(run)
    path = run / "resident_resume_preflight.json"
    write_json(path, build_resident_resume_preflight(run))
    return path
