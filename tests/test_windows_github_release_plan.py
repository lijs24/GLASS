from __future__ import annotations

from pathlib import Path
import sys

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.windows_github_release_plan import build_windows_github_release_plan


def _manifest(path: Path, *, zip_paths: dict[str, Path], source: str = "abc1234") -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "artifact_type": "windows_release_manifest",
            "status": "release_manifest_ready",
            "passed": True,
            "failed_checks": [],
            "packages": [
                {
                    "label": label,
                    "zip_path": str(zip_path),
                    "exists": True,
                    "size_bytes": zip_path.stat().st_size,
                    "sha256": f"{index:064x}",
                    "source_stamp": source,
                }
                for index, (label, zip_path) in enumerate(zip_paths.items(), start=1)
            ],
        },
    )


def _phase2_status(path: Path, *, passed: bool = True, gate: int = 204) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "artifact_type": "glass_phase2_status",
            "status": "green" if passed else "attention_required",
            "passed": passed,
            "latest_checkpoint": {"gate": gate, "status": "green" if passed else "failed", "green": passed},
            "acceptance_audit": {
                "status": "passed" if passed else "failed",
                "native_guardrails_bundle_status": "present",
                "resident_result_contract_source": "run_default",
                "resident_result_contract_run_default": True,
                "resident_result_contract_json": "C:/glass_runs/run/resident_result_contract.json",
                "resident_native_calibration_artifact": True,
                "resident_calibration_master_count": 3,
                "resident_calibrated_light_count": 200,
                "resident_registration_fastpath_status": "present",
                "resident_registration_fastpath_contract_status": "passed",
                "resident_registration_fastpath_mode": "similarity_cuda_triangle",
                "triangle_descriptor_fit_batch": True,
                "triangle_descriptor_fit_batch_mode": "native_batch_shared_reference_device",
                "triangle_descriptor_fit_device_reuse": {
                    "reference": True,
                    "moving": True,
                    "output": True,
                },
                "triangle_pixel_refine_batch": True,
                "triangle_pixel_refine_batch_metric_mode": "flattened_frame_candidate_grid",
                "triangle_warp_batch": True,
                "triangle_warp_batch_mode": "native_matrix_lanczos3_frames",
                "triangle_warp_batch_frame_count": 188,
                "resident_warp_copy_mode": "default_stream_async_device_to_device",
                "resident_warp_scratch_bytes": 493209636,
                "resident_registration_fastpath_contract_check_count": 24,
                "resident_registration_fastpath_contract_failed_check_count": 0,
                "resident_registration_fastpath": {
                    "status": "present",
                    "contract_status": "passed",
                    "mode": "similarity_cuda_triangle",
                    "triangle_descriptor_fit_batch": True,
                    "triangle_descriptor_fit_batch_mode": "native_batch_shared_reference_device",
                    "triangle_descriptor_fit_device_reuse": {
                        "reference": True,
                        "moving": True,
                        "output": True,
                    },
                    "triangle_pixel_refine_batch": True,
                    "triangle_pixel_refine_batch_metric_mode": "flattened_frame_candidate_grid",
                    "triangle_warp_batch": True,
                    "triangle_warp_batch_mode": "native_matrix_lanczos3_frames",
                    "triangle_warp_batch_frame_count": 188,
                    "resident_warp_copy_mode": "default_stream_async_device_to_device",
                    "resident_warp_scratch_bytes": 493209636,
                    "contract_check_count": 24,
                    "contract_failed_check_count": 0,
                },
                "native_guardrails_bundle": {
                    "status": "present",
                    "resident_result_contract_source": "run_default",
                    "resident_result_contract_run_default": True,
                    "resident_native_calibration_artifact": True,
                    "resident_calibration_master_count": 3,
                    "resident_calibrated_light_count": 200,
                },
            },
            "pipeline_contract": {
                "status": "passed" if passed else "failed",
                "passed": passed,
                "failed_check_count": 0 if passed else 1,
                "integration_output_count": 1,
                "integration_map_count": 6,
                "integration_dq_contract": passed,
                "integration_stack_result_contract": passed,
                "integration_resident_result_contract": passed,
                "pixel_verification_enabled": True,
                "integration_dq_map_pixels_match_summary": passed,
                "integration_coverage_map_pixels_match_dq": passed,
                "integration_rejection_map_pixels_match_dq": passed,
            },
        },
    )


def _phase2_compare(path: Path, *, passed: bool = True, baseline_gate: int = 203, candidate_gate: int = 204) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "artifact_type": "glass_phase2_status_compare",
            "status": "passed" if passed else "regressed",
            "passed": passed,
            "baseline": {"latest_gate": baseline_gate},
            "candidate": {"latest_gate": candidate_gate},
        },
    )


