"use client";

import { useState } from "react";
import Link from "next/link";
import { Compass, Search, Flame, Tags, UserPlus, RefreshCw, Check, X as XIcon } from "lucide-react";
import { MobileNav } from "@/components/layout/MobileNav";
import { FeedCard } from "@/components/feed/FeedCard";
import { FeedCardSkeleton } from "@/components/feed/FeedCardSkeleton";
import { SummarySheet } from "@/components/feed/SummarySheet";
import {
  useAccounts,
  useDeleteAccount,
  useFeed,
  usePatchAccount,
  useRunAccountDiscovery,
  useSearch,
} from "@/hooks/useFeed";
import { cn } from "@/lib/utils";
import type { Article } from "@/lib/types";

const TOPICS: { tag: string; label: string }[] = [
  { tag: "llm",                    label: "LLMs" },
  { tag: "computer-vision",        label: "Computer Vision" },
  { tag: "multimodal",             label: "Multimodal" },
  { tag: "reinforcement-learning", label: "RL" },
  { tag: "ai-safety",              label: "AI Safety" },
  { tag: "robotics",               label: "Robotics" },
  { tag: "ai-agents",              label: "Agents" },
  { tag: "audio-speech",           label: "Audio & Speech" },
  { tag: "open-source",            label: "Open Source" },
  { tag: "ai-infrastructure",      label: "Infrastructure" },
  { tag: "products",               label: "Products" },
  { tag: "funding",                label: "Funding" },
];

function SectionTitle({ icon: Icon, children }: { icon: typeof Flame; children: React.ReactNode }) {
  return (
    <h2 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
      <Icon className="h-3.5 w-3.5" />
      {children}
    </h2>
  );
}

function SuggestionsQueue() {
  const { data: accounts, isLoading } = useAccounts();
  const { mutate: patch } = usePatchAccount();
  const { mutate: remove } = useDeleteAccount();
  const { mutate: runDiscovery, isPending: isDiscovering } = useRunAccountDiscovery();

  // Review queue = discovered-but-not-yet-enabled follow targets
  const pending = (accounts ?? []).filter((a) => !a.enabled);

  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between">
        <SectionTitle icon={UserPlus}>Suggested follow targets</SectionTitle>
        <button
          onClick={() => runDiscovery()}
          disabled={isDiscovering}
          className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border border-border hover:bg-muted transition-colors disabled:opacity-50"
        >
          <RefreshCw className={cn("h-3 w-3", isDiscovering && "animate-spin")} />
          Find new
        </button>
      </div>

      {isLoading && <p className="text-xs text-muted-foreground">Loading…</p>}

      {!isLoading && pending.length === 0 && (
        <p className="text-xs text-muted-foreground">
          No pending suggestions — run &ldquo;Find new&rdquo; or manage targets under Sources.
        </p>
      )}

      <div className="space-y-2">
        {pending.slice(0, 6).map((a) => (
          <div key={a.id} className="flex items-center gap-3 rounded-xl border border-border bg-card px-4 py-3">
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{a.display_name}</p>
              <p className="text-xs text-muted-foreground truncate">
                @{a.handle} · {a.platform}
                {a.source_of_discovery && ` · via ${a.source_of_discovery}`}
              </p>
            </div>
            <button
              onClick={() => patch({ id: a.id, body: { enabled: true } })}
              aria-label={`Approve ${a.display_name}`}
              className="min-w-[44px] min-h-[44px] flex items-center justify-center rounded-lg border border-border text-green-600 dark:text-green-400 hover:bg-green-100 dark:hover:bg-green-900/30 transition-colors"
            >
              <Check className="h-4 w-4" />
            </button>
            <button
              onClick={() => remove(a.id)}
              aria-label={`Reject ${a.display_name}`}
              className="min-w-[44px] min-h-[44px] flex items-center justify-center rounded-lg border border-border text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors"
            >
              <XIcon className="h-4 w-4" />
            </button>
          </div>
        ))}
      </div>
    </section>
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
  });

  return (
    <div className="flex flex-col min-h-screen">
      <header className="sticky top-0 z-10 bg-background/80 backdrop-blur-sm border-b border-border px-4 py-3 flex items-center gap-2">
        <Compass className="h-4 w-4 text-primary" />
        <h1 className="font-semibold text-sm">Discover</h1>
      </header>

      <main className="flex-1 px-4 pt-4 pb-24 md:pb-8 max-w-2xl mx-auto w-full space-y-8">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search everything fetched…"
            className="w-full pl-10 pr-4 py-3 text-sm rounded-xl border border-border bg-card outline-none focus:ring-2 focus:ring-primary/30 min-h-[44px]"
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
            {/* Topic explorer */}
            <section className="space-y-3">
              <SectionTitle icon={Tags}>Browse by topic</SectionTitle>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                {TOPICS.map((t) => (
                  <Link
                    key={t.tag}
                    href={`/?topic=${t.tag}`}
                    className="flex items-center justify-center min-h-[44px] rounded-xl border border-border bg-card px-3 py-2 text-sm font-medium text-foreground/90 hover:border-primary/40 hover:text-primary transition-colors text-center"
                  >
                    {t.label}
                  </Link>
                ))}
              </div>
            </section>

            {/* Trending */}
            <section className="space-y-3">
              <SectionTitle icon={Flame}>Trending now</SectionTitle>
              {trendingLoading && Array.from({ length: 3 }).map((_, i) => <FeedCardSkeleton key={i} />)}
              {trending?.items.slice(0, 10).map((a) => (
                <FeedCard key={a.id} article={a} onOpen={setOpenArticle} />
              ))}
              {!trendingLoading && trending?.items.length === 0 && (
                <p className="text-sm text-muted-foreground">No trending items in the last 3 days.</p>
              )}
            </section>

            {/* Source suggestions */}
            <SuggestionsQueue />
          </>
        )}
      </main>

      <MobileNav />
      <SummarySheet article={openArticle} onClose={() => setOpenArticle(null)} />
    </div>
  );
}
