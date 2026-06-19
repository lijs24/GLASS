from __future__ import annotations

from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np

from glass.io.fits_io import FitsImageReader
from glass.io.json_io import read_json, write_json
from glass.models import now_iso


def _read_json_object(path: str | Path) -> dict[str, Any]:
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"JSON artifact must be an object: {path}")
    return payload


def _read_fits(path: str | Path) -> np.ndarray:
    with FitsImageReader(path) as reader:
        return np.asarray(reader.read_full(), dtype=np.float32)


def _resolve_path(path_value: Any, run_root: Path) -> Path:
    if not path_value:
        raise FileNotFoundError(f"missing path value under {run_root}")
    raw = Path(str(path_value))
    candidates = [raw] if raw.is_absolute() else [run_root / raw, Path.cwd() / raw, raw]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _write_markdown(path: str | Path, text: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _calibrated_paths(cpu_run: Path) -> dict[str, Path]:
    payload = _read_json_object(cpu_run / "calibration_artifacts.json")
    rows = payload.get("calibrated_lights")
    if not isinstance(rows, list):
        return {}
    result: dict[str, Path] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        frame_id = str(row.get("frame_id") or "")
        if frame_id:
            result[frame_id] = _resolve_path(row.get("path"), cpu_run)
    return result


def _matrix_rows(path: Path) -> dict[str, dict[str, Any]]:
    payload = _read_json_object(path)
    rows = payload.get("registration_results")
    if not isinstance(rows, list):
        rows = payload.get("results")
    result: dict[str, dict[str, Any]] = {}
    if not isinstance(rows, list):
        return result
    for row in rows:
        if not isinstance(row, dict):
            continue
        frame_id = str(row.get("frame_id") or "")
        matrix = row.get("matrix")
        if frame_id and matrix is not None:
            result[frame_id] = row
    return result


def _frame_ids(
    *,
    cpu_run: Path,
    calibrated: dict[str, Path],
    cpu_rows: dict[str, dict[str, Any]],
    resident_rows: dict[str, dict[str, Any]],
    requested: list[str] | None,
    max_frames: int | None,
) -> list[str]:
    if requested:
        candidates = [str(item) for item in requested]
    else:
        candidates = sorted(set(calibrated) & set(cpu_rows) & set(resident_rows))
    selected: list[str] = []
    for frame_id in candidates:
        if frame_id not in calibrated or frame_id not in cpu_rows or frame_id not in resident_rows:
            continue
        if not (cpu_run / "registered_cache" / f"registered_{frame_id}.fits").exists():
            continue
        if not (cpu_run / "coverage_cache" / f"coverage_{frame_id}.fits").exists():
            continue
        selected.append(frame_id)
        if max_frames is not None and len(selected) >= int(max_frames):
            break
    return selected


def _matrix_array(row: dict[str, Any]) -> np.ndarray:
    matrix = np.asarray(row.get("matrix"), dtype=np.float64)
    if matrix.shape != (3, 3):
        raise ValueError(f"registration matrix must be 3x3, got {matrix.shape}")
    return matrix


def _is_translation(matrix: np.ndarray, atol: float = 1.0e-6) -> bool:
    return bool(
        np.allclose(matrix[:2, :2], np.eye(2), atol=atol)
        and np.allclose(matrix[2], np.asarray([0.0, 0.0, 1.0]), atol=atol)
    )


def _compare_region_mask(
    compare_json: str | Path | None,
    shape: tuple[int, int],
) -> tuple[np.ndarray, dict[str, Any]]:
    height, width = shape
    mask = np.ones((height, width), dtype=bool)
    summary: dict[str, Any] = {"evaluation_region": "full_frame", "pixels": int(mask.size)}
    if compare_json is None:
        return mask, summary
    compare = _read_json_object(compare_json)
    region = compare.get("comparison_region")
    if not isinstance(region, dict):
        return mask, summary
    border = int(region.get("ignore_border_px") or 0)
    if border > 0:
        mask[:] = False
        mask[border : height - border, border : width - border] = True
    summary = {
        "evaluation_region": "compare_region",
        "comparison_region": region,
        "pixels": int(np.count_nonzero(mask)),
    }
    return mask, summary


def _delta_stats(candidate: np.ndarray, reference: np.ndarray, mask: np.ndarray) -> dict[str, Any]:
    cand = np.asarray(candidate, dtype=np.float32)
    ref = np.asarray(reference, dtype=np.float32)
    if cand.shape != ref.shape:
        return {
            "shape_match": False,
            "candidate_shape": list(cand.shape),
            "reference_shape": list(ref.shape),
            "compared_pixels": 0,
            "passed": False,
        }
    finite = mask & np.isfinite(cand) & np.isfinite(ref)
    if not np.any(finite):
        return {
            "shape_match": True,
            "compared_pixels": 0,
            "rms": None,
            "mean_abs": None,
            "p99_abs": None,
            "max_abs": None,
            "signed_mean": None,
        }
    diff = cand[finite].astype(np.float64) - ref[finite].astype(np.float64)
    abs_diff = np.abs(diff)
    return {
        "shape_match": True,
        "compared_pixels": int(finite.sum()),
        "rms": float(np.sqrt(np.mean(diff * diff))),
        "mean_abs": float(np.mean(abs_diff)),
        "p99_abs": float(np.percentile(abs_diff, 99.0)),
        "max_abs": float(np.max(abs_diff)),
        "signed_mean": float(np.mean(diff)),
    }


def _coverage_stats(candidate: np.ndarray, reference: np.ndarray, region_mask: np.ndarray) -> dict[str, Any]:
    cand = np.rint(np.nan_to_num(candidate, nan=0.0)).astype(np.int16)
    ref = np.rint(np.nan_to_num(reference, nan=0.0)).astype(np.int16)
    diff = cand - ref
    scoped = diff[region_mask]
    return {
        "sample_delta": int(np.sum(scoped, dtype=np.int64)),
        "abs_sample_delta": int(np.sum(np.abs(scoped), dtype=np.int64)),
        "mismatch_pixels": int(np.count_nonzero(scoped)),
    }


def _matrix_delta(cpu_matrix: np.ndarray, resident_matrix: np.ndarray) -> dict[str, Any]:
    delta = resident_matrix - cpu_matrix
    tx = float(delta[0, 2])
    ty = float(delta[1, 2])
    return {
        "translation_dx": tx,
        "translation_dy": ty,
        "translation_delta_px": float(np.hypot(tx, ty)),
        "frobenius": float(np.linalg.norm(delta)),
        "cpu_tx": float(cpu_matrix[0, 2]),
        "cpu_ty": float(cpu_matrix[1, 2]),
        "resident_tx": float(resident_matrix[0, 2]),
        "resident_ty": float(resident_matrix[1, 2]),
    }


def _run_resident_warp(
    frame: np.ndarray,
    matrix: np.ndarray,
    *,
    interpolation: str,
) -> dict[str, Any]:
    try:
        import glass_cuda as cuda_module
    except Exception as exc:
        return {
            "status": "skipped_cuda_import_failed",
            "available": False,
            "error": f"{type(exc).__name__}: {exc}",
        }
    if not cuda_module.cuda_available():
        return {
            "status": "skipped_cuda_unavailable",
            "available": False,
            "native_import_error": cuda_module.native_import_error(),
        }
    if interpolation != "bilinear":
        return {
            "status": "skipped_interpolation_unsupported",
            "available": True,
            "interpolation": interpolation,
        }
    height, width = frame.shape
    stack = cuda_module.ResidentCalibratedStack(1, height, width)
    stack.upload_calibrated_frame(0, frame)
    start = perf_counter()
    if _is_translation(matrix):
        stack.apply_translation_bilinear_frame(0, float(matrix[0, 2]), float(matrix[1, 2]), np.nan)
        method = "apply_translation_bilinear_frame"
    else:
        stack.apply_matrix_bilinear_frame(0, matrix.astype(np.float32), np.nan)
        method = "apply_matrix_bilinear_frame"
    warped = stack.download_frame_tile(0, 0, 0, width, height)
    coverage = stack.warp_coverage_map()
    return {
        "status": "completed",
        "available": True,
        "method": method,
        "elapsed_s": float(perf_counter() - start),
        "warped": np.asarray(warped, dtype=np.float32),
        "coverage": np.asarray(coverage, dtype=np.float32),
    }


def _summarize_rows(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    values = [float(row[key]) for row in rows if row.get(key) is not None and np.isfinite(float(row[key]))]
    if not values:
        return {"count": 0, "max": None, "mean": None}
    return {"count": len(values), "max": max(values), "mean": float(np.mean(values))}


def build_resident_warp_input_audit(
    *,
    cpu_run: str | Path,
    resident_run: str | Path,
    compare_json: str | Path | None = None,
    frame_ids: list[str] | None = None,
    max_frames: int | None = 8,
    interpolation: str = "bilinear",
    cpu_matrix_rms_tolerance: float = 5.0e-4,
    resident_matrix_rms_tolerance: float = 0.1,
) -> dict[str, Any]:
    cpu_root = Path(cpu_run)
    resident_root = Path(resident_run)
    calibrated = _calibrated_paths(cpu_root)
    cpu_rows = _matrix_rows(cpu_root / "registration_results.json")
    resident_rows = _matrix_rows(resident_root / "registration_results.json")
    selected = _frame_ids(
        cpu_run=cpu_root,
        calibrated=calibrated,
        cpu_rows=cpu_rows,
        resident_rows=resident_rows,
        requested=frame_ids,
        max_frames=max_frames,
    )
    frame_results: list[dict[str, Any]] = []
    cuda_statuses: list[str] = []
    for frame_id in selected:
        calibrated_frame = _read_fits(calibrated[frame_id])
        registered = _read_fits(cpu_root / "registered_cache" / f"registered_{frame_id}.fits")
        cpu_coverage = _read_fits(cpu_root / "coverage_cache" / f"coverage_{frame_id}.fits")
        region_mask, region_summary = _compare_region_mask(compare_json, registered.shape)
        cpu_valid = region_mask & (np.rint(np.nan_to_num(cpu_coverage, nan=0.0)).astype(np.int16) > 0)
        cpu_matrix = _matrix_array(cpu_rows[frame_id])
        resident_matrix = _matrix_array(resident_rows[frame_id])
        matrix_delta = _matrix_delta(cpu_matrix, resident_matrix)
        source_rows: dict[str, Any] = {}
        for label, matrix in (("cpu_matrix", cpu_matrix), ("resident_matrix", resident_matrix)):
            warped = _run_resident_warp(calibrated_frame, matrix, interpolation=interpolation)
            cuda_statuses.append(str(warped.get("status")))
            if warped.get("status") == "completed":
                resident_coverage = warped["coverage"]
                valid = cpu_valid & (np.rint(np.nan_to_num(resident_coverage, nan=0.0)).astype(np.int16) > 0)
                source_rows[label] = {
                    "status": "completed",
                    "method": warped.get("method"),
                    "elapsed_s": warped.get("elapsed_s"),
                    "value_delta": _delta_stats(warped["warped"], registered, valid),
                    "coverage_delta": _coverage_stats(resident_coverage, cpu_coverage, region_mask),
                }
            else:
                source_rows[label] = {key: value for key, value in warped.items() if key not in {"warped", "coverage"}}
        frame_results.append(
            {
                "frame_id": frame_id,
                "region": region_summary,
                "matrix_delta": matrix_delta,
                "cpu_matrix": cpu_matrix.tolist(),
                "resident_matrix": resident_matrix.tolist(),
                **source_rows,
            }
        )

    cpu_matrix_rows = [
        row["cpu_matrix"]["value_delta"]
        for row in frame_results
        if (row.get("cpu_matrix") or {}).get("status") == "completed"
    ]
    resident_matrix_rows = [
        row["resident_matrix"]["value_delta"]
        for row in frame_results
        if (row.get("resident_matrix") or {}).get("status") == "completed"
    ]
    matrix_delta_rows = [row["matrix_delta"] for row in frame_results]
    cpu_matrix_max_rms = _summarize_rows(cpu_matrix_rows, "rms").get("max")
    resident_matrix_max_rms = _summarize_rows(resident_matrix_rows, "rms").get("max")
    matrix_translation_max = _summarize_rows(matrix_delta_rows, "translation_delta_px").get("max")
    cuda_completed = bool(frame_results) and all(status == "completed" for status in cuda_statuses)
    cpu_matrix_warp_passed = (
        cuda_completed
        and cpu_matrix_max_rms is not None
        and float(cpu_matrix_max_rms) <= float(cpu_matrix_rms_tolerance)
    )
    resident_matrix_warp_passed = (
        cuda_completed
        and resident_matrix_max_rms is not None
        and float(resident_matrix_max_rms) <= float(resident_matrix_rms_tolerance)
    )
    if not frame_results:
        recommendation = "fix_missing_cpu_or_resident_registration_inputs"
    elif not cuda_completed:
        recommendation = "run_warp_input_audit_when_cuda_is_available"
    elif not cpu_matrix_warp_passed:
        recommendation = "fix_resident_warp_kernel_or_cpu_warp_contract"
    elif not resident_matrix_warp_passed:
        recommendation = "target_resident_registration_matrix_precision"
    else:
        recommendation = "resident_warp_input_parity_ready"
    checks = [
        {
            "name": "frame_inputs_present",
            "passed": bool(frame_results),
            "evidence": {"selected_frame_count": len(frame_results)},
        },
        {
            "name": "cuda_warp_replay_completed",
            "passed": cuda_completed,
            "evidence": {"statuses": sorted(set(cuda_statuses))},
        },
        {
            "name": "cpu_matrix_resident_warp_matches_cpu_registered",
            "passed": cpu_matrix_warp_passed,
            "evidence": {
                "max_rms": cpu_matrix_max_rms,
                "tolerance": float(cpu_matrix_rms_tolerance),
            },
        },
        {
            "name": "resident_matrix_warp_delta_attributed",
            "passed": bool(cpu_matrix_warp_passed),
            "evidence": {
                "max_rms": resident_matrix_max_rms,
                "tolerance": float(resident_matrix_rms_tolerance),
                "resident_matrix_warp_parity_passed": resident_matrix_warp_passed,
                "matrix_translation_delta_px_max": matrix_translation_max,
            },
            "note": (
                "Resident-matrix warp parity is reported separately; this attribution check "
                "passes when CPU-matrix resident warp parity proves the kernel/input contract."
            ),
        },
    ]
    attribution_passed = bool(frame_results) and cuda_completed and cpu_matrix_warp_passed
    return {
        "schema_version": 1,
        "artifact_type": "resident_warp_input_audit",
        "created_at": now_iso(),
        "status": "passed" if attribution_passed else "attention_required",
        "passed": attribution_passed,
        "recommendation": recommendation,
        "cpu_run": str(cpu_root),
        "resident_run": str(resident_root),
        "compare_json": None if compare_json is None else str(compare_json),
        "interpolation": interpolation,
        "frame_count": len(frame_results),
        "thresholds": {
            "cpu_matrix_rms_tolerance": float(cpu_matrix_rms_tolerance),
            "resident_matrix_rms_tolerance": float(resident_matrix_rms_tolerance),
        },
        "summary": {
            "cpu_matrix_rms": _summarize_rows(cpu_matrix_rows, "rms"),
            "resident_matrix_rms": _summarize_rows(resident_matrix_rows, "rms"),
            "matrix_translation_delta_px": _summarize_rows(matrix_delta_rows, "translation_delta_px"),
            "resident_matrix_warp_parity_passed": resident_matrix_warp_passed,
            "attribution": recommendation,
        },
        "resident_matrix_warp_parity": {
            "passed": resident_matrix_warp_passed,
            "max_rms": resident_matrix_max_rms,
            "tolerance": float(resident_matrix_rms_tolerance),
            "matrix_translation_delta_px_max": matrix_translation_max,
        },
        "checks": checks,
        "failed_checks": [check["name"] for check in checks if not check["passed"]],
        "frames": frame_results,
    }


def _markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Resident Warp Input Audit",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Passed: `{payload.get('passed')}`",
        f"- Recommendation: `{payload.get('recommendation')}`",
        f"- Frame count: `{payload.get('frame_count')}`",
        f"- Interpolation: `{payload.get('interpolation')}`",
        "",
        "## Summary",
        "",
        f"- CPU-matrix resident warp RMS: `{summary.get('cpu_matrix_rms')}`",
        f"- Resident-matrix resident warp RMS: `{summary.get('resident_matrix_rms')}`",
        f"- Matrix translation delta px: `{summary.get('matrix_translation_delta_px')}`",
        f"- Resident matrix warp parity passed: `{summary.get('resident_matrix_warp_parity_passed')}`",
        "",
        "## Checks",
        "",
    ]
    for check in payload.get("checks", []):
        status = "PASS" if check.get("passed") else "FAIL"
        lines.append(f"- {status}: `{check.get('name')}` - {check.get('evidence')}")
    lines.extend(["", "## Worst Frames", ""])
    frames = sorted(
        payload.get("frames", []),
        key=lambda row: float(((row.get("resident_matrix") or {}).get("value_delta") or {}).get("rms") or 0.0),
        reverse=True,
    )
    lines.append("| frame | matrix delta px | cpu-matrix RMS | resident-matrix RMS |")
    lines.append("| --- | ---: | ---: | ---: |")
    for row in frames[:10]:
        cpu_rms = ((row.get("cpu_matrix") or {}).get("value_delta") or {}).get("rms")
        resident_rms = ((row.get("resident_matrix") or {}).get("value_delta") or {}).get("rms")
        lines.append(
            f"| `{row.get('frame_id')}` | "
            f"{(row.get('matrix_delta') or {}).get('translation_delta_px')} | "
            f"{cpu_rms} | {resident_rms} |"
        )
    lines.append("")
    return "\n".join(lines)


def write_resident_warp_input_audit(
    path: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(path, payload)
    if markdown is not None:
        _write_markdown(markdown, _markdown(payload))
