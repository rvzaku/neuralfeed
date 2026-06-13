# NeuralFeed — Complete Multi-User Plan

Status legend: ⬜ not started · 🟡 in progress · ✅ done

**Core architecture decision:** content is *shared*, personalization is *per-user*.
All users draw from one global pool of fetched articles/sources; per-user state is
ranking, feedback, bookmarks, read-state, prefs, and watched accounts. Do not fork
content per user.

**Constraints:** every solution must be efficient, optimised, secure, and free-tier
friendly (Render + Vercel + Neon + Render Key Value/Redis). Prefer free providers.

---

## Phase 0 — Correctness blockers (before ANY public signup)
- 🟡 **0.1** Eliminate global `Article` state mutations. `GET /feed/{id}` and the
  `elif` in `articles.py` write the global `Article.is_read`; route to
  `user_article_state` when authed, global only as anonymous fallback.
  Files: `api/v1/feed.py`, `api/v1/articles.py`. Test: cross-user isolation.
- ⬜ **0.2** Full data-isolation audit — every write path takes `user.id`; add a
  per-resource isolation test.
- ⬜ **0.3** Decide global vs per-user for **sources** and **watched accounts**
  (custom sources/accounts should be per-user; the curated registry stays global).
  Needs a product decision + possible `user_id` column.

## Phase 1 — Account lifecycle
- ⬜ **1.1** Transactional email (`services/email.py`; Resend/Postmark free tier;
  SMTP dev fallback). Env: `EMAIL_PROVIDER`, `RESEND_API_KEY`, `EMAIL_FROM`.
- ⬜ **1.2** Email verification (`user.is_verified`, signed expiring token,
  `GET /auth/verify`, gate writes behind verified).
- ⬜ **1.3** Password reset (single-use hashed token, 30-min expiry, anti-enumeration).
- ⬜ **1.4** Change password / change email (re-verify new email).
- ⬜ **1.5** Logout + token revocation via `user.token_version` embedded in JWT.
- ⬜ **1.6** Account deletion + data export (cascade; JSON export).

## Phase 2 — Abuse & cost controls
- ⬜ **2.1** Per-user rate limiting on Redis (not just per-IP).
- ⬜ **2.2** Per-user daily quota on summary generation (Groq cost) via Redis TTL keys.
- ⬜ **2.3** Registration abuse: CAPTCHA (Cloudflare Turnstile free) + per-IP signup limit.

## Phase 3 — Scale beyond one instance (when needed)
- ⬜ **3.1** Move scheduler out of web process (Render Cron → internal refresh, or
  Redis leader lock).
- ⬜ **3.2** Shared rate-limit + cache on Redis (falls out of 2.1; cache already done).
- ⬜ **3.3** Confirm stateless web tier → safe to run instances ≥ 2.

## Phase 4 — Data layer hardening
- ⬜ **4.1** Replace additive-column hack with Alembic-on-deploy (`alembic upgrade head`).
- ⬜ **4.2** Backups / PITR on Neon documented.
- ⬜ **4.3** Composite indexes: `user_article_state(user_id, is_read)`,
  `(user_id, is_bookmarked)`.

## Phase 5 — Onboarding & multi-user UX (frontend)
- ⬜ **5.1** Signup → verify → first-run topic picker (seeds `topic_weights`).
- ⬜ **5.2** Account settings page (change pw/email, logout-everywhere, delete, export).
- ⬜ **5.3** Auth UX states (unverified, expired reset, rate-limited).
- ⬜ **5.4** Sensible default feed for a brand-new user.

## Phase 6 — Observability, legal, launch
- ⬜ **6.1** Sentry user context + per-request user logging + basic metrics.
- ⬜ **6.2** Privacy Policy + Terms pages.
- ⬜ **6.3** Minimal admin (list/disable users, manage global sources).
- ⬜ **6.4** Load test feed + summary endpoints.
- ⬜ **6.5** Security scan + dependency audit before opening signup.

---

## Milestones
| Milestone | Phases | Est. |
|---|---|---|
| **M1 — invite-only multi-user safe** | 0 + 1.1–1.3 + 2.1 | ~3–4 days |
| **M2 — open public signup** | 1.4–1.6 + 2.2–2.3 + 5 + 6.2 | ~1 week |
| **M3 — scale & durability** | 3 + 4 + 6.1/6.3/6.4 | ~1 week |

Dependencies: email (1.1) blocks 1.2/1.3; Redis (done) unblocks 2.x/3.x;
Alembic (4.1) before real users accumulate irreplaceable data.
