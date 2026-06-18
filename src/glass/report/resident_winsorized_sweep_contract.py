from __future__ import annotations

from pathlib import Path
from typing import Any

from glass.io.json_io import read_json, write_json
from glass.models import now_iso


DEFAULT_CONTRACT_PATH = Path("benchmarks/resident_winsorized_sweep_contract.json")


def _load_json_object(path: str | Path) -> dict[str, Any]:
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"JSON artifact must be an object: {path}")
    return payload


def _check(name: str, passed: bool, evidence: dict[str, Any], note: str = "") -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "evidence": evidence, "note": note}


def _number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _config(sweep: dict[str, Any]) -> dict[str, Any]:
    return sweep.get("config") if isinstance(sweep.get("config"), dict) else {}


def _summary(sweep: dict[str, Any]) -> dict[str, Any]:
    return sweep.get("summary") if isinstance(sweep.get("summary"), dict) else {}


def _runs(sweep: dict[str, Any]) -> list[dict[str, Any]]:
    runs = sweep.get("runs")
    return [item for item in runs if isinstance(item, dict)] if isinstance(runs, list) else []


def _run_by_frame_count(sweep: dict[str, Any], frame_count: int) -> dict[str, Any]:
    for run in _runs(sweep):
        if run.get("frame_count") == int(frame_count):
            return run
    return {}


def _nested(mapping: dict[str, Any], *keys: str) -> Any:
    current: Any = mapping
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _exact_config_checks(sweep: dict[str, Any], expected: dict[str, Any], *, tolerance: float) -> list[dict[str, Any]]:
    config = _config(sweep)
    checks: list[dict[str, Any]] = []
    for key, expected_value in sorted(expected.items()):
        actual = config.get(key)
        if isinstance(expected_value, list):
            passed = list(actual or []) == expected_value
        elif isinstance(expected_value, int) and not isinstance(expected_value, bool):
            passed = actual == expected_value
        elif isinstance(expected_value, float):
            actual_number = _number(actual)
            passed = actual_number is not None and abs(actual_number - expected_value) <= tolerance
        else:
            passed = actual == expected_value
        checks.append(
            _check(
                f"config_{key}_matches_contract",
                passed,
                {"actual": actual, "expected": expected_value, "tolerance": tolerance},
            )
        )
    return checks


def _run_stat_check(
    run: dict[str, Any],
    *,
    frame_count: int,
    map_name: str,
    stat_name: str,
    required_max: float,
) -> dict[str, Any]:
    actual = _number(_nested(run, "comparisons", "hardened_vs_cpu", map_name, stat_name))
    return _check(
        f"frame_{frame_count}_hardened_{map_name}_{stat_name}_within_contract",
        actual is not None and actual <= float(required_max),
        {"actual": actual, "required_max": float(required_max), "frame_count": int(frame_count)},
    )


def _timing_checks(run: dict[str, Any], *, frame_count: int, keys: list[str]) -> list[dict[str, Any]]:
    timing = run.get("timing_s") if isinstance(run.get("timing_s"), dict) else {}
    checks: list[dict[str, Any]] = []
    for key in keys:
        value = _number(timing.get(key))
        checks.append(
            _check(
                f"frame_{frame_count}_timing_{key}_present",
                value is not None and value >= 0.0,
                {"actual_s": value, "frame_count": int(frame_count)},
            )
        )
    return checks


