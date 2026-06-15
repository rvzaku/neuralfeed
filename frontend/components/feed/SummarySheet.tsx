"use client";

import { useEffect, useState } from "react";
import {
  X, ExternalLink, ThumbsUp, ThumbsDown, Bookmark, BookmarkCheck, AlertCircle, Share2, Check,
} from "lucide-react";
import { shareUrl } from "@/lib/share";
import { SourceBadge } from "@/components/ui/SourceBadge";
import { cn, formatRelativeTime, formatExactTime } from "@/lib/utils";
import { usePostFeedback, useSummary, useToggleBookmark } from "@/hooks/useFeed";
import type { Article } from "@/lib/types";

function Inline({ text }: { text: string }) {
  // Minimal inline GFM: **bold**, *italic*, `code`, [label](url)
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\[[^\]]+\]\([^)]+\))/g);
  return (
    <>
      {parts.map((part, i) => {
        if (part.startsWith("**") && part.endsWith("**"))
          return <strong key={i} className="font-semibold">{part.slice(2, -2)}</strong>;
        if (part.startsWith("`") && part.endsWith("`"))
          return <code key={i} className="font-mono text-[0.85em] bg-muted px-1 py-0.5 rounded">{part.slice(1, -1)}</code>;
        if (part.startsWith("*") && part.endsWith("*") && part.length > 2)
          return <em key={i}>{part.slice(1, -1)}</em>;
        const link = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
        if (link) {
          // Summary markdown is derived from untrusted web pages, so a link URL
          // could be `javascript:`/`data:` — only render an anchor for safe
          // http(s)/mailto schemes; otherwise show the label as plain text.
          const href = link[2].trim();
          if (/^(https?:\/\/|mailto:)/i.test(href)) {
            return (
              <a key={i} href={href} target="_blank" rel="noopener noreferrer" className="text-primary underline underline-offset-2">
                {link[1]}
              </a>
            );
          }
          return <span key={i}>{link[1]}</span>;
        }
        return part;
      })}
    </>
  );
}

type MdBlock =
  | { kind: "tldr"; text: string }
  | { kind: "heading"; text: string }
  | { kind: "ul" | "ol"; items: string[] }
  | { kind: "p"; text: string };

/** Parse line-by-line, not on blank-line blocks. The LLM frequently emits a
 *  heading and its body separated by a SINGLE newline ("## What it is\nA skill
 *  is…"); a blank-line split would glue them into one block and render the whole
 *  thing — body and literal `**` — as a heading. Walking lines makes headings,
 *  lists, and paragraphs robust regardless of blank-line spacing. */
