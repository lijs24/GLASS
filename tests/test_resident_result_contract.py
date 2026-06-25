from __future__ import annotations

from pathlib import Path

import numpy as np

from glass.cli import main
from glass.engine.contracts import DQFlag
from glass.engine.rejection import (
    RESIDENT_WINSORIZED_SIGMA_ALGORITHM,
    resident_rejection_descriptor,
)
from glass.io.fits_io import write_fits_data
from glass.io.json_io import read_json, write_json
from glass.report.dq_map_verify import summarize_count_map_pixels
from glass.report.resident_result_contract import build_resident_result_contract


def _write_resident_run(
    path: Path,
    *,
    mismatch_summary: bool = False,
    mismatch_sample_count: bool = False,
    sample_closure_status: str | None = "passed",
    omit_rejection_semantics: bool = False,
    resident_artifact_legacy_rejection_semantics: bool = False,
    resident_winsorized_mode: str = "fast_approx",
) -> None:
    integration = path / "integration"
    integration.mkdir(parents=True)
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
        write_fits_data(integration / name, data)
    dq_summary = {
        "valid": 1,
        "no_data": 1,
        "low_rejected": 2 if mismatch_summary else 1,
        "high_rejected": 1,
    }
    provenance_summary = {
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
        "rejected_samples": 2 if mismatch_sample_count else 3,
        "output_dq_summary": dq_summary,
    }
    if sample_closure_status is not None:
        provenance_summary["sample_accounting_closure"] = {
            "status": sample_closure_status,
            "input_samples": 12,
            "input_valid_samples_before_rejection": 9,
            "input_invalid_samples_before_rejection": 3,
            "valid_samples_after_rejection": 6,
            "rejected_samples": 3,
            "input_total_match": True,
            "valid_rejection_match": sample_closure_status == "passed",
        }
    output = {
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
            "rejected_sample_count": 2.0 if mismatch_sample_count else 3.0,
            "rejected_sample_count_source": "low_high_rejection_maps",
            "source_terms": [
                "post_rejection_coverage",
                "low_rejection",
                "high_rejection",
                "geometric_warp_coverage",
            ],
        },
        "dq_provenance_summary": provenance_summary,
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
    if not omit_rejection_semantics:
        output["integration_rejection"] = resident_rejection_descriptor(
            "winsorized_sigma",
            3.0,
            3.0,
            resident_winsorized_mode=resident_winsorized_mode,
        )
    write_json(
        path / "integration_results.json",
        {
            "rejection": "winsorized_sigma",
            "rejection_semantics": resident_rejection_descriptor(
                "winsorized_sigma",
                3.0,
                3.0,
                resident_winsorized_mode=resident_winsorized_mode,
            ),
            "outputs": [output],
        },
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


def test_resident_result_contract_passes_with_pixel_verify(tmp_path: Path) -> None:
    _write_resident_run(tmp_path)

    payload = build_resident_result_contract(tmp_path, pixel_verify=True, pixel_verify_tile_size=1)

    assert payload["passed"] is True
    assert payload["outputs"][0]["passed"] is True
    checks = {item["name"]: item for item in payload["outputs"][0]["checks"]}
    assert checks["resident_identity"]["passed"] is True
    assert checks["pixel_maps_match_summaries"]["passed"] is True
    assert payload["outputs"][0]["pixel_verification"]["dq"]["ok"] is True
    accounting = payload["outputs"][0]["pixel_verification"]["rejection_sample_accounting"]
    assert accounting["ok"] is True
    assert accounting["map_rejected_sample_sum"] == 3
    assert accounting["coverage_provenance_rejected_samples"] == 3
    assert accounting["provenance_summary_rejected_samples"] == 3
    assert payload["outputs"][0]["sample_accounting_closure"]["status"] == "passed"
    semantics = checks["resident_winsorized_rejection_semantics_disclosed"]
    assert semantics["passed"] is True
    assert payload["outputs"][0]["rejection_semantics"]["passed"] is True
    assert payload["outputs"][0]["rejection_semantics"]["descriptor"]["cpu_baseline_parity"] is False


def test_resident_result_contract_resolves_cwd_relative_map_paths(
    tmp_path: Path,
    monkeypatch,
) -> None:
    run = tmp_path / "run"
    _write_resident_run(run)
    payload = read_json(run / "integration_results.json")
    output = payload["outputs"][0]
    for key in (
        "master_path",
        "weight_map_path",
        "coverage_map_path",
        "dq_map_path",
        "low_rejection_map_path",
        "high_rejection_map_path",
    ):
        output[key] = str(Path("run") / Path(output[key]).relative_to(run))
    write_json(run / "integration_results.json", payload)
    monkeypatch.chdir(tmp_path)

    contract = build_resident_result_contract(run, pixel_verify=True, pixel_verify_tile_size=1)

    checks = {item["name"]: item for item in contract["outputs"][0]["checks"]}
    assert contract["passed"] is True
    assert checks["required_maps_exist"]["passed"] is True
    assert checks["pixel_maps_match_summaries"]["passed"] is True


def test_resident_result_contract_accepts_hardened_winsorized_parity_descriptor(
    tmp_path: Path,
) -> None:
    _write_resident_run(tmp_path, resident_winsorized_mode="hardened_cpu_parity")

    payload = build_resident_result_contract(tmp_path, pixel_verify=True, pixel_verify_tile_size=1)

    checks = {item["name"]: item for item in payload["outputs"][0]["checks"]}
    semantics = payload["outputs"][0]["rejection_semantics"]
    descriptor = semantics["descriptor"]
    assert payload["passed"] is True
    assert checks["resident_winsorized_rejection_semantics_disclosed"]["passed"] is True
    assert semantics["matched_expected_index"] == 1
    assert descriptor["resident_winsorized_mode"] == "hardened_cpu_parity"
    assert descriptor["cpu_baseline_parity"] is True
    assert descriptor["approximation"] is False


def test_resident_result_contract_requires_winsorized_semantics_disclosure(tmp_path: Path) -> None:
    _write_resident_run(tmp_path, omit_rejection_semantics=True)

    payload = build_resident_result_contract(tmp_path, pixel_verify=True, pixel_verify_tile_size=1)

    checks = {item["name"]: item for item in payload["outputs"][0]["checks"]}
    assert payload["passed"] is False
    assert checks["resident_winsorized_rejection_semantics_disclosed"]["passed"] is False
    semantics = payload["outputs"][0]["rejection_semantics"]
    assert semantics["required"] is True
    assert semantics["present"] is False


def test_resident_result_contract_completes_legacy_resident_artifact_semantics(
    tmp_path: Path,
) -> None:
    _write_resident_run(
        tmp_path,
        omit_rejection_semantics=True,
        resident_artifact_legacy_rejection_semantics=True,
    )

    payload = build_resident_result_contract(tmp_path, pixel_verify=True, pixel_verify_tile_size=1)

    checks = {item["name"]: item for item in payload["outputs"][0]["checks"]}
    semantics = payload["outputs"][0]["rejection_semantics"]
    descriptor = semantics["descriptor"]
    assert payload["passed"] is True
    assert checks["resident_winsorized_rejection_semantics_disclosed"]["passed"] is True
    assert semantics["integration_results_descriptor_present"] is False
    assert semantics["resident_artifacts_descriptor_present"] is True
    assert semantics["descriptor_source"] == "resident_artifacts.integration_rejection"
    assert semantics["legacy_completion_applied"] is True
    assert semantics["legacy_completion_source"] == "fast_approx_algorithm"
    assert descriptor["resident_winsorized_mode"] == "fast_approx"
    assert descriptor["cpu_baseline_parity"] is False
    assert descriptor["parity_status"] == "known_non_parity_pending_cuda_update"
    assert descriptor["approximation"] is True


def test_resident_result_contract_accepts_sample_accounting_closure(tmp_path: Path) -> None:
    _write_resident_run(tmp_path, sample_closure_status="passed")

    payload = build_resident_result_contract(tmp_path, pixel_verify=True, pixel_verify_tile_size=1)

    checks = {item["name"]: item for item in payload["outputs"][0]["checks"]}
    closure = payload["outputs"][0]["sample_accounting_closure"]
    assert payload["passed"] is True
    assert closure["present"] is True
    assert closure["status"] == "passed"
    assert checks["sample_accounting_closure_valid"]["passed"] is True


def test_resident_result_contract_detects_sample_accounting_closure_failure(
    tmp_path: Path,
) -> None:
    _write_resident_run(tmp_path, sample_closure_status="failed")

    payload = build_resident_result_contract(tmp_path, pixel_verify=True, pixel_verify_tile_size=1)

    checks = {item["name"]: item for item in payload["outputs"][0]["checks"]}
    closure = payload["outputs"][0]["sample_accounting_closure"]
    assert payload["passed"] is False
    assert closure["present"] is True
    assert closure["status"] == "failed"
    assert checks["sample_accounting_closure_valid"]["passed"] is False


def test_resident_result_contract_distinguishes_rejected_samples_from_dq_pixels(tmp_path: Path) -> None:
    _write_resident_run(tmp_path)

    payload = build_resident_result_contract(tmp_path, pixel_verify=True, pixel_verify_tile_size=1)

    output = payload["outputs"][0]
    pixel = output["pixel_verification"]
    high_map = pixel["count_maps"]["high_rejection"]
    high_dq = pixel["dq"]["matches"]["high_rejected"]
    assert payload["passed"] is True
    assert high_map["result"]["positive_pixels"] == 1
    assert high_map["result"]["rounded_sum"] == 2
    assert high_map["summary_match"]["high_rejected"]["summary"] == 1
    assert high_dq["summary"] == 1
    assert pixel["rejection_sample_accounting"]["map_rejected_sample_sum"] == 3


def test_resident_result_contract_detects_dq_summary_mismatch(tmp_path: Path) -> None:
    _write_resident_run(tmp_path, mismatch_summary=True)

    payload = build_resident_result_contract(tmp_path, pixel_verify=True, pixel_verify_tile_size=1)

    assert payload["passed"] is False
    checks = {item["name"]: item for item in payload["outputs"][0]["checks"]}
    assert checks["pixel_maps_match_summaries"]["passed"] is False
    assert payload["outputs"][0]["pixel_verification"]["dq"]["matches"]["low_rejected"]["passed"] is False


def test_resident_result_contract_detects_rejection_sample_count_mismatch(tmp_path: Path) -> None:
    _write_resident_run(tmp_path, mismatch_sample_count=True)

    payload = build_resident_result_contract(tmp_path, pixel_verify=True, pixel_verify_tile_size=1)

    checks = {item["name"]: item for item in payload["outputs"][0]["checks"]}
    accounting = payload["outputs"][0]["pixel_verification"]["rejection_sample_accounting"]
    assert payload["passed"] is False
    assert checks["rejection_sample_count_recorded"]["passed"] is True
    assert checks["rejection_sample_count_summary_matches_coverage"]["passed"] is True
    assert checks["pixel_maps_match_summaries"]["passed"] is False
    assert accounting["map_vs_coverage"]["passed"] is False
    assert accounting["map_vs_summary"]["passed"] is False
    assert accounting["map_rejected_sample_sum"] == 3
    assert accounting["coverage_provenance_rejected_samples"] == 2


def test_resident_result_contract_detects_fractional_rejection_count_map(tmp_path: Path) -> None:
    _write_resident_run(tmp_path)
    low_path = tmp_path / "integration" / "low_H.fits"
    write_fits_data(low_path, np.array([[0.0, 1.5], [0.0, 0.0]], dtype=np.float32))

    payload = build_resident_result_contract(tmp_path, pixel_verify=True, pixel_verify_tile_size=1)

    low_map = payload["outputs"][0]["pixel_verification"]["count_maps"]["low_rejection"]
    assert payload["passed"] is False
    assert low_map["ok"] is False
    assert low_map["count_integrity"]["passed"] is False
    assert low_map["result"]["fractional_pixels"] == 1


def test_count_map_summary_reports_negative_and_fractional_pixels(tmp_path: Path) -> None:
    count_map = tmp_path / "count.fits"
    write_fits_data(count_map, np.array([[0.0, 1.5], [-1.0, 2.0]], dtype=np.float32))

    summary = summarize_count_map_pixels(count_map, tile_size=1)

    assert summary["negative_pixels"] == 1
    assert summary["fractional_pixels"] == 1


def test_resident_result_contract_allows_policy_skipped_coverage_provenance(tmp_path: Path) -> None:
    integration = tmp_path / "integration"
    integration.mkdir(parents=True)
    for name, data in {
        "master_H.fits": np.ones((2, 2), dtype=np.float32),
        "weight_H.fits": np.ones((2, 2), dtype=np.float32),
        "dq_H.fits": np.zeros((2, 2), dtype=np.float32),
    }.items():
        write_fits_data(integration / name, data)
    write_json(
        tmp_path / "integration_results.json",
        {
            "rejection": "none",
            "outputs": [
                {
                    "filter": "H",
                    "backend": "cuda_resident_stack",
                    "memory_mode": "resident",
                    "frame_count": 3,
                    "master_path": str(integration / "master_H.fits"),
                    "weight_map_path": str(integration / "weight_H.fits"),
                    "dq_map_path": str(integration / "dq_H.fits"),
                    "dq_summary": {"valid": 4},
                    "dq_coverage_provenance": {"available": False, "reason": "coverage map skipped by policy"},
                    "dq_provenance_summary": {
                        "source_schema": "resident_dq_coverage_provenance",
                        "stage": "integration",
                        "item": "H",
                        "engine": "cuda_resident_stack",
                        "active_frame_count": 3,
                        "source_terms": [],
                        "sample_accounting_closure": {
                            "status": "passed",
                            "input_samples": 12,
                            "input_valid_samples_before_rejection": 12,
                            "input_invalid_samples_before_rejection": 0,
                            "valid_samples_after_rejection": 12,
                            "rejected_samples": 0,
                            "input_total_match": True,
                            "valid_rejection_match": True,
                        },
                        "output_dq_summary": {"valid": 4},
                    },
                    "output_map_policy": {
                        "available": ["master", "weight", "dq"],
                        "written": ["master", "weight", "dq"],
                        "skipped": ["coverage", "low_rejection", "high_rejection"],
                    },
                }
            ],
        },
    )

    payload = build_resident_result_contract(tmp_path)

    checks = {item["name"]: item for item in payload["outputs"][0]["checks"]}
    assert payload["passed"] is True
    assert checks["coverage_provenance_present"]["passed"] is True
    assert checks["source_terms_present"]["passed"] is True


def test_resident_result_contract_accepts_minimal_master_only_policy_without_dq_maps(
    tmp_path: Path,
) -> None:
    integration = tmp_path / "integration"
    integration.mkdir(parents=True)
    write_fits_data(integration / "master_H.fits", np.ones((2, 2), dtype=np.float32))
    write_json(
        tmp_path / "integration_results.json",
        {
            "rejection": "winsorized_sigma",
            "outputs": [
                {
                    "filter": "H",
                    "backend": "cuda_resident_stack",
                    "memory_mode": "resident",
                    "frame_count": 3,
                    "master_path": str(integration / "master_H.fits"),
                    "weight_map_path": None,
                    "coverage_map_path": None,
                    "dq_map_path": None,
                    "low_rejection_map_path": None,
                    "high_rejection_map_path": None,
                    "dq_summary": None,
                    "dq_coverage_provenance": {
                        "available": False,
                        "reason": "minimal output policy skipped diagnostic maps",
                    },
                    "dq_provenance_summary": {
                        "source_schema": "resident_dq_coverage_provenance",
                        "stage": "integration",
                        "item": "H",
                        "engine": "cuda_resident_stack",
                        "active_frame_count": 3,
                        "source_terms": ["source_dq"],
                        "output_dq_summary": {},
                        "sample_accounting_closure": {
                            "status": "passed",
                            "input_valid_samples_before_rejection": 12,
                            "valid_samples_after_rejection": None,
                            "rejected_samples": None,
                            "valid_rejection_match": None,
                        },
                    },
                    "integration_rejection": resident_rejection_descriptor(
                        "winsorized_sigma",
                        3.0,
                        3.0,
                    ),
                    "geometric_warp_coverage": {
                        "available": False,
                        "frame_count_matches_active": False,
                    },
                    "output_map_policy": {
                        "mode": "minimal",
                        "available": ["master"],
                        "written": ["master"],
                        "skipped": ["weight", "coverage", "dq", "low_rejection", "high_rejection"],
                        "download_mode": "master_only",
                        "weight_map_downloaded": False,
                        "diagnostic_maps_downloaded": False,
                    },
                }
            ],
        },
    )

    payload = build_resident_result_contract(tmp_path, pixel_verify=True, pixel_verify_tile_size=1)

    checks = {item["name"]: item for item in payload["outputs"][0]["checks"]}
    assert payload["passed"] is True
    assert checks["dq_summary_present"]["passed"] is True
    assert checks["dq_summary_present"]["evidence"]["required"] is False
    assert checks["dq_summary_matches_provenance"]["passed"] is True
    assert checks["dq_summary_matches_provenance"]["evidence"]["required"] is False
    assert checks["geometric_frame_count_matches_active"]["passed"] is True
    assert checks["geometric_frame_count_matches_active"]["evidence"]["required"] is False
    assert payload["outputs"][0]["pixel_verification"]["dq"]["status"] == "skipped_by_output_policy"
    assert payload["outputs"][0]["pixel_verification"]["dq"]["ok"] is True


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
