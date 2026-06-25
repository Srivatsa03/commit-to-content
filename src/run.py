"""Orchestrator: fetch activity, draft posts, queue them, open a review Issue.

Env vars (see .env.example):
  ANTHROPIC_API_KEY   required
  GITHUB_TOKEN        required (auto-provided in Actions)
  GITHUB_USERNAME     default: Srivatsa03
  ANTHROPIC_MODEL     default: claude-sonnet-4-6
  LOOKBACK_DAYS       default: 14
  GITHUB_REPOSITORY   set automatically in Actions (OWNER/REPO); enables Issue creation
"""

from __future__ import annotations

import datetime as dt
import os
import pathlib
import re

from anthropic import Anthropic

from .draft_posts import draft_post
from .fetch_activity import fetch_activity
from .github_issue import create_issue

DRAFTS_DIR = pathlib.Path(__file__).resolve().parent.parent / "drafts"


def _slug(text: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return text[:50] or "draft"


def _today() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")


def main() -> int:
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if not anthropic_key:
        print("ANTHROPIC_API_KEY is not set. Add it as a repository secret.")
        return 1

    username = os.environ.get("GITHUB_USERNAME", "Srivatsa03")
    model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
    lookback = int(os.environ.get("LOOKBACK_DAYS", "14"))
    gh_token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")  # OWNER/REPO, only in Actions

    print(f"Scanning @{username}'s activity over the last {lookback} days...")
    activity = fetch_activity(username, lookback, gh_token)
    if not activity:
        print("No recent activity found. Nothing to draft.")
        return 0
    print(f"Found {len(activity)} item(s). Drafting with {model}...")

    client = Anthropic(api_key=anthropic_key)
    DRAFTS_DIR.mkdir(exist_ok=True)

    drafts: list[tuple[dict, str]] = []
    for item in activity:
        try:
            post = draft_post(client, model, item)
        except Exception as exc:  # keep going if one draft fails
            print(f"  ! failed to draft '{item['title']}': {exc}")
            continue
        drafts.append((item, post))

        fname = DRAFTS_DIR / f"{_today()}-{_slug(item['title'])}.md"
        fname.write_text(
            f"# Draft: {item['title']}\n\n"
            f"Source: {item['url']}\n\n"
            f"---\n\n{post}\n",
            encoding="utf-8",
        )
        print(f"  drafted: {fname.name}")

    if not drafts:
        print("No drafts produced.")
        return 0

    # Assemble one review Issue with every draft.
    if repo and gh_token:
        body_parts = [
            "Auto-generated LinkedIn drafts from your recent GitHub activity. "
            "Edit any you like, then copy-paste to LinkedIn. Close this issue when done.\n",
        ]
        for item, post in drafts:
            body_parts.append(
                f"### {item['title']}\n"
                f"Source: {item['url']}\n\n"
                f"```\n{post}\n```\n"
            )
        url = create_issue(
            repo=repo,
            token=gh_token,
            title=f"LinkedIn drafts — {_today()} ({len(drafts)})",
            body="\n".join(body_parts),
        )
        if url:
            print(f"Review issue created: {url}")
    else:
        print("GITHUB_REPOSITORY/token not set (local run). Drafts saved to drafts/ only.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
