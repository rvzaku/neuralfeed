"""Maps source_id → fetcher factory. Import this instead of the worker module
so schedulers and scripts don't need Celery."""

from typing import Optional

from app.fetchers.arxiv import ArxivFetcher
from app.fetchers.base import BaseFetcher
from app.fetchers.github_trending import GithubTopicFetcher, GithubTrendingFetcher
from app.fetchers.hackernews import HackerNewsFetcher
from app.fetchers.hf_papers import HFPapersFetcher
from app.fetchers.hf_spaces import HFSpacesFetcher
from app.fetchers.huggingface import HuggingFaceFetcher
from app.fetchers.nitter import NitterFetcher
from app.fetchers.reddit import RedditFetcher
from app.fetchers.rss import RSSFetcher, RSS_SOURCES
from app.fetchers.youtube import YouTubeFetcher

_REDDIT_IDS = [
    "reddit-ml", "reddit-localllama", "reddit-artificial",
    "reddit-singularity", "reddit-chatgpt", "reddit-claudeai",
    "reddit-openai", "reddit-stablediffusion", "reddit-learnml",
    "reddit-deeplearning",
    "reddit-mlscaling", "reddit-llmdevs", "reddit-langchain",
    "reddit-rag", "reddit-aiagents", "reddit-computervision",
    "reddit-reinforcement", "reddit-mlops",
]

FETCHER_MAP = {
    "arxiv-cs-ai":    lambda: ArxivFetcher("arxiv-cs-ai"),
    "arxiv-cs-cv":    lambda: ArxivFetcher("arxiv-cs-cv"),
    "github-trending": lambda: GithubTrendingFetcher(),
    "hackernews-ai":  lambda: HackerNewsFetcher(),
    "hf-papers":      lambda: HFPapersFetcher(),
    "hf-models":      lambda: HuggingFaceFetcher(),
    "hf-spaces":      lambda: HFSpacesFetcher(),
    "youtube-ai":     lambda: YouTubeFetcher(),
    "twitter-nitter": lambda: NitterFetcher(),
    **{sid: (lambda sid=sid: RedditFetcher(sid)) for sid in _REDDIT_IDS},
    **{sid: (lambda sid=sid: RSSFetcher(sid)) for sid in RSS_SOURCES},
}


def is_fetchable(source_id: str) -> bool:
    return source_id in FETCHER_MAP or source_id.startswith("custom-")


def resolve_fetcher(source_id: str, url: Optional[str] = None) -> Optional[BaseFetcher]:
    """Fetcher for a source id. Static sources come from FETCHER_MAP;
    user-added custom-* sources (V8) are resolved from their stored URL."""
    factory = FETCHER_MAP.get(source_id)
    if factory:
        return factory()
    if not url:
        return None
    if source_id.startswith("custom-rss-"):
        return RSSFetcher(source_id, feed_url=url)
    if source_id.startswith("custom-reddit-"):
        return RedditFetcher(source_id, sub=url.rstrip("/").rsplit("/r/", 1)[-1])
    if source_id.startswith("custom-github-"):
        return GithubTopicFetcher(source_id, url.rstrip("/").rsplit("/", 1)[-1])
    return None
