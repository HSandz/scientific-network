import type { GraphEdge } from "../types/explorer";
export function parallelGroups(edges: GraphEdge[]) {
  const groups = new Map<string, GraphEdge[]>();
  for (const e of edges) {
    const key = JSON.stringify([e.source, e.target].sort());
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key)!.push(e);
  }
  return [...groups.values()]
    .filter((g) => g.length > 1)
    .map((g) => g.sort((a, b) => a.edge_id.localeCompare(b.edge_id)));
}
export function lanePath(
  a: { x: number; y: number },
  b: { x: number; y: number },
  index: number,
  count: number,
) {
  const dx = b.x - a.x,
    dy = b.y - a.y,
    len = Math.max(1, Math.hypot(dx, dy));
  // All groups use canonical endpoint orientation; reciprocal arrows reverse the path.
  const offset = (index - (count - 1) / 2) * 24;
  return {
    x: (a.x + b.x) / 2 - (dy / len) * offset,
    y: (a.y + b.y) / 2 + (dx / len) * offset,
  };
}
