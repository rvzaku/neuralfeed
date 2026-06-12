# Plan: NeuralFeed V4 — Full Coverage, Deep Summaries, Editorial Redesign

**Source docs**: `app-feedback-v2.md`, `ideas-v2.md` (V4 section), `CLAUDE.md`
**Date**: 2026-06-12 (replaces the V1 greenfield plan, which shipped)
**Complexity**: Large (≈4 working sessions)
**Status**: PENDING APPROVAL — no implementation until confirmed

---

## Summary

V4 makes every content bucket actually deliver content (the current refresh dies before reaching most of the 50 sources), adds 10-minute deep summaries alongside the existing 1-minute ones, guarantees a preview on every card, hardens Reddit/X and scopes LinkedIn honestly, and replaces the frontend with an editorial, mobile-first design that does not read as AI-generic. Throughout, the codebase is restructured to enforce strict separation of concerns in both backend layers and frontend component architecture.

Live state driving this plan (prod health check, 2026-06-12): ~17/50 sources `ok`; all newsletters, podcasts, and most company-blog RSS never fetched; 3 Reddit subs 429-rate-limited; X-via-Nitter working (125 items); Conferences/Products/Funding buckets have zero sources; LinkedIn absent.

---

## Requirements Traceability (app-feedback-v2.md, re-read 2026-06-12)

| # | Feedback requirement (verbatim intent) | Covered by | Status |
|---|---|---|---|
| R1 | Not showing content from all buckets in ideas.md; only some content | Phase 0 (resumable refresh) + Phase 1 (conference/product sources) | SHIPPED — prod soak ongoing |
| R2 | Frontend not as wanted | Phase 3 (editorial overhaul) | pending |
| R3 | Summary too small — want proper 10-minute summary | Phase 2 (deep summaries) | in progress |
| R4 | All articles must have a preview | Phase 2 (ingest snippet backfill + summary sheet on every card) | in progress |
| R5 | Reddit working | Phase 0 (backoff/pacing 6s) | SHIPPED — monitoring 429s |
| R6 | X.com working | twitter-nitter live (125 items); health-flagged in Sources | SHIPPED |
| R7 | LinkedIn working | Curated manual targets via watched_accounts (`platform='linkedin'`); no ToS-violating scraper — documented in SOURCES.md | SHIPPED (bounded) |
| R8 | Really user-friendly, mobile responsive, non-AI-generic, easy navigation, best UI/UX | Phase 3 (3a–3e) | pending |
| R9 | Refer to ECC skills | a11y + interface-polish + react-review passes wired into Phase 3e | pending |
| R10 | Topic weights auto-adjusted | Phase 2b — feedback_service nudges weights ±0.1 clamped | SHIPPED |
| R11 | Topic weights manually adjustable | API exists (PUT /preferences/topic_weights); Settings sliders in Phase 3 | partial |
| R12 | Smart ranking enabled | Phase 2b — ranked=true default | SHIPPED |
| R13 | Professionally made, desktop + mobile friendly | Phase 3 breakpoints + polish gates (Lighthouse >90) | pending |

## Architecture & Separation of Concerns (target state)

### Backend layering (rule: dependencies only point downward)

```
api/v1/*     ← HTTP only: parse request, call ONE service function, shape response.
               No SQLAlchemy queries, no business logic, no datetime math.
schemas/*    ← Pydantic request/response models. No logic.
services/*   ← ALL business logic. Owns transactions. Never imports from api/.
fetchers/*   ← Pure I/O adapters: fetch from one platform, return list[RawItem].
               NO DB access, NO ingestion logic. Errors raised, not swallowed.
models/*     ← SQLAlchemy models + pure helpers (hashing). No I/O.
core/*       ← config, db session, time, deps, scheduler wiring. No domain logic.
```

**Known violations to fix during V4** (each phase fixes what it touches):

