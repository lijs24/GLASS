from __future__ import annotations

from pathlib import Path

from glass.engine.resident_component_timing import (
    build_resident_component_timing,
    materialize_resident_component_timing,
    write_resident_component_timing,
)
from glass.io.json_io import read_json, write_json


def _write_resident_inputs(run: Path) -> dict:
    timing = {
        "memory_mode": "resident",
        "stages": [
            {
                "stage": "resident_calibration_integration",
                "elapsed_s": 9.0,
                "status": "ok",
            }
        ],
    }
    write_json(run / "run_timing.json", timing)
    write_json(
        run / "resident_artifacts.json",
        {
            "artifacts": [
                {
                    "timing_s": {
                        "light_read_upload_calibrate": 3.1,
                        "resident_registration_warp": 0.27,
                        "resident_local_normalization": 0.41,
                        "resident_integration": 3.28,
                        "output_write": 0.25,
                    }
                }
            ]
        },
    )
    return timing


def test_resident_component_timing_extracts_required_components(tmp_path: Path) -> None:
    run = tmp_path / "run"
    run.mkdir()
    _write_resident_inputs(run)

    payload = build_resident_component_timing(run)

    assert payload["passed"] is True
    assert payload["summary"]["missing_required_components"] == []
    assert payload["summary"]["present_component_count"] == 5
    components = {row["source_key"]: row for row in payload["components"]}
    assert components["light_read_upload_calibrate"]["elapsed_s"] == 3.1
    assert components["resident_integration"]["required"] is True
    assert components["output_write"]["required"] is False


def test_resident_component_timing_materializes_run_timing(tmp_path: Path) -> None:
    run = tmp_path / "run"
    run.mkdir()
    timing = _write_resident_inputs(run)

    path = write_resident_component_timing(run, timing=timing)
    payload = read_json(path)
    materialize_resident_component_timing(timing, payload)
    materialize_resident_component_timing(timing, payload)

    assert timing["resident_component_timing_path"] == "resident_component_timing.json"
    assert len(timing["resident_component_stages"]) == 5
    assert timing["resident_component_stages"][0] == {
        "component": "resident_light_read_upload_calibrate",
        "source_key": "light_read_upload_calibrate",
        "elapsed_s": 3.1,
        "status": "ok",
        "required": True,
        "source_stage": "resident_calibration_integration",
        "source_artifact": "resident_artifacts.json",
    }


def test_resident_component_timing_fails_when_core_component_missing(tmp_path: Path) -> None:
    run = tmp_path / "run"
    run.mkdir()
    write_json(run / "run_timing.json", {"memory_mode": "resident", "stages": []})
    write_json(
        run / "resident_artifacts.json",
        {
            "artifacts": [
                {
                    "timing_s": {
                        "light_read_upload_calibrate": 3.1,
                        "resident_integration": 3.28,
                    }
                }
            ]
        },
    )

    payload = build_resident_component_timing(run)

    assert payload["passed"] is False
    assert payload["summary"]["missing_required_components"] == ["resident_registration_warp"]
