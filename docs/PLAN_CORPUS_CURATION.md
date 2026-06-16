# Corpus Curation — a "matured", structured corpus (2026-06-16)

> Request (app-feedback): the corpus should be **structured and matured** — NOT a
> complete one-year dump, but only the items that stay **relevant and useful**.
> Anything the user has engaged with is sacred.

## Principle
A personal AI-intelligence feed is a *curator, not an archive*. Old news that
nobody acted on is noise; old **landmarks** are reference. So retention tightens
with age: recent items are kept broadly, older items only if they were genuinely
important, ancient items are dropped — except anything the user touched.

## Retention tiers (by published age)
Computed per article from existing signals — `relevance_score` /
`importance_magnitude` / `popularity` (traction), topic tags (AI relevance), and
source family. No new model.

| Tier | Age | Keep rule |
|---|---|---|
| **Preserved** | any | In `user_article_state` (read / bookmarked / feedback) — **always kept**. |
| **Fresh** | ≤ 14d | Keep all, except hard junk: a broad-aggregator (GitHub/HN/Reddit/PH) item that is `general`-only **and** low traction (`magnitude < 0.25`). |
| **Recent** | 14–90d | Keep if AI-relevant (specific tag **or** AI-native source) **and** showed traction/relevance (`magnitude ≥ 0.15` or `popularity ≥ 0.5`). |
| **Older** | 90–365d | Keep **landmarks only**: a specific AI tag **and** `magnitude ≥ 0.45`. |
| **Ancient** | > 365d | Drop (unless preserved). |

The thresholds are constants in `scripts/curate.py` and easy to retune.

## Safety
- **Dry-run by default.** `python -m scripts.curate` only reports per-tier
  keep/drop counts + samples. It deletes nothing.
- **Apply** with `CURATE_APPLY=1`. Deletes are batched.
- Deletions never touch an article referenced by `user_article_state`, so there
  is no dangling FK and no loss of anything the user engaged with.
- Idempotent: re-running converges (already-curated corpus drops ~nothing new).

## Operating it
- One-off now: sharpen the live corpus after the tagger upgrade.
- Ongoing: run weekly (the existing APScheduler can call `curate()` — wired as a
  follow-up; for now it's an admin script so the first prod run is observed).

## Feedback loop
The curator and the ranker share the same relevance signals, so improving
ranking improves curation automatically. User feedback (👍/👎/bookmark/open) both
**personalizes ranking** and **pins items into the preserved tier**, so the
corpus matures around what the user actually finds useful.
