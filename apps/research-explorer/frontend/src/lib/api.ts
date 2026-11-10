import {
  CompareResponse,
  EdgeEvidenceResponse,
  GraphEdge,
  GraphSummaryResponse,
  GraphViewResponse,
  HealthResponse,
  NeighborhoodResponse,
  NodeDetailResponse,
  PathResponse,
  SearchResponse,
  TableEdgesResponse,
  TableNodesResponse,
  ViewMode,
} from "../types/explorer";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";

async function fetchJson<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...(options?.body ? { "Content-Type": "application/json" } : {}),
      ...(options?.headers || {}),
    },
  });
  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const err = await response.json();
      if (err && typeof err.detail === "string") {
        detail = err.detail;
      }
    } catch {
      // ignore parse error
    }
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

function toQueryString(params: Record<string, unknown>): string {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === "") continue;
    if (Array.isArray(v)) {
      for (const item of v) {
        if (item !== undefined && item !== null && item !== "") {
          sp.append(k, String(item));
        }
      }
    } else {
      sp.set(k, String(v));
    }
  }
  const qs = sp.toString();
  return qs ? `?${qs}` : "";
}

export const explorerApi = {
  getHealth: () => fetchJson<HealthResponse>("/health"),

  getSummary: () => fetchJson<GraphSummaryResponse>("/graph/summary"),

  getSchema: () => fetchJson<Record<string, unknown>>("/graph/schema"),

  getViewsMeta: () => fetchJson<Record<string, unknown>>("/views"),

  getViewSubgraph: (
    view: ViewMode,
    filters: Record<string, unknown>,
    signal?: AbortSignal
  ) =>
    fetchJson<GraphViewResponse>(
      `/views/${view}${toQueryString(filters)}`,
      { signal }
    ),

  search: (
    params: {
      q: string;
      label?: string[];
      year_min?: number | null;
      year_max?: number | null;
      venue?: string | null;
      sector?: string | null;
      limit?: number;
    },
    signal?: AbortSignal
  ) =>
    fetchJson<SearchResponse>(
      `/search${toQueryString(params)}`,
      { signal }
    ),

  getNodeDetail: (nodeId: string, signal?: AbortSignal) =>
    fetchJson<NodeDetailResponse>(
      `/nodes/${encodeURIComponent(nodeId)}`,
      { signal }
    ),

  getNodeNeighbors: (
    nodeId: string,
    params: Record<string, unknown>,
    signal?: AbortSignal
  ) =>
    fetchJson<NeighborhoodResponse>(
      `/nodes/${encodeURIComponent(nodeId)}/neighbors${toQueryString(params)}`,
      { signal }
    ),

  getEdgeDetail: (edgeId: string, signal?: AbortSignal) =>
    fetchJson<GraphEdge>(
      `/edges/${encodeURIComponent(edgeId)}`,
      { signal }
    ),

  getEdgeEvidence: (edgeId: string, signal?: AbortSignal) =>
    fetchJson<EdgeEvidenceResponse>(
      `/edges/${encodeURIComponent(edgeId)}/evidence`,
      { signal }
    ),

  getAnalyticsOverview: (signal?: AbortSignal) =>
    fetchJson<Record<string, unknown>>("/analytics/overview", { signal }),

  findPath: (payload: {
    source_id: string;
    target_id: string;
    mode: string;
    max_hops: number;
  }) =>
    fetchJson<PathResponse>("/paths", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  compareEntities: (leftId: string, rightId: string) =>
    fetchJson<CompareResponse>(
      `/compare${toQueryString({ left_id: leftId, right_id: rightId })}`
    ),

  getTableNodes: (params: Record<string, unknown>, signal?: AbortSignal) =>
    fetchJson<TableNodesResponse>(
      `/table/nodes${toQueryString(params)}`,
      { signal }
    ),

  getTableEdges: (params: Record<string, unknown>, signal?: AbortSignal) =>
    fetchJson<TableEdgesResponse>(
      `/table/edges${toQueryString(params)}`,
      { signal }
    ),
};
