"use client";

import { Database, RefreshCw, CheckCircle2, XCircle } from "lucide-react";
import { MobileNav } from "@/components/layout/MobileNav";
import { useSources, usePatchSource } from "@/hooks/useFeed";
import { cn } from "@/lib/utils";
import type { Source } from "@/lib/types";

const CATEGORY_LABELS: Record<string, string> = {
  research: "Research",
  social: "Social",
  company: "Company Blogs",
  newsletter: "Newsletters",
  github: "GitHub",
  video: "Video",
  podcast: "Podcast",
  funding: "Funding",
};

const PRIORITY_DOT: Record<string, string> = {
  high:   "bg-green-500",
  medium: "bg-yellow-500",
  low:    "bg-gray-400",
};

function SourceRow({ source }: { source: Source }) {
  const { mutate, isPending } = usePatchSource();

  return (
    <div className="flex items-center gap-3 py-3 px-4">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span
            className={cn("h-2 w-2 rounded-full shrink-0", PRIORITY_DOT[source.priority] ?? "bg-gray-400")}
          />
          <p className="text-sm font-medium truncate">{source.name}</p>
        </div>
        <div className="flex items-center gap-2 mt-0.5">
          <span className="text-xs text-muted-foreground capitalize">{source.category}</span>
          <span className="text-muted-foreground">·</span>
          <span className="text-xs text-muted-foreground">{source.refresh_interval}</span>
          {source.last_fetched_at && (
            <>
              <span className="text-muted-foreground">·</span>
              <span className="text-xs text-muted-foreground">
                signal {(source.signal_score * 100).toFixed(0)}%
              </span>
            </>
          )}
        </div>
      </div>

      <button
        onClick={() => mutate({ id: source.id, body: { enabled: !source.enabled } })}
        disabled={isPending}
        className={cn(
          "relative inline-flex h-5 w-9 shrink-0 rounded-full transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary",
          source.enabled ? "bg-primary" : "bg-muted",
          isPending && "opacity-50"
        )}
        aria-checked={source.enabled}
        role="switch"
        aria-label={`Toggle ${source.name}`}
      >
        <span
          className={cn(
            "pointer-events-none block h-4 w-4 rounded-full bg-white shadow-sm ring-0 transition-transform duration-200 mt-0.5",
            source.enabled ? "translate-x-4" : "translate-x-0.5"
          )}
        />
      </button>
    </div>
  );
}

export default function SourcesPage() {
  const { data: sources, isLoading, isError } = useSources(true);

  const grouped = sources?.reduce<Record<string, Source[]>>((acc, s) => {
    const cat = s.category;
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(s);
    return acc;
  }, {});

  const enabledCount = sources?.filter((s) => s.enabled).length ?? 0;
  const totalCount = sources?.length ?? 0;

  return (
    <div className="flex flex-col min-h-screen">
      <header className="sticky top-0 z-10 bg-background/80 backdrop-blur-sm border-b border-border px-4 py-3 flex items-center gap-2">
        <Database className="h-4 w-4 text-primary" />
        <h1 className="font-semibold text-sm">Sources</h1>
        <span className="ml-auto text-xs text-muted-foreground">
          {enabledCount}/{totalCount} enabled
        </span>
      </header>

      <main className="flex-1 pb-24 md:pb-6 max-w-2xl mx-auto w-full">
        {isLoading && (
          <div className="flex items-center justify-center py-20">
            <RefreshCw className="h-5 w-5 text-muted-foreground animate-spin" />
          </div>
        )}

        {isError && (
          <div className="flex flex-col items-center justify-center py-16 gap-2 text-center px-4">
            <XCircle className="h-8 w-8 text-destructive" />
            <p className="text-sm text-muted-foreground">Failed to load sources.</p>
          </div>
        )}

        {grouped && Object.entries(grouped).map(([category, items]) => (
          <section key={category} className="mt-4">
            <div className="px-4 pb-1">
              <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                {CATEGORY_LABELS[category] ?? category}
              </h2>
            </div>
            <div className="divide-y divide-border border-y border-border">
              {items.map((source) => (
                <SourceRow key={source.id} source={source} />
              ))}
            </div>
          </section>
        ))}

        {!isLoading && sources?.every((s) => s.enabled) && (
          <div className="flex items-center gap-2 px-4 py-4 text-xs text-muted-foreground">
            <CheckCircle2 className="h-4 w-4 text-green-500" />
            All sources active
          </div>
        )}
      </main>

      <MobileNav />
    </div>
  );
}