function parseMarkdown(markdown: string): MdBlock[] {
  const blocks: MdBlock[] = [];
  let para: string[] = [];
  let list: { kind: "ul" | "ol"; items: string[] } | null = null;

  const flushPara = () => {
    if (para.length) { blocks.push({ kind: "p", text: para.join(" ") }); para = []; }
  };
  const flushList = () => {
    if (list) { blocks.push(list); list = null; }
  };

  for (const rawLine of markdown.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line) { flushPara(); flushList(); continue; }

    if (/^\*\*TL;DR/i.test(line) || /^TL;DR:/i.test(line)) {
      flushPara(); flushList();
      const text = line.replace(/^\*\*TL;DR:?\*\*:?\s*/i, "").replace(/^TL;DR:?\s*/i, "");
      blocks.push({ kind: "tldr", text });
      continue;
    }
    if (/^#{1,3}\s+/.test(line)) {
      flushPara(); flushList();
      blocks.push({ kind: "heading", text: line.replace(/^#{1,3}\s+/, "") });
      continue;
    }
    const bullet = line.match(/^([-*])\s+(.*)$/);
    const ordered = line.match(/^\d+\.\s+(.*)$/);
    if (bullet || ordered) {
      flushPara();
      const kind = ordered ? "ol" : "ul";
      const item = (ordered ? ordered[1] : bullet![2]);
      if (!list || list.kind !== kind) { flushList(); list = { kind, items: [] }; }
      list.items.push(item);
      continue;
    }
    // Plain text line — accumulate into the current paragraph
    flushList();
    para.push(line);
  }
  flushPara(); flushList();
  return blocks;
}

export function DeepMarkdown({ markdown }: { markdown: string }) {
  const blocks = parseMarkdown(markdown);
  return (
    <div className="space-y-3">
      {blocks.map((b, i) => {
        if (b.kind === "tldr") {
          return (
            <div key={i} className="rounded-lg border-l-2 border-primary bg-muted/50 px-4 py-3">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-primary mb-1">TL;DR</p>
              <p className="text-[15px] leading-[1.6] text-foreground font-medium">
                <Inline text={b.text} />
              </p>
            </div>
          );
        }
        if (b.kind === "heading") {
          return (
            <h3 key={i} className="font-semibold tracking-tight text-[15px] pt-2 text-foreground">
              <Inline text={b.text} />
            </h3>
          );
        }
        if (b.kind === "ul" || b.kind === "ol") {
          const Tag = b.kind === "ol" ? "ol" : "ul";
          return (
            <Tag key={i} className={cn(
              "pl-5 space-y-1.5 text-sm leading-relaxed text-foreground/90",
              b.kind === "ol" ? "list-decimal" : "list-disc"
            )}>
              {b.items.map((item, j) => <li key={j}><Inline text={item} /></li>)}
            </Tag>
          );
        }
        if (b.kind === "p") {
          return (
            <p key={i} className="text-[15px] leading-[1.7] text-foreground/90">
              <Inline text={b.text} />
            </p>
          );
        }
        return null;
      })}
    </div>
  );
}

interface SummarySheetProps {
  article: Article | null;
  onClose: () => void;
}

function SummarySkeleton() {
  return (
    <div className="space-y-3 animate-pulse" aria-hidden>
      {[...Array(3)].map((_, i) => (
        <div key={i} className="h-3.5 rounded bg-muted w-full" style={{ width: `${92 - i * 8}%` }} />
      ))}
      <div className="h-3.5 rounded bg-muted w-2/3" />
    </div>
  );
}

export function SummarySheet({ article, onClose }: SummarySheetProps) {
  const { data, isLoading, isError, error, refetch, isFetching } = useSummary(article?.id ?? null);
  const errorDetail =
    (error as { response?: { data?: { detail?: string } } } | null)?.response?.data?.detail ?? null;
  const isRateLimited = !!errorDetail && /rate|busy|try again|minute/i.test(errorDetail);
  const { mutate: postFeedback } = usePostFeedback();
  const { mutate: toggleBookmark } = useToggleBookmark();
  const [shared, setShared] = useState(false);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    if (article) document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [article, onClose]);

  if (!article) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/40 backdrop-blur-[2px] animate-in fade-in duration-150"
        onClick={onClose}
        aria-hidden
      />

      {/* Sheet: bottom on mobile, right panel on md+ */}
      <div
        role="dialog"
        aria-modal="true"
        aria-label={`Summary: ${article.title}`}
        className={cn(
          "fixed z-50 bg-background border-border shadow-xl flex flex-col",
          "inset-0 animate-in slide-in-from-bottom duration-200",
          "md:inset-y-6 md:inset-x-0 md:mx-auto md:max-w-2xl md:rounded-xl md:border md:slide-in-from-bottom-4"
        )}
      >
        {/* Grab handle (mobile) */}
        <div className="md:hidden pt-2 flex justify-center" aria-hidden>
          <div className="h-1 w-10 rounded-full bg-muted" />
        </div>

        {/* Header */}
        <div className="flex items-start gap-3 px-5 pt-3 pb-3 md:pt-5">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1.5">
              <SourceBadge sourceId={article.source_id} />
              <span className="text-xs text-muted-foreground" title={formatExactTime(article.published_at)}>
                {formatRelativeTime(article.published_at)} · {formatExactTime(article.published_at)}
              </span>
              {article.author && (
                <span className="text-xs text-muted-foreground truncate">· {article.author}</span>
              )}
            </div>
            <h2 className="font-semibold tracking-tight text-xl leading-snug">{article.title}</h2>
          </div>
          <button
            onClick={onClose}
            aria-label="Close summary"
            className="min-w-[44px] min-h-[44px] -mr-2 -mt-1 flex items-center justify-center rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-5 pb-4">
          {article.image_url && (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={article.image_url}
              alt=""
              loading="lazy"
              decoding="async"
              referrerPolicy="no-referrer"
              onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
              className="w-full aspect-video object-cover rounded-lg border border-border saturate-[.85] mb-4"
            />
          )}
          {isLoading && (
            <div className="space-y-4">
              <p className="text-xs text-muted-foreground">
                Writing your 5-minute read — this can take a minute the first time…
              </p>
              <SummarySkeleton />
            </div>
          )}

          {isError && (
            <div className="space-y-3">
              <div className="flex items-start gap-2 text-amber-600 dark:text-amber-400">
                <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                <p className="text-xs">
                  {isRateLimited
                    ? "Summaries are busy right now — give it a moment and try again."
                    : errorDetail
                      ? errorDetail
                      : "Couldn't generate a summary — read at the source below."}
                </p>
              </div>
              <button
                onClick={() => refetch()}
                disabled={isFetching}
                className="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 min-h-[36px] text-xs font-medium hover:bg-muted transition-colors disabled:opacity-50"
              >
                {isFetching ? "Retrying…" : "Try again"}
              </button>
              {article.summary && (
                <p className="text-sm leading-relaxed text-foreground/90">{article.summary}</p>
              )}
            </div>
          )}

          {data && (
            <div className="space-y-4">
              <p className="text-[10px] text-muted-foreground uppercase tracking-wider font-semibold">
                ~{data.reading_minutes} min read · AI-generated — read the original for the full story
              </p>
              <DeepMarkdown markdown={data.markdown} />
            </div>
          )}
        </div>

        {/* Footer actions */}
        <div className="border-t border-border px-5 py-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] flex items-center gap-2">
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 flex items-center justify-center gap-2 min-h-[44px] rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors"
          >
            Read at source
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
          <button
            aria-label="Thumbs up"
            onClick={() => postFeedback({ articleId: article.id, value: article.feedback === 1 ? 0 : 1 })}
            className={cn(
              "min-w-[44px] min-h-[44px] flex items-center justify-center rounded-lg border border-border transition-colors hover:bg-green-100 dark:hover:bg-green-900/30",
              article.feedback === 1 ? "text-green-600 dark:text-green-400" : "text-muted-foreground"
            )}
          >
            <ThumbsUp className="h-4 w-4" />
          </button>
          <button
            aria-label="Thumbs down"
            onClick={() => postFeedback({ articleId: article.id, value: article.feedback === -1 ? 0 : -1 })}
            className={cn(
              "min-w-[44px] min-h-[44px] flex items-center justify-center rounded-lg border border-border transition-colors hover:bg-red-100 dark:hover:bg-red-900/30",
              article.feedback === -1 ? "text-red-600 dark:text-red-400" : "text-muted-foreground"
            )}
          >
            <ThumbsDown className="h-4 w-4" />
          </button>
          <button
            aria-label={shared ? "Link copied" : "Share article"}
            onClick={async () => {
              const result = await shareUrl(article.url, article.title);
              if (result === "copied") {
                setShared(true);
                setTimeout(() => setShared(false), 1500);
              }
            }}
            className="min-w-[44px] min-h-[44px] flex items-center justify-center rounded-lg border border-border transition-colors hover:bg-primary/10 text-muted-foreground"
          >
            {shared ? <Check className="h-4 w-4 text-green-600 dark:text-green-400" /> : <Share2 className="h-4 w-4" />}
          </button>
          <button
            aria-label="Bookmark"
            onClick={() => toggleBookmark(article.id)}
            className={cn(
              "min-w-[44px] min-h-[44px] flex items-center justify-center rounded-lg border border-border transition-colors hover:bg-primary/10",
              article.is_bookmarked ? "text-primary" : "text-muted-foreground"
            )}
          >
            {article.is_bookmarked ? <BookmarkCheck className="h-4 w-4" /> : <Bookmark className="h-4 w-4" />}
          </button>
        </div>
      </div>
    </>
  );
}
