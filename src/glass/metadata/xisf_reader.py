from __future__ import annotations

from pathlib import Path

from glass.io.xisf_io import read_xisf_image_spec
from glass.metadata.header_map import as_float, as_int, normalize_frame_type
from glass.models import FrameRecord


def _first_value(*values: object) -> object | None:
    for value in values:
        if value not in (None, ""):
            return value
    return None


def read_xisf_metadata(path: str | Path, frame_id: str) -> FrameRecord:
    p = Path(path)
    warnings = ["xisf metadata parsed from XML header only"]
    spec = read_xisf_image_spec(p)
    attrs = dict(spec.fits_keywords)
    props = spec.properties
    if spec.compression is not None:
        warnings.append(f"compressed XISF pixel attachment requires cache support: {spec.compression}")
    frame_type_value = _first_value(
        attrs.get("IMAGETYP"),
        attrs.get("FRAME"),
        attrs.get("OBSTYPE"),
        spec.image_attributes.get("imageType"),
    )
    frame_type = normalize_frame_type(frame_type_value)
    if frame_type == "unknown":
        warnings.append("unknown frame type")
    return FrameRecord(
        id=frame_id,
        path=str(p),
        file_format="xisf",
        frame_type=frame_type,  # type: ignore[arg-type]
        filter=_first_value(attrs.get("FILTER"), props.get("Instrument:Filter:Name")),  # type: ignore[arg-type]
        exposure_s=as_float(
            _first_value(attrs.get("EXPTIME"), attrs.get("EXPOSURE"), props.get("Instrument:FrameExposureTime"))
        ),
        gain=as_float(attrs.get("GAIN")),
        offset=as_float(attrs.get("OFFSET")),
        temperature_c=as_float(_first_value(attrs.get("CCD-TEMP"), attrs.get("SET-TEMP"))),
        binning_x=as_int(
            _first_value(attrs.get("XBINNING"), attrs.get("BINX"), props.get("Instrument:Camera:XBinning"))
        ),
        binning_y=as_int(
            _first_value(attrs.get("YBINNING"), attrs.get("BINY"), props.get("Instrument:Camera:YBinning"))
        ),
        width=spec.width,
        height=spec.height,
        camera=_first_value(attrs.get("INSTRUME"), attrs.get("CAMERA"), props.get("Instrument:Camera:Name")),  # type: ignore[arg-type]
        date_obs=_first_value(attrs.get("DATE-OBS"), attrs.get("DATE"), props.get("Observation:Time:Start")),  # type: ignore[arg-type]
        object_name=attrs.get("OBJECT"),
        ra=_first_value(attrs.get("RA"), props.get("Observation:Center:RA")),  # type: ignore[arg-type]
        dec=_first_value(attrs.get("DEC"), props.get("Observation:Center:Dec")),  # type: ignore[arg-type]
        header_summary={
            **attrs,
            "XISF_SAMPLE_FORMAT": spec.sample_format,
            "XISF_CHANNELS": spec.channels,
            "XISF_ATTACHMENT_BYTES": spec.byte_count,
            **{f"PROPERTY:{key}": value for key, value in props.items()},
        },
        warnings=warnings,
    )
