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
    cors_origins: list[str] = ["http://localhost:3000"]


settings = Settings()
