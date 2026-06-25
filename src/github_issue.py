"""Open a single GitHub Issue containing the drafts, for human review."""

from __future__ import annotations

import requests

API = "https://api.github.com"
TIMEOUT = 30


def create_issue(repo: str, token: str, title: str, body: str) -> str | None:
    """Create an Issue on `repo` (OWNER/REPO). Returns the Issue URL, or None on failure."""
    resp = requests.post(
        f"{API}/repos/{repo}/issues",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
        },
        json={"title": title, "body": body, "labels": ["content-draft"]},
        timeout=TIMEOUT,
    )
    if resp.status_code == 201:
        return resp.json().get("html_url")
    print(f"Issue creation failed ({resp.status_code}): {resp.text[:300]}")
    return None
