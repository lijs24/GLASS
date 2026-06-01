from __future__ import annotations

from pathlib import Path

import numpy as np
from astropy.io import fits

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.compare_tile_replay import build_compare_tile_replay


def _write_fits(path: Path, data: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fits.writeto(path, np.asarray(data, dtype=np.float32), overwrite=True)


def _write_replay_fixture(tmp_path: Path) -> tuple[Path, Path]:
    run = tmp_path / "run"
    run.mkdir()
    light1 = tmp_path / "light1.fits"
    light2 = tmp_path / "light2.fits"
    master = run / "integration" / "master.fits"
    _write_fits(light1, np.ones((5, 5), dtype=np.float32))
    _write_fits(light2, np.full((5, 5), 3, dtype=np.float32))
    _write_fits(master, np.full((5, 5), 2, dtype=np.float32))
    identity = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    write_json(
        run / "frame_accounting.json",
        {
            "frames": [
                {
                    "frame_id": "F001",
                    "input_path": str(light1),
                    "final_status": "integrated",
                    "integration_weight": 1.0,
                    "warnings": ["triangle_agreement_status=ok"],
                },
                {
                    "frame_id": "F002",
                    "input_path": str(light2),
                    "final_status": "integrated",
                    "integration_weight": 1.0,
                    "warnings": ["triangle_agreement_status=ok"],
                },
            ]
        },
    )
    write_json(
        run / "registration_results.json",
        {
            "results": [
                {"frame_id": "F001", "status": "ok", "matrix": identity, "rms_px": 0.0},
                {"frame_id": "F002", "status": "ok", "matrix": identity, "rms_px": 0.0},
            ]
        },
    )
    write_json(run / "processing_plan.json", {"frames": [{"id": "F001", "exposure_s": 10}, {"id": "F002", "exposure_s": 10}]})
    write_json(run / "integration_results.json", {"outputs": [{"filter": "H", "master_path": str(master)}], "low_sigma": 2, "high_sigma": 2})
    tile_pack = tmp_path / "tile_pack_manifest.json"
    write_json(
        tile_pack,
        {
            "tiles": [
                {
                    "index": 0,
                    "extent": {"x0": 1, "y0": 1, "x1": 4, "y1": 4, "pad_px": 0},
                    "paths": {},
                    "source_top_tile": {"tail_pixels": 9},
                }
            ]
        },
    )
    return run, tile_pack


def test_compare_tile_replay_ranks_frame_deltas(tmp_path: Path) -> None:
    run, tile_pack = _write_replay_fixture(tmp_path)

    payload = build_compare_tile_replay(tile_pack, run, filter_name="H", frame_strategy="frame_id", max_frames=0)

    assert payload["selected_frame_count"] == 2
    tile = payload["tiles"][0]
    assert tile["status"] == "completed"
    assert tile["replayed_frame_count"] == 2
    means = {row["frame_id"]: row["delta_to_master_stats"]["mean"] for row in tile["top_frames"]}
    assert means["F001"] == -1.0
    assert means["F002"] == 1.0
    assert tile["proxy_weighted_mean_delta_to_master"]["mean"] == 0.0


def test_compare_tile_replay_cli_writes_markdown(tmp_path: Path) -> None:
    run, tile_pack = _write_replay_fixture(tmp_path)
    out = tmp_path / "replay.json"
    markdown = tmp_path / "replay.md"

    assert (
        main(
            [
                "compare-tile-replay",
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
                "--frame-strategy",
                "frame_id",
                "--max-frames",
                "0",
            ]
        )
        == 0
    )

    payload = read_json(out)
    assert payload["tiles"][0]["replayed_frame_count"] == 2
    assert markdown.exists()
