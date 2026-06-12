"""Maps source_id → fetcher factory. Import this instead of the worker module
so schedulers and scripts don't need Celery."""

from app.fetchers.arxiv import ArxivFetcher
from app.fetchers.github_trending import GithubTrendingFetcher
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
