from app.services.topic_tagger import tag_topics


def test_tags_llm():
    tags = tag_topics("New GPT-4 language model released by OpenAI")
    assert "llm" in tags


def test_tags_funding_with_ai_context():
    # Funding is kept when the item is clearly about AI.
    tags = tag_topics("AI startup Anthropic raises Series A funding round")
    assert "funding" in tags


def test_tags_multiple():
    tags = tag_topics("Open source LLM with reinforcement learning from human feedback")
    assert "llm" in tags
    assert "open-source" in tags


def test_tags_fallback_to_general():
    tags = tag_topics("Some completely unrelated topic about cooking")
    assert tags == ["general"]


# --- precision regressions (app-feedback-v7) --------------------------------

def test_non_ai_business_news_falls_to_general():
    # The motivating case: a high-traction non-AI post matched "funding"/"products"
    # on the old tagger and dodged the relevance penalty. Now gated to general.
    assert tag_topics("SpaceX IPO: live updates on the rocket company's filing") == ["general"]


def test_word_boundary_no_substring_false_positives():
    # "api" must not match inside "capital"; "rl" not inside "world".
    assert tag_topics("Raising capital to explore the world of fine dining") == ["general"]


def test_ai_product_launch_keeps_products():
    tags = tag_topics("OpenAI announces the launch of a new model API")
    assert "products" in tags


def test_funding_gated_out_without_ai_signal():
    tags = tag_topics("Grocery chain acquired in a $2B acquisition deal")
    assert "funding" not in tags
    assert tags == ["general"]
