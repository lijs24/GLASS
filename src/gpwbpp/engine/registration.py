from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from gpwbpp.cpu.registration import (
    estimate_astroalign_transform,
    estimate_star_transform,
    estimate_translation_phase_correlation,
    translation_matrix,
)
from gpwbpp.gpu.tile_scheduler import iter_tiles
from gpwbpp.io.fits_io import FitsImageReader
from gpwbpp.io.json_io import read_json, write_json
from gpwbpp.engine.quality import detect_stars_streaming
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
    method: str = "auto",
) -> dict[str, Any]:
    if preview_max_dimension <= 0:
        raise ValueError("preview_max_dimension must be positive")
    run = Path(run_dir)
    artifacts = read_json(run / "calibration_artifacts.json")
    quality = read_json(run / "frame_quality.json")
    plan = read_json(run / "processing_plan.json") if (run / "processing_plan.json").exists() else {}
    registration_policy = plan.get("registration_policy", {})
    transform_model = str(registration_policy.get("transform_model") or "translation")
    min_inliers = int(registration_policy.get("min_inliers") or 6)
    max_rms_px = float(registration_policy.get("max_rms_px") or 2.0)
    astroalign_max_control_points = int(registration_policy.get("astroalign_max_control_points") or 50)
    astroalign_detection_sigma = float(registration_policy.get("astroalign_detection_sigma") or 5.0)
    astroalign_min_area = int(registration_policy.get("astroalign_min_area") or 5)
    if transform_model not in {"translation", "similarity", "affine"}:
        transform_model = "translation"
    if method == "astroalign":
        transform_model = "similarity"
    if method not in {"auto", "star", "astroalign"}:
        raise ValueError("registration method must be auto, star, or astroalign")
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
    reference_quality = quality_by_id.get(reference_id, {})
    reference_stars = detect_stars_streaming(
        calibrated[reference_id]["path"],
        float(reference_quality.get("background_median") or 0.0),
        float(reference_quality.get("background_rms") or 0.0),
        tile_size=tile_size,
    )

    results = []
    for frame_id, item in calibrated.items():
        warnings: list[str] = []
        tile_count = reference_tile_count
        row_source = "streaming_star_detector"
        if frame_id == reference_id:
            dx, dy = 0.0, 0.0
            status = "reference"
            rms = 0.0
            matrix = translation_matrix(dx, dy)
            matched = len(reference_stars)
            inliers = len(reference_stars)
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
            matrix = None
            matched = 0
            inliers = 0
            rms = float("nan")
            status = "failed"
            if method == "astroalign":
                try:
                    astroalign_result = estimate_astroalign_transform(
                        reference_preview,
                        moving_preview,
                        max_control_points=astroalign_max_control_points,
                        detection_sigma=astroalign_detection_sigma,
                        min_area=astroalign_min_area,
                    )
                    matrix_array = np.asarray(astroalign_result.matrix, dtype=np.float64)
                    matrix_array[0, 2] *= reference_scale
                    matrix_array[1, 2] *= reference_scale
                    matrix = [[float(value) for value in row] for row in matrix_array]
                    matched = astroalign_result.matched_stars
                    inliers = astroalign_result.inliers
                    rms = float(astroalign_result.rms_px) * reference_scale
                    status = astroalign_result.status
                    warnings.extend(astroalign_result.warnings)
                    warnings.append("astroalign transform estimated on streaming preview")
                    row_source = "open_source_astroalign_preview"
                except Exception as exc:
                    matrix = translation_matrix(0.0, 0.0)
                    matched = 0
                    inliers = 0
                    rms = float("nan")
                    status = "failed"
                    warnings.append(f"astroalign registration failed: {exc}")
                    row_source = "open_source_astroalign_preview"
            if method in {"star", "auto"}:
                moving_quality = quality_by_id.get(frame_id, {})
                moving_stars = detect_stars_streaming(
                    item["path"],
                    float(moving_quality.get("background_median") or 0.0),
                    float(moving_quality.get("background_rms") or 0.0),
                    tile_size=tile_size,
                )
                star_result = estimate_star_transform(
                    reference_stars,
                    moving_stars,
                    transform_model=transform_model,
                    min_inliers=min_inliers,
                    tolerance_px=max(max_rms_px * 1.5, 3.0),
                )
                matrix = star_result.matrix
                matched = star_result.matched_stars
                inliers = star_result.inliers
                rms = star_result.rms_px
                status = star_result.status
                warnings.extend(star_result.warnings)
                warnings.append("star-based clean-room registration")
            if status != "ok" and method == "auto":
                preview_dx, preview_dy = estimate_translation_phase_correlation(reference_preview, moving_preview)
                dx, dy = preview_dx * reference_scale, preview_dy * reference_scale
                matrix = translation_matrix(dx, dy)
                matched = min(
                    int(quality_by_id.get(frame_id, {}).get("star_count") or 0),
                    int(quality_by_id.get(reference_id, {}).get("star_count") or 0),
                )
                inliers = matched
                rms = 0.0
                status = "ok"
                warnings.append("fell back to phase-correlation preview registration")
                row_source = "streaming_preview_fallback"
            if matrix is None:
                matrix = translation_matrix(0.0, 0.0)
            preview_scale = moving_scale
            preview_shape = list(moving_preview.shape)
        if status == "ok" and matched == 0:
            warnings.append("registration estimated by phase correlation without detected star matches")
        row = to_jsonable(
            RegistrationResult(
                frame_id=frame_id,
                reference_frame_id=reference_id,
                transform_model=transform_model,
                matrix=matrix,
                matched_stars=matched,
                inliers=inliers,
                rms_px=rms,
                status=status,
                warnings=warnings,
            )
        )
        row.update(
            {
                "registration_image_source": "streaming_preview",
                "registration_solution_source": row_source,
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
        "transform_model": transform_model,
        "method": method,
        "registration_image_source": "streaming_star_detector",
        "astroalign": {
            "available": method == "astroalign",
            "max_control_points": astroalign_max_control_points,
            "detection_sigma": astroalign_detection_sigma,
            "min_area": astroalign_min_area,
            "license": "MIT",
        },
        "min_inliers": min_inliers,
        "max_rms_px": max_rms_px,
        "preview_max_dimension": preview_max_dimension,
        "tile_size": tile_size,
        "registration_results": results,
    }
    write_json(out_path or (run / "registration_results.json"), payload)
    return payload
