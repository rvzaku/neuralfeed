"use client";

import { useState } from "react";
import { Database, RefreshCw, CheckCircle2, XCircle, AlertTriangle, Users, Plus, Rss, MessageCircle, Github } from "lucide-react";
import { FollowTargets } from "@/components/sources/FollowTargets";
import { useAddSource, useSources, usePatchSource, useSourcesHealth } from "@/hooks/useFeed";
import { cn, formatRelativeTime } from "@/lib/utils";
import type { Source, SourceHealth } from "@/lib/types";

const CATEGORY_LABELS: Record<string, string> = {
  research: "Research",
  social: "Social",
  company: "Company Blogs",
  newsletter: "Newsletters",
  github: "GitHub",
  video: "Video",
  podcast: "Podcast",
  funding: "Funding",
};

const PRIORITY_DOT: Record<string, string> = {
  high:   "bg-green-500",
  medium: "bg-yellow-500",
  low:    "bg-gray-400",
};

function HealthBadge({ health }: { health?: SourceHealth }) {
  if (!health?.last_fetch_status) return null;
  if (health.last_fetch_status === "ok") {
    return (
      <span className="inline-flex items-center gap-1 text-[10px] text-green-600 dark:text-green-400">
        <CheckCircle2 className="h-3 w-3" />
        {health.last_fetched_at ? formatRelativeTime(health.last_fetched_at) : "ok"}
      </span>
    );
  }
  return (
    <span
      className="inline-flex items-center gap-1 text-[10px] text-amber-600 dark:text-amber-400"
      title={health.last_fetch_error ?? undefined}
    >
      <AlertTriangle className="h-3 w-3" />
      fetch failing
    </span>
  );
}

function SourceRow({ source, health }: { source: Source; health?: SourceHealth }) {
  const { mutate, isPending } = usePatchSource();

  return (
    <div className="flex items-center gap-3 py-3 px-4">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span
            className={cn("h-2 w-2 rounded-full shrink-0", PRIORITY_DOT[source.priority] ?? "bg-gray-400")}
          />
          <p className="text-sm font-medium truncate">{source.name}</p>
          <HealthBadge health={health} />
        </div>
        <div className="flex items-center gap-2 mt-0.5">
          <span className="text-xs text-muted-foreground capitalize">{source.category}</span>
          <span className="text-muted-foreground">·</span>
          <span className="text-xs text-muted-foreground">{source.refresh_interval}</span>
          {source.last_fetched_at && (
            <>
              <span className="text-muted-foreground">·</span>
              <span className="text-xs text-muted-foreground">
                signal {(source.signal_score * 100).toFixed(0)}%
              </span>
            </>
          )}
          {!source.enabled && source.notes && (
            <>
              <span className="text-muted-foreground">·</span>
              <span className="text-xs text-muted-foreground/70 truncate" title={source.notes}>
                {source.notes}
              </span>
            </>
          )}
        </div>
      </div>

      <button
        onClick={() => mutate({ id: source.id, body: { enabled: !source.enabled } })}
        disabled={isPending}
        className={cn(
          "relative inline-flex h-5 w-9 shrink-0 rounded-full transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary",
          source.enabled ? "bg-primary" : "bg-muted",
          isPending && "opacity-50"
        )}
        aria-checked={source.enabled}
        role="switch"
        aria-label={`Toggle ${source.name}`}
      >
        <span
          className={cn(
            "pointer-events-none block h-4 w-4 rounded-full bg-white shadow-sm ring-0 transition-transform duration-200 mt-0.5",
            source.enabled ? "translate-x-4" : "translate-x-0.5"
          )}
        />
      </button>
    </div>
  );
}

const KIND_OPTIONS = [
  { kind: "rss" as const,    label: "RSS feed",  icon: Rss,           placeholder: "https://example.com/feed.xml" },
  { kind: "reddit" as const, label: "Subreddit", icon: MessageCircle, placeholder: "LocalLLaMA" },
  { kind: "github" as const, label: "GitHub",    icon: Github,        placeholder: "topic or org, e.g. rag" },
];

