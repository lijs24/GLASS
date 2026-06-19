from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from glass.cli import main
from glass.engine.contracts import DQFlag
from glass.io.fits_io import write_fits_data
from glass.io.json_io import read_json, write_json
from glass.report.acceptance_audit import build_acceptance_audit
from glass.report.benchmark_contract import load_benchmark_contract
from glass.report.benchmark_contract_profile import (
    RESIDENT_CUDA_DQ_PROFILE_NAME,
    build_resident_cuda_dq_benchmark_contract,
)


def _write_manifest(path: Path) -> None:
    frames = []
    for frame_type, count in {"light": 200, "bias": 20, "dark": 20, "flat": 20}.items():
        frames.extend({"id": f"{frame_type}_{idx}", "frame_type": frame_type} for idx in range(count))
    write_json(path, {"frames": frames, "summary": {"count": len(frames)}})


def _write_wbpp_result(path: Path) -> None:
    path.write_text("\ufeff" + json.dumps({"elapsed_s": 1000.0}), encoding="utf-8")


def _write_compare(path: Path) -> None:
    write_json(
        path,
        {
            "shape_match": True,
            "rms_diff": 0.001,
            "abs_diff_p99": 0.002,
            "candidate_transform": {"applied": True},
            "comparison_region": {
                "coverage_fraction": 0.97,
                "compared_pixels": 123,
                "min_coverage": 190.0,
            },
        },
    )


