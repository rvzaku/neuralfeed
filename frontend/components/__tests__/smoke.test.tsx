import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MobileNav } from "@/components/layout/MobileNav";
import { SummarySheet } from "@/components/feed/SummarySheet";
import { FeedCard } from "@/components/feed/FeedCard";
import { ShortcutCheatSheet } from "@/components/feed/ShortcutCheatSheet";
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
  it("renders exactly the 5 destinations (Today folded into Feed)", () => {
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

  it("shows the relevance score and engagement traction", () => {
    withQuery(<FeedCard article={article} onOpen={vi.fn()} />);
    expect(
      screen.getByLabelText(/Relevance 87 out of 100/)
    ).toBeInTheDocument();
    expect(screen.getByText("412")).toBeInTheDocument();
  });
});

describe("ShortcutCheatSheet", () => {
  it("renders nothing when closed", () => {
    const { container } = render(<ShortcutCheatSheet isOpen={false} onClose={vi.fn()} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("lists keyboard shortcuts when open", () => {
    render(<ShortcutCheatSheet isOpen onClose={vi.fn()} />);
    expect(screen.getByRole("dialog", { name: /keyboard shortcuts/i })).toBeInTheDocument();
    expect(screen.getByText("Next item")).toBeInTheDocument();
    expect(screen.getByText("Command palette")).toBeInTheDocument();
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
