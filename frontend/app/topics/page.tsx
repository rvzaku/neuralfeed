"use client";

// V9: topics are a first-class destination, not a strip inside Discover.
// V10: the directory leads with what you actually find useful — topics you
// engage with and topics with the most fresh material float to the top, each
// card shows its live count, and quiet/empty topics drop into a muted shelf
// instead of pretending to be live. Each card routes to the For You feed
// filtered to that topic.

import { useMemo, useState } from "react";
import Link from "next/link";
import {
  Tags, Brain, Eye, Layers, Gamepad2, ShieldCheck, Bot, Cpu,
  AudioLines, GitFork, Server, Package, Banknote, Sparkles,
} from "lucide-react";
import { FeedCard } from "@/components/feed/FeedCard";
import { FeedCardSkeleton } from "@/components/feed/FeedCardSkeleton";
import { SummarySheet } from "@/components/feed/SummarySheet";
import { useFeed, useTopics } from "@/hooks/useFeed";
import { cn } from "@/lib/utils";
import type { Article, TopicTag } from "@/lib/types";

const TOPIC_META: Record<string, { label: string; blurb: string; icon: typeof Brain }> = {
  "llm":                    { label: "Language Models",  blurb: "GPT, Claude, Gemini, open-weight LLMs", icon: Brain },
  "ai-agents":              { label: "Agents",           blurb: "Autonomous tools that plan and act",     icon: Bot },
  "open-source":            { label: "Open Source",      blurb: "Weights, frameworks, community tools",   icon: GitFork },
  "computer-vision":        { label: "Computer Vision",  blurb: "Image and video understanding",          icon: Eye },
  "multimodal":             { label: "Multimodal",       blurb: "Models that see, hear, and read",        icon: Layers },
  "reinforcement-learning": { label: "Reinforcement",    blurb: "Learning by trial, reward, and play",    icon: Gamepad2 },
  "ai-safety":              { label: "AI Safety",        blurb: "Alignment, evals, and governance",       icon: ShieldCheck },
  "robotics":               { label: "Robotics",         blurb: "Embodied AI in the physical world",      icon: Cpu },
  "audio-speech":           { label: "Audio & Speech",   blurb: "Voice, music, and sound generation",     icon: AudioLines },
  "ai-infrastructure":      { label: "Infrastructure",   blurb: "Serving, GPUs, and MLOps",               icon: Server },
  "products":               { label: "Products",         blurb: "Launches and shipping AI features",      icon: Package },
  "funding":                { label: "Funding",          blurb: "Rounds, acquisitions, and the business", icon: Banknote },
};

export default function TopicsPage() {
  const [active, setActive] = useState<TopicTag | null>(null);
  const [openArticle, setOpenArticle] = useState<Article | null>(null);

  const { data: topicsData, isLoading: topicsLoading } = useTopics("7d");
  const { data, isLoading } = useFeed(
    active ? { topic: active, ranked: true, time_range: "7d", limit: 15 } : { limit: 1 }
  );

  // Merge server relevance/counts with the local display metadata, keeping only
  // topics we have a card design for. Server already orders by relevance.
  const ordered = useMemo(() => {
    const rows = topicsData?.items ?? [];
    return rows
      .filter((t) => TOPIC_META[t.tag])
      .map((t) => ({ ...t, ...TOPIC_META[t.tag] }));
  }, [topicsData]);

  const live = ordered.filter((t) => t.count > 0);
  const quiet = ordered.filter((t) => t.count === 0);
  const activeTopic = active ? TOPIC_META[active] : undefined;

  return (
    <div className="flex flex-col min-h-screen">
      <header className="sticky top-[var(--banner-h,0px)] md:static z-10 bg-background/80 backdrop-blur-md border-b border-border px-4 py-3 flex items-center gap-2.5">
        <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-foreground text-background">
          <Tags className="h-3.5 w-3.5" />
        </span>
        <h1 className="font-serif font-bold text-base">Topics</h1>
        {active && (
          <button onClick={() => setActive(null)} className="ml-auto text-xs text-primary hover:underline">
            All topics
          </button>
        )}
      </header>

      <main className="flex-1 px-4 pt-4 pb-24 md:pb-8 max-w-2xl mx-auto w-full space-y-5">
        {!active ? (
          <>
            <p className="text-xs text-muted-foreground -mb-1">
              Ordered by what you read and what&apos;s moving this week.
            </p>

            {topicsLoading ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {Array.from({ length: 6 }).map((_, i) => (
                  <div key={i} className="h-[68px] rounded-xl border border-border bg-card animate-pulse" />
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {live.map(({ tag, label, blurb, icon: Icon, count, weight }) => (
                  <button
                    key={tag}
                    onClick={() => setActive(tag as TopicTag)}
                    className="group flex items-start gap-3 rounded-xl border border-border bg-card px-4 py-3.5 text-left hover:border-primary/40 transition-colors"
                  >
                    <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted">
                      <Icon className="h-4 w-4" />
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="flex items-center gap-1.5">
                        <span className="block text-sm font-semibold truncate">{label}</span>
                        {weight > 0 && (
                          <Sparkles className="h-3 w-3 shrink-0 text-primary" aria-label="A topic you follow" />
                        )}
                      </span>
                      <span className="block text-xs text-muted-foreground leading-snug">{blurb}</span>
                    </span>
                    <span className="shrink-0 self-center rounded-full bg-muted px-2 py-0.5 text-[11px] font-medium tabular-nums text-muted-foreground">
                      {count}
                    </span>
                  </button>
                ))}
              </div>
            )}

            {quiet.length > 0 && (
              <div className="space-y-2">
                <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                  Quiet right now
                </p>
                <div className="flex flex-wrap gap-2">
                  {quiet.map(({ tag, label }) => (
                    <button
                      key={tag}
                      onClick={() => setActive(tag as TopicTag)}
                      className="rounded-full border border-border bg-card px-3 py-1 text-xs text-muted-foreground hover:border-primary/40 transition-colors"
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </>
        ) : (
          <section className="space-y-3">
            <div>
              <h2 className="text-base font-semibold tracking-tight">{activeTopic?.label}</h2>
              <p className="text-xs text-muted-foreground">
                Top items from the last 7 days, ranked by traction and your taste.
              </p>
            </div>
            {isLoading && Array.from({ length: 4 }).map((_, i) => <FeedCardSkeleton key={i} />)}
            {data?.items.map((a) => <FeedCard key={a.id} article={a} onOpen={setOpenArticle} />)}
            {!isLoading && data?.items.length === 0 && (
              <p className="text-sm text-muted-foreground py-8 text-center">
                Nothing in this topic right now — check back after the next fetch.
              </p>
            )}
            {!isLoading && (
              <Link
                href={`/?topic=${active}`}
                className={cn("block text-center text-sm text-primary hover:underline py-2")}
              >
                Open in your feed →
              </Link>
            )}
          </section>
        )}
      </main>

      <SummarySheet article={openArticle} onClose={() => setOpenArticle(null)} />
    </div>
  );
}
