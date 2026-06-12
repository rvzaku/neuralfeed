"use client";

import { useEffect } from "react";
import { X, SlidersHorizontal } from "lucide-react";
import { cn } from "@/lib/utils";
import { FilterContent } from "./FilterContent";

interface FilterDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export function FilterDrawer({ isOpen, onClose }: FilterDrawerProps) {
  useEffect(() => {
    if (!isOpen) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [isOpen, onClose]);

  return (
    <>
      {/* Backdrop — mobile only */}
      <div
        className={cn(
          "fixed inset-0 z-30 bg-black/40 backdrop-blur-sm transition-opacity duration-200",
          isOpen ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
        )}
        onClick={onClose}
      />

      {/* Drawer panel — slides up from bottom on mobile, from left on tablet */}
      <div
        className={cn(
          "fixed bottom-0 left-0 right-0 z-40 bg-background rounded-t-2xl border-t border-border shadow-2xl",
          "transition-transform duration-300 ease-out",
          "max-h-[85vh] flex flex-col",
          "md:right-auto md:left-0 md:bottom-0 md:top-0 md:w-72 md:rounded-none md:rounded-r-xl md:border-r md:border-t-0 md:shadow-xl",
          isOpen ? "translate-y-0 md:translate-x-0" : "translate-y-full md:-translate-x-full"
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-border shrink-0">
          <div className="flex items-center gap-2">
            <SlidersHorizontal className="h-4 w-4 text-primary" />
            <span className="font-semibold text-sm">Advanced Filters</span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-md hover:bg-muted transition-colors"
            aria-label="Close filters"
          >
            <X className="h-4 w-4 text-muted-foreground" />
          </button>
        </div>

        {/* Scrollable body */}
        <div className="flex-1 overflow-y-auto px-5 py-4 pb-8">
          <FilterContent onClear={onClose} />
        </div>
      </div>
    </>
  );
}
