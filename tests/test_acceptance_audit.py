from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from glass.cli import main
from glass.engine.contracts import DQFlag
from glass.io.fits_io import write_fits_data
from glass.io.json_io import read_json, write_json
from glass.report.acceptance_audit import build_acceptance_audit


def _write_manifest(path: Path, *, light: int = 200, bias: int = 20, dark: int = 20, flat: int = 20) -> None:
    frames = []
    for frame_type, count in {"light": light, "bias": bias, "dark": dark, "flat": flat}.items():
        frames.extend({"id": f"{frame_type}_{idx}", "frame_type": frame_type} for idx in range(count))
    write_json(path, {"frames": frames, "summary": {"count": len(frames)}})


def _write_glass_run(
    path: Path,
    *,
    elapsed_s: float = 100.0,
    active: int = 193,
    zero: int = 7,
    command: str | None = None,
    resident_timing: dict[str, float] | None = None,
    resident_dq: bool = False,
    frame_accounting: bool = False,
) -> None:
    path.mkdir()
    write_json(path / "run_timing.json", {"total_elapsed_s": elapsed_s, "memory_mode": "resident"})
    if command is not None:
        (path / "run_command.txt").write_text(command, encoding="utf-8")
    weights = {f"L{idx:04d}": 1.0 for idx in range(active)}
    weights.update({f"Z{idx:04d}": 0.0 for idx in range(zero)})
    output = {
        "backend": "cuda_resident_stack",
        "memory_mode": "resident",
        "frame_count": active + zero,
        "master_path": "master.fits",
    }
    resident_artifact: dict[str, object] = {}
    if resident_timing is not None:
        resident_artifact["timing_s"] = resident_timing
    if resident_dq:
        master = path / "master.fits"
        weight_map = path / "weight_map.fits"
        dq_map = path / "dq_map.fits"
        coverage_map = path / "coverage_map.fits"
        low_rejection_map = path / "low_rejection_map.fits"
        high_rejection_map = path / "high_rejection_map.fits"
        write_fits_data(master, np.ones((2, 3), dtype=np.float32), dtype=np.float32)
        write_fits_data(weight_map, np.ones((2, 3), dtype=np.float32), dtype=np.float32)
        dq_values = np.array(
            [
                [0, int(DQFlag.WARP_EDGE), int(DQFlag.LOW_REJECTED)],
                [int(DQFlag.HIGH_REJECTED), int(DQFlag.WARP_EDGE | DQFlag.HIGH_REJECTED), 0],
            ],
            dtype=np.uint32,
        )
        write_fits_data(dq_map, dq_values, dtype=np.float32)
        write_fits_data(coverage_map, np.ones((2, 3), dtype=np.float32), dtype=np.float32)
        write_fits_data(
            low_rejection_map,
            np.array([[0, 0, 1], [0, 0, 0]], dtype=np.float32),
            dtype=np.float32,
        )
        write_fits_data(
            high_rejection_map,
            np.array([[0, 0, 0], [1, 2, 0]], dtype=np.float32),
            dtype=np.float32,
        )
        dq_summary = {
            "valid": 2,
            "no_data": 0,
            "warp_edge": 2,
            "low_rejected": 1,
            "high_rejected": 2,
        }
        dq_coverage_provenance = {
            "active_frame_count": active,
            "source_terms": [
                "post_rejection_coverage",
                "low_rejection",
                "high_rejection",
                "geometric_warp_coverage",
            ],
            "finite_pre_rejection_coverage": {"finite_pixels": 1000},
            "post_rejection_coverage": {"finite_pixels": 6},
            "rejected_sample_count": 4,
            "geometric_zero_pixels": 0,
            "geometric_partial_pixels": 12,
            "partial_pre_rejection_pixels": 12,
        }
        output.update(
            {
                "master_path": str(master),
                "weight_map_path": str(weight_map),
                "dq_map_path": str(dq_map),
                "coverage_map_path": str(coverage_map),
                "low_rejection_map_path": str(low_rejection_map),
                "high_rejection_map_path": str(high_rejection_map),
                "output_map_policy": {
                    "available": ["master", "weight", "dq", "coverage", "low_rejection", "high_rejection"],
                    "mode": "audit",
                    "skipped": [],
                    "written": ["master", "weight", "dq", "coverage", "low_rejection", "high_rejection"],
                },
                "dq_summary": dq_summary,
                "dq_coverage_provenance": dq_coverage_provenance,
            }
        )
        resident_artifact.update(
            {
                "master_path": str(master),
                "weight_map_path": str(weight_map),
                "dq_map_path": str(dq_map),
                "coverage_map_path": str(coverage_map),
                "low_rejection_map_path": str(low_rejection_map),
                "high_rejection_map_path": str(high_rejection_map),
                "output_map_policy": {
                    "available": ["master", "weight", "dq", "coverage", "low_rejection", "high_rejection"],
                    "mode": "audit",
                    "skipped": [],
                    "written": ["master", "weight", "dq", "coverage", "low_rejection", "high_rejection"],
                },
                "dq_summary": dq_summary,
                "dq_coverage_provenance": dq_coverage_provenance,
            }
        )
    write_json(
        path / "integration_results.json",
        {
            "frame_weights": weights,
            "weighting": "none",
            "rejection": "winsorized_sigma",
            "outputs": [output],
        },
    )
    if resident_artifact:
        write_json(path / "resident_artifacts.json", {"artifacts": [resident_artifact]})
    if frame_accounting:
        write_json(
            path / "registration_results.json",
            {
                "source_stage": "resident_calibrated_stack",
                "results": [
                    *[
                        {"frame_id": f"L{idx:04d}", "status": "ok"}
                        for idx in range(active)
                    ],
                    *[
                        {"frame_id": f"Z{idx:04d}", "status": "excluded"}
                        for idx in range(zero)
                    ],
                ],
            },
        )
        write_json(
            path / "frame_accounting.json",
            {
                "schema_version": 1,
                "artifact": "frame_accounting",
                "integration_source_stage": "resident_calibrated_stack",
                "summary": {
                    "input_light_frames": active + zero,
                    "resident_calibrated_frames": active + zero,
                    "registration_accepted_frames": active,
                    "integrated_frames": active,
                    "zero_weight_frames": zero,
                    "exception_frames": zero,
                    "final_status_counts": {"integrated": active, "zero_weight": zero},
                },
                "exception_summary": {
                    "count": zero,
                    "final_status_counts": {"zero_weight": zero},
                    "primary_stage_counts": {"integration": zero},
                },
                "exception_frames": [
                    {
                        "frame_id": f"Z{idx:04d}",
                        "filter": "H",
                        "final_status": "zero_weight",
                        "primary_stage": "integration",
                        "primary_reason": "integration weight is zero",
                        "registration_status": "excluded",
                        "integration_status": "zero_weight",
                        "integration_weight": 0.0,
                    }
                    for idx in range(zero)
                ],
                "frames": [
                    *[
                        {
                            "frame_id": f"L{idx:04d}",
                            "final_status": "integrated",
                            "integration_status": "used",
                            "integration_weight": 1.0,
                            "registration_status": "ok",
                        }
                        for idx in range(active)
                    ],
                    *[
                        {
                            "frame_id": f"Z{idx:04d}",
                            "final_status": "zero_weight",
                            "integration_status": "zero_weight",
                            "integration_weight": 0.0,
                            "registration_status": "excluded",
                        }
                        for idx in range(zero)
                    ],
                ],
            },
        )


