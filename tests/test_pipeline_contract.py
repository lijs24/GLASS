from __future__ import annotations

from pathlib import Path

import numpy as np

from glass.cli import main
from glass.engine.contracts import DQFlag
from glass.engine.rejection import (
    RESIDENT_WINSORIZED_SIGMA_ALGORITHM,
    resident_rejection_descriptor,
)
from glass.engine.resident_calibration_artifacts import write_resident_calibration_artifacts
from glass.io.fits_io import write_fits_data
from glass.io.json_io import read_json, write_json
from glass.report.html_report import write_html_report
from glass.report.pipeline_contract import build_pipeline_contract_audit
from glass.synthetic.generator import generate_synthetic_dataset


def _write_resident_pipeline_run(
    path: Path,
    *,
    missing_source_terms: bool = False,
    sample_closure_status: str | None = None,
    omit_rejection_semantics: bool = False,
    resident_artifact_legacy_rejection_semantics: bool = False,
) -> None:
    integration_dir = path / "integration"
    integration_dir.mkdir(parents=True)
    master = np.ones((2, 2), dtype=np.float32)
    weight = np.ones((2, 2), dtype=np.float32)
    coverage = np.array([[0, 1], [1, 1]], dtype=np.float32)
    low = np.array([[0, 1], [0, 0]], dtype=np.float32)
    high = np.array([[0, 0], [2, 0]], dtype=np.float32)
    dq = np.array(
        [
            [int(DQFlag.NO_DATA), int(DQFlag.LOW_REJECTED)],
            [int(DQFlag.HIGH_REJECTED), 0],
        ],
        dtype=np.float32,
    )
    for name, data in {
        "master_H.fits": master,
        "weight_H.fits": weight,
        "coverage_H.fits": coverage,
        "dq_H.fits": dq,
        "low_H.fits": low,
        "high_H.fits": high,
    }.items():
        write_fits_data(integration_dir / name, data)
    source_terms = [] if missing_source_terms else [
        "post_rejection_coverage",
        "low_rejection",
        "high_rejection",
        "geometric_warp_coverage",
    ]
    dq_summary = {"valid": 1, "no_data": 1, "low_rejected": 1, "high_rejected": 1}
    provenance_summary = {
        "source_schema": "resident_dq_coverage_provenance",
        "stage": "integration",
        "engine": "cuda_resident_stack",
        "active_frame_count": 3,
        "source_terms": source_terms,
        "rejected_samples": 3,
        "output_dq_summary": dq_summary,
    }
    if sample_closure_status is not None:
        provenance_summary["sample_accounting_closure"] = {
            "status": sample_closure_status,
            "input_valid_samples_before_rejection": 9,
            "valid_samples_after_rejection": 6,
            "rejected_samples": 3,
            "valid_rejection_match": sample_closure_status == "passed",
        }
    output = {
        "filter": "H",
        "backend": "cuda_resident_stack",
        "memory_mode": "resident",
        "frame_count": 3,
        "master_path": str(integration_dir / "master_H.fits"),
        "weight_map_path": str(integration_dir / "weight_H.fits"),
        "coverage_map_path": str(integration_dir / "coverage_H.fits"),
        "dq_map_path": str(integration_dir / "dq_H.fits"),
        "low_rejection_map_path": str(integration_dir / "low_H.fits"),
        "high_rejection_map_path": str(integration_dir / "high_H.fits"),
        "dq_summary": dq_summary,
        "dq_coverage_provenance": {
            "available": True,
            "active_frame_count": 3,
            "geometric_frame_count_matches_active": True,
            "rejected_sample_count": 3.0,
            "rejected_sample_count_source": "low_high_rejection_maps",
            "source_terms": source_terms,
        },
        "dq_provenance_summary": provenance_summary,
        "geometric_warp_coverage": {
            "available": True,
            "frame_count": 3,
            "frame_count_matches_active": True,
        },
        "output_map_policy": {
            "available": [
                "master",
                "weight",
                "coverage",
                "dq",
                "low_rejection",
                "high_rejection",
            ],
            "written": [
                "master",
                "weight",
                "coverage",
                "dq",
                "low_rejection",
                "high_rejection",
            ],
            "skipped": [],
        },
    }
    if not omit_rejection_semantics:
        output["integration_rejection"] = resident_rejection_descriptor(
            "winsorized_sigma",
            3.0,
            3.0,
        )
    write_json(
        path / "integration_results.json",
        {"rejection": "winsorized_sigma", "outputs": [output]},
    )
    if resident_artifact_legacy_rejection_semantics:
        write_json(
            path / "resident_artifacts.json",
            {
                "schema_version": 1,
                "backend": "cuda_resident_stack",
                "artifacts": [
                    {
                        "filter": "H",
                        "integration_rejection": {
                            "mode": "winsorized_sigma",
                            "low_sigma": 3.0,
                            "high_sigma": 3.0,
                            "algorithm": RESIDENT_WINSORIZED_SIGMA_ALGORITHM,
                        },
                    }
                ],
            },
        )


