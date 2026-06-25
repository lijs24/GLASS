from __future__ import annotations

from pathlib import Path

from glass.engine.resident_stage_ledger import build_resident_stage_ledger
from glass.io.json_io import write_json


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
