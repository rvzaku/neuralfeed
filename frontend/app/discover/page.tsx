"use client";

import { useState } from "react";
import Link from "next/link";
import { Compass, Search, Flame, Tags, ArrowRight } from "lucide-react";
import { FeedCard } from "@/components/feed/FeedCard";
import { FeedCardSkeleton } from "@/components/feed/FeedCardSkeleton";
import { SummarySheet } from "@/components/feed/SummarySheet";
import { useFeed, useInfiniteFeed, useSearch } from "@/hooks/useFeed";
import type { Article } from "@/lib/types";

function SectionTitle({ icon: Icon, children }: { icon: typeof Flame; children: React.ReactNode }) {
  return (
    <h2 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
      <Icon className="h-3.5 w-3.5" />
      {children}
    </h2>
  );
}

export default function DiscoverPage() {
  const [query, setQuery] = useState("");
  const [openArticle, setOpenArticle] = useState<Article | null>(null);
  const searching = query.trim().length >= 2;

  const { data: results, isLoading: searchLoading } = useSearch(query, searching);
  const { data: trending, isLoading: trendingLoading } = useFeed({
    ranked: true,
    time_range: "3d",
    limit: 10,
    cap_to_density: false, // Discover explores beyond the Feed's density cap
  });

  // V7-6: Discover is the exploration surface — paginated "Show more" over the
  // full ranked set (the Feed itself stays a finite numbered shortlist).
  const {
    data: exploreData, isLoading: exploreLoading,
    fetchNextPage, hasNextPage, isFetchingNextPage,
  } = useInfiniteFeed({ ranked: true, time_range: "30d", limit: 15, cap_to_density: false });
  const exploreItems = exploreData?.pages.flatMap((p) => p.items) ?? [];

  return (
    <div className="flex flex-col min-h-screen">
      <header className="sticky top-[var(--banner-h,0px)] md:static z-10 bg-background/80 backdrop-blur-md border-b border-border px-4 py-3 flex items-center gap-2.5">
        <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-foreground text-background">
          <Compass className="h-3.5 w-3.5" />
        </span>
        <h1 className="font-serif font-semibold text-lg tracking-tight">Discover</h1>
      </header>

      <main className="flex-1 px-4 pt-4 pb-24 md:pb-8 max-w-2xl mx-auto w-full space-y-8">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search everything fetched…"
            className="w-full pl-10 pr-4 py-3 text-sm rounded-xl border border-border bg-card outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary/40 min-h-[48px] shadow-sm"
            aria-label="Search articles"
          />
        </div>

        {/* Search results take over when active */}
        {searching ? (
          <section className="space-y-3">
            <SectionTitle icon={Search}>
              Results {results ? `(${results.length})` : ""}
            </SectionTitle>
            {searchLoading && Array.from({ length: 3 }).map((_, i) => <FeedCardSkeleton key={i} />)}
            {!searchLoading && results?.length === 0 && (
              <p className="text-sm text-muted-foreground">Nothing found for &ldquo;{query}&rdquo;.</p>
            )}
            {results?.map((a) => (
              <FeedCard key={a.id} article={a} onOpen={setOpenArticle} />
            ))}
          </section>
        ) : (
          <>
            {/* Topics live on their own page now (V9) */}
            <Link
              href="/topics"
              className="flex items-center justify-between rounded-xl border border-border bg-card px-4 py-3.5 hover:border-primary/40 transition-colors"
            >
              <span className="flex items-center gap-2 text-sm font-semibold">
                <Tags className="h-4 w-4" /> Browse by topic
              </span>
              <ArrowRight className="h-4 w-4 text-muted-foreground" />
            </Link>

            {/* Trending */}
            <section className="space-y-3">
              <SectionTitle icon={Flame}>
                Trending now{trending?.items.length ? ` (${Math.min(trending.items.length, 10)})` : ""}
              </SectionTitle>
              {trendingLoading && Array.from({ length: 3 }).map((_, i) => <FeedCardSkeleton key={i} />)}
              {trending?.items.slice(0, 10).map((a) => (
                <FeedCard key={a.id} article={a} onOpen={setOpenArticle} />
              ))}
              {!trendingLoading && trending?.items.length === 0 && (
                <p className="text-sm text-muted-foreground">No trending items in the last 3 days.</p>
              )}
            </section>

            {/* More to explore — paginated, the part the Feed deliberately omits */}
            <section className="space-y-3">
              <SectionTitle icon={Compass}>More to explore</SectionTitle>
              {exploreLoading && Array.from({ length: 4 }).map((_, i) => <FeedCardSkeleton key={i} />)}
              <div className="divide-y divide-border/60">
                {exploreItems
                  .filter((a) => !trending?.items.slice(0, 10).some((t) => t.id === a.id))
                  .map((a) => (
                    <FeedCard key={a.id} article={a} onOpen={setOpenArticle} />
                  ))}
              </div>
              {isFetchingNextPage && Array.from({ length: 3 }).map((_, i) => <FeedCardSkeleton key={`p${i}`} />)}
              {hasNextPage && !isFetchingNextPage && exploreItems.length > 0 && (
                <button
                  onClick={() => fetchNextPage()}
                  className="w-full py-3 text-sm font-medium text-muted-foreground border border-border rounded-xl hover:bg-muted transition-colors"
                >
                  Show more
                </button>
              )}
            </section>
          </>
        )}
      </main>

      <SummarySheet article={openArticle} onClose={() => setOpenArticle(null)} />
    </div>
  );
}
