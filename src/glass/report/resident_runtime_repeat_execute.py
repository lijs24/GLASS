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


def _read_plan(path: str | Path) -> dict[str, Any]:
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"repeat plan must be a JSON object: {path}")
    if payload.get("artifact_type") != "resident_runtime_repeat_plan":
        raise ValueError(f"expected resident_runtime_repeat_plan artifact, got {payload.get('artifact_type')}")
    return payload


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


def _run_timing_exists(run: dict[str, Any]) -> bool:
    run_dir = run.get("run_dir")
    return bool(run_dir) and (Path(str(run_dir)) / "run_timing.json").exists()


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


def build_resident_runtime_repeat_execution(
    plan: str | Path,
    *,
    dry_run: bool = False,
    skip_existing: bool = False,
    run_compare: bool = True,
    glass_executable: str | Path | None = None,
    cwd: str | Path | None = None,
) -> dict[str, Any]:
    payload = _read_plan(plan)
    records: list[dict[str, Any]] = []
    failed = False
    for run in [row for row in payload.get("runs", []) if isinstance(row, dict)]:
        run_id = str(run.get("run_id"))
        if skip_existing and _run_timing_exists(run):
            records.append(
                {
                    "run_id": run_id,
                    "status": "skipped_existing",
                    "step": None,
                    "run_timing_exists": True,
                }
            )
            continue
        command = run.get("command")
        if not isinstance(command, str) or not command:
            raise ValueError(f"repeat run {run_id} is missing command")
        step = _step_record(
            step="run",
            command=command,
            dry_run=dry_run,
            glass_executable=glass_executable,
            cwd=cwd,
        )
        records.append(
            {
                "run_id": run_id,
                "status": step["status"],
                "step": step,
                "run_timing_exists": _run_timing_exists(run),
            }
        )
        if step["status"] == "failed":
            failed = True
            break

    compare_record = None
    if run_compare and not failed:
        compare_command = payload.get("compare_command")
        if not isinstance(compare_command, str) or not compare_command:
            raise ValueError("repeat plan is missing compare_command")
        compare_record = _step_record(
            step="resident_runtime_compare",
            command=compare_command,
            dry_run=dry_run,
            glass_executable=glass_executable,
            cwd=cwd,
        )
        failed = compare_record["status"] == "failed"

    completed = sum(1 for row in records if row.get("status") == "completed")
    skipped = sum(1 for row in records if row.get("status") == "skipped_existing")
    return {
        "schema_version": 1,
        "artifact_type": "resident_runtime_repeat_execution",
        "created_at": now_iso(),
        "plan": str(plan),
        "dry_run": bool(dry_run),
        "skip_existing": bool(skip_existing),
        "run_compare": bool(run_compare),
        "summary": {
            "status": "planned" if dry_run else ("failed" if failed else "completed"),
            "failed": failed,
            "recorded_run_count": len(records),
            "completed_run_count": completed,
            "skipped_existing_count": skipped,
            "compare_status": None if compare_record is None else compare_record.get("status"),
        },
        "runs": records,
        "compare": compare_record,
        "limitations": [
            "Dry-run mode records commands without launching subprocesses.",
            "Skip-existing checks for run_timing.json in each planned run directory.",
            "This executor preserves the commands recorded in the repeat plan.",
        ],
    }


def write_resident_runtime_repeat_execution(out: str | Path, payload: dict[str, Any]) -> None:
    write_json(out, payload)
