from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from gpwbpp.cpu.registration import estimate_translation_phase_correlation, translation_matrix
from gpwbpp.gpu.tile_scheduler import iter_tiles
from gpwbpp.io.fits_io import FitsImageReader
from gpwbpp.io.json_io import read_json, write_json
from gpwbpp.models import RegistrationResult, to_jsonable


def _registration_preview(
    path: str | Path,
    tile_size: int,
    max_dimension: int = 1024,
) -> tuple[np.ndarray, int, int]:
    with FitsImageReader(path) as reader:
        scale = max(1, int(np.ceil(max(reader.width, reader.height) / max_dimension)))
        preview_height = int(np.ceil(reader.height / scale))
        preview_width = int(np.ceil(reader.width / scale))
        sums = np.zeros((preview_height, preview_width), dtype=np.float64)
        counts = np.zeros((preview_height, preview_width), dtype=np.float32)
        tile_count = 0
        for tile in iter_tiles(width=reader.width, height=reader.height, tile_size=tile_size):
            data = reader.read_tile(tile.y0, tile.y1, tile.x0, tile.x1)
            columns = np.arange(tile.x0, tile.x1, dtype=np.int64) // scale
            for local_y, source_y in enumerate(range(tile.y0, tile.y1)):
                row = data[local_y]
                finite = np.isfinite(row)
                if not np.any(finite):
                    continue
                preview_y = source_y // scale
                np.add.at(sums[preview_y], columns[finite], row[finite])
                np.add.at(counts[preview_y], columns[finite], 1.0)
            tile_count += 1
    preview = np.divide(
        sums,
        counts,
        out=np.zeros_like(sums, dtype=np.float64),
        where=counts > 0,
    ).astype(np.float32)
    return preview, scale, tile_count


def register_calibrated_frames(
    run_dir: str | Path,
    out_path: str | Path | None = None,
    tile_size: int = 512,
    preview_max_dimension: int = 1024,
) -> dict[str, Any]:
    run = Path(run_dir)
    artifacts = read_json(run / "calibration_artifacts.json")
    quality = read_json(run / "frame_quality.json")
    reference_id = quality.get("reference_frame_id")
    calibrated = {item["frame_id"]: item for item in artifacts.get("calibrated_lights", [])}
    if reference_id not in calibrated:
        raise ValueError("reference frame is missing from calibrated cache")
    reference_preview, reference_scale, reference_tile_count = _registration_preview(
        calibrated[reference_id]["path"],
        tile_size=tile_size,
        max_dimension=preview_max_dimension,
    )
    quality_by_id = {item["frame_id"]: item for item in quality.get("frame_quality", [])}

    results = []
    for frame_id, item in calibrated.items():
        warnings: list[str] = []
        tile_count = reference_tile_count
        if frame_id == reference_id:
            dx, dy = 0.0, 0.0
            status = "reference"
            rms = 0.0
            preview_scale = reference_scale
            preview_shape = list(reference_preview.shape)
        else:
            moving_preview, moving_scale, tile_count = _registration_preview(
                item["path"],
                tile_size=tile_size,
                max_dimension=preview_max_dimension,
            )
            if moving_preview.shape != reference_preview.shape:
                raise ValueError(
                    f"registration preview shape mismatch: {moving_preview.shape} != {reference_preview.shape}"
                )
            if moving_scale != reference_scale:
                raise ValueError(f"registration preview scale mismatch: {moving_scale} != {reference_scale}")
            preview_dx, preview_dy = estimate_translation_phase_correlation(reference_preview, moving_preview)
            dx, dy = preview_dx * reference_scale, preview_dy * reference_scale
            status = "ok"
            rms = 0.0
            preview_scale = moving_scale
            preview_shape = list(moving_preview.shape)
        matched = min(
            int(quality_by_id.get(frame_id, {}).get("star_count") or 0),
            int(quality_by_id.get(reference_id, {}).get("star_count") or 0),
        )
        if status == "ok" and matched == 0:
            warnings.append("registration estimated by phase correlation without detected star matches")
        row = to_jsonable(
            RegistrationResult(
                frame_id=frame_id,
                reference_frame_id=reference_id,
                transform_model="translation",
                matrix=translation_matrix(dx, dy),
                matched_stars=matched,
                inliers=matched,
                rms_px=rms,
                status=status,
                warnings=warnings,
            )
        )
        row.update(
            {
                "registration_image_source": "streaming_preview",
                "preview_scale": preview_scale,
                "preview_shape": preview_shape,
                "tile_size": tile_size,
                "tile_count": tile_count,
            }
        )
        results.append(row)

    payload = {
        "schema_version": 1,
        "reference_frame_id": reference_id,
        "transform_model": "translation",
        "method": "phase_correlation_streaming_preview",
        "registration_image_source": "streaming_preview",
        "preview_max_dimension": preview_max_dimension,
        "tile_size": tile_size,
        "registration_results": results,
    }
    write_json(out_path or (run / "registration_results.json"), payload)
    return payload
