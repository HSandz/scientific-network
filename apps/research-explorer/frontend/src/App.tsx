import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useQuery } from "@tanstack/react-query";
const AnalyticsView = React.lazy(() =>
  import("./components/analytics/AnalyticsView").then((m) => ({
    default: m.AnalyticsView,
  })),
);
import { effectiveSlice } from "./lib/effectiveGraph";
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
    typeof window !== "undefined" ? window.innerWidth : 1440,
  );

  const anyModalOpen =
    searchModalOpen || pathFinderOpen || compareModalOpen || caveatsModalOpen;

  // Development-only instrumentation for correctness/performance regression checks.
  if (import.meta.env.DEV) (window as any).__explorerStore = useExplorerStore;

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
      } else if (
        prevW < 1264 &&
        w >= 1264 &&
        !state.leftSidebarOpen &&
        !state.canvasExpanded
      ) {
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
      const baseNodes =
        viewMode === "heterogeneous" &&
        filters.preset === "custom" &&
        (!filters.nodeLabels.length || !filters.relations.length)
          ? []
          : viewQuery.data?.nodes || [];
      const baseEdges = baseNodes.length ? viewQuery.data?.edges || [] : [];

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

    rawNodes = rawNodes.slice(0, 250);
    return {
      ...effectiveSlice(rawNodes, rawEdges, edgeFilterMode),
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
    filters,
  ]);

  const expansionController = useRef<AbortController | null>(null);
  const requestKey = JSON.stringify([
    viewMode,
    filters,
    edgeFilterMode,
    graphViewScope.kind,
  ]);
  const requestKeyRef = useRef(requestKey);
  requestKeyRef.current = requestKey;
  useEffect(() => {
    expansionController.current?.abort();
    setIsExpanding(false);
  }, [requestKey]);
  useEffect(() => () => expansionController.current?.abort(), []);

  // Expand 1-hop neighborhood of any entity (even outside top-100 illustration)
  const handleExpandNode = useCallback(
    async (nodeId: string, replace = false, exploreAll = false) => {
      expansionController.current?.abort();
      const controller = new AbortController();
      expansionController.current = controller;
      const key = requestKeyRef.current;
      const current = useExplorerStore.getState();
      try {
        setIsExpanding(true);
        setExpansionError(null);
        if (exploreAll) {
          current.setViewMode("heterogeneous");
          current.updateFilters({ preset: "custom" });
          setExpansionError({
            message:
              "Switched to all relationship types. Retry to load this neighborhood in the new scope.",
            nodeId,
            replace,
          });
          return;
        }
        // These filters require paper-specific joins not supplied by the neighbor endpoint.
        // Keep the last graph rather than silently ignoring a user's constraint.
        if (
          current.filters.communityId ||
          current.filters.countryCode ||
          current.filters.topicId ||
          current.filters.crossSectorOnly
        ) {
          setExpansionError({
            message:
              "Expansion is unavailable with community, country, topic or cross-sector constraints. Use the filtered overview or reset those constraints and Retry.",
            nodeId,
            replace,
          });
          return;
        }
        if (
          current.viewMode === "heterogeneous" &&
          current.filters.preset === "custom" &&
          (!current.filters.nodeLabels.length ||
            !current.filters.relations.length)
        ) {
          setExpansionError({
            message:
              "Select at least one label and predicate before expanding.",
            nodeId,
            replace,
          });
          return;
        }
        const params: Record<string, unknown> = {
          limit: 60,
          year_min: current.filters.yearMin,
          year_max: current.filters.yearMax,
          venue: current.filters.venue || undefined,
          sector: current.filters.sector || undefined,
        };
        if (
          current.viewMode === "researchers" ||
          current.viewMode === "organizations"
        ) {
          params.relations = [
            current.viewMode === "researchers"
              ? "COAUTHORED_WITH"
              : "COLLABORATED_WITH",
          ];
          params.node_labels = [
            current.viewMode === "researchers" ? "Researcher" : "Organization",
          ];
          params.min_support = current.filters.minSupport;
          params.min_weight = current.filters.minWeight;
        } else if (current.viewMode === "citations") {
          params.relations = ["CITES"];
          params.node_labels = ["Paper"];
        } else if (current.filters.preset === "custom") {
          params.relations = current.filters.relations;
          params.node_labels = current.filters.nodeLabels;
        }
        const res = await explorerApi.getNodeNeighbors(
          nodeId,
          params,
          controller.signal,
        );
        if (controller.signal.aborted || key !== requestKeyRef.current) return;
        if (replace) {
          const camera = document.querySelector<HTMLElement>(
            '[data-testid="sigma-canvas-container"]',
          )?.dataset.camera;
          enterEgoView(
            res.center_node,
            res.nodes,
            res.edges,
            camera ? JSON.parse(camera) : null,
            params,
          );
        } else {
          mergeSubgraph(res.nodes, res.edges, false, nodeId);
          selectNode(nodeId, res.center_node.name);
        }
      } catch (err) {
        if (controller.signal.aborted || key !== requestKeyRef.current) return;
        setExpansionError({
          message:
            err instanceof Error
              ? err.message
              : "Neighborhood unavailable. Retry.",
          nodeId,
          replace,
        });
      } finally {
        if (expansionController.current === controller) setIsExpanding(false);
      }
    },
    [enterEgoView, mergeSubgraph, selectNode, setExpansionError],
  );

  // A restored scope must fetch its graph, not just restore its heading.
  useEffect(() => {
    if (extraNodes.length) return;
    if (graphViewScope.kind === "ego" && graphViewScope.centerId) {
      void handleExpandNode(graphViewScope.centerId, true);
    }
    if (graphViewScope.kind === "path" && graphViewScope.pathData?.mode) {
      const p = graphViewScope.pathData;
      let active = true;
      explorerApi
        .findPath({
          source_id: p.sourceId,
          target_id: p.targetId,
          mode: p.mode!,
          max_hops: p.maxHops || 4,
        })
        .then((res) => {
          if (!active) return;
          if (res.found) useExplorerStore.getState().enterPathView(res);
          else
            setExpansionError({
              message: "Shared path unavailable under the recorded traversal.",
              nodeId: p.sourceId,
              replace: false,
            });
        })
        .catch((err) => {
          if (active)
            setExpansionError({
              message: String(err),
              nodeId: p.sourceId,
              replace: false,
            });
        });
      return () => {
        active = false;
      };
    }
  }, [
    graphViewScope.kind,
    graphViewScope.centerId,
    graphViewScope.pathData,
    extraNodes.length,
    handleExpandNode,
    setExpansionError,
  ]);

  // Focus an entity in the Graph tab (from Search, Table, or Analytics)
  const handleFocusNodeInGraph = useCallback(
    (nodeId: string, name?: string) => {
      setWorkspaceTab("graph");
      const current = useExplorerStore.getState();
      if (
        nodeId.startsWith("researcher:") &&
        current.viewMode !== "researchers"
      )
        current.setViewMode("researchers");
      if (
        nodeId.startsWith("organization:") &&
        current.viewMode !== "organizations"
      )
        current.setViewMode("organizations");
      selectNode(nodeId, name);
      const alreadyOnCanvas = effectiveGraph.nodes.some((n) => n.id === nodeId);
      if (!alreadyOnCanvas) {
        void handleExpandNode(nodeId, false);
      }
    },
    [setWorkspaceTab, selectNode, effectiveGraph.nodes, handleExpandNode],
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

        {summaryQuery.isError && (
          <p role="alert" className="p-2 text-xs">
            Release metadata unavailable: {String(summaryQuery.error)}{" "}
            <button
              className="underline"
              onClick={() => summaryQuery.refetch()}
            >
              Retry
            </button>
          </p>
        )}
        <div className="flex-1 flex min-h-0 overflow-hidden relative z-0">
          {workspaceTab === "graph" && (
            <LeftSidebar
              summary={summaryQuery.data}
              availableCommunities={viewQuery.data?.available_communities || []}
            />
          )}

          <main className="flex-1 flex flex-col min-w-0 min-h-0 overflow-hidden bg-ground">
            {useExplorerStore.getState().shareNotice && (
              <p role="status" className="p-2 text-xs">
                {useExplorerStore.getState().shareNotice}
              </p>
            )}
            {workspaceTab === "graph" && (
              <div className="px-4 py-2 flex flex-wrap gap-2 text-xs border-b border-border">
                {useExplorerStore.getState().insightReturn && (
                  <button
                    className="underline"
                    onClick={() => setWorkspaceTab("analytics")}
                  >
                    ← Back to finding
                  </button>
                )}
                <span className="text-muted">Explore findings</span>
                {[
                  ["robustness", "Fragile bridges"],
                  ["sectors", "Academia–industry"],
                  ["topics", "Inferred topic trends"],
                ].map(([id, label]) => (
                  <button
                    className="underline underline-offset-2"
                    key={id}
                    onClick={() => {
                      useExplorerStore.setState({ analyticsSection: id });
                      setWorkspaceTab("analytics");
                    }}
                  >
                    {label} →
                  </button>
                ))}
              </div>
            )}
            {workspaceTab === "graph" && (
              <SigmaGraphCanvas
                viewData={viewQuery.data}
                nodes={effectiveGraph.nodes}
                edges={effectiveGraph.edges}
                rawEdgesCount={effectiveGraph.rawEdges.length}
                isLoading={viewQuery.isLoading}
                error={viewQuery.error as Error | null}
                onRetry={() => { void viewQuery.refetch(); }}
                onExpandNode={handleExpandNode}
                isExpanding={isExpanding}
              />
            )}

            {workspaceTab === "table" && (
              <TableView onFocusNodeInGraph={handleFocusNodeInGraph} />
            )}

            {workspaceTab === "analytics" && (
              <React.Suspense
                fallback={<p className="p-5">Loading analytics…</p>}
              >
                <AnalyticsView
                  summary={summaryQuery.data}
                  onFocusNodeInGraph={(id, name) => {
                    const state = useExplorerStore.getState();
                    state.setViewMode(id.startsWith("researcher:") ? "researchers" : id.startsWith("organization:") ? "organizations" : "citations");
                    state.resetFilters();
                    state.setEdgeFilterMode("all");
                    state.setWorkspaceTab("graph");
                    state.selectNode(id, name);
                    void handleExpandNode(id, true);
                  }}
                />
              </React.Suspense>
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
