from __future__ import annotations

from pathlib import Path

from glass.io.json_io import read_json


def read_golden_truth(path: str | Path) -> dict[str, object]:
    return read_json(Path(path) / "golden_truth.json")

