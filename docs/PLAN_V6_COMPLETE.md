# NeuralFeed — Complete V6 Implementation Plan

> Authoritative remaining-work plan, synthesized 2026-06-16 from a live audit of the
> codebase against `.dev-notes/app-feedback-v6.md`, finalized with user decisions
> (2026-06-16). Supersedes `PLAN_V6_REMAINING.md`.
>
> **Correction to the record:** the Lovable rebuild was **abandoned**. The Next.js
> `frontend/` is the app of record, upgraded **in place**. The "rebuild via Lovable"
> footer in `PLAN_V6_REMAINING.md` is stale.

## Governing rules (every phase)
- Plan-first; conventional commits; **CI must stay green** (`tsc --noEmit`, `npm test`,
  backend `pytest`) — run locally before every push. ≥80% backend coverage on
  `services/`, `fetchers/`.
- Security is a core pillar: `/ecc:security-scan` + `/ecc:security-review` before deploy.
- Curator rule: metadata only; image URLs hotlinked, never stored.
- **Verification:** the user runs `verify-deployed` (browser MCP can't launch Chrome in
  the dev sandbox). I ship + run local build/tsc/test gates; the user flips acceptance
  rows to `PASS`/`FAIL` on the live URL and pastes FAILs back for fixing.

## Resolved product decisions (2026-06-16)
1. **No dedicated `/today` page** — fold it into the **Feed** as a **top-10 "Today"**
   block. **Discover** is for exploring more topics the user wants.
2. **Horizon catch-up is a first-class feature:** the user may open the app a **day, a
   month, or a year** later and must see the **most important + most relevant** items for
   that window — *not merely the most recent*. Ranking must be **horizon-aware**.
3. **Ranking is auto-tuned only — no manual sliders.** It must be genuinely intelligent:
   learn from explicit feedback (👍/👎/bookmark) **and implicit signals (opening + viewing
   an article)**, and have strong **cold-start** relevance from first use.
4. **Density setting applies to the Feed/Today surface**, not Discover.

---

## Status audit (what's already built)

| Item | Status |
|---|---|
| Fraunces serif wordmark + headings; AI-sparkle tells removed | ✅ DONE (this session) |
| Relevance as signal-strength match-meter | ✅ DONE (this session) |
| Editorial summary render + backend prompt/cleanup | ✅ DONE (this session + prior) |
| Smart ranking always-on, no disable toggle | ✅ DONE |
| Learned topic/source affinity + feedback boosts | ✅ DONE (extend in Phase 2) |
| Cross-source dedupe + buzz; hotness/heat color index; topic heat | ✅ DONE |
| Plain-English title enrichment of slugs | ✅ DONE |
| Discover "Trending now"; FollowTargets removed; published dates | ✅ DONE |
| **Fold Today into Feed as top-10 (N1)** | ❌ TODO |
| **Horizon ranges Day/Month/Year + horizon-aware importance (N2)** | ❌ TODO |
| **Open AI summary on click in Today/Feed surfaces (N3)** | ⚠️ Feed ✅ / Today ❌ |
| **Implicit view/open learning + robust auto-tune ranking (N4)** | ❌ TODO |
| **Cold-start relevance "from the get-go"** | ❌ TODO |
| **Density setting scoped to Feed/Today** | ⚠️ VERIFY/ADJUST |
| **GitHub stars-today velocity accuracy (C1)** | ⚠️ VERIFY |
| **Honest blog traction proxy (C3)** | ❌ TODO |
| **LinkedIn ToS-safe sourcing** | ⚠️ PARTIAL |
| **Viewed items don't repeat across Feed + Discover (B2)** | ⚠️ VERIFY |
| **Deployed-site verification of every row** | ❌ TODO (user-run) |

---

## Phase 1 — Horizon-aware Feed with Today top-10 (N1–N3)  ·  back + front
The headline feature. The Feed gains a **horizon selector** (Today · Month · Year) and an
**importance-ranked top-10** so any return cadence is covered.

1. **Backend — importance score.** Add `importance(article, horizon)` to a new
   `services/importance.py` (or extend `ranker.py`): combines cross-source buzz (dedupe
   mention count), peak traction, source authority, and research signal — **independent of
   recency**. Recency is then blended **proportionally to horizon**: dominant for `24h`,
   minor for `30d`, near-zero for `365d`. So a year view ranks the year's *landmark*
   items (e.g., an OpenClaw-scale launch) above last week's minor news.
