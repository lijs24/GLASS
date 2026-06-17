from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import shlex
import subprocess
import time
from typing import Any

from glass.io.json_io import read_json, write_json
from glass.models import now_iso


STEP_ORDER = [
    "run",
    "compare_reference",
    "compare_baseline",
    "guardrails",
    "resident_calibration_contract",
    "resident_result_contract",
    "stack_engine_contract",
    "pipeline_contract",
    "acceptance_audit",
    "candidate_comparison",
]
OPTIONAL_LEGACY_STEPS = {
    "guardrails",
    "pipeline_contract",
    "resident_calibration_contract",
    "resident_result_contract",
    "stack_engine_contract",
}


def _read_plan(path: str | Path) -> dict[str, Any]:
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"runtime sweep plan must be a JSON object: {path}")
    if payload.get("artifact_type") != "candidate_runtime_sweep_plan":
        raise ValueError(f"expected candidate_runtime_sweep_plan artifact, got {payload.get('artifact_type')}")
    return payload


def _selected_variants(plan: dict[str, Any], variant_ids: list[str] | None) -> list[dict[str, Any]]:
    variants = [row for row in plan.get("variants", []) if isinstance(row, dict)]
    if not variant_ids:
        return variants
    requested = set(variant_ids)
    selected = [row for row in variants if str(row.get("variant_id")) in requested]
    found = {str(row.get("variant_id")) for row in selected}
    missing = sorted(requested - found)
    if missing:
        raise ValueError(f"unknown runtime sweep variants: {missing}")
    return selected


def _split_command(command: str) -> list[str]:
    if os.name != "nt":
        return shlex.split(command, posix=True)

    argc = ctypes.c_int()
    shell32 = ctypes.windll.shell32  # type: ignore[attr-defined]
    kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
    shell32.CommandLineToArgvW.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_int)]
    shell32.CommandLineToArgvW.restype = ctypes.POINTER(wintypes.LPWSTR)
    kernel32.LocalFree.argtypes = [wintypes.HLOCAL]
    kernel32.LocalFree.restype = wintypes.HLOCAL
    argv = shell32.CommandLineToArgvW(command, ctypes.byref(argc))
    if not argv:
        raise ValueError(f"could not parse command line: {command}")
    try:
        return [argv[index] for index in range(argc.value)]
    finally:
        kernel32.LocalFree(argv)


def _command_tokens(command: str, glass_executable: str | Path | None) -> list[str]:
    tokens = _split_command(command)
    if tokens and tokens[0].lower() == "glass" and glass_executable is not None:
        tokens[0] = str(glass_executable)
    return tokens


def _comparison_artifact_exists(variant: dict[str, Any]) -> bool:
    artifacts = variant.get("artifacts") if isinstance(variant.get("artifacts"), dict) else {}
    comparison = artifacts.get("candidate_comparison_json")
    return bool(comparison) and Path(str(comparison)).exists()


def _step_record(
    *,
    step: str,
    command: str,
    dry_run: bool,
    glass_executable: str | Path | None,
    cwd: str | Path | None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "step": step,
        "command": command,
        "status": "planned" if dry_run else "pending",
        "returncode": None,
        "elapsed_s": None,
    }
    if dry_run:
        return record
    started = time.perf_counter()
    result = subprocess.run(_command_tokens(command, glass_executable), cwd=None if cwd is None else str(cwd))
    record["elapsed_s"] = float(time.perf_counter() - started)
    record["returncode"] = int(result.returncode)
    record["status"] = "completed" if result.returncode == 0 else "failed"
    return record


def build_candidate_runtime_sweep_execution(
    plan: str | Path,
    *,
    dry_run: bool = False,
    skip_existing: bool = False,
    variants: list[str] | None = None,
    start_at: str | None = None,
    stop_after: str | None = None,
    run_sweep_summary: bool = True,
    glass_executable: str | Path | None = None,
    cwd: str | Path | None = None,
) -> dict[str, Any]:
    payload = _read_plan(plan)
    selected = _selected_variants(payload, variants)
    if start_at is not None:
        ids = [str(row.get("variant_id")) for row in selected]
        if start_at not in ids:
            raise ValueError(f"start_at variant is not selected: {start_at}")
        selected = selected[ids.index(start_at) :]
    if stop_after is not None:
        ids = [str(row.get("variant_id")) for row in selected]
        if stop_after not in ids:
            raise ValueError(f"stop_after variant is not selected: {stop_after}")
        selected = selected[: ids.index(stop_after) + 1]

    records: list[dict[str, Any]] = []
    failed = False
    for variant in selected:
        variant_id = str(variant.get("variant_id"))
        if skip_existing and _comparison_artifact_exists(variant):
            records.append(
                {
                    "variant_id": variant_id,
                    "status": "skipped_existing",
                    "steps": [],
                    "candidate_comparison_exists": True,
                }
            )
            continue
        commands = variant.get("commands") if isinstance(variant.get("commands"), dict) else {}
        steps: list[dict[str, Any]] = []
        variant_status = "planned" if dry_run else "completed"
        for step in STEP_ORDER:
            command = commands.get(step)
            if not command:
                if step in OPTIONAL_LEGACY_STEPS:
                    continue
                raise ValueError(f"variant {variant_id} is missing command for step {step}")
            step_result = _step_record(
                step=step,
                command=str(command),
                dry_run=dry_run,
                glass_executable=glass_executable,
                cwd=cwd,
            )
            steps.append(step_result)
            if step_result["status"] == "failed":
                variant_status = "failed"
                failed = True
                break
        records.append(
            {
                "variant_id": variant_id,
                "status": variant_status,
                "steps": steps,
                "candidate_comparison_exists": _comparison_artifact_exists(variant),
            }
        )
        if failed:
            break

    sweep_record = None
    if run_sweep_summary and not failed:
        sweep_command = payload.get("sweep_command")
        if not isinstance(sweep_command, str) or not sweep_command:
            raise ValueError("runtime sweep plan is missing sweep_command")
        sweep_record = _step_record(
            step="candidate_comparison_sweep",
            command=sweep_command,
            dry_run=dry_run,
            glass_executable=glass_executable,
            cwd=cwd,
        )
        failed = sweep_record["status"] == "failed"

    completed = sum(1 for row in records if row.get("status") == "completed")
    skipped = sum(1 for row in records if row.get("status") == "skipped_existing")
    return {
        "schema_version": 1,
        "artifact_type": "candidate_runtime_sweep_execution",
        "created_at": now_iso(),
        "plan": str(plan),
        "dry_run": bool(dry_run),
        "skip_existing": bool(skip_existing),
        "selected_variant_count": len(selected),
        "summary": {
            "status": "planned" if dry_run else ("failed" if failed else "completed"),
            "failed": failed,
            "completed_variant_count": completed,
            "skipped_existing_count": skipped,
            "recorded_variant_count": len(records),
            "sweep_summary_status": None if sweep_record is None else sweep_record.get("status"),
        },
        "variants": records,
        "sweep_summary": sweep_record,
        "limitations": [
            "This executor runs commands already recorded in a candidate runtime sweep plan.",
            "Dry-run mode does not execute subprocesses and is intended for audit/review.",
            "When GPU memory is occupied by unrelated processes, the run step may fail before comparison artifacts exist.",
        ],
    }


def write_candidate_runtime_sweep_execution(out: str | Path, payload: dict[str, Any]) -> None:
    write_json(out, payload)
