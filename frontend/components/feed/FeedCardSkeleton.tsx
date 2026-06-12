export function FeedCardSkeleton() {
  return (
    <div className="rounded-2xl border border-border bg-card p-4 animate-pulse space-y-3">
      <div className="flex items-center gap-2">
        <div className="h-5 w-16 rounded-full bg-muted" />
        <div className="h-4 w-20 rounded bg-muted" />
      </div>
      <div className="space-y-2">
        <div className="h-5 w-full rounded bg-muted" />
        <div className="h-5 w-3/4 rounded bg-muted" />
      </div>
      <div className="h-4 w-full rounded bg-muted" />
      <div className="h-4 w-2/3 rounded bg-muted" />
      <div className="flex gap-2 pt-1">
        <div className="h-5 w-12 rounded-full bg-muted" />
        <div className="h-5 w-16 rounded-full bg-muted" />
      </div>
    </div>
  );
}
