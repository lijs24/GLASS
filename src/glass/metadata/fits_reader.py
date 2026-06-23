from __future__ import annotations

from pathlib import Path
from typing import Any

from astropy.io import fits

from glass.io.fits_fast import (
    SIMPLE_FITS_SPEC_SUMMARY_KEY,
    FastFitsUnsupported,
    simple_fits_image_spec,
    simple_fits_spec_to_summary,
)
from glass.metadata.header_map import as_float, as_int, first_header_value, normalize_frame_type
from glass.models import FrameRecord


SUMMARY_KEYS = [
    "IMAGETYP",
    "FRAME",
    "OBSTYPE",
    "FILTER",
    "EXPTIME",
    "EXPOSURE",
    "GAIN",
    "OFFSET",
    "CCD-TEMP",
    "SET-TEMP",
    "XBINNING",
    "YBINNING",
    "INSTRUME",
    "DATE-OBS",
    "OBJECT",
    "RA",
    "DEC",
    "PIERSIDE",
    "OBJCTROT",
    "ROTATOR",
    "NAXIS1",
    "NAXIS2",
]


def read_fits_metadata(path: str | Path, frame_id: str) -> FrameRecord:
    warnings: list[str] = []
    p = Path(path)
    header = fits.getheader(p, memmap=True)
    header_dict: dict[str, Any] = {str(k): header[k] for k in header.keys()}
    frame_type_value = first_header_value(header_dict, ["IMAGETYP", "FRAME", "OBSTYPE"])
    width = as_int(first_header_value(header_dict, ["NAXIS1"]))
    height = as_int(first_header_value(header_dict, ["NAXIS2"]))
    if width is None or height is None:
        warnings.append("missing image shape metadata")
    frame_type = normalize_frame_type(frame_type_value)
    if frame_type == "unknown":
        warnings.append("unknown frame type")
    exposure = as_float(first_header_value(header_dict, ["EXPTIME", "EXPOSURE", "EXP-TIME"]))
    gain = as_float(first_header_value(header_dict, ["GAIN", "EGAIN"]))
    offset = as_float(first_header_value(header_dict, ["OFFSET", "BLKLEVEL"]))
    temperature = as_float(first_header_value(header_dict, ["CCD-TEMP", "SET-TEMP", "CCD_TEMP"]))
    bin_x = as_int(first_header_value(header_dict, ["XBINNING", "BINX", "XBIN"]))
    bin_y = as_int(first_header_value(header_dict, ["YBINNING", "BINY", "YBIN"]))
    summary = {key: header_dict[key] for key in SUMMARY_KEYS if key in header_dict}
    try:
        summary[SIMPLE_FITS_SPEC_SUMMARY_KEY] = simple_fits_spec_to_summary(simple_fits_image_spec(p))
    except FastFitsUnsupported:
        pass
    return FrameRecord(
        id=frame_id,
        path=str(p),
        file_format="fits",
        frame_type=frame_type,  # type: ignore[arg-type]
        filter=first_header_value(header_dict, ["FILTER", "FILTERID"]),
        exposure_s=exposure,
        gain=gain,
        offset=offset,
        temperature_c=temperature,
        binning_x=bin_x,
        binning_y=bin_y,
        width=width,
        height=height,
        camera=first_header_value(header_dict, ["INSTRUME", "CAMERA"]),
        date_obs=first_header_value(header_dict, ["DATE-OBS", "DATE"]),
        object_name=first_header_value(header_dict, ["OBJECT"]),
        ra=first_header_value(header_dict, ["RA", "OBJCTRA"]),
        dec=first_header_value(header_dict, ["DEC", "OBJCTDEC"]),
        header_summary=summary,
        warnings=warnings,
    )
