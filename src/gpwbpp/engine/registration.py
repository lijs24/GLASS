from __future__ import annotations

from pathlib import Path
from typing import Any

from gpwbpp.cpu.registration import estimate_translation_phase_correlation, translation_matrix
from gpwbpp.io.fits_io import read_fits_data
from gpwbpp.io.json_io import read_json, write_json
from gpwbpp.models import RegistrationResult, to_jsonable


def register_calibrated_frames(run_dir: str | Path, out_path: str | Path | None = None) -> dict[str, Any]:
    run = Path(run_dir)
    artifacts = read_json(run / "calibration_artifacts.json")
    quality = read_json(run / "frame_quality.json")
    reference_id = quality.get("reference_frame_id")
    calibrated = {item["frame_id"]: item for item in artifacts.get("calibrated_lights", [])}
    if reference_id not in calibrated:
        raise ValueError("reference frame is missing from calibrated cache")
    reference_data = read_fits_data(calibrated[reference_id]["path"])
    quality_by_id = {item["frame_id"]: item for item in quality.get("frame_quality", [])}

    results = []
    for frame_id, item in calibrated.items():
        warnings: list[str] = []
        if frame_id == reference_id:
            dx, dy = 0.0, 0.0
            status = "reference"
            rms = 0.0
        else:
            data = read_fits_data(item["path"])
            dx, dy = estimate_translation_phase_correlation(reference_data, data)
            status = "ok"
            rms = 0.0
        matched = min(
            int(quality_by_id.get(frame_id, {}).get("star_count") or 0),
            int(quality_by_id.get(reference_id, {}).get("star_count") or 0),
        )
        if status == "ok" and matched == 0:
            warnings.append("registration estimated by phase correlation without detected star matches")
        results.append(
            to_jsonable(
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
        )

    payload = {
        "schema_version": 1,
        "reference_frame_id": reference_id,
        "transform_model": "translation",
        "method": "phase_correlation_cpu_baseline",
        "registration_results": results,
    }
    write_json(out_path or (run / "registration_results.json"), payload)
    return payload