2. **API:** extend feed endpoint with `horizon` ∈ {`day`,`month`,`year`} (maps to
   window + recency weight) and a `top` mode returning the importance-ranked top-N.
   Add `365d` to `time_range` allow-list (`lib/types.ts` + API param whitelist).
3. **Frontend — fold Today into Feed.** Remove `/today` from nav (`Header`, `MobileNav`).
   At the top of the Feed render a **"Today in AI — top 10"** block (importance-ranked,
   `horizon=day`). Add the **Day/Month/Year segmented control**; switching re-queries with
   the horizon. Each item opens the **`SummarySheet`** (reuse `FeedView`'s `openArticle`).
4. **Density setting** applies to this Feed/Today surface only; Discover keeps its own
   exploratory layout.
5. Delete `app/today/page.tsx` after migrating its logic; redirect `/today`→`/`.
Acceptance: N1–N3 `PASS`; Year view shows the year's most important+relevant items, not
just recent ones; every item opens the formatted summary.

## Phase 2 — Robust intelligent auto-tuning ranker (N4) + cold-start
1. **Implicit signals.** Record **open** and **view/dwell** events (a card opened to the
   summary, or link-clicked) as positive implicit feedback in `UserArticleState`
   (privacy-safe, per-user). Feed them into `preference_learner.py` alongside 👍/👎/save.
2. **Auto-tuned weights (no UI).** Maintain per-user learned weights for topic affinity,
   source affinity, and the recency-vs-importance balance — adjusted continuously from the
   blended signal set. Lower recency weight automatically if the user consistently engages
   with older deep items. Bounded so base relevance is never overpowered.
3. **Cold-start.** Ship sensible defaults so the feed is useful on day one: emphasize
   high-authority AI sources, landmark/launch detection, and the topics v6 calls out
   (LLMs, AI agents, embodied AI / robotics). Optional one-tap interest pick at first run
   that seeds weights (no blocking onboarding).
4. **Robustness.** Unit tests for monotonicity (more 👍 on a topic ⇒ that topic ranks
   higher), recency-decay-by-horizon, and that disliked topics sink.
Acceptance: N4 `PASS`; opening/viewing items measurably shifts future ranking; new-user
feed is relevant before any feedback.

## Phase 3 — Traction correctness & honesty (C1–C3, C6)
1. **C1 GitHub velocity:** verify/fix `fetchers/github_trending.py` + `services/traction.py`
   compute real current stars + "stars today" from two samples; backfill baseline so the
   first delta isn't garbage. Fixture-based tests.
2. **C3 blog traction:** scrape an exposed count where present; else a social proxy
   (HN/Reddit mentions of the URL); else recency — **never fabricate**; label honestly.
3. **C6 images:** confirm `image_url` renders on cards + summary, hotlinked only.
Acceptance: C1/C3/C6 `PASS`; no invented numbers.

## Phase 4 — Dynamic feed & dedupe (B2/B3)
1. Verify `UserArticleState` hides opened items from "For You" across **both** Feed and
   Discover (incl. Discover "Trending"); add regression tests.
2. Confirm preference skew is observable end-to-end (now reinforced by Phase 2 signals).
Acceptance: B2/B3 `PASS`; an opened item never reappears on refresh in either surface.

## Phase 5 — LinkedIn ToS-safe sourcing
1. Source public LinkedIn-origin items via a compliant bridge (Google News query / public
   RSS), not authenticated scraping. Add as a `Source` (`access=rss`). No auth, no PII,
   metadata + link-out only.
Acceptance: relevant LinkedIn-origin items appear without ToS violation.

## Phase 6 — Verification, security & optimization (release gate)
1. **User runs `verify-deployed`** → every acceptance row `PASS`/`FAIL` with screenshots
   on the live URL; I fix FAILs.
2. `/ecc:security-scan` + `/ecc:security-review`; `/ecc:refactor-clean` for dead code
   (incl. removed `/today` page).
3. Lighthouse mobile ≥90; `prefers-reduced-motion` respected.
Acceptance: all rows `PASS`; security clean; perf budget met.

---

## Sequencing
1 (horizon Feed + Today) → 2 (intelligent ranker) are the core of the user's vision and
ship first. 4 (dedupe) rides on 2's signals. 3 (traction) and 5 (LinkedIn) are
backend/source-heavy. 6 gates the release. CI green + local gates before every push;
user-run `verify-deployed` before each "check the site".

---

# V7 Addendum — UX bugs + filter intelligence (2026-06-16)

> Source: `.dev-notes/app-feedback-v7.md`. These are **broken-UX bugs + filter changes**
> and take priority over the (larger) Phase 1–2 feature work because the app is currently
> hard to use. Engineering principles: single source of truth for auth/chrome, no flash of
> unauthorized content (FOUC/FOUAC), URL as the filter state container, accessible controls,
> no fabricated UI, no gradients (anti-AI).

## V7-1 — Auth gate & app chrome (CRITICAL bug)  ·  frontend
**Symptoms:** the login page shows the nav menu; clicking a menu item briefly flashes
protected content before snapping back to login.
**Root cause:** `Header` + `MobileNav` are rendered inside `AuthGuard`'s children in
`layout.tsx`, so they appear on `/login`; and `AuthGuard` doesn't re-gate per navigation,
so protected content paints before `router.replace('/login')` runs.
**Fix (single source of truth in `AuthGuard`):**
- Move `Header` + `MobileNav` *into* `AuthGuard`; render chrome **only** when authenticated
  AND not on `/login`.
- Gate rendering on a `mounted` flag + live `getToken()`: on protected routes render
  nothing until a token is confirmed (kills the flash). `/login` renders children only,
  no chrome.
- Keep the guest banner + `--banner-h` behavior.
Acceptance: `/login` has no nav; no protected content ever flashes; deep-linking a
protected route while logged out goes straight to login with no flicker.

## V7-2 — Login page alignment & de-AI  ·  frontend
- Remove the blurred `bg-primary/10` **glow backdrop** (a gradient/AI tell; violates
  "no gradients").
- With chrome gone (V7-1), confirm the card is true-centered (`min-h-dvh`, no header
  offset); tighten vertical rhythm and input alignment; ensure 44px tap targets.
Acceptance: login is centered and clean on mobile + desktop; no gradient.

## V7-3 — Multi-select filters  ·  back + front
**Goal:** select multiple values per dimension (content type, topic, source).
- **Frontend:** represent each multi dimension as a comma-joined URL param (e.g.
  `topic=llm,ai-agents`); `FilterContent` toggles membership in the set; chips show
  selected state; `activeFilterCount` counts total selected. `FeedView` parses CSV → arrays.
- **Backend (`feed.py`):** accept CSV for `source_id`, `category`, `topic`; build
  `IN (...)` / OR-of-`LIKE` (topic JSON) queries; update the deep-feed signature, the
  Redis cache key, and param whitelist. Add tests for single + multi + empty.
Acceptance: choosing LLMs + Agents shows items in either; selections survive refresh
(URL-encoded); no N+1 or query errors.

## V7-4 — Remove Source-Quality filter → automatic & smart  ·  back + front
- Delete the **Source Quality** section + `min_signal` param from `FilterContent`,
  `FeedView`, `FILTER_PARAMS`, and the feed API surface used by the client.
- Quality stays enforced **automatically** inside ranking (`source_signal` term in
  `ranker.score_article`) — no user knob, consistent with "smart ranking, no toggles".
Acceptance: no quality filter in UI; low-signal sources still naturally sink via ranking.

## V7-5 — Responsiveness & layout polish  ·  frontend
- **De-duplicate the brand:** on `md+`, the global `Header` and `FeedView`'s own top bar
  both render "NeuralFeed" — hide the in-feed top bar on desktop (Header owns it); keep it
  on mobile where there's no Header.
- Audit breakpoints (sm/md/lg) for consistent gutters, max-widths, and tap targets;
  ensure no horizontal overflow; respect `prefers-reduced-motion`.
- Perceived speed: confirm skeletons + optimistic updates on all mutations; lazy-render
  offscreen images (already `loading="lazy"`).
Acceptance: no duplicated chrome; clean layout at all breakpoints; feels snappy.

## V7 sequencing
V7-1 → V7-2 (auth/login bugs, highest user pain) → V7-4 (quick removal) → V7-3
(multi-select, back+front) → V7-5 (polish). Then resume Phase 1–2. Each step: local
`tsc`+`test`+`pytest` green before push; user runs `verify-deployed`.
