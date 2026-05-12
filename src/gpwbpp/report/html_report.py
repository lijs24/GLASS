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


def write_html_report(
    out_path: str | Path,
    manifest: dict[str, Any] | None = None,
    plan: dict[str, Any] | None = None,
    quality: dict[str, Any] | None = None,
    registration: dict[str, Any] | None = None,
    local_norm: dict[str, Any] | None = None,
    integration: dict[str, Any] | None = None,
    title: str = "GPWBPP Report",
) -> None:
    frames = (manifest or {}).get("frames", [])
    light_plans = (plan or {}).get("light_plans", [])
    frame_quality = (quality or {}).get("frame_quality", [])
    registration_results = (registration or {}).get("registration_results", [])
    local_norm_results = (local_norm or {}).get("local_norm_results", [])
    integration_outputs = (integration or {}).get("outputs", [])
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
  <h2>Output artifacts</h2>
  <p>See adjacent JSON files in the run directory.</p>
  <h2>Memory usage summary</h2>
  <p>Tile/slab streaming is the required execution model for heavy stages.</p>
  <h2>Runtime summary</h2>
  <p>Runtime timings are added by later gates.</p>
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