def _write_nonresident_cuda_fast_path_pipeline_run(path: Path, *, explicit: bool) -> None:
    integration_dir = path / "integration"
    integration_dir.mkdir(parents=True)
    master = np.ones((2, 2), dtype=np.float32)
    weight = np.ones((2, 2), dtype=np.float32)
    coverage = np.ones((2, 2), dtype=np.float32)
    dq = np.zeros((2, 2), dtype=np.float32)
    for name, data in {
        "master_H.fits": master,
        "weight_H.fits": weight,
        "coverage_H.fits": coverage,
        "dq_H.fits": dq,
    }.items():
        write_fits_data(integration_dir / name, data)
    engine_selection = {
        "default_engine": "stack_engine_cpu",
        "actual_backend": "cuda",
        "use_stack_engine": False,
        "tile_stack_mode": "cuda_streaming_accumulator_fast_path",
        "backend": "auto",
        "cuda_available": True,
        "cuda_fast_path_eligible": True,
        "explicit_cuda_fast_path": explicit,
        "allow_cuda_streaming_accumulator_fast_path": explicit,
        "rejection": "none",
        "reason": "explicit_cuda_fast_path_requested"
        if explicit
        else "legacy_implicit_cuda_fast_path_fixture",
    }
    write_json(
        path / "integration_results.json",
        {
            "rejection": "none",
            "integration_engine_policy": engine_selection,
            "outputs": [
                {
                    "filter": "H",
                    "backend": "cuda",
                    "frame_count": 3,
                    "master_path": str(integration_dir / "master_H.fits"),
                    "weight_map_path": str(integration_dir / "weight_H.fits"),
                    "coverage_map_path": str(integration_dir / "coverage_H.fits"),
                    "dq_map_path": str(integration_dir / "dq_H.fits"),
                    "tile_stack_mode": "cuda_streaming_accumulator_fast_path",
                    "stack_engine_enabled": False,
                    "engine_selection": engine_selection,
                    "dq_summary": {"valid": 4, "no_data": 0},
                    "dq_provenance_summary": {
                        "source_schema": "cuda_streaming_accumulator_dq_provenance",
                        "stage": "integration",
                        "engine": "cuda_streaming_accumulator_fast_path",
                        "output_dq_summary": {"valid": 4, "no_data": 0},
                    },
                    "output_map_policy": {
                        "available": ["master", "weight", "coverage", "dq"],
                        "written": ["master", "weight", "coverage", "dq"],
                        "skipped": ["low_rejection", "high_rejection"],
                    },
                }
            ],
        },
    )


def test_pipeline_contract_passes_for_cpu_audit_run(tmp_path: Path):
    data = tmp_path / "data"
    run = tmp_path / "run"
    local_norm_contract = tmp_path / "local_norm_contract.json"
    out = tmp_path / "pipeline_contract.json"
    markdown = tmp_path / "pipeline_contract.md"
    generate_synthetic_dataset(data, frames=3, width=24, height=24)

    assert main(["audit", "--root", str(data), "--out", str(run), "--backend", "cpu", "--tile-size", "8"]) == 0
    assert (
        main(
            [
                "local-norm-contract",
                "--run",
                str(run),
                "--out",
                str(local_norm_contract),
                "--fail-on-failed",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "pipeline-contract",
                "--run",
                str(run),
                "--out",
                str(out),
                "--markdown",
                str(markdown),
                "--local-norm-contract-json",
                str(local_norm_contract),
            ]
        )
        == 0
    )

    audit = read_json(out)
    assert audit["passed"] is True
    checks = {item["name"]: item for item in audit["checks"]}
    assert checks["integration_output_maps_available"]["passed"] is True
    assert checks["integration_dq_contract"]["passed"] is True
    assert checks["integration_default_engine_policy"]["passed"] is True
    assert checks["stack_engine_runtime_default_path"]["passed"] is True
    assert checks["calibration_master_surface_contract"]["passed"] is True
    assert checks["calibrated_light_dq_contract"]["passed"] is True
    assert checks["local_normalization_contract"]["passed"] is True
    assert checks["local_normalization_continuous_contract_audit"]["passed"] is True
    assert checks["warp_outputs_have_dq_and_coverage"]["passed"] is True
    assert audit["artifacts"]["local_norm_contract"]["attached"] is True
    assert audit["artifacts"]["local_norm_contract"]["passed"] is True
    assert audit["local_normalization"]["contract_audit_attached"] is True
    assert audit["local_normalization"]["contract_audit_passed"] is True
    assert audit["integration"]["engine_policy"]["top_level"]["default_engine"] == "stack_engine_cpu"
    assert all(
        item["status"] == "stack_engine_default"
        for item in audit["integration"]["engine_policy"]["outputs"]
        if item["required"]
    )
    runtime_default = audit["stack_engine_runtime_default"]
    assert runtime_default["status"] == "passed"
    assert runtime_default["master_count"] >= 3
    assert runtime_default["legacy_master_count"] == 0
    assert runtime_default["integration_stack_engine_default_count"] >= 1
    assert runtime_default["failed_masters"] == []
    assert audit["calibration"]["master_count"] >= 3
    assert audit["calibration"]["calibrated_light_count"] >= 3
    assert all(item["contract_ok"] for item in audit["calibration"]["masters"])
    assert all(item["contract_ok"] for item in audit["calibration"]["calibrated_lights"])
    assert "GLASS Pipeline Invariant Contract Audit" in markdown.read_text(encoding="utf-8")
    assert "Integration Engine Policy" in markdown.read_text(encoding="utf-8")
    assert "StackEngine Runtime Default Path" in markdown.read_text(encoding="utf-8")


