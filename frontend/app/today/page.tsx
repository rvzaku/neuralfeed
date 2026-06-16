"use client";

// P1.4: "Today in AI" — the top handful of stories rolled up, ranked with the
// same pipeline as the feed. A finite, glanceable daily brief; the same digest
// is what the optional daily email sends.

import Link from "next/link";
import { Sun, ArrowUpRight } from "lucide-react";
import { useDigest } from "@/hooks/useFeed";
import { topicLabel } from "@/lib/topics";

export default function TodayPage() {
  const { data, isLoading } = useDigest(5);

  return (
    <div className="flex flex-col min-h-screen">
      <header className="sticky top-[var(--banner-h,0px)] md:static z-10 bg-background/80 backdrop-blur-md border-b border-border px-4 py-3 flex items-center gap-2.5">
        <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-foreground text-background">
          <Sun className="h-3.5 w-3.5" />
        </span>
        <h1 className="font-serif font-semibold text-lg tracking-tight">Today in AI</h1>
      </header>

      <main className="flex-1 px-4 pt-5 pb-24 md:pb-8 max-w-2xl mx-auto w-full">
        <p className="text-sm text-muted-foreground mb-5">
          The stories worth your attention right now — ranked by freshness,
          traction, and your taste.
        </p>

        {isLoading ? (
          <ol className="space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <li key={i} className="h-24 rounded-xl border border-border bg-card animate-pulse" />
            ))}
          </ol>
        ) : !data || data.items.length === 0 ? (
          <p className="text-sm text-muted-foreground py-12 text-center">
            Nothing to brief yet — check back after the next fetch.
          </p>
        ) : (
          <ol className="space-y-3">
            {data.items.map((item, i) => (
              <li key={item.id}>
                <a
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="group flex gap-3.5 rounded-xl border border-border bg-card px-4 py-4 hover:border-primary/40 transition-colors"
                >
                  <span className="font-serif text-lg font-bold text-muted-foreground/70 tabular-nums leading-none pt-0.5">
                    {i + 1}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                      {item.source_name}
                      {item.topic_tags[0] && (
                        <span className="text-muted-foreground/60">· {topicLabel(item.topic_tags[0])}</span>
                      )}
                    </span>
                    <span className="mt-0.5 flex items-start gap-1 text-[15px] font-semibold leading-snug">
                      <span className="min-w-0">{item.title}</span>
                      <ArrowUpRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                    </span>
                    {item.blurb && (
                      <span className="mt-1 block text-sm text-muted-foreground leading-snug line-clamp-2">
                        {item.blurb}
                      </span>
                    )}
                  </span>
                </a>
              </li>
            ))}
          </ol>
        )}

        <Link
          href="/"
          className="mt-6 block text-center text-sm text-primary hover:underline"
        >
          See the full feed →
        </Link>
      </main>
    </div>
  );
}
