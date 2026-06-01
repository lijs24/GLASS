from __future__ import annotations

from pathlib import Path

import pytest

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.tile_local_policy import build_tile_local_policy_proposal


def _write_inputs(tmp_path: Path, *, signed_mean: float = -0.1, contribution_adu: float = 1.0) -> tuple[Path, Path]:
    tile_pack = tmp_path / "tile_pack.json"
    contribution = tmp_path / "contribution.json"
    write_json(
        tile_pack,
        {
            "candidate_transform": {"scale": 0.1, "offset": 0.0},
            "tiles": [
                {
                    "index": 0,
                    "signed_diff_stats": {"mean": signed_mean},
                    "source_top_tile": {"tail_signed_mean": signed_mean * 2.0},
                }
            ],
        },
    )
    write_json(
        contribution,
        {
            "tile_pack_json": str(tile_pack),
            "tiles": [
                {
                    "index": 0,
                    "extent": {"x0": 0, "x1": 8, "y0": 0, "y1": 8},
                    "focus_summary": {
                        "tile_normalized_delta_contribution_sum": {
                            "mean": contribution_adu,
                        },
                    },
                }
            ],
        },
    )
    return contribution, tile_pack


def test_tile_local_policy_proposal_boosts_opposite_signed_contribution(tmp_path: Path):
    contribution, _tile_pack = _write_inputs(tmp_path, signed_mean=-0.1, contribution_adu=1.0)

    proposal = build_tile_local_policy_proposal(contribution, min_multiplier=0.0, max_multiplier=2.0)

    row = proposal["tiles"][0]
    assert row["action"] == "boost"
    assert row["unconstrained_multiplier"] == pytest.approx(2.0)
    assert row["multiplier"] == pytest.approx(2.0)
    assert row["predicted_signed_residual_after"] == pytest.approx(0.0)
    assert row["moves_toward_reference"] is True
    assert proposal["summary"]["recommendation"] == "tile_local_policy_candidate"


def test_tile_local_policy_proposal_downweights_same_signed_contribution(tmp_path: Path):
    contribution, _tile_pack = _write_inputs(tmp_path, signed_mean=0.1, contribution_adu=1.0)

    proposal = build_tile_local_policy_proposal(contribution, min_multiplier=0.0, max_multiplier=2.0)

    row = proposal["tiles"][0]
    assert row["action"] == "downweight"
    assert row["multiplier"] == pytest.approx(0.0)
    assert row["predicted_signed_residual_after"] == pytest.approx(0.0)
    assert row["moves_toward_reference"] is True


def test_tile_local_policy_proposal_clamps_large_boost(tmp_path: Path):
    contribution, _tile_pack = _write_inputs(tmp_path, signed_mean=-0.3, contribution_adu=1.0)

    proposal = build_tile_local_policy_proposal(contribution, min_multiplier=0.0, max_multiplier=2.0)

    row = proposal["tiles"][0]
    assert row["unconstrained_multiplier"] == pytest.approx(4.0)
    assert row["multiplier"] == pytest.approx(2.0)
    assert row["clamped"] is True
    assert row["predicted_signed_residual_after"] == pytest.approx(-0.2)
    assert proposal["summary"]["recommendation"] == "tile_local_policy_candidate"


def test_cli_tile_local_policy_proposal_writes_json_and_markdown(tmp_path: Path):
    contribution, tile_pack = _write_inputs(tmp_path, signed_mean=-0.1, contribution_adu=1.0)
    out = tmp_path / "proposal.json"
    markdown = tmp_path / "proposal.md"

    assert (
        main(
            [
                "tile-local-policy-proposal",
                "--contribution",
                str(contribution),
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
    assert payload["artifact_type"] == "tile_local_policy_proposal"
    assert payload["summary"]["recommendation"] == "tile_local_policy_candidate"
    assert markdown.exists()
    assert "Tile-Local Policy Proposal" in markdown.read_text(encoding="utf-8")
