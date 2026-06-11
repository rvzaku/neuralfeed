# AI News Tracker — Product Ideas v2

## Problem Statement

The AI field is evolving at an extraordinary pace — new research papers, GitHub repos, products, and models ship weekly. Missing even two weeks of updates means falling significantly behind. No single platform exists to track all of this, forcing you to manually check X (Twitter), LinkedIn, Reddit, arXiv, conference sites, company blogs, and individual researchers separately.

The deeper problem is not just volume — it is **noise and distraction**. Opening X.com to find one good research tweet means scrolling through 40 irrelevant posts. Opening Reddit leads to browsing unrelated threads. Each platform is designed to keep you inside it, not to give you a signal and let you leave. This tool inverts that: it brings the signal to you, tells you exactly what is worth reading today, and sends you directly to the original source. You read the content on the original platform — this tool simply decides *which* content deserves your attention.

---

## Goal

Build a personal website that acts as a single, intelligent dashboard to track everything relevant happening in AI — curated to your interests, updated automatically, and beautiful on any device.

---

## Content Buckets to Track

| Category | Examples |
|---|---|
| **People** | Top AI researchers, notable practitioners |
| **Companies** | OpenAI, Anthropic, Google DeepMind, Meta AI, Mistral, etc. |
| **Research Papers** | arXiv preprints, conference publications |
| **GitHub Repos** | Trending/notable AI repositories |
| **Social — X / Twitter** | Posts from researchers, companies, influencers |
| **Social — LinkedIn** | Professional AI updates and announcements |
| **Social — Reddit** | r/MachineLearning, r/LocalLLaMA, r/artificial, etc. |
| **Conferences** | ICML, NeurIPS, ICLR, CVPR, ACL, EMNLP, etc. |
| **Products** | New AI tools, apps, and services |
| **LLM / Model Releases** | New model announcements and benchmarks |

---

## Sources Registry (Exhaustive)

The quality of the website is directly proportional to the quality of its sources. The following is a comprehensive list organized by category. Each source should be maintained in a structured registry (see Source Management System below).

### Research & Papers

| Source | Type | Access Method |
|---|---|---|
| arXiv (cs.AI, cs.LG, cs.CL, cs.CV, stat.ML) | Preprints | RSS / API |
| Semantic Scholar | Papers + citations | API |
| Papers With Code | Papers + benchmarks + code | API / RSS |
| OpenReview | Conference submissions (NeurIPS, ICLR) | API |
| ACL Anthology | NLP papers | RSS |
| Google Scholar Alerts | Custom keyword alerts | Email → parse |
| Hugging Face Papers | Curated daily AI papers | RSS / scrape |

### Conferences

| Conference | Focus | Cadence |
|---|---|---|
| NeurIPS | General ML | Annual (Dec) |
| ICML | General ML | Annual (Jul) |
| ICLR | Deep Learning / Representation | Annual (May) |
| CVPR | Computer Vision | Annual (Jun) |
| ECCV / ICCV | Computer Vision (alternating) | Biennial |
| ACL / EMNLP / NAACL | NLP | Annual |
| AAAI | General AI | Annual (Feb) |
| COLM | Language Models (new) | Annual |
| CORL | Robotics + Learning | Annual |

### Company Blogs & Official Channels

| Source | Type |
|---|---|
| OpenAI Blog | Blog RSS |
| Anthropic Blog | Blog RSS |
| Google DeepMind Blog | Blog RSS |
| Google AI Blog | Blog RSS |
| Meta AI Blog | Blog RSS |
| Microsoft Research Blog | Blog RSS |
| Mistral AI Blog | Blog RSS |
| Cohere Blog | Blog RSS |
| Stability AI Blog | Blog RSS |
| xAI / Grok announcements | Blog / X |
| Apple Machine Learning Research | Blog RSS |
| Amazon AWS AI Blog | Blog RSS |
| Hugging Face Blog | Blog RSS |
| EleutherAI Blog | Blog RSS |
| Allen Institute for AI (AI2) | Blog RSS |
| DeepSeek Blog | Blog / GitHub |

### Model & Product Releases

| Source | Type |
|---|---|
| Hugging Face Model Hub (trending) | API |
| Hugging Face Spaces (trending) | API |
| Ollama new models | GitHub releases / RSS |
| LM Studio announcements | GitHub / Blog |
| Together AI releases | Blog / X |
| Replicate new models | Blog / RSS |