def _write_wbpp_result(path: Path, *, elapsed_s: float = 1000.0) -> None:
    path.write_text(
        "\ufeff" + json.dumps({"elapsed_s": elapsed_s, "dataset": "fixture"}),
        encoding="utf-8",
    )


def _write_compare(
    path: Path,
    *,
    shape_match: bool = True,
    rms: float = 0.001,
    p99: float = 0.002,
    scale: float = 8.764434957115609e-06,
    offset: float = 0.0006274500691899127,
    min_coverage: float = 190.0,
    coverage_fraction: float = 0.97,
) -> None:
    write_json(
        path,
        {
            "shape_match": shape_match,
            "rms_diff": rms,
            "abs_diff_p99": p99,
            "candidate_transform": {
                "applied": True,
                "scale": scale,
                "offset": offset,
                "clip_low": None,
                "clip_high": None,
            },
            "comparison_region": {
                "coverage_fraction": coverage_fraction,
                "compared_pixels": 123,
                "min_coverage": min_coverage,
            },
        },
    )


def _write_contract(path: Path, *, max_runtime_factor: float = 1.3) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "name": "fixture_contract",
            "dataset_requirements": {
                "light": 200,
                "bias": 20,
                "dark": 20,
                "flat": 20,
                "active_light_frames": 190,
            },
            "runtime": {
                "release_baseline_elapsed_s": 30.0,
                "max_runtime_regression_factor": max_runtime_factor,
                "min_speedup_vs_reference": 20.0,
            },
            "comparison": {
                "required_scale": 8.764434957115609e-06,
                "required_offset": 0.0006274500691899127,
                "required_min_coverage": 190.0,
                "min_coverage_fraction": 0.95,
                "max_rms_diff": 0.01,
                "max_abs_diff_p99": 0.01,
            },
            "required_command_tokens": [
                "--memory-mode resident",
                "--resident-registration similarity_cuda_triangle",
                "--flat-floor 0.05",
            ],
            "timing_baseline": {
                "warning_regression_factor": 1.15,
                "stages_s": {
                    "master_build_or_load": 10.0,
                    "light_read_upload_calibrate": 15.0,
                    "resident_registration_warp": 11.0,
                    "output_write": 1.0,
                },
            },
        },
    )


