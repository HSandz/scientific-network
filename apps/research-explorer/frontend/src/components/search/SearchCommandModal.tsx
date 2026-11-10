import React, { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search, X } from "lucide-react";
import { explorerApi } from "../../lib/api";
import { LABEL_COLORS } from "../../lib/colors";
import { useModalDialog } from "../../lib/useModalDialog";
import { useExplorerStore } from "../../stores/useExplorerStore";
import { NodeLabel } from "../../types/explorer";

interface SearchCommandModalProps {
  onFocusNodeInGraph: (nodeId: string, name?: string) => void;
}

const LABELS: NodeLabel[] = [
  "Researcher",
  "Paper",
  "Organization",
  "Topic",
  "Venue",
];

const QUICK_SUGGESTIONS = [
  { label: "Bo An (top bridge researcher)", query: "Bo An" },
  { label: "Piotr Faliszewski (beyond top-100)", query: "Piotr Faliszewski" },
  { label: "Informer (top cited paper)", query: "Informer" },
  { label: "Undergraduate Games Corpus", query: "Undergraduate Games Corpus" },
  { label: "Shanghai Jiao Tong University", query: "Shanghai Jiao Tong University" },
  { label: "Tencent (China)", query: "Tencent" },
  { label: "Representation learning (topic)", query: "Representation learning" },
];

