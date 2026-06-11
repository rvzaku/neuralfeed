# CLAUDE.md — NeuralFeed

This file is the authoritative guide for Claude Code when working in this repository.
Read it fully before starting any task.

---

## Project Overview

**NeuralFeed** is a personal AI-news intelligence dashboard — a single website that tracks everything relevant happening in AI and surfaces only the signal worth reading.

The core problem it solves: the AI field moves so fast that missing two weeks means falling behind. Every useful source (X, Reddit, arXiv, GitHub, company blogs, conferences) lives on a different platform designed to keep you inside it. NeuralFeed inverts that: it fetches the signal, ranks it by relevance, and sends you directly to the original source. You never read content here — you read it at the source; NeuralFeed simply decides *which* content deserves your attention today.

**Phase 1 target**: personal use only, no auth, running locally.
**Phase 2 target**: multi-user with per-user preference profiles and production hosting.

---

## Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| **Frontend** | Next.js 15 (App Router) | React Server Components where possible |
| **Styling** | Tailwind CSS + shadcn/ui | Design tokens via Tailwind config |
| **Backend** | Python FastAPI | Async, type-annotated throughout |
| **Task Queue** | Celery + Redis | Background fetching and scheduled jobs |
| **Database (dev)** | SQLite (via SQLAlchemy) | Zero config for local development |
| **Database (prod)** | PostgreSQL | Migrate from SQLite at Phase 3 |
| **ORM** | SQLAlchemy 2.x | Async session support |
| **Package manager (FE)** | bun | Lockfile committed |
| **Package manager (BE)** | uv | `pyproject.toml` with `uv.lock` |
| **Hosting (prod)** | Vercel (frontend) + Railway (backend + DB + Redis) | Phase 3 only |

---

## Repository Structure

```
neuralFeed/
├── frontend/                  # Next.js 15 app
│   ├── app/                   # App Router pages and layouts
│   ├── components/            # Shared UI components (shadcn + custom)
│   ├── lib/                   # Client-side utilities, API client
│   ├── hooks/                 # Custom React hooks
│   └── public/                # Static assets
│
├── backend/                   # Python FastAPI service
│   ├── app/
│   │   ├── api/               # Route handlers (v1/)
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas (request/response)
│   │   ├── services/          # Business logic layer
│   │   ├── fetchers/          # One module per source type
│   │   ├── workers/           # Celery task definitions
│   │   └── core/              # Config, DB session, deps
│   ├── tests/
│   ├── alembic/               # DB migrations
│   └── pyproject.toml
│
├── docs/
│   ├── ROADMAP.md
│   ├── SOURCES.md             # Living source registry
│   └── ADRs/                  # Architecture decision records
│
└── CLAUDE.md                  # This file
```

File naming:
- Frontend: `camelCase` for components (`FeedCard.tsx`), `kebab-case` for pages/routes
- Backend: `snake_case` throughout (Python convention)
- Docs: `UPPER_SNAKE_CASE.md` for top-level docs, lowercase for ADRs

---

## Development Philosophy

**Never implement before planning.** Every phase and sub-phase starts with a written plan. No code until the plan is approved.

### Mandatory rules