### Social — X / Twitter (Accounts to Track)

**Researchers**
- Yann LeCun, Geoffrey Hinton, Yoshua Bengio
- Andrej Karpathy, Ilya Sutskever
- Fei-Fei Li, Chelsea Finn
- Sébastien Bubeck, Percy Liang
- Emad Mostaque, Demis Hassabis
- Simonw (Simon Willison), Karpathy, swyx

**Company Accounts**
- @OpenAI, @AnthropicAI, @GoogleDeepMind
- @MetaAI, @MistralAI, @xai
- @HuggingFace, @LangChainAI, @weights_biases

**Curators / Commentators**
- @AravSrinivas (Perplexity), @ylecun, @sama
- @goodside, @natolambert, @alexandr_wang

### Social — Reddit

| Subreddit | Focus |
|---|---|
| r/MachineLearning | Research papers, discussions |
| r/LocalLLaMA | Local model running, open-source LLMs |
| r/artificial | General AI news |
| r/singularity | Futurism, AGI discussions |
| r/ChatGPT | GPT-specific news |
| r/ClaudeAI | Anthropic / Claude news |
| r/OpenAI | OpenAI news |
| r/StableDiffusion | Image gen / Stable Diffusion |
| r/learnmachinelearning | Educational content |
| r/deeplearning | Deep learning research |

### Newsletters (via RSS or Email)

| Newsletter | Author / Publisher |
|---|---|
| The Batch | Andrew Ng / DeepLearning.AI |
| Import AI | Jack Clark |
| Ahead of AI | Sebastian Raschka |
| The Decoder | German AI news |
| Last Week in AI | Skynet Today team |
| Gradient Flow | Ben Lorica |
| The AI Edge | Jon Krohn |
| AlphaSignal | Lior Bar |
| TLDR AI | TLDR newsletter |
| The Algorithmic Bridge | Alberto Romero |
| Davis Summarizes Papers | Davis Blalock |

### GitHub

| Source | Access Method |
|---|---|
| GitHub Trending (Python, overall) | Scrape / API |
| Specific org new repos: huggingface, openai, google-deepmind, meta-llama, microsoft, stability-ai | GitHub API |
| Starred repos from followed researchers | GitHub API |
| Repository release feeds for key projects | GitHub Releases RSS |

### YouTube Channels

| Channel | Focus |
|---|---|
| Andrej Karpathy | Deep learning fundamentals |
| Two Minute Papers | Paper summaries |
| Yannic Kilcher | Paper deep-dives |
| Lex Fridman | Long-form AI interviews |
| AI Explained | News and model analysis |
| Matthew Berman | Product demos and LLM news |
| Sentdex | Practical ML |

### Podcasts

| Podcast | Focus |
|---|---|
| Lex Fridman Podcast | Long-form research interviews |
| The TWIML AI Podcast | Industry + research |
| Practical AI | Applied ML |
| No Priors | Andreessen Horowitz AI |
| Eye on AI | Weekly AI news |
| The Gradient Podcast | Research-focused |

### Funding & Business Intel

| Source | Type |
|---|---|
| Crunchbase (AI companies filter) | Funding rounds |
| TechCrunch AI section | News RSS |
| VentureBeat AI | News RSS |
| The Information (AI section) | Premium — manual check |
| Bloomberg Technology | News |

---

## Source Management System

The sources list above must be treated as a **living registry**, not a static document. As the AI landscape shifts, some sources become irrelevant, new ones emerge, and access methods change.

### Source Record Structure

Every source in the registry should be stored as a structured record:

```
{
  id:           unique slug (e.g., "arxiv-cs-ai")
  name:         display name
  category:     research | social | company | newsletter | github | video | podcast | funding
  url:          canonical URL
  access:       rss | api | scrape | manual
  enabled:      true / false
  priority:     high | medium | low
  refresh:      how often to pull (e.g., "daily", "6h", "weekly")
  added_on:     date
  last_checked: date
  notes:        any special instructions or caveats
}
```

### Source Lifecycle Rules

