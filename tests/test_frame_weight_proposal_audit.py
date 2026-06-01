from __future__ import annotations

from pathlib import Path

import pytest

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.frame_weight_proposal_audit import build_frame_weight_proposal_audit


def _write_inputs(tmp_path: Path, *, signed_mean: float, focus_contribution: float = 5.0) -> tuple[Path, Path, Path]:
    tile_pack = tmp_path / "tile_pack_manifest.json"
    integration = tmp_path / "integration_audit.json"
    proposal = tmp_path / "proposal.json"
    write_json(
        tile_pack,
        {
            "candidate_transform": {"scale": 0.1, "offset": 0.0},
            "tiles": [
                {
                    "index": 0,
                    "signed_diff_stats": {"mean": signed_mean, "rms": abs(signed_mean)},
                    "source_top_tile": {
                        "tail_signed_mean": signed_mean * 2.0,
                        "tail_pixels": 10,
                        "negative_tail_pixels": 10 if signed_mean < 0 else 0,
                        "positive_tail_pixels": 10 if signed_mean > 0 else 0,
                    },
                }
            ],
        },
    )
    write_json(
        integration,
        {
            "tile_pack": str(tile_pack),
            "focus_ids": ["F001"],
            "control_ids": ["F002"],
            "tiles": [
                {
                    "index": 0,
                    "extent": {"x0": 0, "x1": 16, "y0": 0, "y1": 16},
                    "focus_summary": {
                        "tile_normalized_delta_contribution_sum": {
                            "mean": focus_contribution,
                        },
                    },
                }
            ],
        },
    )
    write_json(
        proposal,
        {
            "method": "control_ratio",
            "proposed_multiplier": 0.5,
            "frame_multipliers": [{"frame_id": "F001", "multiplier": 0.5}],
        },
    )
    return integration, proposal, tile_pack


def test_frame_weight_proposal_audit_rejects_away_direction(tmp_path: Path):
    integration, proposal, _tile_pack = _write_inputs(tmp_path, signed_mean=-1.0)

    audit = build_frame_weight_proposal_audit(integration, proposal)

    tile = audit["tiles"][0]
    assert tile["predicted_master_delta_adu"] == pytest.approx(-2.5)
    assert tile["predicted_signed_delta_reference_units"] == pytest.approx(-0.25)
    assert tile["moves_mean_toward_reference"] is False
    assert tile["moves_tail_toward_reference"] is False
    assert audit["summary"]["recommendation"] == "reject_downweight_direction"


def test_frame_weight_proposal_audit_accepts_toward_direction(tmp_path: Path):
    integration, proposal, _tile_pack = _write_inputs(tmp_path, signed_mean=1.0)

    audit = build_frame_weight_proposal_audit(integration, proposal)

    assert audit["tiles"][0]["moves_mean_toward_reference"] is True
    assert audit["tiles"][0]["moves_tail_toward_reference"] is True
    assert audit["summary"]["recommendation"] == "directionally_promising"


def test_cli_frame_weight_proposal_audit_writes_json_and_markdown(tmp_path: Path):
    integration, proposal, tile_pack = _write_inputs(tmp_path, signed_mean=-1.0)
    out = tmp_path / "direction_audit.json"
    markdown = tmp_path / "direction_audit.md"

    assert (
        main(
            [
                "frame-weight-proposal-audit",
                "--integration-audit",
                str(integration),
                "--proposal",
                str(proposal),
                "--tile-pack",
                str(tile_pack),
                "--out",
                str(out),
                "--markdown",
                str(markdown),
            ]
        )
        == 0
    )

    payload = read_json(out)
    assert payload["summary"]["recommendation"] == "reject_downweight_direction"
    assert markdown.exists()
    assert "Frame Weight Proposal Direction Audit" in markdown.read_text(encoding="utf-8")
