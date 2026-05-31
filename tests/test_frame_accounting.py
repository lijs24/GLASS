from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.engine.frame_accounting import build_frame_accounting
from glass.io.json_io import read_json, write_json


def _plan_frame(frame_id: str) -> dict[str, object]:
    return {
        "id": frame_id,
        "path": f"light/{frame_id}.fits",
        "frame_type": "light",
        "filter": "H",
    }


def test_frame_accounting_builds_per_light_ledger(tmp_path: Path):
    run = tmp_path / "run"
    run.mkdir()
    frame_ids = ["ref", "good", "zero", "quality_bad", "registration_bad"]
    write_json(run / "processing_plan.json", {"frames": [_plan_frame(frame_id) for frame_id in frame_ids]})
    write_json(
        run / "calibration_artifacts.json",
        {"calibrated_lights": [{"frame_id": frame_id, "path": f"cal/{frame_id}.fits"} for frame_id in frame_ids]},
    )
    write_json(
        run / "frame_quality.json",
        {
            "frame_quality": [
                {
                    "frame_id": "ref",
                    "quality_gate_status": "accepted",
                    "reference_candidate": True,
                    "quality_score": 1.2,
                },
                {"frame_id": "good", "quality_gate_status": "accepted", "quality_score": 1.0},
                {"frame_id": "zero", "quality_gate_status": "accepted", "quality_score": 0.8},
                {
                    "frame_id": "quality_bad",
                    "quality_gate_status": "rejected",
                    "quality_gate_warnings": ["star_count 1 below min_stars=8"],
                    "quality_score": 0.1,
                },
                {"frame_id": "registration_bad", "quality_gate_status": "accepted", "quality_score": 0.7},
            ],
            "reference_frame_id": "ref",
        },
    )
    write_json(
        run / "registration_results.json",
        {
            "registration_results": [
                {"frame_id": "ref", "status": "reference", "registration_solution_source": "reference"},
                {"frame_id": "good", "status": "ok", "registration_solution_source": "star"},
                {"frame_id": "zero", "status": "ok", "registration_solution_source": "star"},
                {
                    "frame_id": "quality_bad",
                    "status": "quality_rejected",
                    "warnings": ["registration skipped because frame failed the quality gate"],
                },
                {
                    "frame_id": "registration_bad",
                    "status": "failed",
                    "warnings": ["registration failed validation gate"],
                },
            ]
        },
    )
    write_json(
        run / "warp_results.json",
        {
            "warp_results": [
                {"frame_id": "ref", "registered_path": "registered/ref.fits"},
                {"frame_id": "good", "registered_path": "registered/good.fits"},
                {"frame_id": "zero", "registered_path": "registered/zero.fits"},
            ],
            "skipped_frames": [
                {
                    "frame_id": "quality_bad",
                    "status": "quality_rejected",
                    "reason": "registration did not produce an accepted transform",
                },
                {
                    "frame_id": "registration_bad",
                    "status": "failed",
                    "reason": "registration did not produce an accepted transform",
                },
            ],
        },
    )
    write_json(
        run / "local_norm_results.json",
        {
            "enabled": False,
            "local_norm_results": [
                {"frame_id": "ref", "status": "disabled_passthrough"},
                {"frame_id": "good", "status": "disabled_passthrough"},
                {"frame_id": "zero", "status": "disabled_passthrough"},
            ],
        },
    )
    write_json(
        run / "integration_results.json",
        {
            "source_stage": "local_normalization",
            "frame_weights": {"ref": 1.0, "good": 0.9, "zero": 0.0},
            "outputs": [{"filter": "H", "frame_count": 3}],
        },
    )

    accounting = build_frame_accounting(run)
    assert (run / "frame_accounting.json").exists()
    rows = {item["frame_id"]: item for item in accounting["frames"]}

    assert rows["ref"]["final_status"] == "integrated"
    assert rows["good"]["integration_status"] == "used"
    assert rows["zero"]["final_status"] == "zero_weight"
    assert rows["quality_bad"]["final_status"] == "quality_rejected"
    assert "star_count 1 below min_stars=8" in rows["quality_bad"]["reasons"]
    assert rows["registration_bad"]["final_status"] == "registration_rejected"
    assert accounting["summary"]["integrated_frames"] == 2
    assert accounting["summary"]["zero_weight_frames"] == 1
    assert accounting["summary"]["quality_rejected_frames"] == 1
    assert accounting["summary"]["warp_skipped_frames"] == 2
    assert accounting["summary"]["exception_frames"] == 3
    exceptions = {item["frame_id"]: item for item in accounting["exception_frames"]}
    assert exceptions["zero"]["primary_stage"] == "integration"
    assert exceptions["zero"]["primary_reason"] == "integration weight is zero"
    assert exceptions["quality_bad"]["primary_stage"] == "quality"
    assert exceptions["quality_bad"]["primary_reason"] == "star_count 1 below min_stars=8"
    assert exceptions["registration_bad"]["primary_stage"] == "registration"
    assert accounting["exception_summary"]["final_status_counts"] == {
        "quality_rejected": 1,
        "registration_rejected": 1,
        "zero_weight": 1,
    }


