from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.fits_io import write_fits_data
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
    assert all(item["science_contract_ok"] for item in audit["calibration"]["masters"])
    assert all(item["science_contract"]["passed"] for item in audit["calibration"]["masters"])
    assert audit["integration"]["output_count"] >= 1
    assert all(item["contract_ok"] for item in audit["integration"]["outputs"])
    checks = {item["name"]: item for item in audit["checks"]}
    assert checks["calibration_masters_science_auditable"]["passed"] is True
    adoption = audit["adoption"]
    assert adoption["target_engine"] == "stack_engine_cpu"
    assert adoption["surface_count"] == (
        audit["calibration"]["master_count"] + audit["integration"]["output_count"]
    )
    assert adoption["stack_engine_surface_count"] == adoption["surface_count"]
    assert adoption["cuda_resident_surface_count"] == 0
    assert adoption["phase2_stack_engine_default_gap_count"] == 0
    assert adoption["recommendation"] == "stack_engine_default_ready"
    promotion = audit["default_promotion"]
    assert promotion["ready"] is True
    assert promotion["status"] == "ready"
    assert promotion["actual_scope"] == "all"
    assert promotion["blocker_count"] == 0
    markdown_text = markdown.read_text(encoding="utf-8")
    assert "GLASS StackEngine Default Contract Audit" in markdown_text
    assert "StackEngine Adoption" in markdown_text
    assert "Default Promotion Guard" in markdown_text


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
    blockers = {item["name"] for item in audit["default_promotion"]["blockers"]}
    assert audit["default_promotion"]["ready"] is False
    assert "stack_engine_contract_failed" in blockers
    assert "phase2_stack_engine_default_gaps" in blockers
    assert "adoption_recommendation_not_ready" in blockers


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
    blockers = {item["name"] for item in audit["default_promotion"]["blockers"]}
    assert "scope_not_all" in blockers
    assert "missing_calibration_surface" in blockers
    assert "phase2_stack_engine_default_gaps" in blockers


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
    promotion = audit["default_promotion"]
    blockers = {item["name"] for item in promotion["blockers"]}
    assert promotion["ready"] is False
    assert promotion["status"] == "blocked"
    assert "scope_not_all" in blockers
    assert "missing_calibration_surface" in blockers
    assert "phase2_stack_engine_default_gaps" in blockers


def test_stack_engine_contract_accepts_resident_result_contract_parity(tmp_path: Path):
    run = tmp_path / "run"
    run.mkdir()
    resident_contract = {
        "artifact_type": "resident_cuda_result_contract",
        "passed": True,
        "outputs": [
            {
                "index": 0,
                "filter": "H",
                "passed": True,
                "status": "passed",
                "contract_type": "resident_cuda_result_contract",
                "active_frame_count": 193,
                "frame_count": 200,
                "checks": [
                    {"name": "resident_identity", "passed": True},
                    {"name": "required_maps_exist", "passed": True},
                ],
            }
        ],
    }
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
        resident_result_contract=resident_contract,
    )

    output = audit["integration"]["outputs"][0]
    surface = audit["adoption"]["surfaces"][0]
    promotion_blockers = {item["name"] for item in audit["default_promotion"]["blockers"]}
    assert audit["passed"] is True
    assert audit["resident_result_contract_attached"] is True
    assert output["resident_result_contract_passed"] is True
    assert output["result_contract_passed"] is True
    assert output["resident_result_contract_check_count"] == 2
    assert surface["engine_family"] == "cuda_resident_stack"
    assert surface["stack_engine_contract_ready"] is True
    assert surface["phase2_stack_engine_default_gap"] is False
    assert audit["adoption"]["phase2_stack_engine_default_gap_count"] == 0
    assert audit["adoption"]["recommendation"] == "stack_engine_default_ready"
    assert "phase2_stack_engine_default_gaps" not in promotion_blockers
    assert "adoption_recommendation_not_ready" not in promotion_blockers
    assert "scope_not_all" in promotion_blockers
    assert "missing_calibration_surface" in promotion_blockers


