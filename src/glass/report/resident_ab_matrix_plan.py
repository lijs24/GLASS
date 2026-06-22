from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
import shlex
import shutil
import time
import subprocess
from pathlib import Path
from typing import Any

from glass.io.json_io import write_json
from glass.io.json_io import read_json
from glass.models import now_iso
from glass.report.benchmark_contract_profile import RESIDENT_CUDA_DQ_PROFILE_NAME


DEFAULT_VARIANTS: tuple[dict[str, Any], ...] = (
    {
        "variant_id": "throughput_v1_lanczos3_parity",
        "role": "baseline",
        "purpose": "WBPP-like parity route with throughput-v1 scheduling and Lanczos3 matrix warp",
        "runtime_preset": "throughput-v1",
        "warp_interpolation": "lanczos3",
        "integration_dispatch": "stack",
    },
    {
        "variant_id": "throughput_v2_fused_bilinear",
        "role": "candidate",
        "purpose": "fused resident matrix-integration candidate with throughput-v2 preset and bilinear warp sampling",
        "runtime_preset": "throughput-v2-fused",
        "warp_interpolation": "bilinear",
        "integration_dispatch": "auto",
    },
)
EXECUTION_STEP_ORDER = (
    "run",
    "compare_reference",
    "compare_baseline",
    "acceptance_audit",
    "speedup_summary",
    "report",
)


def _command(tokens: list[str | Path | int | float]) -> str:
    return subprocess.list2cmdline([str(token) for token in tokens])


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


def _parse_gpu_readiness(
    text: str | None,
    *,
    min_free_mib: int,
    max_utilization: int,
) -> dict[str, Any]:
    if not text:
        return {
            "status": "unknown",
            "ready": False,
            "reason": "gpu probe was not available",
            "name": None,
            "total_mib": None,
            "used_mib": None,
            "free_mib": None,
            "utilization_percent": None,
            "driver": None,
            "min_free_mib": int(min_free_mib),
            "max_utilization_percent": int(max_utilization),
        }
    first = next((line.strip() for line in str(text).splitlines() if line.strip()), "")
    parts = [part.strip() for part in first.split(",")]
    if len(parts) < 5:
        return {
            "status": "unknown",
            "ready": False,
            "reason": f"unexpected nvidia-smi output: {first}",
            "raw": first,
            "min_free_mib": int(min_free_mib),
            "max_utilization_percent": int(max_utilization),
        }
    try:
        total_mib = int(float(parts[1]))
        used_mib = int(float(parts[2]))
        utilization = int(float(parts[3]))
    except ValueError:
        return {
            "status": "unknown",
            "ready": False,
            "reason": f"could not parse nvidia-smi output: {first}",
            "raw": first,
            "min_free_mib": int(min_free_mib),
            "max_utilization_percent": int(max_utilization),
        }
    free_mib = total_mib - used_mib
    if free_mib < min_free_mib:
        status = "low_free_memory"
        reason = f"only {free_mib} MiB GPU memory is free"
    elif utilization > max_utilization:
        status = "busy"
        reason = f"GPU utilization is {utilization}%, above the clean benchmark threshold"
    else:
        status = "ready"
        reason = "GPU is below the clean benchmark utilization threshold and has enough free memory"
    return {
        "status": status,
        "ready": status == "ready",
        "reason": reason,
        "name": parts[0],
        "total_mib": total_mib,
        "used_mib": used_mib,
        "free_mib": free_mib,
        "utilization_percent": utilization,
        "driver": parts[4],
        "min_free_mib": int(min_free_mib),
        "max_utilization_percent": int(max_utilization),
    }


def _disk_readiness(root: Path, *, min_free_gib: float) -> dict[str, Any]:
    root_parent = root if root.exists() else root.parent
    while not root_parent.exists() and root_parent != root_parent.parent:
        root_parent = root_parent.parent
    usage = shutil.disk_usage(root_parent)
    free_gib = usage.free / (1024**3)
    return {
        "path": str(root_parent),
        "free_gib": free_gib,
        "total_gib": usage.total / (1024**3),
        "min_free_gib": float(min_free_gib),
        "ready": bool(free_gib >= float(min_free_gib)),
        "status": "ready" if free_gib >= float(min_free_gib) else "low_free_space",
    }