def test_report_renders_frame_accounting(tmp_path: Path):
    run = tmp_path / "run"
    run.mkdir()
    write_json(
        run / "frame_accounting.json",
        {
            "summary": {
                "input_light_frames": 1,
                "integrated_frames": 1,
                "final_status_counts": {"integrated": 1},
            },
            "frames": [{"frame_id": "light_001", "final_status": "integrated"}],
            "exception_summary": {"count": 1, "final_status_counts": {"zero_weight": 1}},
            "exception_frames": [
                {
                    "frame_id": "light_002",
                    "final_status": "zero_weight",
                    "primary_stage": "integration",
                    "primary_reason": "integration weight is zero",
                }
            ],
        },
    )
    report = tmp_path / "report.html"
    assert main(["report", "--run", str(run), "--out", str(report)]) == 0

    html = report.read_text(encoding="utf-8")
    assert "Frame accounting" in html
    assert "Rejected/zero-weight frames" in html
    assert "frame_accounting.json" in html
    assert "light_001" in html
    assert "light_002" in html
    assert "integration weight is zero" in html


def test_resident_frame_accounting_uses_frame_weights(tmp_path: Path):
    run = tmp_path / "run"
    run.mkdir()
    write_json(run / "processing_plan.json", {"frames": [_plan_frame("ref"), _plan_frame("excluded")]})
    write_json(
        run / "registration_results.json",
        {
            "source_stage": "resident_calibrated_stack",
            "results": [
                {"frame_id": "ref", "status": "reference"},
                {"frame_id": "excluded", "status": "failed", "warnings": ["resident fit rejected"]},
            ],
        },
    )
    write_json(
        run / "local_norm_results.json",
        {"source_stage": "resident_calibrated_stack", "enabled": True, "groups": []},
    )
    write_json(
        run / "integration_results.json",
        {
            "source_stage": "resident_calibrated_stack",
            "frame_weights": {"ref": 1.0, "excluded": 0.0},
            "outputs": [{"filter": "H", "frame_count": 1}],
        },
    )

    accounting = build_frame_accounting(run)
    rows = {item["frame_id"]: item for item in accounting["frames"]}

    assert rows["ref"]["calibration_status"] == "resident_in_vram"
    assert rows["ref"]["warp_status"] == "resident_in_vram"
    assert rows["ref"]["local_norm_status"] == "resident_applied"
    assert rows["excluded"]["final_status"] == "zero_weight"
    written = read_json(run / "frame_accounting.json")
    assert written["sources"]["integration"] is True
    assert written["exception_summary"]["primary_stage_counts"] == {"integration": 1}
