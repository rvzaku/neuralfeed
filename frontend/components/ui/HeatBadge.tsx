"use client";

// V6 Hotness Index — cross-source velocity rendered as a colour band, not a raw
// number (user ask: "shown using a color index or something like that"). The
// scale runs cool → warm → blazing so a launch week (OpenClaw-style spike that
// lights up every source at once) is obvious at a glance.

import { Flame } from "lucide-react";
import { cn } from "@/lib/utils";

export const HEAT_META: Record<number, { label: string; chip: string; dot: string }> = {
  1: {
    label: "Warm",
    chip: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300",
    dot: "bg-amber-500",
  },
  2: {
    label: "Hot",
    chip: "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300",
    dot: "bg-orange-500",
  },
  3: {
    label: "Blazing",
    chip: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300",
    dot: "bg-red-500",
  },
};

/** Full chip with flame + label — used on feed cards. Renders nothing below the
 *  warm threshold so the ordinary majority of the feed stays unpainted. */
export function HeatBadge({ heat, className }: { heat?: number | null; className?: string }) {
  if (!heat || heat < 1) return null;
  const meta = HEAT_META[heat] ?? HEAT_META[3];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold",
        meta.chip,
        // Only the top band pulses — a restrained, reduced-motion-safe cue that
        // something is genuinely blowing up right now.
        heat >= 3 && "motion-safe:animate-pulse",
        className
      )}
      title={`${meta.label} — gaining traction across multiple sources right now`}
    >
      <Flame className="h-3 w-3" />
      {meta.label}
    </span>
  );
}

/** Compact coloured dot — used on dense topic cards where a chip is too heavy. */
export function HeatDot({ heat, className }: { heat?: number | null; className?: string }) {
  if (!heat || heat < 1) return null;
  const meta = HEAT_META[heat] ?? HEAT_META[3];
  return (
    <span
      className={cn(
        "inline-block h-2 w-2 rounded-full",
        meta.dot,
        heat >= 3 && "motion-safe:animate-pulse",
        className
      )}
      title={`${meta.label} topic — lots of cross-source activity right now`}
      aria-label={`${meta.label} topic`}
    />
  );
}

/** Inline legend explaining the colour scale — one per page (Topics, feed). */
export function HeatLegend({ className }: { className?: string }) {
  return (
    <span className={cn("inline-flex items-center gap-2 text-[11px] text-muted-foreground", className)}>
      <Flame className="h-3 w-3" />
      <span>Heat:</span>
      {[1, 2, 3].map((lvl) => (
        <span key={lvl} className="inline-flex items-center gap-1">
          <span className={cn("h-2 w-2 rounded-full", HEAT_META[lvl].dot)} />
          {HEAT_META[lvl].label}
        </span>
      ))}
    </span>
  );
}
