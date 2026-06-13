import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MobileNav } from "@/components/layout/MobileNav";
import { SummarySheet } from "@/components/feed/SummarySheet";
import { FeedCard } from "@/components/feed/FeedCard";
import type { Article } from "@/lib/types";

function withQuery(ui: React.ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

const article: Article = {
  id: "a1",
  title: "Qwen 3 released",
  url: "https://example.com/qwen3",
  source_id: "reddit-ml",
  author: "ml_fan",
  summary: "A snippet.",
  published_at: new Date().toISOString(),
  fetched_at: new Date().toISOString(),
  topic_tags: ["llm"],
  is_read: false,
  is_bookmarked: false,
  feedback: null,
  trending_score: 10,
  relevance: 87,
  why: ["412 upvotes on Reddit", "published today"],
  engagement: { upvotes: 412, comments: 38 },
};

describe("MobileNav", () => {
  it("renders exactly the 5 destinations", () => {
    render(<MobileNav />);
    for (const label of ["Feed", "Discover", "Topics", "Sources", "Settings"]) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
    expect(screen.getAllByRole("link")).toHaveLength(5);
  });
});

describe("FeedCard", () => {
  it("renders title, source actions, and a direct source link", () => {
    withQuery(<FeedCard article={article} onOpen={vi.fn()} />);
    expect(screen.getByText("Qwen 3 released")).toBeInTheDocument();
    expect(screen.getByLabelText("Thumbs up")).toBeInTheDocument();
    expect(screen.getByLabelText("Open original source")).toHaveAttribute(
      "href",
      "https://example.com/qwen3"
    );
  });

  it("shows the relevance match and why line", () => {
    withQuery(<FeedCard article={article} onOpen={vi.fn()} />);
    expect(screen.getByText("87% match")).toBeInTheDocument();
    expect(screen.getByText(/412 upvotes on Reddit/)).toBeInTheDocument();
  });
});

describe("SummarySheet", () => {
  it("renders nothing when closed", () => {
    const { container } = withQuery(<SummarySheet article={null} onClose={vi.fn()} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("shows the article title and read-at-source link when open", () => {
    withQuery(<SummarySheet article={article} onClose={vi.fn()} />);
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText("Read at source")).toHaveAttribute(
      "href",
      "https://example.com/qwen3"
    );
  });
});
