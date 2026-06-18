from __future__ import annotations

from pathlib import Path
from typing import Any

from glass.engine.rejection import RESIDENT_WINSORIZED_SIGMA_HARDENED_FRAME_LIMIT
from glass.io.json_io import write_json
from glass.models import now_iso
from glass.report.resident_winsorized_benchmark import build_resident_winsorized_benchmark


DEFAULT_FRAME_COUNTS = (8, 32, 128, 200)


def parse_frame_counts(value: str) -> list[int]:
    counts: list[int] = []
    for item in str(value).replace(";", ",").split(","):
        text = item.strip()
        if not text:
            continue
        counts.append(int(text))
    return counts


def _check(name: str, passed: bool, evidence: dict[str, Any], note: str = "") -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "evidence": evidence, "note": note}


def _comparison_summary(benchmark: dict[str, Any]) -> dict[str, Any]:
    comparisons = benchmark.get("comparisons") if isinstance(benchmark.get("comparisons"), dict) else {}
    hardened = comparisons.get("hardened_vs_cpu") if isinstance(comparisons.get("hardened_vs_cpu"), dict) else {}
    fast = comparisons.get("fast_approx_vs_cpu") if isinstance(comparisons.get("fast_approx_vs_cpu"), dict) else {}
    return {
        "hardened_vs_cpu": {
            "master": hardened.get("master"),
            "weight": hardened.get("weight"),
            "coverage": hardened.get("coverage"),
            "low_rejection": hardened.get("low_rejection"),
            "high_rejection": hardened.get("high_rejection"),
        },
        "fast_approx_vs_cpu": {"master": fast.get("master")},
    }


def _run_summary(benchmark: dict[str, Any], *, seed: int) -> dict[str, Any]:
    config = benchmark.get("config") if isinstance(benchmark.get("config"), dict) else {}
    return {
        "frame_count": config.get("frame_count"),
        "seed": int(seed),
        "status": benchmark.get("status"),
        "passed": benchmark.get("passed") is True,
        "timing_s": benchmark.get("timing_s"),
        "comparisons": _comparison_summary(benchmark),
        "failed_checks": benchmark.get("failed_checks", []),
        "checks": benchmark.get("checks", []),
        "cuda_hardened_timing": benchmark.get("cuda_hardened_timing"),
        "cuda_fast_approx_timing": benchmark.get("cuda_fast_approx_timing"),
    }


