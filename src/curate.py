"""Let the model pick the most post-worthy items from all gathered candidates."""

from __future__ import annotations

import json
from typing import Any

from anthropic import Anthropic


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
    return text.strip()


def curate(client: Anthropic, model: str, items: list[dict[str, Any]], top_n: int) -> list[int]:
    """Return indices of the top_n items worth posting about, best first."""
    if len(items) <= top_n:
        return list(range(len(items)))

    listing = "\n".join(
        f"[{i}] ({it['source']}) {it['title']}: {it['summary'][:160]}" for i, it in enumerate(items)
    )
    prompt = (
        f"{listing}\n\n"
        f"You curate content for a build-in-public software and AI engineer. From the list above, "
        f"choose the {top_n} items that would make the strongest posts for an engineering audience. "
        "Prefer the engineer's own work (github, notes) and genuinely novel or surprising items over "
        "generic news. Return ONLY a JSON array of the chosen indices, best first, e.g. [3,0,7]."
    )
    message = client.messages.create(
        model=model,
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    text = _strip_fences("".join(b.text for b in message.content if b.type == "text"))
    try:
        chosen = json.loads(text)
        valid = [i for i in chosen if isinstance(i, int) and 0 <= i < len(items)]
        if valid:
            return valid[:top_n]
    except (json.JSONDecodeError, TypeError):
        pass
    # Fallback: GitHub/notes first, then the rest.
    order = sorted(range(len(items)), key=lambda i: items[i]["source"] not in ("github", "notes"))
    return order[:top_n]
