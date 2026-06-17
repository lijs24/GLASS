from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from glass.gpu.compatibility import WINDOWS_CUDA_PACKAGES, WindowsCudaPackage
from glass.io.json_io import write_json
from glass.models import now_iso

DEFAULT_WINDOWS_CUDA_BASE = Path("C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA")
DEFAULT_WINDOWS_RELEASE_ROOT = Path(".release/windows")
DEFAULT_PACKAGE_LABELS = ("cuda13", "cuda12", "cuda11", "cpu")


def _check(name: str, passed: bool, evidence: dict[str, Any], note: str = "") -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "evidence": evidence, "note": note}


def _parse_version_text(text: str) -> tuple[int, int] | None:
    match = re.search(r"v?(\d+)(?:\.(\d+))?", text.lower())
    if match is None:
        return None
    return int(match.group(1)), int(match.group(2) or "0")


def _version_label(version: tuple[int, int] | None) -> str | None:
    if version is None:
        return None
    return f"{version[0]}.{version[1]}"


def _toolkit_major(toolkit: str) -> int:
    parsed = _parse_version_text(toolkit)
    if parsed is None:
        raise ValueError(f"Unable to parse CUDA toolkit version: {toolkit}")
    return parsed[0]


def discover_cuda_toolkits(cuda_base: str | Path = DEFAULT_WINDOWS_CUDA_BASE) -> list[dict[str, Any]]:
    base = Path(cuda_base)
    rows: list[dict[str, Any]] = []
    if not base.exists():
        return rows
    for child in base.iterdir():
        if not child.is_dir():
            continue
        version = _parse_version_text(child.name)
        if version is None:
            continue
        nvcc = child / "bin" / "nvcc.exe"
        rows.append(
            {
                "name": child.name,
                "path": str(child),
                "version": _version_label(version),
                "major": version[0],
                "minor": version[1],
                "nvcc_exists": nvcc.exists(),
                "nvcc_path": str(nvcc),
            }
        )
    return sorted(rows, key=lambda item: (int(item["major"]), int(item["minor"])), reverse=True)


def parse_toolkit_root_specs(specs: list[str] | tuple[str, ...] | None) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for spec in specs or []:
        if "=" not in spec:
            raise ValueError(f"Toolkit root override must use LABEL=PATH form: {spec}")
        label, path = spec.split("=", 1)
        label = label.strip()
        path = path.strip()
        if not label or not path:
            raise ValueError(f"Toolkit root override must use LABEL=PATH form: {spec}")
        mapping[label] = path
    return mapping


def _package_by_label() -> dict[str, WindowsCudaPackage]:
    return {package.label: package for package in WINDOWS_CUDA_PACKAGES}


def _architectures_arg(package: WindowsCudaPackage) -> str:
    return ";".join(str(arch) for arch in package.architectures)


def _quote_arg(value: str) -> str:
    if not value:
        return '""'
    if re.search(r"\s|;", value):
        return '"' + value.replace('"', '\\"') + '"'
    return value


def _command_text(command: list[str]) -> str:
    return " ".join(_quote_arg(str(part)) for part in command)


def _minimal_toolkit_command(label: str, action: str) -> list[str] | None:
    if label not in {"cuda12", "cuda11"}:
        return None
    command = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        "packaging/windows/install_cuda_toolkit_minimal.ps1",
        "-Label",
        label,
    ]
    if action == "download":
        command.append("-Download")
    elif action == "install":
        command.append("-Install")
    else:
        return None
    return command


def _find_toolkit_for_package(
    package: WindowsCudaPackage,
    *,
    discovered: list[dict[str, Any]],
    explicit_roots: dict[str, str],
) -> dict[str, Any]:
    explicit_root = explicit_roots.get(package.label)
    required_major = _toolkit_major(package.toolkit)
    if explicit_root:
        root = Path(explicit_root)
        version = _parse_version_text(root.name)
        nvcc = root / "bin" / "nvcc.exe"
        major_matches = version is not None and version[0] == required_major
        return {
            "toolkit_root": str(root),
            "toolkit_version": _version_label(version),
            "toolkit_match": "explicit_major_match" if major_matches else "explicit_version_unverified",
            "nvcc_exists": nvcc.exists(),
            "nvcc_path": str(nvcc),
            "ready": root.exists() and nvcc.exists() and major_matches,
            "source": "explicit",
        }
    candidates = [row for row in discovered if int(row["major"]) == required_major]
    if not candidates:
        return {
            "toolkit_root": None,
            "toolkit_version": None,
            "toolkit_match": "missing",
            "nvcc_exists": False,
            "nvcc_path": None,
            "ready": False,
            "source": "discovered",
        }
    chosen = candidates[0]
    exact = str(chosen.get("version")) == package.toolkit
    return {
        "toolkit_root": chosen["path"],
        "toolkit_version": chosen.get("version"),
        "toolkit_match": "exact" if exact else "major_compatible",
        "nvcc_exists": chosen.get("nvcc_exists"),
        "nvcc_path": chosen.get("nvcc_path"),
        "ready": bool(chosen.get("nvcc_exists")),
        "source": "discovered",
    }


