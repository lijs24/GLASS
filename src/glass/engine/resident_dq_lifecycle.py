from __future__ import annotations

from collections import Counter
from typing import Any, Iterable, Mapping


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(round(float(value)))
    except (TypeError, ValueError, OverflowError):
        return None


def _check(name: str, passed: bool, details: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return {
        "name": name,
        "passed": bool(passed),
        "details": dict(details or {}),
    }


def build_resident_dq_lifecycle_group(
    *,
    source_dq_execution_group: Mapping[str, Any],
    frame_mask_group: Mapping[str, Any],
    dq_pixel_closure_group: Mapping[str, Any],
    filter_name: str | None = None,
) -> dict[str, Any]:
    """Tie resident source-DQ, frame admission, and pixel-DQ closure together."""

    source = _mapping(source_dq_execution_group)
    frame_mask_summary = _mapping(frame_mask_group.get("summary"))
    closure = _mapping(dq_pixel_closure_group)
    source_frame_count = _optional_int(source.get("frame_count"))
    source_active = _optional_int(source.get("active_frame_count"))
    mask_frame_count = _optional_int(frame_mask_summary.get("frame_count"))
    mask_active = _optional_int(frame_mask_summary.get("active_frame_count"))
    mask_masked = _optional_int(frame_mask_summary.get("masked_frame_count"))
    closure_active = _optional_int(closure.get("frame_mask_active_frame_count"))
    closure_masked = _optional_int(closure.get("frame_mask_masked_frame_count"))
    source_input_samples = _optional_int(source.get("input_samples"))
    expected_source_samples = (
        None
        if source_active is None
        or _optional_int(source.get("height")) is None
        or _optional_int(source.get("width")) is None
        else source_active * int(source.get("height")) * int(source.get("width"))
    )

    checks = [
        _check(
            "source_dq_execution_passed",
            bool(source.get("passed")),
            {"status": source.get("status")},
        ),
        _check(
            "frame_mask_contract_passed",
            bool(frame_mask_summary.get("passed")),
            {
                "unknown_zero_weight_frame_count": frame_mask_summary.get(
                    "unknown_zero_weight_frame_count"
                )
            },
        ),
        _check(
            "dq_pixel_closure_passed",
            bool(closure.get("passed")),
            {"status": closure.get("status")},
        ),
        _check(
            "source_frame_count_matches_frame_mask",
            source_frame_count is not None
            and mask_frame_count is not None
            and source_frame_count == mask_frame_count,
            {"source_frame_count": source_frame_count, "frame_mask_frame_count": mask_frame_count},
        ),
        _check(
            "source_active_matches_frame_mask",
            source_active is not None and mask_active is not None and source_active == mask_active,
            {"source_active_frame_count": source_active, "frame_mask_active_frame_count": mask_active},
        ),
        _check(
            "frame_mask_active_matches_pixel_closure",
            mask_active is not None and closure_active is not None and mask_active == closure_active,
            {"frame_mask_active_frame_count": mask_active, "pixel_closure_active_frame_count": closure_active},
        ),
        _check(
            "frame_mask_masked_matches_pixel_closure",
            mask_masked is not None and closure_masked is not None and mask_masked == closure_masked,
            {"frame_mask_masked_frame_count": mask_masked, "pixel_closure_masked_frame_count": closure_masked},
        ),
        _check(
            "source_input_samples_use_active_frames",
            source_input_samples is not None
            and expected_source_samples is not None
            and source_input_samples == expected_source_samples,
            {
                "source_input_samples": source_input_samples,
                "expected_source_input_samples": expected_source_samples,
                "source_active_frame_count": source_active,
            },
        ),
        _check(
            "source_dq_stays_resident_streaming",
            source.get("execution_route") == "resident_in_memory_mask_streaming"
            and not bool(source.get("materializes_calibrated_dq_cache")),
            {
                "execution_route": source.get("execution_route"),
                "materializes_calibrated_dq_cache": source.get("materializes_calibrated_dq_cache"),
            },
        ),
    ]
    passed = all(check["passed"] for check in checks)
    return {
        "schema_version": 1,
        "artifact": "resident_dq_lifecycle_group",
        "filter": filter_name if filter_name is not None else source.get("filter"),
        "status": "passed" if passed else "failed",
        "passed": passed,
        "frame_count": source_frame_count,
        "active_frame_count": mask_active,
        "masked_frame_count": mask_masked,
        "source_input_samples": source_input_samples,
        "source_input_invalid_samples_before_rejection": source.get(
            "input_invalid_samples_before_rejection"
        ),
        "all_frame_input_invalid_samples_before_frame_mask": source.get(
            "all_frame_input_invalid_samples_before_frame_mask"
        ),
        "checks": checks,
        "semantics": (
            "Resident DQ lifecycle closes the contract between source-DQ "
            "application, frame-level admission, and output pixel-DQ/coverage "
            "closure. Source-DQ integration sample counts are expressed over the "
            "same active frame set that reaches integration, while all-frame "
            "source-DQ counts remain available for registration/catalog auditing."
        ),
    }


def validate_resident_dq_lifecycle_group(group: Mapping[str, Any]) -> None:
    if bool(group.get("passed")):
        return
    failed = [
        str(check.get("name"))
        for check in group.get("checks") or []
        if isinstance(check, Mapping) and not check.get("passed")
    ]
    raise RuntimeError(
        "resident DQ lifecycle failed"
        + (f": {', '.join(failed)}" if failed else "")
    )


def summarize_resident_dq_lifecycle_groups(groups: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    group_list = list(groups)
    failed_groups = [
        str(group.get("filter") or index)
        for index, group in enumerate(group_list)
        if not group.get("passed")
    ]
    check_counts: Counter[str] = Counter()
    failed_check_counts: Counter[str] = Counter()
    for group in group_list:
        for check in group.get("checks") or []:
            if not isinstance(check, Mapping):
                continue
            name = str(check.get("name") or "unknown")
            check_counts[name] += 1
            if not check.get("passed"):
                failed_check_counts[name] += 1
    return {
        "schema_version": 1,
        "passed": not failed_groups,
        "status": "passed" if not failed_groups else "failed",
        "group_count": len(group_list),
        "passed_group_count": len(group_list) - len(failed_groups),
        "failed_group_count": len(failed_groups),
        "failed_groups": failed_groups,
        "frame_count": int(sum(int(group.get("frame_count") or 0) for group in group_list)),
        "active_frame_count": int(sum(int(group.get("active_frame_count") or 0) for group in group_list)),
        "masked_frame_count": int(sum(int(group.get("masked_frame_count") or 0) for group in group_list)),
        "check_counts": dict(sorted(check_counts.items())),
        "failed_check_counts": dict(sorted(failed_check_counts.items())),
    }
