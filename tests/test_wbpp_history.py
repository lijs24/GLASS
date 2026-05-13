from __future__ import annotations

import html
import json
from pathlib import Path

from glass.cli import main
from glass.report.wbpp_history import parse_fastintegration_history, read_fastintegration_history


def _history_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<ProcessingHistory version="1.0">
  <instance class="FastIntegration" version="2" id="FastIntegration_instance">
    <time start="2026-05-12T13:20:07.521Z" span="225.69198"/>
    <parameter id="referenceImage">C:\\run\\calibrated\\LIGHT_H_0001_c.xisf</parameter>
    <parameter id="rejectionAlgorithm" value="WinsorizedSigmaClipping"/>
    <parameter id="sigmaLow" value="3.0"/>
    <parameter id="sigmaHigh" value="3.0"/>
    <table id="targets" rows="2">
      <tr>
        <td id="enabled" value="true"/>
        <td id="image">C:\\run\\calibrated\\LIGHT_H_0001_c.xisf</td>
      </tr>
      <tr>
        <td id="enabled" value="true"/>
        <td id="image">C:\\run\\calibrated\\LIGHT_H_0002_c.xisf</td>
      </tr>
    </table>
    <table id="outputData" rows="2">
      <tr>
        <td id="totalPairMatches" value="42"/>
        <td id="medianError" value="0.25"/>
        <td id="peakError" value="1.0"/>
        <td id="H11" value="1"/>
        <td id="H12" value="0"/>
        <td id="H13" value="2.5"/>
        <td id="H21" value="0"/>
        <td id="H22" value="1"/>
        <td id="H23" value="-1.5"/>
        <td id="H31" value="0"/>
        <td id="H32" value="0"/>
        <td id="H33" value="1"/>
      </tr>
      <tr>
        <td id="totalPairMatches" value="0"/>
        <td id="medianError" value="0"/>
        <td id="peakError" value="0"/>
        <td id="H11" value="0"/>
        <td id="H22" value="0"/>
        <td id="H33" value="0"/>
      </tr>
    </table>
  </instance>
</ProcessingHistory>
"""


def _write_fake_xisf(path: Path) -> None:
    escaped = html.escape(_history_xml(), quote=True)
    path.write_text(
        f'<?xml version="1.0"?><xisf><Property id="PixInsight:ProcessingHistory" '
        f'type="String">{escaped}</Property></xisf>',
        encoding="utf-8",
    )


def test_parse_fastintegration_history_summarizes_failed_targets():
    payload = parse_fastintegration_history(_history_xml(), source="synthetic.xisf")

    assert payload["parameters"]["rejectionAlgorithm"] == "WinsorizedSigmaClipping"
    assert payload["parameters"]["sigmaLow"] == 3.0
    assert payload["summary"]["target_count"] == 2
    assert payload["summary"]["accepted_count"] == 1
    assert payload["summary"]["failed_target_image_names"] == ["LIGHT_H_0002_c.xisf"]
    assert payload["outputData"][0]["H13"] == 2.5
    assert payload["outputData"][0]["target_image_name"] == "LIGHT_H_0001_c.xisf"
    assert "not used as GLASS registration input" in payload["clean_room_note"]


def test_read_fastintegration_history_from_xisf_property(tmp_path: Path):
    path = tmp_path / "master.xisf"
    _write_fake_xisf(path)

    payload = read_fastintegration_history(path)

    assert payload["source"] == str(path)
    assert payload["summary"]["failed_count"] == 1


def test_blackbox_history_cli_writes_json(tmp_path: Path):
    path = tmp_path / "master.xisf"
    out = tmp_path / "history.json"
    _write_fake_xisf(path)

    assert main(["blackbox-history", "--master", str(path), "--out", str(out)]) == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["summary"]["accepted_count"] == 1