def test_pipeline_contract_pixel_verification_passes_for_cpu_audit_run(tmp_path: Path):
    data = tmp_path / "data"
    run = tmp_path / "run"
    out = tmp_path / "pipeline_contract.json"
    generate_synthetic_dataset(data, frames=3, width=24, height=24)

    assert main(["audit", "--root", str(data), "--out", str(run), "--backend", "cpu", "--tile-size", "8"]) == 0
    assert (
        main(
            [
                "pipeline-contract",
                "--run",
                str(run),
                "--out",
                str(out),
                "--pixel-verify",
                "--pixel-verify-tile-size",
                "7",
            ]
        )
        == 0
    )

    audit = read_json(out)
    checks = {item["name"]: item for item in audit["checks"]}
    assert audit["passed"] is True
    assert audit["pixel_verification"]["enabled"] is True
    assert audit["pixel_verification"]["tile_size"] == 7
    assert checks["integration_stack_result_contract"]["passed"] is True
    assert audit["integration"]["outputs"][0]["stack_result_contract"]["passed"] is True
    assert checks["integration_dq_map_pixels_match_summary"]["passed"] is True
    assert checks["integration_coverage_map_pixels_match_dq"]["passed"] is True
    assert checks["integration_rejection_map_pixels_match_dq"]["passed"] is True
    assert checks["integration_rejection_sample_counts_match_maps"]["passed"] is True


def test_pipeline_contract_pixel_verification_fails_corrupt_dq_summary(tmp_path: Path):
    run = tmp_path / "run"
    integration_dir = run / "integration"
    integration_dir.mkdir(parents=True)
    dq = np.array([[0, 0], [1, 0]], dtype=np.float32)
    coverage = np.array([[1, 1], [0, 1]], dtype=np.float32)
    zeros = np.zeros((2, 2), dtype=np.float32)
    ones = np.ones((2, 2), dtype=np.float32)
    for name, data in {
        "master_H.fits": ones,
        "weight_H.fits": ones,
        "coverage_H.fits": coverage,
        "dq_H.fits": dq,
        "low_H.fits": zeros,
        "high_H.fits": zeros,
    }.items():
        write_fits_data(integration_dir / name, data)
    write_json(
        run / "integration_results.json",
        {
            "rejection": "none",
            "outputs": [
                {
                    "filter": "H",
                    "master_path": str(integration_dir / "master_H.fits"),
                    "weight_map_path": str(integration_dir / "weight_H.fits"),
                    "coverage_map_path": str(integration_dir / "coverage_H.fits"),
                    "dq_map_path": str(integration_dir / "dq_H.fits"),
                    "low_rejection_map_path": str(integration_dir / "low_H.fits"),
                    "high_rejection_map_path": str(integration_dir / "high_H.fits"),
                    "dq_summary": {"valid": 4, "no_data": 0},
                    "dq_provenance_summary": {
                        "engine": "stack_engine_cpu",
                        "output_dq_summary": {"valid": 4, "no_data": 0},
                    },
                }
            ],
        },
    )

    audit = build_pipeline_contract_audit(run, pixel_verify=True, pixel_verify_tile_size=1)
    checks = {item["name"]: item for item in audit["checks"]}
    assert audit["passed"] is False
    assert checks["integration_dq_map_pixels_match_summary"]["passed"] is False
    assert checks["integration_coverage_map_pixels_match_dq"]["passed"] is False


