from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import shlex
import subprocess
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


def _option_value(command: str, option: str) -> str | None:
    tokens = _split_command(command)
    try:
        index = tokens.index(option)
    except ValueError:
        return None
    if index + 1 >= len(tokens):
        return None
    return tokens[index + 1]


def _probe_gpu_text() -> tuple[str | None, str | None]:
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,memory.used,utilization.gpu,driver_version",
                "--format=csv,noheader,nounits",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=3.0,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, str(exc)
    if result.returncode != 0:
        return None, result.stderr.strip() or f"nvidia-smi exited with {result.returncode}"
    return result.stdout, None


def _parse_gpu(text: str | None, *, min_free_mib: int, max_busy_utilization: int) -> dict[str, Any]:
    if not text:
        return {
            "status": "unknown",
            "reason": "gpu probe was not available",
            "name": None,
            "total_mib": None,
            "used_mib": None,
            "free_mib": None,
            "utilization_percent": None,
            "driver": None,
        }
    first = next((line.strip() for line in text.splitlines() if line.strip()), "")
    parts = [part.strip() for part in first.split(",")]
    if len(parts) < 5:
        return {
            "status": "unknown",
            "reason": f"unexpected nvidia-smi output: {first}",
            "raw": first,
        }
    name = parts[0]
    try:
        total_mib = int(float(parts[1]))
        used_mib = int(float(parts[2]))
        utilization = int(float(parts[3]))
    except ValueError:
        return {
            "status": "unknown",
            "reason": f"could not parse nvidia-smi output: {first}",
            "raw": first,
        }
    free_mib = total_mib - used_mib
    used_fraction = used_mib / total_mib if total_mib > 0 else 0.0
    if free_mib < min_free_mib:
        status = "low_free_memory"
        reason = f"only {free_mib} MiB GPU memory is free"
    elif utilization >= max_busy_utilization and used_fraction >= 0.5:
        status = "busy"
        reason = f"GPU is busy ({utilization}% utilization, {used_mib}/{total_mib} MiB used)"
    else:
        status = "ready"
        reason = "GPU has enough free memory and is below the busy utilization threshold"
    return {
        "status": status,
        "reason": reason,
        "name": name,
        "total_mib": total_mib,
        "used_mib": used_mib,
        "free_mib": free_mib,
        "utilization_percent": utilization,
        "driver": parts[4],
        "min_free_mib": min_free_mib,
        "max_busy_utilization": max_busy_utilization,
    }


def _run_status(run: dict[str, Any]) -> dict[str, Any]:
    run_dir = Path(str(run.get("run_dir", "")))
    run_timing = run_dir / "run_timing.json"
    resident_artifacts = run_dir / "resident_artifacts.json"
    if run_timing.exists():
        status = "complete"
    elif run_dir.exists():
        status = "output_dir_exists_without_timing"
    else:
        status = "ready"
    return {
        "run_id": run.get("run_id"),
        "run_dir": str(run_dir),
        "status": status,
        "run_dir_exists": run_dir.exists(),
        "run_timing_exists": run_timing.exists(),
        "resident_artifacts_exists": resident_artifacts.exists(),
    }


def _uses_cuda(payload: dict[str, Any]) -> bool:
    for run in payload.get("runs", []):
        command = run.get("command") if isinstance(run, dict) else None
        if not isinstance(command, str):
            continue
        tokens = _split_command(command)
        if "--backend" in tokens:
            index = tokens.index("--backend")
            if index + 1 < len(tokens) and tokens[index + 1].lower() == "cuda":
                return True
        if "--memory-mode" in tokens:
            index = tokens.index("--memory-mode")
            if index + 1 < len(tokens) and tokens[index + 1].lower() == "resident":
                return True
    return False


def _recommendation(
    *,
    run_rows: list[dict[str, Any]],
    gpu: dict[str, Any],
    uses_cuda: bool,
    allow_existing: bool,
) -> str:
    if not run_rows:
        return "invalid_plan_no_runs"
    complete_count = sum(1 for row in run_rows if row["status"] == "complete")
    conflict_count = sum(1 for row in run_rows if row["status"] == "output_dir_exists_without_timing")
    if complete_count == len(run_rows):
        return "run_compare_only"
    if conflict_count and not allow_existing:
        return "clean_outputs_or_use_skip_existing"
    if uses_cuda and gpu.get("status") in {"busy", "low_free_memory", "unknown"}:
        return "wait_for_controlled_window"
    return "execute_repeat_plan"


def build_resident_runtime_repeat_preflight(
    plan: str | Path,
    *,
    min_free_mib: int = 8192,
    max_busy_utilization: int = 95,
    allow_existing: bool = False,
    probe_gpu: bool = True,
    gpu_query_text: str | None = None,
) -> dict[str, Any]:
    payload = _read_plan(plan)
    probe_error = None
    if gpu_query_text is None and probe_gpu:
        gpu_query_text, probe_error = _probe_gpu_text()
    gpu = _parse_gpu(gpu_query_text, min_free_mib=min_free_mib, max_busy_utilization=max_busy_utilization)
    if probe_error is not None:
        gpu["probe_error"] = probe_error
    run_rows = [_run_status(row) for row in payload.get("runs", []) if isinstance(row, dict)]
    compare_out = _option_value(str(payload.get("compare_command", "")), "--out")
    compare_exists = bool(compare_out) and Path(compare_out).exists()
    uses_cuda = _uses_cuda(payload)
    recommendation = _recommendation(
        run_rows=run_rows,
        gpu=gpu,
        uses_cuda=uses_cuda,
        allow_existing=allow_existing,
    )
    ready_to_execute = recommendation == "execute_repeat_plan"
    return {
        "schema_version": 1,
        "artifact_type": "resident_runtime_repeat_preflight",
        "created_at": now_iso(),
        "plan": str(plan),
        "repeat_count": len(run_rows),
        "uses_cuda": uses_cuda,
        "allow_existing": bool(allow_existing),
        "ready_to_execute": ready_to_execute,
        "recommendation": recommendation,
        "gpu": gpu,
        "runs": run_rows,
        "summary": {
            "complete_run_count": sum(1 for row in run_rows if row["status"] == "complete"),
            "ready_run_count": sum(1 for row in run_rows if row["status"] == "ready"),
            "conflict_run_count": sum(1 for row in run_rows if row["status"] == "output_dir_exists_without_timing"),
            "compare_out": compare_out,
            "compare_exists": compare_exists,
        },
        "limitations": [
            "This preflight checks plan/output/GPU readiness only; it does not execute image processing.",
            "GPU readiness is based on a point-in-time nvidia-smi sample.",
            "Disk/cache state labels in the repeat plan are operator intent, not enforceable guarantees.",
        ],
    }


def write_resident_runtime_repeat_preflight(out: str | Path, payload: dict[str, Any]) -> None:
    write_json(out, payload)
