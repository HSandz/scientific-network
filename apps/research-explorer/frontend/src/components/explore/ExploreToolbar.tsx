import { exportGraph, csv, download } from "../../lib/exportGraph";
import { makeViewSpec } from "../../lib/viewSpec";
import React, { useState, useRef, useEffect } from "react";
import {
  GitBranch,
  Scale,
  AlertTriangle,
  Share2,
  Download,
  PanelLeft,
  PanelRight,
  Check,
  Maximize2,
  Minimize2,
  MoreHorizontal,
} from "lucide-react";
import { useExplorerStore } from "../../stores/useExplorerStore";
import {
  GraphEdge,
  GraphNode,
  GraphSummaryResponse,
  WorkspaceTab,
} from "../../types/explorer";

interface ExploreToolbarProps {
  summary?: GraphSummaryResponse;
  displayedNodes: GraphNode[];
  displayedEdges: GraphEdge[];
}


export const ExploreToolbar: React.FC<ExploreToolbarProps> = ({
  summary,
  displayedNodes,
  displayedEdges,
}) => {
  const {
    workspaceTab,
    setWorkspaceTab,
    leftSidebarOpen,
    setLeftSidebarOpen,
    rightSidebarOpen,
    setRightSidebarOpen,
    canvasExpanded,
    setCanvasExpanded,
    selectedNodeId,
    selectedEdgeId,
    setPathFinderOpen,
    setCompareModalOpen,
    setCaveatsModalOpen,
    buildShareUrl,
    savedViews,
    saveCurrentView,
    applySavedView,
  } = useExplorerStore();

  const [bookmarkName, setBookmarkName] = useState("");
  const [shareFallback, setShareFallback] = useState<string | null>(null);
  const [copiedShare, setCopiedShare] = useState(false);
  const [exportMenuOpen, setExportMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setExportMenuOpen(false);
      }
    };
    if (exportMenuOpen) {
      document.addEventListener("mousedown", onClickOutside);
    }
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, [exportMenuOpen]);

  const handleShare = async () => {
    const url = buildShareUrl();
    window.history.replaceState({}, "", url);
    try {
      await navigator.clipboard.writeText(url);
      setCopiedShare(true);
      setTimeout(() => setCopiedShare(false), 2000);
    } catch {
      setCopiedShare(false);
      setShareFallback(url);
    }
  };

  const handleExportSubgraphJson = () => {
    const payload = exportGraph(
      displayedNodes,
      displayedEdges,
      makeViewSpec(useExplorerStore.getState()),
      summary,
    );
    download(
      JSON.stringify(payload, null, 2),
      "scientific-network-slice.json",
      "application/json",
    );
    setExportMenuOpen(false);
  };
  const handleExportNodesCsv = () => {
    download(
      csv(displayedNodes as unknown as Record<string, unknown>[], [
        "id",
        "label",
        "name",
        "score",
        "displayed_degree",
        "displayed_neighbor_count",
        "displayed_strength",
        "year",
        "sector",
        "country_code",
        "venue",
      ]),
      "scientific-network-nodes.csv",
      "text/csv",
    );
    setExportMenuOpen(false);
  };
  const handleExportEdgesCsv = () => {
    download(
      csv(displayedEdges.map(e => ({ ...e,
        in_window_support_count: e.properties.in_window_support_count,
        in_window_support_paper_ids: JSON.stringify(e.properties.in_window_support_paper_ids || []),
        weight_scope: "full_period",
        evidence_ids: JSON.stringify(e.evidence_ids),
      })) as unknown as Record<string, unknown>[], [
        "edge_id",
        "source",
        "target",
        "relation",
        "directed",
        "symmetric",
        "support_count",
        "fractional_weight",
        "weight_scope",
        "in_window_support_count",
        "in_window_support_paper_ids",
        "evidence_ids",
        "evidence_kind",
        "method_version",
        "graph_version",
        "validation_status",
      ]),
      "scientific-network-edges.csv",
      "text/csv",
    );
    setExportMenuOpen(false);
  };

  const tabs: Array<{ id: WorkspaceTab; label: string }> = [
    { id: "graph", label: "Graph" },
    { id: "table", label: "Table" },
  ];


  const hasActiveSelection = Boolean(selectedNodeId || selectedEdgeId);
  const edgePrecisionPct =
    typeof summary?.quality?.edge_precision === "number"
      ? `${(summary.quality.edge_precision * 100).toFixed(1)}%`
      : null;

  return (
    <div
      className="explore-toolbar"
      role="toolbar"
      aria-label="Explore tools"
      data-testid="explore-toolbar"
    >
      {workspaceTab === "graph" && (
        <button
          type="button"
          onClick={() => setLeftSidebarOpen(!leftSidebarOpen)}
          data-testid="toggle-left-sidebar"
          aria-label="Toggle filter sidebar"
          aria-expanded={leftSidebarOpen}
          title={leftSidebarOpen ? "Hide filters" : "Show filters"}
          className={`explore-tool-icon ${leftSidebarOpen ? "is-on" : ""}`}
        >
          <PanelLeft className="w-4 h-4" />
        </button>
      )}
      <div className="seg" role="group" aria-label="Explore view">
        {tabs.map((t) => {
          const active = workspaceTab === t.id;
          return (
            <button
              key={t.id}
              type="button"
              onClick={() => setWorkspaceTab(t.id)}
              data-testid={`tab-${t.id}`}
              aria-pressed={active}
              data-active={active}
            >
              {t.label}
            </button>
          );
        })}
      </div>
      <span
        data-testid="graph-version-badge"
        className="explore-version"
        title={`Graph version ${summary?.graph_version || "unavailable"}${summary?.graph_version?.startsWith("release-") ? " (frozen v4 release, D040)" : ""}. All versions are listed on About.`}
      >
        {summary?.graph_version?.startsWith("enriched-") ? "Enriched graph" : "Release graph v4"}
      </span>
      <div className="explore-toolbar-spacer" />
      <button
        type="button"
        onClick={() => setPathFinderOpen(true)}
        data-testid="open-path-finder"
        className="explore-tool hidden lg:inline-flex"
        title="Find the shortest connections between two entities"
      >
        <GitBranch className="w-4 h-4" />
        <span>Paths</span>
      </button>
      <button
        type="button"
        onClick={() => setCompareModalOpen(true)}
        data-testid="open-compare-modal"
        className="explore-tool hidden lg:inline-flex"
        title="Compare two researchers or organizations side by side"
      >
        <Scale className="w-4 h-4" />
        <span>Compare</span>
      </button>
      <button
        type="button"
        onClick={() => setCaveatsModalOpen(true)}
        data-testid="open-caveats-modal"
        className="explore-tool hidden lg:inline-flex"
        title={edgePrecisionPct ? `Quality and caveats. Edge precision ${edgePrecisionPct}, AI-assessed.` : "Quality and caveats"}
      >
        <AlertTriangle className="w-4 h-4" />
        <span>Caveats</span>
      </button>
          {/* Export, Share & Secondary Tools Menu */}
          <div className="relative" ref={menuRef}>
            <button
              type="button"
              onClick={() => setExportMenuOpen((v) => !v)}
              data-testid="open-export-menu"
              aria-label="Workspace tools and export actions"
              aria-expanded={exportMenuOpen}
              className="explore-tool-icon"
              title="Share, save, export or expand the canvas"
            >
              <MoreHorizontal className="w-4 h-4" />
            </button>

            {exportMenuOpen && (
              <div className="absolute right-0 mt-1.5 w-56 max-h-[75dvh] overflow-y-auto rounded-[8px] bg-surface border border-border py-1.5 z-50">
                                {/* Secondary analysis tools collapsed on smaller screens (< 1280px) */}
                <div className="lg:hidden border-b border-rule pb-1 mb-1">
                  <button
                    type="button"
                    onClick={() => {
                      setExportMenuOpen(false);
                      setPathFinderOpen(true);
                    }}
                    className="w-full flex items-center gap-2.5 px-3 py-2 text-left text-[13px] text-ink hover:bg-raised transition-colors"
                  >
                    <GitBranch className="w-3.5 h-3.5 text-muted" />
                    <span>Shortest-path finder</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setExportMenuOpen(false);
                      setCompareModalOpen(true);
                    }}
                    className="w-full flex items-center gap-2.5 px-3 py-2 text-left text-[13px] text-ink hover:bg-raised transition-colors"
                  >
                    <Scale className="w-3.5 h-3.5 text-muted" />
                    <span>Compare entities</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setExportMenuOpen(false);
                      setCaveatsModalOpen(true);
                    }}
                    className="w-full flex items-center gap-2.5 px-3 py-2 text-left text-[13px] text-ink hover:bg-raised transition-colors"
                  >
                    <AlertTriangle className="w-3.5 h-3.5 text-[var(--warning)]" />
                    <span>
                      Quality &amp; caveats
                      {edgePrecisionPct ? ` (${edgePrecisionPct})` : ""}
                    </span>
                  </button>
                </div>

                <div className="px-3 py-2 border-b border-rule mb-1">
                  <label htmlFor="workspace-bookmark-name" className="block text-xs font-medium text-muted mb-1">Save workspace</label>
                  <div className="flex gap-1">
                    <input id="workspace-bookmark-name" value={bookmarkName}
                      onChange={e => setBookmarkName(e.target.value)}
                      placeholder="Workspace name" maxLength={100}
                      className="ledger-input min-w-0 flex-1 h-8 text-xs" />
                    <button type="button" disabled={!bookmarkName.trim()}
                      data-testid="save-workspace-bookmark"
                      className="ledger-btn h-8 text-xs disabled:opacity-50"
                      onClick={() => { saveCurrentView(bookmarkName.trim()); setBookmarkName(""); setExportMenuOpen(false); }}>Save</button>
                  </div>
                  {savedViews.length > 0 && <div className="mt-2 space-y-1" aria-label="Saved workspaces">
                    {savedViews.map(view => <button key={view.id} type="button"
                      className="block w-full text-left text-xs py-1.5 px-1 rounded hover:bg-raised truncate"
                      onClick={() => { applySavedView(view); setExportMenuOpen(false); }}>
                      Restore {view.name}
                    </button>)}
                  </div>}
                </div>

                <button
                  type="button"
                  onClick={handleShare}
                  data-testid="share-view-btn"
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-left text-[13px] text-ink hover:bg-raised transition-colors"
                >
                  {copiedShare ? (
                    <Check className="w-3.5 h-3.5 text-[var(--positive)]" />
                  ) : (
                    <Share2 className="w-3.5 h-3.5 text-muted" />
                  )}
                  <span>
                    {copiedShare ? "Copied share link" : "Copy shareable URL"}
                  </span>
                </button>
                {shareFallback && (
                  <label className="block p-3 text-xs" role="alert">
                    Clipboard unavailable. Select and copy this URL:
                    <input
                      aria-label="Share URL to copy"
                      readOnly
                      value={shareFallback}
                      onFocus={(e) => e.target.select()}
                      className="w-full bg-ground p-2 mt-1"
                    />
                  </label>
                )}
                <button
                  type="button"
                  onClick={handleExportEdgesCsv}
                  data-testid="export-edges-csv"
                  className="w-full px-3 py-2 text-left text-[13px] hover:bg-raised"
                >
                  Export displayed edges CSV
                </button>
                <button
                  type="button"
                  onClick={handleExportSubgraphJson}
                  data-testid="export-subgraph-json"
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-left text-[13px] text-ink hover:bg-raised transition-colors"
                >
                  <Download className="w-3.5 h-3.5 text-muted" />
                  <span>Export subgraph JSON</span>
                </button>
                <button
                  type="button"
                  onClick={handleExportNodesCsv}
                  data-testid="export-subgraph-csv"
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-left text-[13px] text-ink hover:bg-raised transition-colors"
                >
                  <Download className="w-3.5 h-3.5 text-muted" />
                  <span>Export displayed nodes CSV</span>
                </button>
                {workspaceTab === "graph" && (
                  <>
                    <div className="my-1 border-t border-rule" />
                    <button
                      type="button"
                      onClick={() => {
                        setCanvasExpanded(!canvasExpanded);
                        setExportMenuOpen(false);
                      }}
                      className="w-full flex items-center gap-2.5 px-3 py-2 text-left text-[13px] text-ink hover:bg-raised transition-colors"
                    >
                      {canvasExpanded ? (
                        <Minimize2 className="w-3.5 h-3.5 text-muted" />
                      ) : (
                        <Maximize2 className="w-3.5 h-3.5 text-muted" />
                      )}
                      <span>
                        {canvasExpanded
                          ? "Restore side panels"
                          : "Focus full canvas"}
                      </span>
                    </button>
                  </>
                )}
              </div>
            )}
          </div>

      {(hasActiveSelection || rightSidebarOpen) && (
        <button
          type="button"
          onClick={() => setRightSidebarOpen(!rightSidebarOpen)}
          data-testid="toggle-right-inspector"
          aria-label="Toggle detail inspector"
          aria-expanded={rightSidebarOpen}
          className={`explore-tool hidden sm:inline-flex ${rightSidebarOpen ? "is-on" : ""}`}
          title={rightSidebarOpen ? "Hide details" : "Show selected details"}
        >
          <PanelRight className="w-4 h-4" />
          <span className="hidden lg:inline">Details</span>
        </button>
      )}
    </div>
  );
};
