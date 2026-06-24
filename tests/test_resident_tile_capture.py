from __future__ import annotations

from pathlib import Path

import numpy as np
from astropy.io import fits

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.resident_tile_capture import build_resident_tile_capture
from tests.conftest import cuda_module_or_skip


def _write_fits(path: Path, data: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fits.writeto(path, np.asarray(data, dtype=np.float32), overwrite=True)


def test_resident_stack_download_frame_tile() -> None:
    cuda = cuda_module_or_skip()
    stack = cuda.ResidentCalibratedStack(1, 4, 5)
    frame = np.arange(20, dtype=np.float32).reshape(4, 5)
    stack.upload_calibrated_frame(0, frame)

    tile = np.asarray(stack.download_frame_tile(0, 1, 1, 4, 3), dtype=np.float32)

    assert np.array_equal(tile, frame[1:3, 1:4])


def test_resident_stack_download_frames_tile() -> None:
    cuda = cuda_module_or_skip()
    stack = cuda.ResidentCalibratedStack(3, 4, 5)
    frames = [
        (np.arange(20, dtype=np.float32).reshape(4, 5) + np.float32(index * 100.0))
        for index in range(3)
    ]
    for index, frame in enumerate(frames):
        stack.upload_calibrated_frame(index, frame)

    tile_stack = np.asarray(stack.download_frames_tile([2, 0], 1, 1, 4, 3), dtype=np.float32)

    assert tile_stack.shape == (2, 2, 3)
    assert np.array_equal(tile_stack[0], frames[2][1:3, 1:4])
    assert np.array_equal(tile_stack[1], frames[0][1:3, 1:4])


def _write_capture_fixture(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
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
    write_json(run / "integration_results.json", {"outputs": [{"filter": "H", "master_path": str(master)}]})
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
    replay = tmp_path / "replay.json"
    write_json(
        replay,
        {
            "tiles": [
                {
                    "index": 0,
                    "top_frames": [
                        {"frame_id": "F001", "weighted_delta_mean": -1.0},
                        {"frame_id": "F002", "weighted_delta_mean": 1.0},
                    ],
                }
            ]
        },
    )
    return run, cache, tile_pack, replay


def test_resident_tile_capture_matches_identity_tiles(tmp_path: Path) -> None:
    cuda_module_or_skip()
    run, cache, tile_pack, replay = _write_capture_fixture(tmp_path)
    out_dir = tmp_path / "capture"

    payload = build_resident_tile_capture(
        tile_pack,
        run,
        out_dir,
        replay_json=replay,
        frame_ids=["F001", "F002"],
        master_cache_dir=cache,
        write_tiles=True,
    )

    assert payload["selected_frame_ids"] == ["F001", "F002"]
    assert payload["tile_summaries"][0]["resident_weighted_delta_mean"]["mean"] == 0.0
    assert payload["tile_summaries"][0]["resident_minus_cpu_weighted_delta_mean"]["mean"] == 0.0
    rows = {row["frame_id"]: row for row in payload["frames"][0]["tiles"] + payload["frames"][1]["tiles"]}
    assert rows["F001"]["weighted_delta_mean"] == -1.0
    assert rows["F002"]["weighted_delta_mean"] == 1.0
    assert Path(rows["F001"]["capture_path"]).exists()


def test_resident_tile_capture_cli_writes_markdown(tmp_path: Path) -> None:
    cuda_module_or_skip()
    run, cache, tile_pack, replay = _write_capture_fixture(tmp_path)
    out_dir = tmp_path / "capture"
    out = tmp_path / "capture.json"
    markdown = tmp_path / "capture.md"

    assert (
        main(
            [
                "resident-tile-capture",
                "--tile-pack",
                str(tile_pack),
                "--run",
                str(run),
                "--replay",
                str(replay),
                "--master-cache-dir",
                str(cache),
                "--frame-id",
                "F001",
                "--frame-id",
                "F002",
                "--out-dir",
                str(out_dir),
                "--out",
                str(out),
                "--markdown",
                str(markdown),
            ]
        )
        == 0
    )

    payload = read_json(out)
    assert payload["selected_frame_count"] == 2
    assert markdown.exists()