def _run_master(run_dir: Path) -> Path:
    return run_dir / "integration" / "resident_master_H.fits"


def _run_coverage(run_dir: Path) -> Path:
    return run_dir / "integration" / "resident_coverage_map_H.fits"


def _build_run_command(
    *,
    plan: str | Path,
    run_dir: Path,
    variant: dict[str, Any],
    reference_frame_id: str,
    output_maps: str,
) -> str:
    tokens: list[str | Path | int | float] = [
        "glass",
        "run",
        "--plan",
        plan,
        "--out",
        run_dir,
        "--backend",
        "cuda",
        "--memory-mode",
        "resident",
        "--resident-runtime-preset",
        variant["runtime_preset"],
        "--until-stage",
        "integration",
        "--local-normalization",
        "off",
        "--integration-rejection",
        "winsorized_sigma",
        "--integration-weighting",
        "none",
        "--flat-floor",
        0.05,
        "--resident-registration",
        "similarity_cuda_triangle",
        "--resident-star-threshold",
        350,
        "--resident-star-max-candidates",
        48,
        "--resident-star-tolerance-px",
        3,
        "--resident-ncc-sample-stride",
        4,
        "--resident-warp-interpolation",
        variant["warp_interpolation"],
        "--reference-frame-id",
        reference_frame_id,
        "--resident-output-maps",
        output_maps,
    ]
    if variant.get("integration_dispatch") == "stack":
        tokens.extend(["--resident-integration-dispatch", "stack"])
    return _command(tokens)


def _compare_command(
    *,
    glass_master: Path,
    reference: str | Path,
    out: Path,
    coverage: Path | None,
    glass_scale: float | None,
    glass_offset: float | None,
    min_coverage: float | None,
    glass_label: str,
    reference_label: str,
) -> str:
    tokens: list[str | Path | int | float] = [
        "glass",
        "compare",
        "--glass",
        glass_master,
        "--reference",
        reference,
        "--out",
        out,
        "--glass-label",
        glass_label,
        "--reference-label",
        reference_label,
    ]
    if glass_scale is not None:
        tokens.extend(["--glass-scale", glass_scale])
    if glass_offset is not None:
        tokens.extend(["--glass-offset", glass_offset])
    if coverage is not None and min_coverage is not None:
        tokens.extend(["--glass-coverage-map", coverage, "--min-coverage", min_coverage])
    return _command(tokens)


def _acceptance_command(
    *,
    manifest: str | Path,
    glass_run: Path,
    wbpp_result: str | Path,
    compare_json: Path,
    out: Path,
    markdown: Path,
    min_speedup: float,
    benchmark_contract_profile: str,
) -> str:
    return _command(
        [
            "glass",
            "acceptance-audit",
            "--manifest",
            manifest,
            "--glass-run",
            glass_run,
            "--wbpp-result",
            wbpp_result,
            "--compare-json",
            compare_json,
            "--out",
            out,
            "--markdown",
            markdown,
            "--min-active-frames",
            190,
            "--min-speedup",
            min_speedup,
            "--min-coverage-fraction",
            0.95,
            "--max-rms-diff",
            0.01,
            "--max-abs-diff-p99",
            0.01,
            "--benchmark-contract-profile",
            benchmark_contract_profile,
        ]
    )


def _speedup_command(
    *,
    glass_run: Path,
    wbpp_result: str | Path,
    compare_json: Path,
    out: Path,
    markdown: Path,
    min_speedup: float,
) -> str:
    return _command(
        [
            "python",
            "benchmarks\\summarize_wbpp_speedup.py",
            "--glass-run",
            glass_run,
            "--wbpp-result",
            wbpp_result,
            "--compare-json",
            compare_json,
            "--out",
            out,
            "--markdown",
            markdown,
            "--min-speedup",
            min_speedup,
        ]
    )


def _report_command(*, glass_run: Path, out: Path) -> str:
    return _command(["glass", "report", "--run", glass_run, "--out", out])


