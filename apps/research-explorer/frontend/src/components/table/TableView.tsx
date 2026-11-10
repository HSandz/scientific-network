import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowDown,
  ArrowUp,
  ChevronLeft,
  ChevronRight,
  Search,
} from "lucide-react";
import { explorerApi } from "../../lib/api";
import { LABEL_COLORS, PREDICATE_R_CODE } from "../../lib/colors";
import { useExplorerStore } from "../../stores/useExplorerStore";
import { EvidenceKind, NodeLabel, RelationType } from "../../types/explorer";

interface TableViewProps {
  onFocusNodeInGraph: (nodeId: string, name?: string) => void;
}

const NODE_LABELS: NodeLabel[] = [
  "Researcher",
  "Paper",
  "Organization",
  "Topic",
  "Venue",
];

const RELATIONS: RelationType[] = [
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

const EVIDENCE_PILL: Record<EvidenceKind, { label: string; className: string }> = {
  observed: { label: "Observed", className: "ledger-pill ledger-pill-pos" },
  inferred_topic: { label: "Inferred topic", className: "ledger-pill ledger-pill-warn" },
  curated_taxonomy: { label: "Curated taxonomy", className: "ledger-pill" },
  derived: { label: "Derived", className: "ledger-pill" },
};

export const TableView: React.FC<TableViewProps> = ({ onFocusNodeInGraph }) => {
  const {
    selectedNodeId,
    selectedEdgeId,
    selectNode,
    selectEdge,
  } = useExplorerStore();

  const [mode, setMode] = useState<"nodes" | "edges">("nodes");

  // Node table state
  const [nodeSearch, setNodeSearch] = useState("");
  const [nodeLabel, setNodeLabel] = useState<string>("Researcher");
  const [nodeSector, setNodeSector] = useState<string>("");
  const [nodeVenue, setNodeVenue] = useState<string>("");
  const [nodeSortBy, setNodeSortBy] = useState<string>("score");
  const [nodeSortOrder, setNodeSortOrder] = useState<"asc" | "desc">("desc");
  const [nodePage, setNodePage] = useState(1);

  // Edge table state
  const [edgeSearch, setEdgeSearch] = useState("");
  const [edgeRelation, setEdgeRelation] = useState<string>("COAUTHORED_WITH");
  const [edgeEvidenceKind, setEdgeEvidenceKind] = useState<string>("");
  const [edgeMinSupport, setEdgeMinSupport] = useState<number>(1);
  const [edgeSortBy, setEdgeSortBy] = useState<string>("support_count");
  const [edgeSortOrder, setEdgeSortOrder] = useState<"asc" | "desc">("desc");
  const [edgePage, setEdgePage] = useState(1);

  const pageSize = 25;

  const nodesQuery = useQuery({
    queryKey: [
      "table-nodes",
      nodeLabel,
      nodeSearch,
      nodeSector,
      nodeVenue,
      nodeSortBy,
      nodeSortOrder,
      nodePage,
    ],
    queryFn: ({ signal }) =>
      explorerApi.getTableNodes(
        {
          label: nodeLabel || undefined,
          q: nodeSearch || undefined,
          sector: nodeSector || undefined,
          venue: nodeVenue || undefined,
          sort_by: nodeSortBy,
          sort_order: nodeSortOrder,
          page: nodePage,
          page_size: pageSize,
        },
        signal
      ),
    enabled: mode === "nodes",
  });

  const edgesQuery = useQuery({
    queryKey: [
      "table-edges",
      edgeRelation,
      edgeEvidenceKind,
      edgeMinSupport,
      edgeSearch,
      edgeSortBy,
      edgeSortOrder,
      edgePage,
    ],
    queryFn: ({ signal }) =>
      explorerApi.getTableEdges(
        {
          relation: edgeRelation || undefined,
          evidence_kind: edgeEvidenceKind || undefined,
          min_support: edgeMinSupport,
          q: edgeSearch || undefined,
          sort_by: edgeSortBy,
          sort_order: edgeSortOrder,
          page: edgePage,
          page_size: pageSize,
        },
        signal
      ),
    enabled: mode === "edges",
  });

  const toggleNodeSort = (field: string) => {
    if (nodeSortBy === field) {
      setNodeSortOrder((o) => (o === "asc" ? "desc" : "asc"));
    } else {
      setNodeSortBy(field);
      setNodeSortOrder(field === "name" ? "asc" : "desc");
    }
    setNodePage(1);
  };

  const toggleEdgeSort = (field: string) => {
    if (edgeSortBy === field) {
      setEdgeSortOrder((o) => (o === "asc" ? "desc" : "asc"));
    } else {
      setEdgeSortBy(field);
      setEdgeSortOrder("desc");
    }
    setEdgePage(1);
  };

  return (
    <div
      data-testid="table-view"
      className="flex-1 flex flex-col min-h-0 overflow-hidden bg-ground px-3 sm:px-6 py-3 sm:py-5"
    >
      {/* Header & Filter Bar */}
      <div className="shrink-0 mb-3 sm:mb-4 space-y-2.5 sm:space-y-3">
        <div className="flex flex-wrap items-baseline justify-between gap-2 sm:gap-4">
          <div>
            <h1 className="text-base sm:text-xl font-semibold text-ink tracking-tight">
              Inventory ledger
            </h1>
            <p className="hidden sm:block text-[13px] text-muted mt-0.5">
              Server-paginated query across all release domain entities and accepted relationships.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="ledger-segmented" role="tablist">
              <button
                type="button"
                role="tab"
                aria-selected={mode === "nodes"}
                data-active={mode === "nodes"}
                onClick={() => setMode("nodes")}
                data-testid="table-mode-nodes"
                className="!px-2 sm:!px-2.5 !text-xs sm:!text-[13px]"
              >
                Domain nodes
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={mode === "edges"}
                data-active={mode === "edges"}
                onClick={() => setMode("edges")}
                data-testid="table-mode-edges"
                className="!px-2 sm:!px-2.5 !text-xs sm:!text-[13px]"
              >
                Accepted edges
              </button>
            </div>
          </div>
        </div>

        {/* Filter Controls Row */}
        {mode === "nodes" ? (
          <div className="flex flex-wrap items-center gap-2.5">
            <div className="relative flex-1 min-w-[220px] max-w-sm">
              <Search className="w-3.5 h-3.5 text-faint absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={nodeSearch}
                onChange={(e) => {
                  setNodeSearch(e.target.value);
                  setNodePage(1);
                }}
                placeholder="Filter by entity name or stable ID..."
                data-testid="table-node-search"
                className="w-full ledger-input pl-8 text-[13px]"
              />
            </div>

            <select
              aria-label="Entity label filter"
              value={nodeLabel}
              onChange={(e) => {
                setNodeLabel(e.target.value);
                setNodePage(1);
              }}
              data-testid="table-node-label-select"
              className="ledger-input text-[13px]"
            >
              <option value="">All 5 entity labels</option>
              {NODE_LABELS.map((lbl) => (
                <option key={lbl} value={lbl}>
                  {lbl}
                </option>
              ))}
            </select>

            {nodeLabel === "Organization" && (
              <select
                aria-label="Organization sector filter"
                value={nodeSector}
                onChange={(e) => {
                  setNodeSector(e.target.value);
                  setNodePage(1);
                }}
                className="ledger-input text-[13px]"
              >
                <option value="">All sectors</option>
                <option value="academia">Academia</option>
                <option value="industry">Industry</option>
                <option value="government">Government</option>
                <option value="nonprofit">Nonprofit</option>
              </select>
            )}

            {nodeLabel === "Paper" && (
              <select
                aria-label="Paper venue filter"
                value={nodeVenue}
                onChange={(e) => {
                  setNodeVenue(e.target.value);
                  setNodePage(1);
                }}
                className="ledger-input text-[13px]"
              >
                <option value="">All venues (AAAI + IJCAI)</option>
                <option value="venue:aaai">AAAI</option>
                <option value="venue:ijcai">IJCAI</option>
              </select>
            )}

            <div className="ml-auto text-[13px] text-muted tabular-nums">
              {nodesQuery.data ? (
                <>
                  Showing page <strong className="text-ink">{nodesQuery.data.page}</strong> of{" "}
                  <strong className="text-ink">{nodesQuery.data.total_pages.toLocaleString()}</strong> (
                  <strong className="text-ink">{nodesQuery.data.total.toLocaleString()}</strong>{" "}
                  matching entities)
                </>
              ) : (
                "Loading..."
              )}
            </div>
          </div>
        ) : (
          <div className="flex flex-wrap items-center gap-2.5">
            <div className="relative flex-1 min-w-[220px] max-w-sm">
              <Search className="w-3.5 h-3.5 text-faint absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={edgeSearch}
                onChange={(e) => {
                  setEdgeSearch(e.target.value);
                  setEdgePage(1);
                }}
                placeholder="Filter by source/target name or edge ID..."
                data-testid="table-edge-search"
                className="w-full ledger-input pl-8 text-[13px]"
              />
            </div>

            <select
              aria-label="Relationship predicate filter"
              value={edgeRelation}
              onChange={(e) => {
                setEdgeRelation(e.target.value);
                setEdgePage(1);
              }}
              data-testid="table-edge-relation-select"
              className="ledger-input text-[13px] font-mono"
            >
              <option value="">All 10 predicates (R1–R10)</option>
              {RELATIONS.map((rel) => (
                <option key={rel} value={rel}>
                  {PREDICATE_R_CODE[rel]} · {rel}
                </option>
              ))}
            </select>

            <select
              aria-label="Evidence class filter"
              value={edgeEvidenceKind}
              onChange={(e) => {
                setEdgeEvidenceKind(e.target.value);
                setEdgePage(1);
              }}
              className="ledger-input text-[13px]"
            >
              <option value="">All 4 evidence classes</option>
              <option value="observed">Observed (R1–R4)</option>
              <option value="inferred_topic">Inferred topic (R5)</option>
              <option value="curated_taxonomy">Curated taxonomy (R6)</option>
              <option value="derived">Derived (R7–R10)</option>
            </select>

            <label className="flex items-center gap-1.5 text-[13px] text-muted">
              <span>Min papers:</span>
              <input
                type="number"
                min={1}
                max={50}
                value={edgeMinSupport}
                onChange={(e) => {
                  setEdgeMinSupport(Math.max(1, Number(e.target.value) || 1));
                  setEdgePage(1);
                }}
                className="w-16 ledger-input text-[13px] tabular-nums text-right"
              />
            </label>

            <div className="ml-auto text-[13px] text-muted tabular-nums">
              {edgesQuery.data ? (
                <>
                  Showing page <strong className="text-ink">{edgesQuery.data.page}</strong> of{" "}
                  <strong className="text-ink">{edgesQuery.data.total_pages.toLocaleString()}</strong> (
                  <strong className="text-ink">{edgesQuery.data.total.toLocaleString()}</strong>{" "}
                  matching edges)
                </>
              ) : (
                "Loading..."
              )}
            </div>
          </div>
        )}
      </div>

      {/* Main Data Table Card */}
      <div className="flex-1 min-h-0 ledger-panel flex flex-col overflow-hidden">
        <div className="flex-1 overflow-auto">
          {mode === "nodes" ? (
            <table className="w-full text-left border-collapse">
              <thead className="sticky top-0 bg-surface border-b border-border z-10 text-xs text-muted">
                <tr>
                  <th className="sticky left-0 z-20 bg-surface py-2.5 px-3 sm:px-4 font-medium">
                    <button
                      type="button"
                      onClick={() => toggleNodeSort("name")}
                      className="inline-flex items-center gap-1 hover:text-ink"
                    >
                      <span>Entity &amp; stable ID</span>
                      {nodeSortBy === "name" &&
                        (nodeSortOrder === "asc" ? (
                          <ArrowUp className="w-3 h-3" />
                        ) : (
                          <ArrowDown className="w-3 h-3" />
                        ))}
                    </button>
                  </th>
                  <th className="hidden md:table-cell py-2.5 px-3 font-medium">
                    Label
                  </th>
                  <th className="hidden lg:table-cell py-2.5 px-3 font-medium">
                    Group &amp; metadata
                  </th>
                  <th className="py-2.5 px-2.5 sm:px-3 font-medium text-right">
                    <button
                      type="button"
                      onClick={() => toggleNodeSort("score")}
                      className="inline-flex items-center justify-end gap-1 hover:text-ink ml-auto"
                    >
                      <span className="hidden sm:inline">Full-projection score</span>
                      <span className="sm:hidden">Score</span>
                      {nodeSortBy === "score" &&
                        (nodeSortOrder === "asc" ? (
                          <ArrowUp className="w-3 h-3" />
                        ) : (
                          <ArrowDown className="w-3 h-3" />
                        ))}
                    </button>
                  </th>
                  <th className="py-2.5 px-2.5 sm:px-3 font-medium text-right">
                    <span className="hidden sm:inline">DB incident edges</span>
                    <span className="sm:hidden">Edges</span>
                  </th>
                  <th className="py-2.5 px-3 sm:px-4 font-medium text-right">
                    Action
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-rule text-xs sm:text-[13px]">
                {nodesQuery.data?.items.map((node) => {
                  const isSelected = selectedNodeId === node.id;
                  return (
                    <tr
                      key={node.id}
                      data-testid={`table-node-row-${node.id}`}
                      aria-selected={isSelected}
                      onClick={() => selectNode(node.id, node.name)}
                      className={`cursor-pointer transition-colors ${
                        isSelected ? "bg-active" : "hover:bg-raised/60"
                      }`}
                    >
                      <td
                        className={`sticky left-0 z-[5] py-2.5 px-3 sm:px-4 max-w-[165px] sm:max-w-md ${
                          isSelected ? "bg-active" : "bg-surface"
                        }`}
                      >
                        <div className="font-medium text-ink truncate">
                          {node.name}
                        </div>
                        <div className="font-mono text-[11px] sm:text-xs text-faint truncate">
                          <span className="md:hidden">{node.label} · </span>
                          {node.id}
                        </div>
                      </td>

                      <td className="hidden md:table-cell py-2.5 px-3 whitespace-nowrap">
                        <span className="inline-flex items-center gap-1.5 text-ink font-medium">
                          <span
                            className="w-2 h-2 rounded-full shrink-0"
                            style={{
                              backgroundColor:
                                LABEL_COLORS[node.label] || "#6e7681",
                            }}
                          />
                          <span>{node.label}</span>
                        </span>
                      </td>

                      <td className="hidden lg:table-cell py-2.5 px-3 text-muted whitespace-nowrap">
                        <div className="font-mono text-ink">{node.group}</div>
                        <div className="text-faint">
                          {node.year && `Year ${node.year} `}
                          {node.sector && `Sector: ${node.sector} `}
                          {node.country_code && `(${node.country_code})`}
                        </div>
                      </td>

                      <td className="py-2.5 px-2.5 sm:px-3 text-right tabular-nums whitespace-nowrap">
                        <div className="font-medium text-ink">
                          {node.score.toFixed(3)}
                        </div>
                        {node.full_metrics?.betweenness !== undefined &&
                          node.full_metrics?.betweenness !== null && (
                            <div className="hidden sm:block text-faint">
                              betw {node.full_metrics.betweenness.toFixed(4)}
                            </div>
                          )}
                      </td>

                      <td className="py-2.5 px-2.5 sm:px-3 text-right tabular-nums whitespace-nowrap">
                        {node.displayed_degree > 0 ? (
                          <span className="font-medium text-ink">
                            {node.displayed_degree.toLocaleString()} edges
                          </span>
                        ) : (
                          <span className="text-faint">—</span>
                        )}
                      </td>

                      <td className="py-2.5 px-3 sm:px-4 text-right whitespace-nowrap">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            onFocusNodeInGraph(node.id, node.name);
                          }}
                          className="ledger-btn h-6 px-2 text-[11px] font-medium text-ink hover:text-accent"
                        >
                          <span className="hidden sm:inline">Focus in graph →</span>
                          <span className="sm:hidden">Graph →</span>
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          ) : (
            <table className="w-full text-left border-collapse">
              <thead className="sticky top-0 bg-surface border-b border-border z-10 text-xs text-muted">
                <tr>
                  <th className="sticky left-0 z-20 bg-surface py-2.5 px-3 sm:px-4 font-medium">
                    <span className="hidden md:inline">Predicate</span>
                    <span className="md:hidden">Relationship</span>
                  </th>
                  <th className="hidden md:table-cell py-2.5 px-3 font-medium">
                    Source entity
                  </th>
                  <th className="hidden md:table-cell py-2.5 px-3 font-medium">
                    Target entity
                  </th>
                  <th className="hidden lg:table-cell py-2.5 px-3 font-medium">
                    Evidence class
                  </th>
                  <th className="py-2.5 px-2.5 sm:px-3 font-medium text-right">
                    <button
                      type="button"
                      onClick={() => toggleEdgeSort("support_count")}
                      className="inline-flex items-center justify-end gap-1 hover:text-ink ml-auto"
                    >
                      <span className="hidden sm:inline">Support papers</span>
                      <span className="sm:hidden">Papers</span>
                      {edgeSortBy === "support_count" &&
                        (edgeSortOrder === "asc" ? (
                          <ArrowUp className="w-3 h-3" />
                        ) : (
                          <ArrowDown className="w-3 h-3" />
                        ))}
                    </button>
                  </th>
                  <th className="hidden sm:table-cell py-2.5 px-3 font-medium text-right">
                    <button
                      type="button"
                      onClick={() => toggleEdgeSort("fractional_weight")}
                      className="inline-flex items-center justify-end gap-1 hover:text-ink ml-auto"
                    >
                      <span>Fractional weight</span>
                      {edgeSortBy === "fractional_weight" &&
                        (edgeSortOrder === "asc" ? (
                          <ArrowUp className="w-3 h-3" />
                        ) : (
                          <ArrowDown className="w-3 h-3" />
                        ))}
                    </button>
                  </th>
                  <th className="py-2.5 px-3 sm:px-4 font-medium text-right">
                    Provenance
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-rule text-xs sm:text-[13px]">
                {edgesQuery.data?.items.map((edge) => {
                  const isSelected = selectedEdgeId === edge.edge_id;
                  const evPill =
                    EVIDENCE_PILL[edge.evidence_kind] || EVIDENCE_PILL.observed;
                  return (
                    <tr
                      key={edge.edge_id}
                      data-testid={`table-edge-row-${edge.edge_id}`}
                      aria-selected={isSelected}
                      onClick={() =>
                        selectEdge(
                          edge.edge_id,
                          `${edge.source_name || edge.source} → ${edge.relation} → ${edge.target_name || edge.target}`
                        )
                      }
                      className={`cursor-pointer transition-colors ${
                        isSelected ? "bg-active" : "hover:bg-raised/60"
                      }`}
                    >
                      <td
                        className={`sticky left-0 z-[5] py-2.5 px-3 sm:px-4 max-w-[195px] md:max-w-none md:whitespace-nowrap ${
                          isSelected ? "bg-active" : "bg-surface"
                        }`}
                      >
                        <div className="font-mono font-medium text-ink truncate">
                          {PREDICATE_R_CODE[edge.relation] || ""} {edge.relation}
                        </div>
                        <div className="md:hidden text-[11px] text-muted truncate mt-0.5">
                          {edge.source_name || edge.source} →{" "}
                          {edge.target_name || edge.target}
                        </div>
                      </td>

                      <td className="hidden md:table-cell py-2.5 px-3 max-w-[240px]">
                        <div className="font-medium text-ink truncate">
                          {edge.source_name || edge.source}
                        </div>
                        <div className="text-faint">{edge.source_label}</div>
                      </td>

                      <td className="hidden md:table-cell py-2.5 px-3 max-w-[240px]">
                        <div className="font-medium text-ink truncate">
                          {edge.target_name || edge.target}
                        </div>
                        <div className="text-faint">{edge.target_label}</div>
                      </td>

                      <td className="hidden lg:table-cell py-2.5 px-3 whitespace-nowrap">
                        <span className={evPill.className}>{evPill.label}</span>
                      </td>

                      <td className="py-2.5 px-2.5 sm:px-3 text-right tabular-nums whitespace-nowrap font-medium text-ink">
                        {edge.support_count.toLocaleString()}
                      </td>

                      <td className="hidden sm:table-cell py-2.5 px-3 text-right tabular-nums whitespace-nowrap text-muted">
                        {typeof edge.fractional_weight === "number"
                          ? edge.fractional_weight.toFixed(4)
                          : "—"}
                      </td>

                      <td className="py-2.5 px-3 sm:px-4 text-right whitespace-nowrap">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            selectEdge(
                              edge.edge_id,
                              `${edge.source_name || edge.source} → ${edge.relation} → ${edge.target_name || edge.target}`
                            );
                          }}
                          className="ledger-btn h-6 px-2 text-[11px] font-medium text-ink hover:text-accent"
                        >
                          <span className="hidden sm:inline">Inspect evidence →</span>
                          <span className="sm:hidden">Evidence →</span>
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>

        {/* Pagination Bar */}
        <div className="shrink-0 px-4 py-2.5 border-t border-border bg-surface flex items-center justify-between text-xs">
          {mode === "nodes" ? (
            <>
              <span className="text-muted tabular-nums">
                Page {nodePage} of {nodesQuery.data?.total_pages || 1} · 25 rows per page
              </span>
              <div className="flex items-center gap-1.5">
                <button
                  type="button"
                  disabled={nodePage <= 1}
                  onClick={() => setNodePage((p) => Math.max(1, p - 1))}
                  className="ledger-btn h-7 px-2.5 text-xs"
                >
                  <ChevronLeft className="w-3.5 h-3.5" />
                  <span>Previous</span>
                </button>
                <button
                  type="button"
                  disabled={
                    !nodesQuery.data || nodePage >= nodesQuery.data.total_pages
                  }
                  onClick={() => setNodePage((p) => p + 1)}
                  className="ledger-btn h-7 px-2.5 text-xs"
                >
                  <span>Next</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </>
          ) : (
            <>
              <span className="text-muted tabular-nums">
                Page {edgePage} of {edgesQuery.data?.total_pages || 1} · 25 rows per page
              </span>
              <div className="flex items-center gap-1.5">
                <button
                  type="button"
                  disabled={edgePage <= 1}
                  onClick={() => setEdgePage((p) => Math.max(1, p - 1))}
                  className="ledger-btn h-7 px-2.5 text-xs"
                >
                  <ChevronLeft className="w-3.5 h-3.5" />
                  <span>Previous</span>
                </button>
                <button
                  type="button"
                  disabled={
                    !edgesQuery.data || edgePage >= edgesQuery.data.total_pages
                  }
                  onClick={() => setEdgePage((p) => p + 1)}
                  className="ledger-btn h-7 px-2.5 text-xs"
                >
                  <span>Next</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
