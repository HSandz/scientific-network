import React, { useEffect, useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { X } from "lucide-react";
import { explorerApi } from "../../lib/api";
import { useModalDialog } from "../../lib/useModalDialog";
import { useExplorerStore } from "../../stores/useExplorerStore";
import { EntityPicker } from "./EntityPicker";

const EXAMPLE_PATHS = [
  {
    label: "Bo An ↔ Bowen Baker (Coauthor bridge)",
    source: "researcher:openalex:A5017743551",
    target: "researcher:openalex:A5000021048",
    mode: "collaboration",
  },
  {
    label: "Shanghai Jiao Tong Univ ↔ Tencent",
    source: "organization:I183067930",
    target: "organization:I2250653659",
    mode: "heterogeneous",
  },
  {
    label: "Informer (2021) ↔ Causal inference topic",
    source: "paper:aaai:2021:17325",
    target: "topic:causal-inference",
    mode: "heterogeneous",
  },
];

export const PathFinderModal: React.FC = () => {
  const {
    pathFinderOpen,
    setPathFinderOpen,
    selectedNodeId,
    enterPathView,
    selectNode,
    selectEdge,
    setWorkspaceTab,
  } = useExplorerStore();

  const [sourceId, setSourceId] = useState(
    selectedNodeId || "researcher:openalex:A5017743551"
  );
  const [targetId, setTargetId] = useState("organization:I2250653659");
  const [mode, setMode] = useState("heterogeneous");
  const [maxHops, setMaxHops] = useState(4);

  const closeButtonRef = useRef<HTMLButtonElement>(null);

  const dialogRef = useModalDialog({
    isOpen: pathFinderOpen,
    onClose: () => setPathFinderOpen(false),
    initialFocusRef: closeButtonRef,
  });

  // Synchronize sourceId when modal opens with an active node selection
  useEffect(() => {
    if (pathFinderOpen && selectedNodeId) {
      setSourceId(selectedNodeId);
    }
  }, [pathFinderOpen, selectedNodeId]);

  const pathMutation = useMutation({
    mutationFn: () =>
      explorerApi.findPath({
        source_id: sourceId.trim(),
        target_id: targetId.trim(),
        mode,
        max_hops: maxHops,
      }),
  });

  if (!pathFinderOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/55"
      onClick={() => setPathFinderOpen(false)}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="path-finder-title"
        tabIndex={-1}
        className="w-full max-w-2xl bg-surface rounded-[8px] border border-border overflow-hidden flex flex-col max-h-[85vh] outline-none"
        onClick={(e) => e.stopPropagation()}
        data-testid="path-finder-modal"
      >
        <div className="px-5 py-3.5 border-b border-border flex items-center justify-between gap-3">
          <div>
            <h2
              id="path-finder-title"
              className="text-base font-semibold text-ink"
            >
              Bounded shortest-path discovery
            </h2>
            <p className="text-xs text-muted mt-0.5">
              Find and verify connection chains between any two entities in Neo4j (bounded to ≤ 4 hops).
            </p>
          </div>
          <button
            ref={closeButtonRef}
            type="button"
            onClick={() => setPathFinderOpen(false)}
            aria-label="Close path finder"
            className="ledger-btn min-h-[36px] sm:h-7 px-2.5 text-xs shrink-0"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="p-5 overflow-y-auto space-y-4 text-xs">
          {/* Example connection queries */}
          <div>
            <div className="text-xs font-medium text-muted mb-1.5">
              Example connection queries
            </div>
            <div className="flex flex-wrap gap-1.5">
              {EXAMPLE_PATHS.map((ex) => (
                <button
                  key={ex.label}
                  type="button"
                  onClick={() => {
                    setSourceId(ex.source);
                    setTargetId(ex.target);
                    setMode(ex.mode);
                  }}
                  className="px-2.5 py-1 rounded-[5px] bg-ground hover:bg-raised text-ink border border-border text-xs transition-colors"
                >
                  {ex.label}
                </button>
              ))}
            </div>
          </div>

          {/* Searchable Entity Pickers */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <EntityPicker
              label="Source entity"
              valueId={sourceId}
              onChange={(id) => setSourceId(id)}
              testIdPrefix="path-source"
            />
            <EntityPicker
              label="Target entity"
              valueId={targetId}
              onChange={(id) => setTargetId(id)}
              testIdPrefix="path-target"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 items-end">
            <div>
              <label className="block font-medium text-ink mb-1">
                Traversal mode
              </label>
              <select
                value={mode}
                onChange={(e) => setMode(e.target.value)}
                className="w-full ledger-input text-xs"
              >
                <option value="heterogeneous">
                  Heterogeneous (all predicates)
                </option>
                <option value="collaboration">
                  Collaboration (coauthor / org / authored)
                </option>
                <option value="citation_directed">
                  Directed citations (citing → cited)
                </option>
                <option value="citation_undirected">
                  Undirected citation chain
                </option>
              </select>
            </div>

            <div>
              <label className="block font-medium text-ink mb-1">
                Max hops (1–6)
              </label>
              <input
                type="number"
                min={1}
                max={6}
                value={maxHops}
                onChange={(e) =>
                  setMaxHops(Math.min(6, Math.max(1, Number(e.target.value))))
                }
                className="w-full ledger-input text-xs tabular-nums"
              />
            </div>

            <button
              type="button"
              onClick={() => pathMutation.mutate()}
              disabled={pathMutation.isPending}
              data-testid="run-path-search-btn"
              className="ledger-btn ledger-btn-primary text-xs w-full"
            >
              {pathMutation.isPending ? "Searching Neo4j..." : "Find shortest path"}
            </button>
          </div>

          {/* Results */}
          {pathMutation.data && (
            <div className="p-4 rounded-[8px] bg-ground border border-border space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <span className="font-semibold text-sm text-ink">
                    {pathMutation.data.found
                      ? `Path Found (${pathMutation.data.hop_count} hops)`
                      : "No Path Found within Hop Limit"}
                  </span>
                  <p className="text-xs text-muted mt-0.5">
                    {pathMutation.data.direction_note}
                  </p>
                </div>
                {pathMutation.data.found && (
                  <button
                    type="button"
                    onClick={() => {
                      if (!pathMutation.data) return;
                      enterPathView(pathMutation.data);
                      setPathFinderOpen(false);
                    }}
                    className="ledger-btn ledger-btn-primary h-8 px-3 text-xs"
                  >
                    Visualize path on canvas
                  </button>
                )}
              </div>

              {pathMutation.data.found && (
                <div className="space-y-1.5">
                  {pathMutation.data.edges.map((edge, idx) => (
                    <div
                      key={edge.edge_id}
                      className="p-2.5 rounded-[6px] bg-surface border border-border flex items-center justify-between gap-2"
                    >
                      <div className="min-w-0">
                        <span className="font-mono text-xs text-faint mr-2 tabular-nums">
                          Step {idx + 1}:
                        </span>
                        <button
                          type="button"
                          onClick={() => {
                            selectNode(edge.source, edge.source_name || edge.source);
                            setPathFinderOpen(false);
                          }}
                          className="font-medium text-ink hover:underline"
                        >
                          {edge.source_name || edge.source}
                        </button>
                        <span className="mx-2 px-1.5 py-0.5 rounded bg-raised font-mono text-xs text-ink">
                          {edge.relation}
                        </span>
                        <button
                          type="button"
                          onClick={() => {
                            selectNode(edge.target, edge.target_name || edge.target);
                            setPathFinderOpen(false);
                          }}
                          className="font-medium text-ink hover:underline"
                        >
                          {edge.target_name || edge.target}
                        </button>
                      </div>
                      <button
                        type="button"
                        onClick={() => {
                          selectEdge(edge.edge_id, edge.relation);
                          setPathFinderOpen(false);
                        }}
                        className="ledger-btn h-7 px-2.5 text-xs shrink-0"
                      >
                        Evidence
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
