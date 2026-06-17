from __future__ import annotations

from pathlib import Path

import numpy as np

from glass.cli import main
from glass.engine.contracts import DQFlag
from glass.io.fits_io import write_fits_data
from glass.io.json_io import read_json, write_json
from glass.report.resident_result_contract import build_resident_result_contract


def _write_resident_run(path: Path, *, mismatch_summary: bool = False) -> None:
    integration = path / "integration"
    integration.mkdir(parents=True)
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
        write_fits_data(integration / name, data)
    dq_summary = {
        "valid": 1,
        "no_data": 1,
        "low_rejected": 2 if mismatch_summary else 1,
        "high_rejected": 1,
    }
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
                    "master_path": str(integration / "master_H.fits"),
                    "weight_map_path": str(integration / "weight_H.fits"),
                    "coverage_map_path": str(integration / "coverage_H.fits"),
                    "dq_map_path": str(integration / "dq_H.fits"),
                    "low_rejection_map_path": str(integration / "low_H.fits"),
                    "high_rejection_map_path": str(integration / "high_H.fits"),
                    "dq_summary": dq_summary,
                    "dq_coverage_provenance": {
                        "available": True,
                        "active_frame_count": 3,
                        "geometric_frame_count_matches_active": True,
                        "source_terms": [
                            "post_rejection_coverage",
                            "low_rejection",
                            "high_rejection",
                            "geometric_warp_coverage",
                        ],
                    },
                    "dq_provenance_summary": {
                        "source_schema": "resident_dq_coverage_provenance",
                        "stage": "integration",
                        "item": "H",
                        "engine": "cuda_resident_stack",
                        "active_frame_count": 3,
                        "source_terms": [
                            "post_rejection_coverage",
                            "low_rejection",
                            "high_rejection",
                            "geometric_warp_coverage",
                        ],
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


def test_resident_result_contract_passes_with_pixel_verify(tmp_path: Path) -> None:
    _write_resident_run(tmp_path)

    payload = build_resident_result_contract(tmp_path, pixel_verify=True, pixel_verify_tile_size=1)

    assert payload["passed"] is True
    assert payload["outputs"][0]["passed"] is True
    checks = {item["name"]: item for item in payload["outputs"][0]["checks"]}
    assert checks["resident_identity"]["passed"] is True
    assert checks["pixel_maps_match_summaries"]["passed"] is True
    assert payload["outputs"][0]["pixel_verification"]["dq"]["ok"] is True


def test_resident_result_contract_detects_dq_summary_mismatch(tmp_path: Path) -> None:
    _write_resident_run(tmp_path, mismatch_summary=True)

    payload = build_resident_result_contract(tmp_path, pixel_verify=True, pixel_verify_tile_size=1)

    assert payload["passed"] is False
    checks = {item["name"]: item for item in payload["outputs"][0]["checks"]}
    assert checks["pixel_maps_match_summaries"]["passed"] is False
    assert payload["outputs"][0]["pixel_verification"]["dq"]["matches"]["low_rejected"]["passed"] is False


def test_resident_result_contract_cli_writes_outputs(tmp_path: Path) -> None:
    _write_resident_run(tmp_path)
    out = tmp_path / "resident_contract.json"
    markdown = tmp_path / "resident_contract.md"

    assert (
        main(
            [
                "resident-result-contract",
                "--run",
                str(tmp_path),
                "--out",
                str(out),
                "--markdown",
                str(markdown),
                "--pixel-verify",
                "--pixel-verify-tile-size",
                "1",
                "--fail-on-failed",
            ]
        )
        == 0
    )

    payload = read_json(out)
    assert payload["artifact_type"] == "resident_cuda_result_contract"
    assert payload["passed"] is True
    assert "Resident CUDA Result Contract" in markdown.read_text(encoding="utf-8")
