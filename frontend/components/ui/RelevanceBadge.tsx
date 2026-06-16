"use client";

// Relevance = "why this is in your feed." It needs to read instantly, so it's a
// signal-strength meter (4 rising bars, like reception bars) — a universally
// understood "how strong is this" glyph — paired with the precise number and a
// short tier word. Bars are ink/accent only; colour stays reserved for heat so a
// card never turns into a rainbow. The top tier earns the indigo accent because
// "this is highly relevant to you" is the one thing worth a flicker of colour.

import { cn } from "@/lib/utils";

interface Tier {
  bars: number;
  label: string;
  /** tailwind text-color class driving the filled bars + number */
  tone: string;
}

function tierFor(score: number): Tier {
  if (score >= 85) return { bars: 4, label: "Top match", tone: "text-primary" };
  if (score >= 65) return { bars: 3, label: "Strong match", tone: "text-foreground" };
  if (score >= 40) return { bars: 2, label: "Relevant", tone: "text-foreground/75" };
  return { bars: 1, label: "Loosely related", tone: "text-muted-foreground" };
}

const BAR_HEIGHTS = ["h-1.5", "h-2", "h-2.5", "h-3"];

export function RelevanceBadge({
  relevance,
  showLabel = false,
  className,
}: {
  relevance?: number | null;
  /** render the tier word inline (used in the summary sheet header) */
  showLabel?: boolean;
  className?: string;
}) {
  if (relevance == null) return null;
  const score = Math.max(0, Math.min(100, Math.round(relevance)));
  const tier = tierFor(score);

  return (
    <span
      className={cn("inline-flex items-center gap-1.5", className)}
      title={`${tier.label} — ${score}% relevant to your interests`}
      aria-label={`Relevance ${score} out of 100, ${tier.label}`}
    >
      <span className="flex items-end gap-[2px]" aria-hidden>
        {BAR_HEIGHTS.map((h, i) => (
          <span
            key={i}
            className={cn(
              "w-[3px] rounded-[1px]",
              h,
              i < tier.bars
                ? cn("bg-current", tier.tone)
                : "bg-border"
            )}
          />
        ))}
      </span>
      <span className={cn("text-[11px] font-semibold tabular-nums", tier.tone)}>
        {score}
      </span>
      {showLabel && (
        <span className="text-[11px] font-medium text-muted-foreground">
          {tier.label}
        </span>
      )}
    </span>
  );
}
