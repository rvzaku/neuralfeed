TOPIC_KEYWORDS: dict[str, list[str]] = {
    "llm": ["llm", "language model", "gpt", "claude", "gemini", "llama", "mistral", "chatgpt", "fine-tun", "prompt", "token", "transformer", "bert", "instruction tuning", "rlhf"],
    "computer-vision": ["computer vision", "image generation", "diffusion", "stable diffusion", "object detection", "segmentation", "vit", "clip", "dall-e", "midjourney", "flux"],
    "multimodal": ["multimodal", "vision-language", "text-to-image", "image-to-text", "audio-visual", "omni", "multi-modal"],
    "reinforcement-learning": ["reinforcement learning", "rl ", " rl,", "reward model", "policy gradient", "dpo", "ppo", "grpo", "agent training", "rlhf"],
    "ai-safety": ["alignment", "safety", "interpretability", "red team", "jailbreak", "hallucination", "bias", "fairness", "responsible ai", "constitutional ai"],
    "robotics": ["robot", "embodied", "manipulation", "locomotion", "sim-to-real", "physical ai", "dexterous"],
    "ai-agents": ["agent", "agentic", "tool use", "planning", "autonomous", "multi-agent", "workflow", "orchestration"],
    "audio-speech": ["speech", "audio", "tts", "asr", "whisper", "voice", "music generation", "sound"],
    "open-source": ["open source", "open-source", "open weight", "open-weight", "hugging face", "ollama", "llama.cpp", "gguf"],
    "ai-infrastructure": ["inference", "quantization", "training infra", "gpu", "cuda", "triton", "vllm", "tensorrt", "serving", "throughput", "latency", "efficiency"],
    "products": ["launch", "product", "api", "app", "startup", "release", "announce", "now available", "pricing"],
    "funding": ["funding", "raises", "series a", "series b", "valuation", "investment", "acquired", "acquisition", "ipo"],
}


def tag_topics(text: str) -> list[str]:
    lower = text.lower()
    return [tag for tag, kws in TOPIC_KEYWORDS.items() if any(kw in lower for kw in kws)] or ["general"]
