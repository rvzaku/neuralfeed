// Single source of truth for keyboard shortcuts — consumed by the feed keyboard
// hook, the `?` cheat sheet, and the command palette so the three never drift.

export interface Shortcut {
  /** Display keys, e.g. ["j"] or ["g", "d"] */
  keys: string[];
  description: string;
  group: "Navigation" | "Actions" | "Views" | "General";
}

export const SHORTCUTS: Shortcut[] = [
  { keys: ["j"], description: "Next item", group: "Navigation" },
  { keys: ["k"], description: "Previous item", group: "Navigation" },
  { keys: ["Enter"], description: "Open summary", group: "Navigation" },
  { keys: ["o"], description: "Open summary", group: "Navigation" },
  { keys: ["v"], description: "Open original source in new tab", group: "Navigation" },

  { keys: ["u"], description: "Thumbs up", group: "Actions" },
  { keys: ["d"], description: "Thumbs down", group: "Actions" },
  { keys: ["b"], description: "Bookmark", group: "Actions" },
  { keys: ["s"], description: "Share / copy link", group: "Actions" },
  { keys: ["r"], description: "Refresh feed", group: "Actions" },

  { keys: ["g", "d"], description: "Horizon: Day", group: "Views" },
  { keys: ["g", "m"], description: "Horizon: Month", group: "Views" },
  { keys: ["g", "y"], description: "Horizon: Year", group: "Views" },

  { keys: ["/"], description: "Search", group: "General" },
  { keys: ["⌘", "K"], description: "Command palette", group: "General" },
  { keys: ["?"], description: "Show this cheat sheet", group: "General" },
  { keys: ["Esc"], description: "Close overlay", group: "General" },
];

export const SHORTCUT_GROUPS = ["Navigation", "Actions", "Views", "General"] as const;

/** True when a keystroke should be ignored because the user is typing or a
 *  dialog owns the keyboard. */
export function isTypingTarget(el: EventTarget | null): boolean {
  if (!(el instanceof HTMLElement)) return false;
  const tag = el.tagName;
  return (
    tag === "INPUT" ||
    tag === "TEXTAREA" ||
    tag === "SELECT" ||
    el.isContentEditable
  );
}
