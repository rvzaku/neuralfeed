"use client";

import { memo, useState } from "react";
import { ThumbsUp, ThumbsDown, Bookmark, BookmarkCheck, ExternalLink, Share2, Check, Star, MessageSquare, ArrowBigUp, TrendingUp, Flame, Download, Heart } from "lucide-react";
import { shareUrl } from "@/lib/share";
import { SourceBadge } from "@/components/ui/SourceBadge";
import { HeatBadge } from "@/components/ui/HeatBadge";
import { cn, formatRelativeTime, formatExactTime } from "@/lib/utils";
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

function compact(n: number): string {
  return Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 }).format(n);
}

/** Platform stats in their own boxes, out of the subtitle flow — GitHub stars
 * (total + today) and Reddit/HN votes + comments are always visible
 * without opening the item (app-feedback-v4). */
// V8: color-coded per metric so the eye learns the legend — amber stars,
// emerald velocity, orange votes, sky comments, violet downloads, rose likes
const CHIP = "inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[11px] font-medium tabular-nums";
const CHIP_STYLES = {
  stars:     "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300",
  velocity:  "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300",
  votes:     "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300",
  comments:  "bg-sky-100 text-sky-700 dark:bg-sky-900/30 dark:text-sky-300",
  downloads: "bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-300",
  likes:     "bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-300",
};

/** Velocity metrics ("+N stars today") only tell the truth while fresh: once a
 *  repo drops off the trending page it is never re-fetched, so an old number
 *  must not keep claiming to be "today". 48h matches the daily fetch cadence. */
function engagementIsFresh(article: Article): boolean {
  if (!article.engagement_at) return false;
  const ageHours = (Date.now() - new Date(article.engagement_at).getTime()) / 3_600_000;
  return ageHours < 48;
}

function EngagementStats({ article }: { article: Article }) {
  const e = article.engagement;
  const fresh = engagementIsFresh(article);
  // arXiv has no native votes — traction comes from HF Daily Papers upvotes
  if (!e) {
    if (article.source_id.startsWith("arxiv") && article.trending_score > 0) {
      return (
        <div className="flex items-center gap-1.5 flex-wrap mb-2">
          <span className={cn(CHIP, CHIP_STYLES.velocity)}>
            <Flame className="h-3 w-3" />gaining traction · {compact(article.trending_score)} HF upvotes
          </span>
        </div>
      );
    }
    return null;
  }
  const stats: React.ReactNode[] = [];
  if (e.stars_total) {
    stats.push(<span key="st" className={cn(CHIP, CHIP_STYLES.stars)}><Star className="h-3 w-3" />{compact(e.stars_total)} stars</span>);
  }
  // "+N today" is a live velocity claim — drop it once the data is stale so a
  // week-old number never masquerades as today's gain (the lifetime star total
  // above stays, since it's still roughly accurate).
  if (e.stars_today && fresh) {
    stats.push(<span key="sd" className={cn(CHIP, CHIP_STYLES.velocity)}><TrendingUp className="h-3 w-3" />+{compact(e.stars_today)} today</span>);
  }
  // HN points and Reddit upvotes are distinct signals — show both when present
  // (editorial posts surfaced via traction lookup carry both).
  if (e.points) {
    // Link straight to the HN thread when we found one — proof the traction is
    // real and a one-tap route to the discussion (stops card-open propagation).
    stats.push(
      e.hn_url ? (
        <a
          key="hn"
          href={e.hn_url}
          target="_blank"
          rel="noopener noreferrer"
          onClick={(ev) => ev.stopPropagation()}
          className={cn(CHIP, CHIP_STYLES.votes, "hover:underline")}
          aria-label={`${compact(e.points)} points — open Hacker News discussion`}
        >
          <Flame className="h-3 w-3" />{compact(e.points)} HN
        </a>
      ) : (
        <span key="hn" className={cn(CHIP, CHIP_STYLES.votes)}><Flame className="h-3 w-3" />{compact(e.points)} HN</span>
      )
    );
  }
  if (e.upvotes) {
    stats.push(<span key="v" className={cn(CHIP, CHIP_STYLES.votes)}><ArrowBigUp className="h-3.5 w-3.5" />{compact(e.upvotes)}</span>);
  }
  if (e.comments) {
    stats.push(<span key="c" className={cn(CHIP, CHIP_STYLES.comments)}><MessageSquare className="h-3 w-3" />{compact(e.comments)}</span>);
  }
  if (e.downloads) {
    stats.push(<span key="d" className={cn(CHIP, CHIP_STYLES.downloads)}><Download className="h-3 w-3" />{compact(e.downloads)}</span>);
  }
  if (e.likes) {
    stats.push(<span key="l" className={cn(CHIP, CHIP_STYLES.likes)}><Heart className="h-3 w-3" />{compact(e.likes)}</span>);
  }
  if (stats.length === 0) return null;
  return <div className="flex items-center gap-1.5 flex-wrap mb-2">{stats}</div>;
}

