from __future__ import annotations

from contextlib import ExitStack
from pathlib import Path
from typing import Any

import numpy as np

from glass.engine.contracts import DQFlag
from glass.io.fits_io import FitsImageReader
from glass.io.json_io import read_json, write_json
from glass.models import now_iso


_MAP_KEYS = {
    "coverage": "coverage_map_path",
    "low_rejection": "low_rejection_map_path",
    "high_rejection": "high_rejection_map_path",
    "dq": "dq_map_path",
}


def _read_json_object(path: str | Path) -> dict[str, Any]:
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"JSON artifact must be an object: {path}")
    return payload


def _optional_json_object(path: str | Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    target = Path(path)
    return _read_json_object(target) if target.exists() else {}


def _first_output(run_root: Path) -> dict[str, Any]:
    path = run_root / "integration_results.json"
    if not path.exists():
        return {}
    payload = _read_json_object(path)
    outputs = payload.get("outputs") if isinstance(payload.get("outputs"), list) else []
    return outputs[0] if outputs and isinstance(outputs[0], dict) else {}


def _resolve_path(path_value: Any, run_root: Path) -> Path | None:
    if not path_value:
        return None
    raw = Path(str(path_value))
    candidates = [raw] if raw.is_absolute() else [run_root / raw, Path.cwd() / raw, raw]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _run_maps(run_root: Path) -> dict[str, Any]:
    output = _first_output(run_root)
    maps: dict[str, dict[str, Any]] = {}
    for name, key in _MAP_KEYS.items():
        path = _resolve_path(output.get(key), run_root)
        maps[name] = {
            "path_key": key,
            "path": str(path) if path is not None else None,
            "exists": bool(path and path.exists()),
        }
    return {
        "path": str(run_root),
        "exists": run_root.exists(),
        "integration_results_path": str(run_root / "integration_results.json"),
        "integration_results_exists": (run_root / "integration_results.json").exists(),
        "backend": output.get("backend"),
        "frame_count": output.get("frame_count"),
        "filter": output.get("filter"),
        "dq_provenance_summary": output.get("dq_provenance_summary")
        if isinstance(output.get("dq_provenance_summary"), dict)
        else {},
        "maps": maps,
    }


def _count_tile(tile: np.ndarray) -> np.ndarray:
    values = np.asarray(tile, dtype=np.float32)
    values = np.where(np.isfinite(values), values, 0.0)
    return np.rint(values).astype(np.int64, copy=False)


def _dq_tile(tile: np.ndarray) -> np.ndarray:
    values = np.asarray(tile, dtype=np.float32)
    values = np.where(np.isfinite(values), values, 0.0)
    return np.rint(values).astype(np.uint32, copy=False)


def _count_flag(values: np.ndarray, flag: DQFlag) -> int:
    if flag == DQFlag.VALID:
        return int(np.count_nonzero(values == 0))
    return int(np.count_nonzero((values & np.uint32(int(flag))) != 0))


def _new_run_summary() -> dict[str, Any]:
    return {
        "coverage_sample_sum": 0,
        "coverage_positive_pixels": 0,
        "coverage_zero_pixels": 0,
        "coverage_min": None,
        "coverage_max": None,
        "low_rejected_samples": 0,
        "low_rejected_pixels": 0,
        "high_rejected_samples": 0,
        "high_rejected_pixels": 0,
        "rejected_samples": 0,
        "rejected_pixels": 0,
        "pre_rejection_sample_sum": 0,
        "dq_valid_pixels": 0,
        "dq_no_data_pixels": 0,
        "dq_warp_edge_pixels": 0,
        "dq_low_rejected_pixels": 0,
        "dq_high_rejected_pixels": 0,
    }


def _update_min_max(summary: dict[str, Any], values: np.ndarray) -> None:
    if values.size == 0:
        return
    min_value = int(np.min(values))
    max_value = int(np.max(values))
    summary["coverage_min"] = (
        min_value if summary["coverage_min"] is None else min(summary["coverage_min"], min_value)
    )
    summary["coverage_max"] = (
        max_value if summary["coverage_max"] is None else max(summary["coverage_max"], max_value)
    )


def _add_run_summary(
    summary: dict[str, Any],
    coverage: np.ndarray,
    low: np.ndarray,
    high: np.ndarray,
    dq: np.ndarray,
) -> None:
    rejected = low + high
    summary["coverage_sample_sum"] += int(np.sum(coverage, dtype=np.int64))
    summary["coverage_positive_pixels"] += int(np.count_nonzero(coverage > 0))
    summary["coverage_zero_pixels"] += int(np.count_nonzero(coverage <= 0))
    _update_min_max(summary, coverage)
    summary["low_rejected_samples"] += int(np.sum(low, dtype=np.int64))
    summary["low_rejected_pixels"] += int(np.count_nonzero(low > 0))
    summary["high_rejected_samples"] += int(np.sum(high, dtype=np.int64))
    summary["high_rejected_pixels"] += int(np.count_nonzero(high > 0))
    summary["rejected_samples"] += int(np.sum(rejected, dtype=np.int64))
    summary["rejected_pixels"] += int(np.count_nonzero(rejected > 0))
    summary["pre_rejection_sample_sum"] += int(np.sum(coverage + rejected, dtype=np.int64))
    summary["dq_valid_pixels"] += _count_flag(dq, DQFlag.VALID)
    summary["dq_no_data_pixels"] += _count_flag(dq, DQFlag.NO_DATA)
    summary["dq_warp_edge_pixels"] += _count_flag(dq, DQFlag.WARP_EDGE)
    summary["dq_low_rejected_pixels"] += _count_flag(dq, DQFlag.LOW_REJECTED)
    summary["dq_high_rejected_pixels"] += _count_flag(dq, DQFlag.HIGH_REJECTED)


def _new_delta_summary() -> dict[str, Any]:
    return {
        "coverage_sample_delta": 0,
        "abs_coverage_sample_delta": 0,
        "coverage_mismatch_pixels": 0,
        "low_rejected_sample_delta": 0,
        "abs_low_rejected_sample_delta": 0,
        "low_rejection_mismatch_pixels": 0,
        "high_rejected_sample_delta": 0,
        "abs_high_rejected_sample_delta": 0,
        "high_rejection_mismatch_pixels": 0,
        "rejected_sample_delta": 0,
        "abs_rejected_sample_delta": 0,
        "rejection_mismatch_pixels": 0,
        "pre_rejection_sample_delta": 0,
        "abs_pre_rejection_sample_delta": 0,
        "pre_rejection_mismatch_pixels": 0,
        "same_pre_rejection_abs_rejected_sample_delta": 0,
        "same_pre_rejection_rejection_mismatch_pixels": 0,
        "same_post_coverage_abs_rejected_sample_delta": 0,
        "same_post_coverage_rejection_mismatch_pixels": 0,
        "rejection_mismatch_with_pre_rejection_mismatch_pixels": 0,
        "rejection_mismatch_with_coverage_mismatch_pixels": 0,
        "resident_warp_edge_rejection_mismatch_pixels": 0,
        "cpu_warp_edge_rejection_mismatch_pixels": 0,
        "dq_mismatch_pixels": 0,
    }


def _add_delta_summary(
    summary: dict[str, Any],
    *,
    coverage_delta: np.ndarray,
    low_delta: np.ndarray,
    high_delta: np.ndarray,
    rejected_delta: np.ndarray,
    pre_rejection_delta: np.ndarray,
    cpu_dq: np.ndarray,
    resident_dq: np.ndarray,
    mask: np.ndarray | None = None,
) -> None:
    if mask is not None:
        coverage_delta = coverage_delta[mask]
        low_delta = low_delta[mask]
        high_delta = high_delta[mask]
        rejected_delta = rejected_delta[mask]
        pre_rejection_delta = pre_rejection_delta[mask]
        cpu_dq = cpu_dq[mask]
        resident_dq = resident_dq[mask]
    if rejected_delta.size == 0:
        return

    coverage_mismatch = coverage_delta != 0
    low_mismatch = low_delta != 0
    high_mismatch = high_delta != 0
    rejection_mismatch = rejected_delta != 0
    pre_rejection_mismatch = pre_rejection_delta != 0
    resident_warp = (resident_dq & np.uint32(int(DQFlag.WARP_EDGE))) != 0
    cpu_warp = (cpu_dq & np.uint32(int(DQFlag.WARP_EDGE))) != 0

    summary["coverage_sample_delta"] += int(np.sum(coverage_delta, dtype=np.int64))
    summary["abs_coverage_sample_delta"] += int(np.sum(np.abs(coverage_delta), dtype=np.int64))
    summary["coverage_mismatch_pixels"] += int(np.count_nonzero(coverage_mismatch))
    summary["low_rejected_sample_delta"] += int(np.sum(low_delta, dtype=np.int64))
    summary["abs_low_rejected_sample_delta"] += int(np.sum(np.abs(low_delta), dtype=np.int64))
    summary["low_rejection_mismatch_pixels"] += int(np.count_nonzero(low_mismatch))
    summary["high_rejected_sample_delta"] += int(np.sum(high_delta, dtype=np.int64))
    summary["abs_high_rejected_sample_delta"] += int(np.sum(np.abs(high_delta), dtype=np.int64))
    summary["high_rejection_mismatch_pixels"] += int(np.count_nonzero(high_mismatch))
    summary["rejected_sample_delta"] += int(np.sum(rejected_delta, dtype=np.int64))
    summary["abs_rejected_sample_delta"] += int(np.sum(np.abs(rejected_delta), dtype=np.int64))
    summary["rejection_mismatch_pixels"] += int(np.count_nonzero(rejection_mismatch))
    summary["pre_rejection_sample_delta"] += int(np.sum(pre_rejection_delta, dtype=np.int64))
    summary["abs_pre_rejection_sample_delta"] += int(
        np.sum(np.abs(pre_rejection_delta), dtype=np.int64)
    )
    summary["pre_rejection_mismatch_pixels"] += int(np.count_nonzero(pre_rejection_mismatch))
    same_pre = rejection_mismatch & ~pre_rejection_mismatch
    same_post = rejection_mismatch & ~coverage_mismatch
    summary["same_pre_rejection_abs_rejected_sample_delta"] += int(
        np.sum(np.abs(rejected_delta[same_pre]), dtype=np.int64)
    )
    summary["same_pre_rejection_rejection_mismatch_pixels"] += int(np.count_nonzero(same_pre))
    summary["same_post_coverage_abs_rejected_sample_delta"] += int(
        np.sum(np.abs(rejected_delta[same_post]), dtype=np.int64)
    )
    summary["same_post_coverage_rejection_mismatch_pixels"] += int(np.count_nonzero(same_post))
    summary["rejection_mismatch_with_pre_rejection_mismatch_pixels"] += int(
        np.count_nonzero(rejection_mismatch & pre_rejection_mismatch)
    )
    summary["rejection_mismatch_with_coverage_mismatch_pixels"] += int(
        np.count_nonzero(rejection_mismatch & coverage_mismatch)
    )
    summary["resident_warp_edge_rejection_mismatch_pixels"] += int(
        np.count_nonzero(rejection_mismatch & resident_warp)
    )
    summary["cpu_warp_edge_rejection_mismatch_pixels"] += int(
        np.count_nonzero(rejection_mismatch & cpu_warp)
    )
    summary["dq_mismatch_pixels"] += int(np.count_nonzero(cpu_dq != resident_dq))


def _comparison_region_mask(
    *,
    y0: int,
    y1: int,
    x0: int,
    x1: int,
    height: int,
    width: int,
    compare_region: dict[str, Any],
    resident_coverage: np.ndarray,
) -> np.ndarray:
    border = int(compare_region.get("ignore_border_px") or 0)
    min_coverage = compare_region.get("min_coverage")
    rows = np.arange(y0, y1)
    cols = np.arange(x0, x1)
    mask = (
        (rows[:, None] >= border)
        & (rows[:, None] < height - border)
        & (cols[None, :] >= border)
        & (cols[None, :] < width - border)
    )
    if min_coverage is not None:
        mask &= resident_coverage >= int(round(float(min_coverage)))
    return mask


def _check(name: str, passed: bool, evidence: dict[str, Any], note: str = "") -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "evidence": evidence, "note": note}


