"""Hacker News source: recent high-signal stories matching your interests."""

from __future__ import annotations

import datetime as dt
from typing import Any

import requests

API = "http://hn.algolia.com/api/v1/search_by_date"
TIMEOUT = 30


def fetch(
    interests: list[str],
    lookback_days: int,
    per_keyword: int = 2,
    min_points: int = 50,
    **_: Any,
) -> list[dict[str, Any]]:
    cutoff_ts = int((dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=lookback_days)).timestamp())
    items: list[dict[str, Any]] = []
    seen: set[str] = set()

    for kw in interests:
        resp = requests.get(
            API,
            params={
                "query": kw,
                "tags": "story",
                "numericFilters": f"created_at_i>{cutoff_ts},points>{min_points}",
                "hitsPerPage": per_keyword,
            },
            timeout=TIMEOUT,
        )
        if resp.status_code != 200:
            continue
        for hit in resp.json().get("hits", []):
            object_id = hit.get("objectID", "")
            url = hit.get("url") or f"https://news.ycombinator.com/item?id={object_id}"
            if url in seen:
                continue
            seen.add(url)
            created = hit.get("created_at")
            items.append(
                {
                    "source": "hackernews",
                    "title": hit.get("title", ""),
                    "summary": f"Trending on Hacker News ({hit.get('points', 0)} points) for '{kw}'.",
                    "url": url,
                    "date": created,
                    "extra": {"points": hit.get("points", 0), "keyword": kw},
                }
            )
    return items
