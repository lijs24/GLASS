from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.gpu.compatibility import recommend_windows_cuda_packages
from glass.io.json_io import read_json, write_json
from glass.report.windows_release_matrix import build_windows_release_matrix


def _blackwell_doctor(path: Path) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "product": "GLASS",
            "cuda": {
                "wrapper_importable": True,
                "native_extension_loaded": True,
                "cuda_available": True,
                "probe_skipped": False,
                "devices": [
                    {
                        "device_id": 0,
                        "name": "NVIDIA RTX PRO 6000 Blackwell Workstation Edition",
                        "compute_capability": "12.0",
                        "memory_total_mib": 97886,
                        "driver_version": "596.21",
                    }
                ],
            },
            "windows_cuda_packages": recommend_windows_cuda_packages(
                [
                    {
                        "device_id": 0,
                        "name": "NVIDIA RTX PRO 6000 Blackwell Workstation Edition",
                        "compute_capability": "12.0",
                        "driver_version": "596.21",
                    }
                ]
            ),
        },
    )


def _cpu_only_doctor(path: Path) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "product": "GLASS",
            "cuda": {
                "wrapper_importable": False,
                "native_extension_loaded": False,
                "cuda_available": False,
                "probe_skipped": False,
                "devices": [],
            },
            "windows_cuda_packages": recommend_windows_cuda_packages([]),
        },
    )


def _release_decision(path: Path, *, ready: bool = True) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "artifact_type": "release_promotion_decision",
            "status": "default_change_ready" if ready else "release_candidate_ready",
            "release_candidate_ready": True,
            "default_change_ready": ready,
            "recommendation": "promote_default_candidate" if ready else "repeat_benchmark_before_default_change",
            "runtime_repeat": {
                "present": True,
                "run_count": 3,
                "considered_run_count": 3,
                "elapsed_ratio_vs_best": 1.0140343433372492,
                "recommendation": "best_observed:repeat02",
            },
        },
    )


def _acceptance(path: Path) -> None:
    write_json(path, {"schema_version": 1, "status": "passed", "passed": True})


def _default_promotion(path: Path, *, ready: bool = True) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "artifact_type": "default_promotion_manifest",
            "status": "default_promotion_ready" if ready else "blocked",
            "passed": ready,
            "default_change_ready": ready,
            "recommendation": "promote_resident_cuda_default"
            if ready
            else "fix_default_blockers",
            "default_candidate": {
                "memory_mode": "resident",
                "fallback_memory_mode": "tile",
                "resident_runtime_preset": "throughput-v1",
                "integration_engine": "cuda_resident_stack",
            },
            "default_route_acceptance": {
                "present": True,
                "status": "passed" if ready else "failed",
                "passed": ready,
                "route_contract_passed": ready,
                "route_check_count": 4 if ready else 2,
                "speedup_vs_reference": 28.75,
            },
        },
    )


def test_windows_release_matrix_passes_blackwell_default(tmp_path: Path):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    acceptance = tmp_path / "acceptance.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision)
    _acceptance(acceptance)
    _default_promotion(default_promotion)

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        acceptance_audit_json=acceptance,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item["passed"] for item in payload["checks"]}
    assert payload["passed"] is True
    assert payload["status"] == "release_matrix_ready"
    assert payload["current_machine"]["primary_package"] == "cuda13"
    assert payload["default_promotion_manifest"]["status"] == "default_promotion_ready"
    assert payload["default_runtime"]["resident_runtime_preset"] == "throughput-v1"
    assert checks["default_promotion_manifest_present"] is True
    assert checks["default_promotion_manifest_ready"] is True
    assert checks["default_promotion_default_route_passed"] is True
    assert checks["required_cuda_package_compatible:cuda13"] is True
    assert checks["required_cuda_package_compatible:cuda12"] is True
    assert checks["required_cuda_package_compatible:cuda11"] is True
    assert [row["label"] for row in payload["packages"]] == ["cuda11", "cuda12", "cuda13", "cpu"]


def test_windows_release_matrix_blocks_cpu_only_cuda_release(tmp_path: Path):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    _cpu_only_doctor(doctor)
    _release_decision(decision)

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
    )

    checks = {item["name"]: item["passed"] for item in payload["checks"]}
    assert payload["passed"] is False
    assert checks["cuda_available_for_release_machine"] is False
    assert checks["required_cuda_package_compatible:cuda13"] is False
    assert payload["recommendation"] == "fix_release_matrix_blockers"


def test_windows_release_matrix_blocks_missing_default_promotion_manifest(tmp_path: Path):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    _blackwell_doctor(doctor)
    _release_decision(decision)

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item["passed"] for item in payload["checks"]}
    assert payload["passed"] is False
    assert checks["default_promotion_manifest_present"] is False
    assert checks["default_promotion_manifest_ready"] is False
    assert checks["default_promotion_default_route_passed"] is False


def test_windows_release_matrix_blocks_failed_default_promotion_manifest(tmp_path: Path):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision)
    _default_promotion(default_promotion, ready=False)

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item["passed"] for item in payload["checks"]}
    assert payload["passed"] is False
    assert checks["default_promotion_manifest_present"] is True
    assert checks["default_promotion_manifest_ready"] is False
    assert checks["default_promotion_default_route_passed"] is False


def test_windows_release_matrix_cli_writes_json_and_markdown(tmp_path: Path):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    default_promotion = tmp_path / "default_promotion.json"
    out = tmp_path / "matrix.json"
    markdown = tmp_path / "matrix.md"
    _blackwell_doctor(doctor)
    _release_decision(decision)
    _default_promotion(default_promotion)

    result = main(
        [
            "windows-release-matrix",
            "--doctor-json",
            str(doctor),
            "--release-decision",
            str(decision),
            "--default-promotion-manifest",
            str(default_promotion),
            "--expected-primary-package",
            "cuda13",
            "--out",
            str(out),
            "--markdown",
            str(markdown),
            "--fail-on-not-ready",
        ]
    )

    assert result == 0
    payload = read_json(out)
    assert payload["passed"] is True
    markdown_text = markdown.read_text(encoding="utf-8")
    assert "GLASS Windows Release Matrix" in markdown_text
    assert "Default Promotion Manifest" in markdown_text
    assert "Default route contract/checks: `True`/`4`" in markdown_text