def _add_dq_contract(path: Path) -> None:
    payload = read_json(path)
    payload["dq_provenance"] = {
        "required": True,
        "min_records": 1,
        "required_source_schemas": ["resident_dq_coverage_provenance"],
        "required_engines": ["cuda_resident_stack"],
        "min_active_frame_count": 190,
        "require_dq_map_path": True,
        "require_existing_dq_map": True,
        "require_coverage_map_path": True,
        "required_summary_fields": ["zero_coverage_pixels", "partial_coverage_pixels"],
        "required_output_dq_flags": ["valid", "warp_edge", "low_rejected", "high_rejected"],
        "verify_dq_map_pixels": True,
        "dq_map_verify_tile_size": 2,
        "dq_map_summary_tolerance_pixels": 0,
        "dq_map_summary_match_flags": ["valid", "warp_edge", "low_rejected", "high_rejected"],
        "verify_output_count_maps": True,
        "count_map_verify_tile_size": 2,
        "coverage_map_finite_pixels_match_provenance": True,
        "coverage_zero_pixels_match_no_data": True,
        "allow_missing_rejection_maps_if_skipped": True,
        "rejection_map_sum_matches_provenance": True,
        "required_resident_artifact_map_paths": [
            "master",
            "weight",
            "coverage",
            "dq",
            "low_rejection",
            "high_rejection",
        ],
        "positive_output_dq_flags": ["valid", "warp_edge"],
        "required_source_terms": ["geometric_warp_coverage"],
    }
    write_json(path, payload)


def _add_frame_accounting_contract(path: Path, *, active: int = 193, zero: int = 7) -> None:
    payload = read_json(path)
    payload["frame_accounting"] = {
        "required": True,
        "required_input_light_frames": active + zero,
        "required_integrated_frames": active,
        "required_zero_weight_frames": zero,
        "required_registration_accepted_frames": active,
        "min_integrated_frames": 190,
        "required_integration_source_stage": "resident_calibrated_stack",
        "required_final_status_counts": {
            "integrated": active,
            "zero_weight": zero,
        },
        "match_integration_frame_weights": True,
        "match_speedup_summary": True,
        "match_dq_active_frame_count": True,
        "match_registration_accepted_frames": True,
    }
    write_json(path, payload)


