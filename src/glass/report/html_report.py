from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any


def _table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "<p>No rows.</p>"
    keys: list[str] = []
    for row in rows:
        for key in row.keys():
            if key not in keys:
                keys.append(key)
    head = "".join(f"<th>{escape(str(k))}</th>" for k in keys)
    body = []
    for row in rows:
        body.append("<tr>" + "".join(f"<td>{escape(str(row.get(k, '')))}</td>" for k in keys) + "</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def _warning_rows(
    manifest: dict[str, Any] | None,
    plan: dict[str, Any] | None,
    calibration: dict[str, Any] | None,
    registration: dict[str, Any] | None,
    local_norm: dict[str, Any] | None,
    integration: dict[str, Any] | None,
    timing: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in (manifest or {}).get("warnings", []):
        rows.append({"stage": "scan", "item": item.get("path") if isinstance(item, dict) else "", "warning": item})
    for item in (plan or {}).get("global_warnings", []):
        rows.append({"stage": "plan", "item": "", "warning": item})
    for item in (calibration or {}).get("calibrated_lights", []):
        for warning in item.get("warnings", []):
            rows.append({"stage": "calibration", "item": item.get("frame_id"), "warning": warning})
    for item in (registration or {}).get("registration_results", []):
        for warning in item.get("warnings", []):
            rows.append({"stage": "registration", "item": item.get("frame_id"), "warning": warning})
    for item in (local_norm or {}).get("local_norm_results", []):
        for warning in item.get("warnings", []):
            rows.append({"stage": "local_normalization", "item": item.get("frame_id"), "warning": warning})
    for warning in (integration or {}).get("warnings", []):
        rows.append({"stage": "integration", "item": "", "warning": warning})
    for item in (timing or {}).get("stages", []):
        if item.get("status") == "failed":
            rows.append({"stage": item.get("stage"), "item": "timing", "warning": item.get("error")})
    return rows


def _resident_rows(resident: dict[str, Any] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in (resident or {}).get("artifacts", []):
        memory = item.get("memory_estimate", {})
        timing = item.get("timing_s", {})
        master_stats = item.get("master_stats", {})
        registration = item.get("resident_registration", {})
        io_pipeline = item.get("resident_io_pipeline", {})
        local_norm = item.get("resident_local_normalization", {})
        weighting = item.get("resident_integration_weighting", {})
        rejection = item.get("integration_rejection", {})
        rows.append(
            {
                "filter": item.get("filter"),
                "frames": len(item.get("frame_ids", [])),
                "bias": master_stats.get("bias_count"),
                "dark": master_stats.get("dark_count"),
                "flat": master_stats.get("flat_count"),
                "registration": registration.get("mode"),
                "warp": registration.get("warp_interpolation"),
                "local_norm": local_norm.get("mode"),
                "weighting": weighting.get("mode"),
                "rejection": rejection.get("mode"),
                "resident_base_gib": round(float(memory.get("resident_base_gib") or 0.0), 3),
                "estimated_peak_gib": round(float(memory.get("estimated_peak_gib") or 0.0), 3),
                "light_calibrate_s": round(float(timing.get("light_read_upload_calibrate") or 0.0), 3),
                "prefetch_frames": io_pipeline.get("prefetch_frames", 0),
                "read_decode_s": round(float(timing.get("light_read_decode") or 0.0), 3),
                "read_decode_worker_s": round(float(timing.get("light_read_decode_worker") or 0.0), 3),
                "h2d_calibrate_store_s": round(float(timing.get("light_h2d_calibrate_store") or 0.0), 3),
                "registration_warp_s": round(float(timing.get("resident_registration_warp") or 0.0), 3),
                "registration_accounted_s": round(
                    float(timing.get("resident_registration_component_accounted") or 0.0), 3
                ),
                "registration_orchestration_s": round(
                    float(timing.get("resident_registration_orchestration") or 0.0), 3
                ),
                "light_loop_unaccounted_s": round(float(timing.get("light_loop_unaccounted") or 0.0), 3),
                "weighting_s": round(float(timing.get("resident_weighting") or 0.0), 3),
                "local_norm_s": round(float(timing.get("resident_local_normalization") or 0.0), 3),
                "resident_integrate_s": round(float(timing.get("resident_integration") or 0.0), 3),
                "write_s": round(float(timing.get("output_write") or 0.0), 3),
            }
        )
    return rows


def write_html_report(
    out_path: str | Path,
    manifest: dict[str, Any] | None = None,
    plan: dict[str, Any] | None = None,
    calibration: dict[str, Any] | None = None,
    quality: dict[str, Any] | None = None,
    registration: dict[str, Any] | None = None,
    local_norm: dict[str, Any] | None = None,
    integration: dict[str, Any] | None = None,
    timing: dict[str, Any] | None = None,
    resident: dict[str, Any] | None = None,
    title: str = "GLASS Report",
) -> None:
    frames = (manifest or {}).get("frames", [])
    light_plans = (plan or {}).get("light_plans", [])
    master_rows = []
    for group_id, master in (calibration or {}).get("masters", {}).items():
        stats = master.get("stats", {})
        master_rows.append(
            {
                "group_id": group_id,
                "type": master.get("type"),
                "filter": master.get("filter"),
                "mean": stats.get("mean"),
                "median": stats.get("median"),
                "std": stats.get("std"),
                "rejection": master.get("master_rejection"),
                "stack": master.get("tile_stack_mode"),
            }
        )
    calibration_policy = (calibration or {}).get("policy", {})
    input_cache_rows = (calibration or {}).get("input_cache", [])
    frame_quality = (quality or {}).get("frame_quality", [])
    registration_results = (registration or {}).get("registration_results", [])
    local_norm_results = (local_norm or {}).get("local_norm_results", [])
    integration_outputs = (integration or {}).get("outputs", [])
    integration_map_rows = [
        {
            "filter": item.get("filter"),
            "master": item.get("master_path"),
            "weight": item.get("weight_map_path"),
            "coverage": item.get("coverage_map_path"),
            "variance": item.get("variance_map_path"),
            "low_rejection": item.get("low_rejection_map_path"),
            "high_rejection": item.get("high_rejection_map_path"),
            "dq": item.get("dq_map_path"),
        }
        for item in integration_outputs
    ]
    dq_rows = []
    for source_name, rows in [
        ("registration/warp", registration_results),
        ("local_normalization", local_norm_results),
        ("integration", integration_outputs),
    ]:
        for row in rows:
            if row.get("dq_summary") or row.get("dq_mask_path") or row.get("dq_map_path"):
                dq_rows.append(
                    {
                        "stage": source_name,
                        "frame_or_filter": row.get("frame_id") or row.get("filter"),
                        "summary": row.get("dq_summary", {}),
                        "path": row.get("dq_mask_path") or row.get("dq_map_path"),
                    }
                )
    timing_rows = (timing or {}).get("stages", [])
    timing_overview = [
        {
            "command": (timing or {}).get("command"),
            "backend": (timing or {}).get("backend"),
            "memory_mode": (timing or {}).get("memory_mode", "tile"),
            "total_elapsed_s": (timing or {}).get("total_elapsed_s"),
            "stage_count": len(timing_rows),
        }
    ]
    stage_coverage_rows = [
        {"stage": "scan", "rows": len(frames), "artifact": "manifest.json" if manifest else "missing"},
        {"stage": "plan", "rows": len(light_plans), "artifact": "processing_plan.json" if plan else "missing"},
        {
            "stage": "calibration",
            "rows": len((calibration or {}).get("calibrated_lights", [])),
            "artifact": "calibration_artifacts.json" if calibration else "missing",
        },
        {
            "stage": "quality",
            "rows": len(frame_quality),
            "artifact": "frame_quality.json" if quality else "missing",
        },
        {
            "stage": "registration",
            "rows": len(registration_results),
            "artifact": "registration_results.json" if registration else "missing",
        },
        {
            "stage": "local_normalization",
            "rows": len(local_norm_results),
            "artifact": "local_norm_results.json" if local_norm else "missing",
        },
        {
            "stage": "integration",
            "rows": len(integration_outputs),
            "artifact": "integration_results.json" if integration else "missing",
        },
    ]
    resident_summary = _resident_rows(resident)
    warning_rows = _warning_rows(manifest, plan, calibration, registration, local_norm, integration, timing)
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{escape(title)}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #202124; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; font-size: 0.9rem; }}
    th, td {{ border: 1px solid #d0d7de; padding: 0.35rem 0.5rem; text-align: left; }}
    th {{ background: #f6f8fa; }}
    code {{ background: #f6f8fa; padding: 0.1rem 0.25rem; }}
  </style>
</head>
<body>
  <h1>{escape(title)}</h1>
  <h2>Project summary</h2>
  <p>Clean-room GLASS report. Input directories are not modified.</p>
  <h2>Stage coverage summary</h2>
  {_table(stage_coverage_rows)}
  <h2>Input frame table</h2>
  {_table(frames)}
  <h2>Frame type distribution</h2>
  <pre>{escape(str((manifest or {}).get("summary", {})))}</pre>
  <h2>Calibration group matching</h2>
  {_table(light_plans)}
  <h2>Master frame statistics</h2>
  <pre>{escape(str(calibration_policy))}</pre>
  {_table(master_rows)}
  <h2>XISF input cache</h2>
  <p>XISF sources are streamed into run-local FITS cache files before calibration.</p>
  {_table(input_cache_rows)}
  <h2>Frame quality table</h2>
  <p>Detector: <code>{escape(str((quality or {}).get("star_detector", "pending")))}</code>.
  Weight source: <code>{escape(str((quality or {}).get("weight_source", "pending")))}</code>.</p>
  {_table(frame_quality)}
  <p>Reference frame: <code>{escape(str((quality or {}).get("reference_frame_id", "pending")))}</code></p>
  <h2>Registration table</h2>
  {_table(registration_results)}
  <h2>Local normalization summary</h2>
  <p>Enabled: <code>{escape(str((local_norm or {}).get("enabled", "pending")))}</code>.
  Reference frame: <code>{escape(str((local_norm or {}).get("reference_frame_id", "pending")))}</code>.</p>
  {_table(local_norm_results)}
  <h2>Integration summary</h2>
  <p>Combine: <code>{escape(str((integration or {}).get("combine", "pending")))}</code>.
  Weighting: <code>{escape(str((integration or {}).get("weighting", "pending")))}</code>.
  Rejection: <code>{escape(str((integration or {}).get("rejection", "pending")))}</code>.</p>
  {_table(integration_outputs)}
  <h2>Integration output maps</h2>
  {_table(integration_map_rows)}
  <h2>DQ/mask summary</h2>
  {_table(dq_rows)}
  <h2>Resident CUDA summary</h2>
  <p>Backend: <code>{escape(str((resident or {}).get("backend", "not used")))}</code>.
  Device: <code>{escape(str(((resident or {}).get("device") or {}).get("name", "pending")))}</code>.</p>
  {_table(resident_summary)}
  <h2>Output artifacts</h2>
  <p>See adjacent JSON files in the run directory.</p>
  <h2>Memory usage summary</h2>
  <p>Heavy stages use explicit memory modes. Tile/slab streaming is the bounded
  fallback; resident mode is allowed only when the planned hot set fits within
  the configured device memory budget.</p>
  <h2>Runtime summary</h2>
  <p>Total elapsed seconds: <code>{escape(str((timing or {}).get("total_elapsed_s", "pending")))}</code>.</p>
  {_table(timing_overview)}
  {_table(timing_rows)}
  <h2>Warnings/errors</h2>
  {_table(warning_rows)}
  <h2>PixInsight comparison if available</h2>
  <p>No comparison artifact attached.</p>
  <h2>Known differences from WBPP</h2>
  <p>This is an independent implementation and does not claim numerical equivalence.</p>
  <h2>Clean-room compliance note</h2>
  <p>No official WBPP/PJSR source code is used as implementation input.</p>
</body>
</html>
"""
    target = Path(out_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding="utf-8")
