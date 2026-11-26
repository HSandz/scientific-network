import React, { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { navigatorApi } from "../../lib/navigatorApi";
import { navigate, pathFor } from "../../lib/router";
import { subjectName } from "../../lib/names";
import { fmtPct, momentumT, readPalette, rowHue, thermal } from "../../lib/thermal";
import { displayMomentum, momentumSentence, MOMENTUM_WORD } from "../../config/display";
import type { TrendRow } from "../../types/navigator";
import { HeatCells, LineChart } from "../charts/charts";
import { EntityDot, ErrorLine, LoadingLine, MethodDrawer, MomentumChip, PageHead, Section } from "../ui/primitives";
import { TrendsMethodNote } from "./methodNotes";

type Kind = "Method" | "Task" | "Dataset" | "Topic";
const KINDS: Array<[Kind, string]> = [
  ["Method", "Methods"],
  ["Task", "Tasks"],
  ["Dataset", "Datasets"],
  ["Topic", "Topics"],
];
const VENUES: Array<[string, string]> = [
  ["all", "AAAI and IJCAI"],
  ["AAAI", "AAAI only"],
  ["IJCAI", "IJCAI only"],
];
const PERIODS = ["2021-2025", "2022-2025", "2023-2025", "2021-2023"] as const;
const MAX_SERIES = 6;

function joinNames(names: string[]): string {
  if (names.length <= 1) return names[0] || "";
  return `${names.slice(0, -1).join(", ")} and ${names[names.length - 1]}`;
}

export const TrendsPage: React.FC<{ onOpenSubject?: (id: string) => void }> = () => {
  const [kind, setKind] = useState<Kind>("Method");
  const [venue, setVenue] = useState("all");
  const [period, setPeriod] = useState<(typeof PERIODS)[number]>("2021-2025");
  const [search, setSearch] = useState("");
  const [picked, setPicked] = useState<string[] | null>(null);

  const q = useQuery({
    queryKey: ["nav-trends", kind, venue, period, search],
    queryFn: ({ signal }) => navigatorApi.getTrends({ kind, venue, period, q: search, limit: 200 }, signal),
    placeholderData: (prev) => prev,
  });
  const data = q.data;
  const p = readPalette();

  const maxSlope = useMemo(() => Math.max(0.000001, ...(data?.items || []).map((r) => Math.abs(r.slope_of_share))), [data]);
  const byId = useMemo(() => new Map((data?.items || []).map((r) => [r.id, r])), [data]);
  const tOf = (r: TrendRow) => momentumT(r.slope_of_share, maxSlope, r.class);
  const name = (r: { name: string; kind?: string }) => subjectName(r.name, r.kind || kind);

  const defaults = useMemo(() => {
    if (!data) return [];
    const heat = [...data.leaderboards.rising, ...data.leaderboards.emerging].sort((a, b) => b.slope_of_share - a.slope_of_share);
    return heat.slice(0, 4).map((r) => r.id);
  }, [data]);
  const chosen = (picked ?? defaults).filter((id) => byId.has(id)).slice(0, MAX_SERIES);
  const series = chosen.map((id) => byId.get(id)!).filter(Boolean);
  const years = (series[0]?.period_yearly || series[0]?.yearly || []).map((pt) => String(pt.year));

  const toggle = (id: string) => {
    const cur = picked ?? defaults;
    if (cur.includes(id)) setPicked(cur.filter((x) => x !== id));
    else setPicked([...cur, id].slice(-MAX_SERIES));
  };

  const headline = useMemo(() => {
    if (!data) return "";
    const heat = [...data.leaderboards.rising, ...data.leaderboards.emerging].sort((a, b) => b.slope_of_share - a.slope_of_share).slice(0, 2);
    const cool = data.leaderboards.declining.slice(0, 2);
    const parts: string[] = [];
    if (heat.length) parts.push(`${joinNames(heat.map((r, i) => (i ? name(r).replace(/^[A-Z](?=[a-z])/, (c) => c.toLowerCase()) : name(r))))} ${heat.length > 1 ? "are" : "is"} gaining share fastest.`);
    if (cool.length) parts.push(`${joinNames(cool.map((r, i) => (i ? name(r).replace(/^[A-Z](?=[a-z])/, (c) => c.toLowerCase()) : name(r))))} ${cool.length > 1 ? "are" : "is"} losing share.`);
    return parts.join(" ");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  const Board: React.FC<{ title: string; rows: TrendRow[]; testId: string }> = ({ title, rows, testId }) => (
    <section className="board" aria-label={title} data-testid={testId}>
      <h3>{title}</h3>
      {rows.length === 0 ? (
        <p className="note">None in this selection.</p>
      ) : (
        <ol>
          {rows.map((r) => {
            const ys = r.period_yearly || r.yearly;
            const shares = ys.map((x) => x.share);
            const on = chosen.includes(r.id);
            return (
              <li key={r.id}>
                <button type="button" className="board-name" onClick={() => navigate(pathFor("topics", r.id))}>
                  {name(r)}
                </button>
                <span className="board-change">
                  {fmtPct(shares[0] * 100)} → <b>{fmtPct(shares[shares.length - 1] * 100)}</b>
                </span>
                <button
                  type="button"
                  className={`plot-toggle ${on ? "is-on" : ""}`}
                  aria-pressed={on}
                  aria-label={`${on ? "Remove" : "Add"} ${name(r)} ${on ? "from" : "to"} the chart`}
                  onClick={() => toggle(r.id)}
                  style={on ? { borderColor: thermal(tOf(r), p) } : undefined}
                >
                  {on ? "On chart" : "Chart"}
                </button>
              </li>
            );
          })}
        </ol>
      )}
    </section>
  );

  return (
    <div data-testid="page-trends">
      <PageHead title="Trends" sub="Every subject's share of AAAI and IJCAI papers, year by year" lede={headline || undefined} />

      <div className="controls" role="group" aria-label="Filters">
        <div className="seg" role="group" aria-label="Kind of subject">
          {KINDS.map(([k, label]) => (
            <button key={k} type="button" aria-pressed={kind === k} onClick={() => { setKind(k); setPicked(null); }} data-testid={`trends-kind-${k.toLowerCase()}`}>
              {label}
            </button>
          ))}
        </div>
        <label className="control">
          <span className="sr-only">Conference</span>
          <select value={venue} onChange={(e) => setVenue(e.target.value)} className="field-input">
            {VENUES.map(([v, l]) => (
              <option key={v} value={v}>
                {l}
              </option>
            ))}
          </select>
        </label>
        <label className="control">
          <span className="sr-only">Years</span>
          <select value={period} onChange={(e) => setPeriod(e.target.value as (typeof PERIODS)[number])} className="field-input">
            {PERIODS.map((p) => (
              <option key={p} value={p}>
                {p.replace("-", "–")}
              </option>
            ))}
          </select>
        </label>
        <label className="control control-grow">
          <span className="sr-only">Filter by name</span>
          <input className="field-input" value={search} onChange={(e) => setSearch(e.target.value)} placeholder={`Filter ${KINDS.find((k) => k[0] === kind)![1].toLowerCase()} by name…`} />
        </label>
      </div>
      {data?.venue_note && <p className="note">{data.venue_note}</p>}
      {q.isLoading && <LoadingLine />}
      {q.isError && <ErrorLine error={q.error} onRetry={() => q.refetch()} />}

      {data && (
        <>
          <section className="trend-chart" aria-labelledby="tc-h">
            <h2 id="tc-h" className="sr-only">
              Share over time
            </h2>
            {series.length ? (
              <>
                <div className="chart-scroll">
                  <LineChart
                    label="Trend share lines"
                    years={years}
                    unit="pct"
                    height={390}
                    series={series.map((r, i) => ({ name: name(r), values: (r.period_yearly || r.yearly).map((x) => x.share * 100), t: tOf(r), emphasis: i === 0 }))}
                  />
                </div>
                <div className="series-chips" aria-label="Lines on the chart">
                  {series.map((r) => (
                    <button key={r.id} type="button" className="echip" onClick={() => toggle(r.id)} aria-label={`Remove ${name(r)} from the chart`}>
                      <span className="swatch" style={{ background: thermal(tOf(r), p) }} />
                      {name(r)} <span className="c">×</span>
                    </button>
                  ))}
                  <span className="note-inline">Pick lines from the lists below. Colour shows momentum: amber heating, blue cooling, grey stable.</span>
                </div>
              </>
            ) : (
              <p className="note">Pick subjects from the lists below to chart them.</p>
            )}
            <div className="chart-foot">
              <span>Share of all papers each year</span>
              <MethodDrawer testId="trends-how">
                <TrendsMethodNote caveats={data.caveats} />
              </MethodDrawer>
            </div>
          </section>

          <div className="boards">
            <Board title="Rising" rows={data.leaderboards.rising} testId="board-rising" />
            <Board title="Emerging" rows={data.leaderboards.emerging} testId="board-emerging" />
            <Board title="Declining" rows={data.leaderboards.declining} testId="board-declining" />
          </div>

          <Section id="heat" title="Year by year" hint={`The ${Math.min(25, data.heatmap.length)} most-studied ${KINDS.find((k) => k[0] === kind)![1].toLowerCase()} in this selection. Darker cell means a larger share that year; colour shows momentum.`}>
            <div className="heat-table" data-chart-label="Trends heat map" data-chart-rendered="true" data-chart-point-count={data.heatmap.length * 5}>
              <div className="heat-head" aria-hidden="true">
                <span>{KINDS.find((k) => k[0] === kind)![0]}</span>
                {(data.heatmap[0]?.years || []).map((y) => (
                  <span key={y.year} className="yr">
                    {y.year}
                  </span>
                ))}
                <span className="r">Momentum</span>
              </div>
              {data.heatmap.slice(0, 25).map((h) => {
                const r = byId.get(h.id);
                const t = r ? tOf(r) : 0;
                const shares = h.years.map((y) => y.share);
                const disp = displayMomentum(h.class, shares);
                return (
                  <button key={h.id} type="button" className="heat-row" onClick={() => navigate(pathFor("topics", h.id))} aria-label={`${name(h)}. ${momentumSentence(h.class, shares)}.`}>
                    <span className="heat-name">
                      <EntityDot kind={kind} />
                      <span>{name(h)}</span>
                    </span>
                    <HeatCells shares={shares.map((x) => x * 100)} hue={rowHue(t, p)} years={h.years.map((y) => String(y.year))} papers={h.years.map((y) => y.papers)} size="sm" />
                    <span className="r">
                      <MomentumChip cls={h.class} t={t} label={MOMENTUM_WORD[disp]} title={momentumSentence(h.class, shares)} />
                    </span>
                  </button>
                );
              })}
            </div>
          </Section>
        </>
      )}
    </div>
  );
};
