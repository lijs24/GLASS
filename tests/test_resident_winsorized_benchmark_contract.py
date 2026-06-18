from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.resident_winsorized_benchmark_contract import DEFAULT_CONTRACT_PATH
from glass.report.resident_winsorized_benchmark_contract import build_resident_winsorized_benchmark_audit
from glass.report.resident_winsorized_benchmark_contract import write_resident_winsorized_benchmark_audit


def _benchmark_payload() -> dict:
    return {
        "schema_version": 1,
        "artifact_type": "resident_winsorized_benchmark",
        "status": "passed",
        "passed": True,
        "config": {
            "frame_count": 8,
            "height": 16,
            "width": 16,
            "seed": 265,
            "low_sigma": 3.0,
            "high_sigma": 3.0,
            "hardened_frame_limit": 256,
            "tolerance_rms": 2e-5,
            "tolerance_max_abs": 2e-4,
        },
        "timing_s": {
            "cpu_baseline": 0.01,
            "cuda_fast_approx": 0.001,
            "cuda_hardened": 0.002,
        },
        "cuda_fast_approx_timing": {
            "resident_winsorized_mode": "fast_approx",
            "native_method": "ResidentCalibratedStack.integrate_sigma_clip",
        },
        "cuda_hardened_timing": {
            "resident_winsorized_mode": "hardened_cpu_parity",
            "native_method": "ResidentCalibratedStack.integrate_hardened_winsorized_sigma",
        },
        "comparisons": {
            "hardened_vs_cpu": {
                "master": {"rms": 5.0e-6, "max_abs": 1.5e-5, "p99_abs": 1.5e-5},
                "weight": {"rms": 0.0, "max_abs": 0.0, "p99_abs": 0.0},
                "coverage": {"rms": 0.0, "max_abs": 0.0, "p99_abs": 0.0},
                "low_rejection": {"rms": 0.0, "max_abs": 0.0, "p99_abs": 0.0},
                "high_rejection": {"rms": 0.0, "max_abs": 0.0, "p99_abs": 0.0},
            },
            "fast_approx_vs_cpu": {
                "master": {"rms": 0.5, "max_abs": 5.0, "p99_abs": 4.0},
                "note": "context only",
            },
        },
        "checks": [{"name": "cuda_available", "passed": True, "evidence": {"cuda_available": True}}],
        "failed_checks": [],
    }


def test_resident_winsorized_benchmark_audit_passes_default_contract(tmp_path: Path) -> None:
    artifact = tmp_path / "benchmark.json"
    write_json(artifact, _benchmark_payload())

    payload = build_resident_winsorized_benchmark_audit(artifact, contract=DEFAULT_CONTRACT_PATH)

    assert payload["passed"] is True
    assert payload["status"] == "passed"
    assert payload["summary"]["hardened_master_rms"] == 5.0e-6
    assert not payload["failed_checks"]


def test_resident_winsorized_benchmark_audit_detects_hardened_rms_drift(tmp_path: Path) -> None:
    drifted = deepcopy(_benchmark_payload())
    drifted["comparisons"]["hardened_vs_cpu"]["master"]["rms"] = 9.0e-4
    artifact = tmp_path / "benchmark.json"
    write_json(artifact, drifted)

    payload = build_resident_winsorized_benchmark_audit(artifact, contract=DEFAULT_CONTRACT_PATH)

    assert payload["passed"] is False
    assert "hardened_master_rms_within_contract" in payload["failed_checks"]


def test_resident_winsorized_benchmark_audit_detects_config_drift(tmp_path: Path) -> None:
    drifted = deepcopy(_benchmark_payload())
    drifted["config"]["seed"] = 999
    artifact = tmp_path / "benchmark.json"
    write_json(artifact, drifted)

    payload = build_resident_winsorized_benchmark_audit(artifact, contract=DEFAULT_CONTRACT_PATH)

    assert payload["passed"] is False
    assert "config_seed_matches_contract" in payload["failed_checks"]


def test_resident_winsorized_benchmark_audit_writes_markdown(tmp_path: Path) -> None:
    artifact = tmp_path / "benchmark.json"
    out = tmp_path / "audit.json"
    markdown = tmp_path / "audit.md"
    write_json(artifact, _benchmark_payload())

    payload = build_resident_winsorized_benchmark_audit(artifact, contract=DEFAULT_CONTRACT_PATH)
    write_resident_winsorized_benchmark_audit(out, payload, markdown=markdown)

    assert read_json(out)["passed"] is True
    assert "Resident Winsorized Benchmark Audit" in markdown.read_text(encoding="utf-8")


def test_resident_winsorized_benchmark_audit_cli_writes_artifacts(tmp_path: Path) -> None:
    artifact = tmp_path / "benchmark.json"
    out = tmp_path / "audit.json"
    markdown = tmp_path / "audit.md"
    write_json(artifact, _benchmark_payload())

    assert (
        main(
            [
                "resident-winsorized-benchmark-audit",
                "--artifact",
                str(artifact),
                "--out",
                str(out),
                "--markdown",
                str(markdown),
                "--fail-on-failure",
            ]
        )
        == 0
    )
    assert read_json(out)["passed"] is True
    assert markdown.exists()


def test_resident_winsorized_benchmark_audit_cli_fail_on_failure(tmp_path: Path) -> None:
    failed = deepcopy(_benchmark_payload())
    failed["passed"] = False
    failed["status"] = "cuda_unavailable"
    failed["checks"] = [{"name": "cuda_available", "passed": False, "evidence": {"reason": "test"}}]
    artifact = tmp_path / "benchmark.json"
    out = tmp_path / "audit.json"
    write_json(artifact, failed)

    assert (
        main(
            [
                "resident-winsorized-benchmark-audit",
                "--artifact",
                str(artifact),
                "--out",
                str(out),
                "--fail-on-failure",
            ]
        )
        == 2
    )
    assert read_json(out)["passed"] is False
