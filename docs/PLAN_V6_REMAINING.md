# NeuralFeed — V6 Remaining Work Plan

> Source: `.dev-notes/app-feedback-v6.md` (expanded) + `docs/PLAN_V6.md` (phases A–F,
> committed e1747e8→5f2ef6d). Synthesized 2026-06-16.
> Phases A–F were **merged in code** but most items are **unverified on the deployed
> site** and the expanded feedback (lines 52–80) added new scope. Every item below maps
> to a row in `.dev-notes/frontend-acceptance.md`; nothing is "done" until that row is
> `PASS` via the `verify-deployed` skill.
>
> Workflow unchanged: plan-first, ECC skills per task type, conventional commits,
> 80%+ backend coverage, `/ecc:security-scan` before deploy. **New gate:** run
> `verify-deployed` before asking the user to check the site.

## Method for every phase
1. Implement against the acceptance rows (set them `TODO`→`BUILT` as you merge).
2. Deploy.
3. Run `verify-deployed` → `frontend-verifier` flips rows to `PASS`/`FAIL` with evidence.
4. Only report to the user the `PASS` items + an honest "still failing" list.

---

## Phase G — Close the gaps in already-"shipped" A–F (highest priority, low risk)
These shipped in code but are unverified or known-broken:
- **A1 (FAIL):** Remove `FollowTargets` — still imported/rendered at
  `frontend/app/sources/page.tsx:5,285`. Delete the import, the tab, and the component
  usage; drop `components/sources/FollowTargets.tsx`.
- **A2:** Confirm no `ranked`/smart-ranking toggle remains in `/settings`, `/`, `/discover`.
- **A3 / A5:** Confirm Discover has no Topics strip; confirm no "Recap" surface exists.
- **C / D / E rows marked BUILT:** verify each on deployed site (dates, context_line,
  heat bands, summary formatting). Fix whatever FAILs.
Acceptance: every A–F row in the contract is `PASS` (not `BUILT`).

## Phase H — Traction signals & GitHub correctness (Phase C completion)
- **C1:** Fix GitHub star batch — correct current totals + "stars today" velocity
  (`backend/app/fetchers/github_trending.py`, `services/traction.py`). The original
  feedback flags this as still broken.
- **C2/C3:** Render social upvotes/comments, HN points/comments, and an honest blog
  traction signal (scraped count where exposed, else social proxy, else recency — never
  fabricated).
- **C6:** Render source `image_url` on cards (hotlinked only).
- **E1:** GitHub/model titles describe what it DOES + why it matters, never raw slug
  (`backend/app/services/enricher.py`).
Acceptance: C1,C2,C3,C6,E1 `PASS`; no fabricated numbers.

## Phase I — New v6 scope (lines 52–80)
- **N1:** Move "Today" into the Discover section.
- **N2:** Add Day / Month / Year ranges to Today.
- **N3:** Clicking a Today article opens its AI summary sheet.
- **N4:** Settings exposes weighting controls (recency / virality / research-interest /
  company-interest) so recent news is no longer over-weighted; ranker reads these weights.
- **N5:** Topics is its own page with accurate, intelligent classification; ensure
  embodied-AI/robotics and AI-agents are first-class (also D2).
- **D3:** "What's hot right now" surface for OpenClaw-style spikes.
- **B2/B3:** Dynamic dedup of viewed items across Feed + Discover; preference skew.
- **LinkedIn:** ToS-safe interesting-item sourcing (Google News / RSSHub public bridge).
Acceptance: N1–N5, D2, D3, B2, B3 `PASS`.

## Phase J — Aesthetic & font overhaul (F1–F3 + new feedback)
- **F2:** Update to a better, professional font; no AI-looking defaults.
- **F1/F3:** Premium flat aesthetic, single indigo accent, subtle motion respecting
  `prefers-reduced-motion`. Use ECC `make-interfaces-feel-better` / `motion-ui`.
- **Lovable MCP redesign:** the user asked to design the frontend via the Lovable MCP for
  a more professional, attractive UI/UX. **Decision needed** (see below) before doing a
  full remix vs. in-place polish — a Lovable remix is a stack change and conflicts with
  the dropped Apple-News redesign direction in CLAUDE.md.
Acceptance: F1–F3 `PASS`; aesthetic confirmed on mobile + desktop screenshots.

## Phase K — Security & optimization pass (cross-cutting, before deploy)
- `/ecc:security-review` + `/ecc:security-scan` (core pillar).
- `/ecc:refactor-clean` to remove dead code (incl. deleted FollowTargets).
- Re-confirm curator rules: metadata only, image URLs hotlinked never stored.

---

## Resolved decision (2026-06-16) — Frontend rebuild via Lovable
The user chose to **rebuild the frontend via the Lovable MCP** (React + Tailwind +
shadcn), superseding the "dropped redesign / V5 premium-restraint as direction of record"
note in CLAUDE.md. Implications for Phase J:
- Phase J becomes a **rebuild**, not in-place polish. Plan the Lovable project, then
  re-wire the API client, login-first auth, and all v6 features (heat bands, traction,
  Today/Topics, settings weights) onto the new shell.
- Keep the FastAPI backend + deployed API contract unchanged; only the frontend is
  regenerated. Backend acceptance rows are unaffected.
- The acceptance contract (`.dev-notes/frontend-acceptance.md`) still governs — the new
  Lovable frontend must make every row `PASS` on its own deployed URL.
- CLAUDE.md should be updated to reflect this reversal before Phase J starts.
