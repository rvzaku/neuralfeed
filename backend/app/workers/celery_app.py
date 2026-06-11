from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "neural_feed",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.fetch_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    beat_schedule={
        "fetch-arxiv-daily": {
            "task": "app.workers.fetch_tasks.fetch_source",
            "schedule": 86400,  # 24h
            "args": ["arxiv-cs-ai"],
        },
        "fetch-arxiv-cv-daily": {
            "task": "app.workers.fetch_tasks.fetch_source",
            "schedule": 86400,
            "args": ["arxiv-cs-cv"],
        },
        "fetch-reddit-ml-8h": {
            "task": "app.workers.fetch_tasks.fetch_source",
            "schedule": 28800,  # 8h
            "args": ["reddit-ml"],
        },
        "fetch-reddit-localllama-8h": {
            "task": "app.workers.fetch_tasks.fetch_source",
            "schedule": 28800,
            "args": ["reddit-localllama"],
        },
        "fetch-reddit-artificial-12h": {
            "task": "app.workers.fetch_tasks.fetch_source",
            "schedule": 43200,  # 12h
            "args": ["reddit-artificial"],
        },
        "fetch-github-trending-daily": {
            "task": "app.workers.fetch_tasks.fetch_source",
            "schedule": 86400,
            "args": ["github-trending"],
        },
        "fetch-rss-blogs-6h": {
            "task": "app.workers.fetch_tasks.fetch_all_rss",
            "schedule": 21600,  # 6h
        },
        # Phase 2 — additional fetchers
        "fetch-hf-models-6h": {
            "task": "app.workers.fetch_tasks.fetch_source",
            "schedule": 21600,
            "args": ["hf-models"],
        },
        "fetch-youtube-daily": {
            "task": "app.workers.fetch_tasks.fetch_source",
            "schedule": 86400,
            "args": ["youtube-ai"],
        },
        "fetch-nitter-6h": {
            "task": "app.workers.fetch_tasks.fetch_source",
            "schedule": 21600,
            "args": ["twitter-nitter"],
        },
        # Additional Reddit subreddits
        "fetch-reddit-singularity-12h": {
            "task": "app.workers.fetch_tasks.fetch_source",
            "schedule": 43200,
            "args": ["reddit-singularity"],
        },
        "fetch-reddit-chatgpt-8h": {
            "task": "app.workers.fetch_tasks.fetch_source",
            "schedule": 28800,
            "args": ["reddit-chatgpt"],
        },
        "fetch-reddit-claudeai-12h": {
            "task": "app.workers.fetch_tasks.fetch_source",
            "schedule": 43200,
            "args": ["reddit-claudeai"],
        },
        "fetch-reddit-openai-12h": {
            "task": "app.workers.fetch_tasks.fetch_source",
            "schedule": 43200,
            "args": ["reddit-openai"],
        },
        "fetch-reddit-stablediffusion-12h": {
            "task": "app.workers.fetch_tasks.fetch_source",
            "schedule": 43200,
            "args": ["reddit-stablediffusion"],
        },
        "fetch-reddit-learnml-daily": {
            "task": "app.workers.fetch_tasks.fetch_source",
            "schedule": 86400,
            "args": ["reddit-learnml"],
        },
        "fetch-reddit-deeplearning-12h": {
            "task": "app.workers.fetch_tasks.fetch_source",
            "schedule": 43200,
            "args": ["reddit-deeplearning"],
        },
    },
)
