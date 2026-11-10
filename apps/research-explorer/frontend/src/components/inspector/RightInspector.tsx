import React, { useState, useEffect, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Share2,
  CircleDot,
  Route,
  GitCompare,
  ExternalLink,
  Copy,
  Check,
  ShieldCheck,
  FileText,
  ArrowLeft,
  ArrowRight,
  AlertTriangle,
  Loader2,
  Info,
  X,
  ChevronRight,
  Search,
} from "lucide-react";
import { explorerApi } from "../../lib/api";
import { LABEL_COLORS, PREDICATE_R_CODE, getNodeColor } from "../../lib/colors";
import { useExplorerStore } from "../../stores/useExplorerStore";
import { EvidenceKind, GraphEdge, GraphNode, NodeDetailResponse } from "../../types/explorer";

interface RightInspectorProps {
  displayedNodes: GraphNode[];
  displayedEdges: GraphEdge[];
  onExpandNode: (nodeId: string, replace?: boolean, exploreAll?: boolean) => void;
  isExpanding: boolean;
}

const EVIDENCE_PILL_STYLE: Record<
  EvidenceKind,
  { label: string; pillClass: string }
> = {
  observed: {
    label: "Observed (R1–R4)",
    pillClass: "ledger-pill ledger-pill-pos",
  },
  inferred_topic: {
    label: "Inferred topic (R5)",
    pillClass: "ledger-pill ledger-pill-warn",
  },
  curated_taxonomy: {
    label: "Curated taxonomy (R6)",
    pillClass: "ledger-pill",
  },
  derived: {
    label: "Derived (R7–R10)",
    pillClass: "ledger-pill",
  },
};

function buildPrimaryFactSummary(detail: NodeDetailResponse): string {
  const { node, relation_counts, total_degree } = detail;
  const rc = relation_counts || {};
  if (node.label === "Researcher") {
    const papers = rc.AUTHORED || 0;
    const coauthors = rc.COAUTHORED_WITH || 0;
    const orgs = rc.AFFILIATED_WITH || 0;
    return `Authored ${papers.toLocaleString()} core paper${papers === 1 ? "" : "s"} with ${coauthors.toLocaleString()} resolved coauthor${coauthors === 1 ? "" : "s"} and ${orgs.toLocaleString()} aligned institution${orgs === 1 ? "" : "s"}.`;
  }
  if (node.label === "Organization") {
    const researchers = rc.AFFILIATED_WITH || 0;
    const partners = rc.COLLABORATED_WITH || 0;
    const sec = node.sector ? `${node.sector} institution` : "Institution";
    const cc = node.country_code ? ` (${node.country_code})` : "";
    return `${sec}${cc} with ${researchers.toLocaleString()} affiliated researchers and ${partners.toLocaleString()} cross-institution collaboration edges.`;
  }
  if (node.label === "Paper") {
    const authors = rc.AUTHORED || 0;
    const cites = rc.CITES || 0;
    const topics = rc.HAS_TOPIC || 0;
    const yr = node.year ? `${node.year} ` : "";
    return `${yr}proceedings paper with ${authors} resolved byline author${authors === 1 ? "" : "s"}, ${cites} within-corpus citation links, and ${topics} topic assignment${topics === 1 ? "" : "s"}.`;
  }
  if (node.label === "Topic") {
    const papers = rc.HAS_TOPIC || 0;
    const res = rc.RESEARCHES_TOPIC || 0;
    return `Taxonomy concept assigned to ${papers.toLocaleString()} core papers and ${res.toLocaleString()} researcher topic profiles.`;
  }
  return `Conference series with ${total_degree.toLocaleString()} incident publication records (2021–2025).`;
}

