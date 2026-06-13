from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.source import Source


async def seed_accounts(db: AsyncSession) -> None:
    """Populate watched_accounts from curated_accounts.json on first startup."""
    from app.fetchers.account_discovery import discover_accounts
    await discover_accounts(db)

ALL_SOURCES = [
    # ── Phase 1 — MVP ────────────────────────────────────────────────────────
    {"id": "arxiv-cs-ai",        "name": "arXiv cs.AI + cs.LG + cs.CL",       "category": "research",    "url": "https://export.arxiv.org/api/query",                          "access": "api",    "priority": "high",   "refresh_interval": "daily"},
    {"id": "arxiv-cs-cv",        "name": "arXiv cs.CV + stat.ML",              "category": "research",    "url": "https://export.arxiv.org/api/query",                          "access": "api",    "priority": "medium", "refresh_interval": "daily"},
    {"id": "reddit-ml",          "name": "r/MachineLearning",                  "category": "social",      "url": "https://www.reddit.com/r/MachineLearning",                    "access": "api",    "priority": "high",   "refresh_interval": "8h"},
    {"id": "reddit-localllama",  "name": "r/LocalLLaMA",                       "category": "social",      "url": "https://www.reddit.com/r/LocalLLaMA",                         "access": "api",    "priority": "high",   "refresh_interval": "8h"},
    {"id": "reddit-artificial",  "name": "r/artificial",                       "category": "social",      "url": "https://www.reddit.com/r/artificial",                         "access": "api",    "priority": "medium", "refresh_interval": "12h"},
    {"id": "github-trending",    "name": "GitHub Trending (Python/AI)",        "category": "github",      "url": "https://github.com/trending/python",                          "access": "scrape", "priority": "high",   "refresh_interval": "daily"},
    {"id": "rss-openai",         "name": "OpenAI Blog",                        "category": "company",     "url": "https://openai.com/blog/rss.xml",                             "access": "rss",    "priority": "high",   "refresh_interval": "6h"},
    {"id": "rss-anthropic",      "name": "Anthropic Blog",                     "category": "company",     "url": "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml",                           "access": "rss",    "priority": "high",   "refresh_interval": "6h"},
    {"id": "rss-deepmind",       "name": "Google DeepMind Blog",               "category": "company",     "url": "https://deepmind.google/blog/rss.xml",                        "access": "rss",    "priority": "high",   "refresh_interval": "6h"},
    {"id": "rss-huggingface",    "name": "Hugging Face Blog",                  "category": "company",     "url": "https://huggingface.co/blog/feed.xml",                        "access": "rss",    "priority": "medium", "refresh_interval": "8h"},
    {"id": "rss-metaai",         "name": "Meta AI Blog",                       "category": "company",     "url": "https://engineering.fb.com/feed/",                              "access": "rss",    "priority": "medium", "refresh_interval": "8h"},
    # ── Phase 2 — HuggingFace, YouTube, Twitter ───────────────────────────────
    {"id": "hf-models",          "name": "HuggingFace Model Releases",         "category": "research",    "url": "https://huggingface.co/api/models",                           "access": "api",    "priority": "high",   "refresh_interval": "6h"},
    {"id": "youtube-ai",         "name": "AI YouTube Channels",                "category": "video",       "url": "https://www.youtube.com/feeds/videos.xml",                    "access": "rss",    "priority": "medium", "refresh_interval": "daily"},
    {"id": "twitter-nitter",     "name": "AI Researchers (X/Twitter)",         "category": "social",      "url": "https://nitter.privacydev.net",                               "access": "scrape", "priority": "medium", "refresh_interval": "6h"},
    # ── Phase 2 — Additional Reddit subreddits ───────────────────────────────
    {"id": "reddit-singularity",     "name": "r/singularity",                  "category": "social",      "url": "https://www.reddit.com/r/singularity",                        "access": "api",    "priority": "medium", "refresh_interval": "12h"},
    {"id": "reddit-chatgpt",         "name": "r/ChatGPT",                      "category": "social",      "url": "https://www.reddit.com/r/ChatGPT",                            "access": "api",    "priority": "medium", "refresh_interval": "8h"},
    {"id": "reddit-claudeai",        "name": "r/ClaudeAI",                     "category": "social",      "url": "https://www.reddit.com/r/ClaudeAI",                           "access": "api",    "priority": "medium", "refresh_interval": "12h"},
    {"id": "reddit-openai",          "name": "r/OpenAI",                       "category": "social",      "url": "https://www.reddit.com/r/OpenAI",                             "access": "api",    "priority": "medium", "refresh_interval": "12h"},
    {"id": "reddit-stablediffusion", "name": "r/StableDiffusion",              "category": "social",      "url": "https://www.reddit.com/r/StableDiffusion",                    "access": "api",    "priority": "medium", "refresh_interval": "12h"},
    {"id": "reddit-learnml",         "name": "r/learnmachinelearning",         "category": "social",      "url": "https://www.reddit.com/r/learnmachinelearning",               "access": "api",    "priority": "low",    "refresh_interval": "daily"},
    {"id": "reddit-deeplearning",    "name": "r/deeplearning",                 "category": "social",      "url": "https://www.reddit.com/r/deeplearning",                       "access": "api",    "priority": "medium", "refresh_interval": "12h"},
    # ── Phase 2 — Company blogs (extended) ───────────────────────────────────
    {"id": "rss-googleai",       "name": "Google AI Blog",                     "category": "company",     "url": "https://blog.research.google/feeds/posts/default",            "access": "rss",    "priority": "high",   "refresh_interval": "6h"},
    {"id": "rss-msresearch",     "name": "Microsoft Research Blog",            "category": "company",     "url": "https://www.microsoft.com/en-us/research/feed/",              "access": "rss",    "priority": "medium", "refresh_interval": "8h"},
    {"id": "rss-mistral",        "name": "Mistral AI Blog",                    "category": "company",     "url": "https://mistral.ai/rss.xml",                                 "access": "rss",    "priority": "high",   "refresh_interval": "6h"},
    {"id": "rss-cohere",         "name": "Cohere Blog",                        "category": "company",     "url": "https://cohere.com/blog/rss.xml",                             "access": "rss",    "priority": "medium", "refresh_interval": "8h", "enabled": False, "notes": "Disabled 2026-06-11: feed endpoint returns 200 but zero entries"},
    {"id": "rss-stability",      "name": "Stability AI Blog",                  "category": "company",     "url": "https://stability.ai/news?format=rss",                        "access": "rss",    "priority": "medium", "refresh_interval": "8h", "enabled": False, "notes": "Disabled 2026-06-11: Squarespace feed returns no entries"},
    {"id": "rss-appleml",        "name": "Apple Machine Learning Research",    "category": "company",     "url": "https://machinelearning.apple.com/rss.xml",                   "access": "rss",    "priority": "medium", "refresh_interval": "8h"},
    {"id": "rss-awsai",          "name": "AWS Machine Learning Blog",          "category": "company",     "url": "https://aws.amazon.com/blogs/machine-learning/feed/",         "access": "rss",    "priority": "medium", "refresh_interval": "8h"},
    {"id": "rss-eleutherai",     "name": "EleutherAI Blog",                    "category": "company",     "url": "https://blog.eleuther.ai/index.xml",                                "access": "rss",    "priority": "medium", "refresh_interval": "8h"},
    {"id": "rss-ai2",            "name": "Allen Institute for AI (AI2)",       "category": "company",     "url": "https://medium.com/feed/ai2-blog",                            "access": "rss",    "priority": "medium", "refresh_interval": "8h", "enabled": False, "notes": "Disabled 2026-06-11: allenai.org/blog/rss is 404; Medium feed unreachable"},
    {"id": "rss-deepseek",       "name": "DeepSeek Blog",                      "category": "company",     "url": "https://api.deepseek.com/blog/rss",                           "access": "rss",    "priority": "high",   "refresh_interval": "6h", "enabled": False, "notes": "Disabled 2026-06-11: no public feed (endpoint returns 401)"},
    # ── Phase 2 — Newsletters ────────────────────────────────────────────────
    {"id": "newsletter-batch",        "name": "The Batch (DeepLearning.AI)",   "category": "newsletter",  "url": "https://www.deeplearning.ai/the-batch/feed/",                 "access": "rss",    "priority": "high",   "refresh_interval": "daily", "enabled": False, "notes": "Disabled 2026-06-11: feed removed from deeplearning.ai (404)"},
    {"id": "newsletter-importai",     "name": "Import AI (Jack Clark)",        "category": "newsletter",  "url": "https://importai.substack.com/feed",                          "access": "rss",    "priority": "high",   "refresh_interval": "daily"},
    {"id": "newsletter-tldr",         "name": "TLDR AI",                       "category": "newsletter",  "url": "https://tldr.tech/api/rss/ai",                                    "access": "rss",    "priority": "medium", "refresh_interval": "daily"},
    {"id": "newsletter-aheadofai",    "name": "Ahead of AI (Raschka)",         "category": "newsletter",  "url": "https://magazine.sebastianraschka.com/feed",                  "access": "rss",    "priority": "high",   "refresh_interval": "daily"},
    {"id": "newsletter-lastweekai",   "name": "Last Week in AI",               "category": "newsletter",  "url": "https://lastweekin.ai/feed",                                  "access": "rss",    "priority": "medium", "refresh_interval": "daily"},
    {"id": "newsletter-decoder",      "name": "The Decoder",                   "category": "newsletter",  "url": "https://the-decoder.com/feed/",                               "access": "rss",    "priority": "medium", "refresh_interval": "daily"},
    {"id": "newsletter-gradientflow", "name": "Gradient Flow",                 "category": "newsletter",  "url": "https://gradientflow.com/feed/",                              "access": "rss",    "priority": "medium", "refresh_interval": "daily"},
    {"id": "newsletter-aiedge",       "name": "The AI Edge",                   "category": "newsletter",  "url": "https://newsletter.theaiedge.io/feed",                        "access": "rss",    "priority": "medium", "refresh_interval": "daily"},
    {"id": "newsletter-alphasignal",  "name": "AlphaSignal",                   "category": "newsletter",  "url": "https://alphasignal.ai/rss",                                  "access": "rss",    "priority": "medium", "refresh_interval": "daily", "enabled": False, "notes": "Disabled 2026-06-11: no public RSS feed (404)"},
    {"id": "newsletter-algbridge",    "name": "The Algorithmic Bridge",        "category": "newsletter",  "url": "https://thealgorithmicbridge.substack.com/feed",              "access": "rss",    "priority": "low",    "refresh_interval": "daily"},
    {"id": "newsletter-davissummarizes", "name": "Davis Summarizes Papers",    "category": "newsletter",  "url": "https://dblalock.substack.com/feed",              "access": "rss",    "priority": "low",    "refresh_interval": "daily"},
    # ── Phase 2 — Podcasts ────────────────────────────────────────────────────
    {"id": "podcast-lexfridman",  "name": "Lex Fridman Podcast",              "category": "podcast",     "url": "https://lexfridman.com/feed/podcast/",                        "access": "rss",    "priority": "high",   "refresh_interval": "daily"},
    {"id": "podcast-twiml",       "name": "TWIML AI Podcast",                 "category": "podcast",     "url": "https://twimlai.com/feed",                                    "access": "rss",    "priority": "medium", "refresh_interval": "daily"},
    {"id": "podcast-practicalai", "name": "Practical AI",                     "category": "podcast",     "url": "https://changelog.com/practicalai/feed",                      "access": "rss",    "priority": "medium", "refresh_interval": "daily"},
    {"id": "podcast-nopriors",    "name": "No Priors",                        "category": "podcast",     "url": "https://feeds.megaphone.fm/nopriors",                      "access": "rss",    "priority": "medium", "refresh_interval": "daily"},
    {"id": "podcast-eyeonai",     "name": "Eye on AI",                        "category": "podcast",     "url": "https://aneyeonai.libsyn.com/rss",                       "access": "rss",    "priority": "medium", "refresh_interval": "daily"},
    {"id": "podcast-gradient",    "name": "The Gradient Podcast",             "category": "podcast",     "url": "https://thegradientpub.substack.com/feed",                    "access": "rss",    "priority": "medium", "refresh_interval": "daily"},
    # ── Phase V4 — Conferences (feeds verified 2026-06-12) ───────────────────
    {"id": "conf-neurips",       "name": "NeurIPS Blog",                      "category": "conference",  "url": "https://blog.neurips.cc/feed/",                               "access": "rss",    "priority": "low",    "refresh_interval": "weekly"},
    {"id": "conf-iclr",          "name": "ICLR Blog",                         "category": "conference",  "url": "https://blog.iclr.cc/feed/",                                  "access": "rss",    "priority": "low",    "refresh_interval": "weekly"},
    {"id": "conf-acl",           "name": "ACL 2025 News",                     "category": "conference",  "url": "https://2025.aclweb.org/feed.xml",                            "access": "rss",    "priority": "low",    "refresh_interval": "weekly"},
    {"id": "conf-icml",          "name": "ICML News",                         "category": "conference",  "url": "https://icml.cc",                                             "access": "manual", "priority": "low",    "refresh_interval": "weekly", "enabled": False, "notes": "Disabled 2026-06-12: no RSS feed; Medium feed unreachable"},
    {"id": "conf-cvpr",          "name": "CVPR News",                         "category": "conference",  "url": "https://cvpr.thecvf.com",                                     "access": "manual", "priority": "low",    "refresh_interval": "weekly", "enabled": False, "notes": "Disabled 2026-06-12: no RSS feed on conference site"},
    # ── Phase V4 — Products ──────────────────────────────────────────────────
    {"id": "producthunt-ai",     "name": "Product Hunt — AI",                 "category": "product",     "url": "https://www.producthunt.com/feed?category=artificial-intelligence", "access": "rss", "priority": "medium", "refresh_interval": "daily"},
    {"id": "hf-spaces",          "name": "HuggingFace Trending Spaces",       "category": "product",     "url": "https://huggingface.co/api/spaces",                           "access": "api",    "priority": "medium", "refresh_interval": "daily"},
    # ── Phase V9 — LinkedIn (Google News proxy, no LinkedIn scraping) ────────
    {"id": "linkedin-pulse",     "name": "LinkedIn (via Google News)",        "category": "social",      "url": "https://news.google.com/rss/search?q=site%3Alinkedin.com%20(AI%20OR%20LLM%20OR%20%22machine%20learning%22)%20when%3A7d&hl=en-US&gl=US&ceid=US:en", "access": "rss", "priority": "medium", "refresh_interval": "12h"},
    # ── Phase V7 — Aggregators & relevance signals ───────────────────────────
    {"id": "hackernews-ai",      "name": "Hacker News (AI)",                  "category": "social",      "url": "https://news.ycombinator.com",                                "access": "api",    "priority": "high",   "refresh_interval": "6h"},
    {"id": "hf-papers",          "name": "HF Daily Papers",                   "category": "research",    "url": "https://huggingface.co/papers",                               "access": "api",    "priority": "high",   "refresh_interval": "daily"},
    # ── Phase V7 — Topic-focused subreddits ──────────────────────────────────
    {"id": "reddit-mlscaling",       "name": "r/mlscaling",                   "category": "social",      "url": "https://www.reddit.com/r/mlscaling",                          "access": "api",    "priority": "medium", "refresh_interval": "12h"},
    {"id": "reddit-llmdevs",         "name": "r/LLMDevs",                     "category": "social",      "url": "https://www.reddit.com/r/LLMDevs",                            "access": "api",    "priority": "medium", "refresh_interval": "12h"},
    {"id": "reddit-langchain",       "name": "r/LangChain",                   "category": "social",      "url": "https://www.reddit.com/r/LangChain",                          "access": "api",    "priority": "low",    "refresh_interval": "daily"},
    {"id": "reddit-rag",             "name": "r/Rag",                         "category": "social",      "url": "https://www.reddit.com/r/Rag",                                "access": "api",    "priority": "low",    "refresh_interval": "daily"},
    {"id": "reddit-aiagents",        "name": "r/AI_Agents",                   "category": "social",      "url": "https://www.reddit.com/r/AI_Agents",                          "access": "api",    "priority": "medium", "refresh_interval": "12h"},
    {"id": "reddit-computervision",  "name": "r/computervision",              "category": "social",      "url": "https://www.reddit.com/r/computervision",                     "access": "api",    "priority": "medium", "refresh_interval": "12h"},
    {"id": "reddit-reinforcement",   "name": "r/reinforcementlearning",       "category": "social",      "url": "https://www.reddit.com/r/reinforcementlearning",              "access": "api",    "priority": "low",    "refresh_interval": "daily"},
    {"id": "reddit-mlops",           "name": "r/mlops",                       "category": "social",      "url": "https://www.reddit.com/r/mlops",                              "access": "api",    "priority": "low",    "refresh_interval": "daily"},
    # ── Phase 2 — Funding / business ─────────────────────────────────────────
    {"id": "rss-techcrunch-ai",   "name": "TechCrunch AI",                    "category": "funding",     "url": "https://techcrunch.com/category/artificial-intelligence/feed/", "access": "rss",  "priority": "medium", "refresh_interval": "8h"},
    {"id": "rss-venturebeat-ai",  "name": "VentureBeat AI",                   "category": "funding",     "url": "https://venturebeat.com/category/ai/feed/",                   "access": "rss",    "priority": "medium", "refresh_interval": "8h"},
]

# Keep backward-compat alias used in tests
MVP_SOURCES = ALL_SOURCES


async def seed_sources(db: AsyncSession) -> None:
    for src in ALL_SOURCES:
        existing = await db.get(Source, src["id"])
        if existing is None:
            db.add(Source(**{"enabled": True, **src}, added_on=date.today(), signal_score=0.5))
        elif existing.url != src["url"]:
            # Feed URL was corrected in the registry — propagate to existing rows
            existing.url = src["url"]
    await db.commit()