def test_acceptance_audit_passes_real_benchmark_thresholds(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    _write_manifest(manifest)
    _write_glass_run(gp_run)
    _write_wbpp_result(wbpp)
    _write_compare(compare)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
    )

    assert audit["passed"] is True
    assert audit["frame_type_counts"] == {"light": 200, "bias": 20, "dark": 20, "flat": 20}
    assert audit["speedup_summary"]["speedup_vs_wbpp"] == 10.0


def test_acceptance_audit_applies_benchmark_contract(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    contract = tmp_path / "contract.json"
    _write_manifest(manifest)
    _write_glass_run(
        gp_run,
        elapsed_s=38.0,
        command=(
            "glass run --memory-mode resident --resident-registration similarity_cuda_triangle "
            "--flat-floor 0.05"
        ),
        resident_timing={
            "master_build_or_load": 11.0,
            "light_read_upload_calibrate": 16.0,
            "light_read_worker_cumulative": 92.0,
            "resident_registration_warp": 12.0,
            "output_write": 3.5,
        },
    )
    _write_wbpp_result(wbpp, elapsed_s=1092.541)
    _write_compare(compare)
    _write_contract(contract)
    contract_payload = read_json(contract)
    timing_baseline = contract_payload["timing_baseline"]
    timing_baseline["stages_s"]["light_read_decode_worker"] = 45.0
    timing_baseline["cumulative_stages"] = ["light_read_decode_worker"]
    timing_baseline["stage_aliases"] = {
        "light_read_decode_worker": "light_read_worker_cumulative",
    }
    timing_baseline["stage_notes"] = {
        "light_read_decode_worker": "Cumulative worker time is informational.",
    }
    write_json(contract, contract_payload)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        benchmark_contract=contract,
    )

    checks = {item["name"]: item["passed"] for item in audit["checks"]}
    assert audit["passed"] is True
    assert audit["benchmark_contract"]["name"] == "fixture_contract"
    assert checks["contract_max_runtime_vs_release_baseline"] is True
    assert checks["contract_required_command_token:--flat-floor 0.05"] is True
    assert checks["contract_compare_scale"] is True
    assert checks["contract_compare_min_coverage"] is True
    regression = audit["performance_regression"]
    assert regression["status"] == "regressed"
    assert regression["worst_regression"]["stage"] == "output_write"
    assert regression["regressed_count"] == 1
    guidance = audit["optimization_guidance"]
    assert guidance["primary_target"] == "io_upload_calibration_pipeline"
    targets = {item["target_id"]: item for item in guidance["targets"]}
    assert targets["io_upload_calibration_pipeline"]["current_s"] == 16.0
    assert targets["resident_registration_warp"]["current_s"] == 12.0
    assert targets["output_write_policy"]["status"] == "regressed"
    cumulative = {
        item["stage"]: item
        for item in regression["items"]
        if item["stage"] == "light_read_decode_worker"
    }["light_read_decode_worker"]
    assert cumulative["actual_key"] == "light_read_worker_cumulative"
    assert cumulative["status"] == "informational_cumulative"
    assert cumulative["timing_kind"] == "worker_cumulative"


