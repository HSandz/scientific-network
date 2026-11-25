import {
  AskDemoItem,
  AskResult,
  CommunitiesResponse,
  CommunityNodeItem,
  GroupDetailResponse,
  GroupsResponse,
  SubjectDetailResponse,
  SubjectListItem,
  TrendsResponse,
} from "../types/navigator";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";

async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { signal });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const err = await res.json();
      if (err && typeof err.detail === "string") detail = err.detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

function qs(params: Record<string, unknown>): string {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === "") continue;
    sp.set(k, String(v));
  }
  const s = sp.toString();
  return s ? `?${s}` : "";
}

export interface AskStreamHandlers {
  onStatus?: (data: Record<string, unknown>) => void;
  onPlan?: (data: Record<string, unknown>) => void;
  onStep?: (data: Record<string, unknown>) => void;
  onAmbiguous?: (data: Record<string, unknown>) => void;
  onToken?: (data: { text: string }) => void;
  onFinal?: (data: AskResult) => void;
  onError?: (err: string) => void;
}

export const navigatorApi = {
  getTrends: (
    params: { kind?: string; venue?: string; period?: string; trend_class?: string; q?: string; limit?: number },
    signal?: AbortSignal,
  ) => getJson<TrendsResponse>(`/trends${qs(params)}`, signal),

  listSubjects: (params: { kind?: string; q?: string; limit?: number }, signal?: AbortSignal) =>
    getJson<{ total: number; items: SubjectListItem[]; classification_note: string }>(`/subjects${qs(params)}`, signal),

  getSubjectDetail: (subjectId: string, signal?: AbortSignal) =>
    getJson<SubjectDetailResponse>(`/subjects/${encodeURIComponent(subjectId)}`, signal),

  listGroups: (
    params: { sector?: string; country?: string; notable_only?: boolean; q?: string; limit?: number; offset?: number },
    signal?: AbortSignal,
  ) => getJson<GroupsResponse>(`/groups${qs(params)}`, signal),

  getGroupDetail: (groupId: string, signal?: AbortSignal) =>
    getJson<GroupDetailResponse>(`/groups/${encodeURIComponent(groupId)}`, signal),

  listCommunities: (params: { source?: string; q?: string; limit?: number }, signal?: AbortSignal) =>
    getJson<CommunitiesResponse>(`/communities${qs(params)}`, signal),

  getCommunityDetail: (communityId: string, signal?: AbortSignal) =>
    getJson<CommunityNodeItem>(`/communities/${encodeURIComponent(communityId)}`, signal),

  getCommunityMembers: (communityId: string, params: { limit?: number; offset?: number } = {}) =>
    getJson<{ community_id: string; total: number; members: Array<{ id: string; name: string; label: string; papers?: number; trend_class?: string }> }>(
      `/communities/${encodeURIComponent(communityId)}/members${qs(params)}`,
    ),

  getNetworkScience: (signal?: AbortSignal) => getJson<Record<string, unknown>>("/network-science", signal),

  getNode360: (nodeId: string, signal?: AbortSignal) =>
    getJson<Record<string, unknown>>(`/node360/${encodeURIComponent(nodeId)}`, signal),

  getAboutData: (signal?: AbortSignal) => getJson<Record<string, unknown>>("/about-data", signal),

  getEnrichedSchema: (signal?: AbortSignal) =>
    getJson<{ graph_version: string; labels: string[]; predicates: Array<{ relation: string; kind: string; source: string; target: string }> }>(
      "/explorer-enriched/schema",
      signal,
    ),

  searchEnriched: (params: { q?: string; label?: string; limit?: number }) =>
    getJson<{ query: string; results: Array<{ id: string; name: string; label: string; year?: number; sector?: string }> }>(
      `/explorer-enriched/search${qs(params)}`,
    ),

  getEnrichedNeighbors: (nodeId: string, limit = 40) =>
    getJson<{ center_id: string; nodes: Array<{ id: string; name: string; label: string }>; edges: Array<{ id: string; relation: string; source: string; target: string; support_count: number; evidence_kind: string }> }>(
      `/explorer-enriched/neighbors/${encodeURIComponent(nodeId)}${qs({ limit })}`,
    ),

  getAskDemos: (signal?: AbortSignal) =>
    getJson<{ demos: AskDemoItem[]; generated_at?: string | null }>("/ask/demos", signal),

  async askStream(
    payload: {
      question: string;
      mode: "auto" | "local" | "global";
      use_cache: boolean;
      resolved_overrides?: Record<string, string>;
    },
    handlers: AskStreamHandlers,
    signal?: AbortSignal,
  ): Promise<void> {
    const res = await fetch(`${API_BASE}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
      body: JSON.stringify({ ...payload, stream: true }),
      signal,
    });
    if (!res.ok || !res.body) {
      handlers.onError?.(`Request failed (HTTP ${res.status})`);
      return;
    }
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const blocks = buffer.split("\n\n");
      buffer = blocks.pop() || "";
      for (const block of blocks) {
        let evName = "message";
        const dataLines: string[] = [];
        for (const line of block.split("\n")) {
          if (line.startsWith("event:")) evName = line.slice(6).trim();
          else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
        }
        if (!dataLines.length) continue;
        try {
          const parsed = JSON.parse(dataLines.join("\n"));
          if (evName === "status") handlers.onStatus?.(parsed);
          else if (evName === "plan") handlers.onPlan?.(parsed);
          else if (evName === "step") handlers.onStep?.(parsed);
          else if (evName === "ambiguous") handlers.onAmbiguous?.(parsed);
          else if (evName === "token") handlers.onToken?.(parsed);
          else if (evName === "final") handlers.onFinal?.(parsed);
          else if (evName === "error") handlers.onError?.(parsed.error || "Unknown error");
        } catch {
          /* ignore malformed SSE chunk */
        }
      }
    }
  },
};
