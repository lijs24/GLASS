from __future__ import annotations

import json
from pathlib import Path

from glass.io.json_io import read_json, write_json


def test_write_json_defaults_to_pretty_output(tmp_path: Path) -> None:
    path = tmp_path / "pretty.json"

    write_json(path, {"b": 2, "a": {"x": 1}})

    text = path.read_text(encoding="utf-8")
    assert "\n  " in text
    assert json.loads(text) == {"a": {"x": 1}, "b": 2}


def test_write_json_compact_preserves_roundtrip_without_indentation(tmp_path: Path) -> None:
    path = tmp_path / "compact.json"

    write_json(path, {"b": 2, "a": {"x": 1}}, compact=True)

    text = path.read_text(encoding="utf-8")
    assert text == '{"a":{"x":1},"b":2}\n'
    assert read_json(path) == {"a": {"x": 1}, "b": 2}
