from __future__ import annotations

from pathlib import Path
from typing import Any

from glass.engine.resident_component_timing import (
    REQUIRED_RESIDENT_COMPONENT_TIMING_KEYS,
    build_resident_component_timing,
)
from glass.engine.resident_stage_ledger import build_resident_stage_ledger
from glass.io.json_io import read_json, write_json
from glass.models import now_iso
from glass.report.resident_active_coverage_contract import (
    build_resident_active_coverage_contract_state,
)


REQUIRED_CORE_ARTIFACTS = (
    "integration_results.json",
    "resident_artifacts.json",
    "frame_accounting.json",
    "calibration_artifacts.json",
    "registration_results.json",
    "local_norm_results.json",
    "resident_frame_masks.json",
    "resident_dq_lifecycle.json",
    "resident_source_dq_execution.json",
    "resident_dq_pixel_closure.json",
    "resident_master_cache.json",
    "resident_stage_ledger.json",
    "resident_component_timing.json",
    "resident_memory_lifecycle.json",
    "resident_registration_runtime_contract.json",
    "resident_result_contract.json",
    "pipeline_contract.json",
    "stack_engine_contract.json",
    "warp_quality_contract.json",
)

REQUIRED_OUTPUT_MAP_FIELDS = (
    "master_path",
    "weight_map_path",
    "coverage_map_path",
    "low_rejection_map_path",
    "high_rejection_map_path",
    "dq_map_path",
)


def _json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = read_json(path)
    return payload if isinstance(payload, dict) else {}


def _number(value: Any) -> float | None:
    try:
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None


def _int_or_none(value: Any) -> int | None:
    try:
        return None if value is None else int(value)
    except (TypeError, ValueError):
        return None


def _check(name: str, passed: bool, evidence: dict[str, Any], note: str = "") -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "evidence": evidence, "note": note}


def _first_resident_artifact(run: Path) -> dict[str, Any]:
    payload = _json_if_exists(run / "resident_artifacts.json")
    artifacts = payload.get("artifacts") if isinstance(payload.get("artifacts"), list) else []
    first = artifacts[0] if artifacts else {}
    return first if isinstance(first, dict) else {}


def _resolve_run_path(run: Path, value: Any) -> Path | None:
    if value in (None, ""):
        return None
    path = Path(str(value))
    return path if path.is_absolute() else run / path


def _artifact_passed(run: Path, name: str) -> dict[str, Any]:
    path = run / name
    payload = _json_if_exists(path)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    passed = payload.get("passed")
    if passed is None:
        passed = summary.get("passed")
    status = payload.get("status")
    if status is None:
        status = summary.get("status")
    return {
        "path": str(path),
        "exists": path.exists(),
        "status": status,
        "passed": passed,
        "artifact_type": payload.get("artifact_type") or payload.get("audit_type") or payload.get("artifact"),
    }


def _registration_runtime_state(run: Path) -> dict[str, Any]:
    name = "resident_registration_runtime_contract.json"
    path = run / name
    payload = _json_if_exists(path)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    return {
        "path": str(path),
        "exists": path.exists(),
        "status": payload.get("status"),
        "passed": payload.get("passed"),
        "applicable": payload.get("applicable"),
        "artifact_type": payload.get("artifact_type"),
        "failed_checks": (
            list(payload.get("failed_checks")) if isinstance(payload.get("failed_checks"), list) else []
        ),
        "summary": summary,
    }


def _stage_elapsed(timing: dict[str, Any], stage: str) -> float | None:
    for item in timing.get("stages") or []:
        if isinstance(item, dict) and item.get("stage") == stage:
            return _number(item.get("elapsed_s"))
    return None


def _output_map_state(run: Path, artifact: dict[str, Any]) -> dict[str, Any]:
    entries: dict[str, dict[str, Any]] = {}
    for field in REQUIRED_OUTPUT_MAP_FIELDS:
        path = _resolve_run_path(run, artifact.get(field))
        entries[field] = {
            "path": None if path is None else str(path),
            "exists": bool(path and path.exists()),
        }
    missing = [field for field, record in entries.items() if not record["exists"]]
    return {
        "required_fields": list(REQUIRED_OUTPUT_MAP_FIELDS),
        "missing_fields": missing,
        "maps": entries,
    }


