import React, { useState, useEffect } from "react";
import {
  Users,
  Building2,
  BookOpen,
  Layers,
  RotateCcw,
  Bookmark,
  Plus,
  History,
  X,
  ChevronRight,
} from "lucide-react";
import { useExplorerStore } from "../../stores/useExplorerStore";
import {
  GraphSummaryResponse,
  CommunityOption,
  NodeLabel,
  RelationType,
  ViewMode,
} from "../../types/explorer";
import { LABEL_COLORS, PREDICATE_R_CODE } from "../../lib/colors";

interface LeftSidebarProps {
  availableCommunities: CommunityOption[];
  summary?: GraphSummaryResponse;
}

const ALL_NODE_LABELS: NodeLabel[] = [
  "Researcher",
  "Paper",
  "Organization",
  "Topic",
  "Venue",
];

const ALL_RELATIONS: RelationType[] = [
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
];

const PROJECTION_MODES: Array<{
  id: ViewMode;
  title: string;
  countLabel: string;
  predicateSummary: string;
  icon: React.FC<{ className?: string }>;
}> = [
  {
    id: "heterogeneous",
    title: "Knowledge graph",
    countLabel: "",
    predicateSummary: "All 5 entity labels and 10 predicates (R1–R10)",
    icon: Layers,
  },
  {
    id: "organizations",
    title: "Organizations",
    countLabel: "",
    predicateSummary: "COLLABORATED_WITH (R8) institutional network",
    icon: Building2,
  },
  {
    id: "researchers",
    title: "Researchers",
    countLabel: "",
    predicateSummary: "COAUTHORED_WITH (R7) collaboration projection",
    icon: Users,
  },
  {
    id: "citations",
    title: "Citations",
    countLabel: "",
    predicateSummary: "Directed CITES (R4) within-corpus references; count = paper nodes",
    icon: BookOpen,
  },
];

