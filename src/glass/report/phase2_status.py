from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from glass.io.json_io import read_json, write_json
from glass.models import now_iso


_CHECKPOINT_RE = re.compile(r"s2_gate_(\d+)_status\.md$")


def _read_json_optional(path: str | Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    target = Path(path)
    if not target.exists():
        return {"path": str(target), "exists": False}
    payload = read_json(target)
    if not isinstance(payload, dict):
        return {"path": str(target), "exists": True, "valid_json_object": False}
    payload = dict(payload)
    payload["_path"] = str(target)
    payload["_exists"] = True
    return payload


def _field_from_status(text: str, key: str) -> str | None:
    prefix = f"- {key}:"
    for line in text.splitlines():
        if line.strip().startswith(prefix):
            return line.split(":", 1)[1].strip()
    return None


def _latest_checkpoint(checkpoint_dir: str | Path) -> dict[str, Any]:
    root = Path(checkpoint_dir)
    candidates: list[tuple[int, Path]] = []
    if root.exists():
        for path in root.glob("s2_gate_*_status.md"):
            match = _CHECKPOINT_RE.match(path.name)
            if match:
                candidates.append((int(match.group(1)), path))
    if not candidates:
        return {"exists": False, "checkpoint_dir": str(root), "gate": None, "status": "missing"}
    gate, path = max(candidates, key=lambda item: item[0])
    text = path.read_text(encoding="utf-8")
    status = _field_from_status(text, "Status")
    scope = _field_from_status(text, "Scope")
    date = _field_from_status(text, "Date")
    return {
        "exists": True,
        "checkpoint_dir": str(root),
        "gate": gate,
        "path": str(path),
        "status": status,
        "scope": scope,
        "date": date,
        "green": str(status).lower() == "green",
    }


def _acceptance_summary(path: str | Path | None) -> dict[str, Any] | None:
    payload = _read_json_optional(path)
    if payload is None:
        return None
    if not payload.get("_exists", payload.get("exists", False)):
        return {
            "path": str(path),
            "exists": False,
            "status": "missing",
            "passed": False,
        }
    speedup = payload.get("speedup_summary") if isinstance(payload.get("speedup_summary"), dict) else {}
    comparison = speedup.get("comparison") if isinstance(speedup.get("comparison"), dict) else {}
    bundle_schema = (
        payload.get("contract_bundle_schema")
        if isinstance(payload.get("contract_bundle_schema"), dict)
        else {}
    )
    resident_contracts = (
        payload.get("resident_contracts") if isinstance(payload.get("resident_contracts"), dict) else {}
    )
    return {
        "path": payload.get("_path"),
        "exists": True,
        "status": payload.get("status"),
        "passed": payload.get("passed"),
        "benchmark_contract": payload.get("benchmark_contract"),
        "frame_type_counts": payload.get("frame_type_counts"),
        "speedup_vs_reference": speedup.get("speedup_vs_wbpp"),
        "active_frames": speedup.get("glass", {}).get("weighted_frame_count")
        if isinstance(speedup.get("glass"), dict)
        else None,
        "rms_diff": comparison.get("rms_diff"),
        "abs_diff_p99": comparison.get("abs_diff_p99"),
        "coverage_fraction": comparison.get("coverage_fraction"),
        "contract_bundle_schema_status": bundle_schema.get("status"),
        "resident_calibration_contract_passed": (resident_contracts.get("calibration") or {}).get("passed")
        if isinstance(resident_contracts.get("calibration"), dict)
        else None,
        "resident_result_contract_passed": (resident_contracts.get("result") or {}).get("passed")
        if isinstance(resident_contracts.get("result"), dict)
        else None,
    }


def _doctor_summary(doctor_payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if doctor_payload is None:
        return None
    cuda = doctor_payload.get("cuda") if isinstance(doctor_payload.get("cuda"), dict) else {}
    devices = cuda.get("devices") if isinstance(cuda.get("devices"), list) else []
    first_device = devices[0] if devices and isinstance(devices[0], dict) else {}
    return {
        "recommendation": doctor_payload.get("recommendation"),
        "cuda_available": cuda.get("cuda_available"),
        "native_extension_loaded": cuda.get("native_extension_loaded"),
        "wrapper_importable": cuda.get("wrapper_importable"),
        "device_count": len(devices),
        "primary_gpu": first_device.get("name"),
        "compute_capability": first_device.get("compute_capability", first_device.get("major_minor")),
        "vram_mib": first_device.get("memory_total_mib", first_device.get("total_global_mem_mib")),
        "driver_version": first_device.get("driver_version"),
        "windows_cuda_packages": doctor_payload.get("windows_cuda_packages"),
    }


def _release_manifest_summary(path: str | Path | None) -> dict[str, Any] | None:
    payload = _read_json_optional(path)
    if payload is None:
        return None
    if not payload.get("_exists", payload.get("exists", False)):
        return {"path": str(path), "exists": False, "status": "missing", "passed": False}
    packages = payload.get("packages") if isinstance(payload.get("packages"), list) else []
    return {
        "path": payload.get("_path"),
        "exists": True,
        "status": payload.get("status"),
        "passed": payload.get("passed"),
        "recommendation": payload.get("recommendation"),
        "package_count": payload.get("package_count", len(packages)),
        "source_stamp": payload.get("source_stamp"),
    }


def _github_release_plan_summary(path: str | Path | None) -> dict[str, Any] | None:
    payload = _read_json_optional(path)
    if payload is None:
        return None
    if not payload.get("_exists", payload.get("exists", False)):
        return {"path": str(path), "exists": False, "status": "missing", "publication_ready": False}
    gh = payload.get("gh") if isinstance(payload.get("gh"), dict) else {}
    script = payload.get("script") if isinstance(payload.get("script"), dict) else {}
    return {
        "path": payload.get("_path"),
        "exists": True,
        "status": payload.get("status"),
        "tag": payload.get("tag"),
        "package_count": payload.get("package_count"),
        "publication_ready": payload.get("publication_ready"),
        "recommendation": payload.get("recommendation"),
        "gh_available": gh.get("available"),
        "gh_auth_ok": gh.get("auth_ok"),
        "script_path": script.get("path"),
        "script_publish_default": script.get("publish_default"),
    }


def build_phase2_status(
    *,
    checkpoint_dir: str | Path,
    acceptance_audit: str | Path | None = None,
    release_manifest: str | Path | None = None,
    github_release_plan: str | Path | None = None,
    doctor_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    checkpoint = _latest_checkpoint(checkpoint_dir)
    acceptance = _acceptance_summary(acceptance_audit)
    doctor = _doctor_summary(doctor_payload)
    release = _release_manifest_summary(release_manifest)
    github_plan = _github_release_plan_summary(github_release_plan)
    checks = [
        {
            "name": "latest_checkpoint_green",
            "passed": bool(checkpoint.get("green")),
            "evidence": {"gate": checkpoint.get("gate"), "status": checkpoint.get("status")},
        }
    ]
    if acceptance is not None:
        checks.append(
            {
                "name": "acceptance_audit_passed",
                "passed": acceptance.get("passed") is True,
                "evidence": {
                    "status": acceptance.get("status"),
                    "speedup_vs_reference": acceptance.get("speedup_vs_reference"),
                },
            }
        )
    if doctor is not None:
        checks.append(
            {
                "name": "cuda_doctor_available",
                "passed": doctor.get("cuda_available") is True,
                "evidence": {
                    "cuda_available": doctor.get("cuda_available"),
                    "primary_gpu": doctor.get("primary_gpu"),
                },
            }
        )
    if release is not None:
        checks.append(
            {
                "name": "release_manifest_ready",
                "passed": release.get("status") == "release_manifest_ready",
                "evidence": {
                    "status": release.get("status"),
                    "package_count": release.get("package_count"),
                },
            }
        )
    if github_plan is not None:
        checks.append(
            {
                "name": "github_release_plan_ready",
                "passed": github_plan.get("status") == "release_plan_ready",
                "evidence": {
                    "status": github_plan.get("status"),
                    "publication_ready": github_plan.get("publication_ready"),
                    "gh_auth_ok": github_plan.get("gh_auth_ok"),
                },
            }
        )
    passed = all(item["passed"] for item in checks)
    return {
        "schema_version": 1,
        "artifact_type": "glass_phase2_status",
        "created_at": now_iso(),
        "status": "green" if passed else "attention_required",
        "passed": passed,
        "latest_checkpoint": checkpoint,
        "acceptance_audit": acceptance,
        "doctor": doctor,
        "release_manifest": release,
        "github_release_plan": github_plan,
        "checks": checks,
    }


def write_phase2_status_markdown(path: str | Path, payload: dict[str, Any]) -> None:
    checkpoint = payload.get("latest_checkpoint") or {}
    acceptance = payload.get("acceptance_audit") or {}
    doctor = payload.get("doctor") or {}
    release = payload.get("release_manifest") or {}
    github_plan = payload.get("github_release_plan") or {}
    lines = [
        "# GLASS Phase 2 Status",
        "",
        f"- Status: {payload.get('status')}",
        f"- Latest checkpoint: S2-Gate {checkpoint.get('gate')} ({checkpoint.get('status')})",
        f"- Checkpoint path: {checkpoint.get('path')}",
    ]
    if acceptance:
        lines.extend(
            [
                "",
                "## Acceptance",
                "",
                f"- Status: {acceptance.get('status')}",
                f"- Speedup vs reference: {acceptance.get('speedup_vs_reference')}",
                f"- Active frames: {acceptance.get('active_frames')}",
                f"- RMS diff: {acceptance.get('rms_diff')}",
                f"- Coverage fraction: {acceptance.get('coverage_fraction')}",
                f"- Contract bundle schema: {acceptance.get('contract_bundle_schema_status')}",
                f"- Resident calibration contract: {acceptance.get('resident_calibration_contract_passed')}",
                f"- Resident result contract: {acceptance.get('resident_result_contract_passed')}",
            ]
        )
    if doctor:
        lines.extend(
            [
                "",
                "## CUDA",
                "",
                f"- CUDA available: {doctor.get('cuda_available')}",
                f"- Native extension loaded: {doctor.get('native_extension_loaded')}",
                f"- Primary GPU: {doctor.get('primary_gpu')}",
                f"- Compute capability: {doctor.get('compute_capability')}",
                f"- VRAM MiB: {doctor.get('vram_mib')}",
                f"- Driver: {doctor.get('driver_version')}",
            ]
        )
    if release:
        lines.extend(
            [
                "",
                "## Windows Release",
                "",
                f"- Manifest status: {release.get('status')}",
                f"- Package count: {release.get('package_count')}",
                f"- Recommendation: {release.get('recommendation')}",
            ]
        )
    if github_plan:
        lines.extend(
            [
                "",
                "## GitHub Release Plan",
                "",
                f"- Plan status: {github_plan.get('status')}",
                f"- Tag: {github_plan.get('tag')}",
                f"- Publication ready: {github_plan.get('publication_ready')}",
                f"- GitHub auth OK: {github_plan.get('gh_auth_ok')}",
                f"- Script path: {github_plan.get('script_path')}",
            ]
        )
    lines.extend(["", "## Checks", ""])
    for item in payload.get("checks") or []:
        marker = "PASS" if item.get("passed") else "FAIL"
        lines.append(f"- {marker}: {item.get('name')} - {item.get('evidence')}")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_phase2_status(
    out_json: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(out_json, payload)
    if markdown is not None:
        write_phase2_status_markdown(markdown, payload)
