from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import shlex
import subprocess
from typing import Any

from glass.io.json_io import write_json
from glass.models import now_iso


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


def _command(tokens: list[str | Path | int | float]) -> str:
    return subprocess.list2cmdline([str(token) for token in tokens])


def _read_command(path: str | Path) -> list[str]:
    text = Path(path).read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"base run command is empty: {path}")
    return _split_command(text)


def _set_option(tokens: list[str], option: str, value: str | Path | int | float) -> list[str]:
    updated = list(tokens)
    try:
        index = updated.index(option)
    except ValueError:
        updated.extend([option, str(value)])
        return updated
    if index + 1 >= len(updated):
        raise ValueError(f"base command option {option} is missing a value")
    updated[index + 1] = str(value)
    return updated


def _run_entry(label: str, root: Path, repeat_index: int, command_tokens: list[str]) -> dict[str, Any]:
    run_id = f"{label}_repeat{repeat_index:02d}"
    run_dir = root / "runs" / run_id
    command = _command(_set_option(command_tokens, "--out", run_dir))
    return {
        "repeat_index": repeat_index,
        "run_id": run_id,
        "run_dir": str(run_dir),
        "command": command,
    }


def build_resident_runtime_repeat_plan(
    *,
    base_run_command: str | Path,
    root: str | Path,
    label: str,
    repeats: int,
    cache_state: str,
    baseline_repeat: int = 1,
) -> dict[str, Any]:
    if repeats <= 0:
        raise ValueError("repeats must be positive")
    if baseline_repeat < 1 or baseline_repeat > repeats:
        raise ValueError("baseline_repeat must be within the planned repeat range")
    if not label:
        raise ValueError("label must not be empty")
    root_path = Path(root)
    command_tokens = _read_command(base_run_command)
    runs = [_run_entry(label, root_path, index, command_tokens) for index in range(1, repeats + 1)]
    compare_tokens: list[str | Path | int | float] = ["glass", "resident-runtime-compare"]
    for row in runs:
        compare_tokens.extend(["--run", f"{row['run_id']}={row['run_dir']}"])
    compare_tokens.extend(
        [
            "--baseline-label",
            runs[baseline_repeat - 1]["run_id"],
            "--out",
            root_path / "runtime_compare.json",
            "--markdown",
            root_path / "runtime_compare.md",
        ]
    )
    return {
        "schema_version": 1,
        "artifact_type": "resident_runtime_repeat_plan",
        "created_at": now_iso(),
        "base_run_command": str(base_run_command),
        "root": str(root_path),
        "label": label,
        "cache_state": cache_state,
        "repeat_count": repeats,
        "baseline_repeat": baseline_repeat,
        "runs": runs,
        "compare_command": _command(compare_tokens),
        "execution_notes": [
            "This plan does not execute image processing.",
            "Run entries should be executed sequentially in the requested I/O window.",
            "Use the compare command after all repeats finish to separate timing variance from configuration changes.",
        ],
    }


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Resident Runtime Repeat Plan",
        "",
        f"- Label: `{payload.get('label')}`",
        f"- Cache state: `{payload.get('cache_state')}`",
        f"- Repeats: `{payload.get('repeat_count')}`",
        f"- Baseline repeat: `{payload.get('baseline_repeat')}`",
        "",
        "## Run Commands",
        "",
    ]
    for row in payload.get("runs", []):
        lines.extend(
            [
                f"### {row.get('run_id')}",
                "",
                "```powershell",
                str(row.get("command")),
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "## Compare Command",
            "",
            "```powershell",
            str(payload.get("compare_command")),
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def write_resident_runtime_repeat_plan(
    out: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(out, payload)
    if markdown is not None:
        Path(markdown).write_text(_markdown(payload), encoding="utf-8")
