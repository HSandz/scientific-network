import type { AnalyticsFilters, ExplorerFilters, TableWorkspaceState } from "../stores/useExplorerStore";
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
  analyticsSection?: string;
  analyticsFilters?: AnalyticsFilters;
  tableWorkspace?: TableWorkspaceState;
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
  const mode = choice(v.viewMode, ["heterogeneous", "researchers", "organizations", "citations"] as const, "heterogeneous");
  const before = JSON.stringify(filters);
  if (mode !== "organizations") {
    filters.countryCode = "";
    filters.crossSectorOnly = false;
    filters.includeTopics = false;
  }
  if (mode !== "organizations" && mode !== "heterogeneous") filters.sector = "";
  if (mode !== "organizations" && mode !== "researchers") filters.communityId = "";
  if (mode === "heterogeneous") filters.includeIsolates = false;
  if (mode === "citations") {
    filters.minSupport = 1; filters.minWeight = 0; filters.includeIsolates = false;
  }
  const cleared = before !== JSON.stringify(filters);
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
    tableWorkspace: {
      mode: choice(v.tableWorkspace?.mode, ["nodes", "edges"] as const, "nodes"),
      nodeSearch: typeof v.tableWorkspace?.nodeSearch === "string" ? v.tableWorkspace.nodeSearch.slice(0,200) : "",
      nodeLabel: choice(v.tableWorkspace?.nodeLabel, ["", "Researcher", "Paper", "Organization", "Topic", "Venue"] as const, "Researcher"),
      nodeSector: choice(v.tableWorkspace?.nodeSector, ["", "academia", "industry", "government", "nonprofit", "unknown"] as const, ""),
      nodeVenue: choice(v.tableWorkspace?.nodeVenue, ["", "venue:aaai", "venue:ijcai"] as const, ""),
      nodeSortBy: choice(v.tableWorkspace?.nodeSortBy, ["score", "name", "year", "sector", "id"] as const, "score"),
      nodeSortOrder: choice(v.tableWorkspace?.nodeSortOrder, ["asc", "desc"] as const, "desc"),
      nodePage: Math.round(number(v.tableWorkspace?.nodePage,1,5000,1)),
      edgeSearch: typeof v.tableWorkspace?.edgeSearch === "string" ? v.tableWorkspace.edgeSearch.slice(0,200) : "",
      edgeRelation: choice(v.tableWorkspace?.edgeRelation, ["", ...defaults.relations] as const, "COAUTHORED_WITH"),
      edgeEvidenceKind: choice(v.tableWorkspace?.edgeEvidenceKind, ["", "observed", "inferred_topic", "curated_taxonomy", "derived"] as const, ""),
      edgeMinSupport: Math.round(number(v.tableWorkspace?.edgeMinSupport,1,100,1)),
      edgeSortBy: choice(v.tableWorkspace?.edgeSortBy, ["support_count", "fractional_weight", "relation", "edge_id"] as const, "support_count"),
      edgeSortOrder: choice(v.tableWorkspace?.edgeSortOrder, ["asc", "desc"] as const, "desc"),
      edgePage: Math.round(number(v.tableWorkspace?.edgePage,1,5000,1)),
    },
    analyticsFilters: {
      venue: choice(v.analyticsFilters?.venue, ["venue:aaai", "venue:ijcai"] as const, "venue:aaai"),
      topic: typeof v.analyticsFilters?.topic === "string" ? v.analyticsFilters.topic.slice(0,80) : "",
      yearMin: Math.round(number(v.analyticsFilters?.yearMin,2021,2025,2021)),
      yearMax: Math.round(number(v.analyticsFilters?.yearMax,2021,2025,2025)),
      family: typeof v.analyticsFilters?.family === "string" ? v.analyticsFilters.family.slice(0,80) : "",
      community: typeof v.analyticsFilters?.community === "string" ? v.analyticsFilters.community.slice(0,80) : "",
    },
    analyticsSection: choice(v.analyticsSection, ["robustness", "topics", "communities", "sectors", "trajectories"] as const, "robustness"),
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
    notice: cleared ? "Unsupported hidden filters were cleared for this projection." : typeof v.notice === "string" ? v.notice.slice(0, 240) : undefined,
  };
}
export function makeViewSpec(state: {
  viewMode: ViewMode;
  workspaceTab: WorkspaceTab;
  analyticsSection?: string;
  analyticsFilters?: AnalyticsFilters;
  tableWorkspace?: TableWorkspaceState;
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
    analyticsSection: state.analyticsSection,
    analyticsFilters: state.analyticsFilters,
    tableWorkspace: state.tableWorkspace,
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
