import {
  makeViewSpec,
  shareSpec,
  validateSpec,
  validId,
  ViewSpec,
} from "../lib/viewSpec";
import { create } from "zustand";
import {
  EdgeFilterMode,
  GraphEdge,
  GraphNode,
  GraphViewScope,
  LayoutMode,
  NodeLabel,
  PathResponse,
  RelationType,
  ViewMode,
  WorkspaceTab,
} from "../types/explorer";

export interface ExplorerFilters {
  limit: number;
  communityId: string;
  sector: string;
  crossSectorOnly: boolean;
  countryCode: string;
  yearMin: number;
  yearMax: number;
  venue: string;
  topicId: string;
  minSupport: number;
  minWeight: number;
  includeIsolates: boolean;
  includeTopics: boolean;
  preset: string;
  nodeLabels: NodeLabel[];
  relations: RelationType[];
}

export interface AnalyticsFilters {
  venue: string;
  topic: string;
  yearMin: number;
  yearMax: number;
  family: string;
  community: string;
}
const DEFAULT_ANALYTICS_FILTERS: AnalyticsFilters = { venue: "venue:aaai", topic: "", yearMin: 2021, yearMax: 2025, family: "", community: "" };

export interface SavedViewBookmark {
  id: string;
  name: string;
  viewMode: ViewMode;
  filters: ExplorerFilters;
  selectedNodeId: string | null;
  spec?: ViewSpec;
}

const THEME_STORAGE_KEY = "scientific-network-theme-v1";

function getInitialDarkMode(): boolean {
  if (typeof window === "undefined") return true;
  let isDark = true;
  try {
    const stored =
      window.localStorage.getItem(THEME_STORAGE_KEY) ||
      window.localStorage.getItem("scientific-network-theme");
    if (stored === "light") {
      isDark = false;
    } else {
      isDark = true;
    }
  } catch {
    // ignore storage access issues
  }
  if (typeof document !== "undefined") {
    document.documentElement.classList.toggle("dark", isDark);
  }
  return isDark;
}

function getInitialLeftSidebarOpen(): boolean {
  if (typeof window === "undefined") return true;
  return window.innerWidth >= 1024;
}

function canKeepBothDesktopRails(): boolean {
  if (typeof window === "undefined") return true;
  return window.innerWidth >= 1264;
}

const DEFAULT_FILTERS: ExplorerFilters = {
  limit: 100,
  communityId: "",
  sector: "",
  crossSectorOnly: false,
  countryCode: "",
  yearMin: 2021,
  yearMax: 2025,
  venue: "",
  topicId: "",
  minSupport: 1,
  minWeight: 0,
  includeIsolates: false,
  includeTopics: false,
  preset: "topic_taxonomy_ecosystem",
  nodeLabels: ["Researcher", "Paper", "Organization", "Topic", "Venue"],
  relations: [
    "AUTHORED",
    "AFFILIATED_WITH",
    "PUBLISHED_IN",
    "CITES",
    "HAS_TOPIC",
    "SUBTOPIC_OF",
    "COAUTHORED_WITH",
    "COLLABORATED_WITH",
    "RESEARCHES_TOPIC",
    "CONTRIBUTES_TO_TOPIC",
  ],
};

interface ExplorerState {
  // Theme & workspace layout
  insightReturn: boolean;
  analyticsSection: string;
  analyticsFilters: AnalyticsFilters;
  darkMode: boolean;
  workspaceTab: WorkspaceTab;
  leftSidebarOpen: boolean;
  rightSidebarOpen: boolean;
  canvasExpanded: boolean;
  layoutMode: LayoutMode;
  edgeFilterMode: EdgeFilterMode;

  // Exploration mode & filters
  viewMode: ViewMode;
  filters: ExplorerFilters;

  // Explicit graph views (Overview, Ego, Path)
  graphViewScope: GraphViewScope;
  cameraState: { x: number; y: number; ratio: number } | null;
  shareNotice: string | null;
  expansionError: { message: string; nodeId: string; replace: boolean } | null;