def _write_resident_dq_run(path: Path) -> None:
    path.mkdir()
    write_json(path / "run_timing.json", {"total_elapsed_s": 38.0, "memory_mode": "resident"})
    (path / "run_command.txt").write_text(
        "glass run --memory-mode resident --resident-runtime-preset throughput-v1",
        encoding="utf-8",
    )
    master = path / "master.fits"
    weight_map = path / "weight_map.fits"
    dq_map = path / "dq_map.fits"
    coverage_map = path / "coverage_map.fits"
    low_rejection_map = path / "low_rejection_map.fits"
    high_rejection_map = path / "high_rejection_map.fits"
    write_fits_data(master, np.ones((2, 3), dtype=np.float32), dtype=np.float32)
    write_fits_data(weight_map, np.ones((2, 3), dtype=np.float32), dtype=np.float32)
    write_fits_data(coverage_map, np.ones((2, 3), dtype=np.float32), dtype=np.float32)
    write_fits_data(
        dq_map,
        np.array(
            [
                [0, int(DQFlag.WARP_EDGE), int(DQFlag.LOW_REJECTED)],
                [int(DQFlag.HIGH_REJECTED), int(DQFlag.WARP_EDGE | DQFlag.HIGH_REJECTED), 0],
            ],
            dtype=np.uint32,
        ),
        dtype=np.float32,
    )
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
    weights = {
        **{f"L{idx:04d}": 1.0 for idx in range(193)},
        **{f"Z{idx:04d}": 0.0 for idx in range(7)},
    }
    dq_summary = {
        "valid": 2,
        "no_data": 0,
        "warp_edge": 2,
        "low_rejected": 1,
        "high_rejected": 2,
    }
    dq_coverage_provenance = {
        "active_frame_count": 193,
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
    output = {
        "backend": "cuda_resident_stack",
        "memory_mode": "resident",
        "frame_count": 200,
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
    write_json(
        path / "integration_results.json",
        {
            "frame_weights": weights,
            "weighting": "none",
            "rejection": "winsorized_sigma",
            "outputs": [output],
        },
    )
    write_json(
        path / "resident_artifacts.json",
        {
            "artifacts": [
                {
                    "master_path": str(master),
                    "weight_map_path": str(weight_map),
                    "dq_map_path": str(dq_map),
                    "coverage_map_path": str(coverage_map),
                    "low_rejection_map_path": str(low_rejection_map),
                    "high_rejection_map_path": str(high_rejection_map),
                    "output_map_policy": output["output_map_policy"],
                    "dq_summary": dq_summary,
                    "dq_coverage_provenance": dq_coverage_provenance,
                }
            ]
        },
    )


def test_resident_cuda_dq_benchmark_contract_profile_defaults():
    contract = build_resident_cuda_dq_benchmark_contract()

    assert contract["schema_version"] == 1
    assert contract["profile"]["name"] == RESIDENT_CUDA_DQ_PROFILE_NAME
    assert contract["dataset_requirements"] == {
        "light": 200,
        "bias": 20,
        "dark": 20,
        "flat": 20,
        "active_light_frames": 190,
    }
    assert contract["runtime"]["min_speedup_vs_reference"] == 2.0
    assert contract["comparison"]["min_coverage_fraction"] == 0.95
    assert contract["comparison"]["max_rms_diff"] == 0.01
    assert contract["comparison"]["max_abs_diff_p99"] == 0.01
    assert contract["required_command_tokens"] == ["--memory-mode resident"]
    assert contract["required_command_token_groups"][0]["name"] == "resident_throughput_pipeline"
    assert contract["dq_provenance"]["required_source_schemas"] == [
        "resident_dq_coverage_provenance"
    ]
    assert contract["dq_provenance"]["required_engines"] == ["cuda_resident_stack"]
    assert contract["dq_provenance"]["min_active_frame_count"] == 190


def test_resident_cuda_dq_benchmark_contract_profile_honors_overrides():
    contract = build_resident_cuda_dq_benchmark_contract(
        name="custom",
        min_lights=12,
        min_bias=3,
        min_dark=4,
        min_flat=5,
        min_active_frames=11,
        min_speedup_vs_reference=1.5,
        release_baseline_elapsed_s=42.0,
        max_runtime_regression_factor=1.2,
        min_coverage_fraction=0.9,
        max_rms_diff=0.02,
        max_abs_diff_p99=0.03,
        require_resident_route=False,
        require_throughput_route=False,
        dq_map_verify_tile_size=16,
        count_map_verify_tile_size=32,
    )

    assert contract["name"] == "custom"
    assert contract["dataset_requirements"]["light"] == 12
    assert contract["dataset_requirements"]["active_light_frames"] == 11
    assert contract["runtime"] == {
        "min_speedup_vs_reference": 1.5,
        "release_baseline_elapsed_s": 42.0,
        "max_runtime_regression_factor": 1.2,
    }
    assert contract["comparison"]["min_coverage_fraction"] == 0.9
    assert contract["comparison"]["max_rms_diff"] == 0.02
    assert contract["comparison"]["max_abs_diff_p99"] == 0.03
    assert "required_command_tokens" not in contract
    assert "required_command_token_groups" not in contract
    assert contract["dq_provenance"]["dq_map_verify_tile_size"] == 16
    assert contract["dq_provenance"]["count_map_verify_tile_size"] == 32


def test_resident_cuda_dq_benchmark_contract_profile_lists_are_independent():
    first = build_resident_cuda_dq_benchmark_contract()
    second = build_resident_cuda_dq_benchmark_contract()

    first["dq_provenance"]["required_output_dq_flags"].append("mutated")

    assert "mutated" not in second["dq_provenance"]["required_output_dq_flags"]


def test_benchmark_contract_profile_cli_writes_loadable_contract(tmp_path: Path):
    out = tmp_path / "contract.json"

    assert (
        main(
            [
                "benchmark-contract-profile",
                "--out",
                str(out),
                "--min-active-frames",
                "193",
                "--dq-map-verify-tile-size",
                "2",
                "--count-map-verify-tile-size",
                "3",
            ]
        )
        == 0
    )

    contract = load_benchmark_contract(out)
    assert contract["profile"]["name"] == RESIDENT_CUDA_DQ_PROFILE_NAME
    assert contract["dataset_requirements"]["active_light_frames"] == 193
    assert contract["dq_provenance"]["dq_map_verify_tile_size"] == 2
    assert contract["dq_provenance"]["count_map_verify_tile_size"] == 3


def test_acceptance_audit_consumes_generated_resident_dq_contract(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    run = tmp_path / "run"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    contract = tmp_path / "contract.json"
    _write_manifest(manifest)
    _write_resident_dq_run(run)
    _write_wbpp_result(wbpp)
    _write_compare(compare)
    write_json(
        contract,
        build_resident_cuda_dq_benchmark_contract(
            dq_map_verify_tile_size=2,
            count_map_verify_tile_size=2,
        ),
    )

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        benchmark_contract=contract,
    )

    checks = {item["name"]: item for item in audit["checks"]}
    assert audit["passed"] is True
    assert audit["benchmark_contract"]["name"] == "glass_resident_cuda_dq_contract_v1"
    assert checks["contract_dq_provenance_records"]["passed"] is True
    assert checks["contract_dq_engine:cuda_resident_stack"]["passed"] is True
    assert checks["contract_dq_map_pixel_verification"]["passed"] is True
    assert checks["contract_coverage_map_pixel_verification"]["passed"] is True
    assert checks["contract_required_command_token:--memory-mode resident"]["passed"] is True
    assert (
        checks["contract_required_command_token_group:resident_throughput_pipeline"]["passed"]
        is True
    )


def test_acceptance_audit_consumes_builtin_resident_dq_contract_profile(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    run = tmp_path / "run"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    _write_manifest(manifest)
    _write_resident_dq_run(run)
    _write_wbpp_result(wbpp)
    _write_compare(compare)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        benchmark_contract_profile=RESIDENT_CUDA_DQ_PROFILE_NAME,
    )

    checks = {item["name"]: item for item in audit["checks"]}
    assert audit["passed"] is True
    assert audit["benchmark_contract"]["source"] == "profile"
    assert audit["benchmark_contract"]["path"] is None
    assert audit["benchmark_contract"]["profile"] == RESIDENT_CUDA_DQ_PROFILE_NAME
    assert checks["contract_dq_provenance_records"]["passed"] is True
    assert checks["contract_required_command_token:--memory-mode resident"]["passed"] is True


def test_acceptance_audit_cli_accepts_builtin_benchmark_contract_profile(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    run = tmp_path / "run"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    out = tmp_path / "acceptance.json"
    _write_manifest(manifest)
    _write_resident_dq_run(run)
    _write_wbpp_result(wbpp)
    _write_compare(compare)

    assert (
        main(
            [
                "acceptance-audit",
                "--manifest",
                str(manifest),
                "--glass-run",
                str(run),
                "--wbpp-result",
                str(wbpp),
                "--compare-json",
                str(compare),
                "--benchmark-contract-profile",
                RESIDENT_CUDA_DQ_PROFILE_NAME,
                "--min-active-frames",
                "190",
                "--out",
                str(out),
            ]
        )
        == 0
    )

    payload = read_json(out)
    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["benchmark_contract"]["source"] == "profile"
    assert payload["benchmark_contract"]["profile"] == RESIDENT_CUDA_DQ_PROFILE_NAME
    assert checks["contract_dq_map_exists"]["passed"] is True
    assert checks["contract_coverage_map_pixel_verification"]["passed"] is True
