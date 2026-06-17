from __future__ import annotations

from pathlib import Path

import numpy as np

from glass.cli import main
from glass.engine.contracts import DQFlag
from glass.io.fits_io import write_fits_data
from glass.io.json_io import read_json, write_json
from glass.report.pipeline_contract import build_pipeline_contract_audit
from glass.synthetic.generator import generate_synthetic_dataset


def _write_resident_pipeline_run(path: Path, *, missing_source_terms: bool = False) -> None:
    integration_dir = path / "integration"
    integration_dir.mkdir(parents=True)
    master = np.ones((2, 2), dtype=np.float32)
    weight = np.ones((2, 2), dtype=np.float32)
    coverage = np.array([[0, 1], [1, 1]], dtype=np.float32)
    low = np.array([[0, 1], [0, 0]], dtype=np.float32)
    high = np.array([[0, 0], [1, 0]], dtype=np.float32)
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
    write_json(
        path / "integration_results.json",
        {
            "rejection": "winsorized_sigma",
            "outputs": [
                {
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
                        "source_terms": source_terms,
                    },
                    "dq_provenance_summary": {
                        "source_schema": "resident_dq_coverage_provenance",
                        "stage": "integration",
                        "engine": "cuda_resident_stack",
                        "active_frame_count": 3,
                        "source_terms": source_terms,
                        "output_dq_summary": dq_summary,
                    },
                    "geometric_warp_coverage": {
                        "available": True,
                        "frame_count": 3,
                        "frame_count_matches_active": True,
                    },
                    "output_map_policy": {
                        "available": ["master", "weight", "coverage", "dq", "low_rejection", "high_rejection"],
                        "written": ["master", "weight", "coverage", "dq", "low_rejection", "high_rejection"],
                        "skipped": [],
                    },
                }
            ],
        },
    )


def test_pipeline_contract_passes_for_cpu_audit_run(tmp_path: Path):
    data = tmp_path / "data"
    run = tmp_path / "run"
    out = tmp_path / "pipeline_contract.json"
    markdown = tmp_path / "pipeline_contract.md"
    generate_synthetic_dataset(data, frames=3, width=24, height=24)

    assert main(["audit", "--root", str(data), "--out", str(run), "--backend", "cpu", "--tile-size", "8"]) == 0
    assert main(["pipeline-contract", "--run", str(run), "--out", str(out), "--markdown", str(markdown)]) == 0

    audit = read_json(out)
    assert audit["passed"] is True
    checks = {item["name"]: item for item in audit["checks"]}
    assert checks["integration_output_maps_available"]["passed"] is True
    assert checks["integration_dq_contract"]["passed"] is True
    assert checks["local_normalization_contract"]["passed"] is True
    assert checks["warp_outputs_have_dq_and_coverage"]["passed"] is True
    assert "GLASS Pipeline Invariant Contract Audit" in markdown.read_text(encoding="utf-8")


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
