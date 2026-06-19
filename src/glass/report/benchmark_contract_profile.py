from __future__ import annotations

from pathlib import Path
from typing import Any

from glass.io.json_io import write_json
from glass.report.dq_contract_profile import resident_dq_provenance_contract

RESIDENT_CUDA_DQ_PROFILE_NAME = "resident_cuda_dq_v1"
RESIDENT_CUDA_DQ_CONTRACT_NAME = "glass_resident_cuda_dq_contract_v1"


def _optional_number(value: float | None) -> float | None:
    if value is None:
        return None
    return float(value)


def build_resident_cuda_dq_benchmark_contract(
    *,
    name: str = RESIDENT_CUDA_DQ_CONTRACT_NAME,
    min_lights: int = 200,
    min_bias: int = 20,
    min_dark: int = 20,
    min_flat: int = 20,
    min_active_frames: int = 190,
    min_speedup_vs_reference: float | None = 2.0,
    release_baseline_elapsed_s: float | None = None,
    max_runtime_regression_factor: float | None = None,
    min_coverage_fraction: float | None = 0.95,
    max_rms_diff: float | None = 0.01,
    max_abs_diff_p99: float | None = 0.01,
    require_resident_route: bool = True,
    require_throughput_route: bool = True,
    dq_map_verify_tile_size: int = 2048,
    count_map_verify_tile_size: int = 2048,
) -> dict[str, Any]:
    """Build the Phase 2 resident CUDA benchmark contract profile."""

    runtime: dict[str, Any] = {}
    speedup = _optional_number(min_speedup_vs_reference)
    baseline = _optional_number(release_baseline_elapsed_s)
    regression_factor = _optional_number(max_runtime_regression_factor)
    if speedup is not None:
        runtime["min_speedup_vs_reference"] = speedup
    if baseline is not None:
        runtime["release_baseline_elapsed_s"] = baseline
    if regression_factor is not None:
        runtime["max_runtime_regression_factor"] = regression_factor

    comparison: dict[str, Any] = {}
    coverage = _optional_number(min_coverage_fraction)
    rms = _optional_number(max_rms_diff)
    p99 = _optional_number(max_abs_diff_p99)
    if coverage is not None:
        comparison["min_coverage_fraction"] = coverage
    if rms is not None:
        comparison["max_rms_diff"] = rms
    if p99 is not None:
        comparison["max_abs_diff_p99"] = p99

    contract: dict[str, Any] = {
        "schema_version": 1,
        "name": name,
        "profile": {
            "name": RESIDENT_CUDA_DQ_PROFILE_NAME,
            "version": 1,
            "purpose": "phase2_resident_cuda_acceptance",
        },
        "dataset_requirements": {
            "light": int(min_lights),
            "bias": int(min_bias),
            "dark": int(min_dark),
            "flat": int(min_flat),
            "active_light_frames": int(min_active_frames),
        },
        "dq_provenance": resident_dq_provenance_contract(
            min_active_frame_count=int(min_active_frames),
            dq_map_verify_tile_size=int(dq_map_verify_tile_size),
            count_map_verify_tile_size=int(count_map_verify_tile_size),
        ),
    }
    if runtime:
        contract["runtime"] = runtime
    if comparison:
        contract["comparison"] = comparison
    if require_resident_route:
        contract["required_command_tokens"] = ["--memory-mode resident"]
    if require_throughput_route:
        contract["required_command_token_groups"] = [
            {
                "name": "resident_throughput_pipeline",
                "any_of": [
                    "--resident-runtime-preset throughput-v1",
                    "--resident-h2d-mode pinned_ring",
                ],
            }
        ]
    return contract


def write_resident_cuda_dq_benchmark_contract(
    path: str | Path,
    contract: dict[str, Any],
) -> None:
    write_json(path, contract)
