"""Content sources. Each module exposes a `fetch(...)` returning normalized items.

Normalized item schema:
  {
    "source":  "github" | "arxiv" | "hackernews" | "notes",
    "title":   str,
    "summary": str,            # description / abstract / note body
    "url":     str,            # may be "" for local notes
    "date":    str | None,     # ISO timestamp when known
    "extra":   dict,           # source-specific fields
  }
"""
