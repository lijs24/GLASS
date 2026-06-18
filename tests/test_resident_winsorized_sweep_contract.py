from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.resident_winsorized_sweep_contract import DEFAULT_CONTRACT_PATH
from glass.report.resident_winsorized_sweep_contract import build_resident_winsorized_sweep_audit
from glass.report.resident_winsorized_sweep_contract import write_resident_winsorized_sweep_audit


def _run(frame_count: int, *, passed: bool = True, rms: float = 1.0e-5) -> dict:
    return {
        "frame_count": frame_count,
        "seed": 268,
        "status": "passed" if passed else "failed",
        "passed": passed,
        "timing_s": {
            "cpu_baseline": 0.01,
            "cuda_fast_approx": 0.001,
            "cuda_hardened": 0.002,
        },
        "comparisons": {
            "hardened_vs_cpu": {
                "master": {"rms": rms, "max_abs": 6.0e-5, "p99_abs": 5.0e-5},
                "weight": {"rms": 0.0, "max_abs": 1.0e-5, "p99_abs": 1.0e-5},
                "coverage": {"rms": 0.0, "max_abs": 0.0, "p99_abs": 0.0},
                "low_rejection": {"rms": 0.0, "max_abs": 0.0, "p99_abs": 0.0},
                "high_rejection": {"rms": 0.0, "max_abs": 0.0, "p99_abs": 0.0},
            },
            "fast_approx_vs_cpu": {
                "master": {"rms": rms, "max_abs": 6.0e-5, "p99_abs": 5.0e-5}
            },
        },
        "cuda_hardened_timing": {
            "resident_winsorized_mode": "hardened_cpu_parity",
            "native_method": "ResidentCalibratedStack.integrate_hardened_winsorized_sigma",
        },
        "cuda_fast_approx_timing": {
            "resident_winsorized_mode": "fast_approx",
            "native_method": "ResidentCalibratedStack.integrate_sigma_clip",
        },
        "failed_checks": [],
    }


def _sweep_payload() -> dict:
    runs = [_run(8), _run(32), _run(128), _run(200, rms=2.3e-5)]
    return {
        "schema_version": 1,
        "artifact_type": "resident_winsorized_frame_count_sweep",
        "status": "passed",
        "passed": True,
        "config": {
            "frame_counts": [8, 32, 128, 200],
            "height": 16,
            "width": 16,
            "seed_base": 268,
            "low_sigma": 3.0,
            "high_sigma": 3.0,
            "tolerance_rms": 5.0e-5,
            "tolerance_max_abs": 2.0e-4,
            "required_frame_count": 200,
            "hardened_frame_limit": 256,
        },
        "runs": runs,
        "checks": [{"name": "all_runs_passed", "passed": True}],
        "failed_checks": [],
        "summary": {
            "run_count": 4,
            "passed_run_count": 4,
            "required_frame_count_present": True,
            "required_frame_count_passed": True,
            "required_frame_count_timing_s": runs[-1]["timing_s"],
            "max_hardened_master_rms": 2.3e-5,
        },
    }


def test_resident_winsorized_sweep_audit_passes_default_contract(tmp_path: Path) -> None:
    artifact = tmp_path / "sweep.json"
    write_json(artifact, _sweep_payload())

    payload = build_resident_winsorized_sweep_audit(artifact, contract=DEFAULT_CONTRACT_PATH)

    assert payload["passed"] is True
    assert payload["status"] == "passed"
    assert payload["summary"]["required_frame_count"] == 200
    assert not payload["failed_checks"]


def test_resident_winsorized_sweep_audit_detects_missing_required_frame(tmp_path: Path) -> None:
    drifted = deepcopy(_sweep_payload())
    drifted["runs"] = drifted["runs"][:-1]
    drifted["config"]["frame_counts"] = [8, 32, 128]
    artifact = tmp_path / "sweep.json"
    write_json(artifact, drifted)

    payload = build_resident_winsorized_sweep_audit(artifact, contract=DEFAULT_CONTRACT_PATH)

    assert payload["passed"] is False
    assert "required_frame_count_present" in payload["failed_checks"]


def test_resident_winsorized_sweep_audit_detects_required_frame_rms_drift(tmp_path: Path) -> None:
    drifted = deepcopy(_sweep_payload())
    drifted["runs"][-1]["comparisons"]["hardened_vs_cpu"]["master"]["rms"] = 8.0e-5
    drifted["summary"]["max_hardened_master_rms"] = 8.0e-5
    artifact = tmp_path / "sweep.json"
    write_json(artifact, drifted)

    payload = build_resident_winsorized_sweep_audit(artifact, contract=DEFAULT_CONTRACT_PATH)

    assert payload["passed"] is False
    assert "frame_200_hardened_master_rms_within_contract" in payload["failed_checks"]
    assert "max_hardened_master_rms_within_contract" in payload["failed_checks"]


def test_resident_winsorized_sweep_audit_writes_markdown(tmp_path: Path) -> None:
    artifact = tmp_path / "sweep.json"
    out = tmp_path / "audit.json"
    markdown = tmp_path / "audit.md"
    write_json(artifact, _sweep_payload())

    payload = build_resident_winsorized_sweep_audit(artifact, contract=DEFAULT_CONTRACT_PATH)
    write_resident_winsorized_sweep_audit(out, payload, markdown=markdown)

    assert read_json(out)["passed"] is True
    assert "Resident Winsorized Sweep Audit" in markdown.read_text(encoding="utf-8")


def test_resident_winsorized_sweep_audit_cli_writes_artifacts(tmp_path: Path) -> None:
    artifact = tmp_path / "sweep.json"
    out = tmp_path / "audit.json"
    markdown = tmp_path / "audit.md"
    write_json(artifact, _sweep_payload())

    assert (
        main(
            [
                "resident-winsorized-sweep-audit",
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
