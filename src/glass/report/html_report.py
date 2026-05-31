from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any

from glass.report.optimization_guide import build_optimization_guidance


_RESIDENT_OUTPUT_MAP_FIELDS = [
    ("master", "master_path"),
    ("weight", "weight_map_path"),
    ("coverage", "coverage_map_path"),
    ("low_rejection", "low_rejection_map_path"),
    ("high_rejection", "high_rejection_map_path"),
    ("dq", "dq_map_path"),
]

_REPORT_TABLE_ROW_LIMIT = 200

_REPORT_SECTIONS = [
    ("project-summary", "Project summary"),
    ("benchmark-comparison", "Benchmark comparison"),
    ("optimization-guidance", "Optimization guidance"),
    ("acceptance-check-failures", "Acceptance check failures"),
    ("output-numerical-drift", "Output numerical drift"),
    ("stage-coverage-summary", "Stage coverage summary"),
    ("input-frame-table", "Input frame table"),
    ("frame-type-distribution", "Frame type distribution"),
    ("calibration-group-matching", "Calibration group matching"),
    ("master-frame-statistics", "Master frame statistics"),
    ("xisf-input-cache", "XISF input cache"),
    ("frame-quality-table", "Frame quality table"),
    ("registration-table", "Registration table"),
    ("local-normalization-summary", "Local normalization summary"),
    ("integration-summary", "Integration summary"),
    ("frame-accounting", "Frame accounting"),
    ("rejected-zero-weight-frames", "Rejected/zero-weight frames"),
    ("output-diagnostics", "Output diagnostics"),
    ("integration-output-maps", "Integration output maps"),
    ("output-map-policy", "Output map policy"),
    ("resident-output-maps", "Resident output maps"),
    ("dq-mask-summary", "DQ/mask summary"),
    ("stackengine-dq-provenance", "StackEngine DQ provenance"),
    ("dq-provenance-contract", "DQ provenance contract"),
    ("geometric-warp-coverage", "Geometric warp coverage"),
    ("resident-cuda-summary", "Resident CUDA summary"),
    ("output-artifacts", "Output artifacts"),
    ("memory-usage-summary", "Memory usage summary"),
    ("runtime-summary", "Runtime summary"),
    ("warnings-errors", "Warnings/errors"),
    ("pixinsight-comparison-if-available", "PixInsight comparison if available"),
    ("known-differences-from-wbpp", "Known differences from WBPP"),
    ("clean-room-compliance-note", "Clean-room compliance note"),
]


def _resolve_report_path(path: Any, run_root: str | Path | None) -> Path | None:
    if not path:
        return None
    candidate = Path(str(path))
    if candidate.is_absolute() or run_root is None:
        return candidate
    return Path(run_root) / candidate


def _path_exists(path: Any, run_root: str | Path | None) -> bool | None:
    resolved = _resolve_report_path(path, run_root)
    if resolved is None:
        return None
    return resolved.exists()


def _estimated_mib(storage: dict[str, Any]) -> float | None:
    bytes_value = storage.get("estimated_data_bytes")
    if bytes_value is None:
        return None
    return round(float(bytes_value) / (1024.0 * 1024.0), 3)


def _table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "<p>No rows.</p>"
    keys: list[str] = []
    for row in rows:
        for key in row.keys():
            if key not in keys:
                keys.append(key)
    head = "".join(f"<th>{escape(str(k))}</th>" for k in keys)
    body = []
    for row in rows:
        body.append("<tr>" + "".join(f"<td>{escape(str(row.get(k, '')))}</td>" for k in keys) + "</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def _limited_table(
    rows: list[dict[str, Any]],
    *,
    label: str,
    artifact: str,
    limit: int = _REPORT_TABLE_ROW_LIMIT,
) -> str:
    total = len(rows)
    if total <= limit:
        return _table(rows)
    shown = rows[:limit]
    note = (
        f'<p class="table-limit-note">Showing first {limit} of {total} '
        f"{escape(label)}. Full details remain in <code>{escape(artifact)}</code>.</p>"
    )
    return note + _table(shown)


def _report_toc() -> str:
    links = "".join(
        f'<li><a href="#{escape(section_id)}">{escape(title)}</a></li>' for section_id, title in _REPORT_SECTIONS
    )
    return f'<nav class="report-toc" aria-label="Report sections"><h2>Report navigation</h2><ol>{links}</ol></nav>'


def _h2(section_id: str, title: str) -> str:
    return (
        f'<h2 id="{escape(section_id)}">{escape(title)} '
        f'<a class="section-anchor" href="#{escape(section_id)}" aria-label="Link to {escape(title)}">#</a></h2>'
    )


