from __future__ import annotations

from pathlib import Path

import glass.cli as cli

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
        "frame_accounting.json",
    ):
        _touch_json(run, name)

    assert is_resident_run(run) is True
    assert cli.main(["resume", "--run", str(run)]) == 0

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

    assert cli.main(["resume", "--run", str(run)]) == 2

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


def test_resident_resume_reenters_from_stored_run_invocation(
    tmp_path: Path,
    monkeypatch,
) -> None:
    run = tmp_path / "resident_reenter"
    run.mkdir()
    plan = tmp_path / "processing_plan.json"
    write_json(plan, {"executable": True})
    _write_resident_timing(run, ["resident_reference_scout"])
    _touch_json(run, "resident_reference_scout.json")
    _write_resident_state(run)
    state = read_json(run / "run_state.json")
    state["current_stage"] = "resident_reference_scout"
    state["completed_stages"] = ["resident_reference_scout"]
    write_json(run / "run_state.json", state)
    argv = [
        "run",
        "--plan",
        str(plan),
        "--out",
        str(run),
        "--backend",
        "cuda",
        "--memory-mode",
        "resident",
    ]
    write_json(
        run / "run_invocation.json",
        {
            "schema_version": 1,
            "artifact_type": "run_invocation",
            "subcommand": "run",
            "argv": argv,
            "cwd": str(tmp_path),
        },
    )
    calls: list[list[str]] = []

    def fake_main(reentry_argv: list[str] | None = None) -> int:
        assert reentry_argv is not None
        calls.append(list(reentry_argv))
        _write_resident_timing(
            run,
            [
                "resident_reference_scout",
                "resident_calibration_integration",
            ],
        )
        for name in (
            "calibration_artifacts.json",
            "frame_quality.json",
            "integration_results.json",
            "registration_results.json",
            "resident_artifacts.json",
            "resident_result_contract.json",
            "frame_accounting.json",
        ):
            _touch_json(run, name)
        write_json(
            run / "run_state.json",
            {
                "run_id": run.name,
                "created_at": "2026-06-25T00:00:00+00:00",
                "current_stage": "integration",
                "completed_stages": ["resident_reference_scout", "resident_integration"],
                "failed_stage": None,
                "artifacts": [],
                "checksums": {},
                "warnings": [],
                "errors": [],
                "resume_supported": True,
            },
        )
        return 0

    monkeypatch.setattr(cli, "main", fake_main)

    assert cli.cmd_resume(type("Args", (), {"run": str(run)})()) == 0

    assert calls == [argv]
    reentry = read_json(run / "resident_resume_reentry.json")
    assert reentry["status"] == "passed"
    assert reentry["exit_code"] == 0
    preflight = read_json(run / "resident_resume_preflight.json")
    assert preflight["resume_action"] == "noop_complete"
    state = read_json(run / "run_state.json")
    assert "resident_resume" in state["completed_stages"]
    assert any(artifact["stage"] == "resident_resume_reentry" for artifact in state["artifacts"])
