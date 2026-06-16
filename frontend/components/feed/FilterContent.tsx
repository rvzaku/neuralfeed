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

const CONTENT_TYPES = [
  { value: "",           label: "All types" },
  { value: "research",   label: "Papers" },
  { value: "github",     label: "GitHub" },
  { value: "social",     label: "Social" },
  { value: "company",    label: "Blogs" },
  { value: "newsletter", label: "Newsletters" },
  { value: "video",      label: "Videos" },
  { value: "podcast",    label: "Podcasts" },
  { value: "funding",    label: "Funding" },
];

const FEEDBACK_OPTIONS = [
  { value: "",   label: "All" },
  { value: "1",  label: "Liked" },
  { value: "-1", label: "Disliked" },
];

interface FilterContentProps {
  onClear?: () => void;
  className?: string;
}

/** CSV param → Set, e.g. "llm,ai-agents" → {llm, ai-agents}. The URL is the single
 *  source of truth for filter state, so multi-select is just set membership in a
 *  comma-joined param — shareable, refresh-safe, no client store needed. */
function parseSet(value: string | null): Set<string> {
  return new Set((value ?? "").split(",").filter(Boolean));
}

export function FilterContent({ onClear, className }: FilterContentProps) {
  const router = useRouter();
  const params = useSearchParams();
  const { data: sources } = useSources();

  // Multi-select dimensions (sets); time + feedback stay single-value.
  const topicSet    = parseSet(params.get("topic"));
  const categorySet = parseSet(params.get("category"));
  const sourceSet   = parseSet(params.get("source_id"));
  const activeFeedback = params.get("feedback") ?? "";

  const setParam = useCallback(
    (key: string, value: string) => {
      const next = new URLSearchParams(params.toString());
      if (value) next.set(key, value);
      else next.delete(key);
      router.push(`?${next.toString()}`, { scroll: false });
    },
    [params, router]
  );

  // Toggle a value's membership in a CSV multi-select param.
  const toggleMulti = useCallback(
    (key: string, value: string) => {
      const set = parseSet(params.get(key));
      if (set.has(value)) set.delete(value);
      else set.add(value);
      setParam(key, [...set].join(","));
    },
    [params, setParam]
  );

  const clearAll = useCallback(() => {
    const next = new URLSearchParams(params.toString());
    ["topic", "source_id", "feedback", "category", "time_range"].forEach((k) => next.delete(k));
    router.push(`?${next.toString()}`, { scroll: false });
    onClear?.();
  }, [params, router, onClear]);

  const hasActive =
    topicSet.size > 0 || sourceSet.size > 0 || categorySet.size > 0 ||
    activeFeedback !== "";

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

      {/* Content type */}
      <section>
        <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
          Content Type
        </p>
        <div className="flex flex-wrap gap-2">
          {CONTENT_TYPES.map((t) => {
            const active = t.value === "" ? categorySet.size === 0 : categorySet.has(t.value);
            return (
              <button
                key={t.value}
                aria-pressed={active}
                onClick={() => (t.value === "" ? setParam("category", "") : toggleMulti("category", t.value))}
                className={cn(
                  "rounded-full px-3 py-1 text-xs font-medium border transition-colors",
                  active
                    ? "bg-primary text-primary-foreground border-primary"
                    : "bg-muted/40 text-muted-foreground border-border hover:bg-muted hover:text-foreground"
                )}
              >
                {t.label}
              </button>
            );
          })}
        </div>
      </section>

      {/* Time range lives on the Feed's Day/Month/Year horizon selector now. */}

      {/* Topic */}
      <section>
        <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
          Topic
        </p>
        <div className="flex flex-wrap gap-2">
          {TOPIC_TAGS.map((t) => {
            const active = topicSet.has(t.value);
            return (
              <button
                key={t.value}
                aria-pressed={active}
                onClick={() => toggleMulti("topic", t.value)}
                className={cn(
                  "rounded-full px-3 py-1 text-xs font-medium border transition-colors",
                  active
                    ? "bg-primary text-primary-foreground border-primary"
                    : "bg-muted/40 text-muted-foreground border-border hover:bg-muted hover:text-foreground"
                )}
              >
                {t.label}
              </button>
            );
          })}
        </div>
      </section>

      {/* Source — multi-select; quality is now automatic (handled by ranking) */}
      {sources && sources.length > 0 && (
        <section>
          <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
            Source
          </p>
          <div className="space-y-1 max-h-52 overflow-y-auto">
            <button
              aria-pressed={sourceSet.size === 0}
              onClick={() => setParam("source_id", "")}
              className={cn(
                "w-full text-left px-3 py-2 rounded-lg text-xs border transition-colors",
                sourceSet.size === 0
                  ? "bg-primary/10 text-primary border-primary/30 font-medium"
                  : "text-muted-foreground border-border hover:bg-muted"
              )}
            >
              All sources
            </button>
            {sources.map((src) => {
              const active = sourceSet.has(src.id);
              return (
                <button
                  key={src.id}
                  aria-pressed={active}
                  onClick={() => toggleMulti("source_id", src.id)}
                  className={cn(
                    "w-full text-left px-3 py-2 rounded-lg text-xs border transition-colors",
                    active
                      ? "bg-primary/10 text-primary border-primary/30 font-medium"
                      : "text-muted-foreground border-border hover:bg-muted"
                  )}
                >
                  {src.name}
                </button>
              );
            })}
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
