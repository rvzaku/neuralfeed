"""V6 cross-source dedup: exact + near-duplicate clustering."""

from unittest.mock import MagicMock

from app.models.article import make_title_hash
from app.services.dedupe import cross_source_buzz, dedupe_cross_source


def _article(aid, title, source_id, trending_score=0.0, topic_tags=None):
    a = MagicMock()
    a.id = aid
    a.title = title
    a.title_hash = make_title_hash(title)
    a.source_id = source_id
    a.trending_score = trending_score
    a.topic_tags = topic_tags or []
    return a


class TestDedupeCrossSource:
    def test_exact_normalized_titles_collapse_to_one(self):
        a = _article("1", "Meta releases Llama 4", "arxiv", trending_score=0.2)
        b = _article("2", "Meta Releases Llama 4!", "reddit", trending_score=0.9)
        kept = dedupe_cross_source([a, b])
        assert len(kept) == 1
        assert kept[0] is b  # higher trending wins

    def test_near_duplicate_headlines_collapse(self):
        a = _article("1", "OpenAI launches new GPT-5 reasoning model today", "hn", trending_score=0.1)
        b = _article("2", "OpenAI launches a new GPT-5 reasoning model", "blog", trending_score=0.5)
        kept = dedupe_cross_source([a, b])
        assert len(kept) == 1
        assert kept[0] is b

    def test_distinct_stories_sharing_a_subject_are_kept(self):
        a = _article("1", "Meta releases Llama 4 weights", "a")
        b = _article("2", "Google announces Gemini 3 pricing changes", "b")
        kept = dedupe_cross_source([a, b])
        assert len(kept) == 2

    def test_winner_absorbs_loser_topic_tags(self):
        a = _article("1", "Llama 4 is here", "a", trending_score=0.9, topic_tags=["llm"])
        b = _article("2", "Llama 4 is here!", "b", trending_score=0.1, topic_tags=["open-source"])
        kept = dedupe_cross_source([a, b])
        assert len(kept) == 1
        assert set(kept[0].topic_tags) == {"llm", "open-source"}


class TestCrossSourceBuzz:
    def test_counts_distinct_sources_per_cluster(self):
        a = _article("1", "Llama 4 released by Meta", "arxiv")
        b = _article("2", "Llama 4 released by Meta!", "reddit")
        c = _article("3", "Llama 4 released by Meta today", "hn")
        buzz = cross_source_buzz([a, b, c])
        assert buzz["1"] == 3 and buzz["2"] == 3 and buzz["3"] == 3

    def test_same_source_does_not_inflate_buzz(self):
        a = _article("1", "Llama 4 released", "reddit")
        b = _article("2", "Llama 4 released!", "reddit")
        buzz = cross_source_buzz([a, b])
        assert buzz["1"] == 1
