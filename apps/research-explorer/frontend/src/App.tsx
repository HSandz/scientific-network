import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AnalyticsView } from "./components/analytics/AnalyticsView";
import { LeftSidebar } from "./components/filters/LeftSidebar";
import { SigmaGraphCanvas } from "./components/graph/SigmaGraphCanvas";
import { RightInspector } from "./components/inspector/RightInspector";
import { TopHeader } from "./components/layout/TopHeader";
import { CaveatsModal } from "./components/modals/CaveatsModal";
import { CompareModal } from "./components/modals/CompareModal";
import { PathFinderModal } from "./components/modals/PathFinderModal";
import { SearchCommandModal } from "./components/search/SearchCommandModal";
import { TableView } from "./components/table/TableView";
import { explorerApi } from "./lib/api";
import { useExplorerStore } from "./stores/useExplorerStore";
import { GraphEdge, GraphNode } from "./types/explorer";

export const App: React.FC = () => {
  const {
    darkMode,
    workspaceTab,
    setWorkspaceTab,
    viewMode,
    filters,
    extraNodes,
    extraEdges,
    graphViewScope,
    edgeFilterMode,
    selectedNodeId,
    leftSidebarOpen,
    setLeftSidebarOpen,
    rightSidebarOpen,
    setRightSidebarOpen,
    searchModalOpen,
    pathFinderOpen,
    compareModalOpen,
    caveatsModalOpen,
    selectNode,
    mergeSubgraph,
    enterEgoView,
    setExpansionError,
    hydrateFromUrl,
    setSearchModalOpen,
    setPathFinderOpen,
    setCompareModalOpen,
    setCaveatsModalOpen,
  } = useExplorerStore();

  const [isExpanding, setIsExpanding] = useState(false);
  const workspaceShellRef = useRef<HTMLDivElement>(null);
  const prevViewportWidthRef = useRef<number>(
    typeof window !== "undefined" ? window.innerWidth : 1440
  );

  const anyModalOpen =
    searchModalOpen || pathFinderOpen || compareModalOpen || caveatsModalOpen;

  // Hydrate initial state from URL parameters on mount
  useEffect(() => {
    hydrateFromUrl();
  }, [hydrateFromUrl]);

  // Synchronize dark mode class on root html element
  useEffect(() => {
    document.documentElement.classList.toggle("dark", darkMode);
  }, [darkMode]);

  // Set background workspace shell inert while any modal dialog is open
  useEffect(() => {
    const shell = workspaceShellRef.current;
    if (!shell) return;
    if (anyModalOpen) {
      shell.setAttribute("inert", "");
      shell.setAttribute("aria-hidden", "true");
    } else {
      shell.removeAttribute("inert");
      shell.removeAttribute("aria-hidden");
    }
  }, [anyModalOpen]);

  // Fold static rails cleanly across responsive breakpoint transitions
  useEffect(() => {
    const handleResize = () => {
      const w = window.innerWidth;
      const prevW = prevViewportWidthRef.current;
      prevViewportWidthRef.current = w;

      const state = useExplorerStore.getState();
      // Crossing from desktop (>= 1024) down to tablet/phone (< 1024):
      // fold the desktop filter rail rather than converting it into a blocking overlay drawer
      if (prevW >= 1024 && w < 1024 && state.leftSidebarOpen) {
        state.setLeftSidebarOpen(false);
      } else if (
        w >= 1024 &&
        w < 1264 &&
        state.leftSidebarOpen &&
        state.rightSidebarOpen
      ) {
        // At 1024–1263px, keep >= 600px graph width by folding the filter rail when inspector is open
        state.setLeftSidebarOpen(false);
      } else if (prevW < 1264 && w >= 1264 && !state.leftSidebarOpen && !state.canvasExpanded) {
        // Returning to wide desktop restores the left filter rail
        state.setLeftSidebarOpen(true);
      }
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // Global keyboard shortcuts: `/` or `Cmd/Ctrl+K` opens search; `Escape` closes drawers when no modal is open
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null;
      const isInput =
        target &&
        (target.tagName === "INPUT" ||
          target.tagName === "TEXTAREA" ||
          target.tagName === "SELECT" ||
          target.isContentEditable);

      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setSearchModalOpen(true);
        return;
      }

      if (!anyModalOpen && !isInput && e.key === "/") {
        e.preventDefault();
        setSearchModalOpen(true);
        return;
      }

      if (e.key === "Escape" && !anyModalOpen && !e.defaultPrevented) {
        if (rightSidebarOpen) {
          e.preventDefault();
          setRightSidebarOpen(false);
          return;
        }
        if (leftSidebarOpen && window.innerWidth < 1024) {
          e.preventDefault();
          setLeftSidebarOpen(false);
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [
    anyModalOpen,
    leftSidebarOpen,
    rightSidebarOpen,
    setLeftSidebarOpen,
    setRightSidebarOpen,
    setSearchModalOpen,
  ]);

  const summaryQuery = useQuery({
    queryKey: ["graph-summary"],
    queryFn: () => explorerApi.getSummary(),
    staleTime: 300_000,
  });

  const viewQueryParams = useMemo(() => {
    return {
      limit: filters.limit,
      community_id: filters.communityId || undefined,
      sector: filters.sector || undefined,
      cross_sector_only: filters.crossSectorOnly || undefined,
      country_code: filters.countryCode || undefined,
      year_min: filters.yearMin,
      year_max: filters.yearMax,
      venue: filters.venue || undefined,
      topic_id: filters.topicId || undefined,
      min_support: filters.minSupport,
      min_weight: filters.minWeight,
      include_isolates: filters.includeIsolates || undefined,
      include_topics: filters.includeTopics || undefined,
      preset: viewMode === "heterogeneous" ? filters.preset : undefined,
      node_labels:
        viewMode === "heterogeneous" && filters.preset === "custom"
          ? filters.nodeLabels
          : undefined,
      relations:
        viewMode === "heterogeneous" && filters.preset === "custom"
          ? filters.relations
          : undefined,
    };
  }, [viewMode, filters]);

  const viewQuery = useQuery({
    queryKey: ["view-subgraph", viewMode, viewQueryParams],
    queryFn: ({ signal }) =>
      explorerApi.getViewSubgraph(viewMode, viewQueryParams, signal),
    staleTime: 60_000,
  });

  // Derive authoritative graph slice according to active graph scope & presentation filters
  const effectiveGraph = useMemo(() => {
    let rawNodes: GraphNode[] = [];
    let rawEdges: GraphEdge[] = [];

    if (graphViewScope.kind === "ego" || graphViewScope.kind === "path") {
      // In isolated Ego or dedicated Path view, display only the bounded neighborhood or path steps
      rawNodes = extraNodes;
      rawEdges = extraEdges;
    } else {
      // Overview view: base view subgraph + any appended expansion nodes
      const baseNodes = viewQuery.data?.nodes || [];
      const baseEdges = viewQuery.data?.edges || [];

      if (extraNodes.length === 0 && extraEdges.length === 0) {
        rawNodes = baseNodes;
        rawEdges = baseEdges;
      } else {
        const nodeMap = new Map<string, GraphNode>();
        for (const n of baseNodes) nodeMap.set(n.id, n);
        for (const n of extraNodes) nodeMap.set(n.id, n);

        const edgeMap = new Map<string, GraphEdge>();
        for (const e of baseEdges) edgeMap.set(e.edge_id, e);
        for (const e of extraEdges) edgeMap.set(e.edge_id, e);

        rawNodes = Array.from(nodeMap.values());
        rawEdges = Array.from(edgeMap.values());
      }
    }

    // 2. Presentation Edge Filtering (all vs strong vs connected)
    let effectiveEdges = rawEdges;
    if (edgeFilterMode === "strong") {
      if (viewMode === "citations") {
        // Shared-paper support filter is inapplicable on citation graph
        effectiveEdges = [];
      } else {
        effectiveEdges = rawEdges.filter(
          (e) =>
            (e.support_count ?? 1) >= 2 ||
            (typeof e.fractional_weight === "number" && e.fractional_weight >= 0.45)
        );
      }
    }

    let effectiveNodes = rawNodes;
    if (edgeFilterMode === "connected") {
      const connectedIds = new Set<string>();
      for (const e of effectiveEdges) {
        connectedIds.add(e.source);
        connectedIds.add(e.target);
      }
      effectiveNodes = rawNodes.filter(
        (n) => connectedIds.has(n.id) || n.id === selectedNodeId
      );
    }

    // 3. Compute accurate rendered visible degree & strength metrics from effectiveEdges
    const visibleDegrees = new Map<string, number>();
    const visibleStrengths = new Map<string, number>();
    for (const e of effectiveEdges) {
      visibleDegrees.set(e.source, (visibleDegrees.get(e.source) || 0) + 1);
      visibleDegrees.set(e.target, (visibleDegrees.get(e.target) || 0) + 1);
      const w = e.fractional_weight ?? e.support_count ?? 1;
      visibleStrengths.set(e.source, (visibleStrengths.get(e.source) || 0) + w);
      visibleStrengths.set(e.target, (visibleStrengths.get(e.target) || 0) + w);
    }

    const finalNodes = effectiveNodes.map((n) => ({
      ...n,
      displayed_degree: visibleDegrees.get(n.id) || 0,
      displayed_strength: visibleStrengths.get(n.id) || 0,
    }));

    return {
      nodes: finalNodes,
      edges: effectiveEdges,
      rawNodes,
      rawEdges,
    };
  }, [
    graphViewScope.kind,
    extraNodes,
    extraEdges,
    viewQuery.data,
    edgeFilterMode,
    viewMode,
    selectedNodeId,
  ]);

  // Expand 1-hop neighborhood of any entity (even outside top-100 illustration)
  const handleExpandNode = useCallback(
    async (nodeId: string, replace = false, exploreAll = false) => {
      try {
        setIsExpanding(true);
        setExpansionError(null);

        const params: Record<string, unknown> = {
          limit: 60,
          year_min: filters.yearMin,
          year_max: filters.yearMax,
        };

        if (!exploreAll) {
          if (viewMode === "researchers") {
            params.relations = ["COAUTHORED_WITH"];
            params.node_labels = ["Researcher"];
            if (filters.minSupport > 1) params.min_support = filters.minSupport;
            if (filters.minWeight > 0) params.min_weight = filters.minWeight;
            if (filters.venue) params.venue = filters.venue;
          } else if (viewMode === "organizations") {
            params.relations = ["COLLABORATED_WITH"];
            params.node_labels = ["Organization"];
            if (filters.sector) params.sector = filters.sector;
          } else if (viewMode === "citations") {
            params.relations = ["CITES"];
            params.node_labels = ["Paper"];
          }
        }

        const res = await explorerApi.getNodeNeighbors(nodeId, params as any);
        if (replace) {
          enterEgoView(res.center_node, res.nodes, res.edges);
        } else {
          mergeSubgraph(res.nodes, res.edges, false, nodeId);
          selectNode(nodeId, res.center_node.name);
        }
      } catch (err: any) {
        console.error("Failed to expand neighborhood:", err);
        setExpansionError({
          message: `Failed to load neighborhood for ${nodeId}. Server returned an error.`,
          nodeId,
          replace,
        });
      } finally {
        setIsExpanding(false);
      }
    },
    [
      filters.yearMin,
      filters.yearMax,
      filters.minSupport,
      filters.minWeight,
      filters.venue,
      filters.sector,
      viewMode,
      enterEgoView,
      mergeSubgraph,
      selectNode,
      setExpansionError,
    ]
  );

  // Focus an entity in the Graph tab (from Search, Table, or Analytics)
  const handleFocusNodeInGraph = useCallback(
    (nodeId: string, name?: string) => {
      setWorkspaceTab("graph");
      selectNode(nodeId, name);
      const alreadyOnCanvas = effectiveGraph.nodes.some((n) => n.id === nodeId);
      if (!alreadyOnCanvas) {
        void handleExpandNode(nodeId, false);
      }
    },
    [setWorkspaceTab, selectNode, effectiveGraph.nodes, handleExpandNode]
  );

  return (
    <div className="h-screen w-screen overflow-hidden flex flex-col bg-ground text-ink">
      <div
        ref={workspaceShellRef}
        data-testid="workspace-shell"
        className="flex-1 flex flex-col min-h-0 overflow-hidden"
      >
        <TopHeader
          summary={summaryQuery.data}
          displayedNodes={effectiveGraph.nodes}
          displayedEdges={effectiveGraph.edges}
        />

        <div className="flex-1 flex min-h-0 overflow-hidden relative">
          {workspaceTab === "graph" && (
            <LeftSidebar
              availableCommunities={viewQuery.data?.available_communities || []}
            />
          )}

          <main className="flex-1 flex flex-col min-w-0 min-h-0 overflow-hidden bg-ground">
            {workspaceTab === "graph" && (
              <SigmaGraphCanvas
                viewData={viewQuery.data}
                nodes={effectiveGraph.nodes}
                edges={effectiveGraph.edges}
                rawEdgesCount={effectiveGraph.rawEdges.length}
                isLoading={viewQuery.isLoading}
                error={viewQuery.error as Error | null}
                onExpandNode={handleExpandNode}
                isExpanding={isExpanding}
              />
            )}

            {workspaceTab === "table" && (
              <TableView onFocusNodeInGraph={handleFocusNodeInGraph} />
            )}

            {workspaceTab === "analytics" && (
              <AnalyticsView
                summary={summaryQuery.data}
                onFocusNodeInGraph={handleFocusNodeInGraph}
              />
            )}
          </main>

          <RightInspector
            displayedNodes={effectiveGraph.nodes}
            displayedEdges={effectiveGraph.edges}
            onExpandNode={handleExpandNode}
            isExpanding={isExpanding}
          />
        </div>
      </div>

      {/* Modals */}
      <SearchCommandModal onFocusNodeInGraph={handleFocusNodeInGraph} />
      <PathFinderModal />
      <CompareModal />
      <CaveatsModal summary={summaryQuery.data} />
    </div>
  );
};
