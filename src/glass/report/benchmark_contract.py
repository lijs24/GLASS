from __future__ import annotations

from pathlib import Path
from typing import Any

from glass.report.speedup_report import _read_json_lenient


def load_benchmark_contract(path: str | Path) -> dict[str, Any]:
    contract = _read_json_lenient(path)
    if not isinstance(contract, dict):
        raise ValueError(f"benchmark contract must be a JSON object: {path}")
    if int(contract.get("schema_version", 1)) != 1:
        raise ValueError(f"unsupported benchmark contract schema_version: {contract.get('schema_version')}")
    return contract


def _numeric(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _check(name: str, passed: bool, evidence: dict[str, Any], note: str = "") -> dict[str, Any]:
    return {
        "name": name,
        "passed": bool(passed),
        "evidence": evidence,
        "note": note,
    }


def _close_enough(actual: Any, expected: Any, *, abs_tol: float, rel_tol: float) -> bool:
    actual_number = _numeric(actual)
    expected_number = _numeric(expected)
    if actual_number is None or expected_number is None:
        return False
    tolerance = max(float(abs_tol), abs(expected_number) * float(rel_tol))
    return abs(actual_number - expected_number) <= tolerance


def _read_run_command(glass_run: str | Path) -> str | None:
    path = Path(glass_run) / "run_command.txt"
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8", errors="replace")


def _load_resident_timing(glass_run: str | Path) -> dict[str, Any]:
    path = Path(glass_run) / "resident_artifacts.json"
    if not path.exists():
        return {}
    payload = _read_json_lenient(path)
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        return {}
    first = artifacts[0]
    if not isinstance(first, dict):
        return {}
    timing = first.get("timing_s")
    return timing if isinstance(timing, dict) else {}


def build_benchmark_performance_diagnostics(
    contract: dict[str, Any],
    *,
    glass_run: str | Path,
) -> dict[str, Any] | None:
    baseline = contract.get("timing_baseline") or {}
    stage_baselines = baseline.get("stages_s") or {}
    if not isinstance(stage_baselines, dict) or not stage_baselines:
        return None

    warning_factor = _numeric(baseline.get("warning_regression_factor")) or 1.15
    current_timing = _load_resident_timing(glass_run)
    items: list[dict[str, Any]] = []
    for stage, baseline_value in stage_baselines.items():
        baseline_s = _numeric(baseline_value)
        actual_s = _numeric(current_timing.get(stage))
        if baseline_s is None:
            continue
        factor = actual_s / baseline_s if actual_s is not None and baseline_s > 0.0 else None
        delta_s = actual_s - baseline_s if actual_s is not None else None
        status = "missing_current"
        if factor is not None:
            status = "regressed" if factor > warning_factor else "ok"
        items.append(
            {
                "stage": str(stage),
                "baseline_s": baseline_s,
                "actual_s": actual_s,
                "delta_s": delta_s,
                "factor": factor,
                "status": status,
            }
        )

    items.sort(
        key=lambda item: (
            item["factor"] is not None,
            float(item["factor"] or 0.0),
            float(item["delta_s"] or 0.0),
        ),
        reverse=True,
    )
    regressed = [item for item in items if item["status"] == "regressed"]
    missing = [item for item in items if item["status"] == "missing_current"]
    if regressed:
        status = "regressed"
    elif missing:
        status = "incomplete"
    else:
        status = "ok"
    return {
        "schema_version": 1,
        "status": status,
        "warning_regression_factor": warning_factor,
        "items": items,
        "regressed_count": len(regressed),
        "missing_count": len(missing),
        "worst_regression": regressed[0] if regressed else (items[0] if items else None),
    }


def build_benchmark_contract_checks(
    contract: dict[str, Any],
    *,
    glass_run: str | Path,
    speedup_summary: dict[str, Any],
    compare_payload: dict[str, Any],
    frame_type_counts: dict[str, int],
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    dataset = contract.get("dataset_requirements") or {}
    for frame_type in ("light", "bias", "dark", "flat"):
        required = dataset.get(frame_type)
        if required is None:
            continue
        actual = int(frame_type_counts.get(frame_type, 0))
        checks.append(
            _check(
                f"contract_minimum_{frame_type}_frames",
                actual >= int(required),
                {"actual": actual, "required": int(required)},
            )
        )

    active_required = dataset.get("active_light_frames")
    if active_required is not None:
        actual_active = int((speedup_summary.get("glass") or {}).get("weighted_frame_count") or 0)
        checks.append(
            _check(
                "contract_minimum_active_light_frames",
                actual_active >= int(active_required),
                {"actual": actual_active, "required": int(active_required)},
            )
        )

    runtime = contract.get("runtime") or {}
    glass_elapsed = _numeric((speedup_summary.get("glass") or {}).get("elapsed_s"))
    baseline_elapsed = _numeric(runtime.get("release_baseline_elapsed_s"))
    max_factor = _numeric(runtime.get("max_runtime_regression_factor"))
    if glass_elapsed is not None and baseline_elapsed is not None and max_factor is not None:
        required_max = baseline_elapsed * max_factor
        checks.append(
            _check(
                "contract_max_runtime_vs_release_baseline",
                glass_elapsed <= required_max,
                {
                    "actual_s": glass_elapsed,
                    "release_baseline_s": baseline_elapsed,
                    "max_regression_factor": max_factor,
                    "required_max_s": required_max,
                },
            )
        )

    min_speedup = _numeric(runtime.get("min_speedup_vs_reference"))
    speedup = _numeric(speedup_summary.get("speedup_vs_wbpp"))
    if min_speedup is not None:
        checks.append(
            _check(
                "contract_minimum_speedup_vs_reference",
                speedup is not None and speedup >= min_speedup,
                {"actual": speedup, "required": min_speedup},
            )
        )

    command_text = _read_run_command(glass_run)
    for token in contract.get("required_command_tokens") or []:
        token_text = str(token)
        checks.append(
            _check(
                f"contract_required_command_token:{token_text}",
                command_text is not None and token_text in command_text,
                {"token": token_text, "run_command_present": command_text is not None},
            )
        )

    compare_contract = contract.get("comparison") or {}
    transform = compare_payload.get("candidate_transform") or {}
    region = compare_payload.get("comparison_region") or {}
    abs_tol = float(compare_contract.get("numeric_abs_tolerance", 1.0e-12))
    rel_tol = float(compare_contract.get("numeric_rel_tolerance", 1.0e-9))
    for key, actual_key in [
        ("required_scale", "scale"),
        ("required_offset", "offset"),
    ]:
        if key not in compare_contract:
            continue
        expected = compare_contract[key]
        actual = transform.get(actual_key)
        checks.append(
            _check(
                f"contract_compare_{actual_key}",
                _close_enough(actual, expected, abs_tol=abs_tol, rel_tol=rel_tol),
                {"actual": actual, "required": expected, "abs_tol": abs_tol, "rel_tol": rel_tol},
            )
        )
    if "required_min_coverage" in compare_contract:
        actual_min_coverage = _numeric(region.get("min_coverage"))
        expected_min_coverage = _numeric(compare_contract.get("required_min_coverage"))
        checks.append(
            _check(
                "contract_compare_min_coverage",
                actual_min_coverage == expected_min_coverage,
                {"actual": actual_min_coverage, "required": expected_min_coverage},
            )
        )
    if "max_rms_diff" in compare_contract:
        rms = _numeric(compare_payload.get("rms_diff"))
        required = _numeric(compare_contract.get("max_rms_diff"))
        checks.append(
            _check(
                "contract_max_rms_diff",
                rms is not None and required is not None and rms <= required,
                {"actual": rms, "required_max": required},
            )
        )
    if "max_abs_diff_p99" in compare_contract:
        p99 = _numeric(compare_payload.get("abs_diff_p99"))
        required = _numeric(compare_contract.get("max_abs_diff_p99"))
        checks.append(
            _check(
                "contract_max_abs_diff_p99",
                p99 is not None and required is not None and p99 <= required,
                {"actual": p99, "required_max": required},
            )
        )
    if "min_coverage_fraction" in compare_contract:
        coverage_fraction = _numeric(region.get("coverage_fraction"))
        required = _numeric(compare_contract.get("min_coverage_fraction"))
        checks.append(
            _check(
                "contract_min_coverage_fraction",
                coverage_fraction is not None and required is not None and coverage_fraction >= required,
                {"actual": coverage_fraction, "required": required},
            )
        )
    return checks
