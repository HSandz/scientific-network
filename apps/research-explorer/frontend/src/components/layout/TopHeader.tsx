import { exportGraph, csv, download } from "../../lib/exportGraph";
import { makeViewSpec } from "../../lib/viewSpec";
import React, { useState, useRef, useEffect } from "react";
import {
  Search,
  GitBranch,
  Scale,
  AlertTriangle,
  Share2,
  Download,
  Sun,
  Moon,
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

interface TopHeaderProps {
  summary?: GraphSummaryResponse;
  displayedNodes: GraphNode[];
  displayedEdges: GraphEdge[];
}

export const TopHeader: React.FC<TopHeaderProps> = ({
  summary,
  displayedNodes,
  displayedEdges,
}) => {
  const {
    darkMode,
    toggleDarkMode,
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
    setSearchModalOpen,
    setPathFinderOpen,
    setCompareModalOpen,
    setCaveatsModalOpen,
    buildShareUrl,
  } = useExplorerStore();

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
    { id: "analytics", label: "Analytics" },
  ];

  const hasActiveSelection = Boolean(selectedNodeId || selectedEdgeId);
  const edgePrecisionPct =
    typeof summary?.quality?.edge_precision === "number"
      ? `${(summary.quality.edge_precision * 100).toFixed(1)}%`
      : null;

  return (
    <header className="relative shrink-0 bg-surface border-b border-border px-1.5 sm:px-4 lg:px-5 py-1.5 md:py-2.5 z-30 select-none">
      <div className="flex items-center justify-between gap-1 sm:gap-2.5 lg:gap-4 flex-nowrap">
        {/* Left: Filter drawer toggle + Product Identity + Scope */}
        <div className="flex items-center gap-1.5 sm:gap-2.5 min-w-0 shrink-0">
          {workspaceTab === "graph" && (
            <button
              type="button"
              onClick={() => setLeftSidebarOpen(!leftSidebarOpen)}
              data-testid="toggle-left-sidebar"
              aria-label="Toggle filter sidebar"
              aria-expanded={leftSidebarOpen}
              title={
                leftSidebarOpen
                  ? "Hide filters & scope"
                  : "Show filters & scope"
              }
              className={`inline-flex items-center justify-center w-11 h-11 md:w-8 md:h-8 rounded-[6px] border transition-colors shrink-0 ${
                leftSidebarOpen
                  ? "bg-raised border-control text-ink"
                  : "bg-surface border-border text-muted hover:text-ink hover:bg-raised"
              }`}
            >
              <PanelLeft className="w-4 h-4" />
            </button>
          )}

          <div className="flex items-baseline gap-x-2 min-w-0">
            <span
              className="text-[13px] sm:text-[15px] font-semibold tracking-tight text-ink whitespace-nowrap"
              title="AI Research Network — AAAI & IJCAI 2021–2025"
            >
              <span className="sm:hidden">AIRN</span>
              <span className="hidden sm:inline">AI Research Network</span>
            </span>
            <span className="hidden 2xl:inline text-[13px] text-muted whitespace-nowrap">
              AAAI · IJCAI 2021–2025
            </span>
            <span
              data-testid="graph-version-badge"
              className="hidden lg:inline text-xs font-mono text-faint whitespace-nowrap"
              title="Isolated release Neo4j graph version (D040)"
            >
              {summary?.graph_version || "Version unavailable"}
            </span>
          </div>
        </div>

        {/* Center: Primary Entity Search + Workspace Switcher */}
        <div className="flex items-center gap-1 sm:gap-2 min-w-0 md:flex-1 md:justify-center max-w-xl z-10">
          <button
            type="button"
            onClick={() => setSearchModalOpen(true)}
            data-testid="open-global-search"
            aria-label="Search all entities"
            className="inline-flex items-center justify-center md:justify-between gap-2 w-11 h-11 md:w-[136px] lg:w-[180px] xl:w-[240px] md:h-[34px] px-0 md:px-2.5 lg:px-3 rounded-[6px] border border-control bg-ground hover:border-ink/40 text-muted hover:text-ink transition-colors shrink-0"
            title="Search all entities by name, ID, DOI, or ORCID (Shortcut: /)"
          >
            <span className="flex items-center gap-2 min-w-0 truncate text-[13px]">
              <Search className="w-4 h-4 md:w-3.5 md:h-3.5 shrink-0 text-faint" />
              <span className="hidden md:inline truncate">
                Search all entities…
              </span>
            </span>
            <kbd className="hidden xl:inline-block px-1.5 py-0.5 text-xs font-mono bg-surface text-faint rounded border border-border shrink-0">
              /
            </kbd>
          </button>

          <nav
            aria-label="Primary workspace views"
            className="ledger-segmented shrink-0 relative z-20"
          >
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
                  className="!px-2.5 sm:!px-3.5 !py-1.5 md:!py-1.5 !text-[12px] sm:!text-[13px] font-medium min-h-[32px] cursor-pointer"
                >
                  {t.label}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Right: Analysis workflows, Scientific Quality status, Export & Theme */}
        <div className="flex items-center gap-1 sm:gap-1.5 shrink-0">
          <button
            type="button"
            onClick={() => setPathFinderOpen(true)}
            data-testid="open-path-finder"
            className="hidden xl:inline-flex ledger-btn h-[32px] px-2.5 text-[13px]"
            title="Find bounded shortest paths between any two entities"
          >
            <GitBranch className="w-3.5 h-3.5 text-muted" />
            <span>Paths</span>
          </button>

          <button
            type="button"
            onClick={() => setCompareModalOpen(true)}
            data-testid="open-compare-modal"
            className="hidden xl:inline-flex ledger-btn h-[32px] px-2.5 text-[13px]"
            title="Compare two researchers or organizations side by side"
          >
            <Scale className="w-3.5 h-3.5 text-muted" />
            <span>Compare</span>
          </button>

          <button
            type="button"
            onClick={() => setCaveatsModalOpen(true)}
            data-testid="open-caveats-modal"
            className="hidden xl:inline-flex ledger-btn h-[32px] px-2.5 text-[13px]"
            title="Inspect AI-assessed edge precision, affiliation coverage, topic coverage, and topic precision"
          >
            <AlertTriangle className="w-3.5 h-3.5 text-[var(--warning)]" />
            <span className="hidden 2xl:inline tabular-nums">
              {edgePrecisionPct ? `${edgePrecisionPct} AI-assessed` : "Caveats"}
            </span>
            <span className="2xl:hidden">Caveats</span>
          </button>

          {/* Export, Share & Secondary Tools Menu */}
          <div className="relative" ref={menuRef}>
            <button
              type="button"
              onClick={() => setExportMenuOpen((v) => !v)}
              data-testid="open-export-menu"
              aria-label="Workspace tools and export actions"
              aria-expanded={exportMenuOpen}
              className="inline-flex items-center justify-center w-11 h-11 md:w-8 md:h-8 rounded-[6px] border border-border bg-surface hover:bg-raised text-muted hover:text-ink transition-colors"
              title="Tools, share link, export subgraph data, or expand canvas"
            >
              <MoreHorizontal className="w-4 h-4" />
            </button>

            {exportMenuOpen && (
              <div className="absolute right-0 mt-1.5 w-56 rounded-[8px] bg-surface border border-border py-1.5 z-50">
                {/* Secondary analysis tools collapsed on smaller screens (< 1280px) */}
                <div className="xl:hidden border-b border-rule pb-1 mb-1">
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

          <button
            type="button"
            onClick={toggleDarkMode}
            data-testid="theme-toggle"
            aria-label={
              darkMode ? "Switch to light mode" : "Switch to dark mode"
            }
            className="inline-flex items-center justify-center w-11 h-11 md:w-8 md:h-8 rounded-[6px] border border-border bg-surface hover:bg-raised text-muted hover:text-ink transition-colors"
            title={
              darkMode
                ? "Switch to stone light theme"
                : "Switch to soft graphite dark theme"
            }
          >
            {darkMode ? (
              <Sun className="w-4 h-4" />
            ) : (
              <Moon className="w-4 h-4" />
            )}
          </button>

          {(hasActiveSelection || rightSidebarOpen) && (
            <button
              type="button"
              onClick={() => setRightSidebarOpen(!rightSidebarOpen)}
              data-testid="toggle-right-inspector"
              aria-label="Toggle detail inspector"
              aria-expanded={rightSidebarOpen}
              className={`hidden sm:inline-flex items-center gap-1.5 h-11 md:h-8 px-2.5 rounded-[6px] border text-[13px] font-medium transition-colors ${
                rightSidebarOpen
                  ? "bg-raised border-control text-ink"
                  : "bg-surface border-border text-muted hover:text-ink hover:bg-raised"
              }`}
              title={
                rightSidebarOpen ? "Hide inspector" : "Show selected details"
              }
            >
              <PanelRight className="w-3.5 h-3.5" />
              <span className="hidden lg:inline">Details</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
