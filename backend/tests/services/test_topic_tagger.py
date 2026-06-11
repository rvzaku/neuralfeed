from app.services.topic_tagger import tag_topics


def test_tags_llm():
    tags = tag_topics("New GPT-4 language model released by OpenAI")
    assert "llm" in tags


def test_tags_funding():
    tags = tag_topics("Startup raises Series A funding round")
    assert "funding" in tags


def test_tags_multiple():
    tags = tag_topics("Open source LLM with reinforcement learning from human feedback")
    assert "llm" in tags
    assert "open-source" in tags


def test_tags_fallback_to_general():
    tags = tag_topics("Some completely unrelated topic about cooking")
    assert tags == ["general"]