def _variant_row(
    label: str,
    *,
    root: Path,
    python: str,
    configuration: str,
    static_cuda_runtime: bool,
    discovered: list[dict[str, Any]],
    explicit_roots: dict[str, str],
) -> dict[str, Any]:
    package_map = _package_by_label()
    release_root = root.resolve()
    package_root = release_root / "GLASS"
    zip_path = release_root / f"GLASS-Portable-win64-{label}.zip"
    base_command = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        "packaging/windows/build_portable.ps1",
        "-Python",
        python,
        "-Configuration",
        configuration,
        "-PackageLabel",
        label,
    ]
    if label == "cpu":
        command = base_command
        return {
            "label": label,
            "build_cuda": False,
            "known_label": True,
            "toolkit_required": None,
            "toolkit_root": None,
            "toolkit_version": None,
            "toolkit_match": "not_required",
            "cuda_architectures": None,
            "build_ready": True,
            "skip_reason": None,
            "package_root": str(package_root),
            "zip_path": str(zip_path),
            "build_command": command,
            "build_command_text": _command_text(command),
        }
    package = package_map.get(label)
    if package is None:
        return {
            "label": label,
            "build_cuda": None,
            "known_label": False,
            "toolkit_required": None,
            "toolkit_root": None,
            "toolkit_version": None,
            "toolkit_match": "unknown_label",
            "cuda_architectures": None,
            "build_ready": False,
            "skip_reason": "unknown_package_label",
            "package_root": str(package_root),
            "zip_path": str(zip_path),
            "build_command": None,
            "build_command_text": None,
        }
    toolkit = _find_toolkit_for_package(package, discovered=discovered, explicit_roots=explicit_roots)
    command = [
        *base_command,
        "-BuildCuda",
        "-CudaArchitectures",
        _architectures_arg(package),
    ]
    if static_cuda_runtime:
        command.append("-StaticCudaRuntime")
    if toolkit["toolkit_root"] is not None:
        command.extend(["-CudaToolkitRoot", str(toolkit["toolkit_root"])])
    ready = bool(toolkit["ready"])
    download_command = _minimal_toolkit_command(label, "download")
    install_command = _minimal_toolkit_command(label, "install")
    return {
        "label": label,
        "build_cuda": True,
        "known_label": True,
        "toolkit_required": package.toolkit,
        "toolkit_root": toolkit["toolkit_root"],
        "toolkit_version": toolkit["toolkit_version"],
        "toolkit_match": toolkit["toolkit_match"],
        "toolkit_source": toolkit["source"],
        "nvcc_exists": toolkit["nvcc_exists"],
        "nvcc_path": toolkit["nvcc_path"],
        "cuda_architectures": _architectures_arg(package),
        "build_ready": ready,
        "skip_reason": None if ready else "matching_cuda_toolkit_not_found",
        "package_root": str(package_root),
        "zip_path": str(zip_path),
        "build_command": command if ready else None,
        "build_command_text": _command_text(command) if ready else None,
        "toolkit_download_command": None if download_command is None else download_command,
        "toolkit_download_command_text": None if download_command is None else _command_text(download_command),
        "toolkit_install_command": None if install_command is None else install_command,
        "toolkit_install_command_text": None if install_command is None else _command_text(install_command),
    }


