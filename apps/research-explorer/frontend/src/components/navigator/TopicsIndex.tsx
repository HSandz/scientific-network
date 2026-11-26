import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { navigatorApi } from "../../lib/navigatorApi";
import { subjectName } from "../../lib/names";
import { fmtPct } from "../../lib/thermal";
import { displayMomentum, momentumSentence, MOMENTUM_WORD } from "../../config/display";
import { EntityDot, ErrorLine, LoadingLine, MomentumChip, PageHead } from "../ui/primitives";

const KINDS: Array<[string, string]> = [
  ["", "All"],
  ["Topic", "Topics"],
  ["Method", "Methods"],
  ["Task", "Tasks"],
  ["Dataset", "Datasets"],
];
const HEAT_T: Record<string, number> = { rising: 0.7, emerging: 0.8, stable: 0, declining: -0.7 };

/** Browse and search every subject; each opens its own page. */
export const TopicsIndex: React.FC<{ onSelect: (id: string) => void }> = ({ onSelect }) => {
  const [kind, setKind] = useState("");
  const [search, setSearch] = useState("");
  const q = useQuery({
    queryKey: ["nav-subjects", kind, search],
    queryFn: ({ signal }) => navigatorApi.listSubjects({ kind: kind || undefined, q: search, limit: 60 }, signal),
    placeholderData: (prev) => prev,
  });
  return (
    <>
      <PageHead title="Topics" sub="Every topic, method, task and dataset in the graph" />
      <div className="controls" role="group" aria-label="Filters">
        <div className="seg" role="group" aria-label="Kind of subject">
          {KINDS.map(([k, label]) => (
            <button key={label} type="button" aria-pressed={kind === k} onClick={() => setKind(k)}>
              {label}
            </button>
          ))}
        </div>
        <label className="control control-grow">
          <span className="sr-only">Find a subject</span>
          <input className="field-input" type="search" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Find a subject by name…" data-testid="topics-search" />
        </label>
      </div>
      {q.isLoading && <LoadingLine />}
      {q.isError && <ErrorLine error={q.error} onRetry={() => q.refetch()} />}
      {q.data && (
        <>
          <p className="note">
            {q.data.total > q.data.items.length ? `Showing ${q.data.items.length} of ${q.data.total.toLocaleString("en")}. Search to find the rest.` : `${q.data.total.toLocaleString("en")} found.`}
          </p>
          <ul className="subject-list">
            {q.data.items.map((s) => (
              <li key={s.id}>
                <button type="button" onClick={() => onSelect(s.id)} data-testid="subject-row">
                  <EntityDot kind={s.kind} />
                  <span className="n">
                    {subjectName(s.name, s.kind)}
                    <small>
                      {s.kind}, {s.total_papers.toLocaleString("en")} papers, {fmtPct(s.recent_share * 100)} of papers in 2024–2025
                    </small>
                  </span>
                  <MomentumChip cls={s.class} t={HEAT_T[s.class] ?? 0} label={MOMENTUM_WORD[displayMomentum(s.class, s.shares || [])]} title={momentumSentence(s.class, s.shares || [])} />
                </button>
              </li>
            ))}
          </ul>
        </>
      )}
    </>
  );
};
