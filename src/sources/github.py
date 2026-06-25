"""GitHub source: recent merged PRs and your own updated repos."""

from __future__ import annotations

import datetime as dt
from typing import Any

import requests

API = "https://api.github.com"
TIMEOUT = 30


def _headers(token: str | None) -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _since(lookback_days: int) -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=lookback_days)


def fetch(username: str, lookback_days: int, token: str | None = None, **_: Any) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    cutoff = _since(lookback_days)

    # Merged PRs authored by the user (including to other people's repos).
    resp = requests.get(
        f"{API}/search/issues",
        headers=_headers(token),
        params={"q": f"author:{username} is:pr is:merged", "sort": "updated", "order": "desc", "per_page": 20},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    for it in resp.json().get("items", []):
        closed = it.get("closed_at")
        if not closed or dt.datetime.fromisoformat(closed.replace("Z", "+00:00")) < cutoff:
            continue
        repo_full = it.get("repository_url", "").split("/repos/")[-1]
        items.append(
            {
                "source": "github",
                "title": f"Merged PR: {it.get('title', '')}",
                "summary": (it.get("body") or "")[:1500],
                "url": it.get("html_url", ""),
                "date": closed,
                "extra": {"repo": repo_full, "kind": "merged_pr"},
            }
        )

    # The user's own (non-fork, non-archived) repos pushed to recently.
    resp = requests.get(
        f"{API}/users/{username}/repos",
        headers=_headers(token),
        params={"sort": "pushed", "direction": "desc", "per_page": 30},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    for repo in resp.json():
        if repo.get("fork") or repo.get("archived"):
            continue
        pushed = repo.get("pushed_at")
        if not pushed or dt.datetime.fromisoformat(pushed.replace("Z", "+00:00")) < cutoff:
            continue
        items.append(
            {
                "source": "github",
                "title": f"Project update: {repo.get('name', '')}",
                "summary": (repo.get("description") or "")[:500],
                "url": repo.get("html_url", ""),
                "date": pushed,
                "extra": {
                    "repo": repo.get("full_name", ""),
                    "kind": "repo_update",
                    "language": repo.get("language"),
                    "stars": repo.get("stargazers_count", 0),
                },
            }
        )
    return items
