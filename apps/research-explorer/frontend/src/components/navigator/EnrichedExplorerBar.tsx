import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { navigatorApi } from "../../lib/navigatorApi";
import { plural, subjectName } from "../../lib/names";
import { EntityDot } from "../ui/primitives";

interface EnrichedExplorerBarProps {
  onOpenNode360: (id: string) => void;
}

const KINDS = [
  ["Method", "Methods"],
  ["Task", "Tasks"],
  ["Dataset", "Datasets"],
] as const;

/** A way into the methods, tasks and datasets that the graph canvas (publication records) does not draw. */
export const EnrichedExplorerBar: React.FC<EnrichedExplorerBarProps> = ({ onOpenNode360 }) => {
  const [open, setOpen] = useState(false);
  const [label, setLabel] = useState<(typeof KINDS)[number][0]>("Method");
  const [q, setQ] = useState("");
  const [selected, setSelected] = useState<{ id: string; name: string } | null>(null);

  const searchQuery = useQuery({
    queryKey: ["nav-enriched-search", label, q],
    queryFn: () => navigatorApi.searchEnriched({ label, q, limit: 15 }),
    enabled: open,
  });

  const nbQuery = useQuery({
    queryKey: ["nav-enriched-nb", selected?.id],
    queryFn: () => navigatorApi.getEnrichedNeighbors(selected!.id, 20),
    enabled: open && Boolean(selected),
  });

  return (
    <>
      <button type="button" data-testid="toggle-enriched-explorer" aria-expanded={open} onClick={() => setOpen((v) => !v)} className="textlink ml-auto text-sm">
        {open ? "Close the subject finder" : "Find methods, tasks and datasets"}
      </button>
      {open && (
        <div data-testid="enriched-explorer-panel" className="enriched-panel">
          <div className="flex flex-wrap items-center gap-3">
            <div className="seg" role="group" aria-label="Kind of subject">
              {KINDS.map(([k, kindLabel]) => (
                <button
                  key={k}
                  type="button"
                  aria-pressed={label === k}
                  onClick={() => {
                    setLabel(k);
                    setSelected(null);
                  }}
                >
                  {kindLabel}
                </button>
              ))}
            </div>
            <input type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Filter by name…" aria-label={`Search ${label.toLowerCase()}s`} className="field-input" />
          </div>
          <div className="chips">
            {(searchQuery.data?.results || []).slice(0, 12).map((r) => (
              <button key={r.id} type="button" className="echip" aria-pressed={selected?.id === r.id} onClick={() => setSelected({ id: r.id, name: subjectName(r.name, label) })}>
                <EntityDot kind={label} />
                {subjectName(r.name, label)}
              </button>
            ))}
          </div>
          {selected && nbQuery.data && (
            <p className="note">
              {selected.name} has at least {plural(nbQuery.data.edges.length, "connection")} outside the publication graph.{" "}
              <button type="button" className="textlink" onClick={() => onOpenNode360(selected.id)}>
                Open the profile of {selected.name}
              </button>
            </p>
          )}
        </div>
      )}
    </>
  );
};
