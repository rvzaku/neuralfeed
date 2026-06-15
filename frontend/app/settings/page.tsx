"use client";

import { useState, useEffect } from "react";
import { Settings, Save, RotateCcw } from "lucide-react";
import { ThemeToggle } from "@/components/layout/ThemeToggle";
import { LogOut } from "lucide-react";
import { useRouter } from "next/navigation";
import { clearSession, getEmail } from "@/lib/auth";
import { usePreferences, useSetPreference, useSources } from "@/hooks/useFeed";
import { cn } from "@/lib/utils";

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

  useEffect(() => {
    if (!prefs) return;
    const density = Number(prefs.feed_density);
    setFeedDensity(Number.isFinite(density) && density > 0 ? density : 10);
    try {
      setMutedSources(prefs.muted_sources ? JSON.parse(prefs.muted_sources) : []);
    } catch {
      setMutedSources([]);
    }
  }, [prefs]);

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
        <h1 className="font-serif font-bold text-base">Settings</h1>
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
            How many top items each source category may contribute per day.
            Lower = only the biggest stories; higher = broader coverage.
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
                {n}<span className="font-normal text-xs">/day</span>
              </button>
            ))}
          </div>
        </section>

        {/* Learned personalization — V8: no manual sliders */}
        <section>
          <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
            Personalization
          </h2>
          <div className="rounded-xl border border-border bg-card p-4">
            <p className="text-sm font-medium mb-1">Learned from your reactions</p>
            <p className="text-xs text-muted-foreground leading-relaxed">
              NeuralFeed tunes itself from your thumbs up/down and saves — liked topics and
              sources rise, disliked ones sink. No sliders to maintain; just react to articles
              and the For You feed adapts.
            </p>
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
