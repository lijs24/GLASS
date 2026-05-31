from __future__ import annotations

from pathlib import Path
from typing import Any

from glass.io.json_io import write_json
from glass.report.benchmark_contract import (
    build_benchmark_contract_checks,
    build_benchmark_performance_diagnostics,
    collect_dq_provenance_records,
    collect_frame_accounting_record,
    load_benchmark_contract,
)
from glass.report.speedup_report import _read_json_lenient, summarize_wbpp_speedup


def _frame_type_counts(manifest: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {"light": 0, "bias": 0, "dark": 0, "flat": 0}
    for frame in manifest.get("frames") or []:
        frame_type = str(frame.get("frame_type") or "unknown").lower()
        counts[frame_type] = counts.get(frame_type, 0) + 1
    return counts


def _numeric(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _check(name: str, passed: bool, evidence: dict[str, Any], note: str = "") -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "evidence": evidence, "note": note}


def build_acceptance_audit(
    *,
    manifest_path: str | Path,
    glass_run: str | Path,
    wbpp_result: str | Path,
    compare_json: str | Path,
    min_lights: int = 200,
    min_bias: int = 20,
    min_dark: int = 20,
    min_flat: int = 20,
    min_active_frames: int = 1,
    min_speedup: float = 2.0,
    min_coverage_fraction: float = 0.95,
    max_rms_diff: float | None = 0.01,
    max_abs_diff_p99: float | None = 0.01,
    benchmark_contract: str | Path | None = None,
) -> dict[str, Any]:
    manifest = _read_json_lenient(manifest_path)
    speedup = summarize_wbpp_speedup(
        glass_run,
        wbpp_result,
        compare_json=compare_json,
        min_speedup=min_speedup,
    )
    counts = _frame_type_counts(manifest)
    compare_payload = _read_json_lenient(compare_json)
    comparison = speedup.get("comparison") or {}
    gp = speedup["glass"]

    rms = _numeric(comparison.get("rms_diff"))
    p99 = _numeric(comparison.get("abs_diff_p99"))
    coverage = _numeric(comparison.get("coverage_fraction"))
    active_frames = int(gp.get("weighted_frame_count") or 0)

    checks = [
        _check(
            "minimum_light_frames",
            counts.get("light", 0) >= int(min_lights),
            {"actual": counts.get("light", 0), "required": int(min_lights)},
        ),
        _check(
            "minimum_bias_frames",
            counts.get("bias", 0) >= int(min_bias),
            {"actual": counts.get("bias", 0), "required": int(min_bias)},
        ),
        _check(
            "minimum_dark_frames",
            counts.get("dark", 0) >= int(min_dark),
            {"actual": counts.get("dark", 0), "required": int(min_dark)},
        ),
        _check(
            "minimum_flat_frames",
            counts.get("flat", 0) >= int(min_flat),
            {"actual": counts.get("flat", 0), "required": int(min_flat)},
        ),
        _check(
            "minimum_active_frames",
            active_frames >= int(min_active_frames),
            {"actual": active_frames, "required": int(min_active_frames)},
        ),
        _check(
            "minimum_speedup",
            bool(speedup.get("meets_min_speedup")),
            {"actual": speedup.get("speedup_vs_wbpp"), "required": float(min_speedup)},
        ),
        _check(
            "shape_match",
            comparison.get("shape_match") is True,
            {"actual": comparison.get("shape_match"), "required": True},
        ),
        _check(
            "minimum_coverage_fraction",
            coverage is not None and coverage >= float(min_coverage_fraction),
            {"actual": coverage, "required": float(min_coverage_fraction)},
        ),
    ]

    if max_rms_diff is not None:
        checks.append(
            _check(
                "maximum_rms_diff",
                rms is not None and rms <= float(max_rms_diff),
                {"actual": rms, "required_max": float(max_rms_diff)},
            )
        )
    if max_abs_diff_p99 is not None:
        checks.append(
            _check(
                "maximum_abs_diff_p99",
                p99 is not None and p99 <= float(max_abs_diff_p99),
                {"actual": p99, "required_max": float(max_abs_diff_p99)},
            )
        )

    contract_payload: dict[str, Any] | None = None
    if benchmark_contract is not None:
        contract_payload = load_benchmark_contract(benchmark_contract)
    performance_regression: dict[str, Any] | None = None
    dq_provenance_records = collect_dq_provenance_records(
        glass_run,
        dq_contract=(contract_payload or {}).get("dq_provenance"),
    )
    frame_accounting_record = collect_frame_accounting_record(glass_run)
    if benchmark_contract is not None:
        checks.extend(
            build_benchmark_contract_checks(
                contract_payload,
                glass_run=glass_run,
                speedup_summary=speedup,
                compare_payload=compare_payload,
                frame_type_counts=counts,
                dq_provenance_records=dq_provenance_records,
                frame_accounting_record=frame_accounting_record,
            )
        )
        performance_regression = build_benchmark_performance_diagnostics(
            contract_payload,
            glass_run=glass_run,
        )

    passed = all(item["passed"] for item in checks)
    return {
        "schema_version": 1,
        "status": "passed" if passed else "failed",
        "passed": passed,
        "manifest_path": str(manifest_path),
        "glass_run": str(glass_run),
        "wbpp_result": str(wbpp_result),
        "compare_json": str(compare_json),
        "benchmark_contract": None
        if benchmark_contract is None
        else {
            "path": str(benchmark_contract),
            "name": contract_payload.get("name") if contract_payload else None,
            "schema_version": contract_payload.get("schema_version") if contract_payload else None,
        },
        "frame_type_counts": counts,
        "checks": checks,
        "performance_regression": performance_regression,
        "dq_provenance": {
            "schema_version": 1,
            "record_count": len(dq_provenance_records),
            "records": dq_provenance_records,
            "contract": (contract_payload or {}).get("dq_provenance") if contract_payload else None,
        },
        "frame_accounting": frame_accounting_record,
        "speedup_summary": speedup,
        "clean_room": {
            "status": "compliant",
            "note": (
                "Acceptance audit consumes GLASS artifacts and user-generated PixInsight/WBPP "
                "black-box timing/output metadata only."
            ),
        },
    }


def write_acceptance_audit_markdown(path: str | Path, audit: dict[str, Any]) -> None:
    speedup = audit["speedup_summary"]
    comparison = speedup.get("comparison") or {}
    lines = [
        "# GLASS Acceptance Audit",
        "",
        f"- Status: {audit['status']}",
        f"- Benchmark contract: {(audit.get('benchmark_contract') or {}).get('name')}",
        f"- DQ provenance records: {(audit.get('dq_provenance') or {}).get('record_count')}",
        f"- Frame accounting artifact: {(audit.get('frame_accounting') or {}).get('path')}",
        f"- Speedup vs WBPP: {speedup.get('speedup_vs_wbpp')}",
        f"- Frame counts: {audit.get('frame_type_counts')}",
        f"- Shape match: {comparison.get('shape_match')}",
        f"- RMS diff: {comparison.get('rms_diff')}",
        f"- abs diff p99: {comparison.get('abs_diff_p99')}",
        f"- Coverage fraction: {comparison.get('coverage_fraction')}",
        "",
        "## Checks",
        "",
    ]
    for item in audit["checks"]:
        marker = "PASS" if item["passed"] else "FAIL"
        lines.append(f"- {marker}: {item['name']} - {item['evidence']}")
    dq = audit.get("dq_provenance") or {}
    if dq.get("records"):
        lines.extend(["", "## DQ Provenance", ""])
        for record in dq.get("records") or []:
            summary = record.get("summary") or {}
            verification = record.get("dq_map_pixel_verification") or {}
            output_maps = record.get("output_count_map_verification") or {}
            lines.append(
                "- "
                f"{record.get('source_file')}[{record.get('index')}] "
                f"schema={summary.get('source_schema')} engine={summary.get('engine')} "
                f"stage={summary.get('stage')} item={summary.get('item')} "
                f"dq_map_exists={record.get('dq_map_exists')} "
                f"legacy_normalized={record.get('normalized_from_legacy')} "
                f"pixel_verification={verification.get('status')} "
                f"coverage_verification={(output_maps.get('coverage') or {}).get('status')}"
            )
    accounting = audit.get("frame_accounting") or {}
    if accounting:
        summary = accounting.get("summary") or {}
        weights = accounting.get("integration_weight_counts") or {}
        registration = accounting.get("registration_counts") or {}
        lines.extend(["", "## Frame Accounting", ""])
        lines.append(f"- Exists: {accounting.get('exists')}")
        lines.append(f"- Input lights: {summary.get('input_light_frames')}")
        lines.append(f"- Integrated frames: {summary.get('integrated_frames')}")
        lines.append(f"- Zero-weight frames: {summary.get('zero_weight_frames')}")
        lines.append(f"- Final status counts: {summary.get('final_status_counts')}")
        lines.append(f"- Integration weight counts: {weights}")
        lines.append(f"- Registration counts: {registration}")
    regression = audit.get("performance_regression")
    if regression:
        lines.extend(["", "## Performance Regression Diagnostics", ""])
        lines.append(f"- Status: {regression.get('status')}")
        worst = regression.get("worst_regression") or {}
        if worst:
            lines.append(
                "- Worst stage: "
                f"{worst.get('stage')} actual={worst.get('actual_s')}s "
                f"baseline={worst.get('baseline_s')}s factor={worst.get('factor')}"
            )
        for item in (regression.get("items") or [])[:8]:
            lines.append(
                "- "
                f"{item.get('status')}: {item.get('stage')} "
                f"actual={item.get('actual_s')}s baseline={item.get('baseline_s')}s "
                f"delta={item.get('delta_s')}s factor={item.get('factor')}"
            )
    lines.extend(["", "## Clean-room", "", f"- {audit['clean_room']['note']}", ""])
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines), encoding="utf-8")


def write_acceptance_audit(
    out_json: str | Path,
    audit: dict[str, Any],
    markdown: str | Path | None = None,
) -> None:
    write_json(out_json, audit)
    if markdown is not None:
        write_acceptance_audit_markdown(markdown, audit)
