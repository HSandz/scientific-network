import { create } from "zustand";
import {
  GraphEdge,
  GraphNode,
  NodeLabel,
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

  // Exploration mode & filters
  viewMode: ViewMode;
  filters: ExplorerFilters;

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

  viewMode: "researchers",
  filters: { ...DEFAULT_FILTERS },

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

  setViewMode: (viewMode) => {
    const defaultLimits: Record<ViewMode, number> = {
      researchers: 100,
      organizations: 60,
      citations: 80,
      heterogeneous: 120,
    };
    set((state) => ({
      viewMode,
      extraNodes: [],
      extraEdges: [],
      focusedCenterId: null,
      filters: {
        ...state.filters,
        limit: defaultLimits[viewMode],
        communityId: "",
      },
    }));
  },

  updateFilters: (partial) =>
    set((state) => ({
      filters: { ...state.filters, ...partial },
      extraNodes: [],
      extraEdges: [],
      focusedCenterId: null,
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

  clearExtraSubgraph: () =>
    set({ extraNodes: [], extraEdges: [], focusedCenterId: null }),

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
      workspaceTab: "graph",
    }),

  hydrateFromUrl: () => {
    if (typeof window === "undefined") return;
    const sp = new URLSearchParams(window.location.search);
    const mode = sp.get("mode") as ViewMode | null;
    const tab = sp.get("tab") as WorkspaceTab | null;
    const node = sp.get("node");
    const edge = sp.get("edge");
    const comm = sp.get("community");
    const sector = sp.get("sector");
    const preset = sp.get("preset");

    set((state) => {
      const nextNode = node || state.selectedNodeId;
      const nextEdge = edge || state.selectedEdgeId;
      return {
        viewMode:
          mode && ["researchers", "organizations", "citations", "heterogeneous"].includes(mode)
            ? mode
            : state.viewMode,
        workspaceTab:
          tab && ["graph", "table", "analytics"].includes(tab)
            ? tab
            : state.workspaceTab,
        selectedNodeId: nextNode,
        selectedEdgeId: nextEdge,
        rightSidebarOpen: Boolean(nextNode || nextEdge) || state.rightSidebarOpen,
        filters: {
          ...state.filters,
          communityId: comm ?? state.filters.communityId,
          sector: sector ?? state.filters.sector,
          preset: preset ?? state.filters.preset,
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
    if (state.selectedNodeId) sp.set("node", state.selectedNodeId);
    if (state.selectedEdgeId) sp.set("edge", state.selectedEdgeId);
    if (state.filters.communityId) sp.set("community", state.filters.communityId);
    if (state.filters.sector) sp.set("sector", state.filters.sector);
    if (state.viewMode === "heterogeneous" && state.filters.preset) {
      sp.set("preset", state.filters.preset);
    }
    return `${window.location.origin}${window.location.pathname}?${sp.toString()}`;
  },
}));
