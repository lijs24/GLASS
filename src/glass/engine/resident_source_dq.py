from __future__ import annotations

from typing import Any

import numpy as np

from glass.engine.contracts import DQFlag, DQMask


def _empty_flag_counts() -> dict[str, int]:
    return {flag.name.lower(): 0 for flag in DQFlag if flag != DQFlag.VALID}


def _dq_flag_counts(data: np.ndarray) -> dict[str, int]:
    counts = _empty_flag_counts()
    bits = np.asarray(data, dtype=np.uint32)
    for flag in DQFlag:
        if flag == DQFlag.VALID:
            continue
        counts[flag.name.lower()] = int(np.count_nonzero((bits & np.uint32(int(flag))) != 0))
    return counts


def source_invalid_mask_from_array(
    data: Any,
    *,
    height: int,
    width: int,
) -> tuple[np.ndarray | None, dict[str, Any]]:
    """Build a source-DQ invalid mask from a resident input array.

    Resident CUDA kernels already treat NaN samples as invalid. This helper
    gives finite DQ flags the same route by turning invalid source samples into
    NaN before integration. Raw byte FITS payloads are reported as unsupported
    for mask extraction here because their compatibility guard implies integer
    samples without NaN payload values.
    """

    shape = (int(height), int(width))
    array = np.asarray(data)
    if array.shape != shape:
        return None, {
            "supported": False,
            "reason": "source_array_shape_not_image",
            "shape": list(array.shape),
            "expected_shape": list(shape),
            "invalid_samples": 0,
        }
    if not np.issubdtype(array.dtype, np.floating):
        return None, {
            "supported": False,
            "reason": "source_array_not_floating",
            "shape": list(array.shape),
            "dtype": str(array.dtype),
            "invalid_samples": 0,
        }

    invalid = ~np.isfinite(array)
    invalid_count = int(np.count_nonzero(invalid))
    return invalid.astype(np.uint8, copy=False), {
        "supported": True,
        "reason": "",
        "shape": list(array.shape),
        "dtype": str(array.dtype),
        "invalid_samples": invalid_count,
        "flagged_samples": 0,
        "nonfinite_samples": invalid_count,
        "flag_counts": {},
        "source_model": "nonfinite_source_samples",
    }


def source_invalid_mask_from_dq_mask(
    dq: DQMask | np.ndarray,
    *,
    height: int,
    width: int,
) -> tuple[np.ndarray | None, dict[str, Any]]:
    shape = (int(height), int(width))
    data = dq.data if isinstance(dq, DQMask) else np.asarray(dq)
    if data.shape != shape:
        return None, {
            "supported": False,
            "reason": "source_dq_shape_not_image",
            "shape": list(data.shape),
            "expected_shape": list(shape),
            "invalid_samples": 0,
            "flag_counts": {},
            "source_model": "dq_bitmask",
        }
    data_u32 = np.asarray(data, dtype=np.uint32)
    invalid = data_u32 != 0
    invalid_count = int(np.count_nonzero(invalid))
    return invalid.astype(np.uint8, copy=False), {
        "supported": True,
        "reason": "",
        "shape": list(data_u32.shape),
        "dtype": str(data_u32.dtype),
        "invalid_samples": invalid_count,
        "flagged_samples": invalid_count,
        "nonfinite_samples": 0,
        "flag_counts": _dq_flag_counts(data_u32),
        "source_model": "dq_bitmask",
    }


