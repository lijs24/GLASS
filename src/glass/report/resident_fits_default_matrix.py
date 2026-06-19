from __future__ import annotations

from pathlib import Path
from typing import Any

from glass.io.json_io import read_json, write_json
from glass.models import now_iso


def _load_json_object(path: str | Path) -> dict[str, Any]:
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"JSON artifact must be an object: {path}")
    return payload


def _check(name: str, passed: bool, evidence: dict[str, Any], note: str = "") -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "evidence": evidence, "note": note}


def _first_resident_io(run: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    resident_path = run / "resident_artifacts.json"
    if not resident_path.exists():
        return {}, []
    resident = _load_json_object(resident_path)
    artifacts = resident.get("artifacts")
    if not isinstance(artifacts, list):
        return {}, []
    artifact_objects = [item for item in artifacts if isinstance(item, dict)]
    if not artifact_objects:
        return {}, artifact_objects
    io_pipeline = artifact_objects[0].get("resident_io_pipeline")
    return io_pipeline if isinstance(io_pipeline, dict) else {}, artifact_objects


def _run_timing(run: Path) -> dict[str, Any]:
    timing_path = run / "run_timing.json"
    return _load_json_object(timing_path) if timing_path.exists() else {}


def _raw_selection(io_pipeline: dict[str, Any]) -> dict[str, Any]:
    selection = io_pipeline.get("resident_fits_auto_selection")
    raw = selection.get("raw_u16_gpu") if isinstance(selection, dict) else None
    return raw if isinstance(raw, dict) else {}


def _fallback_reason_counts(raw: dict[str, Any]) -> dict[str, int]:
    counts = raw.get("fallback_reason_counts")
    if not isinstance(counts, dict):
        return {}
    return {str(key): int(value or 0) for key, value in sorted(counts.items())}


def _backend_counts(io_pipeline: dict[str, Any]) -> dict[str, int]:
    counts = io_pipeline.get("fits_backend_counts")
    if not isinstance(counts, dict):
        return {}
    return {str(key): int(value or 0) for key, value in sorted(counts.items())}


def _case_summary(case: dict[str, Any]) -> dict[str, Any]:
    run = Path(case["run"])
    io_pipeline, resident_artifacts = _first_resident_io(run)
    timing = _run_timing(run)
    mode_resolution = io_pipeline.get("fits_read_mode_resolution")
    if not isinstance(mode_resolution, dict):
        mode_resolution = timing.get("resident_fits_read_mode_resolution")
    if not isinstance(mode_resolution, dict):
        mode_resolution = {}
    raw = _raw_selection(io_pipeline)
    fallback_counts = _fallback_reason_counts(raw)
    backend_counts = _backend_counts(io_pipeline)
    return {
        "name": str(case["name"]),
        "run": str(run),
        "resident": bool(resident_artifacts),
        "resident_artifact_count": len(resident_artifacts),
        "run_timing_present": bool(timing),
        "fits_read_mode": io_pipeline.get("fits_read_mode"),
        "fits_read_mode_requested": io_pipeline.get("fits_read_mode_requested"),
        "fits_read_mode_effective": io_pipeline.get("fits_read_mode_effective"),
        "fits_read_mode_resolution": mode_resolution,
        "resolution_source": mode_resolution.get("source"),
        "resolution_explicit": mode_resolution.get("explicit"),
        "backend_counts": backend_counts,
        "raw_gpu_decode_enabled": io_pipeline.get("raw_gpu_decode_enabled"),
        "raw_u16_gpu": {
            "checked": raw.get("checked"),
            "runtime_eligible": raw.get("runtime_eligible"),
            "selected": raw.get("selected"),
            "eligible": raw.get("eligible"),
            "checked_frame_count": int(raw.get("checked_frame_count", 0) or 0),
            "eligible_frame_count": int(raw.get("eligible_frame_count", 0) or 0),
            "fallback_reason_counts": fallback_counts,
        },
    }


def _expected_backend_checks(summary: dict[str, Any], expected: dict[str, Any]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    backend_min = expected.get("backend_count_min", {})
    if isinstance(backend_min, dict):
        for backend, required in sorted(backend_min.items()):
            actual = int(summary["backend_counts"].get(str(backend), 0) or 0)
            checks.append(
                _check(
                    f"backend_{backend}_count_min",
                    actual >= int(required),
                    {"actual": actual, "required_min": int(required), "backend_counts": summary["backend_counts"]},
                )
            )
    fallback_min = expected.get("fallback_reason_min", {})
    if isinstance(fallback_min, dict):
        actual_counts = summary["raw_u16_gpu"]["fallback_reason_counts"]
        for reason, required in sorted(fallback_min.items()):
            actual = int(actual_counts.get(str(reason), 0) or 0)
            checks.append(
                _check(
                    f"fallback_reason_{reason}_count_min",
                    actual >= int(required),
                    {"actual": actual, "required_min": int(required), "fallback_reason_counts": actual_counts},
                )
            )
    return checks


def _case_checks(summary: dict[str, Any], expected: dict[str, Any]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    scalar_expectations = {
        "resident": "resident",
        "resolution_source": "resolution_source",
        "fits_read_mode_requested": "fits_read_mode_requested",
        "fits_read_mode_effective": "fits_read_mode_effective",
        "raw_gpu_decode_enabled": "raw_gpu_decode_enabled",
    }
    for expected_key, summary_key in scalar_expectations.items():
        if expected_key not in expected:
            continue
        checks.append(
            _check(
                f"{expected_key}_matches",
                summary.get(summary_key) == expected[expected_key],
                {"actual": summary.get(summary_key), "expected": expected[expected_key]},
            )
        )
    raw_expectations = {
        "raw_gpu_checked": "checked",
        "raw_gpu_runtime_eligible": "runtime_eligible",
        "raw_gpu_selected": "selected",
        "raw_gpu_eligible": "eligible",
        "raw_gpu_checked_frame_count": "checked_frame_count",
        "raw_gpu_eligible_frame_count": "eligible_frame_count",
    }
    raw = summary["raw_u16_gpu"]
    for expected_key, raw_key in raw_expectations.items():
        if expected_key not in expected:
            continue
        checks.append(
            _check(
                f"{expected_key}_matches",
                raw.get(raw_key) == expected[expected_key],
                {"actual": raw.get(raw_key), "expected": expected[expected_key], "raw_u16_gpu": raw},
            )
        )
    if "fallback_reason_counts" in expected:
        checks.append(
            _check(
                "fallback_reason_counts_match",
                raw.get("fallback_reason_counts") == expected["fallback_reason_counts"],
                {"actual": raw.get("fallback_reason_counts"), "expected": expected["fallback_reason_counts"]},
            )
        )
    checks.extend(_expected_backend_checks(summary, expected))
    return checks


def build_resident_fits_default_matrix(cases_path: str | Path) -> dict[str, Any]:
    cases_payload = _load_json_object(cases_path)
    cases = cases_payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("cases JSON must contain a non-empty 'cases' list")
    rows: list[dict[str, Any]] = []
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("each matrix case must be a JSON object")
        if not case.get("name") or not case.get("run"):
            raise ValueError("each matrix case requires 'name' and 'run'")
        expected = case.get("expect", {})
        if expected is not None and not isinstance(expected, dict):
            raise ValueError("case 'expect' must be an object when provided")
        summary = _case_summary(case)
        checks = _case_checks(summary, expected or {})
        failed = [check["name"] for check in checks if not check["passed"]]
        rows.append(
            {
                "name": summary["name"],
                "run": summary["run"],
                "passed": not failed,
                "failed_checks": failed,
                "summary": summary,
                "checks": checks,
            }
        )
    failed_cases = [row["name"] for row in rows if not row["passed"]]
    return {
        "schema_version": 1,
        "artifact_type": "resident_fits_default_matrix",
        "created_at": now_iso(),
        "cases_path": str(Path(cases_path)),
        "passed": not failed_cases,
        "status": "passed" if not failed_cases else "failed",
        "case_count": len(rows),
        "failed_cases": failed_cases,
        "cases": rows,
    }


def _format_counts(counts: dict[str, int]) -> str:
    if not counts:
        return "{}"
    return ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))


def write_resident_fits_default_matrix(
    out: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(out, payload)
    if markdown is None:
        return
    lines = [
        "# Resident FITS Default Compatibility Matrix",
        "",
        f"- Status: `{payload['status']}`",
        f"- Cases: `{payload['case_count']}`",
        f"- Failed cases: `{', '.join(payload['failed_cases']) if payload['failed_cases'] else 'none'}`",
        "",
        "| Case | Passed | Resident | Source | Requested | Effective | Backends | Raw selected | Fallback reasons |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["cases"]:
        summary = row["summary"]
        raw = summary["raw_u16_gpu"]
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["name"]),
                    "yes" if row["passed"] else "no",
                    "yes" if summary["resident"] else "no",
                    str(summary.get("resolution_source")),
                    str(summary.get("fits_read_mode_requested")),
                    str(summary.get("fits_read_mode_effective")),
                    _format_counts(summary["backend_counts"]),
                    str(raw.get("selected")),
                    _format_counts(raw.get("fallback_reason_counts", {})),
                ]
            )
            + " |"
        )
    Path(markdown).parent.mkdir(parents=True, exist_ok=True)
    Path(markdown).write_text("\n".join(lines) + "\n", encoding="utf-8")
