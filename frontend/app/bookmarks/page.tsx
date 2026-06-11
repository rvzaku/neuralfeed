"use client";

import { Bookmark, Inbox } from "lucide-react";
import { FeedCard } from "@/components/feed/FeedCard";
import { FeedCardSkeleton } from "@/components/feed/FeedCardSkeleton";
import { MobileNav } from "@/components/layout/MobileNav";
import { useFeed } from "@/hooks/useFeed";

export default function BookmarksPage() {
  const { data, isLoading, isError } = useFeed({ is_bookmarked: true, limit: 50 });

  return (
    <div className="flex flex-col min-h-screen">
      <header className="sticky top-0 z-10 bg-background/80 backdrop-blur-sm border-b border-border px-4 py-3 flex items-center gap-2">
        <Bookmark className="h-4 w-4 text-primary" />
        <h1 className="font-semibold text-sm">Saved Articles</h1>
        {data && (
          <span className="ml-auto text-xs text-muted-foreground">{data.total} saved</span>
        )}
      </header>

      <main className="flex-1 px-4 pt-4 pb-24 md:pb-6 max-w-2xl mx-auto w-full space-y-3">
        {isLoading && Array.from({ length: 4 }).map((_, i) => <FeedCardSkeleton key={i} />)}

        {isError && (
          <div className="flex flex-col items-center justify-center py-16 gap-2 text-center">
            <p className="text-sm text-muted-foreground">Failed to load bookmarks.</p>
          </div>
        )}

        {!isLoading && !isError && data?.items.length === 0 && (
          <div className="flex flex-col items-center justify-center py-20 gap-3 text-center">
            <Inbox className="h-10 w-10 text-muted-foreground" />
            <p className="text-sm font-medium">No saved articles yet</p>
            <p className="text-xs text-muted-foreground max-w-xs">
              Tap the bookmark icon on any article to save it here for later.
            </p>
          </div>
        )}

        {!isLoading && !isError && data?.items.map((article) => (
          <FeedCard key={article.id} article={article} />
        ))}
      </main>

      <MobileNav />
    </div>
  );
}
