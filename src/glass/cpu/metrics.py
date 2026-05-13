from __future__ import annotations

import numpy as np

from glass.cpu.star_detect import detect_stars
from glass.models import FrameQuality


def measure_quality(frame_id: str, filt: str | None, data: np.ndarray) -> FrameQuality:
    image = np.asarray(data, dtype=np.float32)
    median = float(np.median(image))
    rms = float(np.std(image))
    stars = detect_stars(image)
    snr = 0.0 if rms == 0 else float(max((np.mean(image) - median) / rms, 0.0))
    weight = 1.0 / max(rms * rms, 1.0e-6)
    return FrameQuality(
        frame_id=frame_id,
        filter=filt,
        background_median=median,
        background_rms=rms,
        star_count=len(stars),
        fwhm_px=3.0 if stars else None,
        eccentricity=0.0 if stars else None,
        snr=snr,
        weight=weight,
        warnings=[] if stars else ["no stars detected"],
    )
