from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from glass.models import to_jsonable


def read_json(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def write_json(path: str | Path, value: Any, *, compact: bool = False) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as f:
        if compact:
            json.dump(to_jsonable(value), f, separators=(",", ":"), sort_keys=True)
        else:
            json.dump(to_jsonable(value), f, indent=2, sort_keys=True)
        f.write("\n")