def build_resident_winsorized_frame_count_sweep(
    *,
    frame_counts: list[int] | tuple[int, ...] = DEFAULT_FRAME_COUNTS,
    height: int = 16,
    width: int = 16,
    seed_base: int = 268,
    low_sigma: float = 3.0,
    high_sigma: float = 3.0,
    tolerance_rms: float = 5.0e-5,
    tolerance_max_abs: float = 2.0e-4,
    required_frame_count: int = 200,
) -> dict[str, Any]:
    counts = [int(item) for item in frame_counts]
    if not counts:
        raise ValueError("frame_counts must not be empty")
    if height <= 0 or width <= 0:
        raise ValueError("height and width must be positive")
    bad_counts = [count for count in counts if count <= 0]
    if bad_counts:
        raise ValueError(f"frame_counts must be positive: {bad_counts}")
    over_limit = [count for count in counts if count > RESIDENT_WINSORIZED_SIGMA_HARDENED_FRAME_LIMIT]
    if over_limit:
        raise ValueError(
            "resident hardened winsorized sweep frame counts must be at most "
            f"{RESIDENT_WINSORIZED_SIGMA_HARDENED_FRAME_LIMIT}: {over_limit}"
        )

    runs: list[dict[str, Any]] = []
    for index, count in enumerate(counts):
        seed = int(seed_base) + index
        benchmark = build_resident_winsorized_benchmark(
            frame_count=count,
            height=height,
            width=width,
            seed=seed,
            low_sigma=low_sigma,
            high_sigma=high_sigma,
            tolerance_rms=tolerance_rms,
            tolerance_max_abs=tolerance_max_abs,
        )
        runs.append(_run_summary(benchmark, seed=seed))

    target_runs = [run for run in runs if run.get("frame_count") == int(required_frame_count)]
    all_runs_passed = all(run.get("passed") is True for run in runs)
    any_cuda_unavailable = any(run.get("status") == "cuda_unavailable" for run in runs)
    checks = [
        _check("frame_counts_present", bool(counts), {"frame_counts": counts}),
        _check(
            "all_frame_counts_within_hardened_limit",
            not over_limit,
            {"frame_counts": counts, "limit": RESIDENT_WINSORIZED_SIGMA_HARDENED_FRAME_LIMIT},
        ),
        _check("required_frame_count_present", bool(target_runs), {"required_frame_count": required_frame_count}),
        _check(
            "required_frame_count_passed",
            bool(target_runs) and target_runs[0].get("passed") is True,
            {"required_frame_count": required_frame_count, "target_runs": target_runs},
        ),
        _check("all_runs_passed", all_runs_passed, {"run_count": len(runs)}),
    ]
    failed = [item for item in checks if not item.get("passed")]
    status = "passed" if not failed else "failed"
    if failed and any_cuda_unavailable and not any(run.get("passed") for run in runs):
        status = "cuda_unavailable"
    return {
        "schema_version": 1,
        "artifact_type": "resident_winsorized_frame_count_sweep",
        "created_at": now_iso(),
        "status": status,
        "passed": not failed,
        "config": {
            "frame_counts": counts,
            "height": int(height),
            "width": int(width),
            "seed_base": int(seed_base),
            "low_sigma": float(low_sigma),
            "high_sigma": float(high_sigma),
            "tolerance_rms": float(tolerance_rms),
            "tolerance_max_abs": float(tolerance_max_abs),
            "required_frame_count": int(required_frame_count),
            "hardened_frame_limit": RESIDENT_WINSORIZED_SIGMA_HARDENED_FRAME_LIMIT,
        },
        "runs": runs,
        "checks": checks,
        "failed_checks": [str(item.get("name")) for item in failed],
        "summary": {
            "run_count": len(runs),
            "passed_run_count": sum(1 for run in runs if run.get("passed") is True),
            "required_frame_count_present": bool(target_runs),
            "required_frame_count_passed": bool(target_runs) and target_runs[0].get("passed") is True,
            "required_frame_count_timing_s": target_runs[0].get("timing_s") if target_runs else None,
            "max_hardened_master_rms": max(
                (
                    run.get("comparisons", {})
                    .get("hardened_vs_cpu", {})
                    .get("master", {})
                    .get("rms")
                    for run in runs
                    if isinstance(
                        run.get("comparisons", {})
                        .get("hardened_vs_cpu", {})
                        .get("master"),
                        dict,
                    )
                ),
                default=None,
            ),
        },
        "limitations": [
            "Synthetic frame-count sweep only; it does not replace the 200-light real-data benchmark.",
            "The 200-frame row validates prototype frame-count scale on a small image, not end-to-end I/O or registration.",
            "Timing is recorded for attribution but is not a hardware-independent performance contract.",
        ],
    }


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Resident Winsorized Frame-Count Sweep",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Passed: `{payload.get('passed')}`",
        f"- Frame counts: `{payload.get('config', {}).get('frame_counts')}`",
        f"- Shape: `{payload.get('config', {}).get('height')}x{payload.get('config', {}).get('width')}`",
        f"- Required frame count: `{payload.get('config', {}).get('required_frame_count')}`",
        "",
        "## Runs",
        "",
        "| frames | status | passed | CPU s | fast CUDA s | hardened CUDA s | hardened RMS | hardened max abs |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for run in payload.get("runs", []):
        timing = run.get("timing_s") if isinstance(run.get("timing_s"), dict) else {}
        master = (
            run.get("comparisons", {})
            .get("hardened_vs_cpu", {})
            .get("master", {})
            if isinstance(run.get("comparisons"), dict)
            else {}
        )
        lines.append(
            "| "
            f"{run.get('frame_count')} | {run.get('status')} | `{run.get('passed')}` | "
            f"{timing.get('cpu_baseline')} | {timing.get('cuda_fast_approx')} | "
            f"{timing.get('cuda_hardened')} | {master.get('rms')} | {master.get('max_abs')} |"
        )
    lines.extend(["", "## Failed Checks", ""])
    failed = payload.get("failed_checks", [])
    if failed:
        for name in failed:
            lines.append(f"- `{name}`")
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def write_resident_winsorized_frame_count_sweep(
    out: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(out, payload)
    if markdown is not None:
        Path(markdown).write_text(_markdown(payload), encoding="utf-8")