def test_pipeline_contract_passes_resident_result_contract(tmp_path: Path):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run)

    audit = build_pipeline_contract_audit(run)
    checks = {item["name"]: item for item in audit["checks"]}

    assert audit["passed"] is True
    assert checks["integration_resident_result_contract"]["passed"] is True
    assert checks["integration_resident_result_contract"]["evidence"]["required_count"] == 1
    resident_contract = audit["integration"]["outputs"][0]["resident_result_contract"]
    assert resident_contract["required"] is True
    assert resident_contract["passed"] is True
    assert resident_contract["contract"]["contract_type"] == "resident_cuda_result_contract"


def test_pipeline_contract_uses_resident_artifact_winsorized_semantics_handoff(
    tmp_path: Path,
):
    run = tmp_path / "run"
    _write_resident_pipeline_run(
        run,
        omit_rejection_semantics=True,
        resident_artifact_legacy_rejection_semantics=True,
    )

    audit = build_pipeline_contract_audit(run, pixel_verify=True, pixel_verify_tile_size=1)
    checks = {item["name"]: item for item in audit["checks"]}
    contract = audit["integration"]["outputs"][0]["resident_result_contract"]["contract"]
    semantics = contract["rejection_semantics"]

    assert audit["passed"] is True
    assert checks["integration_resident_result_contract"]["passed"] is True
    assert semantics["descriptor_source"] == "resident_artifacts.integration_rejection"
    assert semantics["integration_results_descriptor_present"] is False
    assert semantics["resident_artifacts_descriptor_present"] is True
    assert semantics["legacy_completion_applied"] is True
    assert semantics["descriptor"]["resident_winsorized_mode"] == "fast_approx"
    assert semantics["descriptor"]["cpu_baseline_parity"] is False


def test_pipeline_contract_allows_explicit_nonresident_cuda_fast_path(tmp_path: Path):
    run = tmp_path / "run"
    _write_nonresident_cuda_fast_path_pipeline_run(run, explicit=True)

    audit = build_pipeline_contract_audit(run)
    checks = {item["name"]: item for item in audit["checks"]}
    engine_policy = audit["integration"]["engine_policy"]
    runtime_default = audit["stack_engine_runtime_default"]

    assert audit["passed"] is True
    assert checks["integration_default_engine_policy"]["passed"] is True
    assert checks["stack_engine_runtime_default_path"]["passed"] is True
    assert engine_policy["non_resident_count"] == 1
    assert engine_policy["failed"] == []
    assert engine_policy["outputs"][0]["status"] == "explicit_cuda_fast_path"
    assert runtime_default["explicit_cuda_fast_path_count"] == 1
    assert runtime_default["integration_stack_engine_default_count"] == 0
    assert runtime_default["failed_outputs"] == []


def test_pipeline_contract_blocks_implicit_nonresident_cuda_fast_path(tmp_path: Path):
    run = tmp_path / "run"
    _write_nonresident_cuda_fast_path_pipeline_run(run, explicit=False)

    audit = build_pipeline_contract_audit(run)
    checks = {item["name"]: item for item in audit["checks"]}
    engine_policy = audit["integration"]["engine_policy"]

    assert audit["passed"] is False
    assert checks["integration_default_engine_policy"]["passed"] is False
    assert checks["integration_default_engine_policy"]["evidence"]["failed"] == [
        {
            "item": "H",
            "status": "implicit_cuda_fast_path",
            "backend": "cuda",
            "tile_stack_mode": "cuda_streaming_accumulator_fast_path",
            "failures": ["cuda_fast_path_not_explicit"],
        }
    ]
    assert engine_policy["failed"][0]["status"] == "implicit_cuda_fast_path"
    assert engine_policy["outputs"][0]["selection_explicit_cuda_fast_path"] is False


