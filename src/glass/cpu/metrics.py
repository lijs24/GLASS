from __future__ import annotations

import numpy as np

from glass.cpu.star_detect import Star, detect_stars, robust_background
from glass.models import FrameQuality


def _finite_median(values: list[float | None]) -> float | None:
    finite = [float(value) for value in values if value is not None and np.isfinite(value)]
    if not finite:
        return None
    return float(np.median(np.asarray(finite, dtype=np.float32)))


def summarize_stars(stars: list[Star]) -> dict[str, float | None]:
    fwhm_values = [star.fwhm_px for star in stars]
    eccentricity_values = [star.eccentricity for star in stars]
    snr_values = [star.snr for star in stars]
    flux_values = [star.flux for star in stars if np.isfinite(star.flux)]
    fwhm_median = _finite_median(fwhm_values)
    fwhm_finite = np.asarray(
        [float(value) for value in fwhm_values if value is not None and np.isfinite(value)],
        dtype=np.float32,
    )
    fwhm_iqr = None
    if fwhm_finite.size:
        q75, q25 = np.percentile(fwhm_finite, [75, 25])
        fwhm_iqr = float(q75 - q25)
    return {
        "fwhm_median_px": fwhm_median,
        "fwhm_iqr_px": fwhm_iqr,
        "eccentricity_median": _finite_median(eccentricity_values),
        "star_snr_median": _finite_median(snr_values),
        "star_flux_median": None if not flux_values else float(np.median(np.asarray(flux_values, dtype=np.float32))),
    }


def combined_quality_weight(
    *,
    star_count: int,
    star_snr: float,
    fwhm_px: float | None,
    eccentricity: float | None,
    background_rms: float,
    saturation_fraction: float = 0.0,
) -> tuple[float, dict[str, float]]:
    snr_component = max(float(star_snr), 0.0)
    count_component = float(np.sqrt(max(int(star_count), 1)))
    fwhm_component = 1.0 / max(float(fwhm_px or 3.0), 0.75) ** 2
    eccentricity_component = max(0.05, 1.0 - float(eccentricity or 0.0))
    noise_component = 1.0 / max(float(background_rms), 1.0e-6)
    saturation_component = max(0.0, 1.0 - 5.0 * max(float(saturation_fraction), 0.0))
    weight = (
        snr_component
        * count_component
        * fwhm_component
        * eccentricity_component
        * noise_component
        * saturation_component
    )
    components = {
        "star_snr": snr_component,
        "sqrt_star_count": count_component,
        "fwhm_penalty": fwhm_component,
        "eccentricity_penalty": eccentricity_component,
        "noise_penalty": noise_component,
        "saturation_penalty": saturation_component,
    }
    return float(max(weight, 0.0)), components


def measure_quality(
    frame_id: str,
    filt: str | None,
    data: np.ndarray,
    *,
    saturation_level: float | None = None,
) -> FrameQuality:
    image = np.asarray(data, dtype=np.float32)
    finite = image[np.isfinite(image)]
    stats = robust_background(image)
    median = stats.median
    mean = float(np.mean(finite)) if finite.size else 0.0
    rms = stats.rms
    stars = detect_stars(image)
    star_metrics = summarize_stars(stars)
    star_snr = float(star_metrics["star_snr_median"] or 0.0)
    saturation_fraction = 0.0
    if saturation_level is not None and finite.size:
        saturation_fraction = float(np.count_nonzero(finite >= float(saturation_level)) / finite.size)
    weight, components = combined_quality_weight(
        star_count=len(stars),
        star_snr=star_snr,
        fwhm_px=star_metrics["fwhm_median_px"],
        eccentricity=star_metrics["eccentricity_median"],
        background_rms=rms,
        saturation_fraction=saturation_fraction,
    )
    return FrameQuality(
        frame_id=frame_id,
        filter=filt,
        background_median=median,
        background_rms=rms,
        star_count=len(stars),
        fwhm_px=star_metrics["fwhm_median_px"],
        eccentricity=star_metrics["eccentricity_median"],
        snr=star_snr,
        weight=weight,
        warnings=[] if stars else ["no stars detected"],
        background_mean=mean,
        background_mad=stats.mad,
        noise_mad=stats.noise,
        saturation_fraction=saturation_fraction,
        quality_score=weight,
        weight_source="combined_psf_snr_v1",
        weight_components=components,
        star_metrics=star_metrics,
    )
