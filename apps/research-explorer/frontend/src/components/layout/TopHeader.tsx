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
import { GraphEdge, GraphNode, GraphSummaryResponse, WorkspaceTab } from "../../types/explorer";

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
      setCopiedShare(true);
      setTimeout(() => setCopiedShare(false), 2000);
    }
  };

  const handleExportSubgraphJson = () => {
    const payload = {
      exported_at: new Date().toISOString(),
      graph_version: summary?.graph_version || "release-d3c788c3114a",
      node_count: displayedNodes.length,
      edge_count: displayedEdges.length,
      nodes: displayedNodes,
      edges: displayedEdges,
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `scientific-network-subgraph-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    setExportMenuOpen(false);
  };

  const handleExportNodesCsv = () => {
    const headers = [
      "id",
      "label",
      "name",
      "group",
      "full_projection_score",
      "displayed_degree",
      "year",
      "sector",
      "country_code",
      "venue",
    ];
    const escapeCsv = (val: unknown) => {
      if (val === null || val === undefined) return "";
      const str = String(val);
      if (str.includes(",") || str.includes('"') || str.includes("\n")) {
        return `"${str.replace(/"/g, '""')}"`;
      }
      return str;
    };
    const rows = displayedNodes.map((n) =>
      [
        n.id,
        n.label,
        n.name,
        n.group,
        n.score,
        n.displayed_degree,
        n.year ?? "",
        n.sector ?? "",
        n.country_code ?? "",
        n.venue ?? "",
      ]
        .map(escapeCsv)
        .join(",")
    );
    const csv = [headers.join(","), ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `scientific-network-nodes-${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    setExportMenuOpen(false);
  };

  const tabs: Array<{ id: WorkspaceTab; label: string }> = [
    { id: "graph", label: "Graph" },
    { id: "table", label: "Table" },
    { id: "analytics", label: "Analytics" },
  ];

  const hasActiveSelection = Boolean(selectedNodeId || selectedEdgeId);
  const edgePrecisionPct =
    summary?.quality?.edge_precision !== undefined
      ? `${(summary.quality.edge_precision * 100).toFixed(1)}%`
      : null;

  return (
    <header className="shrink-0 bg-surface border-b border-border px-1.5 sm:px-4 lg:px-5 py-1.5 md:py-2.5 z-30 select-none">
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
              title={leftSidebarOpen ? "Hide filters & scope" : "Show filters & scope"}
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
              className="hidden sm:inline text-xs font-mono text-faint whitespace-nowrap"
              title="Isolated release Neo4j graph version (D040)"
            >
              {summary?.graph_version || "release-d3c788c3114a"}
            </span>
          </div>
        </div>

        {/* Center: Primary Entity Search + Workspace Switcher */}
        <div className="flex items-center gap-1 sm:gap-2 min-w-0 md:flex-1 md:justify-center max-w-2xl">
          <button
            type="button"
            onClick={() => setSearchModalOpen(true)}
            data-testid="open-global-search"
            aria-label="Search all 47,875 entities"
            className="inline-flex items-center justify-center md:justify-between gap-2 w-11 h-11 md:w-[136px] lg:w-[200px] xl:w-[260px] md:h-[34px] px-0 md:px-2.5 lg:px-3 rounded-[6px] border border-control bg-ground hover:border-ink/40 text-muted hover:text-ink transition-colors shrink-0"
            title="Search all 47,875 entities by name, ID, DOI, or ORCID (Shortcut: /)"
          >
            <span className="flex items-center gap-2 min-w-0 truncate text-[13px]">
              <Search className="w-4 h-4 md:w-3.5 md:h-3.5 shrink-0 text-faint" />
              <span className="hidden md:inline truncate">
                Search 47,875 entities...
              </span>
            </span>
            <kbd className="hidden lg:inline-block px-1.5 py-0.5 text-xs font-mono bg-surface text-faint rounded border border-border shrink-0">
              /
            </kbd>
          </button>

          <nav
            aria-label="Primary workspace views"
            className="ledger-segmented shrink-0"
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
                  className="!px-2 sm:!px-2.5 !py-1.5 md:!py-1 !text-[12px] sm:!text-[13px]"
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
            className="hidden md:inline-flex ledger-btn h-[32px] px-2 lg:px-2.5 text-[13px]"
            title="Find bounded shortest paths between any two entities"
          >
            <GitBranch className="w-3.5 h-3.5 text-muted" />
            <span className="hidden lg:inline">Paths</span>
          </button>

          <button
            type="button"
            onClick={() => setCompareModalOpen(true)}
            data-testid="open-compare-modal"
            className="hidden md:inline-flex ledger-btn h-[32px] px-2 lg:px-2.5 text-[13px]"
            title="Compare two researchers or organizations side by side"
          >
            <Scale className="w-3.5 h-3.5 text-muted" />
            <span className="hidden lg:inline">Compare</span>
          </button>

          <button
            type="button"
            onClick={() => setCaveatsModalOpen(true)}
            data-testid="open-caveats-modal"
            className="hidden md:inline-flex ledger-btn h-[32px] px-2 lg:px-2.5 text-[13px]"
            title="Inspect AI-assessed edge precision (96.5%), affiliation coverage (48,259 / 65,469 = 73.71% FAIL), topic coverage (85.00% PASS), and topic precision (68.63% FAIL)"
          >
            <AlertTriangle className="w-3.5 h-3.5 text-[var(--warning)]" />
            <span className="hidden xl:inline tabular-nums">
              {edgePrecisionPct ? `${edgePrecisionPct} AI-assessed` : "Caveats"}
            </span>
            <span className="xl:hidden">Caveats</span>
          </button>

          {/* Export, Share & Mobile Tools Menu */}
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
                {/* Mobile-only analysis tools */}
                <div className="md:hidden border-b border-rule pb-1 mb-1">
                  <button
                    type="button"
                    onClick={() => {
                      setExportMenuOpen(false);
                      setPathFinderOpen(true);
                    }}
                    className="w-full flex items-center gap-2.5 px-3 py-2.5 text-left text-[13px] text-ink hover:bg-raised transition-colors"
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
                    className="w-full flex items-center gap-2.5 px-3 py-2.5 text-left text-[13px] text-ink hover:bg-raised transition-colors"
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
                    className="w-full flex items-center gap-2.5 px-3 py-2.5 text-left text-[13px] text-ink hover:bg-raised transition-colors"
                  >
                    <AlertTriangle className="w-3.5 h-3.5 text-[var(--warning)]" />
                    <span>
                      Quality & caveats{edgePrecisionPct ? ` (${edgePrecisionPct})` : ""}
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
                  <span>{copiedShare ? "Copied share link" : "Copy shareable URL"}</span>
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
                      <span>{canvasExpanded ? "Restore side panels" : "Focus full canvas"}</span>
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
            aria-label={darkMode ? "Switch to light mode" : "Switch to dark mode"}
            className="inline-flex items-center justify-center w-11 h-11 md:w-8 md:h-8 rounded-[6px] border border-border bg-surface hover:bg-raised text-muted hover:text-ink transition-colors"
            title={darkMode ? "Switch to stone light theme" : "Switch to soft graphite dark theme"}
          >
            {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
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
              title={rightSidebarOpen ? "Hide inspector" : "Show selected details"}
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