def build_resident_winsorized_sweep_audit(
    artifact: str | Path,
    *,
    contract: str | Path = DEFAULT_CONTRACT_PATH,
) -> dict[str, Any]:
    artifact_path = Path(artifact)
    contract_path = Path(contract)
    sweep = _load_json_object(artifact_path)
    contract_payload = _load_json_object(contract_path)
    requirements = (
        contract_payload.get("requirements")
        if isinstance(contract_payload.get("requirements"), dict)
        else {}
    )
    config = _config(sweep)
    summary = _summary(sweep)

    checks: list[dict[str, Any]] = [
        _check(
            "artifact_type_matches",
            sweep.get("artifact_type") == requirements.get("artifact_type", "resident_winsorized_frame_count_sweep"),
            {
                "actual": sweep.get("artifact_type"),
                "expected": requirements.get("artifact_type", "resident_winsorized_frame_count_sweep"),
            },
        )
    ]
    if bool(requirements.get("require_passed", True)):
        checks.append(
            _check(
                "sweep_passed",
                sweep.get("passed") is True and sweep.get("status") == "passed",
                {"passed": sweep.get("passed"), "status": sweep.get("status")},
            )
        )

    expected_config = (
        requirements.get("config") if isinstance(requirements.get("config"), dict) else {}
    )
    checks.extend(
        _exact_config_checks(
            sweep,
            expected_config,
            tolerance=float(requirements.get("config_float_tolerance", 1.0e-12)),
        )
    )

    expected_frame_counts = [int(item) for item in expected_config.get("frame_counts", [])]
    actual_frame_counts = [int(run.get("frame_count")) for run in _runs(sweep) if run.get("frame_count") is not None]
    checks.append(
        _check(
            "run_frame_counts_match_contract",
            actual_frame_counts == expected_frame_counts,
            {"actual": actual_frame_counts, "expected": expected_frame_counts},
        )
    )
    checks.append(
        _check(
            "all_runs_passed",
            all(run.get("passed") is True for run in _runs(sweep)) and len(_runs(sweep)) == len(expected_frame_counts),
            {"run_count": len(_runs(sweep)), "expected_run_count": len(expected_frame_counts)},
        )
    )

    required_frame_count = int(requirements.get("required_frame_count", expected_config.get("required_frame_count", 200)))
    required_run = _run_by_frame_count(sweep, required_frame_count)
    checks.append(
        _check(
            "required_frame_count_present",
            bool(required_run),
            {"required_frame_count": required_frame_count},
        )
    )
    checks.append(
        _check(
            "required_frame_count_passed",
            bool(required_run) and required_run.get("passed") is True and summary.get("required_frame_count_passed") is True,
            {
                "required_frame_count": required_frame_count,
                "run_passed": required_run.get("passed"),
                "summary_required_frame_count_passed": summary.get("required_frame_count_passed"),
            },
        )
    )

    limits = (
        requirements.get("required_frame_hardened_vs_cpu")
        if isinstance(requirements.get("required_frame_hardened_vs_cpu"), dict)
        else {}
    )
    master_limits = limits.get("master") if isinstance(limits.get("master"), dict) else {}
    if "rms_max" in master_limits:
        checks.append(
            _run_stat_check(
                required_run,
                frame_count=required_frame_count,
                map_name="master",
                stat_name="rms",
                required_max=float(master_limits["rms_max"]),
            )
        )
    if "max_abs_max" in master_limits:
        checks.append(
            _run_stat_check(
                required_run,
                frame_count=required_frame_count,
                map_name="master",
                stat_name="max_abs",
                required_max=float(master_limits["max_abs_max"]),
            )
        )
    map_max_abs = limits.get("map_max_abs_max")
    if map_max_abs is not None:
        for map_name in ["weight", "coverage", "low_rejection", "high_rejection"]:
            checks.append(
                _run_stat_check(
                    required_run,
                    frame_count=required_frame_count,
                    map_name=map_name,
                    stat_name="max_abs",
                    required_max=float(map_max_abs),
                )
            )

    max_hardened_master_rms = _number(summary.get("max_hardened_master_rms"))
    max_rms_required = requirements.get("max_hardened_master_rms_max")
    if max_rms_required is not None:
        checks.append(
            _check(
                "max_hardened_master_rms_within_contract",
                max_hardened_master_rms is not None and max_hardened_master_rms <= float(max_rms_required),
                {"actual": max_hardened_master_rms, "required_max": float(max_rms_required)},
            )
        )

    timing = requirements.get("timing") if isinstance(requirements.get("timing"), dict) else {}
    required_timing_keys = [str(item) for item in timing.get("required_timing_keys", [])]
    checks.extend(_timing_checks(required_run, frame_count=required_frame_count, keys=required_timing_keys))

    expected_hardened_mode = timing.get("hardened_resident_winsorized_mode")
    if expected_hardened_mode:
        checks.append(
            _check(
                "required_frame_hardened_timing_mode_matches_contract",
                _nested(required_run, "cuda_hardened_timing", "resident_winsorized_mode") == expected_hardened_mode,
                {
                    "actual": _nested(required_run, "cuda_hardened_timing", "resident_winsorized_mode"),
                    "expected": expected_hardened_mode,
                },
            )
        )
    expected_hardened_method = timing.get("hardened_native_method")
    if expected_hardened_method:
        checks.append(
            _check(
                "required_frame_hardened_native_method_matches_contract",
                _nested(required_run, "cuda_hardened_timing", "native_method") == expected_hardened_method,
                {
                    "actual": _nested(required_run, "cuda_hardened_timing", "native_method"),
                    "expected": expected_hardened_method,
                },
            )
        )

    failed = [item for item in checks if not item.get("passed")]
    required_master = _nested(required_run, "comparisons", "hardened_vs_cpu", "master")
    required_timing = required_run.get("timing_s") if isinstance(required_run.get("timing_s"), dict) else {}
    return {
        "schema_version": 1,
        "artifact_type": "resident_winsorized_sweep_audit",
        "created_at": now_iso(),
        "sweep_path": str(artifact_path),
        "contract_path": str(contract_path),
        "contract_name": contract_payload.get("name"),
        "status": "passed" if not failed else "failed",
        "passed": not failed,
        "checks": checks,
        "failed_checks": [str(item.get("name")) for item in failed],
        "summary": {
            "sweep_status": sweep.get("status"),
            "sweep_passed": sweep.get("passed"),
            "frame_counts": config.get("frame_counts"),
            "run_count": len(_runs(sweep)),
            "required_frame_count": required_frame_count,
            "required_frame_count_passed": required_run.get("passed") is True,
            "required_frame_master": required_master,
            "required_frame_timing_s": required_timing,
            "max_hardened_master_rms": max_hardened_master_rms,
        },
        "limitations": [
            "This audit validates the synthetic frame-count sweep artifact only.",
            "The required 200-frame row is a small-image sample-count probe, not a real-data benchmark.",
            "Timing presence is required, but no wall-time upper bound is imposed.",
        ],
    }


