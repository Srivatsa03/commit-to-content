"""arXiv source: recent papers in your categories, filtered by your interests."""

from __future__ import annotations

import datetime as dt
import xml.etree.ElementTree as ET
from typing import Any

import requests

API = "http://export.arxiv.org/api/query"
ATOM = "{http://www.w3.org/2005/Atom}"
TIMEOUT = 30


def fetch(
    categories: list[str],
    interests: list[str],
    lookback_days: int,
    max_results: int = 20,
    **_: Any,
) -> list[dict[str, Any]]:
    if not categories:
        return []

    query = " OR ".join(f"cat:{c}" for c in categories)
    resp = requests.get(
        API,
        params={
            "search_query": query,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": max_results,
        },
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    root = ET.fromstring(resp.text)

    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=lookback_days)
    interests_lc = [kw.lower() for kw in interests]
    items: list[dict[str, Any]] = []

    for entry in root.findall(f"{ATOM}entry"):
        title = (entry.findtext(f"{ATOM}title") or "").strip().replace("\n", " ")
        summary = (entry.findtext(f"{ATOM}summary") or "").strip().replace("\n", " ")
        url = (entry.findtext(f"{ATOM}id") or "").strip()
        published = (entry.findtext(f"{ATOM}published") or "").strip()

        if published:
            pub_dt = dt.datetime.fromisoformat(published.replace("Z", "+00:00"))
            if pub_dt < cutoff:
                continue

        # Keep only papers that match an interest keyword (if any interests are set).
        haystack = f"{title} {summary}".lower()
        if interests_lc and not any(kw in haystack for kw in interests_lc):
            continue

        items.append(
            {
                "source": "arxiv",
                "title": title,
                "summary": summary[:1500],
                "url": url,
                "date": published or None,
                "extra": {},
            }
        )
    return items
