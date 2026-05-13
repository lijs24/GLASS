from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class MemoryBudget:
    ram_bytes: int | None = None
    vram_bytes: int | None = None

