from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.phase2_status import build_phase2_status, build_phase2_status_compare


def _write_checkpoint(path: Path, *, gate: int, status: str = "green") -> Path:
    target = path / f"s2_gate_{gate}_status.md"
    target.write_text(
        "\n".join(
            [
                f"# S2-Gate {gate} Status",
                "",
                f"- Gate: S2-Gate {gate}",
                "- Scope: fixture checkpoint",
                f"- Status: {status}",
                "- Date: 2026-06-18",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return target


def _write_acceptance(path: Path) -> None:
    write_json(
        path,
        {
            "status": "passed",
            "passed": True,
            "benchmark_contract": {"name": "fixture_contract"},
            "frame_type_counts": {"light": 200, "bias": 20, "dark": 20, "flat": 20},
            "contract_bundle_schema": {"status": "passed"},
            "native_guardrails_bundle": {
                "status": "present",
                "bundle_status": "passed",
                "resident_result_contract_source": "run_default",
                "resident_result_contract_run_default": True,
                "resident_result_contract_json": "C:/glass_runs/run/resident_result_contract.json",
                "resident_native_calibration_artifact": True,
                "resident_calibration_master_count": 3,
                "resident_calibrated_light_count": 200,
            },
            "resident_contracts": {
                "calibration": {"passed": True},
                "result": {"passed": True},
            },
            "speedup_summary": {
                "speedup_vs_wbpp": 58.0,
                "glass": {"weighted_frame_count": 193},
                "comparison": {
                    "rms_diff": 0.001,
                    "abs_diff_p99": 0.002,
                    "coverage_fraction": 0.957,
                },
            },
        },
    )


def _doctor_payload() -> dict:
    return {
        "recommendation": "cuda",
        "cuda": {
            "wrapper_importable": True,
            "native_extension_loaded": True,
            "cuda_available": True,
            "devices": [
                {
                    "device_id": 0,
                    "name": "Fixture GPU",
                    "compute_capability": "12.0",
                    "memory_total_mib": 97886,
                    "driver_version": "596.21",
                }
            ],
        },
        "windows_cuda_packages": {"ordered_try_list": ["cuda13", "cuda12", "cuda11", "cpu"]},
    }


def _status_payload(
    *,
    gate: int = 203,
    status: str = "green",
    checkpoint_green: bool = True,
    acceptance_passed: bool = True,
    acceptance_status: str = "passed",
    cuda_available: bool = True,
    release_status: str = "release_manifest_ready",
    github_status: str = "release_plan_ready",
) -> dict:
    return {
        "schema_version": 1,
        "artifact_type": "glass_phase2_status",
        "status": status,
        "passed": status == "green",
        "latest_checkpoint": {
            "gate": gate,
            "status": "green" if checkpoint_green else "failed",
            "green": checkpoint_green,
        },
        "acceptance_audit": {"status": acceptance_status, "passed": acceptance_passed},
        "doctor": {"cuda_available": cuda_available},
        "release_manifest": {"status": release_status},
        "github_release_plan": {"status": github_status},
        "checks": [],
    }


def test_phase2_status_summarizes_green_handoff(tmp_path: Path):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=201)
    latest = _write_checkpoint(checkpoints, gate=202)
    acceptance = tmp_path / "acceptance.json"
    release = tmp_path / "release_manifest.json"
    github_plan = tmp_path / "github_release_plan.json"
    _write_acceptance(acceptance)
    write_json(
        release,
        {
            "status": "release_manifest_ready",
            "passed": True,
            "recommendation": "ready_for_upload",
            "package_count": 4,
            "source_stamp": "abcdef0",
        },
    )
    write_json(
        github_plan,
        {
            "status": "release_plan_ready",
            "tag": "v0.1.0-test",
            "package_count": 4,
            "publication_ready": False,
            "recommendation": "authenticate_github_cli_then_run_release_command",
            "gh": {"available": True, "auth_ok": False},
            "script": {"path": "publish.ps1", "publish_default": False},
        },
    )

    payload = build_phase2_status(
        checkpoint_dir=checkpoints,
        acceptance_audit=acceptance,
        release_manifest=release,
        github_release_plan=github_plan,
        doctor_payload=_doctor_payload(),
    )

    assert payload["status"] == "green"
    assert payload["latest_checkpoint"]["path"] == str(latest)
    assert payload["acceptance_audit"]["speedup_vs_reference"] == 58.0
    assert payload["acceptance_audit"]["native_guardrails_bundle_status"] == "present"
    assert payload["acceptance_audit"]["resident_result_contract_source"] == "run_default"
    assert payload["acceptance_audit"]["resident_result_contract_run_default"] is True
    assert payload["acceptance_audit"]["resident_native_calibration_artifact"] is True
    assert payload["acceptance_audit"]["resident_calibrated_light_count"] == 200
    assert payload["doctor"]["primary_gpu"] == "Fixture GPU"
    assert payload["release_manifest"]["package_count"] == 4
    assert payload["github_release_plan"]["status"] == "release_plan_ready"


def test_cli_phase2_status_writes_outputs(tmp_path: Path):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=202)
    acceptance = tmp_path / "acceptance.json"
    out = tmp_path / "phase2_status.json"
    markdown = tmp_path / "phase2_status.md"
    _write_acceptance(acceptance)

    result = main(
        [
            "phase2-status",
            "--checkpoint-dir",
            str(checkpoints),
            "--acceptance-audit",
            str(acceptance),
            "--out",
            str(out),
            "--markdown",
            str(markdown),
            "--skip-cuda-probe",
        ]
    )

    assert result == 0
    payload = read_json(out)
    assert payload["artifact_type"] == "glass_phase2_status"
    assert payload["latest_checkpoint"]["gate"] == 202
    assert payload["acceptance_audit"]["contract_bundle_schema_status"] == "passed"
    assert payload["acceptance_audit"]["resident_result_contract_source"] == "run_default"
    text = markdown.read_text(encoding="utf-8")
    assert "GLASS Phase 2 Status" in text
    assert "Acceptance" in text
    assert "Native resident result source: run_default" in text
    assert "Native calibrated lights: 200" in text


def test_phase2_status_compare_passes_non_regression(tmp_path: Path):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    write_json(baseline, _status_payload(gate=203))
    write_json(candidate, _status_payload(gate=204))

    payload = build_phase2_status_compare(
        baseline_status=baseline,
        candidate_status=candidate,
    )

    checks = {item["name"]: item["passed"] for item in payload["checks"]}
    assert payload["status"] == "passed"
    assert checks["latest_checkpoint_gate_not_decreased"] is True
    assert checks["acceptance_audit_passed_preserved"] is True
    assert checks["cuda_available_preserved"] is True
    assert checks["release_manifest_ready_preserved"] is True


def test_phase2_status_compare_flags_handoff_regressions(tmp_path: Path):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    write_json(baseline, _status_payload(gate=203))
    write_json(
        candidate,
        _status_payload(
            gate=202,
            status="attention_required",
            checkpoint_green=False,
            acceptance_passed=False,
            acceptance_status="failed",
            cuda_available=False,
            release_status="failed",
            github_status="failed",
        ),
    )

    payload = build_phase2_status_compare(
        baseline_status=baseline,
        candidate_status=candidate,
    )

    checks = {item["name"]: item["passed"] for item in payload["checks"]}
    assert payload["status"] == "regressed"
    assert checks["latest_checkpoint_gate_not_decreased"] is False
    assert checks["overall_status_green_preserved"] is False
    assert checks["latest_checkpoint_green_preserved"] is False
    assert checks["acceptance_audit_passed_preserved"] is False
    assert checks["acceptance_status_preserved"] is False
    assert checks["cuda_available_preserved"] is False
    assert checks["release_manifest_ready_preserved"] is False
    assert checks["github_release_plan_ready_preserved"] is False


def test_cli_phase2_status_compare_writes_outputs_and_returns_failure(tmp_path: Path):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    out = tmp_path / "compare.json"
    markdown = tmp_path / "compare.md"
    write_json(baseline, _status_payload(gate=203))
    write_json(candidate, _status_payload(gate=202, cuda_available=False))

    result = main(
        [
            "phase2-status-compare",
            "--baseline-status",
            str(baseline),
            "--candidate-status",
            str(candidate),
            "--out",
            str(out),
            "--markdown",
            str(markdown),
            "--fail-on-regression",
        ]
    )

    assert result == 2
    payload = read_json(out)
    assert payload["artifact_type"] == "glass_phase2_status_compare"
    assert payload["status"] == "regressed"
    text = markdown.read_text(encoding="utf-8")
    assert "GLASS Phase 2 Status Compare" in text
    assert "latest_checkpoint_gate_not_decreased" in text
