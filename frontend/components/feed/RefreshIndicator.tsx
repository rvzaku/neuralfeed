"use client";

import { RefreshCw } from "lucide-react";
import { useTriggerRefresh } from "@/hooks/useFeed";
import { cn } from "@/lib/utils";

export function RefreshIndicator() {
  const { mutate: refresh, isPending } = useTriggerRefresh();

  return (
    <button
      onClick={() => refresh()}
      disabled={isPending}
      className={cn(
        "flex items-center gap-1.5 text-xs text-muted-foreground",
        "hover:text-foreground transition-colors min-h-[44px] px-2",
        isPending && "opacity-50 cursor-not-allowed"
      )}
    >
      <RefreshCw className={cn("h-3.5 w-3.5", isPending && "animate-spin")} />
      <span>{isPending ? "Refreshing…" : "Refresh"}</span>
    </button>
  );
}