def test_acceptance_audit_applies_dq_provenance_contract(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    contract = tmp_path / "contract.json"
    _write_manifest(manifest)
    _write_glass_run(
        gp_run,
        elapsed_s=38.0,
        active=193,
        command=(
            "glass run --memory-mode resident --resident-registration similarity_cuda_triangle "
            "--flat-floor 0.05"
        ),
        resident_dq=True,
    )
    _write_wbpp_result(wbpp, elapsed_s=1092.541)
    _write_compare(compare)
    _write_contract(contract)
    _add_dq_contract(contract)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        benchmark_contract=contract,
    )

    checks = {item["name"]: item["passed"] for item in audit["checks"]}
    assert audit["passed"] is True
    assert audit["dq_provenance"]["record_count"] == 2
    assert audit["dq_provenance"]["records"][0]["normalized_from_legacy"] is True
    assert checks["contract_dq_provenance_records"] is True
    assert checks["contract_dq_source_schema:resident_dq_coverage_provenance"] is True
    assert checks["contract_dq_engine:cuda_resident_stack"] is True
    assert checks["contract_dq_min_active_frame_count"] is True
    assert checks["contract_dq_map_exists"] is True
    assert checks["contract_dq_output_flag:warp_edge"] is True
    assert checks["contract_dq_positive_output_flag:warp_edge"] is True
    assert checks["contract_dq_map_pixel_verification"] is True
    assert checks["contract_dq_map_summary_match:valid"] is True
    assert checks["contract_dq_map_summary_match:warp_edge"] is True
    assert checks["contract_coverage_map_pixel_verification"] is True
    assert checks["contract_coverage_map_finite_pixels_match"] is True
    assert checks["contract_coverage_zero_pixels_match_no_data"] is True
    assert checks["contract_low_rejection_map_available_or_skipped"] is True
    assert checks["contract_low_rejection_map_positive_pixels_match:low_rejected"] is True
    assert checks["contract_high_rejection_map_positive_pixels_match:high_rejected"] is True
    assert checks["contract_rejection_map_sum_matches_provenance"] is True
    assert checks["contract_resident_artifact_map_path:master"] is True
    assert checks["contract_resident_artifact_map_path:low_rejection"] is True
    assert checks["contract_resident_artifact_map_path:high_rejection"] is True
    assert checks["contract_dq_source_term:geometric_warp_coverage"] is True
    verification = audit["dq_provenance"]["records"][0]["dq_map_pixel_verification"]
    assert verification["status"] == "verified"
    assert verification["result"]["counts"]["high_rejected"] == 2
    count_maps = audit["dq_provenance"]["records"][0]["output_count_map_verification"]
    assert count_maps["coverage"]["result"]["finite_pixels"] == 6
    assert count_maps["low_rejection"]["result"]["positive_pixels"] == 1
    assert count_maps["high_rejection"]["result"]["rounded_sum"] == 3


def test_acceptance_audit_applies_frame_accounting_contract(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    contract = tmp_path / "contract.json"
    _write_manifest(manifest)
    _write_glass_run(
        gp_run,
        elapsed_s=38.0,
        active=193,
        zero=7,
        command=(
            "glass run --memory-mode resident --resident-registration similarity_cuda_triangle "
            "--flat-floor 0.05"
        ),
        resident_dq=True,
        frame_accounting=True,
    )
    _write_wbpp_result(wbpp, elapsed_s=1092.541)
    _write_compare(compare)
    _write_contract(contract)
    _add_dq_contract(contract)
    _add_frame_accounting_contract(contract)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        benchmark_contract=contract,
    )

    checks = {item["name"]: item["passed"] for item in audit["checks"]}
    assert audit["passed"] is True
    assert audit["frame_accounting"]["exists"] is True
    assert audit["frame_accounting"]["summary"]["integrated_frames"] == 193
    assert audit["frame_accounting"]["exception_summary"]["count"] == 7
    assert audit["frame_accounting"]["exception_frames"][0]["primary_reason"] == "integration weight is zero"
    assert audit["optimization_guidance"]["exception_context"]["count"] == 7
    assert audit["optimization_guidance"]["exception_context"]["dominant_stage"] == "integration"
    assert checks["contract_frame_accounting_present"] is True
    assert checks["contract_frame_accounting_input_light_frames"] is True
    assert checks["contract_frame_accounting_integrated_frames"] is True
    assert checks["contract_frame_accounting_zero_weight_frames"] is True
    assert checks["contract_frame_accounting_final_status:integrated"] is True
    assert checks["contract_frame_accounting_final_status:zero_weight"] is True
    assert checks["contract_frame_accounting_matches_integration_weights"] is True
    assert checks["contract_frame_accounting_matches_speedup_summary"] is True
    assert checks["contract_frame_accounting_matches_dq_active_frames"] is True
    assert checks["contract_frame_accounting_matches_registration"] is True