def test_windows_github_release_plan_records_assets(tmp_path: Path):
    zip_file = tmp_path / "GLASS-Portable-win64-cuda13.zip"
    zip_file.write_bytes(b"zip")
    manifest = tmp_path / "manifest.json"
    _manifest(manifest, zip_paths={"cuda13": zip_file})

    payload = build_windows_github_release_plan(
        manifest_artifact=manifest,
        tag="v0.1.0-test",
        title="Test Release",
        notes_file=tmp_path / "notes.md",
        require_same_source_stamp=True,
    )

    assert payload["passed"] is True
    assert payload["publication_ready"] is True
    assert payload["assets"][0]["label"] == "cuda13"
    assert "gh release create v0.1.0-test" in payload["release"]["command"]
    assert "--draft" in payload["release"]["command"]


def test_windows_github_release_plan_accepts_phase2_handoff_evidence(tmp_path: Path):
    zip_file = tmp_path / "GLASS-Portable-win64-cuda13.zip"
    zip_file.write_bytes(b"zip")
    manifest = tmp_path / "manifest.json"
    phase2_status = tmp_path / "phase2_status.json"
    phase2_compare = tmp_path / "phase2_compare.json"
    _manifest(manifest, zip_paths={"cuda13": zip_file})
    _phase2_status(phase2_status, gate=204)
    _phase2_compare(phase2_compare, baseline_gate=203, candidate_gate=204)

    payload = build_windows_github_release_plan(
        manifest_artifact=manifest,
        tag="v0.1.0-test",
        phase2_status=phase2_status,
        phase2_status_compare=phase2_compare,
    )

    checks = {str(item["name"]): item["passed"] for item in payload["checks"]}
    assert payload["passed"] is True
    assert payload["phase2"]["status"]["latest_gate"] == 204
    assert payload["phase2"]["status"]["resident_result_contract_source"] == "run_default"
    assert payload["phase2"]["status"]["resident_result_contract_run_default"] is True
    assert payload["phase2"]["status"]["resident_native_calibration_artifact"] is True
    assert payload["phase2"]["status"]["resident_calibrated_light_count"] == 200
    assert payload["phase2"]["status"]["resident_registration_fastpath_status"] == "present"
    assert payload["phase2"]["status"]["resident_registration_fastpath_contract_status"] == "passed"
    assert payload["phase2"]["status"]["resident_registration_fastpath_mode"] == "similarity_cuda_triangle"
    assert payload["phase2"]["status"]["triangle_descriptor_fit_batch"] is True
    assert payload["phase2"]["status"]["triangle_warp_batch_frame_count"] == 188
    assert payload["phase2"]["status"]["pipeline_contract_status"] == "passed"
    assert payload["phase2"]["status"]["pipeline_integration_dq_contract"] is True
    assert payload["phase2"]["status"]["pipeline_pixel_verification_enabled"] is True
    assert payload["phase2"]["status_compare"]["candidate_gate"] == 204
    assert checks["phase2_status_present"] is True
    assert checks["phase2_status_green"] is True
    assert checks["phase2_status_compare_present"] is True
    assert checks["phase2_status_compare_passed"] is True