def _timing_components(run: Path, timing: dict[str, Any], artifact: dict[str, Any]) -> dict[str, Any]:
    timing_s = artifact.get("timing_s") if isinstance(artifact.get("timing_s"), dict) else {}
    component_path = run / "resident_component_timing.json"
    component_payload = _json_if_exists(component_path)
    if not component_payload:
        component_payload = build_resident_component_timing(
            run,
            timing=timing,
            resident_payload={"artifacts": [artifact]},
        )
    component_summary = (
        component_payload.get("summary")
        if isinstance(component_payload.get("summary"), dict)
        else {}
    )
    component_rows = (
        component_payload.get("components")
        if isinstance(component_payload.get("components"), list)
        else []
    )
    components_from_artifact = {
        str(row.get("source_key")): _number(row.get("elapsed_s"))
        for row in component_rows
        if isinstance(row, dict) and row.get("source_key") is not None
    }
    stages = {
        "resident_reference_scout": _stage_elapsed(timing, "resident_reference_scout"),
        "resident_reference_health": _stage_elapsed(timing, "resident_reference_health"),
        "resident_calibration_integration": _stage_elapsed(timing, "resident_calibration_integration"),
        "pipeline_contract": _stage_elapsed(timing, "pipeline_contract"),
        "stack_engine_contract": _stage_elapsed(timing, "stack_engine_contract"),
        "warp_quality_contract": _stage_elapsed(timing, "warp_quality_contract"),
    }
    components = {
        "light_read_upload_calibrate": components_from_artifact.get(
            "light_read_upload_calibrate",
            _number(timing_s.get("light_read_upload_calibrate")),
        ),
        "resident_registration_warp": components_from_artifact.get(
            "resident_registration_warp",
            _number(timing_s.get("resident_registration_warp")),
        ),
        "resident_local_normalization": components_from_artifact.get(
            "resident_local_normalization",
            _number(timing_s.get("resident_local_normalization")),
        ),
        "resident_integration": components_from_artifact.get(
            "resident_integration",
            _number(timing_s.get("resident_integration")),
        ),
        "output_write": components_from_artifact.get(
            "output_write",
            _number(timing_s.get("output_write")),
        ),
    }
    return {
        "total_elapsed_s": _number(timing.get("total_elapsed_s")),
        "stages": stages,
        "resident_components_s": components,
        "component_artifact": {
            "path": str(component_path),
            "exists": component_path.exists(),
            "passed": component_payload.get("passed"),
            "status": component_payload.get("status"),
            "required_component_keys": list(REQUIRED_RESIDENT_COMPONENT_TIMING_KEYS),
            "missing_required_components": component_summary.get("missing_required_components"),
            "present_component_count": component_summary.get("present_component_count"),
            "total_component_elapsed_s": _number(component_summary.get("total_component_elapsed_s")),
            "largest_component": component_summary.get("largest_component"),
        },
        "largest_stage": max(
            ((name, value) for name, value in stages.items() if value is not None),
            key=lambda item: item[1],
            default=(None, None),
        ),
        "largest_resident_component": max(
            ((name, value) for name, value in components.items() if value is not None),
            key=lambda item: item[1],
            default=(None, None),
        ),
    }


def _stage_ledger_state(run: Path) -> dict[str, Any]:
    computed = build_resident_stage_ledger(run)
    summary = computed.get("summary") if isinstance(computed.get("summary"), dict) else {}
    rows = computed.get("stages") if isinstance(computed.get("stages"), list) else []
    stage_status = {
        str(row.get("stage")): row.get("status")
        for row in rows
        if isinstance(row, dict) and row.get("stage") is not None
    }
    complete_stages = {stage for stage, status in stage_status.items() if status == "complete"}
    required_complete = {
        "resident_calibration",
        "resident_registration",
        "resident_local_normalization",
        "resident_integration",
    }
    unexpected_component_stages = [
        stage
        for stage in ("resident_light_calibration", "resident_calibration_contract")
        if stage in stage_status
    ]
    missing_required_complete = sorted(required_complete - complete_stages)
    passed = bool(
        computed.get("resident_run") is True
        and summary.get("can_noop_resume") is True
        and int(summary.get("missing_artifact_count") or 0) == 0
        and not missing_required_complete
        and not unexpected_component_stages
    )
    return {
        "path": str(run / "resident_stage_ledger.json"),
        "stored_exists": (run / "resident_stage_ledger.json").exists(),
        "resident_run": computed.get("resident_run"),
        "summary": {
            "complete_stage_count": summary.get("complete_stage_count"),
            "expected_artifact_count": summary.get("expected_artifact_count"),
            "missing_artifact_count": summary.get("missing_artifact_count"),
            "can_noop_resume": summary.get("can_noop_resume"),
            "integration_complete": summary.get("integration_complete"),
        },
        "stage_status": stage_status,
        "required_complete_stages": sorted(required_complete),
        "missing_required_complete_stages": missing_required_complete,
        "unexpected_component_stages": unexpected_component_stages,
        "passed": passed,
    }


