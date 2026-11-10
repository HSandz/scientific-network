import type { GraphNode, GraphEdge, EdgeFilterMode } from "../types/explorer";
export const repeatedCollaboration = (edge: GraphEdge) =>
  !["COAUTHORED_WITH", "COLLABORATED_WITH"].includes(edge.relation) ||
  edge.support_count >= 2;
export function effectiveSlice(
  nodes: GraphNode[],
  edges: GraphEdge[],
  filter: EdgeFilterMode,
) {
  const ids = new Set(nodes.map((n) => n.id));
  const effectiveEdges = edges.filter(
    (e) =>
      ids.has(e.source) &&
      ids.has(e.target) &&
      (filter !== "strong" || repeatedCollaboration(e)),
  );
  const degree = new Map<string, number>(),
    neighbors = new Map<string, Set<string>>(),
    strength = new Map<string, number>();
  for (const e of effectiveEdges)
    for (const [a, b] of [
      [e.source, e.target],
      [e.target, e.source],
    ]) {
      degree.set(a, (degree.get(a) || 0) + 1);
      if (!neighbors.has(a)) neighbors.set(a, new Set());
      neighbors.get(a)!.add(b);
      // Strength has comparable units only for collaboration predicates.
      if (["COAUTHORED_WITH", "COLLABORATED_WITH"].includes(e.relation))
        strength.set(a, (strength.get(a) || 0) + (e.fractional_weight ?? 0));
    }
  return {
    nodes: nodes
      .filter((n) => filter !== "connected" || degree.has(n.id))
      .map((n) => ({
        ...n,
        displayed_degree: degree.get(n.id) || 0,
        displayed_neighbor_count: neighbors.get(n.id)?.size || 0,
        displayed_strength: strength.get(n.id) || 0,
      })),
    edges: effectiveEdges,
  };
}
