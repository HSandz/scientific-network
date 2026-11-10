import React, { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ExternalLink, X } from "lucide-react";
import { explorerApi } from "../../lib/api";
import { useModalDialog } from "../../lib/useModalDialog";
import { useExplorerStore } from "../../stores/useExplorerStore";
import { EntityPicker } from "./EntityPicker";

const COMPARE_PRESETS = [
  {
    label: "Shanghai Jiao Tong Univ vs Tencent",
    left: "organization:I183067930",
    right: "organization:I2250653659",
  },
  {
    label: "Tsinghua Univ vs Alibaba Group",
    left: "organization:I99065089",
    right: "organization:I4210095624",
  },
  {
    label: "Peking Univ vs Microsoft (USA)",
    left: "organization:I20231570",
    right: "organization:I1290206253",
  },
];

export const CompareModal: React.FC = () => {
  const {
    compareModalOpen,
    setCompareModalOpen,
    compareLeftId,
    compareRightId,
    selectNode,
    selectEdge,
  } = useExplorerStore();

  const [leftInput, setLeftInput] = useState(compareLeftId);
  const [rightInput, setRightInput] = useState(compareRightId);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  const dialogRef = useModalDialog({
    isOpen: compareModalOpen,
    onClose: () => setCompareModalOpen(false),
    initialFocusRef: closeButtonRef,
  });

  useEffect(() => {
    setLeftInput(compareLeftId);
    setRightInput(compareRightId);
  }, [compareLeftId, compareRightId]);

  const compareQuery = useQuery({
    queryKey: ["compare-entities", compareLeftId, compareRightId],
    queryFn: () => explorerApi.compareEntities(compareLeftId, compareRightId),
    enabled: compareModalOpen && Boolean(compareLeftId && compareRightId),
  });

  if (!compareModalOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/55"
      onClick={() => setCompareModalOpen(false)}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="compare-modal-title"
        tabIndex={-1}
        className="w-full max-w-3xl bg-surface rounded-[8px] border border-border overflow-hidden flex flex-col max-h-[85vh] outline-none"
        onClick={(e) => e.stopPropagation()}
        data-testid="compare-modal"
      >
        <div className="px-5 py-3.5 border-b border-border flex items-center justify-between gap-3">
          <div>
            <h2
              id="compare-modal-title"
              className="text-base font-semibold text-ink"
            >
              Entity collaboration & topic portfolio comparison
            </h2>
            <p className="text-xs text-muted mt-0.5">
              Compare shared core papers, direct relationships, shared neighbors, and fractional topic portfolios.
            </p>
          </div>
          <button
            ref={closeButtonRef}
            type="button"
            onClick={() => setCompareModalOpen(false)}
            aria-label="Close comparison"
            className="ledger-btn min-h-[36px] sm:h-7 px-2.5 text-xs shrink-0"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="p-5 overflow-y-auto space-y-4 text-xs">
          {/* Quick Presets */}
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-xs font-medium text-muted mr-1">
              Comparison presets:
            </span>
            {COMPARE_PRESETS.map((p) => (
              <button
                key={p.label}
                type="button"
                onClick={() => setCompareModalOpen(true, p.left, p.right)}
                className="px-2.5 py-1 rounded-[5px] bg-ground hover:bg-raised text-ink border border-border text-xs transition-colors"
              >
                {p.label}
              </button>
            ))}
          </div>

          {/* Searchable Entity Pickers */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <EntityPicker
              label="Left entity"
              valueId={leftInput}
              resolvedName={
                compareQuery.data?.left_node.id === leftInput
                  ? compareQuery.data.left_node.name
                  : undefined
              }
              resolvedLabel={
                compareQuery.data?.left_node.id === leftInput
                  ? compareQuery.data.left_node.label
                  : undefined
              }
              onChange={(id) => {
                setLeftInput(id);
                setCompareModalOpen(true, id, rightInput);
              }}
              testIdPrefix="compare-left"
            />
            <EntityPicker
              label="Right entity"
              valueId={rightInput}
              resolvedName={
                compareQuery.data?.right_node.id === rightInput
                  ? compareQuery.data.right_node.name
                  : undefined
              }
              resolvedLabel={
                compareQuery.data?.right_node.id === rightInput
                  ? compareQuery.data.right_node.label
                  : undefined
              }
              onChange={(id) => {
                setRightInput(id);
                setCompareModalOpen(true, leftInput, id);
              }}
              testIdPrefix="compare-right"
            />
          </div>

          {compareQuery.isLoading ? (
            <div className="py-10 text-center text-muted">
              Computing comparison from Neo4j...
            </div>
          ) : compareQuery.data ? (
            <div className="space-y-4">
              {/* Side by side cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {[compareQuery.data.left_node, compareQuery.data.right_node].map(
                  (node) => (
                    <div
                      key={node.id}
                      className="p-3.5 rounded-[8px] bg-ground border border-border"
                    >
                      <div className="flex items-center justify-between text-xs text-muted">
                        <span className="font-medium capitalize">
                          {node.label}{" "}
                          {node.sector ? `· ${node.sector}` : ""}{" "}
                          {node.country_code ? `(${node.country_code})` : ""}
                        </span>
                        <button
                          type="button"
                          onClick={() => {
                            selectNode(node.id, node.name);
                            setCompareModalOpen(false);
                          }}
                          className="text-ink font-medium hover:underline"
                        >
                          Inspect dossier →
                        </button>
                      </div>
                      <div className="text-sm font-semibold text-ink mt-1">
                        {node.name}
                      </div>
                      <div className="text-xs font-mono text-faint mt-0.5 tabular-nums">
                        {node.id} · Score: {node.score.toFixed(2)}
                      </div>
                    </div>
                  )
                )}
              </div>

              {/* Direct Edges */}
              <div className="p-3.5 rounded-[8px] border border-border bg-ground">
                <div className="font-semibold text-ink mb-2">
                  Direct accepted relationships (
                  {compareQuery.data.direct_edges.length})
                </div>
                {compareQuery.data.direct_edges.length === 0 ? (
                  <div className="text-muted">
                    No direct edge between these two entities.
                  </div>
                ) : (
                  <div className="space-y-1.5">
                    {compareQuery.data.direct_edges.map((edge) => (
                      <div
                        key={edge.edge_id}
                        className="flex items-center justify-between p-2.5 rounded-[6px] bg-surface border border-border"
                      >
                        <div className="tabular-nums">
                          <span className="font-mono font-semibold text-ink">
                            {edge.relation}
                          </span>{" "}
                          <span className="text-muted">
                            · support = {edge.support_count} papers
                            {edge.fractional_weight
                              ? ` · fractional weight = ${edge.fractional_weight.toFixed(3)}`
                              : ""}
                          </span>
                        </div>
                        <button
                          type="button"
                          onClick={() => {
                            selectEdge(edge.edge_id, edge.relation);
                            setCompareModalOpen(false);
                          }}
                          className="ledger-btn h-7 px-2.5 text-xs"
                        >
                          Inspect provenance
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Shared Core Papers */}
              <div className="p-3.5 rounded-[8px] border border-border bg-ground">
                <div className="font-semibold text-ink mb-2">
                  Shared core papers ({compareQuery.data.shared_papers.length})
                </div>
                {compareQuery.data.shared_papers.length === 0 ? (
                  <div className="text-muted">No shared core papers found.</div>
                ) : (
                  <div className="space-y-1.5 max-h-48 overflow-y-auto">
                    {compareQuery.data.shared_papers.map((p) => (
                      <div
                        key={p.paper_id}
                        className="flex items-center justify-between gap-2 p-2.5 rounded-[6px] bg-surface border border-border"
                      >
                        <div className="min-w-0">
                          <button
                            type="button"
                            onClick={() => {
                              selectNode(p.paper_id, p.title);
                              setCompareModalOpen(false);
                            }}
                            className="font-medium text-ink hover:underline truncate block text-left"
                          >
                            {p.title}
                          </button>
                          <div className="text-xs font-mono text-faint tabular-nums">
                            {p.paper_id} · {p.year}
                          </div>
                        </div>
                        {p.official_url && (
                          <a
                            href={p.official_url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-ink hover:underline shrink-0 flex items-center gap-1 text-xs"
                          >
                            <span>Proceedings</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Side-by-Side Topic Portfolios */}
              {(compareQuery.data.left_topics.length > 0 ||
                compareQuery.data.right_topics.length > 0) && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div className="p-3.5 rounded-[8px] border border-border bg-ground">
                    <div className="font-semibold text-ink mb-2">
                      {compareQuery.data.left_node.name} top topics
                    </div>
                    <div className="space-y-1.5">
                      {compareQuery.data.left_topics.slice(0, 6).map((t) => (
                        <div
                          key={t.topic_id}
                          className="flex items-center justify-between text-xs tabular-nums"
                        >
                          <span className="truncate text-ink">{t.topic}</span>
                          <span className="text-muted shrink-0">
                            {t.supported_paper_count} papers (
                            {(t.fractional_topic_portfolio_share * 100).toFixed(
                              1
                            )}
                            %)
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="p-3.5 rounded-[8px] border border-border bg-ground">
                    <div className="font-semibold text-ink mb-2">
                      {compareQuery.data.right_node.name} top topics
                    </div>
                    <div className="space-y-1.5">
                      {compareQuery.data.right_topics.slice(0, 6).map((t) => (
                        <div
                          key={t.topic_id}
                          className="flex items-center justify-between text-xs tabular-nums"
                        >
                          <span className="truncate text-ink">{t.topic}</span>
                          <span className="text-muted shrink-0">
                            {t.supported_paper_count} papers (
                            {(t.fractional_topic_portfolio_share * 100).toFixed(
                              1
                            )}
                            %)
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
};
