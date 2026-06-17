from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from glass.io.json_io import write_json
from glass.models import now_iso
from glass.report.benchmark_contract import collect_frame_accounting_record, load_benchmark_contract


def _read_json_lenient(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def _numeric(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _check(name: str, passed: bool, evidence: dict[str, Any], *, required: bool = True, note: str = "") -> dict[str, Any]:
    return {
        "name": name,
        "passed": bool(passed),
        "required": bool(required),
        "evidence": evidence,
        "note": note,
    }


def _first_artifact(resident: dict[str, Any]) -> dict[str, Any]:
    artifacts = resident.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        return {}
    first = artifacts[0]
    return first if isinstance(first, dict) else {}


def _load_run_timing(run: Path) -> dict[str, Any]:
    path = run / "run_timing.json"
    if not path.exists():
        return {}
    payload = _read_json_lenient(path)
    return payload if isinstance(payload, dict) else {}


def _elapsed_from_timing(timing: dict[str, Any]) -> float | None:
    elapsed = _numeric(timing.get("total_elapsed_s"))
    if elapsed is not None:
        return elapsed
    stages = timing.get("stages")
    if not isinstance(stages, list):
        return None
    return float(sum(float((stage or {}).get("elapsed_s") or 0.0) for stage in stages if isinstance(stage, dict)))


def _load_compare(path: str | Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    payload = _read_json_lenient(path)
    if not isinstance(payload, dict):
        raise ValueError(f"compare JSON must be an object: {path}")
    region = payload.get("comparison_region") if isinstance(payload.get("comparison_region"), dict) else {}
    timing = payload.get("timing") if isinstance(payload.get("timing"), dict) else {}
    return {
        "path": str(path),
        "shape_match": payload.get("shape_match"),
        "rms_diff": _numeric(payload.get("rms_diff")),
        "abs_diff_p50": _numeric(payload.get("abs_diff_p50")),
        "abs_diff_p90": _numeric(payload.get("abs_diff_p90")),
        "abs_diff_p99": _numeric(payload.get("abs_diff_p99")),
        "abs_diff_p999": _numeric(payload.get("abs_diff_p999")),
        "relative_rms_diff": _numeric(payload.get("relative_rms_diff")),
        "coverage_fraction": _numeric(region.get("coverage_fraction")),
        "compared_pixels": region.get("compared_pixels"),
        "glass_time_seconds": _numeric(timing.get("glass_time_seconds")),
        "reference_time_seconds": _numeric(timing.get("reference_time_seconds")),
        "speedup_vs_reference": _numeric(timing.get("speedup_vs_reference")),
    }


def _tile_local_policy_from_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    weighting = artifact.get("resident_integration_weighting")
    if not isinstance(weighting, dict):
        return {}
    policy = weighting.get("tile_local_policy_replay")
    return policy if isinstance(policy, dict) else {}


def _summarize_tile_local_policy(policy: dict[str, Any]) -> dict[str, Any]:
    summary = policy.get("summary") if isinstance(policy.get("summary"), dict) else {}
    native_timing = policy.get("native_timing_s") if isinstance(policy.get("native_timing_s"), dict) else {}
    return {
        "present": bool(policy),
        "enabled": bool(policy.get("enabled")),
        "requested_mode": policy.get("requested_mode"),
        "effective_mode": policy.get("effective_mode"),
        "applied": bool(policy.get("applied")),
        "application_status": policy.get("application_status"),
        "native_method": policy.get("native_method"),
        "native_timing_s": native_timing,
        "native_elapsed_s": _numeric(native_timing.get("total")) or _numeric(native_timing.get("elapsed_s")),
        "target_group": policy.get("target_group"),
        "target_frame_count": len(policy.get("target_frame_ids") or []),
        "target_frame_count_applied": policy.get("target_frame_count_applied"),
        "target_frame_ids_missing": policy.get("target_frame_ids_missing") or [],
        "tile_count": policy.get("tile_count"),
        "tile_count_applied": policy.get("tile_count_applied"),
        "multiplier_min": policy.get("multiplier_min"),
        "multiplier_mean": policy.get("multiplier_mean"),
        "multiplier_max": policy.get("multiplier_max"),
        "replay_summary": {
            "recommendation": summary.get("recommendation"),
            "boost_tiles": summary.get("boost_tiles"),
            "downweight_tiles": summary.get("downweight_tiles"),
            "clamped_tiles": summary.get("clamped_tiles"),
            "moves_toward_reference": summary.get("moves_toward_reference"),
            "moves_away_from_reference": summary.get("moves_away_from_reference"),
            "mean_abs_residual_before": summary.get("mean_abs_residual_before"),
            "mean_abs_residual_after": summary.get("mean_abs_residual_after"),
        },
    }


def _load_run_summary(run: str | Path) -> dict[str, Any]:
    root = Path(run)
    timing = _load_run_timing(root)
    resident_path = root / "resident_artifacts.json"
    resident = _read_json_lenient(resident_path) if resident_path.exists() else {}
    resident = resident if isinstance(resident, dict) else {}
    artifact = _first_artifact(resident)
    timing_s = artifact.get("timing_s") if isinstance(artifact.get("timing_s"), dict) else {}
    accounting = collect_frame_accounting_record(root)
    summary = accounting.get("summary") if isinstance(accounting.get("summary"), dict) else {}
    return {
        "path": str(root),
        "elapsed_s": _elapsed_from_timing(timing),
        "backend": timing.get("backend") or resident.get("backend"),
        "memory_mode": timing.get("memory_mode"),
        "run_command_present": (root / "run_command.txt").exists(),
        "device": resident.get("device") if isinstance(resident.get("device"), dict) else None,
        "master_path": artifact.get("master_path"),
        "coverage_map_path": artifact.get("coverage_map_path"),
        "high_rejection_map_path": artifact.get("high_rejection_map_path"),
        "low_rejection_map_path": artifact.get("low_rejection_map_path"),
        "shape": artifact.get("shape") if isinstance(artifact.get("shape"), dict) else None,
        "memory_estimate": artifact.get("memory_estimate") if isinstance(artifact.get("memory_estimate"), dict) else {},
        "timing_s": {
            key: timing_s.get(key)
            for key in [
                "master_build_or_load",
                "light_read_upload_calibrate",
                "light_read_wait_wall",
                "light_h2d_calibrate_store",
                "resident_registration_warp",
                "resident_registration_component_accounted",
                "resident_integration",
                "output_write",
                "gc",
            ]
            if key in timing_s
        },
        "frame_accounting": accounting,
        "frame_accounting_summary": {
            "input_light_frames": summary.get("input_light_frames"),
            "integrated_frames": summary.get("integrated_frames"),
            "zero_weight_frames": summary.get("zero_weight_frames"),
            "registration_accepted_frames": summary.get("registration_accepted_frames"),
            "final_status_counts": summary.get("final_status_counts"),
            "integration_source_stage": accounting.get("integration_source_stage"),
        },
        "tile_local_policy": _summarize_tile_local_policy(_tile_local_policy_from_artifact(artifact)),
    }


def _comparison_checks(
    compare: dict[str, Any],
    contract: dict[str, Any] | None,
    *,
    prefix: str,
    required: bool,
) -> list[dict[str, Any]]:
    checks = [
        _check(
            f"{prefix}_shape_match",
            compare.get("shape_match") is True,
            {"actual": compare.get("shape_match"), "required": True},
            required=required,
        )
    ]
    comparison_contract = (contract or {}).get("comparison") if contract else {}
    if isinstance(comparison_contract, dict):
        min_coverage = _numeric(comparison_contract.get("min_coverage_fraction"))
        max_rms = _numeric(comparison_contract.get("max_rms_diff"))
        max_p99 = _numeric(comparison_contract.get("max_abs_diff_p99"))
        if min_coverage is not None:
            coverage = _numeric(compare.get("coverage_fraction"))
            checks.append(
                _check(
                    f"{prefix}_minimum_coverage_fraction",
                    coverage is not None and coverage >= min_coverage,
                    {"actual": coverage, "required": min_coverage},
                    required=required,
                )
            )
        if max_rms is not None:
            rms = _numeric(compare.get("rms_diff"))
            checks.append(
                _check(
                    f"{prefix}_maximum_rms_diff",
                    rms is not None and rms <= max_rms,
                    {"actual": rms, "required_max": max_rms},
                    required=required,
                )
            )
        if max_p99 is not None:
            p99 = _numeric(compare.get("abs_diff_p99"))
            checks.append(
                _check(
                    f"{prefix}_maximum_abs_diff_p99",
                    p99 is not None and p99 <= max_p99,
                    {"actual": p99, "required_max": max_p99},
                    required=required,
                )
            )
    return checks


def _frame_accounting_key(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "input_light_frames": summary.get("input_light_frames"),
        "integrated_frames": summary.get("integrated_frames"),
        "zero_weight_frames": summary.get("zero_weight_frames"),
        "registration_accepted_frames": summary.get("registration_accepted_frames"),
        "final_status_counts": summary.get("final_status_counts"),
    }


def build_tile_local_apply_experiment(
    *,
    baseline_run: str | Path,
    candidate_run: str | Path,
    replay: str | Path,
    benchmark_contract: str | Path | None = None,
    baseline_compare_json: str | Path | None = None,
    candidate_compare_json: str | Path | None = None,
    candidate_vs_baseline_json: str | Path | None = None,
) -> dict[str, Any]:
    contract = load_benchmark_contract(benchmark_contract) if benchmark_contract is not None else None
    baseline = _load_run_summary(baseline_run)
    candidate = _load_run_summary(candidate_run)
    replay_payload = _read_json_lenient(replay)
    if not isinstance(replay_payload, dict) or replay_payload.get("artifact_type") != "tile_local_policy_replay":
        raise ValueError("replay must be a tile_local_policy_replay artifact")

    baseline_compare = _load_compare(baseline_compare_json)
    candidate_compare = _load_compare(candidate_compare_json)
    candidate_vs_baseline = _load_compare(candidate_vs_baseline_json)

    replay_summary = replay_payload.get("summary") if isinstance(replay_payload.get("summary"), dict) else {}
    target_frame_ids = replay_payload.get("target_frame_ids") if isinstance(replay_payload.get("target_frame_ids"), list) else []
    candidate_policy = candidate["tile_local_policy"]
    baseline_accounting = _frame_accounting_key(baseline["frame_accounting_summary"])
    candidate_accounting = _frame_accounting_key(candidate["frame_accounting_summary"])
    checks: list[dict[str, Any]] = [
        _check(
            "tile_local_policy_applied",
            candidate_policy.get("applied") is True
            and str(candidate_policy.get("application_status") or "").startswith("applied"),
            {
                "applied": candidate_policy.get("applied"),
                "application_status": candidate_policy.get("application_status"),
                "requested_mode": candidate_policy.get("requested_mode"),
                "effective_mode": candidate_policy.get("effective_mode"),
            },
        ),
        _check(
            "tile_local_policy_scope_matches_replay",
            int(candidate_policy.get("tile_count_applied") or -1) == int(replay_payload.get("tile_count") or -2)
            and int(candidate_policy.get("target_frame_count_applied") or -1) == len(target_frame_ids)
            and not candidate_policy.get("target_frame_ids_missing"),
            {
                "candidate_tile_count_applied": candidate_policy.get("tile_count_applied"),
                "replay_tile_count": replay_payload.get("tile_count"),
                "candidate_target_frame_count_applied": candidate_policy.get("target_frame_count_applied"),
                "replay_target_frame_count": len(target_frame_ids),
                "missing_target_frame_ids": candidate_policy.get("target_frame_ids_missing"),
            },
        ),
        _check(
            "localized_replay_direction",
            replay_summary.get("recommendation") == "tile_local_replay_promising"
            and int(replay_summary.get("moves_toward_reference") or 0)
            >= int(replay_summary.get("known_direction_tiles") or 0)
            and _numeric(replay_summary.get("mean_abs_residual_after")) is not None
            and _numeric(replay_summary.get("mean_abs_residual_before")) is not None
            and float(replay_summary["mean_abs_residual_after"]) < float(replay_summary["mean_abs_residual_before"]),
            {
                "recommendation": replay_summary.get("recommendation"),
                "known_direction_tiles": replay_summary.get("known_direction_tiles"),
                "moves_toward_reference": replay_summary.get("moves_toward_reference"),
                "moves_away_from_reference": replay_summary.get("moves_away_from_reference"),
                "mean_abs_residual_before": replay_summary.get("mean_abs_residual_before"),
                "mean_abs_residual_after": replay_summary.get("mean_abs_residual_after"),
            },
            note="This is the bounded replay prediction that justified the native apply experiment.",
        ),
        _check(
            "frame_accounting_matches_baseline",
            candidate_accounting == baseline_accounting,
            {"baseline": baseline_accounting, "candidate": candidate_accounting},
        ),
    ]

    frame_contract = (contract or {}).get("frame_accounting") if contract else {}
    if isinstance(frame_contract, dict) and frame_contract:
        expected = {
            "input_light_frames": frame_contract.get("required_input_light_frames"),
            "integrated_frames": frame_contract.get("required_integrated_frames"),
            "zero_weight_frames": frame_contract.get("required_zero_weight_frames"),
            "registration_accepted_frames": frame_contract.get("required_registration_accepted_frames"),
            "final_status_counts": frame_contract.get("required_final_status_counts"),
        }
        checks.append(
            _check(
                "frame_accounting_matches_contract",
                all(expected[key] is None or candidate_accounting.get(key) == expected[key] for key in expected),
                {"candidate": candidate_accounting, "expected": expected},
            )
        )

    runtime_contract = (contract or {}).get("runtime") if contract else {}
    candidate_elapsed = _numeric(candidate.get("elapsed_s"))
    if isinstance(runtime_contract, dict) and runtime_contract:
        baseline_elapsed = _numeric(runtime_contract.get("release_baseline_elapsed_s"))
        max_factor = _numeric(runtime_contract.get("max_runtime_regression_factor"))
        if baseline_elapsed is not None and max_factor is not None:
            checks.append(
                _check(
                    "runtime_within_release_contract",
                    candidate_elapsed is not None and candidate_elapsed <= baseline_elapsed * max_factor,
                    {
                        "candidate_elapsed_s": candidate_elapsed,
                        "release_baseline_elapsed_s": baseline_elapsed,
                        "max_regression_factor": max_factor,
                        "required_max_s": baseline_elapsed * max_factor,
                    },
                )
            )
        reference_elapsed = _numeric(runtime_contract.get("external_reference_elapsed_s"))
        min_speedup = _numeric(runtime_contract.get("min_speedup_vs_reference"))
        speedup = reference_elapsed / candidate_elapsed if reference_elapsed is not None and candidate_elapsed else None
        if min_speedup is not None:
            checks.append(
                _check(
                    "speedup_within_release_contract",
                    speedup is not None and speedup >= min_speedup,
                    {"actual": speedup, "required": min_speedup, "reference_elapsed_s": reference_elapsed},
                )
            )

    if candidate_compare is None:
        checks.append(
            _check(
                "candidate_compare_available",
                False,
                {"path": None},
                note="A real apply experiment must compare the candidate master against the same reference.",
            )
        )
    else:
        checks.extend(
            _comparison_checks(candidate_compare, contract, prefix="candidate_compare", required=True)
        )

    if baseline_compare is not None:
        checks.extend(_comparison_checks(baseline_compare, contract, prefix="baseline_compare", required=False))
    if baseline_compare is not None and candidate_compare is not None:
        baseline_rms = _numeric(baseline_compare.get("rms_diff"))
        candidate_rms = _numeric(candidate_compare.get("rms_diff"))
        baseline_p99 = _numeric(baseline_compare.get("abs_diff_p99"))
        candidate_p99 = _numeric(candidate_compare.get("abs_diff_p99"))
        checks.append(
            _check(
                "candidate_global_compare_not_worse_than_baseline_20pct",
                baseline_rms is not None
                and candidate_rms is not None
                and baseline_p99 is not None
                and candidate_p99 is not None
                and candidate_rms <= max(baseline_rms * 1.2, baseline_rms + 1e-9)
                and candidate_p99 <= max(baseline_p99 * 1.2, baseline_p99 + 1e-9),
                {
                    "baseline_rms_diff": baseline_rms,
                    "candidate_rms_diff": candidate_rms,
                    "baseline_abs_diff_p99": baseline_p99,
                    "candidate_abs_diff_p99": candidate_p99,
                    "allowed_relative_growth": 1.2,
                },
                required=False,
                note="Diagnostic only: a bounded local policy may not improve full-frame metrics.",
            )
        )

    if candidate_vs_baseline is not None:
        checks.append(
            _check(
                "candidate_vs_baseline_drift_available",
                candidate_vs_baseline.get("shape_match") is True,
                {
                    "shape_match": candidate_vs_baseline.get("shape_match"),
                    "rms_diff": candidate_vs_baseline.get("rms_diff"),
                    "abs_diff_p99": candidate_vs_baseline.get("abs_diff_p99"),
                    "coverage_fraction": candidate_vs_baseline.get("coverage_fraction"),
                },
                required=False,
            )
        )

    required_checks = [item for item in checks if item.get("required")]
    required_passed = all(item["passed"] for item in required_checks)
    recommendation = (
        "promote_to_bounded_policy_sweep"
        if required_passed
        else "hold_tile_local_apply"
    )
    return {
        "schema_version": 1,
        "artifact_type": "tile_local_apply_experiment",
        "created_at": now_iso(),
        "baseline": baseline,
        "candidate": candidate,
        "replay": {
            "path": str(replay),
            "target_group": replay_payload.get("target_group"),
            "target_frame_count": len(target_frame_ids),
            "tile_count": replay_payload.get("tile_count"),
            "summary": replay_summary,
        },
        "benchmark_contract": None
        if contract is None
        else {
            "path": str(benchmark_contract),
            "name": contract.get("name"),
            "schema_version": contract.get("schema_version"),
        },
        "comparisons": {
            "baseline_vs_reference": baseline_compare,
            "candidate_vs_reference": candidate_compare,
            "candidate_vs_baseline": candidate_vs_baseline,
        },
        "checks": checks,
        "summary": {
            "passed": required_passed,
            "status": "passed" if required_passed else "failed",
            "required_check_count": len(required_checks),
            "required_failed_count": sum(1 for item in required_checks if not item["passed"]),
            "diagnostic_failed_count": sum(1 for item in checks if not item["required"] and not item["passed"]),
            "recommendation": recommendation,
            "candidate_elapsed_s": candidate_elapsed,
            "baseline_elapsed_s": baseline.get("elapsed_s"),
            "candidate_tile_local_application_status": candidate_policy.get("application_status"),
            "candidate_tile_local_native_timing_s": candidate_policy.get("native_timing_s"),
        },
        "limitations": [
            "This audit verifies a bounded real apply experiment from existing artifacts.",
            "Localized improvement is inferred from the replay contract unless an additional localized compare package is supplied externally.",
            "The command does not mutate FITS data, resident CUDA buffers, or run state.",
        ],
    }


def write_tile_local_apply_experiment_markdown(path: str | Path, payload: dict[str, Any]) -> None:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    replay = payload.get("replay") if isinstance(payload.get("replay"), dict) else {}
    candidate = payload.get("candidate") if isinstance(payload.get("candidate"), dict) else {}
    policy = candidate.get("tile_local_policy") if isinstance(candidate.get("tile_local_policy"), dict) else {}
    lines = [
        "# Tile-Local Apply Experiment",
        "",
        f"- Status: `{summary.get('status')}`",
        f"- Recommendation: `{summary.get('recommendation')}`",
        f"- Baseline elapsed: `{summary.get('baseline_elapsed_s')}` s",
        f"- Candidate elapsed: `{summary.get('candidate_elapsed_s')}` s",
        f"- Application status: `{policy.get('application_status')}`",
        f"- Applied tiles / frames: `{policy.get('tile_count_applied')}` / `{policy.get('target_frame_count_applied')}`",
        f"- Replay tiles / frames: `{replay.get('tile_count')}` / `{replay.get('target_frame_count')}`",
        "",
        "## Checks",
        "",
    ]
    for item in payload.get("checks", []):
        if not isinstance(item, dict):
            continue
        marker = "PASS" if item.get("passed") else "FAIL"
        required = "required" if item.get("required") else "diagnostic"
        lines.append(f"- {marker} `{item.get('name')}` ({required}): {item.get('evidence')}")
    replay_summary = replay.get("summary") if isinstance(replay.get("summary"), dict) else {}
    lines.extend(
        [
            "",
            "## Local Replay",
            "",
            f"- Replay recommendation: `{replay_summary.get('recommendation')}`",
            f"- Toward / away: `{replay_summary.get('moves_toward_reference')}` / `{replay_summary.get('moves_away_from_reference')}`",
            f"- Mean abs residual before / after: `{replay_summary.get('mean_abs_residual_before')}` / `{replay_summary.get('mean_abs_residual_after')}`",
            "",
            "## Limitations",
            "",
        ]
    )
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_tile_local_apply_experiment(
    out: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(out, payload)
    if markdown is not None:
        write_tile_local_apply_experiment_markdown(markdown, payload)
