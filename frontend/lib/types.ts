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
    /** Permalink to the Hacker News discussion (editorial traction lookup) */
    hn_url?: string;
  } | null;
  /** When `engagement` was last refreshed — velocity chips ("+N today") are
   *  only shown while this is fresh, so a stale number never reads as "today" */
  engagement_at?: string | null;
  /** Cached one-line LLM "why this matters" context */
  context_line?: string | null;
  /** Slug/raw title as fetched, kept when the title was rewritten */
  original_title?: string | null;
  /** V8 visible relevance: 0-100 match (ranked views only) */
  relevance?: number | null;
  /** Human-readable reasons this item surfaced (traction, topic fit) */
  why?: string[] | null;
  /** V6 Hotness Index — raw 0..1 cross-source-velocity score (ranked views) */
  hotness?: number | null;
  /** V6 Hotness Index colour band: 0 none · 1 warm · 2 hot · 3 blazing */
  heat?: number | null;
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
  /** single id or comma-joined ids (multi-select) */
  source_id?: string;
  /** single category or comma-joined categories (multi-select) */
  category?: SourceCategory | string;
  /** single topic or comma-joined topics (multi-select) */
  topic?: TopicTag | string;
  is_read?: boolean;
  is_bookmarked?: boolean;
  feedback?: FeedbackValue;
  time_range?: "1d" | "3d" | "7d" | "30d";
  ranked?: boolean;
  /** V6: include already-viewed items (the "All items" archive view) */
  include_read?: boolean;
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

export interface DigestItem {
  id: string;
  title: string;
  url: string;
  source_id: string;
  source_name: string;
  published_at: string | null;
  topic_tags: TopicTag[];
  blurb: string | null;
}

export interface Digest {
  generated_at: string;
  window_hours: number;
  count: number;
  items: DigestItem[];
}

export interface TopicInfo {
  tag: TopicTag;
  /** Articles tagged with this topic within the requested window */
  count: number;
  /** Learned affinity from likes/saves/dislikes (−1..1); 0 when neutral */
  weight: number;
  /** V6 Hotness Index colour band: 0 none · 1 warm · 2 hot · 3 blazing */
  heat?: number;
}

export interface TopicsResponse {
  items: TopicInfo[];
  time_range: "1d" | "3d" | "7d" | "30d";
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
