"""Draft cross-platform content (LinkedIn, X thread, dev.to) for one item."""

from __future__ import annotations

import json
import pathlib
from typing import Any

from anthropic import Anthropic

STYLE_PATH = pathlib.Path(__file__).resolve().parent.parent / "prompts" / "style.md"

INSTRUCTIONS = (
    "Draft content for three platforms about the item below, following the voice guide. "
    "Return ONLY valid JSON (no markdown fences) with exactly these keys:\n"
    '  "linkedin": a single LinkedIn post, 60 to 130 words.\n'
    '  "x_thread": an array of 3 to 6 strings, each a tweet under 280 characters.\n'
    '  "devto":    a dev.to article outline: a title line, then 4 to 6 bullet points.\n'
    "Do not invent facts that are not in the item. If the item is someone else's work "
    "(an arXiv paper or a news story), write it as your take or summary, not as your own work."
)


def _load_style() -> str:
    return STYLE_PATH.read_text(encoding="utf-8")


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
    return text.strip()


def _item_context(item: dict[str, Any]) -> str:
    return (
        f"Source: {item['source']}\n"
        f"Title: {item['title']}\n"
        f"Details: {item['summary'] or '(none)'}\n"
        f"Link: {item['url'] or '(no link)'}"
    )


def draft_all_platforms(client: Anthropic, model: str, item: dict[str, Any]) -> dict[str, Any]:
    """Return {"linkedin": str, "x_thread": [str], "devto": str}."""
    message = client.messages.create(
        model=model,
        max_tokens=1500,
        system=_load_style(),
        messages=[{"role": "user", "content": f"{INSTRUCTIONS}\n\nITEM:\n{_item_context(item)}"}],
    )
    text = _strip_fences("".join(b.text for b in message.content if b.type == "text"))
    try:
        data = json.loads(text)
        return {
            "linkedin": str(data.get("linkedin", "")).strip(),
            "x_thread": [str(t).strip() for t in data.get("x_thread", []) if str(t).strip()],
            "devto": str(data.get("devto", "")).strip(),
        }
    except (json.JSONDecodeError, TypeError):
        # If JSON parsing fails, keep the raw text as the LinkedIn draft so nothing is lost.
        return {"linkedin": text, "x_thread": [], "devto": ""}


def render_markdown(item: dict[str, Any], drafts: dict[str, Any]) -> str:
    """Render one item's drafts as a markdown block (used for files and the review issue)."""
    parts = [
        f"## {item['title']}",
        f"Source ({item['source']}): {item['url'] or '(local note)'}\n",
        "### LinkedIn",
        drafts["linkedin"] or "(none)",
        "",
        "### X / Twitter thread",
    ]
    if drafts["x_thread"]:
        parts += [f"{i}. {t}" for i, t in enumerate(drafts["x_thread"], 1)]
    else:
        parts.append("(none)")
    parts += ["", "### dev.to outline", drafts["devto"] or "(none)", ""]
    return "\n".join(parts)