def test_pipeline_contract_blocks_legacy_master_runtime_default(tmp_path: Path):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run)
    calib_dir = run / "calib_cache"
    master_dir = calib_dir / "masters"
    light_dir = calib_dir / "calibrated"
    dq_dir = calib_dir / "dq"
    master_dir.mkdir(parents=True)
    light_dir.mkdir()
    dq_dir.mkdir()
    master_path = master_dir / "master_bias_legacy.fits"
    light_path = light_dir / "calibrated_L1.fits"
    dq_path = dq_dir / "dq_calibrated_L1.fits"
    write_fits_data(master_path, np.ones((2, 2), dtype=np.float32))
    write_fits_data(light_path, np.ones((2, 2), dtype=np.float32))
    write_fits_data(dq_path, np.zeros((2, 2), dtype=np.float32))
    write_json(
        run / "calibration_artifacts.json",
        {
            "masters": {
                "bias_legacy": {
                    "path": str(master_path),
                    "stats": {
                        "min": 1.0,
                        "max": 1.0,
                        "mean": 1.0,
                        "median": 1.0,
                        "std": 0.0,
                    },
                    "type": "bias",
                    "streaming": True,
                    "tile_stack_mode": "legacy_streaming_accumulator",
                    "stack_engine_enabled": False,
                    "stack_engine_fallback_reason": "diagnostic fixture",
                    "master_rejection": "none",
                    "tile_size": 2,
                }
            },
            "calibrated_lights": [
                {
                    "frame_id": "L1",
                    "path": str(light_path),
                    "dq_mask_path": str(dq_path),
                    "dq_summary": {"valid": 4, "no_data": 0},
                    "tile_count": 1,
                    "tile_size": 2,
                }
            ],
        },
    )

    audit = build_pipeline_contract_audit(run)
    checks = {item["name"]: item for item in audit["checks"]}
    runtime_default = audit["stack_engine_runtime_default"]

    assert audit["passed"] is False
    assert checks["calibration_master_surface_contract"]["passed"] is True
    assert checks["stack_engine_runtime_default_path"]["passed"] is False
    assert runtime_default["legacy_master_count"] == 1
    assert runtime_default["failed_masters"][0]["name"] == "bias_legacy"
    assert "legacy_master_stack_mode" in runtime_default["failed_masters"][0]["failures"]


def test_pipeline_contract_surfaces_sample_accounting_closure(tmp_path: Path):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run, sample_closure_status="passed")

    audit = build_pipeline_contract_audit(run)
    checks = {item["name"]: item for item in audit["checks"]}
    closure = audit["integration"]["outputs"][0]["sample_accounting_closure"]

    assert audit["passed"] is True
    assert checks["integration_sample_accounting_closure"]["passed"] is True
    assert checks["integration_sample_accounting_closure"]["evidence"]["present_count"] == 1
    assert closure["status"] == "passed"
    assert closure["input_valid_samples_before_rejection"] == 9
    assert closure["valid_samples_after_rejection"] == 6
    assert closure["rejected_samples"] == 3


def test_pipeline_contract_blocks_failed_sample_accounting_closure(tmp_path: Path):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run, sample_closure_status="failed")

    audit = build_pipeline_contract_audit(run)
    checks = {item["name"]: item for item in audit["checks"]}
    closure = audit["integration"]["outputs"][0]["sample_accounting_closure"]

    assert audit["passed"] is False
    assert checks["integration_sample_accounting_closure"]["passed"] is False
    assert checks["integration_sample_accounting_closure"]["evidence"]["failed"] == [
        {
            "item": "H",
            "status": "failed",
            "input_valid_samples_before_rejection": 9,
            "valid_samples_after_rejection": 6,
            "rejected_samples": 3,
        }
    ]
    assert closure["status"] == "failed"


def test_pipeline_contract_markdown_reports_sample_accounting_closure(tmp_path: Path):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run, sample_closure_status="passed")
    out = tmp_path / "pipeline_contract.json"
    markdown = tmp_path / "pipeline_contract.md"

    assert (
        main(
            [
                "pipeline-contract",
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

    text = markdown.read_text(encoding="utf-8")
    assert "Integration Sample Accounting Closure" in text
    assert "input-valid `9`" in text
    assert "rejected `3`" in text


def test_html_report_surfaces_pipeline_sample_accounting_closure(tmp_path: Path):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run, sample_closure_status="passed")
    audit = build_pipeline_contract_audit(run)
    integration = read_json(run / "integration_results.json")
    report = tmp_path / "report.html"

    write_html_report(
        report,
        integration=integration,
        pipeline_contract=audit,
        run_root=run,
    )

    text = report.read_text(encoding="utf-8")
    assert "pipeline contract sample-closure rows" in text
    assert "valid_rejection_match" in text
    assert "<td>passed</td>" in text


def test_pipeline_contract_pixel_verification_reports_resident_rejection_sample_accounting(tmp_path: Path):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run)

    audit = build_pipeline_contract_audit(run, pixel_verify=True, pixel_verify_tile_size=1)
    checks = {item["name"]: item for item in audit["checks"]}
    row = audit["pixel_verification"]["integration_outputs"][0]
    accounting = row["rejection_sample_accounting"]

    assert audit["passed"] is True
    assert checks["integration_rejection_map_pixels_match_dq"]["passed"] is True
    assert checks["integration_rejection_sample_counts_match_maps"]["passed"] is True
    assert row["count_maps"]["high_rejection"]["result"]["positive_pixels"] == 1
    assert row["count_maps"]["high_rejection"]["result"]["rounded_sum"] == 2
    assert accounting["ok"] is True
    assert accounting["map_rejected_sample_sum"] == 3
    assert accounting["source_counts"] == [
        {"name": "dq_coverage_provenance.rejected_sample_count", "count": 3},
        {"name": "dq_provenance_summary.rejected_samples", "count": 3},
    ]


def test_pipeline_contract_pixel_verification_detects_resident_rejection_sample_drift(tmp_path: Path):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run)
    payload = read_json(run / "integration_results.json")
    output = payload["outputs"][0]
    output["dq_coverage_provenance"]["rejected_sample_count"] = 2.0
    output["dq_provenance_summary"]["rejected_samples"] = 2
    write_json(run / "integration_results.json", payload)

    audit = build_pipeline_contract_audit(run, pixel_verify=True, pixel_verify_tile_size=1)
    checks = {item["name"]: item for item in audit["checks"]}
    accounting = audit["pixel_verification"]["integration_outputs"][0]["rejection_sample_accounting"]

    assert audit["passed"] is False
    assert checks["integration_resident_result_contract"]["passed"] is True
    assert checks["integration_rejection_sample_counts_match_maps"]["passed"] is False
    assert accounting["map_rejected_sample_sum"] == 3
    assert all(match["actual"] == 3 and match["summary"] == 2 for match in accounting["source_matches"])


