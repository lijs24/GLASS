from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RuntimeConfig:
    backend: str = "auto"
    vram_budget_gb: float | None = None
    ram_budget_gb: float | None = None
    allow_partial: bool = False
    until_stage: str | None = None