| Violation | Fix |
|---|---|
| `api/v1/feed.py` builds queries + calls ranker inline | extract `services/feed_service.py`; route becomes thin |
| `api/v1/feedback.py` computes signal_score inline | extract `services/feedback_service.py` |
| `api/v1/refresh.py` owns the refresh loop | extract `services/refresh_orchestrator.py` (Phase 0) |
| Fetchers return inconsistently-shaped dicts | `RawItem` TypedDict contract in `fetchers/base.py`; only ingest parses dates |

### Frontend layering

```
app/*                ← routes/layouts only; data via hooks; no inline fetch calls.
components/ui/*      ← dumb primitives (Button, Chip, Sheet, Skeleton…). No data access.
components/<feature>/* ← feature components; data via props/hooks only.
hooks/*              ← ALL server-state access; one hook per resource
                       (useFeed, useStories, useSummary, useSources).
lib/api.ts           ← the only axios surface. lib/types.ts mirrors backend schemas.
```

**Violations to fix**: components importing `lib/api` directly move behind hooks; design tokens consolidated into `globals.css` + Tailwind config as the single source.

---

## Patterns to Mirror

| Category | Source | Pattern |
|---|---|---|
| Fetcher shape | `backend/app/fetchers/arxiv.py` | async callable returning items; registered in `fetchers/registry.py` `FETCHER_MAP` |
| Service entry | `backend/app/services/fetch_runner.py` | single entry point, structlog, health recorded on Source row |
| Error isolation | `backend/app/services/ingest.py:80` | `db.begin_nested()` savepoint per item |
| Time handling | `backend/app/core/time.py` | naive UTC everywhere; `utcnow()` / `to_naive_utc()` only — never `datetime.now(timezone.utc)` near the DB |
| Migrations | `backend/alembic/versions/0004_article_ai_summary.py` | one concern per revision, dialect-neutral (works on SQLite + Postgres) |
| Tests | `backend/tests/` | pytest-asyncio; SQLite in-memory integration; HTTP mocked in unit tests |
| Hooks | `frontend/hooks/useFeed.ts` | resource hook owning fetch+state |
| Summary flow | `backend/app/services/summarizer.py` | provider Protocol (groq/ollama), transient extraction, cached on Article |

---

## Phase 0 — Fetch Reliability & Refresh Orchestration

**Problem**: `POST /refresh` runs ~50 sources sequentially inside one Starlette background task. Render free-tier restarts kill it mid-list; the same front-of-list sources always win; Reddit 429s from burst requests. This is the root cause of "not showing content from all buckets."

### Files

| File | Action | Why |
|---|---|---|
| `backend/app/services/refresh_orchestrator.py` | CREATE | batched concurrency, resumability, progress tracking |
| `backend/app/api/v1/refresh.py` | UPDATE | thin route → orchestrator; add `GET /refresh/status` |
| `backend/app/fetchers/base.py` | UPDATE | `RawItem` TypedDict + shared `fetch_with_backoff()` (httpx; exp backoff 1s/4s/15s; honors `Retry-After`; raises `FetchError` after 3 tries) |
| `backend/app/fetchers/reddit.py` | UPDATE | shared backoff; 2.5s spacing between subs; one module-level descriptive User-Agent; JSON→RSS fallback kept |
| `backend/app/core/scheduler.py` | UPDATE | wider stagger + jitter; skip source if fetched within 50% of its interval |
| `backend/app/models/source.py` | UPDATE (migration 0005) | add `fetch_attempted_at` for resume ordering |
| `backend/scripts/check_sources.py` | UPDATE | non-zero exit if any enabled source errored; prints table |
| `backend/tests/test_refresh_orchestrator.py` | CREATE | TDD: batching, per-source isolation, resume ordering |

### Tasks

1. **`RawItem` contract** — `title, url, author?, summary?, published_at? (datetime|iso str), trending_score?`; all 9 fetchers conform. *Validate*: existing fetcher tests green.
2. **`fetch_with_backoff()`** — *Validate*: unit test with mocked 429→429→200 sequence.
3. **Orchestrator** — `refresh_all()`: orders enabled sources by `fetch_attempted_at` ASC NULLS FIRST; `asyncio.Semaphore(3)`; stamps `fetch_attempted_at` *before* fetching so a crash still advances the cursor next run; each source in its own session + try/except; in-memory progress for `GET /refresh/status`. *Validate*: test that a second call (simulated restart) starts with previously unattempted sources.
4. **Reddit hardening** — spacing + backoff + UA; order rotation falls out of task 3. *Validate*: live prod, all reddit-* `ok`.
5. **Prod soak** — deploy, run refresh twice, `check_sources.py` against prod: zero errors, zero never-fetched among enabled.

