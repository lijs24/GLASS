from __future__ import annotations

from pathlib import Path

import pytest

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.tile_local_residual_source_audit import build_tile_local_residual_source_audit


def _write_inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    tile_pack = tmp_path / "tile_pack.json"
    contribution = tmp_path / "contribution.json"
    frame_search = tmp_path / "frame_family_search.json"
    write_json(
        tile_pack,
        {
            "tiles": [
                {
                    "index": 0,
                    "extent": {"x0": 0, "x1": 8, "y0": 0, "y1": 8},
                    "source_top_tile": {"tail_signed_mean": -0.1},
                    "tail_pixels": 32,
                    "tail_fraction_of_valid": 0.5,
                }
            ],
        },
    )
    write_json(
        contribution,
        {
            "artifact_type": "resident_tile_contribution_capture",
            "tile_pack_json": str(tile_pack),
            "selected_frame_count": 100,
            "tiles": [
                {
                    "index": 0,
                    "extent": {"x0": 0, "x1": 8, "y0": 0, "y1": 8},
                    "diagnostic_coverage_map_stats": {"mean": 99.0},
                    "diagnostic_high_rejection_map_stats": {"mean": 2.0},
                    "diagnostic_low_rejection_map_stats": {"mean": 0.25},
                    "diagnostic_master_delta_to_master": {"mean": 0.0},
                    "focus_vs_control": {
                        "high_rejected_fraction": {"focus_minus_control": 0.03},
                        "rejected_fraction": {"focus_minus_control": 0.031},
                        "tile_normalized_delta_contribution_sum": {"focus_minus_control": 2.0},
                    },
                }
            ],
        },
    )
    write_json(
        frame_search,
        {
            "artifact_type": "tile_local_frame_family_search",
            "top_candidate": {
                "candidate_id": "F001-F003",
                "summary": {
                    "total_abs_residual_before": 0.1,
                    "total_abs_residual_reduction": 0.001,
                },
            },
            "candidates": [
                {
                    "candidate_id": "F001-F003",
                    "tiles": [
                        {
                            "tile_index": 0,
                            "residual_reduction_fraction": 0.01,
                            "group_contribution_adu": 2.0,
                            "multiplier": 2.0,
                        }
                    ],
                }
            ],
        },
    )
    return contribution, tile_pack, frame_search


def test_tile_local_residual_source_audit_prioritizes_rejection_registration(tmp_path: Path) -> None:
    contribution, tile_pack, frame_search = _write_inputs(tmp_path)

    payload = build_tile_local_residual_source_audit(
        contribution,
        tile_pack=tile_pack,
        frame_family_search=frame_search,
    )

    row = payload["tiles"][0]
    assert payload["artifact_type"] == "tile_local_residual_source_audit"
    assert payload["summary"]["recommendation"] == "prioritize_rejection_registration_diagnostics"
    assert payload["summary"]["coverage_below_threshold_tiles"] == 0
    assert payload["summary"]["focus_high_rejection_excess_tiles"] == 1
    assert payload["summary"]["top_frame_family_explained_fraction"] == pytest.approx(0.01)
    assert row["coverage_fraction_mean"] == pytest.approx(0.99)
    assert row["focus_high_rejection_excess"] is True


def test_cli_tile_local_residual_source_audit_writes_json_and_markdown(tmp_path: Path) -> None:
    contribution, tile_pack, frame_search = _write_inputs(tmp_path)
    out = tmp_path / "residual_source_audit.json"
    markdown = tmp_path / "residual_source_audit.md"

    assert (
        main(
            [
                "tile-local-residual-source-audit",
                "--contribution",
                str(contribution),
                "--tile-pack",
                str(tile_pack),
                "--frame-family-search",
                str(frame_search),
                "--out",
                str(out),
                "--markdown",
                str(markdown),
            ]
        )
        == 0
    )

    payload = read_json(out)
    assert payload["summary"]["recommendation"] == "prioritize_rejection_registration_diagnostics"
    assert markdown.exists()
    assert "Tile-Local Residual Source Audit" in markdown.read_text(encoding="utf-8")