def build_resident_ab_matrix_plan(
    *,
    root: str | Path,
    plan: str | Path,
    manifest: str | Path,
    wbpp_result: str | Path,
    reference: str | Path,
    glass_scale: float | None = None,
    glass_offset: float | None = None,
    min_coverage: float = 190.0,
    min_speedup: float = 2.0,
    reference_frame_id: str = "LIGHT_H_0136",
    output_maps: str = "audit",
    min_gpu_free_mib: int = 65000,
    max_gpu_utilization: int = 20,
    min_disk_free_gib: float = 8.0,
    benchmark_contract_profile: str = RESIDENT_CUDA_DQ_PROFILE_NAME,
    probe_gpu: bool = True,
    gpu_query_text: str | None = None,
) -> dict[str, Any]:
    root_path = Path(root)
    gpu_error = None
    if gpu_query_text is None and probe_gpu:
        gpu_query_text, gpu_error = _probe_gpu_text()
    gpu = _parse_gpu_readiness(
        gpu_query_text,
        min_free_mib=min_gpu_free_mib,
        max_utilization=max_gpu_utilization,
    )
    if gpu_error is not None:
        gpu["probe_error"] = gpu_error
    disk = _disk_readiness(root_path, min_free_gib=min_disk_free_gib)
    baseline_run = root_path / "runs" / DEFAULT_VARIANTS[0]["variant_id"]
    baseline_master = _run_master(baseline_run)

    variants: list[dict[str, Any]] = []
    for variant in DEFAULT_VARIANTS:
        variant_id = str(variant["variant_id"])
        run_dir = root_path / "runs" / variant_id
        master = _run_master(run_dir)
        coverage = _run_coverage(run_dir)
        compare_reference_html = root_path / "compare" / f"{variant_id}_vs_wbpp.html"
        acceptance_json = root_path / "acceptance" / f"{variant_id}_acceptance.json"
        acceptance_md = root_path / "acceptance" / f"{variant_id}_acceptance.md"
        speedup_json = root_path / "speedup" / f"{variant_id}_speedup.json"
        speedup_md = root_path / "speedup" / f"{variant_id}_speedup.md"
        report_html = root_path / "reports" / f"{variant_id}_report.html"
        commands = {
            "run": _build_run_command(
                plan=plan,
                run_dir=run_dir,
                variant=variant,
                reference_frame_id=reference_frame_id,
                output_maps=output_maps,
            ),
            "compare_reference": _compare_command(
                glass_master=master,
                reference=reference,
                out=compare_reference_html,
                coverage=coverage,
                glass_scale=glass_scale,
                glass_offset=glass_offset,
                min_coverage=min_coverage,
                glass_label=f"GLASS {variant_id}",
                reference_label="WBPP FastIntegration black-box",
            ),
            "acceptance_audit": _acceptance_command(
                manifest=manifest,
                glass_run=run_dir,
                wbpp_result=wbpp_result,
                compare_json=compare_reference_html.with_suffix(".json"),
                out=acceptance_json,
                markdown=acceptance_md,
                min_speedup=min_speedup,
                benchmark_contract_profile=benchmark_contract_profile,
            ),
            "speedup_summary": _speedup_command(
                glass_run=run_dir,
                wbpp_result=wbpp_result,
                compare_json=compare_reference_html.with_suffix(".json"),
                out=speedup_json,
                markdown=speedup_md,
                min_speedup=min_speedup,
            ),
            "report": _report_command(glass_run=run_dir, out=report_html),
        }
        if variant["role"] != "baseline":
            compare_baseline_html = root_path / "compare" / f"{variant_id}_vs_{DEFAULT_VARIANTS[0]['variant_id']}.html"
            commands["compare_baseline"] = _compare_command(
                glass_master=master,
                reference=baseline_master,
                out=compare_baseline_html,
                coverage=coverage,
                glass_scale=None,
                glass_offset=None,
                min_coverage=min_coverage,
                glass_label=f"GLASS {variant_id}",
                reference_label=f"GLASS {DEFAULT_VARIANTS[0]['variant_id']}",
            )
        run_timing = run_dir / "run_timing.json"
        variants.append(
            {
                "variant_id": variant_id,
                "role": variant["role"],
                "purpose": variant["purpose"],
                "run_dir": str(run_dir),
                "runtime_preset": variant["runtime_preset"],
                "warp_interpolation": variant["warp_interpolation"],
                "integration_dispatch": variant["integration_dispatch"],
                "run_timing_exists": run_timing.exists(),
                "artifacts": {
                    "master": str(master),
                    "coverage_map": str(coverage),
                    "compare_reference_json": str(compare_reference_html.with_suffix(".json")),
                    "acceptance_json": str(acceptance_json),
                    "speedup_json": str(speedup_json),
                    "report_html": str(report_html),
                },
                "commands": commands,
            }
        )

    ready_to_execute = bool(gpu.get("ready") and disk.get("ready"))
    return {
        "schema_version": 1,
        "artifact_type": "resident_ab_matrix_plan",
        "created_at": now_iso(),
        "root": str(root_path),
        "plan": str(plan),
        "manifest": str(manifest),
        "wbpp_result": str(wbpp_result),
        "reference": str(reference),
        "variant_count": len(variants),
        "ready_to_execute": ready_to_execute,
        "recommendation": "execute_when_gpu_idle" if ready_to_execute else "wait_for_clean_gpu_or_disk_window",
        "readiness": {
            "gpu": gpu,
            "disk": disk,
        },
        "comparison_policy": {
            "glass_scale": glass_scale,
            "glass_offset": glass_offset,
            "min_coverage": float(min_coverage),
            "min_speedup": float(min_speedup),
            "benchmark_contract_profile": benchmark_contract_profile,
        },
        "variants": variants,
        "limitations": [
            "This artifact plans commands only; it does not execute image processing.",
            "GPU readiness is a point-in-time nvidia-smi sample and must be rechecked before execution.",
            "The fused candidate intentionally changes interpolation to bilinear so it must pass compare and DQ checks before any promotion.",
        ],
    }


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Resident 200-Light A/B Matrix Plan",
        "",
        f"- Status: {'ready' if payload.get('ready_to_execute') else 'waiting'}",
        f"- Recommendation: {payload.get('recommendation')}",
        f"- Root: `{payload.get('root')}`",
        f"- Plan: `{payload.get('plan')}`",
        f"- Reference: `{payload.get('reference')}`",
        "",
        "## Readiness",
        "",
    ]
    gpu = payload.get("readiness", {}).get("gpu", {})
    disk = payload.get("readiness", {}).get("disk", {})
    lines.extend(
        [
            f"- GPU: {gpu.get('status')} - {gpu.get('reason')}",
            f"- GPU utilization: {gpu.get('utilization_percent')}",
            f"- GPU free MiB: {gpu.get('free_mib')}",
            f"- Disk: {disk.get('status')} - free GiB {disk.get('free_gib')}",
            "",
            "## Variants",
            "",
        ]
    )
    for variant in payload.get("variants", []):
        lines.extend(
            [
                f"### {variant.get('variant_id')}",
                "",
                f"- Role: {variant.get('role')}",
                f"- Runtime preset: `{variant.get('runtime_preset')}`",
                f"- Warp interpolation: `{variant.get('warp_interpolation')}`",
                f"- Integration dispatch: `{variant.get('integration_dispatch')}`",
                f"- Run dir: `{variant.get('run_dir')}`",
                "",
                "Commands:",
                "",
            ]
        )
        for name, command in (variant.get("commands") or {}).items():
            lines.extend([f"- `{name}`:", "", "```powershell", str(command), "```", ""])
    return "\n".join(lines).rstrip() + "\n"


