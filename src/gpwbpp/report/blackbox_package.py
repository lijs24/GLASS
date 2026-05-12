from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from gpwbpp.io.json_io import read_json, write_json


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