def _map_paths_present(run: dict[str, Any]) -> bool:
    return all((row.get("exists") is True) for row in (run.get("maps") or {}).values())


def _shape_summary(paths: dict[str, Path]) -> dict[str, Any]:
    shapes: dict[str, tuple[int, int]] = {}
    for name, path in paths.items():
        with FitsImageReader(path) as reader:
            shapes[name] = tuple(int(v) for v in reader.shape)
    unique_shapes = sorted(set(shapes.values()))
    return {
        "shapes": {name: list(shape) for name, shape in shapes.items()},
        "shape_match": len(unique_shapes) == 1,
        "shape": list(unique_shapes[0]) if len(unique_shapes) == 1 else None,
    }


def _recommendation(
    *,
    maps_present: bool,
    shape_match: bool,
    deltas: dict[str, Any],
    thresholds: dict[str, Any],
) -> str:
    if not maps_present:
        return "fix_missing_cpu_or_resident_maps"
    if not shape_match:
        return "fix_cpu_resident_map_shape_mismatch"
    rejected_delta = abs(int(deltas.get("rejected_sample_delta") or 0))
    pre_delta = abs(int(deltas.get("pre_rejection_sample_delta") or 0))
    same_pre_abs = int(deltas.get("same_pre_rejection_abs_rejected_sample_delta") or 0)
    if rejected_delta <= int(thresholds["max_rejected_sample_delta"]) and pre_delta <= int(
        thresholds["max_pre_rejection_sample_delta"]
    ):
        return "rejection_sample_accounting_ready"
    if pre_delta > int(thresholds["max_pre_rejection_sample_delta"]):
        return "fix_resident_geometric_coverage_or_transform"
    if same_pre_abs > int(thresholds["max_same_pre_rejection_abs_delta"]):
        return "fix_resident_winsorized_rejection_semantics"
    return "inspect_rejection_hotspot_tiles"


