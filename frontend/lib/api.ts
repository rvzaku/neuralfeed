import axios from "axios";
import type { Article, FeedFilters, FeedResponse, Source, FeedbackValue } from "./types";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
  timeout: 10000,
});

// Feed
export async function getFeed(filters: FeedFilters = {}): Promise<FeedResponse> {
  const params = Object.fromEntries(
    Object.entries(filters).filter(([, v]) => v !== undefined && v !== null)
  );
  const { data } = await api.get<FeedResponse>("/api/v1/feed", { params });
  return data;
}

export async function getArticle(id: string): Promise<Article> {
  const { data } = await api.get<Article>(`/api/v1/feed/${id}`);
  return data;
}

// Search
export async function searchArticles(q: string, limit = 20): Promise<Article[]> {
  const { data } = await api.get<Article[]>("/api/v1/search", { params: { q, limit } });
  return data;
}

// Sources
export async function getSources(all = false): Promise<Source[]> {
  const { data } = await api.get<Source[]>("/api/v1/sources", { params: all ? { all: true } : {} });
  return data;
}

export async function patchSource(sourceId: string, body: { enabled?: boolean; priority?: string }): Promise<Source> {
  const { data } = await api.patch<Source>(`/api/v1/sources/${sourceId}`, body);
  return data;
}

export async function triggerSourceFetch(sourceId: string): Promise<void> {
  await api.post(`/api/v1/sources/${sourceId}/fetch`);
}

// Feedback
export async function postFeedback(articleId: string, value: FeedbackValue): Promise<void> {
  await api.post("/api/v1/feedback", { article_id: articleId, value });
}

// Bookmarks
export async function toggleBookmark(articleId: string): Promise<Article> {
  const { data } = await api.post<Article>(`/api/v1/articles/${articleId}/bookmark`);
  return data;
}

// Preferences
export async function getPreferences(): Promise<Record<string, string>> {
  const { data } = await api.get<Record<string, string>>("/api/v1/preferences");
  return data;
}

export async function setPreference(key: string, value: unknown): Promise<void> {
  await api.put(`/api/v1/preferences/${key}`, { value: JSON.stringify(value) });
}

// Refresh all
export async function triggerRefresh(): Promise<void> {
  await api.post("/api/v1/refresh");
}

// Stories (event clusters)
import type { ArticleSummary, SourceHealth, StoryDetail, StoryDigest, WatchedAccount } from "./types";

export async function getStories(params: {
  days?: number;
  limit?: number;
  unread_only?: boolean;
  topic?: string;
} = {}): Promise<StoryDigest> {
  const { data } = await api.get<StoryDigest>("/api/v1/stories", { params });
  return data;
}

export async function getStoryDetail(storyId: string, days = 7): Promise<StoryDetail> {
  const { data } = await api.get<StoryDetail>(`/api/v1/stories/${storyId}`, { params: { days } });
  return data;
}

// AI summary (generation can take a few seconds on first open)
export async function getSummary(articleId: string): Promise<ArticleSummary> {
  const { data } = await api.get<ArticleSummary>(`/api/v1/articles/${articleId}/summary`, {
    timeout: 90000,
  });
  return data;
}

// Source health
export async function getSourcesHealth(): Promise<SourceHealth[]> {
  const { data } = await api.get<SourceHealth[]>("/api/v1/sources/health");
  return data;
}

// Watched accounts

export async function getAccounts(platform?: string): Promise<WatchedAccount[]> {
  const { data } = await api.get<WatchedAccount[]>("/api/v1/accounts", {
    params: platform ? { platform } : {},
  });
  return data;
}

export async function addAccount(body: {
  platform: string;
  handle: string;
  display_name: string;
  notes?: string;
}): Promise<WatchedAccount> {
  const { data } = await api.post<WatchedAccount>("/api/v1/accounts", body);
  return data;
}

export async function patchAccount(
  id: string,
  body: { enabled?: boolean; display_name?: string; notes?: string }
): Promise<WatchedAccount> {
  const { data } = await api.patch<WatchedAccount>(`/api/v1/accounts/${encodeURIComponent(id)}`, body);
  return data;
}

export async function deleteAccount(id: string): Promise<void> {
  await api.delete(`/api/v1/accounts/${encodeURIComponent(id)}`);
}

export async function runAccountDiscovery(): Promise<{ upserted: number }> {
  const { data } = await api.post<{ ok: boolean; upserted: number }>("/api/v1/accounts/discover");
  return data;
}
