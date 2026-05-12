from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any


def _table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "<p>No rows.</p>"
    keys = list(rows[0].keys())
    head = "".join(f"<th>{escape(str(k))}</th>" for k in keys)
    body = []
    for row in rows:
        body.append("<tr>" + "".join(f"<td>{escape(str(row.get(k, '')))}</td>" for k in keys) + "</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def _resident_rows(resident: dict[str, Any] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in (resident or {}).get("artifacts", []):
        memory = item.get("memory_estimate", {})
        timing = item.get("timing_s", {})
        master_stats = item.get("master_stats", {})
        rows.append(
            {
                "filter": item.get("filter"),
                "frames": len(item.get("frame_ids", [])),
                "bias": master_stats.get("bias_count"),
                "dark": master_stats.get("dark_count"),
                "flat": master_stats.get("flat_count"),
                "resident_base_gib": round(float(memory.get("resident_base_gib") or 0.0), 3),
                "estimated_peak_gib": round(float(memory.get("estimated_peak_gib") or 0.0), 3),
                "light_calibrate_s": round(float(timing.get("light_read_upload_calibrate") or 0.0), 3),
                "resident_integrate_s": round(float(timing.get("resident_integration") or 0.0), 3),
                "write_s": round(float(timing.get("output_write") or 0.0), 3),
            }
        )
    return rows


def write_html_report(
    out_path: str | Path,
    manifest: dict[str, Any] | None = None,
    plan: dict[str, Any] | None = None,
    quality: dict[str, Any] | None = None,
    registration: dict[str, Any] | None = None,
    local_norm: dict[str, Any] | None = None,
    integration: dict[str, Any] | None = None,
    timing: dict[str, Any] | None = None,
    resident: dict[str, Any] | None = None,
    title: str = "GPWBPP Report",
) -> None:
    frames = (manifest or {}).get("frames", [])
    light_plans = (plan or {}).get("light_plans", [])
    frame_quality = (quality or {}).get("frame_quality", [])
    registration_results = (registration or {}).get("registration_results", [])
    local_norm_results = (local_norm or {}).get("local_norm_results", [])
    integration_outputs = (integration or {}).get("outputs", [])
    timing_rows = (timing or {}).get("stages", [])
    resident_summary = _resident_rows(resident)
    warnings = []
    warnings.extend((manifest or {}).get("warnings", []))
    warnings.extend((plan or {}).get("global_warnings", []))
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
  <p>Clean-room GPWBPP report. Input directories are not modified.</p>
  <h2>Input frame table</h2>
  {_table(frames)}
  <h2>Frame type distribution</h2>
  <pre>{escape(str((manifest or {}).get("summary", {})))}</pre>
  <h2>Calibration group matching</h2>
  {_table(light_plans)}
  <h2>Master frame statistics</h2>
  <p>Pending until calibration stages run.</p>
  <h2>Frame quality table</h2>
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
  {_table(timing_rows)}
  <h2>Warnings/errors</h2>
  <pre>{escape(str(warnings))}</pre>
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
