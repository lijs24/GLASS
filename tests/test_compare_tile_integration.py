from __future__ import annotations

from pathlib import Path

import numpy as np
from astropy.io import fits

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.compare_tile_integration import build_compare_tile_integration_audit


def _write_fits(path: Path, data: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fits.writeto(path, np.asarray(data, dtype=np.float32), overwrite=True)


def _write_integration_fixture(tmp_path: Path) -> tuple[Path, Path]:
    run = tmp_path / "run"
    run.mkdir()
    master = run / "integration" / "master.fits"
    _write_fits(master, np.full((5, 5), 10.0, dtype=np.float32))
    frames = []
    plan_frames = []
    registrations = []
    identity = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    for index, value in enumerate([10.0, 10.0, 10.0, 50.0], start=1):
        frame_id = f"F{index:03d}"
        path = tmp_path / f"{frame_id}.fits"
        _write_fits(path, np.full((5, 5), value, dtype=np.float32))
        frames.append(
            {
                "frame_id": frame_id,
                "input_path": str(path),
                "final_status": "integrated",
                "integration_weight": 1.0,
                "warnings": ["triangle_agreement_status=ok"],
            }
        )
        plan_frames.append({"id": frame_id, "path": str(path), "exposure_s": 10.0})
        registrations.append({"frame_id": frame_id, "status": "ok", "matrix": identity, "rms_px": 0.0})
    write_json(run / "frame_accounting.json", {"frames": frames})
    write_json(run / "registration_results.json", {"results": registrations})
    write_json(run / "processing_plan.json", {"frames": plan_frames})
    write_json(
        run / "integration_results.json",
        {
            "outputs": [{"filter": "H", "master_path": str(master), "rejection": "winsorized_sigma"}],
            "rejection": "winsorized_sigma",
            "low_sigma": 1.0,
            "high_sigma": 1.0,
        },
    )
    tile_pack = tmp_path / "tile_pack_manifest.json"
    write_json(
        tile_pack,
        {
            "tiles": [
                {
                    "index": 0,
                    "extent": {"x0": 1, "y0": 1, "x1": 4, "y1": 4, "pad_px": 0},
                    "source_top_tile": {"tail_pixels": 9},
                }
            ]
        },
    )
    return run, tile_pack


def test_compare_tile_integration_audit_replays_winsorized_rejection(tmp_path: Path) -> None:
    run, tile_pack = _write_integration_fixture(tmp_path)

    payload = build_compare_tile_integration_audit(
        tile_pack,
        run,
        filter_name="H",
        frame_strategy="frame_id",
        max_frames=0,
        rejection="winsorized_sigma",
        low_sigma=1.0,
        high_sigma=1.0,
        replay_interpolation="bilinear",
        focus_frames=["F004"],
        control_frames=["F001", "F002", "F003"],
    )

    assert payload["selected_frame_count"] == 4
    tile = payload["tiles"][0]
    assert tile["status"] == "completed"
    assert tile["diagnostic_master_delta_to_master"]["mean"] == 0.0
    rows = {row["frame_id"]: row for row in tile["top_frames"]}
    assert rows["F004"]["high_rejected_pixels"] == 9
    assert rows["F004"]["accepted_pixels"] == 0
    assert rows["F001"]["accepted_pixels"] == 9
    assert payload["focus_summary"]["high_rejected_fraction"] == 1.0
    assert payload["control_summary"]["accepted_fraction"] == 1.0


def test_compare_tile_integration_cli_writes_markdown(tmp_path: Path) -> None:
    run, tile_pack = _write_integration_fixture(tmp_path)
    out = tmp_path / "integration_audit.json"
    markdown = tmp_path / "integration_audit.md"

    assert (
        main(
            [
                "compare-tile-integration",
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
                "--rejection",
                "winsorized_sigma",
                "--low-sigma",
                "1.0",
                "--high-sigma",
                "1.0",
                "--replay-interpolation",
                "bilinear",
                "--focus-frame",
                "F004",
                "--control-frame",
                "F001",
                "--control-frame",
                "F002",
                "--control-frame",
                "F003",
            ]
        )
        == 0
    )

    payload = read_json(out)
    assert payload["tiles"][0]["replayed_frame_count"] == 4
    assert markdown.exists()
