from __future__ import annotations

import math
from collections import Counter
import hashlib
from pathlib import Path
from typing import Any

import numpy as np

from glass.io.fits_io import read_fits_data
from glass.io.json_io import read_json, write_json


_HASH_FIELDS = (
    "reference_catalog",
    "moving_catalog",
    "reference_descriptor",
    "moving_descriptor",
    "selected_fit",
    "trial_signature",
)

_COMBINED_HASH_FIELDS = (
    "triangle_determinism_reference_combined_sha256",
    "triangle_determinism_moving_catalog_combined_sha256",
    "triangle_determinism_selected_fit_combined_sha256",
    "triangle_determinism_trial_combined_sha256",
)

_OUTPUT_PATH_FIELDS = (
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


def _resident_artifacts_path(run_or_file: str | Path) -> Path:
    path = Path(run_or_file)
    if path.is_dir():
        return path / "resident_artifacts.json"
    return path


def _run_dir_from_input(run_or_file: str | Path) -> Path:
    path = Path(run_or_file)
    return path if path.is_dir() else path.parent


def _timing_elapsed(run: Path) -> float | None:
    timing = _json_if_exists(run / "run_timing.json")
    value = timing.get("total_elapsed_s")
    try:
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None


def _artifact_key(index: int, artifact: dict[str, Any]) -> str:
    filt = str(artifact.get("filter") or f"artifact_{index}")
    frame_ids = artifact.get("frame_ids") if isinstance(artifact.get("frame_ids"), list) else []
    if frame_ids:
        return f"{filt}:{len(frame_ids)}:{frame_ids[0]}:{frame_ids[-1]}"
    return f"{filt}:{index}"


def _resolve_artifact_path(run: Path, value: Any) -> Path | None:
    if value in (None, ""):
        return None
    path = Path(str(value))
    return path if path.is_absolute() else run / path


def _fits_data_signature(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"available": False, "exists": False, "path": str(path)}
    data = np.ascontiguousarray(read_fits_data(path, dtype=np.float32))
    finite = np.isfinite(data)
    finite_count = int(np.count_nonzero(finite))
    digest = hashlib.sha256()
    digest.update(str(data.shape).encode("utf-8"))
    digest.update(str(data.dtype).encode("utf-8"))
    digest.update(data.view(np.uint8))
    stats: dict[str, Any] = {
        "finite_pixels": finite_count,
        "nonfinite_pixels": int(data.size - finite_count),
    }
    if finite_count:
        finite_values = data[finite]
        stats.update(
            {
                "min": float(np.min(finite_values)),
                "max": float(np.max(finite_values)),
                "mean": float(np.mean(finite_values)),
                "std": float(np.std(finite_values)),
            }
        )
    return {
        "available": True,
        "exists": True,
        "path": str(path),
        "sha256": digest.hexdigest(),
        "shape": [int(item) for item in data.shape],
        "dtype": str(data.dtype),
        **stats,
    }


def _fits_numerical_drift(baseline_signature: dict[str, Any], candidate_signature: dict[str, Any]) -> dict[str, Any]:
    baseline_path = Path(str(baseline_signature.get("path") or ""))
    candidate_path = Path(str(candidate_signature.get("path") or ""))
    if not baseline_path.exists() or not candidate_path.exists():
        return {
            "available": False,
            "reason": "missing_file",
            "baseline_path": str(baseline_path),
            "candidate_path": str(candidate_path),
        }
    baseline = np.ascontiguousarray(read_fits_data(baseline_path, dtype=np.float32))
    candidate = np.ascontiguousarray(read_fits_data(candidate_path, dtype=np.float32))
    if baseline.shape != candidate.shape:
        return {
            "available": False,
            "reason": "shape_mismatch",
            "baseline_path": str(baseline_path),
            "candidate_path": str(candidate_path),
            "baseline_shape": [int(item) for item in baseline.shape],
            "candidate_shape": [int(item) for item in candidate.shape],
        }
    finite = np.isfinite(baseline) & np.isfinite(candidate)
    finite_count = int(np.count_nonzero(finite))
    nonfinite_mismatch_count = int(np.count_nonzero(np.isfinite(baseline) != np.isfinite(candidate)))
    if finite_count == 0:
        return {
            "available": False,
            "reason": "no_joint_finite_pixels",
            "baseline_path": str(baseline_path),
            "candidate_path": str(candidate_path),
            "shape": [int(item) for item in baseline.shape],
            "joint_finite_pixels": 0,
            "nonfinite_mismatch_pixels": nonfinite_mismatch_count,
        }
    delta = candidate[finite] - baseline[finite]
    abs_delta = np.abs(delta)
    baseline_values = baseline[finite]
    candidate_values = candidate[finite]
    rms = float(np.sqrt(np.mean(delta * delta)))
    baseline_std = float(np.std(baseline_values))
    return {
        "available": True,
        "baseline_path": str(baseline_path),
        "candidate_path": str(candidate_path),
        "shape": [int(item) for item in baseline.shape],
        "dtype": str(baseline.dtype),
        "joint_finite_pixels": finite_count,
        "nonfinite_mismatch_pixels": nonfinite_mismatch_count,
        "mean_signed": float(np.mean(delta)),
        "mean_abs": float(np.mean(abs_delta)),
        "median_abs": float(np.median(abs_delta)),
        "rms": rms,
        "p95_abs": float(np.percentile(abs_delta, 95)),
        "p99_abs": float(np.percentile(abs_delta, 99)),
        "max_abs": float(np.max(abs_delta)),
        "baseline_mean": float(np.mean(baseline_values)),
        "candidate_mean": float(np.mean(candidate_values)),
        "baseline_std": baseline_std,
        "candidate_std": float(np.std(candidate_values)),
        "relative_rms_to_baseline_std": None if baseline_std == 0.0 else rms / baseline_std,
    }


def _index_output_signatures(run: Path, payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    artifacts = payload.get("artifacts") if isinstance(payload.get("artifacts"), list) else []
    output_signatures: dict[str, dict[str, Any]] = {}
    for index, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict):
            continue
        key = _artifact_key(index, artifact)
        signatures: dict[str, Any] = {}
        for field in _OUTPUT_PATH_FIELDS:
            path = _resolve_artifact_path(run, artifact.get(field))
            if path is not None:
                signatures[field] = _fits_data_signature(path)
        output_signatures[key] = signatures
    return output_signatures


def _output_numerical_drifts(
    baseline_outputs: dict[str, dict[str, Any]],
    candidate_outputs: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    drifts: list[dict[str, Any]] = []
    for key in sorted(set(baseline_outputs) | set(candidate_outputs)):
        baseline_fields = baseline_outputs.get(key) or {}
        candidate_fields = candidate_outputs.get(key) or {}
        for field in _OUTPUT_PATH_FIELDS:
            baseline_signature = baseline_fields.get(field)
            candidate_signature = candidate_fields.get(field)
            if not isinstance(baseline_signature, dict) or not isinstance(candidate_signature, dict):
                continue
            if not baseline_signature.get("available") or not candidate_signature.get("available"):
                continue
            if baseline_signature.get("sha256") == candidate_signature.get("sha256"):
                continue
            drift = _fits_numerical_drift(baseline_signature, candidate_signature)
            drifts.append({"key": key, "field": field, "drift": drift})
    return drifts


def _registration_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = payload.get("registration_results")
    if rows is None:
        rows = payload.get("results")
    return rows if isinstance(rows, list) else []


def _hash_value(item: dict[str, Any], key: str) -> str | None:
    value = item.get(key)
    if isinstance(value, dict):
        digest = value.get("sha256")
        return str(digest) if digest else None
    return None


def _values_equal(left: Any, right: Any) -> bool:
    if isinstance(left, float) and isinstance(right, float):
        if math.isnan(left) and math.isnan(right):
            return True
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(
            _values_equal(left_item, right_item) for left_item, right_item in zip(left, right, strict=True)
        )
    if isinstance(left, dict) and isinstance(right, dict):
        keys = set(left) | set(right)
        if "path" in keys and ("sha256" in keys or "available" in keys):
            keys.discard("path")
        return all(_values_equal(left.get(key), right.get(key)) for key in keys)
    return left == right


def _index_artifact_determinism(payload: dict[str, Any]) -> dict[str, Any]:
    artifacts = payload.get("artifacts") if isinstance(payload.get("artifacts"), list) else []
    artifact_summaries: dict[str, dict[str, Any]] = {}
    frames: dict[str, dict[str, Any]] = {}
    for index, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict):
            continue
        key = _artifact_key(index, artifact)
        registration = artifact.get("resident_registration")
        registration = registration if isinstance(registration, dict) else {}
        artifact_summaries[key] = {
            "filter": artifact.get("filter"),
            "frame_count": len(artifact.get("frame_ids") or []),
            "active_frame_count": registration.get("active_frame_count"),
            "signature_mode": registration.get("triangle_determinism_signature_mode"),
            "moving_frame_count": registration.get("triangle_determinism_moving_frame_count"),
            "threshold_count": registration.get("triangle_determinism_threshold_count"),
            **{field: registration.get(field) for field in _COMBINED_HASH_FIELDS},
        }
        determinism = registration.get("triangle_determinism")
        determinism = determinism if isinstance(determinism, dict) else {}
        moving = determinism.get("moving") if isinstance(determinism.get("moving"), dict) else {}
        for frame_id, frame_info in moving.items():
            if not isinstance(frame_info, dict):
                continue
            frame_key = str(frame_id)
            frames[frame_key] = {
                "artifact_key": key,
                "frame_id": frame_key,
                "status": frame_info.get("status"),
                "threshold_mode": frame_info.get("threshold_mode"),
                "selected_threshold": frame_info.get("selected_threshold"),
                "threshold_candidates": frame_info.get("threshold_candidates"),
                "hashes": {field: _hash_value(frame_info, field) for field in _HASH_FIELDS},
                "counts": {
                    "reference_catalog_stored": (frame_info.get("reference_catalog") or {}).get("stored_count")
                    if isinstance(frame_info.get("reference_catalog"), dict)
                    else None,
                    "moving_catalog_stored": (frame_info.get("moving_catalog") or {}).get("stored_count")
                    if isinstance(frame_info.get("moving_catalog"), dict)
                    else None,
                    "reference_descriptor_count": (frame_info.get("reference_descriptor") or {}).get("count")
                    if isinstance(frame_info.get("reference_descriptor"), dict)
                    else None,
                    "moving_descriptor_count": (frame_info.get("moving_descriptor") or {}).get("count")
                    if isinstance(frame_info.get("moving_descriptor"), dict)
                    else None,
                },
            }
    return {"artifacts": artifact_summaries, "frames": frames}


def _registration_index(run: Path) -> dict[str, dict[str, Any]]:
    rows = _registration_rows(_json_if_exists(run / "registration_results.json"))
    return {
        str(row.get("frame_id")): {
            "status": row.get("status"),
            "matched_stars": row.get("matched_stars"),
            "inliers": row.get("inliers"),
            "rms_px": row.get("rms_px"),
            "matrix": row.get("matrix"),
        }
        for row in rows
        if isinstance(row, dict) and row.get("frame_id") is not None
    }


def _frame_accounting_index(run: Path) -> dict[str, dict[str, Any]]:
    payload = _json_if_exists(run / "frame_accounting.json")
    rows = payload.get("frames") if isinstance(payload.get("frames"), list) else []
    return {
        str(row.get("frame_id")): {
            "final_status": row.get("final_status"),
            "registration_status": row.get("registration_status"),
            "integration_status": row.get("integration_status"),
            "integration_weight": row.get("integration_weight"),
        }
        for row in rows
        if isinstance(row, dict) and row.get("frame_id") is not None
    }


def _diff_mapping(
    baseline: dict[str, Any],
    candidate: dict[str, Any],
    *,
    fields: tuple[str, ...],
) -> list[dict[str, Any]]:
    diffs: list[dict[str, Any]] = []
    all_keys = sorted(set(baseline) | set(candidate))
    for key in all_keys:
        left = baseline.get(key)
        right = candidate.get(key)
        if left is None or right is None:
            diffs.append(
                {
                    "key": key,
                    "difference": "missing_key",
                    "baseline_present": left is not None,
                    "candidate_present": right is not None,
                }
            )
            continue
        changed = {
            field: {"baseline": left.get(field), "candidate": right.get(field)}
            for field in fields
            if not _values_equal(left.get(field), right.get(field))
        }
        if changed:
            diffs.append({"key": key, "difference": "field_mismatch", "fields": changed})
    return diffs


def _diff_frames(
    baseline: dict[str, dict[str, Any]],
    candidate: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    diffs: list[dict[str, Any]] = []
    all_ids = sorted(set(baseline) | set(candidate))
    for frame_id in all_ids:
        left = baseline.get(frame_id)
        right = candidate.get(frame_id)
        if left is None or right is None:
            diffs.append(
                {
                    "frame_id": frame_id,
                    "difference_types": ["missing_frame"],
                    "baseline_present": left is not None,
                    "candidate_present": right is not None,
                }
            )
            continue
        difference_types: list[str] = []
        field_changes: dict[str, Any] = {}
        for field in ("status", "threshold_mode", "selected_threshold", "threshold_candidates"):
            if not _values_equal(left.get(field), right.get(field)):
                difference_types.append(field)
                field_changes[field] = {"baseline": left.get(field), "candidate": right.get(field)}
        hash_changes = {
            field: {
                "baseline": left.get("hashes", {}).get(field),
                "candidate": right.get("hashes", {}).get(field),
            }
            for field in _HASH_FIELDS
            if not _values_equal(left.get("hashes", {}).get(field), right.get("hashes", {}).get(field))
        }
        if hash_changes:
            difference_types.extend(f"{field}_hash" for field in hash_changes)
        count_changes = {
            field: {
                "baseline": left.get("counts", {}).get(field),
                "candidate": right.get("counts", {}).get(field),
            }
            for field in sorted(set(left.get("counts", {})) | set(right.get("counts", {})))
            if not _values_equal(left.get("counts", {}).get(field), right.get("counts", {}).get(field))
        }
        if count_changes:
            difference_types.extend(f"{field}_count" for field in count_changes)
        if difference_types:
            diffs.append(
                {
                    "frame_id": frame_id,
                    "difference_types": difference_types,
                    "fields": field_changes,
                    "hashes": hash_changes,
                    "counts": count_changes,
                    "baseline": left,
                    "candidate": right,
                }
            )
    return diffs


def _status_counts(index: dict[str, dict[str, Any]], field: str) -> dict[str, int]:
    return dict(Counter(str(row.get(field) or "unknown") for row in index.values()))


def _difference_type_counts(frame_differences: list[dict[str, Any]]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for item in frame_differences:
        for difference_type in item.get("difference_types", []):
            counter[str(difference_type)] += 1
    return dict(counter)


def _check(name: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "evidence": evidence}


def build_resident_determinism_audit(
    baseline_run: str | Path,
    candidate_run: str | Path,
) -> dict[str, Any]:
    baseline_path = _resident_artifacts_path(baseline_run)
    candidate_path = _resident_artifacts_path(candidate_run)
    baseline_dir = _run_dir_from_input(baseline_run)
    candidate_dir = _run_dir_from_input(candidate_run)

    baseline_resident = _json_if_exists(baseline_path)
    candidate_resident = _json_if_exists(candidate_path)
    baseline_det = _index_artifact_determinism(baseline_resident)
    candidate_det = _index_artifact_determinism(candidate_resident)
    frame_differences = _diff_frames(baseline_det["frames"], candidate_det["frames"])
    artifact_differences = _diff_mapping(
        baseline_det["artifacts"],
        candidate_det["artifacts"],
        fields=("signature_mode", "moving_frame_count", "threshold_count", *_COMBINED_HASH_FIELDS),
    )
    baseline_outputs = _index_output_signatures(baseline_dir, baseline_resident)
    candidate_outputs = _index_output_signatures(candidate_dir, candidate_resident)
    output_differences = _diff_mapping(
        baseline_outputs,
        candidate_outputs,
        fields=_OUTPUT_PATH_FIELDS,
    )
    output_numerical_drifts = _output_numerical_drifts(baseline_outputs, candidate_outputs)

    baseline_registration = _registration_index(baseline_dir)
    candidate_registration = _registration_index(candidate_dir)
    registration_differences = _diff_mapping(
        baseline_registration,
        candidate_registration,
        fields=("status", "matched_stars", "inliers", "rms_px", "matrix"),
    )

    baseline_accounting = _frame_accounting_index(baseline_dir)
    candidate_accounting = _frame_accounting_index(candidate_dir)
    accounting_differences = _diff_mapping(
        baseline_accounting,
        candidate_accounting,
        fields=("final_status", "registration_status", "integration_status", "integration_weight"),
    )

    baseline_elapsed = _timing_elapsed(baseline_dir)
    candidate_elapsed = _timing_elapsed(candidate_dir)
    elapsed_delta = (
        None if baseline_elapsed is None or candidate_elapsed is None else candidate_elapsed - baseline_elapsed
    )
    elapsed_ratio = (
        None
        if baseline_elapsed is None or candidate_elapsed is None or baseline_elapsed == 0.0
        else candidate_elapsed / baseline_elapsed
    )
    checks = [
        _check(
            "resident_artifacts_present",
            bool(baseline_resident) and bool(candidate_resident),
            {"baseline": str(baseline_path), "candidate": str(candidate_path)},
        ),
        _check(
            "artifact_signatures_match",
            len(artifact_differences) == 0,
            {"difference_count": len(artifact_differences)},
        ),
        _check(
            "frame_signatures_match",
            len(frame_differences) == 0,
            {"difference_count": len(frame_differences)},
        ),
        _check(
            "registration_results_match",
            len(registration_differences) == 0,
            {"difference_count": len(registration_differences)},
        ),
        _check(
            "frame_accounting_match",
            len(accounting_differences) == 0,
            {"difference_count": len(accounting_differences)},
        ),
        _check(
            "output_pixels_match",
            len(output_differences) == 0,
            {"difference_count": len(output_differences)},
        ),
    ]
    passed = all(item["passed"] for item in checks)
    return {
        "schema_version": 1,
        "audit_type": "resident_triangle_determinism",
        "baseline": {
            "run": str(baseline_dir),
            "resident_artifacts": str(baseline_path),
            "moving_frame_count": len(baseline_det["frames"]),
            "artifact_count": len(baseline_det["artifacts"]),
            "registration_status_counts": _status_counts(baseline_registration, "status"),
            "frame_accounting_final_status_counts": _status_counts(baseline_accounting, "final_status"),
            "elapsed_s": baseline_elapsed,
        },
        "candidate": {
            "run": str(candidate_dir),
            "resident_artifacts": str(candidate_path),
            "moving_frame_count": len(candidate_det["frames"]),
            "artifact_count": len(candidate_det["artifacts"]),
            "registration_status_counts": _status_counts(candidate_registration, "status"),
            "frame_accounting_final_status_counts": _status_counts(candidate_accounting, "final_status"),
            "elapsed_s": candidate_elapsed,
        },
        "timing": {
            "baseline_elapsed_s": baseline_elapsed,
            "candidate_elapsed_s": candidate_elapsed,
            "elapsed_delta_s": elapsed_delta,
            "candidate_over_baseline_ratio": elapsed_ratio,
        },
        "summary": {
            "passed": passed,
            "artifact_difference_count": len(artifact_differences),
            "frame_signature_difference_count": len(frame_differences),
            "frame_signature_difference_type_counts": _difference_type_counts(frame_differences),
            "registration_difference_count": len(registration_differences),
            "frame_accounting_difference_count": len(accounting_differences),
            "output_difference_count": len(output_differences),
            "output_numerical_drift_count": len(output_numerical_drifts),
            "output_numerical_drift_max_relative_rms": max(
                (
                    float(item["drift"].get("relative_rms_to_baseline_std"))
                    for item in output_numerical_drifts
                    if isinstance(item.get("drift"), dict)
                    and item["drift"].get("relative_rms_to_baseline_std") is not None
                ),
                default=None,
            ),
        },
        "checks": checks,
        "artifact_differences": artifact_differences,
        "frame_signature_differences": frame_differences,
        "registration_differences": registration_differences,
        "frame_accounting_differences": accounting_differences,
        "output_differences": output_differences,
        "output_numerical_drifts": output_numerical_drifts,
    }


def write_resident_determinism_markdown(path: str | Path, audit: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    summary = audit["summary"]
    timing = audit["timing"]
    lines = [
        "# Resident CUDA Determinism Audit",
        "",
        f"- Result: {'PASS' if summary['passed'] else 'FAIL'}",
        f"- Baseline run: `{audit['baseline']['run']}`",
        f"- Candidate run: `{audit['candidate']['run']}`",
        f"- Baseline elapsed: `{timing['baseline_elapsed_s']}` s",
        f"- Candidate elapsed: `{timing['candidate_elapsed_s']}` s",
        f"- Candidate/baseline ratio: `{timing['candidate_over_baseline_ratio']}`",
        "",
        "## Difference Counts",
        "",
        f"- Artifact signatures: `{summary['artifact_difference_count']}`",
        f"- Frame signatures: `{summary['frame_signature_difference_count']}`",
        f"- Registration results: `{summary['registration_difference_count']}`",
        f"- Frame accounting: `{summary['frame_accounting_difference_count']}`",
        f"- Output pixels/maps: `{summary['output_difference_count']}`",
        f"- Output numerical drifts: `{summary.get('output_numerical_drift_count', 0)}`",
        f"- Max relative output RMS drift: `{summary.get('output_numerical_drift_max_relative_rms')}`",
        "",
    ]
    if summary.get("frame_signature_difference_type_counts"):
        lines.extend(["## Frame Signature Difference Types", ""])
        for key, value in sorted(summary["frame_signature_difference_type_counts"].items()):
            lines.append(f"- `{key}`: `{value}`")
        lines.append("")
    lines.extend(["## Checks", ""])
    for check in audit["checks"]:
        lines.append(f"- `{check['name']}`: {'PASS' if check['passed'] else 'FAIL'}")
    if audit["frame_signature_differences"]:
        lines.extend(["", "## First Frame Signature Differences", ""])
        for item in audit["frame_signature_differences"][:20]:
            lines.append(f"- `{item['frame_id']}`: `{', '.join(item['difference_types'])}`")
    if audit["registration_differences"]:
        lines.extend(["", "## First Registration Differences", ""])
        for item in audit["registration_differences"][:20]:
            lines.append(f"- `{item['key']}`: `{item['difference']}`")
    if audit["frame_accounting_differences"]:
        lines.extend(["", "## First Frame Accounting Differences", ""])
        for item in audit["frame_accounting_differences"][:20]:
            lines.append(f"- `{item['key']}`: `{item['difference']}`")
    if audit["output_differences"]:
        lines.extend(["", "## First Output Differences", ""])
        for item in audit["output_differences"][:20]:
            lines.append(f"- `{item['key']}`: `{item['difference']}`")
    if audit.get("output_numerical_drifts"):
        lines.extend(["", "## First Output Numerical Drifts", ""])
        for item in audit["output_numerical_drifts"][:20]:
            drift = item.get("drift", {})
            lines.append(
                "- "
                f"`{item['key']}` `{item['field']}`: "
                f"rms=`{drift.get('rms')}`, "
                f"mean_abs=`{drift.get('mean_abs')}`, "
                f"p99_abs=`{drift.get('p99_abs')}`, "
                f"relative_rms=`{drift.get('relative_rms_to_baseline_std')}`"
            )
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_resident_determinism_audit(
    out: str | Path,
    audit: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(out, audit)
    if markdown:
        write_resident_determinism_markdown(markdown, audit)