**Acceptance**: `/api/v1/sources/health` — every enabled source `ok` with count > 0, or `enabled:false` with a note.

---

## Phase 1 — Bucket Completion

**Problem**: Conferences, Products, Funding have no sources; People has no UI surface; LinkedIn absent.

### Files

| File | Action | Why |
|---|---|---|
| `backend/alembic/versions/0006_seed_v4_sources.py` | CREATE | data migration inserting new Source rows (never delete existing) |
| `backend/app/fetchers/registry.py` | UPDATE | register new sources |
| `backend/app/fetchers/rss.py` | UPDATE | per-source category mapping |
| `backend/app/models/watched_account.py` | UPDATE (0005/0006) | allow `platform='linkedin'`; add `profile_url` |
| `backend/app/services/topic_tagger.py` | UPDATE | funding keywords (`raises`, `series A/B`, `acquisition`, `valuation`) |
| `docs/SOURCES.md` | UPDATE | registry matches DB; LinkedIn stance documented |
| `backend/tests/test_new_sources.py` | CREATE | each new fetcher returns ≥1 normalized item (mocked HTTP) |

### New sources

| id | bucket | access |
|---|---|---|
| `conf-neurips/-icml/-iclr/-cvpr/-acl` | conferences | news RSS where available, else headline scrape; weekly |
| `rss-techcrunch-ai`, `rss-venturebeat-ai` (exist, never fetched) | products/funding | unblocked by Phase 0; funding via topic tags |
| `hf-spaces-trending` | products | HF API |
| `producthunt-ai` | products | RSS (AI topic) |
| LinkedIn | people/social | **manual curated only**: watched_accounts with `platform='linkedin'` + `profile_url`; UI links out. No scraping (ToS). |

People bucket = feed filter over articles whose author/handle matches a watched account + Accounts tab in Sources (extends existing `api/v1/accounts.py`).

**Acceptance**: every bucket chip returns >0 items after full refresh (LinkedIn shows curated link-out targets).

---

## Phase 2b — Smart Ranking & Adaptive Topic Weights (added 2026-06-12 from updated app-feedback-v2.md)

**Requirement**: topic weights auto-adjust from thumbs up/down, are manually adjustable, and smart ranking is enabled.

Existing foundation: `services/ranker.py` already scores by recency/source-signal/topic-weights/trending/feedback and reads `topic_weights` + `muted_sources` from UserPreference. Gaps:

| File | Action | Why |
|---|---|---|
| `backend/app/services/feedback_service.py` | CREATE | `apply_feedback()`: sets article feedback, logs FeedbackLog, recomputes source signal_score (moved out of route — SoC), and **nudges topic_weights** ±0.1 per article tag (clamped [-1.0, 2.0], "general" excluded) |
| `backend/app/api/v1/feedback.py` | UPDATE | thin route → `apply_feedback()` |
| `backend/app/api/v1/feed.py` | UPDATE | `ranked` defaults to **True** (smart ranking on) |
| `backend/tests/services/test_feedback_service.py` | CREATE | TDD: weight nudge up/down, clamping, signal_score recompute |
| Frontend (Phase 3 settings) | UPDATE | Topic-weight sliders in Settings reading/writing `PUT /preferences/topic_weights`; "ranked" already wired via useFeed |

Manual adjustment API already exists (`PUT /api/v1/preferences/{key}`); Phase 3 adds the Settings UI sliders.

**Acceptance**: thumbs-up on an LLM-tagged article raises `topic_weights["llm"]`; weights clamp; feed default order is ranked; manual PUT overrides persist.