def write_resident_ab_matrix_plan(
    out: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(out, payload)
    if markdown is not None:
        Path(markdown).write_text(_markdown(payload), encoding="utf-8")


def _read_ab_plan(path: str | Path) -> dict[str, Any]:
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"A/B matrix plan must be a JSON object: {path}")
    if payload.get("artifact_type") != "resident_ab_matrix_plan":
        raise ValueError(f"expected resident_ab_matrix_plan artifact, got {payload.get('artifact_type')}")
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


def _variant_complete(variant: dict[str, Any]) -> bool:
    artifacts = variant.get("artifacts") if isinstance(variant.get("artifacts"), dict) else {}
    acceptance = artifacts.get("acceptance_json")
    return bool(acceptance) and Path(str(acceptance)).exists()


def _selected_plan_variants(plan: dict[str, Any], variant_ids: list[str] | None) -> list[dict[str, Any]]:
    variants = [row for row in plan.get("variants", []) if isinstance(row, dict)]
    if not variant_ids:
        return variants
    requested = set(variant_ids)
    selected = [row for row in variants if str(row.get("variant_id")) in requested]
    found = {str(row.get("variant_id")) for row in selected}
    missing = sorted(requested - found)
    if missing:
        raise ValueError(f"unknown A/B matrix variants: {missing}")
    return selected


