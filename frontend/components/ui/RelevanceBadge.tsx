"use client";

// Relevance is the "why this is in your feed" signal. The old "rel 97" mono text
// read as a cryptic debug value. Here it's a small monochrome progress ring + the
// number: the arc gives an at-a-glance sense of strength, the digits give the
// precise score, and it stays in ink (no indigo pill) to honour colour restraint —
// heat is the only painted signal on a card.

import { cn } from "@/lib/utils";

function tierLabel(score: number): string {
  if (score >= 85) return "Top match";
  if (score >= 65) return "Strong match";
  if (score >= 40) return "Relevant";
  return "Loosely related";
}

export function RelevanceBadge({
  relevance,
  className,
}: {
  relevance?: number | null;
  className?: string;
}) {
  if (relevance == null) return null;
  const score = Math.max(0, Math.min(100, Math.round(relevance)));

  // 14px ring; circumference for r=6 ≈ 37.7
  const r = 6;
  const c = 2 * Math.PI * r;
  const dash = (score / 100) * c;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 tabular-nums text-muted-foreground",
        className
      )}
      title={`${tierLabel(score)} — ${score}% relevant to your interests`}
      aria-label={`Relevance ${score} out of 100, ${tierLabel(score)}`}
    >
      <svg width="14" height="14" viewBox="0 0 16 16" className="-rotate-90 shrink-0">
        <circle
          cx="8"
          cy="8"
          r={r}
          fill="none"
          strokeWidth="2"
          className="stroke-border"
        />
        <circle
          cx="8"
          cy="8"
          r={r}
          fill="none"
          strokeWidth="2"
          strokeLinecap="round"
          strokeDasharray={`${dash} ${c}`}
          className={cn(
            score >= 65 ? "stroke-foreground/70" : "stroke-muted-foreground/60"
          )}
        />
      </svg>
      <span className="text-[11px] font-medium text-foreground/70">{score}</span>
    </span>
  );
}