def _benchmark_comparison_rows(
    compare: dict[str, Any] | None,
    acceptance_audit: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    if not compare and not acceptance_audit:
        return []
    speedup = (acceptance_audit or {}).get("speedup_summary") or {}
    speedup_comparison = speedup.get("comparison") or {}
    glass = speedup.get("glass") or {}
    reference = speedup.get("wbpp_blackbox") or {}
    timing = (compare or {}).get("timing") or {}
    region = (compare or {}).get("comparison_region") or {}
    checks = (acceptance_audit or {}).get("checks") or []
    failed_checks = [str(item.get("name")) for item in checks if not item.get("passed")]
    counts = (acceptance_audit or {}).get("frame_type_counts") or {}
    contract = (acceptance_audit or {}).get("benchmark_contract") or {}
    return [
        {
            "acceptance_status": (acceptance_audit or {}).get("status"),
            "benchmark_contract": contract.get("name"),
            "compare_json": (compare or {}).get("_report_source_path") or speedup_comparison.get("path"),
            "acceptance_json": (acceptance_audit or {}).get("_report_source_path"),
            "glass_time_s": timing.get("glass_time_seconds", glass.get("elapsed_s")),
            "reference_time_s": timing.get("reference_time_seconds", reference.get("elapsed_s")),
            "speedup": timing.get("speedup_vs_reference", speedup.get("speedup_vs_wbpp")),
            "shape_match": (compare or {}).get("shape_match", speedup_comparison.get("shape_match")),
            "rms_diff": (compare or {}).get("rms_diff", speedup_comparison.get("rms_diff")),
            "abs_diff_p99": (compare or {}).get("abs_diff_p99", speedup_comparison.get("abs_diff_p99")),
            "coverage_fraction": region.get("coverage_fraction", speedup_comparison.get("coverage_fraction")),
            "compared_pixels": region.get("compared_pixels", speedup_comparison.get("compared_pixels")),
            "active_frames": glass.get("weighted_frame_count"),
            "zero_weight_frames": glass.get("zero_weight_frame_count"),
            "light_frames": counts.get("light"),
            "bias_frames": counts.get("bias"),
            "dark_frames": counts.get("dark"),
            "flat_frames": counts.get("flat"),
            "checks_passed": sum(1 for item in checks if item.get("passed")),
            "checks_failed": len(failed_checks),
            "failed_check_names": ", ".join(failed_checks[:8]),
        }
    ]


def _quality_gate_rows(quality: dict[str, Any] | None) -> list[dict[str, Any]]:
    summary = (quality or {}).get("quality_gate_summary") or {}
    if not summary:
        return []
    policy = summary.get("policy") or {}
    return [
        {
            "accepted": summary.get("accepted_count"),
            "rejected": summary.get("rejected_count"),
            "reference_candidates": summary.get("reference_candidate_count"),
            "fallback_used": summary.get("fallback_used"),
            "min_stars": policy.get("min_stars"),
            "max_saturation_fraction": policy.get("max_saturation_fraction"),
            "min_quality_score": policy.get("min_quality_score"),
            "rejection_reasons": summary.get("rejection_reason_counts"),
        }
    ]


def _frame_accounting_summary_rows(frame_accounting: dict[str, Any] | None) -> list[dict[str, Any]]:
    summary = (frame_accounting or {}).get("summary") or {}
    if not summary:
        return []
    return [
        {
            "input_light_frames": summary.get("input_light_frames"),
            "integrated_frames": summary.get("integrated_frames"),
            "zero_weight_frames": summary.get("zero_weight_frames"),
            "quality_rejected_frames": summary.get("quality_rejected_frames"),
            "registration_accepted_frames": summary.get("registration_accepted_frames"),
            "warp_accepted_frames": summary.get("warp_accepted_frames"),
            "warp_skipped_frames": summary.get("warp_skipped_frames"),
            "not_integrated_frames": summary.get("not_integrated_frames"),
            "final_status_counts": summary.get("final_status_counts"),
        }
    ]


def _frame_accounting_rows(frame_accounting: dict[str, Any] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in (frame_accounting or {}).get("frames", []):
        reasons = item.get("reasons") if isinstance(item.get("reasons"), list) else []
        warnings = item.get("warnings") if isinstance(item.get("warnings"), list) else []
        rows.append(
            {
                "frame_id": item.get("frame_id"),
                "filter": item.get("filter"),
                "final_status": item.get("final_status"),
                "quality_gate": item.get("quality_gate_status"),
                "registration": item.get("registration_status"),
                "warp": item.get("warp_status"),
                "local_norm": item.get("local_norm_status"),
                "integration": item.get("integration_status"),
                "weight": item.get("integration_weight"),
                "reason_count": len(reasons),
                "first_reason": reasons[0] if reasons else "",
                "warning_count": len(warnings),
            }
        )
    return rows


def _frame_accounting_exception_rows(frame_accounting: dict[str, Any] | None) -> list[dict[str, Any]]:
    explicit = (frame_accounting or {}).get("exception_frames")
    if isinstance(explicit, list):
        return [item for item in explicit if isinstance(item, dict)]
    return [row for row in _frame_accounting_rows(frame_accounting) if row.get("final_status") != "integrated"]


def _frame_accounting_exception_summary_rows(frame_accounting: dict[str, Any] | None) -> list[dict[str, Any]]:
    summary = (frame_accounting or {}).get("exception_summary") or {}
    if not summary:
        exceptions = _frame_accounting_exception_rows(frame_accounting)
        if not exceptions:
            return []
        final_counts: dict[str, int] = {}
        stage_counts: dict[str, int] = {}
        for item in exceptions:
            final = str(item.get("final_status") or "unknown")
            stage = str(item.get("primary_stage") or "unknown")
            final_counts[final] = final_counts.get(final, 0) + 1
            stage_counts[stage] = stage_counts.get(stage, 0) + 1
        summary = {
            "count": len(exceptions),
            "final_status_counts": final_counts,
            "primary_stage_counts": stage_counts,
        }
    return [
        {
            "exception_frames": summary.get("count"),
            "final_status_counts": summary.get("final_status_counts"),
            "primary_stage_counts": summary.get("primary_stage_counts"),
        }
    ]


def _acceptance_failure_rows(acceptance_audit: dict[str, Any] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in (acceptance_audit or {}).get("checks") or []:
        if item.get("passed"):
            continue
        evidence = item.get("evidence") if isinstance(item.get("evidence"), dict) else {}
        rows.append(
            {
                "check": item.get("name"),
                "note": item.get("note", ""),
                "actual": evidence.get("actual"),
                "required": evidence.get("required", evidence.get("required_min", evidence.get("required_max"))),
                "details": ", ".join(
                    f"{key}={value}"
                    for key, value in evidence.items()
                    if key not in {"actual", "required", "required_min", "required_max"}
                ),
            }
        )
    return rows


def _output_numerical_drift_rows(audit: dict[str, Any] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in (audit or {}).get("output_numerical_drifts") or []:
        if not isinstance(item, dict):
            continue
        drift = item.get("drift") if isinstance(item.get("drift"), dict) else {}
        rows.append(
            {
                "artifact": item.get("key"),
                "field": item.get("field"),
                "available": drift.get("available"),
                "joint_finite_pixels": drift.get("joint_finite_pixels"),
                "nonfinite_mismatch_pixels": drift.get("nonfinite_mismatch_pixels"),
                "mean_signed": drift.get("mean_signed"),
                "mean_abs": drift.get("mean_abs"),
                "median_abs": drift.get("median_abs"),
                "rms": drift.get("rms"),
                "p95_abs": drift.get("p95_abs"),
                "p99_abs": drift.get("p99_abs"),
                "max_abs": drift.get("max_abs"),
                "baseline_std": drift.get("baseline_std"),
                "candidate_std": drift.get("candidate_std"),
                "relative_rms_to_baseline_std": drift.get("relative_rms_to_baseline_std"),
            }
        )
    return rows


def _optimization_target_rows(guidance: dict[str, Any] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in (guidance or {}).get("targets") or []:
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "rank": item.get("rank"),
                "target": item.get("label"),
                "primary_stage": item.get("primary_stage"),
                "current_s": item.get("current_s"),
                "baseline_s": item.get("baseline_s"),
                "factor": item.get("factor"),
                "share_of_selected_wall": item.get("share_of_selected_wall"),
                "status": item.get("status"),
                "next_action": item.get("next_action"),
            }
        )
    return rows


def _optimization_stage_rows(guidance: dict[str, Any] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in (guidance or {}).get("stage_timing_rows") or []:
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "stage": item.get("stage"),
                "actual_key": item.get("actual_key"),
                "actual_s": item.get("actual_s"),
                "baseline_s": item.get("baseline_s"),
                "delta_s": item.get("delta_s"),
                "factor": item.get("factor"),
                "status": item.get("status"),
                "timing_kind": item.get("timing_kind"),
            }
        )
    return rows[:12]


def _optimization_exception_rows(guidance: dict[str, Any] | None) -> list[dict[str, Any]]:
    context = (guidance or {}).get("exception_context") or {}
    if not context:
        return []
    return [
        {
            "exception_frames": context.get("count"),
            "dominant_stage": context.get("dominant_stage"),
            "primary_stage_counts": context.get("primary_stage_counts"),
            "final_status_counts": context.get("final_status_counts"),
            "sample_frame_ids": ", ".join(str(item) for item in context.get("sample_frame_ids") or []),
            "note": context.get("note"),
        }
    ]


def _warning_rows(
    manifest: dict[str, Any] | None,
    plan: dict[str, Any] | None,
    calibration: dict[str, Any] | None,
    registration: dict[str, Any] | None,
    local_norm: dict[str, Any] | None,
    integration: dict[str, Any] | None,
    timing: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in (manifest or {}).get("warnings", []):
        rows.append({"stage": "scan", "item": item.get("path") if isinstance(item, dict) else "", "warning": item})
    for item in (plan or {}).get("global_warnings", []):
        rows.append({"stage": "plan", "item": "", "warning": item})
    for item in (calibration or {}).get("calibrated_lights", []):
        for warning in item.get("warnings", []):
            rows.append({"stage": "calibration", "item": item.get("frame_id"), "warning": warning})
    for item in (registration or {}).get("registration_results", []):
        for warning in item.get("warnings", []):
            rows.append({"stage": "registration", "item": item.get("frame_id"), "warning": warning})
    for item in (local_norm or {}).get("local_norm_results", []):
        for warning in item.get("warnings", []):
            rows.append({"stage": "local_normalization", "item": item.get("frame_id"), "warning": warning})
    for warning in (integration or {}).get("warnings", []):
        rows.append({"stage": "integration", "item": "", "warning": warning})
    for item in (timing or {}).get("stages", []):
        if item.get("status") == "failed":
            rows.append({"stage": item.get("stage"), "item": "timing", "warning": item.get("error")})
    return rows


def _resident_rows(resident: dict[str, Any] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in (resident or {}).get("artifacts", []):
        memory = item.get("memory_estimate", {})
        timing = item.get("timing_s", {})
        master_stats = item.get("master_stats", {})
        registration = item.get("resident_registration", {})
        io_pipeline = item.get("resident_io_pipeline", {})
        local_norm = item.get("resident_local_normalization", {})
        weighting = item.get("resident_integration_weighting", {})
        rejection = item.get("integration_rejection", {})
        rows.append(
            {
                "filter": item.get("filter"),
                "frames": len(item.get("frame_ids", [])),
                "bias": master_stats.get("bias_count"),
                "dark": master_stats.get("dark_count"),
                "flat": master_stats.get("flat_count"),
                "registration": registration.get("mode"),
                "warp": registration.get("warp_interpolation"),
                "catalog_timing_model": registration.get("triangle_catalog_timing_model"),
                "catalog_sort_mode": registration.get("triangle_catalog_sort_mode"),
                "catalog_topk_mode": registration.get("triangle_catalog_topk_mode"),
                "catalog_native_sync_s": round(
                    float(registration.get("triangle_catalog_native_sync_s") or 0.0), 3
                ),
                "catalog_native_output_download_s": round(
                    float(registration.get("triangle_catalog_native_output_download_s") or 0.0),
                    3,
                ),
                "catalog_native_total_s": round(
                    float(registration.get("triangle_catalog_native_total_s") or 0.0), 3
                ),
                "descriptor_fit_batch": registration.get("triangle_descriptor_fit_batch"),
                "descriptor_fit_batch_mode": registration.get("triangle_descriptor_fit_batch_mode"),
                "descriptor_reference_reuse": registration.get(
                    "triangle_descriptor_fit_reference_device_reuse"
                ),
                "descriptor_reference_mib": round(
                    float(registration.get("triangle_descriptor_fit_reference_device_bytes") or 0.0)
                    / (1024.0**2),
                    3,
                ),
                "descriptor_moving_reuse": registration.get(
                    "triangle_descriptor_fit_moving_device_reuse"
                ),
                "descriptor_moving_mib": round(
                    float(registration.get("triangle_descriptor_fit_moving_device_bytes") or 0.0)
                    / (1024.0**2),
                    3,
                ),
                "descriptor_output_reuse": registration.get(
                    "triangle_descriptor_fit_output_device_reuse"
                ),
                "descriptor_output_mib": round(
                    float(registration.get("triangle_descriptor_fit_output_device_bytes") or 0.0)
                    / (1024.0**2),
                    3,
                ),
                "pixel_refine_workspace_mode": registration.get("triangle_pixel_refine_workspace_mode"),
                "pixel_refine_metric_mode": registration.get("triangle_pixel_refine_batch_metric_mode"),
                "pixel_refine_metric_launches": registration.get("triangle_pixel_refine_batch_metric_kernel_launches"),
                "pixel_refine_coarse_candidates": registration.get("triangle_pixel_refine_coarse_total_candidates"),
                "pixel_refine_fine_candidates": registration.get("triangle_pixel_refine_fine_total_candidates"),
                "pixel_refine_workspace_mib": round(
                    float(registration.get("triangle_pixel_refine_workspace_bytes") or 0.0)
                    / (1024.0**2),
                    3,
                ),
                "pixel_refine_native_coarse_s": round(
                    float(registration.get("triangle_pixel_refine_native_coarse_s") or 0.0),
                    3,
                ),
                "pixel_refine_native_fine_s": round(
                    float(registration.get("triangle_pixel_refine_native_fine_s") or 0.0),
                    3,
                ),
                "determinism_signature_mode": registration.get("triangle_determinism_signature_mode"),
                "determinism_moving_frames": registration.get("triangle_determinism_moving_frame_count"),
                "determinism_thresholds": registration.get("triangle_determinism_threshold_count"),
                "determinism_reference_sha256": registration.get("triangle_determinism_reference_combined_sha256"),
                "determinism_catalog_sha256": registration.get("triangle_determinism_moving_catalog_combined_sha256"),
                "determinism_fit_sha256": registration.get("triangle_determinism_selected_fit_combined_sha256"),
                "local_norm": local_norm.get("mode"),
                "weighting": weighting.get("mode"),
                "rejection": rejection.get("mode"),
                "resident_base_gib": round(float(memory.get("resident_base_gib") or 0.0), 3),
                "estimated_peak_gib": round(float(memory.get("estimated_peak_gib") or 0.0), 3),
                "warp_scratch_mib": round(float(item.get("resident_warp_scratch_bytes") or 0.0) / (1024.0**2), 3),
                "warp_copy_mode": item.get("resident_warp_copy_mode"),
                "light_calibrate_s": round(float(timing.get("light_read_upload_calibrate") or 0.0), 3),
                "prefetch_frames": io_pipeline.get("prefetch_frames", 0),
                "read_decode_s": round(float(timing.get("light_read_decode") or 0.0), 3),
                "read_decode_worker_s": round(float(timing.get("light_read_decode_worker") or 0.0), 3),
                "h2d_calibrate_store_s": round(float(timing.get("light_h2d_calibrate_store") or 0.0), 3),
                "registration_warp_s": round(float(timing.get("resident_registration_warp") or 0.0), 3),
                "registration_accounted_s": round(
                    float(timing.get("resident_registration_component_accounted") or 0.0), 3
                ),
                "registration_orchestration_s": round(
                    float(timing.get("resident_registration_orchestration") or 0.0), 3
                ),
                "light_loop_unaccounted_s": round(float(timing.get("light_loop_unaccounted") or 0.0), 3),
                "weighting_s": round(float(timing.get("resident_weighting") or 0.0), 3),
                "local_norm_s": round(float(timing.get("resident_local_normalization") or 0.0), 3),
                "resident_integrate_s": round(float(timing.get("resident_integration") or 0.0), 3),
                "write_s": round(float(timing.get("output_write") or 0.0), 3),
            }
        )
    return rows


def _active_frame_count(item: dict[str, Any]) -> Any:
    summary = item.get("dq_provenance_summary") or {}
    provenance = item.get("dq_coverage_provenance") or {}
    return summary.get("active_frame_count", provenance.get("active_frame_count"))


def _integration_output_rows(integration: dict[str, Any] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    source_stage = (integration or {}).get("source_stage")
    for item in (integration or {}).get("outputs", []):
        rows.append(
            {
                "filter": item.get("filter"),
                "source_stage": source_stage,
                "backend": item.get("backend"),
                "memory_mode": item.get("memory_mode"),
                "frame_count": item.get("frame_count"),
                "active_frames": _active_frame_count(item),
                "weighting": item.get("weighting", (integration or {}).get("weighting")),
                "rejection": item.get("rejection", (integration or {}).get("rejection")),
                "master": item.get("master_path"),
                "stack_engine": item.get("stack_engine_enabled"),
                "resident_integration_s": item.get("resident_integration_s"),
                "estimated_peak_gib": item.get("estimated_peak_gib"),
            }
        )
    return rows


def _output_diagnostic_rows(
    integration: dict[str, Any] | None,
    resident: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source, items in [
        ("integration", (integration or {}).get("outputs", [])),
        ("resident", (resident or {}).get("artifacts", [])),
    ]:
        for item in items:
            diagnostics = item.get("output_diagnostics") or {}
            if not diagnostics:
                continue
            stats = diagnostics.get("statistics") or {}
            clipping = diagnostics.get("clipping_probe") or {}
            normalization = diagnostics.get("normalization_probe") or {}
            rows.append(
                {
                    "source": source,
                    "filter": item.get("filter"),
                    "total_pixels": diagnostics.get("total_pixels"),
                    "finite_pixels": diagnostics.get("finite_pixels"),
                    "nonfinite_pixels": diagnostics.get("nonfinite_pixels"),
                    "mean": stats.get("mean"),
                    "p50": stats.get("p50"),
                    "std": stats.get("std"),
                    "min": stats.get("min"),
                    "max": stats.get("max"),
                    "lt_0_count": clipping.get("lt_0_count"),
                    "gt_1_count": clipping.get("gt_1_count"),
                    "gt_65535_count": clipping.get("gt_65535_count"),
                    "positive_weight_pixels": clipping.get("positive_weight_pixels"),
                    "zero_weight_pixels": clipping.get("zero_weight_pixels"),
                    "normalization_method": normalization.get("method"),
                    "normalization_scale": normalization.get("scale"),
                    "normalization_offset": normalization.get("offset"),
                    "normalization_black": normalization.get("black"),
                    "normalization_white": normalization.get("white"),
                }
            )
    return rows


def _geometric_warp_coverage_rows(
    integration: dict[str, Any] | None,
    resident: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in (integration or {}).get("outputs", []):
        provenance = item.get("dq_coverage_provenance") or {}
        geometric = item.get("geometric_warp_coverage") or {}
        geometric_stats = provenance.get("geometric_warp_coverage") or {}
        if not geometric and not geometric_stats:
            continue
        dq_summary = item.get("dq_summary") or {}
        rows.append(
            {
                "source": "integration",
                "filter": item.get("filter"),
                "available": geometric.get("available", bool(geometric_stats)),
                "active_frames": provenance.get("active_frame_count"),
                "coverage_frames": provenance.get(
                    "geometric_warp_coverage_frame_count",
                    geometric.get("frame_count"),
                ),
                "matches_active": provenance.get(
                    "geometric_frame_count_matches_active",
                    geometric.get("frame_count_matches_active"),
                ),
                "min": geometric_stats.get("min"),
                "max": geometric_stats.get("max"),
                "mean": geometric_stats.get("mean"),
                "geometric_zero_pixels": provenance.get("geometric_zero_pixels"),
                "geometric_partial_pixels": provenance.get("geometric_partial_pixels"),
                "geometric_full_pixels": provenance.get("geometric_full_pixels"),
                "dq_warp_edge": dq_summary.get("warp_edge"),
                "dq_no_data": dq_summary.get("no_data"),
                "inference": provenance.get("partial_edge_inference"),
            }
        )

    for item in (resident or {}).get("artifacts", []):
        registration = item.get("resident_registration") or {}
        coverage = registration.get("warp_coverage") or {}
        if not coverage:
            continue
        stats = coverage.get("statistics") or {}
        rows.append(
            {
                "source": "resident",
                "filter": item.get("filter"),
                "available": coverage.get("available"),
                "active_frames": coverage.get("active_frame_count"),
                "coverage_frames": coverage.get("frame_count"),
                "matches_active": coverage.get("frame_count_matches_active"),
                "warped_frames": coverage.get("warped_frame_count"),
                "full_frames": coverage.get("full_frame_count"),
                "min": stats.get("min"),
                "max": stats.get("max"),
                "mean": stats.get("mean"),
                "native_source": coverage.get("native_source"),
            }
        )
    return rows


def _dq_summary_rows(
    integration_outputs: list[dict[str, Any]],
    registration_results: list[dict[str, Any]],
    local_norm_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_name, items in [
        ("registration/warp", registration_results),
        ("local_normalization", local_norm_results),
        ("integration", integration_outputs),
    ]:
        for item in items:
            summary = item.get("dq_summary") or {}
            dq_path = item.get("dq_mask_path") or item.get("dq_map_path")
            if not summary and not dq_path:
                continue
            provenance = item.get("dq_coverage_provenance") or {}
            rows.append(
                {
                    "stage": source_name,
                    "frame_or_filter": item.get("frame_id") or item.get("filter"),
                    "path": dq_path,
                    "valid": summary.get("valid"),
                    "no_data": summary.get("no_data"),
                    "warp_edge": summary.get("warp_edge"),
                    "low_rejected": summary.get("low_rejected"),
                    "high_rejected": summary.get("high_rejected"),
                    "source_terms": ", ".join(str(name) for name in provenance.get("source_terms", [])),
                    "active_frames": provenance.get("active_frame_count"),
                    "coverage_inference": provenance.get("partial_edge_inference"),
                }
            )
    return rows


def _output_policy_rows(
    integration: dict[str, Any] | None,
    resident: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for item in (integration or {}).get("outputs", []):
        policy = item.get("output_map_policy") or {}
        if policy:
            rows.append(
                {
                    "source": "integration",
                    "filter": item.get("filter"),
                    "mode": policy.get("mode"),
                    "available": ", ".join(str(name) for name in policy.get("available", [])),
                    "written": ", ".join(str(name) for name in policy.get("written", [])),
                    "skipped": ", ".join(str(name) for name in policy.get("skipped", [])),
                }
            )

    for item in (resident or {}).get("artifacts", []):
        policy = item.get("output_map_policy") or {}
        if policy:
            rows.append(
                {
                    "source": "resident",
                    "filter": item.get("filter"),
                    "mode": policy.get("mode"),
                    "available": ", ".join(str(name) for name in policy.get("available", [])),
                    "written": ", ".join(str(name) for name in policy.get("written", [])),
                    "skipped": ", ".join(str(name) for name in policy.get("skipped", [])),
                    "description": policy.get("description", ""),
                }
            )

    return rows


def _resident_output_map_rows(
    resident: dict[str, Any] | None,
    run_root: str | Path | None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in (resident or {}).get("artifacts", []):
        policy = item.get("output_map_policy") or {}
        available = {str(name) for name in policy.get("available", [])}
        written = {str(name) for name in policy.get("written", [])}
        skipped = {str(name) for name in policy.get("skipped", [])}
        output_write = item.get("output_write") or {}
        storage = item.get("output_write_storage") or output_write.get("storage") or {}
        breakdown = output_write.get("breakdown_s") or {}
        for map_name, path_key in _RESIDENT_OUTPUT_MAP_FIELDS:
            path = item.get(path_key)
            if not path and map_name not in available and map_name not in written and map_name not in skipped:
                continue
            map_storage = storage.get(map_name) or {}
            if map_name in written:
                policy_status = "written"
            elif map_name in skipped:
                policy_status = "skipped"
            elif map_name in available:
                policy_status = "available"
            else:
                policy_status = "not_available"
            rows.append(
                {
                    "filter": item.get("filter"),
                    "map": map_name,
                    "policy": policy_status,
                    "path": path,
                    "exists": _path_exists(path, run_root),
                    "dtype": map_storage.get("dtype"),
                    "estimated_mib": _estimated_mib(map_storage),
                    "write_s": round(float(breakdown.get(map_name) or 0.0), 3)
                    if map_name in breakdown
                    else None,
                }
            )
    return rows


def _stack_engine_dq_rows(
    calibration: dict[str, Any] | None,
    integration: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for group_id, master in (calibration or {}).get("masters", {}).items():
        provenance = master.get("stack_engine_dq_provenance") or {}
        if not provenance:
            continue
        flag_counts = provenance.get("input_dq_flag_counts") or {}
        rows.append(
            {
                "stage": "master_calibration",
                "item": group_id,
                "type": master.get("type"),
                "stack": master.get("tile_stack_mode"),
                "input_samples": provenance.get("input_samples"),
                "flagged_samples": provenance.get("input_flagged_samples"),
                "nonfinite_samples": provenance.get("input_nonfinite_samples"),
                "zero_coverage_pixels": provenance.get("output_coverage_zero_pixels"),
                "low_rejected_pixels": provenance.get("output_low_rejected_pixels"),
                "high_rejected_pixels": provenance.get("output_high_rejected_pixels"),
                "hot_pixel_samples": flag_counts.get("hot_pixel"),
                "no_data_samples": flag_counts.get("no_data"),
                "output_dq": provenance.get("output_dq_summary"),
            }
        )

    for item in (integration or {}).get("outputs", []):
        provenance = item.get("stack_engine_dq_provenance") or {}
        if not provenance:
            continue
        flag_counts = provenance.get("input_dq_flag_counts") or {}
        rows.append(
            {
                "stage": "integration",
                "item": item.get("filter"),
                "type": "light",
                "stack": item.get("tile_stack_mode"),
                "input_samples": provenance.get("input_samples"),
                "flagged_samples": provenance.get("input_flagged_samples"),
                "nonfinite_samples": provenance.get("input_nonfinite_samples"),
                "zero_coverage_pixels": provenance.get("output_coverage_zero_pixels"),
                "low_rejected_pixels": provenance.get("output_low_rejected_pixels"),
                "high_rejected_pixels": provenance.get("output_high_rejected_pixels"),
                "hot_pixel_samples": flag_counts.get("hot_pixel"),
                "no_data_samples": flag_counts.get("no_data"),
                "output_dq": provenance.get("output_dq_summary"),
            }
        )

    return rows


def _dq_provenance_contract_rows(
    calibration: dict[str, Any] | None,
    integration: dict[str, Any] | None,
    resident: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for group_id, master in (calibration or {}).get("masters", {}).items():
        summary = master.get("dq_provenance_summary") or {}
        if not summary:
            continue
        rows.append(
            {
                "source": "calibration",
                "stage": summary.get("stage"),
                "item": summary.get("item", group_id),
                "engine": summary.get("engine"),
                "schema": summary.get("source_schema"),
                "input_samples": summary.get("input_samples"),
                "flagged_samples": summary.get("input_flagged_samples"),
                "nonfinite_samples": summary.get("input_nonfinite_samples"),
                "zero_coverage": summary.get("zero_coverage_pixels"),
                "partial_coverage": summary.get("partial_coverage_pixels"),
                "low_rejected": summary.get("low_rejected_pixels"),
                "high_rejected": summary.get("high_rejected_pixels"),
                "valid": summary.get("valid_pixels"),
                "no_data": summary.get("no_data_pixels"),
                "warp_edge": summary.get("warp_edge_pixels"),
            }
        )

    for item in (integration or {}).get("outputs", []):
        summary = item.get("dq_provenance_summary") or {}
        if not summary:
            continue
        rows.append(
            {
                "source": "integration",
                "stage": summary.get("stage"),
                "item": summary.get("item", item.get("filter")),
                "engine": summary.get("engine"),
                "schema": summary.get("source_schema"),
                "input_samples": summary.get("input_samples"),
                "flagged_samples": summary.get("input_flagged_samples"),
                "nonfinite_samples": summary.get("input_nonfinite_samples"),
                "zero_coverage": summary.get("zero_coverage_pixels"),
                "partial_coverage": summary.get("partial_coverage_pixels"),
                "low_rejected": summary.get("low_rejected_pixels"),
                "high_rejected": summary.get("high_rejected_pixels"),
                "valid": summary.get("valid_pixels"),
                "no_data": summary.get("no_data_pixels"),
                "warp_edge": summary.get("warp_edge_pixels"),
            }
        )

    for item in (resident or {}).get("artifacts", []):
        summary = item.get("dq_provenance_summary") or {}
        if not summary:
            continue
        rows.append(
            {
                "source": "resident",
                "stage": summary.get("stage"),
                "item": summary.get("item", item.get("filter")),
                "engine": summary.get("engine"),
                "schema": summary.get("source_schema"),
                "active_frames": summary.get("active_frame_count"),
                "zero_coverage": summary.get("zero_coverage_pixels"),
                "partial_coverage": summary.get("partial_coverage_pixels"),
                "low_rejected": summary.get("low_rejected_pixels"),
                "high_rejected": summary.get("high_rejected_pixels"),
                "valid": summary.get("valid_pixels"),
                "no_data": summary.get("no_data_pixels"),
                "warp_edge": summary.get("warp_edge_pixels"),
            }
        )

    return rows


def write_html_report(
    out_path: str | Path,
    manifest: dict[str, Any] | None = None,
    plan: dict[str, Any] | None = None,
    calibration: dict[str, Any] | None = None,
    quality: dict[str, Any] | None = None,
    registration: dict[str, Any] | None = None,
    local_norm: dict[str, Any] | None = None,
    integration: dict[str, Any] | None = None,
    timing: dict[str, Any] | None = None,
    resident: dict[str, Any] | None = None,
    frame_accounting: dict[str, Any] | None = None,
    compare: dict[str, Any] | None = None,
    acceptance_audit: dict[str, Any] | None = None,
    title: str = "GLASS Report",
    run_root: str | Path | None = None,
) -> None:
    frames = (manifest or {}).get("frames", [])
    light_plans = (plan or {}).get("light_plans", [])
    benchmark_comparison_rows = _benchmark_comparison_rows(compare, acceptance_audit)
    optimization_guidance = (acceptance_audit or {}).get("optimization_guidance")
    if not isinstance(optimization_guidance, dict) or not optimization_guidance.get("targets"):
        optimization_guidance = build_optimization_guidance(
            performance_regression=(acceptance_audit or {}).get("performance_regression"),
            frame_accounting=frame_accounting,
            resident=resident,
        )
    optimization_target_rows = _optimization_target_rows(optimization_guidance)
    optimization_stage_rows = _optimization_stage_rows(optimization_guidance)
    optimization_exception_rows = _optimization_exception_rows(optimization_guidance)
    acceptance_failure_rows = _acceptance_failure_rows(acceptance_audit)
    output_numerical_drift_rows = _output_numerical_drift_rows(acceptance_audit)
    master_rows = []
    for group_id, master in (calibration or {}).get("masters", {}).items():
        stats = master.get("stats", {})
        master_rows.append(
            {
                "group_id": group_id,
                "type": master.get("type"),
                "filter": master.get("filter"),
                "mean": stats.get("mean"),
                "median": stats.get("median"),
                "std": stats.get("std"),
                "rejection": master.get("master_rejection"),
                "stack": master.get("tile_stack_mode"),
            }
        )
    calibration_policy = (calibration or {}).get("policy", {})
    input_cache_rows = (calibration or {}).get("input_cache", [])
    frame_quality = (quality or {}).get("frame_quality", [])
    quality_gate_rows = _quality_gate_rows(quality)
    registration_results = (registration or {}).get("registration_results", [])
    local_norm_results = (local_norm or {}).get("local_norm_results", [])
    integration_outputs = (integration or {}).get("outputs", [])
    integration_summary_rows = _integration_output_rows(integration)
    frame_accounting_summary_rows = _frame_accounting_summary_rows(frame_accounting)
    frame_accounting_rows = _frame_accounting_rows(frame_accounting)
    frame_accounting_exception_summary_rows = _frame_accounting_exception_summary_rows(frame_accounting)
    frame_accounting_exception_rows = _frame_accounting_exception_rows(frame_accounting)
    output_diagnostic_rows = _output_diagnostic_rows(integration, resident)
    integration_map_rows = [
        {
            "filter": item.get("filter"),
            "master": item.get("master_path"),
            "weight": item.get("weight_map_path"),
            "coverage": item.get("coverage_map_path"),
            "variance": item.get("variance_map_path"),
            "low_rejection": item.get("low_rejection_map_path"),
            "high_rejection": item.get("high_rejection_map_path"),
            "dq": item.get("dq_map_path"),
        }
        for item in integration_outputs
    ]
    dq_rows = _dq_summary_rows(integration_outputs, registration_results, local_norm_results)
    timing_rows = (timing or {}).get("stages", [])
    timing_overview = [
        {
            "command": (timing or {}).get("command"),
            "backend": (timing or {}).get("backend"),
            "memory_mode": (timing or {}).get("memory_mode", "tile"),
            "total_elapsed_s": (timing or {}).get("total_elapsed_s"),
            "stage_count": len(timing_rows),
        }
    ]
    stage_coverage_rows = [
        {"stage": "scan", "rows": len(frames), "artifact": "manifest.json" if manifest else "missing"},
        {"stage": "plan", "rows": len(light_plans), "artifact": "processing_plan.json" if plan else "missing"},
        {
            "stage": "calibration",
            "rows": len((calibration or {}).get("calibrated_lights", [])),
            "artifact": "calibration_artifacts.json" if calibration else "missing",
        },
        {
            "stage": "quality",
            "rows": len(frame_quality),
            "artifact": "frame_quality.json" if quality else "missing",
        },
        {
            "stage": "registration",
            "rows": len(registration_results),
            "artifact": "registration_results.json" if registration else "missing",
        },
        {
            "stage": "local_normalization",
            "rows": len(local_norm_results),
            "artifact": "local_norm_results.json" if local_norm else "missing",
        },
        {
            "stage": "integration",
            "rows": len(integration_outputs),
            "artifact": "integration_results.json" if integration else "missing",
        },
        {
            "stage": "frame_accounting",
            "rows": len(frame_accounting_rows),
            "artifact": "frame_accounting.json" if frame_accounting else "missing",
        },
        {
            "stage": "frame_accounting_exceptions",
            "rows": len(frame_accounting_exception_rows),
            "artifact": "frame_accounting.json" if frame_accounting else "missing",
        },
    ]
    resident_summary = _resident_rows(resident)
    geometric_warp_coverage_rows = _geometric_warp_coverage_rows(integration, resident)
    output_policy_rows = _output_policy_rows(integration, resident)
    resident_output_map_rows = _resident_output_map_rows(resident, run_root)
    stack_engine_dq_rows = _stack_engine_dq_rows(calibration, integration)
    dq_provenance_contract_rows = _dq_provenance_contract_rows(calibration, integration, resident)
    warning_rows = _warning_rows(manifest, plan, calibration, registration, local_norm, integration, timing)
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{escape(title)}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #202124; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; font-size: 0.9rem; }}
    th, td {{ border: 1px solid #d0d7de; padding: 0.35rem 0.5rem; text-align: left; }}
    th {{ background: #f6f8fa; }}
    code {{ background: #f6f8fa; padding: 0.1rem 0.25rem; }}
    .report-toc {{ border: 1px solid #d0d7de; padding: 0.75rem 1rem; margin: 1rem 0 1.5rem; }}
    .report-toc h2 {{ margin-top: 0; }}
    .report-toc ol {{ columns: 2; padding-left: 1.25rem; }}
    .section-anchor {{ color: #57606a; text-decoration: none; font-size: 0.8em; }}
    .table-limit-note {{ color: #57606a; font-size: 0.9rem; }}
  </style>
</head>
<body>
  <h1>{escape(title)}</h1>
  {_report_toc()}
  {_h2("project-summary", "Project summary")}
  <p>Clean-room GLASS report. Input directories are not modified.</p>
  {_h2("benchmark-comparison", "Benchmark comparison")}
  <p>When compare and acceptance-audit JSON artifacts are present, this table
  brings speed, image-difference, frame-count, and pass/fail evidence into the
  main report.</p>
  {_table(benchmark_comparison_rows)}
  {_h2("optimization-guidance", "Optimization guidance")}
  <p>This diagnostic view joins benchmark stage timings with rejected-frame
  accounting so the next optimization target is explicit instead of inferred
  from scattered artifacts.</p>
  {_table(optimization_target_rows)}
  {_table(optimization_exception_rows)}
  {_limited_table(optimization_stage_rows, label="optimization timing rows", artifact="acceptance-audit JSON or resident_artifacts.json")}
  {_h2("acceptance-check-failures", "Acceptance check failures")}
  <p>Only failed acceptance-audit checks are listed here. A green run reports no
  rows while retaining the authoritative check list in the audit JSON.</p>
  {_table(acceptance_failure_rows)}
  {_h2("output-numerical-drift", "Output numerical drift")}
  <p>When a resident determinism or acceptance audit contains output FITS
  numerical drift evidence, this table reports the magnitude of strict output
  mismatches instead of leaving only hashes to interpret.</p>
  {_table(output_numerical_drift_rows)}
  {_h2("stage-coverage-summary", "Stage coverage summary")}
  {_table(stage_coverage_rows)}
  {_h2("input-frame-table", "Input frame table")}
  {_limited_table(frames, label="input frames", artifact="manifest.json")}
  {_h2("frame-type-distribution", "Frame type distribution")}
  <pre>{escape(str((manifest or {}).get("summary", {})))}</pre>
  {_h2("calibration-group-matching", "Calibration group matching")}
  {_limited_table(light_plans, label="light plans", artifact="processing_plan.json")}
  {_h2("master-frame-statistics", "Master frame statistics")}
  <pre>{escape(str(calibration_policy))}</pre>
  {_table(master_rows)}
  {_h2("xisf-input-cache", "XISF input cache")}
  <p>XISF sources are streamed into run-local FITS cache files before calibration.</p>
  {_table(input_cache_rows)}
  {_h2("frame-quality-table", "Frame quality table")}
  <p>Detector: <code>{escape(str((quality or {}).get("star_detector", "pending")))}</code>.
  Weight source: <code>{escape(str((quality or {}).get("weight_source", "pending")))}</code>.</p>
  {_table(quality_gate_rows)}
  {_limited_table(frame_quality, label="frame quality rows", artifact="frame_quality.json")}
  <p>Reference frame: <code>{escape(str((quality or {}).get("reference_frame_id", "pending")))}</code></p>
  {_h2("registration-table", "Registration table")}
  {_limited_table(registration_results, label="registration rows", artifact="registration_results.json")}
  {_h2("local-normalization-summary", "Local normalization summary")}
  <p>Enabled: <code>{escape(str((local_norm or {}).get("enabled", "pending")))}</code>.
  Reference frame: <code>{escape(str((local_norm or {}).get("reference_frame_id", "pending")))}</code>.</p>
  {_limited_table(local_norm_results, label="local normalization rows", artifact="local_norm_results.json")}
  {_h2("integration-summary", "Integration summary")}
  <p>Combine: <code>{escape(str((integration or {}).get("combine", "pending")))}</code>.
  Weighting: <code>{escape(str((integration or {}).get("weighting", "pending")))}</code>.
  Rejection: <code>{escape(str((integration or {}).get("rejection", "pending")))}</code>.</p>
  {_table(integration_summary_rows)}
  {_h2("frame-accounting", "Frame accounting")}
  <p>Per-light acceptance accounting joins quality, registration, warp, local
  normalization, integration weight, and final use/skip status. Full details are
  authoritative in <code>frame_accounting.json</code>.</p>
  {_table(frame_accounting_summary_rows)}
  {_limited_table(frame_accounting_rows, label="frame accounting rows", artifact="frame_accounting.json")}
  {_h2("rejected-zero-weight-frames", "Rejected/zero-weight frames")}
  <p>This compact table focuses on frames that did not enter the final integrated
  stack. The complete per-frame ledger remains in <code>frame_accounting.json</code>.</p>
  {_table(frame_accounting_exception_summary_rows)}
  {_limited_table(frame_accounting_exception_rows, label="frame accounting exception rows", artifact="frame_accounting.json")}
  {_h2("output-diagnostics", "Output diagnostics")}
  <p>Output diagnostics are flattened from integration and resident artifacts to
  avoid dumping nested JSON into the report.</p>
  {_table(output_diagnostic_rows)}
  {_h2("integration-output-maps", "Integration output maps")}
  {_table(integration_map_rows)}
  {_h2("output-map-policy", "Output map policy")}
  {_table(output_policy_rows)}
  {_h2("resident-output-maps", "Resident output maps")}
  <p>Resident artifact records expose map paths, write policy status, storage
  dtype, estimated payload size, and per-map write timing for audit review.</p>
  {_table(resident_output_map_rows)}
  {_h2("dq-mask-summary", "DQ/mask summary")}
  {_table(dq_rows)}
  {_h2("stackengine-dq-provenance", "StackEngine DQ provenance")}
  <p>StackEngine paths record source DQ flag counts, non-finite samples,
  zero-coverage pixels, rejection-touched pixels, and output DQ summaries.</p>
  {_table(stack_engine_dq_rows)}
  {_h2("dq-provenance-contract", "DQ provenance contract")}
  <p>This normalized summary bridges StackEngine and resident CUDA provenance
  schemas for report and audit consumers.</p>
  {_table(dq_provenance_contract_rows)}
  {_h2("geometric-warp-coverage", "Geometric warp coverage")}
  <p>Resident CUDA runs can accumulate a pre-rejection geometric footprint from
  warp kernels. Partial geometric coverage is reported separately from low/high
  rejection counts.</p>
  {_table(geometric_warp_coverage_rows)}
  {_h2("resident-cuda-summary", "Resident CUDA summary")}
  <p>Backend: <code>{escape(str((resident or {}).get("backend", "not used")))}</code>.
  Device: <code>{escape(str(((resident or {}).get("device") or {}).get("name", "pending")))}</code>.</p>
  {_table(resident_summary)}
  {_h2("output-artifacts", "Output artifacts")}
  <p>See adjacent JSON files in the run directory.</p>
  {_h2("memory-usage-summary", "Memory usage summary")}
  <p>Heavy stages use explicit memory modes. Tile/slab streaming is the bounded
  fallback; resident mode is allowed only when the planned hot set fits within
  the configured device memory budget.</p>
  {_h2("runtime-summary", "Runtime summary")}
  <p>Total elapsed seconds: <code>{escape(str((timing or {}).get("total_elapsed_s", "pending")))}</code>.</p>
  {_table(timing_overview)}
  {_limited_table(timing_rows, label="timing rows", artifact="run_timing.json")}
  {_h2("warnings-errors", "Warnings/errors")}
  {_table(warning_rows)}
  {_h2("pixinsight-comparison-if-available", "PixInsight comparison if available")}
  <p>No comparison artifact attached.</p>
  {_h2("known-differences-from-wbpp", "Known differences from WBPP")}
  <p>This is an independent implementation and does not claim numerical equivalence.</p>
  {_h2("clean-room-compliance-note", "Clean-room compliance note")}
  <p>No official WBPP/PJSR source code is used as implementation input.</p>
</body>
</html>
"""
    target = Path(out_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding="utf-8")
