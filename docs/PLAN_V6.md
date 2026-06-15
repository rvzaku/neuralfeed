# NeuralFeed — V6 Feedback Implementation Plan

> Source: `.dev-notes/app-feedback-v6.md`. Synthesized 2026-06-15.
> Status: **APPROVED, not yet implemented** — to be executed in a fresh session.
> Workflow: per `.dev-notes/CLAUDE.md`, plan-first; use ECC skills per task type
> (fastapi-patterns/review, react-patterns/review, tdd-workflow, security-review,
> make-interfaces-feel-better/motion-ui, refactor-clean). Ship in small phases,
> conventional commits, 80%+ backend coverage, security-scan before deploy.

## Decisions (from user, 2026-06-15)
1. **Recap:** "remove recap" refers to something not present in the codebase →
   treat as a **no-op**. **Keep** the "Today in AI" digest + daily email shipped
   this session.
2. **Hotness Index basis:** **cross-source velocity** — how many distinct sources
   carry a story and how fast it's spreading in the last 24–48h vs a baseline.
3. **Blog/newsletter traction:** **attempt to scrape view/read counts** where a
   platform exposes them (e.g. Medium claps, dev.to reactions, Substack where
   visible). Engineering rule: **never fabricate** — when a count isn't available,
   fall back to a social/discussion proxy (HN points, Reddit upvotes, cross-source
   mentions) or recency-only. No fake numbers.
4. **Sequencing:** persist this plan; implement in a **fresh session**, phases in
   order A → B → C → D → E, with F (aesthetic/security/optimization) woven through.

---

## Phase A — Quick removals & always-on smart ranking (low risk)
- Remove **"Suggest follow targets"** from Discover (`frontend/components/sources/FollowTargets.tsx`,
  usage in `frontend/app/sources/page.tsx` / discover).
- **Recap:** no-op (nothing to remove); confirm during implementation via grep.
- **Smart ranking always-on:** remove the `ranked` toggle from the UI
  (`frontend/components/feed/FeedView.tsx`, `app/discover/page.tsx`) and any
  mention in `app/settings/page.tsx`. Server keeps `ranked=true` default; do not
  expose a way to disable.
- **Topics off Discover:** Discover should not duplicate the Topics directory
  (Topics already has its own page). 
- **Discrete counts:** show "Showing N of M" (or similar finite framing) on Feed
  and Discover so the feed reads as precise, not "thrown at you."

Acceptance: no follow-targets UI; no ranked toggle anywhere; Discover has no topics
strip; both pages show a finite count.

## Phase B — Relevance, dedup & dynamic feed
- Strengthen **cross-source dedup** (`backend/app/services/dedupe.py`) to cut
  redundant near-duplicate articles.
- **Dynamic everywhere:** viewed items drop out of **Feed and Discover/search**
  (Feed already excludes per-user read ids via `feed._read_article_ids`; extend the
  same exclusion to Discover + search results).
- **Suppress off-preference items:** lean harder on learned `topic_weights` /
  `source_affinity` in the ranker so low-relevance items sink.

Acceptance: opening an article removes it from Feed and Discover; visibly fewer
duplicates; feed skews to learned preferences.

## Phase C — Traction & "why relevant" signals
- **Fix GitHub star batch** (`backend/app/fetchers/github_trending.py`,
  `services/traction.py`): correct current star totals + "stars today" velocity.
- **Per-source traction:** social → upvotes/comments; HN → points/comments;
  GitHub → stars + velocity + "tools gaining traction"; blogs/newsletters →
  scraped view/read counts where exposed, else social/discussion proxy, else
  recency-only (decision #3).
- **Dates:** always show original **publish / first-release** date and
  **traction-since-published**; never fetch/ingest time. (Model already stores
  `published_at`; audit all display paths.)
- **Richer previews/cards:** each item conveys *what it is + why it's useful to you
  + whether it's gaining traction* — not a bare model name. Use `context_line`
  (LLM "why this matters") more prominently; generate where missing.
- **Images:** render the source article's image when `image_url` is present
  (hotlinked only — never stored, per CLAUDE.md curator rule).

Acceptance: GitHub stars correct; every card shows publish date + a real traction
signal + a useful "why"; images show when available.

## Phase D — Hotness Index (flagship)
- **Compute** cross-source velocity per story/topic: distinct-source coverage and
  spread rate over 24–48h vs baseline (extends existing `dedupe.cross_source_buzz`).
- **Display** as a **color scheme** (e.g. cool→warm heat) on items and topics, not a
  raw number; include a legend/tooltip.
- **Emphasis tracking:** ensure embodied-AI/robotics and AI-agents topics are
  first-class in the heat computation and topic directory.
- **"What's hot right now"** surfacing so spikes (OpenClaw-style) are obvious.

Acceptance: a visible heat indicator that demonstrably spikes for a story blowing
up across multiple sources; robotics + agents tracked explicitly.

## Phase E — Intelligence & titles
- **Titles** (`backend/app/services/enricher.py`): describe what a repo/model *does
  and why it matters*; never raw slug/repo name. Strengthen prompt + fallback.
- **AI summary formatting** (`services/summarizer.py`): enforce clean structured
  markdown; eliminate the "copy-pasted from an LLM" feel.
- **Learning loop:** reinforce feedback → ranking; document the "smart brain decides
  what's relevant now" behavior.

Acceptance: no raw-slug titles; summaries render as polished structured briefs.

## Phase F — Aesthetic, security, optimization (cross-cutting)
- **Frontend polish + restrained animations** (ECC `make-interfaces-feel-better`,
  `motion-ui`): premium, consistent, *not* AI-looking. Respect
  `prefers-reduced-motion`. One shared motion primitive; subtle (<200ms) per
  CLAUDE.md.
- **Security pass:** `/ecc:security-review` + `/ecc:security-scan` before deploy;
  security is a core pillar.
- **Codebase optimization:** `/ecc:refactor-clean`; remove dead code; tighten hot
  paths.
- **LinkedIn:** improve ToS-safe sourcing (current: Google News proxy + RSSHub
  public-page bridge) without scraping private content.

Acceptance: app reads as premium/human-crafted; clean security scan; no dead code.

---

## Notes / constraints
- Curator rule stands: store metadata only; image URLs hotlinked, never stored;
  no full article text persisted.
- "Scrape view counts" (decision #3) is best-effort per platform with honest
  fallback — flag any source where it proves unreliable and disable that path
  rather than show misleading numbers.
- Front-page hero/Artifact redesign remains **dropped** (CLAUDE.md, 2026-06-15) —
  keep V5 premium-restraint direction; aesthetic work is polish within it.
