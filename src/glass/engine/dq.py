from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from glass.engine.contracts import DQFlag, DQMask
from glass.io.fits_io import FitsTileWriter


def dq_header(stage: str, frame_id: str | None = None) -> dict[str, Any]:
    header: dict[str, Any] = {"IMAGETYP": "dq_mask", "DQSTAGE": stage}
    if frame_id is not None:
        header["FRAMEID"] = frame_id
    return header


def dq_summary(mask: DQMask | np.ndarray) -> dict[str, int]:
    if isinstance(mask, DQMask):
        return mask.summary()
    return DQMask(np.asarray(mask, dtype=np.uint32)).summary()


def dq_mask_from_invalid(shape: tuple[int, int], invalid: np.ndarray, flag: DQFlag) -> DQMask:
    mask = DQMask.empty(shape)
    if np.any(invalid):
        mask.mark(flag, invalid)
    return mask


def dq_mask_from_coverage(coverage: np.ndarray, invalid_flag: DQFlag) -> DQMask:
    cov = np.asarray(coverage, dtype=np.float32)
    return dq_mask_from_invalid(cov.shape, (~np.isfinite(cov)) | (cov <= 0.5), invalid_flag)


def write_dq_tile(writer: FitsTileWriter, tile: Any, mask: DQMask | np.ndarray) -> None:
    data = mask.data if isinstance(mask, DQMask) else np.asarray(mask, dtype=np.uint32)
    writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, data.astype(np.float32))


def add_summary_counts(target: dict[str, int], summary: dict[str, int]) -> None:
    for key, value in summary.items():
        target[key] = int(target.get(key, 0) + int(value))


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(numeric):
        return None
    return int(numeric)


def _summary_count(summary: dict[str, Any], key: str) -> int | None:
    return _optional_int(summary.get(key))


def _first_optional_int(source: dict[str, Any], *keys: str) -> int | None:
    for key in keys:
        value = _optional_int(source.get(key))
        if value is not None:
            return value
    return None


def _coverage_sample_sum(stats: Any) -> int | None:
    if not isinstance(stats, dict):
        return None
    return _first_optional_int(stats, "rounded_sum", "sample_sum", "sum")


def _sample_accounting_closure(
    *,
    input_samples: int | None = None,
    input_valid_before_rejection: int | None,
    input_invalid_before_rejection: int | None = None,
    valid_after_rejection: int | None,
    rejected_samples: int | None,
) -> dict[str, Any]:
    input_total_match = None
    if (
        input_samples is not None
        and input_valid_before_rejection is not None
        and input_invalid_before_rejection is not None
    ):
        input_total_match = (
            input_valid_before_rejection + input_invalid_before_rejection == input_samples
        )
    valid_rejection_match = None
    if (
        input_valid_before_rejection is not None
        and valid_after_rejection is not None
        and rejected_samples is not None
    ):
        valid_rejection_match = (
            input_valid_before_rejection == valid_after_rejection + rejected_samples
        )
    checks = [value for value in (input_total_match, valid_rejection_match) if value is not None]
    status = "missing" if not checks else ("passed" if all(checks) else "failed")
    return {
        "status": status,
        "input_total_match": input_total_match,
        "valid_rejection_match": valid_rejection_match,
        "input_samples": input_samples,
        "input_valid_samples_before_rejection": input_valid_before_rejection,
        "input_invalid_samples_before_rejection": input_invalid_before_rejection,
        "valid_samples_after_rejection": valid_after_rejection,
        "rejected_samples": rejected_samples,
        "semantics": (
            "Initial valid input samples close over final valid samples plus "
            "low/high rejected samples. Invalid input samples are not rejection samples."
        ),
    }


