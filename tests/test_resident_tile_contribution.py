from __future__ import annotations

from pathlib import Path

import numpy as np
from astropy.io import fits

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.resident_tile_contribution import build_resident_tile_contribution
from tests.conftest import cuda_module_or_skip


def _write_fits(path: Path, data: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fits.writeto(path, np.asarray(data, dtype=np.float32), overwrite=True)


def _write_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    run = tmp_path / "run"
    run.mkdir()
    cache = tmp_path / "cache"
    cache.mkdir()
    light1 = tmp_path / "light1.fits"
    light2 = tmp_path / "light2.fits"
    master = run / "integration" / "resident_master_H.fits"
    _write_fits(light1, np.ones((5, 6), dtype=np.float32))
    _write_fits(light2, np.full((5, 6), 3.0, dtype=np.float32))
    _write_fits(master, np.full((5, 6), 2.0, dtype=np.float32))
    write_json(cache / "h_master_stats.json", {"dark_exposure_s": None, "master_dark_includes_bias": True})
    (run / "run_command.txt").write_text(
        f"glass run --resident-master-cache-dir {cache} "
        "--resident-warp-interpolation bilinear --resident-warp-clamping-threshold 0.3",
        encoding="utf-8",
    )
    write_json(
        run / "frame_accounting.json",
        {
            "frames": [
                {"frame_id": "F001", "input_path": str(light1), "integration_weight": 1.0},
                {"frame_id": "F002", "input_path": str(light2), "integration_weight": 1.0},
            ]
        },
    )
    identity = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    write_json(
        run / "registration_results.json",
        {
            "results": [
                {"frame_id": "F001", "status": "ok", "matrix": identity},
                {"frame_id": "F002", "status": "ok", "matrix": identity},
            ]
        },
    )
    write_json(
        run / "processing_plan.json",
        {
            "frames": [
                {"id": "F001", "path": str(light1), "exposure_s": 10.0},
                {"id": "F002", "path": str(light2), "exposure_s": 10.0},
            ]
        },
    )
    write_json(
        run / "integration_results.json",
        {
            "rejection": "none",
            "outputs": [
                {
                    "filter": "H",
                    "master_path": str(master),
                    "rejection": "none",
                }
            ],
        },
    )
    write_json(run / "resident_artifacts.json", {"policy": {}, "artifacts": [{"filter": "H", "master_path": str(master)}]})
    tile_pack = tmp_path / "tile_pack.json"
    write_json(
        tile_pack,
        {
            "tiles": [
                {"index": 0, "extent": {"x0": 1, "y0": 1, "x1": 4, "y1": 4}, "source_top_tile": {}}
            ]
        },
    )
    return run, cache, tile_pack


def test_resident_tile_contribution_matches_identity_mean(tmp_path: Path) -> None:
    cuda_module_or_skip()
    run, cache, tile_pack = _write_fixture(tmp_path)

    payload = build_resident_tile_contribution(
        tile_pack,
        run,
        master_cache_dir=cache,
        rejection="none",
        focus_frames=["F001"],
        control_frames=["F002"],
    )

    tile = payload["tiles"][0]
    rows = {row["frame_id"]: row for row in tile["top_frames"]}
    assert payload["selected_frame_count"] == 2
    assert tile["diagnostic_master_delta_to_master"]["mean"] == 0.0
    assert rows["F001"]["accepted_weighted_delta_mean"] == -1.0
    assert rows["F002"]["accepted_weighted_delta_mean"] == 1.0
    assert rows["F001"]["normalized_delta_contribution_mean"] == -0.5
    assert rows["F002"]["normalized_delta_contribution_mean"] == 0.5
    assert tile["focus_summary"]["tile_normalized_delta_contribution_sum"]["mean"] == -0.5
    assert tile["control_summary"]["tile_normalized_delta_contribution_sum"]["mean"] == 0.5


def test_resident_tile_contribution_cli_writes_markdown(tmp_path: Path) -> None:
    cuda_module_or_skip()
    run, cache, tile_pack = _write_fixture(tmp_path)
    out = tmp_path / "contribution.json"
    markdown = tmp_path / "contribution.md"

    assert (
        main(
            [
                "resident-tile-contribution",
                "--tile-pack",
                str(tile_pack),
                "--run",
                str(run),
                "--master-cache-dir",
                str(cache),
                "--out",
                str(out),
                "--markdown",
                str(markdown),
                "--rejection",
                "none",
                "--focus-frame",
                "F001",
                "--control-frame",
                "F002",
            ]
        )
        == 0
    )

    payload = read_json(out)
    assert payload["artifact_type"] == "resident_tile_contribution_capture"
    assert markdown.exists()
    assert "Resident Tile Contribution Capture" in markdown.read_text(encoding="utf-8")
