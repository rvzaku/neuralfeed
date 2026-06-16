import pytest

from app.services.landmarks import (
    _parse_entities,
    compile_matcher,
    detect_landmark_entities,
    title_is_landmark,
)


class TestParse:
    def test_parses_json_array(self):
        assert _parse_entities('["OpenClaw", "Moltbook"]') == ["openclaw", "moltbook"]

    def test_extracts_array_from_chatter(self):
        raw = 'Sure! Here you go:\n["Qwen3", "GPT-5"]\nHope that helps.'
        assert _parse_entities(raw) == ["qwen3", "gpt-5"]

    def test_dedupes_and_bounds(self):
        assert _parse_entities('["OpenClaw", "openclaw", "x"]') == ["openclaw"]

    def test_bad_output_returns_empty(self):
        assert _parse_entities("no json here") == []


class TestMatcher:
    def test_word_boundary_match(self):
        m = compile_matcher(["OpenClaw", "Qwen3"])
        assert title_is_landmark("Liberate your OpenClaw today", m)
        assert title_is_landmark("Running Qwen3 locally", m)

    def test_no_substring_false_positive(self):
        m = compile_matcher(["claw"])
        assert not title_is_landmark("clawback provisions explained", m)

    def test_empty_matcher_is_none(self):
        assert compile_matcher([]) is None
        assert not title_is_landmark("anything", None)


@pytest.mark.asyncio
async def test_detect_returns_empty_without_key(monkeypatch):
    # Best-effort: no key configured anywhere → no call, empty list (never raises).
    from app.core.config import settings
    monkeypatch.setattr(settings, "groq_api_key", "")
    assert await detect_landmark_entities(["OpenClaw launches"], api_key="") == []


@pytest.mark.asyncio
async def test_detect_returns_empty_on_no_titles():
    assert await detect_landmark_entities([]) == []