1. **Plan first** — use `/ecc:plan` or `/ecc:blueprint` to write a plan doc before any implementation sprint.
2. **Conventional commits** — all commits use prefixes: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`. Vague messages are rejected.
3. **Dev → Prod pipeline** — develop and validate locally; never push untested changes to production.
4. **Incremental delivery** — ship in small, working increments. No big-bang features.
5. **Test coverage target** — 80%+ on all `services/`, `fetchers/`, and `workers/` modules. Frontend components need at least smoke tests.
6. **Skill-first workflow** — use the ECC skills listed below to drive each task type. Do not reinvent what a skill already handles.
7. **Security gate** — run `/ecc:security-scan` before any deploy. Never commit secrets; use `.env` files with `.env.example` as the committed template.

---

## ECC Skills — When to Use What

| Task | Skill to invoke |
|---|---|
| Planning a new phase or feature | `/ecc:plan` → `/ecc:blueprint` |
| Architecture decisions | `/ecc:api-design` → document in `docs/ADRs/` |
| FastAPI routes, services, schemas | `/ecc:fastapi-patterns` |
| FastAPI code review | `/ecc:fastapi-review` |
| React components, hooks, layouts | `/ecc:react-patterns` |
| React code review | `/ecc:react-review` |
| Building a new source fetcher | `/ecc:data-scraper-agent` |
| Connecting a new API | `/ecc:api-connector-builder` |
| Writing tests (always TDD) | `/ecc:tdd-workflow` |
| React component tests | `/ecc:react-test` |
| Security audit before shipping | `/ecc:security-review` + `/ecc:security-scan` |
| Mobile/accessibility review | `/ecc:frontend-a11y` |
| UI feel and polish | `/ecc:make-interfaces-feel-better` |
| Database migrations | `/ecc:database-migrations` |
| Docker / deployment config | `/ecc:docker-patterns` + `/ecc:deployment-patterns` |
| E2E tests | `/ecc:e2e-testing` |
| Code cleanup after a sprint | `/ecc:refactor-clean` |

---

## Sub-agents to Build (Phase 1+)

These are custom agents to be defined as the project grows. Create them in `docs/agents/` as Markdown with YAML frontmatter.

| Agent | Responsibility | Build in Phase |
|---|---|---|
| `news-fetcher-agent` | Pulls raw items from each source, normalises to unified schema | Phase 1.2 |
| `dedup-agent` | Detects duplicate stories across sources (URL + title similarity) | Phase 1.2 |
| `ranker-agent` | Re-ranks content based on user thumbs-up/down feedback history | Phase 2.1 |
| `topic-tagger-agent` | Auto-tags items with topic labels (LLMs, CV, RL, etc.) via keyword classifier | Phase 2.1 |
| `source-suggestion-agent` | Suggests new follow targets based on co-citation and liked items | Phase 2.2 |
| `ui-reviewer-agent` | Reviews frontend components for mobile responsiveness and a11y | Phase 1.3+ |

---

## Data Models (Core)

### Article (unified item schema)

```python
class Article(Base):
    id: str              # hash of (source_id + original_url)
    title: str
    url: str             # original URL — always link out, never copy content
    source_id: str       # FK to Source
    author: str | None
    summary: str | None  # snippet / abstract, max ~500 chars
    published_at: datetime
    fetched_at: datetime
    topic_tags: list[str]  # auto-tagged on ingestion
    is_read: bool
    is_bookmarked: bool
    feedback: int | None   # +1 thumbs up, -1 thumbs down, None = no rating
    trending_score: float  # engagement metric from original platform
```

### Source (registry record)

```python
class Source(Base):
    id: str           # slug, e.g. "arxiv-cs-ai"
    name: str
    category: str     # research | social | company | newsletter | github | video | podcast | funding
    url: str
    access: str       # rss | api | scrape | manual
    enabled: bool
    priority: str     # high | medium | low
    refresh_interval: str   # "4h", "daily", "weekly"
    added_on: date
    last_fetched_at: datetime | None
    signal_score: float     # rolling thumbs-up ratio
    notes: str | None
```

### UserPreference

```python
class UserPreference(Base):
    key: str    # e.g. "default_view", "muted_sources", "topic_weights"
    value: str  # JSON-encoded value