def test_stack_engine_contract_accepts_resident_calibration_for_default_ready(tmp_path: Path):
    run = tmp_path / "run"
    run.mkdir()
    resident_calibration_contract = {
        "artifact_type": "resident_cuda_calibration_contract",
        "passed": True,
        "outputs": [
            {
                "index": 0,
                "filter": "H",
                "passed": True,
                "status": "passed",
                "master_path": str(run / "integration" / "resident_master_H.fits"),
                "master_path_exists": True,
                "frame_count": 200,
                "set_count": 1,
                "bias_count": 20,
                "dark_count": 20,
                "flat_count": 20,
                "calibration_group_policy": "planner_matching_groups_per_light",
                "checks": [{"name": "resident_output_contracts_passed", "passed": True}],
            }
        ],
    }
    resident_result_contract = {
        "artifact_type": "resident_cuda_result_contract",
        "passed": True,
        "outputs": [
            {
                "index": 0,
                "filter": "H",
                "passed": True,
                "status": "passed",
                "active_frame_count": 193,
                "frame_count": 200,
                "checks": [{"name": "resident_identity", "passed": True}],
            }
        ],
    }
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
        scope="all",
        expected_integration_engine="cuda_resident_stack",
        resident_calibration_contract=resident_calibration_contract,
        resident_result_contract=resident_result_contract,
    )

    promotion = audit["default_promotion"]
    assert audit["passed"] is True
    assert audit["resident_calibration_contract_attached"] is True
    assert audit["resident_result_contract_attached"] is True
    assert audit["calibration"]["master_count"] == 1
    assert audit["calibration"]["masters"][0]["resident_calibration_contract_passed"] is True
    assert audit["adoption"]["phase2_stack_engine_default_gap_count"] == 0
    assert audit["adoption"]["cuda_resident_surface_count"] == 2
    assert promotion["ready"] is True
    assert promotion["status"] == "ready"
    assert promotion["blocker_count"] == 0


def test_stack_engine_contract_require_default_ready_rejects_resident_only_gap(tmp_path: Path):
    run = tmp_path / "run"
    run.mkdir()
    out = tmp_path / "stack_engine_contract.json"
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

    assert (
        main(
            [
                "stack-engine-contract",
                "--run",
                str(run),
                "--scope",
                "integration",
                "--expected-integration-engine",
                "cuda_resident_stack",
                "--require-default-ready",
                "--out",
                str(out),
            ]
        )
        == 3
    )

    audit = read_json(out)
    assert audit["passed"] is True
    assert audit["default_promotion"]["ready"] is False
    assert audit["default_promotion"]["status"] == "blocked"


def test_stack_engine_contract_cli_uses_resident_result_contract_json(tmp_path: Path):
    run = tmp_path / "run"
    run.mkdir()
    resident_contract = tmp_path / "resident_result_contract.json"
    out = tmp_path / "stack_engine_contract.json"
    write_json(
        resident_contract,
        {
            "artifact_type": "resident_cuda_result_contract",
            "passed": True,
            "outputs": [
                {
                    "index": 0,
                    "filter": "H",
                    "passed": True,
                    "status": "passed",
                    "checks": [{"name": "resident_identity", "passed": True}],
                }
            ],
        },
    )
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
                    },
                }
            ]
        },
    )

    assert (
        main(
            [
                "stack-engine-contract",
                "--run",
                str(run),
                "--scope",
                "integration",
                "--expected-integration-engine",
                "cuda_resident_stack",
                "--resident-result-contract-json",
                str(resident_contract),
                "--out",
                str(out),
            ]
        )
        == 0
    )

    audit = read_json(out)
    assert audit["resident_result_contract_attached"] is True
    assert audit["integration"]["outputs"][0]["resident_result_contract_passed"] is True
    assert audit["adoption"]["phase2_stack_engine_default_gap_count"] == 0


