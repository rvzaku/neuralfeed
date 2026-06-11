"use client";

import { useState } from "react";
import { useSearchParams } from "next/navigation";
import { Search, AlertCircle, Inbox } from "lucide-react";
import { FeedCard } from "./FeedCard";
import { FeedCardSkeleton } from "./FeedCardSkeleton";
import { FilterBar } from "./FilterBar";
import { FilterDrawer } from "./FilterDrawer";
import { DesktopSidebar } from "./DesktopSidebar";
import { RefreshIndicator } from "./RefreshIndicator";
import { SavedViewSwitcher } from "./SavedViewSwitcher";
import { SearchModal } from "./SearchModal";
import { useFeed } from "@/hooks/useFeed";
import type { FeedFilters } from "@/lib/types";

export function FeedView() {
  const params = useSearchParams();
  const [searchOpen, setSearchOpen] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const filters: FeedFilters = {
    category:    (params.get("category") as FeedFilters["category"]) || undefined,
    topic:       (params.get("topic") as FeedFilters["topic"]) || undefined,
    source_id:   params.get("source_id") || undefined,
    time_range:  (params.get("time_range") as FeedFilters["time_range"]) || "7d",
    is_read:     params.get("is_read") === "false" ? false : params.get("is_read") === "true" ? true : undefined,
    ranked:      params.get("ranked") === "true" ? true : undefined,
    feedback:    params.get("feedback") ? Number(params.get("feedback")) as FeedFilters["feedback"] : undefined,
    min_signal:  params.get("min_signal") ? Number(params.get("min_signal")) : undefined,
    limit: 30,
  };

  const { data, isLoading, isError, refetch } = useFeed(filters);

  return (
    <div className="flex min-h-screen">
      {/* Desktop sidebar — hidden on mobile/tablet, visible lg+ */}
      <DesktopSidebar />

      {/* Main content column */}
      <div className="flex flex-col flex-1 min-w-0">
        {/* Saved view presets — mobile/tablet only (desktop uses sidebar) */}
        <div className="lg:hidden">
          <SavedViewSwitcher />
        </div>

        {/* Filter bar */}
        <FilterBar onFilterClick={() => setDrawerOpen(true)} />

        <main className="flex-1 px-4 pt-4 pb-24 md:pb-6 lg:pb-8 max-w-2xl lg:max-w-3xl xl:max-w-4xl mx-auto w-full space-y-3">
          {/* Mobile top bar */}
          <div className="flex items-center justify-between lg:hidden">
            <h1 className="font-bold text-base tracking-tight">NeuralFeed</h1>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setSearchOpen(true)}
                className="p-2 rounded-lg hover:bg-muted transition-colors"
                aria-label="Search"
              >
                <Search className="h-4 w-4 text-muted-foreground" />
              </button>
              <RefreshIndicator />
            </div>
          </div>

          {/* Desktop top bar */}
          <div className="hidden lg:flex items-center justify-between pb-2">
            <h1 className="font-bold text-lg tracking-tight">Feed</h1>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setSearchOpen(true)}
                className="flex items-center gap-2 px-3 py-1.5 text-sm text-muted-foreground border border-border rounded-lg hover:bg-muted transition-colors"
                aria-label="Search"
              >
                <Search className="h-3.5 w-3.5" />
                Search…
                <kbd className="ml-2 text-[10px] text-muted-foreground/60 border border-border rounded px-1">⌘K</kbd>
              </button>
              <RefreshIndicator />
            </div>
          </div>

          {/* Loading */}
          {isLoading && Array.from({ length: 6 }).map((_, i) => <FeedCardSkeleton key={i} />)}

          {/* Error */}
          {isError && (
            <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
              <AlertCircle className="h-8 w-8 text-destructive" />
              <p className="text-sm text-muted-foreground">Failed to load feed.</p>
              <button onClick={() => refetch()} className="text-sm text-primary hover:underline">
                Try again
              </button>
            </div>
          )}

          {/* Empty */}
          {!isLoading && !isError && data?.items.length === 0 && (
            <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
              <Inbox className="h-8 w-8 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">No items match your filters.</p>
              <p className="text-xs text-muted-foreground">Try refreshing or broadening your filters.</p>
            </div>
          )}

          {/* Feed items */}
          {!isLoading && !isError && data?.items.map((article) => (
            <FeedCard key={article.id} article={article} />
          ))}

          {data?.has_more && (
            <div className="py-4 text-center">
              <p className="text-xs text-muted-foreground">
                Showing {data.items.length} of {data.total} items
              </p>
            </div>
          )}
        </main>
      </div>

      {/* Mobile/tablet filter drawer */}
      <FilterDrawer isOpen={drawerOpen} onClose={() => setDrawerOpen(false)} />

      <SearchModal isOpen={searchOpen} onClose={() => setSearchOpen(false)} />
    </div>
  );
}
