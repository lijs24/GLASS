from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.tile_local_policy_subset import build_tile_local_policy_subset


def _write_replay(path: Path) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "artifact_type": "tile_local_policy_replay",
            "target_group": "focus",
            "target_frame_ids": ["F000100", "F000101"],
            "tile_count": 3,
            "summary": {"recommendation": "tile_local_replay_promising"},
            "tiles": [
                {
                    "tile_index": 0,
                    "action": "boost",
                    "extent": {"x0": 0, "y0": 0, "x1": 10, "y1": 10},
                    "multiplier": 2.0,
                    "clamped": True,
                    "canonical_delta_contribution_adu": 5.0,
                    "per_frame_delta_minus_canonical_delta_adu": 0.0,
                    "signed_residual_reference_units_before": -0.5,
                    "signed_residual_reference_units_after": -0.25,
                    "residual_reduction_fraction": 0.5,
                    "moves_toward_reference": True,
                },
                {
                    "tile_index": 1,
                    "action": "boost",
                    "extent": {"x0": 20, "y0": 20, "x1": 30, "y1": 30},
                    "multiplier": 1.5,
                    "clamped": False,
                    "canonical_delta_contribution_adu": 4.0,
                    "per_frame_delta_minus_canonical_delta_adu": 0.0,
                    "signed_residual_reference_units_before": -0.4,
                    "signed_residual_reference_units_after": -0.2,
                    "residual_reduction_fraction": 0.5,
                    "moves_toward_reference": True,
                },
                {
                    "tile_index": 2,
                    "action": "boost",
                    "extent": {"x0": 5, "y0": 5, "x1": 15, "y1": 15},
                    "multiplier": 2.0,
                    "clamped": True,
                    "canonical_delta_contribution_adu": 3.0,
                    "per_frame_delta_minus_canonical_delta_adu": 0.0,
                    "signed_residual_reference_units_before": -0.3,
                    "signed_residual_reference_units_after": -0.1,
                    "residual_reduction_fraction": 0.666,
                    "moves_toward_reference": True,
                },
            ],
        },
    )


def test_tile_local_policy_subset_selects_non_overlapping_tiles(tmp_path: Path) -> None:
    replay = tmp_path / "replay.json"
    _write_replay(replay)

    subset = build_tile_local_policy_subset(replay)

    assert subset["artifact_type"] == "tile_local_policy_replay"
    assert subset["source_replay"] == str(replay)
    assert subset["original_tile_count"] == 3
    assert subset["tile_count"] == 2
    assert [tile["tile_index"] for tile in subset["tiles"]] == [0, 1]
    assert subset["dropped_overlap_tiles"] == [
        {"tile_index": 2, "overlaps_with": [0], "extent": {"x0": 5, "y0": 5, "x1": 15, "y1": 15}}
    ]
    assert subset["summary"]["recommendation"] == "tile_local_replay_promising"
    assert subset["summary"]["known_direction_tiles"] == 2
    assert subset["summary"]["moves_toward_reference"] == 2


def test_cli_tile_local_policy_subset_writes_outputs(tmp_path: Path) -> None:
    replay = tmp_path / "replay.json"
    out = tmp_path / "subset.json"
    markdown = tmp_path / "subset.md"
    _write_replay(replay)

    assert (
        main(
            [
                "tile-local-policy-subset",
                "--replay",
                str(replay),
                "--out",
                str(out),
                "--markdown",
                str(markdown),
            ]
        )
        == 0
    )

    payload = read_json(out)
    assert payload["tile_count"] == 2
    assert "Tile-Local Policy Subset" in markdown.read_text(encoding="utf-8")
