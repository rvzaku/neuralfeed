"use client";

import { useState } from "react";
import { Users, Plus, Trash2, RefreshCw, Twitter, Linkedin, Youtube, CheckCircle2, XCircle } from "lucide-react";
import { MobileNav } from "@/components/layout/MobileNav";
import { useAccounts, useAddAccount, usePatchAccount, useDeleteAccount, useRunAccountDiscovery } from "@/hooks/useFeed";
import { cn } from "@/lib/utils";
import type { WatchedAccount, AccountPlatform } from "@/lib/types";

const PLATFORM_ICON: Record<AccountPlatform, React.ReactNode> = {
  twitter:  <Twitter className="h-3.5 w-3.5" />,
  linkedin: <Linkedin className="h-3.5 w-3.5" />,
  youtube:  <Youtube className="h-3.5 w-3.5" />,
};

const PLATFORM_COLOR: Record<AccountPlatform, string> = {
  twitter:  "text-sky-500",
  linkedin: "text-blue-600",
  youtube:  "text-red-500",
};

const PLATFORM_LABELS: Record<AccountPlatform, string> = {
  twitter:  "X / Twitter",
  linkedin: "LinkedIn",
  youtube:  "YouTube",
};

function AccountRow({ account }: { account: WatchedAccount }) {
  const { mutate: patch, isPending: isPatching } = usePatchAccount();
  const { mutate: remove, isPending: isDeleting } = useDeleteAccount();

  return (
    <div className="flex items-center gap-3 py-3 px-4">
      <span className={cn("shrink-0", PLATFORM_COLOR[account.platform])}>
        {PLATFORM_ICON[account.platform]}
      </span>

      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">{account.display_name}</p>
        <p className="text-xs text-muted-foreground truncate">
          @{account.handle}
          {account.notes && <span className="ml-1 text-muted-foreground/70">· {account.notes}</span>}
        </p>
      </div>

      {/* Toggle */}
      <button
        onClick={() => patch({ id: account.id, body: { enabled: !account.enabled } })}
        disabled={isPatching}
        className={cn(
          "relative inline-flex h-5 w-9 shrink-0 rounded-full transition-colors duration-200",
          account.enabled ? "bg-primary" : "bg-muted",
          isPatching && "opacity-50"
        )}
        role="switch"
        aria-checked={account.enabled}
        aria-label={`Toggle ${account.display_name}`}
      >
        <span className={cn(
          "pointer-events-none block h-4 w-4 rounded-full bg-white shadow-sm ring-0 transition-transform duration-200 mt-0.5",
          account.enabled ? "translate-x-4" : "translate-x-0.5"
        )} />
      </button>

      {/* Delete */}
      <button
        onClick={() => remove(account.id)}
        disabled={isDeleting}
        className="p-1.5 rounded-md text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors disabled:opacity-50"
        aria-label={`Remove ${account.display_name}`}
      >
        <Trash2 className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}

function AddAccountForm({ onDone }: { onDone: () => void }) {
  const [platform, setPlatform] = useState<AccountPlatform>("twitter");
  const [handle, setHandle] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [notes, setNotes] = useState("");
  const { mutate: add, isPending } = useAddAccount();

  function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!handle.trim() || !displayName.trim()) return;
    add(
      { platform, handle: handle.trim().replace(/^@/, ""), display_name: displayName.trim(), notes: notes.trim() || undefined },
      { onSuccess: onDone }
    );
  }

  return (
    <form onSubmit={submit} className="px-4 py-4 border-t border-border space-y-3 bg-muted/20">
      <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Add account</p>

      <div className="flex gap-2">
        {(["twitter", "linkedin", "youtube"] as AccountPlatform[]).map((p) => (
          <button
            key={p}
            type="button"
            onClick={() => setPlatform(p)}
            className={cn(
              "flex-1 py-1.5 rounded-lg text-xs border transition-colors",
              platform === p ? "bg-primary text-primary-foreground border-primary" : "border-border text-muted-foreground hover:bg-muted"
            )}
          >
            {PLATFORM_LABELS[p]}
          </button>
        ))}
      </div>

      <input
        value={handle}
        onChange={(e) => setHandle(e.target.value)}
        placeholder="@handle or username"
        className="w-full px-3 py-2 text-sm rounded-lg border border-border bg-background outline-none focus:ring-2 focus:ring-primary/30"
        required
      />
      <input
        value={displayName}
        onChange={(e) => setDisplayName(e.target.value)}
        placeholder="Display name"
        className="w-full px-3 py-2 text-sm rounded-lg border border-border bg-background outline-none focus:ring-2 focus:ring-primary/30"
        required
      />
      <input
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        placeholder="Notes (optional)"
        className="w-full px-3 py-2 text-sm rounded-lg border border-border bg-background outline-none focus:ring-2 focus:ring-primary/30"
      />

      <div className="flex gap-2">
        <button
          type="submit"
          disabled={isPending}
          className="flex-1 py-2 bg-primary text-primary-foreground text-sm rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
        >
          {isPending ? "Adding…" : "Add account"}
        </button>
        <button
          type="button"
          onClick={onDone}
          className="px-4 py-2 text-sm border border-border rounded-lg hover:bg-muted transition-colors"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}