- **Adding a source**: any source added must have a valid `access` method defined; no source is added without knowing how it will be fetched
- **Disabling a source**: sources are never deleted — they are set to `enabled: false` with a note explaining why (e.g., "API deprecated", "paywall added", "low signal quality")
- **Reviewing sources**: a quarterly review process to audit which sources are still producing quality signal; sources with consistently low engagement or low relevance scores get demoted or disabled
- **Priority levels**: high-priority sources are fetched more frequently and shown first; low-priority sources are background-fetched and shown only if nothing better exists

### Source Quality Signals (automatic)

Over time, the system should track per-source quality:
- Average user engagement rate (thumbs up / thumbs down ratio)
- Deduplication rate (how often a source publishes content already seen elsewhere)
- Staleness rate (how often fetched items are old by the time they appear)

These signals should surface in the source management UI so you can make informed decisions about what to keep, boost, or remove.

---

## Within-Platform Signal Discovery System

Platforms like X, LinkedIn, and Reddit are enormous. The challenge is not just fetching from them — it is knowing *what* within them to fetch. Following the wrong accounts or subreddits produces noise. Not following enough produces blind spots.

This system solves the "what do I follow?" problem for each platform.

### The Core Idea

Every noisy platform is broken down into **follow targets** — the specific accounts, subreddits, hashtags, communities, or search terms that act as the actual signal source. The platform itself is never tracked whole; only these curated follow targets are.

```
Platform  →  Follow Targets  →  Fetched Content  →  Your Feed
  X.com       @karpathy              tweets             card
  Reddit      r/MachineLearning      posts              card
  LinkedIn    Yann LeCun             posts              card
```

### Follow Target Types by Platform

| Platform | Follow Target Type | Examples |
|---|---|---|
| **X / Twitter** | Accounts, Lists, Search terms | `@karpathy`, `list:AI-researchers`, `#NeurIPS2025` |
| **LinkedIn** | People, Companies, Hashtags | `Yann LeCun`, `Anthropic`, `#LLM` |
| **Reddit** | Subreddits, Flair filters, Keyword search | `r/MachineLearning`, `r/LocalLLaMA flair:News` |
| **YouTube** | Channels, Playlists | `@YannicKilcher`, `@TwoMinutePapers` |
| **GitHub** | Orgs, Users, Topics, Trending | `huggingface`, `topic:large-language-model` |
| **Podcasts** | Show RSS feeds | `Lex Fridman Podcast` RSS |
| **Newsletters** | RSS or email | `The Batch` RSS |

### How the Discovery System Works

**Step 1 — Seed list**
Start with a manually curated seed list of follow targets (the accounts and subreddits already listed in this document). These are the known-good starting points.

**Step 2 — Automated suggestions**
The system periodically suggests new follow targets based on:
- Content you gave thumbs up to — "the account that posted this has 3 more posts you liked, do you want to follow them?"
- Co-citation / co-mention — accounts or subreddits that frequently appear together with sources you already follow
- Trending in your interest areas — new accounts gaining traction in AI that are not yet in your list

**Step 3 — User approval gate** *(see Source Approval System below)*
Suggested targets go into a queue. You approve or reject each one before it starts contributing to your feed.

**Step 4 — Ongoing quality tracking**
Each follow target accumulates a signal quality score over time based on your feedback. Targets with low scores are flagged for review.

### Per-Platform Notes

**X / Twitter**
- Track specific accounts, not the full timeline
- Twitter Lists are very useful — maintain one private list of AI researchers and pull from that
- Search terms like `"new paper" AI filter:links` can surface relevant content beyond followed accounts

**LinkedIn**
- LinkedIn has no public API; scraping is difficult and against ToS at scale
- Practical approach: track specific people's posts by monitoring their public profile URLs periodically
- Focus on a small list of high-signal people (< 30) rather than broad keyword searches
- Hashtag feeds (`#GenerativeAI`, `#LLM`) can be scraped but tend to be noisy

**Reddit**
- Subreddits are the primary follow target
- Within a subreddit, filter by `Hot` or `Top / Week` to avoid low-quality posts
- Optional: keyword filters within a subreddit (e.g., only posts in r/MachineLearning containing "paper" or "code")
- Reddit's public JSON API (`/r/subreddit.json`) is the most reliable access method

**GitHub**
- Follow specific organizations (huggingface, openai, google-deepmind, etc.) via their public activity feed
- Monitor GitHub trending daily — it surfaces new repos gaining stars fast
- Watch releases on key repos (transformers, llama.cpp, ollama, etc.)

---

