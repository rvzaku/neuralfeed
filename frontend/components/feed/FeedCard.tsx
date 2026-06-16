"use client";

import { memo, useState } from "react";
import { ThumbsUp, ThumbsDown, Bookmark, BookmarkCheck, ExternalLink, Share2, Check, Star, MessageSquare, ArrowBigUp, TrendingUp, Flame, Download } from "lucide-react";
import { shareUrl } from "@/lib/share";
import { SourceBadge } from "@/components/ui/SourceBadge";
import { HeatBadge } from "@/components/ui/HeatBadge";
import { RelevanceBadge } from "@/components/ui/RelevanceBadge";
import { cn, formatRelativeTime, formatExactTime } from "@/lib/utils";
import { usePostFeedback, useToggleBookmark } from "@/hooks/useFeed";
import type { Article } from "@/lib/types";

interface FeedCardProps {
  article: Article;
  /** Opens the 1-minute summary sheet; falls back to direct link-out when absent */
  onOpen?: (article: Article) => void;
  /** 1-based rank shown as a quiet editorial index on the finite numbered Feed */
  rank?: number;
}

function compact(n: number): string {
  return Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 }).format(n);
}

/** Traction is shown as quiet monochrome text + a small glyph — NOT filled colour
 *  pills. A confetti of coloured badges is the #1 "AI-slop" tell; restraint reads
 *  premium. The single permitted tint is a faint green on live "+today" velocity. */
const STAT = "inline-flex items-center gap-1 text-[11.5px] tabular-nums text-muted-foreground";

function engagementIsFresh(article: Article): boolean {
  if (!article.engagement_at) return false;
  const ageHours = (Date.now() - new Date(article.engagement_at).getTime()) / 3_600_000;
  return ageHours < 48;
}

function EngagementStats({ article }: { article: Article }) {
  const e = article.engagement;
  const fresh = engagementIsFresh(article);
  if (!e) {
    if (article.source_id.startsWith("arxiv") && article.trending_score > 0) {
      return (
        <span className={STAT}>
          <Flame className="h-3 w-3" /> {compact(article.trending_score)} HF upvotes
        </span>
      );
    }
    return null;
  }
  const stats: React.ReactNode[] = [];
  if (e.stars_total) {
    stats.push(<span key="st" className={STAT}><Star className="h-3 w-3" />{compact(e.stars_total)}</span>);
  }
  if (e.stars_today && fresh) {
    stats.push(
      <span key="sd" className="inline-flex items-center gap-1 text-[11.5px] tabular-nums text-emerald-600 dark:text-emerald-400">
        <TrendingUp className="h-3 w-3" />+{compact(e.stars_today)} today
      </span>
    );
  }
  if (e.points) {
    stats.push(
      e.hn_url ? (
        <a key="hn" href={e.hn_url} target="_blank" rel="noopener noreferrer" onClick={(ev) => ev.stopPropagation()} className={cn(STAT, "hover:text-foreground hover:underline")} aria-label={`${compact(e.points)} points — open Hacker News discussion`}>
          <Flame className="h-3 w-3" />{compact(e.points)} HN
        </a>
      ) : (
        <span key="hn" className={STAT}><Flame className="h-3 w-3" />{compact(e.points)} HN</span>
      )
    );
  }
  if (e.upvotes) {
    stats.push(<span key="v" className={STAT}><ArrowBigUp className="h-3.5 w-3.5" />{compact(e.upvotes)}</span>);
  }
  if (e.comments) {
    stats.push(<span key="c" className={STAT}><MessageSquare className="h-3 w-3" />{compact(e.comments)}</span>);
  }
  if (e.downloads) {
    stats.push(<span key="d" className={STAT}><Download className="h-3 w-3" />{compact(e.downloads)}</span>);
  }
  if (stats.length === 0) return null;
  return <div className="flex items-center gap-3 flex-wrap">{stats}</div>;
}

function isUnseen(article: Article): boolean {
  if (article.is_read) return false;
  const ageHours = (Date.now() - new Date(article.published_at).getTime()) / 3_600_000;
  return ageHours > 48;
}

