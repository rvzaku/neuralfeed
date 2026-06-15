import type { TopicTag } from "./types";

// Human-readable labels for topic slugs, shared across the Topics directory and
// the "Your taste" personalization surface so they never drift apart.
export const TOPIC_LABELS: Record<string, string> = {
  "llm": "Language Models",
  "ai-agents": "Agents",
  "open-source": "Open Source",
  "computer-vision": "Computer Vision",
  "multimodal": "Multimodal",
  "reinforcement-learning": "Reinforcement Learning",
  "ai-safety": "AI Safety",
  "robotics": "Robotics",
  "audio-speech": "Audio & Speech",
  "ai-infrastructure": "Infrastructure",
  "products": "Products",
  "funding": "Funding",
  "research-paper": "Research Papers",
  "github": "GitHub",
  "general": "General",
};

export function topicLabel(tag: string): string {
  return TOPIC_LABELS[tag] ?? tag.replace(/-/g, " ");
}

export type { TopicTag };
