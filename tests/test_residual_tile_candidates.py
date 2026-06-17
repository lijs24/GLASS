from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.residual_tile_candidates import build_residual_tile_candidates


def _write_outlier_audit(path: Path, tiles: list[dict]) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "audit_type": "compare_outlier_audit",
            "status": "completed",
            "glass": "glass.fits",
            "reference": "reference.fits",
            "coverage_map": "coverage.fits",
            "recommendation": {"status": "localized_tail"},
            "target_exceedance": {"pixels": 123},
            "top_tiles": tiles,
        },
    )


def _tile(x0: int, y0: int, x1: int, y1: int, tail_pixels: int, fraction: float) -> dict:
    return {
        "x0": x0,
        "y0": y0,
        "x1": x1,
        "y1": y1,
        "tail_pixels": tail_pixels,
        "valid_pixels": 1000,
        "tail_fraction_of_valid": fraction,
        "tail_abs_mean": 0.01,
        "tail_abs_max": 0.05,
        "tail_signed_mean": -0.01,
        "negative_tail_pixels": tail_pixels,
        "positive_tail_pixels": 0,
    }


def test_residual_tile_candidates_selects_non_overlapping_tiles(tmp_path: Path) -> None:
    audit_a = tmp_path / "audit_a.json"
    audit_b = tmp_path / "audit_b.json"
    known_pack = tmp_path / "known.json"
    _write_outlier_audit(
        audit_a,
        [
            _tile(0, 0, 10, 10, 100, 0.1),
            _tile(20, 0, 30, 10, 50, 0.05),
        ],
    )
    _write_outlier_audit(
        audit_b,
        [
            _tile(2, 2, 12, 12, 90, 0.09),
            _tile(40, 0, 50, 10, 80, 0.08),
        ],
    )
    write_json(
        known_pack,
        {
            "artifact_type": "compare_tile_pack",
            "tiles": [{"index": 0, "extent": {"x0": 0, "y0": 0, "x1": 10, "y1": 10}}],
        },
    )

    payload = build_residual_tile_candidates(
        [audit_a, audit_b],
        known_tile_packs=[known_pack],
        max_tiles=3,
        min_tail_pixels=10,
    )

    assert payload["summary"]["raw_candidate_count"] == 4
    assert payload["summary"]["selected_tile_count"] == 3
    assert payload["summary"]["dropped_overlap_count"] == 1
    assert payload["tiles"][0]["tail_pixels"] == 100
    assert payload["tiles"][0]["known_overlap_count"] == 1
    assert [tile["extent"]["x0"] for tile in payload["tiles"]] == [0, 40, 20]

    new_only = build_residual_tile_candidates(
        [audit_a, audit_b],
        known_tile_packs=[known_pack],
        max_tiles=3,
        min_tail_pixels=10,
        known_overlap_mode="exclude",
    )
    assert new_only["summary"]["selected_known_overlap_count"] == 0
    assert new_only["summary"]["filtered_known_overlap_count"] == 2
    assert [tile["extent"]["x0"] for tile in new_only["tiles"]] == [40, 20]


def test_residual_tile_candidates_cli_writes_outputs(tmp_path: Path) -> None:
    audit = tmp_path / "audit.json"
    out = tmp_path / "candidates.json"
    markdown = tmp_path / "candidates.md"
    _write_outlier_audit(audit, [_tile(0, 0, 10, 10, 100, 0.1)])

    assert (
        main(
            [
                "residual-tile-candidates",
                "--outlier-audit",
                str(audit),
                "--out",
                str(out),
                "--markdown",
                str(markdown),
                "--max-tiles",
                "1",
            ]
        )
        == 0
    )
    payload = read_json(out)
    assert payload["artifact_type"] == "residual_tile_candidates"
    assert payload["tile_count"] == 1
    assert "Residual Tile Candidates" in markdown.read_text(encoding="utf-8")
