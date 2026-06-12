"use client";

import { useState, useEffect } from "react";
import { Settings, Save, RotateCcw } from "lucide-react";
import { ThemeToggle } from "@/components/layout/ThemeToggle";
import { LogOut } from "lucide-react";
import { useRouter } from "next/navigation";
import { clearSession, getEmail } from "@/lib/auth";
import { usePreferences, useSetPreference, useSources } from "@/hooks/useFeed";
import { cn } from "@/lib/utils";

const TOPICS = [
  { key: "llm",                  label: "LLMs & Language Models" },
  { key: "computer-vision",      label: "Computer Vision" },
  { key: "multimodal",           label: "Multimodal AI" },
  { key: "reinforcement-learning", label: "Reinforcement Learning" },
  { key: "ai-safety",            label: "AI Safety & Alignment" },
  { key: "robotics",             label: "Robotics" },
  { key: "ai-agents",            label: "AI Agents" },
  { key: "audio-speech",         label: "Audio & Speech" },
  { key: "open-source",          label: "Open Source" },
  { key: "ai-infrastructure",    label: "Infrastructure & MLOps" },
  { key: "products",             label: "Products & Launches" },
  { key: "funding",              label: "Funding & Business" },
];

function WeightSlider({
  topicKey,
  label,
  value,
  onChange,
}: {
  topicKey: string;
  label: string;
  value: number;
  onChange: (k: string, v: number) => void;
}) {
  return (
    <div className="flex items-center gap-3 py-2">
      <label className="text-sm w-44 shrink-0">{label}</label>
      <input
        type="range"
        min={0}
        max={1}
        step={0.1}
        value={value}
        onChange={(e) => onChange(topicKey, parseFloat(e.target.value))}
        className="flex-1 accent-primary"
      />
      <span className="text-xs text-muted-foreground w-8 text-right">
        {value.toFixed(1)}
      </span>
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

  const [topicWeights, setTopicWeights] = useState<Record<string, number>>({});
  const [mutedSources, setMutedSources] = useState<string[]>([]);
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    if (!prefs) return;
    try {
      setTopicWeights(prefs.topic_weights ? JSON.parse(prefs.topic_weights) : {});
    } catch {
      setTopicWeights({});
    }
    try {
      setMutedSources(prefs.muted_sources ? JSON.parse(prefs.muted_sources) : []);
    } catch {
      setMutedSources([]);
    }
  }, [prefs]);

  const handleWeightChange = (key: string, value: number) => {
    setTopicWeights((prev) => ({ ...prev, [key]: value }));
    setDirty(true);
  };

  const toggleMutedSource = (id: string) => {
    setMutedSources((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]
    );
    setDirty(true);
  };

  const handleSave = () => {
    setPref({ key: "topic_weights", value: topicWeights });
    setPref({ key: "muted_sources", value: mutedSources });
    setDirty(false);
  };

  const handleReset = () => {
    setTopicWeights({});
    setMutedSources([]);
    setDirty(true);
  };

  return (
    <div className="flex flex-col min-h-screen">
      <header className="sticky top-0 md:static z-10 bg-background/80 backdrop-blur-md border-b border-border px-4 py-3 flex items-center gap-2.5">
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

        {/* Topic Weights */}
        <section>
          <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
            Topic Weights
          </h2>
          <p className="text-xs text-muted-foreground mb-4">
            Boost topics you care about. Higher weight = ranked higher in feed.
          </p>
          {isLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="h-7 bg-muted rounded animate-pulse" />
              ))}
            </div>
          ) : (
            <div className="space-y-1">
              {TOPICS.map(({ key, label }) => (
                <WeightSlider
                  key={key}
                  topicKey={key}
                  label={label}
                  value={topicWeights[key] ?? 0}
                  onChange={handleWeightChange}
                />
              ))}
            </div>
          )}
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

        {/* Ranked feed toggle info */}
        <section>
          <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
            Feed Behavior
          </h2>
          <div className="rounded-xl border border-border bg-card p-4 space-y-2">
            <p className="text-sm font-medium">Smart Ranking</p>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Enable smart ranking on the feed to sort articles by a score that combines
              recency, source signal, topic preferences, trending score, and your feedback history.
              Toggle via <code className="px-1 py-0.5 bg-muted rounded text-xs">?ranked=true</code> in the feed URL.
            </p>
          </div>
        </section>
      </main>

    </div>
  );
}
