from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from glass.io.json_io import read_json, write_json
from glass.models import now_iso


RESIDENT_REENTRY_BOUNDARY_SCHEMA_VERSION = 1


def _read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = read_json(path)
    return payload if isinstance(payload, dict) else {}


def _artifact_row(path: Path, *, required: bool = True) -> dict[str, Any]:
    return {
        "path": str(path),
        "exists": path.exists(),
        "required": required,
    }


def _int_or_zero(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return 0


def _summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    summary = payload.get("summary")
    return dict(summary) if isinstance(summary, Mapping) else {}


def _argv_option_value(argv: list[str], flag: str) -> str | None:
    for index, token in enumerate(argv):
        if token == flag and index + 1 < len(argv):
            return argv[index + 1]
        prefix = f"{flag}="
        if token.startswith(prefix):
            return token[len(prefix) :]
    return None


def _invocation_boundary(
    *,
    run: Path,
    path: Path,
    payload: Mapping[str, Any],
) -> tuple[bool, dict[str, Any], list[str]]:
    argv = [str(item) for item in payload.get("argv") or []]
    subcommand = payload.get("subcommand")
    cwd = Path(str(payload.get("cwd") or Path.cwd()))
    out_arg = _argv_option_value(argv, "--out")
    out_path = None if out_arg is None else Path(out_arg)
    resolved_out = None if out_path is None else (out_path if out_path.is_absolute() else cwd / out_path)
    out_matches = bool(resolved_out is not None and resolved_out.resolve() == run.resolve())
    reasons: list[str] = []
    if not path.exists():
        reasons.append("missing_run_invocation")
    if subcommand != "run":
        reasons.append("run_invocation_not_run")
    if out_arg is None:
        reasons.append("run_invocation_missing_out")
    elif not out_matches:
        reasons.append("run_invocation_out_mismatch")
    evidence = {
        "subcommand": subcommand,
        "argv_count": len(argv),
        "cwd": str(cwd),
        "out_arg": out_arg,
        "resolved_out": None if resolved_out is None else str(resolved_out),
        "out_matches_run": out_matches,
    }
    return not reasons, evidence, reasons


def _master_cache_ready(payload: Mapping[str, Any]) -> tuple[bool, dict[str, Any], list[str]]:
    summary = _summary(payload)
    set_count = _int_or_zero(summary.get("set_count"))
    complete_set_count = _int_or_zero(summary.get("complete_set_count"))
    incomplete_set_count = _int_or_zero(summary.get("incomplete_set_count"))
    failed_group_count = _int_or_zero(summary.get("failed_group_count"))
    missing_required = []
    for group in payload.get("groups") or []:
        if isinstance(group, Mapping):
            missing_required.extend(group.get("missing_required_files") or [])
    reasons: list[str] = []
    if payload.get("artifact") != "resident_master_cache":
        reasons.append("artifact_type_not_resident_master_cache")
    if summary.get("passed") is not True:
        reasons.append("resident_master_cache_summary_not_passed")
    if set_count <= 0:
        reasons.append("resident_master_cache_has_no_sets")
    if complete_set_count != set_count:
        reasons.append("resident_master_cache_incomplete_sets_present")
    if incomplete_set_count > 0:
        reasons.append("resident_master_cache_incomplete_set_count_nonzero")
    if failed_group_count > 0:
        reasons.append("resident_master_cache_failed_group_count_nonzero")
    if missing_required:
        reasons.append("resident_master_cache_missing_required_files")
    evidence = {
        "set_count": set_count,
        "complete_set_count": complete_set_count,
        "incomplete_set_count": incomplete_set_count,
        "failed_group_count": failed_group_count,
        "missing_required_file_count": len(missing_required),
        "cache_hit_count": _int_or_zero(summary.get("cache_hit_count")),
        "cache_miss_count": _int_or_zero(summary.get("cache_miss_count")),
        "total_required_bytes": _int_or_zero(summary.get("total_required_bytes")),
    }
    return not reasons, evidence, reasons


def _calibration_artifacts_ready(payload: Mapping[str, Any]) -> tuple[bool, dict[str, Any], list[str]]:
    masters = payload.get("masters") if isinstance(payload.get("masters"), Mapping) else {}
    calibrated_lights = payload.get("calibrated_lights")
    calibrated_lights = calibrated_lights if isinstance(calibrated_lights, list) else []
    master_contract_failures = []
    for name, master in masters.items():
        if not isinstance(master, Mapping):
            master_contract_failures.append(str(name))
            continue
        contract = master.get("resident_calibration_contract")
        if isinstance(contract, Mapping) and contract.get("passed") is True:
            continue
        master_contract_failures.append(str(name))
    dq_contract_failures = [
        str(light.get("frame_id") or index)
        for index, light in enumerate(calibrated_lights)
        if isinstance(light, Mapping) and light.get("dq_contract_ok") is False
    ]
    reasons: list[str] = []
    if payload.get("artifact_type") != "resident_cuda_calibration_artifacts":
        reasons.append("artifact_type_not_resident_cuda_calibration_artifacts")
    if not masters:
        reasons.append("resident_calibration_artifacts_have_no_masters")
    if not calibrated_lights:
        reasons.append("resident_calibration_artifacts_have_no_calibrated_lights")
    if master_contract_failures:
        reasons.append("resident_master_contract_failures_present")
    if dq_contract_failures:
        reasons.append("resident_calibrated_light_dq_contract_failures_present")
    evidence = {
        "master_count": len(masters),
        "calibrated_light_count": len(calibrated_lights),
        "master_contract_failure_count": len(master_contract_failures),
        "dq_contract_failure_count": len(dq_contract_failures),
        "memory_mode": payload.get("memory_mode"),
        "backend": payload.get("backend"),
    }
    return not reasons, evidence, reasons


def _calibration_contract_ready(payload: Mapping[str, Any]) -> tuple[bool, dict[str, Any], list[str]]:
    output_count = _int_or_zero(payload.get("output_count"))
    failed_outputs = [
        str(output.get("index") or index)
        for index, output in enumerate(payload.get("outputs") or [])
        if isinstance(output, Mapping) and output.get("passed") is not True
    ]
    reasons: list[str] = []
    if payload.get("artifact_type") != "resident_cuda_calibration_contract":
        reasons.append("artifact_type_not_resident_cuda_calibration_contract")
    if payload.get("passed") is not True:
        reasons.append("resident_calibration_contract_not_passed")
    if output_count <= 0:
        reasons.append("resident_calibration_contract_has_no_outputs")
    if failed_outputs:
        reasons.append("resident_calibration_contract_failed_outputs_present")
    evidence = {
        "output_count": output_count,
        "failed_output_count": len(failed_outputs),
        "status": payload.get("status"),
    }
    return not reasons, evidence, reasons


def _boundary_row(
    *,
    name: str,
    ready: bool,
    artifacts: list[dict[str, Any]],
    evidence: dict[str, Any],
    reasons: list[str],
    resume_supported: bool,
    resume_action: str,
) -> dict[str, Any]:
    missing = [
        artifact["path"]
        for artifact in artifacts
        if artifact.get("required") and not artifact.get("exists")
    ]
    effective_reasons = list(reasons)
    if missing:
        effective_reasons.append("required_artifacts_missing")
    return {
        "name": name,
        "ready": bool(ready and not missing),
        "resume_supported": bool(resume_supported and ready and not missing),
        "resume_action": resume_action,
        "artifacts": artifacts,
        "evidence": evidence,
        "reasons": effective_reasons,
    }


def build_resident_reentry_boundary(run_dir: str | Path) -> dict[str, Any]:
    run = Path(run_dir)
    run_invocation_path = run / "run_invocation.json"
    resident_master_cache_path = run / "resident_master_cache.json"
    calibration_artifacts_path = run / "calibration_artifacts.json"
    resident_calibration_contract_path = run / "resident_calibration_contract.json"

    master_cache = _read_json_if_exists(resident_master_cache_path)
    calibration_artifacts = _read_json_if_exists(calibration_artifacts_path)
    calibration_contract = _read_json_if_exists(resident_calibration_contract_path)

    invocation_payload = _read_json_if_exists(run_invocation_path)
    invocation_ready, invocation_evidence, invocation_reasons = _invocation_boundary(
        run=run,
        path=run_invocation_path,
        payload=invocation_payload,
    )
    pre_integration = _boundary_row(
        name="pre_integration_invocation",
        ready=invocation_ready,
        artifacts=[_artifact_row(run_invocation_path, required=True)],
        evidence=invocation_evidence,
        reasons=invocation_reasons,
        resume_supported=True,
        resume_action="reenter_from_run_invocation",
    )

    master_ready, master_evidence, master_reasons = _master_cache_ready(master_cache)
    master_cache_boundary = _boundary_row(
        name="resident_master_cache",
        ready=master_ready,
        artifacts=[_artifact_row(resident_master_cache_path, required=True)],
        evidence=master_evidence,
        reasons=master_reasons,
        resume_supported=False,
        resume_action="blocked_master_cache_reentry_not_implemented",
    )

    artifacts_ready, artifacts_evidence, artifacts_reasons = _calibration_artifacts_ready(
        calibration_artifacts
    )
    contract_ready, contract_evidence, contract_reasons = _calibration_contract_ready(
        calibration_contract
    )
    calibration_ready = (
        master_cache_boundary["ready"]
        and artifacts_ready
        and contract_ready
        and calibration_artifacts_path.exists()
        and resident_calibration_contract_path.exists()
    )
    calibration_boundary = _boundary_row(
        name="resident_calibration",
        ready=calibration_ready,
        artifacts=[
            _artifact_row(calibration_artifacts_path, required=True),
            _artifact_row(resident_calibration_contract_path, required=True),
            _artifact_row(resident_master_cache_path, required=True),
        ],
        evidence={
            "calibration_artifacts": artifacts_evidence,
            "resident_calibration_contract": contract_evidence,
            "resident_master_cache": master_evidence,
        },
        reasons=artifacts_reasons + contract_reasons + master_cache_boundary["reasons"],
        resume_supported=False,
        resume_action="blocked_calibration_boundary_reentry_not_implemented",
    )

    boundaries = [pre_integration, master_cache_boundary, calibration_boundary]
    ready_boundaries = [row for row in boundaries if row["ready"]]
    supported_boundaries = [row for row in boundaries if row["resume_supported"]]
    strongest_ready = ready_boundaries[-1]["name"] if ready_boundaries else None
    strongest_supported = supported_boundaries[-1]["name"] if supported_boundaries else None
    return {
        "schema_version": RESIDENT_REENTRY_BOUNDARY_SCHEMA_VERSION,
        "artifact_type": "resident_reentry_boundary",
        "created_at": now_iso(),
        "run": str(run),
        "summary": {
            "ready_boundary_count": len(ready_boundaries),
            "supported_boundary_count": len(supported_boundaries),
            "strongest_ready_boundary": strongest_ready,
            "strongest_supported_boundary": strongest_supported,
            "pre_integration_ready": bool(pre_integration["ready"]),
            "master_cache_boundary_ready": bool(master_cache_boundary["ready"]),
            "calibration_boundary_ready": bool(calibration_boundary["ready"]),
            "calibration_boundary_resume_supported": bool(
                calibration_boundary["resume_supported"]
            ),
            "resume_action": (
                calibration_boundary["resume_action"]
                if calibration_boundary["ready"]
                else master_cache_boundary["resume_action"]
                if master_cache_boundary["ready"]
                else pre_integration["resume_action"]
                if pre_integration["ready"]
                else "blocked_incomplete_resident_run"
            ),
        },
        "boundaries": boundaries,
    }


def write_resident_reentry_boundary(run_dir: str | Path) -> Path:
    run = Path(run_dir)
    path = run / "resident_reentry_boundary.json"
    write_json(path, build_resident_reentry_boundary(run))
    return path
