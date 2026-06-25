"""Fetch recent GitHub activity worth posting about.

Pulls two kinds of signal from the public GitHub REST API:
  1. Merged pull requests authored by the user (including to other people's repos).
  2. The user's own repositories pushed to recently (excludes forks).

Each item is normalized into a small dict the drafting step can consume.
"""

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


def fetch_merged_prs(username: str, lookback_days: int, token: str | None) -> list[dict[str, Any]]:
    """Merged PRs authored by `username`, most recent first."""
    query = f"author:{username} is:pr is:merged"
    resp = requests.get(
        f"{API}/search/issues",
        headers=_headers(token),
        params={"q": query, "sort": "updated", "order": "desc", "per_page": 20},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()

    cutoff = _since(lookback_days)
    items: list[dict[str, Any]] = []
    for it in resp.json().get("items", []):
        closed = it.get("closed_at")
        if not closed:
            continue
        closed_dt = dt.datetime.fromisoformat(closed.replace("Z", "+00:00"))
        if closed_dt < cutoff:
            continue
        # repository_url looks like https://api.github.com/repos/OWNER/REPO
        repo_full = it.get("repository_url", "").split("/repos/")[-1]
        items.append(
            {
                "type": "merged_pr",
                "title": it.get("title", ""),
                "repo": repo_full,
                "url": it.get("html_url", ""),
                "body": (it.get("body") or "")[:1500],
                "date": closed,
            }
        )
    return items


def fetch_recent_repos(username: str, lookback_days: int, token: str | None) -> list[dict[str, Any]]:
    """The user's own (non-fork) repos pushed to within the lookback window."""
    resp = requests.get(
        f"{API}/users/{username}/repos",
        headers=_headers(token),
        params={"sort": "pushed", "direction": "desc", "per_page": 30},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()

    cutoff = _since(lookback_days)
    items: list[dict[str, Any]] = []
    for repo in resp.json():
        if repo.get("fork") or repo.get("archived"):
            continue
        pushed = repo.get("pushed_at")
        if not pushed:
            continue
        pushed_dt = dt.datetime.fromisoformat(pushed.replace("Z", "+00:00"))
        if pushed_dt < cutoff:
            continue
        items.append(
            {
                "type": "repo_update",
                "title": repo.get("name", ""),
                "repo": repo.get("full_name", ""),
                "url": repo.get("html_url", ""),
                "body": (repo.get("description") or "")[:500],
                "date": pushed,
                "language": repo.get("language"),
                "stars": repo.get("stargazers_count", 0),
            }
        )
    return items


def fetch_activity(username: str, lookback_days: int, token: str | None) -> list[dict[str, Any]]:
    """All notable activity, merged PRs first (they make the strongest posts)."""
    activity = fetch_merged_prs(username, lookback_days, token)
    activity += fetch_recent_repos(username, lookback_days, token)
    return activity
