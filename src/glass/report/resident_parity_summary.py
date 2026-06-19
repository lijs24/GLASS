from __future__ import annotations

from pathlib import Path
from typing import Any

from glass.io.json_io import read_json, write_json
from glass.models import now_iso


def _read_json_object(path: str | Path) -> dict[str, Any]:
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"JSON artifact must be an object: {path}")
    return payload


def _optional_json_object(path: Path) -> dict[str, Any]:
    return _read_json_object(path) if path.exists() else {}


def _check(name: str, passed: bool, evidence: dict[str, Any], note: str = "") -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "evidence": evidence, "note": note}


def _number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_value(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _stage_times(timing: dict[str, Any]) -> dict[str, float]:
    stages = timing.get("stages") if isinstance(timing.get("stages"), list) else []
    rows: dict[str, float] = {}
    for item in stages:
        if not isinstance(item, dict) or item.get("stage") is None:
            continue
        value = _number(item.get("elapsed_s"))
        if value is not None:
            rows[str(item["stage"])] = value
    return rows


def _registration_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = payload.get("registration_results")
    if not isinstance(rows, list):
        rows = payload.get("results")
    return [item for item in rows or [] if isinstance(item, dict)]


def _registration_summary(run: Path) -> dict[str, Any]:
    payload = _optional_json_object(run / "registration_results.json")
    rows = _registration_rows(payload)
    status_counts: dict[str, int] = {}
    reference_ids: set[str] = set()
    models: set[str] = set()
    for row in rows:
        status = str(row.get("status") or "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
        if row.get("reference_frame_id") is not None:
            reference_ids.add(str(row["reference_frame_id"]))
        if row.get("transform_model") is not None:
            models.add(str(row["transform_model"]))
    payload_reference = payload.get("reference_frame_id")
    reference_frame_id = (
        str(payload_reference)
        if payload_reference is not None
        else sorted(reference_ids)[0]
        if len(reference_ids) == 1
        else None
    )
    failed_count = sum(
        count
        for status, count in status_counts.items()
        if status not in {"ok", "reference", "accepted"}
    )
    return {
        "present": bool(payload),
        "path": str(run / "registration_results.json"),
        "reference_frame_id": reference_frame_id,
        "row_count": len(rows),
        "status_counts": status_counts,
        "failed_count": failed_count,
        "reference_frame_ids": sorted(reference_ids),
        "transform_models": sorted(models),
        "method": payload.get("method"),
        "source_stage": payload.get("source_stage"),
    }


def _first_output(run: Path) -> dict[str, Any]:
    payload = _optional_json_object(run / "integration_results.json")
    outputs = payload.get("outputs") if isinstance(payload.get("outputs"), list) else []
    first = outputs[0] if outputs and isinstance(outputs[0], dict) else {}
    return first


def _integration_summary(run: Path) -> dict[str, Any]:
    output = _first_output(run)
    dq = output.get("dq_provenance_summary") if isinstance(output.get("dq_provenance_summary"), dict) else {}
    rejection = output.get("integration_rejection")
    if not isinstance(rejection, dict):
        stack = output.get("stack_engine_dq_provenance")
        rejection = (
            stack.get("rejection_policy")
            if isinstance(stack, dict) and isinstance(stack.get("rejection_policy"), dict)
            else {}
        )
    return {
        "present": bool(output),
        "backend": output.get("backend"),
        "frame_count": _int_value(output.get("frame_count")),
        "master_path": output.get("master_path"),
        "coverage_map_path": output.get("coverage_map_path"),
        "dq_map_path": output.get("dq_map_path"),
        "low_rejection_map_path": output.get("low_rejection_map_path"),
        "high_rejection_map_path": output.get("high_rejection_map_path"),
        "valid_pixels": _int_value(dq.get("valid_pixels")),
        "rejected_samples": _int_value(dq.get("rejected_samples")),
        "low_rejected_pixels": _int_value(dq.get("low_rejected_pixels")),
        "high_rejected_pixels": _int_value(dq.get("high_rejected_pixels")),
        "warp_edge_pixels": _int_value(dq.get("warp_edge_pixels")),
        "sample_accounting_status": (dq.get("sample_accounting_closure") or {}).get("status")
        if isinstance(dq.get("sample_accounting_closure"), dict)
        else None,
        "rejection": rejection,
    }


def _timing_summary(run: Path) -> dict[str, Any]:
    payload = _optional_json_object(run / "run_timing.json")
    return {
        "present": bool(payload),
        "path": str(run / "run_timing.json"),
        "backend": payload.get("backend"),
        "memory_mode": payload.get("memory_mode"),
        "total_elapsed_s": _number(payload.get("total_elapsed_s")),
        "stages": _stage_times(payload),
    }


def _contract_summary(run: Path) -> dict[str, Any]:
    payload = _optional_json_object(run / "resident_result_contract.json")
    checks = payload.get("checks") if isinstance(payload.get("checks"), list) else []
    failed = [item.get("name") for item in checks if isinstance(item, dict) and item.get("passed") is not True]
    return {
        "present": bool(payload),
        "path": str(run / "resident_result_contract.json"),
        "status": payload.get("status"),
        "passed": payload.get("passed"),
        "failed_checks": [str(item) for item in failed if item is not None],
    }


def _run_summary(run: str | Path, *, label: str) -> dict[str, Any]:
    root = Path(run)
    return {
        "label": label,
        "path": str(root),
        "exists": root.exists(),
        "timing": _timing_summary(root),
        "registration": _registration_summary(root),
        "integration": _integration_summary(root),
        "resident_result_contract": _contract_summary(root),
    }


def _compare_summary(path: str | Path) -> dict[str, Any]:
    target = Path(path)
    payload = _read_json_object(target)
    return {
        "path": str(target),
        "shape_match": payload.get("shape_match"),
        "rms_diff": _number(payload.get("rms_diff")),
        "relative_rms_diff": _number(payload.get("relative_rms_diff")),
        "abs_diff_p90": _number(payload.get("abs_diff_p90")),
        "abs_diff_p99": _number(payload.get("abs_diff_p99")),
        "max_abs_diff": _number(payload.get("max_abs_diff")),
        "glass_label": payload.get("glass_label"),
        "reference_label": payload.get("reference_label"),
    }


def _delta_int(left: int | None, right: int | None) -> int | None:
    return None if left is None or right is None else int(left) - int(right)


def build_resident_parity_summary(
    *,
    cpu_run: str | Path,
    resident_run: str | Path,
    compare_json: str | Path,
    cpu_label: str = "cpu_tile",
    resident_label: str = "cuda_resident",
    max_rms_diff: float = 0.1,
    max_relative_rms_diff: float = 0.001,
    max_rejected_sample_delta: int = 64,
    require_resident_contract: bool = True,
) -> dict[str, Any]:
    cpu = _run_summary(cpu_run, label=cpu_label)
    resident = _run_summary(resident_run, label=resident_label)
    compare = _compare_summary(compare_json)
    cpu_integration = cpu["integration"]
    resident_integration = resident["integration"]
    cpu_registration = cpu["registration"]
    resident_registration = resident["registration"]
    rejected_delta = _delta_int(
        resident_integration.get("rejected_samples"),
        cpu_integration.get("rejected_samples"),
    )
    frame_delta = _delta_int(
        resident_integration.get("frame_count"),
        cpu_integration.get("frame_count"),
    )
    elapsed_ratio = None
    resident_elapsed = resident["timing"].get("total_elapsed_s")
    cpu_elapsed = cpu["timing"].get("total_elapsed_s")
    if resident_elapsed is not None and cpu_elapsed not in (None, 0.0):
        elapsed_ratio = float(resident_elapsed) / float(cpu_elapsed)

    parity_checks = [
        _check("cpu_run_present", cpu["exists"], {"path": cpu["path"]}),
        _check("resident_run_present", resident["exists"], {"path": resident["path"]}),
        _check(
            "frame_count_match",
            frame_delta == 0,
            {
                "cpu_frame_count": cpu_integration.get("frame_count"),
                "resident_frame_count": resident_integration.get("frame_count"),
                "delta": frame_delta,
            },
        ),
        _check(
            "registration_reference_match",
            bool(cpu_registration.get("reference_frame_id"))
            and cpu_registration.get("reference_frame_id")
            == resident_registration.get("reference_frame_id"),
            {
                "cpu_reference_frame_id": cpu_registration.get("reference_frame_id"),
                "resident_reference_frame_id": resident_registration.get("reference_frame_id"),
            },
        ),
        _check(
            "registration_row_count_match",
            cpu_registration.get("row_count") == resident_registration.get("row_count"),
            {
                "cpu_rows": cpu_registration.get("row_count"),
                "resident_rows": resident_registration.get("row_count"),
            },
        ),
        _check(
            "compare_shape_match",
            compare.get("shape_match") is True,
            {"shape_match": compare.get("shape_match")},
        ),
        _check(
            "compare_rms_within_limit",
            compare.get("rms_diff") is not None and float(compare["rms_diff"]) <= float(max_rms_diff),
            {"rms_diff": compare.get("rms_diff"), "max_rms_diff": float(max_rms_diff)},
        ),
        _check(
            "compare_relative_rms_within_limit",
            compare.get("relative_rms_diff") is not None
            and float(compare["relative_rms_diff"]) <= float(max_relative_rms_diff),
            {
                "relative_rms_diff": compare.get("relative_rms_diff"),
                "max_relative_rms_diff": float(max_relative_rms_diff),
            },
        ),
        _check(
            "rejected_sample_delta_within_limit",
            rejected_delta is not None and abs(rejected_delta) <= int(max_rejected_sample_delta),
            {
                "cpu_rejected_samples": cpu_integration.get("rejected_samples"),
                "resident_rejected_samples": resident_integration.get("rejected_samples"),
                "delta": rejected_delta,
                "max_abs_delta": int(max_rejected_sample_delta),
            },
        ),
    ]
    contract_check = _check(
        "resident_result_contract_passed",
        resident["resident_result_contract"].get("passed") is True,
        resident["resident_result_contract"],
        note="Required for top-level pass unless require_resident_contract is false.",
    )
    parity_failed = [item for item in parity_checks if not item.get("passed")]
    contract_failed = [] if contract_check.get("passed") else [contract_check]
    parity_passed = not parity_failed
    passed = parity_passed and (not require_resident_contract or not contract_failed)
    return {
        "schema_version": 1,
        "artifact_type": "resident_parity_summary",
        "created_at": now_iso(),
        "status": "passed" if passed else "attention_required",
        "passed": passed,
        "parity_passed": parity_passed,
        "require_resident_contract": bool(require_resident_contract),
        "cpu": cpu,
        "resident": resident,
        "compare": compare,
        "deltas": {
            "elapsed_ratio_resident_vs_cpu": elapsed_ratio,
            "frame_count_delta": frame_delta,
            "rejected_sample_delta": rejected_delta,
            "valid_pixel_delta": _delta_int(
                resident_integration.get("valid_pixels"),
                cpu_integration.get("valid_pixels"),
            ),
            "low_rejected_pixel_delta": _delta_int(
                resident_integration.get("low_rejected_pixels"),
                cpu_integration.get("low_rejected_pixels"),
            ),
            "high_rejected_pixel_delta": _delta_int(
                resident_integration.get("high_rejected_pixels"),
                cpu_integration.get("high_rejected_pixels"),
            ),
        },
        "thresholds": {
            "max_rms_diff": float(max_rms_diff),
            "max_relative_rms_diff": float(max_relative_rms_diff),
            "max_rejected_sample_delta": int(max_rejected_sample_delta),
        },
        "checks": [*parity_checks, contract_check],
        "failed_checks": [str(item.get("name")) for item in [*parity_failed, *contract_failed]],
        "recommendation": (
            "parity_and_contract_ready"
            if passed
            else "fix_resident_result_contract"
            if parity_passed and contract_failed and require_resident_contract
            else "fix_resident_registration_or_dq_parity"
        ),
    }


def _markdown(payload: dict[str, Any]) -> str:
    cpu = payload.get("cpu") or {}
    resident = payload.get("resident") or {}
    compare = payload.get("compare") or {}
    deltas = payload.get("deltas") or {}
    lines = [
        "# Resident Parity Summary",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Passed: `{payload.get('passed')}`",
        f"- Parity passed: `{payload.get('parity_passed')}`",
        f"- Recommendation: `{payload.get('recommendation')}`",
        "",
        "## Runs",
        "",
        "| label | backend | memory | elapsed s | reference | frames | rejected samples | valid pixels |",
        "| --- | --- | --- | ---: | --- | ---: | ---: | ---: |",
    ]
    for row in (cpu, resident):
        timing = row.get("timing") or {}
        registration = row.get("registration") or {}
        integration = row.get("integration") or {}
        lines.append(
            "| "
            f"{row.get('label')} | {integration.get('backend')} | {timing.get('memory_mode')} | "
            f"{timing.get('total_elapsed_s')} | {registration.get('reference_frame_id')} | "
            f"{integration.get('frame_count')} | {integration.get('rejected_samples')} | "
            f"{integration.get('valid_pixels')} |"
        )
    lines.extend(
        [
            "",
            "## Compare",
            "",
            f"- Shape match: `{compare.get('shape_match')}`",
            f"- RMS diff: `{compare.get('rms_diff')}`",
            f"- Relative RMS diff: `{compare.get('relative_rms_diff')}`",
            f"- P99 abs diff: `{compare.get('abs_diff_p99')}`",
            f"- Max abs diff: `{compare.get('max_abs_diff')}`",
            "",
            "## Deltas",
            "",
            f"- Resident/CPU elapsed ratio: `{deltas.get('elapsed_ratio_resident_vs_cpu')}`",
            f"- Rejected sample delta: `{deltas.get('rejected_sample_delta')}`",
            f"- Valid pixel delta: `{deltas.get('valid_pixel_delta')}`",
            "",
            "## Checks",
            "",
        ]
    )
    for item in payload.get("checks") or []:
        marker = "PASS" if item.get("passed") else "FAIL"
        lines.append(f"- {marker}: `{item.get('name')}` - {item.get('evidence')}")
    lines.append("")
    return "\n".join(lines)


def write_resident_parity_summary(
    out: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(out, payload)
    if markdown is not None:
        Path(markdown).parent.mkdir(parents=True, exist_ok=True)
        Path(markdown).write_text(_markdown(payload), encoding="utf-8")
