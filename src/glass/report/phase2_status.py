from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from glass.io.json_io import read_json, write_json
from glass.models import now_iso


_CHECKPOINT_RE = re.compile(r"s2_gate_(\d+)_status\.md$")
_DEFAULT_ROUTE_CHECKS = {
    "memory_mode": "contract_required_command_token:--memory-mode resident",
    "backend": "contract_required_command_token:--backend cuda",
    "resident_registration": (
        "contract_required_command_token:--resident-registration similarity_cuda_triangle"
    ),
    "runtime_preset": "contract_required_command_token_group:resident_h2d_or_runtime_preset",
}


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


def _check_by_name(payload: dict[str, Any], name: str) -> dict[str, Any] | None:
    checks = payload.get("checks") if isinstance(payload.get("checks"), list) else []
    for item in checks:
        if isinstance(item, dict) and item.get("name") == name:
            return item
    return None


def _default_route_acceptance_summary(path: str | Path | None) -> dict[str, Any] | None:
    payload = _read_json_optional(path)
    if payload is None:
        return None
    if not payload.get("_exists", payload.get("exists", False)):
        return {
            "path": str(path),
            "exists": False,
            "status": "missing",
            "passed": False,
            "route_contract_passed": False,
        }
    speedup = payload.get("speedup_summary") if isinstance(payload.get("speedup_summary"), dict) else {}
    comparison = speedup.get("comparison") if isinstance(speedup.get("comparison"), dict) else {}
    route_checks: dict[str, dict[str, Any]] = {}
    for key, check_name in _DEFAULT_ROUTE_CHECKS.items():
        check = _check_by_name(payload, check_name)
        route_checks[key] = {
            "name": check_name,
            "present": check is not None,
            "passed": check.get("passed") is True if isinstance(check, dict) else False,
            "evidence": check.get("evidence") if isinstance(check, dict) else None,
        }
    route_contract_passed = all(item["passed"] for item in route_checks.values())
    return {
        "schema_version": 1,
        "path": payload.get("_path"),
        "exists": True,
        "status": payload.get("status"),
        "passed": payload.get("passed") is True and route_contract_passed,
        "acceptance_passed": payload.get("passed"),
        "benchmark_contract": payload.get("benchmark_contract"),
        "speedup_vs_reference": speedup.get("speedup_vs_wbpp"),
        "active_frames": speedup.get("glass", {}).get("weighted_frame_count")
        if isinstance(speedup.get("glass"), dict)
        else None,
        "rms_diff": comparison.get("rms_diff"),
        "abs_diff_p99": comparison.get("abs_diff_p99"),
        "coverage_fraction": comparison.get("coverage_fraction"),
        "route_contract_passed": route_contract_passed,
        "route_checks": route_checks,
        "route_check_count": len(route_checks),
        "route_failed_checks": [
            item["name"] for item in route_checks.values() if item["passed"] is not True
        ],
    }


def _resident_winsorized_benchmark_audit_summary(path: str | Path | None) -> dict[str, Any] | None:
    payload = _read_json_optional(path)
    if payload is None:
        return None
    if not payload.get("_exists", payload.get("exists", False)):
        return {
            "path": str(path),
            "exists": False,
            "status": "missing",
            "passed": False,
            "failed_checks": ["artifact_missing"],
            "check_count": 0,
            "failed_check_count": 1,
        }
    checks = payload.get("checks") if isinstance(payload.get("checks"), list) else []
    failed_checks = payload.get("failed_checks") if isinstance(payload.get("failed_checks"), list) else []
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    return {
        "schema_version": 1,
        "path": payload.get("_path"),
        "exists": True,
        "status": payload.get("status"),
        "passed": payload.get("passed") is True,
        "contract_name": payload.get("contract_name"),
        "contract_path": payload.get("contract_path"),
        "benchmark_path": payload.get("benchmark_path"),
        "failed_checks": [str(item) for item in failed_checks],
        "check_count": len(checks),
        "failed_check_count": len(failed_checks),
        "frame_count": summary.get("frame_count"),
        "shape": summary.get("shape"),
        "hardened_master_rms": summary.get("hardened_master_rms"),
        "hardened_master_max_abs": summary.get("hardened_master_max_abs"),
        "fast_approx_master_rms": summary.get("fast_approx_master_rms"),
        "cuda_hardened_s": summary.get("cuda_hardened_s"),
        "cuda_fast_approx_s": summary.get("cuda_fast_approx_s"),
        "cpu_baseline_s": summary.get("cpu_baseline_s"),
    }


