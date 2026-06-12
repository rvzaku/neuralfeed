"use client";

import { useInfiniteQuery, useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getFeed,
  getSources,
  patchSource,
  searchArticles,
  postFeedback,
  triggerRefresh,
  toggleBookmark,
  getPreferences,
  setPreference,
  getStories,
  getStoryDetail,
  getSummary,
  getDeepSummary,
  getSourcesHealth,
  getAccounts,
  addAccount,
  patchAccount,
  deleteAccount,
  runAccountDiscovery,
} from "@/lib/api";
import type { FeedFilters, FeedbackValue } from "@/lib/types";

export function useFeed(filters: FeedFilters = {}) {
  return useQuery({
    queryKey: ["feed", filters],
    queryFn: () => getFeed(filters),
    staleTime: 1000 * 60 * 5,
  });
}

export function useInfiniteFeed(filters: FeedFilters = {}) {
  return useInfiniteQuery({
    queryKey: ["feed-infinite", filters],
    queryFn: ({ pageParam }) => getFeed({ ...filters, page: pageParam }),
    initialPageParam: 1,
    getNextPageParam: (last) => (last.has_more ? last.page + 1 : undefined),
    staleTime: 1000 * 60 * 5,
  });
}

export function useStories(params: { days?: number; limit?: number; unread_only?: boolean; topic?: string } = {}) {
  return useQuery({
    queryKey: ["stories", params],
    queryFn: () => getStories(params),
    staleTime: 1000 * 60 * 5,
    // Render free tier cold-starts can exceed one request timeout — keep
    // retrying with backoff and show stale data instead of an error flash
    retry: 3,
    retryDelay: (attempt) => Math.min(2000 * 2 ** attempt, 15000),
    placeholderData: (prev) => prev,
  });
}

export function useDeepSummary(articleId: string | null) {
  return useQuery({
    queryKey: ["deep-summary", articleId],
    queryFn: () => getDeepSummary(articleId as string),
    enabled: !!articleId,
    staleTime: Infinity,
    retry: 1,
  });
}

export function useStoryDetail(storyId: string | null, days = 7) {
  return useQuery({
    queryKey: ["story", storyId, days],
    queryFn: () => getStoryDetail(storyId as string, days),
    enabled: !!storyId,
    staleTime: 1000 * 60 * 5,
  });
}

export function useSummary(articleId: string | null) {
  return useQuery({
    queryKey: ["summary", articleId],
    queryFn: () => getSummary(articleId as string),
    enabled: !!articleId,
    staleTime: Infinity, // cached server-side; never goes stale
    retry: 1,
  });
}

export function useSourcesHealth() {
  return useQuery({
    queryKey: ["sources-health"],
    queryFn: getSourcesHealth,
    staleTime: 1000 * 60,
  });
}

export function useSources(all = false) {
  return useQuery({
    queryKey: ["sources", all],
    queryFn: () => getSources(all),
    staleTime: 1000 * 60 * 10,
  });
}

export function usePatchSource() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: { enabled?: boolean; priority?: string } }) =>
      patchSource(id, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sources"] });
    },
  });
}

export function useSearch(q: string, enabled = true) {
  return useQuery({
    queryKey: ["search", q],
    queryFn: () => searchArticles(q),
    enabled: enabled && q.trim().length >= 2,
    staleTime: 1000 * 30,
  });
}

export function usePreferences() {
  return useQuery({
    queryKey: ["preferences"],
    queryFn: getPreferences,
    staleTime: 1000 * 60 * 5,
  });
}

export function useSetPreference() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ key, value }: { key: string; value: unknown }) => setPreference(key, value),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["preferences"] }),
  });
}

export function usePostFeedback() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ articleId, value }: { articleId: string; value: FeedbackValue }) =>
      postFeedback(articleId, value),
    onMutate: async ({ articleId, value }) => {
      await queryClient.cancelQueries({ queryKey: ["feed"] });
      const previous = queryClient.getQueriesData({ queryKey: ["feed"] });
      queryClient.setQueriesData({ queryKey: ["feed"] }, (old: unknown) => {
        if (!old || typeof old !== "object") return old;
        const data = old as { items: Array<{ id: string; feedback: unknown }> };
        return {
          ...data,
          items: data.items.map((item) =>
            item.id === articleId ? { ...item, feedback: value } : item
          ),
        };
      });
      return { previous };
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) {
        context.previous.forEach(([queryKey, data]) => {
          queryClient.setQueryData(queryKey, data);
        });
      }
    },
  });
}

export function useToggleBookmark() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (articleId: string) => toggleBookmark(articleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["feed"] });
    },
  });
}

export function useAccounts(platform?: string) {
  return useQuery({
    queryKey: ["accounts", platform],
    queryFn: () => getAccounts(platform),
    staleTime: 1000 * 60 * 10,
  });
}

export function useAddAccount() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { platform: string; handle: string; display_name: string; notes?: string }) =>
      addAccount(body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["accounts"] }),
  });
}

export function usePatchAccount() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: { enabled?: boolean; notes?: string } }) =>
      patchAccount(id, body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["accounts"] }),
  });
}

export function useDeleteAccount() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteAccount(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["accounts"] }),
  });
}

export function useRunAccountDiscovery() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: runAccountDiscovery,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["accounts"] }),
  });
}

export function useTriggerRefresh() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: triggerRefresh,
    onSuccess: () => {
      setTimeout(() => queryClient.invalidateQueries({ queryKey: ["feed"] }), 3000);
    },
  });
}
