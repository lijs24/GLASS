from __future__ import annotations

from pathlib import Path
from typing import Any

from gpwbpp.cpu.metrics import measure_quality
from gpwbpp.io.fits_io import read_fits_data
from gpwbpp.io.json_io import read_json, write_json
from gpwbpp.models import to_jsonable


def measure_calibrated_quality(run_dir: str | Path, out_path: str | Path | None = None) -> dict[str, Any]:
    run = Path(run_dir)
    artifacts = read_json(run / "calibration_artifacts.json")
    qualities = []
    for item in artifacts.get("calibrated_lights", []):
        data = read_fits_data(item["path"])
        quality = measure_quality(item["frame_id"], None, data)
        qualities.append(to_jsonable(quality))
    reference = None
    if qualities:
        reference = max(
            qualities,
            key=lambda q: (
                int(q.get("star_count") or 0),
                float(q.get("weight") or 0.0),
                -float(q.get("background_rms") or 0.0),
            ),
        )["frame_id"]
    result = {
        "schema_version": 1,
        "frame_quality": qualities,
        "reference_frame_id": reference,
        "reference_selection": "max star_count, then max weight, then min background_rms",
    }
    write_json(out_path or (run / "frame_quality.json"), result)
    return result