def test_windows_github_release_plan_blocks_failed_phase2_handoff_evidence(tmp_path: Path):
    zip_file = tmp_path / "GLASS-Portable-win64-cuda13.zip"
    zip_file.write_bytes(b"zip")
    manifest = tmp_path / "manifest.json"
    phase2_status = tmp_path / "phase2_status.json"
    phase2_compare = tmp_path / "phase2_compare.json"
    _manifest(manifest, zip_paths={"cuda13": zip_file})
    _phase2_status(phase2_status, passed=False, gate=204)
    _phase2_compare(phase2_compare, passed=False, baseline_gate=204, candidate_gate=203)

    payload = build_windows_github_release_plan(
        manifest_artifact=manifest,
        tag="v0.1.0-test",
        phase2_status=phase2_status,
        phase2_status_compare=phase2_compare,
    )

    checks = {str(item["name"]): item["passed"] for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["publication_ready"] is False
    assert checks["phase2_status_green"] is False
    assert checks["phase2_status_compare_passed"] is False
    assert "phase2_status_green" in payload["failed_checks"]
    assert "phase2_status_compare_passed" in payload["failed_checks"]


def test_windows_github_release_plan_blocks_mixed_sources(tmp_path: Path):
    zip_a = tmp_path / "a.zip"
    zip_b = tmp_path / "b.zip"
    zip_a.write_bytes(b"a")
    zip_b.write_bytes(b"b")
    manifest = tmp_path / "manifest.json"
    _manifest(manifest, zip_paths={"cuda13": zip_a}, source="aaa1111")
    payload = read_json(manifest)
    payload["packages"].append(
        {
            "label": "cpu",
            "zip_path": str(zip_b),
            "exists": True,
            "size_bytes": zip_b.stat().st_size,
            "sha256": "2".zfill(64),
            "source_stamp": "bbb2222",
        }
    )
    write_json(manifest, payload)

    plan = build_windows_github_release_plan(
        manifest_artifact=manifest,
        tag="v0.1.0-test",
        require_same_source_stamp=True,
    )

    checks = {str(item["name"]): item["passed"] for item in plan["checks"]}
    assert plan["passed"] is False
    assert checks["same_source_stamp"] is False


def test_windows_github_release_plan_cli_writes_outputs(tmp_path: Path):
    zip_file = tmp_path / "GLASS-Portable-win64-cpu.zip"
    zip_file.write_bytes(b"cpu")
    manifest = tmp_path / "manifest.json"
    _manifest(manifest, zip_paths={"cpu": zip_file})
    out = tmp_path / "plan.json"
    markdown = tmp_path / "plan.md"
    notes = tmp_path / "notes.md"
    script = tmp_path / "publish_release.ps1"
    phase2_status = tmp_path / "phase2_status.json"
    phase2_compare = tmp_path / "phase2_compare.json"
    _phase2_status(phase2_status)
    _phase2_compare(phase2_compare)

    result = main(
        [
            "windows-github-release-plan",
            "--manifest",
            str(manifest),
            "--tag",
            "v0.1.0-test",
            "--out",
            str(out),
            "--markdown",
            str(markdown),
            "--notes",
            str(notes),
            "--script",
            str(script),
            "--phase2-status",
            str(phase2_status),
            "--phase2-status-compare",
            str(phase2_compare),
            "--require-same-source-stamp",
            "--fail-on-failure",
        ]
    )

    assert result == 0
    payload = read_json(out)
    assert payload["status"] == "release_plan_ready"
    assert payload["release"]["script_file"] == str(script.resolve())
    assert payload["release"]["script_default_mode"] == "dry_run_requires_publish_switch"
    markdown_text = markdown.read_text(encoding="utf-8")
    assert "GLASS Windows GitHub Release Plan" in markdown_text
    assert "Publish script" in markdown_text
    assert "Phase 2 Handoff Preflight" in markdown_text
    assert "Native resident contract source: `run_default`" in markdown_text
    assert "Native calibrated lights: `200`" in markdown_text
    assert "Resident registration fast path: `present`" in markdown_text
    assert "Triangle warp batch: `True`" in markdown_text
    assert "Pipeline contract: `passed`" in markdown_text
    assert "Pipeline integration DQ contract: `True`" in markdown_text
    assert "Recommended Install Order" in notes.read_text(encoding="utf-8")
    notes_text = notes.read_text(encoding="utf-8")
    assert "Native resident contract source: `run_default`" in notes_text
    assert "calibrated lights `200`" in notes_text
    assert "Resident registration fast path: `present`" in notes_text
    assert "warp batch `True` frames `188`" in notes_text
    assert "Pipeline DQ contract: `passed` passed `True` DQ `True`" in notes_text
    assert "Pipeline pixel verification: `True`" in notes_text
    script_text = script.read_text(encoding="utf-8")
    assert "$ExpectedTag = 'v0.1.0-test'" in script_text
    assert "$Phase2StatusFile =" in script_text
    assert "$Phase2StatusCompareFile =" in script_text
    assert "Phase 2 status check failed" in script_text
    assert "Phase 2 status compare check failed" in script_text
    assert "GitHub CLI authentication check failed" in script_text
    assert "Get-FileHash -LiteralPath $asset.Path -Algorithm SHA256" in script_text
    assert "SizeBytes = 3" in script_text
    assert "Re-run this script with -Publish" in script_text
    assert "& $GhPath @releaseArgs" in script_text
    assert "GitHub release creation failed" in script_text


def test_windows_github_release_plan_auth_check_blocks_publication(tmp_path: Path):
    zip_file = tmp_path / "GLASS-Portable-win64-cpu.zip"
    zip_file.write_bytes(b"cpu")
    manifest = tmp_path / "manifest.json"
    _manifest(manifest, zip_paths={"cpu": zip_file})

    payload = build_windows_github_release_plan(
        manifest_artifact=manifest,
        tag="v0.1.0-test",
        gh_path=sys.executable,
        check_gh=True,
        check_gh_auth=True,
    )

    assert payload["passed"] is True
    assert payload["publication_ready"] is False
    assert payload["gh"]["available"] is True
    assert payload["gh"]["auth_ok"] is False
    assert payload["recommendation"] == "authenticate_github_cli_then_run_release_command"
