from __future__ import annotations

from pathlib import Path

from glass.engine.state import read_run_state


def resume_summary(run_dir: str | Path) -> dict[str, object]:
    state = read_run_state(run_dir)
    return {
        "run": str(run_dir),
        "current_stage": state.get("current_stage"),
        "completed_stages": state.get("completed_stages", []),
        "resume_supported": state.get("resume_supported", False),
    }

