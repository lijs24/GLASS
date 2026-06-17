from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from glass.io.json_io import read_json, write_json
from glass.models import now_iso


_CHECKPOINT_RE = re.compile(r"s2_gate_(\d+)_status\.md$")


def _read_json_optional(path: str | Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    target = Path(path)
    if not target.exists():
        return {"path": str(target), "exists": False}
    payload = read_json(target)
    if not isinstance(payload, dict):
        return {"path": str(target), "exists": True, "valid_json_object": False}
    payload = dict(payload)
    payload["_path"] = str(target)
    payload["_exists"] = True
    return payload


def _field_from_status(text: str, key: str) -> str | None:
    prefix = f"- {key}:"
    for line in text.splitlines():
        if line.strip().startswith(prefix):
            return line.split(":", 1)[1].strip()
    return None


def _latest_checkpoint(checkpoint_dir: str | Path) -> dict[str, Any]:
    root = Path(checkpoint_dir)
    candidates: list[tuple[int, Path]] = []
    if root.exists():
        for path in root.glob("s2_gate_*_status.md"):
            match = _CHECKPOINT_RE.match(path.name)
            if match:
                candidates.append((int(match.group(1)), path))
    if not candidates:
        return {"exists": False, "checkpoint_dir": str(root), "gate": None, "status": "missing"}
    gate, path = max(candidates, key=lambda item: item[0])
    text = path.read_text(encoding="utf-8")
    status = _field_from_status(text, "Status")
    scope = _field_from_status(text, "Scope")
    date = _field_from_status(text, "Date")
    return {
        "exists": True,
        "checkpoint_dir": str(root),
        "gate": gate,
        "path": str(path),
        "status": status,
        "scope": scope,
        "date": date,
        "green": str(status).lower() == "green",
    }


def _acceptance_summary(path: str | Path | None) -> dict[str, Any] | None:
    payload = _read_json_optional(path)
    if payload is None:
        return None
    if not payload.get("_exists", payload.get("exists", False)):
        return {
            "path": str(path),
            "exists": False,
            "status": "missing",
            "passed": False,
        }
    speedup = payload.get("speedup_summary") if isinstance(payload.get("speedup_summary"), dict) else {}
    comparison = speedup.get("comparison") if isinstance(speedup.get("comparison"), dict) else {}
    bundle_schema = (
        payload.get("contract_bundle_schema")
        if isinstance(payload.get("contract_bundle_schema"), dict)
        else {}
    )
    resident_contracts = (
        payload.get("resident_contracts") if isinstance(payload.get("resident_contracts"), dict) else {}
    )
    native_guardrails_bundle = _native_guardrails_summary(payload)
    registration_fastpath = _resident_registration_fastpath_summary(payload)
    return {
        "path": payload.get("_path"),
        "exists": True,
        "status": payload.get("status"),
        "passed": payload.get("passed"),
        "benchmark_contract": payload.get("benchmark_contract"),
        "frame_type_counts": payload.get("frame_type_counts"),
        "speedup_vs_reference": speedup.get("speedup_vs_wbpp"),
        "active_frames": speedup.get("glass", {}).get("weighted_frame_count")
        if isinstance(speedup.get("glass"), dict)
        else None,
        "rms_diff": comparison.get("rms_diff"),
        "abs_diff_p99": comparison.get("abs_diff_p99"),
        "coverage_fraction": comparison.get("coverage_fraction"),
        "contract_bundle_schema_status": bundle_schema.get("status"),
        "native_guardrails_bundle": native_guardrails_bundle,
        "native_guardrails_bundle_status": native_guardrails_bundle.get("status")
        if native_guardrails_bundle
        else None,
        "resident_result_contract_source": native_guardrails_bundle.get("resident_result_contract_source")
        if native_guardrails_bundle
        else None,
        "resident_result_contract_run_default": native_guardrails_bundle.get(
            "resident_result_contract_run_default"
        )
        if native_guardrails_bundle
        else None,
        "resident_result_contract_json": native_guardrails_bundle.get("resident_result_contract_json")
        if native_guardrails_bundle
        else None,
        "resident_native_calibration_artifact": native_guardrails_bundle.get(
            "resident_native_calibration_artifact"
        )
        if native_guardrails_bundle
        else None,
        "resident_calibration_master_count": native_guardrails_bundle.get(
            "resident_calibration_master_count"
        )
        if native_guardrails_bundle
        else None,
        "resident_calibrated_light_count": native_guardrails_bundle.get(
            "resident_calibrated_light_count"
        )
        if native_guardrails_bundle
        else None,
        "resident_registration_fastpath": registration_fastpath,
        "resident_registration_fastpath_status": registration_fastpath.get("status")
        if registration_fastpath
        else None,
        "resident_registration_fastpath_contract_status": registration_fastpath.get("contract_status")
        if registration_fastpath
        else None,
        "resident_registration_fastpath_mode": registration_fastpath.get("mode")
        if registration_fastpath
        else None,
        "triangle_descriptor_fit_batch": registration_fastpath.get("triangle_descriptor_fit_batch")
        if registration_fastpath
        else None,
        "triangle_descriptor_fit_batch_mode": registration_fastpath.get(
            "triangle_descriptor_fit_batch_mode"
        )
        if registration_fastpath
        else None,
        "triangle_descriptor_fit_device_reuse": registration_fastpath.get(
            "triangle_descriptor_fit_device_reuse"
        )
        if registration_fastpath
        else None,
        "triangle_pixel_refine_batch": registration_fastpath.get("triangle_pixel_refine_batch")
        if registration_fastpath
        else None,
        "triangle_pixel_refine_batch_metric_mode": registration_fastpath.get(
            "triangle_pixel_refine_batch_metric_mode"
        )
        if registration_fastpath
        else None,
        "triangle_warp_batch": registration_fastpath.get("triangle_warp_batch")
        if registration_fastpath
        else None,
        "triangle_warp_batch_mode": registration_fastpath.get("triangle_warp_batch_mode")
        if registration_fastpath
        else None,
        "triangle_warp_batch_frame_count": registration_fastpath.get(
            "triangle_warp_batch_frame_count"
        )
        if registration_fastpath
        else None,
        "resident_warp_copy_mode": registration_fastpath.get("resident_warp_copy_mode")
        if registration_fastpath
        else None,
        "resident_warp_scratch_bytes": registration_fastpath.get("resident_warp_scratch_bytes")
        if registration_fastpath
        else None,
        "resident_registration_fastpath_contract_check_count": registration_fastpath.get(
            "contract_check_count"
        )
        if registration_fastpath
        else None,
        "resident_registration_fastpath_contract_failed_check_count": registration_fastpath.get(
            "contract_failed_check_count"
        )
        if registration_fastpath
        else None,
        "resident_calibration_contract_passed": (resident_contracts.get("calibration") or {}).get("passed")
        if isinstance(resident_contracts.get("calibration"), dict)
        else None,
        "resident_result_contract_passed": (resident_contracts.get("result") or {}).get("passed")
        if isinstance(resident_contracts.get("result"), dict)
        else None,
    }


def _resident_registration_fastpath_summary(payload: dict[str, Any]) -> dict[str, Any] | None:
    fastpath = (
        payload.get("resident_registration_fastpath")
        if isinstance(payload.get("resident_registration_fastpath"), dict)
        else None
    )
    if fastpath is None:
        return None
    registration = (
        fastpath.get("resident_registration")
        if isinstance(fastpath.get("resident_registration"), dict)
        else {}
    )
    artifact = fastpath.get("artifact") if isinstance(fastpath.get("artifact"), dict) else {}
    io_pipeline = (
        fastpath.get("resident_io_pipeline")
        if isinstance(fastpath.get("resident_io_pipeline"), dict)
        else {}
    )
    contract_checks = [
        item
        for item in payload.get("checks") or []
        if isinstance(item, dict)
        and str(item.get("name") or "").startswith("contract_resident_registration_fastpath")
    ]
    failed_checks = [str(item.get("name")) for item in contract_checks if not item.get("passed")]
    device_reuse = {
        "reference": registration.get("triangle_descriptor_fit_reference_device_reuse"),
        "moving": registration.get("triangle_descriptor_fit_moving_device_reuse"),
        "output": registration.get("triangle_descriptor_fit_output_device_reuse"),
    }
    contract_status = "not_requested"
    if contract_checks:
        contract_status = "passed" if not failed_checks else "failed"
    return {
        "schema_version": 1,
        "status": "present" if fastpath.get("exists") and fastpath.get("available") else "missing",
        "path": fastpath.get("path"),
        "exists": fastpath.get("exists"),
        "available": fastpath.get("available"),
        "artifact_count": fastpath.get("artifact_count"),
        "contract_status": contract_status,
        "contract_check_count": len(contract_checks),
        "contract_failed_check_count": len(failed_checks),
        "contract_failed_checks": failed_checks,
        "mode": registration.get("mode"),
        "triangle_descriptor_fit_batch": registration.get("triangle_descriptor_fit_batch"),
        "triangle_descriptor_fit_batch_mode": registration.get("triangle_descriptor_fit_batch_mode"),
        "triangle_descriptor_fit_device_reuse": device_reuse,
        "triangle_pixel_refine_batch": registration.get("triangle_pixel_refine_batch"),
        "triangle_pixel_refine_batch_mode": registration.get("triangle_pixel_refine_batch_mode"),
        "triangle_pixel_refine_batch_metric_mode": registration.get(
            "triangle_pixel_refine_batch_metric_mode"
        ),
        "triangle_warp_batch": registration.get("triangle_warp_batch"),
        "triangle_warp_batch_mode": registration.get("triangle_warp_batch_mode"),
        "triangle_warp_batch_frame_count": registration.get("triangle_warp_batch_frame_count"),
        "resident_warp_copy_mode": artifact.get("resident_warp_copy_mode"),
        "resident_io_pipeline_warp_copy_mode": io_pipeline.get("warp_copy_mode"),
        "resident_warp_scratch_bytes": artifact.get("resident_warp_scratch_bytes"),
        "resident_io_pipeline_warp_scratch_bytes": io_pipeline.get("warp_scratch_bytes"),
    }


def _native_guardrails_summary(payload: dict[str, Any]) -> dict[str, Any] | None:
    native_guardrails_bundle = (
        payload.get("native_guardrails_bundle")
        if isinstance(payload.get("native_guardrails_bundle"), dict)
        else None
    )
    if native_guardrails_bundle is not None:
        return dict(native_guardrails_bundle)

    contract_bundle = (
        payload.get("contract_bundle") if isinstance(payload.get("contract_bundle"), dict) else None
    )
    if contract_bundle is None:
        return None
    resident_native_calibration = (
        contract_bundle.get("resident_native_calibration")
        if isinstance(contract_bundle.get("resident_native_calibration"), dict)
        else {}
    )
    resident_result_source = contract_bundle.get("resident_result_contract_source")
    return {
        "schema_version": 1,
        "status": "present" if contract_bundle.get("exists") else "missing",
        "bundle_path": contract_bundle.get("path"),
        "bundle_status": contract_bundle.get("status"),
        "guardrails_summary_json": contract_bundle.get("guardrails_summary_json"),
        "resident_result_contract_json": contract_bundle.get("resident_result_contract_json"),
        "resident_result_contract_attached": bool(
            contract_bundle.get("resident_result_contract_attached")
        )
        or contract_bundle.get("resident_result_contract_json") is not None,
        "resident_result_contract_source": resident_result_source,
        "resident_result_contract_run_default": resident_result_source == "run_default",
        "resident_calibration_contract_json": contract_bundle.get("resident_calibration_contract_json"),
        "resident_calibration_contract_attached": bool(
            contract_bundle.get("resident_calibration_contract_attached")
        )
        or contract_bundle.get("resident_calibration_contract_json") is not None,
        "resident_native_calibration_artifact": bool(
            resident_native_calibration.get("artifact_present")
        ),
        "resident_calibration_master_count": resident_native_calibration.get("master_count"),
        "resident_calibrated_light_count": resident_native_calibration.get(
            "resident_calibrated_light_count"
        ),
    }


def _doctor_summary(doctor_payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if doctor_payload is None:
        return None
    cuda = doctor_payload.get("cuda") if isinstance(doctor_payload.get("cuda"), dict) else {}
    devices = cuda.get("devices") if isinstance(cuda.get("devices"), list) else []
    first_device = devices[0] if devices and isinstance(devices[0], dict) else {}
    return {
        "recommendation": doctor_payload.get("recommendation"),
        "cuda_available": cuda.get("cuda_available"),
        "native_extension_loaded": cuda.get("native_extension_loaded"),
        "wrapper_importable": cuda.get("wrapper_importable"),
        "device_count": len(devices),
        "primary_gpu": first_device.get("name"),
        "compute_capability": first_device.get("compute_capability", first_device.get("major_minor")),
        "vram_mib": first_device.get("memory_total_mib", first_device.get("total_global_mem_mib")),
        "driver_version": first_device.get("driver_version"),
        "windows_cuda_packages": doctor_payload.get("windows_cuda_packages"),
    }


def _release_manifest_summary(path: str | Path | None) -> dict[str, Any] | None:
    payload = _read_json_optional(path)
    if payload is None:
        return None
    if not payload.get("_exists", payload.get("exists", False)):
        return {"path": str(path), "exists": False, "status": "missing", "passed": False}
    packages = payload.get("packages") if isinstance(payload.get("packages"), list) else []
    return {
        "path": payload.get("_path"),
        "exists": True,
        "status": payload.get("status"),
        "passed": payload.get("passed"),
        "recommendation": payload.get("recommendation"),
        "package_count": payload.get("package_count", len(packages)),
        "source_stamp": payload.get("source_stamp"),
    }


def _github_release_plan_summary(path: str | Path | None) -> dict[str, Any] | None:
    payload = _read_json_optional(path)
    if payload is None:
        return None
    if not payload.get("_exists", payload.get("exists", False)):
        return {"path": str(path), "exists": False, "status": "missing", "publication_ready": False}
    gh = payload.get("gh") if isinstance(payload.get("gh"), dict) else {}
    script = payload.get("script") if isinstance(payload.get("script"), dict) else {}
    return {
        "path": payload.get("_path"),
        "exists": True,
        "status": payload.get("status"),
        "tag": payload.get("tag"),
        "package_count": payload.get("package_count"),
        "publication_ready": payload.get("publication_ready"),
        "recommendation": payload.get("recommendation"),
        "gh_available": gh.get("available"),
        "gh_auth_ok": gh.get("auth_ok"),
        "script_path": script.get("path"),
        "script_publish_default": script.get("publish_default"),
    }


def _check_passed(payload: dict[str, Any], name: str) -> bool | None:
    checks = payload.get("checks") if isinstance(payload.get("checks"), list) else []
    for item in checks:
        if isinstance(item, dict) and item.get("name") == name:
            return bool(item.get("passed"))
    return None


def _pipeline_contract_summary(path: str | Path | None) -> dict[str, Any] | None:
    payload = _read_json_optional(path)
    if payload is None:
        return None
    if not payload.get("_exists", payload.get("exists", False)):
        return {"path": str(path), "exists": False, "status": "missing", "passed": False}

    checks = [item for item in payload.get("checks") or [] if isinstance(item, dict)]
    failed_checks = [str(item.get("name")) for item in checks if not item.get("passed")]
    integration = payload.get("integration") if isinstance(payload.get("integration"), dict) else {}
    calibration = payload.get("calibration") if isinstance(payload.get("calibration"), dict) else {}
    pixel_verification = (
        payload.get("pixel_verification")
        if isinstance(payload.get("pixel_verification"), dict)
        else {}
    )
    return {
        "path": payload.get("_path"),
        "exists": True,
        "audit_type": payload.get("audit_type"),
        "status": payload.get("status"),
        "passed": payload.get("passed"),
        "check_count": len(checks),
        "failed_check_count": len(failed_checks),
        "failed_checks": failed_checks,
        "integration_output_count": len(integration.get("outputs") or []),
        "integration_map_count": len(integration.get("maps") or []),
        "integration_output_maps_available": _check_passed(
            payload,
            "integration_output_maps_available",
        ),
        "integration_dq_contract": _check_passed(payload, "integration_dq_contract"),
        "integration_stack_result_contract": _check_passed(
            payload,
            "integration_stack_result_contract",
        ),
        "integration_resident_result_contract": _check_passed(
            payload,
            "integration_resident_result_contract",
        ),
        "integration_dq_map_pixels_match_summary": _check_passed(
            payload,
            "integration_dq_map_pixels_match_summary",
        ),
        "integration_coverage_map_pixels_match_dq": _check_passed(
            payload,
            "integration_coverage_map_pixels_match_dq",
        ),
        "integration_rejection_map_pixels_match_dq": _check_passed(
            payload,
            "integration_rejection_map_pixels_match_dq",
        ),
        "pixel_verification_enabled": pixel_verification.get("enabled"),
        "pixel_verification_tile_size": pixel_verification.get("tile_size"),
        "pixel_verification_tolerance_pixels": pixel_verification.get("tolerance_pixels"),
        "calibration_master_count": calibration.get("master_count"),
        "calibrated_light_count": calibration.get("calibrated_light_count"),
        "resident_native_calibration_artifact": calibration.get(
            "resident_native_calibration_artifact"
        ),
        "resident_calibrated_light_count": calibration.get("resident_calibrated_light_count"),
    }


def _release_decision_summary(path: str | Path | None) -> dict[str, Any] | None:
    payload = _read_json_optional(path)
    if payload is None:
        return None
    if not payload.get("_exists", payload.get("exists", False)):
        return {"path": str(path), "exists": False, "status": "missing", "passed": False}

    runtime_repeat = (
        payload.get("runtime_repeat")
        if isinstance(payload.get("runtime_repeat"), dict)
        else {}
    )
    pipeline_handoff = (
        payload.get("pipeline_handoff")
        if isinstance(payload.get("pipeline_handoff"), dict)
        else {}
    )
    speedup = payload.get("speedup") if isinstance(payload.get("speedup"), dict) else {}
    return {
        "path": payload.get("_path"),
        "exists": True,
        "artifact_type": payload.get("artifact_type"),
        "status": payload.get("status"),
        "passed": payload.get("passed"),
        "release_candidate_ready": payload.get("release_candidate_ready"),
        "default_change_ready": payload.get("default_change_ready"),
        "recommendation": payload.get("recommendation"),
        "speedup_actual": speedup.get("actual"),
        "speedup_required_min": speedup.get("required_min"),
        "runtime_repeat_present": runtime_repeat.get("present"),
        "runtime_repeat_run_count": runtime_repeat.get("run_count"),
        "runtime_repeat_considered_run_count": runtime_repeat.get("considered_run_count"),
        "runtime_repeat_best_label": runtime_repeat.get("best_label"),
        "runtime_repeat_best_elapsed_s": runtime_repeat.get("best_elapsed_s"),
        "runtime_repeat_slowest_elapsed_s": runtime_repeat.get("slowest_elapsed_s"),
        "runtime_repeat_elapsed_ratio_vs_best": runtime_repeat.get("elapsed_ratio_vs_best"),
        "runtime_repeat_max_elapsed_ratio_vs_best": runtime_repeat.get(
            "max_elapsed_ratio_vs_best"
        ),
        "runtime_repeat_recommendation": runtime_repeat.get("recommendation"),
        "pipeline_handoff_source": pipeline_handoff.get("source"),
        "pipeline_handoff_status": pipeline_handoff.get("status"),
        "pipeline_handoff_passed": pipeline_handoff.get("passed"),
        "pipeline_handoff_pixel_verification_enabled": pipeline_handoff.get(
            "pixel_verification_enabled"
        ),
    }


def _default_change_is_ready(decision: dict[str, Any] | None) -> bool:
    if not isinstance(decision, dict):
        return False
    return (
        decision.get("default_change_ready") is True
        and decision.get("recommendation") == "promote_default_candidate"
    )


def _resident_fastpath_contract_passed(acceptance: dict[str, Any] | None) -> bool:
    if not isinstance(acceptance, dict):
        return False
    return (
        acceptance.get("resident_registration_fastpath_contract_status") == "passed"
        and int(acceptance.get("resident_registration_fastpath_contract_check_count") or 0) > 0
    )


def build_phase2_status(
    *,
    checkpoint_dir: str | Path,
    acceptance_audit: str | Path | None = None,
    release_manifest: str | Path | None = None,
    github_release_plan: str | Path | None = None,
    pipeline_contract: str | Path | None = None,
    release_decision: str | Path | None = None,
    doctor_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    checkpoint = _latest_checkpoint(checkpoint_dir)
    acceptance = _acceptance_summary(acceptance_audit)
    doctor = _doctor_summary(doctor_payload)
    release = _release_manifest_summary(release_manifest)
    github_plan = _github_release_plan_summary(github_release_plan)
    pipeline = _pipeline_contract_summary(pipeline_contract)
    decision = _release_decision_summary(release_decision)
    checks = [
        {
            "name": "latest_checkpoint_green",
            "passed": bool(checkpoint.get("green")),
            "evidence": {"gate": checkpoint.get("gate"), "status": checkpoint.get("status")},
        }
    ]
    if acceptance is not None:
        checks.append(
            {
                "name": "acceptance_audit_passed",
                "passed": acceptance.get("passed") is True,
                "evidence": {
                    "status": acceptance.get("status"),
                    "speedup_vs_reference": acceptance.get("speedup_vs_reference"),
                },
            }
        )
    if doctor is not None:
        checks.append(
            {
                "name": "cuda_doctor_available",
                "passed": doctor.get("cuda_available") is True,
                "evidence": {
                    "cuda_available": doctor.get("cuda_available"),
                    "primary_gpu": doctor.get("primary_gpu"),
                },
            }
        )
    if release is not None:
        checks.append(
            {
                "name": "release_manifest_ready",
                "passed": release.get("status") == "release_manifest_ready",
                "evidence": {
                    "status": release.get("status"),
                    "package_count": release.get("package_count"),
                },
            }
        )
    if github_plan is not None:
        checks.append(
            {
                "name": "github_release_plan_ready",
                "passed": github_plan.get("status") == "release_plan_ready",
                "evidence": {
                    "status": github_plan.get("status"),
                    "publication_ready": github_plan.get("publication_ready"),
                    "gh_auth_ok": github_plan.get("gh_auth_ok"),
                },
            }
        )
    if pipeline is not None:
        checks.append(
            {
                "name": "pipeline_contract_passed",
                "passed": pipeline.get("passed") is True,
                "evidence": {
                    "status": pipeline.get("status"),
                    "failed_check_count": pipeline.get("failed_check_count"),
                    "integration_dq_contract": pipeline.get("integration_dq_contract"),
                    "pixel_verification_enabled": pipeline.get("pixel_verification_enabled"),
                },
            }
        )
    if decision is not None:
        checks.append(
            {
                "name": "release_decision_default_change_ready",
                "passed": _default_change_is_ready(decision),
                "evidence": {
                    "status": decision.get("status"),
                    "release_candidate_ready": decision.get("release_candidate_ready"),
                    "default_change_ready": decision.get("default_change_ready"),
                    "recommendation": decision.get("recommendation"),
                    "runtime_repeat_elapsed_ratio_vs_best": decision.get(
                        "runtime_repeat_elapsed_ratio_vs_best"
                    ),
                },
            }
        )
        if acceptance is not None and _default_change_is_ready(decision):
            checks.append(
                {
                    "name": "resident_registration_fastpath_contract_passed_for_default",
                    "passed": _resident_fastpath_contract_passed(acceptance),
                    "evidence": {
                        "status": acceptance.get(
                            "resident_registration_fastpath_contract_status"
                        ),
                        "check_count": acceptance.get(
                            "resident_registration_fastpath_contract_check_count"
                        ),
                        "failed_check_count": acceptance.get(
                            "resident_registration_fastpath_contract_failed_check_count"
                        ),
                        "fastpath_status": acceptance.get(
                            "resident_registration_fastpath_status"
                        ),
                        "mode": acceptance.get("resident_registration_fastpath_mode"),
                    },
                }
            )
    passed = all(item["passed"] for item in checks)
    return {
        "schema_version": 1,
        "artifact_type": "glass_phase2_status",
        "created_at": now_iso(),
        "status": "green" if passed else "attention_required",
        "passed": passed,
        "latest_checkpoint": checkpoint,
        "acceptance_audit": acceptance,
        "doctor": doctor,
        "release_manifest": release,
        "github_release_plan": github_plan,
        "pipeline_contract": pipeline,
        "release_decision": decision,
        "checks": checks,
    }


def write_phase2_status_markdown(path: str | Path, payload: dict[str, Any]) -> None:
    checkpoint = payload.get("latest_checkpoint") or {}
    acceptance = payload.get("acceptance_audit") or {}
    doctor = payload.get("doctor") or {}
    release = payload.get("release_manifest") or {}
    github_plan = payload.get("github_release_plan") or {}
    pipeline = payload.get("pipeline_contract") or {}
    decision = payload.get("release_decision") or {}
    lines = [
        "# GLASS Phase 2 Status",
        "",
        f"- Status: {payload.get('status')}",
        f"- Latest checkpoint: S2-Gate {checkpoint.get('gate')} ({checkpoint.get('status')})",
        f"- Checkpoint path: {checkpoint.get('path')}",
    ]
    if acceptance:
        lines.extend(
            [
                "",
                "## Acceptance",
                "",
                f"- Status: {acceptance.get('status')}",
                f"- Speedup vs reference: {acceptance.get('speedup_vs_reference')}",
                f"- Active frames: {acceptance.get('active_frames')}",
                f"- RMS diff: {acceptance.get('rms_diff')}",
                f"- Coverage fraction: {acceptance.get('coverage_fraction')}",
                f"- Contract bundle schema: {acceptance.get('contract_bundle_schema_status')}",
                f"- Resident calibration contract: {acceptance.get('resident_calibration_contract_passed')}",
                f"- Resident result contract: {acceptance.get('resident_result_contract_passed')}",
                f"- Native guardrails bundle: {acceptance.get('native_guardrails_bundle_status')}",
                f"- Native resident result source: {acceptance.get('resident_result_contract_source')}",
                f"- Native resident result run default: {acceptance.get('resident_result_contract_run_default')}",
                f"- Native resident result contract: {acceptance.get('resident_result_contract_json')}",
                f"- Native calibration artifact: {acceptance.get('resident_native_calibration_artifact')}",
                f"- Native calibration masters: {acceptance.get('resident_calibration_master_count')}",
                f"- Native calibrated lights: {acceptance.get('resident_calibrated_light_count')}",
                f"- Registration fast path: {acceptance.get('resident_registration_fastpath_status')}",
                (
                    "- Registration fast path contract: "
                    f"{acceptance.get('resident_registration_fastpath_contract_status')} "
                    f"checks={acceptance.get('resident_registration_fastpath_contract_check_count')} "
                    f"failed={acceptance.get('resident_registration_fastpath_contract_failed_check_count')}"
                ),
                f"- Registration fast path mode: {acceptance.get('resident_registration_fastpath_mode')}",
                f"- Descriptor fit batch: {acceptance.get('triangle_descriptor_fit_batch')}",
                f"- Descriptor fit batch mode: {acceptance.get('triangle_descriptor_fit_batch_mode')}",
                f"- Descriptor device reuse: {acceptance.get('triangle_descriptor_fit_device_reuse')}",
                f"- Pixel refine batch: {acceptance.get('triangle_pixel_refine_batch')}",
                f"- Pixel refine metric mode: {acceptance.get('triangle_pixel_refine_batch_metric_mode')}",
                f"- Triangle warp batch: {acceptance.get('triangle_warp_batch')}",
                f"- Triangle warp batch mode: {acceptance.get('triangle_warp_batch_mode')}",
                f"- Triangle warp batch frames: {acceptance.get('triangle_warp_batch_frame_count')}",
                f"- Resident warp copy mode: {acceptance.get('resident_warp_copy_mode')}",
                f"- Resident warp scratch bytes: {acceptance.get('resident_warp_scratch_bytes')}",
            ]
        )
    if doctor:
        lines.extend(
            [
                "",
                "## CUDA",
                "",
                f"- CUDA available: {doctor.get('cuda_available')}",
                f"- Native extension loaded: {doctor.get('native_extension_loaded')}",
                f"- Primary GPU: {doctor.get('primary_gpu')}",
                f"- Compute capability: {doctor.get('compute_capability')}",
                f"- VRAM MiB: {doctor.get('vram_mib')}",
                f"- Driver: {doctor.get('driver_version')}",
            ]
        )
    if release:
        lines.extend(
            [
                "",
                "## Windows Release",
                "",
                f"- Manifest status: {release.get('status')}",
                f"- Package count: {release.get('package_count')}",
                f"- Recommendation: {release.get('recommendation')}",
            ]
        )
    if github_plan:
        lines.extend(
            [
                "",
                "## GitHub Release Plan",
                "",
                f"- Plan status: {github_plan.get('status')}",
                f"- Tag: {github_plan.get('tag')}",
                f"- Publication ready: {github_plan.get('publication_ready')}",
                f"- GitHub auth OK: {github_plan.get('gh_auth_ok')}",
                f"- Script path: {github_plan.get('script_path')}",
            ]
        )
    if pipeline:
        lines.extend(
            [
                "",
                "## Pipeline Contract",
                "",
                f"- Status: {pipeline.get('status')}",
                f"- Passed: {pipeline.get('passed')}",
                f"- Check count: {pipeline.get('check_count')}",
                f"- Failed checks: {pipeline.get('failed_check_count')}",
                f"- Integration outputs: {pipeline.get('integration_output_count')}",
                f"- Integration maps: {pipeline.get('integration_map_count')}",
                f"- Integration DQ contract: {pipeline.get('integration_dq_contract')}",
                (
                    "- Integration StackEngine result contract: "
                    f"{pipeline.get('integration_stack_result_contract')}"
                ),
                (
                    "- Integration resident result contract: "
                    f"{pipeline.get('integration_resident_result_contract')}"
                ),
                f"- Pixel verification enabled: {pipeline.get('pixel_verification_enabled')}",
                (
                    "- DQ pixels match summary: "
                    f"{pipeline.get('integration_dq_map_pixels_match_summary')}"
                ),
                (
                    "- Coverage pixels match DQ: "
                    f"{pipeline.get('integration_coverage_map_pixels_match_dq')}"
                ),
                (
                    "- Rejection pixels match DQ: "
                    f"{pipeline.get('integration_rejection_map_pixels_match_dq')}"
                ),
            ]
        )
    if decision:
        lines.extend(
            [
                "",
                "## Release Decision",
                "",
                f"- Status: {decision.get('status')}",
                f"- Recommendation: {decision.get('recommendation')}",
                f"- Release candidate ready: {decision.get('release_candidate_ready')}",
                f"- Default change ready: {decision.get('default_change_ready')}",
                f"- Speedup: {decision.get('speedup_actual')}",
                f"- Runtime repeat runs: {decision.get('runtime_repeat_run_count')}",
                (
                    "- Runtime repeat ratio vs best: "
                    f"{decision.get('runtime_repeat_elapsed_ratio_vs_best')}"
                ),
                (
                    "- Runtime repeat best: "
                    f"{decision.get('runtime_repeat_best_label')} "
                    f"{decision.get('runtime_repeat_best_elapsed_s')} s"
                ),
                f"- Pipeline handoff source: {decision.get('pipeline_handoff_source')}",
                (
                    "- Pipeline handoff pixel verification: "
                    f"{decision.get('pipeline_handoff_pixel_verification_enabled')}"
                ),
            ]
        )
    lines.extend(["", "## Checks", ""])
    for item in payload.get("checks") or []:
        marker = "PASS" if item.get("passed") else "FAIL"
        lines.append(f"- {marker}: {item.get('name')} - {item.get('evidence')}")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_phase2_status(
    out_json: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(out_json, payload)
    if markdown is not None:
        write_phase2_status_markdown(markdown, payload)


def _load_phase2_status(path: str | Path) -> dict[str, Any]:
    target = Path(path)
    payload = read_json(target)
    if not isinstance(payload, dict):
        raise ValueError(f"Phase 2 status artifact must be a JSON object: {target}")
    payload = dict(payload)
    payload["_path"] = str(target)
    return payload


def _status_value(payload: dict[str, Any], *keys: str) -> Any:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _compare_check(
    name: str,
    passed: bool,
    *,
    baseline: Any,
    candidate: Any,
    note: str = "",
) -> dict[str, Any]:
    return {
        "name": name,
        "passed": bool(passed),
        "evidence": {"baseline": baseline, "candidate": candidate},
        "note": note,
    }


def build_phase2_status_compare(
    *,
    baseline_status: str | Path,
    candidate_status: str | Path,
) -> dict[str, Any]:
    baseline = _load_phase2_status(baseline_status)
    candidate = _load_phase2_status(candidate_status)
    baseline_gate = _status_value(baseline, "latest_checkpoint", "gate")
    candidate_gate = _status_value(candidate, "latest_checkpoint", "gate")
    checks = [
        _compare_check(
            "baseline_artifact_type",
            baseline.get("artifact_type") == "glass_phase2_status",
            baseline=baseline.get("artifact_type"),
            candidate="glass_phase2_status",
        ),
        _compare_check(
            "candidate_artifact_type",
            candidate.get("artifact_type") == "glass_phase2_status",
            baseline="glass_phase2_status",
            candidate=candidate.get("artifact_type"),
        ),
        _compare_check(
            "latest_checkpoint_gate_not_decreased",
            candidate_gate is not None and baseline_gate is not None and int(candidate_gate) >= int(baseline_gate),
            baseline=baseline_gate,
            candidate=candidate_gate,
        ),
        _compare_check(
            "overall_status_green_preserved",
            baseline.get("status") != "green" or candidate.get("status") == "green",
            baseline=baseline.get("status"),
            candidate=candidate.get("status"),
        ),
        _compare_check(
            "latest_checkpoint_green_preserved",
            _status_value(baseline, "latest_checkpoint", "green") is not True
            or _status_value(candidate, "latest_checkpoint", "green") is True,
            baseline=_status_value(baseline, "latest_checkpoint", "green"),
            candidate=_status_value(candidate, "latest_checkpoint", "green"),
        ),
        _compare_check(
            "acceptance_audit_passed_preserved",
            _status_value(baseline, "acceptance_audit", "passed") is not True
            or _status_value(candidate, "acceptance_audit", "passed") is True,
            baseline=_status_value(baseline, "acceptance_audit", "passed"),
            candidate=_status_value(candidate, "acceptance_audit", "passed"),
        ),
        _compare_check(
            "acceptance_status_preserved",
            _status_value(baseline, "acceptance_audit", "status") != "passed"
            or _status_value(candidate, "acceptance_audit", "status") == "passed",
            baseline=_status_value(baseline, "acceptance_audit", "status"),
            candidate=_status_value(candidate, "acceptance_audit", "status"),
        ),
        _compare_check(
            "resident_registration_fastpath_contract_passed_preserved",
            _status_value(
                baseline,
                "acceptance_audit",
                "resident_registration_fastpath_contract_status",
            )
            != "passed"
            or _status_value(
                candidate,
                "acceptance_audit",
                "resident_registration_fastpath_contract_status",
            )
            == "passed",
            baseline=_status_value(
                baseline,
                "acceptance_audit",
                "resident_registration_fastpath_contract_status",
            ),
            candidate=_status_value(
                candidate,
                "acceptance_audit",
                "resident_registration_fastpath_contract_status",
            ),
        ),
        _compare_check(
            "resident_registration_fastpath_contract_check_count_preserved",
            int(
                _status_value(
                    baseline,
                    "acceptance_audit",
                    "resident_registration_fastpath_contract_check_count",
                )
                or 0
            )
            <= 0
            or int(
                _status_value(
                    candidate,
                    "acceptance_audit",
                    "resident_registration_fastpath_contract_check_count",
                )
                or 0
            )
            >= int(
                _status_value(
                    baseline,
                    "acceptance_audit",
                    "resident_registration_fastpath_contract_check_count",
                )
                or 0
            ),
            baseline=_status_value(
                baseline,
                "acceptance_audit",
                "resident_registration_fastpath_contract_check_count",
            ),
            candidate=_status_value(
                candidate,
                "acceptance_audit",
                "resident_registration_fastpath_contract_check_count",
            ),
        ),
        _compare_check(
            "cuda_available_preserved",
            _status_value(baseline, "doctor", "cuda_available") is not True
            or _status_value(candidate, "doctor", "cuda_available") is True,
            baseline=_status_value(baseline, "doctor", "cuda_available"),
            candidate=_status_value(candidate, "doctor", "cuda_available"),
        ),
        _compare_check(
            "release_manifest_ready_preserved",
            _status_value(baseline, "release_manifest", "status") != "release_manifest_ready"
            or _status_value(candidate, "release_manifest", "status") == "release_manifest_ready",
            baseline=_status_value(baseline, "release_manifest", "status"),
            candidate=_status_value(candidate, "release_manifest", "status"),
        ),
        _compare_check(
            "github_release_plan_ready_preserved",
            _status_value(baseline, "github_release_plan", "status") != "release_plan_ready"
            or _status_value(candidate, "github_release_plan", "status") == "release_plan_ready",
            baseline=_status_value(baseline, "github_release_plan", "status"),
            candidate=_status_value(candidate, "github_release_plan", "status"),
        ),
        _compare_check(
            "pipeline_contract_passed_preserved",
            _status_value(baseline, "pipeline_contract", "passed") is not True
            or _status_value(candidate, "pipeline_contract", "passed") is True,
            baseline=_status_value(baseline, "pipeline_contract", "passed"),
            candidate=_status_value(candidate, "pipeline_contract", "passed"),
        ),
        _compare_check(
            "pipeline_integration_dq_contract_preserved",
            _status_value(baseline, "pipeline_contract", "integration_dq_contract") is not True
            or _status_value(candidate, "pipeline_contract", "integration_dq_contract") is True,
            baseline=_status_value(baseline, "pipeline_contract", "integration_dq_contract"),
            candidate=_status_value(candidate, "pipeline_contract", "integration_dq_contract"),
        ),
        _compare_check(
            "pipeline_pixel_verification_preserved",
            _status_value(baseline, "pipeline_contract", "pixel_verification_enabled") is not True
            or _status_value(candidate, "pipeline_contract", "pixel_verification_enabled") is True,
            baseline=_status_value(baseline, "pipeline_contract", "pixel_verification_enabled"),
            candidate=_status_value(candidate, "pipeline_contract", "pixel_verification_enabled"),
        ),
        _compare_check(
            "release_decision_default_change_ready_preserved",
            _status_value(baseline, "release_decision", "default_change_ready") is not True
            or _status_value(candidate, "release_decision", "default_change_ready") is True,
            baseline=_status_value(baseline, "release_decision", "default_change_ready"),
            candidate=_status_value(candidate, "release_decision", "default_change_ready"),
        ),
        _compare_check(
            "release_decision_promote_recommendation_preserved",
            _status_value(baseline, "release_decision", "recommendation")
            != "promote_default_candidate"
            or _status_value(candidate, "release_decision", "recommendation")
            == "promote_default_candidate",
            baseline=_status_value(baseline, "release_decision", "recommendation"),
            candidate=_status_value(candidate, "release_decision", "recommendation"),
        ),
    ]
    passed = all(item["passed"] for item in checks)
    return {
        "schema_version": 1,
        "artifact_type": "glass_phase2_status_compare",
        "created_at": now_iso(),
        "status": "passed" if passed else "regressed",
        "passed": passed,
        "baseline_path": str(baseline_status),
        "candidate_path": str(candidate_status),
        "baseline": {
            "status": baseline.get("status"),
            "latest_gate": baseline_gate,
            "acceptance_status": _status_value(baseline, "acceptance_audit", "status"),
            "cuda_available": _status_value(baseline, "doctor", "cuda_available"),
            "release_manifest_status": _status_value(baseline, "release_manifest", "status"),
            "github_release_plan_status": _status_value(baseline, "github_release_plan", "status"),
            "pipeline_contract_status": _status_value(baseline, "pipeline_contract", "status"),
            "pipeline_contract_passed": _status_value(baseline, "pipeline_contract", "passed"),
            "release_decision_status": _status_value(baseline, "release_decision", "status"),
            "default_change_ready": _status_value(
                baseline,
                "release_decision",
                "default_change_ready",
            ),
        },
        "candidate": {
            "status": candidate.get("status"),
            "latest_gate": candidate_gate,
            "acceptance_status": _status_value(candidate, "acceptance_audit", "status"),
            "cuda_available": _status_value(candidate, "doctor", "cuda_available"),
            "release_manifest_status": _status_value(candidate, "release_manifest", "status"),
            "github_release_plan_status": _status_value(candidate, "github_release_plan", "status"),
            "pipeline_contract_status": _status_value(candidate, "pipeline_contract", "status"),
            "pipeline_contract_passed": _status_value(candidate, "pipeline_contract", "passed"),
            "release_decision_status": _status_value(candidate, "release_decision", "status"),
            "default_change_ready": _status_value(
                candidate,
                "release_decision",
                "default_change_ready",
            ),
        },
        "checks": checks,
    }


def write_phase2_status_compare_markdown(path: str | Path, payload: dict[str, Any]) -> None:
    lines = [
        "# GLASS Phase 2 Status Compare",
        "",
        f"- Status: {payload.get('status')}",
        f"- Baseline: {payload.get('baseline_path')}",
        f"- Candidate: {payload.get('candidate_path')}",
        "",
        "## Summary",
        "",
        f"- Baseline: {payload.get('baseline')}",
        f"- Candidate: {payload.get('candidate')}",
        "",
        "## Checks",
        "",
    ]
    for item in payload.get("checks") or []:
        marker = "PASS" if item.get("passed") else "FAIL"
        lines.append(f"- {marker}: {item.get('name')} - {item.get('evidence')}")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_phase2_status_compare(
    out_json: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(out_json, payload)
    if markdown is not None:
        write_phase2_status_compare_markdown(markdown, payload)