def test_pipeline_contract_pixel_verification_detects_fractional_rejection_count_map(tmp_path: Path):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run)
    write_fits_data(run / "integration" / "low_H.fits", np.array([[0.0, 1.5], [0.0, 0.0]], dtype=np.float32))

    audit = build_pipeline_contract_audit(run, pixel_verify=True, pixel_verify_tile_size=1)
    checks = {item["name"]: item for item in audit["checks"]}
    low_map = audit["pixel_verification"]["integration_outputs"][0]["count_maps"]["low_rejection"]

    assert audit["passed"] is False
    assert checks["integration_rejection_map_pixels_match_dq"]["passed"] is False
    assert checks["integration_rejection_sample_counts_match_maps"]["passed"] is False
    assert low_map["count_integrity"]["passed"] is False
    assert low_map["result"]["fractional_pixels"] == 1


def test_pipeline_contract_accepts_resident_calibration_contract(tmp_path: Path):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run)
    resident_calibration_contract = {
        "artifact_type": "resident_cuda_calibration_contract",
        "passed": True,
        "outputs": [
            {
                "index": 0,
                "filter": "H",
                "passed": True,
                "status": "passed",
                "master_path": str(run / "integration" / "master_H.fits"),
                "master_path_exists": True,
                "frame_count": 3,
                "set_count": 1,
                "bias_count": 2,
                "dark_count": 2,
                "flat_count": 2,
                "checks": [{"name": "resident_output_contracts_passed", "passed": True}],
            }
        ],
    }

    audit = build_pipeline_contract_audit(
        run,
        resident_calibration_contract=resident_calibration_contract,
    )
    checks = {item["name"]: item for item in audit["checks"]}

    assert audit["passed"] is True
    assert audit["calibration"]["resident_calibration_contract_attached"] is True
    assert audit["calibration"]["resident_master_count"] == 1
    assert audit["calibration"]["master_count"] == 1
    assert checks["calibration_master_surface_contract"]["passed"] is True
    assert checks["resident_calibration_surface_contract"]["passed"] is True
    resident_row = audit["calibration"]["resident_masters"][0]
    assert resident_row["contract_ok"] is True
    assert resident_row["science_contract"]["contract_type"] == "resident_calibration_surface_contract"


def _write_resident_native_calibration_source(run: Path) -> None:
    cache_dir = run / "calib_cache" / "resident_masters"
    cache_dir.mkdir(parents=True)
    cache_key = "H_2x2_bias-B_dark-D_flat-F_abc123"
    for suffix in ["master_bias.npy", "master_dark.npy", "master_flat.npy", "master_stats.json"]:
        (cache_dir / f"{cache_key}_{suffix}").write_bytes(b"fixture")
    stats = {"min": 1.0, "max": 2.0, "mean": 1.5, "median": 1.5, "std": 0.1}
    write_json(
        run / "resident_artifacts.json",
        {
            "schema_version": 1,
            "backend": "cuda_resident_stack",
            "policy": {
                "flat_floor": 0.05,
                "flat_normalization": "median",
                "master_dark_includes_bias": True,
                "master_rejection": "winsorized_sigma",
            },
            "artifacts": [
                {
                    "filter": "H",
                    "frame_ids": ["light_001", "light_002", "light_003"],
                    "master_path": str(run / "integration" / "master_H.fits"),
                    "master_stats": {
                        "bias_count": 2,
                        "dark_count": 2,
                        "flat_count": 2,
                        "set_count": 1,
                        "calibration_group_policy": "planner_matching_groups_per_light",
                        "sets": {
                            "set-H": {
                                "filter": "H",
                                "bias_group": "B",
                                "dark_group": "D",
                                "flat_group": "F",
                                "flat_bias_group": "B",
                                "bias_count": 2,
                                "dark_count": 2,
                                "flat_count": 2,
                                "dark_exposure_s": 60.0,
                                "master_dark_includes_bias": True,
                                "bias": stats,
                                "dark": stats,
                                "flat": stats,
                                "shape": {"height": 2, "width": 2},
                                "cache_dir": str(cache_dir),
                                "cache_key": cache_key,
                            }
                        },
                    },
                }
            ],
        },
    )


