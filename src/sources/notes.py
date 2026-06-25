"""Notes source: raw ideas you drop into the notes/ folder become post candidates."""

from __future__ import annotations

import pathlib
from typing import Any

NOTES_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / "notes"


def _title_from(text: str, fallback: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("#"):
            return line.lstrip("#").strip()
        if line:
            return line[:80]
    return fallback


def fetch(**_: Any) -> list[dict[str, Any]]:
    if not NOTES_DIR.exists():
        return []
    items: list[dict[str, Any]] = []
    for path in sorted(NOTES_DIR.glob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            continue
        items.append(
            {
                "source": "notes",
                "title": _title_from(text, path.stem),
                "summary": text[:1500],
                "url": "",
                "date": None,
                "extra": {"file": path.name},
            }
        )
    return items
