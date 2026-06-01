from __future__ import annotations

from pathlib import Path

import pytest

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.tile_local_policy_replay import build_tile_local_policy_replay


def _write_inputs(tmp_path: Path) -> tuple[Path, Path]:
    contribution = tmp_path / "contribution.json"
    proposal = tmp_path / "proposal.json"
    write_json(
        contribution,
        {
            "artifact_type": "resident_tile_contribution_capture",
            "focus_ids": ["F001"],
            "control_ids": ["F002"],
            "tiles": [
                {
                    "index": 0,
                    "extent": {"x0": 0, "x1": 8, "y0": 0, "y1": 8},
                    "top_frames": [
                        {
                            "frame_id": "F001",
                            "tile_index": 0,
                            "integration_weight": 1.0,
                            "accepted_pixels": 64,
                            "rejected_pixels": 0,
                            "accepted_fraction": 1.0,
                            "accepted_weighted_delta_mean": 1.0,
                            "normalized_delta_contribution_mean": 1.0,
                        },
                        {
                            "frame_id": "F002",
                            "tile_index": 0,
                            "integration_weight": 1.0,
                            "accepted_pixels": 64,
                            "rejected_pixels": 0,
                            "accepted_fraction": 1.0,
                            "accepted_weighted_delta_mean": 0.5,
                            "normalized_delta_contribution_mean": 0.5,
                        },
                    ],
                }
            ],
        },
    )
    write_json(
        proposal,
        {
            "artifact_type": "tile_local_policy_proposal",
            "target_group": "focus",
            "residual_stat": "signed_mean",
            "tiles": [
                {
                    "tile_index": 0,
                    "extent": {"x0": 0, "x1": 8, "y0": 0, "y1": 8},
                    "action": "boost",
                    "multiplier": 2.0,
                    "clamped": False,
                    "group_contribution_adu": 1.0,
                    "group_contribution_reference_units": 0.1,
                    "predicted_delta_reference_units": 0.1,
                    "signed_residual_reference_units": -0.1,
                    "predicted_signed_residual_after": 0.0,
                    "moves_toward_reference": True,
                }
            ],
        },
    )
    return contribution, proposal


def test_tile_local_policy_replay_applies_multiplier_to_focus_group(tmp_path: Path) -> None:
    contribution, proposal = _write_inputs(tmp_path)

    replay = build_tile_local_policy_replay(contribution, proposal)

    tile = replay["tiles"][0]
    frame = tile["selected_frame_rows"][0]
    assert replay["artifact_type"] == "tile_local_policy_replay"
    assert replay["summary"]["recommendation"] == "tile_local_replay_promising"
    assert replay["summary"]["mean_abs_residual_before"] == pytest.approx(0.1)
    assert replay["summary"]["mean_abs_residual_after"] == pytest.approx(0.0)
    assert tile["canonical_original_contribution_adu"] == pytest.approx(1.0)
    assert tile["canonical_proposed_contribution_adu"] == pytest.approx(2.0)
    assert tile["canonical_delta_contribution_adu"] == pytest.approx(1.0)
    assert tile["per_frame_original_contribution_sum"] == pytest.approx(1.0)
    assert tile["per_frame_proposed_contribution_sum"] == pytest.approx(2.0)
    assert tile["per_frame_delta_minus_canonical_delta_adu"] == pytest.approx(0.0)
    assert frame["frame_id"] == "F001"
    assert frame["proposed_normalized_delta_contribution_mean"] == pytest.approx(2.0)


def test_cli_tile_local_policy_replay_writes_json_and_markdown(tmp_path: Path) -> None:
    contribution, proposal = _write_inputs(tmp_path)
    out = tmp_path / "replay.json"
    markdown = tmp_path / "replay.md"

    assert (
        main(
            [
                "tile-local-policy-replay",
                "--contribution",
                str(contribution),
                "--proposal",
                str(proposal),
                "--out",
                str(out),
                "--markdown",
                str(markdown),
            ]
        )
        == 0
    )

    payload = read_json(out)
    assert payload["artifact_type"] == "tile_local_policy_replay"
    assert payload["summary"]["recommendation"] == "tile_local_replay_promising"
    assert markdown.exists()
    assert "Tile-Local Policy Replay" in markdown.read_text(encoding="utf-8")
