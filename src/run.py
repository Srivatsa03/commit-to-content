"""Orchestrator: gather multi-source candidates, curate, draft, queue, open a review Issue.

Env vars (see .env.example):
  ANTHROPIC_API_KEY   required
  GITHUB_TOKEN        required for GitHub source + Issue (auto-provided in Actions)
  GITHUB_USERNAME     default: Srivatsa03
  ANTHROPIC_MODEL     default: claude-opus-4-8
  LOOKBACK_DAYS       default: 14
  MAX_DRAFTS          default: 3
  INTERESTS           comma-separated keywords for arXiv/HN filtering
  ARXIV_CATEGORIES    comma-separated arXiv categories (e.g. cs.CL,cs.LG)
  GITHUB_REPOSITORY   set automatically in Actions (OWNER/REPO); enables Issue creation
"""

from __future__ import annotations

import datetime as dt
import os
import pathlib
import re

from anthropic import Anthropic

from .curate import curate
from .draft_posts import draft_all_platforms, render_markdown
from .github_issue import create_issue
from .sources import arxiv, github, hackernews, notes

DRAFTS_DIR = pathlib.Path(__file__).resolve().parent.parent / "drafts"


def _env(name: str, default: str) -> str:
    value = os.environ.get(name)
    return value if value else default


def _csv(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def _slug(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")[:50] or "draft"


def _today() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")


def gather(username, token, lookback, interests, categories) -> list[dict]:
    """Run every source, skipping any that error so one outage can't kill the run."""
    plan = [
        ("github", lambda: github.fetch(username, lookback, token)),
        ("arxiv", lambda: arxiv.fetch(categories, interests, lookback)),
        ("hackernews", lambda: hackernews.fetch(interests, lookback)),
        ("notes", lambda: notes.fetch()),
    ]
    items: list[dict] = []
    for name, fn in plan:
        try:
            found = fn()
            print(f"  {name}: {len(found)} item(s)")
            items += found
        except Exception as exc:
            print(f"  {name}: skipped ({exc})")
    return items


def main() -> int:
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if not anthropic_key:
        print("ANTHROPIC_API_KEY is not set. Add it as a repository secret.")
        return 1

    username = _env("GITHUB_USERNAME", "Srivatsa03")
    model = _env("ANTHROPIC_MODEL", "claude-opus-4-8")
    lookback = int(_env("LOOKBACK_DAYS", "14"))
    top_n = int(_env("MAX_DRAFTS", "3"))
    interests = _csv(_env("INTERESTS", "RAG,LLM evaluation,MLOps,Kubernetes,LLM security,vector search"))
    categories = _csv(_env("ARXIV_CATEGORIES", "cs.CL,cs.LG,cs.AI,cs.SE"))
    gh_token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")

    print(f"Gathering candidates (lookback {lookback}d, interests: {', '.join(interests)})...")
    items = gather(username, gh_token, lookback, interests, categories)
    if not items:
        print("No candidates found. Nothing to draft.")
        return 0

    client = Anthropic(api_key=anthropic_key)
    print(f"Curating top {top_n} of {len(items)} with {model}...")
    chosen = curate(client, model, items, top_n)

    DRAFTS_DIR.mkdir(exist_ok=True)
    blocks: list[str] = []
    for idx in chosen:
        item = items[idx]
        try:
            drafts = draft_all_platforms(client, model, item)
        except Exception as exc:
            print(f"  ! failed to draft '{item['title']}': {exc}")
            continue
        block = render_markdown(item, drafts)
        blocks.append(block)
        fname = DRAFTS_DIR / f"{_today()}-{item['source']}-{_slug(item['title'])}.md"
        fname.write_text(f"# Draft ({_today()})\n\n{block}", encoding="utf-8")
        print(f"  drafted: {fname.name}")

    if not blocks:
        print("No drafts produced.")
        return 0

    if repo and gh_token:
        body = (
            "Auto-generated cross-platform drafts from your GitHub, arXiv, Hacker News, and notes. "
            "Edit what you like, post the winners, close when done.\n\n" + "\n---\n".join(blocks)
        )
        url = create_issue(repo, gh_token, f"Content drafts — {_today()} ({len(blocks)})", body)
        if url:
            print(f"Review issue created: {url}")
    else:
        print("GITHUB_REPOSITORY/token not set (local run). Drafts saved to drafts/ only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