export const LeftSidebar: React.FC<LeftSidebarProps> = ({
  availableCommunities,
  summary,
}) => {
  const {
    leftSidebarOpen,
    setLeftSidebarOpen,
    viewMode,
    setViewMode,
    filters,
    updateFilters,
    resetFilters,
    extraNodes,
    clearExtraSubgraph,
    savedViews,
    saveCurrentView,
    applySavedView,
    selectionHistory,
    selectNode,
    selectEdge,
  } = useExplorerStore();

  const [bookmarkName, setBookmarkName] = useState("");

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && leftSidebarOpen) {
        setLeftSidebarOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [leftSidebarOpen, setLeftSidebarOpen]);

  if (!leftSidebarOpen) return null;

  const activeMode =
    PROJECTION_MODES.find((m) => m.id === viewMode) || PROJECTION_MODES[0];

  const activeFilterTags: Array<{ label: string; onClear: () => void }> = [];
  if (filters.communityId) {
    activeFilterTags.push({
      label: `Community: ${filters.communityId}`,
      onClear: () => updateFilters({ communityId: "" }),
    });
  }
  if (filters.sector) {
    activeFilterTags.push({
      label: `Sector: ${filters.sector}`,
      onClear: () => updateFilters({ sector: "" }),
    });
  }
  if (filters.crossSectorOnly) {
    activeFilterTags.push({
      label: "Cross-sector only",
      onClear: () => updateFilters({ crossSectorOnly: false }),
    });
  }
  if (filters.countryCode) {
    activeFilterTags.push({
      label: `Country: ${filters.countryCode}`,
      onClear: () => updateFilters({ countryCode: "" }),
    });
  }
  if (filters.venue) {
    activeFilterTags.push({
      label: `Venue: ${filters.venue.replace("venue:", "").toUpperCase()}`,
      onClear: () => updateFilters({ venue: "" }),
    });
  }
  if (filters.yearMin !== 2021 || filters.yearMax !== 2025) {
    activeFilterTags.push({
      label: `Years: ${filters.yearMin}–${filters.yearMax}`,
      onClear: () => updateFilters({ yearMin: 2021, yearMax: 2025 }),
    });
  }
  if (filters.minSupport > 1) {
    activeFilterTags.push({
      label: `Min papers ≥ ${filters.minSupport}`,
      onClear: () => updateFilters({ minSupport: 1 }),
    });
  }
  if (filters.minWeight > 0) {
    activeFilterTags.push({
      label: `Weight ≥ ${filters.minWeight.toFixed(2)}`,
      onClear: () => updateFilters({ minWeight: 0 }),
    });
  }
  if (extraNodes.length > 0) {
    activeFilterTags.push({
      label: `+${extraNodes.length} expanded nodes`,
      onClear: () => clearExtraSubgraph(),
    });
  }

  const toggleNodeLabel = (lbl: NodeLabel) => {
    const exists = filters.nodeLabels.includes(lbl);
    if (exists && filters.nodeLabels.length > 1) {
      updateFilters({
        preset: "custom",
        nodeLabels: filters.nodeLabels.filter((x) => x !== lbl),
      });
    } else if (!exists) {
      updateFilters({
        preset: "custom",
        nodeLabels: [...filters.nodeLabels, lbl],
      });
    }
  };

  const toggleRelation = (rel: RelationType) => {
    const exists = filters.relations.includes(rel);
    if (exists && filters.relations.length > 1) {
      updateFilters({
        preset: "custom",
        relations: filters.relations.filter((x) => x !== rel),
      });
    } else if (!exists) {
      updateFilters({
        preset: "custom",
        relations: [...filters.relations, rel],
      });
    }
  };

  return (
    <>
      {/* Backdrop for tablet and phone drawer */}
      <div
        className="absolute inset-0 bg-black/50 z-30 lg:hidden"
        onClick={() => setLeftSidebarOpen(false)}
        aria-hidden="true"
      />

      <aside
        data-testid="left-sidebar"
        role={
          typeof window !== "undefined" && window.innerWidth < 1024
            ? "dialog"
            : undefined
        }
        aria-modal={
          typeof window !== "undefined" && window.innerWidth < 1024
            ? "true"
            : undefined
        }
        aria-label="Graph projection and scope filters"
        className="absolute inset-y-0 left-0 z-40 w-[300px] max-w-[90vw] lg:static lg:w-[272px] shrink-0 bg-surface border-r border-border flex flex-col h-full overflow-y-auto select-none"
      >
        {/* Mobile/Tablet drawer header */}
        <div className="flex items-center justify-between px-4 py-2.5 border-b border-border lg:hidden">
          <span className="text-sm font-semibold text-ink">
            Projection & filters
          </span>
          <button
            type="button"
            onClick={() => setLeftSidebarOpen(false)}
            data-testid="close-left-sidebar"
            className="ledger-btn min-h-[44px] px-3 text-[13px]"
          >
            <X className="w-4 h-4" />
            <span>Return to graph</span>
          </button>
        </div>

        {/* 1. Compact Projection Selector */}
        <div className="px-5 pt-4 pb-4 border-b border-border">
          <div className="text-[13px] font-medium text-muted mb-2">
            Network projection
          </div>
          <div
            className="space-y-1"
            role="radiogroup"
            aria-label="Network projection"
          >
            {PROJECTION_MODES.map((m) => {
              const Icon = m.icon;
              const active = viewMode === m.id;
              return (
                <button
                  key={m.id}
                  type="button"
                  role="radio"
                  aria-checked={active}
                  onClick={() => setViewMode(m.id)}
                  data-testid={`mode-${m.id}`}
                  className={`w-full flex items-center justify-between gap-2 h-[34px] px-2.5 rounded-[6px] text-left text-[13px] transition-colors ${
                    active
                      ? "bg-active text-ink font-medium"
                      : "text-muted hover:bg-raised hover:text-ink"
                  }`}
                >
                  <span className="flex items-center gap-2 min-w-0 truncate">
                    <Icon className="w-4 h-4 shrink-0 text-faint" />
                    <span className="truncate">{m.title}</span>
                  </span>
                  <span className="text-[13px] text-faint tabular-nums shrink-0">
                    {(m.id === "heterogeneous"
                      ? summary?.total_nodes
                      : summary?.nodes_by_label[
                          m.id === "researchers"
                            ? "Researcher"
                            : m.id === "organizations"
                              ? "Organization"
                              : "Paper"
                        ]
                    )?.toLocaleString() ?? "Unavailable"}{m.id === "citations" ? " papers" : ""}
                  </span>
                </button>
              );
            })}
          </div>
          <p className="mt-2.5 text-xs text-faint leading-relaxed">
            {activeMode.predicateSummary}
          </p>
        </div>

        {/* 2. Primary Scope Filters */}
        <div className="px-5 py-4 border-b border-border space-y-3.5">
          <div className="flex items-center justify-between">
            <span className="text-[13px] font-medium text-muted">
              Scope & filters
            </span>
            {activeFilterTags.length > 0 && (
              <button
                type="button"
                onClick={resetFilters}
                data-testid="reset-filters-btn"
                className="inline-flex items-center gap-1 text-[13px] text-ink hover:underline"
              >
                <RotateCcw className="w-3 h-3" />
                <span>Reset ({activeFilterTags.length})</span>
              </button>
            )}
          </div>

          {/* Active filter pills */}
          {activeFilterTags.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {activeFilterTags.map((tag) => (
                <button
                  key={tag.label}
                  type="button"
                  onClick={tag.onClear}
                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded-[4px] bg-raised border border-border text-xs text-ink hover:border-control"
                  title="Click to remove filter"
                >
                  <span className="truncate max-w-[180px]">{tag.label}</span>
                  <X className="w-3 h-3 text-faint shrink-0" />
                </button>
              ))}
            </div>
          )}

          {/* Mode A: Community selector */}
          {viewMode === "researchers" && (
            <div>
              <label
                htmlFor="filter-community"
                className="block text-[13px] font-medium text-ink mb-1.5"
              >
                Louvain community
              </label>
              <select
                id="filter-community"
                value={filters.communityId}
                onChange={(e) => updateFilters({ communityId: e.target.value })}
                data-testid="filter-community"
                className="w-full ledger-input text-[13px]"
              >
                <option value="">All communities (top by degree)</option>
                {availableCommunities.map((c) => (
                  <option key={c.community_id} value={c.community_id}>
                    {c.community_id} ({c.member_count.toLocaleString()}{" "}
                    researchers)
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Mode B: Organization sector & cross-sector */}
          {viewMode === "organizations" && (
            <div className="space-y-3">
              <div>
                <label
                  htmlFor="filter-sector"
                  className="block text-[13px] font-medium text-ink mb-1.5"
                >
                  Institution sector (both endpoints)
                </label>
                <select
                  id="filter-sector"
                  value={filters.sector}
                  onChange={(e) => updateFilters({ sector: e.target.value })}
                  data-testid="filter-sector"
                  className="w-full ledger-input text-[13px]"
                >
                  <option value="">All sectors (2,047 orgs)</option>
                  <option value="academia">Academia (1,452)</option>
                  <option value="industry">Industry (253)</option>
                  <option value="government">Government (185)</option>
                  <option value="nonprofit">Nonprofit / Other (157)</option>
                </select>
              </div>

              <label className="flex items-center justify-between gap-2 py-1 cursor-pointer">
                <span className="text-[13px] text-ink">
                  Cross-sector collaborations only
                </span>
                <input
                  type="checkbox"
                  checked={filters.crossSectorOnly}
                  onChange={(e) =>
                    updateFilters({ crossSectorOnly: e.target.checked })
                  }
                  data-testid="filter-cross-sector"
                  className="rounded border-control text-ink focus:ring-0"
                />
              </label>

              <div>
                <label
                  htmlFor="filter-country"
                  className="block text-[13px] font-medium text-ink mb-1.5"
                >
                  ISO country code (both endpoints)
                </label>
                <input
                  id="filter-country"
                  type="text"
                  placeholder="e.g. US, CN, GB, SG"
                  maxLength={2}
                  value={filters.countryCode}
                  onChange={(e) =>
                    updateFilters({ countryCode: e.target.value.toUpperCase() })
                  }
                  className="w-full ledger-input text-[13px] font-mono"
                />
              </div>
            </div>
          )}

          {/* Paper-support filters apply to all four projections. */}
          {(
            <div className="space-y-3">
              <div>
                <label
                  htmlFor="filter-venue"
                  className="block text-[13px] font-medium text-ink mb-1.5"
                >
                  Conference series
                </label>
                <select
                  id="filter-venue"
                  value={filters.venue}
                  onChange={(e) => updateFilters({ venue: e.target.value })}
                  data-testid="filter-venue"
                  className="w-full ledger-input text-[13px]"
                >
                  <option value="">AAAI + IJCAI (all 13,617 papers)</option>
                  <option value="venue:aaai">AAAI only (10,206 papers)</option>
                  <option value="venue:ijcai">IJCAI only (3,411 papers)</option>
                </select>
              </div>

              <div>
                <div className="flex items-center justify-between text-[13px] mb-1.5">
                  <span className="font-medium text-ink">
                    Publication window
                  </span>
                  <span className="text-muted tabular-nums">
                    {filters.yearMin}–{filters.yearMax}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <select
                    aria-label="Start year"
                    value={filters.yearMin}
                    onChange={(e) =>
                      updateFilters({
                        yearMin: Math.min(
                          Number(e.target.value),
                          filters.yearMax,
                        ),
                      })
                    }
                    className="ledger-input text-[13px] tabular-nums"
                  >
                    {[2021, 2022, 2023, 2024, 2025].map((y) => (
                      <option key={y} value={y}>
                        From {y}
                      </option>
                    ))}
                  </select>
                  <select
                    aria-label="End year"
                    value={filters.yearMax}
                    onChange={(e) =>
                      updateFilters({
                        yearMax: Math.max(
                          Number(e.target.value),
                          filters.yearMin,
                        ),
                      })
                    }
                    className="ledger-input text-[13px] tabular-nums"
                  >
                    {[2021, 2022, 2023, 2024, 2025].map((y) => (
                      <option key={y} value={y}>
                        To {y}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          )}

          {(viewMode === "researchers" || viewMode === "organizations") && (
            <p className="text-xs text-muted leading-relaxed">Paper-window filters require accepted support in that window. Weights and minimum shared-paper thresholds retain their full-period meaning. Results are bounded illustrative slices.</p>
          )}
          {/* Mode D: Curated Schema Presets */}
          {viewMode === "heterogeneous" && (
            <div>
              <label
                htmlFor="filter-preset"
                className="block text-[13px] font-medium text-ink mb-1.5"
              >
                Knowledge graph slice
              </label>
              <select
                id="filter-preset"
                value={filters.preset}
                onChange={(e) => updateFilters({ preset: e.target.value })}
                data-testid="filter-preset"
                className="w-full ledger-input text-[13px]"
              >
                <option value="topic_taxonomy_ecosystem">
                  10-Predicate ecosystem (all 5 labels)
                </option>
                <option value="researcher_paper_topic">
                  Researcher → Paper → Topic → Venue
                </option>
                <option value="researcher_organization">
                  Researcher → Affiliation → Organization
                </option>
                <option value="academia_industry_topics">
                  Cross-sector orgs & topic portfolios
                </option>
                <option value="paper_venue_citation">
                  Cited papers, venues & topics
                </option>
                <option value="custom">Custom label & predicate slice</option>
              </select>
            </div>
          )}

          {/* Mode A & B: Min Support Papers */}
          {(viewMode === "researchers" || viewMode === "organizations") && (
            <div>
              <div className="flex items-center justify-between text-[13px] mb-1">
                <label
                  htmlFor="filter-min-support"
                  className="font-medium text-ink"
                >
                  Min shared papers (full period)
                </label>
                <span className="text-muted tabular-nums">
                  ≥ {filters.minSupport}
                </span>
              </div>
              <input
                id="filter-min-support"
                type="range"
                min={1}
                max={10}
                step={1}
                value={filters.minSupport}
                onChange={(e) =>
                  updateFilters({ minSupport: Number(e.target.value) })
                }
                data-testid="filter-min-support"
                className="w-full accent-[var(--text)] cursor-pointer"
              />
            </div>
          )}

          {/* Subgraph Node Cap */}
          <div>
            <div className="flex items-center justify-between text-[13px] mb-1">
              <label
                htmlFor="filter-node-limit"
                className="font-medium text-ink"
              >
                Displayed node limit
              </label>
              <span className="text-muted tabular-nums">
                {filters.limit} nodes
              </span>
            </div>
            <input
              id="filter-node-limit"
              type="range"
              min={25}
              max={220}
              step={5}
              value={filters.limit}
              onChange={(e) => updateFilters({ limit: Number(e.target.value) })}
              data-testid="filter-node-limit"
              className="w-full accent-[var(--text)] cursor-pointer"
            />
          </div>
        </div>

        {/* 3. Progressive Disclosure: Advanced Parameters & Schema Slice */}
        <details
          className="group px-5 py-3.5 border-b border-border"
          open={viewMode === "heterogeneous" && filters.preset === "custom"}
        >
          <summary className="flex items-center justify-between cursor-pointer list-none text-[13px] font-medium text-muted hover:text-ink">
            <span>Advanced parameters & schema</span>
            <ChevronRight className="w-3.5 h-3.5 transition-transform group-open:rotate-90" />
          </summary>

          <div className="mt-3.5 space-y-3.5">
            {(viewMode === "researchers" || viewMode === "organizations") && (
              <>
                <div>
                  <div className="flex items-center justify-between text-[13px] mb-1">
                    <label htmlFor="filter-min-weight" className="text-ink">
                      Min fractional weight
                    </label>
                    <span className="text-muted tabular-nums">
                      {filters.minWeight.toFixed(2)}
                    </span>
                  </div>
                  <input
                    id="filter-min-weight"
                    type="range"
                    min={0}
                    max={3}
                    step={0.1}
                    value={filters.minWeight}
                    onChange={(e) =>
                      updateFilters({ minWeight: Number(e.target.value) })
                    }
                    className="w-full accent-[var(--text)] cursor-pointer"
                  />
                </div>

                <label className="flex items-center justify-between gap-2 text-[13px] text-ink cursor-pointer">
                  <span>Retain isolated nodes</span>
                  <input
                    type="checkbox"
                    checked={filters.includeIsolates}
                    onChange={(e) =>
                      updateFilters({ includeIsolates: e.target.checked })
                    }
                    className="rounded border-control"
                  />
                </label>
              </>
            )}

            {viewMode === "citations" && (
              <label className="flex items-center justify-between gap-2 text-[13px] text-ink cursor-pointer">
                <span>Include HAS_TOPIC (R5) nodes</span>
                <input
                  type="checkbox"
                  checked={filters.includeTopics}
                  onChange={(e) =>
                    updateFilters({ includeTopics: e.target.checked })
                  }
                  className="rounded border-control"
                />
              </label>
            )}

            {/* Entity Labels (5) */}
            <div>
              <div className="text-[13px] font-medium text-ink mb-1.5">
                Entity labels (5)
              </div>
              <div className="flex flex-wrap gap-1.5">
                {ALL_NODE_LABELS.map((lbl) => {
                  const checked = filters.nodeLabels.includes(lbl);
                  return (
                    <button
                      key={lbl}
                      type="button"
                      onClick={() => toggleNodeLabel(lbl)}
                      className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-[5px] text-xs border transition-colors ${
                        checked
                          ? "bg-raised border-control text-ink font-medium"
                          : "bg-surface border-border text-faint"
                      }`}
                    >
                      <span
                        className="w-2 h-2 rounded-full shrink-0"
                        style={{ backgroundColor: LABEL_COLORS[lbl] }}
                      />
                      <span>{lbl}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Predicates (10) */}
            <div>
              <div className="text-[13px] font-medium text-ink mb-1.5">
                Predicates (R1–R10)
              </div>
              <div className="space-y-1 max-h-48 overflow-y-auto pr-1">
                {ALL_RELATIONS.map((rel) => {
                  const checked = filters.relations.includes(rel);
                  return (
                    <label
                      key={rel}
                      className="flex items-center justify-between gap-2 px-2 py-1 rounded-[4px] hover:bg-raised cursor-pointer text-xs"
                    >
                      <span className="flex items-center gap-1.5 min-w-0">
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={() => toggleRelation(rel)}
                          className="rounded border-control"
                        />
                        <span className="font-mono text-faint">
                          {PREDICATE_R_CODE[rel]}
                        </span>
                        <span className="font-mono text-ink truncate">
                          {rel}
                        </span>
                      </span>
                    </label>
                  );
                })}
              </div>
            </div>
          </div>
        </details>

        {/* 4. Progressive Disclosure: Saved Views & Recent Trail */}
        <details className="group px-5 py-3.5 border-b border-border">
          <summary className="flex items-center justify-between cursor-pointer list-none text-[13px] font-medium text-muted hover:text-ink">
            <span className="flex items-center gap-1.5">
              <Bookmark className="w-3.5 h-3.5 text-faint" />
              <span>Saved views ({savedViews.length})</span>
            </span>
            <ChevronRight className="w-3.5 h-3.5 transition-transform group-open:rotate-90" />
          </summary>

          <div className="mt-3 space-y-2">
            <div className="space-y-1">
              {savedViews.map((bm) => (
                <button
                  key={bm.id}
                  type="button"
                  onClick={() => applySavedView(bm)}
                  className="w-full text-left px-2.5 py-1.5 rounded-[5px] text-[13px] text-muted hover:text-ink hover:bg-raised transition-colors flex items-center justify-between gap-2"
                >
                  <span className="truncate font-medium text-ink">
                    {bm.name}
                  </span>
                  <span className="text-xs text-faint shrink-0">
                    {bm.viewMode}
                  </span>
                </button>
              ))}
            </div>

            <div className="flex gap-1.5 pt-1">
              <input
                type="text"
                placeholder="Save current view as..."
                value={bookmarkName}
                onChange={(e) => setBookmarkName(e.target.value)}
                className="flex-1 ledger-input h-7 text-xs"
              />
              <button
                type="button"
                onClick={() => {
                  saveCurrentView(bookmarkName);
                  setBookmarkName("");
                }}
                className="ledger-btn h-7 px-2 text-xs"
                title="Save current filter configuration"
              >
                <Plus className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </details>

        {/* 5. Recent Inspection History (if any) */}
        {selectionHistory.length > 0 && (
          <div className="px-5 py-3.5">
            <div className="flex items-center gap-1.5 text-[13px] font-medium text-muted mb-2">
              <History className="w-3.5 h-3.5 text-faint" />
              <span>Recent selections</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {selectionHistory
                .slice()
                .reverse()
                .slice(0, 5)
                .map((item) => (
                  <button
                    key={`${item.type}-${item.id}`}
                    type="button"
                    onClick={() =>
                      item.type === "node"
                        ? selectNode(item.id, item.label)
                        : selectEdge(item.id, item.label)
                    }
                    className="px-2 py-1 rounded-[4px] bg-raised hover:bg-active text-xs text-ink truncate max-w-full transition-colors"
                    title={`${item.type}: ${item.label}`}
                  >
                    {item.label}
                  </button>
                ))}
            </div>
          </div>
        )}
      </aside>
    </>
  );
};
