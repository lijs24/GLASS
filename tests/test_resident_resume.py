from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.engine.resident_resume import is_resident_run
from glass.io.json_io import read_json, write_json


def _write_resident_timing(run: Path, stages: list[str]) -> None:
    write_json(
        run / "run_timing.json",
        {
            "schema_version": 1,
            "command": "run",
            "backend": "cuda",
            "memory_mode": "resident",
            "stages": [{"stage": stage, "status": "ok", "elapsed_s": 0.01} for stage in stages],
        },
    )


def _write_resident_state(run: Path) -> None:
    write_json(
        run / "run_state.json",
        {
            "run_id": run.name,
            "created_at": "2026-06-25T00:00:00+00:00",
            "current_stage": "report",
            "completed_stages": ["resident_calibration_integration", "integration"],
            "failed_stage": None,
            "artifacts": [],
            "checksums": {},
            "warnings": [],
            "errors": [],
            "resume_supported": True,
        },
    )


def _touch_json(run: Path, name: str) -> None:
    write_json(run / name, {"artifact": name})


def test_resident_resume_completed_run_noops_after_preflight(tmp_path: Path) -> None:
    run = tmp_path / "resident_complete"
    run.mkdir()
    _write_resident_timing(run, ["resident_calibration_integration"])
    _write_resident_state(run)
    for name in (
        "calibration_artifacts.json",
        "frame_quality.json",
        "integration_results.json",
        "registration_results.json",
        "resident_artifacts.json",
        "resident_result_contract.json",
    ):
        _touch_json(run, name)

    assert is_resident_run(run) is True
    assert main(["resume", "--run", str(run)]) == 0

    preflight = read_json(run / "resident_resume_preflight.json")
    assert preflight["passed"] is True
    assert preflight["resume_action"] == "noop_complete"
    assert preflight["summary"]["missing_artifact_count"] == 0
    assert preflight["summary"]["integration_complete"] is True
    assert preflight["summary"]["stage_ledger_can_noop_resume"] is True
    assert preflight["stage_ledger"]["path"] == str(run / "resident_stage_ledger.json")
    ledger = read_json(run / "resident_stage_ledger.json")
    assert ledger["summary"]["can_noop_resume"] is True
    state = read_json(run / "run_state.json")
    assert "resident_resume" in state["completed_stages"]
    assert any(artifact["stage"] == "resident_stage_ledger" for artifact in state["artifacts"])
    assert any(artifact["stage"] == "resident_resume" for artifact in state["artifacts"])


def test_resident_resume_incomplete_run_blocks_cpu_fallback(tmp_path: Path) -> None:
    run = tmp_path / "resident_incomplete"
    run.mkdir()
    _write_resident_timing(run, ["resident_reference_scout"])
    _touch_json(run, "resident_reference_scout.json")
    write_json(run / "processing_plan.json", {"executable": True})

    assert main(["resume", "--run", str(run)]) == 2

    preflight = read_json(run / "resident_resume_preflight.json")
    assert preflight["passed"] is False
    assert preflight["resume_action"] == "blocked_incomplete_resident_run"
    assert preflight["stage_ledger"]["path"] == str(run / "resident_stage_ledger.json")
    assert not (run / "calib_cache").exists()
    state = read_json(run / "run_state.json")
    assert state["failed_stage"] == "resident_resume"
    assert state["resume_supported"] is False
    assert any(artifact["stage"] == "resident_stage_ledger" for artifact in state["artifacts"])
    assert any("CPU/tile resume fallback is not safe" in error for error in state["errors"])
