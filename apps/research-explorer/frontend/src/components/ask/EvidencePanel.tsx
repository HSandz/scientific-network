import React, { useEffect, useMemo, useRef, useState } from "react";
import type { ChartSpec, Footnote, GraphModel, StepTable } from "../../lib/askModel";
import { formatCell } from "../../lib/askModel";
import { paperMeta, usePapers } from "../../lib/usePapers";
import { readPalette } from "../../lib/thermal";
import { BarList, Dumbbell, LineChart } from "../charts/charts";
import { EmptyGraphArt, EvidenceGraph } from "./EvidenceGraph";
import { EntityDot } from "../ui/primitives";

export type EvidenceTab = "Graph" | "Chart" | "Table" | "Papers";
const TABS: EvidenceTab[] = ["Graph", "Chart", "Table", "Papers"];

export interface EvidenceData {
  graph: GraphModel | null;
  graphEmptyReason: string;
  revealed: number;
  done: boolean;
  chart: ChartSpec;
  tables: StepTable[];
  footnotes: Footnote[];
  resultPaperIds: string[];
  citedPaperIds: string[];
}

const unitFormat = (u: string) => (v: number) =>
  u === "pct" ? `${(v * 100).toFixed(1)}%` : u === "x" ? `${v.toFixed(1)}×` : u === "score" ? (v < 0.01 ? v.toExponential(1) : v.toFixed(3)) : v.toLocaleString("en");

export const EvidencePanel: React.FC<{
  data: EvidenceData | null;
  tab: EvidenceTab;
  onTab: (t: EvidenceTab) => void;
  flashFootnote: number | null;
}> = ({ data, tab, onTab, flashFootnote }) => {
  const tabRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const counts: Record<EvidenceTab, string> = {
    Graph: data?.graph ? String(data.graph.nodes.length) : "",
    Chart: "",
    Table: data ? String(data.tables.reduce((a, t) => a + t.rows.length, 0) || "") : "",
    Papers: data ? String(new Set([...data.citedPaperIds, ...data.resultPaperIds]).size || "") : "",
  };
  const onKey = (e: React.KeyboardEvent, i: number) => {
    if (e.key !== "ArrowRight" && e.key !== "ArrowLeft" && e.key !== "Home" && e.key !== "End") return;
    e.preventDefault();
    const n = e.key === "Home" ? 0 : e.key === "End" ? TABS.length - 1 : (i + (e.key === "ArrowRight" ? 1 : TABS.length - 1)) % TABS.length;
    onTab(TABS[n]);
    tabRefs.current[n]?.focus();
  };

  return (
    <section className="evidence" aria-label="Evidence" data-testid="ask-evidence">
      <div className="ev-head">
        <h2>Evidence</h2>
        <div className="tabs" role="tablist" aria-label="Evidence views">
          {TABS.map((t, i) => (
            <button
              key={t}
              ref={(el) => (tabRefs.current[i] = el)}
              type="button"
              role="tab"
              id={`ev-tab-${t}`}
              aria-selected={tab === t}
              aria-controls="ev-body"
              tabIndex={tab === t ? 0 : -1}
              disabled={!data}
              className="tab"
              onClick={() => onTab(t)}
              onKeyDown={(e) => onKey(e, i)}
              data-testid={`ev-tab-${t.toLowerCase()}`}
            >
              {t}
              {counts[t] && <span className="n">{counts[t]}</span>}
            </button>
          ))}
        </div>
      </div>
      <div className="ev-body" id="ev-body" role="tabpanel" aria-labelledby={`ev-tab-${tab}`} tabIndex={0}>
        {!data ? (
          <div className="ev-empty">
            <EmptyGraphArt />
            <p>The graph walk, charts, result rows and cited papers for an answer appear here.</p>
          </div>
        ) : tab === "Graph" ? (
          data.graph ? (
            <EvidenceGraph model={data.graph} revealed={data.revealed} done={data.done} />
          ) : (
            <div className="ev-empty">
              <EmptyGraphArt />
              <p>{data.graphEmptyReason}</p>
            </div>
          )
        ) : tab === "Chart" ? (
          <EvidenceChart spec={data.chart} />
        ) : tab === "Table" ? (
          <EvidenceTables tables={data.tables} />
        ) : (
          <EvidencePapers footnotes={data.footnotes} resultPaperIds={data.resultPaperIds} flash={flashFootnote} />
        )}
      </div>
    </section>
  );
};

const EvidenceChart: React.FC<{ spec: ChartSpec }> = ({ spec }) => {
  if (spec.kind === "none")
    return (
      <div className="ev-empty">
        <EmptyGraphArt />
        <p>{spec.reason}</p>
      </div>
    );
  if (spec.kind === "lines") {
    const p = readPalette();
    void p;
    const maxW = Math.max(...spec.series.map((s) => Math.abs(s.weight)), 0.0001);
    return (
      <div>
        <p className="ev-caption">{spec.caption}</p>
        <div className="chart-scroll">
          <LineChart
            label="Ask answer chart"
            years={spec.years}
            unit={spec.unit}
            series={spec.series.map((s, i) => ({ name: s.name, values: s.values, t: spec.series.length > 1 ? 0.3 + 0.7 * (Math.abs(s.weight) / maxW) * Math.sign(s.weight || 1) : 0.8, emphasis: i === 0 }))}
          />
        </div>
      </div>
    );
  }
  if (spec.kind === "dumbbell")
    return (
      <div>
        <p className="ev-caption">{spec.caption}</p>
        <Dumbbell label="Ask answer chart" before={spec.before} after={spec.after} items={spec.items} />
      </div>
    );
  return (
    <div>
      <p className="ev-caption">{spec.caption}</p>
      {spec.panels.map((panel, i) => (
        <BarList
          key={i}
          label="Ask answer chart"
          title={
            panel.title ? (
              <>
                <EntityDot kind={panel.dotKind} /> {panel.title}
              </>
            ) : undefined
          }
          items={panel.items}
          format={unitFormat(panel.unit)}
        />
      ))}
    </div>
  );
};