## Source Approval & Rating System

No source or follow target should enter the live feed without explicit approval. This is the **curation gate** — the mechanism that keeps the feed high-quality and prevents noise from creeping in.

### How It Works

**New sources (accounts, subreddits, channels, etc.) go through a two-step process:**

```
Suggested  →  Review Queue  →  [Approve / Reject]  →  Live / Archived
```

1. A source is surfaced (either suggested by the system or manually added)
2. It enters a **Review Queue** — it does not fetch or display anything yet
3. You are shown a preview: the source's name, description, a sample of recent posts from it
4. You assign a rating and approve or reject it

### Rating Scale

| Rating | Meaning | Effect |
|---|---|---|
| ⭐⭐⭐ High signal | Consistently excellent, must-follow | Fetched frequently, shown at top of feed |
| ⭐⭐ Medium signal | Sometimes good, worth monitoring | Fetched on standard cadence, normal ranking |
| ⭐ Low signal | Occasional gems, mostly noise | Fetched infrequently, shown only if nothing better |
| ✗ Rejected | Not relevant, too noisy, off-topic | Never fetched, archived in registry |

### Ongoing Re-rating

Sources are not rated once and forgotten. The system should:
- Track each source's **signal-to-noise ratio** over time (thumbs up rate on its posts)
- Flag sources whose quality has dropped ("This source had a thumbs-up rate of 60% last month, now 15%")
- Surface these flagged sources for your re-review during a periodic **Source Audit**
- Suggest demoting or disabling sources that consistently underperform

### Source Audit Cadence

| Review Type | Frequency | What Happens |
|---|---|---|
| New suggestions review | As they appear (batched weekly) | Approve or reject new follow targets |
| Quality check | Monthly | Review sources whose signal score dropped |
| Full audit | Quarterly | Review all active sources; prune dead/low-value ones |

### Why Rejected Sources Are Never Deleted