def _resident_memory_lifecycle_state(run: Path, timing: dict[str, Any]) -> dict[str, Any]:
    path = run / "resident_memory_lifecycle.json"
    payload = _json_if_exists(path)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    timing_summary = (
        timing.get("resident_memory_lifecycle_summary")
        if isinstance(timing.get("resident_memory_lifecycle_summary"), dict)
        else {}
    )
    group_count = _int_or_none(summary.get("group_count"))
    failed_group_count = _int_or_none(summary.get("failed_group_count"))
    calibrated_bytes = _int_or_none(summary.get("max_estimated_calibrated_stack_bytes"))
    peak_bytes = _int_or_none(summary.get("max_estimated_peak_bytes"))
    timing_path = timing.get("resident_memory_lifecycle_path")
    passed = bool(
        path.exists()
        and payload.get("artifact_type") == "resident_memory_lifecycle"
        and payload.get("passed") is True
        and group_count is not None
        and group_count > 0
        and failed_group_count == 0
        and summary.get("raw_all_frames_resident") is False
        and summary.get("calibrated_stack_resident") is True
        and summary.get("registered_cache_materialized_on_disk") is False
        and calibrated_bytes is not None
        and calibrated_bytes > 0
        and peak_bytes is not None
        and peak_bytes >= calibrated_bytes
        and timing_path == "resident_memory_lifecycle.json"
        and timing_summary.get("calibrated_stack_resident") is True
    )
    return {
        "path": str(path),
        "exists": path.exists(),
        "artifact_type": payload.get("artifact_type"),
        "status": payload.get("status"),
        "payload_passed": payload.get("passed"),
        "summary": {
            "group_count": group_count,
            "failed_group_count": failed_group_count,
            "raw_all_frames_resident": summary.get("raw_all_frames_resident"),
            "calibrated_stack_resident": summary.get("calibrated_stack_resident"),
            "registered_cache_materialized_on_disk": summary.get("registered_cache_materialized_on_disk"),
            "max_estimated_calibrated_stack_bytes": calibrated_bytes,
            "max_estimated_peak_bytes": peak_bytes,
        },
        "timing_path": timing_path,
        "timing_summary": {
            "calibrated_stack_resident": timing_summary.get("calibrated_stack_resident"),
            "raw_all_frames_resident": timing_summary.get("raw_all_frames_resident"),
            "registered_cache_materialized_on_disk": timing_summary.get(
                "registered_cache_materialized_on_disk"
            ),
            "max_estimated_peak_bytes": timing_summary.get("max_estimated_peak_bytes"),
        },
        "passed": passed,
    }


def _comparison_summary(compare_payload: dict[str, Any]) -> dict[str, Any]:
    region = (
        compare_payload.get("comparison_region")
        if isinstance(compare_payload.get("comparison_region"), dict)
        else {}
    )
    full = (
        compare_payload.get("full_frame_stats")
        if isinstance(compare_payload.get("full_frame_stats"), dict)
        else {}
    )
    return {
        "shape_match": compare_payload.get("shape_match"),
        "rms_diff": _number(compare_payload.get("rms_diff")),
        "abs_diff_p99": _number(compare_payload.get("abs_diff_p99")),
        "coverage_fraction": _number(region.get("coverage_fraction")),
        "compared_pixels": _int_or_none(region.get("compared_pixels")),
        "full_frame_rms_diff": _number(full.get("rms_diff")),
        "full_frame_abs_diff_p99": _number(full.get("abs_diff_p99")),
    }


