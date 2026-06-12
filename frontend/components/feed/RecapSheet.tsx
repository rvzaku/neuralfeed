"use client";

// V7 Stage 7: LLM "what happened" brief for a chosen window. The server
// generates once per day per window and caches; reopening is free.

import { useState } from "react";
import { X, Sparkles } from "lucide-react";
import { DeepMarkdown } from "./SummarySheet";
import { useRecap } from "@/hooks/useFeed";
import { cn } from "@/lib/utils";

const WINDOWS = [
  { days: 7, label: "Last week" },
  { days: 30, label: "Last month" },
];

export function RecapSheet({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const [days, setDays] = useState(7);
  const { data, isLoading, isError, refetch } = useRecap(days, isOpen);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end md:items-center md:justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} aria-hidden />
      <div
        role="dialog"
        aria-label="AI recap"
        className="relative w-full md:max-w-2xl max-h-[85vh] overflow-y-auto rounded-t-2xl md:rounded-2xl border border-border bg-background p-5 pb-10 animate-in slide-in-from-bottom-4 duration-200"
      >
        <div className="flex items-center justify-between gap-3 mb-4">
          <h2 className="flex items-center gap-2 font-semibold tracking-tight text-base">
            <Sparkles className="h-4 w-4 text-primary" />
            While you were away
          </h2>
          <div className="flex items-center gap-1.5">
            {WINDOWS.map((w) => (
              <button
                key={w.days}
                onClick={() => setDays(w.days)}
                className={cn(
                  "text-xs px-3 py-1.5 rounded-full border transition-colors",
                  days === w.days
                    ? "bg-foreground text-background border-foreground"
                    : "border-border text-muted-foreground hover:bg-muted"
                )}
              >
                {w.label}
              </button>
            ))}
            <button
              onClick={onClose}
              aria-label="Close recap"
              className="min-w-[44px] min-h-[44px] flex items-center justify-center rounded-lg hover:bg-muted transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {isLoading && (
          <div className="space-y-3 py-2">
            <p className="text-xs text-muted-foreground">
              Distilling the last {days} days — first generation of the day takes a few seconds…
            </p>
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-4 bg-muted rounded animate-pulse" style={{ width: `${90 - i * 12}%` }} />
            ))}
          </div>
        )}

        {isError && (
          <div className="py-8 text-center space-y-2">
            <p className="text-sm text-muted-foreground">Could not generate the recap.</p>
            <button onClick={() => refetch()} className="text-sm text-primary hover:underline">
              Try again
            </button>
          </div>
        )}

        {data && <DeepMarkdown markdown={data.markdown} />}
      </div>
    </div>
  );
}
