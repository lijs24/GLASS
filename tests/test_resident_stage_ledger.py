from __future__ import annotations

from pathlib import Path

from glass import cli
from glass.engine.resident_stage_ledger import build_resident_stage_ledger
from glass.io.json_io import read_json, write_json


def _touch_json(run: Path, name: str) -> None:
    write_json(run / name, {"artifact": name})


def test_resident_stage_ledger_marks_started_stage_incomplete_when_artifact_missing(
    tmp_path: Path,
) -> None:
    run = tmp_path / "resident_missing_artifact"
    run.mkdir()
    write_json(
        run / "run_timing.json",
        {
            "schema_version": 1,
            "memory_mode": "resident",
            "stages": [
                {
                    "stage": "resident_calibration_integration",
                    "status": "ok",
                    "elapsed_s": 1.0,
                }
            ],
        },
    )
    write_json(
        run / "run_state.json",
        {
            "run_id": run.name,
            "created_at": "2026-06-25T00:00:00+00:00",
            "current_stage": "integration",
            "completed_stages": [],
            "failed_stage": None,
            "artifacts": [],
            "checksums": {},
            "warnings": [],
            "errors": [],
            "resume_supported": True,
        },
    )
    for name in (
        "calibration_artifacts.json",
        "integration_results.json",
        "registration_results.json",
        "resident_artifacts.json",
        "resident_result_contract.json",
    ):
        _touch_json(run, name)

    ledger = build_resident_stage_ledger(run)

    assert ledger["resident_run"] is True
    assert ledger["summary"]["missing_artifact_count"] == 1
    assert ledger["summary"]["can_noop_resume"] is False
    missing_paths = {Path(row["path"]).name for row in ledger["missing_artifacts"]}
    assert missing_paths == {"frame_quality.json"}
    stages = {row["stage"]: row for row in ledger["stages"]}
    assert stages["resident_calibration_integration"]["status"] == "incomplete"


def test_resident_stage_ledger_does_not_start_stage_from_overlapping_artifact_only(
    tmp_path: Path,
) -> None:
    run = tmp_path / "resident_overlap"
    run.mkdir()
    write_json(
        run / "run_timing.json",
        {
            "schema_version": 1,
            "memory_mode": "resident",
            "stages": [],
        },
    )
    write_json(
        run / "run_state.json",
        {
            "run_id": run.name,
            "created_at": "2026-06-25T00:00:00+00:00",
            "current_stage": "created",
            "completed_stages": [],
            "failed_stage": None,
            "artifacts": [],
            "checksums": {},
            "warnings": [],
            "errors": [],
            "resume_supported": True,
        },
    )
    _touch_json(run, "calibration_artifacts.json")

    ledger = build_resident_stage_ledger(run)

    stages = {row["stage"]: row for row in ledger["stages"]}
    assert stages["resident_calibration"]["status"] == "not_started"
    assert stages["resident_calibration_integration"]["status"] == "not_started"
    assert ledger["summary"]["missing_artifact_count"] == 0


def test_resident_stage_ledger_canonicalizes_light_calibration_component(
    tmp_path: Path,
) -> None:
    run = tmp_path / "resident_component_alias"
    run.mkdir()
    write_json(
        run / "run_timing.json",
        {
            "schema_version": 1,
            "memory_mode": "resident",
            "stages": [],
        },
    )
    write_json(
        run / "run_state.json",
        {
            "run_id": run.name,
            "created_at": "2026-06-25T00:00:00+00:00",
            "current_stage": "integration",
            "completed_stages": ["resident_light_calibration"],
            "failed_stage": None,
            "artifacts": [
                {"stage": "resident_calibration", "path": str(run / "calibration_artifacts.json")},
                {
                    "stage": "resident_calibration_contract",
                    "path": str(run / "resident_calibration_contract.json"),
                },
            ],
            "checksums": {},
            "warnings": [],
            "errors": [],
            "resume_supported": True,
        },
    )
    _touch_json(run, "calibration_artifacts.json")
    _touch_json(run, "resident_calibration_contract.json")

    ledger = build_resident_stage_ledger(run)

    stages = {row["stage"]: row for row in ledger["stages"]}
    assert "resident_light_calibration" not in stages
    assert "resident_calibration_contract" not in stages
    assert stages["resident_calibration"]["status"] == "complete"
    assert stages["resident_calibration"]["completed_in_state"] is True
    expected_paths = {
        Path(row["path"]).name for row in stages["resident_calibration"]["expected_artifacts"]
    }
    assert expected_paths == {"calibration_artifacts.json", "resident_calibration_contract.json"}


def test_resident_stage_ledger_cli_writes_component_ledger(tmp_path: Path) -> None:
    run = tmp_path / "resident_component_cli"
    run.mkdir()
    write_json(
        run / "run_timing.json",
        {
            "schema_version": 1,
            "memory_mode": "resident",
            "stages": [],
        },
    )
    write_json(
        run / "run_state.json",
        {
            "run_id": run.name,
            "created_at": "2026-06-25T00:00:00+00:00",
            "current_stage": "integration",
            "completed_stages": ["resident_light_calibration"],
            "failed_stage": None,
            "artifacts": [
                {"stage": "resident_calibration", "path": str(run / "calibration_artifacts.json")},
                {
                    "stage": "resident_calibration_contract",
                    "path": str(run / "resident_calibration_contract.json"),
                },
            ],
            "checksums": {},
            "warnings": [],
            "errors": [],
            "resume_supported": True,
        },
    )
    _touch_json(run, "calibration_artifacts.json")
    _touch_json(run, "resident_calibration_contract.json")
    out = tmp_path / "component_ledger.json"

    assert (
        cli.cmd_resident_stage_ledger(
            type(
                "Args",
                (),
                {"run": str(run), "out": str(out), "fail_on_missing": True},
            )()
        )
        == 0
    )

    payload = read_json(out)
    stages = {row["stage"]: row for row in payload["stages"]}
    assert payload["summary"]["missing_artifact_count"] == 0
    assert stages["resident_calibration"]["status"] == "complete"
    assert "resident_light_calibration" not in stages