export const SearchCommandModal: React.FC<SearchCommandModalProps> = ({
  onFocusNodeInGraph,
}) => {
  const {
    searchModalOpen,
    setSearchModalOpen,
    selectNode,
  } = useExplorerStore();

  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [selectedLabel, setSelectedLabel] = useState<NodeLabel | "">("");
  const [activeIndex, setActiveIndex] = useState<number>(-1);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const dialogRef = useModalDialog({
    isOpen: searchModalOpen,
    onClose: () => setSearchModalOpen(false),
    initialFocusRef: inputRef,
  });

  useEffect(() => {
    if (searchModalOpen) {
      setQuery("");
      setDebouncedQuery("");
      setActiveIndex(-1);
    }
  }, [searchModalOpen]);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query.trim());
    }, 150);
    return () => clearTimeout(timer);
  }, [query]);

  const searchQuery = useQuery({
    queryKey: ["global-search", debouncedQuery, selectedLabel],
    queryFn: ({ signal }) =>
      explorerApi.search(
        {
          q: debouncedQuery,
          label: selectedLabel ? [selectedLabel] : undefined,
          limit: 30,
        },
        signal
      ),
    enabled: searchModalOpen && debouncedQuery.length >= 1,
  });

  const results = searchQuery.data?.results || [];

  useEffect(() => {
    setActiveIndex(-1);
  }, [debouncedQuery, selectedLabel, results.length]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (results.length === 0) return;

    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIndex((prev) => (prev + 1) % results.length);
      return;
    }

    if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex((prev) => (prev <= 0 ? results.length - 1 : prev - 1));
      return;
    }

    if (e.key === "Enter") {
      if (activeIndex >= 0 && activeIndex < results.length) {
        e.preventDefault();
        const item = results[activeIndex];
        onFocusNodeInGraph(item.id, item.name);
        setSearchModalOpen(false);
      }
    }
  };

  if (!searchModalOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-8 sm:pt-16 px-3 sm:px-4 bg-black/55"
      onClick={() => setSearchModalOpen(false)}
      data-testid="search-modal-backdrop"
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="global-search-heading"
        tabIndex={-1}
        className="w-full max-w-2xl bg-surface rounded-[8px] border border-border overflow-hidden flex flex-col max-h-[85vh] sm:max-h-[80vh] outline-none"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={handleKeyDown}
        data-testid="search-modal"
      >
        <h2 id="global-search-heading" className="sr-only">
          Search graph entities and papers
        </h2>

        {/* Search Input Bar */}
        <div className="px-4 py-3 border-b border-border flex items-center gap-3">
          <Search className="w-4 h-4 text-muted shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search all 47,875 entities by name, paper title, DOI, OpenAlex ID, or topic..."
            data-testid="global-search-input"
            className="flex-1 bg-transparent text-sm text-ink placeholder-[var(--faint)] focus:outline-none"
          />
          {query && (
            <button
              type="button"
              onClick={() => setQuery("")}
              className="text-xs text-muted hover:text-ink px-1"
            >
              Clear
            </button>
          )}
          <button
            type="button"
            onClick={() => setSearchModalOpen(false)}
            data-testid="close-search-modal"
            aria-label="Close search"
            className="ledger-btn min-h-[36px] sm:h-7 px-2.5 text-xs"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Entity Type Filter Pills */}
        <div className="px-4 py-2 bg-ground border-b border-border flex flex-wrap items-center gap-1.5">
          <button
            type="button"
            onClick={() => setSelectedLabel("")}
            className={`px-2.5 py-1 rounded-[5px] text-xs font-medium border transition-colors ${
              selectedLabel === ""
                ? "bg-active border-control text-ink"
                : "bg-surface border-border text-muted hover:text-ink"
            }`}
          >
            All types
            {searchQuery.data ? ` (${searchQuery.data.total_matches})` : ""}
          </button>
          {LABELS.map((lbl) => {
            const count = searchQuery.data?.grouped_counts?.[lbl];
            const active = selectedLabel === lbl;
            return (
              <button
                key={lbl}
                type="button"
                onClick={() =>
                  setSelectedLabel(selectedLabel === lbl ? "" : lbl)
                }
                data-testid={`search-filter-${lbl}`}
                className={`px-2.5 py-1 rounded-[5px] text-xs font-medium border transition-colors flex items-center gap-1.5 ${
                  active
                    ? "bg-active border-control text-ink"
                    : "bg-surface border-border text-muted hover:text-ink"
                }`}
              >
                <span
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: LABEL_COLORS[lbl] }}
                />
                <span>{lbl}</span>
                {count !== undefined && (
                  <span className="tabular-nums">({count})</span>
                )}
              </button>
            );
          })}
        </div>

        {/* Results List */}
        <div className="flex-1 overflow-y-auto p-3 divide-y divide-rule">
          {!debouncedQuery ? (
            <div className="py-3 px-2 space-y-2.5">
              <div className="text-xs font-medium text-muted">
                Suggested queries (including entities beyond top-100 default view)
              </div>
              <div className="flex flex-wrap gap-2">
                {QUICK_SUGGESTIONS.map((item) => (
                  <button
                    key={item.query}
                    type="button"
                    onClick={() => setQuery(item.query)}
                    data-testid={`search-suggestion-${item.query}`}
                    className="px-3 py-1.5 rounded-[6px] text-xs bg-ground hover:bg-raised text-ink border border-border transition-colors"
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </div>
          ) : searchQuery.isLoading ? (
            <div className="py-10 text-center text-xs text-muted">
              Searching Neo4j release graph...
            </div>
          ) : results.length === 0 ? (
            <div className="py-10 text-center text-xs text-muted">
              No matching entities found for &ldquo;{debouncedQuery}&rdquo;.
            </div>
          ) : (
            results.map((item, idx) => {
              const isItemActive = idx === activeIndex;
              return (
                <div
                  key={item.id}
                  id={`search-result-item-${idx}`}
                  data-testid={`search-result-${item.id}`}
                  className={`py-2.5 px-2.5 flex items-center justify-between gap-3 transition-colors ${
                    isItemActive ? "bg-active" : "hover:bg-raised/60"
                  }`}
                >
                  <div
                    className="min-w-0 flex-1 cursor-pointer"
                    onClick={() => {
                      selectNode(item.id, item.name);
                      setSearchModalOpen(false);
                    }}
                  >
                    <div className="flex items-center gap-2">
                      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-raised text-xs font-medium text-ink shrink-0">
                        <span
                          className="w-2 h-2 rounded-full"
                          style={{
                            backgroundColor:
                              LABEL_COLORS[item.label] || "#6e7681",
                          }}
                        />
                        <span>{item.label}</span>
                      </span>
                      <span className="text-xs font-semibold text-ink truncate">
                        {item.name}
                      </span>
                    </div>
                    <div className="text-xs text-muted mt-0.5 flex items-center gap-2 truncate">
                      <span className="font-mono text-faint">{item.id}</span>
                      {item.subtitle && (
                        <>
                          <span>·</span>
                          <span>{item.subtitle}</span>
                        </>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-1.5 shrink-0">
                    <button
                      type="button"
                      onClick={() => {
                        selectNode(item.id, item.name);
                        setSearchModalOpen(false);
                      }}
                      data-testid={`search-inspect-${item.id}`}
                      className="ledger-btn h-7 px-2.5 text-xs"
                    >
                      Inspect
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        onFocusNodeInGraph(item.id, item.name);
                        setSearchModalOpen(false);
                      }}
                      data-testid={`search-focus-graph-${item.id}`}
                      className="ledger-btn ledger-btn-primary h-7 px-2.5 text-xs"
                    >
                      Focus &amp; +1 hop
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2.5 bg-ground border-t border-border flex items-center justify-between text-xs text-muted">
          <span>
            Queries the complete Neo4j database (not limited to the currently displayed subgraph).
          </span>
          <span className="font-mono text-faint">↑↓ navigate · Enter to focus · Esc to close</span>
        </div>
      </div>
    </div>
  );
};
