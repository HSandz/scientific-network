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

export interface SavedViewBookmark {
  id: string;
  name: string;
  viewMode: ViewMode;
  filters: ExplorerFilters;
  selectedNodeId: string | null;
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
  setCameraState: (camera: { x: number; y: number; ratio: number } | null) => void;
  setExpansionError: (err: { message: string; nodeId: string; replace: boolean } | null) => void;
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
    centerId?: string | null
  ) => void;
  enterEgoView: (
    centerNode: GraphNode,
    nodes: GraphNode[],
    edges: GraphEdge[],
    cameraState?: { x: number; y: number; ratio: number } | null
  ) => void;
  enterPathView: (
    path: PathResponse,
    cameraState?: { x: number; y: number; ratio: number } | null
  ) => void;
  restorePriorGraphScope: () => void;
  clearExtraSubgraph: () => void;
  setSearchModalOpen: (open: boolean) => void;
  setPathFinderOpen: (open: boolean) => void;
  setCompareModalOpen: (open: boolean, leftId?: string, rightId?: string) => void;
  setCaveatsModalOpen: (open: boolean) => void;
  saveCurrentView: (name: string) => void;
  applySavedView: (bookmark: SavedViewBookmark) => void;
  hydrateFromUrl: () => void;
  buildShareUrl: () => string;
}

