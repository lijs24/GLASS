from __future__ import annotations

from pathlib import Path

from glass.metadata.xisf_reader import read_xisf_metadata


def test_xisf_prefix_metadata(tmp_path: Path):
    path = tmp_path / "light.xisf"
    path.write_text(
        '<xisf><Image geometry="32:24:1" sampleFormat="Float32">'
        '<FITSKeyword name="IMAGETYP" value="Light"/>'
        '<FITSKeyword name="FILTER" value="H"/>'
        '<FITSKeyword name="EXPTIME" value="120"/>'
        "</Image></xisf>",
        encoding="utf-8",
    )
    record = read_xisf_metadata(path, "F000001")
    assert record.file_format == "xisf"
    assert record.frame_type == "light"
    assert record.width == 32
    assert record.height == 24
    assert record.exposure_s == 120.0

