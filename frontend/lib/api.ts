import axios from "axios";
import type { Article, FeedFilters, FeedResponse, Source, FeedbackValue, TopicsResponse } from "./types";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
  // Render free tier cold-starts can take 60-90s; 10s made every first visit fail
  timeout: 90000,
});

// Attach the auth token when present (no-op while logged out / AUTH_REQUIRED=false)
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("neuralfeed_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// When the backend enforces auth (AUTH_REQUIRED=true), bounce to login
// instead of surfacing opaque load errors
api.interceptors.response.use(
  (resp) => resp,
  (error) => {
    if (
      error?.response?.status === 401 &&
      typeof window !== "undefined" &&
      !window.location.pathname.startsWith("/login")
    ) {
      localStorage.removeItem("neuralfeed_token");
      localStorage.removeItem("neuralfeed_email");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export interface AuthResponse {
  access_token: string;
  token_type: string;
  email: string;
}

export async function authRegister(email: string, password: string): Promise<AuthResponse> {
  const { data } = await api.post<AuthResponse>("/api/v1/auth/register", { email, password });
  return data;
}

export async function authLogin(email: string, password: string): Promise<AuthResponse> {
  const { data } = await api.post<AuthResponse>("/api/v1/auth/login", { email, password });
  return data;
}

export async function authGuest(): Promise<AuthResponse> {
  const { data } = await api.post<AuthResponse>("/api/v1/auth/guest");
  return data;
}

// Feed
export async function getFeed(filters: FeedFilters = {}): Promise<FeedResponse> {
  const params = Object.fromEntries(
    Object.entries(filters).filter(([, v]) => v !== undefined && v !== null)
  );
  const { data } = await api.get<FeedResponse>("/api/v1/feed", { params });
  return data;
}

export async function getTopics(
  timeRange: "1d" | "3d" | "7d" | "30d" = "7d"
): Promise<TopicsResponse> {
  const { data } = await api.get<TopicsResponse>("/api/v1/topics", {
    params: { time_range: timeRange },
  });
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

export async function createSource(body: {
  kind: "rss" | "reddit" | "github";
  value: string;
  name?: string;
}): Promise<Source> {
  const { data } = await api.post<Source>("/api/v1/sources", body);
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

import type { ArticleSummary, SourceHealth, WatchedAccount } from "./types";

// AI "5-minute read" summary (generation can take a minute on first open)
export async function getSummary(articleId: string): Promise<ArticleSummary> {
  const { data } = await api.get<ArticleSummary>(`/api/v1/articles/${articleId}/summary`, {
    timeout: 120000,
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
