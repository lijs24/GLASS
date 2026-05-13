from __future__ import annotations

from contextlib import contextmanager
from time import perf_counter
from typing import Iterator


@contextmanager
def timer() -> Iterator[dict[str, float]]:
    state = {"elapsed_s": 0.0}
    start = perf_counter()
    try:
        yield state
    finally:
        state["elapsed_s"] = perf_counter() - start

