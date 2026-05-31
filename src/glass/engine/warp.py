from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from glass.engine.contracts import DQFlag
from glass.engine.dq import add_summary_counts, dq_header, dq_mask_from_coverage, write_dq_tile
from glass.gpu.tile_scheduler import iter_tiles
from glass.io.fits_io import FitsImageReader, FitsTileWriter
from glass.io.json_io import read_json, write_json


def _translation_from_matrix(matrix: list[list[float]]) -> tuple[int, int]:
    return int(round(float(matrix[0][2]))), int(round(float(matrix[1][2])))


def _matrix_is_integer_translation(matrix: list[list[float]], atol: float = 1.0e-6) -> bool:
    m = np.asarray(matrix, dtype=np.float64)
    if m.shape != (3, 3):
        return False
    linear_identity = np.allclose(m[:2, :2], np.eye(2), atol=atol)
    projective_identity = np.allclose(m[2], np.asarray([0.0, 0.0, 1.0]), atol=atol)
    integer_offset = abs(m[0, 2] - round(float(m[0, 2]))) <= atol and abs(
        m[1, 2] - round(float(m[1, 2]))
    ) <= atol
    return bool(linear_identity and projective_identity and integer_offset)


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


def _warp_tile_matrix_bilinear(
    reader: FitsImageReader,
    tile,
    matrix: list[list[float]],
    fill: float = 0.0,
) -> tuple[np.ndarray, np.ndarray]:
    out_h = tile.y1 - tile.y0
    out_w = tile.x1 - tile.x0
    out = np.full((out_h, out_w), fill, dtype=np.float32)
    coverage = np.zeros((out_h, out_w), dtype=np.float32)
    height, width = reader.shape
    transform = np.asarray(matrix, dtype=np.float64)
    if transform.shape != (3, 3):
        raise ValueError(f"warp matrix must be 3x3, got {transform.shape}")
    try:
        inverse = np.linalg.inv(transform)
    except np.linalg.LinAlgError as exc:
        raise ValueError("warp matrix is singular") from exc

    ys, xs = np.mgrid[tile.y0 : tile.y1, tile.x0 : tile.x1].astype(np.float64)
    denom = inverse[2, 0] * xs + inverse[2, 1] * ys + inverse[2, 2]
    valid_denominator = np.abs(denom) > 1.0e-12
    src_x = np.divide(
        inverse[0, 0] * xs + inverse[0, 1] * ys + inverse[0, 2],
        denom,
        out=np.full_like(xs, np.nan),
        where=valid_denominator,
    )
    src_y = np.divide(
        inverse[1, 0] * xs + inverse[1, 1] * ys + inverse[1, 2],
        denom,
        out=np.full_like(ys, np.nan),
        where=valid_denominator,
    )
    valid = (
        np.isfinite(src_x)
        & np.isfinite(src_y)
        & (src_x >= 0.0)
        & (src_x <= float(width - 1))
        & (src_y >= 0.0)
        & (src_y <= float(height - 1))
    )
    if not np.any(valid):
        return out, coverage

    valid_src_x = src_x[valid]
    valid_src_y = src_y[valid]
    read_x0 = max(0, int(np.floor(float(np.min(valid_src_x)))))
    read_x1 = min(width, int(np.ceil(float(np.max(valid_src_x)))) + 1)
    read_y0 = max(0, int(np.floor(float(np.min(valid_src_y)))))
    read_y1 = min(height, int(np.ceil(float(np.max(valid_src_y)))) + 1)
    if read_x0 >= read_x1 or read_y0 >= read_y1:
        return out, coverage

    source = reader.read_tile(read_y0, read_y1, read_x0, read_x1)
    x0 = np.floor(valid_src_x).astype(np.int64)
    y0 = np.floor(valid_src_y).astype(np.int64)
    x1 = np.minimum(x0 + 1, width - 1)
    y1 = np.minimum(y0 + 1, height - 1)
    tx = (valid_src_x - x0).astype(np.float32)
    ty = (valid_src_y - y0).astype(np.float32)
    lx0 = x0 - read_x0
    lx1 = x1 - read_x0
    ly0 = y0 - read_y0
    ly1 = y1 - read_y0
    top = source[ly0, lx0] * (1.0 - tx) + source[ly0, lx1] * tx
    bottom = source[ly1, lx0] * (1.0 - tx) + source[ly1, lx1] * tx
    out[valid] = top * (1.0 - ty) + bottom * ty
    coverage[valid] = 1.0
    return out, coverage


def warp_registered_frames(run_dir: str | Path, tile_size: int = 512) -> dict[str, Any]:
    run = Path(run_dir)
    calibration = read_json(run / "calibration_artifacts.json")
    registration = read_json(run / "registration_results.json")
    calibrated = {item["frame_id"]: item for item in calibration.get("calibrated_lights", [])}
    registered_dir = run / "registered_cache"
    coverage_dir = run / "coverage_cache"
    dq_dir = run / "dq_cache"
    registered_dir.mkdir(parents=True, exist_ok=True)
    coverage_dir.mkdir(parents=True, exist_ok=True)
    dq_dir.mkdir(parents=True, exist_ok=True)
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
        matrix = result["matrix"]
        dx, dy = float(matrix[0][2]), float(matrix[1][2])
        integer_translation = _matrix_is_integer_translation(matrix)
        with FitsImageReader(source) as reader:
            height, width = reader.shape
            registered_path = registered_dir / f"registered_{frame_id}.fits"
            coverage_path = coverage_dir / f"coverage_{frame_id}.fits"
            dq_path = dq_dir / f"dq_warp_{frame_id}.fits"
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
            ) as coverage_writer, FitsTileWriter(
                dq_path,
                width,
                height,
                dq_header("warp", frame_id),
            ) as dq_writer:
                tile_count = 0
                valid_pixels = 0
                dq_summary: dict[str, int] = {}
                for tile in iter_tiles(width=width, height=height, tile_size=tile_size):
                    if integer_translation:
                        warped, coverage = _warp_tile_nearest(reader, tile, int(round(dx)), int(round(dy)))
                        warp_model = "integer_translation_nearest"
                    else:
                        warped, coverage = _warp_tile_matrix_bilinear(reader, tile, matrix)
                        warp_model = "matrix_bilinear"
                    registered_writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, warped)
                    coverage_writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, coverage)
                    tile_dq = dq_mask_from_coverage(coverage, DQFlag.WARP_EDGE)
                    write_dq_tile(dq_writer, tile, tile_dq)
                    add_summary_counts(dq_summary, tile_dq.summary())
                    tile_count += 1
                    valid_pixels += int(np.sum(coverage))
        outputs.append(
            {
                "frame_id": frame_id,
                "registered_path": str(registered_path),
                "coverage_path": str(coverage_path),
                "dq_mask_path": str(dq_path),
                "dq_summary": dq_summary,
                "registration_status": status,
                "dx": dx,
                "dy": dy,
                "matrix": matrix,
                "warp_model": warp_model,
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
