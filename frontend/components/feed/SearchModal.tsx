"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { Search, X, Loader2, FileText } from "lucide-react";
import { useSearch } from "@/hooks/useFeed";
import { SourceBadge } from "@/components/ui/SourceBadge";
import { formatRelativeTime } from "@/lib/utils";

interface SearchModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SearchModal({ isOpen, onClose }: SearchModalProps) {
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(query), 300);
    return () => clearTimeout(timer);
  }, [query]);

  useEffect(() => {
    if (isOpen) {
      setQuery("");
      setDebouncedQuery("");
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  // ⌘K / Ctrl+K to open/close
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        if (isOpen) onClose();
      }
      if (e.key === "Escape" && isOpen) onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [isOpen, onClose]);

  const { data: results, isLoading } = useSearch(debouncedQuery);

  const handleBackdropClick = useCallback(
    (e: React.MouseEvent) => {
      if (e.target === e.currentTarget) onClose();
    },
    [onClose]
  );

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-start justify-center pt-[10vh] px-4"
      onClick={handleBackdropClick}
    >
      <div className="w-full max-w-xl bg-background border border-border rounded-2xl shadow-2xl overflow-hidden">
        {/* Input row */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-border">
          <Search className="h-4 w-4 text-muted-foreground shrink-0" />
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search articles, papers, repos…"
            className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
          />
          {isLoading && <Loader2 className="h-4 w-4 text-muted-foreground animate-spin shrink-0" />}
          <button
            onClick={onClose}
            className="p-1 rounded-md hover:bg-muted transition-colors"
            aria-label="Close search"
          >
            <X className="h-4 w-4 text-muted-foreground" />
          </button>
        </div>

        {/* Results */}
        <div className="max-h-[60vh] overflow-y-auto">
          {!debouncedQuery && (
            <div className="px-4 py-8 text-center text-sm text-muted-foreground">
              Type at least 2 characters to search
            </div>
          )}

          {debouncedQuery && !isLoading && results?.length === 0 && (
            <div className="px-4 py-8 text-center text-sm text-muted-foreground">
              No results for &ldquo;{debouncedQuery}&rdquo;
            </div>
          )}

          {results && results.length > 0 && (
            <ul className="py-2">
              {results.map((article) => (
                <li key={article.id}>
                  <a
                    href={article.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={onClose}
                    className="flex items-start gap-3 px-4 py-3 hover:bg-muted transition-colors"
                  >
                    <FileText className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium line-clamp-1">{article.title}</p>
                      {article.summary && (
                        <p className="text-xs text-muted-foreground line-clamp-1 mt-0.5">
                          {article.summary}
                        </p>
                      )}
                      <div className="flex items-center gap-2 mt-1">
                        <SourceBadge sourceId={article.source_id} />
                        <span className="text-xs text-muted-foreground">
                          {formatRelativeTime(article.published_at)}
                        </span>
                      </div>
                    </div>
                  </a>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Footer hint */}
        <div className="px-4 py-2 border-t border-border flex gap-4 text-[10px] text-muted-foreground">
          <span><kbd className="px-1 py-0.5 rounded bg-muted font-mono">↵</kbd> open</span>
          <span><kbd className="px-1 py-0.5 rounded bg-muted font-mono">Esc</kbd> close</span>
          <span><kbd className="px-1 py-0.5 rounded bg-muted font-mono">⌘K</kbd> toggle</span>
        </div>
      </div>
    </div>
  );
}
