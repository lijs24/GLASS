from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from glass.cpu.integration import weighted_integrate_stack
from glass.io.fits_io import FitsImageReader
from glass.io.json_io import read_json, write_json
from glass.models import now_iso
from glass.report.resident_rejection_sample_audit import (
    _comparison_region_mask,
    _first_output,
    _resolve_path,
    build_resident_rejection_sample_audit,
)


_COUNT_MAPS = ("coverage", "low_rejection", "high_rejection")


def _read_json_object(path: str | Path) -> dict[str, Any]:
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"JSON artifact must be an object: {path}")
    return payload


def _read_fits(path: Path) -> np.ndarray:
    with FitsImageReader(path) as reader:
        return np.asarray(reader.read_full(), dtype=np.float32)


def _write_markdown(path: str | Path, text: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _frame_ids(cpu_run: Path, frame_weights: dict[str, Any]) -> list[str]:
    registered = cpu_run / "registered_cache"
    available = {
        path.stem.removeprefix("registered_"): path
        for path in registered.glob("registered_*.fits")
    }
    if frame_weights:
        ordered = [str(frame_id) for frame_id in frame_weights.keys()]
        selected = [frame_id for frame_id in ordered if frame_id in available]
        if selected:
            return selected
    return sorted(available)


def _load_cpu_registered_stack(
    cpu_run: Path,
    frame_ids: list[str],
) -> tuple[np.ndarray, np.ndarray]:
    frames: list[np.ndarray] = []
    coverage: list[np.ndarray] = []
    for frame_id in frame_ids:
        registered_path = cpu_run / "registered_cache" / f"registered_{frame_id}.fits"
        coverage_path = cpu_run / "coverage_cache" / f"coverage_{frame_id}.fits"
        if not registered_path.exists():
            raise FileNotFoundError(f"missing registered frame: {registered_path}")
        if not coverage_path.exists():
            raise FileNotFoundError(f"missing coverage frame: {coverage_path}")
        registered = _read_fits(registered_path)
        cov = _read_fits(coverage_path)
        if registered.shape != cov.shape:
            raise ValueError(f"registered and coverage shapes differ for {frame_id}")
        frames.append(np.where(cov > 0.5, registered, np.nan).astype(np.float32))
        coverage.append(cov.astype(np.float32))
    if not frames:
        raise ValueError(f"no registered frames found in {cpu_run / 'registered_cache'}")
    return np.stack(frames, axis=0), np.stack(coverage, axis=0)


def _output_paths(run_root: Path) -> dict[str, Path]:
    output = _first_output(run_root)
    keys = {
        "master": "master_path",
        "coverage": "coverage_map_path",
        "low_rejection": "low_rejection_map_path",
        "high_rejection": "high_rejection_map_path",
    }
    paths: dict[str, Path] = {}
    for name, key in keys.items():
        resolved = _resolve_path(output.get(key), run_root)
        if resolved is None or not resolved.exists():
            raise FileNotFoundError(f"missing {name} output map for {run_root}: {resolved}")
        paths[name] = resolved
    return paths


def _delta_stats(
    candidate: np.ndarray,
    reference: np.ndarray,
    *,
    tolerance: float = 0.0,
    mask: np.ndarray | None = None,
    round_counts: bool = False,
) -> dict[str, Any]:
    cand = np.asarray(candidate, dtype=np.float32)
    ref = np.asarray(reference, dtype=np.float32)
    if cand.shape != ref.shape:
        return {
            "shape_match": False,
            "candidate_shape": list(cand.shape),
            "reference_shape": list(ref.shape),
            "passed": False,
        }
    if round_counts:
        cand = np.rint(np.nan_to_num(cand, nan=0.0)).astype(np.int64)
        ref = np.rint(np.nan_to_num(ref, nan=0.0)).astype(np.int64)
    diff = cand - ref
    if mask is not None:
        diff = diff[mask]
    finite = np.isfinite(diff)
    finite_diff = diff[finite]
    if finite_diff.size == 0:
        return {
            "shape_match": True,
            "pixels": 0,
            "finite_pixels": 0,
            "max_abs_delta": None,
            "abs_delta_sum": 0,
            "signed_delta_sum": 0,
            "mismatch_pixels": 0,
            "passed": True,
        }
    abs_diff = np.abs(finite_diff)
    mismatch = abs_diff > float(tolerance)
    return {
        "shape_match": True,
        "pixels": int(diff.size),
        "finite_pixels": int(finite_diff.size),
        "max_abs_delta": float(np.max(abs_diff)),
        "abs_delta_sum": float(np.sum(abs_diff, dtype=np.float64)),
        "signed_delta_sum": float(np.sum(finite_diff, dtype=np.float64)),
        "mismatch_pixels": int(np.count_nonzero(mismatch)),
        "passed": bool(not np.any(mismatch)),
    }


def _map_delta_set(
    candidate: dict[str, np.ndarray],
    reference: dict[str, np.ndarray],
    *,
    master_tolerance: float,
    mask: np.ndarray | None = None,
) -> dict[str, Any]:
    result = {
        "master": _delta_stats(
            candidate["master"],
            reference["master"],
            tolerance=master_tolerance,
            mask=mask,
        )
    }
    for name in _COUNT_MAPS:
        result[name] = _delta_stats(
            candidate[name],
            reference[name],
            tolerance=0.0,
            mask=mask,
            round_counts=True,
        )
    result["passed"] = all(row.get("passed") is True for row in result.values() if isinstance(row, dict))
    return result


def _comparison_mask(
    *,
    compare_json: str | Path | None,
    resident_coverage: np.ndarray,
    evaluation_region: str,
) -> tuple[np.ndarray | None, dict[str, Any]]:
    if evaluation_region == "full_frame":
        return None, {"evaluation_region": "full_frame"}
    if evaluation_region != "compare_region":
        raise ValueError("evaluation_region must be full_frame or compare_region")
    if compare_json is None:
        raise ValueError("compare_json is required when evaluation_region=compare_region")
    compare = _read_json_object(compare_json)
    region = compare.get("comparison_region") if isinstance(compare.get("comparison_region"), dict) else {}
    if not region:
        raise ValueError("compare_json does not contain comparison_region")
    height, width = resident_coverage.shape
    mask = _comparison_region_mask(
        y0=0,
        y1=height,
        x0=0,
        x1=width,
        height=height,
        width=width,
        compare_region=region,
        resident_coverage=np.rint(np.nan_to_num(resident_coverage, nan=0.0)).astype(np.int64),
    )
    return mask, {
        "evaluation_region": "compare_region",
        "comparison_region": region,
        "evaluated_pixels": int(np.count_nonzero(mask)),
    }


def _run_cuda_exact_input(
    stack: np.ndarray,
    weights: np.ndarray,
    *,
    low_sigma: float,
    high_sigma: float,
) -> dict[str, Any]:
    try:
        import glass_cuda as cuda_module
    except Exception as exc:
        return {
            "available": False,
            "ran": False,
            "status": "skipped_cuda_import_failed",
            "error": f"{type(exc).__name__}: {exc}",
        }
    if not cuda_module.cuda_available():
        return {
            "available": False,
            "ran": False,
            "status": "skipped_cuda_unavailable",
            "native_import_error": cuda_module.native_import_error(),
        }
    if not hasattr(cuda_module, "ResidentCalibratedStack"):
        return {
            "available": False,
            "ran": False,
            "status": "skipped_resident_stack_unavailable",
        }
    frame_count, height, width = stack.shape
    if frame_count > 256:
        return {
            "available": True,
            "ran": False,
            "status": "skipped_frame_limit",
            "frame_count": int(frame_count),
            "frame_limit": 256,
        }
    resident = cuda_module.ResidentCalibratedStack(frame_count, height, width)
    for index in range(frame_count):
        resident.upload_calibrated_frame(index, stack[index])
    master, weight_map, coverage, low, high, timing = resident.integrate_hardened_winsorized_sigma_timed(
        weights,
        low_sigma,
        high_sigma,
    )
    return {
        "available": True,
        "ran": True,
        "status": "completed",
        "timing_s": timing,
        "maps": {
            "master": master,
            "weight": weight_map,
            "coverage": coverage,
            "low_rejection": low,
            "high_rejection": high,
        },
    }


def _recommendation(
    *,
    cpu_replay_passed: bool,
    cuda_exact_status: str,
    cuda_exact_passed: bool | None,
    resident_same_pre_abs_delta: int,
    resident_pre_abs_delta: int,
    max_same_pre_rejection_abs_delta: int,
) -> str:
    if not cpu_replay_passed:
        return "fix_cpu_registered_replay_or_run_artifacts"
    if cuda_exact_status != "completed":
        return "run_cuda_exact_input_audit_when_cuda_is_available"
    if cuda_exact_passed is False:
        return "fix_resident_hardened_winsorized_kernel_semantics"
    if resident_pre_abs_delta != 0:
        return "target_resident_geometric_coverage_or_transform_parity"
    if resident_same_pre_abs_delta > max_same_pre_rejection_abs_delta:
        return "target_resident_registration_warp_input_parity"
    return "resident_rejection_input_semantics_ready"


def build_resident_rejection_input_audit(
    *,
    cpu_run: str | Path,
    resident_run: str | Path,
    compare_json: str | Path | None = None,
    evaluation_region: str = "compare_region",
    run_cuda_exact_input: bool = True,
    master_tolerance: float = 5.0e-4,
    max_same_pre_rejection_abs_delta: int = 16,
) -> dict[str, Any]:
    cpu_root = Path(cpu_run)
    resident_root = Path(resident_run)
    cpu_results = _read_json_object(cpu_root / "integration_results.json")
    frame_weights_raw = cpu_results.get("frame_weights")
    frame_weights = frame_weights_raw if isinstance(frame_weights_raw, dict) else {}
    frame_ids = _frame_ids(cpu_root, frame_weights)
    weights = np.asarray([float(frame_weights.get(frame_id, 1.0)) for frame_id in frame_ids], dtype=np.float32)
    low_sigma = float(cpu_results.get("low_sigma", 3.0) or 3.0)
    high_sigma = float(cpu_results.get("high_sigma", 3.0) or 3.0)

    registered_stack, coverage_stack = _load_cpu_registered_stack(cpu_root, frame_ids)
    cpu_replay = weighted_integrate_stack(
        registered_stack,
        coverage=coverage_stack,
        weights=weights,
        rejection="winsorized_sigma",
        low_sigma=low_sigma,
        high_sigma=high_sigma,
    )
    cpu_replay_maps = {
        "master": cpu_replay[0],
        "weight": cpu_replay[1],
        "coverage": cpu_replay[2],
        "low_rejection": cpu_replay[3],
        "high_rejection": cpu_replay[4],
    }
    cpu_paths = _output_paths(cpu_root)
    resident_paths = _output_paths(resident_root)
    cpu_output_maps = {name: _read_fits(path) for name, path in cpu_paths.items()}
    resident_output_maps = {name: _read_fits(path) for name, path in resident_paths.items()}
    mask, region_summary = _comparison_mask(
        compare_json=compare_json,
        resident_coverage=resident_output_maps["coverage"],
        evaluation_region=evaluation_region,
    )

    cpu_replay_delta = _map_delta_set(
        cpu_replay_maps,
        cpu_output_maps,
        master_tolerance=master_tolerance,
        mask=None,
    )
    cuda_exact: dict[str, Any]
    if run_cuda_exact_input:
        cuda_exact = _run_cuda_exact_input(
            registered_stack,
            weights,
            low_sigma=low_sigma,
            high_sigma=high_sigma,
        )
        if cuda_exact.get("ran"):
            cuda_exact_delta = _map_delta_set(
                cuda_exact["maps"],
                cpu_output_maps,
                master_tolerance=master_tolerance,
                mask=None,
            )
            cuda_exact = {
                key: value for key, value in cuda_exact.items() if key != "maps"
            }
            cuda_exact["delta_vs_cpu_output"] = cuda_exact_delta
            cuda_exact["passed"] = bool(cuda_exact_delta.get("passed"))
        else:
            cuda_exact["passed"] = None
    else:
        cuda_exact = {
            "available": None,
            "ran": False,
            "status": "skipped_by_request",
            "passed": None,
        }

    resident_output_delta = _map_delta_set(
        resident_output_maps,
        cpu_output_maps,
        master_tolerance=master_tolerance,
        mask=mask,
    )
    sample_audit = build_resident_rejection_sample_audit(
        cpu_run=cpu_root,
        resident_run=resident_root,
        compare_json=compare_json,
        max_same_pre_rejection_abs_delta=max_same_pre_rejection_abs_delta,
        evaluation_region=evaluation_region,
    )
    evaluation_deltas = sample_audit.get("evaluation_deltas") or sample_audit.get("deltas") or {}
    resident_same_pre_abs_delta = int(
        evaluation_deltas.get("same_pre_rejection_abs_rejected_sample_delta") or 0
    )
    resident_pre_abs_delta = int(evaluation_deltas.get("abs_pre_rejection_sample_delta") or 0)
    resident_output_parity_passed = (
        resident_pre_abs_delta == 0
        and resident_same_pre_abs_delta <= int(max_same_pre_rejection_abs_delta)
    )
    recommendation = _recommendation(
        cpu_replay_passed=bool(cpu_replay_delta.get("passed")),
        cuda_exact_status=str(cuda_exact.get("status")),
        cuda_exact_passed=cuda_exact.get("passed"),
        resident_same_pre_abs_delta=resident_same_pre_abs_delta,
        resident_pre_abs_delta=resident_pre_abs_delta,
        max_same_pre_rejection_abs_delta=int(max_same_pre_rejection_abs_delta),
    )
    attribution_passed = bool(cpu_replay_delta.get("passed")) and cuda_exact.get("passed") is True
    attribution_status = (
        "resident_output_parity_ready"
        if resident_output_parity_passed
        else "resident_registration_warp_input_delta"
        if attribution_passed and resident_pre_abs_delta == 0
        else "resident_geometric_coverage_or_transform_delta"
        if attribution_passed
        else "unattributed"
    )
    sample_raw_recommendation = sample_audit.get("recommendation")
    sample_attributed_recommendation = (
        recommendation if attribution_status != "unattributed" else sample_raw_recommendation
    )
    checks = [
        {
            "name": "cpu_registered_replay_matches_cpu_outputs",
            "passed": bool(cpu_replay_delta.get("passed")),
            "evidence": cpu_replay_delta,
            "note": "Replays CPU registered_cache and coverage_cache through the CPU winsorized baseline.",
        },
        {
            "name": "cuda_exact_input_matches_cpu_outputs",
            "passed": cuda_exact.get("passed") is True,
            "evidence": {
                "status": cuda_exact.get("status"),
                "available": cuda_exact.get("available"),
                "ran": cuda_exact.get("ran"),
                "delta_vs_cpu_output": cuda_exact.get("delta_vs_cpu_output"),
            },
            "note": "Uploads the same CPU registered stack to resident CUDA and runs hardened winsorized sigma.",
        },
        {
            "name": "resident_rejection_delta_attributed",
            "passed": attribution_status != "unattributed",
            "evidence": {
                "same_pre_rejection_abs_rejected_sample_delta": resident_same_pre_abs_delta,
                "max_same_pre_rejection_abs_delta": int(max_same_pre_rejection_abs_delta),
                "resident_output_parity_passed": resident_output_parity_passed,
                "attribution_status": attribution_status,
                "recommendation": recommendation,
                "evaluation_region": evaluation_region,
            },
            "note": (
                "The audit passes when exact-input CUDA matches CPU and any remaining resident "
                "output delta is attributed to the upstream resident registration/warp input path."
            ),
        },
    ]
    passed = all(check["passed"] for check in checks)
    return {
        "schema_version": 1,
        "artifact_type": "resident_rejection_input_audit",
        "created_at": now_iso(),
        "status": "passed" if passed else "attention_required",
        "passed": bool(passed),
        "recommendation": recommendation,
        "cpu_run": str(cpu_root),
        "resident_run": str(resident_root),
        "compare_json": None if compare_json is None else str(compare_json),
        "frame_ids": frame_ids,
        "frame_count": int(len(frame_ids)),
        "shape": {
            "frames": int(registered_stack.shape[0]),
            "height": int(registered_stack.shape[1]),
            "width": int(registered_stack.shape[2]),
        },
        "low_sigma": low_sigma,
        "high_sigma": high_sigma,
        "thresholds": {
            "master_tolerance": float(master_tolerance),
            "max_same_pre_rejection_abs_delta": int(max_same_pre_rejection_abs_delta),
        },
        "evaluation": region_summary,
        "cpu_replay": {
            "source": "cpu_registered_cache_plus_coverage_cache",
            "delta_vs_cpu_output": cpu_replay_delta,
        },
        "cuda_exact_input": cuda_exact,
        "resident_output_delta_vs_cpu": resident_output_delta,
        "resident_output_parity": {
            "passed": resident_output_parity_passed,
            "same_pre_rejection_abs_rejected_sample_delta": resident_same_pre_abs_delta,
            "max_same_pre_rejection_abs_delta": int(max_same_pre_rejection_abs_delta),
            "pre_rejection_abs_delta": resident_pre_abs_delta,
            "attribution_status": attribution_status,
        },
        "resident_rejection_sample_audit": {
            "status": sample_audit.get("status"),
            "passed": sample_audit.get("passed"),
            "recommendation": sample_attributed_recommendation,
            "raw_recommendation": sample_raw_recommendation,
            "evaluation_region": sample_audit.get("evaluation_region"),
            "evaluation_deltas": evaluation_deltas,
            "failed_checks": sample_audit.get("failed_checks"),
        },
        "checks": checks,
        "failed_checks": [check["name"] for check in checks if not check["passed"]],
    }


def _markdown(payload: dict[str, Any]) -> str:
    sample = payload.get("resident_rejection_sample_audit") or {}
    exact = payload.get("cuda_exact_input") or {}
    resident_delta = payload.get("resident_output_delta_vs_cpu") or {}
    resident_parity = payload.get("resident_output_parity") or {}
    lines = [
        "# Resident Rejection Input Audit",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Passed: `{payload.get('passed')}`",
        f"- Recommendation: `{payload.get('recommendation')}`",
        f"- Frame count: `{payload.get('frame_count')}`",
        f"- Evaluation region: `{(payload.get('evaluation') or {}).get('evaluation_region')}`",
        "",
        "## Exact Input",
        "",
        f"- CUDA exact-input status: `{exact.get('status')}`",
        f"- CUDA exact-input passed: `{exact.get('passed')}`",
        f"- CPU replay passed: `{((payload.get('cpu_replay') or {}).get('delta_vs_cpu_output') or {}).get('passed')}`",
        "",
        "## Resident Output Delta",
        "",
        f"- Coverage abs delta: `{(resident_delta.get('coverage') or {}).get('abs_delta_sum')}`",
        f"- Low rejection abs delta: `{(resident_delta.get('low_rejection') or {}).get('abs_delta_sum')}`",
        f"- High rejection abs delta: `{(resident_delta.get('high_rejection') or {}).get('abs_delta_sum')}`",
        f"- Resident output parity passed: `{resident_parity.get('passed')}`",
        f"- Attribution status: `{resident_parity.get('attribution_status')}`",
        "",
        "## Rejection Sample Audit",
        "",
        f"- Status: `{sample.get('status')}`",
        f"- Recommendation: `{sample.get('recommendation')}`",
        f"- Raw sample recommendation: `{sample.get('raw_recommendation')}`",
        f"- Evaluation deltas: `{sample.get('evaluation_deltas')}`",
        "",
        "## Checks",
        "",
    ]
    for check in payload.get("checks", []):
        status = "PASS" if check.get("passed") else "FAIL"
        lines.append(f"- {status}: `{check.get('name')}`")
    lines.append("")
    return "\n".join(lines)


def write_resident_rejection_input_audit(
    path: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(path, payload)
    if markdown is not None:
        _write_markdown(markdown, _markdown(payload))
