from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from glass.io.json_io import read_json, write_json


def _registration_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_dir():
        candidate = candidate / "registration_results.json"
    return candidate


def _load_registration(path: str | Path) -> tuple[Path, dict[str, Any]]:
    registration_path = _registration_path(path)
    payload = read_json(registration_path)
    if not isinstance(payload, dict):
        raise ValueError(f"registration payload must be a JSON object: {registration_path}")
    return registration_path, payload


def _rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = payload.get("registration_results")
    if rows is None:
        rows = payload.get("results", [])
    return [dict(row) for row in rows] if isinstance(rows, list) else []


def _rows_by_frame(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in _rows(payload):
        frame_id = str(row.get("frame_id") or "")
        if frame_id:
            result[frame_id] = row
    return result


def _matrix(row: dict[str, Any] | None) -> np.ndarray | None:
    if not row:
        return None
    try:
        matrix = np.asarray(row.get("matrix"), dtype=np.float64)
    except (TypeError, ValueError):
        return None
    return matrix if matrix.shape == (3, 3) and np.all(np.isfinite(matrix)) else None


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if np.isfinite(number) else None


def _reference_frame_id(payload: dict[str, Any], rows_by_id: dict[str, dict[str, Any]]) -> str | None:
    if payload.get("reference_frame_id") is not None:
        return str(payload["reference_frame_id"])
    references = sorted(
        str(row.get("frame_id"))
        for row in rows_by_id.values()
        if str(row.get("status") or "") == "reference" and row.get("frame_id") is not None
    )
    if references:
        return references[0]
    row_references = sorted(
        str(row.get("reference_frame_id"))
        for row in rows_by_id.values()
        if row.get("reference_frame_id") is not None
    )
    return row_references[0] if row_references else None


def _translation(matrix: np.ndarray | None) -> tuple[float | None, float | None]:
    if matrix is None:
        return None, None
    return float(matrix[0, 2]), float(matrix[1, 2])


def _row_compare(frame_id: str, baseline: dict[str, Any] | None, candidate: dict[str, Any] | None) -> dict[str, Any]:
    baseline_matrix = _matrix(baseline)
    candidate_matrix = _matrix(candidate)
    baseline_tx, baseline_ty = _translation(baseline_matrix)
    candidate_tx, candidate_ty = _translation(candidate_matrix)
    matrix_delta = None
    linear_delta = None
    translation_delta = None
    if baseline_matrix is not None and candidate_matrix is not None:
        delta = candidate_matrix - baseline_matrix
        matrix_delta = float(np.linalg.norm(delta))
        linear_delta = float(np.linalg.norm(delta[:2, :2]))
        translation_delta = float(np.linalg.norm(delta[:2, 2]))
    baseline_status = None if baseline is None else baseline.get("status")
    candidate_status = None if candidate is None else candidate.get("status")
    baseline_reference = None if baseline is None else baseline.get("reference_frame_id")
    candidate_reference = None if candidate is None else candidate.get("reference_frame_id")
    return {
        "frame_id": frame_id,
        "present_in_baseline": baseline is not None,
        "present_in_candidate": candidate is not None,
        "baseline_status": baseline_status,
        "candidate_status": candidate_status,
        "status_match": baseline_status == candidate_status,
        "baseline_reference_frame_id": None if baseline_reference is None else str(baseline_reference),
        "candidate_reference_frame_id": None if candidate_reference is None else str(candidate_reference),
        "reference_match": baseline_reference == candidate_reference,
        "baseline_transform_model": None if baseline is None else baseline.get("transform_model"),
        "candidate_transform_model": None if candidate is None else candidate.get("transform_model"),
        "baseline_translation": {"x": baseline_tx, "y": baseline_ty},
        "candidate_translation": {"x": candidate_tx, "y": candidate_ty},
        "translation_delta_px": translation_delta,
        "linear_delta_frobenius": linear_delta,
        "matrix_delta_frobenius": matrix_delta,
        "baseline_rms_px": _float_or_none(None if baseline is None else baseline.get("rms_px")),
        "candidate_rms_px": _float_or_none(None if candidate is None else candidate.get("rms_px")),
        "baseline_inliers": None if baseline is None else baseline.get("inliers"),
        "candidate_inliers": None if candidate is None else candidate.get("inliers"),
        "baseline_matched_stars": None if baseline is None else baseline.get("matched_stars"),
        "candidate_matched_stars": None if candidate is None else candidate.get("matched_stars"),
    }


def _finite_values(rows: list[dict[str, Any]], key: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        value = _float_or_none(row.get(key))
        if value is not None:
            values.append(value)
    return values


def _stats(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"count": 0, "mean": None, "max": None, "p95": None}
    data = np.asarray(values, dtype=np.float64)
    return {
        "count": int(data.size),
        "mean": float(np.mean(data)),
        "max": float(np.max(data)),
        "p95": float(np.percentile(data, 95)),
    }


def _check(name: str, passed: bool, **details: Any) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "details": details}


def _recommendation(checks: list[dict[str, Any]]) -> dict[str, str]:
    failed = {str(item["name"]) for item in checks if not item.get("passed")}
    if "reference_frame_match" in failed:
        return {
            "status": "fix_reference_handoff",
            "next_target": "make resident registration use the same reference frame before transform tuning",
        }
    if "row_count_match" in failed or "missing_frame_rows" in failed:
        return {
            "status": "fix_registration_frame_accounting",
            "next_target": "make CPU and resident registration emit matching frame rows",
        }
    if "status_rows_match" in failed:
        return {
            "status": "fix_registration_admission",
            "next_target": "inspect frames whose reference/ok/failed status differs before comparing matrices",
        }
    if "translation_delta_within_limit" in failed or "matrix_delta_within_limit" in failed:
        return {
            "status": "fix_resident_transform_estimation",
            "next_target": "compare triangle descriptor fit and pixel-refine outputs against CPU/external matrices",
        }
    return {
        "status": "registration_matrices_ready",
        "next_target": "continue with warp, DQ, rejection, and image parity validation",
    }


def build_resident_registration_matrix_compare(
    baseline_registration: str | Path,
    candidate_registration: str | Path,
    *,
    baseline_label: str = "baseline",
    candidate_label: str = "candidate",
    max_translation_delta_px: float = 0.5,
    max_matrix_delta_frobenius: float = 0.05,
) -> dict[str, Any]:
    baseline_path, baseline_payload = _load_registration(baseline_registration)
    candidate_path, candidate_payload = _load_registration(candidate_registration)
    baseline_rows = _rows_by_frame(baseline_payload)
    candidate_rows = _rows_by_frame(candidate_payload)
    frame_ids = sorted(set(baseline_rows) | set(candidate_rows))
    rows = [_row_compare(frame_id, baseline_rows.get(frame_id), candidate_rows.get(frame_id)) for frame_id in frame_ids]
    translation_values = _finite_values(rows, "translation_delta_px")
    matrix_values = _finite_values(rows, "matrix_delta_frobenius")
    baseline_reference = _reference_frame_id(baseline_payload, baseline_rows)
    candidate_reference = _reference_frame_id(candidate_payload, candidate_rows)
    missing_rows = [row for row in rows if not row["present_in_baseline"] or not row["present_in_candidate"]]
    status_mismatches = [row for row in rows if row["present_in_baseline"] and row["present_in_candidate"] and not row["status_match"]]
    reference_mismatches = [
        row
        for row in rows
        if row["present_in_baseline"] and row["present_in_candidate"] and not row["reference_match"]
    ]
    max_translation = max(translation_values) if translation_values else None
    max_matrix = max(matrix_values) if matrix_values else None
    checks = [
        _check(
            "reference_frame_match",
            baseline_reference == candidate_reference,
            baseline_reference_frame_id=baseline_reference,
            candidate_reference_frame_id=candidate_reference,
        ),
        _check(
            "row_count_match",
            len(baseline_rows) == len(candidate_rows),
            baseline_row_count=len(baseline_rows),
            candidate_row_count=len(candidate_rows),
        ),
        _check("missing_frame_rows", not missing_rows, missing_frame_count=len(missing_rows)),
        _check("status_rows_match", not status_mismatches, status_mismatch_count=len(status_mismatches)),
        _check("reference_rows_match", not reference_mismatches, reference_mismatch_count=len(reference_mismatches)),
        _check(
            "translation_delta_within_limit",
            max_translation is not None and max_translation <= max_translation_delta_px,
            max_translation_delta_px=max_translation,
            threshold=max_translation_delta_px,
        ),
        _check(
            "matrix_delta_within_limit",
            max_matrix is not None and max_matrix <= max_matrix_delta_frobenius,
            max_matrix_delta_frobenius=max_matrix,
            threshold=max_matrix_delta_frobenius,
        ),
    ]
    passed = all(item["passed"] for item in checks)
    return {
        "schema_version": 1,
        "artifact_type": "resident_registration_matrix_compare",
        "status": "passed" if passed else "attention_required",
        "passed": passed,
        "baseline_label": baseline_label,
        "candidate_label": candidate_label,
        "baseline_registration": str(baseline_path),
        "candidate_registration": str(candidate_path),
        "baseline_transform_model": baseline_payload.get("transform_model"),
        "candidate_transform_model": candidate_payload.get("transform_model"),
        "baseline_reference_frame_id": baseline_reference,
        "candidate_reference_frame_id": candidate_reference,
        "thresholds": {
            "max_translation_delta_px": float(max_translation_delta_px),
            "max_matrix_delta_frobenius": float(max_matrix_delta_frobenius),
        },
        "summary": {
            "baseline_row_count": len(baseline_rows),
            "candidate_row_count": len(candidate_rows),
            "common_row_count": len(set(baseline_rows) & set(candidate_rows)),
            "missing_frame_count": len(missing_rows),
            "status_mismatch_count": len(status_mismatches),
            "reference_mismatch_count": len(reference_mismatches),
            "translation_delta_px": _stats(translation_values),
            "matrix_delta_frobenius": _stats(matrix_values),
        },
        "failed_checks": [item["name"] for item in checks if not item["passed"]],
        "checks": checks,
        "recommendation": _recommendation(checks),
        "worst_translation_rows": sorted(
            [row for row in rows if row.get("translation_delta_px") is not None],
            key=lambda row: float(row["translation_delta_px"]),
            reverse=True,
        )[:10],
        "worst_matrix_rows": sorted(
            [row for row in rows if row.get("matrix_delta_frobenius") is not None],
            key=lambda row: float(row["matrix_delta_frobenius"]),
            reverse=True,
        )[:10],
        "rows": rows,
    }


def write_resident_registration_matrix_compare_markdown(path: str | Path, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Resident Registration Matrix Compare",
        "",
        f"- Status: `{payload['status']}`",
        f"- Passed: `{payload['passed']}`",
        f"- Recommendation: `{payload['recommendation']['status']}`",
        f"- Next target: `{payload['recommendation']['next_target']}`",
        f"- Baseline: `{payload['baseline_label']}` `{payload['baseline_registration']}`",
        f"- Candidate: `{payload['candidate_label']}` `{payload['candidate_registration']}`",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
    ]
    summary = payload.get("summary", {})
    for key in (
        "baseline_row_count",
        "candidate_row_count",
        "common_row_count",
        "missing_frame_count",
        "status_mismatch_count",
        "reference_mismatch_count",
    ):
        lines.append(f"| `{key}` | {summary.get(key)} |")
    translation = summary.get("translation_delta_px") or {}
    matrix = summary.get("matrix_delta_frobenius") or {}
    lines.extend(
        [
            f"| `translation_delta_px.max` | {translation.get('max')} |",
            f"| `translation_delta_px.mean` | {translation.get('mean')} |",
            f"| `matrix_delta_frobenius.max` | {matrix.get('max')} |",
            f"| `matrix_delta_frobenius.mean` | {matrix.get('mean')} |",
            "",
            "## Checks",
            "",
        ]
    )
    for check in payload.get("checks", []):
        status = "PASS" if check.get("passed") else "FAIL"
        lines.append(f"- {status}: `{check['name']}` - {check.get('details', {})}")
    lines.extend(
        [
            "",
            "## Worst Translation Rows",
            "",
            "| Frame | Baseline status | Candidate status | Baseline tx | Baseline ty | Candidate tx | Candidate ty | Delta px | Matrix delta |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in payload.get("worst_translation_rows", []):
        baseline_t = row.get("baseline_translation") or {}
        candidate_t = row.get("candidate_translation") or {}
        lines.append(
            "| "
            f"`{row['frame_id']}` | "
            f"{row.get('baseline_status')} | "
            f"{row.get('candidate_status')} | "
            f"{baseline_t.get('x')} | "
            f"{baseline_t.get('y')} | "
            f"{candidate_t.get('x')} | "
            f"{candidate_t.get('y')} | "
            f"{row.get('translation_delta_px')} | "
            f"{row.get('matrix_delta_frobenius')} |"
        )
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_resident_registration_matrix_compare(
    path: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(path, payload)
    if markdown:
        write_resident_registration_matrix_compare_markdown(markdown, payload)
