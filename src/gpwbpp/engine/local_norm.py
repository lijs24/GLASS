from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from gpwbpp.cpu.local_norm import apply_tile_normalization, estimate_tile_normalization
from gpwbpp.gpu.tile_scheduler import iter_tiles
from gpwbpp.io.fits_io import FitsImageReader, FitsTileWriter
from gpwbpp.io.json_io import read_json, write_json


def _cuda_module_if_requested(backend: str):
    if backend == "cpu":
        return None
    try:
        import gpwbpp_cuda
    except Exception:
        return None
    if gpwbpp_cuda.cuda_available() and hasattr(gpwbpp_cuda, "local_norm_apply_f32"):
        return gpwbpp_cuda
    if backend == "cuda":
        raise RuntimeError("CUDA backend requested but local normalization CUDA backend is unavailable")
    return None


def _policy_from_plan(plan_path: str | Path | None) -> dict[str, Any]:
    if plan_path is None:
        return {"enabled": False}
    path = Path(plan_path)
    if not path.exists():
        return {"enabled": False}
    raw = read_json(path).get("local_normalization_policy", {})
    return raw if isinstance(raw, dict) else {"enabled": False}


def _local_norm_enabled(policy: dict[str, Any], enabled_override: bool | None) -> bool:
    if enabled_override is not None:
        return enabled_override
    return bool(policy.get("enabled", False))


def _disabled_payload(run: Path, policy: dict[str, Any], warp: dict[str, Any], reference_id: str | None) -> dict[str, Any]:
    outputs = []
    for item in warp.get("warp_results", []):
        outputs.append(
            {
                "frame_id": item["frame_id"],
                "input_path": item["registered_path"],
                "normalized_path": item["registered_path"],
                "coverage_path": item["coverage_path"],
                "backend": "passthrough",
                "tile_count": 0,
                "status": "disabled_passthrough",
                "warnings": [],
            }
        )
    return {
        "schema_version": 1,
        "enabled": False,
        "reference_frame_id": reference_id,
        "tile_radius": policy.get("tile_radius", 64),
        "background_mask_policy": policy.get("background_mask_policy", "sigma"),
        "outlier_policy": policy.get("outlier_policy", "clip"),
        "crop_box": None,
        "local_norm_results": outputs,
        "output_dir": str(run / "registered_cache"),
    }


def local_normalize_registered_frames(
    run_dir: str | Path,
    plan_path: str | Path | None = None,
    backend: str = "auto",
    tile_size: int = 512,
    enabled_override: bool | None = None,
) -> dict[str, Any]:
    run = Path(run_dir)
    registration = read_json(run / "registration_results.json")
    warp = read_json(run / "warp_results.json")
    policy = _policy_from_plan(plan_path)
    reference_id = registration.get("reference_frame_id")
    if not _local_norm_enabled(policy, enabled_override):
        payload = _disabled_payload(run, policy, warp, reference_id)
        write_json(run / "local_norm_results.json", payload)
        return payload

    by_frame = {item["frame_id"]: item for item in warp.get("warp_results", [])}
    if reference_id not in by_frame:
        raise ValueError("local normalization reference frame is missing from warp results")
    reference = by_frame[reference_id]
    output_dir = run / "local_norm_cache"
    output_dir.mkdir(parents=True, exist_ok=True)
    cuda_module = _cuda_module_if_requested(backend)
    outputs: list[dict[str, Any]] = []

    with FitsImageReader(reference["registered_path"]) as reference_data, FitsImageReader(
        reference["coverage_path"]
    ) as reference_coverage:
        height, width = reference_data.shape
        for item in warp.get("warp_results", []):
            frame_id = item["frame_id"]
            out_path = output_dir / f"local_norm_{frame_id}.fits"
            warnings: list[str] = []
            scales: list[float] = []
            offsets: list[float] = []
            valid_counts: list[int] = []
            with FitsImageReader(item["registered_path"]) as source_data, FitsImageReader(
                item["coverage_path"]
            ) as source_coverage, FitsTileWriter(
                out_path,
                width=width,
                height=height,
                header={"IMAGETYP": "local_norm", "FRAMEID": frame_id},
            ) as writer:
                tile_count = 0
                actual_backend = "cuda" if cuda_module is not None else "cpu"
                for tile in iter_tiles(width=width, height=height, tile_size=tile_size):
                    src_tile = source_data.read_tile(tile.y0, tile.y1, tile.x0, tile.x1)
                    ref_tile = reference_data.read_tile(tile.y0, tile.y1, tile.x0, tile.x1)
                    valid_mask = (
                        source_coverage.read_tile(tile.y0, tile.y1, tile.x0, tile.x1) > 0.5
                    ) & (reference_coverage.read_tile(tile.y0, tile.y1, tile.x0, tile.x1) > 0.5)
                    if cuda_module is not None and hasattr(
                        cuda_module, "local_norm_estimate_apply_mean_std_f32"
                    ):
                        normalized, stats = cuda_module.local_norm_estimate_apply_mean_std_f32(
                            src_tile,
                            ref_tile,
                            valid_mask,
                        )
                        actual_backend = "cuda_mean_std"
                    else:
                        stats = estimate_tile_normalization(src_tile, ref_tile, valid_mask)
                        scale = float(stats["scale"])
                        offset = float(stats["offset"])
                        if cuda_module is not None:
                            normalized = cuda_module.local_norm_apply_f32(src_tile, scale, offset)
                            normalized[~valid_mask] = src_tile[~valid_mask]
                        else:
                            normalized = apply_tile_normalization(src_tile, scale, offset, valid_mask)
                    if stats["status"] == "empty":
                        warnings.append(
                            f"empty normalization tile y={tile.y0}:{tile.y1} x={tile.x0}:{tile.x1}"
                        )
                    scale = float(stats["scale"])
                    offset = float(stats["offset"])
                    writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, normalized)
                    tile_count += 1
                    scales.append(scale)
                    offsets.append(offset)
                    valid_counts.append(int(stats["valid_pixels"]))
            outputs.append(
                {
                    "frame_id": frame_id,
                    "input_path": item["registered_path"],
                    "normalized_path": str(out_path),
                    "coverage_path": item["coverage_path"],
                    "backend": actual_backend,
                    "tile_size": tile_size,
                    "tile_count": tile_count,
                    "mean_scale": float(np.mean(scales)) if scales else 1.0,
                    "mean_offset": float(np.mean(offsets)) if offsets else 0.0,
                    "valid_pixels": int(np.sum(valid_counts)) if valid_counts else 0,
                    "status": "reference" if frame_id == reference_id else "ok",
                    "warnings": warnings,
                }
            )

    payload = {
        "schema_version": 1,
        "enabled": True,
        "reference_frame_id": reference_id,
        "reference_path": reference["registered_path"],
        "tile_radius": policy.get("tile_radius", 64),
        "background_mask_policy": policy.get("background_mask_policy", "sigma"),
        "outlier_policy": policy.get("outlier_policy", "clip"),
        "crop_box": None,
        "local_norm_results": outputs,
        "output_dir": str(output_dir),
    }
    write_json(run / "local_norm_results.json", payload)
    return payload