/** V8: user-added sources — RSS URL, subreddit, or GitHub topic/org. */
function AddSourceForm() {
  const [open, setOpen] = useState(false);
  const [kind, setKind] = useState<"rss" | "reddit" | "github">("rss");
  const [value, setValue] = useState("");
  const { mutate: add, isPending, error, reset } = useAddSource();
  const selected = KIND_OPTIONS.find((o) => o.kind === kind)!;

  function submit() {
    if (!value.trim()) return;
    add({ kind, value: value.trim() }, { onSuccess: () => { setValue(""); setOpen(false); } });
  }

  if (!open) {
    return (
      <div className="px-4 pt-4">
        <button
          onClick={() => setOpen(true)}
          className="w-full flex items-center justify-center gap-2 py-2.5 text-sm font-medium border border-dashed border-border rounded-xl hover:bg-muted transition-colors text-muted-foreground"
        >
          <Plus className="h-4 w-4" /> Add a source
        </button>
      </div>
    );
  }

  return (
    <div className="mx-4 mt-4 rounded-xl border border-border bg-card p-4 space-y-3">
      <div className="flex items-center gap-1.5">
        {KIND_OPTIONS.map(({ kind: k, label, icon: Icon }) => (
          <button
            key={k}
            onClick={() => { setKind(k); reset(); }}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold border transition-colors",
              kind === k ? "bg-foreground text-background border-foreground" : "border-border text-muted-foreground hover:bg-muted"
            )}
          >
            <Icon className="h-3.5 w-3.5" /> {label}
          </button>
        ))}
      </div>
      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && submit()}
        placeholder={selected.placeholder}
        className="w-full px-3 py-2.5 text-sm rounded-lg border border-border bg-background outline-none focus:ring-2 focus:ring-primary/40"
        aria-label="Source value"
      />
      {error ? (
        <p className="text-xs text-destructive">
          {(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? "Could not add source."}
        </p>
      ) : null}
      <div className="flex items-center gap-2">
        <button
          onClick={submit}
          disabled={isPending || !value.trim()}
          className="px-4 py-2 rounded-full bg-foreground text-background text-xs font-semibold disabled:opacity-50"
        >
          {isPending ? "Adding…" : "Add source"}
        </button>
        <button onClick={() => setOpen(false)} className="text-xs text-muted-foreground hover:text-foreground">
          Cancel
        </button>
      </div>
    </div>
  );
}

function SourceList() {
  const { data: sources, isLoading, isError } = useSources(true);
  const { data: health } = useSourcesHealth();
  const healthById = new Map((health ?? []).map((h) => [h.id, h]));

  const grouped = sources?.reduce<Record<string, Source[]>>((acc, s) => {
    const cat = s.category;
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(s);
    return acc;
  }, {});

  const failing = (health ?? []).filter((h) => h.enabled && h.last_fetch_status === "error");

  return (
    <div>
      <AddSourceForm />
      {isLoading && (
        <div className="flex items-center justify-center py-20">
          <RefreshCw className="h-5 w-5 text-muted-foreground animate-spin" />
        </div>
      )}

      {isError && (
        <div className="flex flex-col items-center justify-center py-16 gap-2 text-center px-4">
          <XCircle className="h-8 w-8 text-destructive" />
          <p className="text-sm text-muted-foreground">Failed to load sources.</p>
        </div>
      )}

      {failing.length > 0 && (
        <div className="mx-4 mt-4 rounded-lg border border-amber-300 dark:border-amber-700 bg-amber-50 dark:bg-amber-900/20 px-3 py-2">
          <p className="text-xs text-amber-700 dark:text-amber-300">
            {failing.length} enabled {failing.length === 1 ? "source is" : "sources are"} failing to fetch — check the badges below.
          </p>
        </div>
      )}

      {grouped && Object.entries(grouped).map(([category, items]) => (
        <section key={category} className="mt-4">
          <div className="px-4 pb-1">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              {CATEGORY_LABELS[category] ?? category}
            </h2>
          </div>
          <div className="divide-y divide-border border-y border-border">
            {items.map((source) => (
              <SourceRow key={source.id} source={source} health={healthById.get(source.id)} />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}

export default function SourcesPage() {
  const [tab, setTab] = useState<"sources" | "targets">("sources");
  const { data: sources } = useSources(true);
  const enabledCount = sources?.filter((s) => s.enabled).length ?? 0;
  const totalCount = sources?.length ?? 0;

  return (
    <div className="flex flex-col min-h-screen">
      <header className="sticky top-0 md:static z-10 bg-background/80 backdrop-blur-md border-b border-border px-4 py-3 flex items-center gap-2.5">
        <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-foreground text-background">
          <Database className="h-3.5 w-3.5" />
        </span>
        <h1 className="font-serif font-bold text-base">Sources</h1>
        <span className="ml-auto text-xs text-muted-foreground">
          {enabledCount}/{totalCount} enabled
        </span>
      </header>

      {/* Tabs */}
      <div className="px-4 pt-3 max-w-2xl mx-auto w-full">
        <div className="flex items-center gap-1 rounded-full bg-muted p-0.5 w-fit" role="tablist">
          {([
            ["sources", "Sources", Database],
            ["targets", "Follow targets", Users],
          ] as const).map(([value, label, Icon]) => (
            <button
              key={value}
              role="tab"
              aria-selected={tab === value}
              onClick={() => setTab(value)}
              className={cn(
                "flex items-center gap-1.5 px-4 py-1.5 rounded-full text-xs font-semibold transition-all min-h-[36px]",
                tab === value
                  ? "bg-foreground text-background shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              <Icon className="h-3.5 w-3.5" />
              {label}
            </button>
          ))}
        </div>
      </div>

      <main className="flex-1 pb-24 md:pb-6 max-w-2xl mx-auto w-full">
        {tab === "sources" ? <SourceList /> : <FollowTargets />}
      </main>

    </div>
  );
}
