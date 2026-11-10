import type { ExplorerFilters } from "../stores/useExplorerStore";
import type {
  EdgeFilterMode,
  GraphViewScope,
  LayoutMode,
  ViewMode,
  WorkspaceTab,
} from "../types/explorer";

export interface ViewSpec {
  version: 2;
  viewMode: ViewMode;
  workspaceTab: WorkspaceTab;
  filters: ExplorerFilters;
  layoutMode: LayoutMode;
  edgeFilterMode: EdgeFilterMode;
  selectedNodeId: string | null;
  selectedEdgeId: string | null;
  scope: Pick<
    GraphViewScope,
    "kind" | "title" | "centerId" | "pathData" | "neighborParams"
  >;
  shareable: boolean;
  notice?: string;
}
export const validId = (x: unknown): x is string =>
  typeof x === "string" &&
  /^(researcher|organization|paper|topic|venue|edge):[\w:.-]{1,180}$/.test(x);
const choice = <T extends string>(
  x: unknown,
  allowed: readonly T[],
  fallback: T,
): T => (allowed.includes(x as T) ? (x as T) : fallback);
const number = (x: unknown, lo: number, hi: number, fallback: number) =>
  typeof x === "number" && Number.isFinite(x)
    ? Math.min(hi, Math.max(lo, x))
    : fallback;
export function validateSpec(
  input: unknown,
  defaults: ExplorerFilters,
): ViewSpec | null {
  if (!input || typeof input !== "object" || (input as any).version !== 2)
    return null;
  const v = input as any,
    f = v.filters || {},
    filters = { ...defaults };
  for (const key of [
    "communityId",
    "sector",
    "countryCode",
    "venue",
    "topicId",
    "preset",
  ] as const) {
    if (typeof f[key] === "string") filters[key] = f[key].slice(0, 80);
  }
  for (const key of [
    "crossSectorOnly",
    "includeIsolates",
    "includeTopics",
  ] as const)
    if (typeof f[key] === "boolean") filters[key] = f[key];
  filters.limit = Math.round(number(f.limit, 10, 250, defaults.limit));
  filters.minSupport = Math.round(number(f.minSupport, 1, 100, 1));
  filters.minWeight = number(f.minWeight, 0, 50, 0);
  filters.yearMin = Math.round(number(f.yearMin, 2021, 2025, 2021));
  filters.yearMax = Math.max(
    filters.yearMin,
    Math.round(number(f.yearMax, 2021, 2025, 2025)),
  );
  if (Array.isArray(f.nodeLabels))
    filters.nodeLabels = defaults.nodeLabels.filter((x) =>
      f.nodeLabels.includes(x),
    );
  if (Array.isArray(f.relations))
    filters.relations = defaults.relations.filter((x) =>
      f.relations.includes(x),
    );
  const kind = choice(
    v.scope?.kind,
    ["overview", "ego", "path"] as const,
    "overview",
  );
  const scope: ViewSpec["scope"] = {
    kind,
    title:
      typeof v.scope?.title === "string"
        ? v.scope.title.slice(0, 180)
        : `${kind}: restored view`,
  };
  if (kind === "ego" && validId(v.scope?.centerId))
    scope.centerId = v.scope.centerId;
  if (
    kind === "path" &&
    validId(v.scope?.pathData?.sourceId) &&
    validId(v.scope?.pathData?.targetId)
  ) {
    const p = v.scope.pathData;
    scope.pathData = {
      sourceId: p.sourceId,
      targetId: p.targetId,
      hopCount: 0,
      steps: [],
      mode: choice(
        p.mode,
        [
          "heterogeneous",
          "collaboration",
          "citation_directed",
          "citation_undirected",
        ] as const,
        "heterogeneous",
      ),
      maxHops: Math.round(number(p.maxHops, 1, 4, 4)),
    };
  }
  // Requests are rebuilt from validated filters, never from arbitrary URL request parameters.
  if (
    (kind === "ego" && !scope.centerId) ||
    (kind === "path" && !scope.pathData)
  )
    scope.kind = "overview";
  return {
    version: 2,
    viewMode: choice(
      v.viewMode,
      ["heterogeneous", "researchers", "organizations", "citations"] as const,
      "heterogeneous",
    ),
    workspaceTab: choice(
      v.workspaceTab,
      ["graph", "table", "analytics"] as const,
      "graph",
    ),
    layoutMode: choice(
      v.layoutMode,
      ["seeded", "circular", "concentric"] as const,
      "seeded",
    ),
    edgeFilterMode: choice(
      v.edgeFilterMode,
      ["all", "strong", "connected"] as const,
      "all",
    ),
    filters,
    scope,
    selectedNodeId: validId(v.selectedNodeId) ? v.selectedNodeId : null,
    selectedEdgeId: validId(v.selectedEdgeId) ? v.selectedEdgeId : null,
    shareable: true,
    notice: typeof v.notice === "string" ? v.notice.slice(0, 240) : undefined,
  };
}
export function makeViewSpec(state: {
  viewMode: ViewMode;
  workspaceTab: WorkspaceTab;
  filters: ExplorerFilters;
  layoutMode: LayoutMode;
  edgeFilterMode: EdgeFilterMode;
  selectedNodeId: string | null;
  selectedEdgeId: string | null;
  graphViewScope: GraphViewScope;
  extraNodes: unknown[];
  extraEdges: unknown[];
}): ViewSpec {
  const { kind, title, centerId, pathData, neighborParams } =
    state.graphViewScope;
  const shareable =
    !state.graphViewScope.transient &&
    (kind === "overview"
      ? !state.extraNodes.length && !state.extraEdges.length
      : kind === "path"
        ? !!pathData?.mode
        : !!neighborParams);
  return {
    version: 2,
    viewMode: state.viewMode,
    workspaceTab: state.workspaceTab,
    filters: state.filters,
    layoutMode: state.layoutMode,
    edgeFilterMode: state.edgeFilterMode,
    selectedNodeId: state.selectedNodeId,
    selectedEdgeId: state.selectedEdgeId,
    scope: { kind, title, centerId, pathData, neighborParams },
    shareable,
    ...(!shareable
      ? {
          notice:
            "Expanded or legacy transient view cannot be reconstructed exactly. Link opens the filtered overview; export JSON preserves the displayed slice.",
        }
      : {}),
  };
}
export function shareSpec(spec: ViewSpec): ViewSpec {
  return spec.shareable
    ? spec
    : {
        ...spec,
        scope: { kind: "overview", title: "Overview" },
        selectedNodeId: null,
        selectedEdgeId: null,
      };
}