def dq_provenance_summary_from_stack_engine(
    provenance: dict[str, Any] | None,
    *,
    stage: str,
    item: str | None = None,
    engine: str = "stack_engine_cpu",
) -> dict[str, Any]:
    source = provenance or {}
    output_dq = source.get("output_dq_summary") or {}
    low_rejected_samples = _optional_int(source.get("low_rejected_samples"))
    high_rejected_samples = _optional_int(source.get("high_rejected_samples"))
    rejected_samples = _optional_int(source.get("rejected_samples"))
    if rejected_samples is None and low_rejected_samples is not None and high_rejected_samples is not None:
        rejected_samples = low_rejected_samples + high_rejected_samples
    input_samples = _optional_int(source.get("input_samples"))
    input_valid = _optional_int(source.get("input_valid_samples_before_rejection"))
    input_invalid = _optional_int(source.get("input_invalid_samples_before_rejection"))
    valid_after = _optional_int(source.get("valid_samples_after_rejection"))
    return {
        "schema_version": 1,
        "source_schema": "stack_engine_dq_provenance",
        "stage": stage,
        "item": item,
        "engine": engine,
        "input_samples": input_samples,
        "input_valid_samples_before_rejection": input_valid,
        "input_invalid_samples_before_rejection": input_invalid,
        "input_flagged_samples": _optional_int(source.get("input_flagged_samples")),
        "input_nonfinite_samples": _optional_int(source.get("input_nonfinite_samples")),
        "source_dq_flag_counts": dict(source.get("input_dq_flag_counts") or {}),
        "valid_samples_after_rejection": valid_after,
        "low_rejected_samples": low_rejected_samples,
        "high_rejected_samples": high_rejected_samples,
        "rejected_samples": rejected_samples,
        "zero_coverage_pixels": _optional_int(source.get("output_coverage_zero_pixels")),
        "partial_coverage_pixels": None,
        "low_rejected_pixels": _optional_int(source.get("output_low_rejected_pixels")),
        "high_rejected_pixels": _optional_int(source.get("output_high_rejected_pixels")),
        "valid_pixels": _summary_count(output_dq, "valid"),
        "no_data_pixels": _summary_count(output_dq, "no_data"),
        "warp_edge_pixels": _summary_count(output_dq, "warp_edge"),
        "output_dq_summary": dict(output_dq),
        "sample_accounting_closure": _sample_accounting_closure(
            input_samples=input_samples,
            input_valid_before_rejection=input_valid,
            input_invalid_before_rejection=input_invalid,
            valid_after_rejection=valid_after,
            rejected_samples=rejected_samples,
        ),
        "semantics": (
            "StackEngine consumes source DQ flags and non-finite samples as invalid samples; "
            "output DQ records zero-coverage and rejection-touched pixels; rejected sample "
            "counts are separate from invalid input sample counts."
        ),
    }


def dq_provenance_summary_from_resident(
    provenance: dict[str, Any] | None,
    dq_summary: dict[str, Any] | None,
    *,
    stage: str = "integration",
    item: str | None = None,
    engine: str = "cuda_resident_stack",
) -> dict[str, Any]:
    source = provenance or {}
    summary = dq_summary or {}
    finite_pre = source.get("finite_pre_rejection_coverage") or {}
    post_rejection = source.get("post_rejection_coverage") or {}
    input_valid = _coverage_sample_sum(finite_pre)
    valid_after = _coverage_sample_sum(post_rejection)
    rejected_samples = _optional_int(source.get("rejected_sample_count"))
    return {
        "schema_version": 1,
        "source_schema": "resident_dq_coverage_provenance",
        "stage": stage,
        "item": item,
        "engine": engine,
        "active_frame_count": _optional_int(source.get("active_frame_count")),
        "source_terms": list(source.get("source_terms") or []),
        "input_samples": None,
        "input_valid_samples_before_rejection": input_valid,
        "input_invalid_samples_before_rejection": _optional_int(
            source.get("input_invalid_samples_before_rejection")
        ),
        "input_flagged_samples": None,
        "input_nonfinite_samples": None,
        "source_dq_flag_counts": {},
        "finite_pre_rejection_pixels": _optional_int(finite_pre.get("finite_pixels")),
        "post_rejection_pixels": _optional_int(post_rejection.get("finite_pixels")),
        "valid_samples_after_rejection": valid_after,
        "rejected_samples": rejected_samples,
        "zero_coverage_pixels": _first_optional_int(
            source,
            "geometric_zero_pixels",
            "post_rejection_zero_pixels",
            "zero_pre_rejection_pixels",
        ),
        "partial_coverage_pixels": _first_optional_int(
            source,
            "geometric_partial_pixels",
            "partial_pre_rejection_pixels",
        ),
        "low_rejected_pixels": _summary_count(summary, "low_rejected"),
        "high_rejected_pixels": _summary_count(summary, "high_rejected"),
        "valid_pixels": _summary_count(summary, "valid"),
        "no_data_pixels": _summary_count(summary, "no_data"),
        "warp_edge_pixels": _summary_count(summary, "warp_edge"),
        "output_dq_summary": dict(summary),
        "sample_accounting_closure": _sample_accounting_closure(
            input_samples=None,
            input_valid_before_rejection=input_valid,
            input_invalid_before_rejection=None,
            valid_after_rejection=valid_after,
            rejected_samples=rejected_samples,
        ),
        "semantics": (
            "Resident CUDA provenance summarizes post-rejection coverage, rejection counts, "
            "and optional geometric warp coverage from resident output maps. When coverage "
            "sample sums are available, rejected samples are checked against pre/post "
            "rejection coverage closure."
        ),
    }


def write_full_dq_map(path: str | Path, mask: DQMask | np.ndarray, stage: str, frame_id: str | None = None) -> None:
    data = mask.data if isinstance(mask, DQMask) else np.asarray(mask, dtype=np.uint32)
    height, width = data.shape
    with FitsTileWriter(path, width=width, height=height, header=dq_header(stage, frame_id)) as writer:
        class FullTile:
            y0 = 0
            x0 = 0
            y1 = height
            x1 = width

        write_dq_tile(writer, FullTile, data)
