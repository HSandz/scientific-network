import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { navigatorApi } from "../../lib/navigatorApi";

interface EnrichedExplorerBarProps {
  onOpenNode360: (id: string) => void;
}

export const EnrichedExplorerBar: React.FC<EnrichedExplorerBarProps> = ({ onOpenNode360 }) => {
  const [open, setOpen] = useState(false);
  const [label, setLabel] = useState<"Method" | "Task" | "Dataset">("Method");
  const [q, setQ] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const schemaQuery = useQuery({
    queryKey: ["nav-enriched-schema"],
    queryFn: ({ signal }) => navigatorApi.getEnrichedSchema(signal),
    enabled: open,
  });

  const searchQuery = useQuery({
    queryKey: ["nav-enriched-search", label, q],
    queryFn: () => navigatorApi.searchEnriched({ label, q, limit: 15 }),
    enabled: open,
  });

  const nbQuery = useQuery({
    queryKey: ["nav-enriched-nb", selectedId],
    queryFn: () => navigatorApi.getEnrichedNeighbors(selectedId!, 20),
    enabled: open && Boolean(selectedId),
  });

  return (
    <>
      <button
        type="button"
        data-testid="toggle-enriched-explorer"
        onClick={() => setOpen((v) => !v)}
        className="ml-auto h-4 px-1.5 py-0 rounded border border-control bg-surface hover:bg-raised text-[11px] font-medium leading-[14px] inline-flex items-center"
      >
        {open ? "Hide Enriched v5" : "+ Enriched v5"}
      </button>
      {schemaQuery.data && open && (
        <span className="text-[11px] text-faint font-mono">
          {schemaQuery.data.labels.length} labels · {schemaQuery.data.predicates.length} predicates ({schemaQuery.data.graph_version})
        </span>
      )}
      {open && (
        <div data-testid="enriched-explorer-panel" className="w-full mt-1.5 p-2.5 rounded border border-border bg-surface text-xs space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            {(["Method", "Task", "Dataset"] as const).map((lbl) => (
              <button
                key={lbl}
                type="button"
                onClick={() => {
                  setLabel(lbl);
                  setSelectedId(null);
                }}
                className={`px-2 py-0.5 rounded border ${label === lbl ? "bg-raised border-control font-semibold" : "border-border"}`}
              >
                {lbl}
              </button>
            ))}
            <input
              type="search"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder={`Search ${label}s…`}
              aria-label={`Search enriched ${label} entities`}
              className="ledger-input h-7 px-2 w-48"
            />
          </div>
          <div className="flex flex-wrap gap-1.5">
            {(searchQuery.data?.results || []).slice(0, 12).map((r) => (
              <button
                key={r.id}
                type="button"
                onClick={() => setSelectedId(r.id)}
                className={`px-2 py-0.5 rounded border ${selectedId === r.id ? "border-[var(--accent)] bg-raised" : "border-border hover:bg-raised"}`}
              >
                {r.name}
              </button>
            ))}
          </div>
          {nbQuery.data && (
            <div className="pt-1.5 border-t border-rule flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={() => onOpenNode360(nbQuery.data.center_id)}
                className="font-semibold text-[var(--accent)] hover:underline"
              >
                Inspect {nbQuery.data.center_id} in Node 360 →
              </button>
              <span className="text-muted">({nbQuery.data.edges.length} edges loaded)</span>
            </div>
          )}
        </div>
      )}
    </>
  );
};
