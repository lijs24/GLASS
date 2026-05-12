from __future__ import annotations

from pathlib import Path

from gpwbpp.models import RunState, now_iso


def initialize_run(run_dir: str | Path) -> RunState:
    Path(run_dir).mkdir(parents=True, exist_ok=True)
    return RunState(run_id=Path(run_dir).name or "gpwbpp-run", created_at=now_iso(), current_stage="created")

