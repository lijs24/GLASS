from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.tile_local_sweep_plan import build_tile_local_sweep_plan


def _write_replay(path: Path, tile_count: int = 3) -> None:
    tiles = []
    for index in range(tile_count):
        x0 = index * 20
        tiles.append(
            {
                "tile_index": index,
                "extent": {"x0": x0, "y0": 0, "x1": x0 + 10, "y1": 10},
                "action": "boost",
                "multiplier": 2.0,
                "moves_toward_reference": True,
                "signed_residual_reference_units_before": -0.01,
                "signed_residual_reference_units_after": -0.005,
                "residual_reduction_fraction": 0.5,
                "canonical_delta_contribution_adu": 1.0 + index,
            }
        )
    write_json(
        path,
        {
            "schema_version": 1,
            "artifact_type": "tile_local_policy_replay",
            "tile_count": tile_count,
            "tiles": tiles,
        },
    )


def test_tile_local_sweep_plan_rewrites_base_run_command(tmp_path: Path) -> None:
    replay = tmp_path / "replay.json"
    base_command = tmp_path / "run_command.txt"
    _write_replay(replay)
    base_command.write_text(
        "glass run --plan plan.json --out old_run "
        "--resident-tile-local-policy-replay old_replay.json --resident-tile-local-policy-mode apply",
        encoding="utf-8",
    )

    payload = build_tile_local_sweep_plan(
        replay,
        root=tmp_path / "sweep",
        max_tiles=[1, 3],
        base_run_command=base_command,
        existing_decisions=[tmp_path / "existing_decision.json"],
    )

    assert payload["artifact_type"] == "tile_local_sweep_plan"
    assert payload["candidate_count"] == 2
    first = payload["candidates"][0]
    assert first["max_tiles"] == 1
    assert "--out" in first["commands"]["run"]
    assert first["run_dir"] in first["commands"]["run"]
    assert first["subset_replay"] in first["commands"]["run"]
    assert str(tmp_path / "existing_decision.json") in payload["final_sweep"]["command"]
    assert payload["planned_decisions"][1].endswith("_tiles3_decision.json")


def test_cli_tile_local_sweep_plan_writes_outputs(tmp_path: Path) -> None:
    replay = tmp_path / "replay.json"
    out = tmp_path / "plan.json"
    markdown = tmp_path / "plan.md"
    _write_replay(replay)

    assert (
        main(
            [
                "tile-local-sweep-plan",
                "--replay",
                str(replay),
                "--root",
                str(tmp_path / "sweep"),
                "--max-tiles",
                "2",
                "--out",
                str(out),
                "--markdown",
                str(markdown),
            ]
        )
        == 0
    )
    payload = read_json(out)
    assert payload["candidate_count"] == 1
    assert payload["candidates"][0]["max_tiles"] == 2
    assert "Tile-Local Sweep Plan" in markdown.read_text(encoding="utf-8")