function FeedCardInner({ article, onOpen, rank }: FeedCardProps) {
  const { mutate: postFeedback } = usePostFeedback();
  const { mutate: toggleBookmark } = useToggleBookmark();
  const unread = !article.is_read;
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
    <article
      role="article"
      tabIndex={0}
      onClick={handleCardClick}
      onKeyDown={(e) => e.key === "Enter" && activate()}
      className={cn(
        "group relative cursor-pointer px-1 py-5 transition-colors sm:px-2",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:rounded-lg",
        article.is_read && "opacity-55 hover:opacity-90"
      )}
    >
      {/* Unread accent dot — the only chrome announcing freshness (no coloured badge) */}
      {unread && (
        <span aria-hidden className="absolute left-[-2px] top-[26px] h-1.5 w-1.5 rounded-full bg-primary sm:left-[-6px]" />
      )}

      {/* Meta line — one quiet row */}
      <div className="mb-2 flex items-center gap-2 text-[11.5px] text-muted-foreground">
        <SourceBadge sourceId={article.source_id} />
        {article.author && <span className="truncate max-w-[140px]">{article.author}</span>}
        <span className="text-muted-foreground/40">·</span>
        <span className="tabular-nums" title={formatExactTime(article.published_at)}>{formatRelativeTime(article.published_at)}</span>
        <div className="ml-auto flex items-center gap-2">
          <RelevanceBadge relevance={article.relevance} />
          <HeatBadge heat={article.heat} />
        </div>
      </div>

      {/* Title + optional quiet thumbnail */}
      <div className="flex items-start gap-4">
        {rank != null && (
          <span
            aria-hidden
            className="shrink-0 font-serif text-xl font-semibold leading-[1.3] tabular-nums text-muted-foreground/50"
          >
            {rank}.
          </span>
        )}
        <div className="min-w-0 flex-1">
          <h3 className="font-display text-[18px] font-medium leading-[1.3] text-foreground transition-colors group-hover:text-primary line-clamp-2">
            {article.title}
          </h3>
          {article.original_title && article.original_title !== article.title && (
            <p className="mt-1 truncate font-mono text-[11px] text-muted-foreground/70">{article.original_title}</p>
          )}
          {article.context_line && (
            <p className="mt-1.5 border-l border-primary/50 pl-2.5 text-[13px] leading-snug text-foreground/85">
              {article.context_line}
            </p>
          )}
          {article.summary && !article.context_line && (
            <p className="mt-1.5 line-clamp-2 text-[13px] leading-relaxed text-muted-foreground">{article.summary}</p>
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
            className="hidden h-[72px] w-24 shrink-0 rounded-md border border-border object-cover sm:block"
          />
        )}
      </div>

      {/* Footer — traction · topics · actions, all quiet */}
      <div className="mt-3 flex items-center gap-x-4 gap-y-2">
        <EngagementStats article={article} />

        {/* Topic tags — hairline outline, single muted tone (no rainbow) */}
        <div className="hidden flex-wrap gap-1.5 sm:flex">
          {article.topic_tags.slice(0, 2).map((tag) => (
            <span key={tag} className="inline-flex items-center rounded-full border border-border px-2 py-0.5 text-[10px] font-medium lowercase text-muted-foreground">
              {tag.replace(/-/g, " ")}
            </span>
          ))}
        </div>

        <div className="ml-auto flex items-center gap-0.5 shrink-0">
          <button
            aria-label="Thumbs up"
            onClick={(e) => handleFeedback(e, 1)}
            className={cn("flex h-9 w-9 items-center justify-center rounded-lg transition-colors hover:bg-secondary", article.feedback === 1 ? "text-primary" : "text-muted-foreground/70")}
          >
            <ThumbsUp className="h-3.5 w-3.5" />
          </button>
          <button
            aria-label="Thumbs down"
            onClick={(e) => handleFeedback(e, -1)}
            className={cn("flex h-9 w-9 items-center justify-center rounded-lg transition-colors hover:bg-secondary", article.feedback === -1 ? "text-foreground" : "text-muted-foreground/70")}
          >
            <ThumbsDown className="h-3.5 w-3.5" />
          </button>
          <button
            aria-label={shared ? "Link copied" : "Share"}
            onClick={handleShare}
            className="flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground/70 transition-colors hover:bg-secondary"
          >
            {shared ? <Check className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" /> : <Share2 className="h-3.5 w-3.5" />}
          </button>
          <button
            aria-label="Bookmark"
            onClick={handleBookmark}
            className={cn("flex h-9 w-9 items-center justify-center rounded-lg transition-colors hover:bg-secondary", article.is_bookmarked ? "text-primary" : "text-muted-foreground/70")}
          >
            {article.is_bookmarked ? <BookmarkCheck className="h-3.5 w-3.5" /> : <Bookmark className="h-3.5 w-3.5" />}
          </button>
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            aria-label="Open original source"
            onClick={(e) => e.stopPropagation()}
            className="flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground/70 transition-colors hover:bg-secondary"
          >
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
        </div>
      </div>
    </article>
  );
}

// Infinite scroll appends pages; memo keeps existing cards from re-rendering
// unless their own article object (or onOpen) changes.
export const FeedCard = memo(FeedCardInner);
