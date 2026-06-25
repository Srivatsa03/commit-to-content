# commit-to-content

**Turn your GitHub activity into reviewed LinkedIn drafts, automatically.**

Most "LinkedIn automation" tools auto-post and auto-connect, which violates LinkedIn's terms and gets accounts restricted. This does the opposite: it watches what you actually ship on GitHub (merged PRs, new repos, releases), drafts LinkedIn posts in your voice with an LLM, and opens a **GitHub Issue for you to review and edit**. Publishing stays a human decision. No scraping, no bots, no ban risk.

It runs entirely on **GitHub Actions** (free), needs no server, and keeps a versioned content queue in the repo.

## Why human-in-the-loop

Auto-posting is a liability: off-tone posts go out under your name, and aggressive automation trips LinkedIn's anti-bot systems. Drafting is the hard part; clicking "post" is not. So this tool automates the draft and leaves the judgment to you. That single design choice is what makes it safe to run on your real account.

## How it works

```
   schedule / manual run
            │
            ▼
   fetch_activity.py ── GitHub REST API ──> recent merged PRs, new repos, releases
            │
            ▼
   draft_posts.py ──── Claude (Anthropic) + your style guide ──> post drafts
            │
            ├─> drafts/YYYY-MM-DD-*.md         (versioned content queue, committed back)
            └─> github_issue.py ──> one GitHub Issue with all drafts for review
                                         │
                                         ▼
                            you edit, then copy-paste to LinkedIn
```

## Setup (5 minutes)

1. **Use this repo** (it's yours, edit freely).
2. Add two repository secrets in **Settings → Secrets and variables → Actions**:
   - `ANTHROPIC_API_KEY` — from https://console.anthropic.com
   - *(`GITHUB_TOKEN` is provided automatically by Actions; nothing to add.)*
3. Optional repository **variables** (Settings → Variables) to tune behavior:
   - `GITHUB_USERNAME` (default: `Srivatsa03`)
   - `ANTHROPIC_MODEL` (default: `claude-sonnet-4-6`)
   - `LOOKBACK_DAYS` (default: `14`)
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

All voice and tone rules live in [`prompts/style.md`](prompts/style.md). Edit that file to change how the drafts read. It ships tuned for a build-in-public engineering voice: concrete, honest about metrics, no buzzwords, no fabrication.

## Tech

`Python` · `GitHub Actions` · `GitHub REST API` · `Anthropic Claude (Messages API)`

## A note on scope

This drafts and queues. It does not publish to LinkedIn, by design. If you ever want auto-publish, do it through LinkedIn's official Marketing API with the `w_member_social` scope and an approved app, never through browser automation or scraping.

## License

MIT