def _evaluation_deltas(
    *,
    deltas: dict[str, Any],
    region_deltas: dict[str, dict[str, Any]],
    evaluation_region: str,
) -> dict[str, Any]:
    if evaluation_region == "full_frame":
        return deltas
    if evaluation_region == "compare_region":
        return region_deltas.get("inside_compare_region", {})
    raise ValueError("evaluation_region must be full_frame or compare_region")


def _top_tiles(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    return sorted(
        rows,
        key=lambda row: (
            int(row.get("abs_rejected_sample_delta") or 0),
            int(row.get("abs_pre_rejection_sample_delta") or 0),
            int(row.get("rejection_mismatch_pixels") or 0),
        ),
        reverse=True,
    )[: max(0, int(limit))]


def build_resident_rejection_sample_audit(
    *,
    cpu_run: str | Path,
    resident_run: str | Path,
    compare_json: str | Path | None = None,
    tile_size: int = 2048,
    top_tiles: int = 10,
    max_rejected_sample_delta: int = 64,
    max_pre_rejection_sample_delta: int = 0,
    max_same_pre_rejection_abs_delta: int = 16,
    evaluation_region: str = "full_frame",
) -> dict[str, Any]:
    if evaluation_region not in {"full_frame", "compare_region"}:
        raise ValueError("evaluation_region must be full_frame or compare_region")
    cpu_root = Path(cpu_run)
    resident_root = Path(resident_run)
    cpu = _run_maps(cpu_root)
    resident = _run_maps(resident_root)
    compare = _optional_json_object(compare_json)
    compare_region = (
        compare.get("comparison_region") if isinstance(compare.get("comparison_region"), dict) else {}
    )
    thresholds = {
        "max_rejected_sample_delta": int(max_rejected_sample_delta),
        "max_pre_rejection_sample_delta": int(max_pre_rejection_sample_delta),
        "max_same_pre_rejection_abs_delta": int(max_same_pre_rejection_abs_delta),
    }

    maps_present = _map_paths_present(cpu) and _map_paths_present(resident)
    checks: list[dict[str, Any]] = [
        _check("cpu_maps_present", _map_paths_present(cpu), {"maps": cpu["maps"]}),
        _check("resident_maps_present", _map_paths_present(resident), {"maps": resident["maps"]}),
    ]
    if not maps_present:
        recommendation = _recommendation(
            maps_present=False,
            shape_match=False,
            deltas={},
            thresholds=thresholds,
        )
        checks.append(_check("map_shapes_match", False, {}, "Skipped because maps are missing."))
        return {
            "schema_version": 1,
            "artifact_type": "resident_rejection_sample_audit",
            "created_at": now_iso(),
            "status": "failed",
            "passed": False,
            "recommendation": recommendation,
            "cpu": cpu,
            "resident": resident,
            "compare_json": str(compare_json) if compare_json else None,
            "thresholds": thresholds,
            "evaluation_region": evaluation_region,
            "checks": checks,
            "failed_checks": [item["name"] for item in checks if not item["passed"]],
        }

    cpu_paths = {name: Path(row["path"]) for name, row in cpu["maps"].items()}
    resident_paths = {name: Path(row["path"]) for name, row in resident["maps"].items()}
    all_paths = {f"cpu_{name}": path for name, path in cpu_paths.items()}
    all_paths.update({f"resident_{name}": path for name, path in resident_paths.items()})
    shapes = _shape_summary(all_paths)
    shape_match = bool(shapes["shape_match"])
    checks.append(_check("map_shapes_match", shape_match, shapes))
    if not shape_match:
        recommendation = _recommendation(
            maps_present=True,
            shape_match=False,
            deltas={},
            thresholds=thresholds,
        )
        return {
            "schema_version": 1,
            "artifact_type": "resident_rejection_sample_audit",
            "created_at": now_iso(),
            "status": "failed",
            "passed": False,
            "recommendation": recommendation,
            "cpu": cpu,
            "resident": resident,
            "compare_json": str(compare_json) if compare_json else None,
            "shape_summary": shapes,
            "thresholds": thresholds,
            "evaluation_region": evaluation_region,
            "checks": checks,
            "failed_checks": [item["name"] for item in checks if not item["passed"]],
        }

    height, width = (int(value) for value in shapes["shape"])
    step = max(1, int(tile_size))
    cpu_summary = _new_run_summary()
    resident_summary = _new_run_summary()
    deltas = _new_delta_summary()
    region_deltas = {
        "inside_compare_region": _new_delta_summary(),
        "outside_compare_region": _new_delta_summary(),
    }
    tile_rows: list[dict[str, Any]] = []

    with ExitStack() as stack:
        readers = {
            f"cpu_{name}": stack.enter_context(FitsImageReader(path))
            for name, path in cpu_paths.items()
        }
        readers.update(
            {
                f"resident_{name}": stack.enter_context(FitsImageReader(path))
                for name, path in resident_paths.items()
            }
        )
        for y0 in range(0, height, step):
            y1 = min(height, y0 + step)
            for x0 in range(0, width, step):
                x1 = min(width, x0 + step)
                c_cov = _count_tile(readers["cpu_coverage"].read_tile(y0, y1, x0, x1))
                r_cov = _count_tile(readers["resident_coverage"].read_tile(y0, y1, x0, x1))
                c_low = _count_tile(readers["cpu_low_rejection"].read_tile(y0, y1, x0, x1))
                r_low = _count_tile(
                    readers["resident_low_rejection"].read_tile(y0, y1, x0, x1)
                )
                c_high = _count_tile(readers["cpu_high_rejection"].read_tile(y0, y1, x0, x1))
                r_high = _count_tile(
                    readers["resident_high_rejection"].read_tile(y0, y1, x0, x1)
                )
                c_dq = _dq_tile(readers["cpu_dq"].read_tile(y0, y1, x0, x1))
                r_dq = _dq_tile(readers["resident_dq"].read_tile(y0, y1, x0, x1))

                _add_run_summary(cpu_summary, c_cov, c_low, c_high, c_dq)
                _add_run_summary(resident_summary, r_cov, r_low, r_high, r_dq)

                coverage_delta = r_cov - c_cov
                low_delta = r_low - c_low
                high_delta = r_high - c_high
                rejected_delta = low_delta + high_delta
                pre_rejection_delta = (r_cov + r_low + r_high) - (c_cov + c_low + c_high)
                _add_delta_summary(
                    deltas,
                    coverage_delta=coverage_delta,
                    low_delta=low_delta,
                    high_delta=high_delta,
                    rejected_delta=rejected_delta,
                    pre_rejection_delta=pre_rejection_delta,
                    cpu_dq=c_dq,
                    resident_dq=r_dq,
                )

                inside = _comparison_region_mask(
                    y0=y0,
                    y1=y1,
                    x0=x0,
                    x1=x1,
                    height=height,
                    width=width,
                    compare_region=compare_region,
                    resident_coverage=r_cov,
                )
                _add_delta_summary(
                    region_deltas["inside_compare_region"],
                    coverage_delta=coverage_delta,
                    low_delta=low_delta,
                    high_delta=high_delta,
                    rejected_delta=rejected_delta,
                    pre_rejection_delta=pre_rejection_delta,
                    cpu_dq=c_dq,
                    resident_dq=r_dq,
                    mask=inside,
                )
                _add_delta_summary(
                    region_deltas["outside_compare_region"],
                    coverage_delta=coverage_delta,
                    low_delta=low_delta,
                    high_delta=high_delta,
                    rejected_delta=rejected_delta,
                    pre_rejection_delta=pre_rejection_delta,
                    cpu_dq=c_dq,
                    resident_dq=r_dq,
                    mask=~inside,
                )

                tile_rejected_abs = int(np.sum(np.abs(rejected_delta), dtype=np.int64))
                tile_pre_abs = int(np.sum(np.abs(pre_rejection_delta), dtype=np.int64))
                tile_rejection_mismatch = int(np.count_nonzero(rejected_delta != 0))
                if tile_rejected_abs or tile_pre_abs or tile_rejection_mismatch:
                    tile_rows.append(
                        {
                            "y0": int(y0),
                            "y1": int(y1),
                            "x0": int(x0),
                            "x1": int(x1),
                            "pixels": int((y1 - y0) * (x1 - x0)),
                            "coverage_sample_delta": int(
                                np.sum(coverage_delta, dtype=np.int64)
                            ),
                            "abs_coverage_sample_delta": int(
                                np.sum(np.abs(coverage_delta), dtype=np.int64)
                            ),
                            "rejected_sample_delta": int(
                                np.sum(rejected_delta, dtype=np.int64)
                            ),
                            "abs_rejected_sample_delta": tile_rejected_abs,
                            "pre_rejection_sample_delta": int(
                                np.sum(pre_rejection_delta, dtype=np.int64)
                            ),
                            "abs_pre_rejection_sample_delta": tile_pre_abs,
                            "rejection_mismatch_pixels": tile_rejection_mismatch,
                            "coverage_mismatch_pixels": int(
                                np.count_nonzero(coverage_delta != 0)
                            ),
                        }
                    )

    eval_deltas = _evaluation_deltas(
        deltas=deltas,
        region_deltas=region_deltas,
        evaluation_region=evaluation_region,
    )
    checks.extend(
        [
            _check(
                "rejected_sample_delta_within_limit",
                abs(int(eval_deltas["rejected_sample_delta"])) <= int(max_rejected_sample_delta),
                {
                    "delta": eval_deltas["rejected_sample_delta"],
                    "max_abs_delta": int(max_rejected_sample_delta),
                    "evaluation_region": evaluation_region,
                },
            ),
            _check(
                "pre_rejection_sample_delta_within_limit",
                abs(int(eval_deltas["pre_rejection_sample_delta"]))
                <= int(max_pre_rejection_sample_delta),
                {
                    "delta": eval_deltas["pre_rejection_sample_delta"],
                    "max_abs_delta": int(max_pre_rejection_sample_delta),
                    "evaluation_region": evaluation_region,
                    "note": (
                        "pre-rejection sample delta compares coverage+low+high maps and "
                        "identifies geometric/warp/DQ input-sample drift before rejection."
                    ),
                },
            ),
            _check(
                "same_pre_rejection_semantic_delta_within_limit",
                int(eval_deltas["same_pre_rejection_abs_rejected_sample_delta"])
                <= int(max_same_pre_rejection_abs_delta),
                {
                    "abs_delta": eval_deltas["same_pre_rejection_abs_rejected_sample_delta"],
                    "max_abs_delta": int(max_same_pre_rejection_abs_delta),
                    "evaluation_region": evaluation_region,
                },
            ),
        ]
    )
    recommendation = _recommendation(
        maps_present=True,
        shape_match=True,
        deltas=eval_deltas,
        thresholds=thresholds,
    )
    passed = all(item["passed"] for item in checks)
    return {
        "schema_version": 1,
        "artifact_type": "resident_rejection_sample_audit",
        "created_at": now_iso(),
        "status": "passed" if passed else "attention_required",
        "passed": passed,
        "recommendation": recommendation,
        "cpu": {**cpu, "pixel_summary": cpu_summary},
        "resident": {**resident, "pixel_summary": resident_summary},
        "compare_json": str(compare_json) if compare_json else None,
        "comparison_region": compare_region,
        "shape_summary": shapes,
        "tile_size": step,
        "thresholds": thresholds,
        "evaluation_region": evaluation_region,
        "deltas": deltas,
        "evaluation_deltas": eval_deltas,
        "region_deltas": region_deltas,
        "top_tiles": _top_tiles(tile_rows, top_tiles),
        "checks": checks,
        "failed_checks": [item["name"] for item in checks if not item["passed"]],
    }


def _markdown(payload: dict[str, Any]) -> str:
    deltas = payload.get("deltas") or {}
    evaluation_deltas = payload.get("evaluation_deltas") or deltas
    region_deltas = payload.get("region_deltas") or {}
    lines = [
        "# Resident Rejection Sample Audit",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Passed: `{payload.get('passed')}`",
        f"- Recommendation: `{payload.get('recommendation')}`",
        f"- Evaluation region: `{payload.get('evaluation_region', 'full_frame')}`",
        f"- Tile size: `{payload.get('tile_size')}`",
        "",
        "## Evaluation Deltas",
        "",
        f"- Rejected sample delta: `{evaluation_deltas.get('rejected_sample_delta')}`",
        f"- Coverage sample delta: `{evaluation_deltas.get('coverage_sample_delta')}`",
        f"- Pre-rejection sample delta: `{evaluation_deltas.get('pre_rejection_sample_delta')}`",
        f"- Same-pre-rejection abs rejected delta: "
        f"`{evaluation_deltas.get('same_pre_rejection_abs_rejected_sample_delta')}`",
        "",
        "## Global Deltas",
        "",
        f"- Rejected sample delta: `{deltas.get('rejected_sample_delta')}`",
        f"- Coverage sample delta: `{deltas.get('coverage_sample_delta')}`",
        f"- Pre-rejection sample delta: `{deltas.get('pre_rejection_sample_delta')}`",
        f"- Same-pre-rejection abs rejected delta: "
        f"`{deltas.get('same_pre_rejection_abs_rejected_sample_delta')}`",
        f"- Rejection mismatch pixels: `{deltas.get('rejection_mismatch_pixels')}`",
        f"- DQ mismatch pixels: `{deltas.get('dq_mismatch_pixels')}`",
        "",
        "## Compare Region",
        "",
    ]
    for name, row in region_deltas.items():
        lines.extend(
            [
                f"### {name}",
                "",
                f"- Rejected sample delta: `{row.get('rejected_sample_delta')}`",
                f"- Abs rejected sample delta: `{row.get('abs_rejected_sample_delta')}`",
                f"- Coverage sample delta: `{row.get('coverage_sample_delta')}`",
                f"- Pre-rejection sample delta: `{row.get('pre_rejection_sample_delta')}`",
                f"- Rejection mismatch pixels: `{row.get('rejection_mismatch_pixels')}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Top Tiles",
            "",
            "| y0 | y1 | x0 | x1 | rejected delta | abs rejected | coverage delta | pre-rejection delta | mismatch px |",
            "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in payload.get("top_tiles") or []:
        lines.append(
            "| "
            f"{row.get('y0')} | {row.get('y1')} | {row.get('x0')} | {row.get('x1')} | "
            f"{row.get('rejected_sample_delta')} | {row.get('abs_rejected_sample_delta')} | "
            f"{row.get('coverage_sample_delta')} | {row.get('pre_rejection_sample_delta')} | "
            f"{row.get('rejection_mismatch_pixels')} |"
        )
    lines.extend(["", "## Checks", ""])
    for item in payload.get("checks") or []:
        marker = "PASS" if item.get("passed") else "FAIL"
        lines.append(f"- {marker}: `{item.get('name')}` - {item.get('evidence')}")
    lines.append("")
    return "\n".join(lines)


def write_resident_rejection_sample_audit(
    out: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(out, payload)
    if markdown is not None:
        target = Path(markdown)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(_markdown(payload), encoding="utf-8")