export const useExplorerStore = create<ExplorerState>((set, get) => ({
  darkMode: getInitialDarkMode(),
  workspaceTab: "graph",
  leftSidebarOpen: getInitialLeftSidebarOpen(),
  rightSidebarOpen: false,
  canvasExpanded: false,
  layoutMode: "seeded",
  edgeFilterMode: "all",

  viewMode: "researchers",
  filters: { ...DEFAULT_FILTERS },

  graphViewScope: {
    kind: "overview",
    title: "Overview: Researchers",
  },
  cameraState: null,
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
          window.localStorage.setItem(THEME_STORAGE_KEY, next ? "dark" : "light");
          window.localStorage.setItem("scientific-network-theme", next ? "dark" : "light");
        } catch {
          // ignore storage errors
        }
      }
      return { darkMode: next };
    }),

  setWorkspaceTab: (workspaceTab) =>
    set((state) => ({
      workspaceTab,
      rightSidebarOpen:
        workspaceTab === "graph"
          ? Boolean(state.selectedNodeId || state.selectedEdgeId)
          : false,
      leftSidebarOpen:
        workspaceTab === "graph" &&
        state.leftSidebarOpen &&
        (!Boolean(state.selectedNodeId || state.selectedEdgeId) || canKeepBothDesktopRails()),
    })),
  setLeftSidebarOpen: (leftSidebarOpen) =>
    set((state) => ({
      leftSidebarOpen,
      rightSidebarOpen:
        leftSidebarOpen && !canKeepBothDesktopRails() ? false : state.rightSidebarOpen,
    })),
  setRightSidebarOpen: (rightSidebarOpen) =>
    set((state) => ({
      rightSidebarOpen,
      leftSidebarOpen:
        rightSidebarOpen && !canKeepBothDesktopRails() ? false : state.leftSidebarOpen,
    })),
  setCanvasExpanded: (canvasExpanded) =>
    set((state) => ({
      canvasExpanded,
      leftSidebarOpen: !canvasExpanded && (typeof window === "undefined" || window.innerWidth >= 1024),
      rightSidebarOpen: !canvasExpanded && Boolean(state.selectedNodeId || state.selectedEdgeId),
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
        if (viewMode === "researchers" && !nextSelectedNodeId.startsWith("researcher:")) {
          nextSelectedNodeId = null;
        } else if (viewMode === "organizations" && !nextSelectedNodeId.startsWith("organization:")) {
          nextSelectedNodeId = null;
        } else if (viewMode === "citations" && !nextSelectedNodeId.startsWith("paper:")) {
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
        },
      };
    });
  },

  updateFilters: (partial) =>
    set((state) => ({
      filters: { ...state.filters, ...partial },
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
          (item) => !(item.type === "node" && item.id === nodeId)
        ),
        { type: "node" as const, id: nodeId, label: label || nodeId },
      ].slice(-12);
      return {
        selectedNodeId: nodeId,
        selectedEdgeId: null,
        rightSidebarOpen: true,
        leftSidebarOpen: canKeepBothDesktopRails() ? state.leftSidebarOpen : false,
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
          (item) => !(item.type === "edge" && item.id === edgeId)
        ),
        { type: "edge" as const, id: edgeId, label: label || edgeId },
      ].slice(-12);
      return {
        selectedEdgeId: edgeId,
        selectedNodeId: null,
        rightSidebarOpen: true,
        leftSidebarOpen: canKeepBothDesktopRails() ? state.leftSidebarOpen : false,
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
        extraNodes: Array.from(nodeMap.values()),
        extraEdges: Array.from(edgeMap.values()),
        focusedCenterId: centerId ?? state.focusedCenterId,
      };
    }),

  enterEgoView: (centerNode, nodes, edges, cameraState = null) =>
    set((state) => {
      const prior = {
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
          priorState: state.graphViewScope.kind === "ego" ? state.graphViewScope.priorState : prior,
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
        graphViewScope: {
          kind: "path",
          title: `Path: ${sName} → ${tName}`,
          description: `${pathRes.hop_count} hops, ${pathRes.nodes.length} entities`,
          pathData: {
            sourceId: pathRes.source_id,
            targetId: pathRes.target_id,
            sourceName: sName,
            targetName: tName,
            hopCount: pathRes.hop_count,
            steps: pathRes.step_descriptions || [],
          },
          priorState: state.graphViewScope.kind === "path" ? state.graphViewScope.priorState : prior,
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
        viewMode: prior.viewMode,
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

  saveCurrentView: (name) =>
    set((state) => ({
      savedViews: [
        ...state.savedViews,
        {
          id: `custom-${Date.now()}`,
          name: name.trim() || `Saved View ${state.savedViews.length + 1}`,
          viewMode: state.viewMode,
          filters: { ...state.filters },
          selectedNodeId: state.selectedNodeId,
        },
      ],
    })),

  applySavedView: (bookmark) =>
    set({
      viewMode: bookmark.viewMode,
      filters: { ...bookmark.filters },
      selectedNodeId: bookmark.selectedNodeId,
      selectedEdgeId: null,
      rightSidebarOpen: Boolean(bookmark.selectedNodeId),
      extraNodes: [],
      extraEdges: [],
      focusedCenterId: null,
      graphViewScope: {
        kind: "overview",
        title: `Overview: ${bookmark.viewMode.charAt(0).toUpperCase() + bookmark.viewMode.slice(1)}`,
      },
      workspaceTab: "graph",
      expansionError: null,
    }),

  hydrateFromUrl: () => {
    if (typeof window === "undefined") return;
    const sp = new URLSearchParams(window.location.search);
    const mode = sp.get("mode") as ViewMode | null;
    const tab = sp.get("tab") as WorkspaceTab | null;
    const layout = sp.get("layout");
    const edgeFilter = sp.get("edge_filter");
    const scope = sp.get("scope");
    const center = sp.get("center");
    const node = sp.get("node");
    const edge = sp.get("edge");
    const comm = sp.get("community");
    const sector = sp.get("sector");
    const preset = sp.get("preset");
    const limit = sp.get("limit");
    const minSupport = sp.get("min_support");
    const minWeight = sp.get("min_weight");
    const yearMin = sp.get("year_min");
    const yearMax = sp.get("year_max");
    const crossSector = sp.get("cross_sector");

    set((state) => {
      const nextMode =
        mode && ["researchers", "organizations", "citations", "heterogeneous"].includes(mode)
          ? mode
          : state.viewMode;
      const nextTab =
        tab && ["graph", "table", "analytics"].includes(tab)
          ? tab
          : state.workspaceTab;
      const nextLayout =
        layout && ["seeded", "circular", "concentric"].includes(layout)
          ? (layout as LayoutMode)
          : state.layoutMode;
      const nextFilter =
        edgeFilter && ["all", "strong", "connected"].includes(edgeFilter)
          ? (edgeFilter as EdgeFilterMode)
          : state.edgeFilterMode;
      const nextNode = node || state.selectedNodeId;
      const nextEdge = edge || state.selectedEdgeId;

      const nextScope: GraphViewScope = {
        kind: scope && ["overview", "ego", "path"].includes(scope) ? (scope as any) : state.graphViewScope.kind,
        title:
          scope === "ego" && center
            ? `Ego: ${center}`
            : `Overview: ${nextMode.charAt(0).toUpperCase() + nextMode.slice(1)}`,
        centerId: center ?? state.graphViewScope.centerId,
      };

      return {
        viewMode: nextMode,
        workspaceTab: nextTab,
        layoutMode: nextLayout,
        edgeFilterMode: nextFilter,
        graphViewScope: nextScope,
        selectedNodeId: nextNode,
        selectedEdgeId: nextEdge,
        rightSidebarOpen: Boolean(nextNode || nextEdge) || state.rightSidebarOpen,
        filters: {
          ...state.filters,
          limit: limit ? Math.min(250, Math.max(10, parseInt(limit, 10))) : state.filters.limit,
          communityId: comm ?? state.filters.communityId,
          sector: sector ?? state.filters.sector,
          preset: preset ?? state.filters.preset,
          minSupport: minSupport ? parseInt(minSupport, 10) : state.filters.minSupport,
          minWeight: minWeight ? parseFloat(minWeight) : state.filters.minWeight,
          yearMin: yearMin ? parseInt(yearMin, 10) : state.filters.yearMin,
          yearMax: yearMax ? parseInt(yearMax, 10) : state.filters.yearMax,
          crossSectorOnly: crossSector === "1" ? true : state.filters.crossSectorOnly,
        },
      };
    });
  },

  buildShareUrl: () => {
    if (typeof window === "undefined") return "";
    const state = get();
    const sp = new URLSearchParams();
    sp.set("mode", state.viewMode);
    sp.set("tab", state.workspaceTab);
    sp.set("layout", state.layoutMode);
    sp.set("edge_filter", state.edgeFilterMode);
    sp.set("scope", state.graphViewScope.kind);
    if (state.graphViewScope.centerId) {
      sp.set("center", state.graphViewScope.centerId);
    }
    if (state.selectedNodeId) sp.set("node", state.selectedNodeId);
    if (state.selectedEdgeId) sp.set("edge", state.selectedEdgeId);
    if (state.filters.limit) sp.set("limit", String(state.filters.limit));
    if (state.filters.communityId) sp.set("community", state.filters.communityId);
    if (state.filters.sector) sp.set("sector", state.filters.sector);
    if (state.filters.minSupport > 1) sp.set("min_support", String(state.filters.minSupport));
    if (state.filters.minWeight > 0) sp.set("min_weight", String(state.filters.minWeight));
    if (state.filters.yearMin !== 2021) sp.set("year_min", String(state.filters.yearMin));
    if (state.filters.yearMax !== 2025) sp.set("year_max", String(state.filters.yearMax));
    if (state.filters.crossSectorOnly) sp.set("cross_sector", "1");
    if (state.viewMode === "heterogeneous" && state.filters.preset) {
      sp.set("preset", state.filters.preset);
    }
    return `${window.location.origin}${window.location.pathname}?${sp.toString()}`;
  },
}));
