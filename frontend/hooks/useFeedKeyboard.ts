"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { isTypingTarget } from "@/lib/shortcuts";
import type { Article } from "@/lib/types";

export interface FeedKeyboardActions {
  onOpen: (article: Article) => void;
  onOpenSource: (article: Article) => void;
  onFeedback: (article: Article, value: 1 | -1) => void;
  onBookmark: (article: Article) => void;
  onShare: (article: Article) => void;
  onRefresh: () => void;
  onSearch: () => void;
  onHorizon: (h: "day" | "month" | "year") => void;
  /** True when any overlay (palette, sheet, search, drawer) owns the keyboard. */
  isBlocked: () => boolean;
}

/**
 * j/k focus model + single-key actions over the finite numbered feed.
 * Returns the focused index so the list can render a focus ring and scroll it
 * into view. All keystrokes are ignored while typing or while an overlay is open.
 */
export function useFeedKeyboard(items: Article[], actions: FeedKeyboardActions) {
  const [focused, setFocused] = useState(-1);
  // Mirror focused into a ref so the (stable) keydown handler reads the latest value.
  const focusedRef = useRef(focused);
  focusedRef.current = focused;
  // `g` is a leader key: `g d/m/y` switches horizon. Track the pending leader.
  const leaderRef = useRef(false);
  const leaderTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Keep the latest actions/items without re-binding the listener every render.
  const actionsRef = useRef(actions);
  actionsRef.current = actions;
  const itemsRef = useRef(items);
  itemsRef.current = items;

  // Reset focus if the list shrinks past the cursor (e.g. opened items drop out).
  useEffect(() => {
    setFocused((f) => (f >= items.length ? items.length - 1 : f));
  }, [items.length]);

  const clearLeader = useCallback(() => {
    leaderRef.current = false;
    if (leaderTimer.current) clearTimeout(leaderTimer.current);
  }, []);

  useEffect(() => {
    function handler(e: KeyboardEvent) {
      if (isTypingTarget(e.target)) return;
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      if (actionsRef.current.isBlocked()) return;

      const list = itemsRef.current;
      const a = actionsRef.current;

      // Leader sequence: g → d / m / y
      if (leaderRef.current) {
        clearLeader();
        if (e.key === "d") return e.preventDefault(), a.onHorizon("day");
        if (e.key === "m") return e.preventDefault(), a.onHorizon("month");
        if (e.key === "y") return e.preventDefault(), a.onHorizon("year");
        return;
      }

      const cur = () => (focusedRef.current >= 0 ? list[focusedRef.current] : undefined);

      switch (e.key) {
        case "g":
          e.preventDefault();
          leaderRef.current = true;
          leaderTimer.current = setTimeout(() => (leaderRef.current = false), 800);
          return;
        case "j":
          e.preventDefault();
          // From "nothing focused" (-1), j lands on the first item.
          setFocused((f) => (f < 0 ? 0 : Math.min(f + 1, list.length - 1)));
          return;
        case "k":
          e.preventDefault();
          setFocused((f) => Math.max(f - 1, 0));
          return;
        case "Enter":
        case "o": {
          const art = cur();
          if (art) { e.preventDefault(); a.onOpen(art); }
          return;
        }
        case "v": {
          const art = cur();
          if (art) { e.preventDefault(); a.onOpenSource(art); }
          return;
        }
        case "u": {
          const art = cur();
          if (art) { e.preventDefault(); a.onFeedback(art, 1); }
          return;
        }
        case "d": {
          const art = cur();
          if (art) { e.preventDefault(); a.onFeedback(art, -1); }
          return;
        }
        case "b": {
          const art = cur();
          if (art) { e.preventDefault(); a.onBookmark(art); }
          return;
        }
        case "s": {
          const art = cur();
          if (art) { e.preventDefault(); a.onShare(art); }
          return;
        }
        case "r":
          e.preventDefault();
          a.onRefresh();
          return;
        case "/":
          e.preventDefault();
          a.onSearch();
          return;
      }
    }
    document.addEventListener("keydown", handler);
    return () => {
      document.removeEventListener("keydown", handler);
      if (leaderTimer.current) clearTimeout(leaderTimer.current);
    };
  }, [clearLeader]);

  return { focused, setFocused };
}