def build_windows_package_build_plan(
    *,
    release_root: str | Path = DEFAULT_WINDOWS_RELEASE_ROOT,
    cuda_base: str | Path = DEFAULT_WINDOWS_CUDA_BASE,
    package_labels: tuple[str, ...] = DEFAULT_PACKAGE_LABELS,
    toolkit_roots: dict[str, str] | None = None,
    python: str = r".\.venv\Scripts\python.exe",
    configuration: str = "Release",
    static_cuda_runtime: bool = True,
    require_all_toolkits: bool = False,
) -> dict[str, Any]:
    discovered = discover_cuda_toolkits(cuda_base)
    explicit_roots = dict(toolkit_roots or {})
    root = Path(release_root)
    variants = [
        _variant_row(
            label,
            root=root,
            python=python,
            configuration=configuration,
            static_cuda_runtime=static_cuda_runtime,
            discovered=discovered,
            explicit_roots=explicit_roots,
        )
        for label in package_labels
    ]
    cuda_variants = [row for row in variants if row.get("build_cuda") is True]
    missing_cuda = [str(row["label"]) for row in cuda_variants if not row.get("build_ready")]
    unknown_labels = [str(row["label"]) for row in variants if not row.get("known_label")]
    ready_variants = [str(row["label"]) for row in variants if row.get("build_ready")]
    checks = [
        _check(
            "all_package_labels_known",
            not unknown_labels,
            {"unknown_labels": unknown_labels, "requested_labels": list(package_labels)},
        ),
        _check(
            "cpu_package_planned",
            any(row.get("label") == "cpu" and row.get("build_ready") for row in variants),
            {"ready_variants": ready_variants},
        ),
    ]
    if cuda_variants:
        checks.append(
            _check(
                "at_least_one_cuda_variant_ready",
                any(row.get("build_ready") for row in cuda_variants),
                {
                    "ready_cuda_variants": [str(row["label"]) for row in cuda_variants if row.get("build_ready")],
                    "missing_cuda_variants": missing_cuda,
                },
            )
        )
    if require_all_toolkits:
        checks.append(
            _check(
                "all_requested_cuda_toolkits_ready",
                not missing_cuda,
                {"missing_cuda_variants": missing_cuda},
            )
        )
    failed = [item for item in checks if not item.get("passed")]
    all_requested_ready = not missing_cuda and not unknown_labels
    status = "build_plan_ready" if all_requested_ready else "partial_toolkits"
    if failed:
        status = "blocked"
    return {
        "schema_version": 1,
        "artifact_type": "windows_package_build_plan",
        "created_at": now_iso(),
        "status": status,
        "passed": not failed,
        "recommendation": (
            "build_all_variants"
            if all_requested_ready
            else "build_ready_variants_and_install_missing_toolkits"
            if not failed
            else "fix_package_build_plan_blockers"
        ),
        "inputs": {
            "release_root": str(root),
            "cuda_base": str(cuda_base),
            "package_labels": list(package_labels),
            "python": python,
            "configuration": configuration,
            "static_cuda_runtime": bool(static_cuda_runtime),
            "require_all_toolkits": bool(require_all_toolkits),
            "toolkit_root_overrides": explicit_roots,
        },
        "discovered_toolkits": discovered,
        "variants": variants,
        "ready_variants": ready_variants,
        "missing_cuda_variants": missing_cuda,
        "checks": checks,
        "failed_checks": [str(item.get("name")) for item in failed],
        "limitations": [
            "This artifact plans package builds; it does not install CUDA Toolkits or build packages.",
            "CUDA Toolkit compatibility is matched by major version unless an exact version is discovered.",
            "Each build_portable.ps1 invocation overwrites the shared .release/windows/GLASS package root.",
        ],
    }


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# GLASS Windows Package Build Plan",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Passed: `{payload.get('passed')}`",
        f"- Recommendation: `{payload.get('recommendation')}`",
        f"- Ready variants: `{', '.join(payload.get('ready_variants') or [])}`",
        f"- Missing CUDA variants: `{', '.join(payload.get('missing_cuda_variants') or [])}`",
        "",
        "## Discovered Toolkits",
        "",
        "| Version | Path | nvcc |",
        "| --- | --- | --- |",
    ]
    for row in payload.get("discovered_toolkits") or []:
        lines.append(f"| {row.get('version')} | `{row.get('path')}` | {row.get('nvcc_exists')} |")
    lines.extend(["", "## Variants", "", "| Label | Ready | Toolkit | Match | Zip |", "| --- | --- | --- | --- | --- |"])
    for row in payload.get("variants") or []:
        lines.append(
            "| "
            f"{row.get('label')} | {row.get('build_ready')} | {row.get('toolkit_version')} | "
            f"{row.get('toolkit_match')} | `{row.get('zip_path')}` |"
        )
    lines.extend(["", "## Build Commands", ""])
    for row in payload.get("variants") or []:
        command = row.get("build_command_text")
        if command:
            lines.extend([f"### {row.get('label')}", "", "```powershell", str(command), "```", ""])
    missing_rows = [
        row
        for row in payload.get("variants") or []
        if row.get("build_cuda") is True and not row.get("build_ready")
    ]
    if missing_rows:
        lines.extend(["## Missing Toolkit Commands", ""])
        for row in missing_rows:
            label = row.get("label")
            download = row.get("toolkit_download_command_text")
            install = row.get("toolkit_install_command_text")
            if download:
                lines.extend([f"### {label} download", "", "```powershell", str(download), "```", ""])
            if install:
                lines.extend([f"### {label} install", "", "```powershell", str(install), "```", ""])
    lines.extend(["## Checks", ""])
    for item in payload.get("checks") or []:
        marker = "PASS" if item.get("passed") else "FAIL"
        lines.append(f"- {marker}: `{item.get('name')}` - {item.get('evidence')}")
    lines.append("")
    return "\n".join(lines)


def write_windows_package_build_plan(
    out: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(out, payload)
    if markdown is not None:
        Path(markdown).parent.mkdir(parents=True, exist_ok=True)
        Path(markdown).write_text(_markdown(payload), encoding="utf-8")
