from __future__ import annotations

from pathlib import Path
from typing import Any

from glass.engine.rejection import RESIDENT_WINSORIZED_SIGMA_HARDENED_MODE
from glass.io.json_io import read_json, write_json
from glass.models import now_iso


DEFAULT_CONTRACT_PATH = Path("benchmarks/resident_winsorized_microbenchmark_contract.json")


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


def _nested(mapping: dict[str, Any], *keys: str) -> Any:
    current: Any = mapping
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _named_check(artifact: dict[str, Any], name: str) -> dict[str, Any]:
    checks = artifact.get("checks")
    if not isinstance(checks, list):
        return {}
    for item in checks:
        if isinstance(item, dict) and item.get("name") == name:
            return item
    return {}


def _exact_config_check(artifact: dict[str, Any], expected: dict[str, Any], *, tolerance: float) -> list[dict[str, Any]]:
    config = artifact.get("config") if isinstance(artifact.get("config"), dict) else {}
    rows: list[dict[str, Any]] = []
    for key, expected_value in sorted(expected.items()):
        actual = config.get(key)
        if isinstance(expected_value, int) and not isinstance(expected_value, bool):
            passed = actual == expected_value
        elif isinstance(expected_value, float):
            actual_number = _number(actual)
            passed = actual_number is not None and abs(actual_number - expected_value) <= tolerance
        else:
            passed = actual == expected_value
        rows.append(
            _check(
                f"config_{key}_matches_contract",
                passed,
                {"actual": actual, "expected": expected_value, "tolerance": tolerance},
            )
        )
    return rows


def _stat_threshold_check(
    artifact: dict[str, Any],
    *,
    map_name: str,
    stat_name: str,
    required_max: float,
) -> dict[str, Any]:
    actual = _number(_nested(artifact, "comparisons", "hardened_vs_cpu", map_name, stat_name))
    return _check(
        f"hardened_{map_name}_{stat_name}_within_contract",
        actual is not None and actual <= required_max,
        {"actual": actual, "required_max": float(required_max)},
    )


def _timing_present_check(artifact: dict[str, Any], key: str) -> dict[str, Any]:
    value = _number(_nested(artifact, "timing_s", key))
    return _check(f"timing_{key}_present", value is not None and value >= 0.0, {"actual_s": value})


