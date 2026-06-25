from __future__ import annotations

from collections import Counter
from typing import Any, Iterable, Mapping, Sequence

import numpy as np


_ZERO_OBSERVATION_STATUSES = {"zero_weight", "skipped_zero_weight"}
_REGISTRATION_REJECT_STATUSES = {"excluded", "failed", "rejected", "missing"}
_LOCAL_NORM_REJECT_STATUSES = {"empty"}
_WEIGHTING_REJECT_STATUSES = {"empty"}


def _field(source: Any, name: str, default: Any = None) -> Any:
    if isinstance(source, Mapping):
        return source.get(name, default)
    return getattr(source, name, default)


def _append_unique(values: list[str], value: str) -> None:
    if value and value not in values:
        values.append(value)


def _float_or_nan(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _weights_match(left: float, right: float) -> bool:
    left_finite = bool(np.isfinite(left))
    right_finite = bool(np.isfinite(right))
    if left_finite != right_finite:
        return False
    if not left_finite and not right_finite:
        return True
    return abs(float(left) - float(right)) <= 1.0e-6


def _by_frame(rows: Iterable[Any] | Mapping[str, Any] | None) -> dict[str, Any]:
    if rows is None:
        return {}
    if isinstance(rows, Mapping):
        return {str(key): value for key, value in rows.items()}
    result: dict[str, Any] = {}
    for row in rows:
        frame_id = _field(row, "frame_id")
        if frame_id is not None:
            result[str(frame_id)] = row
    return result


def build_resident_frame_mask_contract(
    *,
    frame_ids: Sequence[str],
    frame_weights: Sequence[float],
    registration_results: Iterable[Any] | Mapping[str, Any] | None = None,
    registration_quality_decisions: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None = None,
    manual_excluded_frame_ids: Iterable[str] | None = None,
    frame_weight_by_id: Mapping[str, float] | None = None,
    weighting_frame_results: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None = None,
    local_norm_frame_results: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None = None,
    filter_name: str | None = None,
    registration_mode: str | None = None,
    integration_dispatch: str | None = None,
) -> dict[str, Any]:
    """Build the resident frame-level DQ/mask admission contract.

    The contract is intentionally frame-level. Pixel-level invalid warp
    footprints and rejection masks are still represented by output DQ/count maps;
    this artifact ensures that a frame with zero integration weight is never an
    anonymous drop before those pixel maps exist.
    """

    if len(frame_ids) != len(frame_weights):
        raise ValueError("frame_ids and frame_weights must have the same length")

    registration_by_id = _by_frame(registration_results)
    quality_by_id = _by_frame(registration_quality_decisions)
    weighting_by_id = _by_frame(weighting_frame_results)
    local_norm_by_id = _by_frame(local_norm_frame_results)
    manual_excluded = {str(frame_id) for frame_id in (manual_excluded_frame_ids or [])}
    weight_by_id = {str(key): _float_or_nan(value) for key, value in (frame_weight_by_id or {}).items()}
    weight_alignment_checked = frame_weight_by_id is not None

    rows: list[dict[str, Any]] = []
    unknown_zero_weight_frame_ids: list[str] = []
    unknown_zero_weight_frame_indices: list[int] = []
    masked_frame_ids: list[str] = []
    masked_frame_indices: list[int] = []
    active_frame_ids: list[str] = []
    active_frame_indices: list[int] = []
    weight_mismatch_frame_ids: list[str] = []
    weight_mismatch_frame_indices: list[int] = []
    weight_missing_frame_ids: list[str] = []
    weight_missing_frame_indices: list[int] = []
    category_counts: Counter[str] = Counter()

    for frame_index, (frame_id_raw, weight_raw) in enumerate(zip(frame_ids, frame_weights, strict=True)):
        frame_id = str(frame_id_raw)
        weight = _float_or_nan(weight_raw)
        map_weight = weight_by_id.get(frame_id)
        weight_map_present = frame_id in weight_by_id
        weight_matches_map = None
        if weight_alignment_checked:
            if not weight_map_present or map_weight is None:
                weight_missing_frame_ids.append(frame_id)
                weight_missing_frame_indices.append(frame_index)
                weight_matches_map = False
            else:
                weight_matches_map = _weights_match(weight, map_weight)
                if not weight_matches_map:
                    weight_mismatch_frame_ids.append(frame_id)
                    weight_mismatch_frame_indices.append(frame_index)
        active = bool(np.isfinite(weight) and weight > 0.0)
        categories: list[str] = []
        reasons: list[str] = []
        observed: list[str] = []

        registration = registration_by_id.get(frame_id)
        quality = quality_by_id.get(frame_id)
        weighting = weighting_by_id.get(frame_id)
        local_norm = local_norm_by_id.get(frame_id)

        registration_status = str(_field(registration, "status", "missing"))
        quality_status = str(_field(quality, "decision_status", "missing"))
        quality_final_status = str(_field(quality, "final_status", "missing"))
        weighting_status = str(_field(weighting, "status", "missing"))
        local_norm_status = str(_field(local_norm, "status", "missing"))

        if frame_id in manual_excluded:
            _append_unique(categories, "manual_exclude")
            _append_unique(reasons, "manual_exclude")

        if quality_status == "rejected" or quality_final_status == "excluded":
            _append_unique(categories, "registration_quality")
            quality_reasons = _field(quality, "reasons", [])
            if isinstance(quality_reasons, list) and quality_reasons:
                for reason in quality_reasons:
                    _append_unique(reasons, f"registration_quality:{reason}")
            else:
                _append_unique(reasons, "registration_quality:rejected")

        if registration_status in _REGISTRATION_REJECT_STATUSES:
            _append_unique(categories, "registration")
            _append_unique(reasons, f"registration_status:{registration_status}")

        if local_norm_status in _LOCAL_NORM_REJECT_STATUSES:
            _append_unique(categories, "local_normalization")
            _append_unique(reasons, f"local_normalization_status:{local_norm_status}")
        elif local_norm_status in _ZERO_OBSERVATION_STATUSES:
            _append_unique(observed, f"local_normalization_status:{local_norm_status}")

        if weighting_status in _WEIGHTING_REJECT_STATUSES:
            _append_unique(categories, "weighting")
            _append_unique(reasons, f"weighting_status:{weighting_status}")
        elif weighting_status in _ZERO_OBSERVATION_STATUSES:
            _append_unique(observed, f"weighting_status:{weighting_status}")

        for multiplier_key, category in (
            ("agreement_weight_multiplier", "triangle_agreement"),
            ("registration_motion_weight_multiplier", "registration_motion"),
            ("frame_weight_proposal_multiplier", "frame_weight_proposal"),
        ):
            multiplier = _field(weighting, multiplier_key)
            if multiplier is None:
                continue
            multiplier_value = _float_or_nan(multiplier)
            if np.isfinite(multiplier_value) and multiplier_value <= 0.0:
                _append_unique(categories, category)
                _append_unique(reasons, f"{multiplier_key}:0")

        if not np.isfinite(weight):
            _append_unique(categories, "invalid_weight")
            _append_unique(reasons, "integration_weight_nonfinite")

        if active:
            active_frame_ids.append(frame_id)
            active_frame_indices.append(frame_index)
            mask_status = "active"
            auditable = True
        else:
            masked_frame_ids.append(frame_id)
            masked_frame_indices.append(frame_index)
            mask_status = "masked"
            auditable = bool(reasons)
            if not auditable:
                unknown_zero_weight_frame_ids.append(frame_id)
                unknown_zero_weight_frame_indices.append(frame_index)

        for category in categories:
            category_counts[category] += 1

        rows.append(
            {
                "frame_index": frame_index,
                "frame_id": frame_id,
                "filter": filter_name,
                "integration_weight": None if not np.isfinite(weight) else float(weight),
                "frame_weight_map_value": (
                    None
                    if not weight_alignment_checked or map_weight is None or not np.isfinite(map_weight)
                    else float(map_weight)
                ),
                "frame_weight_map_present": weight_map_present if weight_alignment_checked else None,
                "frame_weight_matches_map": weight_matches_map,
                "mask_status": mask_status,
                "auditable": auditable,
                "mask_categories": categories,
                "mask_reasons": reasons,
                "observed_zero_weight_statuses": observed,
                "manual_excluded": frame_id in manual_excluded,
                "registration_status": registration_status,
                "registration_quality_status": quality_status,
                "registration_quality_final_status": quality_final_status,
                "weighting_status": weighting_status,
                "local_norm_status": local_norm_status,
            }
        )

    summary = {
        "frame_count": len(rows),
        "active_frame_count": len(active_frame_ids),
        "masked_frame_count": len(masked_frame_ids),
        "unknown_zero_weight_frame_count": len(unknown_zero_weight_frame_ids),
        "active_frame_ids": active_frame_ids,
        "active_frame_indices": active_frame_indices,
        "masked_frame_ids": masked_frame_ids,
        "masked_frame_indices": masked_frame_indices,
        "unknown_zero_weight_frame_ids": unknown_zero_weight_frame_ids,
        "unknown_zero_weight_frame_indices": unknown_zero_weight_frame_indices,
        "frame_index_alignment_contract": {
            "checked": weight_alignment_checked,
            "index_origin": "resident_stack_frame_index",
            "frame_id_order": "light_group_order",
            "frame_weight_order": "resident_stack_frame_index",
            "frame_weight_by_id_source": "resident_cuda_frame_weights_map"
            if weight_alignment_checked
            else "not_provided",
            "weight_mismatch_frame_count": len(weight_mismatch_frame_ids),
            "weight_mismatch_frame_ids": weight_mismatch_frame_ids,
            "weight_mismatch_frame_indices": weight_mismatch_frame_indices,
            "weight_missing_frame_count": len(weight_missing_frame_ids),
            "weight_missing_frame_ids": weight_missing_frame_ids,
            "weight_missing_frame_indices": weight_missing_frame_indices,
            "passed": not weight_mismatch_frame_ids and not weight_missing_frame_ids,
        },
        "mask_category_counts": dict(sorted(category_counts.items())),
        "status_counts": dict(Counter(row["mask_status"] for row in rows)),
        "passed": not unknown_zero_weight_frame_ids
        and not weight_mismatch_frame_ids
        and not weight_missing_frame_ids,
    }
    return {
        "schema_version": 1,
        "artifact": "resident_frame_mask_contract_group",
        "filter": filter_name,
        "registration_mode": registration_mode,
        "integration_dispatch": integration_dispatch,
        "summary": summary,
        "rows": rows,
        "semantics": (
            "Frame-level resident mask admission runs after registration, weighting, "
            "and local normalization but before integration. Any frame with zero or "
            "non-finite integration weight must have a structured reason. Pixel-level "
            "warp footprint and low/high rejection masks remain represented by DQ and "
            "count maps in integration outputs."
        ),
    }


def validate_resident_frame_mask_contract(contract: Mapping[str, Any]) -> None:
    summary = contract.get("summary") if isinstance(contract.get("summary"), Mapping) else {}
    unknown = summary.get("unknown_zero_weight_frame_ids") or []
    if unknown:
        joined = ", ".join(str(frame_id) for frame_id in unknown)
        raise RuntimeError(f"resident frame mask contract found unaudited zero-weight frames: {joined}")
    alignment = summary.get("frame_index_alignment_contract")
    if isinstance(alignment, Mapping) and not alignment.get("passed", True):
        mismatch = alignment.get("weight_mismatch_frame_ids") or []
        missing = alignment.get("weight_missing_frame_ids") or []
        details = []
        if mismatch:
            details.append("mismatched weights for " + ", ".join(str(frame_id) for frame_id in mismatch))
        if missing:
            details.append("missing weight-map entries for " + ", ".join(str(frame_id) for frame_id in missing))
        message = "; ".join(details) if details else "frame-weight index alignment failed"
        raise RuntimeError(f"resident frame mask contract frame-index alignment failed: {message}")


def summarize_resident_frame_mask_contracts(groups: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    group_list = list(groups)
    category_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    active_frame_ids: list[str] = []
    masked_frame_ids: list[str] = []
    unknown_zero_weight_frame_ids: list[str] = []
    unknown_zero_weight_frame_indices: list[int] = []
    weight_mismatch_frame_ids: list[str] = []
    weight_mismatch_frame_indices: list[int] = []
    weight_missing_frame_ids: list[str] = []
    weight_missing_frame_indices: list[int] = []
    alignment_checked = False
    frame_count = 0
    for group in group_list:
        summary = group.get("summary") if isinstance(group.get("summary"), Mapping) else {}
        frame_count += int(summary.get("frame_count") or 0)
        active_frame_ids.extend(str(value) for value in summary.get("active_frame_ids") or [])
        masked_frame_ids.extend(str(value) for value in summary.get("masked_frame_ids") or [])
        unknown_zero_weight_frame_ids.extend(
            str(value) for value in summary.get("unknown_zero_weight_frame_ids") or []
        )
        unknown_zero_weight_frame_indices.extend(
            int(value) for value in summary.get("unknown_zero_weight_frame_indices") or []
        )
        alignment = summary.get("frame_index_alignment_contract")
        if isinstance(alignment, Mapping):
            alignment_checked = alignment_checked or bool(alignment.get("checked"))
            weight_mismatch_frame_ids.extend(
                str(value) for value in alignment.get("weight_mismatch_frame_ids") or []
            )
            weight_mismatch_frame_indices.extend(
                int(value) for value in alignment.get("weight_mismatch_frame_indices") or []
            )
            weight_missing_frame_ids.extend(
                str(value) for value in alignment.get("weight_missing_frame_ids") or []
            )
            weight_missing_frame_indices.extend(
                int(value) for value in alignment.get("weight_missing_frame_indices") or []
            )
        category_counts.update(summary.get("mask_category_counts") or {})
        status_counts.update(summary.get("status_counts") or {})
    return {
        "group_count": len(group_list),
        "frame_count": frame_count,
        "active_frame_count": len(active_frame_ids),
        "masked_frame_count": len(masked_frame_ids),
        "unknown_zero_weight_frame_count": len(unknown_zero_weight_frame_ids),
        "active_frame_ids": active_frame_ids,
        "masked_frame_ids": masked_frame_ids,
        "unknown_zero_weight_frame_ids": unknown_zero_weight_frame_ids,
        "unknown_zero_weight_frame_indices": unknown_zero_weight_frame_indices,
        "frame_index_alignment_contract": {
            "checked": alignment_checked,
            "index_origin": "resident_stack_frame_index",
            "frame_id_order": "light_group_order",
            "frame_weight_order": "resident_stack_frame_index",
            "frame_weight_by_id_source": "resident_cuda_frame_weights_map"
            if alignment_checked
            else "not_provided",
            "weight_mismatch_frame_count": len(weight_mismatch_frame_ids),
            "weight_mismatch_frame_ids": weight_mismatch_frame_ids,
            "weight_mismatch_frame_indices": weight_mismatch_frame_indices,
            "weight_missing_frame_count": len(weight_missing_frame_ids),
            "weight_missing_frame_ids": weight_missing_frame_ids,
            "weight_missing_frame_indices": weight_missing_frame_indices,
            "passed": not weight_mismatch_frame_ids and not weight_missing_frame_ids,
        },
        "mask_category_counts": dict(sorted(category_counts.items())),
        "status_counts": dict(sorted(status_counts.items())),
        "passed": not unknown_zero_weight_frame_ids
        and not weight_mismatch_frame_ids
        and not weight_missing_frame_ids,
    }
