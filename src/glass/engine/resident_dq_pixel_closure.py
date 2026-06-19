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


def _summary_counts_match(left: Mapping[str, Any], right: Mapping[str, Any]) -> dict[str, Any]:
    keys = sorted({str(key) for key in left.keys()} | {str(key) for key in right.keys()})
    mismatches: list[dict[str, Any]] = []
    for key in keys:
        left_value = _optional_int(left.get(key)) or 0
        right_value = _optional_int(right.get(key)) or 0
        if left_value != right_value:
            mismatches.append({"key": key, "left": left_value, "right": right_value})
    return {"passed": not mismatches, "mismatches": mismatches}


def _sample_closure_state(provenance_summary: Mapping[str, Any]) -> dict[str, Any]:
    closure = _mapping(provenance_summary.get("sample_accounting_closure"))
    status = str(closure.get("status") or "missing")
    input_valid = _optional_int(closure.get("input_valid_samples_before_rejection"))
    valid_after = _optional_int(closure.get("valid_samples_after_rejection"))
    rejected = _optional_int(closure.get("rejected_samples"))
    delta = None
    arithmetic_match = None
    if input_valid is not None and valid_after is not None and rejected is not None:
        delta = input_valid - valid_after - rejected
        arithmetic_match = delta == 0
    return {
        "status": status,
        "passed": status == "passed" and arithmetic_match is not False,
        "input_valid_samples_before_rejection": input_valid,
        "valid_samples_after_rejection": valid_after,
        "rejected_samples": rejected,
        "arithmetic_delta": delta,
        "arithmetic_match": arithmetic_match,
        "valid_rejection_match": closure.get("valid_rejection_match"),
    }


