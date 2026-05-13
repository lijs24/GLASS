from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from glass.io.json_io import read_json, write_json
from glass.report.compare_report import compare_fits, write_compare_report


def _frame_rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for frame in manifest.get("frames", []):
        rows.append(
            {
                "id": frame.get("id"),
                "frame_type": frame.get("frame_type"),
                "filter": frame.get("filter"),
                "exposure_s": frame.get("exposure_s"),
                "gain": frame.get("gain"),
                "offset": frame.get("offset"),
                "temperature_c": frame.get("temperature_c"),
                "width": frame.get("width"),
                "height": frame.get("height"),
                "path": frame.get("path"),
            }
        )
    return rows


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = list(rows[0].keys()) if rows else [
        "id",
        "frame_type",
        "filter",
        "exposure_s",
        "gain",
        "offset",
        "temperature_c",
        "width",
        "height",
        "path",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def _master_paths(run_dir: Path | None) -> list[str]:
    if run_dir is None:
        return []
    integration = run_dir / "integration_results.json"
    if not integration.exists():
        return []
    payload = read_json(integration)
    return [str(item.get("master_path")) for item in payload.get("outputs", []) if item.get("master_path")]


def _run_timing(run_dir: Path | None) -> dict[str, Any] | None:
    if run_dir is None:
        return None
    timing_path = run_dir / "run_timing.json"
    if not timing_path.exists():
        return None
    timing = read_json(timing_path)
    return timing if isinstance(timing, dict) else None


def _resolve_glass_time(
    run_dir: Path | None, explicit_seconds: float | None
) -> tuple[float | None, str | None, list[dict[str, Any]]]:
    if explicit_seconds is not None:
        return float(explicit_seconds), "explicit_cli", []
    timing = _run_timing(run_dir)
    if timing is None:
        return None, None, []
    total = timing.get("total_elapsed_s")
    if total is None:
        return None, None, []
    stages = timing.get("stages", [])
    return float(total), "run_timing_json", stages if isinstance(stages, list) else []


def _write_manual(path: Path, rows: list[dict[str, Any]], glass_masters: list[str], glass_time: float | None) -> None:
    counts: dict[str, int] = {}
    for row in rows:
        counts[str(row.get("frame_type"))] = counts.get(str(row.get("frame_type")), 0) + 1
    lines = [
        "# PixInsight/WBPP Black-box Handoff",
        "",
        "This package is for a clean-room black-box comparison. Do not read or copy official WBPP/PJSR source.",
        "",
        "## Input Counts",
        "",
    ]
    for key in sorted(counts):
        lines.append(f"- {key}: {counts[key]}")
    lines.extend(
        [
            "",
            "## Manual WBPP Run",
            "",
            "1. Start PixInsight normally.",
            "2. Open WBPP through the installed application UI.",
            "3. Add the files listed in `input_frames.csv` with their recorded frame types.",
            "4. Keep output in a separate WBPP directory; do not modify the original input files.",
            "5. Record wall-clock elapsed seconds and save/export the WBPP log or process settings if available.",
            "6. Put the WBPP final master path and elapsed seconds into `timing_template.json`.",
            "   GLASS time is prefilled when `run_timing.json` exists in the GLASS run directory.",
            "7. Run the generated `compare_command.ps1` after replacing the placeholder reference path/time.",
            "",
            "## GLASS Masters",
            "",
        ]
    )
    if glass_masters:
        lines.extend(f"- `{value}`" for value in glass_masters)
    else:
        lines.append("- No GLASS integration master was found in the supplied run directory.")
    lines.extend(["", f"GLASS elapsed seconds: `{glass_time}`"])
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def create_blackbox_package(
    manifest_path: str | Path,
    plan_path: str | Path | None,
    out_dir: str | Path,
    glass_run: str | Path | None = None,
    glass_time_seconds: float | None = None,
    reference_label: str = "PixInsight WBPP",
) -> dict[str, Any]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    manifest = read_json(manifest_path)
    plan = read_json(plan_path) if plan_path is not None and Path(plan_path).exists() else None
    run = Path(glass_run) if glass_run is not None else None
    rows = _frame_rows(manifest)
    masters = _master_paths(run)
    resolved_glass_time, timing_source, stage_timings = _resolve_glass_time(run, glass_time_seconds)
    csv_path = out / "input_frames.csv"
    manual_path = out / "wbpp_manual_run.md"
    timing_path = out / "timing_template.json"
    compare_path = out / "compare_command.ps1"
    _write_csv(csv_path, rows)
    _write_manual(manual_path, rows, masters, resolved_glass_time)

    timing = {
        "manifest_path": str(manifest_path),
        "plan_path": None if plan_path is None else str(plan_path),
        "glass_run": None if run is None else str(run),
        "glass_time_seconds": resolved_glass_time,
        "glass_timing_source": timing_source,
        "glass_stage_timings": stage_timings,
        "glass_master_paths": masters,
        "reference_label": reference_label,
        "reference_time_seconds": None,
        "reference_master_paths": [],
        "plan_executable": None if plan is None else bool(plan.get("executable")),
        "frame_count": len(rows),
    }
    write_json(timing_path, timing)
    gp_master = masters[0] if masters else "<GLASS_MASTER_FITS>"
    compare_path.write_text(
        "\n".join(
            [
                "$ErrorActionPreference='Stop'",
                "$glassMaster = " + repr(gp_master),
                "$referenceMaster = '<WBPP_MASTER_FITS>'",
                "$glassSeconds = "
                + ("<GLASS_SECONDS>" if resolved_glass_time is None else repr(float(resolved_glass_time))),
                "$referenceSeconds = '<WBPP_SECONDS>'",
                ".\\.venv\\Scripts\\glass compare --glass $glassMaster --reference $referenceMaster --out "
                + repr(str(out / "glass_vs_wbpp.html"))
                + " --glass-time-seconds $glassSeconds --reference-time-seconds $referenceSeconds "
                + "--reference-label "
                + repr(reference_label),
                "",
            ]
        ),
        encoding="utf-8",
    )
    payload = {
        "input_frames_csv": str(csv_path),
        "manual_run_md": str(manual_path),
        "timing_template_json": str(timing_path),
        "compare_command_ps1": str(compare_path),
        "frame_count": len(rows),
        "glass_master_count": len(masters),
    }
    write_json(out / "blackbox_package.json", payload)
    return payload


def finalize_blackbox_package(timing_path: str | Path, out_dir: str | Path | None = None) -> dict[str, Any]:
    timing_file = Path(timing_path)
    timing = read_json(timing_file)
    out = Path(out_dir) if out_dir is not None else timing_file.parent
    out.mkdir(parents=True, exist_ok=True)

    glass_time = timing.get("glass_time_seconds")
    reference_time = timing.get("reference_time_seconds")
    glass_masters = [str(value) for value in timing.get("glass_master_paths", [])]
    reference_masters = [str(value) for value in timing.get("reference_master_paths", [])]
    reference_label = str(timing.get("reference_label") or "PixInsight WBPP")
    if glass_time is None:
        run = Path(timing["glass_run"]) if timing.get("glass_run") else None
        glass_time, timing_source, stage_timings = _resolve_glass_time(run, None)
        timing["glass_time_seconds"] = glass_time
        timing["glass_timing_source"] = timing_source
        timing["glass_stage_timings"] = stage_timings

    errors: list[str] = []
    if glass_time is None:
        errors.append("glass_time_seconds is required")
    if reference_time is None:
        errors.append("reference_time_seconds is required")
    if not glass_masters:
        errors.append("glass_master_paths must contain at least one path")
    if not reference_masters:
        errors.append("reference_master_paths must contain at least one path")
    if len(glass_masters) != len(reference_masters):
        errors.append("glass_master_paths and reference_master_paths must have the same length")
    for path in glass_masters + reference_masters:
        if path and not Path(path).exists():
            errors.append(f"missing master path: {path}")
    if errors:
        payload = {"status": "blocked", "errors": errors, "timing_template": str(timing_file)}
        write_json(out / "blackbox_finalize_summary.json", payload)
        return payload

    comparisons = []
    for index, (gp_master, ref_master) in enumerate(zip(glass_masters, reference_masters, strict=True), start=1):
        comparison = compare_fits(
            gp_master,
            ref_master,
            glass_time_seconds=float(glass_time),
            reference_time_seconds=float(reference_time),
            glass_label="GLASS",
            reference_label=reference_label,
        )
        stem = f"glass_vs_wbpp_{index:02d}"
        json_path = out / f"{stem}.json"
        html_path = out / f"{stem}.html"
        write_json(json_path, comparison)
        write_compare_report(html_path, comparison)
        comparisons.append(
            {
                "glass_master": gp_master,
                "reference_master": ref_master,
                "json": str(json_path),
                "html": str(html_path),
                "shape_match": comparison.get("shape_match"),
                "rms_diff": comparison.get("rms_diff"),
                "max_abs_diff": comparison.get("max_abs_diff"),
                "speedup_vs_reference": comparison.get("timing", {}).get("speedup_vs_reference"),
                "glass_faster": comparison.get("timing", {}).get("glass_faster"),
            }
        )

    speedups = [item["speedup_vs_reference"] for item in comparisons if item["speedup_vs_reference"] is not None]
    payload = {
        "status": "complete",
        "timing_template": str(timing_file),
        "glass_time_seconds": float(glass_time),
        "reference_time_seconds": float(reference_time),
        "reference_label": reference_label,
        "glass_timing_source": timing.get("glass_timing_source"),
        "comparison_count": len(comparisons),
        "speedup_vs_reference": speedups[0] if speedups else None,
        "speedup_observed": bool(speedups and speedups[0] > 1.0),
        "all_glass_faster": all(bool(item["glass_faster"]) for item in comparisons),
        "comparisons": comparisons,
    }
    write_json(out / "blackbox_finalize_summary.json", payload)
    return payload