```

---

## Source Registry

The full source list lives in `docs/SOURCES.md`. Key rules:

- **Never delete a source** — set `enabled: false` with a note explaining why.
- **No source goes live without a defined `access` method** (rss / api / scrape / manual).
- **Priority levels** drive fetch frequency:
  - `high` → fetch every 4–6 hours
  - `medium` → fetch every 12–24 hours
  - `low` → fetch weekly

### MVP Sources (Phase 1.2)

| Source ID | Name | Access | Priority |
|---|---|---|---|
| `arxiv-cs-ai` | arXiv cs.AI + cs.LG + cs.CL | arXiv API | high |
| `arxiv-cs-cv` | arXiv cs.CV + stat.ML | arXiv API | medium |
| `reddit-ml` | r/MachineLearning | Reddit JSON API | high |
| `reddit-localllama` | r/LocalLLaMA | Reddit JSON API | high |
| `reddit-artificial` | r/artificial | Reddit JSON API | medium |
| `github-trending` | GitHub Trending (Python/AI) | Scrape | high |
| `rss-openai` | OpenAI Blog | RSS | high |
| `rss-anthropic` | Anthropic Blog | RSS | high |
| `rss-deepmind` | Google DeepMind Blog | RSS | high |
| `rss-huggingface` | Hugging Face Blog | RSS | medium |
| `rss-metaai` | Meta AI Blog | RSS | medium |

---

## Data Fetching Rules

**NeuralFeed is a curator, not a copy machine.** Store metadata only — never full article text or third-party images.

### What gets stored

- Title, URL, source, author, date, short snippet/abstract (≤ 500 chars)
- User feedback (thumbs up/down, bookmarked, read/unread)
- Source registry and config
- User preferences

### What never gets stored

- Full article text
- Images from third-party sources
- Paywalled content

### Fetch method hierarchy

| Source Type | Primary | Fallback |
|---|---|---|
| Blogs / news | RSS feed | HTML scrape of headlines only |
| arXiv | arXiv API (export.arxiv.org) | RSS |
| Reddit | Reddit public JSON API (`/r/sub.json`) | RSS |
| GitHub | GitHub REST API | RSS (releases/trending) |
| X / Twitter | Twitter API v2 (free tier) | Nitter RSS |
| Hugging Face | HF Hub API | RSS |
| YouTube | YouTube Data API | Channel RSS feed |
| Conference sites | HTML scrape of proceedings page | Manual entry |

### Rate limiting and backoff

- All fetchers must implement exponential backoff on 429/503 responses.
- Respect `Retry-After` headers.
- GitHub API: use authenticated requests to get 5000 req/hr instead of 60.
- Reddit: include a descriptive `User-Agent` header (required by Reddit API ToS).

---

## UI / UX Principles

**Mobile-first.** The primary use case is checking NeuralFeed on a phone while traveling.

### Breakpoints

| Screen | Layout |
|---|---|
| Mobile `< 640px` | Single-column feed, bottom navigation, large tap targets (min 44px) |
| Tablet `640–1024px` | Two-column grid, optional side nav |
| Desktop `> 1024px` | Multi-column dashboard with sidebar filters |

### Design rules

- Dark mode is required, not optional. System preference respected by default.
- Typography: readable at small sizes. Minimum 16px body text on mobile.
- Animations: subtle and fast (< 200ms). Use Tailwind's `transition` classes.
- Card tap area: the entire card is tappable, not just the title.
- Colour palette: defined in `tailwind.config.ts` as CSS variables. No hardcoded hex values in components.
- Loading states: skeleton loaders, never spinners alone.

### Key components to build

- `FeedCard` — title, source badge, date, summary snippet, thumbs up/down, bookmark
- `FilterBar` — horizontal scrollable pill chips (Content Type, Time Range, Read Status)
- `FilterDrawer` — slide-in panel for advanced filters (mobile) / sidebar (desktop)
- `SourceBadge` — coloured icon badge per platform (Reddit alien, arXiv logo, etc.)
- `RefreshIndicator` — "Last updated: 2 hours ago" with manual refresh button
- `SavedViewSwitcher` — one-tap switch between named filter presets

---

## Filtering System

### Filter dimensions (all combinable)

1. **Content type**: Research Papers, GitHub, Social, News, Newsletters, Models, Videos, Podcasts, Funding
2. **Platform**: arXiv, Reddit (by subreddit), GitHub, X, LinkedIn, HuggingFace, company blogs, newsletters
3. **Topic tag**: LLMs, CV, Multimodal, RL, AI Safety, Robotics, Agents, Audio, Open Source, Infrastructure, Products, Funding
4. **Time range**: Today, 24h, 3d, 7d, 30d, custom
5. **People / orgs**: filter by specific researcher or company
6. **Source quality**: High signal only / High+Medium / All approved / Include low
7. **Read status**: Unread (default), Read, Bookmarked, All
8. **Feedback**: Liked, Unrated, Similar to liked, Disliked
9. **Trending**: High engagement / fast-rising items

### Default view

Unread · All content types · Last 7 days · High + Medium signal sources

### Built-in saved views

| Name | Filters |
|---|---|
| Morning Digest | Unread · 24h · High signal · All types |
| Papers Only | Research Papers · 7d · Unread |
| What's Trending | All · Trending · 3d |
| Open Source Watch | GitHub + Topic:Open Source · 7d |
| Company Updates | News · Company blogs · 7d |

---

## Feedback & Personalization

- Thumbs up / thumbs down on every card — stored immediately, no page reload.
- `ranker-agent` (Phase 2) uses feedback history to re-score future items.
- Explicit preference panel: "more papers", "fewer product news", mute specific sources/people/topics.
- "Show more like this" action on any card.
- System tracks per-source signal score (rolling thumbs-up ratio). Sources dropping below threshold are flagged for audit.

---

## Content Refresh Cadence

| Source Type | Default Interval |
|---|---|
| X / Twitter | 4–6 hours |
| Reddit | 6–12 hours |
| arXiv | Daily (new submissions at ~00:00 UTC) |
| GitHub Trending | Daily |
| Company blogs (RSS) | 6–12 hours |
| Newsletters | Daily |
| Conference sites | Weekly |
| YouTube | Daily |

- Configurable globally and per-source from the settings panel.
- "Refresh now" manual trigger always visible in the UI.
- Celery beat handles the scheduled tasks; workers handle individual fetch jobs.

---

## Development Roadmap

### Phase 1 — Foundation (MVP, local only)

#### 1.1 Planning & Architecture
- [ ] Finalize and commit this `CLAUDE.md`
- [ ] Write `docs/ROADMAP.md` (living document)
- [ ] Write `docs/SOURCES.md` (source registry)
- [ ] Define all data models and write Alembic migrations
- [ ] Set up project scaffolding (both `frontend/` and `backend/`)

#### 1.2 Core Backend
- [ ] FastAPI app with SQLite + SQLAlchemy (async)
- [ ] Celery + Redis setup with beat scheduler
- [ ] Fetcher: arXiv API (cs.AI, cs.LG, cs.CL, cs.CV)
- [ ] Fetcher: Reddit JSON API (r/MachineLearning, r/LocalLLaMA, r/artificial)
- [ ] Fetcher: GitHub Trending (scrape)
- [ ] Fetcher: RSS blogs (OpenAI, Anthropic, DeepMind, HuggingFace, MetaAI)
- [ ] Deduplication: URL-exact + title-similarity hash
- [ ] Data normalisation layer (unified Article schema)
- [ ] REST API endpoints: feed, sources, feedback, preferences

#### 1.3 Core Frontend
- [ ] Next.js 15 scaffold with Tailwind + shadcn/ui
- [ ] Mobile-first layout and navigation
- [ ] `FeedCard` component
- [ ] Feed view (paginated or infinite scroll)
- [ ] Category filter tabs (pill chips)
- [ ] Dark mode (system preference default)
- [ ] "Last updated" indicator + manual refresh button

#### 1.4 Polish & Local Testing
- [ ] Responsive testing at all three breakpoints
- [ ] Error states: empty feed, fetch failed, source unavailable
- [ ] Manual end-to-end test of fetch → display pipeline
- [ ] 80%+ test coverage on `services/` and `fetchers/`

---

### Phase 2 — Personalization & More Sources

#### 2.1 Feedback System
- [ ] Thumbs up/down UI on cards (optimistic update)
- [ ] Feedback persistence to DB
- [ ] Basic re-ranking based on feedback history

#### 2.2 Additional Sources
- [ ] X / Twitter (API v2 or Nitter RSS fallback)
- [ ] LinkedIn (feasibility: unofficial API or scrape of public profiles)
- [ ] Hugging Face model releases (HF Hub API)
- [ ] Newsletter RSS feeds (The Batch, Import AI, TLDR AI)
- [ ] YouTube channels (Karpathy, Two Minute Papers, Yannic Kilcher)

#### 2.3 Discovery Features
- [ ] Global search across all fetched content
- [ ] "Trending this week" section
- [ ] Bookmarks / save-for-later
- [ ] Advanced filter drawer
- [ ] Saved views / presets
- [ ] Source management UI (approve, reject, re-rate)

---

### Phase 3 — Multi-User & Production

#### 3.1 Authentication
- [ ] User registration and login (email/password + OAuth)
- [ ] Per-user preference profiles
- [ ] Session management (JWT or server sessions)

#### 3.2 Production Infrastructure
- [ ] Migrate SQLite → PostgreSQL
- [ ] Vercel deployment for frontend
- [ ] Railway deployment for FastAPI + PostgreSQL + Redis
- [ ] Environment config (`dev` / `staging` / `prod`)
- [ ] CI/CD pipeline (GitHub Actions)

#### 3.3 Quality & Monitoring
- [ ] Error monitoring (Sentry)
- [ ] Uptime monitoring
- [ ] Mobile Lighthouse score target: > 90
- [ ] Rate limiting on public API endpoints

---

## Testing Requirements

- **Backend**: pytest with `pytest-asyncio`. Integration tests hit SQLite in-memory; unit tests mock external HTTP.
- **Frontend**: Vitest + React Testing Library for components; Playwright for E2E.
- **Coverage**: 80%+ on all `services/`, `fetchers/`, `workers/`.
- **TDD**: write the test first, then the implementation. Use `/ecc:tdd-workflow`.
- **No mocking the DB** in integration tests — use SQLite in-memory as a real DB.

---

## Environment Variables

All secrets via `.env` files. `.env.example` is the committed template — never commit `.env`.

```bash
# Backend (.env)
DATABASE_URL=sqlite+aiosqlite:///./neuralFeed.db
REDIS_URL=redis://localhost:6379/0
ARXIV_API_BASE=https://export.arxiv.org/api/query
REDDIT_USER_AGENT=NeuralFeed/0.1 (personal; contact: your@email.com)
GITHUB_TOKEN=                   # optional — raises rate limit to 5000/hr
TWITTER_BEARER_TOKEN=           # Phase 2
HF_API_TOKEN=                   # optional

# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Git Workflow

- Branch naming: `feat/source-arxiv`, `fix/dedup-collision`, `docs/update-roadmap`
- Commit format: `feat(fetcher): add arXiv cs.AI fetcher with exponential backoff`
- PR required for any Phase 2+ changes; self-review is fine for Phase 1
- Never force-push to `main`
- Tag releases: `v0.1.0` (Phase 1 complete), `v0.2.0` (Phase 2 complete)

---

## Security Rules

- Never store full article text or third-party images — link out only.
- Never hardcode API keys or tokens; use environment variables.
- Sanitize all scraped content before storing (strip scripts/HTML).
- Rate-limit all write endpoints in Phase 3 (auth required).
- Run `/ecc:security-scan` before any deploy.
- Validate and sanitize all external data (RSS feeds, API responses) — treat as untrusted.
- No eval, no dynamic code execution on scraped content.

---

## Open Questions (resolve before Phase 1.2)

| # | Question | Status |
|---|---|---|
| 1 | Final product name | **Resolved: NeuralFeed** |
| 2 | Tech stack | **Resolved: Next.js + FastAPI + Celery + SQLite→PG** |
| 3 | MVP sources | **Resolved: arXiv, Reddit, GitHub Trending, Company RSS** |
| 4 | DB strategy | **Resolved: SQLite for dev, PostgreSQL for prod** |
| 5 | Hosting | **Resolved: Vercel + Railway** |
| 6 | Refresh trigger | **Resolved: Celery beat + Redis** |
| 7 | LinkedIn feasibility | Open — research before Phase 2.2 |
| 8 | Twitter API tier | Open — evaluate free tier limits before Phase 2.2 |
