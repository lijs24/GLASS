from __future__ import annotations

from pathlib import Path

import pytest

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.frame_weight_proposal import build_frame_weight_proposal


def _integration_audit_payload() -> dict:
    return {
        "focus_ids": ["F000100", "F000101"],
        "control_ids": ["F000099", "F000102"],
        "focus_summary": {
            "tile_normalized_delta_contribution_sum": {
                "mean": 5.0,
            },
        },
        "control_summary": {
            "tile_normalized_delta_contribution_sum": {
                "mean": 2.0,
            },
        },
    }


def test_build_frame_weight_proposal_uses_control_ratio(tmp_path: Path):
    audit = tmp_path / "integration_audit.json"
    write_json(audit, _integration_audit_payload())

    proposal = build_frame_weight_proposal(audit, min_multiplier=0.05, max_multiplier=1.0)

    assert proposal["artifact_type"] == "frame_weight_proposal"
    assert proposal["method"] == "control_ratio"
    assert proposal["status"] == "proposed"
    assert proposal["proposed_multiplier"] == pytest.approx(0.4)
    assert proposal["focus_ids"] == ["F000100", "F000101"]
    assert proposal["control_ids"] == ["F000099", "F000102"]
    assert [row["multiplier"] for row in proposal["frame_multipliers"]] == [pytest.approx(0.4)] * 2


def test_build_frame_weight_proposal_clamps_multiplier(tmp_path: Path):
    audit = tmp_path / "integration_audit.json"
    payload = _integration_audit_payload()
    payload["control_summary"]["tile_normalized_delta_contribution_sum"]["mean"] = 0.1
    write_json(audit, payload)

    proposal = build_frame_weight_proposal(audit, min_multiplier=0.25, max_multiplier=1.0)

    assert proposal["proposed_multiplier"] == pytest.approx(0.25)
    assert proposal["frame_multipliers"][0]["status"] == "proposed"


def test_cli_frame_weight_proposal_writes_json_and_markdown(tmp_path: Path):
    audit = tmp_path / "integration_audit.json"
    out = tmp_path / "proposal.json"
    markdown = tmp_path / "proposal.md"
    write_json(audit, _integration_audit_payload())

    assert (
        main(
            [
                "frame-weight-proposal",
                "--integration-audit",
                str(audit),
                "--out",
                str(out),
                "--markdown",
                str(markdown),
                "--reason",
                "localized contribution experiment",
            ]
        )
        == 0
    )

    proposal = read_json(out)
    assert proposal["proposed_multiplier"] == pytest.approx(0.4)
    assert proposal["frame_multipliers"][0]["reason"] == "localized contribution experiment"
    assert markdown.exists()
    assert "Frame Weight Proposal" in markdown.read_text(encoding="utf-8")
