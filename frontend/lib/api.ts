const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export interface IngestResponse {
  job_id: string;
  content_id: string;
  status: string;
}

export interface JobStatus {
  job_id: string;
  content_id: string;
  status: "pending" | "processing" | "complete" | "failed";
  progress: number;
  error?: string;
}

export interface ContentSummary {
  one_liner: string;
  detailed_summary: string;
  key_topics: string[];
  tags: string[];
  sentiment: string;
  content_type: string;
  language: string;
  quality_score: number;
}

export interface MediaMetadata {
  title: string;
  author: string;
  channel: string;
  duration_seconds: number;
  view_count: number;
  like_count: number;
  thumbnail_url: string;
}

export interface ContentItem {
  content_id: string;
  url: string;
  source: "youtube" | "instagram";
  score?: number;
  metadata: MediaMetadata;
  summary: ContentSummary;
}

export interface SearchResponse {
  answer: string;
  sources: ContentItem[];
}

async function fetchJSON<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  ingest: (url: string) =>
    fetchJSON<IngestResponse>("/ingest", {
      method: "POST",
      body: JSON.stringify({ url }),
    }),

  getJobStatus: (jobId: string) =>
    fetchJSON<JobStatus>(`/ingest/${jobId}/status`),

  listContent: (params?: { source?: string; limit?: number; skip?: number }) => {
    const qs = new URLSearchParams();
    if (params?.source) qs.set("source", params.source);
    if (params?.limit) qs.set("limit", String(params.limit));
    if (params?.skip) qs.set("skip", String(params.skip));
    return fetchJSON<ContentItem[]>(`/content?${qs}`);
  },

  getContent: (contentId: string) =>
    fetchJSON<ContentItem & { raw?: object }>(`/content/${contentId}`),

  search: (query: string, userId?: string) =>
    fetchJSON<SearchResponse>("/search", {
      method: "POST",
      body: JSON.stringify({ query, user_id: userId }),
    }),

  getRecommendations: (userId: string, limit = 10) =>
    fetchJSON<{ items: ContentItem[] }>(
      `/recommendations?user_id=${encodeURIComponent(userId)}&limit=${limit}`
    ),

  updateInterests: (userId: string, interests: string[]) =>
    fetchJSON<{ user_id: string; interests: string[] }>(
      `/users/${userId}/interests`,
      {
        method: "POST",
        body: JSON.stringify({ interests }),
      }
    ),
};