  // Selection & navigation history
  selectedNodeId: string | null;
  selectedEdgeId: string | null;
  hoveredNodeId: string | null;
  selectionHistory: Array<{ type: "node" | "edge"; id: string; label: string }>;

  // Incrementally expanded nodes/edges merged onto the current graph canvas
  extraNodes: GraphNode[];
  extraEdges: GraphEdge[];
  focusedCenterId: string | null;

  // Modals / tools
  searchModalOpen: boolean;
  pathFinderOpen: boolean;
  compareModalOpen: boolean;
  caveatsModalOpen: boolean;
  compareLeftId: string;
  compareRightId: string;

  // Saved bookmarks
  savedViews: SavedViewBookmark[];

  // Actions
  toggleDarkMode: () => void;
  setWorkspaceTab: (tab: WorkspaceTab) => void;
  setLeftSidebarOpen: (open: boolean) => void;
  setRightSidebarOpen: (open: boolean) => void;
  setCanvasExpanded: (expanded: boolean) => void;
  setLayoutMode: (mode: LayoutMode) => void;
  setEdgeFilterMode: (mode: EdgeFilterMode) => void;
  setGraphViewScope: (scope: GraphViewScope) => void;
  setCameraState: (
    camera: { x: number; y: number; ratio: number } | null,
  ) => void;
  setExpansionError: (
    err: { message: string; nodeId: string; replace: boolean } | null,
  ) => void;
  setViewMode: (mode: ViewMode) => void;
  updateFilters: (partial: Partial<ExplorerFilters>) => void;
  resetFilters: () => void;
  selectNode: (nodeId: string | null, label?: string) => void;
  selectEdge: (edgeId: string | null, label?: string) => void;
  clearSelection: () => void;
  setHoveredNodeId: (nodeId: string | null) => void;
  goBackSelection: () => void;
  mergeSubgraph: (
    nodes: GraphNode[],
    edges: GraphEdge[],
    replace?: boolean,
    centerId?: string | null,
  ) => void;
  enterEgoView: (
    centerNode: GraphNode,
    nodes: GraphNode[],
    edges: GraphEdge[],
    cameraState?: { x: number; y: number; ratio: number } | null,
    params?: Record<string, unknown>,
  ) => void;
  enterPathView: (
    path: PathResponse,
    cameraState?: { x: number; y: number; ratio: number } | null,
  ) => void;
  restorePriorGraphScope: () => void;
  clearExtraSubgraph: () => void;
  setSearchModalOpen: (open: boolean) => void;
  setPathFinderOpen: (open: boolean) => void;
  setCompareModalOpen: (
    open: boolean,
    leftId?: string,
    rightId?: string,
  ) => void;
  setCaveatsModalOpen: (open: boolean) => void;
  saveCurrentView: (name: string) => void;
  applySavedView: (bookmark: SavedViewBookmark) => void;
  hydrateFromUrl: () => void;
  buildShareUrl: () => string;
}

