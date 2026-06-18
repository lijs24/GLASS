from __future__ import annotations

from pathlib import Path

from glass.io.json_io import write_json
from glass.report.registration_quality import build_registration_quality_contract


def _write_registration_run(path: Path) -> None:
    path.mkdir(parents=True)
    write_json(
        path / "registration_results.json",
        {
            "schema_version": 1,
            "reference_frame_id": "F1",
            "method": "fixture",
            "transform_model": "translation",
            "registration_results": [
                {
                    "frame_id": "F1",
                    "status": "reference",
                    "inliers": 10,
                    "matched_stars": 10,
                    "rms_px": 0.0,
                    "registration_validation": {"accepted": True, "rms_px": 0.0, "inliers": 10},
                },
                {
                    "frame_id": "F2",
                    "status": "registered",
                    "inliers": 8,
                    "matched_stars": 9,
                    "rms_px": 0.4,
                    "registration_validation": {"accepted": True, "rms_px": 0.4, "inliers": 8},
                },
                {
                    "frame_id": "F3",
                    "status": "quality_rejected",
                    "inliers": 0,
                    "matched_stars": 0,
                    "rms_px": float("nan"),
                    "registration_validation": {"accepted": False, "rms_px": None, "inliers": 0},
                },
            ],
        },
    )


def test_registration_quality_contract_passes_thresholds(tmp_path: Path) -> None:
    run = tmp_path / "run"
    _write_registration_run(run)

    payload = build_registration_quality_contract(run, max_rms_px=0.5, min_inliers=8)

    assert payload["artifact_type"] == "registration_quality_contract"
    assert payload["passed"] is True
    assert payload["required"] is True
    assert payload["summary"]["output_count"] == 3
    assert payload["summary"]["accepted_count"] == 2
    assert payload["summary"]["failed_count"] == 1
    assert payload["summary"]["max_rms_px"] == 0.4
    assert payload["summary"]["min_inliers"] == 8


def test_registration_quality_contract_fails_thresholds_and_all_accepted(tmp_path: Path) -> None:
    run = tmp_path / "run"
    _write_registration_run(run)

    payload = build_registration_quality_contract(
        run,
        max_rms_px=0.1,
        min_inliers=9,
        require_all_accepted=True,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert checks["accepted_registration_rms_within_threshold"]["passed"] is False
    assert checks["accepted_registration_inliers_meet_threshold"]["passed"] is False
    assert checks["all_registration_outputs_accepted"]["passed"] is False
    assert payload["failed_outputs"][0]["frame_id"] == "F3"