def apply_resident_source_invalid_mask(
    stack: Any,
    *,
    frame_index: int,
    frame_id: str,
    invalid_mask: np.ndarray | None,
    mask_info: dict[str, Any],
    source: str,
    require_native: bool = True,
) -> dict[str, Any]:
    invalid_count = int(mask_info.get("invalid_samples") or 0)
    row: dict[str, Any] = {
        "schema_version": 1,
        "frame_id": str(frame_id),
        "frame_index": int(frame_index),
        "source": str(source),
        "supported": bool(mask_info.get("supported")),
        "reason": str(mask_info.get("reason") or ""),
        "invalid_samples": invalid_count,
        "flagged_samples": int(mask_info.get("flagged_samples") or 0),
        "nonfinite_samples": int(mask_info.get("nonfinite_samples") or 0),
        "flag_counts": dict(mask_info.get("flag_counts") or {}),
        "source_model": str(mask_info.get("source_model") or source),
        "applied": False,
        "native_method": None,
    }
    if not row["supported"]:
        row["status"] = "unsupported_no_invalid_samples" if invalid_count == 0 else "unsupported"
        if invalid_count > 0 and require_native:
            raise RuntimeError(f"resident source-DQ mask is unsupported for {frame_id}: {row['reason']}")
        return row
    if invalid_count == 0:
        row["status"] = "no_invalid_samples"
        return row
    if invalid_mask is None:
        row["status"] = "missing_invalid_mask"
        if require_native:
            raise RuntimeError(f"resident source-DQ invalid mask is missing for {frame_id}")
        return row
    if not hasattr(stack, "apply_invalid_mask_frame"):
        row["status"] = "native_method_unavailable"
        if require_native:
            raise RuntimeError(
                "resident CUDA backend must expose apply_invalid_mask_frame "
                f"to consume source-DQ invalid samples for {frame_id}"
            )
        return row

    native = dict(stack.apply_invalid_mask_frame(int(frame_index), invalid_mask))
    row.update(
        {
            "status": "applied",
            "applied": True,
            "native_method": str(native.get("native_method") or "ResidentCalibratedStack.apply_invalid_mask_frame"),
            "native": native,
        }
    )
    return row


def build_resident_source_dq_summary(
    rows: list[dict[str, Any]],
    *,
    frame_count: int,
    height: int,
    width: int,
    active_frame_count: int | None = None,
) -> dict[str, Any]:
    total_invalid = sum(int(row.get("invalid_samples") or 0) for row in rows)
    total_flagged = sum(int(row.get("flagged_samples") or 0) for row in rows)
    total_nonfinite = sum(int(row.get("nonfinite_samples") or 0) for row in rows)
    applied_invalid = sum(
        int(row.get("invalid_samples") or 0) for row in rows if bool(row.get("applied"))
    )
    unsupported = [row for row in rows if str(row.get("status") or "").startswith("unsupported")]
    native_missing = [row for row in rows if row.get("status") == "native_method_unavailable"]
    source_counts: dict[str, int] = {}
    status_counts: dict[str, int] = {}
    flag_counts = _empty_flag_counts()
    for row in rows:
        source = str(row.get("source") or "unknown")
        source_counts[source] = source_counts.get(source, 0) + 1
        status = str(row.get("status") or "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
        for flag, count in dict(row.get("flag_counts") or {}).items():
            flag_counts[str(flag)] = int(flag_counts.get(str(flag), 0)) + int(count or 0)

    effective_frame_count = int(frame_count if active_frame_count is None else active_frame_count)
    input_samples = int(effective_frame_count) * int(height) * int(width)
    input_valid_before_rejection = max(0, input_samples - int(total_invalid))
    return {
        "schema_version": 1,
        "source_model": "resident_source_dq_mask_to_nan",
        "native_method": "ResidentCalibratedStack.apply_invalid_mask_frame",
        "frame_count": int(frame_count),
        "active_frame_count": int(effective_frame_count),
        "height": int(height),
        "width": int(width),
        "input_samples": int(input_samples),
        "input_valid_samples_before_rejection": int(input_valid_before_rejection),
        "input_invalid_samples_before_rejection": int(total_invalid),
        "input_flagged_samples": int(total_flagged),
        "input_nonfinite_samples": int(total_nonfinite),
        "source_dq_flag_counts": {key: value for key, value in sorted(flag_counts.items()) if value},
        "applied_invalid_samples": int(applied_invalid),
        "frame_with_invalid_count": int(sum(1 for row in rows if int(row.get("invalid_samples") or 0) > 0)),
        "applied_frame_count": int(sum(1 for row in rows if bool(row.get("applied")))),
        "unsupported_frame_count": len(unsupported),
        "native_missing_frame_count": len(native_missing),
        "source_counts": dict(sorted(source_counts.items())),
        "status_counts": dict(sorted(status_counts.items())),
        "passed": len(unsupported) == 0 and len(native_missing) == 0 and applied_invalid == total_invalid,
        "rows": rows,
        "semantics": (
            "Resident CUDA consumes source-DQ invalid samples by setting masked "
            "resident frame pixels to NaN before integration. Existing resident "
            "integration kernels then skip those samples before rejection, matching "
            "the CPU StackEngine valid-sample contract."
        ),
    }
