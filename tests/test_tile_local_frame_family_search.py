from __future__ import annotations

from pathlib import Path

import pytest

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.tile_local_frame_family_search import build_tile_local_frame_family_search


def _write_inputs(tmp_path: Path) -> tuple[Path, Path]:
    tile_pack = tmp_path / "tile_pack.json"
    contribution = tmp_path / "contribution.json"
    write_json(
        tile_pack,
        {
            "candidate_transform": {"scale": 0.1},
            "tiles": [
                {
                    "index": 0,
                    "extent": {"x0": 0, "x1": 8, "y0": 0, "y1": 8},
                    "source_top_tile": {"tail_signed_mean": -0.1},
                    "signed_diff_stats": {"mean": -0.1},
                }
            ],
        },
    )
    write_json(
        contribution,
        {
            "artifact_type": "resident_tile_contribution_capture",
            "tile_pack_json": str(tile_pack),
            "tiles": [
                {
                    "index": 0,
                    "extent": {"x0": 0, "x1": 8, "y0": 0, "y1": 8},
                    "top_frames": [
                        {"frame_id": "F001", "normalized_delta_contribution_mean": 0.1},
                        {"frame_id": "F002", "normalized_delta_contribution_mean": 1.0},
                        {"frame_id": "F003", "normalized_delta_contribution_mean": -0.5},
                    ],
                }
            ],
        },
    )
    return contribution, tile_pack


def test_tile_local_frame_family_search_ranks_best_bounded_window(tmp_path: Path) -> None:
    contribution, tile_pack = _write_inputs(tmp_path)

    payload = build_tile_local_frame_family_search(
        contribution,
        tile_pack=tile_pack,
        window_sizes=[1],
        top_n=3,
    )

    top = payload["top_candidate"]
    assert payload["artifact_type"] == "tile_local_frame_family_search"
    assert top["candidate_id"] == "F002"
    assert top["summary"]["mean_abs_residual_after"] == pytest.approx(0.0)
    assert top["summary"]["total_abs_residual_reduction"] == pytest.approx(0.1)
    assert top["summary"]["applied_to_required_boost_ratio_stats"]["mean"] == pytest.approx(1.0)


def test_cli_tile_local_frame_family_search_writes_json_and_markdown(tmp_path: Path) -> None:
    contribution, tile_pack = _write_inputs(tmp_path)
    out = tmp_path / "frame_family_search.json"
    markdown = tmp_path / "frame_family_search.md"

    assert (
        main(
            [
                "tile-local-frame-family-search",
                "--contribution",
                str(contribution),
                "--tile-pack",
                str(tile_pack),
                "--out",
                str(out),
                "--markdown",
                str(markdown),
                "--window-size",
                "1",
            ]
        )
        == 0
    )

    payload = read_json(out)
    assert payload["top_candidate"]["candidate_id"] == "F002"
    assert markdown.exists()
    assert "Tile-Local Frame-Family Search" in markdown.read_text(encoding="utf-8")
