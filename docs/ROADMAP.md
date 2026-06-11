# NeuralFeed — Roadmap

## Phase 1 — Foundation (MVP, local only)

### 1.0 Scaffolding
- [x] Git repo + root structure
- [x] Frontend: Next.js 15 + bun + Tailwind + shadcn/ui
- [x] Backend: FastAPI + uv
- [x] Docker Compose for Redis

### 1.1 Data Models
- [ ] SQLAlchemy models: Article, Source, UserPreference
- [ ] Alembic initial migration
- [ ] Seed data: 11 MVP sources
- [ ] Model tests

### 1.2 Core Backend
- [ ] Pydantic schemas
- [ ] arXiv fetcher
- [ ] Reddit fetcher
- [ ] GitHub Trending fetcher
- [ ] RSS blog fetcher
- [ ] Ingest + dedup service
- [ ] Topic tagger
- [ ] Celery workers + beat schedule
- [ ] REST API: feed, sources, feedback, preferences, refresh

### 1.3 Core Frontend
- [ ] API client + React Query hooks
- [ ] Layout: Header, MobileNav, DesktopSidebar
- [ ] SourceBadge component
- [ ] FeedCard + FeedCardSkeleton
- [ ] FilterBar
- [ ] Feed page (paginated)
- [ ] Dark mode toggle
- [ ] RefreshIndicator

### 1.4 Integration & Polish
- [ ] CORS config
- [ ] Error boundaries
- [ ] Loading states
- [ ] Responsive QA (375 / 768 / 1280px)
- [ ] Manual E2E smoke test

---

## Phase 2 — Personalization & More Sources

### 2.1 Feedback System
- [ ] FeedbackLog model + migration
- [ ] Re-ranking service
- [ ] Preference settings panel

### 2.2 Additional Sources
- [ ] Hugging Face model releases
- [ ] Newsletter RSS feeds
- [ ] YouTube channels (RSS)
- [ ] X / Twitter (API v2 or Nitter RSS — feasibility gate)
- [ ] LinkedIn (feasibility gate)

### 2.3 Discovery Features
- [ ] Global search (FTS5)
- [ ] Bookmarks page
- [ ] Advanced filter drawer
- [ ] Saved views / presets
- [ ] Source management UI

---

## Phase 3 — Multi-User & Production

### 3.1 Authentication
- [ ] User model + migration
- [ ] JWT auth endpoints
- [ ] Per-user data isolation
- [ ] Frontend auth pages

### 3.2 Production Infrastructure
- [ ] SQLite → PostgreSQL migration
- [ ] Full Docker Compose stack
- [ ] Vercel deployment (frontend)
- [ ] Railway deployment (backend + DB + Redis)
- [ ] GitHub Actions CI/CD

### 3.3 Quality & Monitoring
- [ ] Sentry (backend + frontend)
- [ ] Rate limiting
- [ ] Lighthouse mobile ≥ 90
