# commit-to-content

**A content agent that turns what you build, read, and notice into reviewed, multi-platform drafts.**

Most "LinkedIn automation" tools auto-post and auto-connect, which violates platform terms and gets accounts restricted. This does the opposite. It pulls from four signals of what you're actually doing, has an LLM pick the most post-worthy items and draft them for **LinkedIn, X, and dev.to** in your voice, then opens a **GitHub Issue for you to review and edit**. Publishing stays a human decision. No scraping, no bots, no ban risk.

It runs entirely on **GitHub Actions** (free), needs no server, and keeps a versioned content queue in the repo.

## Sources it watches

- **GitHub** — your merged PRs (including to other people's repos) and your own updated projects.
- **arXiv** — recent papers in categories you choose, filtered to your interest keywords.
- **Hacker News** — high-signal stories matching your interests.
- **Your notes** — drop raw ideas into [`notes/`](notes/) and they become drafts too.

This is the difference between "engineer who posts their own commits" and "engineer who tracks the field." The second one builds reach.

## Why human-in-the-loop

Auto-posting is a liability: off-tone posts go out under your name, and aggressive automation trips anti-bot systems. Drafting is the hard part; clicking "post" is not. So this automates the draft and leaves the judgment to you. That single design choice is what makes it safe to run on your real accounts.

## How it works

```
  GitHub PRs/repos ─┐
  arXiv papers ─────┤
  Hacker News ──────┼─> curate (Claude picks the top N most post-worthy)
  your notes/ ──────┘                     │
                                          ▼
                         draft per platform (Claude + your style guide)
                                          │
        drafts/*.md (versioned queue) <───┤───> one GitHub Issue with every draft
                                          ▼
                    LinkedIn post · X thread · dev.to outline  (you edit, then post)
```

## Setup (5 minutes)

1. **Use this repo** (it's yours, edit freely).
2. Add one repository secret in **Settings → Secrets and variables → Actions**:
   - `ANTHROPIC_API_KEY` — from https://console.anthropic.com
   - *(`GITHUB_TOKEN` is provided automatically by Actions.)*
3. Optional repository **variables** to tune behavior (all have defaults):
   - `GITHUB_USERNAME` (`Srivatsa03`), `ANTHROPIC_MODEL` (`claude-opus-4-8`), `LOOKBACK_DAYS` (`14`), `MAX_DRAFTS` (`3`)
   - `INTERESTS` (comma-separated keywords) and `ARXIV_CATEGORIES` (e.g. `cs.CL,cs.LG,cs.AI,cs.SE`)
4. Enable Actions, then run it: **Actions → draft-posts → Run workflow**. Check the new Issue.

It also runs automatically every Monday at 09:00 UTC.

## Run it locally

```bash
cp .env.example .env        # fill in ANTHROPIC_API_KEY and a GITHUB_TOKEN
pip install -r requirements.txt
python -m src.run
```

Drafts land in `drafts/`. (Local runs skip Issue creation unless `GITHUB_REPOSITORY` is set.)

## Make it sound like you

All voice and tone rules live in [`prompts/style.md`](prompts/style.md). Edit that file to change how every draft reads. It ships tuned for a build-in-public engineering voice: concrete, honest about metrics, no buzzwords, no fabrication.

## Architecture

```
src/
  sources/        one module per signal (github, arxiv, hackernews, notes)
  curate.py       LLM ranks all candidates, returns the best N
  draft_posts.py  LLM drafts LinkedIn + X + dev.to for one item
  github_issue.py opens the review issue
  run.py          orchestrates: gather -> curate -> draft -> queue -> issue
```

Adding a new source is one file: expose a `fetch(...)` that returns the normalized item schema documented in `src/sources/__init__.py`, then add it to the gather plan in `run.py`.

## Tech

`Python` · `GitHub Actions` · `Anthropic Claude (Messages API)` · GitHub / arXiv / Hacker News APIs

## A note on scope

This drafts and queues. It does not publish to any platform, by design. If you ever want auto-publish, do it through a platform's official API with the right scopes and an approved app, never through browser automation or scraping.

## License

MIT
