from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from glass.io.json_io import read_json, write_json
from glass.models import now_iso


RESIDENT_REGISTRATION_RUNTIME_CONTRACT_SCHEMA_VERSION = 1
TRIANGLE_RUNTIME_MODE = "similarity_cuda_triangle"
_ACTIVE_STATUSES = {"ok", "reference", "registered", "aligned"}


def _json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = read_json(path)
    return payload if isinstance(payload, dict) else {}


def _first_resident_artifact(run: Path) -> dict[str, Any]:
    payload = _json_object(run / "resident_artifacts.json")
    artifacts = payload.get("artifacts") if isinstance(payload.get("artifacts"), list) else []
    first = artifacts[0] if artifacts else {}
    return first if isinstance(first, dict) else {}


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


def _registration_rows(run: Path) -> list[dict[str, Any]]:
    payload = _json_object(run / "registration_results.json")
    rows = payload.get("results") if isinstance(payload.get("results"), list) else []
    return [row for row in rows if isinstance(row, dict)]


def _registration_source_dq_input_state(
    run: Path,
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    path = run / "registration_results.json"
    payload = _json_object(path)
    summary = (
        payload.get("source_dq_registration_input_summary")
        if isinstance(payload.get("source_dq_registration_input_summary"), dict)
        else {}
    )
    row_inputs = [
        row.get("source_dq_registration_input")
        for row in rows
        if isinstance(row.get("source_dq_registration_input"), dict)
    ]
    row_invalid = sum(int(item.get("invalid_samples") or 0) for item in row_inputs)
    row_applied = sum(int(item.get("applied_invalid_samples") or 0) for item in row_inputs)
    row_pre_visible = sum(
        int(item.get("pre_registration_catalog_visible_invalid_samples") or 0)
        for item in row_inputs
    )
    row_post_deferred = sum(
        int(item.get("post_registration_deferred_invalid_samples") or 0) for item in row_inputs
    )
    row_required_not_visible = sum(
        int(item.get("required_invalid_samples_not_visible_to_registration_catalog") or 0)
        for item in row_inputs
    )
    return {
        "path": str(path),
        "exists": bool(payload),
        "available": bool(summary.get("available")),
        "summary_present": bool(summary),
        "row_input_count": len(row_inputs),
        "registration_row_count": len(rows),
        "registration_rows_with_source_dq_input": int(
            summary.get("registration_rows_with_source_dq_input") or 0
        ),
        "registration_rows_missing_source_dq_input": int(
            summary.get("registration_rows_missing_source_dq_input") or 0
        ),
        "source_dq_row_count": int(summary.get("source_dq_row_count") or 0),
        "frames_with_invalid_samples": int(summary.get("frames_with_invalid_samples") or 0),
        "invalid_samples": int(summary.get("invalid_samples") or 0),
        "applied_invalid_samples": int(summary.get("applied_invalid_samples") or 0),
        "pre_registration_catalog_visible_invalid_samples": int(
            summary.get("pre_registration_catalog_visible_invalid_samples") or 0
        ),
        "post_registration_deferred_invalid_samples": int(
            summary.get("post_registration_deferred_invalid_samples") or 0
        ),
        "required_invalid_samples_not_visible_to_registration_catalog": int(
            summary.get("required_invalid_samples_not_visible_to_registration_catalog") or 0
        ),
        "row_invalid_samples": row_invalid,
        "row_applied_invalid_samples": row_applied,
        "row_pre_registration_catalog_visible_invalid_samples": row_pre_visible,
        "row_post_registration_deferred_invalid_samples": row_post_deferred,
        "row_required_invalid_samples_not_visible_to_registration_catalog": row_required_not_visible,
    }


def _component_elapsed(run: Path, source_key: str) -> float | None:
    payload = _json_object(run / "resident_component_timing.json")
    rows = payload.get("components") if isinstance(payload.get("components"), list) else []
    for row in rows:
        if isinstance(row, dict) and row.get("source_key") == source_key:
            return _number(row.get("elapsed_s"))
    artifact = _first_resident_artifact(run)
    timing_s = artifact.get("timing_s") if isinstance(artifact.get("timing_s"), dict) else {}
    return _number(timing_s.get(source_key))


def _status_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(Counter(str(row.get("status") or "").lower() for row in rows))


def _frame_mask_summary(run: Path) -> dict[str, Any]:
    payload = _json_object(run / "resident_frame_masks.json")
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    return summary


def _source_dq_execution_state(run: Path) -> dict[str, Any]:
    path = run / "resident_source_dq_execution.json"
    if not path.exists():
        return {
            "path": str(path),
            "exists": False,
            "passed": True,
            "status": "not_present",
            "input_invalid_samples_before_rejection": 0,
            "applied_invalid_samples": 0,
            "all_frame_input_invalid_samples_before_frame_mask": 0,
            "all_frame_applied_invalid_samples": 0,
            "required_invalid_samples_not_visible_to_registration_catalog": 0,
            "pre_registration_catalog_visible_invalid_samples": 0,
            "post_registration_deferred_invalid_samples": 0,
            "application_order_counts": {},
            "registration_catalog_visibility_counts": {},
            "failed_groups": [],
        }
    payload = _json_object(path)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    groups = payload.get("groups") if isinstance(payload.get("groups"), list) else []
    group_rows = [group for group in groups if isinstance(group, dict)]
    required_not_visible = sum(
        int(group.get("required_invalid_samples_not_visible_to_registration_catalog") or 0)
        for group in group_rows
    )
    pre_visible = sum(
        int(group.get("pre_registration_catalog_visible_invalid_samples") or 0)
        for group in group_rows
    )
    post_deferred = sum(
        int(group.get("post_registration_deferred_invalid_samples") or 0)
        for group in group_rows
    )
    application_order_counts: dict[str, int] = {}
    registration_visibility_counts: dict[str, int] = {}
    for group in group_rows:
        for key, value in dict(group.get("application_order_counts") or {}).items():
            application_order_counts[str(key)] = application_order_counts.get(str(key), 0) + int(
                value or 0
            )
        for key, value in dict(group.get("registration_catalog_visibility_counts") or {}).items():
            registration_visibility_counts[str(key)] = registration_visibility_counts.get(
                str(key), 0
            ) + int(value or 0)
    failed_groups = [
        str(group.get("filter") or "unknown") for group in group_rows if group.get("passed") is not True
    ]
    return {
        "path": str(path),
        "exists": True,
        "passed": summary.get("passed") is True and not failed_groups,
        "status": summary.get("status") or payload.get("status"),
        "input_invalid_samples_before_rejection": int(
            summary.get("input_invalid_samples_before_rejection") or 0
        ),
        "applied_invalid_samples": int(summary.get("applied_invalid_samples") or 0),
        "all_frame_input_invalid_samples_before_frame_mask": int(
            summary.get(
                "all_frame_input_invalid_samples_before_frame_mask",
                summary.get("input_invalid_samples_before_rejection"),
            )
            or 0
        ),
        "all_frame_applied_invalid_samples": int(
            summary.get("all_frame_applied_invalid_samples", summary.get("applied_invalid_samples"))
            or 0
        ),
        "required_invalid_samples_not_visible_to_registration_catalog": int(required_not_visible),
        "pre_registration_catalog_visible_invalid_samples": int(pre_visible),
        "post_registration_deferred_invalid_samples": int(post_deferred),
        "application_order_counts": dict(sorted(application_order_counts.items())),
        "registration_catalog_visibility_counts": dict(sorted(registration_visibility_counts.items())),
        "failed_groups": failed_groups,
    }


def _registration_mode(artifact: dict[str, Any], timing: dict[str, Any]) -> str:
    registration = artifact.get("resident_registration")
    if isinstance(registration, dict) and registration.get("mode") is not None:
        return str(registration.get("mode"))
    if timing.get("resident_registration") is not None:
        return str(timing.get("resident_registration"))
    return ""


def _registration_payload(artifact: dict[str, Any]) -> dict[str, Any]:
    payload = artifact.get("resident_registration")
    return payload if isinstance(payload, dict) else {}


def _runtime_value(artifact: dict[str, Any], key: str) -> Any:
    registration = _registration_payload(artifact)
    if key in registration:
        return registration.get(key)
    return artifact.get(key)


def build_resident_registration_runtime_contract(run_dir: str | Path) -> dict[str, Any]:
    """Summarize and validate the default resident registration/warp execution path."""

    run = Path(run_dir)
    timing = _json_object(run / "run_timing.json")
    artifact = _first_resident_artifact(run)
    registration = _registration_payload(artifact)
    rows = _registration_rows(run)
    frame_masks = _frame_mask_summary(run)
    source_dq = _source_dq_execution_state(run)
    registration_source_dq = _registration_source_dq_input_state(run, rows)
    mode = _registration_mode(artifact, timing).lower()
    applicable = mode == TRIANGLE_RUNTIME_MODE

    frame_count = _int_or_none(frame_masks.get("frame_count"))
    if frame_count is None and rows:
        frame_count = len(rows)
    active_frame_count = _int_or_none(frame_masks.get("active_frame_count"))
    masked_frame_count = _int_or_none(frame_masks.get("masked_frame_count"))
    status_counts = _status_counts(rows)
    active_status_count = sum(status_counts.get(status, 0) for status in _ACTIVE_STATUSES)
    reference_count = status_counts.get("reference", 0)
    excluded_count = status_counts.get("excluded", 0)
    expected_warped_frames = max(0, int(active_frame_count or 0) - max(1, reference_count))
    warp_batch_mode = _runtime_value(artifact, "triangle_warp_batch_mode")
    native_batch_required = applicable and str(warp_batch_mode or "") != "fused_matrix_deferred"
    warped_frame_count = _int_or_none(_runtime_value(artifact, "triangle_warp_batch_frame_count"))
    fallback_frame_count = _int_or_none(_runtime_value(artifact, "triangle_warp_batch_fallback_frame_count"))
    native_chunk_count = _int_or_none(_runtime_value(artifact, "triangle_warp_batch_native_chunk_count"))
    native_chunk_frames = _int_or_none(_runtime_value(artifact, "triangle_warp_batch_native_chunk_frames"))
    component_elapsed_s = _component_elapsed(run, "resident_registration_warp")
    native_total_s = _number(_runtime_value(artifact, "triangle_warp_batch_native_total_s"))
    warp_fps = (
        float(warped_frame_count) / float(component_elapsed_s)
        if warped_frame_count is not None and component_elapsed_s and component_elapsed_s > 0
        else None
    )
    coverage_raw = _runtime_value(artifact, "warp_coverage")
    coverage = coverage_raw if isinstance(coverage_raw, dict) else {}
    coverage_required = applicable and bool(coverage) and coverage.get("available") is not False
    source_dq_positive = int(source_dq["input_invalid_samples_before_rejection"]) > 0
    registration_matches_active_source_dq = (
        registration_source_dq["invalid_samples"]
        == source_dq["input_invalid_samples_before_rejection"]
        and registration_source_dq["applied_invalid_samples"] == source_dq["applied_invalid_samples"]
    )
    registration_matches_all_frame_source_dq = (
        registration_source_dq["invalid_samples"]
        == source_dq["all_frame_input_invalid_samples_before_frame_mask"]
        and registration_source_dq["applied_invalid_samples"]
        == source_dq["all_frame_applied_invalid_samples"]
    )
    coverage_frame_count = _int_or_none(coverage.get("frame_count"))
    coverage_warped_frame_count = _int_or_none(coverage.get("warped_frame_count"))

    checks = [
        _check(
            "resident_artifacts_present",
            bool(artifact),
            {"path": str(run / "resident_artifacts.json"), "exists": bool(artifact)},
        ),
        _check(
            "registration_results_present",
            bool(rows) or not applicable,
            {"path": str(run / "registration_results.json"), "row_count": len(rows), "applicable": applicable},
        ),
        _check(
            "resident_frame_masks_present",
            frame_masks.get("passed") is True or not applicable,
            {
                "path": str(run / "resident_frame_masks.json"),
                "passed": frame_masks.get("passed"),
                "frame_count": frame_count,
                "active_frame_count": active_frame_count,
                "masked_frame_count": masked_frame_count,
                "applicable": applicable,
            },
        ),
        _check(
            "triangle_runtime_applicable_or_not_required",
            applicable or mode not in {"", TRIANGLE_RUNTIME_MODE},
            {"registration_mode": mode, "required_mode": TRIANGLE_RUNTIME_MODE},
        ),
        _check(
            "registration_rows_match_frame_masks",
            not applicable or (frame_count is not None and len(rows) == frame_count),
            {"registration_row_count": len(rows), "frame_mask_frame_count": frame_count},
        ),
        _check(
            "registration_active_count_matches_frame_masks",
            not applicable or (active_frame_count is not None and active_status_count == active_frame_count),
            {
                "active_status_count": active_status_count,
                "active_frame_count": active_frame_count,
                "status_counts": status_counts,
            },
        ),
        _check(
            "registration_masked_count_matches_frame_masks",
            not applicable or (masked_frame_count is not None and excluded_count == masked_frame_count),
            {
                "excluded_status_count": excluded_count,
                "masked_frame_count": masked_frame_count,
                "status_counts": status_counts,
            },
        ),
        _check(
            "triangle_catalog_batch_enabled",
            not applicable or _runtime_value(artifact, "triangle_catalog_batch") is True,
            {"triangle_catalog_batch": _runtime_value(artifact, "triangle_catalog_batch")},
        ),
        _check(
            "triangle_descriptor_generation_batch_enabled",
            not applicable or _runtime_value(artifact, "triangle_descriptor_generation_batch") is True,
            {
                "triangle_descriptor_generation_batch": _runtime_value(
                    artifact, "triangle_descriptor_generation_batch"
                )
            },
        ),
        _check(
            "triangle_descriptor_fit_batch_enabled",
            not applicable or _runtime_value(artifact, "triangle_descriptor_fit_batch") is True,
            {"triangle_descriptor_fit_batch": _runtime_value(artifact, "triangle_descriptor_fit_batch")},
        ),
        _check(
            "triangle_warp_batch_enabled",
            not native_batch_required or _runtime_value(artifact, "triangle_warp_batch") is True,
            {
                "triangle_warp_batch": _runtime_value(artifact, "triangle_warp_batch"),
                "triangle_warp_batch_mode": warp_batch_mode,
                "triangle_warp_batch_dispatch": _runtime_value(
                    artifact, "triangle_warp_batch_dispatch"
                ),
                "native_batch_required": native_batch_required,
            },
        ),
        _check(
            "triangle_warp_batch_has_no_fallback",
            not native_batch_required or fallback_frame_count == 0,
            {"fallback_frame_count": fallback_frame_count, "native_batch_required": native_batch_required},
        ),
        _check(
            "triangle_warp_batch_frame_count_closes",
            not native_batch_required or warped_frame_count == expected_warped_frames,
            {
                "warped_frame_count": warped_frame_count,
                "expected_warped_frames": expected_warped_frames,
                "active_frame_count": active_frame_count,
                "reference_count": reference_count,
                "native_batch_required": native_batch_required,
            },
        ),
        _check(
            "triangle_warp_native_chunks_cover_frames",
            not native_batch_required
            or (
                native_chunk_count is not None
                and native_chunk_frames is not None
                and warped_frame_count is not None
                and native_chunk_count > 0
                and native_chunk_frames > 0
                and native_chunk_count * native_chunk_frames >= warped_frame_count
            ),
            {
                "native_chunk_count": native_chunk_count,
                "native_chunk_frames": native_chunk_frames,
                "warped_frame_count": warped_frame_count,
                "native_batch_required": native_batch_required,
            },
        ),
        _check(
            "warp_coverage_closes_active_frames",
            not coverage_required
            or (
                coverage.get("available") is True
                and coverage_frame_count == active_frame_count
                and coverage_warped_frame_count == warped_frame_count
            ),
            {
                "coverage_available": coverage.get("available"),
                "coverage_frame_count": coverage_frame_count,
                "active_frame_count": active_frame_count,
                "coverage_warped_frame_count": coverage_warped_frame_count,
                "warped_frame_count": warped_frame_count,
                "coverage_required": coverage_required,
            },
        ),
        _check(
            "registration_warp_component_timing_present",
            not applicable or component_elapsed_s is not None,
            {
                "component_elapsed_s": component_elapsed_s,
                "native_total_s": native_total_s,
                "warp_frames_per_s": warp_fps,
            },
        ),
        _check(
            "source_dq_execution_passed_if_present",
            not source_dq["exists"] or source_dq["passed"] is True,
            {
                "exists": source_dq["exists"],
                "status": source_dq["status"],
                "passed": source_dq["passed"],
                "failed_groups": source_dq["failed_groups"],
            },
        ),
        _check(
            "source_dq_invalid_samples_applied_if_present",
            not source_dq["exists"]
            or source_dq["applied_invalid_samples"]
            == source_dq["input_invalid_samples_before_rejection"],
            {
                "exists": source_dq["exists"],
                "input_invalid_samples_before_rejection": source_dq[
                    "input_invalid_samples_before_rejection"
                ],
                "applied_invalid_samples": source_dq["applied_invalid_samples"],
            },
        ),
        _check(
            "source_dq_registration_visibility_closes",
            not applicable
            or not source_dq_positive
            or source_dq["required_invalid_samples_not_visible_to_registration_catalog"] == 0,
            {
                "applicable": applicable,
                "source_dq_positive": source_dq_positive,
                "required_invalid_samples_not_visible_to_registration_catalog": source_dq[
                    "required_invalid_samples_not_visible_to_registration_catalog"
                ],
                "pre_registration_catalog_visible_invalid_samples": source_dq[
                    "pre_registration_catalog_visible_invalid_samples"
                ],
                "post_registration_deferred_invalid_samples": source_dq[
                    "post_registration_deferred_invalid_samples"
                ],
                "application_order_counts": source_dq["application_order_counts"],
                "registration_catalog_visibility_counts": source_dq[
                    "registration_catalog_visibility_counts"
                ],
            },
            "Non-inline source-DQ invalid samples must be visible before resident registration catalogs are built.",
        ),
        _check(
            "registration_results_carry_source_dq_input_if_positive",
            not applicable
            or not source_dq_positive
            or (
                registration_source_dq["available"]
                and registration_source_dq["row_input_count"] == len(rows)
                and registration_source_dq["registration_rows_missing_source_dq_input"] == 0
            ),
            {
                "applicable": applicable,
                "source_dq_positive": source_dq_positive,
                "available": registration_source_dq["available"],
                "row_input_count": registration_source_dq["row_input_count"],
                "registration_row_count": len(rows),
                "registration_rows_with_source_dq_input": registration_source_dq[
                    "registration_rows_with_source_dq_input"
                ],
                "registration_rows_missing_source_dq_input": registration_source_dq[
                    "registration_rows_missing_source_dq_input"
                ],
            },
            "Positive source-DQ resident registration runs must expose per-frame catalog-input evidence.",
        ),
        _check(
            "registration_source_dq_input_matches_execution",
            not applicable
            or not source_dq_positive
            or (
                (registration_matches_active_source_dq or registration_matches_all_frame_source_dq)
                and registration_source_dq["pre_registration_catalog_visible_invalid_samples"]
                == source_dq["pre_registration_catalog_visible_invalid_samples"]
                and registration_source_dq["post_registration_deferred_invalid_samples"]
                == source_dq["post_registration_deferred_invalid_samples"]
                and registration_source_dq[
                    "required_invalid_samples_not_visible_to_registration_catalog"
                ]
                == source_dq["required_invalid_samples_not_visible_to_registration_catalog"]
                and registration_source_dq["row_invalid_samples"]
                == registration_source_dq["invalid_samples"]
            ),
            {
                "applicable": applicable,
                "source_dq_positive": source_dq_positive,
                "source_dq_input_invalid_samples_before_rejection": source_dq[
                    "input_invalid_samples_before_rejection"
                ],
                "source_dq_applied_invalid_samples": source_dq["applied_invalid_samples"],
                "source_dq_all_frame_input_invalid_samples_before_frame_mask": source_dq[
                    "all_frame_input_invalid_samples_before_frame_mask"
                ],
                "source_dq_all_frame_applied_invalid_samples": source_dq[
                    "all_frame_applied_invalid_samples"
                ],
                "source_dq_pre_registration_catalog_visible_invalid_samples": source_dq[
                    "pre_registration_catalog_visible_invalid_samples"
                ],
                "source_dq_post_registration_deferred_invalid_samples": source_dq[
                    "post_registration_deferred_invalid_samples"
                ],
                "source_dq_required_invalid_samples_not_visible_to_registration_catalog": source_dq[
                    "required_invalid_samples_not_visible_to_registration_catalog"
                ],
                "registration_matches_active_source_dq": registration_matches_active_source_dq,
                "registration_matches_all_frame_source_dq": registration_matches_all_frame_source_dq,
                "registration_invalid_samples": registration_source_dq["invalid_samples"],
                "registration_applied_invalid_samples": registration_source_dq[
                    "applied_invalid_samples"
                ],
                "registration_pre_registration_catalog_visible_invalid_samples": (
                    registration_source_dq[
                        "pre_registration_catalog_visible_invalid_samples"
                    ]
                ),
                "registration_post_registration_deferred_invalid_samples": (
                    registration_source_dq["post_registration_deferred_invalid_samples"]
                ),
                "registration_required_invalid_samples_not_visible_to_registration_catalog": (
                    registration_source_dq[
                        "required_invalid_samples_not_visible_to_registration_catalog"
                    ]
                ),
                "registration_row_invalid_samples": registration_source_dq["row_invalid_samples"],
            },
            "Registration artifact source-DQ input totals must match resident source-DQ execution.",
        ),
    ]
    failed_checks = [str(check["name"]) for check in checks if not check["passed"]]
    passed = not failed_checks
    return {
        "schema_version": RESIDENT_REGISTRATION_RUNTIME_CONTRACT_SCHEMA_VERSION,
        "artifact_type": "resident_registration_runtime_contract",
        "created_at": now_iso(),
        "run": str(run),
        "status": "passed" if passed else "failed",
        "passed": passed,
        "applicable": applicable,
        "summary": {
            "registration_mode": mode,
            "frame_count": frame_count,
            "registration_row_count": len(rows),
            "active_frame_count": active_frame_count,
            "masked_frame_count": masked_frame_count,
            "registration_status_counts": status_counts,
            "expected_warped_frame_count": expected_warped_frames if applicable else None,
            "triangle_native_batch_required": native_batch_required,
            "warp_coverage_required": coverage_required,
            "source_dq_exists": source_dq["exists"],
            "source_dq_positive": source_dq_positive,
            "source_dq_input_invalid_samples_before_rejection": source_dq[
                "input_invalid_samples_before_rejection"
            ],
            "source_dq_applied_invalid_samples": source_dq["applied_invalid_samples"],
            "source_dq_all_frame_input_invalid_samples_before_frame_mask": source_dq[
                "all_frame_input_invalid_samples_before_frame_mask"
            ],
            "source_dq_all_frame_applied_invalid_samples": source_dq[
                "all_frame_applied_invalid_samples"
            ],
            "source_dq_pre_registration_catalog_visible_invalid_samples": source_dq[
                "pre_registration_catalog_visible_invalid_samples"
            ],
            "source_dq_post_registration_deferred_invalid_samples": source_dq[
                "post_registration_deferred_invalid_samples"
            ],
            "source_dq_required_invalid_samples_not_visible_to_registration_catalog": source_dq[
                "required_invalid_samples_not_visible_to_registration_catalog"
            ],
            "registration_source_dq_input_available": registration_source_dq["available"],
            "registration_source_dq_input_row_count": registration_source_dq["row_input_count"],
            "registration_source_dq_input_invalid_samples": registration_source_dq[
                "invalid_samples"
            ],
            "registration_source_dq_input_applied_invalid_samples": registration_source_dq[
                "applied_invalid_samples"
            ],
            "registration_source_dq_input_pre_registration_catalog_visible_invalid_samples": (
                registration_source_dq["pre_registration_catalog_visible_invalid_samples"]
            ),
            "registration_source_dq_input_required_invalid_samples_not_visible_to_registration_catalog": (
                registration_source_dq[
                    "required_invalid_samples_not_visible_to_registration_catalog"
                ]
            ),
            "triangle_warp_batch_frame_count": warped_frame_count,
            "triangle_warp_batch_fallback_frame_count": fallback_frame_count,
            "triangle_warp_batch_native_chunk_count": native_chunk_count,
            "triangle_warp_batch_native_chunk_frames": native_chunk_frames,
            "registration_warp_component_elapsed_s": component_elapsed_s,
            "triangle_warp_batch_native_total_s": native_total_s,
            "warp_frames_per_s": warp_fps,
        },
        "checks": checks,
        "failed_checks": failed_checks,
        "sources": {
            "resident_artifacts": str(run / "resident_artifacts.json"),
            "resident_registration_object_present": bool(registration),
            "registration_results": str(run / "registration_results.json"),
            "registration_source_dq_input_summary_present": registration_source_dq[
                "summary_present"
            ],
            "resident_frame_masks": str(run / "resident_frame_masks.json"),
            "resident_component_timing": str(run / "resident_component_timing.json"),
            "resident_source_dq_execution": source_dq["path"],
        },
    }


def write_resident_registration_runtime_contract(run_dir: str | Path) -> Path:
    run = Path(run_dir)
    path = run / "resident_registration_runtime_contract.json"
    write_json(path, build_resident_registration_runtime_contract(run))
    return path
