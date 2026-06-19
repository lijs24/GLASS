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


def _number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _sum_backend_counts(artifacts: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for artifact in artifacts:
        io_pipeline = artifact.get("resident_io_pipeline")
        if not isinstance(io_pipeline, dict):
            continue
        backend_counts = io_pipeline.get("fits_backend_counts")
        if not isinstance(backend_counts, dict):
            continue
        for key, value in backend_counts.items():
            counts[str(key)] = counts.get(str(key), 0) + int(value or 0)
    return dict(sorted(counts.items()))


def _first_artifact_io(artifacts: list[dict[str, Any]]) -> dict[str, Any]:
    if not artifacts:
        return {}
    io_pipeline = artifacts[0].get("resident_io_pipeline")
    return io_pipeline if isinstance(io_pipeline, dict) else {}


def _frame_count(artifacts: list[dict[str, Any]]) -> int:
    total = 0
    for artifact in artifacts:
        frame_ids = artifact.get("frame_ids")
        if isinstance(frame_ids, list):
            total += len(frame_ids)
    return total


def _raw_selection_summary(artifacts: list[dict[str, Any]]) -> dict[str, Any]:
    checked = 0
    eligible = 0
    ineligible_samples: list[dict[str, Any]] = []
    fallback_counts: dict[str, int] = {}
    selected_all = True
    runtime_eligible_all = True
    checked_all = True
    for artifact in artifacts:
        io_pipeline = artifact.get("resident_io_pipeline")
        selection = io_pipeline.get("resident_fits_auto_selection") if isinstance(io_pipeline, dict) else None
        raw = selection.get("raw_u16_gpu") if isinstance(selection, dict) else None
        if not isinstance(raw, dict):
            selected_all = False
            runtime_eligible_all = False
            checked_all = False
            continue
        selected_all = selected_all and raw.get("selected") is True
        runtime_eligible_all = runtime_eligible_all and raw.get("runtime_eligible") is True
        checked_all = checked_all and raw.get("checked") is True
        checked += int(raw.get("checked_frame_count", 0) or 0)
        eligible += int(raw.get("eligible_frame_count", 0) or 0)
        for key, value in (raw.get("fallback_reason_counts") or {}).items():
            fallback_counts[str(key)] = fallback_counts.get(str(key), 0) + int(value or 0)
        samples = raw.get("ineligible_samples")
        if isinstance(samples, list):
            ineligible_samples.extend(item for item in samples if isinstance(item, dict))
    return {
        "checked_frame_count": checked,
        "eligible_frame_count": eligible,
        "selected_all_groups": selected_all,
        "runtime_eligible_all_groups": runtime_eligible_all,
        "checked_all_groups": checked_all,
        "fallback_reason_counts": dict(sorted(fallback_counts.items())),
        "ineligible_samples": ineligible_samples[:8],
    }


def _mask_summary(artifacts: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {
        "active_frame_count": 0,
        "masked_frame_count": 0,
        "unknown_zero_weight_frame_count": 0,
        "passed_all_groups": True,
    }
    for artifact in artifacts:
        contract = artifact.get("resident_frame_mask_contract")
        contract_summary = contract.get("summary") if isinstance(contract, dict) else None
        if not isinstance(contract_summary, dict):
            summary["passed_all_groups"] = False
            continue
        summary["active_frame_count"] += int(contract_summary.get("active_frame_count", 0) or 0)
        summary["masked_frame_count"] += int(contract_summary.get("masked_frame_count", 0) or 0)
        summary["unknown_zero_weight_frame_count"] += int(
            contract_summary.get("unknown_zero_weight_frame_count", 0) or 0
        )
        summary["passed_all_groups"] = summary["passed_all_groups"] and contract_summary.get("passed") is True
    return summary


def _timing_summary(run: Path, artifacts: list[dict[str, Any]]) -> dict[str, Any]:
    run_timing_path = run / "run_timing.json"
    run_timing = _load_json_object(run_timing_path) if run_timing_path.exists() else {}
    light_bucket = 0.0
    h2d_cal = 0.0
    output_write = 0.0
    for artifact in artifacts:
        timing = artifact.get("timing_s")
        if not isinstance(timing, dict):
            continue
        light_bucket += float(timing.get("light_read_upload_calibrate", 0.0) or 0.0)
        h2d_cal += float(timing.get("light_h2d_calibrate_store", 0.0) or 0.0)
        output_write += float(timing.get("output_write", 0.0) or 0.0)
    return {
        "run_elapsed_s": _number(run_timing.get("total_elapsed_s")),
        "light_read_upload_calibrate_s": light_bucket,
        "light_h2d_calibrate_store_s": h2d_cal,
        "output_write_s": output_write,
    }


def _load_run(run: str | Path) -> dict[str, Any]:
    root = Path(run)
    resident = _load_json_object(root / "resident_artifacts.json")
    artifacts = resident.get("artifacts") if isinstance(resident.get("artifacts"), list) else []
    artifacts = [item for item in artifacts if isinstance(item, dict)]
    dq_path = root / "resident_dq_pixel_closure.json"
    dq = _load_json_object(dq_path) if dq_path.exists() else {}
    return {
        "path": str(root),
        "io": _first_artifact_io(artifacts),
        "frame_count": _frame_count(artifacts),
        "backend_counts": _sum_backend_counts(artifacts),
        "raw_selection": _raw_selection_summary(artifacts),
        "mask_summary": _mask_summary(artifacts),
        "dq_summary": dq.get("summary") if isinstance(dq.get("summary"), dict) else {},
        "timing": _timing_summary(root, artifacts),
    }


def _compare_check(prefix: str, compare_payload: dict[str, Any], max_rms: float, max_abs: float) -> list[dict[str, Any]]:
    rms = _number(compare_payload.get("rms_diff"))
    max_abs_diff = _number(compare_payload.get("max_abs_diff"))
    return [
        _check(
            f"{prefix}_shape_matches",
            compare_payload.get("shape_match") is True,
            {"actual": compare_payload.get("shape_match")},
        ),
        _check(
            f"{prefix}_rms_within_limit",
            rms is not None and rms <= max_rms,
            {"actual": rms, "required_max": max_rms},
        ),
        _check(
            f"{prefix}_max_abs_within_limit",
            max_abs_diff is not None and max_abs_diff <= max_abs,
            {"actual": max_abs_diff, "required_max": max_abs},
        ),
    ]


def build_resident_fits_auto_regression(
    run: str | Path,
    *,
    compare_explicit: str | Path,
    compare_control: str | Path,
    explicit_run: str | Path | None = None,
    control_run: str | Path | None = None,
    min_lights: int = 200,
    expected_active: int | None = 193,
    expected_masked: int | None = 7,
    expected_unknown_zero_weight: int | None = 0,
    expected_requested_mode: str = "auto",
    expected_effective_mode: str = "native_u16_gpu",
    expected_backend: str = "native_u16be_raw",
    max_rms_diff: float = 0.0,
    max_abs_diff: float = 0.0,
    max_total_vs_explicit_ratio: float = 1.10,
    max_total_vs_control_ratio: float = 0.90,
    max_light_bucket_vs_control_ratio: float = 0.70,
) -> dict[str, Any]:
    run_payload = _load_run(run)
    explicit_payload = _load_run(explicit_run) if explicit_run else None
    control_payload = _load_run(control_run) if control_run else None
    compare_explicit_payload = _load_json_object(compare_explicit)
    compare_control_payload = _load_json_object(compare_control)
    io = run_payload["io"]
    raw = run_payload["raw_selection"]
    mask = run_payload["mask_summary"]
    dq = run_payload["dq_summary"]
    timing = run_payload["timing"]
    backend_counts = run_payload["backend_counts"]

    checks: list[dict[str, Any]] = [
        _check(
            "minimum_light_count",
            run_payload["frame_count"] >= int(min_lights),
            {"actual": run_payload["frame_count"], "required_min": int(min_lights)},
        ),
        _check(
            "fits_read_mode_requested_matches",
            io.get("fits_read_mode_requested", io.get("fits_read_mode")) == expected_requested_mode,
            {
                "actual": io.get("fits_read_mode_requested", io.get("fits_read_mode")),
                "expected": expected_requested_mode,
            },
        ),
        _check(
            "fits_read_mode_effective_matches",
            io.get("fits_read_mode_effective") == expected_effective_mode,
            {"actual": io.get("fits_read_mode_effective"), "expected": expected_effective_mode},
        ),
        _check(
            "raw_gpu_selected_for_all_groups",
            raw["selected_all_groups"] is True and raw["checked_all_groups"] is True,
            raw,
        ),
        _check(
            "raw_gpu_all_checked_frames_eligible",
            raw["checked_frame_count"] >= min_lights
            and raw["eligible_frame_count"] == raw["checked_frame_count"]
            and not raw["fallback_reason_counts"],
            raw,
        ),
        _check(
            "raw_gpu_runtime_eligible",
            raw["runtime_eligible_all_groups"] is True,
            raw,
        ),
        _check(
            "raw_gpu_decode_enabled",
            io.get("raw_gpu_decode_enabled") is True,
            {"actual": io.get("raw_gpu_decode_enabled")},
        ),
        _check(
            "expected_backend_count",
            int(backend_counts.get(expected_backend, 0)) >= min_lights,
            {"backend_counts": backend_counts, "expected_backend": expected_backend, "required_min": min_lights},
        ),
        _check(
            "frame_mask_contract_passed",
            mask["passed_all_groups"] is True,
            mask,
        ),
        _check(
            "dq_pixel_closure_passed",
            dq.get("passed") is True,
            dq,
        ),
    ]
    if expected_active is not None:
        checks.append(
            _check(
                "active_frame_count_matches",
                mask["active_frame_count"] == int(expected_active),
                {"actual": mask["active_frame_count"], "expected": int(expected_active)},
            )
        )
    if expected_masked is not None:
        checks.append(
            _check(
                "masked_frame_count_matches",
                mask["masked_frame_count"] == int(expected_masked),
                {"actual": mask["masked_frame_count"], "expected": int(expected_masked)},
            )
        )
    if expected_unknown_zero_weight is not None:
        checks.append(
            _check(
                "unknown_zero_weight_count_matches",
                mask["unknown_zero_weight_frame_count"] == int(expected_unknown_zero_weight),
                {
                    "actual": mask["unknown_zero_weight_frame_count"],
                    "expected": int(expected_unknown_zero_weight),
                },
            )
        )
    checks.extend(_compare_check("auto_vs_explicit", compare_explicit_payload, max_rms_diff, max_abs_diff))
    checks.extend(_compare_check("auto_vs_control", compare_control_payload, max_rms_diff, max_abs_diff))

    run_total = _number(timing.get("run_elapsed_s"))
    checks.append(
        _check(
            "run_total_timing_present",
            run_total is not None and run_total > 0.0,
            {"actual_s": run_total},
        )
    )
    if explicit_payload is not None:
        explicit_total = _number(explicit_payload["timing"].get("run_elapsed_s"))
        checks.append(
            _check(
                "run_total_close_to_explicit_raw_gpu",
                run_total is not None
                and explicit_total is not None
                and run_total <= explicit_total * float(max_total_vs_explicit_ratio),
                {
                    "actual_s": run_total,
                    "explicit_s": explicit_total,
                    "required_ratio_max": float(max_total_vs_explicit_ratio),
                },
            )
        )
    if control_payload is not None:
        control_total = _number(control_payload["timing"].get("run_elapsed_s"))
        control_light = _number(control_payload["timing"].get("light_read_upload_calibrate_s"))
        run_light = _number(timing.get("light_read_upload_calibrate_s"))
        checks.append(
            _check(
                "run_total_faster_than_control",
                run_total is not None
                and control_total is not None
                and run_total <= control_total * float(max_total_vs_control_ratio),
                {
                    "actual_s": run_total,
                    "control_s": control_total,
                    "required_ratio_max": float(max_total_vs_control_ratio),
                },
            )
        )
        checks.append(
            _check(
                "light_bucket_faster_than_control",
                run_light is not None
                and control_light is not None
                and run_light <= control_light * float(max_light_bucket_vs_control_ratio),
                {
                    "actual_s": run_light,
                    "control_s": control_light,
                    "required_ratio_max": float(max_light_bucket_vs_control_ratio),
                },
            )
        )

    failed = [item for item in checks if not item.get("passed")]
    return {
        "schema_version": 1,
        "artifact_type": "resident_fits_auto_regression",
        "created_at": now_iso(),
        "status": "passed" if not failed else "failed",
        "passed": not failed,
        "run": run_payload,
        "explicit_run": explicit_payload,
        "control_run": control_payload,
        "compare_explicit_path": str(compare_explicit),
        "compare_control_path": str(compare_control),
        "thresholds": {
            "min_lights": int(min_lights),
            "expected_active": expected_active,
            "expected_masked": expected_masked,
            "expected_unknown_zero_weight": expected_unknown_zero_weight,
            "expected_requested_mode": expected_requested_mode,
            "expected_effective_mode": expected_effective_mode,
            "expected_backend": expected_backend,
            "max_rms_diff": float(max_rms_diff),
            "max_abs_diff": float(max_abs_diff),
            "max_total_vs_explicit_ratio": float(max_total_vs_explicit_ratio),
            "max_total_vs_control_ratio": float(max_total_vs_control_ratio),
            "max_light_bucket_vs_control_ratio": float(max_light_bucket_vs_control_ratio),
        },
        "checks": checks,
        "failed_checks": [item["name"] for item in failed],
        "summary": {
            "effective_mode": io.get("fits_read_mode_effective"),
            "backend_counts": backend_counts,
            "checked_frame_count": raw["checked_frame_count"],
            "eligible_frame_count": raw["eligible_frame_count"],
            "active_frame_count": mask["active_frame_count"],
            "masked_frame_count": mask["masked_frame_count"],
            "unknown_zero_weight_frame_count": mask["unknown_zero_weight_frame_count"],
            "run_elapsed_s": run_total,
            "light_read_upload_calibrate_s": timing.get("light_read_upload_calibrate_s"),
            "failed_check_count": len(failed),
        },
    }


def write_resident_fits_auto_regression(
    path: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(path, payload)
    if markdown is None:
        return
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    thresholds = payload.get("thresholds") if isinstance(payload.get("thresholds"), dict) else {}
    lines = [
        "# Resident FITS Auto Regression",
        "",
        f"- Status: {payload.get('status')}",
        f"- Passed: {payload.get('passed')}",
        f"- Effective mode: {summary.get('effective_mode')}",
        f"- Checked/eligible frames: {summary.get('checked_frame_count')} / {summary.get('eligible_frame_count')}",
        f"- Active/masked/unknown zero-weight: {summary.get('active_frame_count')} / {summary.get('masked_frame_count')} / {summary.get('unknown_zero_weight_frame_count')}",
        f"- Run elapsed s: {summary.get('run_elapsed_s')}",
        f"- Light read/upload/calibrate s: {summary.get('light_read_upload_calibrate_s')}",
        f"- Expected backend: {thresholds.get('expected_backend')}",
        "",
        "## Failed Checks",
        "",
    ]
    failed = payload.get("failed_checks") if isinstance(payload.get("failed_checks"), list) else []
    if failed:
        lines.extend(f"- {item}" for item in failed)
    else:
        lines.append("- None")
    Path(markdown).write_text("\n".join(lines) + "\n", encoding="utf-8")
