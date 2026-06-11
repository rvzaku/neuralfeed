# NeuralFeed — Source Registry

This is the living registry of all sources. **Never delete a source** — set `enabled: false` with a note.

## MVP Sources (Phase 1)

| ID | Name | Category | Access | Priority | Refresh | Enabled |
|---|---|---|---|---|---|---|
| `arxiv-cs-ai` | arXiv cs.AI + cs.LG + cs.CL | research | api | high | daily | ✓ |
| `arxiv-cs-cv` | arXiv cs.CV + stat.ML | research | api | medium | daily | ✓ |
| `reddit-ml` | r/MachineLearning | social | api | high | 8h | ✓ |
| `reddit-localllama` | r/LocalLLaMA | social | api | high | 8h | ✓ |
| `reddit-artificial` | r/artificial | social | api | medium | 12h | ✓ |
| `github-trending` | GitHub Trending (Python/AI) | github | scrape | high | daily | ✓ |
| `rss-openai` | OpenAI Blog | company | rss | high | 6h | ✓ |
| `rss-anthropic` | Anthropic Blog | company | rss | high | 6h | ✓ |
| `rss-deepmind` | Google DeepMind Blog | company | rss | high | 6h | ✓ |
| `rss-huggingface` | Hugging Face Blog | company | rss | medium | 8h | ✓ |
| `rss-metaai` | Meta AI Blog | company | rss | medium | 8h | ✓ |

## Phase 2 Sources (planned)

| ID | Name | Category | Access | Priority | Notes |
|---|---|---|---|---|---|
| `hf-models` | HuggingFace Model Releases | research | api | high | Phase 2.2 |
| `newsletter-batch` | The Batch (DeepLearning.AI) | newsletter | rss | high | Phase 2.2 |
| `newsletter-importai` | Import AI (Jack Clark) | newsletter | rss | high | Phase 2.2 |
| `newsletter-tldr-ai` | TLDR AI | newsletter | rss | medium | Phase 2.2 |
| `newsletter-aheadofai` | Ahead of AI (Raschka) | newsletter | rss | high | Phase 2.2 |
| `newsletter-lastweekinai` | Last Week in AI | newsletter | rss | medium | Phase 2.2 |
| `yt-karpathy` | Andrej Karpathy (YouTube) | video | rss | high | Phase 2.2 |
| `yt-twominutepapers` | Two Minute Papers | video | rss | high | Phase 2.2 |
| `yt-yannic` | Yannic Kilcher | video | rss | high | Phase 2.2 |
| `twitter-researchers` | AI Researchers (X/Twitter) | social | api | high | Phase 2.2 — feasibility gate |
| `linkedin-researchers` | AI Researchers (LinkedIn) | social | scrape | medium | Phase 2.2 — ToS review needed |

## Source Lifecycle Rules

1. **Adding**: must have a valid `access` method before going live
2. **Disabling**: set `enabled: false` with a note — never delete
3. **Quality review**: monthly for sources with signal_score < 0.3
4. **Full audit**: quarterly — prune stale or low-value sources

## RSS Feed URLs

| Source ID | Feed URL |
|---|---|
| `rss-openai` | `https://openai.com/blog/rss.xml` |
| `rss-anthropic` | `https://www.anthropic.com/rss.xml` |
| `rss-deepmind` | `https://deepmind.google/blog/rss.xml` |
| `rss-huggingface` | `https://huggingface.co/blog/feed.xml` |
| `rss-metaai` | `https://ai.meta.com/blog/rss/` |

## V4 Additions (2026-06-12)

| Source ID | Name | Category | Access | Status |
|---|---|---|---|---|
| `conf-neurips` | NeurIPS Blog | conference | rss | live (feed verified) |
| `conf-iclr` | ICLR Blog | conference | rss | live (feed verified) |
| `conf-acl` | ACL 2025 News | conference | rss | live (sparse feed) |
| `conf-icml` | ICML News | conference | manual | disabled — no RSS feed exists |
| `conf-cvpr` | CVPR News | conference | manual | disabled — no RSS feed exists |
| `producthunt-ai` | Product Hunt — AI | product | rss | live (feed verified) |
| `hf-spaces` | HuggingFace Trending Spaces | product | api | live |

## LinkedIn Stance (V4)

LinkedIn has no public API and scraping it at scale violates its ToS. NeuralFeed therefore
supports LinkedIn only as **curated manual follow targets**: `watched_accounts` rows with
`platform='linkedin'` whose cards link out to the person's public profile/activity page.
No automated LinkedIn fetching is implemented, deliberately.
