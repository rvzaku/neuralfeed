"use client";

// V9: topics are a first-class destination, not a strip inside Discover.
// Each card routes to the For You feed filtered to that topic.

import { useState } from "react";
import Link from "next/link";
import {
  Tags, Brain, Eye, Layers, Gamepad2, ShieldCheck, Bot, Cpu,
  AudioLines, GitFork, Server, Package, Banknote,
} from "lucide-react";
import { FeedCard } from "@/components/feed/FeedCard";
import { FeedCardSkeleton } from "@/components/feed/FeedCardSkeleton";
import { SummarySheet } from "@/components/feed/SummarySheet";
import { useFeed } from "@/hooks/useFeed";
import { cn } from "@/lib/utils";
import type { Article, TopicTag } from "@/lib/types";

const TOPICS: { tag: TopicTag; label: string; blurb: string; icon: typeof Brain }[] = [
  { tag: "llm",                    label: "Language Models",  blurb: "GPT, Claude, Gemini, open-weight LLMs", icon: Brain },
  { tag: "ai-agents",              label: "Agents",           blurb: "Autonomous tools that plan and act",     icon: Bot },
  { tag: "open-source",            label: "Open Source",      blurb: "Weights, frameworks, community tools",   icon: GitFork },
  { tag: "computer-vision",        label: "Computer Vision",  blurb: "Image and video understanding",          icon: Eye },
  { tag: "multimodal",             label: "Multimodal",       blurb: "Models that see, hear, and read",        icon: Layers },
  { tag: "reinforcement-learning", label: "Reinforcement",    blurb: "Learning by trial, reward, and play",    icon: Gamepad2 },
  { tag: "ai-safety",              label: "AI Safety",        blurb: "Alignment, evals, and governance",       icon: ShieldCheck },
  { tag: "robotics",               label: "Robotics",         blurb: "Embodied AI in the physical world",      icon: Cpu },
  { tag: "audio-speech",           label: "Audio & Speech",   blurb: "Voice, music, and sound generation",     icon: AudioLines },
  { tag: "ai-infrastructure",      label: "Infrastructure",   blurb: "Serving, GPUs, and MLOps",               icon: Server },
  { tag: "products",               label: "Products",         blurb: "Launches and shipping AI features",      icon: Package },
  { tag: "funding",                label: "Funding",          blurb: "Rounds, acquisitions, and the business",  icon: Banknote },
];

export default function TopicsPage() {
  const [active, setActive] = useState<TopicTag | null>(null);
  const [openArticle, setOpenArticle] = useState<Article | null>(null);
  const { data, isLoading } = useFeed(
    active ? { topic: active, ranked: true, time_range: "7d", limit: 15 } : { limit: 0 }
  );
  const activeTopic = TOPICS.find((t) => t.tag === active);

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

      <main className="flex-1 px-4 pt-4 pb-24 md:pb-8 max-w-2xl mx-auto w-full space-y-4">
        {!active ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {TOPICS.map(({ tag, label, blurb, icon: Icon }) => (
              <button
                key={tag}
                onClick={() => setActive(tag)}
                className="flex items-start gap-3 rounded-xl border border-border bg-card px-4 py-3.5 text-left hover:border-primary/40 transition-colors"
              >
                <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted">
                  <Icon className="h-4 w-4" />
                </span>
                <span className="min-w-0">
                  <span className="block text-sm font-semibold">{label}</span>
                  <span className="block text-xs text-muted-foreground leading-snug">{blurb}</span>
                </span>
              </button>
            ))}
          </div>
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
