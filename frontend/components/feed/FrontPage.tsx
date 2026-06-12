"use client";

// V6 front page: editor-arranged hierarchy — one hero story, then themed
// sections. Text-first: every layout works identically with zero images
// (V6.1 image discipline — images are furniture, never content).

import { useState } from "react";
import { ChevronDown } from "lucide-react";
import { FeedCard } from "./FeedCard";
import { SourceBadge } from "@/components/ui/SourceBadge";
import { useStoryDetail } from "@/hooks/useFeed";
import { cn, formatRelativeTime } from "@/lib/utils";
import type { Article, Story } from "@/lib/types";

const SECTION_LABELS: Record<string, string> = {
  llm: "Large Language Models",
  "computer-vision": "Computer Vision",
  multimodal: "Multimodal",
  "reinforcement-learning": "Reinforcement Learning",
  "ai-safety": "AI Safety",
  robotics: "Robotics",
  "ai-agents": "Agents",
  "audio-speech": "Audio & Speech",
  "open-source": "Open Source",
  "ai-infrastructure": "Infrastructure",
  products: "Products",
  funding: "Industry & Funding",
  general: "More Today",
};

function dateline(): string {
  return new Date().toLocaleDateString("en-US", {
    weekday: "long", month: "long", day: "numeric",
  });
}

/** Hidden-on-error image with V6.1 muted treatment. */
function QuietImage({ src, className, sizes }: { src: string; className?: string; sizes?: string }) {
  const [broken, setBroken] = useState(false);
  if (broken) return null;
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={src}
      alt=""
      loading="lazy"
      decoding="async"
      referrerPolicy="no-referrer"
      sizes={sizes}
      onError={() => setBroken(true)}
      className={cn("object-cover saturate-[.85] border border-border", className)}
    />
  );
}

/** Inline-expanding related items (story detail), shared by hero and rows. */
function RelatedItems({ story, onOpenArticle }: { story: Story; onOpenArticle: (a: Article) => void }) {
  const { data: detail, isLoading } = useStoryDetail(story.id);
  if (isLoading) return <p className="px-1 py-3 text-xs text-muted-foreground">Loading related items…</p>;
  if (!detail) return null;
  return (
    <div className="space-y-2 pt-3">
      {Object.values(detail.groups).flat().map((a) => (
        <FeedCard key={a.id} article={a as Article} onOpen={onOpenArticle} />
      ))}
    </div>
  );
}

function HeroStory({ story, onOpenArticle }: { story: Story; onOpenArticle: (a: Article) => void }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <article className="border-b border-border pb-6">
      <button
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
        className="w-full text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-lg"
      >
        <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-primary mb-3">
          Top story
        </p>
        {story.image_url && (
          <QuietImage
            src={story.image_url}
            className="w-full aspect-video rounded-lg mb-4"
            sizes="(max-width: 768px) 100vw, 768px"
          />
        )}
        <h2 className="font-semibold tracking-tight text-[26px] leading-[1.15] md:text-[32px] md:leading-[1.1]">
          {story.headline}
        </h2>
        {/* "Why this matters" — never clipped (app-feedback-v4) */}
        {(story.context_line || story.summary) && (
          <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
            {story.context_line ?? story.summary}
          </p>
        )}
        <div className="mt-3 flex items-center gap-2 flex-wrap text-sm text-muted-foreground">
          {story.source_ids?.slice(0, 4).map((sid) => (
            <SourceBadge key={sid} sourceId={sid} className="text-[10px]" />
          ))}
          <span>
            {story.article_count > 1
              ? `${story.article_count} related items · ${formatRelativeTime(story.latest_at)}`
              : formatRelativeTime(story.latest_at)}
          </span>
          <ChevronDown
            className={cn("inline h-3.5 w-3.5 transition-transform", expanded && "rotate-180")}
            aria-hidden
          />
        </div>
      </button>
      {expanded && <RelatedItems story={story} onOpenArticle={onOpenArticle} />}
    </article>
  );
}

function SectionRow({ story, onOpenArticle }: { story: Story; onOpenArticle: (a: Article) => void }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <li className="border-b border-border last:border-b-0">
      <button
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
        className="w-full flex items-start gap-4 py-4 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-lg"
      >
        <div className="flex-1 min-w-0">
          <h3 className={cn(
            "font-semibold text-[16px] leading-snug tracking-tight",
            story.is_read && "text-muted-foreground"
          )}>
            {!story.is_read && (
              <span className="inline-block h-1.5 w-1.5 rounded-full bg-primary mr-2 mb-0.5" aria-label="Unread" />
            )}
            {story.headline}
          </h3>
          {/* Context line shown in full — the clipped subtitle was the v4 complaint */}
          {(story.context_line || story.summary) && (
            <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
              {story.context_line ?? story.summary}
            </p>
          )}
          <div className="mt-1.5 flex items-center gap-1.5 flex-wrap text-xs text-muted-foreground">
            {story.source_ids?.slice(0, 3).map((sid) => (
              <SourceBadge key={sid} sourceId={sid} className="text-[9px] px-1.5" />
            ))}
            <span>
              {formatRelativeTime(story.latest_at)}
              {story.article_count > 1 && ` · ${story.article_count} items`}
            </span>
          </div>
        </div>
        {story.image_url && (
          <QuietImage
            src={story.image_url}
            className="h-16 w-16 md:h-[72px] md:w-[72px] rounded-lg shrink-0"
            sizes="72px"
          />
        )}
      </button>
      {expanded && <div className="pb-4"><RelatedItems story={story} onOpenArticle={onOpenArticle} /></div>}
    </li>
  );
}

export function FrontPage({ stories, onOpenArticle }: { stories: Story[]; onOpenArticle: (a: Article) => void }) {
  if (stories.length === 0) return null;
  const [hero, ...rest] = stories;

  // Group by dominant topic, preserving rank order; thin topics pool into "More Today"
  const sections = new Map<string, Story[]>();
  for (const s of rest) {
    const key = s.topic_tags[0] && SECTION_LABELS[s.topic_tags[0]] ? s.topic_tags[0] : "general";
    sections.set(key, [...(sections.get(key) ?? []), s]);
  }
  const ordered = [...sections.entries()].sort((a, b) => b[1].length - a[1].length);

  return (
    <div className="space-y-8">
      {/* Masthead dateline */}
      <div className="flex items-baseline justify-between border-b-2 border-foreground pb-3">
        <h1 className="font-semibold tracking-tight text-lg">For You</h1>
        <p className="text-xs text-muted-foreground">{dateline()}</p>
      </div>

      <HeroStory story={hero} onOpenArticle={onOpenArticle} />

      {ordered.map(([topic, items]) => (
        <section key={topic}>
          <h2 className="text-[11px] font-semibold uppercase tracking-[0.12em] text-muted-foreground border-b border-border pb-2">
            {SECTION_LABELS[topic]}
          </h2>
          <ul>
            {items.map((s) => (
              <SectionRow key={s.id} story={s} onOpenArticle={onOpenArticle} />
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}
