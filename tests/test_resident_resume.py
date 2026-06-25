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


def _write_ready_calibration_boundary(run: Path) -> None:
    cache = run / "calib_cache" / "resident_masters"
    cache.mkdir(parents=True, exist_ok=True)
    cache_key = "H_24x24_bias-B_dark-D_flat-F_abc123"
    for suffix in ["master_stats.json", "master_bias.npy", "master_dark.npy", "master_flat.npy"]:
        (cache / f"{cache_key}_{suffix}").write_bytes(b"fixture")
    stats = {"min": 1.0, "max": 2.0, "mean": 1.5, "median": 1.5, "std": 0.1}
    write_json(
        run / "resident_master_cache.json",
        {
            "schema_version": 1,
            "artifact": "resident_master_cache",
            "summary": {
                "passed": True,
                "set_count": 1,
                "cache_hit_count": 1,
                "cache_miss_count": 0,
                "complete_set_count": 1,
                "incomplete_set_count": 0,
                "failed_group_count": 0,
                "total_required_bytes": 4,
            },
            "groups": [{"filter": "H", "passed": True, "missing_required_files": []}],
        },
    )
    write_json(
        run / "resident_calibration_contract.json",
        {
            "schema_version": 1,
            "artifact_type": "resident_cuda_calibration_contract",
            "status": "passed",
            "passed": True,
            "output_count": 1,
            "outputs": [{"index": 0, "passed": True, "frame_count": 2}],
        },
    )
    write_json(
        run / "calibration_artifacts.json",
        {
            "schema_version": 1,
            "artifact_type": "resident_cuda_calibration_artifacts",
            "backend": "cuda_resident_stack",
            "memory_mode": "resident",
            "masters": {
                "resident_bias_H": {
                    "path": str(cache / f"{cache_key}_master_bias.npy"),
                    "resident_calibration_contract": {"passed": True},
                    "stats": stats,
                }
            },
            "calibrated_lights": [
                {"frame_id": "L1", "status": "resident_in_vram", "dq_contract_ok": True}
            ],
        },
    )


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


def test_resident_resume_reenters_from_calibration_boundary(
    tmp_path: Path,
    monkeypatch,
) -> None:
    run = tmp_path / "resident_calibration_reenter"
    run.mkdir()
    plan = tmp_path / "processing_plan.json"
    write_json(plan, {"executable": True})
    _write_ready_calibration_boundary(run)
    _write_resident_timing(run, ["resident_calibration_integration"])
    write_json(
        run / "run_state.json",
        {
            "run_id": run.name,
            "created_at": "2026-06-25T00:00:00+00:00",
            "current_stage": "resident_calibration_integration",
            "completed_stages": [],
            "failed_stage": None,
            "artifacts": [],
            "checksums": {},
            "warnings": [],
            "errors": [],
            "resume_supported": True,
        },
    )
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
        _write_resident_timing(run, ["resident_calibration_integration"])
        for name in (
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
                "completed_stages": ["resident_integration"],
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
    assert reentry["preflight_action"] == "reenter_from_calibration_boundary"
    assert reentry["boundary_name"] == "resident_calibration"
    preflight = read_json(run / "resident_resume_preflight.json")
    assert preflight["resume_action"] == "noop_complete"
    state = read_json(run / "run_state.json")
    assert "resident_resume" in state["completed_stages"]
    assert any(artifact["stage"] == "resident_resume_reentry" for artifact in state["artifacts"])