def build_phase2_mainline_audit(
    run: str | Path,
    *,
    acceptance_audit: str | Path | None = None,
    compare_json: str | Path | None = None,
    min_lights: int = 200,
    min_active_frames: int = 190,
    max_masked_frames: int = 10,
    min_speedup: float | None = None,
    min_coverage_fraction: float | None = None,
    max_rms_diff: float | None = None,
    max_abs_diff_p99: float | None = None,
    require_acceptance: bool = False,
    require_compare: bool = False,
) -> dict[str, Any]:
    run_root = Path(run)
    timing = _json_if_exists(run_root / "run_timing.json")
    run_state = _json_if_exists(run_root / "run_state.json")
    frame_accounting = _json_if_exists(run_root / "frame_accounting.json")
    frame_summary = (
        frame_accounting.get("summary")
        if isinstance(frame_accounting.get("summary"), dict)
        else {}
    )
    frame_masks = _json_if_exists(run_root / "resident_frame_masks.json")
    frame_mask_summary = (
        frame_masks.get("summary") if isinstance(frame_masks.get("summary"), dict) else {}
    )
    reference_health = _json_if_exists(run_root / "resident_reference_health.json")
    reference_health_summary = (
        reference_health.get("summary") if isinstance(reference_health.get("summary"), dict) else {}
    )
    lifecycle = _json_if_exists(run_root / "resident_dq_lifecycle.json")
    lifecycle_summary = (
        lifecycle.get("summary") if isinstance(lifecycle.get("summary"), dict) else {}
    )
    pipeline_contract = _json_if_exists(run_root / "pipeline_contract.json")
    pipeline_contract_summary = (
        pipeline_contract.get("summary")
        if isinstance(pipeline_contract.get("summary"), dict)
        else {}
    )
    pipeline_dq_ledger = (
        pipeline_contract.get("dq_ledger")
        if isinstance(pipeline_contract.get("dq_ledger"), dict)
        else {}
    )
    resident_artifact = _first_resident_artifact(run_root)

    input_light_frames = _int_or_none(frame_summary.get("input_light_frames"))
    active_frames = _int_or_none(frame_summary.get("resident_frame_mask_active_frames"))
    if active_frames is None:
        active_frames = _int_or_none(frame_mask_summary.get("active_frame_count"))
    masked_frames = _int_or_none(frame_summary.get("resident_frame_mask_masked_frames"))
    if masked_frames is None:
        masked_frames = _int_or_none(frame_mask_summary.get("masked_frame_count"))

    required_paths = {name: str(run_root / name) for name in REQUIRED_CORE_ARTIFACTS}
    missing_core = [name for name in REQUIRED_CORE_ARTIFACTS if not (run_root / name).exists()]

    contract_names = (
        "pipeline_contract.json",
        "stack_engine_contract.json",
        "warp_quality_contract.json",
        "resident_result_contract.json",
        "resident_frame_masks.json",
        "resident_dq_lifecycle.json",
        "resident_source_dq_execution.json",
        "resident_dq_pixel_closure.json",
        "resident_master_cache.json",
        "resident_registration_runtime_contract.json",
    )
    contract_state = {name: _artifact_passed(run_root, name) for name in contract_names}
    failed_contracts = [
        name
        for name, record in contract_state.items()
        if not record["exists"] or record["passed"] is not True
    ]

    output_maps = _output_map_state(run_root, resident_artifact)
    timing_state = _timing_components(run_root, timing, resident_artifact)
    stage_ledger_state = _stage_ledger_state(run_root)
    memory_lifecycle_state = _resident_memory_lifecycle_state(run_root, timing)
    registration_runtime = _registration_runtime_state(run_root)
    active_coverage_contract = build_resident_active_coverage_contract_state(run_root)

    default_route_evidence = {
        "backend": timing.get("backend"),
        "memory_mode": timing.get("memory_mode"),
        "resident_runtime_preset": timing.get("resident_runtime_preset"),
        "resident_registration": timing.get("resident_registration"),
        "integration_rejection": timing.get("integration_rejection"),
        "local_normalization": timing.get("local_normalization"),
        "resident_local_normalization_mode": timing.get("resident_local_normalization_mode"),
        "resident_warp_interpolation": timing.get("resident_warp_interpolation"),
        "resident_fits_read_mode_effective": (
            timing.get("resident_fits_read_mode_resolution") or {}
        ).get("effective")
        if isinstance(timing.get("resident_fits_read_mode_resolution"), dict)
        else None,
    }
    default_route_passed = (
        default_route_evidence["backend"] == "cuda"
        and default_route_evidence["memory_mode"] == "resident"
        and default_route_evidence["resident_runtime_preset"] == "throughput-v4-native-completion"
        and default_route_evidence["resident_registration"] == "similarity_cuda_triangle"
        and default_route_evidence["integration_rejection"] == "winsorized_sigma"
        and default_route_evidence["local_normalization"] == "on"
        and default_route_evidence["resident_local_normalization_mode"] == "grid_mean_std"
        and default_route_evidence["resident_warp_interpolation"] == "lanczos3"
    )

    lifecycle_evidence = {
        "frame_accounting_present": frame_summary.get("resident_dq_lifecycle_present"),
        "frame_accounting_status": frame_summary.get("resident_dq_lifecycle_status"),
        "frame_accounting_passed": frame_summary.get("resident_dq_lifecycle_passed"),
        "frame_accounting_rows": frame_summary.get("resident_dq_lifecycle_rows"),
        "frame_accounting_active_frames": frame_summary.get("resident_dq_lifecycle_active_frames"),
        "frame_accounting_masked_frames": frame_summary.get("resident_dq_lifecycle_masked_frames"),
        "lifecycle_status": lifecycle_summary.get("status"),
        "lifecycle_passed": lifecycle_summary.get("passed"),
        "lifecycle_frame_count": lifecycle_summary.get("frame_count"),
        "lifecycle_active_frames": lifecycle_summary.get("active_frame_count"),
        "lifecycle_masked_frames": lifecycle_summary.get("masked_frame_count"),
    }
    lifecycle_passed = (
        lifecycle_evidence["frame_accounting_present"] is True
        and lifecycle_evidence["frame_accounting_passed"] is True
        and lifecycle_evidence["lifecycle_passed"] is True
        and _int_or_none(lifecycle_evidence["frame_accounting_rows"]) == input_light_frames
        and _int_or_none(lifecycle_evidence["lifecycle_frame_count"]) == input_light_frames
        and _int_or_none(lifecycle_evidence["frame_accounting_active_frames"]) == active_frames
        and _int_or_none(lifecycle_evidence["lifecycle_active_frames"]) == active_frames
        and _int_or_none(lifecycle_evidence["frame_accounting_masked_frames"]) == masked_frames
        and _int_or_none(lifecycle_evidence["lifecycle_masked_frames"]) == masked_frames
    )
    pipeline_dq_ledger_evidence = {
        "pipeline_contract_exists": bool(pipeline_contract),
        "pipeline_contract_status": pipeline_contract.get("status"),
        "pipeline_contract_passed": pipeline_contract.get("passed"),
        "dq_ledger_present": bool(pipeline_dq_ledger),
        "dq_ledger_status": pipeline_dq_ledger.get("status"),
        "dq_ledger_passed": pipeline_dq_ledger.get("passed"),
        "resident_integration_required": pipeline_dq_ledger.get(
            "resident_integration_required"
        ),
        "resident_integration_output_count": pipeline_dq_ledger.get(
            "resident_integration_output_count"
        ),
        "failed_sections": pipeline_dq_ledger.get("failed_sections"),
        "failed_integration_outputs": pipeline_dq_ledger.get(
            "failed_integration_outputs"
        ),
        "summary_dq_ledger_status": pipeline_contract_summary.get("dq_ledger_status"),
        "summary_dq_ledger_passed": pipeline_contract_summary.get("dq_ledger_passed"),
    }
    pipeline_dq_ledger_passed = (
        pipeline_contract.get("passed") is True
        and pipeline_dq_ledger.get("resident_integration_required") is True
        and pipeline_dq_ledger.get("passed") is True
        and pipeline_contract_summary.get("dq_ledger_passed") is True
    )

    acceptance_payload: dict[str, Any] = {}
    if acceptance_audit is not None:
        acceptance_payload = _json_if_exists(Path(acceptance_audit))
    compare_payload: dict[str, Any] = {}
    if compare_json is not None:
        compare_payload = _json_if_exists(Path(compare_json))
    elif isinstance(acceptance_payload.get("compare_json"), str):
        compare_payload = _json_if_exists(Path(acceptance_payload["compare_json"]))

    speedup = None
    comparison_summary: dict[str, Any] = {}
    if acceptance_payload:
        speedup_summary = (
            acceptance_payload.get("speedup_summary")
            if isinstance(acceptance_payload.get("speedup_summary"), dict)
            else {}
        )
        speedup = _number(speedup_summary.get("speedup_vs_wbpp"))
        comparison = speedup_summary.get("comparison") if isinstance(speedup_summary.get("comparison"), dict) else {}
        if comparison:
            comparison_summary = {
                "shape_match": comparison.get("shape_match"),
                "rms_diff": _number(comparison.get("rms_diff")),
                "abs_diff_p99": _number(comparison.get("abs_diff_p99")),
                "coverage_fraction": _number(comparison.get("coverage_fraction")),
                "compared_pixels": _int_or_none(comparison.get("compared_pixels")),
                "full_frame_rms_diff": _number(comparison.get("full_frame_rms_diff")),
                "full_frame_abs_diff_p99": _number(comparison.get("full_frame_abs_diff_p99")),
            }
    if compare_payload:
        comparison_summary = _comparison_summary(compare_payload)

    acceptance_required_passed = True
    if require_acceptance:
        acceptance_required_passed = bool(acceptance_payload) and acceptance_payload.get("passed") is True
    acceptance_speedup_passed = True
    if min_speedup is not None:
        acceptance_speedup_passed = speedup is not None and speedup >= float(min_speedup)

    compare_required_passed = True
    if require_compare:
        compare_required_passed = bool(comparison_summary) and comparison_summary.get("shape_match") is True
    compare_thresholds_passed = True
    if min_coverage_fraction is not None:
        value = _number(comparison_summary.get("coverage_fraction"))
        compare_thresholds_passed = compare_thresholds_passed and value is not None and value >= min_coverage_fraction
    if max_rms_diff is not None:
        value = _number(comparison_summary.get("rms_diff"))
        compare_thresholds_passed = compare_thresholds_passed and value is not None and value <= max_rms_diff
    if max_abs_diff_p99 is not None:
        value = _number(comparison_summary.get("abs_diff_p99"))
        compare_thresholds_passed = compare_thresholds_passed and value is not None and value <= max_abs_diff_p99

    checks = [
        _check("run_exists", run_root.exists(), {"run_dir": str(run_root)}),
        _check(
            "run_state_not_failed",
            run_state.get("failed_stage") in (None, ""),
            {
                "failed_stage": run_state.get("failed_stage"),
                "error_count": len(run_state.get("errors") or []),
                "current_stage": run_state.get("current_stage"),
            },
        ),
        _check(
            "default_resident_cuda_route",
            default_route_passed,
            default_route_evidence,
            "Phase 2 mainline expects the high-VRAM resident CUDA default route.",
        ),
        _check(
            "core_artifacts_present",
            not missing_core,
            {"missing": missing_core, "required_paths": required_paths},
        ),
        _check(
            "contracts_passed",
            not failed_contracts,
            {"failed_contracts": failed_contracts, "contracts": contract_state},
        ),
        _check(
            "frame_thresholds_met",
            input_light_frames is not None
            and input_light_frames >= min_lights
            and active_frames is not None
            and active_frames >= min_active_frames
            and masked_frames is not None
            and masked_frames <= max_masked_frames,
            {
                "input_light_frames": input_light_frames,
                "min_lights": min_lights,
                "active_frames": active_frames,
                "min_active_frames": min_active_frames,
                "masked_frames": masked_frames,
                "max_masked_frames": max_masked_frames,
            },
        ),
        _check("resident_dq_lifecycle_closes", lifecycle_passed, lifecycle_evidence),
        _check(
            "pipeline_contract_dq_ledger_contract",
            pipeline_dq_ledger_passed,
            pipeline_dq_ledger_evidence,
            "Pipeline contract must expose a passing resident DQ/mask ledger for the Phase 2 mainline route.",
        ),
        _check(
            "resident_stage_ledger_component_contract",
            bool(stage_ledger_state["passed"]),
            stage_ledger_state,
        ),
        _check(
            "resident_memory_lifecycle_contract",
            bool(memory_lifecycle_state["passed"]),
            memory_lifecycle_state,
            "Default resident CUDA runs must preserve the raw-stream, calibrated-stack-resident, no registered-cache lifecycle.",
        ),
        _check(
            "resident_registration_runtime_contract_passed",
            registration_runtime["exists"] is True and registration_runtime["passed"] is True,
            registration_runtime,
            "Default resident CUDA runs must prove batched triangle registration and native matrix warp without fallback.",
        ),
        _check(
            "resident_output_maps_present",
            not output_maps["missing_fields"],
            output_maps,
        ),
        _check(
            "resident_active_coverage_stack_surface_contract",
            bool(active_coverage_contract["passed"]),
            active_coverage_contract,
            "Resident StackEngine output support must close active frames, coverage, and weight maps.",
        ),
        _check(
            "timing_components_available",
            timing_state["total_elapsed_s"] is not None
            and timing_state["stages"]["resident_calibration_integration"] is not None
            and timing_state["component_artifact"]["exists"] is True
            and timing_state["component_artifact"]["passed"] is True
            and not timing_state["component_artifact"]["missing_required_components"]
            and timing_state["resident_components_s"]["light_read_upload_calibrate"] is not None
            and timing_state["resident_components_s"]["resident_registration_warp"] is not None
            and timing_state["resident_components_s"]["resident_integration"] is not None,
            timing_state,
        ),
        _check(
            "acceptance_audit_passed_when_required",
            acceptance_required_passed,
            {
                "required": require_acceptance,
                "path": None if acceptance_audit is None else str(acceptance_audit),
                "present": bool(acceptance_payload),
                "passed": acceptance_payload.get("passed"),
                "status": acceptance_payload.get("status"),
            },
        ),
        _check(
            "speedup_threshold_met",
            acceptance_speedup_passed,
            {"speedup_vs_wbpp": speedup, "min_speedup": min_speedup},
        ),
        _check(
            "compare_shape_passed_when_required",
            compare_required_passed,
            {"required": require_compare, "comparison": comparison_summary},
        ),
        _check(
            "compare_thresholds_met",
            compare_thresholds_passed,
            {
                "comparison": comparison_summary,
                "min_coverage_fraction": min_coverage_fraction,
                "max_rms_diff": max_rms_diff,
                "max_abs_diff_p99": max_abs_diff_p99,
            },
        ),
    ]
    failed_checks = [item["name"] for item in checks if not item["passed"]]

    reference_scout_s = timing_state["stages"].get("resident_reference_scout") or 0.0
    reference_health_s = timing_state["stages"].get("resident_reference_health") or 0.0
    cpu_crosscheck_reused = reference_health_summary.get("cpu_crosscheck_reused") is True
    post_resident_reused = reference_health_summary.get("post_resident_artifact_reused") is True
    reference_reuse_reason = (
        "post-resident artifacts validate the CPU-guarded reference without pre-compute calibrated sampling"
        if post_resident_reused
        else "CPU scout rows are reused; calibrated and CUDA-calibrated health still add wall time"
        if cpu_crosscheck_reused
        else "reference scout plus calibrated health are correctness gates but add wall time"
    )
    next_priorities = [
        {
            "priority": 1,
            "area": "resident calibration/integration execution",
            "reason": "largest measured mainline stage remains resident_calibration_integration",
            "evidence_s": timing_state["stages"].get("resident_calibration_integration"),
        },
        {
            "priority": 2,
            "area": (
                "reference health post-resident artifact reuse monitoring"
                if post_resident_reused
                else "reference calibrated-health resident reuse"
                if cpu_crosscheck_reused
                else "reference scout/health resident reuse"
            ),
            "reason": reference_reuse_reason,
            "evidence_s": reference_scout_s + reference_health_s,
            "evidence": {
                "resident_reference_scout_s": reference_scout_s,
                "resident_reference_health_s": reference_health_s,
                "cpu_crosscheck_reused": cpu_crosscheck_reused,
                "post_resident_artifact_reused": post_resident_reused,
                "calibrated_available": reference_health_summary.get("calibrated_available"),
                "cuda_calibrated_available": reference_health_summary.get("cuda_calibrated_available"),
            },
        },
        {
            "priority": 3,
            "area": "DQ/mask semantics under nonzero source-DQ inputs",
            "reason": "current real benchmark has no sidecar/inline source-DQ invalid samples",
            "evidence": {
                "resident_source_dq_contract_rows": frame_summary.get("resident_source_dq_contract_rows"),
                "source_input_samples": frame_summary.get("resident_dq_lifecycle_source_input_samples"),
            },
        },
    ]

    passed = all(item["passed"] for item in checks)
    return {
        "schema_version": 1,
        "artifact_type": "phase2_mainline_audit",
        "created_at": now_iso(),
        "run_dir": str(run_root),
        "status": "passed" if passed else "failed",
        "passed": passed,
        "failed_checks": failed_checks,
        "thresholds": {
            "min_lights": min_lights,
            "min_active_frames": min_active_frames,
            "max_masked_frames": max_masked_frames,
            "min_speedup": min_speedup,
            "min_coverage_fraction": min_coverage_fraction,
            "max_rms_diff": max_rms_diff,
            "max_abs_diff_p99": max_abs_diff_p99,
            "require_acceptance": require_acceptance,
            "require_compare": require_compare,
        },
        "summary": {
            "input_light_frames": input_light_frames,
            "active_frames": active_frames,
            "masked_frames": masked_frames,
            "total_elapsed_s": timing_state["total_elapsed_s"],
            "speedup_vs_wbpp": speedup,
            "comparison": comparison_summary,
            "largest_stage": timing_state["largest_stage"],
            "largest_resident_component": timing_state["largest_resident_component"],
            "resident_memory_lifecycle": memory_lifecycle_state["summary"],
            "resident_registration_runtime": registration_runtime,
            "resident_active_coverage_contract": {
                "status": active_coverage_contract["status"],
                "output_count": active_coverage_contract["output_count"],
                "failed_output_count": active_coverage_contract["failed_output_count"],
            },
            "pipeline_dq_ledger": {
                "status": pipeline_dq_ledger.get("status"),
                "passed": pipeline_dq_ledger.get("passed"),
                "resident_integration_output_count": pipeline_dq_ledger.get(
                    "resident_integration_output_count"
                ),
                "failed_section_count": len(pipeline_dq_ledger.get("failed_sections") or []),
                "failed_integration_output_count": len(
                    pipeline_dq_ledger.get("failed_integration_outputs") or []
                ),
            },
        },
        "checks": checks,
        "next_priorities": next_priorities,
    }