export const RightInspector: React.FC<RightInspectorProps> = ({
  displayedNodes,
  displayedEdges,
  onExpandNode,
  isExpanding,
}) => {
  const {
    rightSidebarOpen,
    setRightSidebarOpen,
    selectedNodeId,
    selectedEdgeId,
    selectNode,
    selectEdge,
    clearSelection,
    setHoveredNodeId,
    selectionHistory,
    goBackSelection,
    setPathFinderOpen,
    setCompareModalOpen,
    updateFilters,
    setViewMode,
    setWorkspaceTab,
    viewMode,
  } = useExplorerStore();

  const [copiedId, setCopiedId] = useState(false);
  const [visibleFilter, setVisibleFilter] = useState("");

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        if (selectedEdgeId) {
          selectEdge(null);
        } else if (rightSidebarOpen) {
          setRightSidebarOpen(false);
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [rightSidebarOpen, selectedEdgeId, selectEdge, setRightSidebarOpen]);

  const nodeQuery = useQuery({
    queryKey: ["node-detail", selectedNodeId],
    queryFn: ({ signal }) =>
      explorerApi.getNodeDetail(selectedNodeId!, signal),
    enabled: Boolean(selectedNodeId),
  });

  const edgeEvidenceQuery = useQuery({
    queryKey: ["edge-evidence", selectedEdgeId],
    queryFn: ({ signal }) =>
      explorerApi.getEdgeEvidence(selectedEdgeId!, signal),
    enabled: Boolean(selectedEdgeId),
  });

  // Calculate authoritative visible metrics from displayedEdges
  const incidentEdges = useMemo(() => {
    if (!selectedNodeId) return [];
    return displayedEdges.filter(
      (e: GraphEdge) => e.source === selectedNodeId || e.target === selectedNodeId
    );
  }, [selectedNodeId, displayedEdges]);

  const visibleDegree = incidentEdges.length;
  const visibleStrength = incidentEdges.reduce(
    (sum: number, e: GraphEdge) => sum + (e.fractional_weight ?? e.support_count ?? 1),
    0
  );

  const visibleNeighborsList = useMemo(() => {
    if (!selectedNodeId) return [];
    const nodeMap = new Map<string, GraphNode>();
    for (const n of displayedNodes) nodeMap.set(n.id, n);

    const map = new Map<
      string,
      { neighborNode: GraphNode; edges: GraphEdge[] }
    >();

    for (const e of incidentEdges) {
      const otherId = e.source === selectedNodeId ? e.target : e.source;
      const otherNode = nodeMap.get(otherId);
      if (!otherNode) continue;
      if (!map.has(otherId)) {
        map.set(otherId, { neighborNode: otherNode, edges: [] });
      }
      map.get(otherId)!.edges.push(e);
    }

    return Array.from(map.values()).sort(
      (a, b) => (b.neighborNode.score || 0) - (a.neighborNode.score || 0)
    );
  }, [selectedNodeId, incidentEdges, displayedNodes]);

  const filteredVisibleNeighbors = useMemo(() => {
    if (!visibleFilter.trim()) return visibleNeighborsList;
    const q = visibleFilter.toLowerCase();
    return visibleNeighborsList.filter(
      ({ neighborNode }: { neighborNode: GraphNode; edges: GraphEdge[] }) =>
        neighborNode.name.toLowerCase().includes(q) ||
        neighborNode.id.toLowerCase().includes(q) ||
        neighborNode.label.toLowerCase().includes(q)
    );
  }, [visibleNeighborsList, visibleFilter]);

  if (!rightSidebarOpen) return null;

  const displayedNodeObj = displayedNodes.find((n) => n.id === selectedNodeId);

  const handleCopy = (text: string) => {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(text).catch(() => {});
    }
    setCopiedId(true);
    setTimeout(() => setCopiedId(false), 1800);
  };

  return (
    <>
      {/* Backdrop on tablet and phone (< 1024px) */}
      <div
        className="absolute inset-0 bg-black/50 z-30 lg:hidden"
        onClick={() => setRightSidebarOpen(false)}
        aria-hidden="true"
      />

      <aside
        data-testid="right-inspector"
        role={typeof window !== "undefined" && window.innerWidth < 1024 ? "dialog" : undefined}
        aria-modal={typeof window !== "undefined" && window.innerWidth < 1024 ? "true" : undefined}
        aria-label="Entity and relationship evidence inspector"
        className="absolute inset-y-0 right-0 z-40 w-[400px] max-w-[100vw] lg:static lg:w-[392px] border-l border-border bg-surface flex flex-col h-full shrink-0 overflow-y-auto"
      >
        {/* Top Navigation & Return Bar */}
        <div className="px-4 sm:px-5 py-2.5 lg:py-3 border-b border-border flex items-center justify-between bg-surface sticky top-0 z-10">
          <div className="flex items-center gap-2 min-w-0">
            <button
              type="button"
              onClick={() => setRightSidebarOpen(false)}
              data-testid="inspector-mobile-back"
              className="inline-flex lg:hidden items-center gap-1.5 min-h-[44px] px-3 rounded-[6px] border border-border bg-ground hover:bg-raised text-[13px] font-medium text-ink"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Return to workspace</span>
            </button>
            {selectionHistory.length > 1 && (
              <button
                type="button"
                onClick={goBackSelection}
                data-testid="inspector-back-button"
                title="Return to previous selection"
                className="inline-flex items-center justify-center min-w-[44px] min-h-[44px] lg:min-w-0 lg:min-h-0 lg:w-7 lg:h-7 rounded-[6px] lg:rounded-[5px] border border-border bg-ground hover:bg-raised text-muted hover:text-ink"
              >
                <ArrowLeft className="w-4 h-4 lg:w-3.5 lg:h-3.5" />
              </button>
            )}
            <span className="hidden lg:inline text-[13px] font-medium text-muted truncate">
              {selectedEdgeId
                ? "Relationship provenance (Mode E)"
                : selectedNodeId
                ? "Entity dossier & connections"
                : "Details"}
            </span>
          </div>

          <div className="flex items-center gap-1.5 shrink-0">
            <button
              type="button"
              onClick={() => clearSelection()}
              data-testid="close-right-inspector"
              aria-label="Close inspector"
              className="ledger-btn min-h-[44px] lg:min-h-0 lg:h-7 px-3 lg:px-2.5 text-[13px]"
            >
              <X className="w-4 h-4 lg:w-3.5 lg:h-3.5" />
              <span>Close</span>
            </button>
          </div>
        </div>

        {/* Empty State if opened manually without selection */}
        {!selectedNodeId && !selectedEdgeId && (
          <div
            data-testid="inspector-empty-state"
            className="p-6 flex-1 flex flex-col items-center justify-center text-center space-y-2"
          >
            <h2 className="text-sm font-semibold text-ink">
              No entity or relationship selected
            </h2>
            <p className="text-xs text-muted leading-relaxed max-w-xs">
              Select a node on the canvas, search for any of the 47,875 entities, or click an edge to inspect its supporting core papers and affiliation observations.
            </p>
          </div>
        )}

        {/* ========================================================= */}
        {/* NODE INSPECTOR VIEW                                       */}
        {/* ========================================================= */}
        {selectedNodeId && (
          <div className="px-5 py-4 space-y-5">
            {nodeQuery.isLoading && (
              <div className="py-12 flex flex-col items-center justify-center gap-2">
                <Loader2 className="w-5 h-5 text-ink animate-spin" />
                <span className="text-xs text-muted">
                  Loading entity dossier & connections...
                </span>
              </div>
            )}

            {nodeQuery.error && (
              <div className="p-3.5 rounded-[8px] bg-[var(--pill-negative-bg)] text-xs text-[var(--pill-negative-ink)]">
                {(nodeQuery.error as Error).message}
              </div>
            )}

            {nodeQuery.data && (
              <>
                {/* 1. Identity & Primary Supported Fact */}
                <section className="space-y-2.5">
                  <div className="flex items-center justify-between gap-2 flex-wrap">
                    <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-[5px] bg-raised border border-border text-xs font-medium text-ink">
                      <span
                        className="w-2 h-2 rounded-full"
                        style={{
                          backgroundColor:
                            LABEL_COLORS[nodeQuery.data.node.label] || "#6e7681",
                        }}
                      />
                      <span>{nodeQuery.data.node.label}</span>
                    </span>

                    <div className="flex items-center gap-2 text-xs text-muted">
                      {nodeQuery.data.node.year && (
                        <span className="tabular-nums">
                          Edition {nodeQuery.data.node.year}
                        </span>
                      )}
                      {nodeQuery.data.node.sector && (
                        <span className="capitalize px-2 py-0.5 rounded bg-raised text-ink font-medium">
                          {nodeQuery.data.node.sector}
                        </span>
                      )}
                    </div>
                  </div>

                  <h2
                    data-testid="inspector-node-name"
                    className="text-base font-semibold text-ink leading-snug"
                  >
                    {nodeQuery.data.node.name}
                  </h2>

                  <p className="text-xs text-muted leading-relaxed">
                    {buildPrimaryFactSummary(nodeQuery.data)}
                  </p>

                  {/* Primary Exploration Actions */}
                  <div className="grid grid-cols-2 gap-2 pt-1">
                    <button
                      type="button"
                      disabled={isExpanding}
                      onClick={() => {
                        setWorkspaceTab("graph");
                        onExpandNode(nodeQuery.data.node.id, false);
                      }}
                      data-testid="inspector-expand-neighbors"
                      className="ledger-btn ledger-btn-primary h-[32px] text-xs"
                      title="Expand 1 hop within active network projection"
                    >
                      <Share2 className="w-3.5 h-3.5" />
                      <span>Expand +1 hop</span>
                    </button>

                    <button
                      type="button"
                      disabled={isExpanding}
                      onClick={() => {
                        setWorkspaceTab("graph");
                        onExpandNode(nodeQuery.data.node.id, true);
                      }}
                      data-testid="inspector-isolate-ego"
                      className="ledger-btn h-[32px] text-xs"
                      title="Isolate bounded 1-hop ego network and replace overview"
                    >
                      <CircleDot className="w-3.5 h-3.5 text-muted" />
                      <span>Focus ego view</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => setPathFinderOpen(true)}
                      className="ledger-btn h-[32px] text-xs"
                    >
                      <Route className="w-3.5 h-3.5 text-muted" />
                      <span>Find path</span>
                    </button>

                    <button
                      type="button"
                      onClick={() =>
                        setCompareModalOpen(true, nodeQuery.data.node.id)
                      }
                      className="ledger-btn h-[32px] text-xs"
                    >
                      <GitCompare className="w-3.5 h-3.5 text-muted" />
                      <span>Compare</span>
                    </button>

                    {viewMode !== "heterogeneous" && (
                      <button
                        type="button"
                        disabled={isExpanding}
                        onClick={() => {
                          setViewMode("heterogeneous");
                          setWorkspaceTab("graph");
                          onExpandNode(nodeQuery.data.node.id, false, true);
                        }}
                        data-testid="inspector-explore-all-relations"
                        className="col-span-2 ledger-btn h-[28px] text-[11px] text-muted hover:text-ink"
                        title="Switch to heterogeneous knowledge graph to explore all 10 relationship types"
                      >
                        <span>Explore all relationship types (switch to heterogeneous)</span>
                      </button>
                    )}
                  </div>
                </section>

                {/* 2. Overview: Full-Projection vs Subgraph Metrics */}
                <section className="p-3.5 rounded-[8px] bg-ground border border-border space-y-2.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-medium text-ink">
                      Overview & centrality metrics
                    </span>
                    <span className="font-mono text-faint">
                      {nodeQuery.data.node.full_metrics?.projection || "release-v4"}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="p-2.5 rounded-[6px] bg-surface border border-border">
                      <div className="text-muted">Full-projection score</div>
                      <div className="mt-0.5 text-sm font-semibold text-ink tabular-nums">
                        {nodeQuery.data.node.score.toFixed(3)}
                      </div>
                    </div>
                    <div className="p-2.5 rounded-[6px] bg-surface border border-border">
                      <div className="text-muted">Total DB incident edges</div>
                      <div className="mt-0.5 text-sm font-semibold text-ink tabular-nums">
                        {nodeQuery.data.total_degree.toLocaleString()}
                      </div>
                    </div>

                    {nodeQuery.data.node.full_metrics?.betweenness !== undefined &&
                      nodeQuery.data.node.full_metrics?.betweenness !== null && (
                        <div className="p-2.5 rounded-[6px] bg-surface border border-border">
                          <div className="text-muted">Full betweenness</div>
                          <div className="mt-0.5 font-medium text-ink tabular-nums">
                            {nodeQuery.data.node.full_metrics.betweenness.toFixed(5)}
                          </div>
                        </div>
                      )}

                    {nodeQuery.data.node.full_metrics?.pagerank !== undefined &&
                      nodeQuery.data.node.full_metrics?.pagerank !== null && (
                        <div className="p-2.5 rounded-[6px] bg-surface border border-border">
                          <div className="text-muted">Full PageRank</div>
                          <div className="mt-0.5 font-medium text-ink tabular-nums">
                            {nodeQuery.data.node.full_metrics.pagerank.toFixed(6)}
                          </div>
                        </div>
                      )}
                  </div>

                  <div className="pt-2 border-t border-border flex items-center justify-between text-xs">
                    <span className="text-muted">Displayed subgraph degree</span>
                    <span
                      data-testid="inspector-displayed-degree"
                      className="font-medium text-ink tabular-nums"
                    >
                      {visibleDegree} visible edges (weight {visibleStrength.toFixed(2)})
                    </span>
                  </div>

                  {nodeQuery.data.node.full_metrics?.community_id && (
                    <div className="pt-2 border-t border-border flex items-center justify-between text-xs">
                      <span className="text-muted">Louvain community</span>
                      <button
                        type="button"
                        onClick={() => {
                          const cid =
                            nodeQuery.data.node.full_metrics?.community_id || "";
                          setViewMode(
                            nodeQuery.data.node.label === "Organization"
                              ? "organizations"
                              : "researchers"
                          );
                          updateFilters({ communityId: cid });
                          setWorkspaceTab("graph");
                        }}
                        className="font-mono text-xs text-ink underline underline-offset-2 hover:text-accent tabular-nums"
                      >
                        {nodeQuery.data.node.full_metrics.community_id} (
                        {nodeQuery.data.node.full_metrics.community_size} members)
                      </button>
                    </div>
                  )}
                </section>

                {/* Topic Definition if Topic node */}
                {nodeQuery.data.node.label === "Topic" &&
                  Boolean(nodeQuery.data.node.properties.definition) && (
                    <section className="p-3.5 rounded-[8px] bg-ground border border-border text-xs space-y-1">
                      <div className="font-medium text-ink">
                        Taxonomy definition ({String(nodeQuery.data.node.properties.level)})
                      </div>
                      <p className="text-muted leading-relaxed">
                        {String(nodeQuery.data.node.properties.definition)}
                      </p>
                    </section>
                  )}

                {/* Organization Topic Portfolio (R10) */}
                {nodeQuery.data.topic_portfolio.length > 0 && (
                  <section className="space-y-2">
                    <div className="text-xs font-medium text-ink">
                      Topic portfolio (R10 CONTRIBUTES_TO_TOPIC)
                    </div>
                    <div className="rounded-[8px] border border-border divide-y divide-rule bg-surface">
                      {nodeQuery.data.topic_portfolio.slice(0, 6).map((tp) => (
                        <div
                          key={tp.topic_id}
                          className="px-3 py-2 flex items-center justify-between gap-2 text-xs"
                        >
                          <button
                            type="button"
                            onClick={() => selectNode(tp.topic_id, tp.topic)}
                            className="font-medium text-ink hover:underline text-left truncate"
                          >
                            {tp.topic}
                          </button>
                          <span className="text-muted tabular-nums shrink-0">
                            {tp.supported_paper_count} papers (
                            {(tp.fractional_topic_portfolio_share * 100).toFixed(1)}
                            %)
                          </span>
                        </div>
                      ))}
                    </div>
                  </section>
                )}

                {/* On This Graph (Visible Neighbors & Incident Edges) */}
                <section className="space-y-2.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-medium text-ink">
                      On this graph ({visibleNeighborsList.length} visible{" "}
                      {visibleNeighborsList.length === 1 ? "neighbor" : "neighbors"})
                    </span>
                    <span className="text-muted text-[11px] tabular-nums">
                      {visibleDegree} visible {visibleDegree === 1 ? "edge" : "edges"}
                    </span>
                  </div>

                  {visibleNeighborsList.length > 5 && (
                    <div className="relative">
                      <Search className="w-3.5 h-3.5 text-faint absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                      <input
                        type="text"
                        value={visibleFilter}
                        onChange={(e) => setVisibleFilter(e.target.value)}
                        placeholder="Filter visible neighbors by name or ID..."
                        className="w-full h-7 pl-8 pr-2.5 text-xs rounded-[5px] bg-ground border border-border text-ink placeholder:text-faint focus:outline-none focus:border-accent"
                      />
                      {visibleFilter && (
                        <button
                          type="button"
                          onClick={() => setVisibleFilter("")}
                          className="absolute right-2 top-1/2 -translate-y-1/2 text-faint hover:text-ink text-xs"
                        >
                          ×
                        </button>
                      )}
                    </div>
                  )}

                  {visibleNeighborsList.length === 0 ? (
                    <div className="p-3 rounded-[8px] bg-ground border border-border text-xs text-muted">
                      No visible neighbors on current canvas under active filters.
                    </div>
                  ) : filteredVisibleNeighbors.length === 0 ? (
                    <div className="p-3 rounded-[8px] bg-ground border border-border text-xs text-muted">
                      No visible neighbors match &ldquo;{visibleFilter}&rdquo;.
                    </div>
                  ) : (
                    <div className="rounded-[8px] border border-border bg-surface divide-y divide-rule max-h-72 overflow-y-auto">
                      {filteredVisibleNeighbors.map(({ neighborNode, edges }: { neighborNode: GraphNode; edges: GraphEdge[] }) => {
                        const labelColor = LABEL_COLORS[neighborNode.label] || "#7fa6cc";
                        return (
                          <div
                            key={neighborNode.id}
                            onMouseEnter={() => setHoveredNodeId(neighborNode.id)}
                            onMouseLeave={() => setHoveredNodeId(null)}
                            onFocus={() => setHoveredNodeId(neighborNode.id)}
                            onBlur={() => setHoveredNodeId(null)}
                            className="p-2.5 space-y-1.5 hover:bg-raised/60 text-xs transition-colors"
                          >
                            <div className="flex items-start justify-between gap-2">
                              <div className="min-w-0 flex-1">
                                <button
                                  type="button"
                                  onClick={() => selectNode(neighborNode.id, neighborNode.name)}
                                  className="font-medium text-ink hover:underline text-left truncate block w-full"
                                  title={`${neighborNode.name} (${neighborNode.id})`}
                                >
                                  {neighborNode.name}
                                </button>
                                <div className="flex items-center gap-1.5 text-[11px] text-muted font-mono truncate">
                                  <span
                                    className="w-2 h-2 rounded-full shrink-0"
                                    style={{ backgroundColor: labelColor }}
                                    title={neighborNode.label}
                                  />
                                  <span>{neighborNode.label}</span>
                                  <span className="text-faint truncate">· {neighborNode.id}</span>
                                </div>
                              </div>
                              <button
                                type="button"
                                onClick={() => selectNode(neighborNode.id, neighborNode.name)}
                                className="ledger-btn h-6 px-2 text-[11px] shrink-0"
                                title="Center and inspect this entity"
                              >
                                Select
                              </button>
                            </div>

                            {/* Edges connecting selectedNodeId and this neighbor */}
                            <div className="pl-3.5 border-l-2 border-border/70 space-y-1 pt-0.5">
                              {edges.map((e: GraphEdge) => {
                                const rCode = PREDICATE_R_CODE[e.relation] || e.relation;
                                const dirSymbol = e.symmetric || !e.directed
                                  ? "↔"
                                  : e.source === selectedNodeId
                                  ? "→"
                                  : "←";
                                return (
                                  <div
                                    key={e.edge_id}
                                    className="flex items-center justify-between gap-2 text-[11px]"
                                  >
                                    <div className="flex items-center gap-1 min-w-0 text-muted">
                                      <span className="font-mono font-medium text-ink">
                                        {dirSymbol}
                                      </span>
                                      <span className="font-mono text-faint">
                                        {rCode}
                                      </span>
                                      <span className="truncate" title={e.relation}>
                                        {e.relation}
                                      </span>
                                      {e.support_count > 1 && (
                                        <span className="tabular-nums text-faint shrink-0">
                                          ({e.support_count} {e.relation === "CITES" ? "citations" : "papers"})
                                        </span>
                                      )}
                                      {typeof e.fractional_weight === "number" && (
                                        <span className="tabular-nums text-faint shrink-0">
                                          (wt {e.fractional_weight.toFixed(2)})
                                        </span>
                                      )}
                                    </div>
                                    <button
                                      type="button"
                                      data-testid={`inspect-visible-edge-${e.edge_id}`}
                                      onClick={() =>
                                        selectEdge(
                                          e.edge_id,
                                          `${e.relation}: ${neighborNode.name}`
                                        )
                                      }
                                      className="font-mono text-[10px] text-accent hover:underline shrink-0"
                                      title="Inspect relationship evidence"
                                    >
                                      Evidence
                                    </button>
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </section>

                {/* 3. All database connections by Predicate */}
                <section className="space-y-2.5">
                  <div className="flex items-start justify-between gap-2 text-xs">
                    <div>
                      <span className="font-medium text-ink">
                        All database connections ({nodeQuery.data.total_degree.toLocaleString()} total)
                      </span>
                      <p className="text-[11px] text-muted">
                        Stored across all projections and filters. Showing top {nodeQuery.data.connected_groups.reduce((acc, g) => acc + g.items.length, 0)} results.
                      </p>
                    </div>
                    <span className="text-faint text-[11px] shrink-0">Click Evidence to trace</span>
                  </div>

                  {nodeQuery.data.connected_groups.map((grp) => {
                    const rCode =
                      PREDICATE_R_CODE[grp.relation] || grp.relation;
                    return (
                      <div
                        key={`${grp.relation}-${grp.direction}`}
                        className="rounded-[8px] border border-border bg-surface overflow-hidden"
                      >
                        <div className="px-3 py-2 bg-ground border-b border-border flex items-center justify-between gap-2 text-xs">
                          <div className="flex items-center gap-1.5 min-w-0">
                            <span className="font-mono text-faint">{rCode}</span>
                            <span className="font-mono font-medium text-ink truncate">
                              {grp.relation}
                            </span>
                            <span className="text-muted">({grp.direction})</span>
                          </div>
                          <span className="px-2 py-0.5 rounded bg-raised text-ink font-medium tabular-nums shrink-0">
                            {grp.total_count.toLocaleString()}
                          </span>
                        </div>

                        <div className="divide-y divide-rule max-h-56 overflow-y-auto">
                          {grp.items.map((item) => (
                            <div
                              key={item.edge_id}
                              className="px-3 py-2 flex items-center justify-between gap-2 hover:bg-raised/60 text-xs transition-colors"
                            >
                              <div className="min-w-0 flex-1">
                                <button
                                  type="button"
                                  onClick={() =>
                                    selectNode(
                                      item.neighbor_id,
                                      item.neighbor_name
                                    )
                                  }
                                  className="font-medium text-ink hover:underline text-left truncate block w-full"
                                >
                                  {item.neighbor_name}
                                </button>
                                <div className="flex items-center gap-1.5 text-xs text-muted tabular-nums">
                                  <span>{item.neighbor_label}</span>
                                  {item.year && <span>· {item.year}</span>}
                                  {item.support_count > 1 && (
                                    <span>· {item.support_count} papers</span>
                                  )}
                                  {typeof item.fractional_weight === "number" && (
                                    <span>
                                      · weight {item.fractional_weight.toFixed(2)}
                                    </span>
                                  )}
                                </div>
                              </div>

                              <button
                                type="button"
                                data-testid={`inspect-edge-${item.edge_id}`}
                                onClick={() =>
                                  selectEdge(
                                    item.edge_id,
                                    `${grp.relation}: ${item.neighbor_name}`
                                  )
                                }
                                title="Inspect relationship evidence (Mode E)"
                                className="ledger-btn h-7 px-2.5 text-xs shrink-0"
                              >
                                Evidence
                              </button>
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </section>

                {/* 4. Evidence & Provenance: Affiliation Triples, External Links, Progressive Disclosure */}
                {nodeQuery.data.affiliation_observations.length > 0 && (
                  <section className="space-y-2">
                    <div className="text-xs font-medium text-ink">
                      Authorship-aligned affiliation observations (
                      {nodeQuery.data.affiliation_observations.length})
                    </div>
                    <div className="rounded-[8px] border border-border divide-y divide-rule bg-surface max-h-48 overflow-y-auto">
                      {nodeQuery.data.affiliation_observations.map((obs, idx) => {
                        const rawStrings = Array.isArray(obs.raw_affiliation_strings)
                          ? (obs.raw_affiliation_strings as string[])
                          : [];
                        return (
                          <div
                            key={String(obs.id || idx)}
                            className="p-2.5 text-xs space-y-1"
                          >
                            <div className="font-medium text-ink">
                              {String(obs.organization_name || obs.organization_id || "")}
                            </div>
                            <div className="text-muted truncate">
                              Paper ({String(obs.paper_year || "2021–2025")}):{" "}
                              {String(obs.paper_title || obs.paper_id || "")}
                            </div>
                            {rawStrings.length > 0 && (
                              <div className="text-faint truncate">
                                Raw string: “{rawStrings[0]}”
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </section>
                )}

                {nodeQuery.data.external_links.length > 0 && (
                  <section className="space-y-1.5">
                    <div className="text-xs font-medium text-ink">
                      External source records
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {nodeQuery.data.external_links.map((link) => (
                        <a
                          key={link.url}
                          href={link.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="ledger-btn h-7 px-2.5 text-xs"
                        >
                          <span>{link.label}</span>
                          <ExternalLink className="w-3 h-3 text-muted" />
                        </a>
                      ))}
                    </div>
                  </section>
                )}

                {/* Progressive Disclosure for Stable ID & Technical Metadata */}
                <details
                  className="group rounded-[8px] border border-border bg-ground px-3.5 py-2.5"
                  open
                >
                  <summary className="flex items-center justify-between cursor-pointer list-none text-xs font-medium text-muted hover:text-ink">
                    <span>Identifiers & methodological scope</span>
                    <ChevronRight className="w-3.5 h-3.5 transition-transform group-open:rotate-90" />
                  </summary>
                  <div className="mt-2.5 space-y-2.5 text-xs">
                    <div className="flex items-center justify-between gap-2 bg-surface px-2.5 py-1.5 rounded-[5px] border border-border">
                      <code
                        data-testid="inspector-node-id"
                        className="font-mono text-xs text-ink truncate"
                      >
                        {nodeQuery.data.node.id}
                      </code>
                      <button
                        type="button"
                        onClick={() => handleCopy(nodeQuery.data.node.id)}
                        title="Copy stable entity ID"
                        className="text-muted hover:text-ink shrink-0"
                      >
                        {copiedId ? (
                          <Check className="w-3.5 h-3.5 text-[var(--positive)]" />
                        ) : (
                          <Copy className="w-3.5 h-3.5" />
                        )}
                      </button>
                    </div>

                    {nodeQuery.data.scientific_notes.map((note, idx) => (
                      <p key={idx} className="text-muted leading-relaxed">
                        • {note}
                      </p>
                    ))}
                  </div>
                </details>
              </>
            )}
          </div>
        )}

        {/* ========================================================= */}
        {/* EDGE & EVIDENCE INSPECTOR VIEW (MODE E)                   */}
        {/* ========================================================= */}
        {selectedEdgeId && (
          <div
            data-testid="edge-evidence-panel"
            className="px-5 py-4 space-y-4"
          >
            {edgeEvidenceQuery.isLoading && (
              <div className="py-12 flex flex-col items-center justify-center gap-2">
                <Loader2 className="w-5 h-5 text-ink animate-spin" />
                <span className="text-xs text-muted">
                  Resolving relationship provenance & supporting papers...
                </span>
              </div>
            )}

            {edgeEvidenceQuery.error && (
              <div className="p-3.5 rounded-[8px] bg-[var(--pill-negative-bg)] text-xs text-[var(--pill-negative-ink)]">
                {(edgeEvidenceQuery.error as Error).message}
              </div>
            )}

            {edgeEvidenceQuery.data && (
              <>
                {/* 1. Predicate & Evidence Class Identity */}
                <section className="space-y-3">
                  <div className="flex items-center justify-between gap-2 flex-wrap">
                    <span
                      data-testid="evidence-predicate-badge"
                      className="px-2.5 py-1 rounded-[5px] font-mono text-xs font-semibold bg-raised border border-control text-ink"
                    >
                      {PREDICATE_R_CODE[edgeEvidenceQuery.data.edge.relation] || ""}{" "}
                      {edgeEvidenceQuery.data.edge.relation}
                    </span>
                    <span
                      data-testid="evidence-kind-badge"
                      className={
                        EVIDENCE_PILL_STYLE[
                          edgeEvidenceQuery.data.edge.evidence_kind
                        ]?.pillClass || "ledger-pill"
                      }
                    >
                      {EVIDENCE_PILL_STYLE[
                        edgeEvidenceQuery.data.edge.evidence_kind
                      ]?.label || edgeEvidenceQuery.data.edge.evidence_kind}
                    </span>
                  </div>

                  {/* Source -> Target Endpoint Cards */}
                  <div className="p-3 rounded-[8px] bg-ground border border-border space-y-2">
                    <button
                      type="button"
                      onClick={() =>
                        selectNode(
                          edgeEvidenceQuery.data.source_node.id,
                          edgeEvidenceQuery.data.source_node.name
                        )
                      }
                      className="w-full text-left p-2.5 rounded-[6px] bg-surface border border-border hover:border-control transition-colors"
                    >
                      <div className="text-xs text-muted">
                        Source ({edgeEvidenceQuery.data.source_node.label})
                      </div>
                      <div className="text-xs font-semibold text-ink truncate mt-0.5">
                        {edgeEvidenceQuery.data.source_node.name}
                      </div>
                    </button>

                    <div className="flex items-center justify-center gap-1.5 text-xs text-muted">
                      <ArrowRight className="w-3.5 h-3.5 text-ink" />
                      <span>
                        {edgeEvidenceQuery.data.edge.symmetric
                          ? "Symmetric undirected pair"
                          : "Directed claim"}
                      </span>
                    </div>

                    <button
                      type="button"
                      onClick={() =>
                        selectNode(
                          edgeEvidenceQuery.data.target_node.id,
                          edgeEvidenceQuery.data.target_node.name
                        )
                      }
                      className="w-full text-left p-2.5 rounded-[6px] bg-surface border border-border hover:border-control transition-colors"
                    >
                      <div className="text-xs text-muted">
                        Target ({edgeEvidenceQuery.data.target_node.label})
                      </div>
                      <div className="text-xs font-semibold text-ink truncate mt-0.5">
                        {edgeEvidenceQuery.data.target_node.name}
                      </div>
                    </button>
                  </div>
                </section>

                {/* 2. Primary Supported Fact: Derivation & Support Explanation */}
                <section className="p-3.5 rounded-[8px] bg-ground border border-border text-xs space-y-1.5">
                  <div className="font-semibold text-ink flex items-center gap-1.5">
                    <ShieldCheck className="w-4 h-4 text-[var(--positive)] shrink-0" />
                    <span>Support & derivation rule</span>
                  </div>
                  <p
                    data-testid="evidence-derivation-explanation"
                    className="text-muted leading-relaxed"
                  >
                    {edgeEvidenceQuery.data.derivation_explanation}
                  </p>
                </section>

                {/* 3. Supporting Core Papers */}
                {edgeEvidenceQuery.data.supporting_papers.length > 0 && (
                  <section className="space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-medium text-ink flex items-center gap-1.5">
                        <FileText className="w-3.5 h-3.5 text-muted" />
                        <span>
                          Supporting core papers (
                          {edgeEvidenceQuery.data.supporting_papers.length})
                        </span>
                      </span>
                    </div>

                    <div className="space-y-2">
                      {edgeEvidenceQuery.data.supporting_papers.map((p) => (
                        <div
                          key={p.paper_id}
                          data-testid={`supporting-paper-${p.paper_id}`}
                          className="p-3 rounded-[8px] bg-ground border border-border text-xs space-y-1.5"
                        >
                          <button
                            type="button"
                            onClick={() => selectNode(p.paper_id, p.title)}
                            className="font-semibold text-ink hover:underline text-left leading-snug block"
                          >
                            {p.title}
                          </button>
                          <div className="flex flex-wrap items-center gap-2 text-xs text-muted font-mono tabular-nums">
                            <span>{p.paper_id}</span>
                            {p.year && <span>· {p.year}</span>}
                          </div>
                          <div className="flex flex-wrap gap-3 pt-1">
                            {p.official_url && (
                              <a
                                href={p.official_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-1 text-xs text-ink font-medium hover:underline"
                              >
                                <span>Proceedings URL</span>
                                <ExternalLink className="w-3 h-3" />
                              </a>
                            )}
                            {p.pdf_url && (
                              <a
                                href={p.pdf_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-1 text-xs text-ink font-medium hover:underline"
                              >
                                <span>PDF</span>
                                <ExternalLink className="w-3 h-3" />
                              </a>
                            )}
                            {p.doi && (
                              <a
                                href={`https://doi.org/${p.doi}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-1 text-xs text-muted hover:text-ink hover:underline"
                              >
                                <span>DOI</span>
                                <ExternalLink className="w-3 h-3" />
                              </a>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </section>
                )}

                {/* 4. Aligned Affiliation Observations */}
                {edgeEvidenceQuery.data.affiliation_observations.length > 0 && (
                  <section className="space-y-2">
                    <div className="text-xs font-medium text-ink">
                      Aligned affiliation observations (
                      {edgeEvidenceQuery.data.affiliation_observations.length})
                    </div>
                    <div className="space-y-1.5 max-h-48 overflow-y-auto">
                      {edgeEvidenceQuery.data.affiliation_observations.map(
                        (obs) => (
                          <div
                            key={obs.id}
                            className="p-2.5 rounded-[6px] bg-ground border border-border text-xs space-y-0.5"
                          >
                            <div className="font-medium text-ink">
                              {obs.researcher_name || obs.researcher_id} →{" "}
                              {obs.organization_name || obs.organization_id}
                            </div>
                            <div className="text-muted truncate">
                              Paper ({obs.paper_year}):{" "}
                              {obs.paper_title || obs.paper_id}
                            </div>
                          </div>
                        )
                      )}
                    </div>
                  </section>
                )}

                {/* 5. Progressive Disclosure: Provenance Ledger, Hashes & Versions */}
                <details
                  className="group rounded-[8px] border border-border bg-ground px-3.5 py-2.5"
                  open
                >
                  <summary className="flex items-center justify-between cursor-pointer list-none text-xs font-medium text-muted hover:text-ink">
                    <span>
                      Provenance ledger & hashes (
                      {edgeEvidenceQuery.data.evidence_records.length} records)
                    </span>
                    <ChevronRight className="w-3.5 h-3.5 transition-transform group-open:rotate-90" />
                  </summary>

                  <div className="mt-3 space-y-3 text-xs">
                    <div className="grid grid-cols-2 gap-2">
                      <div className="p-2 rounded-[5px] bg-surface border border-border">
                        <div className="text-muted">Support count</div>
                        <div className="font-semibold text-ink tabular-nums">
                          {edgeEvidenceQuery.data.edge.support_count} paper(s)
                        </div>
                      </div>
                      <div className="p-2 rounded-[5px] bg-surface border border-border">
                        <div className="text-muted">Fractional weight</div>
                        <div className="font-semibold text-ink tabular-nums">
                          {typeof edgeEvidenceQuery.data.edge
                            .fractional_weight === "number"
                            ? edgeEvidenceQuery.data.edge.fractional_weight.toFixed(
                                4
                              )
                            : "1.0000 (unit)"}
                        </div>
                      </div>
                      <div className="p-2 rounded-[5px] bg-surface border border-border">
                        <div className="text-muted">Method version</div>
                        <div className="font-mono text-ink truncate">
                          {edgeEvidenceQuery.data.edge.method_version}
                        </div>
                      </div>
                      <div className="p-2 rounded-[5px] bg-surface border border-border">
                        <div className="text-muted">Graph version</div>
                        <div className="font-mono text-ink truncate">
                          {edgeEvidenceQuery.data.edge.graph_version}
                        </div>
                      </div>
                    </div>

                    <div className="p-2 rounded-[5px] bg-surface border border-border">
                      <div className="text-muted mb-0.5">Deterministic edge ID</div>
                      <div className="font-mono text-xs text-ink break-all">
                        {edgeEvidenceQuery.data.edge.edge_id}
                      </div>
                    </div>

                    {edgeEvidenceQuery.data.evidence_records.map((rec) => (
                      <div
                        key={rec.id}
                        className="p-2.5 rounded-[6px] bg-surface border border-border space-y-1.5"
                      >
                        <div className="font-mono text-ink font-medium break-all">
                          {rec.id}
                        </div>
                        {rec.excerpt && (
                          <blockquote className="p-2 rounded bg-ground border-l-2 border-control text-ink italic">
                            “{rec.excerpt}”
                          </blockquote>
                        )}
                        {rec.source_url && (
                          <div>
                            <a
                              href={rec.source_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1 text-ink underline break-all"
                            >
                              <span>{rec.source_url}</span>
                              <ExternalLink className="w-3 h-3 shrink-0" />
                            </a>
                          </div>
                        )}
                        {rec.source_locator && (
                          <div className="font-mono text-xs text-muted break-all">
                            Locator: {rec.source_locator}
                          </div>
                        )}
                        {rec.raw_sha256 && (
                          <div className="font-mono text-xs text-faint truncate">
                            SHA-256: {rec.raw_sha256}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </details>

                {/* 6. Scientific Caveats */}
                <section className="p-3.5 rounded-[8px] bg-ground border border-border space-y-1.5 text-xs text-muted">
                  <div className="font-semibold text-ink flex items-center gap-1.5">
                    <AlertTriangle className="w-3.5 h-3.5 text-[var(--warning)] shrink-0" />
                    <span>Scientific caveats</span>
                  </div>
                  {edgeEvidenceQuery.data.scientific_limitations.map(
                    (lim, i) => (
                      <p key={i} className="leading-relaxed">
                        • {lim}
                      </p>
                    )
                  )}
                </section>
              </>
            )}
          </div>
        )}
      </aside>
    </>
  );
};
