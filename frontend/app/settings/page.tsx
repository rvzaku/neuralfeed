"use client";

import { useState, useEffect } from "react";
import { Settings, Save, RotateCcw } from "lucide-react";
import { ThemeToggle } from "@/components/layout/ThemeToggle";
import { LogOut } from "lucide-react";
import { useRouter } from "next/navigation";
import { clearSession, getEmail } from "@/lib/auth";
import { usePreferences, useSetPreference, useSources } from "@/hooks/useFeed";
import { topicLabel } from "@/lib/topics";
import { cn } from "@/lib/utils";

function parseWeights(raw: unknown): Record<string, number> {
  let val = raw;
  if (typeof val === "string") {
    try {
      val = JSON.parse(val);
    } catch {
      return {};
    }
  }
  if (!val || typeof val !== "object") return {};
  const out: Record<string, number> = {};
  for (const [k, v] of Object.entries(val as Record<string, unknown>)) {
    const n = Number(v);
    if (Number.isFinite(n) && n !== 0) out[k] = n;
  }
  return out;
}

// Renders the topics NeuralFeed has learned the user leans into vs tunes out,
// from their reactions — making the otherwise-invisible personalization legible.
function YourTasteSection({ weights }: { weights: Record<string, number> }) {
  const entries = Object.entries(weights).sort((a, b) => b[1] - a[1]);
  const liked = entries.filter(([, w]) => w > 0);
  const avoided = entries.filter(([, w]) => w < 0).reverse(); // strongest first
  const max = Math.max(1, ...entries.map(([, w]) => Math.abs(w)));

  return (
    <section>
      <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
        Your Taste
      </h2>
      <p className="text-xs text-muted-foreground mb-4">
        Learned from your thumbs up/down and saves — no sliders to maintain. React
        to articles and the For You feed adapts.
      </p>

      {entries.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border bg-card p-4">
          <p className="text-sm text-muted-foreground">
            Nothing learned yet. Like, save, or hide a few articles and your taste
            will start to show up here.
          </p>
        </div>
      ) : (
        <div className="space-y-4 rounded-xl border border-border bg-card p-4">
          {liked.length > 0 && (
            <TasteList title="Leaning into" tone="positive" items={liked} max={max} />
          )}
          {avoided.length > 0 && (
            <TasteList title="Tuning out" tone="negative" items={avoided} max={max} />
          )}
        </div>
      )}
    </section>
  );
}

