import React, { useState } from "react";
import { RankedBars } from "./RankedFigures";
import { Table } from "./DashboardPrimitives";
import type { PersistencePair } from "./TemporalFigures";
export interface TopicPair {
  academia_organization_id: string;
  industry_organization_id: string;
  academia_organization: string;
  industry_organization: string;
  topic_id: string;
  topic: string;
  supported_paper_count: number;
  supporting_papers: { paper_id: string; title: string; year: number }[];
}
import { pairKey } from "../../lib/persistence";
export function PartnershipFigures({
  pairs,
  persistence,
  onSelect,
  onOpen,
  onPaper,
}: {
  pairs: TopicPair[];
  persistence: PersistencePair[];
  onSelect: (key: string) => void;
  onOpen: (a: string, b: string) => void;
  onPaper: (id: string, name: string) => void;
}) {
  const [index, setIndex] = useState(0),
    [expanded, setExpanded] = useState(false);
  const visible = pairs.slice(0, expanded ? pairs.length : 5),
    selected = pairs[index] || pairs[0];
  const choose = (i: number) => {
    setIndex(i);
    const p = pairs[i];
    onSelect(pairKey(p.academia_organization_id, p.industry_organization_id));
  };
  const annual =
    selected &&
    persistence.find(
      (p) =>
        pairKey(p.source_id, p.target_id) ===
        pairKey(
          selected.academia_organization_id,
          selected.industry_organization_id,
        ),
    );
  return (
    <>
      <p className="text-xs text-muted">
        Each ranked bar is a pair within one inferred topic. Select a bar or use
        the selector for full names and evidence. Topic supports overlap; do not
        sum across topics.
      </p>
      <RankedBars
        label="Leading cross-sector pair-topic evidence"
        unit="distinct papers"
        rows={visible.map((p, i) => ({
          id: String(i),
          name: `${i + 1}. ${p.academia_organization} ↔ ${p.industry_organization} · ${p.topic}`,
          value: p.supported_paper_count,
        }))}
        onOpen={choose}
        selectedIndex={index}
      />
      {pairs.length > 5 && (
        <button
          className="ledger-btn text-xs px-2 py-1"
          aria-expanded={expanded}
          onClick={() => setExpanded((v) => !v)}
        >
          {expanded
            ? "Show leading 5"
            : `Show all ${pairs.length} pair-topic entries`}
        </button>
      )}
      <label className="text-xs block mt-3">
        Selected partnership and inferred topic
        <select
          aria-label="Selected partnership"
          className="ledger-input w-full mt-1"
          value={index}
          onChange={(e) => choose(Number(e.target.value))}
        >
          {pairs.map((p, i) => (
            <option
              key={`${pairKey(p.academia_organization_id, p.industry_organization_id)}:${p.topic_id}`}
              value={i}
            >
              {i + 1}. {p.academia_organization} ↔ {p.industry_organization} ·{" "}
              {p.topic}
            </option>
          ))}
        </select>
      </label>
      {selected && (
        <div
          data-testid="partnership-details"
          className="partnership-details mt-3 text-xs"
          aria-live="polite"
        >
          <h4 className="text-sm font-semibold break-words">
            {selected.academia_organization} ↔ {selected.industry_organization}
          </h4>
          <p className="mt-1">
            Inferred topic: {selected.topic} ·{" "}
            <strong>
              {selected.supported_paper_count} distinct supporting papers
            </strong>
          </p>
          {annual ? (
            <p className="mt-2">
              All-topic pair support by year:{" "}
              {annual.by_year
                .map((y) => `${y.year}: ${y.distinct_support_papers}`)
                .join(" · ")}
              . Matching row highlighted below.
            </p>
          ) : (
            <p className="mt-2 text-muted">
              This pair is outside the stored persistence shortlist. Full annual
              totals unavailable here.
            </p>
          )}
          <p className="mt-2 text-muted">
            Paper evidence preview ({selected.supporting_papers.length} of{" "}
            {selected.supported_paper_count}; not annual totals):{" "}
            {selected.supporting_papers
              .map((p) => p.year)
              .filter((v, i, a) => a.indexOf(v) === i)
              .sort()
              .join(", ") || "Unavailable"}
            .
          </p>
          <button
            className="ledger-btn px-3 py-2 mt-2"
            onClick={() =>
              onOpen(
                selected.academia_organization_id,
                selected.industry_organization_id,
              )
            }
          >
            Compare portfolios & supporting papers
          </button>
          <Table
            label="Selected partnership paper evidence"
            headers={["Paper / inspect", "Year"]}
            rows={selected.supporting_papers.map((p) => [
              <button
                className="underline text-left"
                onClick={() => onPaper(p.paper_id, p.title)}
              >
                {p.title}
              </button>,
              p.year,
            ])}
          />
        </div>
      )}
    </>
  );
}
