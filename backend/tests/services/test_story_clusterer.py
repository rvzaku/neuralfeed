from datetime import datetime, timedelta, timezone

from app.models.article import Article
from app.services.story_clusterer import cluster_articles, title_signature


def _article(id, title, source_id="reddit-ml", trending=0.0, tags=None, read=False, age_hours=0):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    return Article(
        id=id,
        title=title,
        url=f"https://example.com/{id}",
        source_id=source_id,
        summary=None,
        published_at=now - timedelta(hours=age_hours),
        fetched_at=now,
        topic_tags=tags or [],
        is_read=read,
        is_bookmarked=False,
        trending_score=trending,
    )


class TestTitleSignature:
    def test_drops_stopwords_and_punctuation(self):
        sig = title_signature("Introducing the new Qwen 3 model!")
        assert "qwen" in sig
        assert "the" not in sig and "new" not in sig and "model" not in sig

    def test_keeps_distinguishing_tokens(self):
        assert title_signature("Qwen3 beats GPT-5") & {"qwen3", "beats", "gpt"}


class TestClusterArticles:
    def test_same_event_across_sources_merges(self):
        arts = [
            _article("a1", "Qwen 3 released with 235B parameters", "reddit-localllama", trending=900),
            _article("a2", "Alibaba releases Qwen 3 family of models", "rss-techcrunch-ai"),
            _article("a3", "QwenLM/Qwen3", "github-trending"),
            _article("a4", "Qwen 3 Technical Report", "arxiv-cs-ai"),
        ]
        stories = cluster_articles(arts)
        # The three with >=2 shared signature tokens merge; bare repo name may stand alone
        biggest = stories[0]
        assert biggest["article_count"] >= 3
        assert biggest["source_count"] >= 3
        assert biggest["headline"] == "Qwen 3 released with 235B parameters"  # most engaged

    def test_unrelated_articles_stay_separate(self):
        arts = [
            _article("b1", "Qwen 3 released with 235B parameters"),
            _article("b2", "CVPR 2026 best paper award announced"),
            _article("b3", "Anthropic ships Claude agent SDK update"),
        ]
        stories = cluster_articles(arts)
        assert len(stories) == 3
        assert all(s["article_count"] == 1 for s in stories)

    def test_stories_sorted_by_size_then_trending(self):
        arts = [
            _article("c1", "Llama 5 weights leaked on torrent sites", trending=10),
            _article("c2", "Llama 5 weights leaked ahead of launch", trending=20),
            _article("c3", "Some unrelated robotics paper", trending=9999),
        ]
        stories = cluster_articles(arts)
        assert stories[0]["article_count"] == 2  # cluster size beats raw trending

    def test_read_state_aggregates(self):
        arts = [
            _article("d1", "Gemini 4 Pro launches today", read=True),
            _article("d2", "Google launches Gemini 4 Pro", read=True),
        ]
        assert cluster_articles(arts)[0]["is_read"] is True

    def test_empty_input(self):
        assert cluster_articles([]) == []

    def test_story_id_stable_across_orderings(self):
        a = [_article("e1", "Mistral Large 3 announced"), _article("e2", "Mistral announces Large 3")]
        s1 = cluster_articles(a)[0]["id"]
        s2 = cluster_articles(list(reversed(a)))[0]["id"]
        assert s1 == s2