A rejected source is archived, not removed. Reasons:
- The source may become relevant later (e.g., a researcher who wasn't active before suddenly starts posting important work)
- It creates an audit trail — you can see what was considered and why it was excluded
- If someone else uses the platform (Phase 2 multi-user), they may want a source you rejected

---

## Data Fetching Philosophy

**This is a curator, not a copy machine.**

The website does not need to scrape and store full article content. Its job is to:
1. Fetch metadata — title, summary/snippet, source name, author, date, original URL
2. Display that metadata as a card in your feed
3. When you tap/click a card → open the original source in a new tab

This approach has several advantages:
- **Legal simplicity** — you're not reproducing copyrighted content, just linking to it
- **Always fresh** — reader always sees the original, up-to-date article
- **Lower storage requirements** — store metadata only, not full text
- **Respects paywalls** — if a source is paywalled, the user decides whether they have access; you're not bypassing anything

### What gets stored locally
- Article metadata (title, URL, source, date, short snippet/abstract)
- Your feedback on each item (thumbs up/down, bookmarked, read/unread)
- Source registry and configuration
- User preferences

### What never gets stored
- Full article text
- Images from third-party sources
- Paywalled content

### Fetch methods by source type

| Source Type | Preferred Method | Fallback |
|---|---|---|
| Blogs / news sites | RSS feed | HTML scrape of headlines only |
| arXiv | arXiv API | RSS |
| Reddit | Reddit JSON API (public) | RSS |
| GitHub | GitHub REST API | RSS (releases/trending) |
| X / Twitter | Twitter API v2 (limited free tier) | Nitter RSS instance |
| Hugging Face | HF Hub API | RSS |
| Newsletters | RSS (most publish one) | Email forwarding → parse |
| YouTube | YouTube Data API | RSS (channel feed) |
| Conference sites | HTML scrape of proceedings page | Manual entry |

---

## UI / UX Requirements

**This is a high priority.** The interface must feel premium and be delightful to use on both laptop and mobile.

### Design Principles
- **Mobile-first**: the primary usage scenario is checking the site while traveling or on a phone — every layout decision must start from mobile and scale up to desktop
- **Modern aesthetic**: clean typography, generous whitespace, subtle animations, card-based content layout
- **Fast and snappy**: no heavy page loads; content should feel instant
- **Dark mode support**: essential for evening/night reading
- **Accessible**: readable fonts, sufficient contrast, touch-friendly tap targets (min 44px)

### Layout Targets
| Screen | Layout Goal |
|---|---|
| Mobile (< 640px) | Single-column feed, bottom nav, large tap targets |
| Tablet (640–1024px) | Two-column grid, side nav optional |
| Desktop (> 1024px) | Multi-column dashboard with sidebar filters |

### Key UI Components
- Global search bar
- Category / bucket filter tabs
- Content cards (title, source, date, summary, relevance score)
- Thumbs up / thumbs down feedback on each card
- Bookmark / save-for-later
- Source badges (Reddit, arXiv, X, etc.)
- Refresh status indicator ("Last updated: 2 hours ago")

---

## Filtering & Display Controls

The feed should be fully controllable. Every dimension of content should be filterable so that at any moment you can narrow down to exactly what you want to see — without changing your preferences permanently. Filters are temporary views; preferences are permanent settings. These are different things.

### Filter Dimensions

#### 1. Content Type
Filter by the kind of item being shown.

| Filter Value | What It Shows |
|---|---|
| Research Papers | arXiv preprints, conference papers, OpenReview submissions |
| GitHub Repos | New or trending repositories |
| Social Posts | Tweets, Reddit posts, LinkedIn posts |
| News & Blogs | Company blogs, TechCrunch, VentureBeat, etc. |
| Newsletters | Issues from subscribed newsletters |
| Model Releases | New LLM / model announcements |
| Videos | YouTube videos from tracked channels |
| Podcasts | New podcast episodes |
| Funding / Business | Funding rounds, acquisitions, company news |

#### 2. Platform / Source
Filter by where the content came from.

- arXiv, Papers With Code, Semantic Scholar
- X / Twitter
- Reddit (and by specific subreddit)
- LinkedIn
- GitHub
- Hugging Face
- Specific company blogs (OpenAI, Anthropic, DeepMind…)
- Specific newsletters (The Batch, Import AI…)
- YouTube
- Podcast feeds

#### 3. Topic / Subject Area
Filter by the AI subfield or theme.

| Topic Tag | Covers |
|---|---|
| Large Language Models | GPT, Claude, Gemini, Llama, fine-tuning, prompting |
| Computer Vision | Image generation, object detection, video models |
| Multimodal | Models combining text, image, audio, video |
| Reinforcement Learning | RL, RLHF, agent training |
| AI Safety & Alignment | Alignment research, interpretability, red-teaming |
| Robotics & Embodied AI | Physical robots, simulation, motor control |
| AI Agents | Autonomous agents, tool-use, planning |
| Audio / Speech | TTS, ASR, music generation |
| Open Source AI | Open weights models, open tooling |
| AI Infrastructure | Training infra, serving, efficiency, quantization |
| Products & Applications | Consumer products, APIs, enterprise tools |
| Funding & Business | Company news, funding rounds, acquisitions |

> Topics are auto-tagged on ingestion using keyword matching or a lightweight classifier. Tags can be manually corrected.

#### 4. Time Range
Filter by when the item was published or fetched.

- Today
- Last 24 hours
- Last 3 days
- This week
- This month
- Custom date range (date picker)

#### 5. People & Organizations
Filter by a specific person or company.

- Show only content from / about a specific researcher (e.g., Andrej Karpathy)
- Show only content from / about a specific company (e.g., Anthropic)
- Combine: "Andrej Karpathy AND open source"

#### 6. Source Quality / Rating
Filter by the quality rating assigned to the source during the approval process.

- High signal only (⭐⭐⭐)
- High + Medium signal (⭐⭐ and above)
- All approved sources
- Include low-signal sources

#### 7. Read Status
Filter by whether you have already seen the item.

- Unread only (default view)
- Read only
- Bookmarked / Saved
- All items

#### 8. Your Feedback
Filter by how you have rated content in the past.

- Items you liked (thumbs up)
- Items you haven't rated yet
- Items similar to ones you liked
- Items you disliked (thumbs down) — useful for auditing why

#### 9. Trending / Popularity
Filter by how much traction an item has on its original platform.

- Highly cited / high-star repos
- High-engagement tweets (retweets, replies)
- Top posts of the week on Reddit
- Viral / fast-rising items

---

### Filter UI Design

**Filters should be fast and frictionless.** The design must support quick switching between different views without hunting through menus.

| Component | Behaviour |
|---|---|
| **Top filter bar** | Horizontal scrollable pill chips for the most-used filters (Content Type, Time Range, Read Status). Always visible. |
| **Filter drawer / panel** | Slide-in panel (mobile) or sidebar (desktop) for advanced filters — topic tags, source quality, people/orgs, feedback. |
| **Active filter indicator** | When any non-default filter is active, a visible badge shows how many filters are on and a one-tap "Clear all" resets to default. |
| **Saved filter sets** | Save a named combination of filters as a "View" (e.g., "Papers only — this week", "Morning digest — high signal"). Switch between saved views with one tap. |
| **Default view** | Unread + All content types + Last 7 days + High & Medium signal. Configurable. |

### Saved Views (Presets)

Pre-built filter combinations that can be accessed in one tap:

| View Name | Filters Applied |
|---|---|
| **Morning Digest** | Unread · Last 24h · High signal · All types |
| **Papers Only** | Research Papers · Last 7 days · Unread |
| **What's Trending** | All types · Trending/Popular · Last 3 days |
| **Open Source Watch** | GitHub Repos + Topic: Open Source AI · Last 7 days |
| **Company Updates** | News & Blogs · Company blogs only · Last 7 days |
| **Deep Dive** | Research Papers + Newsletters · Any time · Bookmarked |

> Saved views are fully customizable. The user can create, rename, reorder, and delete their own views.

---

## Personalization & Feedback System

- Thumbs up / thumbs down on individual items
- System learns preferences over time and re-ranks future content
- Explicit preference settings panel (e.g., "more papers, fewer product news")
- Ability to mute specific sources, people, or topics
- "Show more like this" action on any card

---

## Content Refresh Cadence

- Configurable globally and per-source
- Suggested defaults:
  - X / Twitter: every 4–6 hours
  - Reddit: every 6–12 hours
  - arXiv: daily (new submissions post at ~midnight UTC)
  - GitHub trending: daily
  - Conference news: weekly
- "Refresh now" manual trigger always available

---

## User & Auth Model

**Phase 1 — Single User (MVP)**
- No authentication required
- Built for personal use only
- Preferences stored in a local config or simple DB

**Phase 2 — Multi-User**
- User accounts and login (email/password or OAuth)
- Per-user preference profiles stored server-side
- Feed personalized per user based on their feedback history

---

## Development Philosophy (from ECC Best Practices)

Following the patterns from [everything-claude-code](https://github.com/affaan-m/everything-claude-code):

- **Plan before building** — every phase begins with a written plan document; no implementation without a plan
- **Incremental delivery** — ship in small, working increments; no big-bang releases
- **Conventional commits** — use `feat:`, `fix:`, `docs:`, `test:` prefixes on all commits
- **Dev → Prod pipeline** — develop and validate locally before any production deployment
- **Skill-first workflow** — use ECC skills to drive development tasks (planning, review, testing, deployment)
- **Versioned roadmap** — maintain a living roadmap document that updates as the project evolves
- **Test coverage** — aim for 80%+ on all scripts and utility functions
- **Code style** — camelCase filenames, relative imports, no vague commit messages

---

## Development Roadmap

### Phase 1 — Foundation (MVP)

**Goal**: A working personal feed with at least 2–3 data sources, basic UI, running locally.

#### Sub-phase 1.1 — Planning & Architecture
- [ ] Finalize tech stack decision (frontend framework, backend, DB)
- [ ] Define data models (articles, sources, user preferences)
- [ ] Design system: choose component library or define design tokens
- [ ] Set up project structure following ECC conventions
- [ ] Write `ROADMAP.md` and initial `CLAUDE.md`

#### Sub-phase 1.2 — Core Backend
- [ ] Scraper / fetcher for 2–3 sources (arXiv + Reddit as starting point)
- [ ] Data normalization layer (unified article schema)
- [ ] Simple storage (SQLite or JSON-file for MVP)
- [ ] Scheduled refresh job (cron or background task)
- [ ] Basic REST or tRPC API

#### Sub-phase 1.3 — Core Frontend
- [ ] Mobile-first layout scaffolding
- [ ] Content card component
- [ ] Feed view (list of cards, infinite scroll or pagination)
- [ ] Category filter tabs
- [ ] Dark mode toggle
- [ ] "Last updated" indicator

#### Sub-phase 1.4 — Polish & Local Testing
- [ ] Responsive testing across breakpoints
- [ ] Basic error states (empty feed, fetch failed)
- [ ] Manual end-to-end test of the fetch → display pipeline

---

### Phase 2 — Personalization & More Sources

**Goal**: Feedback loop working, more sources added, preferences persist.

#### Sub-phase 2.1 — Feedback System
- [ ] Thumbs up / thumbs down UI on cards
- [ ] Preference storage (DB or config)
- [ ] Basic re-ranking algorithm based on feedback

#### Sub-phase 2.2 — Additional Sources
- [ ] GitHub trending repos
- [ ] X / Twitter (via API or scrape)
- [ ] LinkedIn (research feasibility — may need unofficial API)
- [ ] Hugging Face model releases
- [ ] Newsletter RSS feeds

#### Sub-phase 2.3 — Discovery Features
- [ ] "Trending this week" section
- [ ] "You haven't seen" highlight
- [ ] Global search across all fetched content
- [ ] Bookmarks / save-for-later

---

### Phase 3 — Multi-User & Production

**Goal**: Auth system, production deployment, shareable with others.

#### Sub-phase 3.1 — Authentication
- [ ] User registration and login
- [ ] Per-user preference profiles
- [ ] Session management

#### Sub-phase 3.2 — Production Infrastructure
- [ ] Choose hosting (Vercel, Railway, Fly.io, etc.)
- [ ] Environment config (dev vs. prod)
- [ ] Database migration from SQLite to PostgreSQL (if needed)
- [ ] CI/CD pipeline

#### Sub-phase 3.3 — Quality & Monitoring
- [ ] Error monitoring (Sentry or similar)
- [ ] Uptime monitoring
- [ ] Performance audit (mobile Lighthouse score target: >90)

---

## Skills & Sub-Agents to Use During Development

Following ECC conventions, these are the recommended skills and agents to activate at each phase:

| Phase | ECC Skills / Agents to Use |
|---|---|
| Planning | `ecc:plan`, `ecc:plan-prd`, `ecc:blueprint` |
| Architecture | `ecc:api-design`, `ecc:backend-patterns`, `ecc:frontend-patterns` |
| Frontend | `ecc:react-patterns`, `ecc:react-build`, `ecc:react-review`, `ecc:motion-ui` |
| Mobile UI | `ecc:frontend-a11y`, `ecc:make-interfaces-feel-better`, `ecc:liquid-glass-design` |
| Backend | `ecc:fastapi-patterns` or `ecc:nodejs-*`, `ecc:database-migrations` |
| Testing | `ecc:react-test`, `ecc:e2e-testing`, `ecc:tdd-workflow` |
| Code Review | `ecc:code-review`, `ecc:react-review`, `ecc:python-review` |
| Security | `ecc:security-review`, `ecc:security-scan` |
| Deployment | `ecc:deployment-patterns`, `ecc:docker-patterns` |
| Data Fetching | `ecc:data-scraper-agent`, `ecc:api-connector-builder` |

**Sub-agents to define for this project** (to be created as work progresses):
- `news-fetcher-agent` — responsible for pulling and normalizing content from each source
- `ranker-agent` — re-ranks content based on user feedback and preferences
- `dedup-agent` — detects and merges duplicate stories across sources
- `ui-reviewer-agent` — reviews frontend components for mobile responsiveness and accessibility

---

## Naming

A good product name is needed. Criteria: memorable, reflects AI + news/tracking/intelligence theme, ideally short (1–2 words).

> Name brainstorming is a separate discussion — to be finalized before Phase 1.2.

---

## V3 Redesign Plan — Approved 2026-06-11

This section is the authoritative plan for the frontend redesign, summarization feature, story clustering, and free hosting. It incorporates user feedback from `app-feedback-v1.md`.

### Requirements

1. **Exactly 4 navigation destinations**: Feed, Discover, Sources, Settings. Bottom nav on mobile (primary use: traveling), sidebar on desktop. Bookmarks folds into Feed as a "Saved" filter chip; the Accounts page folds into Sources as a "Follow targets" tab.
2. **1-minute summaries**: tapping a card opens a summary view (bottom sheet on mobile, side panel on desktop) — ~150 words plus 3 key takeaways, generated on first open and cached in the DB. Prominent "Read at source →" button links out. The small external-link icon still deep-links directly.
3. **Story clustering — the feed must feel finite** (from app-feedback-v1): related items about the same event (e.g., "Qwen 3 released") are grouped into one **Story** card instead of many near-duplicate posts. Tapping a story shows everything related — papers, GitHub repos, Reddit threads, blog posts — inside the site, each linking out. The default feed shows a bounded digest of today's stories ("You're caught up" at the end), never an infinite list, unless the user explicitly asks for more.
4. **Discover page**: global search, trending now, topic explorer grid, and the source-suggestion approve/reject queue.
5. **Professional, non-AI-ish design**: editorial direction — serif display typography, warm neutral palette with one restrained accent, no gradients/sparkles/glassmorphism, <200ms transitions, 44px tap targets, dark mode parity.
6. **Source health visibility**: every source's last fetch status, error, and item count visible in the Sources UI; a check script validates all fetchers.

### Architecture decisions (scalability path)

| Decision | Now (free, single-user) | Scales later to | How |
|---|---|---|---|
| Summarizer | Groq free tier (`llama-3.1-8b-instant`) | Claude / Gemini / Ollama | `SummaryProvider` interface; env-var selected |
| Scheduling | APScheduler in-process | Celery + Redis (Phase 3) | Fetch logic untouched; only the trigger wrapper swaps |
| Database | SQLite on persistent disk | PostgreSQL | Async SQLAlchemy 2.x + dialect-neutral Alembic migrations |
| Hosting | Vercel (FE) + Render free (BE) | Paid tiers | Config only |
| API | REST `/api/v1/` | Multi-user | Auth middleware added later without breaking routes |

Compliance note: full article text is fetched transiently for summarization and discarded; only the generated derivative summary is stored (per the "never store full article text" rule). ADRs to be written for Groq-over-Ollama, APScheduler-over-Celery, Render-over-Railway.

### Execution phases

| # | Phase | Contents |
|---|---|---|
| 0 | Source health audit | `last_fetch_status`/`last_fetch_error` on Source; `scripts/check_sources.py`; `GET /api/v1/sources/health`; fix broken fetchers |
| 1 | Summarizer backend | `services/summarizer.py` (httpx + trafilatura extraction, Groq/Ollama providers); `Article.ai_summary` migration; `GET /articles/{id}/summary` (cached-or-generate, marks read); TDD |
| 2 | APScheduler | `core/scheduler.py` in FastAPI lifespan; intervals from source priority; manual refresh kept; Redis/Celery removed from runtime |
| 3 | Story clustering | `services/story_clusterer.py` groups recent articles by event (entity/keyword + title similarity); `Story` model + `/api/v1/stories`; bounded daily digest |
| 4 | Nav restructure | 4 tabs; delete `/bookmarks` and `/accounts` pages; fold into Feed chip and Sources tab |
| 5 | Summary UI | `SummarySheet` bottom sheet / side panel with loading, error→snippet fallback, takeaways, actions |
| 6 | Discover | Search (existing endpoint), trending rail, topic grid, suggestions queue |
| 7 | Visual redesign | Tokens, serif display font via `next/font`, restyled cards/header/filters/states, story-first feed, breakpoint + dark-mode verification |
| 8 | Deploy + validate | `render.yaml`, env templates, keep-awake ping, pytest ≥80% on services/fetchers, frontend tests + build, source check green |

### Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Dead sources (esp. Nitter instances) | High | Phase 0 audit; fallback methods; health visible in UI |
| Render cold starts (~30–60s) | High | cron-job.org ping to `/health` every 10 min |
| Groq free-tier limits | Low | On-demand + cached summaries = tens of calls/day; provider swap is config |
| Clustering quality (over/under-grouping) | Medium | Conservative similarity threshold; singleton stories are fine; tags manually correctable |

---

## Open Questions (to resolve before Phase 1.1)

1. **Tech stack**: React + Next.js? Vue? What backend — Node.js, Python/FastAPI?
2. **Data sources priority**: Which 2–3 to implement first for MVP?
3. **Fetch strategy**: APIs vs. RSS vs. scraping — per source?
4. **Storage**: SQLite for MVP → PostgreSQL for prod, or start with Postgres?
5. **Hosting target**: Local-only first, then which platform for prod?
6. **UI library**: Tailwind + shadcn/ui? Or fully custom design system?
7. **Refresh trigger**: Cron job, background worker, or on-demand