export default function AccountsPage() {
  const [showForm, setShowForm] = useState(false);
  const [platformFilter, setPlatformFilter] = useState<AccountPlatform | "">("");
  const { data: accounts, isLoading, isError } = useAccounts(platformFilter || undefined);
  const { mutate: runDiscovery, isPending: isDiscovering } = useRunAccountDiscovery();

  const grouped = accounts?.reduce<Record<string, WatchedAccount[]>>((acc, a) => {
    if (!acc[a.platform]) acc[a.platform] = [];
    acc[a.platform].push(a);
    return acc;
  }, {});

  const enabledCount = accounts?.filter((a) => a.enabled).length ?? 0;

  return (
    <div className="flex flex-col min-h-screen">
      <header className="sticky top-0 z-10 bg-background/80 backdrop-blur-sm border-b border-border px-4 py-3 flex items-center gap-2">
        <Users className="h-4 w-4 text-primary" />
        <h1 className="font-semibold text-sm">Watched Accounts</h1>
        <span className="ml-auto text-xs text-muted-foreground">
          {enabledCount}/{accounts?.length ?? 0} active
        </span>
      </header>

      {/* Toolbar */}
      <div className="px-4 py-3 border-b border-border flex items-center gap-2 flex-wrap">
        {/* Platform filter */}
        <div className="flex gap-1.5 flex-1">
          {([["", "All"], ["twitter", "X"], ["linkedin", "LinkedIn"], ["youtube", "YouTube"]] as [string, string][]).map(([val, label]) => (
            <button
              key={val}
              onClick={() => setPlatformFilter(val as AccountPlatform | "")}
              className={cn(
                "rounded-full px-3 py-1 text-xs border transition-colors",
                platformFilter === val
                  ? "bg-primary text-primary-foreground border-primary"
                  : "border-border text-muted-foreground hover:bg-muted"
              )}
            >
              {label}
            </button>
          ))}
        </div>

        <button
          onClick={() => runDiscovery()}
          disabled={isDiscovering}
          className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border border-border hover:bg-muted transition-colors disabled:opacity-50"
          title="Re-run discovery from curated_accounts.json"
        >
          <RefreshCw className={cn("h-3 w-3", isDiscovering && "animate-spin")} />
          Rediscover
        </button>

        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          <Plus className="h-3 w-3" />
          Add
        </button>
      </div>

      {showForm && <AddAccountForm onDone={() => setShowForm(false)} />}

      <main className="flex-1 pb-24 md:pb-6 max-w-2xl mx-auto w-full">
        {isLoading && (
          <div className="flex items-center justify-center py-20">
            <RefreshCw className="h-5 w-5 text-muted-foreground animate-spin" />
          </div>
        )}

        {isError && (
          <div className="flex flex-col items-center justify-center py-16 gap-2 text-center px-4">
            <XCircle className="h-8 w-8 text-destructive" />
            <p className="text-sm text-muted-foreground">Failed to load accounts.</p>
          </div>
        )}

        {!isLoading && accounts?.length === 0 && (
          <div className="flex flex-col items-center justify-center py-20 gap-3 text-center px-4">
            <Users className="h-10 w-10 text-muted-foreground" />
            <p className="text-sm font-medium">No accounts yet</p>
            <p className="text-xs text-muted-foreground max-w-xs">
              Click &ldquo;Rediscover&rdquo; to seed from the curated list, or add accounts manually.
            </p>
          </div>
        )}

        {grouped && Object.entries(grouped).map(([platform, items]) => (
          <section key={platform} className="mt-4">
            <div className="px-4 pb-1 flex items-center gap-2">
              <span className={cn("shrink-0", PLATFORM_COLOR[platform as AccountPlatform])}>
                {PLATFORM_ICON[platform as AccountPlatform]}
              </span>
              <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                {PLATFORM_LABELS[platform as AccountPlatform]}
                <span className="ml-1.5 font-normal normal-case">({items.filter(a => a.enabled).length}/{items.length})</span>
              </h2>
            </div>
            <div className="divide-y divide-border border-y border-border">
              {items.map((account) => (
                <AccountRow key={account.id} account={account} />
              ))}
            </div>
          </section>
        ))}

        {!isLoading && accounts && accounts.every((a) => a.enabled) && accounts.length > 0 && (
          <div className="flex items-center gap-2 px-4 py-4 text-xs text-muted-foreground">
            <CheckCircle2 className="h-4 w-4 text-green-500" />
            All accounts active
          </div>
        )}
      </main>

      <MobileNav />
    </div>
  );
}