function TasteList({
  title,
  tone,
  items,
  max,
}: {
  title: string;
  tone: "positive" | "negative";
  items: [string, number][];
  max: number;
}) {
  return (
    <div>
      <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground mb-2">
        {title}
      </p>
      <div className="space-y-2">
        {items.map(([tag, w]) => (
          <div key={tag} className="flex items-center gap-3">
            <span className="w-36 shrink-0 truncate text-sm">{topicLabel(tag)}</span>
            <div className="h-1.5 flex-1 rounded-full bg-muted overflow-hidden">
              <div
                className={cn(
                  "h-full rounded-full",
                  tone === "positive" ? "bg-foreground" : "bg-destructive/60"
                )}
                style={{ width: `${Math.round((Math.abs(w) / max) * 100)}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function AccountSection() {
  const router = useRouter();
  const email = typeof window !== "undefined" ? getEmail() : null;
  return (
    <section>
      <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
        Account
      </h2>
      <div className="flex items-center justify-between py-2.5 border border-border rounded-xl px-4 bg-card">
        <div className="min-w-0">
          <p className="text-sm font-medium truncate">{email ?? "Signed in"}</p>
          <p className="text-xs text-muted-foreground">JWT session · this device</p>
        </div>
        <button
          onClick={() => { clearSession(); router.replace("/login"); }}
          className="flex items-center gap-1.5 text-xs font-semibold text-destructive px-3 py-2 rounded-full border border-destructive/30 hover:bg-destructive/10 transition-colors"
        >
          <LogOut className="h-3.5 w-3.5" />
          Sign out
        </button>
      </div>
    </section>
  );
}

export default function SettingsPage() {
  const { data: prefs, isLoading } = usePreferences();
  const { mutate: setPref, isPending: isSaving } = useSetPreference();
  const { data: sources } = useSources(true);

  const [mutedSources, setMutedSources] = useState<string[]>([]);
  const [feedDensity, setFeedDensity] = useState(10);
  const [dirty, setDirty] = useState(false);

  // topic_weights is learned from likes/dislikes/saves; the API may hand it back
  // as an already-parsed object or a JSON string, so normalize both.
  const topicWeights = parseWeights(prefs?.topic_weights);

  const [digestEmail, setDigestEmail] = useState(false);

  useEffect(() => {
    if (!prefs) return;
    const density = Number(prefs.feed_density);
    setFeedDensity(Number.isFinite(density) && density > 0 ? density : 10);
    try {
      setMutedSources(prefs.muted_sources ? JSON.parse(prefs.muted_sources) : []);
    } catch {
      setMutedSources([]);
    }
    const de: unknown = prefs.digest_email_enabled;
    setDigestEmail(de === true || de === "true");
  }, [prefs]);

  const toggleDigestEmail = () => {
    const next = !digestEmail;
    setDigestEmail(next);
    setPref({ key: "digest_email_enabled", value: next });
  };

  const toggleMutedSource = (id: string) => {
    setMutedSources((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]
    );
    setDirty(true);
  };

  const handleSave = () => {
    setPref({ key: "muted_sources", value: mutedSources });
    setPref({ key: "feed_density", value: feedDensity });
    setDirty(false);
  };

  const handleReset = () => {
    setMutedSources([]);
    setDirty(true);
  };

  return (
    <div className="flex flex-col min-h-screen">
      <header className="sticky top-[var(--banner-h,0px)] md:static z-10 bg-background/80 backdrop-blur-md border-b border-border px-4 py-3 flex items-center gap-2.5">
        <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-foreground text-background">
          <Settings className="h-3.5 w-3.5" />
        </span>
        <h1 className="font-serif font-semibold text-lg tracking-tight">Settings</h1>
        {dirty && (
          <div className="ml-auto flex items-center gap-2">
            <button
              onClick={handleReset}
              className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground px-2 py-1 rounded-md hover:bg-muted transition-colors"
            >
              <RotateCcw className="h-3 w-3" />
              Reset
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="flex items-center gap-1 text-xs bg-foreground text-background px-3.5 py-1.5 rounded-full font-semibold shadow-sm hover:opacity-90 transition-opacity disabled:opacity-50"
            >
              <Save className="h-3 w-3" />
              Save
            </button>
          </div>
        )}
      </header>

      <main className="flex-1 pb-24 md:pb-6 max-w-2xl mx-auto w-full px-4 space-y-8 pt-6">
        <AccountSection />

        {/* Appearance */}
        <section>
          <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
            Appearance
          </h2>
          <div className="flex items-center justify-between py-2.5 border border-border rounded-xl px-4 bg-card">
            <span className="text-sm">Theme</span>
            <ThemeToggle />
          </div>
        </section>

        {/* Feed density — V7 anti-overwhelm control */}
        <section>
          <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
            Feed Density
          </h2>
          <p className="text-xs text-muted-foreground mb-4">
            How many ranked items your Feed shows. Lower = only the biggest
            stories; higher = broader coverage. Discover always has more.
          </p>
          <div className="flex items-center gap-2">
            {[5, 10, 15, 20].map((n) => (
              <button
                key={n}
                onClick={() => { setFeedDensity(n); setDirty(true); }}
                className={cn(
                  "flex-1 py-2.5 rounded-xl border text-sm font-semibold transition-colors",
                  feedDensity === n
                    ? "bg-foreground text-background border-foreground"
                    : "border-border hover:bg-muted text-muted-foreground"
                )}
              >
                {n}<span className="font-normal text-xs"> items</span>
              </button>
            ))}
          </div>
        </section>

        {/* Learned personalization — V8: no manual sliders, but now visible */}
        <YourTasteSection weights={topicWeights} />

        {/* Daily digest email opt-in (P1.4) */}
        <section>
          <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
            Daily Digest
          </h2>
          <div className="flex items-center justify-between gap-4 rounded-xl border border-border bg-card px-4 py-3.5">
            <div className="min-w-0">
              <p className="text-sm font-medium">Email me “Today in AI”</p>
              <p className="text-xs text-muted-foreground leading-snug">
                A short daily brief of the top stories, sent each morning. See it
                anytime on the Today tab.
              </p>
            </div>
            <button
              role="switch"
              aria-checked={digestEmail}
              onClick={toggleDigestEmail}
              className={cn(
                "relative h-6 w-11 shrink-0 rounded-full transition-colors",
                digestEmail ? "bg-foreground" : "bg-muted"
              )}
            >
              <span
                className={cn(
                  "absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-background shadow transition-transform",
                  digestEmail && "translate-x-5"
                )}
              />
            </button>
          </div>
        </section>

        {/* Muted Sources */}
        {sources && sources.length > 0 && (
          <section>
            <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
              Muted Sources
            </h2>
            <p className="text-xs text-muted-foreground mb-4">
              Articles from muted sources are hidden from the ranked feed.
            </p>
            <div className="space-y-1">
              {sources.map((source) => {
                const muted = mutedSources.includes(source.id);
                return (
                  <button
                    key={source.id}
                    onClick={() => toggleMutedSource(source.id)}
                    className={cn(
                      "w-full flex items-center justify-between px-4 py-2.5 rounded-lg border transition-colors text-left",
                      muted
                        ? "border-destructive/40 bg-destructive/5 text-destructive"
                        : "border-border hover:bg-muted"
                    )}
                  >
                    <span className="text-sm">{source.name}</span>
                    <span className="text-xs text-muted-foreground">
                      {muted ? "muted" : "active"}
                    </span>
                  </button>
                );
              })}
            </div>
          </section>
        )}

      </main>

    </div>
  );
}
