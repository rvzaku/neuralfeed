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

    # Summarization — provider is swappable via env (groq | ollama)
    summary_provider: str = "groq"
    summary_model: str = ""  # empty → provider default
    groq_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"


settings = Settings()