def _markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    lines = [
        "# Phase 2 Mainline Audit",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Passed: `{payload.get('passed')}`",
        f"- Run: `{payload.get('run_dir')}`",
        f"- Input lights: `{summary.get('input_light_frames')}`",
        f"- Active / masked frames: `{summary.get('active_frames')}` / `{summary.get('masked_frames')}`",
        f"- Total elapsed: `{summary.get('total_elapsed_s')}` s",
        f"- Speedup vs WBPP: `{summary.get('speedup_vs_wbpp')}`",
        f"- Pipeline DQ ledger: `{(summary.get('pipeline_dq_ledger') or {}).get('status')}`",
        f"- Failed checks: `{payload.get('failed_checks')}`",
        "",
        "## Checks",
    ]
    for check in payload.get("checks") or []:
        status = "PASS" if check.get("passed") else "FAIL"
        lines.append(f"- `{check.get('name')}`: {status}")
    lines.extend(["", "## Next Priorities"])
    for item in payload.get("next_priorities") or []:
        lines.append(f"- P{item.get('priority')} `{item.get('area')}`: {item.get('reason')}")
    lines.append("")
    return "\n".join(lines)


def write_phase2_mainline_audit(
    path: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(path, payload)
    if markdown is not None:
        Path(markdown).parent.mkdir(parents=True, exist_ok=True)
        Path(markdown).write_text(_markdown(payload), encoding="utf-8")
