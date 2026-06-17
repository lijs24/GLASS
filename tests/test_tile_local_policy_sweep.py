from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.tile_local_policy_sweep import build_tile_local_policy_sweep


def _write_decision(path: Path, *, accepted: bool, score: float, tile_count: int) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "artifact_type": "tile_local_policy_decision",
            "summary": {
                "accepted": accepted,
                "status": "accepted" if accepted else "rejected",
                "top_score": score,
                "top_verification": f"{path.stem}_verification.json",
                "recommendation": "promote_measured_subset_to_sweep_candidate" if accepted else "hold_policy_subset",
            },
            "candidates": [
                {
                    "verification": f"{path.stem}_verification.json",
                    "replay": f"{path.stem}_replay.json",
                    "candidate": f"{path.stem}_candidate.fits",
                    "tile_count": tile_count,
                    "signed_mean_improved_fraction": 1.0 if accepted else 0.5,
                    "rms_improved_fraction": 1.0,
                    "mean_abs_improved_fraction": 0.5,
                    "mean_abs_delta": -0.001 if accepted else 0.001,
                    "mean_rms_delta": -0.002,
                    "score": score,
                    "passed": accepted,
                }
            ],
        },
    )


def test_tile_local_policy_sweep_ranks_accepted_decisions(tmp_path: Path) -> None:
    rejected = tmp_path / "rejected.json"
    accepted_low = tmp_path / "accepted_low.json"
    accepted_high = tmp_path / "accepted_high.json"
    _write_decision(rejected, accepted=False, score=500.0, tile_count=1)
    _write_decision(accepted_low, accepted=True, score=1000.0, tile_count=1)
    _write_decision(accepted_high, accepted=True, score=1200.0, tile_count=2)

    payload = build_tile_local_policy_sweep([rejected, accepted_low, accepted_high])

    assert payload["summary"]["status"] == "accepted_candidate_available"
    assert payload["summary"]["accepted_decision_count"] == 2
    assert payload["summary"]["top_decision"] == str(accepted_high)
    assert [row["path"] for row in payload["decisions"]] == [str(accepted_high), str(accepted_low), str(rejected)]


def test_cli_tile_local_policy_sweep_writes_outputs(tmp_path: Path) -> None:
    decision = tmp_path / "decision.json"
    out = tmp_path / "sweep.json"
    markdown = tmp_path / "sweep.md"
    _write_decision(decision, accepted=True, score=1200.0, tile_count=2)

    assert (
        main(
            [
                "tile-local-policy-sweep",
                "--decision",
                str(decision),
                "--out",
                str(out),
                "--markdown",
                str(markdown),
                "--fail-on-no-accepted",
            ]
        )
        == 0
    )
    payload = read_json(out)
    assert payload["summary"]["top_decision"] == str(decision)
    assert "Tile-Local Policy Sweep Summary" in markdown.read_text(encoding="utf-8")