## Phase 2 — Deep Summaries (10-minute read) + Preview Guarantee

### Files

| File | Action | Why |
|---|---|---|
| `backend/app/services/summarizer.py` | UPDATE | `mode: "quick"|"deep"`; deep prompt → sectioned markdown ~1,500–2,000 words (Context · What's new · How it works · Results · Why it matters · Limitations · Who should care); source-type-aware extraction: arXiv abs page, Reddit post + top comments (`.json`), GitHub README (raw), blogs via trafilatura |
| `backend/app/models/article.py` | UPDATE (migration 0007) | `ai_deep_summary: Text?`, `ai_deep_summary_at` |
| `backend/app/api/v1/articles.py` | UPDATE | `GET /articles/{id}/summary?mode=deep` — cached-or-generate |
| `backend/app/schemas/article.py` | UPDATE | summary schema: `mode`, `reading_minutes` |
| `backend/app/services/ingest.py` | UPDATE | preview guarantee: backfill `summary` snippet when source provides none |
| `backend/tests/test_summarizer_deep.py` | CREATE | TDD per source type; provider mocked |

Data rule preserved: source text fetched transiently, never stored; only the derivative summary is cached.

**Acceptance**: deep summary renders for an arXiv paper, Reddit thread, GitHub repo, and blog post; quick mode unchanged; no card without a preview snippet; all tests green.

---

## Phase 3 — Frontend Overhaul (editorial, mobile-first)

Direction: digital-newspaper feel. Serif display via `next/font` (Newsreader or Source Serif) + humanist sans body; warm paper-neutral palette; one restrained accent (deep red or ink blue); no gradients, no glassmorphism, no emoji décor; strong typographic hierarchy and rules/dividers; dark mode = ink-on-charcoal, not inverted gray.

### 3a — Design system
- `frontend/app/globals.css` + `tailwind.config.ts` REWRITE: palette as CSS vars (light+dark), type scale, spacing, small radii (editorial, not pill-everything).
- `components/ui/` CREATE primitives: `Button`, `Chip`, `Sheet`, `Skeleton`, `EmptyState`, `Kicker`; keep `SourceBadge`.

### 3b — Feed
- `FeedView.tsx` REWRITE: story-first bounded digest ("Today" → "Earlier this week"), "You're caught up ✓" terminal state, explicit "Show more" (no infinite scroll by default).
- `FeedCard.tsx` / `StoryCard.tsx` REWRITE: kicker (bucket), serif headline, snippet (guaranteed by Phase 2), badge + relative time + reading-time, whole-card tap → summary sheet, thumbs/bookmark as quiet icon actions.

### 3c — Summary sheet
- `SummarySheet.tsx` REWRITE: opens instantly with quick summary (skeleton while generating); "Read the 10-minute brief" expander loads deep summary as typographic markdown; sticky "Read at source →" primary action; error → snippet fallback.

### 3d — Navigation & filters
- `MobileNav.tsx`: 4 tabs (Feed/Discover/Sources/Settings), ≥44px targets.
- `FilterBar.tsx`: scrollable bucket chips, active-filter count badge + one-tap clear.
- `FilterDrawer.tsx`: advanced dimensions (topic, time, quality, read, feedback); `SavedViewSwitcher` for presets.
- New `hooks/useSummary.ts`, `useStories.ts`, `useSources.ts`; remove all direct `lib/api` imports from components.

### 3e — Polish & review
- Skeletons everywhere; transitions <200ms; designed empty/error states.
- `/ecc:frontend-a11y` + `/ecc:make-interfaces-feel-better` passes; react-reviewer on the diff.
- Verify 360px / 768px / 1280px, dark+light; Lighthouse mobile >90.

**Acceptance**: smoke tests for rewritten components pass; `bun run build` green; breakpoint checklist done; no component imports `lib/api` directly.

---

## Phase 4 — Docs, Security, Deploy

1. `CLAUDE.md` UPDATE: hosting = Render (not Railway); refresh architecture (orchestrator + APScheduler); deep-summary data rule; LinkedIn stance; new buckets in source table.
2. `docs/SOURCES.md` + `docs/ROADMAP.md` sync; mark superseded V3 bullets in `ideas-v2.md`.
3. Security: `/ecc:security-scan`; pre-push secret grep over the diff; `.env.example` placeholder-only. (2026-06-12: leaked Groq key found in commit `4507670`, removed from tip — **user must revoke at console.groq.com and rotate in Render**.)
4. Deploy (Render + Vercel auto); run full refresh twice; `check_sources.py` green against prod; manual E2E on phone-width: browse every bucket, open quick + deep summary, link out.

---

## Validation (run before every push)

```bash
cd backend && ./.venv/bin/python -m pytest -q              # all green; coverage ≥80% on services/fetchers
cd frontend && bun run build && bun test                   # build + component tests
cd backend && ./.venv/bin/python scripts/check_sources.py  # post-deploy, against prod
git diff origin/main | grep -nE "gsk_|sk-[A-Za-z0-9]{20}|ghp_|github_pat_|AKIA|://[^/]+:[^@]+@" && echo LEAK || echo clean
```

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Reddit 429 persists from Render shared IP | Medium | backoff + spacing; per-sub RSS fallback; lower frequency last resort |
| Nitter instance death (X bucket dark) | High over time | instance rotation list + health flag in Sources UI |
| LinkedIn expectations vs ToS | High | curated manual targets only; documented |
| Groq limits on deep summaries | Low | on-demand + cached; provider swap via env |
| Render restart mid-refresh | High | resumable orchestrator (Phase 0) |
| Redesign scope creep | Medium | 3a–3e ordered, individually shippable |

## Execution order & commits

Phases ship 0→4. Each task is its own conventional commit (`feat(refresh): …`, `feat(sources): …`, `feat(summary): …`, `feat(ui): …`, `docs: …`, `test: …`). Deploy + prod-validate at the end of each phase, not only at the end.

## Acceptance (overall)

- [ ] Every enabled source healthy; every bucket non-empty in the UI
- [ ] Quick + deep summaries across all source types; every card has a preview
- [ ] Reddit stable; X monitored; LinkedIn curated targets live
- [ ] Editorial UI shipped, mobile-first, dark-mode parity, Lighthouse mobile >90
- [ ] SoC rules hold: api thin, services own logic, fetchers pure I/O, components behind hooks
- [ ] Coverage ≥80% on services/fetchers; no secrets in any pushed diff
- [ ] CLAUDE.md, SOURCES.md, ROADMAP.md updated

---

# Phase 3 — Multi-User & Production (planned 2026-06-12)

Status of CLAUDE.md Phase 3 items: 3.2 is largely done (Render backend + Neon Postgres + Vercel frontend, env-based config). Remaining: 3.1 auth, CI/CD, 3.3 rate limiting + monitoring.

## Increment 1 (this sprint)

### 3.1a Authentication core (backend)
- `User` model (`users` table): id (uuid hex), email unique, password_hash, created_at. Migration 0007.
- Password hashing: stdlib `hashlib.scrypt` + per-user salt (no new heavy deps).
- JWT (HS256) via `pyjwt`; settings: `JWT_SECRET`, `JWT_EXPIRES_MINUTES` (default 7d), `AUTH_REQUIRED` (default false → existing single-user deploy keeps working until flipped).
- `app/services/auth_service.py` — register/authenticate/token issue+verify.
- `app/api/v1/auth.py` — POST /auth/register, POST /auth/login, GET /auth/me.
- `require_user` dependency applied to write endpoints when AUTH_REQUIRED=true.

### 3.3a Rate limiting
- In-memory sliding-window limiter middleware (per-IP): 10/min on /auth/*, 60/min on other write methods. Adequate for single-instance Render; swap to Redis-backed at scale.

### CI/CD
- `.github/workflows/ci.yml`: backend pytest on 3.12; frontend typecheck + vitest via bun.

### Frontend
- Token storage + axios Authorization interceptor in `lib/api.ts`.
- `/login` page (login + register form). Logout clears token.

## Increment 2 (deferred)
- Per-user article state (`user_article_state`: user_id, article_id, is_read, is_bookmarked, feedback) and user-scoped preferences; OAuth providers; Sentry; Lighthouse audit.

---

# V4 Frontend Redesign — "Vibrant app-like" (2026-06-12, user-selected direction)

User feedback (app-feedback-v2.md): not user-friendly enough, looks AI-generic, must be mobile + desktop friendly, easy navigation, distinctive. Direction chosen via review: vibrant/app-like — gradient accents, large radius, bold topic colors, lively motion (Spotify/iOS feel).

## Token layer
- New palette: light = clean near-white + vivid indigo-violet primary with gradient (indigo→fuchsia); dark = deep blue-black, same gradient brightened.
- Radius 1rem base; colored shadows on hover; per-topic accent colors kept but boldened.
- Display font: Bricolage Grotesque (replaces Newsreader serif var — headlines go bold grotesque, kills the generic-AI look).

## Components
- MobileNav → floating pill dock with active-tab highlight + spring motion.
- Header → gradient wordmark, rounded search.
- FeedCard/StoryCard → rounded-2xl, hover lift, topic emoji chips, 🔥 trending badge.
- FilterBar → chunky chips, gradient active state.
- Skeletons → note about free-tier cold start ("waking the server…") so empty feed reads as loading, not broken.

## Reliability (root cause of "empty feed")
- Render free instance sleeps → scheduler stops + first load times out. Fix: GitHub Actions keepalive ping every 10 min (.github/workflows/keepalive.yml) + manual refresh triggered.

---

# Feedback-v2 round 2 (2026-06-12, lines 17-21 of app-feedback-v2.md)

## A. Infinite scroll (frontend)
- `useInfiniteFeed` (useInfiniteQuery over /api/v1/feed pages) for the "All items" view.
- IntersectionObserver sentinel triggers next page; digest stays finite by design (that's its differentiator).

## B. Share links
- Share button on FeedCard actions + SummarySheet footer: Web Share API on mobile, clipboard-copy fallback on desktop ("Link copied").
- Shares the original article URL (NeuralFeed is a curator — link out). Topic/filter views are already shareable URLs (e.g. /?topic=llm).

## C. Security hardening (backend)
- Security headers middleware: HSTS, X-Content-Type-Options, X-Frame-Options DENY, Referrer-Policy, no-store on API responses.
- Fail-fast guard: refuse AUTH_REQUIRED=true with the default JWT secret.
- CORS tightened: explicit methods/headers instead of "*".
- `ALLOW_REGISTRATION` flag (default true) — set false in Render after creating your account to close signup.
- Existing: PBKDF2 600k, JWT HS256, per-IP rate limiting, no secrets in repo, input sanitization in fetchers.

## Deferred (needs user/credentials or separate sprint)
- LinkedIn/X sources (Phase 2.2 feasibility — X API tier, LinkedIn ToS), Reddit API credentials for richer briefs, daily auto-briefing differentiator.

## Round 3 (feedback line 25): login-first gating
- AuthGuard in root layout: no stored token → immediate /login redirect (no API-401 wait, no content flash).
- 401 responses clear the stored session (expired/tampered JWT) before redirect; no react-query retries on 401.
- AuthZ model: per-user data scoping server-side from the JWT sub claim (user_article_state, namespaced prefs); HS256 signed tokens, 7-day expiry, PBKDF2-600k passwords, rate-limited auth endpoints, registration kill-switch.

## Round 4 (feedback line 27): professional auth experience
- Login page rebuilt: brand glow backdrop, sign-in/register pill toggle, icon inputs, show/hide password, confirm-password on register, inline alert errors, gradient CTA.
- Settings → Account section: signed-in email + sign out (clears session, returns to /login).

---

# V5 — Premium restraint redesign (2026-06-12, app-feedback-v3.md)

User verdict on V4: gradients read AI-generic/low-effort; wants premium, human-crafted.
Direction: Linear/Stripe/Vercel restraint — restraint IS the premium signal.
- Tokens: neutral ink-on-paper, ONE flat refined-indigo accent (primary actions/active states only), true-neutral dark mode, radius 10px.
- All gradients removed; active states are flat ink pills (bg-foreground/text-background); CTAs ink buttons.
- Typography: single clean grotesk (Geist) everywhere; Bricolage display face dropped; weight+tracking carry hierarchy.
- Hover: hairline border emphasis + 1px shadow — no lift, no glow. Flourishes (🔥, ✦) removed.

---

# V6 — Apple News / Artifact full restructure (2026-06-12, user-selected)

North star: a personal *front page*, journalistic not techy. Editor-arranged hierarchy:
one dominant top story, then themed sections. Images where available (hotlinked URLs
only — CLAUDE.md forbids storing image files; storing the og:image URL is metadata).

## Phase A — Backend: article preview images
1. Migration 0009: `articles.image_url TEXT NULL`.
2. Capture at ingest (no extra requests):
   - Reddit fetcher: `preview.images[0].source.url` / `thumbnail` from the JSON payload.
   - RSS fetcher: `media:content` / `media:thumbnail` / first `enclosure` image.
3. Lazy enrichment: the summarizer already fetches the article page — extract
   `og:image` there and cache onto the row (covers blogs/arXiv on first open).
4. Expose `image_url` in ArticleOut + story payloads (lead image = lead article's).

## Phase B — Frontend: front-page restructure
1. **Front page (feed)**:
   - Masthead row: "For You" + dateline (e.g. "Thursday, June 12"), refresh + search.
   - **Top Story hero**: largest/most-trending story cluster — full-width block,
     image (if any) above, 28-32px bold headline, summary line, "N related items
     from M sources" footer. Tap → reading view.
   - **Sections**: remaining stories grouped by dominant topic into named sections
     ("Large Language Models", "Open Source", "Research", "Industry & Funding", …).
     Each section: small-caps rule header + 2-4 compact items (thumbnail right,
     headline left, source·time metadata). No uniform card grid anywhere.
   - End: quiet "You're caught up" dateline rule.
2. **Reading view**: story tap opens a full-screen article reader (mobile full-page,
   desktop centered overlay): headline block → image → 10-min brief (default) with
   1-min toggle → related items list → actions (share/save/feedback) as a bottom bar.
3. **List view ("All items")**: Artifact-style rows — thumbnail right, headline +
   metadata left, hairline dividers; infinite scroll retained.
4. **Typography**: Geist, headline-weight-driven: hero 28-32/700 tight, section
   items 16/600, metadata 12/500 muted, small-caps section labels.
5. **Color**: keep V5 ink-neutral tokens (they fit Apple News); accent only for
   small "live" details (unread dot, section label hover).

## Phase C — Cleanup
- Remove now-unused digest/all pill toggle from front page (All items moves to a
  text link under the caught-up rule + stays a URL state).
- Smoke tests updated; SOURCES.md untouched; coverage maintained.

## Acceptance
- Front page shows hero + ≥2 themed sections with real data; images render when
  image_url present and never break layout when absent.
- Reading flow: front page → reader → back, one tap each way, mobile and desktop.
- No stored image files; only URLs hotlinked with referrerpolicy + lazy loading.

---

# V6.1 — Image discipline addendum (2026-06-12, supersedes V6 image notes)

Core tension: images raise scannability and warmth, but NeuralFeed's identity is
signal-over-noise. Resolution: **images are typographic furniture, never content**.
The page must work identically with zero images; an image may make one story easier
to recognize, never louder.

## Where images appear (exhaustive — nowhere else)
1. **Top Story hero — one image per page, max.** Full-width, fixed 16:9 crop above
   the hero headline. This is the only "large" image in the entire app.
2. **Section rows & All-items rows — small fixed thumbnail**, 64×64 (mobile) /
   72×72 (desktop), right-aligned, rounded-lg, object-cover. Constant size whether
   the source image is a meme or a paper figure — uniformity kills visual noise.
3. **Reader view — single header image** under the headline, same 16:9 crop,
   only when the article has one. Never inline images inside the brief.

## Where images never appear
- No images in the summary/brief body, no galleries, no avatars, no source logos
  as images (SourceBadge stays typographic), no video embeds, no GIF playback
  (static frame only if a GIF URL lands in image_url — `loading=lazy`, no autoplay).

## Noise-control rules
- **Absence is the default.** Layouts are text-first; a missing image collapses to
  pure text with zero reserved whitespace (no gray placeholder boxes — placeholders
  ARE noise). Width/height attrs prevent layout shift only when an image exists.
- **Reddit thumbnails are filtered**: drop `self`, `default`, `nsfw`, `spoiler`
  pseudo-thumbnails and any URL not matching an image extension/preview host.
- **Muted rendering**: thumbnails get a 1px hairline border and slight desaturation
  (`saturate-[.85]`) so mixed-quality web images sit quietly in the ink palette;
  hero gets no decoration at all.
- **No images in dark-pattern positions**: never under action buttons, never as
  tap targets distinct from the story (the whole row stays one tap target).
- Lazy-load everything below the hero (`loading="lazy" decoding="async"
  referrerpolicy="no-referrer"`); broken images self-remove via onError → text-only
  row (no broken-glyph noise).

## Technical capture (unchanged from V6, recap)
- `articles.image_url` (migration 0009) — URL metadata only, files never stored.
- Free capture at ingest: Reddit JSON `preview`/`thumbnail` (post-filtering above),
  RSS `media:content`/`media:thumbnail`/image enclosure.
- Lazy enrichment: summarizer's existing page fetch also extracts `og:image`.
- Exposed in ArticleOut + story payloads; story hero image = lead article's.

## Acceptance additions
- A page with zero images must look intentional, not degraded (test with images
  feature-flagged off).
- Max one large image per viewport on the front page; thumbnails uniform.
- Lighthouse CLS ≈ 0 with and without images.

STATUS: PLAN ONLY — implementation awaits explicit go-ahead.

## V6.2 — Mobile filter collapse (app-feedback-v3 line 10)
- Mobile: both chip rows removed; one quiet summary pill ("Week · All types") opens
  the bottom-sheet drawer + a small Saved toggle. Clear appears only when filters active.
- Drawer gains Content Type + Time Range sections (nothing lost), included in clear-all.
- Desktop keeps the full chip rows.

## V6.3 — Meaningful titles for HF/GitHub items (app-feedback-v3 line 12)

Problem: HF Spaces/models and GitHub items surface as bare slugs
("r3gm/wan2-2-fp8da-aoti-preview") — meaningless to a newcomer.

1. **Deterministic, at fetch (free):**
   - HF Spaces: request card data; summary = short description + likes
     (replaces the useless "Trending Space on Hugging Face: <slug>" string).
   - HF models: summary = pipeline tag ("Text-to-video model") + downloads.
   - GitHub trending already captures repo descriptions — no change.
2. **LLM title enrichment (the real fix):** scheduled job (hourly, batch ≤15) finds
   articles from hf/github sources whose title still looks like a slug
   (contains "/" or no spaces), transiently fetches README/model card via existing
   extractors, and asks Groq for JSON {"title": plain-English name ≤90 chars,
   "summary": one sentence "what it is + why it matters" ≤300 chars}. Stored
   title/summary replaced; original slug stays in the URL and author fields.
   Slug-shaped-title heuristic doubles as the "not yet enriched" marker — no
   schema change. Covers existing backlog progressively (newest first).
3. Frontend: no changes needed — enriched titles flow through feed/stories/reader.

## V6.4 — feedback-v3 lines 14/16/18
- Infinite feed: API pagination verified healthy; frontend observer rebinds on item
  count + explicit "Load more" fallback button so scroll-loading can never strand.
- Summary context: HF README/model-card extraction branch (raw endpoint, frontmatter
  stripped, prepended enriched summary); default Groq model → llama-3.3-70b-versatile.
- Brief formatting: inline GFM rendering (bold/italic/code/links), ###-heading support,
  consistent 15px/1.7 reading type with bordered section headings.
