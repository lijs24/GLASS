from __future__ import annotations

from pathlib import Path
from typing import Any

from glass.io.json_io import read_json, write_json


def _label_path(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise ValueError(f"expected label=path entry, got: {value}")
    label, path = value.split("=", 1)
    label = label.strip()
    if not label:
        raise ValueError(f"matrix sweep entry has empty label: {value}")
    return label, Path(path)


def _load_json(path: Path) -> dict[str, Any]:
    payload = read_json(path)
    return payload if isinstance(payload, dict) else {}


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number == number and number not in (float("inf"), float("-inf")) else None


def _matrix_row(label: str, path: Path, parity: dict[str, Any] | None) -> dict[str, Any]:
    payload = _load_json(path)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    translation = summary.get("translation_delta_px") if isinstance(summary.get("translation_delta_px"), dict) else {}
    matrix = summary.get("matrix_delta_frobenius") if isinstance(summary.get("matrix_delta_frobenius"), dict) else {}
    recommendation = payload.get("recommendation") if isinstance(payload.get("recommendation"), dict) else {}
    compare = parity.get("compare", {}) if isinstance(parity, dict) else {}
    deltas = parity.get("deltas", {}) if isinstance(parity, dict) else {}
    return {
        "label": label,
        "matrix_compare_path": str(path),
        "matrix_status": payload.get("status"),
        "matrix_passed": bool(payload.get("passed")),
        "matrix_failed_checks": list(payload.get("failed_checks") or []),
        "matrix_recommendation": recommendation.get("status"),
        "translation_delta_max_px": _float_or_none(translation.get("max")),
        "translation_delta_mean_px": _float_or_none(translation.get("mean")),
        "matrix_delta_max_frobenius": _float_or_none(matrix.get("max")),
        "matrix_delta_mean_frobenius": _float_or_none(matrix.get("mean")),
        "status_mismatch_count": int(summary.get("status_mismatch_count") or 0),
        "reference_mismatch_count": int(summary.get("reference_mismatch_count") or 0),
        "missing_frame_count": int(summary.get("missing_frame_count") or 0),
        "parity_path": None if parity is None else str(parity.get("_path")),
        "parity_status": None if parity is None else parity.get("status"),
        "parity_passed": None if parity is None else bool(parity.get("parity_passed")),
        "rms_diff": _float_or_none(compare.get("rms_diff")),
        "relative_rms_diff": _float_or_none(compare.get("relative_rms_diff")),
        "p99_abs_diff": _float_or_none(compare.get("abs_diff_p99")),
        "rejected_sample_delta": None
        if not isinstance(deltas, dict) or deltas.get("rejected_sample_delta") is None
        else int(deltas.get("rejected_sample_delta")),
    }


def _sort_key(row: dict[str, Any]) -> tuple[int, float, float, float]:
    matrix_passed = 0 if row.get("matrix_passed") else 1
    rms = row.get("rms_diff")
    translation = row.get("translation_delta_max_px")
    rejected_delta = row.get("rejected_sample_delta")
    return (
        matrix_passed,
        float("inf") if translation is None else float(translation),
        float("inf") if rms is None else float(rms),
        float("inf") if rejected_delta is None else abs(float(rejected_delta)),
    )


def _recommendation(rows: list[dict[str, Any]]) -> dict[str, str]:
    if not rows:
        return {
            "status": "no_variants",
            "next_target": "run at least one resident matrix comparison",
        }
    best = sorted(rows, key=_sort_key)[0]
    if best.get("matrix_passed") and best.get("parity_passed"):
        return {
            "status": "promote_candidate_for_benchmark_repeat",
            "next_target": f"rerun larger synthetic/200-light validation for {best['label']}",
        }
    if best.get("matrix_passed"):
        return {
            "status": "matrix_ready_but_image_parity_blocked",
            "next_target": "focus next gate on warp, DQ, rejection, or integration sample accounting",
        }
    return {
        "status": "subpixel_refinement_still_blocked",
        "next_target": "change resident transform refinement metric/model before running larger benchmarks",
    }


def build_resident_registration_matrix_sweep(
    matrix_compare_entries: list[str],
    *,
    parity_entries: list[str] | None = None,
) -> dict[str, Any]:
    parity_by_label: dict[str, dict[str, Any]] = {}
    for entry in parity_entries or []:
        label, path = _label_path(entry)
        payload = _load_json(path)
        payload["_path"] = str(path)
        parity_by_label[label] = payload
    rows = []
    for entry in matrix_compare_entries:
        label, path = _label_path(entry)
        rows.append(_matrix_row(label, path, parity_by_label.get(label)))
    ranked = sorted(rows, key=_sort_key)
    return {
        "schema_version": 1,
        "artifact_type": "resident_registration_matrix_sweep",
        "variant_count": len(rows),
        "matrix_passed_count": sum(1 for row in rows if row["matrix_passed"]),
        "parity_passed_count": sum(1 for row in rows if row["parity_passed"]),
        "best_variant": None if not ranked else ranked[0]["label"],
        "recommendation": _recommendation(rows),
        "rows": rows,
        "ranked_rows": ranked,
    }


def write_resident_registration_matrix_sweep_markdown(path: str | Path, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Resident Registration Matrix Sweep",
        "",
        f"- Variant count: `{payload['variant_count']}`",
        f"- Matrix passed count: `{payload['matrix_passed_count']}`",
        f"- Parity passed count: `{payload['parity_passed_count']}`",
        f"- Best variant: `{payload['best_variant']}`",
        f"- Recommendation: `{payload['recommendation']['status']}`",
        f"- Next target: `{payload['recommendation']['next_target']}`",
        "",
        "## Ranked Variants",
        "",
        "| Variant | Matrix passed | Max delta px | Mean delta px | RMS diff | P99 abs | Rejected delta | Matrix recommendation |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in payload.get("ranked_rows", []):
        lines.append(
            "| "
            f"`{row['label']}` | "
            f"{row.get('matrix_passed')} | "
            f"{row.get('translation_delta_max_px')} | "
            f"{row.get('translation_delta_mean_px')} | "
            f"{row.get('rms_diff')} | "
            f"{row.get('p99_abs_diff')} | "
            f"{row.get('rejected_sample_delta')} | "
            f"{row.get('matrix_recommendation')} |"
        )
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_resident_registration_matrix_sweep(
    path: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(path, payload)
    if markdown:
        write_resident_registration_matrix_sweep_markdown(markdown, payload)
