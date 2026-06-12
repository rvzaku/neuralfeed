"use client";

import { useState } from "react";
import { ChevronDown, Layers } from "lucide-react";
import { FeedCard } from "./FeedCard";
import { useStoryDetail } from "@/hooks/useFeed";
import { cn, formatRelativeTime } from "@/lib/utils";
import type { Article, Story } from "@/lib/types";

const GROUP_LABELS: Record<string, string> = {
  research: "Papers",
  github: "Code & repos",
  social: "Discussion",
  company: "Official posts",
  newsletter: "Newsletters",
  video: "Videos",
  podcast: "Podcasts",
  funding: "Business",
  other: "More",
};

interface StoryCardProps {
  story: Story;
  onOpenArticle: (article: Article) => void;
}

export function StoryCard({ story, onOpenArticle }: StoryCardProps) {
  const [expanded, setExpanded] = useState(false);
  const { data: detail, isLoading } = useStoryDetail(expanded ? story.id : null);
  const single = story.article_count === 1;

  return (
    <div
      className={cn(
        "rounded-xl border border-border bg-card animate-in fade-in slide-in-from-bottom-2 duration-300",
        !expanded && "card-lift hover:border-primary/40",
        story.is_read && !expanded && "opacity-70"
      )}
    >
      <button
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
        className="w-full text-left p-4 cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-xl"
      >
        <div className="flex items-center justify-between gap-2 mb-1.5">
          <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
            {!single && <Layers className="h-3 w-3" aria-hidden />}
            {single
              ? "1 item"
              : `${story.article_count} items · ${story.source_count} sources`}
          </span>
          <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
            {formatRelativeTime(story.latest_at)}
            <ChevronDown
              className={cn("h-3.5 w-3.5 transition-transform duration-150", expanded && "rotate-180")}
              aria-hidden
            />
          </span>
        </div>

        <h3 className="font-serif font-bold text-[17px] leading-snug text-foreground">
          {!story.is_read && (
            <span className="inline-block h-2 w-2 rounded-full bg-primary mr-2 mb-0.5" aria-label="Unread" />
          )}
          {story.headline}
        </h3>

        {story.topic_tags.length > 0 && (
          <div className="flex gap-1.5 flex-wrap mt-2">
            {story.topic_tags.slice(0, 3).map((tag) => (
              <span
                key={tag}
                className="inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold bg-primary/10 text-primary"
              >
                {tag.replace(/-/g, " ")}
              </span>
            ))}
          </div>
        )}
      </button>

      {expanded && (
        <div className="border-t border-border px-3 pb-3 space-y-4">
          {isLoading && (
            <p className="px-1 pt-3 text-xs text-muted-foreground">Loading related items…</p>
          )}
          {detail &&
            Object.entries(detail.groups).map(([group, items]) => (
              <div key={group} className="pt-3">
                <p className="px-1 pb-2 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                  {GROUP_LABELS[group] ?? group}
                </p>
                <div className="space-y-2">
                  {items.map((a) => (
                    <FeedCard key={a.id} article={a} onOpen={onOpenArticle} />
                  ))}
                </div>
              </div>
            ))}
        </div>
      )}
    </div>
  );
}
