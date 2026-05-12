from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


_PROCESSING_HISTORY_RE = re.compile(
    rb'<Property\s+[^>]*id="PixInsight:ProcessingHistory"[^>]*>(.*?)</Property>',
    re.DOTALL,
)


def _coerce_value(value: str | None) -> Any:
    if value is None:
        return None
    text = value.strip()
    if text == "":
        return ""
    lowered = text.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    try:
        if re.fullmatch(r"[+-]?\d+", text):
            return int(text)
        if re.fullmatch(r"[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?", text):
            return float(text)
    except ValueError:
        return text
    return text


def _element_text(element: ET.Element) -> str:
    return "".join(element.itertext()).strip()


def extract_processing_history_xml(xisf_path: str | Path, max_bytes: int = 32 * 1024 * 1024) -> str:
    with Path(xisf_path).open("rb") as handle:
        data = handle.read(max_bytes)
    match = _PROCESSING_HISTORY_RE.search(data)
    if match is None:
        raise ValueError(f"PixInsight:ProcessingHistory property was not found in {xisf_path}")
    return html.unescape(match.group(1).decode("utf-8", errors="replace")).strip()


def _parse_table(table: ET.Element) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for tr in table.findall("tr"):
        row: dict[str, Any] = {}
        for td in tr.findall("td"):
            key = str(td.attrib.get("id") or f"column_{len(row)}")
            raw_value = td.attrib.get("value")
            if raw_value is None:
                raw_value = _element_text(td)
            row[key] = _coerce_value(raw_value)
        rows.append(row)
    return rows


def _image_name(value: Any) -> str | None:
    if value in {None, ""}:
        return None
    text = str(value).replace("\\", "/")
    return text.rsplit("/", 1)[-1]


def _row_is_accepted(row: dict[str, Any]) -> bool:
    matches = row.get("totalPairMatches")
    if isinstance(matches, (int, float)):
        return matches > 0
    h_values = [row.get(f"H{i}{j}") for i in range(1, 4) for j in range(1, 4)]
    return any(isinstance(value, (int, float)) and abs(float(value)) > 1.0e-12 for value in h_values)


def parse_fastintegration_history(processing_history_xml: str, source: str | Path | None = None) -> dict[str, Any]:
    root = ET.fromstring(processing_history_xml)
    instances = [item for item in root.findall("instance") if item.attrib.get("class") == "FastIntegration"]
    if not instances:
        raise ValueError("FastIntegration instance was not found in ProcessingHistory")
    instance = instances[-1]

    parameters: dict[str, Any] = {}
    tables: dict[str, list[dict[str, Any]]] = {}
    timing: dict[str, Any] = {}
    for child in instance:
        if child.tag == "time":
            timing = {key: _coerce_value(value) for key, value in child.attrib.items()}
        elif child.tag == "parameter":
            key = str(child.attrib.get("id") or f"parameter_{len(parameters)}")
            raw_value = child.attrib.get("value")
            if raw_value is None:
                raw_value = _element_text(child)
            parameters[key] = _coerce_value(raw_value)
        elif child.tag == "table":
            table_id = str(child.attrib.get("id") or f"table_{len(tables)}")
            tables[table_id] = _parse_table(child)

    targets = tables.get("targets", [])
    output_data = tables.get("outputData", [])
    accepted = 0
    failed: list[dict[str, Any]] = []
    output_rows: list[dict[str, Any]] = []
    for index, row in enumerate(output_data):
        target = targets[index] if index < len(targets) else {}
        enriched = dict(row)
        enriched["target_index"] = index
        enriched["target_image"] = target.get("image")
        enriched["target_image_name"] = _image_name(target.get("image"))
        accepted_row = _row_is_accepted(row)
        enriched["accepted"] = accepted_row
        output_rows.append(enriched)
        if accepted_row:
            accepted += 1
        else:
            failed.append(
                {
                    "target_index": index,
                    "target_image": target.get("image"),
                    "target_image_name": _image_name(target.get("image")),
                    "totalPairMatches": row.get("totalPairMatches"),
                    "medianError": row.get("medianError"),
                    "peakError": row.get("peakError"),
                }
            )

    summary = {
        "target_count": len(targets),
        "output_data_count": len(output_data),
        "accepted_count": accepted,
        "failed_count": len(failed),
        "failed_target_image_names": [item["target_image_name"] for item in failed],
    }
    return {
        "schema_version": 1,
        "source": None if source is None else str(source),
        "history_class": "FastIntegration",
        "instance_id": instance.attrib.get("id"),
        "instance_version": _coerce_value(instance.attrib.get("version")),
        "time": timing,
        "parameters": parameters,
        "summary": summary,
        "failed_targets": failed,
        "targets": targets,
        "outputData": output_rows,
        "clean_room_note": (
            "Parsed user-generated PixInsight ProcessingHistory for black-box diagnostics only; "
            "not used as GPWBPP registration input."
        ),
    }


def read_fastintegration_history(xisf_path: str | Path, max_bytes: int = 32 * 1024 * 1024) -> dict[str, Any]:
    history_xml = extract_processing_history_xml(xisf_path, max_bytes=max_bytes)
    return parse_fastintegration_history(history_xml, source=xisf_path)
