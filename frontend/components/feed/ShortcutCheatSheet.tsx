"use client";

import { useEffect } from "react";
import { X } from "lucide-react";
import { SHORTCUTS, SHORTCUT_GROUPS } from "@/lib/shortcuts";

interface ShortcutCheatSheetProps {
  isOpen: boolean;
  onClose: () => void;
}

/** The discoverability layer for keyboard navigation — opened with `?`. */
export function ShortcutCheatSheet({ isOpen, onClose }: ShortcutCheatSheetProps) {
  useEffect(() => {
    if (!isOpen) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Keyboard shortcuts"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4 backdrop-blur-sm fade-in"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="w-full max-w-lg overflow-hidden rounded-xl border border-border bg-background shadow-2xl">
        <div className="flex items-center justify-between border-b border-border px-5 py-3.5">
          <h2 className="font-display text-base font-medium text-foreground">Keyboard shortcuts</h2>
          <button
            onClick={onClose}
            aria-label="Close"
            className="rounded-md p-1 text-muted-foreground transition-colors hover:bg-muted"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="grid grid-cols-1 gap-x-8 gap-y-1 px-5 py-4 sm:grid-cols-2">
          {SHORTCUT_GROUPS.map((group) => {
            const items = SHORTCUTS.filter((s) => s.group === group);
            if (items.length === 0) return null;
            return (
              <div key={group} className="py-1">
                <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/70">
                  {group}
                </p>
                <ul className="space-y-1.5">
                  {items.map((s) => (
                    <li key={s.keys.join("+") + s.description} className="flex items-center justify-between gap-3">
                      <span className="text-[13px] text-foreground/85">{s.description}</span>
                      <span className="flex shrink-0 items-center gap-1">
                        {s.keys.map((k) => (
                          <kbd
                            key={k}
                            className="rounded border border-border bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground"
                          >
                            {k}
                          </kbd>
                        ))}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
