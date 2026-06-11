"use client";

import { useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { cn } from "@/lib/utils";
import { useSources } from "@/hooks/useFeed";

const TOPIC_TAGS = [
  { value: "llm",                    label: "LLMs" },
  { value: "computer-vision",        label: "Computer Vision" },
  { value: "multimodal",             label: "Multimodal" },
  { value: "reinforcement-learning", label: "RL" },
  { value: "ai-safety",              label: "AI Safety" },
  { value: "robotics",               label: "Robotics" },
  { value: "ai-agents",              label: "Agents" },
  { value: "audio-speech",           label: "Audio" },
  { value: "open-source",            label: "Open Source" },
  { value: "ai-infrastructure",      label: "Infrastructure" },
  { value: "products",               label: "Products" },
  { value: "funding",                label: "Funding" },
];

const FEEDBACK_OPTIONS = [
  { value: "",   label: "All" },
  { value: "1",  label: "Liked" },
  { value: "-1", label: "Disliked" },
];

const QUALITY_OPTIONS = [
  { value: "",    label: "All sources" },
  { value: "0.7", label: "High signal" },
  { value: "0.4", label: "High + Medium" },
];

interface FilterContentProps {
  onClear?: () => void;
  className?: string;
}

export function FilterContent({ onClear, className }: FilterContentProps) {
  const router = useRouter();
  const params = useSearchParams();
  const { data: sources } = useSources();

  const activeTopic    = params.get("topic") ?? "";
  const activeSource   = params.get("source_id") ?? "";
  const activeFeedback = params.get("feedback") ?? "";
  const activeQuality  = params.get("min_signal") ?? "";

  const setParam = useCallback(
    (key: string, value: string) => {
      const next = new URLSearchParams(params.toString());
      if (value) next.set(key, value);
      else next.delete(key);
      router.push(`?${next.toString()}`, { scroll: false });
    },
    [params, router]
  );

  const clearAll = useCallback(() => {
    const next = new URLSearchParams(params.toString());
    ["topic", "source_id", "feedback", "min_signal"].forEach((k) => next.delete(k));
    router.push(`?${next.toString()}`, { scroll: false });
    onClear?.();
  }, [params, router, onClear]);

  const hasActive = activeTopic || activeSource || activeFeedback || activeQuality;

  return (
    <div className={cn("space-y-6", className)}>
      {hasActive && (
        <button
          onClick={clearAll}
          className="w-full text-xs text-destructive border border-destructive/30 rounded-lg py-1.5 hover:bg-destructive/10 transition-colors"
        >
          Clear all filters
        </button>
      )}

      {/* Topic */}
      <section>
        <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
          Topic
        </p>
        <div className="flex flex-wrap gap-2">
          {TOPIC_TAGS.map((t) => (
            <button
              key={t.value}
              onClick={() => setParam("topic", activeTopic === t.value ? "" : t.value)}
              className={cn(
                "rounded-full px-3 py-1 text-xs font-medium border transition-colors",
                activeTopic === t.value
                  ? "bg-primary text-primary-foreground border-primary"
                  : "bg-muted/40 text-muted-foreground border-border hover:bg-muted hover:text-foreground"
              )}
            >
              {t.label}
            </button>
          ))}
        </div>
      </section>

      {/* Source quality */}
      <section>
        <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
          Source Quality
        </p>
        <div className="flex flex-col gap-1.5">
          {QUALITY_OPTIONS.map((q) => (
            <button
              key={q.value}
              onClick={() => setParam("min_signal", q.value)}
              className={cn(
                "w-full text-left px-3 py-2 rounded-lg text-xs border transition-colors",
                activeQuality === q.value
                  ? "bg-primary/10 text-primary border-primary/30 font-medium"
                  : "text-muted-foreground border-border hover:bg-muted"
              )}
            >
              {q.label}
            </button>
          ))}
        </div>
      </section>

      {/* Source */}
      {sources && sources.length > 0 && (
        <section>
          <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
            Source
          </p>
          <div className="space-y-1 max-h-52 overflow-y-auto">
            <button
              onClick={() => setParam("source_id", "")}
              className={cn(
                "w-full text-left px-3 py-2 rounded-lg text-xs border transition-colors",
                !activeSource
                  ? "bg-primary/10 text-primary border-primary/30 font-medium"
                  : "text-muted-foreground border-border hover:bg-muted"
              )}
            >
              All sources
            </button>
            {sources.map((src) => (
              <button
                key={src.id}
                onClick={() => setParam("source_id", activeSource === src.id ? "" : src.id)}
                className={cn(
                  "w-full text-left px-3 py-2 rounded-lg text-xs border transition-colors",
                  activeSource === src.id
                    ? "bg-primary/10 text-primary border-primary/30 font-medium"
                    : "text-muted-foreground border-border hover:bg-muted"
                )}
              >
                {src.name}
              </button>
            ))}
          </div>
        </section>
      )}

      {/* Feedback */}
      <section>
        <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
          Feedback
        </p>
        <div className="flex gap-2">
          {FEEDBACK_OPTIONS.map((f) => (
            <button
              key={f.value}
              onClick={() => setParam("feedback", f.value)}
              className={cn(
                "flex-1 rounded-lg px-3 py-2 text-xs font-medium border transition-colors",
                activeFeedback === f.value
                  ? "bg-primary text-primary-foreground border-primary"
                  : "bg-muted/40 text-muted-foreground border-border hover:bg-muted hover:text-foreground"
              )}
            >
              {f.label}
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}