def test_acceptance_audit_frame_accounting_contract_catches_mismatch(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    contract = tmp_path / "contract.json"
    _write_manifest(manifest)
    _write_glass_run(
        gp_run,
        elapsed_s=38.0,
        active=193,
        zero=7,
        command=(
            "glass run --memory-mode resident --resident-registration similarity_cuda_triangle "
            "--flat-floor 0.05"
        ),
        resident_dq=True,
        frame_accounting=True,
    )
    accounting = read_json(gp_run / "frame_accounting.json")
    accounting["summary"]["integrated_frames"] = 192
    accounting["summary"]["final_status_counts"]["integrated"] = 192
    write_json(gp_run / "frame_accounting.json", accounting)
    _write_wbpp_result(wbpp, elapsed_s=1092.541)
    _write_compare(compare)
    _write_contract(contract)
    _add_dq_contract(contract)
    _add_frame_accounting_contract(contract)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        benchmark_contract=contract,
    )

    checks = {item["name"]: item["passed"] for item in audit["checks"]}
    assert audit["passed"] is False
    assert checks["contract_frame_accounting_integrated_frames"] is False
    assert checks["contract_frame_accounting_final_status:integrated"] is False
    assert checks["contract_frame_accounting_matches_integration_weights"] is False
    assert checks["contract_frame_accounting_matches_speedup_summary"] is False
    assert checks["contract_frame_accounting_matches_dq_active_frames"] is False


def test_acceptance_audit_rejection_sum_uses_explicit_tolerance(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    contract = tmp_path / "contract.json"
    _write_manifest(manifest)
    _write_glass_run(
        gp_run,
        elapsed_s=38.0,
        active=193,
        command=(
            "glass run --memory-mode resident --resident-registration similarity_cuda_triangle "
            "--flat-floor 0.05"
        ),
        resident_dq=True,
    )
    for artifact_name, list_key in [
        ("integration_results.json", "outputs"),
        ("resident_artifacts.json", "artifacts"),
    ]:
        payload = read_json(gp_run / artifact_name)
        payload[list_key][0]["dq_coverage_provenance"]["rejected_sample_count"] = 3
        write_json(gp_run / artifact_name, payload)
    _write_wbpp_result(wbpp, elapsed_s=1092.541)
    _write_compare(compare)
    _write_contract(contract)
    _add_dq_contract(contract)
    contract_payload = read_json(contract)
    contract_payload["dq_provenance"]["rejection_map_sum_tolerance_samples"] = 1
    write_json(contract, contract_payload)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        benchmark_contract=contract,
    )

    checks = {item["name"]: item for item in audit["checks"]}
    rejection_sum = checks["contract_rejection_map_sum_matches_provenance"]
    assert audit["passed"] is True
    assert rejection_sum["passed"] is True
    assert rejection_sum["evidence"]["tolerance_samples"] == 1
    assert rejection_sum["evidence"]["matches"][0]["delta"] == 1


def test_acceptance_audit_dq_contract_fails_when_artifact_missing(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    contract = tmp_path / "contract.json"
    _write_manifest(manifest)
    _write_glass_run(
        gp_run,
        elapsed_s=38.0,
        command=(
            "glass run --memory-mode resident --resident-registration similarity_cuda_triangle "
            "--flat-floor 0.05"
        ),
    )
    _write_wbpp_result(wbpp, elapsed_s=1092.541)
    _write_compare(compare)
    _write_contract(contract)
    _add_dq_contract(contract)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        benchmark_contract=contract,
    )

    checks = {item["name"]: item["passed"] for item in audit["checks"]}
    assert audit["passed"] is False
    assert audit["dq_provenance"]["record_count"] == 0
    assert checks["contract_dq_provenance_records"] is False
    assert checks["contract_dq_source_schema:resident_dq_coverage_provenance"] is False
    assert checks["contract_dq_map_path_present"] is False
    assert checks["contract_dq_map_pixel_verification"] is False
    assert checks["contract_coverage_map_pixel_verification"] is False
    assert checks["contract_low_rejection_map_available_or_skipped"] is False