def build_resident_dq_pixel_closure_group(
    *,
    output: Mapping[str, Any],
    frame_mask_contract: Mapping[str, Any],
    filter_name: str | None = None,
) -> dict[str, Any]:
    """Build a resident pixel-DQ closure group from in-memory run artifacts."""

    mask_summary = _mapping(frame_mask_contract.get("summary"))
    dq_summary = _mapping(output.get("dq_summary"))
    coverage = _mapping(output.get("dq_coverage_provenance"))
    provenance = _mapping(output.get("dq_provenance_summary"))
    geometric = _mapping(output.get("geometric_warp_coverage"))
    output_contract = _mapping(output.get("resident_frame_mask_contract"))
    output_mask_summary = _mapping(output_contract.get("summary"))

    frame_mask_active = _optional_int(mask_summary.get("active_frame_count"))
    frame_mask_masked = _optional_int(mask_summary.get("masked_frame_count"))
    frame_mask_unknown = _optional_int(mask_summary.get("unknown_zero_weight_frame_count"))
    provenance_active = _optional_int(provenance.get("active_frame_count"))
    coverage_active = _optional_int(coverage.get("active_frame_count"))
    coverage_geometric_count = _optional_int(coverage.get("geometric_warp_coverage_frame_count"))
    output_geometric_count = _optional_int(geometric.get("frame_count"))
    geometric_count = coverage_geometric_count if coverage_geometric_count is not None else output_geometric_count
    output_mask_active = _optional_int(output_mask_summary.get("active_frame_count"))
    output_frame_count = _optional_int(output.get("frame_count"))
    source_terms = {str(item) for item in (provenance.get("source_terms") or coverage.get("source_terms") or [])}
    rejection = str(output.get("rejection") or "none")
    pixel_coverage_terms = {"post_rejection_coverage", "low_rejection", "high_rejection"}
    coverage_available = bool(coverage.get("available")) or bool(source_terms & pixel_coverage_terms)
    geometric_available = (
        bool(geometric.get("available"))
        or (coverage_geometric_count is not None and coverage_geometric_count > 0)
        or (output_geometric_count is not None and output_geometric_count > 0)
    )
    post_rejection_required = coverage_available or "post_rejection_coverage" in source_terms
    geometric_required = geometric_available

    summary_match = _summary_counts_match(dq_summary, _mapping(provenance.get("output_dq_summary")))
    coverage_rejected = _optional_int(coverage.get("rejected_sample_count"))
    provenance_rejected = _optional_int(provenance.get("rejected_samples"))
    sample_closure = _sample_closure_state(provenance)
    rejection_count_required = rejection != "none" and bool(source_terms & {"low_rejection", "high_rejection"})
    sample_closure_required = rejection_count_required or "post_rejection_coverage" in source_terms

    checks = [
        _check(
            "frame_mask_contract_passed",
            bool(mask_summary.get("passed")) and (frame_mask_unknown == 0),
            {
                "frame_mask_passed": mask_summary.get("passed"),
                "unknown_zero_weight_frame_count": frame_mask_unknown,
            },
        ),
        _check(
            "frame_mask_active_matches_output_link",
            output_mask_active is None or frame_mask_active == output_mask_active,
            {"frame_mask_active": frame_mask_active, "output_link_active": output_mask_active},
        ),
        _check(
            "active_frame_count_matches_provenance",
            frame_mask_active is not None
            and (provenance_active is None or frame_mask_active == provenance_active)
            and (coverage_active is None or frame_mask_active == coverage_active),
            {
                "frame_mask_active": frame_mask_active,
                "provenance_active": provenance_active,
                "coverage_active": coverage_active,
            },
        ),
        _check(
            "geometric_coverage_count_matches_active",
            (not geometric_required)
            or (
                frame_mask_active is not None
                and (coverage_geometric_count is None or coverage_geometric_count == frame_mask_active)
                and (output_geometric_count is None or output_geometric_count == frame_mask_active)
                and bool(coverage.get("geometric_frame_count_matches_active", True))
                and bool(geometric.get("frame_count_matches_active", True))
            ),
            {
                "required": geometric_required,
                "frame_mask_active": frame_mask_active,
                "coverage_geometric_count": coverage_geometric_count,
                "output_geometric_count": output_geometric_count,
                "coverage_flag": coverage.get("geometric_frame_count_matches_active"),
                "output_flag": geometric.get("frame_count_matches_active"),
            },
        ),
        _check(
            "post_rejection_coverage_present",
            (not post_rejection_required) or "post_rejection_coverage" in source_terms,
            {"required": post_rejection_required, "source_terms": sorted(source_terms)},
        ),
        _check(
            "geometric_coverage_present",
            (not geometric_required)
            or bool(geometric.get("available"))
            or "geometric_warp_coverage" in source_terms
            or (coverage_geometric_count is not None and coverage_geometric_count > 0)
            or (output_geometric_count is not None and output_geometric_count > 0),
            {
                "required": geometric_required,
                "source_terms": sorted(source_terms),
                "geometric_available": geometric.get("available"),
                "coverage_geometric_count": coverage_geometric_count,
                "output_geometric_count": output_geometric_count,
            },
        ),
        _check(
            "dq_summary_matches_provenance",
            (not provenance.get("output_dq_summary")) or bool(summary_match["passed"]),
            {"required": bool(provenance.get("output_dq_summary")), **summary_match},
        ),
        _check(
            "rejection_sample_count_recorded",
            (not rejection_count_required)
            or (coverage_rejected is not None and provenance_rejected is not None),
            {
                "required": rejection_count_required,
                "coverage_rejected_samples": coverage_rejected,
                "provenance_rejected_samples": provenance_rejected,
                "source_terms": sorted(source_terms),
            },
        ),
        _check(
            "rejection_sample_count_matches",
            (not rejection_count_required) or coverage_rejected == provenance_rejected,
            {
                "required": rejection_count_required,
                "coverage_rejected_samples": coverage_rejected,
                "provenance_rejected_samples": provenance_rejected,
            },
        ),
        _check(
            "sample_accounting_closure_passed",
            (not sample_closure_required) or bool(sample_closure["passed"]),
            {"required": sample_closure_required, **sample_closure},
        ),
        _check(
            "active_not_greater_than_input_frame_count",
            output_frame_count is None or frame_mask_active is None or frame_mask_active <= output_frame_count,
            {"frame_mask_active": frame_mask_active, "output_frame_count": output_frame_count},
        ),
    ]
    passed = all(check["passed"] for check in checks)
    return {
        "schema_version": 1,
        "artifact": "resident_dq_pixel_closure_group",
        "filter": filter_name if filter_name is not None else output.get("filter"),
        "passed": passed,
        "status": "passed" if passed else "failed",
        "frame_mask_active_frame_count": frame_mask_active,
        "frame_mask_masked_frame_count": frame_mask_masked,
        "provenance_active_frame_count": provenance_active,
        "geometric_warp_coverage_frame_count": geometric_count,
        "rejection": rejection,
        "source_terms": sorted(source_terms),
        "sample_accounting_closure": sample_closure,
        "checks": checks,
        "semantics": (
            "Frame-level resident masks define which frames are eligible to "
            "contribute. Pixel-level DQ closure verifies that resident coverage, "
            "geometric warp coverage, low/high rejection counts, and DQ summaries "
            "are consistent with that active-frame set."
        ),
    }


def validate_resident_dq_pixel_closure_group(group: Mapping[str, Any]) -> None:
    if bool(group.get("passed")):
        return
    failed = [
        str(check.get("name"))
        for check in group.get("checks") or []
        if isinstance(check, Mapping) and not check.get("passed")
    ]
    raise RuntimeError(
        "resident DQ pixel closure failed"
        + (f": {', '.join(failed)}" if failed else "")
    )


def summarize_resident_dq_pixel_closure_groups(groups: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
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
        "group_count": len(group_list),
        "passed_group_count": len(group_list) - len(failed_groups),
        "failed_group_count": len(failed_groups),
        "failed_groups": failed_groups,
        "check_counts": dict(sorted(check_counts.items())),
        "failed_check_counts": dict(sorted(failed_check_counts.items())),
        "passed": not failed_groups,
    }
