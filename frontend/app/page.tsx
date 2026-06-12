import { Suspense } from "react";
import { FeedView } from "@/components/feed/FeedView";
import { FeedCardSkeleton } from "@/components/feed/FeedCardSkeleton";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-background">
      <Suspense fallback={
        <div className="px-4 pt-4 space-y-3 max-w-2xl mx-auto">
          {Array.from({ length: 6 }).map((_, i) => <FeedCardSkeleton key={i} />)}
        </div>
      }>
        <FeedView />
      </Suspense>
    </div>
  );
}
