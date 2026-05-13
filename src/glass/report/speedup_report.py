from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from glass.io.json_io import write_json


def _read_json_lenient(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def _first_output(integration: dict[str, Any]) -> dict[str, Any]:
    outputs = integration.get("outputs") or []
    return outputs[0] if outputs and isinstance(outputs[0], dict) else {}


def _weight_counts(integration: dict[str, Any]) -> dict[str, int]:
    weights = integration.get("frame_weights") or {}
    if not isinstance(weights, dict):
        return {"weighted_frame_count": 0, "zero_weight_frame_count": 0}
    active = 0
    zero = 0
    for value in weights.values():
        try:
            weight = float(value)
        except (TypeError, ValueError):
            continue
        if weight > 0.0:
            active += 1
        else:
            zero += 1
    return {"weighted_frame_count": active, "zero_weight_frame_count": zero}


def _load_glass_run(run: str | Path) -> dict[str, Any]:
    root = Path(run)
    timing = _read_json_lenient(root / "run_timing.json")
    integration_path = root / "integration_results.json"
    integration = _read_json_lenient(integration_path) if integration_path.exists() else {}
    resident_path = root / "resident_artifacts.json"
    resident = _read_json_lenient(resident_path) if resident_path.exists() else {}
    output = _first_output(integration)
    weight_counts = _weight_counts(integration)
    elapsed = timing.get("total_elapsed_s")
    if elapsed is None:
        elapsed = sum(float(stage.get("elapsed_s") or 0.0) for stage in timing.get("stages", []))
    return {
        "run": str(root),
        "elapsed_s": float(elapsed),
        "command": timing.get("command"),
        "backend": output.get("backend") or timing.get("backend"),
        "memory_mode": output.get("memory_mode") or timing.get("memory_mode"),
        "frame_count": output.get("frame_count"),
        **weight_counts,
        "master_path": output.get("master_path"),
        "weighting": integration.get("weighting") or output.get("weighting"),
        "rejection": integration.get("rejection") or output.get("rejection"),
        "resident_device": (resident.get("device") or {}).get("name"),
        "resident_estimated_peak_gib": (
            ((resident.get("artifacts") or [{}])[0].get("memory_estimate") or {}).get("estimated_peak_gib")
            if resident.get("artifacts")
            else None
        ),
    }


def _load_wbpp_result(path: str | Path) -> dict[str, Any]:
    payload = _read_json_lenient(path)
    return {
        "result_path": str(path),
        "elapsed_s": float(payload["elapsed_s"]),
        "dataset": payload.get("dataset"),
        "reported_wbpp_time": payload.get("reported_wbpp_time"),
        "output_dir": payload.get("output_dir"),
        "final_master_files": payload.get("final_master_files", []),
        "clean_room_note": payload.get("clean_room_note"),
    }


def _load_compare(path: str | Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    payload = _read_json_lenient(path)
    timing = payload.get("timing", {}) if isinstance(payload.get("timing"), dict) else {}
    region = payload.get("comparison_region", {}) if isinstance(payload.get("comparison_region"), dict) else {}
    return {
        "path": str(path),
        "shape_match": payload.get("shape_match"),
        "rms_diff": payload.get("rms_diff"),
        "abs_diff_p50": payload.get("abs_diff_p50"),
        "abs_diff_p90": payload.get("abs_diff_p90"),
        "abs_diff_p99": payload.get("abs_diff_p99"),
        "abs_diff_p999": payload.get("abs_diff_p999"),
        "relative_rms_diff": payload.get("relative_rms_diff"),
        "coverage_fraction": region.get("coverage_fraction"),
        "compared_pixels": region.get("compared_pixels"),
        "compare_speedup_vs_reference": timing.get("speedup_vs_reference"),
    }


def summarize_wbpp_speedup(
    glass_run: str | Path,
    wbpp_result: str | Path,
    *,
    compare_json: str | Path | None = None,
    min_speedup: float = 1.25,
) -> dict[str, Any]:
    gp = _load_glass_run(glass_run)
    wbpp = _load_wbpp_result(wbpp_result)
    speedup = wbpp["elapsed_s"] / gp["elapsed_s"] if gp["elapsed_s"] > 0 else None
    summary = {
        "schema_version": 1,
        "glass": gp,
        "wbpp_blackbox": wbpp,
        "speedup_vs_wbpp": speedup,
        "glass_faster": speedup is not None and speedup > 1.0,
        "meets_min_speedup": speedup is not None and speedup >= float(min_speedup),
        "min_speedup": float(min_speedup),
        "comparison": _load_compare(compare_json),
        "clean_room": {
            "status": "compliant",
            "note": (
                "This summary uses GLASS artifacts and user-generated PixInsight/WBPP black-box timing/output "
                "metadata only. It does not use PixInsight/WBPP implementation source."
            ),
        },
    }
    return summary


def write_speedup_markdown(path: str | Path, summary: dict[str, Any]) -> None:
    gp = summary["glass"]
    wbpp = summary["wbpp_blackbox"]
    comparison = summary.get("comparison") or {}
    lines = [
        "# GLASS vs WBPP Speedup Summary",
        "",
        f"- GLASS elapsed: {gp['elapsed_s']:.3f} s",
        f"- WBPP elapsed: {wbpp['elapsed_s']:.3f} s",
        f"- Speedup: {summary['speedup_vs_wbpp']:.3f}x",
        f"- Meets threshold ({summary['min_speedup']:.3f}x): {summary['meets_min_speedup']}",
        f"- GLASS backend: {gp.get('backend')}",
        f"- GLASS memory mode: {gp.get('memory_mode')}",
        f"- Planned frame count: {gp.get('frame_count')}",
        f"- Active weighted frames: {gp.get('weighted_frame_count')}",
        f"- Zero-weight frames: {gp.get('zero_weight_frame_count')}",
        f"- Resident device: {gp.get('resident_device')}",
        f"- WBPP dataset: {wbpp.get('dataset')}",
        "",
        "## Image Comparison",
        "",
        f"- Shape match: {comparison.get('shape_match')}",
        f"- RMS diff: {comparison.get('rms_diff')}",
        f"- abs diff p99: {comparison.get('abs_diff_p99')}",
        f"- coverage fraction: {comparison.get('coverage_fraction')}",
        "",
        "## Clean-room",
        "",
        f"- {summary['clean_room']['note']}",
        "",
    ]
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines), encoding="utf-8")


def write_speedup_summary(
    out_json: str | Path,
    summary: dict[str, Any],
    markdown: str | Path | None = None,
) -> None:
    write_json(out_json, summary)
    if markdown is not None:
        write_speedup_markdown(markdown, summary)