def _markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {}) if isinstance(payload.get("summary"), dict) else {}
    required_master = (
        summary.get("required_frame_master")
        if isinstance(summary.get("required_frame_master"), dict)
        else {}
    )
    timing = (
        summary.get("required_frame_timing_s")
        if isinstance(summary.get("required_frame_timing_s"), dict)
        else {}
    )
    lines = [
        "# Resident Winsorized Sweep Audit",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Passed: `{payload.get('passed')}`",
        f"- Contract: `{payload.get('contract_name')}`",
        f"- Sweep: `{payload.get('sweep_path')}`",
        f"- Frame counts: `{summary.get('frame_counts')}`",
        f"- Required frame count: `{summary.get('required_frame_count')}`",
        f"- Required frame RMS: `{required_master.get('rms')}`",
        f"- Required frame max abs: `{required_master.get('max_abs')}`",
        f"- Required frame CPU s: `{timing.get('cpu_baseline')}`",
        f"- Required frame hardened CUDA s: `{timing.get('cuda_hardened')}`",
        f"- Max hardened master RMS: `{summary.get('max_hardened_master_rms')}`",
        "",
        "## Checks",
        "",
        "| check | passed | note |",
        "| --- | ---: | --- |",
    ]
    for check in payload.get("checks", []):
        if isinstance(check, dict):
            lines.append(f"| {check.get('name')} | `{check.get('passed')}` | {check.get('note', '')} |")
    lines.extend(["", "## Failed Checks", ""])
    failed = payload.get("failed_checks", [])
    if failed:
        for name in failed:
            lines.append(f"- `{name}`")
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def write_resident_winsorized_sweep_audit(
    out: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(out, payload)
    if markdown is not None:
        Path(markdown).write_text(_markdown(payload), encoding="utf-8")