const EvidenceTables: React.FC<{ tables: StepTable[] }> = ({ tables }) => {
  const [which, setWhich] = useState(tables.length - 1);
  useEffect(() => setWhich(tables.length - 1), [tables.length]);
  if (!tables.length)
    return (
      <div className="ev-empty">
        <EmptyGraphArt />
        <p>No result rows for this answer.</p>
      </div>
    );
  const t = tables[Math.max(0, Math.min(which, tables.length - 1))];
  return (
    <div>
      {tables.length > 1 && (
        <div className="seg-steps" role="group" aria-label="Result step">
          {tables.map((x, i) => (
            <button key={x.step} type="button" aria-pressed={i === which} onClick={() => setWhich(i)}>
              Step {x.step}: {x.title}
            </button>
          ))}
        </div>
      )}
      <p className="ev-caption" style={{ marginTop: 12 }}>
        {t.title}. {t.rows.length.toLocaleString("en")} {t.rows.length === 1 ? "row" : "rows"}
        {t.totalRows > t.rows.length ? `, of ${t.totalRows.toLocaleString("en")} found` : ""}.
      </p>
      <div className="table-scroll">
        <table className="data" data-testid="ask-table">
          <thead>
            <tr>
              {t.columns.map((c) => (
                <th key={c.key} className={c.numeric ? "num" : ""} scope="col">
                  {c.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {t.rows.map((r, i) => (
              <tr key={i}>
                {t.columns.map((c) => (
                  <td key={c.key} className={c.numeric ? "num" : ""}>
                    {formatCell(r[c.key], c.format)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const EvidencePapers: React.FC<{ footnotes: Footnote[]; resultPaperIds: string[]; flash: number | null }> = ({ footnotes, resultPaperIds, flash }) => {
  const cited = useMemo(() => [...new Set(footnotes.flatMap((f) => f.papers))], [footnotes]);
  const others = useMemo(() => resultPaperIds.filter((id) => !cited.includes(id)), [resultPaperIds, cited]);
  const papers = usePapers([...cited, ...others.slice(0, 12)]);
  const meta = papers.data || {};
  useEffect(() => {
    if (flash == null) return;
    const el = document.getElementById(`fn-${flash}`);
    if (!el) return;
    el.scrollIntoView({ block: "center", behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
    el.classList.remove("flash");
    void el.offsetWidth;
    el.classList.add("flash");
  }, [flash]);

  const paperLine = (id: string) => {
    const p = meta[id];
    return (
      <div className="paper-ref" key={id}>
        {p?.url ? (
          <a href={p.url} target="_blank" rel="noopener noreferrer">
            {p.title || "Untitled paper"}
          </a>
        ) : (
          <span className="t">{p?.title || (papers.isLoading ? "Loading title…" : "Paper details unavailable")}</span>
        )}
        <div className="meta">{paperMeta(p)}</div>
      </div>
    );
  };

  return (
    <div data-testid="ask-papers">
      <h3 className="papers-h">Cited in the answer</h3>
      {footnotes.length === 0 ? (
        <p className="note" data-testid="ask-citations-empty">
          The answer has no footnotes.
        </p>
      ) : (
        <ol className="cites" data-testid="ask-citations">
          {footnotes.map((f) => (
            <li key={f.n} id={`fn-${f.n}`} tabIndex={-1}>
              <span className="num">{f.n}</span>
              <div>
                <div className="lab">{f.label}</div>
                {f.kind === "step" && (
                  <div className="meta-line">Result table from this step; the Table tab has every row.{f.papers.length ? " Example papers behind it:" : ""}</div>
                )}
                {f.papers.map(paperLine)}
              </div>
            </li>
          ))}
        </ol>
      )}
      <h3 className="papers-h">Other papers in this result</h3>
      {others.length ? (
        <>
          <p className="note" style={{ marginTop: 4 }} data-testid="ask-result-papers">
            {others.length.toLocaleString("en")} more {others.length === 1 ? "paper supports" : "papers support"} the result rows without being cited directly.
            {others.length > 12 ? " The first 12 are listed." : ""}
          </p>
          <ul className="plain-papers">
            {others.slice(0, 12).map((id) => (
              <li key={id}>{paperLine(id)}</li>
            ))}
          </ul>
        </>
      ) : (
        <p className="note" style={{ marginTop: 4 }} data-testid="ask-result-papers">
          None. Every paper behind this result is cited above.
        </p>
      )}
    </div>
  );
};
