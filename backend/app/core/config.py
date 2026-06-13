from typing import Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "sqlite+aiosqlite:///./neuralFeed.db"
    redis_url: str = "redis://localhost:6379/0"
    arxiv_api_base: str = "https://export.arxiv.org/api/query"
    reddit_user_agent: str = "NeuralFeed/0.1 (personal)"
    github_token: str = ""
    twitter_bearer_token: str = ""
    hf_api_token: str = ""
    # Accepts JSON ('["https://a","https://b"]') or comma-separated ("https://a,https://b")
    cors_origins: Union[str, list[str]] = [
        "http://localhost:3000",
        "https://neuralfeed.vercel.app",
    ]

    @field_validator("cors_origins", mode="after")
    @classmethod
    def _split_cors_origins(cls, v: Union[str, list[str]]) -> list[str]:
        if isinstance(v, str):
            v = v.split(",")
        # Browsers send Origin without a trailing slash; exact match would fail
        return [o.strip().rstrip("/") for o in v if o.strip()]

    # In-process scheduled fetching (replaces Celery beat for single-user deploys)
    scheduler_enabled: bool = True
    # V6: keep the feed fresh — no source waits longer than this between fetches,
    # so the user always has new relevant material within the window (3-4h).
    refresh_max_hours: int = 2

    # Auth (Phase 3.1) — gate is off by default so single-user deploys keep working
    auth_required: bool = False
    jwt_secret: str = "dev-secret-change-me"  # MUST override in production env
    jwt_expires_minutes: int = 60 * 24 * 7  # 7 days

    # Set false after creating your account to close public signup
    allow_registration: bool = True

    # Monitoring (Phase 3.3) — leave empty to disable
    sentry_dsn: str = ""

    # Feed ranked-order cache (Redis). Degrades to a no-op if Redis is
    # unreachable, so the feed still works without it — see app/core/cache.py.
    feed_cache_enabled: bool = True
    feed_cache_ttl_seconds: int = 45

    # Rate limiting (per-IP, in-memory; single-instance deploys)
    rate_limit_enabled: bool = True
    rate_limit_auth_per_minute: int = 10
    rate_limit_write_per_minute: int = 60

    # LinkedIn public-page bridge (V6): RSSHub turns public company pages into
    # RSS without touching LinkedIn directly or scraping private content. Point
    # at a self-hosted instance for reliability; the public instance is default.
    rsshub_base: str = "https://rsshub.app"

    # Summarization — provider is swappable via env (groq | ollama)
    summary_provider: str = "groq"
    summary_model: str = ""  # empty → provider default
    # Title/summary enrichment for slug-named items. Defaults to the stronger
    # 70b model: titles are the most-complained-about surface, and a weak 8b
    # model produced bland, repo-name-echoing headlines. Override to a faster
    # model only if the enrich backlog can't keep up.
    enrich_model: str = "llama-3.3-70b-versatile"
    groq_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"


settings = Settings()
