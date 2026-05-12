from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from gpwbpp.gpu.tile_scheduler import iter_tiles
from gpwbpp.io.fits_io import FitsImageReader, FitsTileWriter
from gpwbpp.io.json_io import read_json, write_json


def _translation_from_matrix(matrix: list[list[float]]) -> tuple[int, int]:
    return int(round(float(matrix[0][2]))), int(round(float(matrix[1][2])))


def _warp_tile_nearest(reader: FitsImageReader, tile, dx: int, dy: int) -> tuple[np.ndarray, np.ndarray]:
    out_h = tile.y1 - tile.y0
    out_w = tile.x1 - tile.x0
    out = np.zeros((out_h, out_w), dtype=np.float32)
    coverage = np.zeros((out_h, out_w), dtype=np.float32)
    height, width = reader.shape
    src_x0 = max(0, tile.x0 - dx)
    src_x1 = min(width, tile.x1 - dx)
    src_y0 = max(0, tile.y0 - dy)
    src_y1 = min(height, tile.y1 - dy)
    if src_x0 >= src_x1 or src_y0 >= src_y1:
        return out, coverage
    dst_x0 = src_x0 + dx - tile.x0
    dst_x1 = src_x1 + dx - tile.x0
    dst_y0 = src_y0 + dy - tile.y0
    dst_y1 = src_y1 + dy - tile.y0
    out[dst_y0:dst_y1, dst_x0:dst_x1] = reader.read_tile(src_y0, src_y1, src_x0, src_x1)
    coverage[dst_y0:dst_y1, dst_x0:dst_x1] = 1.0
    return out, coverage


def warp_registered_frames(run_dir: str | Path, tile_size: int = 512) -> dict[str, Any]:
    run = Path(run_dir)
    calibration = read_json(run / "calibration_artifacts.json")
    registration = read_json(run / "registration_results.json")
    calibrated = {item["frame_id"]: item for item in calibration.get("calibrated_lights", [])}
    registered_dir = run / "registered_cache"
    coverage_dir = run / "coverage_cache"
    registered_dir.mkdir(parents=True, exist_ok=True)
    coverage_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    skipped = []
    for result in registration.get("registration_results", []):
        frame_id = result["frame_id"]
        status = str(result.get("status") or "unknown")
        if status not in {"ok", "reference"}:
            skipped.append(
                {
                    "frame_id": frame_id,
                    "status": status,
                    "reason": "registration did not produce an accepted transform",
                    "warnings": result.get("warnings", []),
                }
            )
            continue
        source = calibrated[frame_id]["path"]
        dx, dy = _translation_from_matrix(result["matrix"])
        with FitsImageReader(source) as reader:
            height, width = reader.shape
            registered_path = registered_dir / f"registered_{frame_id}.fits"
            coverage_path = coverage_dir / f"coverage_{frame_id}.fits"
            with FitsTileWriter(
                registered_path,
                width,
                height,
                {"IMAGETYP": "registered", "FRAMEID": frame_id},
            ) as registered_writer, FitsTileWriter(
                coverage_path,
                width,
                height,
                {"IMAGETYP": "coverage", "FRAMEID": frame_id},
            ) as coverage_writer:
                tile_count = 0
                valid_pixels = 0
                for tile in iter_tiles(width=width, height=height, tile_size=tile_size):
                    warped, coverage = _warp_tile_nearest(reader, tile, dx, dy)
                    registered_writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, warped)
                    coverage_writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, coverage)
                    tile_count += 1
                    valid_pixels += int(np.sum(coverage))
        outputs.append(
            {
                "frame_id": frame_id,
                "registered_path": str(registered_path),
                "coverage_path": str(coverage_path),
                "registration_status": status,
                "dx": dx,
                "dy": dy,
                "tile_size": tile_size,
                "tile_count": tile_count,
                "valid_pixels": valid_pixels,
            }
        )
    if not outputs:
        raise ValueError("registration produced no accepted frames for warp")
    payload = {"schema_version": 1, "warp_results": outputs, "skipped_frames": skipped}
    write_json(run / "warp_results.json", payload)
    return payload
