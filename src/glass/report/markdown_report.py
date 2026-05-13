from __future__ import annotations

from pathlib import Path


def write_markdown_report(path: str | Path, title: str, lines: list[str]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("# " + title + "\n\n" + "\n".join(lines) + "\n", encoding="utf-8")