def test_stack_engine_contract_cli_uses_resident_calibration_contract_json(tmp_path: Path):
    run = tmp_path / "run"
    run.mkdir()
    resident_calibration_contract = tmp_path / "resident_calibration_contract.json"
    resident_result_contract = tmp_path / "resident_result_contract.json"
    out = tmp_path / "stack_engine_contract.json"
    write_json(
        resident_calibration_contract,
        {
            "artifact_type": "resident_cuda_calibration_contract",
            "passed": True,
            "outputs": [
                {
                    "index": 0,
                    "filter": "H",
                    "passed": True,
                    "status": "passed",
                    "frame_count": 200,
                    "set_count": 1,
                    "bias_count": 20,
                    "dark_count": 20,
                    "flat_count": 20,
                    "checks": [{"name": "resident_output_contracts_passed", "passed": True}],
                }
            ],
        },
    )
    write_json(
        resident_result_contract,
        {
            "artifact_type": "resident_cuda_result_contract",
            "passed": True,
            "outputs": [
                {
                    "index": 0,
                    "filter": "H",
                    "passed": True,
                    "status": "passed",
                    "checks": [{"name": "resident_identity", "passed": True}],
                }
            ],
        },
    )
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
                    },
                }
            ]
        },
    )

    assert (
        main(
            [
                "stack-engine-contract",
                "--run",
                str(run),
                "--scope",
                "all",
                "--expected-integration-engine",
                "cuda_resident_stack",
                "--resident-calibration-contract-json",
                str(resident_calibration_contract),
                "--resident-result-contract-json",
                str(resident_result_contract),
                "--out",
                str(out),
                "--require-default-ready",
            ]
        )
        == 0
    )

    audit = read_json(out)
    assert audit["resident_calibration_contract_attached"] is True
    assert audit["default_promotion"]["ready"] is True


def test_stack_engine_contract_requires_master_stats_and_semantics(tmp_path: Path):
    run = tmp_path / "run"
    master_dir = run / "calib_cache" / "masters"
    master_dir.mkdir(parents=True)
    master_path = master_dir / "master_bias_bad.fits"
    write_fits_data(master_path, [[1.0, 2.0], [3.0, 4.0]])
    provenance = {
        "schema_version": 1,
        "input_samples": 8,
        "output_dq_summary": None,
        "output_coverage_zero_pixels": 0,
        "result_contract": {
            "schema_version": 1,
            "contract_type": "stack_engine_result_contract",
            "passed": True,
            "status": "passed",
            "checks": [{"name": "fixture", "passed": True}],
        },
    }
    write_json(
        run / "calibration_artifacts.json",
        {
            "masters": {
                "bias_bad": {
                    "type": "bias",
                    "path": str(master_path),
                    "tile_stack_mode": "stack_engine_cpu",
                    "stack_engine_enabled": True,
                    "stack_engine_fallback_reason": None,
                    "stack_engine_dq_provenance": provenance,
                    "dq_provenance_summary": {
                        "source_schema": "stack_engine_dq_provenance",
                        "engine": "stack_engine_cpu",
                        "stage": "master_calibration",
                        "item": "bias_bad",
                        "input_samples": 8,
                    },
                }
            }
        },
    )

    audit = build_stack_engine_contract_audit(run, scope="calibration")
    checks = {item["name"]: item for item in audit["checks"]}
    master = audit["calibration"]["masters"][0]

    assert audit["passed"] is False
    assert master["result_contract_passed"] is True
    assert master["science_contract_ok"] is False
    assert master["science_contract"]["stats"]["missing_keys"] == ["min", "max", "mean", "median", "std"]
    assert checks["calibration_masters_science_auditable"]["passed"] is False
    assert checks["calibration_masters_use_stack_engine"]["passed"] is False
    assert audit["adoption"]["gap_surfaces"][0]["gap_reason"] == "master_calibration_science_contract_failed"
