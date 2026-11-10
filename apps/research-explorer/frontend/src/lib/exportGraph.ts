import type {
  GraphEdge,
  GraphNode,
  GraphSummaryResponse,
} from "../types/explorer";
import type { ViewSpec } from "./viewSpec";
export function exportGraph(
  nodes: GraphNode[],
  edges: GraphEdge[],
  spec: ViewSpec,
  summary?: GraphSummaryResponse,
) {
  return {
    schema_version: "explorer-slice-v2",
    exported_at: new Date().toISOString(),
    graph_version: summary?.graph_version ?? null,
    view_spec: spec,
    scope: "effective_displayed_subgraph",
    sampling:
      "Bounded illustrative selection; not statistically representative or the full projection",
    metric_meanings: {
      displayed_degree: "incident displayed semantic edges",
      displayed_neighbor_count: "unique displayed neighbors",
      displayed_strength:
        "sum of frozen full-period fractional weights on displayed collaboration edges; not recomputed for a paper window; mixed predicates are not comparable",
      full_metrics:
        "frozen full-projection metrics, separate from displayed metrics",
    },
    method_versions: [...new Set(edges.map((e) => e.method_version))].sort(),
    quality: summary?.quality ?? null,
    caveats: summary?.scientific_caveats ?? [
      "Quality artifacts unavailable. AI assessment is not independent human validation; topic coverage is not accuracy. Within-corpus citations are not global influence.",
    ],
    node_count: nodes.length,
    edge_count: edges.length,
    nodes,
    edges,
  };
}
export function csv(rows: Record<string, unknown>[], headers: string[]) {
  const escape = (x: unknown) => `"${String(x ?? "").replace(/"/g, '""')}"`;
  return [headers, ...rows.map((r) => headers.map((h) => r[h]))]
    .map((r) => r.map(escape).join(","))
    .join("\r\n");
}
export function download(content: string, name: string, type: string) {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
