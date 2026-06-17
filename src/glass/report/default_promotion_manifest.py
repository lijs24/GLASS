from __future__ import annotations

from pathlib import Path
from typing import Any

from glass.io.json_io import read_json, write_json
from glass.models import now_iso


def _read_json_object(path: str | Path) -> dict[str, Any]:
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"JSON artifact must be an object: {path}")
    return payload


def _read_json_object_optional(path: str | Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    return _read_json_object(path)


def _check(name: str, passed: bool, evidence: dict[str, Any], note: str = "") -> dict[str, Any]:
    return {
        "name": name,
        "passed": bool(passed),
        "evidence": evidence,
        "note": note,
    }


def _number(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_value(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _status_value(payload: dict[str, Any], *keys: str) -> Any:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _artifact_type(payload: dict[str, Any]) -> str | None:
    value = payload.get("artifact_type")
    return None if value is None else str(value)


def _same_artifact_name(left: str | Path, right: Any) -> bool:
    if right is None:
        return False
    return Path(str(left)).name == Path(str(right)).name


def _runtime_repeat_summary(decision: dict[str, Any]) -> dict[str, Any]:
    runtime = decision.get("runtime_repeat") if isinstance(decision.get("runtime_repeat"), dict) else {}
    run_count = _int_value(runtime.get("considered_run_count"))
    if run_count is None:
        run_count = _int_value(runtime.get("run_count"))
    return {
        "present": runtime.get("present"),
        "run_count": _int_value(runtime.get("run_count")),
        "considered_run_count": run_count,
        "required_min_runtime_runs": _int_value(runtime.get("required_min_runtime_runs")),
        "best_label": runtime.get("best_label"),
        "best_elapsed_s": _number(runtime.get("best_elapsed_s")),
        "slowest_elapsed_s": _number(runtime.get("slowest_elapsed_s")),
        "elapsed_ratio_vs_best": _number(runtime.get("elapsed_ratio_vs_best")),
        "max_elapsed_ratio_vs_best": _number(runtime.get("max_elapsed_ratio_vs_best")),
        "recommendation": runtime.get("recommendation"),
    }


def _doctor_summary(doctor: dict[str, Any]) -> dict[str, Any]:
    if not doctor:
        return {"present": False}
    cuda = doctor.get("cuda") if isinstance(doctor.get("cuda"), dict) else {}
    packages = (
        doctor.get("windows_cuda_packages")
        if isinstance(doctor.get("windows_cuda_packages"), dict)
        else {}
    )
    devices = cuda.get("devices") if isinstance(cuda.get("devices"), list) else []
    first_device = devices[0] if devices and isinstance(devices[0], dict) else {}
    ordered_try_list = [str(item) for item in packages.get("ordered_try_list") or []]
    package_rows = [
        {
            "label": item.get("label"),
            "toolkit": item.get("toolkit"),
            "compatible": item.get("compatible"),
            "match": item.get("match"),
            "architectures": item.get("architectures"),
        }
        for item in packages.get("packages") or []
        if isinstance(item, dict)
    ]
    return {
        "present": True,
        "schema_version": doctor.get("schema_version"),
        "recommendation": doctor.get("recommendation"),
        "cuda_available": cuda.get("cuda_available"),
        "wrapper_importable": cuda.get("wrapper_importable"),
        "native_extension_loaded": cuda.get("native_extension_loaded"),
        "probe_skipped": cuda.get("probe_skipped"),
        "device": first_device,
        "primary_package": packages.get("primary"),
        "ordered_try_list": ordered_try_list,
        "package_rows": package_rows,
        "guidance": packages.get("guidance"),
    }


def _pipeline_summary(phase2: dict[str, Any]) -> dict[str, Any]:
    pipeline = (
        phase2.get("pipeline_contract") if isinstance(phase2.get("pipeline_contract"), dict) else {}
    )
    return {
        "present": bool(pipeline),
        "status": pipeline.get("status"),
        "passed": pipeline.get("passed"),
        "check_count": pipeline.get("check_count"),
        "failed_check_count": pipeline.get("failed_check_count"),
        "failed_checks": pipeline.get("failed_checks") or [],
        "integration_output_count": pipeline.get("integration_output_count"),
        "integration_map_count": pipeline.get("integration_map_count"),
        "integration_dq_contract": pipeline.get("integration_dq_contract"),
        "integration_stack_result_contract": pipeline.get("integration_stack_result_contract"),
        "integration_resident_result_contract": pipeline.get("integration_resident_result_contract"),
        "integration_dq_map_pixels_match_summary": pipeline.get(
            "integration_dq_map_pixels_match_summary"
        ),
        "integration_coverage_map_pixels_match_dq": pipeline.get(
            "integration_coverage_map_pixels_match_dq"
        ),
        "integration_rejection_map_pixels_match_dq": pipeline.get(
            "integration_rejection_map_pixels_match_dq"
        ),
        "integration_rejection_sample_counts_match_maps": pipeline.get(
            "integration_rejection_sample_counts_match_maps"
        ),
        "integration_sample_accounting_closure": pipeline.get(
            "integration_sample_accounting_closure"
        ),
        "rejection_sample_accounting": pipeline.get("rejection_sample_accounting")
        if isinstance(pipeline.get("rejection_sample_accounting"), dict)
        else {},
        "rejection_sample_accounting_status": pipeline.get("rejection_sample_accounting_status"),
        "rejection_sample_accounting_failed_count": pipeline.get(
            "rejection_sample_accounting_failed_count"
        ),
        "sample_accounting_closure": pipeline.get("sample_accounting_closure")
        if isinstance(pipeline.get("sample_accounting_closure"), dict)
        else {},
        "sample_accounting_closure_status": pipeline.get("sample_accounting_closure_status"),
        "sample_accounting_closure_present_count": pipeline.get(
            "sample_accounting_closure_present_count"
        ),
        "sample_accounting_closure_failed_count": pipeline.get(
            "sample_accounting_closure_failed_count"
        ),
        "pixel_verification_enabled": pipeline.get("pixel_verification_enabled"),
        "pixel_verification_tile_size": pipeline.get("pixel_verification_tile_size"),
        "resident_native_calibration_artifact": pipeline.get("resident_native_calibration_artifact"),
        "resident_calibrated_light_count": pipeline.get("resident_calibrated_light_count"),
        "calibrated_light_count": pipeline.get("calibrated_light_count"),
    }


def _default_route_acceptance_summary(phase2: dict[str, Any]) -> dict[str, Any]:
    default_route = (
        phase2.get("default_route_acceptance")
        if isinstance(phase2.get("default_route_acceptance"), dict)
        else {}
    )
    return {
        "present": bool(default_route),
        "path": default_route.get("path"),
        "status": default_route.get("status"),
        "passed": default_route.get("passed"),
        "acceptance_passed": default_route.get("acceptance_passed"),
        "benchmark_contract": default_route.get("benchmark_contract"),
        "speedup_vs_reference": _number(default_route.get("speedup_vs_reference")),
        "active_frames": _int_value(default_route.get("active_frames")),
        "route_contract_passed": default_route.get("route_contract_passed"),
        "route_check_count": _int_value(default_route.get("route_check_count")),
        "route_failed_checks": default_route.get("route_failed_checks") or [],
    }


def build_default_promotion_manifest(
    *,
    release_decision_json: str | Path,
    phase2_status_json: str | Path,
    doctor_json: str | Path | None = None,
    default_memory_mode: str = "resident",
    fallback_memory_mode: str = "tile",
    default_runtime_preset: str = "throughput-v1",
    integration_engine: str = "cuda_resident_stack",
    min_runtime_runs: int = 2,
    max_runtime_ratio: float = 1.25,
    min_resident_lights: int = 200,
    require_doctor: bool = False,
) -> dict[str, Any]:
    decision = _read_json_object(release_decision_json)
    phase2 = _read_json_object(phase2_status_json)
    doctor = _read_json_object_optional(doctor_json)
    runtime = _runtime_repeat_summary(decision)
    pipeline = _pipeline_summary(phase2)
    default_route = _default_route_acceptance_summary(phase2)
    doctor_info = _doctor_summary(doctor)
    phase2_decision = (
        phase2.get("release_decision") if isinstance(phase2.get("release_decision"), dict) else {}
    )
    latest_checkpoint = (
        phase2.get("latest_checkpoint")
        if isinstance(phase2.get("latest_checkpoint"), dict)
        else {}
    )
    ordered_try_list = doctor_info.get("ordered_try_list") or []
    runtime_ratio = runtime.get("elapsed_ratio_vs_best")
    considered_runs = runtime.get("considered_run_count")
    resident_light_count = _int_value(pipeline.get("resident_calibrated_light_count"))
    if resident_light_count is None:
        resident_light_count = _int_value(pipeline.get("calibrated_light_count"))

    checks = [
        _check(
            "release_decision_artifact_type",
            _artifact_type(decision) == "release_promotion_decision",
            {"actual": _artifact_type(decision), "required": "release_promotion_decision"},
        ),
        _check(
            "phase2_status_artifact_type",
            _artifact_type(phase2) == "glass_phase2_status",
            {"actual": _artifact_type(phase2), "required": "glass_phase2_status"},
        ),
        _check(
            "phase2_status_green",
            phase2.get("status") == "green" and phase2.get("passed") is True,
            {"status": phase2.get("status"), "passed": phase2.get("passed")},
        ),
        _check(
            "latest_checkpoint_green",
            latest_checkpoint.get("green") is True,
            {
                "gate": latest_checkpoint.get("gate"),
                "status": latest_checkpoint.get("status"),
                "green": latest_checkpoint.get("green"),
            },
        ),
        _check(
            "release_decision_default_change_ready",
            decision.get("default_change_ready") is True,
            {"actual": decision.get("default_change_ready"), "status": decision.get("status")},
        ),
        _check(
            "release_decision_recommends_promotion",
            decision.get("recommendation") == "promote_default_candidate",
            {"actual": decision.get("recommendation"), "required": "promote_default_candidate"},
        ),
        _check(
            "phase2_embeds_same_release_decision",
            _same_artifact_name(release_decision_json, phase2_decision.get("path")),
            {
                "input": str(release_decision_json),
                "phase2_release_decision_path": phase2_decision.get("path"),
            },
        ),
        _check(
            "phase2_release_decision_default_change_ready",
            phase2_decision.get("default_change_ready") is True,
            {"actual": phase2_decision.get("default_change_ready")},
        ),
        _check(
            "phase2_release_decision_recommends_promotion",
            phase2_decision.get("recommendation") == "promote_default_candidate",
            {
                "actual": phase2_decision.get("recommendation"),
                "required": "promote_default_candidate",
            },
        ),
        _check(
            "default_route_acceptance_present",
            default_route.get("present") is True,
            {"path": default_route.get("path"), "status": default_route.get("status")},
        ),
        _check(
            "default_route_acceptance_passed",
            default_route.get("passed") is True,
            {
                "status": default_route.get("status"),
                "passed": default_route.get("passed"),
                "acceptance_passed": default_route.get("acceptance_passed"),
            },
        ),
        _check(
            "default_route_acceptance_route_contract_passed",
            default_route.get("route_contract_passed") is True,
            {
                "route_contract_passed": default_route.get("route_contract_passed"),
                "route_failed_checks": default_route.get("route_failed_checks"),
            },
        ),
        _check(
            "default_route_acceptance_route_check_count",
            (default_route.get("route_check_count") or 0) >= 4,
            {"actual": default_route.get("route_check_count"), "required_min": 4},
        ),
        _check(
            "runtime_repeat_present",
            runtime.get("present") is True,
            {"present": runtime.get("present"), "recommendation": runtime.get("recommendation")},
        ),
        _check(
            "runtime_repeat_count",
            considered_runs is not None and considered_runs >= int(min_runtime_runs),
            {"actual": considered_runs, "required_min": int(min_runtime_runs)},
        ),
        _check(
            "runtime_repeat_ratio_within_bound",
            runtime_ratio is not None and runtime_ratio <= float(max_runtime_ratio),
            {"actual": runtime_ratio, "required_max": float(max_runtime_ratio)},
        ),
        _check(
            "pipeline_contract_passed",
            pipeline.get("passed") is True and pipeline.get("status") == "passed",
            {"status": pipeline.get("status"), "passed": pipeline.get("passed")},
        ),
        _check(
            "pipeline_dq_contract_passed",
            pipeline.get("integration_dq_contract") is True,
            {"actual": pipeline.get("integration_dq_contract")},
        ),
        _check(
            "pipeline_stack_and_resident_result_contracts_passed",
            pipeline.get("integration_stack_result_contract") is True
            and pipeline.get("integration_resident_result_contract") is True,
            {
                "stack": pipeline.get("integration_stack_result_contract"),
                "resident": pipeline.get("integration_resident_result_contract"),
            },
        ),
        _check(
            "pipeline_pixel_verification_enabled",
            pipeline.get("pixel_verification_enabled") is True,
            {
                "enabled": pipeline.get("pixel_verification_enabled"),
                "tile_size": pipeline.get("pixel_verification_tile_size"),
            },
        ),
        _check(
            "pipeline_pixel_maps_match_dq",
            pipeline.get("integration_dq_map_pixels_match_summary") is True
            and pipeline.get("integration_coverage_map_pixels_match_dq") is True
            and pipeline.get("integration_rejection_map_pixels_match_dq") is True,
            {
                "dq": pipeline.get("integration_dq_map_pixels_match_summary"),
                "coverage": pipeline.get("integration_coverage_map_pixels_match_dq"),
                "rejection": pipeline.get("integration_rejection_map_pixels_match_dq"),
            },
        ),
        _check(
            "pipeline_rejection_sample_accounting_passed",
            pipeline.get("integration_rejection_sample_counts_match_maps") is True
            and pipeline.get("rejection_sample_accounting_status") == "passed",
            {
                "check": pipeline.get("integration_rejection_sample_counts_match_maps"),
                "status": pipeline.get("rejection_sample_accounting_status"),
                "failed_count": pipeline.get("rejection_sample_accounting_failed_count"),
                "failed_items": (pipeline.get("rejection_sample_accounting") or {}).get(
                    "failed_items"
                ),
            },
        ),
        _check(
            "pipeline_sample_accounting_closure_passed",
            pipeline.get("integration_sample_accounting_closure") is True
            and pipeline.get("sample_accounting_closure_status") == "passed",
            {
                "check": pipeline.get("integration_sample_accounting_closure"),
                "status": pipeline.get("sample_accounting_closure_status"),
                "present_count": pipeline.get("sample_accounting_closure_present_count"),
                "failed_count": pipeline.get("sample_accounting_closure_failed_count"),
                "failed_items": (pipeline.get("sample_accounting_closure") or {}).get(
                    "failed_items"
                ),
            },
        ),
        _check(
            "resident_calibration_artifact_present",
            pipeline.get("resident_native_calibration_artifact") is True,
            {"actual": pipeline.get("resident_native_calibration_artifact")},
        ),
        _check(
            "resident_light_count",
            resident_light_count is not None and resident_light_count >= int(min_resident_lights),
            {"actual": resident_light_count, "required_min": int(min_resident_lights)},
        ),
        _check(
            "default_memory_mode_candidate",
            default_memory_mode == "resident",
            {"actual": default_memory_mode, "required": "resident"},
        ),
        _check(
            "fallback_memory_mode_preserved",
            fallback_memory_mode == "tile",
            {"actual": fallback_memory_mode, "required": "tile"},
        ),
        _check(
            "default_runtime_preset_candidate",
            default_runtime_preset == "throughput-v1",
            {"actual": default_runtime_preset, "required": "throughput-v1"},
        ),
        _check(
            "integration_engine_candidate",
            integration_engine == "cuda_resident_stack",
            {"actual": integration_engine, "required": "cuda_resident_stack"},
        ),
        _check(
            "doctor_artifact_available",
            bool(doctor_info.get("present")) or not require_doctor,
            {"present": doctor_info.get("present"), "required": bool(require_doctor)},
        ),
    ]
    if doctor_info.get("present"):
        checks.extend(
            [
                _check(
                    "doctor_cuda_available",
                    doctor_info.get("cuda_available") is True,
                    {
                        "cuda_available": doctor_info.get("cuda_available"),
                        "native_extension_loaded": doctor_info.get("native_extension_loaded"),
                        "wrapper_importable": doctor_info.get("wrapper_importable"),
                    },
                ),
                _check(
                    "doctor_native_extension_loaded",
                    doctor_info.get("native_extension_loaded") is True,
                    {"actual": doctor_info.get("native_extension_loaded")},
                ),
                _check(
                    "windows_package_try_list_has_cpu_fallback",
                    "cpu" in ordered_try_list,
                    {"ordered_try_list": ordered_try_list},
                ),
                _check(
                    "windows_package_primary_present",
                    bool(doctor_info.get("primary_package")),
                    {"primary": doctor_info.get("primary_package")},
                ),
            ]
        )

    failed = [item for item in checks if not item.get("passed")]
    status = "default_promotion_ready" if not failed else "blocked"
    return {
        "schema_version": 1,
        "artifact_type": "default_promotion_manifest",
        "created_at": now_iso(),
        "status": status,
        "passed": not failed,
        "default_change_ready": not failed,
        "recommendation": "promote_resident_cuda_default" if not failed else "fix_default_blockers",
        "inputs": {
            "release_decision_json": str(release_decision_json),
            "phase2_status_json": str(phase2_status_json),
            "doctor_json": None if doctor_json is None else str(doctor_json),
        },
        "default_candidate": {
            "memory_mode": default_memory_mode,
            "fallback_memory_mode": fallback_memory_mode,
            "resident_runtime_preset": default_runtime_preset,
            "integration_engine": integration_engine,
            "cpu_only_install_preserved": True,
            "cuda_optional": True,
        },
        "release_decision": {
            "status": decision.get("status"),
            "passed": decision.get("passed"),
            "release_candidate_ready": decision.get("release_candidate_ready"),
            "default_change_ready": decision.get("default_change_ready"),
            "recommendation": decision.get("recommendation"),
            "speedup": decision.get("speedup"),
        },
        "phase2_status": {
            "status": phase2.get("status"),
            "passed": phase2.get("passed"),
            "latest_checkpoint": latest_checkpoint,
            "release_decision": phase2_decision,
        },
        "runtime_repeat": runtime,
        "default_route_acceptance": default_route,
        "pipeline_contract": pipeline,
        "doctor": doctor_info,
        "checks": checks,
        "failed_checks": [str(item.get("name")) for item in failed],
        "limitations": [
            "This manifest proves readiness for a default promotion; it does not change CLI defaults.",
            "The resident CUDA default candidate still requires the tile and CPU fallback paths to remain available.",
            "Runtime evidence is bounded by the supplied repeat artifacts and the current storage/GPU state.",
        ],
    }


def _markdown(payload: dict[str, Any]) -> str:
    default_candidate = payload.get("default_candidate") or {}
    runtime = payload.get("runtime_repeat") or {}
    default_route = payload.get("default_route_acceptance") or {}
    pipeline = payload.get("pipeline_contract") or {}
    doctor = payload.get("doctor") or {}
    device = doctor.get("device") if isinstance(doctor, dict) else {}
    lines = [
        "# GLASS Default Promotion Manifest",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Recommendation: `{payload.get('recommendation')}`",
        f"- Passed: `{payload.get('passed')}`",
        f"- Default memory mode candidate: `{default_candidate.get('memory_mode')}`",
        f"- Fallback memory mode: `{default_candidate.get('fallback_memory_mode')}`",
        f"- Runtime preset: `{default_candidate.get('resident_runtime_preset')}`",
        f"- Integration engine: `{default_candidate.get('integration_engine')}`",
        "",
        "## Runtime Evidence",
        "",
        f"- Runs: `{runtime.get('considered_run_count')}`",
        f"- Best: `{runtime.get('best_label')}` `{runtime.get('best_elapsed_s')}` s",
        f"- Slowest: `{runtime.get('slowest_elapsed_s')}` s",
        f"- Slowest/best ratio: `{runtime.get('elapsed_ratio_vs_best')}`",
        "",
        "## Default Route Evidence",
        "",
        f"- Present: `{default_route.get('present')}`",
        f"- Status: `{default_route.get('status')}`",
        f"- Passed: `{default_route.get('passed')}`",
        f"- Route contract passed: `{default_route.get('route_contract_passed')}`",
        f"- Route check count: `{default_route.get('route_check_count')}`",
        f"- Route failed checks: `{default_route.get('route_failed_checks')}`",
        f"- Speedup vs reference: `{default_route.get('speedup_vs_reference')}`",
        f"- Rejection sample accounting: `{pipeline.get('rejection_sample_accounting_status')}`",
        f"- Sample accounting closure: `{pipeline.get('sample_accounting_closure_status')}`",
        "",
        "## Release Machine",
        "",
        f"- Doctor present: `{doctor.get('present')}`",
        f"- CUDA available: `{doctor.get('cuda_available')}`",
        f"- Native extension loaded: `{doctor.get('native_extension_loaded')}`",
        f"- GPU: `{device.get('name') if isinstance(device, dict) else None}`",
        f"- Primary package: `{doctor.get('primary_package')}`",
        f"- Try order: `{', '.join(doctor.get('ordered_try_list') or [])}`",
        "",
        "## Checks",
        "",
    ]
    for item in payload.get("checks") or []:
        marker = "PASS" if item.get("passed") else "FAIL"
        lines.append(f"- {marker}: `{item.get('name')}` - {item.get('evidence')}")
    lines.append("")
    return "\n".join(lines)


def write_default_promotion_manifest(
    out: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(out, payload)
    if markdown is not None:
        target = Path(markdown)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(_markdown(payload), encoding="utf-8")