def test_pipeline_contract_accepts_resident_native_calibration_artifacts(tmp_path: Path):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run)
    _write_resident_native_calibration_source(run)
    write_resident_calibration_artifacts(run)

    audit = build_pipeline_contract_audit(run)
    checks = {item["name"]: item for item in audit["checks"]}

    assert audit["passed"] is True
    assert audit["calibration"]["resident_native_calibration_artifact"] is True
    assert audit["calibration"]["local_master_count"] == 3
    assert audit["calibration"]["resident_calibrated_light_count"] == 3
    assert checks["calibration_master_surface_contract"]["passed"] is True
    assert checks["resident_calibrated_lights_present"]["passed"] is True
    assert checks["resident_calibrated_light_contract"]["passed"] is True
    assert "calibrated_light_dq_contract" not in checks


def test_pipeline_contract_synthesizes_resident_calibration_visibility_from_resident_artifacts(
    tmp_path: Path,
):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run)
    _write_resident_native_calibration_source(run)

    audit = build_pipeline_contract_audit(run)
    checks = {item["name"]: item for item in audit["checks"]}

    assert not (run / "calibration_artifacts.json").exists()
    assert audit["passed"] is True
    assert audit["artifacts"]["calibration"]["exists"] is True
    assert audit["artifacts"]["calibration"]["path_exists"] is False
    assert audit["artifacts"]["calibration"]["source"] == "resident_artifacts_json_fallback"
    assert audit["calibration"]["generated_for_pipeline_contract"] is True
    assert audit["calibration"]["write_back"] is False
    assert audit["calibration"]["resident_native_calibration_artifact"] is True
    assert audit["calibration"]["resident_calibrated_light_count"] == 3
    assert checks["resident_calibrated_lights_present"]["passed"] is True
    assert checks["resident_calibrated_light_contract"]["passed"] is True


def test_pipeline_contract_cli_uses_resident_calibration_contract_json(tmp_path: Path):
    run = tmp_path / "run"
    out = tmp_path / "pipeline_contract.json"
    resident_contract = tmp_path / "resident_calibration_contract.json"
    _write_resident_pipeline_run(run)
    write_json(
        resident_contract,
        {
            "artifact_type": "resident_cuda_calibration_contract",
            "passed": True,
            "outputs": [
                {
                    "index": 0,
                    "filter": "H",
                    "passed": True,
                    "status": "passed",
                    "master_path_exists": True,
                    "frame_count": 3,
                    "set_count": 1,
                    "bias_count": 2,
                    "dark_count": 2,
                    "flat_count": 2,
                    "checks": [{"name": "resident_output_contracts_passed", "passed": True}],
                }
            ],
        },
    )

    assert (
        main(
            [
                "pipeline-contract",
                "--run",
                str(run),
                "--out",
                str(out),
                "--resident-calibration-contract-json",
                str(resident_contract),
            ]
        )
        == 0
    )

    audit = read_json(out)
    assert audit["calibration"]["resident_calibration_contract_attached"] is True
    assert {item["name"]: item["passed"] for item in audit["checks"]}[
        "resident_calibration_surface_contract"
    ] is True


def test_pipeline_contract_fails_resident_result_contract(tmp_path: Path):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run, missing_source_terms=True)

    audit = build_pipeline_contract_audit(run)
    checks = {item["name"]: item for item in audit["checks"]}

    assert audit["passed"] is False
    assert checks["integration_resident_result_contract"]["passed"] is False
    assert checks["integration_resident_result_contract"]["evidence"]["failed"] == ["H"]
    resident_checks = {
        item["name"]: item for item in audit["integration"]["outputs"][0]["resident_result_contract"]["contract"]["checks"]
    }
    assert resident_checks["source_terms_present"]["passed"] is False


