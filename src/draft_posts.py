"""Draft a LinkedIn post from one GitHub activity item using Claude."""

from __future__ import annotations

import pathlib
from typing import Any

from anthropic import Anthropic

STYLE_PATH = pathlib.Path(__file__).resolve().parent.parent / "prompts" / "style.md"


def _load_style() -> str:
    return STYLE_PATH.read_text(encoding="utf-8")


def _activity_to_prompt(item: dict[str, Any]) -> str:
    if item["type"] == "merged_pr":
        return (
            "Activity type: a merged pull request.\n"
            f"Repository: {item['repo']}\n"
            f"PR title: {item['title']}\n"
            f"PR description:\n{item['body'] or '(no description)'}\n"
            f"Link: {item['url']}\n\n"
            "Write a post about shipping this fix or feature. If the repo is a well-known "
            "open-source project, lean into that. Focus on the problem solved and the judgment "
            "involved, not just the diff."
        )
    # repo_update
    extra = []
    if item.get("language"):
        extra.append(f"Primary language: {item['language']}")
    if item.get("stars"):
        extra.append(f"Stars: {item['stars']}")
    return (
        "Activity type: a personal project that was updated.\n"
        f"Project: {item['title']}\n"
        f"Description: {item['body'] or '(no description)'}\n"
        + ("\n".join(extra) + "\n" if extra else "")
        + f"Link: {item['url']}\n\n"
        "Write a post introducing or sharing progress on this project. Make the reader curious "
        "about what it does and why it is interesting."
    )


def draft_post(client: Anthropic, model: str, item: dict[str, Any]) -> str:
    """Return a single LinkedIn post draft as plain text."""
    style = _load_style()
    message = client.messages.create(
        model=model,
        max_tokens=700,
        system=style,
        messages=[{"role": "user", "content": _activity_to_prompt(item)}],
    )
    return "".join(block.text for block in message.content if block.type == "text").strip()
