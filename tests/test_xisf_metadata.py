from __future__ import annotations

from pathlib import Path
import struct

import numpy as np

from glass.metadata.xisf_reader import read_xisf_metadata


def _write_metadata_xisf(path: Path) -> None:
    payload = np.zeros((24, 32), dtype="<f4").tobytes(order="C")
    offset = 4096
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<xisf version="1.0">'
        f'<Image geometry="32:24:1" sampleFormat="Float32" location="attachment:{offset}:{len(payload)}">'
        '<FITSKeyword name="IMAGETYP" value="Light"/>'
        '<FITSKeyword name="FILTER" value="\'H\'"/>'
        '<FITSKeyword name="EXPTIME" value="120"/>'
        '<Property id="Instrument:Camera:Name" type="String">QHY600M</Property>'
        '<Property id="Instrument:Camera:XBinning" type="UInt32" value="1"/>'
        '<Property id="Instrument:Camera:YBinning" type="UInt32" value="1"/>'
        "</Image></xisf>"
    ).encode("utf-8")
    path.write_bytes(b"XISF0100" + struct.pack("<Q", len(xml)) + xml + b"\0" * (offset - 16 - len(xml)) + payload)


def test_xisf_prefix_metadata(tmp_path: Path):
    path = tmp_path / "light.xisf"
    _write_metadata_xisf(path)
    record = read_xisf_metadata(path, "F000001")
    assert record.file_format == "xisf"
    assert record.frame_type == "light"
    assert record.filter == "H"
    assert record.width == 32
    assert record.height == 24
    assert record.exposure_s == 120.0
    assert record.camera == "QHY600M"
    assert record.binning_x == 1
    assert record.header_summary["XISF_SAMPLE_FORMAT"] == "Float32"