function isUnseen(article: Article): boolean {
  if (article.is_read) return false;
  const ageHours = (Date.now() - new Date(article.published_at).getTime()) / 3_600_000;
  return ageHours > 48;
}

function FeedCardInner({ article, onOpen }: FeedCardProps) {
  const { mutate: postFeedback } = usePostFeedback();
  const { mutate: toggleBookmark } = useToggleBookmark();
  const unseen = isUnseen(article);
  const [shared, setShared] = useState(false);

  async function handleShare(e: React.MouseEvent) {
    e.stopPropagation();
    const result = await shareUrl(article.url, article.title);
    if (result === "copied") {
      setShared(true);
      setTimeout(() => setShared(false), 1500);
    }
  }

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
        "group relative rounded-xl border border-border bg-card p-4 cursor-pointer card-lift animate-in fade-in slide-in-from-bottom-2 duration-300",
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
          <HeatBadge heat={article.heat} />
          {unseen && (
            <span className="inline-flex items-center rounded-full bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 px-2 py-0.5 text-[10px] font-medium">
              Unread
            </span>
          )}
          {/* Generic trending chip only when there are no structured stats */}
          {!article.engagement && article.trending_score > 0 && (
            <span className={cn(
              "text-[10px] font-semibold rounded-full px-1.5 py-0.5",
              article.trending_score >= 500
                ? "bg-secondary text-secondary-foreground"
                : "text-muted-foreground"
            )}>
              {"↑"}{compact(article.trending_score)}
            </span>
          )}
          <span className="text-xs text-muted-foreground" title={formatExactTime(article.published_at)}>
            {formatRelativeTime(article.published_at)} · {formatExactTime(article.published_at)}
          </span>
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

      {/* V8 visible relevance — why this earned its slot (distinct from the
          content preview: tinted, icon-led, never mistakable for the summary) */}
      {(article.relevance != null || (article.why && article.why.length > 0)) && (
        <div className="flex items-center gap-1.5 flex-wrap mb-2 text-[11px] text-primary/90">
          {article.relevance != null && (
            <span className="inline-flex items-center rounded-full bg-primary/10 px-2 py-0.5 font-semibold tabular-nums">
              {article.relevance}% match
            </span>
          )}
          {article.why && article.why.length > 0 && (
            <span className="font-medium">✦ {article.why.join(" · ")}</span>
          )}
        </div>
      )}

      {/* Title + optional quiet thumbnail */}
      <div className="flex items-start gap-3">
        <div className="flex-1 min-w-0">
          <h3 className="font-display font-medium text-[17px] leading-[1.28] mb-1.5 line-clamp-2 text-foreground group-hover:text-primary transition-colors">
            {article.title}
          </h3>
          {/* Identity of rewritten slug titles — "what repo/model is this actually" */}
          {article.original_title && article.original_title !== article.title && (
            <p className="font-mono text-[11px] text-muted-foreground/80 mb-1.5 truncate">
              {article.original_title}
            </p>
          )}
          {/* V6: "why this matters now" — the editorial hook that sells the
              item's relevance, distinct from the neutral content summary below */}
          {article.context_line && (
            <p className="text-[13px] leading-snug text-foreground/90 font-medium mb-1.5">
              {article.context_line}
            </p>
          )}
          <EngagementStats article={article} />
          {article.summary && (
            <p className="text-xs text-muted-foreground line-clamp-2 mb-3 leading-relaxed">
              {article.summary}
            </p>
          )}
        </div>
        {article.image_url && (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={article.image_url}
            alt=""
            loading="lazy"
            decoding="async"
            referrerPolicy="no-referrer"
            onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
            className="h-16 w-16 rounded-lg object-cover border border-border saturate-[.85] shrink-0"
          />
        )}
      </div>

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
            aria-label={shared ? "Link copied" : "Share"}
            onClick={handleShare}
            className="min-w-[44px] min-h-[44px] flex items-center justify-center rounded-lg transition-colors hover:bg-primary/10 text-muted-foreground"
          >
            {shared ? <Check className="h-3.5 w-3.5 text-green-600 dark:text-green-400" /> : <Share2 className="h-3.5 w-3.5" />}
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

// Infinite scroll appends pages; memo keeps existing cards from re-rendering
// unless their own article object (or onOpen) changes.
export const FeedCard = memo(FeedCardInner);
