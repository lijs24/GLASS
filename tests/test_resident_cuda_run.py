from __future__ import annotations

from pathlib import Path

from gpwbpp.cli import main
from gpwbpp.io.json_io import read_json
from gpwbpp.engine.resident_cuda import _matches_any_token
from tests.conftest import cuda_module_or_skip


def test_cli_resident_cuda_run_smoke(small_fits_dataset, tmp_path: Path):
    cuda_module_or_skip()
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_run"

    assert main(["scan", "--root", str(small_fits_dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--flat-floor",
            "0.05",
            "--resident-registration",
            "translation_preview",
            "--reference-frame-id",
            "light_001",
            "--exclude-frame-id",
            "does_not_exist",
        ]
    ) == 0

    integration = read_json(run / "integration_results.json")
    registration = read_json(run / "registration_results.json")
    state = read_json(run / "run_state.json")
    resident = read_json(run / "resident_artifacts.json")
    assert integration["source_stage"] == "resident_calibrated_stack"
    assert integration["outputs"][0]["backend"] == "cuda_resident_stack"
    assert integration["outputs"][0]["resident_registration"] == "translation_preview"
    assert integration["excluded_frame_tokens"] == ["does_not_exist"]
    assert integration["outputs"][0]["output_diagnostics"]["normalization_probe"]["method"]
    assert registration["source_stage"] == "resident_calibrated_stack"
    assert registration["results"][0]["status"] == "reference"
    assert state["current_stage"] == "integration"
    assert "resident_registration" in state["completed_stages"]
    assert "resident_integration" in state["completed_stages"]
    assert resident["backend"] == "cuda_resident_stack"
    assert resident["policy"]["flat_floor"] == 0.05
    assert resident["artifacts"][0]["resident_registration"]["mode"] == "translation_preview"
    assert resident["artifacts"][0]["output_diagnostics"]["clipping_probe"]["nonfinite_count"] == 0


def test_resident_frame_exclusion_matches_id_name_or_stem():
    frame = {
        "id": "F000196",
        "path": r"C:\data\LIGHT_H_0136.fits",
    }

    assert _matches_any_token(frame, {"F000196"})
    assert _matches_any_token(frame, {"LIGHT_H_0136.fits"})
    assert _matches_any_token(frame, {"LIGHT_H_0136"})
    assert not _matches_any_token(frame, {"LIGHT_H_0137"})
