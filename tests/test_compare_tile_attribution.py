from __future__ import annotations

from pathlib import Path

import numpy as np
from astropy.io import fits

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.compare_tile_attribution import build_compare_tile_attribution


def _write_fits(path: Path, data: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fits.writeto(path, np.asarray(data, dtype=np.float32), overwrite=True)


def _write_run(tmp_path: Path) -> Path:
    run = tmp_path / "run"
    integration = run / "integration"
    integration.mkdir(parents=True)
    coverage = np.full((5, 5), 10, dtype=np.float32)
    weight = np.full((5, 5), 7.5, dtype=np.float32)
    low = np.zeros((5, 5), dtype=np.float32)
    high = np.zeros((5, 5), dtype=np.float32)
    low[1:4, 1:4] = 2
    dq = np.zeros((5, 5), dtype=np.float32)
    dq[1:4, 1:4] = 256
    paths = {
        "coverage_map_path": integration / "coverage.fits",
        "weight_map_path": integration / "weight.fits",
        "low_rejection_map_path": integration / "low.fits",
        "high_rejection_map_path": integration / "high.fits",
        "dq_map_path": integration / "dq.fits",
    }
    for key, path in paths.items():
        data = {
            "coverage_map_path": coverage,
            "weight_map_path": weight,
            "low_rejection_map_path": low,
            "high_rejection_map_path": high,
            "dq_map_path": dq,
        }[key]
        _write_fits(path, data)
    write_json(
        run / "integration_results.json",
        {
            "outputs": [
                {
                    "filter": "H",
                    **{key: str(path) for key, path in paths.items()},
                }
            ]
        },
    )
    write_json(
        run / "resident_artifacts.json",
        {"artifacts": [{"filter": "H", "dq_flag_bits": {"low_rejected": 256, "high_rejected": 512, "warp_edge": 64}}]},
    )
    write_json(
        run / "frame_accounting.json",
        {
            "frames": [
                {
                    "frame_id": "F001",
                    "final_status": "integrated",
                    "integration_status": "used",
                    "registration_status": "ok",
                    "integration_weight": 0.25,
                    "warnings": [
                        "triangle_agreement_status=downweighted",
                        "triangle_agreement_score=0.125",
                        "triangle_agreement_weight_multiplier=0.25",
                    ],
                },
                {
                    "frame_id": "F002",
                    "final_status": "integrated",
                    "integration_status": "used",
                    "registration_status": "ok",
                    "integration_weight": 1.0,
                    "warnings": ["triangle_agreement_status=ok"],
                },
            ],
            "exception_summary": {"count": 0},
        },
    )
    return run


def _write_tile_pack(tmp_path: Path) -> Path:
    path = tmp_path / "tile_pack_manifest.json"
    write_json(
        path,
        {
            "tiles": [
                {
                    "index": 0,
                    "extent": {"x0": 1, "y0": 1, "x1": 4, "y1": 4, "pad_px": 0},
                    "paths": {},
                    "source_top_tile": {"tail_pixels": 5},
                    "signed_diff_stats": {"mean": -0.1},
                    "abs_diff_stats": {"p99": 0.2},
                }
            ]
        },
    )
    return path


def test_compare_tile_attribution_joins_maps_and_frame_accounting(tmp_path: Path) -> None:
    run = _write_run(tmp_path)
    tile_pack = _write_tile_pack(tmp_path)

    payload = build_compare_tile_attribution(tile_pack, run, filter_name="H", frame_limit=4)

    assert payload["tile_count"] == 1
    tile = payload["tiles"][0]
    assert tile["coverage"]["mean"] == 10.0
    assert tile["low_rejection"]["sum"] == 18.0
    assert tile["dq_flag_counts"]["low_rejected"] == 9
    assert tile["recommendation"]["status"] == "rejection_heavy_tile"
    assert payload["frame_accounting"]["downweighted_count"] == 1
    assert payload["frame_accounting"]["lowest_weight_frames"][0]["frame_id"] == "F001"


def test_compare_tile_attribution_cli_writes_json_and_markdown(tmp_path: Path) -> None:
    run = _write_run(tmp_path)
    tile_pack = _write_tile_pack(tmp_path)
    out = tmp_path / "attribution.json"
    markdown = tmp_path / "attribution.md"

    assert (
        main(
            [
                "compare-tile-attribution",
                "--tile-pack",
                str(tile_pack),
                "--run",
                str(run),
                "--out",
                str(out),
                "--markdown",
                str(markdown),
                "--filter",
                "H",
            ]
        )
        == 0
    )

    payload = read_json(out)
    assert payload["tile_count"] == 1
    assert payload["frame_accounting"]["integrated_count"] == 2
    assert markdown.exists()
