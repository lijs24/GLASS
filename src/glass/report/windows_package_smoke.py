from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Any

from glass.io.json_io import read_json, write_json
from glass.models import now_iso


def _check(name: str, passed: bool, evidence: dict[str, Any], note: str = "") -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "evidence": evidence, "note": note}


def _run_command(command: list[str], *, cwd: Path, timeout_s: int) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
    except Exception as exc:  # pragma: no cover - environment-specific diagnostics
        return {
            "command": command,
            "cwd": str(cwd),
            "returncode": None,
            "stdout_tail": "",
            "stderr_tail": str(exc),
            "exception": type(exc).__name__,
        }
    return {
        "command": command,
        "cwd": str(cwd),
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
        "exception": None,
    }


def _safe_read_text(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8", errors="replace").strip()


def _json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = read_json(path)
    return payload if isinstance(payload, dict) else None


def build_windows_package_smoke(
    *,
    package_root: str | Path,
    zip_path: str | Path | None = None,
    expected_source: str | None = None,
    expected_package_label: str | None = None,
    require_cuda: bool = False,
    execute: bool = True,
    timeout_s: int = 120,
) -> dict[str, Any]:
    root = Path(package_root).resolve()
    runtime = root / "runtime"
    python_exe = runtime / "python.exe"
    glass_cmd = root / "glass.cmd"
    doctor_cmd = root / "glass-doctor.cmd"
    source_stamp = root / "source"
    package_manifest_path = root / "package_manifest.json"
    docs_dir = root / "docs"
    zip_file = Path(zip_path).resolve() if zip_path is not None else root.parent / "GLASS-Portable-win64.zip"
    package_manifest = _json_if_exists(package_manifest_path)

    structure_checks = [
        _check("package_root_exists", root.exists() and root.is_dir(), {"path": str(root)}),
        _check("runtime_python_exists", python_exe.exists(), {"path": str(python_exe)}),
        _check("glass_cmd_exists", glass_cmd.exists(), {"path": str(glass_cmd)}),
        _check("glass_doctor_cmd_exists", doctor_cmd.exists(), {"path": str(doctor_cmd)}),
        _check("readme_exists", (root / "README.md").exists(), {"path": str(root / "README.md")}),
        _check("license_exists", (root / "LICENSE").exists(), {"path": str(root / "LICENSE")}),
        _check("docs_windows_release_exists", (docs_dir / "windows_release.md").exists(), {"path": str(docs_dir / "windows_release.md")}),
        _check("source_stamp_exists", source_stamp.exists(), {"path": str(source_stamp)}),
        _check("package_manifest_exists", package_manifest_path.exists(), {"path": str(package_manifest_path)}),
        _check("portable_zip_exists", zip_file.exists(), {"path": str(zip_file)}),
    ]
    if zip_file.exists():
        structure_checks.append(
            _check(
                "portable_zip_nonempty",
                zip_file.stat().st_size > 0,
                {"path": str(zip_file), "size_bytes": zip_file.stat().st_size},
            )
        )
    if expected_package_label is not None:
        structure_checks.append(
            _check(
                "package_label_matches_expected",
                package_manifest is not None and package_manifest.get("package_label") == expected_package_label,
                {
                    "actual": None if package_manifest is None else package_manifest.get("package_label"),
                    "required": expected_package_label,
                },
            )
        )
    if require_cuda:
        structure_checks.append(
            _check(
                "package_manifest_cuda_build",
                package_manifest is not None and package_manifest.get("build_cuda") is True,
                {"actual": None if package_manifest is None else package_manifest.get("build_cuda"), "required": True},
            )
        )
    source_text = _safe_read_text(source_stamp)
    if expected_source is not None:
        structure_checks.append(
            _check(
                "source_stamp_matches_expected",
                source_text == expected_source,
                {"actual": source_text, "required": expected_source},
            )
        )

    execution: dict[str, Any] = {
        "execute": bool(execute),
        "doctor_command": None,
        "help_command": None,
        "doctor_json": None,
    }
    execution_checks: list[dict[str, Any]] = []
    doctor_json_path = root.parent / "portable_doctor.json"
    if execute:
        doctor_json_path.unlink(missing_ok=True)
        doctor_command = _run_command(
            [str(doctor_cmd), "--json", str(doctor_json_path)],
            cwd=root,
            timeout_s=timeout_s,
        )
        help_command = _run_command([str(glass_cmd), "--help"], cwd=root, timeout_s=timeout_s)
        doctor_json = _json_if_exists(doctor_json_path)
        execution.update(
            {
                "doctor_command": doctor_command,
                "help_command": help_command,
                "doctor_json": doctor_json,
                "doctor_json_path": str(doctor_json_path),
            }
        )
        cuda = doctor_json.get("cuda") if isinstance(doctor_json, dict) and isinstance(doctor_json.get("cuda"), dict) else {}
        execution_checks.extend(
            [
                _check(
                    "portable_doctor_exit_zero",
                    doctor_command.get("returncode") == 0,
                    {"returncode": doctor_command.get("returncode")},
                ),
                _check(
                    "portable_help_exit_zero",
                    help_command.get("returncode") == 0,
                    {"returncode": help_command.get("returncode")},
                ),
                _check(
                    "portable_doctor_json_written",
                    doctor_json is not None,
                    {"path": str(doctor_json_path), "exists": doctor_json_path.exists()},
                ),
                _check(
                    "portable_doctor_product",
                    doctor_json is not None and doctor_json.get("product") == "GLASS",
                    {"actual": None if doctor_json is None else doctor_json.get("product"), "required": "GLASS"},
                ),
                _check(
                    "portable_cuda_requirement",
                    bool(cuda.get("cuda_available")) if require_cuda else True,
                    {"actual": cuda.get("cuda_available"), "required": bool(require_cuda)},
                ),
            ]
        )
    else:
        execution_checks.append(
            _check(
                "portable_execution_skipped",
                True,
                {"execute": False},
                "Structure-only smoke; command execution was skipped.",
            )
        )

    checks = [*structure_checks, *execution_checks]
    failed = [item for item in checks if not item.get("passed")]
    return {
        "schema_version": 1,
        "artifact_type": "windows_package_smoke",
        "created_at": now_iso(),
        "status": "package_smoke_passed" if not failed else "package_smoke_failed",
        "passed": not failed,
        "recommendation": "portable_package_ready_for_next_release_step" if not failed else "fix_package_smoke_failures",
        "package": {
            "root": str(root),
            "zip_path": str(zip_file),
            "zip_size_bytes": zip_file.stat().st_size if zip_file.exists() else None,
            "source_stamp": source_text,
            "manifest_path": str(package_manifest_path),
            "manifest": package_manifest,
        },
        "requirements": {
            "execute": bool(execute),
            "require_cuda": bool(require_cuda),
            "expected_source": expected_source,
            "expected_package_label": expected_package_label,
            "timeout_s": int(timeout_s),
        },
        "execution": execution,
        "checks": checks,
        "failed_checks": [str(item.get("name")) for item in failed],
        "limitations": [
            "This smoke test validates package structure and CLI startup; it does not sign or publish artifacts.",
            "CPU-only package smoke does not prove CUDA native module loading.",
            "A CUDA release package must be smoked with require_cuda=true on the target release machine.",
        ],
    }


def _markdown(payload: dict[str, Any]) -> str:
    package = payload.get("package") if isinstance(payload.get("package"), dict) else {}
    lines = [
        "# GLASS Windows Package Smoke",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Passed: `{payload.get('passed')}`",
        f"- Recommendation: `{payload.get('recommendation')}`",
        f"- Package root: `{package.get('root')}`",
        f"- Zip: `{package.get('zip_path')}`",
        f"- Zip size bytes: `{package.get('zip_size_bytes')}`",
        f"- Source stamp: `{package.get('source_stamp')}`",
        "",
        "## Checks",
        "",
    ]
    for item in payload.get("checks") or []:
        marker = "PASS" if item.get("passed") else "FAIL"
        lines.append(f"- {marker}: `{item.get('name')}` - {item.get('evidence')}")
    lines.append("")
    return "\n".join(lines)


def write_windows_package_smoke(
    out: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(out, payload)
    if markdown is not None:
        Path(markdown).parent.mkdir(parents=True, exist_ok=True)
        Path(markdown).write_text(_markdown(payload), encoding="utf-8")