def _execution_step_record(
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


def build_resident_ab_matrix_execution(
    plan: str | Path,
    *,
    dry_run: bool = False,
    skip_existing: bool = False,
    variants: list[str] | None = None,
    ignore_readiness: bool = False,
    glass_executable: str | Path | None = None,
    cwd: str | Path | None = None,
) -> dict[str, Any]:
    payload = _read_ab_plan(plan)
    selected = _selected_plan_variants(payload, variants)
    readiness_allows_execution = bool(payload.get("ready_to_execute"))
    blocked = bool(not dry_run and not ignore_readiness and not readiness_allows_execution)

    records: list[dict[str, Any]] = []
    failed = False
    if not blocked:
        for variant in selected:
            variant_id = str(variant.get("variant_id"))
            if skip_existing and _variant_complete(variant):
                records.append(
                    {
                        "variant_id": variant_id,
                        "status": "skipped_existing",
                        "steps": [],
                        "acceptance_exists": True,
                    }
                )
                continue
            commands = variant.get("commands") if isinstance(variant.get("commands"), dict) else {}
            steps: list[dict[str, Any]] = []
            variant_status = "planned" if dry_run else "completed"
            for step in EXECUTION_STEP_ORDER:
                command = commands.get(step)
                if not command:
                    if step == "compare_baseline" and variant.get("role") == "baseline":
                        continue
                    raise ValueError(f"variant {variant_id} is missing command for step {step}")
                step_record = _execution_step_record(
                    step=step,
                    command=str(command),
                    dry_run=dry_run,
                    glass_executable=glass_executable,
                    cwd=cwd,
                )
                steps.append(step_record)
                if step_record["status"] == "failed":
                    failed = True
                    variant_status = "failed"
                    break
            records.append(
                {
                    "variant_id": variant_id,
                    "status": variant_status,
                    "steps": steps,
                    "acceptance_exists": _variant_complete(variant),
                }
            )
            if failed:
                break

    status = "blocked_by_readiness" if blocked else "planned" if dry_run else "failed" if failed else "completed"
    return {
        "schema_version": 1,
        "artifact_type": "resident_ab_matrix_execution",
        "created_at": now_iso(),
        "plan": str(plan),
        "dry_run": bool(dry_run),
        "skip_existing": bool(skip_existing),
        "ignore_readiness": bool(ignore_readiness),
        "selected_variant_count": len(selected),
        "summary": {
            "status": status,
            "failed": failed,
            "blocked": blocked,
            "recorded_variant_count": len(records),
            "completed_variant_count": sum(1 for row in records if row.get("status") == "completed"),
            "planned_variant_count": sum(1 for row in records if row.get("status") == "planned"),
            "skipped_existing_count": sum(1 for row in records if row.get("status") == "skipped_existing"),
        },
        "readiness": payload.get("readiness"),
        "variants": records,
        "limitations": [
            "This executor runs only commands recorded in a resident A/B matrix plan.",
            "Non-dry-run execution is blocked by plan readiness unless ignore_readiness is set.",
            "Dry-run mode records intended commands without executing subprocesses.",
        ],
    }


def write_resident_ab_matrix_execution(out: str | Path, payload: dict[str, Any]) -> None:
    write_json(out, payload)