def _resident_winsorized_sweep_audit_summary(path: str | Path | None) -> dict[str, Any] | None:
    payload = _read_json_optional(path)
    if payload is None:
        return None
    if not payload.get("_exists", payload.get("exists", False)):
        return {
            "path": str(path),
            "exists": False,
            "status": "missing",
            "passed": False,
            "failed_checks": ["artifact_missing"],
            "check_count": 0,
            "failed_check_count": 1,
        }
    checks = payload.get("checks") if isinstance(payload.get("checks"), list) else []
    failed_checks = payload.get("failed_checks") if isinstance(payload.get("failed_checks"), list) else []
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    required_master = (
        summary.get("required_frame_master")
        if isinstance(summary.get("required_frame_master"), dict)
        else {}
    )
    required_timing = (
        summary.get("required_frame_timing_s")
        if isinstance(summary.get("required_frame_timing_s"), dict)
        else {}
    )
    return {
        "schema_version": 1,
        "path": payload.get("_path"),
        "exists": True,
        "status": payload.get("status"),
        "passed": payload.get("passed") is True,
        "contract_name": payload.get("contract_name"),
        "contract_path": payload.get("contract_path"),
        "sweep_path": payload.get("sweep_path"),
        "failed_checks": [str(item) for item in failed_checks],
        "check_count": len(checks),
        "failed_check_count": len(failed_checks),
        "frame_counts": summary.get("frame_counts"),
        "run_count": summary.get("run_count"),
        "required_frame_count": summary.get("required_frame_count"),
        "required_frame_count_passed": summary.get("required_frame_count_passed"),
        "required_frame_master_rms": required_master.get("rms"),
        "required_frame_master_max_abs": required_master.get("max_abs"),
        "max_hardened_master_rms": summary.get("max_hardened_master_rms"),
        "required_frame_cpu_baseline_s": required_timing.get("cpu_baseline"),
        "required_frame_cuda_fast_approx_s": required_timing.get("cuda_fast_approx"),
        "required_frame_cuda_hardened_s": required_timing.get("cuda_hardened"),
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


def _publish_preflight_summary(path: str | Path | None) -> dict[str, Any] | None:
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
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    return {
        "path": payload.get("_path"),
        "exists": True,
        "artifact_type": payload.get("artifact_type"),
        "status": payload.get("status"),
        "passed": payload.get("passed"),
        "recommendation": payload.get("recommendation"),
        "release_tag": summary.get("release_tag"),
        "asset_count": summary.get("asset_count"),
        "package_count": summary.get("package_count"),
        "primary_package": summary.get("primary_package"),
        "ordered_try_list": summary.get("ordered_try_list"),
        "source_stamps": summary.get("source_stamps"),
        "default_promotion_status": summary.get("default_promotion_status"),
        "default_route_check_count": summary.get("default_route_check_count"),
        "default_route_speedup_vs_reference": summary.get(
            "default_route_speedup_vs_reference"
        ),
        "github_plan_phase2_rejection_sample_accounting_status": summary.get(
            "github_plan_phase2_rejection_sample_accounting_status"
        ),
        "github_plan_matrix_rejection_sample_accounting_status": summary.get(
            "github_plan_matrix_rejection_sample_accounting_status"
        ),
        "matrix_rejection_sample_accounting_status": summary.get(
            "matrix_rejection_sample_accounting_status"
        ),
        "default_promotion_rejection_sample_accounting_status": summary.get(
            "default_promotion_rejection_sample_accounting_status"
        ),
        "github_plan_phase2_sample_accounting_closure_status": summary.get(
            "github_plan_phase2_sample_accounting_closure_status"
        ),
        "github_plan_matrix_sample_accounting_closure_status": summary.get(
            "github_plan_matrix_sample_accounting_closure_status"
        ),
        "matrix_sample_accounting_closure_status": summary.get(
            "matrix_sample_accounting_closure_status"
        ),
        "default_promotion_sample_accounting_closure_status": summary.get(
            "default_promotion_sample_accounting_closure_status"
        ),
        "github_plan_phase2_stack_engine_contract_status": summary.get(
            "github_plan_phase2_stack_engine_contract_status"
        ),
        "github_plan_matrix_stack_engine_contract_status": summary.get(
            "github_plan_matrix_stack_engine_contract_status"
        ),
        "matrix_stack_engine_contract_status": summary.get(
            "matrix_stack_engine_contract_status"
        ),
        "default_promotion_stack_engine_contract_status": summary.get(
            "default_promotion_stack_engine_contract_status"
        ),
        "matrix_stack_engine_contract_default_gap_count": summary.get(
            "matrix_stack_engine_contract_default_gap_count"
        ),
        "default_promotion_stack_engine_contract_default_gap_count": summary.get(
            "default_promotion_stack_engine_contract_default_gap_count"
        ),
        "matrix_resident_winsorized_sweep_status": summary.get(
            "matrix_resident_winsorized_sweep_status"
        ),
        "matrix_resident_winsorized_sweep_required_frame_count": summary.get(
            "matrix_resident_winsorized_sweep_required_frame_count"
        ),
        "matrix_resident_winsorized_sweep_required_frame_count_passed": summary.get(
            "matrix_resident_winsorized_sweep_required_frame_count_passed"
        ),
        "matrix_resident_winsorized_sweep_check_count": summary.get(
            "matrix_resident_winsorized_sweep_check_count"
        ),
        "default_promotion_resident_winsorized_sweep_status": summary.get(
            "default_promotion_resident_winsorized_sweep_status"
        ),
        "default_promotion_resident_winsorized_sweep_required_frame_count": summary.get(
            "default_promotion_resident_winsorized_sweep_required_frame_count"
        ),
        "default_promotion_resident_winsorized_sweep_required_frame_count_passed": (
            summary.get(
                "default_promotion_resident_winsorized_sweep_required_frame_count_passed"
            )
        ),
        "default_promotion_resident_winsorized_sweep_check_count": summary.get(
            "default_promotion_resident_winsorized_sweep_check_count"
        ),
        "github_plan_phase2_rejection_sample_accounting_passed": _check_passed(
            payload,
            "github_plan_phase2_rejection_sample_accounting_passed",
        ),
        "github_plan_matrix_rejection_sample_accounting_passed": _check_passed(
            payload,
            "github_plan_matrix_rejection_sample_accounting_passed",
        ),
        "matrix_rejection_sample_accounting_passed": _check_passed(
            payload,
            "matrix_rejection_sample_accounting_passed",
        ),
        "default_promotion_rejection_sample_accounting_passed": _check_passed(
            payload,
            "default_promotion_rejection_sample_accounting_passed",
        ),
        "github_plan_matrix_rejection_accounting_matches_matrix": _check_passed(
            payload,
            "github_plan_matrix_rejection_accounting_matches_matrix",
        ),
        "github_plan_phase2_sample_accounting_closure_passed": _check_passed(
            payload,
            "github_plan_phase2_sample_accounting_closure_passed",
        ),
        "github_plan_matrix_sample_accounting_closure_passed": _check_passed(
            payload,
            "github_plan_matrix_sample_accounting_closure_passed",
        ),
        "matrix_sample_accounting_closure_passed": _check_passed(
            payload,
            "matrix_sample_accounting_closure_passed",
        ),
        "default_promotion_sample_accounting_closure_passed": _check_passed(
            payload,
            "default_promotion_sample_accounting_closure_passed",
        ),
        "github_plan_matrix_sample_closure_matches_matrix": _check_passed(
            payload,
            "github_plan_matrix_sample_closure_matches_matrix",
        ),
        "github_plan_phase2_stack_engine_default_contract_ready": _check_passed(
            payload,
            "github_plan_phase2_stack_engine_default_contract_ready",
        ),
        "github_plan_matrix_stack_engine_contract_ready": _check_passed(
            payload,
            "github_plan_matrix_stack_engine_contract_ready",
        ),
        "github_plan_stack_engine_contract_agreement_passed": _check_passed(
            payload,
            "github_plan_stack_engine_contract_agreement_passed",
        ),
        "matrix_stack_engine_contract_ready": _check_passed(
            payload,
            "matrix_stack_engine_contract_ready",
        ),
        "default_promotion_stack_engine_contract_ready": _check_passed(
            payload,
            "default_promotion_stack_engine_contract_ready",
        ),
        "github_plan_matrix_stack_engine_contract_matches_matrix": _check_passed(
            payload,
            "github_plan_matrix_stack_engine_contract_matches_matrix",
        ),
        "matrix_stack_engine_contract_matches_default_promotion": _check_passed(
            payload,
            "matrix_stack_engine_contract_matches_default_promotion",
        ),
        "matrix_resident_winsorized_sweep_audit_passed": _check_passed(
            payload,
            "matrix_resident_winsorized_sweep_audit_passed",
        ),
        "matrix_resident_winsorized_required_frame_passed": _check_passed(
            payload,
            "matrix_resident_winsorized_required_frame_passed",
        ),
        "matrix_resident_winsorized_sweep_check_count_passed": _check_passed(
            payload,
            "matrix_resident_winsorized_sweep_check_count",
        ),
        "default_promotion_resident_winsorized_sweep_audit_passed": _check_passed(
            payload,
            "default_promotion_resident_winsorized_sweep_audit_passed",
        ),
        "default_promotion_resident_winsorized_required_frame_passed": _check_passed(
            payload,
            "default_promotion_resident_winsorized_required_frame_passed",
        ),
        "default_promotion_resident_winsorized_sweep_matches_matrix": _check_passed(
            payload,
            "default_promotion_resident_winsorized_sweep_matches_matrix",
        ),
        "failed_checks": payload.get("failed_checks"),
    }


def _check_passed(payload: dict[str, Any], name: str) -> bool | None:
    checks = payload.get("checks") if isinstance(payload.get("checks"), list) else []
    for item in checks:
        if isinstance(item, dict) and item.get("name") == name:
            return bool(item.get("passed"))
    return None


def _rejection_sample_accounting_summary(payload: dict[str, Any]) -> dict[str, Any]:
    check_name = "integration_rejection_sample_counts_match_maps"
    checks = [item for item in payload.get("checks") or [] if isinstance(item, dict)]
    check = next((item for item in checks if item.get("name") == check_name), None)
    pixel_verification = (
        payload.get("pixel_verification")
        if isinstance(payload.get("pixel_verification"), dict)
        else {}
    )
    integration_outputs = pixel_verification.get("integration_outputs")
    if not isinstance(integration_outputs, list):
        integration_outputs = []

    rows: list[dict[str, Any]] = []
    for output in integration_outputs:
        if not isinstance(output, dict):
            continue
        accounting = output.get("rejection_sample_accounting")
        if not isinstance(accounting, dict):
            continue
        source_counts = accounting.get("source_counts")
        if not isinstance(source_counts, list):
            source_counts = []
        source_matches = accounting.get("source_matches")
        if not isinstance(source_matches, list):
            source_matches = []
        failed_matches = [
            {
                "source": match.get("source"),
                "actual": match.get("actual"),
                "summary": match.get("summary"),
                "delta": match.get("delta"),
            }
            for match in source_matches
            if isinstance(match, dict) and not match.get("passed")
        ]
        rows.append(
            {
                "item": output.get("item"),
                "status": accounting.get("status"),
                "required": bool(accounting.get("required")),
                "verified": bool(accounting.get("verified")),
                "ok": bool(accounting.get("ok")),
                "rejection": accounting.get("rejection"),
                "map_rejected_sample_sum": accounting.get("map_rejected_sample_sum"),
                "source_counts": source_counts,
                "failed_matches": failed_matches,
            }
        )

    failed_items = [row for row in rows if not row.get("ok")]
    check_present = isinstance(check, dict)
    check_passed = check.get("passed") is True if check_present else None
    if check_present:
        status = "passed" if check_passed else "failed"
    elif rows:
        status = "passed" if not failed_items else "failed"
    else:
        status = "not_available"
    return {
        "schema_version": 1,
        "status": status,
        "check_name": check_name,
        "check_present": check_present,
        "check_passed": check_passed,
        "pixel_verification_enabled": bool(pixel_verification.get("enabled")),
        "output_count": len(integration_outputs),
        "accounted_output_count": len(rows),
        "required_count": sum(1 for row in rows if row.get("required")),
        "verified_count": sum(1 for row in rows if row.get("verified")),
        "failed_count": len(failed_items),
        "failed_items": failed_items,
    }


def _sample_accounting_closure_summary(payload: dict[str, Any]) -> dict[str, Any]:
    check_name = "integration_sample_accounting_closure"
    checks = [item for item in payload.get("checks") or [] if isinstance(item, dict)]
    check = next((item for item in checks if item.get("name") == check_name), None)
    integration = payload.get("integration") if isinstance(payload.get("integration"), dict) else {}
    integration_outputs = integration.get("outputs")
    if not isinstance(integration_outputs, list):
        integration_outputs = []

    rows: list[dict[str, Any]] = []
    for output in integration_outputs:
        if not isinstance(output, dict):
            continue
        closure = output.get("sample_accounting_closure")
        if not isinstance(closure, dict):
            continue
        rows.append(
            {
                "item": output.get("item"),
                "status": closure.get("status"),
                "present": bool(closure.get("present")),
                "required": bool(closure.get("required")),
                "passed": bool(closure.get("passed")),
                "input_total_match": closure.get("input_total_match"),
                "valid_rejection_match": closure.get("valid_rejection_match"),
                "input_samples": closure.get("input_samples"),
                "input_valid_samples_before_rejection": closure.get(
                    "input_valid_samples_before_rejection"
                ),
                "input_invalid_samples_before_rejection": closure.get(
                    "input_invalid_samples_before_rejection"
                ),
                "valid_samples_after_rejection": closure.get(
                    "valid_samples_after_rejection"
                ),
                "rejected_samples": closure.get("rejected_samples"),
                "semantics": closure.get("semantics"),
            }
        )

    failed_items = [row for row in rows if not row.get("passed")]
    check_present = isinstance(check, dict)
    check_passed = check.get("passed") is True if check_present else None
    if check_present:
        status = "passed" if check_passed else "failed"
    elif rows:
        status = "passed" if not failed_items else "failed"
    else:
        status = "not_available"
    return {
        "schema_version": 1,
        "status": status,
        "check_name": check_name,
        "check_present": check_present,
        "check_passed": check_passed,
        "output_count": len(integration_outputs),
        "present_count": sum(1 for row in rows if row.get("present")),
        "required_count": sum(1 for row in rows if row.get("required")),
        "failed_count": len(failed_items),
        "failed_items": failed_items,
        "rows": rows,
    }


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
    rejection_sample_accounting = _rejection_sample_accounting_summary(payload)
    sample_accounting_closure = _sample_accounting_closure_summary(payload)
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
        "integration_rejection_sample_counts_match_maps": _check_passed(
            payload,
            "integration_rejection_sample_counts_match_maps",
        ),
        "integration_sample_accounting_closure": _check_passed(
            payload,
            "integration_sample_accounting_closure",
        ),
        "rejection_sample_accounting": rejection_sample_accounting,
        "rejection_sample_accounting_status": rejection_sample_accounting.get("status"),
        "rejection_sample_accounting_check_present": rejection_sample_accounting.get(
            "check_present"
        ),
        "rejection_sample_accounting_failed_count": rejection_sample_accounting.get(
            "failed_count"
        ),
        "sample_accounting_closure": sample_accounting_closure,
        "sample_accounting_closure_status": sample_accounting_closure.get("status"),
        "sample_accounting_closure_check_present": sample_accounting_closure.get(
            "check_present"
        ),
        "sample_accounting_closure_present_count": sample_accounting_closure.get(
            "present_count"
        ),
        "sample_accounting_closure_failed_count": sample_accounting_closure.get(
            "failed_count"
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


def _stack_engine_contract_summary(path: str | Path | None) -> dict[str, Any] | None:
    payload = _read_json_optional(path)
    if payload is None:
        return None
    if not payload.get("_exists", payload.get("exists", False)):
        return {
            "path": str(path),
            "exists": False,
            "status": "missing",
            "passed": False,
            "default_promotion_ready": False,
        }

    checks = [item for item in payload.get("checks") or [] if isinstance(item, dict)]
    failed_checks = [str(item.get("name")) for item in checks if not item.get("passed")]
    adoption = payload.get("adoption") if isinstance(payload.get("adoption"), dict) else {}
    default_promotion = (
        payload.get("default_promotion")
        if isinstance(payload.get("default_promotion"), dict)
        else {}
    )
    gap_surfaces = adoption.get("gap_surfaces") if isinstance(adoption.get("gap_surfaces"), list) else []
    blockers = (
        default_promotion.get("blockers")
        if isinstance(default_promotion.get("blockers"), list)
        else []
    )
    return {
        "path": payload.get("_path"),
        "exists": True,
        "audit_type": payload.get("audit_type"),
        "status": payload.get("status"),
        "passed": payload.get("passed"),
        "scope": payload.get("scope"),
        "expected_integration_engine": payload.get("expected_integration_engine"),
        "resident_calibration_contract_attached": payload.get(
            "resident_calibration_contract_attached"
        ),
        "resident_result_contract_attached": payload.get("resident_result_contract_attached"),
        "check_count": len(checks),
        "failed_check_count": len(failed_checks),
        "failed_checks": failed_checks,
        "adoption_target_engine": adoption.get("target_engine"),
        "adoption_surface_count": adoption.get("surface_count"),
        "adoption_stack_engine_surface_count": adoption.get("stack_engine_surface_count"),
        "adoption_cuda_resident_surface_count": adoption.get("cuda_resident_surface_count"),
        "adoption_contract_ready_count": adoption.get("contract_ready_count"),
        "adoption_result_contract_passed_count": adoption.get(
            "result_contract_passed_count"
        ),
        "adoption_fallback_count": adoption.get("fallback_count"),
        "adoption_phase2_stack_engine_default_gap_count": adoption.get(
            "phase2_stack_engine_default_gap_count"
        ),
        "adoption_recommendation": adoption.get("recommendation"),
        "adoption_gap_surfaces": gap_surfaces,
        "default_promotion_ready": default_promotion.get("ready"),
        "default_promotion_status": default_promotion.get("status"),
        "default_promotion_required_scope": default_promotion.get("required_scope"),
        "default_promotion_actual_scope": default_promotion.get("actual_scope"),
        "default_promotion_surface_count": default_promotion.get("surface_count"),
        "default_promotion_calibration_surface_count": default_promotion.get(
            "calibration_surface_count"
        ),
        "default_promotion_integration_surface_count": default_promotion.get(
            "integration_surface_count"
        ),
        "default_promotion_phase2_stack_engine_default_gap_count": (
            default_promotion.get("phase2_stack_engine_default_gap_count")
        ),
        "default_promotion_recommendation": default_promotion.get("recommendation"),
        "default_promotion_blocker_count": default_promotion.get(
            "blocker_count",
            len(blockers),
        ),
        "default_promotion_blockers": blockers,
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


def _stack_engine_default_contract_ready(contract: dict[str, Any] | None) -> bool:
    if not isinstance(contract, dict):
        return False
    adoption_gap_count = int(contract.get("adoption_phase2_stack_engine_default_gap_count") or 0)
    promotion_gap_count = int(
        contract.get("default_promotion_phase2_stack_engine_default_gap_count") or 0
    )
    return (
        contract.get("audit_type") == "stack_engine_default_contract"
        and contract.get("status") == "passed"
        and contract.get("passed") is True
        and contract.get("default_promotion_ready") is True
        and contract.get("default_promotion_status") == "ready"
        and contract.get("adoption_recommendation") == "stack_engine_default_ready"
        and contract.get("default_promotion_recommendation") == "stack_engine_default_ready"
        and adoption_gap_count == 0
        and promotion_gap_count == 0
        and int(contract.get("default_promotion_blocker_count") or 0) == 0
    )


def build_phase2_status(
    *,
    checkpoint_dir: str | Path,
    acceptance_audit: str | Path | None = None,
    default_route_acceptance_audit: str | Path | None = None,
    release_manifest: str | Path | None = None,
    github_release_plan: str | Path | None = None,
    publish_preflight: str | Path | None = None,
    pipeline_contract: str | Path | None = None,
    stack_engine_contract: str | Path | None = None,
    resident_winsorized_benchmark_audit: str | Path | None = None,
    resident_winsorized_sweep_audit: str | Path | None = None,
    release_decision: str | Path | None = None,
    doctor_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    checkpoint = _latest_checkpoint(checkpoint_dir)
    acceptance = _acceptance_summary(acceptance_audit)
    default_route_acceptance = _default_route_acceptance_summary(default_route_acceptance_audit)
    doctor = _doctor_summary(doctor_payload)
    release = _release_manifest_summary(release_manifest)
    github_plan = _github_release_plan_summary(github_release_plan)
    preflight = _publish_preflight_summary(publish_preflight)
    pipeline = _pipeline_contract_summary(pipeline_contract)
    stack_engine = _stack_engine_contract_summary(stack_engine_contract)
    winsorized_audit = _resident_winsorized_benchmark_audit_summary(
        resident_winsorized_benchmark_audit
    )
    winsorized_sweep_audit = _resident_winsorized_sweep_audit_summary(
        resident_winsorized_sweep_audit
    )
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
    if default_route_acceptance is not None:
        checks.append(
            {
                "name": "default_route_acceptance_passed",
                "passed": default_route_acceptance.get("passed") is True,
                "evidence": {
                    "status": default_route_acceptance.get("status"),
                    "acceptance_passed": default_route_acceptance.get("acceptance_passed"),
                    "speedup_vs_reference": default_route_acceptance.get("speedup_vs_reference"),
                },
            }
        )
        checks.append(
            {
                "name": "default_route_acceptance_route_contract_passed",
                "passed": default_route_acceptance.get("route_contract_passed") is True,
                "evidence": {
                    "route_check_count": default_route_acceptance.get("route_check_count"),
                    "route_failed_checks": default_route_acceptance.get("route_failed_checks"),
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
    if preflight is not None:
        checks.append(
            {
                "name": "windows_publish_preflight_ready",
                "passed": preflight.get("status") == "publish_preflight_ready"
                and preflight.get("passed") is True,
                "evidence": {
                    "status": preflight.get("status"),
                    "passed": preflight.get("passed"),
                    "asset_count": preflight.get("asset_count"),
                    "package_count": preflight.get("package_count"),
                    "primary_package": preflight.get("primary_package"),
                    "default_route_check_count": preflight.get("default_route_check_count"),
                    "failed_checks": preflight.get("failed_checks"),
                },
            }
        )
        checks.append(
            {
                "name": "windows_publish_preflight_rejection_sample_accounting_passed",
                "passed": (
                    preflight.get("github_plan_phase2_rejection_sample_accounting_passed")
                    is True
                    and preflight.get(
                        "github_plan_matrix_rejection_sample_accounting_passed"
                    )
                    is True
                    and preflight.get("matrix_rejection_sample_accounting_passed") is True
                    and preflight.get(
                        "default_promotion_rejection_sample_accounting_passed"
                    )
                    is True
                    and preflight.get(
                        "github_plan_matrix_rejection_accounting_matches_matrix"
                    )
                    is True
                ),
                "evidence": {
                    "phase2_status": preflight.get(
                        "github_plan_phase2_rejection_sample_accounting_status"
                    ),
                    "plan_matrix_status": preflight.get(
                        "github_plan_matrix_rejection_sample_accounting_status"
                    ),
                    "matrix_status": preflight.get(
                        "matrix_rejection_sample_accounting_status"
                    ),
                    "default_promotion_status": preflight.get(
                        "default_promotion_rejection_sample_accounting_status"
                    ),
                    "phase2_check": preflight.get(
                        "github_plan_phase2_rejection_sample_accounting_passed"
                    ),
                    "plan_matrix_check": preflight.get(
                        "github_plan_matrix_rejection_sample_accounting_passed"
                    ),
                    "matrix_check": preflight.get(
                        "matrix_rejection_sample_accounting_passed"
                    ),
                    "default_promotion_check": preflight.get(
                        "default_promotion_rejection_sample_accounting_passed"
                    ),
                    "matrix_match_check": preflight.get(
                        "github_plan_matrix_rejection_accounting_matches_matrix"
                    ),
                    "failed_checks": preflight.get("failed_checks"),
                },
            }
        )
        checks.append(
            {
                "name": "windows_publish_preflight_sample_accounting_closure_passed",
                "passed": (
                    preflight.get("github_plan_phase2_sample_accounting_closure_passed")
                    is True
                    and preflight.get(
                        "github_plan_matrix_sample_accounting_closure_passed"
                    )
                    is True
                    and preflight.get("matrix_sample_accounting_closure_passed") is True
                    and preflight.get(
                        "default_promotion_sample_accounting_closure_passed"
                    )
                    is True
                    and preflight.get("github_plan_matrix_sample_closure_matches_matrix")
                    is True
                ),
                "evidence": {
                    "phase2_status": preflight.get(
                        "github_plan_phase2_sample_accounting_closure_status"
                    ),
                    "plan_matrix_status": preflight.get(
                        "github_plan_matrix_sample_accounting_closure_status"
                    ),
                    "matrix_status": preflight.get(
                        "matrix_sample_accounting_closure_status"
                    ),
                    "default_promotion_status": preflight.get(
                        "default_promotion_sample_accounting_closure_status"
                    ),
                    "phase2_check": preflight.get(
                        "github_plan_phase2_sample_accounting_closure_passed"
                    ),
                    "plan_matrix_check": preflight.get(
                        "github_plan_matrix_sample_accounting_closure_passed"
                    ),
                    "matrix_check": preflight.get("matrix_sample_accounting_closure_passed"),
                    "default_promotion_check": preflight.get(
                        "default_promotion_sample_accounting_closure_passed"
                    ),
                    "matrix_match_check": preflight.get(
                        "github_plan_matrix_sample_closure_matches_matrix"
                    ),
                    "failed_checks": preflight.get("failed_checks"),
                },
            }
        )
        checks.append(
            {
                "name": "windows_publish_preflight_stack_engine_default_contract_ready",
                "passed": (
                    preflight.get(
                        "github_plan_phase2_stack_engine_default_contract_ready"
                    )
                    is True
                    and preflight.get("github_plan_matrix_stack_engine_contract_ready")
                    is True
                    and preflight.get(
                        "github_plan_stack_engine_contract_agreement_passed"
                    )
                    is True
                    and preflight.get("matrix_stack_engine_contract_ready") is True
                    and preflight.get("default_promotion_stack_engine_contract_ready")
                    is True
                    and preflight.get(
                        "github_plan_matrix_stack_engine_contract_matches_matrix"
                    )
                    is True
                    and preflight.get(
                        "matrix_stack_engine_contract_matches_default_promotion"
                    )
                    is True
                ),
                "evidence": {
                    "phase2_status": preflight.get(
                        "github_plan_phase2_stack_engine_contract_status"
                    ),
                    "plan_matrix_status": preflight.get(
                        "github_plan_matrix_stack_engine_contract_status"
                    ),
                    "matrix_status": preflight.get(
                        "matrix_stack_engine_contract_status"
                    ),
                    "default_promotion_status": preflight.get(
                        "default_promotion_stack_engine_contract_status"
                    ),
                    "matrix_default_gap_count": preflight.get(
                        "matrix_stack_engine_contract_default_gap_count"
                    ),
                    "default_promotion_default_gap_count": preflight.get(
                        "default_promotion_stack_engine_contract_default_gap_count"
                    ),
                    "phase2_check": preflight.get(
                        "github_plan_phase2_stack_engine_default_contract_ready"
                    ),
                    "plan_matrix_check": preflight.get(
                        "github_plan_matrix_stack_engine_contract_ready"
                    ),
                    "agreement_check": preflight.get(
                        "github_plan_stack_engine_contract_agreement_passed"
                    ),
                    "matrix_check": preflight.get(
                        "matrix_stack_engine_contract_ready"
                    ),
                    "default_promotion_check": preflight.get(
                        "default_promotion_stack_engine_contract_ready"
                    ),
                    "plan_matrix_match_check": preflight.get(
                        "github_plan_matrix_stack_engine_contract_matches_matrix"
                    ),
                    "default_promotion_match_check": preflight.get(
                        "matrix_stack_engine_contract_matches_default_promotion"
                    ),
                    "failed_checks": preflight.get("failed_checks"),
                },
            }
        )
        checks.append(
            {
                "name": "windows_publish_preflight_resident_winsorized_sweep_passed",
                "passed": (
                    preflight.get("matrix_resident_winsorized_sweep_audit_passed")
                    is True
                    and preflight.get(
                        "matrix_resident_winsorized_required_frame_passed"
                    )
                    is True
                    and preflight.get(
                        "matrix_resident_winsorized_sweep_check_count_passed"
                    )
                    is True
                    and preflight.get(
                        "default_promotion_resident_winsorized_sweep_audit_passed"
                    )
                    is True
                    and preflight.get(
                        "default_promotion_resident_winsorized_required_frame_passed"
                    )
                    is True
                    and preflight.get(
                        "default_promotion_resident_winsorized_sweep_matches_matrix"
                    )
                    is True
                ),
                "evidence": {
                    "matrix_status": preflight.get(
                        "matrix_resident_winsorized_sweep_status"
                    ),
                    "matrix_required_frame_count": preflight.get(
                        "matrix_resident_winsorized_sweep_required_frame_count"
                    ),
                    "matrix_required_frame_count_passed": preflight.get(
                        "matrix_resident_winsorized_sweep_required_frame_count_passed"
                    ),
                    "matrix_check_count": preflight.get(
                        "matrix_resident_winsorized_sweep_check_count"
                    ),
                    "default_promotion_status": preflight.get(
                        "default_promotion_resident_winsorized_sweep_status"
                    ),
                    "default_promotion_required_frame_count": preflight.get(
                        "default_promotion_resident_winsorized_sweep_required_frame_count"
                    ),
                    "default_promotion_required_frame_count_passed": preflight.get(
                        "default_promotion_resident_winsorized_sweep_required_frame_count_passed"
                    ),
                    "default_promotion_check_count": preflight.get(
                        "default_promotion_resident_winsorized_sweep_check_count"
                    ),
                    "matrix_audit_check": preflight.get(
                        "matrix_resident_winsorized_sweep_audit_passed"
                    ),
                    "matrix_required_frame_check": preflight.get(
                        "matrix_resident_winsorized_required_frame_passed"
                    ),
                    "matrix_check_count_check": preflight.get(
                        "matrix_resident_winsorized_sweep_check_count_passed"
                    ),
                    "default_promotion_audit_check": preflight.get(
                        "default_promotion_resident_winsorized_sweep_audit_passed"
                    ),
                    "default_promotion_required_frame_check": preflight.get(
                        "default_promotion_resident_winsorized_required_frame_passed"
                    ),
                    "default_promotion_match_check": preflight.get(
                        "default_promotion_resident_winsorized_sweep_matches_matrix"
                    ),
                    "failed_checks": preflight.get("failed_checks"),
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
        rejection_accounting = (
            pipeline.get("rejection_sample_accounting")
            if isinstance(pipeline.get("rejection_sample_accounting"), dict)
            else {}
        )
        requires_rejection_accounting = (
            pipeline.get("pixel_verification_enabled") is True
            or rejection_accounting.get("check_present") is True
            or int(rejection_accounting.get("accounted_output_count") or 0) > 0
        )
        checks.append(
            {
                "name": "pipeline_rejection_sample_accounting_passed",
                "passed": (not requires_rejection_accounting)
                or rejection_accounting.get("status") == "passed",
                "evidence": {
                    "status": rejection_accounting.get("status"),
                    "check_present": rejection_accounting.get("check_present"),
                    "check_passed": rejection_accounting.get("check_passed"),
                    "pixel_verification_enabled": rejection_accounting.get(
                        "pixel_verification_enabled"
                    ),
                    "accounted_output_count": rejection_accounting.get(
                        "accounted_output_count"
                    ),
                    "failed_count": rejection_accounting.get("failed_count"),
                    "failed_items": rejection_accounting.get("failed_items"),
                },
            }
        )
        sample_closure = (
            pipeline.get("sample_accounting_closure")
            if isinstance(pipeline.get("sample_accounting_closure"), dict)
            else {}
        )
        requires_sample_closure = (
            sample_closure.get("check_present") is True
            or int(sample_closure.get("present_count") or 0) > 0
        )
        checks.append(
            {
                "name": "pipeline_sample_accounting_closure_passed",
                "passed": (not requires_sample_closure)
                or sample_closure.get("status") == "passed",
                "evidence": {
                    "status": sample_closure.get("status"),
                    "check_present": sample_closure.get("check_present"),
                    "check_passed": sample_closure.get("check_passed"),
                    "present_count": sample_closure.get("present_count"),
                    "required_count": sample_closure.get("required_count"),
                    "failed_count": sample_closure.get("failed_count"),
                    "failed_items": sample_closure.get("failed_items"),
                },
            }
        )
    if stack_engine is not None:
        checks.append(
            {
                "name": "stack_engine_default_contract_ready",
                "passed": _stack_engine_default_contract_ready(stack_engine),
                "evidence": {
                    "status": stack_engine.get("status"),
                    "passed": stack_engine.get("passed"),
                    "scope": stack_engine.get("scope"),
                    "expected_integration_engine": stack_engine.get(
                        "expected_integration_engine"
                    ),
                    "adoption_recommendation": stack_engine.get(
                        "adoption_recommendation"
                    ),
                    "adoption_gap_count": stack_engine.get(
                        "adoption_phase2_stack_engine_default_gap_count"
                    ),
                    "default_promotion_ready": stack_engine.get(
                        "default_promotion_ready"
                    ),
                    "default_promotion_status": stack_engine.get(
                        "default_promotion_status"
                    ),
                    "default_promotion_blocker_count": stack_engine.get(
                        "default_promotion_blocker_count"
                    ),
                    "failed_checks": stack_engine.get("failed_checks"),
                    "blockers": stack_engine.get("default_promotion_blockers"),
                },
            }
        )
    if winsorized_audit is not None:
        checks.append(
            {
                "name": "resident_winsorized_benchmark_audit_passed",
                "passed": winsorized_audit.get("passed") is True,
                "evidence": {
                    "status": winsorized_audit.get("status"),
                    "contract_name": winsorized_audit.get("contract_name"),
                    "check_count": winsorized_audit.get("check_count"),
                    "failed_check_count": winsorized_audit.get("failed_check_count"),
                    "failed_checks": winsorized_audit.get("failed_checks"),
                    "hardened_master_rms": winsorized_audit.get("hardened_master_rms"),
                    "hardened_master_max_abs": winsorized_audit.get(
                        "hardened_master_max_abs"
                    ),
                    "fast_approx_master_rms": winsorized_audit.get(
                        "fast_approx_master_rms"
                    ),
                },
            }
        )
    if winsorized_sweep_audit is not None:
        checks.append(
            {
                "name": "resident_winsorized_sweep_audit_passed",
                "passed": winsorized_sweep_audit.get("passed") is True,
                "evidence": {
                    "status": winsorized_sweep_audit.get("status"),
                    "contract_name": winsorized_sweep_audit.get("contract_name"),
                    "check_count": winsorized_sweep_audit.get("check_count"),
                    "failed_check_count": winsorized_sweep_audit.get("failed_check_count"),
                    "failed_checks": winsorized_sweep_audit.get("failed_checks"),
                    "required_frame_count": winsorized_sweep_audit.get("required_frame_count"),
                    "required_frame_count_passed": winsorized_sweep_audit.get(
                        "required_frame_count_passed"
                    ),
                    "required_frame_master_rms": winsorized_sweep_audit.get(
                        "required_frame_master_rms"
                    ),
                    "required_frame_master_max_abs": winsorized_sweep_audit.get(
                        "required_frame_master_max_abs"
                    ),
                    "max_hardened_master_rms": winsorized_sweep_audit.get(
                        "max_hardened_master_rms"
                    ),
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
        "default_route_acceptance": default_route_acceptance,
        "doctor": doctor,
        "release_manifest": release,
        "github_release_plan": github_plan,
        "publish_preflight": preflight,
        "pipeline_contract": pipeline,
        "stack_engine_contract": stack_engine,
        "resident_winsorized_benchmark_audit": winsorized_audit,
        "resident_winsorized_sweep_audit": winsorized_sweep_audit,
        "release_decision": decision,
        "checks": checks,
    }


def write_phase2_status_markdown(path: str | Path, payload: dict[str, Any]) -> None:
    checkpoint = payload.get("latest_checkpoint") or {}
    acceptance = payload.get("acceptance_audit") or {}
    default_route_acceptance = payload.get("default_route_acceptance") or {}
    doctor = payload.get("doctor") or {}
    release = payload.get("release_manifest") or {}
    github_plan = payload.get("github_release_plan") or {}
    preflight = payload.get("publish_preflight") or {}
    pipeline = payload.get("pipeline_contract") or {}
    stack_engine = payload.get("stack_engine_contract") or {}
    winsorized_audit = payload.get("resident_winsorized_benchmark_audit") or {}
    winsorized_sweep_audit = payload.get("resident_winsorized_sweep_audit") or {}
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
    if default_route_acceptance:
        contract = default_route_acceptance.get("benchmark_contract") or {}
        lines.extend(
            [
                "",
                "## Default Route Acceptance",
                "",
                f"- Status: {default_route_acceptance.get('status')}",
                f"- Passed: {default_route_acceptance.get('passed')}",
                f"- Route contract passed: {default_route_acceptance.get('route_contract_passed')}",
                f"- Contract: {contract.get('name')}",
                f"- Speedup vs reference: {default_route_acceptance.get('speedup_vs_reference')}",
                f"- Active frames: {default_route_acceptance.get('active_frames')}",
                f"- Route check count: {default_route_acceptance.get('route_check_count')}",
                f"- Route failed checks: {default_route_acceptance.get('route_failed_checks')}",
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
    if preflight:
        lines.extend(
            [
                "",
                "## Windows Publish Preflight",
                "",
                f"- Preflight status: {preflight.get('status')}",
                f"- Passed: {preflight.get('passed')}",
                f"- Recommendation: {preflight.get('recommendation')}",
                f"- Release tag: {preflight.get('release_tag')}",
                f"- Assets/packages: {preflight.get('asset_count')}/{preflight.get('package_count')}",
                f"- Primary package: {preflight.get('primary_package')}",
                f"- Try order: {preflight.get('ordered_try_list')}",
                f"- Default promotion: {preflight.get('default_promotion_status')}",
                f"- Default route checks: {preflight.get('default_route_check_count')}",
                (
                    "- Default route speedup vs reference: "
                    f"{preflight.get('default_route_speedup_vs_reference')}"
                ),
                (
                    "- Rejection sample accounting statuses: "
                    f"phase2={preflight.get('github_plan_phase2_rejection_sample_accounting_status')}, "
                    f"plan-matrix={preflight.get('github_plan_matrix_rejection_sample_accounting_status')}, "
                    f"matrix={preflight.get('matrix_rejection_sample_accounting_status')}, "
                    "default-promotion="
                    f"{preflight.get('default_promotion_rejection_sample_accounting_status')}"
                ),
                (
                    "- Rejection sample accounting checks: "
                    f"phase2={preflight.get('github_plan_phase2_rejection_sample_accounting_passed')}, "
                    f"plan-matrix={preflight.get('github_plan_matrix_rejection_sample_accounting_passed')}, "
                    f"matrix={preflight.get('matrix_rejection_sample_accounting_passed')}, "
                    "default-promotion="
                    f"{preflight.get('default_promotion_rejection_sample_accounting_passed')}, "
                    "matrix-match="
                    f"{preflight.get('github_plan_matrix_rejection_accounting_matches_matrix')}"
                ),
                (
                    "- Sample accounting closure statuses: "
                    f"phase2={preflight.get('github_plan_phase2_sample_accounting_closure_status')}, "
                    f"plan-matrix={preflight.get('github_plan_matrix_sample_accounting_closure_status')}, "
                    f"matrix={preflight.get('matrix_sample_accounting_closure_status')}, "
                    "default-promotion="
                    f"{preflight.get('default_promotion_sample_accounting_closure_status')}"
                ),
                (
                    "- Sample accounting closure checks: "
                    f"phase2={preflight.get('github_plan_phase2_sample_accounting_closure_passed')}, "
                    f"plan-matrix={preflight.get('github_plan_matrix_sample_accounting_closure_passed')}, "
                    f"matrix={preflight.get('matrix_sample_accounting_closure_passed')}, "
                    "default-promotion="
                    f"{preflight.get('default_promotion_sample_accounting_closure_passed')}, "
                    "matrix-match="
                    f"{preflight.get('github_plan_matrix_sample_closure_matches_matrix')}"
                ),
                (
                    "- StackEngine default contract statuses: "
                    f"phase2={preflight.get('github_plan_phase2_stack_engine_contract_status')}, "
                    f"plan-matrix={preflight.get('github_plan_matrix_stack_engine_contract_status')}, "
                    f"matrix={preflight.get('matrix_stack_engine_contract_status')}, "
                    "default-promotion="
                    f"{preflight.get('default_promotion_stack_engine_contract_status')}"
                ),
                (
                    "- StackEngine default contract checks: "
                    "phase2="
                    f"{preflight.get('github_plan_phase2_stack_engine_default_contract_ready')}, "
                    "plan-matrix="
                    f"{preflight.get('github_plan_matrix_stack_engine_contract_ready')}, "
                    "agreement="
                    f"{preflight.get('github_plan_stack_engine_contract_agreement_passed')}, "
                    f"matrix={preflight.get('matrix_stack_engine_contract_ready')}, "
                    "default-promotion="
                    f"{preflight.get('default_promotion_stack_engine_contract_ready')}, "
                    "plan-matrix-match="
                    f"{preflight.get('github_plan_matrix_stack_engine_contract_matches_matrix')}, "
                    "default-promotion-match="
                    f"{preflight.get('matrix_stack_engine_contract_matches_default_promotion')}"
                ),
                (
                    "- StackEngine default gaps: "
                    f"matrix={preflight.get('matrix_stack_engine_contract_default_gap_count')}, "
                    "default-promotion="
                    f"{preflight.get('default_promotion_stack_engine_contract_default_gap_count')}"
                ),
                (
                    "- Resident winsorized sweep statuses: "
                    f"matrix={preflight.get('matrix_resident_winsorized_sweep_status')}, "
                    "default-promotion="
                    f"{preflight.get('default_promotion_resident_winsorized_sweep_status')}"
                ),
                (
                    "- Resident winsorized sweep required frame: "
                    f"matrix={preflight.get('matrix_resident_winsorized_sweep_required_frame_count')}/"
                    f"{preflight.get('matrix_resident_winsorized_sweep_required_frame_count_passed')}, "
                    "default-promotion="
                    f"{preflight.get('default_promotion_resident_winsorized_sweep_required_frame_count')}/"
                    f"{preflight.get('default_promotion_resident_winsorized_sweep_required_frame_count_passed')}"
                ),
                (
                    "- Resident winsorized sweep checks: "
                    f"matrix-count={preflight.get('matrix_resident_winsorized_sweep_check_count')}, "
                    "default-promotion-count="
                    f"{preflight.get('default_promotion_resident_winsorized_sweep_check_count')}, "
                    f"matrix-audit={preflight.get('matrix_resident_winsorized_sweep_audit_passed')}, "
                    "matrix-frame="
                    f"{preflight.get('matrix_resident_winsorized_required_frame_passed')}, "
                    "matrix-count-check="
                    f"{preflight.get('matrix_resident_winsorized_sweep_check_count_passed')}, "
                    "default-promotion-audit="
                    f"{preflight.get('default_promotion_resident_winsorized_sweep_audit_passed')}, "
                    "default-promotion-frame="
                    f"{preflight.get('default_promotion_resident_winsorized_required_frame_passed')}, "
                    "default-promotion-match="
                    f"{preflight.get('default_promotion_resident_winsorized_sweep_matches_matrix')}"
                ),
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
                (
                    "- Rejection sample counts match maps: "
                    f"{pipeline.get('integration_rejection_sample_counts_match_maps')}"
                ),
                (
                    "- Rejection sample accounting: "
                    f"{pipeline.get('rejection_sample_accounting_status')} "
                    f"failed={pipeline.get('rejection_sample_accounting_failed_count')}"
                ),
                (
                    "- Sample accounting closure: "
                    f"{pipeline.get('sample_accounting_closure_status')} "
                    f"present={pipeline.get('sample_accounting_closure_present_count')} "
                    f"failed={pipeline.get('sample_accounting_closure_failed_count')}"
                ),
            ]
        )
        accounting = pipeline.get("rejection_sample_accounting")
        if isinstance(accounting, dict):
            for row in accounting.get("failed_items") or []:
                if not isinstance(row, dict):
                    continue
                source_counts = ", ".join(
                    f"{source.get('name')}={source.get('count')}"
                    for source in row.get("source_counts") or []
                    if isinstance(source, dict)
                )
                failed_matches = "; ".join(
                    (
                        f"{match.get('source')}: actual={match.get('actual')} "
                        f"summary={match.get('summary')} delta={match.get('delta')}"
                    )
                    for match in row.get("failed_matches") or []
                    if isinstance(match, dict)
                )
                lines.append(
                    "- Rejection sample mismatch "
                    f"{row.get('item')}: map_rejected_sample_sum="
                    f"{row.get('map_rejected_sample_sum')} source_counts=[{source_counts}] "
                    f"failed_matches=[{failed_matches}]"
                )
        sample_closure = pipeline.get("sample_accounting_closure")
        if isinstance(sample_closure, dict):
            for row in sample_closure.get("failed_items") or []:
                if not isinstance(row, dict):
                    continue
                lines.append(
                    "- Sample closure mismatch "
                    f"{row.get('item')}: status={row.get('status')} "
                    "input_valid_samples_before_rejection="
                    f"{row.get('input_valid_samples_before_rejection')} "
                    "valid_samples_after_rejection="
                    f"{row.get('valid_samples_after_rejection')} "
                    f"rejected_samples={row.get('rejected_samples')} "
                    f"valid_rejection_match={row.get('valid_rejection_match')}"
                )
    if stack_engine:
        lines.extend(
            [
                "",
                "## StackEngine Default Contract",
                "",
                f"- Status: {stack_engine.get('status')}",
                f"- Passed: {stack_engine.get('passed')}",
                f"- Scope: {stack_engine.get('scope')}",
                (
                    "- Expected integration engine: "
                    f"{stack_engine.get('expected_integration_engine')}"
                ),
                (
                    "- Adoption recommendation: "
                    f"{stack_engine.get('adoption_recommendation')}"
                ),
                (
                    "- Adoption surfaces: "
                    f"{stack_engine.get('adoption_surface_count')} "
                    f"ready={stack_engine.get('adoption_contract_ready_count')}"
                ),
                (
                    "- StackEngine/resident surfaces: "
                    f"{stack_engine.get('adoption_stack_engine_surface_count')}/"
                    f"{stack_engine.get('adoption_cuda_resident_surface_count')}"
                ),
                (
                    "- Phase 2 default gaps: "
                    f"{stack_engine.get('adoption_phase2_stack_engine_default_gap_count')}"
                ),
                (
                    "- Default promotion: "
                    f"{stack_engine.get('default_promotion_status')} "
                    f"ready={stack_engine.get('default_promotion_ready')} "
                    f"blockers={stack_engine.get('default_promotion_blocker_count')}"
                ),
            ]
        )
        for blocker in stack_engine.get("default_promotion_blockers") or []:
            if not isinstance(blocker, dict):
                continue
            lines.append(
                f"- StackEngine default blocker {blocker.get('name')}: {blocker}"
            )
    if winsorized_audit:
        lines.extend(
            [
                "",
                "## Resident Winsorized Benchmark Audit",
                "",
                f"- Status: {winsorized_audit.get('status')}",
                f"- Passed: {winsorized_audit.get('passed')}",
                f"- Contract: {winsorized_audit.get('contract_name')}",
                f"- Benchmark: {winsorized_audit.get('benchmark_path')}",
                f"- Check count: {winsorized_audit.get('check_count')}",
                f"- Failed checks: {winsorized_audit.get('failed_checks')}",
                f"- Frame count: {winsorized_audit.get('frame_count')}",
                f"- Shape: {winsorized_audit.get('shape')}",
                f"- Hardened master RMS: {winsorized_audit.get('hardened_master_rms')}",
                (
                    "- Hardened master max abs: "
                    f"{winsorized_audit.get('hardened_master_max_abs')}"
                ),
                (
                    "- Fast approximation master RMS: "
                    f"{winsorized_audit.get('fast_approx_master_rms')}"
                ),
                f"- CUDA hardened seconds: {winsorized_audit.get('cuda_hardened_s')}",
            ]
        )
    if winsorized_sweep_audit:
        lines.extend(
            [
                "",
                "## Resident Winsorized Sweep Audit",
                "",
                f"- Status: {winsorized_sweep_audit.get('status')}",
                f"- Passed: {winsorized_sweep_audit.get('passed')}",
                f"- Contract: {winsorized_sweep_audit.get('contract_name')}",
                f"- Sweep: {winsorized_sweep_audit.get('sweep_path')}",
                f"- Check count: {winsorized_sweep_audit.get('check_count')}",
                f"- Failed checks: {winsorized_sweep_audit.get('failed_checks')}",
                f"- Frame counts: {winsorized_sweep_audit.get('frame_counts')}",
                f"- Run count: {winsorized_sweep_audit.get('run_count')}",
                f"- Required frame count: {winsorized_sweep_audit.get('required_frame_count')}",
                (
                    "- Required frame count passed: "
                    f"{winsorized_sweep_audit.get('required_frame_count_passed')}"
                ),
                (
                    "- Required frame master RMS: "
                    f"{winsorized_sweep_audit.get('required_frame_master_rms')}"
                ),
                (
                    "- Required frame master max abs: "
                    f"{winsorized_sweep_audit.get('required_frame_master_max_abs')}"
                ),
                (
                    "- Max hardened master RMS: "
                    f"{winsorized_sweep_audit.get('max_hardened_master_rms')}"
                ),
                (
                    "- Required frame hardened CUDA seconds: "
                    f"{winsorized_sweep_audit.get('required_frame_cuda_hardened_s')}"
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


def _int_status_value(payload: dict[str, Any], *keys: str) -> int | None:
    value = _status_value(payload, *keys)
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _int_or_zero(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


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


_PUBLISH_PREFLIGHT_REJECTION_CHECK_FIELDS = (
    "github_plan_phase2_rejection_sample_accounting_passed",
    "github_plan_matrix_rejection_sample_accounting_passed",
    "matrix_rejection_sample_accounting_passed",
    "default_promotion_rejection_sample_accounting_passed",
    "github_plan_matrix_rejection_accounting_matches_matrix",
)

_PUBLISH_PREFLIGHT_REJECTION_STATUS_FIELDS = (
    "github_plan_phase2_rejection_sample_accounting_status",
    "github_plan_matrix_rejection_sample_accounting_status",
    "matrix_rejection_sample_accounting_status",
    "default_promotion_rejection_sample_accounting_status",
)


_PUBLISH_PREFLIGHT_SAMPLE_CLOSURE_CHECK_FIELDS = (
    "github_plan_phase2_sample_accounting_closure_passed",
    "github_plan_matrix_sample_accounting_closure_passed",
    "matrix_sample_accounting_closure_passed",
    "default_promotion_sample_accounting_closure_passed",
    "github_plan_matrix_sample_closure_matches_matrix",
)

_PUBLISH_PREFLIGHT_SAMPLE_CLOSURE_STATUS_FIELDS = (
    "github_plan_phase2_sample_accounting_closure_status",
    "github_plan_matrix_sample_accounting_closure_status",
    "matrix_sample_accounting_closure_status",
    "default_promotion_sample_accounting_closure_status",
)


_PUBLISH_PREFLIGHT_STACK_ENGINE_CHECK_FIELDS = (
    "github_plan_phase2_stack_engine_default_contract_ready",
    "github_plan_matrix_stack_engine_contract_ready",
    "github_plan_stack_engine_contract_agreement_passed",
    "matrix_stack_engine_contract_ready",
    "default_promotion_stack_engine_contract_ready",
    "github_plan_matrix_stack_engine_contract_matches_matrix",
    "matrix_stack_engine_contract_matches_default_promotion",
)

_PUBLISH_PREFLIGHT_STACK_ENGINE_STATUS_FIELDS = (
    "github_plan_phase2_stack_engine_contract_status",
    "github_plan_matrix_stack_engine_contract_status",
    "matrix_stack_engine_contract_status",
    "default_promotion_stack_engine_contract_status",
)

_PUBLISH_PREFLIGHT_RESIDENT_WINSORIZED_CHECK_FIELDS = (
    "matrix_resident_winsorized_sweep_audit_passed",
    "matrix_resident_winsorized_required_frame_passed",
    "matrix_resident_winsorized_sweep_check_count_passed",
    "default_promotion_resident_winsorized_sweep_audit_passed",
    "default_promotion_resident_winsorized_required_frame_passed",
    "default_promotion_resident_winsorized_sweep_matches_matrix",
)

_PUBLISH_PREFLIGHT_RESIDENT_WINSORIZED_STATUS_FIELDS = (
    "matrix_resident_winsorized_sweep_status",
    "matrix_resident_winsorized_sweep_required_frame_count",
    "matrix_resident_winsorized_sweep_required_frame_count_passed",
    "matrix_resident_winsorized_sweep_check_count",
    "default_promotion_resident_winsorized_sweep_status",
    "default_promotion_resident_winsorized_sweep_required_frame_count",
    "default_promotion_resident_winsorized_sweep_required_frame_count_passed",
    "default_promotion_resident_winsorized_sweep_check_count",
)


def _publish_preflight_rejection_checks_passed(payload: dict[str, Any]) -> bool:
    return all(
        _status_value(payload, "publish_preflight", field) is True
        for field in _PUBLISH_PREFLIGHT_REJECTION_CHECK_FIELDS
    )


def _publish_preflight_rejection_statuses(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        field: _status_value(payload, "publish_preflight", field)
        for field in _PUBLISH_PREFLIGHT_REJECTION_STATUS_FIELDS
    }


def _publish_preflight_rejection_statuses_passed(payload: dict[str, Any]) -> bool:
    statuses = _publish_preflight_rejection_statuses(payload)
    return bool(statuses) and all(value == "passed" for value in statuses.values())


def _publish_preflight_sample_closure_checks_passed(payload: dict[str, Any]) -> bool:
    return all(
        _status_value(payload, "publish_preflight", field) is True
        for field in _PUBLISH_PREFLIGHT_SAMPLE_CLOSURE_CHECK_FIELDS
    )


def _publish_preflight_sample_closure_statuses(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        field: _status_value(payload, "publish_preflight", field)
        for field in _PUBLISH_PREFLIGHT_SAMPLE_CLOSURE_STATUS_FIELDS
    }


def _publish_preflight_sample_closure_statuses_passed(payload: dict[str, Any]) -> bool:
    statuses = _publish_preflight_sample_closure_statuses(payload)
    return bool(statuses) and all(value == "passed" for value in statuses.values())


def _publish_preflight_stack_engine_checks_passed(payload: dict[str, Any]) -> bool:
    return all(
        _status_value(payload, "publish_preflight", field) is True
        for field in _PUBLISH_PREFLIGHT_STACK_ENGINE_CHECK_FIELDS
    )


def _publish_preflight_stack_engine_statuses(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        field: _status_value(payload, "publish_preflight", field)
        for field in _PUBLISH_PREFLIGHT_STACK_ENGINE_STATUS_FIELDS
    }


def _publish_preflight_stack_engine_statuses_passed(payload: dict[str, Any]) -> bool:
    statuses = _publish_preflight_stack_engine_statuses(payload)
    return bool(statuses) and all(value == "passed" for value in statuses.values())


def _publish_preflight_resident_winsorized_checks_passed(payload: dict[str, Any]) -> bool:
    return all(
        _status_value(payload, "publish_preflight", field) is True
        for field in _PUBLISH_PREFLIGHT_RESIDENT_WINSORIZED_CHECK_FIELDS
    )


def _publish_preflight_resident_winsorized_statuses(
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        field: _status_value(payload, "publish_preflight", field)
        for field in _PUBLISH_PREFLIGHT_RESIDENT_WINSORIZED_STATUS_FIELDS
    }


def _publish_preflight_resident_winsorized_statuses_passed(
    payload: dict[str, Any],
) -> bool:
    statuses = _publish_preflight_resident_winsorized_statuses(payload)
    return (
        bool(statuses)
        and statuses.get("matrix_resident_winsorized_sweep_status") == "passed"
        and statuses.get("default_promotion_resident_winsorized_sweep_status")
        == "passed"
        and statuses.get(
            "matrix_resident_winsorized_sweep_required_frame_count_passed"
        )
        is True
        and statuses.get(
            "default_promotion_resident_winsorized_sweep_required_frame_count_passed"
        )
        is True
        and _int_or_zero(
            statuses.get("matrix_resident_winsorized_sweep_required_frame_count")
        )
        >= 200
        and _int_or_zero(
            statuses.get(
                "default_promotion_resident_winsorized_sweep_required_frame_count"
            )
        )
        >= 200
        and _int_or_zero(statuses.get("matrix_resident_winsorized_sweep_check_count"))
        > 0
        and _int_or_zero(
            statuses.get("default_promotion_resident_winsorized_sweep_check_count")
        )
        > 0
    )


def _stack_engine_status_summary(payload: dict[str, Any]) -> dict[str, Any]:
    contract = _status_value(payload, "stack_engine_contract")
    if not isinstance(contract, dict):
        return {
            "present": False,
            "ready": False,
            "status": None,
            "default_promotion_status": None,
            "gap_count": None,
            "recommendation": None,
        }
    gap_count = contract.get("default_promotion_phase2_stack_engine_default_gap_count")
    if gap_count is None:
        gap_count = contract.get("adoption_phase2_stack_engine_default_gap_count")
    return {
        "present": True,
        "ready": _stack_engine_default_contract_ready(contract),
        "status": contract.get("status"),
        "passed": contract.get("passed"),
        "scope": contract.get("scope"),
        "expected_integration_engine": contract.get("expected_integration_engine"),
        "default_promotion_ready": contract.get("default_promotion_ready"),
        "default_promotion_status": contract.get("default_promotion_status"),
        "gap_count": gap_count,
        "blocker_count": contract.get("default_promotion_blocker_count"),
        "recommendation": contract.get("adoption_recommendation"),
    }


def _stack_engine_gap_count(payload: dict[str, Any]) -> int | None:
    summary = _stack_engine_status_summary(payload)
    value = summary.get("gap_count")
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def build_phase2_status_compare(
    *,
    baseline_status: str | Path,
    candidate_status: str | Path,
) -> dict[str, Any]:
    baseline = _load_phase2_status(baseline_status)
    candidate = _load_phase2_status(candidate_status)
    baseline_gate = _status_value(baseline, "latest_checkpoint", "gate")
    candidate_gate = _status_value(candidate, "latest_checkpoint", "gate")
    baseline_stack_engine = _stack_engine_status_summary(baseline)
    candidate_stack_engine = _stack_engine_status_summary(candidate)
    baseline_stack_gap_count = _stack_engine_gap_count(baseline)
    candidate_stack_gap_count = _stack_engine_gap_count(candidate)
    baseline_sweep_check_count = _int_status_value(
        baseline,
        "resident_winsorized_sweep_audit",
        "check_count",
    )
    candidate_sweep_check_count = _int_status_value(
        candidate,
        "resident_winsorized_sweep_audit",
        "check_count",
    )
    baseline_sweep_required_frame_count = _int_status_value(
        baseline,
        "resident_winsorized_sweep_audit",
        "required_frame_count",
    )
    candidate_sweep_required_frame_count = _int_status_value(
        candidate,
        "resident_winsorized_sweep_audit",
        "required_frame_count",
    )
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
            "default_route_acceptance_passed_preserved",
            _status_value(baseline, "default_route_acceptance", "passed") is not True
            or _status_value(candidate, "default_route_acceptance", "passed") is True,
            baseline=_status_value(baseline, "default_route_acceptance", "passed"),
            candidate=_status_value(candidate, "default_route_acceptance", "passed"),
        ),
        _compare_check(
            "default_route_acceptance_route_contract_preserved",
            _status_value(baseline, "default_route_acceptance", "route_contract_passed")
            is not True
            or _status_value(candidate, "default_route_acceptance", "route_contract_passed")
            is True,
            baseline=_status_value(
                baseline,
                "default_route_acceptance",
                "route_contract_passed",
            ),
            candidate=_status_value(
                candidate,
                "default_route_acceptance",
                "route_contract_passed",
            ),
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
            "windows_publish_preflight_ready_preserved",
            _status_value(baseline, "publish_preflight", "status") != "publish_preflight_ready"
            or _status_value(candidate, "publish_preflight", "status") == "publish_preflight_ready",
            baseline=_status_value(baseline, "publish_preflight", "status"),
            candidate=_status_value(candidate, "publish_preflight", "status"),
        ),
        _compare_check(
            "windows_publish_preflight_rejection_sample_accounting_preserved",
            not _publish_preflight_rejection_checks_passed(baseline)
            or _publish_preflight_rejection_checks_passed(candidate),
            baseline={
                "checks_passed": _publish_preflight_rejection_checks_passed(baseline),
                "statuses": _publish_preflight_rejection_statuses(baseline),
            },
            candidate={
                "checks_passed": _publish_preflight_rejection_checks_passed(candidate),
                "statuses": _publish_preflight_rejection_statuses(candidate),
            },
        ),
        _compare_check(
            "windows_publish_preflight_rejection_sample_status_preserved",
            not _publish_preflight_rejection_statuses_passed(baseline)
            or _publish_preflight_rejection_statuses_passed(candidate),
            baseline=_publish_preflight_rejection_statuses(baseline),
            candidate=_publish_preflight_rejection_statuses(candidate),
        ),
        _compare_check(
            "windows_publish_preflight_sample_accounting_closure_preserved",
            not _publish_preflight_sample_closure_checks_passed(baseline)
            or _publish_preflight_sample_closure_checks_passed(candidate),
            baseline={
                "checks_passed": _publish_preflight_sample_closure_checks_passed(baseline),
                "statuses": _publish_preflight_sample_closure_statuses(baseline),
            },
            candidate={
                "checks_passed": _publish_preflight_sample_closure_checks_passed(
                    candidate
                ),
                "statuses": _publish_preflight_sample_closure_statuses(candidate),
            },
        ),
        _compare_check(
            "windows_publish_preflight_sample_closure_status_preserved",
            not _publish_preflight_sample_closure_statuses_passed(baseline)
            or _publish_preflight_sample_closure_statuses_passed(candidate),
            baseline=_publish_preflight_sample_closure_statuses(baseline),
            candidate=_publish_preflight_sample_closure_statuses(candidate),
        ),
        _compare_check(
            "windows_publish_preflight_stack_engine_contract_preserved",
            not _publish_preflight_stack_engine_checks_passed(baseline)
            or _publish_preflight_stack_engine_checks_passed(candidate),
            baseline={
                "checks_passed": _publish_preflight_stack_engine_checks_passed(
                    baseline
                ),
                "statuses": _publish_preflight_stack_engine_statuses(baseline),
            },
            candidate={
                "checks_passed": _publish_preflight_stack_engine_checks_passed(
                    candidate
                ),
                "statuses": _publish_preflight_stack_engine_statuses(candidate),
            },
        ),
        _compare_check(
            "windows_publish_preflight_stack_engine_status_preserved",
            not _publish_preflight_stack_engine_statuses_passed(baseline)
            or _publish_preflight_stack_engine_statuses_passed(candidate),
            baseline=_publish_preflight_stack_engine_statuses(baseline),
            candidate=_publish_preflight_stack_engine_statuses(candidate),
        ),
        _compare_check(
            "windows_publish_preflight_resident_winsorized_sweep_preserved",
            not _publish_preflight_resident_winsorized_checks_passed(baseline)
            or _publish_preflight_resident_winsorized_checks_passed(candidate),
            baseline={
                "checks_passed": _publish_preflight_resident_winsorized_checks_passed(
                    baseline
                ),
                "statuses": _publish_preflight_resident_winsorized_statuses(baseline),
            },
            candidate={
                "checks_passed": _publish_preflight_resident_winsorized_checks_passed(
                    candidate
                ),
                "statuses": _publish_preflight_resident_winsorized_statuses(candidate),
            },
        ),
        _compare_check(
            "windows_publish_preflight_resident_winsorized_status_preserved",
            not _publish_preflight_resident_winsorized_statuses_passed(baseline)
            or _publish_preflight_resident_winsorized_statuses_passed(candidate),
            baseline=_publish_preflight_resident_winsorized_statuses(baseline),
            candidate=_publish_preflight_resident_winsorized_statuses(candidate),
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
            "pipeline_rejection_sample_accounting_check_preserved",
            _status_value(
                baseline,
                "pipeline_contract",
                "rejection_sample_accounting",
                "check_present",
            )
            is not True
            or _status_value(
                candidate,
                "pipeline_contract",
                "rejection_sample_accounting",
                "check_present",
            )
            is True,
            baseline=_status_value(
                baseline,
                "pipeline_contract",
                "rejection_sample_accounting",
                "check_present",
            ),
            candidate=_status_value(
                candidate,
                "pipeline_contract",
                "rejection_sample_accounting",
                "check_present",
            ),
        ),
        _compare_check(
            "pipeline_rejection_sample_accounting_passed_preserved",
            _status_value(
                baseline,
                "pipeline_contract",
                "rejection_sample_accounting",
                "status",
            )
            != "passed"
            or _status_value(
                candidate,
                "pipeline_contract",
                "rejection_sample_accounting",
                "status",
            )
            == "passed",
            baseline=_status_value(
                baseline,
                "pipeline_contract",
                "rejection_sample_accounting",
                "status",
            ),
            candidate=_status_value(
                candidate,
                "pipeline_contract",
                "rejection_sample_accounting",
                "status",
            ),
        ),
        _compare_check(
            "pipeline_sample_accounting_closure_check_preserved",
            _status_value(
                baseline,
                "pipeline_contract",
                "sample_accounting_closure",
                "check_present",
            )
            is not True
            or _status_value(
                candidate,
                "pipeline_contract",
                "sample_accounting_closure",
                "check_present",
            )
            is True,
            baseline=_status_value(
                baseline,
                "pipeline_contract",
                "sample_accounting_closure",
                "check_present",
            ),
            candidate=_status_value(
                candidate,
                "pipeline_contract",
                "sample_accounting_closure",
                "check_present",
            ),
        ),
        _compare_check(
            "pipeline_sample_accounting_closure_passed_preserved",
            _status_value(
                baseline,
                "pipeline_contract",
                "sample_accounting_closure",
                "status",
            )
            != "passed"
            or _status_value(
                candidate,
                "pipeline_contract",
                "sample_accounting_closure",
                "status",
            )
            == "passed",
            baseline=_status_value(
                baseline,
                "pipeline_contract",
                "sample_accounting_closure",
                "status",
            ),
            candidate=_status_value(
                candidate,
                "pipeline_contract",
                "sample_accounting_closure",
                "status",
            ),
        ),
        _compare_check(
            "resident_winsorized_sweep_audit_passed_preserved",
            _status_value(baseline, "resident_winsorized_sweep_audit", "passed")
            is not True
            or _status_value(candidate, "resident_winsorized_sweep_audit", "passed")
            is True,
            baseline=_status_value(baseline, "resident_winsorized_sweep_audit", "passed"),
            candidate=_status_value(candidate, "resident_winsorized_sweep_audit", "passed"),
        ),
        _compare_check(
            "resident_winsorized_sweep_required_frame_preserved",
            _status_value(
                baseline,
                "resident_winsorized_sweep_audit",
                "required_frame_count_passed",
            )
            is not True
            or _status_value(
                candidate,
                "resident_winsorized_sweep_audit",
                "required_frame_count_passed",
            )
            is True,
            baseline={
                "required_frame_count": baseline_sweep_required_frame_count,
                "required_frame_count_passed": _status_value(
                    baseline,
                    "resident_winsorized_sweep_audit",
                    "required_frame_count_passed",
                ),
            },
            candidate={
                "required_frame_count": candidate_sweep_required_frame_count,
                "required_frame_count_passed": _status_value(
                    candidate,
                    "resident_winsorized_sweep_audit",
                    "required_frame_count_passed",
                ),
            },
        ),
        _compare_check(
            "resident_winsorized_sweep_check_count_not_decreased",
            baseline_sweep_check_count is None
            or (
                candidate_sweep_check_count is not None
                and candidate_sweep_check_count >= baseline_sweep_check_count
            ),
            baseline=baseline_sweep_check_count,
            candidate=candidate_sweep_check_count,
        ),
        _compare_check(
            "stack_engine_default_contract_ready_preserved",
            not baseline_stack_engine.get("ready") or candidate_stack_engine.get("ready") is True,
            baseline=baseline_stack_engine,
            candidate=candidate_stack_engine,
        ),
        _compare_check(
            "stack_engine_default_gap_count_not_increased",
            baseline_stack_gap_count is None
            or (
                candidate_stack_gap_count is not None
                and candidate_stack_gap_count <= baseline_stack_gap_count
            ),
            baseline=baseline_stack_gap_count,
            candidate=candidate_stack_gap_count,
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
            "default_route_acceptance_status": _status_value(
                baseline,
                "default_route_acceptance",
                "status",
            ),
            "default_route_acceptance_passed": _status_value(
                baseline,
                "default_route_acceptance",
                "passed",
            ),
            "cuda_available": _status_value(baseline, "doctor", "cuda_available"),
            "release_manifest_status": _status_value(baseline, "release_manifest", "status"),
            "github_release_plan_status": _status_value(baseline, "github_release_plan", "status"),
            "publish_preflight_status": _status_value(baseline, "publish_preflight", "status"),
            "publish_preflight_rejection_sample_accounting": (
                _publish_preflight_rejection_statuses(baseline)
            ),
            "publish_preflight_sample_accounting_closure": (
                _publish_preflight_sample_closure_statuses(baseline)
            ),
            "publish_preflight_stack_engine_contract": (
                _publish_preflight_stack_engine_statuses(baseline)
            ),
            "publish_preflight_resident_winsorized_sweep": (
                _publish_preflight_resident_winsorized_statuses(baseline)
            ),
            "pipeline_contract_status": _status_value(baseline, "pipeline_contract", "status"),
            "pipeline_contract_passed": _status_value(baseline, "pipeline_contract", "passed"),
            "pipeline_sample_accounting_closure": _status_value(
                baseline,
                "pipeline_contract",
                "sample_accounting_closure",
                "status",
            ),
            "resident_winsorized_sweep_audit": _status_value(
                baseline,
                "resident_winsorized_sweep_audit",
            ),
            "stack_engine_default_contract": baseline_stack_engine,
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
            "default_route_acceptance_status": _status_value(
                candidate,
                "default_route_acceptance",
                "status",
            ),
            "default_route_acceptance_passed": _status_value(
                candidate,
                "default_route_acceptance",
                "passed",
            ),
            "cuda_available": _status_value(candidate, "doctor", "cuda_available"),
            "release_manifest_status": _status_value(candidate, "release_manifest", "status"),
            "github_release_plan_status": _status_value(candidate, "github_release_plan", "status"),
            "publish_preflight_status": _status_value(candidate, "publish_preflight", "status"),
            "publish_preflight_rejection_sample_accounting": (
                _publish_preflight_rejection_statuses(candidate)
            ),
            "publish_preflight_sample_accounting_closure": (
                _publish_preflight_sample_closure_statuses(candidate)
            ),
            "publish_preflight_stack_engine_contract": (
                _publish_preflight_stack_engine_statuses(candidate)
            ),
            "publish_preflight_resident_winsorized_sweep": (
                _publish_preflight_resident_winsorized_statuses(candidate)
            ),
            "pipeline_contract_status": _status_value(candidate, "pipeline_contract", "status"),
            "pipeline_contract_passed": _status_value(candidate, "pipeline_contract", "passed"),
            "pipeline_sample_accounting_closure": _status_value(
                candidate,
                "pipeline_contract",
                "sample_accounting_closure",
                "status",
            ),
            "resident_winsorized_sweep_audit": _status_value(
                candidate,
                "resident_winsorized_sweep_audit",
            ),
            "stack_engine_default_contract": candidate_stack_engine,
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
