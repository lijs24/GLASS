from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from gpwbpp.io.json_io import read_json, write_json
from gpwbpp.report.compare_report import compare_fits, write_compare_report


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


def _write_manual(path: Path, rows: list[dict[str, Any]], gpwbpp_masters: list[str]) -> None:
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
            "7. Run the generated `compare_command.ps1` after replacing the placeholder reference path/time.",
            "",
            "## GPWBPP Masters",
            "",
        ]
    )
    if gpwbpp_masters:
        lines.extend(f"- `{value}`" for value in gpwbpp_masters)
    else:
        lines.append("- No GPWBPP integration master was found in the supplied run directory.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def create_blackbox_package(
    manifest_path: str | Path,
    plan_path: str | Path | None,
    out_dir: str | Path,
    gpwbpp_run: str | Path | None = None,
    gpwbpp_time_seconds: float | None = None,
    reference_label: str = "PixInsight WBPP",
) -> dict[str, Any]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    manifest = read_json(manifest_path)
    plan = read_json(plan_path) if plan_path is not None and Path(plan_path).exists() else None
    run = Path(gpwbpp_run) if gpwbpp_run is not None else None
    rows = _frame_rows(manifest)
    masters = _master_paths(run)
    csv_path = out / "input_frames.csv"
    manual_path = out / "wbpp_manual_run.md"
    timing_path = out / "timing_template.json"
    compare_path = out / "compare_command.ps1"
    _write_csv(csv_path, rows)
    _write_manual(manual_path, rows, masters)

    timing = {
        "manifest_path": str(manifest_path),
        "plan_path": None if plan_path is None else str(plan_path),
        "gpwbpp_run": None if run is None else str(run),
        "gpwbpp_time_seconds": gpwbpp_time_seconds,
        "gpwbpp_master_paths": masters,
        "reference_label": reference_label,
        "reference_time_seconds": None,
        "reference_master_paths": [],
        "plan_executable": None if plan is None else bool(plan.get("executable")),
        "frame_count": len(rows),
    }
    write_json(timing_path, timing)
    gp_master = masters[0] if masters else "<GPWBPP_MASTER_FITS>"
    compare_path.write_text(
        "\n".join(
            [
                "$ErrorActionPreference='Stop'",
                "$gpwbppMaster = " + repr(gp_master),
                "$referenceMaster = '<WBPP_MASTER_FITS>'",
                "$gpwbppSeconds = "
                + ("<GPWBPP_SECONDS>" if gpwbpp_time_seconds is None else repr(float(gpwbpp_time_seconds))),
                "$referenceSeconds = '<WBPP_SECONDS>'",
                ".\\.venv\\Scripts\\gpwbpp compare --gpwbpp $gpwbppMaster --reference $referenceMaster --out "
                + repr(str(out / "gpwbpp_vs_wbpp.html"))
                + " --gpwbpp-time-seconds $gpwbppSeconds --reference-time-seconds $referenceSeconds "
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
        "gpwbpp_master_count": len(masters),
    }
    write_json(out / "blackbox_package.json", payload)
    return payload


def finalize_blackbox_package(timing_path: str | Path, out_dir: str | Path | None = None) -> dict[str, Any]:
    timing_file = Path(timing_path)
    timing = read_json(timing_file)
    out = Path(out_dir) if out_dir is not None else timing_file.parent
    out.mkdir(parents=True, exist_ok=True)

    gpwbpp_time = timing.get("gpwbpp_time_seconds")
    reference_time = timing.get("reference_time_seconds")
    gpwbpp_masters = [str(value) for value in timing.get("gpwbpp_master_paths", [])]
    reference_masters = [str(value) for value in timing.get("reference_master_paths", [])]
    reference_label = str(timing.get("reference_label") or "PixInsight WBPP")

    errors: list[str] = []
    if gpwbpp_time is None:
        errors.append("gpwbpp_time_seconds is required")
    if reference_time is None:
        errors.append("reference_time_seconds is required")
    if not gpwbpp_masters:
        errors.append("gpwbpp_master_paths must contain at least one path")
    if not reference_masters:
        errors.append("reference_master_paths must contain at least one path")
    if len(gpwbpp_masters) != len(reference_masters):
        errors.append("gpwbpp_master_paths and reference_master_paths must have the same length")
    for path in gpwbpp_masters + reference_masters:
        if path and not Path(path).exists():
            errors.append(f"missing master path: {path}")
    if errors:
        payload = {"status": "blocked", "errors": errors, "timing_template": str(timing_file)}
        write_json(out / "blackbox_finalize_summary.json", payload)
        return payload

    comparisons = []
    for index, (gp_master, ref_master) in enumerate(zip(gpwbpp_masters, reference_masters, strict=True), start=1):
        comparison = compare_fits(
            gp_master,
            ref_master,
            gpwbpp_time_seconds=float(gpwbpp_time),
            reference_time_seconds=float(reference_time),
            gpwbpp_label="GPWBPP",
            reference_label=reference_label,
        )
        stem = f"gpwbpp_vs_wbpp_{index:02d}"
        json_path = out / f"{stem}.json"
        html_path = out / f"{stem}.html"
        write_json(json_path, comparison)
        write_compare_report(html_path, comparison)
        comparisons.append(
            {
                "gpwbpp_master": gp_master,
                "reference_master": ref_master,
                "json": str(json_path),
                "html": str(html_path),
                "shape_match": comparison.get("shape_match"),
                "rms_diff": comparison.get("rms_diff"),
                "max_abs_diff": comparison.get("max_abs_diff"),
                "speedup_vs_reference": comparison.get("timing", {}).get("speedup_vs_reference"),
                "gpwbpp_faster": comparison.get("timing", {}).get("gpwbpp_faster"),
            }
        )

    speedups = [item["speedup_vs_reference"] for item in comparisons if item["speedup_vs_reference"] is not None]
    payload = {
        "status": "complete",
        "timing_template": str(timing_file),
        "gpwbpp_time_seconds": float(gpwbpp_time),
        "reference_time_seconds": float(reference_time),
        "reference_label": reference_label,
        "comparison_count": len(comparisons),
        "speedup_vs_reference": speedups[0] if speedups else None,
        "all_gpwbpp_faster": all(bool(item["gpwbpp_faster"]) for item in comparisons),
        "comparisons": comparisons,
    }
    write_json(out / "blackbox_finalize_summary.json", payload)
    return payload
