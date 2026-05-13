from __future__ import annotations

from pathlib import Path

from glass.io.json_io import write_json


def write_stage_artifact(run_dir: str | Path, stage: str, payload: dict[str, object]) -> Path:
    path = Path(run_dir) / f"{stage}_artifacts.json"
    write_json(path, payload)
    return path

