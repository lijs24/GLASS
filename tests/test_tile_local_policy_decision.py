from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.tile_local_policy_decision import build_tile_local_policy_decision


def _write_verification(
    path: Path,
    *,
    signed_tiles: int,
    rms_tiles: int,
    mean_abs_delta: float,
    rms_delta: float,
) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "artifact_type": "tile_local_apply_verification",
            "baseline": "baseline.fits",
            "candidate": "candidate.fits",
            "reference": "reference.xisf",
            "replay": "subset.json",
            "summary": {
                "status": "passed" if signed_tiles == 2 and rms_tiles == 2 and mean_abs_delta < 0 and rms_delta < 0 else "failed",
                "passed": signed_tiles == 2 and rms_tiles == 2 and mean_abs_delta < 0 and rms_delta < 0,
                "tile_count": 2,
                "signed_mean_improved_tiles": signed_tiles,
                "rms_improved_tiles": rms_tiles,
                "mean_abs_improved_tiles": 1,
                "mean_abs_delta": mean_abs_delta,
                "mean_rms_delta": rms_delta,
                "recommendation": "measured_local_improvement",
            },
            "tiles": [],
        },
    )


def _write_pass_artifact(path: Path, *, kind: str = "apply") -> None:
    payload = {"schema_version": 1, "status": "passed", "passed": True}
    if kind == "apply":
        payload["artifact_type"] = "tile_local_apply_experiment"
        payload["summary"] = {"passed": True, "status": "passed"}
    write_json(path, payload)


def test_tile_local_policy_decision_accepts_best_measured_candidate(tmp_path: Path) -> None:
    accepted = tmp_path / "accepted.json"
    rejected = tmp_path / "rejected.json"
    apply = tmp_path / "apply.json"
    acceptance = tmp_path / "acceptance.json"
    _write_verification(accepted, signed_tiles=2, rms_tiles=2, mean_abs_delta=-1e-5, rms_delta=-2e-5)
    _write_verification(rejected, signed_tiles=1, rms_tiles=2, mean_abs_delta=-2e-5, rms_delta=-1e-5)
    _write_pass_artifact(apply, kind="apply")
    _write_pass_artifact(acceptance, kind="acceptance")

    payload = build_tile_local_policy_decision(
        [rejected, accepted],
        apply_experiment=apply,
        acceptance_audit=acceptance,
    )

    assert payload["summary"]["accepted"] is True
    assert payload["summary"]["status"] == "accepted"
    assert payload["summary"]["top_verification"] == str(accepted)
    assert payload["candidates"][0]["passed"] is True
    assert payload["candidates"][1]["passed"] is False


def test_cli_tile_local_policy_decision_writes_outputs(tmp_path: Path) -> None:
    verification = tmp_path / "verification.json"
    apply = tmp_path / "apply.json"
    acceptance = tmp_path / "acceptance.json"
    out = tmp_path / "decision.json"
    markdown = tmp_path / "decision.md"
    _write_verification(verification, signed_tiles=2, rms_tiles=2, mean_abs_delta=-1e-5, rms_delta=-2e-5)
    _write_pass_artifact(apply, kind="apply")
    _write_pass_artifact(acceptance, kind="acceptance")

    assert (
        main(
            [
                "tile-local-policy-decision",
                "--verification",
                str(verification),
                "--apply-experiment",
                str(apply),
                "--acceptance-audit",
                str(acceptance),
                "--out",
                str(out),
                "--markdown",
                str(markdown),
                "--fail-on-rejected",
            ]
        )
        == 0
    )

    payload = read_json(out)
    assert payload["summary"]["status"] == "accepted"
    assert "Tile-Local Policy Decision" in markdown.read_text(encoding="utf-8")
