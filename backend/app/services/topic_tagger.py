"""Keyword topic tagger (precise, dependency-free).

Why not an LLM classifier: tagging runs inline on every ingested item, so it
must be fast and free. The win over the old version is *precision*, not a new
model:

1. **Word-boundary matching.** The old tagger used naive `in` substring tests,
   so "api" matched "c*api*tal", "rl" matched "wo*rl*d", "ipo" matched
   "trampol*ipo*…" — flooding items with bogus tags. We now match on
   alphanumeric boundaries, so a keyword hits only as a whole word/phrase.

2. **AI-context gate for generic topics.** "products" and "funding" are
   business categories that fire on plenty of non-AI tech/business news (a
   "SpaceX IPO" post hit `funding` and so dodged the relevance penalty). These
   two topics are kept ONLY when the text also shows a genuine AI signal;
   otherwise the item falls through to the catch-all "general" (which the ranker
   down-weights). Topical AI categories (llm, robotics, …) are self-evidently
   about AI and need no gate.
"""

import re

TOPIC_KEYWORDS: dict[str, list[str]] = {
    "llm": ["llm", "language model", "gpt", "claude", "gemini", "llama", "mistral", "chatgpt", "fine-tune", "fine-tuning", "prompt", "token", "transformer", "bert", "instruction tuning", "rlhf"],
    "computer-vision": ["computer vision", "image generation", "diffusion", "stable diffusion", "object detection", "segmentation", "vit", "clip", "dall-e", "midjourney", "flux"],
    "multimodal": ["multimodal", "vision-language", "text-to-image", "image-to-text", "audio-visual", "omni", "multi-modal"],
    "reinforcement-learning": ["reinforcement learning", "rl", "reward model", "policy gradient", "dpo", "ppo", "grpo", "rlhf"],
    "ai-safety": ["alignment", "safety", "interpretability", "red team", "jailbreak", "hallucination", "bias", "fairness", "responsible ai", "constitutional ai"],
    "robotics": ["robot", "robotics", "embodied", "manipulation", "locomotion", "sim-to-real", "physical ai", "dexterous"],
    "ai-agents": ["agent", "agentic", "tool use", "autonomous", "multi-agent", "orchestration"],
    "audio-speech": ["speech", "audio", "tts", "asr", "whisper", "voice", "music generation"],
    "open-source": ["open source", "open-source", "open weight", "open-weight", "hugging face", "ollama", "llama.cpp", "gguf"],
    "ai-infrastructure": ["inference", "quantization", "gpu", "cuda", "triton", "vllm", "tensorrt", "throughput", "latency"],
    "products": ["launch", "product", "api", "app", "startup", "release", "announce", "now available", "pricing"],
    "funding": ["funding", "raises", "series a", "series b", "valuation", "investment", "acquired", "acquisition", "ipo"],
}

# Topics that are business/product categories rather than inherently-AI ones.
# Kept only when the text independently shows an AI signal (see _AI_SIGNAL).
_GATED_TOPICS = frozenset({"products", "funding"})

# A standalone signal that an item is actually about AI — used to gate the
# generic business topics. Deliberately broad but AI-specific.
_AI_SIGNAL_TERMS = [
    "ai", "a.i.", "artificial intelligence", "machine learning", "deep learning",
    "neural", "llm", "language model", "gpt", "chatgpt", "claude", "gemini",
    "llama", "mistral", "openai", "anthropic", "deepmind", "hugging face",
    "agent", "agentic", "model", "inference", "diffusion", "multimodal",
    "transformer", "generative",
]


def _boundary_pattern(terms: list[str]) -> "re.Pattern[str]":
    """A single regex that matches any term as a whole token. Boundaries are on
    alphanumerics only (not \\b), so phrases with '-', '.', or spaces
    ('llama.cpp', 'text-to-image') still match cleanly."""
    alts = "|".join(re.escape(t) for t in sorted(terms, key=len, reverse=True))
    return re.compile(rf"(?<![a-z0-9])(?:{alts})(?![a-z0-9])", re.IGNORECASE)


_TOPIC_PATTERNS = {topic: _boundary_pattern(kws) for topic, kws in TOPIC_KEYWORDS.items()}
_AI_SIGNAL = _boundary_pattern(_AI_SIGNAL_TERMS)


def tag_topics(text: str) -> list[str]:
    """Return the matched AI topic slugs, or ["general"] when nothing specific
    (and AI-relevant) is found. Order follows TOPIC_KEYWORDS for stability."""
    lower = text.lower()
    has_ai_signal = bool(_AI_SIGNAL.search(lower))
    matched = [
        topic
        for topic, pat in _TOPIC_PATTERNS.items()
        if pat.search(lower) and (has_ai_signal or topic not in _GATED_TOPICS)
    ]
    return matched or ["general"]
