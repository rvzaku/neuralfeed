"use client";

import { ThumbsUp, ThumbsDown, Bookmark, BookmarkCheck, ExternalLink } from "lucide-react";
import { SourceBadge } from "@/components/ui/SourceBadge";
import { cn, formatRelativeTime } from "@/lib/utils";
import { usePostFeedback, useToggleBookmark } from "@/hooks/useFeed";
import type { Article } from "@/lib/types";

interface FeedCardProps {
  article: Article;
  /** Opens the 1-minute summary sheet; falls back to direct link-out when absent */
  onOpen?: (article: Article) => void;
}

const TOPIC_COLORS: Record<string, string> = {
  llm:                    "bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-300",
  "computer-vision":      "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300",
  multimodal:             "bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-300",
  "reinforcement-learning":"bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300",
  "ai-safety":            "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300",
  robotics:               "bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-300",
  "ai-agents":            "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300",
  "open-source":          "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300",
  "ai-infrastructure":    "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
  products:               "bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-300",
  funding:                "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300",
};

function isUnseen(article: Article): boolean {
  if (article.is_read) return false;
  const ageHours = (Date.now() - new Date(article.published_at).getTime()) / 3_600_000;
  return ageHours > 48;
}

export function FeedCard({ article, onOpen }: FeedCardProps) {
  const { mutate: postFeedback } = usePostFeedback();
  const { mutate: toggleBookmark } = useToggleBookmark();
  const unseen = isUnseen(article);

  function activate() {
    if (onOpen) onOpen(article);
    else window.open(article.url, "_blank", "noopener,noreferrer");
  }

  function handleCardClick(e: React.MouseEvent) {
    // Prevent propagation from action buttons and the direct link
    const target = e.target as HTMLElement;
    if (target.closest("button") || target.closest("a")) return;
    activate();
  }

  function handleFeedback(e: React.MouseEvent, value: 1 | -1) {
    e.stopPropagation();
    const next = article.feedback === value ? 0 : value;
    postFeedback({ articleId: article.id, value: next as 1 | -1 | 0 });
  }

  function handleBookmark(e: React.MouseEvent) {
    e.stopPropagation();
    toggleBookmark(article.id);
  }

  return (
    <div
      role="article"
      tabIndex={0}
      onClick={handleCardClick}
      onKeyDown={(e) => e.key === "Enter" && activate()}
      className={cn(
        "group relative rounded-2xl border border-border bg-card p-4 cursor-pointer card-lift animate-in fade-in slide-in-from-bottom-2 duration-300",
        "hover:border-primary/40",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        article.is_read && "opacity-70"
      )}
    >
      {/* Header row */}
      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="flex items-center gap-2 flex-wrap">
          <SourceBadge sourceId={article.source_id} />
          {article.author && (
            <span className="text-xs text-muted-foreground truncate max-w-[140px]">{article.author}</span>
          )}
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          {unseen && (
            <span className="inline-flex items-center rounded-full bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 px-2 py-0.5 text-[10px] font-medium">
              Unread
            </span>
          )}
          {article.trending_score > 0 && (
            <span className={cn(
              "text-[10px] font-semibold rounded-full px-1.5 py-0.5",
              article.trending_score >= 500
                ? "bg-accent/10 text-accent"
                : "text-muted-foreground"
            )}>
              {article.trending_score >= 500 ? "🔥 " : "↑"}{Math.round(article.trending_score).toLocaleString()}
            </span>
          )}
          <span className="text-xs text-muted-foreground">{formatRelativeTime(article.published_at)}</span>
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            aria-label="Open original source"
            onClick={(e) => e.stopPropagation()}
            className="p-1 -m-1"
          >
            <ExternalLink className="h-3 w-3 text-muted-foreground/50 opacity-0 group-hover:opacity-100 transition-opacity" />
          </a>
        </div>
      </div>

      {/* Title */}
      <h3 className="font-serif font-semibold text-[15px] leading-snug mb-1.5 line-clamp-2 text-foreground group-hover:text-primary transition-colors">
        {article.title}
      </h3>

      {/* Summary */}
      {article.summary && (
        <p className="text-xs text-muted-foreground line-clamp-2 mb-3 leading-relaxed">
          {article.summary}
        </p>
      )}

      {/* Footer row */}
      <div className="flex items-center justify-between gap-2">
        {/* Topic tags */}
        <div className="flex gap-1.5 flex-wrap">
          {article.topic_tags.slice(0, 3).map((tag) => (
            <span
              key={tag}
              className={cn(
                "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium",
                TOPIC_COLORS[tag] ?? "bg-muted text-muted-foreground"
              )}
            >
              {tag.replace(/-/g, " ")}
            </span>
          ))}
        </div>

        {/* Action buttons — min 44px touch targets */}
        <div className="flex items-center gap-0.5 shrink-0">
          <button
            aria-label="Thumbs up"
            onClick={(e) => handleFeedback(e, 1)}
            className={cn(
              "min-w-[44px] min-h-[44px] flex items-center justify-center rounded-lg transition-colors",
              "hover:bg-green-100 dark:hover:bg-green-900/30",
              article.feedback === 1 ? "text-green-600 dark:text-green-400" : "text-muted-foreground"
            )}
          >
            <ThumbsUp className="h-3.5 w-3.5" />
          </button>
          <button
            aria-label="Thumbs down"
            onClick={(e) => handleFeedback(e, -1)}
            className={cn(
              "min-w-[44px] min-h-[44px] flex items-center justify-center rounded-lg transition-colors",
              "hover:bg-red-100 dark:hover:bg-red-900/30",
              article.feedback === -1 ? "text-red-600 dark:text-red-400" : "text-muted-foreground"
            )}
          >
            <ThumbsDown className="h-3.5 w-3.5" />
          </button>
          <button
            aria-label="Bookmark"
            onClick={handleBookmark}
            className={cn(
              "min-w-[44px] min-h-[44px] flex items-center justify-center rounded-lg transition-colors",
              "hover:bg-primary/10",
              article.is_bookmarked ? "text-primary" : "text-muted-foreground"
            )}
          >
            {article.is_bookmarked ? <BookmarkCheck className="h-3.5 w-3.5" /> : <Bookmark className="h-3.5 w-3.5" />}
          </button>
        </div>
      </div>
    </div>
  );
}
