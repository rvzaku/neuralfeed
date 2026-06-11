"use client";

import { cn } from "@/lib/utils";

const SOURCE_CONFIG: Record<string, { label: string; color: string }> = {
  "arxiv-cs-ai":       { label: "arXiv",       color: "bg-violet-100 text-violet-800 dark:bg-violet-900/40 dark:text-violet-300" },
  "arxiv-cs-cv":       { label: "arXiv CV",    color: "bg-violet-100 text-violet-800 dark:bg-violet-900/40 dark:text-violet-300" },
  "reddit-ml":         { label: "r/ML",         color: "bg-orange-100 text-orange-800 dark:bg-orange-900/40 dark:text-orange-300" },
  "reddit-localllama": { label: "r/LocalLLaMA", color: "bg-orange-100 text-orange-800 dark:bg-orange-900/40 dark:text-orange-300" },
  "reddit-artificial": { label: "r/artificial", color: "bg-orange-100 text-orange-800 dark:bg-orange-900/40 dark:text-orange-300" },
  "github-trending":   { label: "GitHub",       color: "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300" },
  "rss-openai":        { label: "OpenAI",       color: "bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300" },
  "rss-anthropic":     { label: "Anthropic",    color: "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300" },
  "rss-deepmind":      { label: "DeepMind",     color: "bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300" },
  "rss-huggingface":   { label: "HuggingFace",  color: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-300" },
  "rss-metaai":        { label: "Meta AI",      color: "bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300" },
};

const CATEGORY_CONFIG: Record<string, { label: string; color: string }> = {
  research:   { label: "Research",   color: "bg-violet-100 text-violet-800 dark:bg-violet-900/40 dark:text-violet-300" },
  social:     { label: "Social",     color: "bg-orange-100 text-orange-800 dark:bg-orange-900/40 dark:text-orange-300" },
  company:    { label: "Blog",       color: "bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300" },
  github:     { label: "GitHub",     color: "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300" },
  newsletter: { label: "Newsletter", color: "bg-teal-100 text-teal-800 dark:bg-teal-900/40 dark:text-teal-300" },
  video:      { label: "Video",      color: "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300" },
};

interface SourceBadgeProps {
  sourceId: string;
  category?: string;
  className?: string;
}

export function SourceBadge({ sourceId, category, className }: SourceBadgeProps) {
  const cfg = SOURCE_CONFIG[sourceId] ?? (category ? CATEGORY_CONFIG[category] : null) ?? {
    label: sourceId,
    color: "bg-muted text-muted-foreground",
  };

  return (
    <span className={cn("inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium", cfg.color, className)}>
      {cfg.label}
    </span>
  );
}