def build_resident_winsorized_benchmark_audit(
    artifact: str | Path,
    *,
    contract: str | Path = DEFAULT_CONTRACT_PATH,
) -> dict[str, Any]:
    artifact_path = Path(artifact)
    contract_path = Path(contract)
    benchmark = _load_json_object(artifact_path)
    contract_payload = _load_json_object(contract_path)
    requirements = (
        contract_payload.get("requirements")
        if isinstance(contract_payload.get("requirements"), dict)
        else {}
    )

    checks: list[dict[str, Any]] = [
        _check(
            "artifact_type_matches",
            benchmark.get("artifact_type") == requirements.get("artifact_type", "resident_winsorized_benchmark"),
            {
                "actual": benchmark.get("artifact_type"),
                "expected": requirements.get("artifact_type", "resident_winsorized_benchmark"),
            },
        )
    ]
    if bool(requirements.get("require_passed", True)):
        checks.append(
            _check(
                "benchmark_passed",
                benchmark.get("passed") is True and benchmark.get("status") == "passed",
                {"passed": benchmark.get("passed"), "status": benchmark.get("status")},
            )
        )
    if bool(requirements.get("require_cuda_available", True)):
        cuda_check = _named_check(benchmark, "cuda_available")
        checks.append(
            _check(
                "cuda_available",
                benchmark.get("status") != "cuda_unavailable" and cuda_check.get("passed") is True,
                {"status": benchmark.get("status"), "benchmark_check": cuda_check},
            )
        )

    config_requirements = (
        requirements.get("config") if isinstance(requirements.get("config"), dict) else {}
    )
    checks.extend(
        _exact_config_check(
            benchmark,
            config_requirements,
            tolerance=float(requirements.get("config_float_tolerance", 1.0e-12)),
        )
    )

    hardened_requirements = (
        requirements.get("hardened_vs_cpu")
        if isinstance(requirements.get("hardened_vs_cpu"), dict)
        else {}
    )
    master_limits = (
        hardened_requirements.get("master")
        if isinstance(hardened_requirements.get("master"), dict)
        else {}
    )
    if "rms_max" in master_limits:
        checks.append(
            _stat_threshold_check(
                benchmark,
                map_name="master",
                stat_name="rms",
                required_max=float(master_limits["rms_max"]),
            )
        )
    if "max_abs_max" in master_limits:
        checks.append(
            _stat_threshold_check(
                benchmark,
                map_name="master",
                stat_name="max_abs",
                required_max=float(master_limits["max_abs_max"]),
            )
        )
    map_max_abs = hardened_requirements.get("map_max_abs_max")
    if map_max_abs is not None:
        for map_name in ["weight", "coverage", "low_rejection", "high_rejection"]:
            checks.append(
                _stat_threshold_check(
                    benchmark,
                    map_name=map_name,
                    stat_name="max_abs",
                    required_max=float(map_max_abs),
                )
            )

    timing_requirements = (
        requirements.get("timing")
        if isinstance(requirements.get("timing"), dict)
        else {}
    )
    for key in timing_requirements.get("required_timing_keys", []):
        checks.append(_timing_present_check(benchmark, str(key)))

    hardened_timing = (
        benchmark.get("cuda_hardened_timing")
        if isinstance(benchmark.get("cuda_hardened_timing"), dict)
        else {}
    )
    expected_mode = timing_requirements.get("resident_winsorized_mode", RESIDENT_WINSORIZED_SIGMA_HARDENED_MODE)
    checks.append(
        _check(
            "hardened_timing_mode_matches_contract",
            hardened_timing.get("resident_winsorized_mode") == expected_mode,
            {"actual": hardened_timing.get("resident_winsorized_mode"), "expected": expected_mode},
        )
    )
    expected_method = timing_requirements.get("native_method")
    if expected_method:
        checks.append(
            _check(
                "hardened_native_method_matches_contract",
                hardened_timing.get("native_method") == expected_method,
                {"actual": hardened_timing.get("native_method"), "expected": expected_method},
            )
        )

    fast_requirements = (
        requirements.get("fast_approx")
        if isinstance(requirements.get("fast_approx"), dict)
        else {}
    )
    if bool(fast_requirements.get("require_present", True)):
        fast_stats = _nested(benchmark, "comparisons", "fast_approx_vs_cpu", "master")
        fast_timing = benchmark.get("cuda_fast_approx_timing")
        checks.append(
            _check(
                "fast_approx_context_present",
                isinstance(fast_stats, dict) and isinstance(fast_timing, dict),
                {"stats_present": isinstance(fast_stats, dict), "timing_present": isinstance(fast_timing, dict)},
                "Fast approximation is context only and is not required to match CPU parity.",
            )
        )

    failed = [item for item in checks if not item.get("passed")]
    return {
        "schema_version": 1,
        "artifact_type": "resident_winsorized_benchmark_audit",
        "created_at": now_iso(),
        "benchmark_path": str(artifact_path),
        "contract_path": str(contract_path),
        "contract_name": contract_payload.get("name"),
        "status": "passed" if not failed else "failed",
        "passed": not failed,
        "checks": checks,
        "failed_checks": [str(item.get("name")) for item in failed],
        "summary": {
            "benchmark_status": benchmark.get("status"),
            "benchmark_passed": benchmark.get("passed"),
            "frame_count": _nested(benchmark, "config", "frame_count"),
            "shape": [
                _nested(benchmark, "config", "height"),
                _nested(benchmark, "config", "width"),
            ],
            "hardened_master_rms": _nested(benchmark, "comparisons", "hardened_vs_cpu", "master", "rms"),
            "hardened_master_max_abs": _nested(
                benchmark,
                "comparisons",
                "hardened_vs_cpu",
                "master",
                "max_abs",
            ),
            "fast_approx_master_rms": _nested(
                benchmark,
                "comparisons",
                "fast_approx_vs_cpu",
                "master",
                "rms",
            ),
            "cuda_hardened_s": _nested(benchmark, "timing_s", "cuda_hardened"),
            "cuda_fast_approx_s": _nested(benchmark, "timing_s", "cuda_fast_approx"),
            "cpu_baseline_s": _nested(benchmark, "timing_s", "cpu_baseline"),
        },
        "limitations": [
            "This audit validates the synthetic microbenchmark artifact only.",
            "Timing presence is required, but the default contract does not impose a wall-time limit.",
            "Fast approximation drift is reported as context; hardened CPU-parity agreement is the gate.",
        ],
    }


def _markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {}) if isinstance(payload.get("summary"), dict) else {}
    lines = [
        "# Resident Winsorized Benchmark Audit",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Passed: `{payload.get('passed')}`",
        f"- Contract: `{payload.get('contract_name')}`",
        f"- Benchmark: `{payload.get('benchmark_path')}`",
        f"- Frames: `{summary.get('frame_count')}`",
        f"- Shape: `{summary.get('shape')}`",
        f"- Hardened master RMS: `{summary.get('hardened_master_rms')}`",
        f"- Hardened master max abs: `{summary.get('hardened_master_max_abs')}`",
        f"- Fast approximation master RMS: `{summary.get('fast_approx_master_rms')}`",
        "",
        "## Checks",
        "",
        "| check | passed | note |",
        "| --- | ---: | --- |",
    ]
    for check in payload.get("checks", []):
        if not isinstance(check, dict):
            continue
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


def write_resident_winsorized_benchmark_audit(
    out: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(out, payload)
    if markdown is not None:
        Path(markdown).write_text(_markdown(payload), encoding="utf-8")