def test_pipeline_contract_fails_missing_maps_and_crop_records(tmp_path: Path):
    run = tmp_path / "run"
    run.mkdir()
    write_json(
        run / "integration_results.json",
        {
            "rejection": "winsorized_sigma",
            "outputs": [
                {
                    "filter": "H",
                    "master_path": "integration/master_H.fits",
                    "weight_map_path": None,
                    "coverage_map_path": None,
                    "dq_map_path": None,
                    "low_rejection_map_path": None,
                    "high_rejection_map_path": None,
                    "dq_summary": {},
                }
            ],
        },
    )
    write_json(
        run / "local_norm_results.json",
        {
            "enabled": True,
            "reference_frame_id": "F1",
            "local_norm_results": [
                {
                    "frame_id": "F1",
                    "normalized_path": "local_norm_cache/local_norm_F1.fits",
                    "coverage_path": "registered_cache/coverage_F1.fits",
                    "dq_summary": {},
                }
            ],
        },
    )

    audit = build_pipeline_contract_audit(run)
    checks = {item["name"]: item for item in audit["checks"]}
    assert audit["passed"] is False
    assert checks["integration_output_maps_available"]["passed"] is False
    assert checks["integration_dq_contract"]["passed"] is False
    assert checks["local_normalization_contract"]["passed"] is False


def test_pipeline_contract_fails_malformed_calibration_artifacts(tmp_path: Path):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run)
    write_json(
        run / "calibration_artifacts.json",
        {
            "masters": {
                "bad_bias": {
                    "type": "bias",
                    "path": "calib_cache/masters/missing_bias.fits",
                    "tile_stack_mode": "stack_engine_cpu",
                    "stack_engine_enabled": True,
                    "stack_engine_dq_provenance": {
                        "result_contract": {
                            "contract_type": "stack_engine_result_contract",
                            "passed": True,
                        }
                    },
                }
            },
            "calibrated_lights": [
                {
                    "frame_id": "L1",
                    "path": "calib_cache/calibrated/missing_L1.fits",
                    "dq_mask_path": None,
                    "dq_summary": {},
                    "tile_count": 1,
                    "tile_size": 8,
                }
            ],
        },
    )

    audit = build_pipeline_contract_audit(run)
    checks = {item["name"]: item for item in audit["checks"]}
    master = audit["calibration"]["masters"][0]
    light = audit["calibration"]["calibrated_lights"][0]

    assert audit["passed"] is False
    assert checks["calibration_master_surface_contract"]["passed"] is False
    assert checks["calibrated_light_dq_contract"]["passed"] is False
    assert master["science_contract"]["stats"]["missing_keys"] == ["min", "max", "mean", "median", "std"]
    assert master["contract_ok"] is False
    assert light["dq_mask_path_exists"] is False
    assert light["dq_summary_has_valid"] is False
    assert light["contract_ok"] is False


def test_pipeline_contract_requires_stack_result_contract_for_cpu_stack_output(tmp_path: Path):
    run = tmp_path / "run"
    integration_dir = run / "integration"
    integration_dir.mkdir(parents=True)
    ones = np.ones((2, 2), dtype=np.float32)
    zeros = np.zeros((2, 2), dtype=np.float32)
    for name, data in {
        "master_H.fits": ones,
        "weight_H.fits": ones,
        "coverage_H.fits": ones,
        "dq_H.fits": zeros,
        "low_H.fits": zeros,
        "high_H.fits": zeros,
    }.items():
        write_fits_data(integration_dir / name, data)
    write_json(
        run / "integration_results.json",
        {
            "rejection": "none",
            "outputs": [
                {
                    "filter": "H",
                    "master_path": str(integration_dir / "master_H.fits"),
                    "weight_map_path": str(integration_dir / "weight_H.fits"),
                    "coverage_map_path": str(integration_dir / "coverage_H.fits"),
                    "dq_map_path": str(integration_dir / "dq_H.fits"),
                    "low_rejection_map_path": str(integration_dir / "low_H.fits"),
                    "high_rejection_map_path": str(integration_dir / "high_H.fits"),
                    "tile_stack_mode": "stack_engine_cpu",
                    "stack_engine_enabled": True,
                    "dq_summary": {"valid": 4},
                    "stack_engine_dq_provenance": {
                        "input_samples": 8,
                        "output_dq_summary": {"valid": 4},
                    },
                    "dq_provenance_summary": {
                        "source_schema": "stack_engine_dq_provenance",
                        "engine": "stack_engine_cpu",
                        "stage": "integration",
                    },
                }
            ],
        },
    )

    audit = build_pipeline_contract_audit(run)
    checks = {item["name"]: item for item in audit["checks"]}

    assert audit["passed"] is False
    assert checks["integration_stack_result_contract"]["passed"] is False
    assert checks["integration_stack_result_contract"]["evidence"]["failed"] == ["H"]
    assert audit["integration"]["outputs"][0]["stack_result_contract"]["status"] == "missing_or_failed"