def test_acceptance_audit_contract_catches_missing_parameters(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    contract = tmp_path / "contract.json"
    _write_manifest(manifest)
    _write_glass_run(
        gp_run,
        elapsed_s=42.0,
        command="glass run --memory-mode resident --resident-registration similarity_cuda_triangle",
    )
    _write_wbpp_result(wbpp, elapsed_s=1092.541)
    _write_compare(compare, scale=1.0, min_coverage=99.0, coverage_fraction=0.5)
    _write_contract(contract)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        benchmark_contract=contract,
    )

    checks = {item["name"]: item["passed"] for item in audit["checks"]}
    assert audit["passed"] is False
    assert checks["contract_max_runtime_vs_release_baseline"] is False
    assert checks["contract_required_command_token:--flat-floor 0.05"] is False
    assert checks["contract_compare_scale"] is False
    assert checks["contract_compare_min_coverage"] is False
    assert checks["contract_min_coverage_fraction"] is False


def test_acceptance_audit_cli_writes_outputs_and_returns_failure(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    resident_det = tmp_path / "resident_determinism.json"
    out_json = tmp_path / "audit.json"
    out_md = tmp_path / "audit.md"
    _write_manifest(manifest, light=199)
    _write_glass_run(gp_run, elapsed_s=100.0)
    _write_wbpp_result(wbpp, elapsed_s=150.0)
    _write_compare(compare, rms=0.02)
    write_json(
        resident_det,
        {
            "audit_type": "resident_triangle_determinism",
            "summary": {
                "passed": False,
                "output_difference_count": 1,
                "output_numerical_drift_count": 1,
                "output_numerical_drift_max_relative_rms": 0.011916,
            },
            "timing": {"candidate_over_baseline_ratio": 0.95},
            "output_numerical_drifts": [
                {
                    "key": "H:200:F000061:F000260",
                    "field": "master_path",
                    "drift": {
                        "available": True,
                        "joint_finite_pixels": 61651200,
                        "mean_abs": 0.642260,
                        "rms": 3.751400,
                        "p99_abs": 3.408920,
                        "relative_rms_to_baseline_std": 0.011916,
                    },
                }
            ],
        },
    )

    result = main(
        [
            "acceptance-audit",
            "--manifest",
            str(manifest),
            "--glass-run",
            str(gp_run),
            "--wbpp-result",
            str(wbpp),
            "--compare-json",
            str(compare),
            "--resident-determinism-json",
            str(resident_det),
            "--out",
            str(out_json),
            "--markdown",
            str(out_md),
            "--min-active-frames",
            "190",
        ]
    )

    assert result == 2
    payload = read_json(out_json)
    assert payload["passed"] is False
    assert {item["name"]: item["passed"] for item in payload["checks"]}["minimum_light_frames"] is False
    assert {item["name"]: item["passed"] for item in payload["checks"]}["minimum_speedup"] is False
    assert {item["name"]: item["passed"] for item in payload["checks"]}["maximum_rms_diff"] is False
    assert payload["resident_determinism"]["path"] == str(resident_det)
    assert payload["resident_determinism"]["strict_passed"] is False
    assert payload["resident_determinism"]["output_numerical_drift_count"] == 1
    assert payload["output_numerical_drifts"][0]["drift"]["rms"] == 3.751400
    assert "FAIL: minimum_light_frames" in out_md.read_text(encoding="utf-8")
    assert "Resident Determinism" in out_md.read_text(encoding="utf-8")
    assert "relative_rms=0.011916" in out_md.read_text(encoding="utf-8")
