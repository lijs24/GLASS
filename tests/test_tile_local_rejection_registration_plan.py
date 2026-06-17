from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.tile_local_rejection_registration_plan import build_tile_local_rejection_registration_plan


def _write_inputs(tmp_path: Path) -> tuple[Path, Path]:
    audit = tmp_path / "audit.json"
    run_command = tmp_path / "run_command.txt"
    write_json(
        audit,
        {
            "artifact_type": "tile_local_rejection_registration_audit",
            "summary": {
                "recommendation": "prioritize_registration_agreement_rejection_interaction",
                "focus_minus_control_high_rejected_fraction_mean": 0.03,
                "top_high_rejection_frames": [
                    {
                        "frame_id": "F001",
                        "high_rejected_fraction_mean": 0.08,
                        "in_focus_group": True,
                        "in_top_frame_family": True,
                    },
                    {
                        "frame_id": "F002",
                        "high_rejected_fraction_mean": 0.06,
                        "in_focus_group": True,
                        "in_top_frame_family": True,
                    },
                    {
                        "frame_id": "F050",
                        "high_rejected_fraction_mean": 0.05,
                        "in_focus_group": False,
                        "in_top_frame_family": False,
                    },
                ],
            },
        },
    )
    run_command.write_text(
        "glass run --plan plan.json --out old_run --backend cuda "
        "--resident-triangle-agreement-action downweight "
        "--resident-triangle-min-agreement-score 0.8",
        encoding="utf-8",
    )
    return audit, run_command


def test_tile_local_rejection_registration_plan_builds_candidate_commands(tmp_path: Path) -> None:
    audit, run_command = _write_inputs(tmp_path)
    root = tmp_path / "plan"

    payload = build_tile_local_rejection_registration_plan(
        audit,
        root=root,
        base_run_command=run_command,
        reference="reference.fits",
        glass_scale=0.5,
        min_coverage=1.0,
        exclude_top_count=2,
    )

    assert payload["artifact_type"] == "tile_local_rejection_registration_plan"
    assert payload["hotspot_frames"] == ["F001", "F002"]
    assert payload["candidate_count"] == 4
    soft = next(candidate for candidate in payload["candidates"] if candidate["candidate_id"] == "agreement_soft_downweight")
    exclude = next(candidate for candidate in payload["candidates"] if candidate["candidate_id"] == "exclude_top2_hotspot_frames")
    assert "--resident-triangle-min-agreement-score 0.6" in soft["commands"]["run"]
    assert str(root / "runs" / "agreement_soft_downweight") in soft["commands"]["run"]
    assert "--exclude-frame-id F001 --exclude-frame-id F002" in exclude["commands"]["run"]
    assert "compare_reference" in soft["commands"]


def test_cli_tile_local_rejection_registration_plan_writes_json_and_markdown(tmp_path: Path) -> None:
    audit, run_command = _write_inputs(tmp_path)
    out = tmp_path / "plan.json"
    markdown = tmp_path / "plan.md"

    assert (
        main(
            [
                "tile-local-rejection-registration-plan",
                "--audit",
                str(audit),
                "--root",
                str(tmp_path / "root"),
                "--base-run-command",
                str(run_command),
                "--out",
                str(out),
                "--markdown",
                str(markdown),
                "--exclude-top-count",
                "2",
            ]
        )
        == 0
    )

    payload = read_json(out)
    assert payload["candidate_count"] == 4
    assert markdown.exists()
    assert "Tile-Local Rejection/Registration Experiment Plan" in markdown.read_text(encoding="utf-8")
