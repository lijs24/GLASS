from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.stack_engine_contract import build_stack_engine_contract_audit
from glass.synthetic.generator import generate_synthetic_dataset


def test_stack_engine_contract_passes_for_cpu_audit_run(tmp_path: Path):
    data = tmp_path / "data"
    run = tmp_path / "run"
    out = tmp_path / "stack_engine_contract.json"
    markdown = tmp_path / "stack_engine_contract.md"
    generate_synthetic_dataset(data, frames=3, width=24, height=24)

    assert main(["audit", "--root", str(data), "--out", str(run), "--backend", "cpu", "--tile-size", "8"]) == 0
    assert (
        main(
            [
                "stack-engine-contract",
                "--run",
                str(run),
                "--out",
                str(out),
                "--markdown",
                str(markdown),
            ]
        )
        == 0
    )

    audit = read_json(out)
    assert audit["passed"] is True
    assert audit["status"] == "passed"
    assert audit["calibration"]["master_count"] >= 3
    assert all(item["contract_ok"] for item in audit["calibration"]["masters"])
    assert audit["integration"]["output_count"] >= 1
    assert all(item["contract_ok"] for item in audit["integration"]["outputs"])
    adoption = audit["adoption"]
    assert adoption["target_engine"] == "stack_engine_cpu"
    assert adoption["surface_count"] == (
        audit["calibration"]["master_count"] + audit["integration"]["output_count"]
    )
    assert adoption["stack_engine_surface_count"] == adoption["surface_count"]
    assert adoption["cuda_resident_surface_count"] == 0
    assert adoption["phase2_stack_engine_default_gap_count"] == 0
    assert adoption["recommendation"] == "stack_engine_default_ready"
    markdown_text = markdown.read_text(encoding="utf-8")
    assert "GLASS StackEngine Default Contract Audit" in markdown_text
    assert "StackEngine Adoption" in markdown_text


def test_stack_engine_contract_fails_legacy_or_missing_provenance(tmp_path: Path):
    run = tmp_path / "run"
    run.mkdir()
    write_json(
        run / "calibration_artifacts.json",
        {
            "masters": {
                "bias_bad": {
                    "type": "bias",
                    "path": "calib_cache/masters/master_bias_bad.fits",
                    "tile_stack_mode": "legacy_streaming_accumulator",
                    "stack_engine_enabled": False,
                    "stack_engine_fallback_reason": "fixture fallback",
                }
            }
        },
    )
    write_json(
        run / "integration_results.json",
        {
            "outputs": [
                {
                    "filter": "H",
                    "tile_stack_mode": "legacy_streaming_accumulator",
                    "stack_engine_enabled": False,
                }
            ]
        },
    )

    audit = build_stack_engine_contract_audit(run)
    checks = {item["name"]: item for item in audit["checks"]}
    assert audit["passed"] is False
    assert checks["calibration_masters_use_stack_engine"]["passed"] is False
    assert checks["integration_outputs_use:stack_engine_cpu"]["passed"] is False
    assert audit["adoption"]["phase2_stack_engine_default_gap_count"] == 2
    assert audit["adoption"]["recommendation"] == "stack_engine_contract_gaps_remain"


def test_stack_engine_contract_requires_embedded_result_contract(tmp_path: Path):
    run = tmp_path / "run"
    run.mkdir()
    legacy_provenance = {
        "input_samples": 16,
        "output_dq_summary": {"valid": 4},
        "output_coverage_zero_pixels": 0,
    }
    summary = {
        "source_schema": "stack_engine_dq_provenance",
        "engine": "stack_engine_cpu",
        "stage": "integration",
        "input_samples": 16,
    }
    write_json(
        run / "integration_results.json",
        {
            "outputs": [
                {
                    "filter": "H",
                    "tile_stack_mode": "stack_engine_cpu",
                    "stack_engine_enabled": True,
                    "stack_engine_dq_provenance": legacy_provenance,
                    "dq_provenance_summary": summary,
                }
            ]
        },
    )

    audit = build_stack_engine_contract_audit(run, scope="integration")
    checks = {item["name"]: item for item in audit["checks"]}

    assert audit["passed"] is False
    assert audit["integration"]["outputs"][0]["result_contract_passed"] is False
    assert checks["integration_outputs_use:stack_engine_cpu"]["passed"] is False
    assert audit["adoption"]["phase2_stack_engine_default_gap_count"] == 1
    assert audit["adoption"]["gap_surfaces"][0]["gap_reason"] == "missing_or_failed_result_contract"


def test_stack_engine_contract_tracks_resident_cuda_adoption_gap(tmp_path: Path):
    run = tmp_path / "run"
    run.mkdir()
    write_json(
        run / "integration_results.json",
        {
            "outputs": [
                {
                    "filter": "H",
                    "backend": "cuda_resident_stack",
                    "dq_provenance_summary": {
                        "source_schema": "resident_dq_coverage_provenance",
                        "engine": "cuda_resident_stack",
                        "stage": "integration",
                        "active_frame_count": 193,
                    },
                }
            ]
        },
    )

    audit = build_stack_engine_contract_audit(
        run,
        scope="integration",
        expected_integration_engine="cuda_resident_stack",
    )
    checks = {item["name"]: item for item in audit["checks"]}

    assert audit["passed"] is True
    assert checks["integration_outputs_use:cuda_resident_stack"]["passed"] is True
    adoption = audit["adoption"]
    assert adoption["surface_count"] == 1
    assert adoption["cuda_resident_surface_count"] == 1
    assert adoption["stack_engine_surface_count"] == 0
    assert adoption["phase2_stack_engine_default_gap_count"] == 1
    assert adoption["gap_surfaces"][0]["gap_reason"] == "resident_cuda_surface"
    assert adoption["recommendation"] == "resident_cuda_surfaces_remain"
