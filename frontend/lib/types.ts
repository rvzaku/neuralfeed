export type TopicTag =
  | "llm"
  | "computer-vision"
  | "multimodal"
  | "reinforcement-learning"
  | "ai-safety"
  | "robotics"
  | "ai-agents"
  | "audio-speech"
  | "open-source"
  | "ai-infrastructure"
  | "products"
  | "funding"
  | "research-paper"
  | "github"
  | "general";

export type SourceCategory =
  | "research"
  | "social"
  | "company"
  | "newsletter"
  | "github"
  | "video"
  | "podcast"
  | "funding";

export type SourcePriority = "high" | "medium" | "low";
export type FeedbackValue = 1 | -1 | 0;

export interface Article {
  id: string;
  title: string;
  url: string;
  source_id: string;
  author: string | null;
  summary: string | null;
  image_url?: string | null;
  published_at: string;
  fetched_at: string;
  topic_tags: TopicTag[];
  is_read: boolean;
  is_bookmarked: boolean;
  feedback: FeedbackValue | null;
  trending_score: number;
  /** Platform stats — keys present only when the source provides them */
  engagement?: {
    stars_total?: number;
    stars_today?: number;
    forks?: number;
    upvotes?: number;
    points?: number;
    comments?: number;
    downloads?: number;
    likes?: number;
  } | null;
  /** Cached one-line LLM "why this matters" context */
  context_line?: string | null;
  /** Slug/raw title as fetched, kept when the title was rewritten */
  original_title?: string | null;
  /** V8 visible relevance: 0-100 match (ranked views only) */
  relevance?: number | null;
  /** Human-readable reasons this item surfaced (traction, topic fit) */
  why?: string[] | null;
}

export interface Source {
  id: string;
  name: string;
  category: SourceCategory;
  url: string;
  access: "rss" | "api" | "scrape" | "manual";
  enabled: boolean;
  priority: SourcePriority;
  refresh_interval: string;
  added_on: string;
  last_fetched_at: string | null;
  signal_score: number;
  notes: string | null;
}

export interface FeedResponse {
  items: Article[];
  total: number;
  page: number;
  limit: number;
  has_more: boolean;
}

export interface FeedFilters {
  page?: number;
  limit?: number;
  source_id?: string;
  category?: SourceCategory;
  topic?: TopicTag;
  is_read?: boolean;
  is_bookmarked?: boolean;
  feedback?: FeedbackValue;
  time_range?: "1d" | "3d" | "7d" | "30d";
  ranked?: boolean;
  min_signal?: number;
}

export interface ArticleSummary {
  article_id: string;
  url: string;
  markdown: string;
  reading_minutes: number;
  cached: boolean;
}

export interface SourceHealth {
  id: string;
  name: string;
  enabled: boolean;
  last_fetched_at: string | null;
  last_fetch_status: "ok" | "error" | null;
  last_fetch_error: string | null;
  last_fetch_count: number | null;
}

export interface UserPreference {
  key: string;
  value: string;
}

export type AccountPlatform = "twitter" | "linkedin" | "youtube";

export interface WatchedAccount {
  id: string;
  platform: AccountPlatform;
  handle: string;
  display_name: string;
  source_of_discovery: string | null;
  enabled: boolean;
  added_on: string;
  notes: string | null;
}