export const useExplorerStore = create<ExplorerState>((set, get) => ({
  insightReturn: false,
  analyticsSection: "robustness",
  analyticsFilters: { ...DEFAULT_ANALYTICS_FILTERS },
  darkMode: getInitialDarkMode(),
  workspaceTab: "graph",
  leftSidebarOpen: getInitialLeftSidebarOpen(),
  rightSidebarOpen: false,
  canvasExpanded: false,
  layoutMode: "seeded",
  edgeFilterMode: "all",

  viewMode: "heterogeneous",
  filters: { ...DEFAULT_FILTERS, limit: 120 },

  graphViewScope: {
    kind: "overview",
    title: "Overview: Knowledge graph",
  },
  cameraState: null,
  shareNotice: null,
  expansionError: null,

  selectedNodeId: null,
  selectedEdgeId: null,
  hoveredNodeId: null,
  selectionHistory: [],

  extraNodes: [],
  extraEdges: [],
  focusedCenterId: null,

  searchModalOpen: false,
  pathFinderOpen: false,
  compareModalOpen: false,
  caveatsModalOpen: false,
  compareLeftId: "organization:I183067930",
  compareRightId: "organization:I2250653659",

  savedViews: [
    {
      id: "preset-bridges",
      name: "Top Researcher Collaborations (100)",
      viewMode: "researchers",
      filters: { ...DEFAULT_FILTERS, limit: 100 },
      selectedNodeId: "researcher:openalex:A5017743551",
    },
    {
      id: "preset-cross-sector",
      name: "Cross-Sector Org Partnerships",
      viewMode: "organizations",
      filters: { ...DEFAULT_FILTERS, limit: 60, crossSectorOnly: true },
      selectedNodeId: null,
    },
    {
      id: "preset-informer-citations",
      name: "Within-Corpus Citation Leaders",
      viewMode: "citations",
      filters: { ...DEFAULT_FILTERS, limit: 80 },
      selectedNodeId: "paper:aaai:2021:17325",
    },
    {
      id: "preset-ten-predicates",
      name: "10-Predicate Knowledge Ecosystem",
      viewMode: "heterogeneous",
      filters: {
        ...DEFAULT_FILTERS,
        limit: 120,
        preset: "topic_taxonomy_ecosystem",
      },
      selectedNodeId: null,
    },
  ],

  toggleDarkMode: () =>
    set((state) => {
      const next = !state.darkMode;
      if (typeof document !== "undefined") {
        document.documentElement.classList.toggle("dark", next);
      }
      if (typeof window !== "undefined") {
        try {
          window.localStorage.setItem(
            THEME_STORAGE_KEY,
            next ? "dark" : "light",
          );
          window.localStorage.setItem(
            "scientific-network-theme",
            next ? "dark" : "light",
          );
        } catch {
          // ignore storage errors
        }
      }
      return { darkMode: next };
    }),

  setWorkspaceTab: (workspaceTab) =>
    set((state) => ({
      workspaceTab,
      insightReturn:
        state.insightReturn ||
        (state.workspaceTab === "analytics" && workspaceTab === "graph"),
      rightSidebarOpen:
        workspaceTab === "graph"
          ? Boolean(state.selectedNodeId || state.selectedEdgeId)
          : false,
      leftSidebarOpen:
        workspaceTab === "graph" &&
        state.leftSidebarOpen &&
        (!Boolean(state.selectedNodeId || state.selectedEdgeId) ||
          canKeepBothDesktopRails()),
    })),
  setLeftSidebarOpen: (leftSidebarOpen) =>
    set((state) => ({
      leftSidebarOpen,
      rightSidebarOpen:
        leftSidebarOpen && !canKeepBothDesktopRails()
          ? false
          : state.rightSidebarOpen,
    })),
  setRightSidebarOpen: (rightSidebarOpen) =>
    set((state) => ({
      rightSidebarOpen,
      leftSidebarOpen:
        rightSidebarOpen && !canKeepBothDesktopRails()
          ? false
          : state.leftSidebarOpen,
    })),
  setCanvasExpanded: (canvasExpanded) =>
    set((state) => ({
      canvasExpanded,
      leftSidebarOpen:
        !canvasExpanded &&
        (typeof window === "undefined" || window.innerWidth >= 1024),
      rightSidebarOpen:
        !canvasExpanded &&
        Boolean(state.selectedNodeId || state.selectedEdgeId),
    })),

  setLayoutMode: (layoutMode) => set({ layoutMode }),
  setEdgeFilterMode: (edgeFilterMode) => set({ edgeFilterMode }),
  setGraphViewScope: (graphViewScope) => set({ graphViewScope }),
  setCameraState: (cameraState) => set({ cameraState }),
  setExpansionError: (expansionError) => set({ expansionError }),

  setViewMode: (viewMode) => {
    const defaultLimits: Record<ViewMode, number> = {
      researchers: 100,
      organizations: 60,
      citations: 80,
      heterogeneous: 120,
    };
    set((state) => {
      // Clear selection if it does not belong in the new projection
      let nextSelectedNodeId = state.selectedNodeId;
      if (nextSelectedNodeId) {
        if (
          viewMode === "researchers" &&
          !nextSelectedNodeId.startsWith("researcher:")
        ) {
          nextSelectedNodeId = null;
        } else if (
          viewMode === "organizations" &&
          !nextSelectedNodeId.startsWith("organization:")
        ) {
          nextSelectedNodeId = null;
        } else if (
          viewMode === "citations" &&
          !nextSelectedNodeId.startsWith("paper:")
        ) {
          nextSelectedNodeId = null;
        }
      }
      return {
        viewMode,
        extraNodes: [],
        extraEdges: [],
        focusedCenterId: null,
        hoveredNodeId: null,
        expansionError: null,
        selectedNodeId: nextSelectedNodeId,
        selectedEdgeId: null,
        rightSidebarOpen: Boolean(nextSelectedNodeId),
        graphViewScope: {
          kind: "overview",
          title: `Overview: ${viewMode.charAt(0).toUpperCase() + viewMode.slice(1)}`,
        },
        filters: {
          ...state.filters,
          limit: defaultLimits[viewMode],
          communityId: "",
          ...(viewMode !== "organizations" ? { countryCode: "", crossSectorOnly: false, includeTopics: false } : {}),
          ...(viewMode !== "organizations" && viewMode !== "heterogeneous" ? { sector: "" } : {}),
          ...(viewMode === "heterogeneous" ? { includeIsolates: false } : {}),
          ...(viewMode === "citations" ? { minSupport: 1, minWeight: 0, includeIsolates: false } : {}),
        },
      };
    });
  },

  updateFilters: (partial) =>
    set((state) => ({
      filters: { ...state.filters, ...partial },
      selectedEdgeId: null,
      hoveredNodeId: null,
      graphViewScope: {
        kind: "overview",
        title: `Overview: ${state.viewMode}`,
      },
      extraNodes: [],
      extraEdges: [],
      focusedCenterId: null,
      expansionError: null,
    })),

  resetFilters: () =>
    set((state) => ({
      filters: {
        ...DEFAULT_FILTERS,
        limit:
          state.viewMode === "organizations"
            ? 60
            : state.viewMode === "citations"
              ? 80
              : state.viewMode === "heterogeneous"
                ? 120
                : 100,
      },
      extraNodes: [],
      extraEdges: [],
      focusedCenterId: null,
      edgeFilterMode: "all",
      expansionError: null,
    })),

  selectNode: (nodeId, label) =>
    set((state) => {
      if (!nodeId) {
        return {
          selectedNodeId: null,
          rightSidebarOpen: Boolean(state.selectedEdgeId),
        };
      }
      const nextHistory = [
        ...state.selectionHistory.filter(
          (item) => !(item.type === "node" && item.id === nodeId),
        ),
        { type: "node" as const, id: nodeId, label: label || nodeId },
      ].slice(-12);
      return {
        selectedNodeId: nodeId,
        selectedEdgeId: null,
        rightSidebarOpen: true,
        leftSidebarOpen: canKeepBothDesktopRails()
          ? state.leftSidebarOpen
          : false,
        selectionHistory: nextHistory,
      };
    }),

  selectEdge: (edgeId, label) =>
    set((state) => {
      if (!edgeId) {
        return {
          selectedEdgeId: null,
          rightSidebarOpen: Boolean(state.selectedNodeId),
        };
      }
      const nextHistory = [
        ...state.selectionHistory.filter(
          (item) => !(item.type === "edge" && item.id === edgeId),
        ),
        { type: "edge" as const, id: edgeId, label: label || edgeId },
      ].slice(-12);
      return {
        selectedEdgeId: edgeId,
        selectedNodeId: null,
        rightSidebarOpen: true,
        leftSidebarOpen: canKeepBothDesktopRails()
          ? state.leftSidebarOpen
          : false,
        selectionHistory: nextHistory,
      };
    }),

  clearSelection: () =>
    set((state) => ({
      selectedNodeId: null,
      selectedEdgeId: null,
      rightSidebarOpen: false,
      leftSidebarOpen:
        state.workspaceTab === "graph" &&
        !state.canvasExpanded &&
        typeof window !== "undefined" &&
        window.innerWidth >= 1024
          ? true
          : state.leftSidebarOpen,
    })),

  setHoveredNodeId: (hoveredNodeId) => set({ hoveredNodeId }),

  goBackSelection: () =>
    set((state) => {
      if (state.selectionHistory.length < 2) return {};
      const nextHist = state.selectionHistory.slice(0, -1);
      const prev = nextHist[nextHist.length - 1];
      return {
        selectionHistory: nextHist,
        selectedNodeId: prev.type === "node" ? prev.id : null,
        selectedEdgeId: prev.type === "edge" ? prev.id : null,
        rightSidebarOpen: true,
      };
    }),

  mergeSubgraph: (nodes, edges, replace = false, centerId = null) =>
    set((state) => {
      if (replace) {
        return {
          extraNodes: nodes,
          extraEdges: edges,
          focusedCenterId: centerId,
        };
      }
      const nodeMap = new Map<string, GraphNode>();
      for (const n of state.extraNodes) nodeMap.set(n.id, n);
      for (const n of nodes) nodeMap.set(n.id, n);

      const edgeMap = new Map<string, GraphEdge>();
      for (const e of state.extraEdges) edgeMap.set(e.edge_id, e);
      for (const e of edges) edgeMap.set(e.edge_id, e);

      return {
        graphViewScope: { ...state.graphViewScope, transient: true },
        extraNodes: Array.from(nodeMap.values()),
        extraEdges: Array.from(edgeMap.values()),
        focusedCenterId: centerId ?? state.focusedCenterId,
      };
    }),

  enterEgoView: (centerNode, nodes, edges, cameraState = null, params) =>
    set((state) => {
      const prior = {
        filters: state.filters,
        viewMode: state.viewMode,
        selectedNodeId: state.selectedNodeId,
        cameraState: cameraState ?? state.cameraState,
        extraNodes: state.extraNodes,
        extraEdges: state.extraEdges,
        graphViewScope: {
          kind: state.graphViewScope.kind,
          title: state.graphViewScope.title,
          description: state.graphViewScope.description,
          centerId: state.graphViewScope.centerId,
        },
      };
      return {
        graphViewScope: {
          kind: "ego",
          title: `Ego: ${centerNode.name}`,
          description: `Isolated 1-hop neighborhood (${nodes.length} nodes, ${edges.length} relationships)`,
          centerId: centerNode.id,
          neighborParams: params,
          priorState:
            state.graphViewScope.kind === "ego"
              ? state.graphViewScope.priorState
              : prior,
        },
        extraNodes: nodes,
        extraEdges: edges,
        focusedCenterId: centerNode.id,
        selectedNodeId: centerNode.id,
        rightSidebarOpen: true,
        expansionError: null,
      };
    }),

  enterPathView: (pathRes, cameraState = null) =>
    set((state) => {
      const prior = {
        filters: state.filters,
        viewMode: state.viewMode,
        selectedNodeId: state.selectedNodeId,
        cameraState: cameraState ?? state.cameraState,
        extraNodes: state.extraNodes,
        extraEdges: state.extraEdges,
        graphViewScope: {
          kind: state.graphViewScope.kind,
          title: state.graphViewScope.title,
          description: state.graphViewScope.description,
          centerId: state.graphViewScope.centerId,
        },
      };
      const sourceNode = pathRes.nodes.find((n) => n.id === pathRes.source_id);
      const targetNode = pathRes.nodes.find((n) => n.id === pathRes.target_id);
      const sName = sourceNode?.name || pathRes.source_id;
      const tName = targetNode?.name || pathRes.target_id;
      return {
        filters: { ...DEFAULT_FILTERS, limit: state.filters.limit },
        shareNotice: "Path traversal covers the full release period. Overview filters are suspended; Back restores them.",
        graphViewScope: {
          kind: "path",
          title: `Path: ${sName} → ${tName}`,
          description: `${pathRes.hop_count} hops, ${pathRes.nodes.length} entities`,
          pathData: {
            sourceId: pathRes.source_id,
            targetId: pathRes.target_id,
            sourceName: sName,
            targetName: tName,
            mode: pathRes.mode,
            maxHops: pathRes.max_hops,
            hopCount: pathRes.hop_count,
            steps: pathRes.step_descriptions || [],
          },
          priorState:
            state.graphViewScope.kind === "path"
              ? state.graphViewScope.priorState
              : prior,
        },
        extraNodes: pathRes.nodes,
        extraEdges: pathRes.edges,
        focusedCenterId: pathRes.source_id,
        selectedNodeId: pathRes.source_id,
        rightSidebarOpen: true,
        workspaceTab: "graph",
        expansionError: null,
      };
    }),

  restorePriorGraphScope: () =>
    set((state) => {
      const prior = state.graphViewScope.priorState;
      if (!prior) {
        return {
          graphViewScope: {
            kind: "overview",
            title: `Overview: ${state.viewMode.charAt(0).toUpperCase() + state.viewMode.slice(1)}`,
          },
          extraNodes: [],
          extraEdges: [],
          focusedCenterId: null,
          expansionError: null,
        };
      }
      return {
        graphViewScope: {
          kind: prior.graphViewScope.kind,
          title: prior.graphViewScope.title,
          description: prior.graphViewScope.description,
          centerId: prior.graphViewScope.centerId,
          priorState: null,
        },
        cameraState: prior.cameraState ?? null,
        viewMode: prior.viewMode,
        filters: prior.filters || state.filters,
        shareNotice: null,
        selectedNodeId: prior.selectedNodeId,
        extraNodes: prior.extraNodes,
        extraEdges: prior.extraEdges,
        focusedCenterId: prior.graphViewScope.centerId || null,
        rightSidebarOpen: Boolean(prior.selectedNodeId),
        expansionError: null,
      };
    }),

  clearExtraSubgraph: () =>
    set({
      extraNodes: [],
      extraEdges: [],
      focusedCenterId: null,
      graphViewScope: {
        kind: "overview",
        title: `Overview: ${get().viewMode.charAt(0).toUpperCase() + get().viewMode.slice(1)}`,
      },
      expansionError: null,
    }),

  setSearchModalOpen: (searchModalOpen) => set({ searchModalOpen }),
  setPathFinderOpen: (pathFinderOpen) => set({ pathFinderOpen }),
  setCompareModalOpen: (compareModalOpen, leftId, rightId) =>
    set((state) => ({
      compareModalOpen,
      compareLeftId: leftId ?? state.compareLeftId,
      compareRightId: rightId ?? state.compareRightId,
    })),
  setCaveatsModalOpen: (caveatsModalOpen) => set({ caveatsModalOpen }),

  saveCurrentView: (name) => {
    const state = get();
    const spec = makeViewSpec(state);
    const bookmark = {
      id: `custom-${Date.now()}`,
      name: name.trim() || "Saved view",
      viewMode: state.viewMode,
      filters: { ...state.filters },
      selectedNodeId: state.selectedNodeId,
      spec: shareSpec(spec),
    };
    const savedViews = [...state.savedViews, bookmark];
    try {
      localStorage.setItem(
        "scientific-network-views-v2",
        JSON.stringify(savedViews.filter((v) => v.id.startsWith("custom-"))),
      );
    } catch {
      /* storage may be unavailable */
    }
    set({ savedViews, shareNotice: spec.notice || null });
  },
  applySavedView: (bookmark) => {
    const spec = bookmark.spec
      ? validateSpec(bookmark.spec, DEFAULT_FILTERS)
      : validateSpec(
          { version: 2, ...bookmark, scope: { kind: "overview" } },
          DEFAULT_FILTERS,
        );
    if (!spec) return;
    set({
      viewMode: spec.viewMode,
      filters: spec.filters,
      selectedNodeId: spec.selectedNodeId,
      selectedEdgeId: spec.selectedEdgeId,
      rightSidebarOpen: !!(spec.selectedNodeId || spec.selectedEdgeId),
      layoutMode: spec.layoutMode,
      edgeFilterMode: spec.edgeFilterMode,
      graphViewScope: spec.scope,
      extraNodes: [],
      extraEdges: [],
      focusedCenterId: null,
      workspaceTab: spec.workspaceTab,
      analyticsSection: spec.analyticsSection || "robustness",
      analyticsFilters: spec.analyticsFilters || { ...DEFAULT_ANALYTICS_FILTERS },
      insightReturn: false,
      hoveredNodeId: null,
      expansionError: null,
      shareNotice: spec.notice || null,
    });
  },
  hydrateFromUrl: () => {
    if (typeof window === "undefined") return;
    try {
      const stored = JSON.parse(
        localStorage.getItem("scientific-network-views-v2") || localStorage.getItem("scientific-network-views-v1") || "[]",
      );
      if (Array.isArray(stored))
        set((s) => ({
          savedViews: [
            ...s.savedViews.filter((v) => !v.id.startsWith("custom-")),
            ...stored.filter(
              (v) =>
                v &&
                typeof v.name === "string" &&
                validateSpec(v.spec || { version: 2, ...v, scope: { kind: "overview" } }, DEFAULT_FILTERS),
            ),
          ],
        }));
    } catch {
      /* inaccessible storage */
    }
    const sp = new URLSearchParams(window.location.search);
    let spec: ViewSpec | null = null;
    try {
      if (sp.has("view"))
        spec = validateSpec(JSON.parse(sp.get("view")!), DEFAULT_FILTERS);
    } catch {
      /* invalid links use safe overview */
    }
    if (!spec) {
      const legacy: Record<string, unknown> = { ...get().filters };
      for (const [param, key] of Object.entries({
        limit: "limit",
        year_min: "yearMin",
        year_max: "yearMax",
        min_support: "minSupport",
        min_weight: "minWeight",
      }))
        if (sp.has(param)) legacy[key] = Number(sp.get(param));
      for (const [param, key] of Object.entries({
        community: "communityId",
        sector: "sector",
        preset: "preset",
        country: "countryCode",
        venue: "venue",
        topic: "topicId",
      }))
        if (sp.has(param)) legacy[key] = sp.get(param);
      legacy.crossSectorOnly = sp.get("cross_sector") === "1";
      spec = validateSpec(
        {
          version: 2,
          viewMode: sp.get("mode") || get().viewMode,
          workspaceTab: sp.get("tab"),
          filters: legacy,
          layoutMode: sp.get("layout"),
          edgeFilterMode: sp.get("edge_filter"),
          selectedNodeId: sp.get("node"),
          selectedEdgeId: sp.get("edge"),
          scope: {
            kind:
              sp.get("scope") === "ego" && validId(sp.get("center"))
                ? "ego"
                : "overview",
            centerId: sp.get("center"),
          },
          notice:
            sp.get("scope") === "path"
              ? "Legacy path URL has no traversal parameters; showing overview."
              : undefined,
        },
        DEFAULT_FILTERS,
      );
    }
    if (spec)
      set({
        viewMode: spec.viewMode,
        workspaceTab: spec.workspaceTab,
        analyticsSection: spec.analyticsSection || "robustness",
      analyticsFilters: spec.analyticsFilters || { ...DEFAULT_ANALYTICS_FILTERS },
        filters: spec.filters,
        layoutMode: spec.layoutMode,
        edgeFilterMode: spec.edgeFilterMode,
        graphViewScope: spec.scope,
        selectedNodeId: spec.selectedNodeId,
        selectedEdgeId: spec.selectedEdgeId,
        rightSidebarOpen: !!(spec.selectedNodeId || spec.selectedEdgeId),
        extraNodes: [],
        extraEdges: [],
        shareNotice: spec.notice || null,
      });
  },
  buildShareUrl: () => {
    if (typeof window === "undefined") return "";
    const spec = makeViewSpec(get());
    set({ shareNotice: spec.notice || null });
    const sp = new URLSearchParams({
      v: "2",
      view: JSON.stringify(shareSpec(spec)),
    });
    return `${window.location.origin}${window.location.pathname}?${sp}`;
  },
}));
