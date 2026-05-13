from __future__ import annotations

from pathlib import Path

from glass.io.json_io import read_json, write_json
from glass.models import RunState


def write_run_state(path: str | Path, state: RunState) -> None:
    write_json(Path(path) / "run_state.json", state)


def read_run_state(path: str | Path) -> dict[str, object]:
    return read_json(Path(path) / "run_state.json")

