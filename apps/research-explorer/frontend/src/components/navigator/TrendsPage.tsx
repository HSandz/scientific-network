import React, { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { navigatorApi } from "../../lib/navigatorApi";
import { TrendRow } from "../../types/navigator";
import { Panel, Table, pct } from "../analytics/DashboardPrimitives";
import { EChartBox } from "../analytics/EChartBox";
import { MetricTooltip } from "./MetricTooltip";

interface TrendsPageProps {
  onOpenSubject: (subjectId: string) => void;
}

const KINDS: Array<"Topic" | "Method" | "Task" | "Dataset"> = ["Method", "Topic", "Task", "Dataset"];
const VENUES = ["all", "AAAI", "IJCAI"] as const;
const PERIODS = ["2021-2025", "2022-2025", "2023-2025", "2021-2023"] as const;

export const TrendsPage: React.FC<TrendsPageProps> = ({ onOpenSubject }) => {
  const [kind, setKind] = useState<"Topic" | "Method" | "Task" | "Dataset">("Method");
  const [venue, setVenue] = useState<(typeof VENUES)[number]>("all");
  const [period, setPeriod] = useState<(typeof PERIODS)[number]>("2021-2025");
  const [search, setSearch] = useState("");
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  const { data, isLoading, error } = useQuery({
    queryKey: ["nav-trends", kind, venue, period, search],
    queryFn: ({ signal }) => navigatorApi.getTrends({ kind, venue, period, q: search, limit: 60 }, signal),
  });

  const lineItems = useMemo(() => {
    if (!data) return [];
    if (selectedIds.length) {
      const picked = data.items.filter((x) => selectedIds.includes(x.id));
      if (picked.length) return picked;
    }
    return [...data.leaderboards.rising.slice(0, 4), ...data.leaderboards.declining.slice(0, 2)];
  }, [data, selectedIds]);

  const years = useMemo(() => {
    const first = lineItems[0]?.period_yearly || lineItems[0]?.yearly || [];
    return first.map((p) => String(p.year));
  }, [lineItems]);

  const lineOption = useMemo(
    () => ({
      tooltip: { trigger: "axis" },
      legend: { bottom: 0, textStyle: { fontSize: 11 } },
      grid: { top: 24, left: 52, right: 20, bottom: 48 },
      xAxis: { type: "category", data: years },
      yAxis: {
        type: "value",
        name: "Share (%)",
        axisLabel: { formatter: (v: number) => `${(v * 100).toFixed(1)}%` },
      },
      series: lineItems.map((it) => ({
        name: it.name,
        type: "line",
        smooth: true,
        data: (it.period_yearly || it.yearly).map((p) => Number(p.share.toFixed(4))),
      })),
    }),
    [lineItems, years],
  );

  const heatmapOption = useMemo(() => {
    const hm = (data?.heatmap || []).slice(0, 18);
    const hmYears = hm[0]?.years.map((y) => String(y.year)) || ["2021", "2022", "2023", "2024", "2025"];
    const pts: Array<[number, number, number]> = [];
    let maxVal = 0.01;
    hm.forEach((row, yi) => {
      row.years.forEach((pt, xi) => {
        const val = Number((pt.share * 100).toFixed(2));
        if (val > maxVal) maxVal = val;
        pts.push([xi, yi, val]);
      });
    });
    return {
      tooltip: {
        position: "top",
        formatter: (p: { value: [number, number, number] }) =>
          `${hm[p.value[1]]?.name || ""} (${hmYears[p.value[0]]}): ${p.value[2]}%`,
      },
      grid: { top: 12, left: 190, right: 24, bottom: 28 },
      xAxis: { type: "category", data: hmYears },
      yAxis: { type: "category", data: hm.map((r) => r.name.slice(0, 28)), inverse: true },
      visualMap: { min: 0, max: Number(maxVal.toFixed(2)), orient: "horizontal", left: "center", bottom: 0, show: false },
      series: [{ type: "heatmap", data: pts }],
    };
  }, [data]);

  const toggleLine = (id: string) =>
    setSelectedIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev.slice(-5), id]));

  const renderBoard = (title: string, rows: TrendRow[]) => (
    <Panel title={title}>
      {!rows.length ? (
        <p className="text-xs text-muted">No matching subjects in this descriptive category.</p>
      ) : (
        <ul className="space-y-1.5 text-xs">
          {rows.slice(0, 8).map((r) => (
            <li key={r.id} className="flex items-center justify-between gap-2 border-b border-rule pb-1">
              <div className="min-w-0">
                <button
                  type="button"
                  onClick={() => onOpenSubject(r.id)}
                  className="text-left font-medium text-ink hover:underline truncate block max-w-full"
                >
                  {r.name}
                </button>
                {r.display_aliases && r.display_aliases.length > 0 && (
                  <span className="text-[11px] text-faint block truncate">
                    Aliases: {r.display_aliases.slice(0, 2).join(", ")}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2 shrink-0 tabular-nums">
                <span className="text-muted">{pct(r.recent_share, 2)}</span>
                <button
                  type="button"
                  onClick={() => toggleLine(r.id)}
                  className="px-1.5 py-0.5 rounded border border-border text-[11px] hover:bg-raised"
                >
                  {selectedIds.includes(r.id) ? "Pinned" : "Plot"}
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );

  return (
    <div data-testid="page-trends" className="p-4 sm:p-6 space-y-4 overflow-y-auto h-full">
      <div className="flex flex-wrap items-center justify-between gap-3 ledger-panel p-4">
        <div>
          <h1 className="text-lg font-semibold text-ink">Research Trends (AAAI & IJCAI)</h1>
          <p className="text-xs text-muted mt-0.5">
            Classes are{" "}
            <strong className="font-medium text-ink">
              {data?.classification_note || "descriptive (p <= 0.10 per subject, no multiple-testing correction)"}
            </strong>
            . Near-duplicate names use display aliases only (graph entities remain distinct).
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2 text-xs">
          <div role="group" aria-label="Subject type" className="ledger-segmented">
            {KINDS.map((k) => (
              <button key={k} type="button" data-active={kind === k} onClick={() => { setKind(k); setSelectedIds([]); }}>
                {k}
              </button>
            ))}
          </div>
          <label className="sr-only" htmlFor="trends-venue">Venue</label>
          <select
            id="trends-venue"
            value={venue}
            onChange={(e) => setVenue(e.target.value as (typeof VENUES)[number])}
            className="ledger-input h-8 px-2"
          >
            {VENUES.map((v) => <option key={v} value={v}>Venue: {v}</option>)}
          </select>
          <label className="sr-only" htmlFor="trends-period">Period</label>
          <select
            id="trends-period"
            value={period}
            onChange={(e) => setPeriod(e.target.value as (typeof PERIODS)[number])}
            className="ledger-input h-8 px-2"
          >
            {PERIODS.map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
          <input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Filter name or alias…"
            aria-label="Filter trends by name or alias"
            className="ledger-input h-8 px-2.5 w-44"
          />
        </div>
      </div>

      {data?.venue_note && (
        <p className="text-xs text-[var(--warning)] px-1">{data.venue_note}</p>
      )}
      {isLoading && <p role="status" className="text-sm text-muted">Loading trend analytics…</p>}
      {error && <p role="alert" className="text-sm text-[var(--negative)]">{String(error)}</p>}

      {data && (
        <>
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
            <Panel title={`${kind} Annual Paper Share (${data.period})`}>
              <div className="text-xs text-muted mb-2 flex items-center gap-3">
                <MetricTooltip
                  label="Annual share definition"
                  definition={data.metric_definitions?.share?.definition || "Fraction of year papers mentioning subject."}
                  denominator={data.metric_definitions?.share?.denominator}
                  network={data.metric_definitions?.share?.network}
                  graphVersion={data.metric_definitions?.share?.graph_version}
                />
                <span>· Matching: {data.total_matching.toLocaleString()}</span>
              </div>
              <EChartBox option={lineOption} label={`${kind} share trend lines`} height={310} />
            </Panel>

            <Panel title={`Top ${kind}s × Year Share Heatmap`}>
              <EChartBox option={heatmapOption} label={`${kind} share heatmap`} height={335} />
            </Panel>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {renderBoard("Rising (descriptive p <= 0.10)", data.leaderboards.rising)}
            {renderBoard("Emerging", data.leaderboards.emerging)}
            {renderBoard("Declining (descriptive p <= 0.10)", data.leaderboards.declining)}
          </div>

          <Panel title={`All Matching ${kind}s`}>
            <Table
              label={`${kind} trend metrics`}
              headers={["Subject", "Class", "Papers", "Base Share", "Recent Share", "Period Δ (pp)"]}
              rows={data.items.map((r) => [
                <button key={r.id} type="button" onClick={() => onOpenSubject(r.id)} className="text-[var(--accent)] hover:underline text-left">
                  {r.name}
                </button>,
                r.class,
                r.total_papers.toLocaleString(),
                pct(r.base_share, 2),
                pct(r.recent_share, 2),
                typeof r.period_delta_pp === "number" ? `${r.period_delta_pp > 0 ? "+" : ""}${r.period_delta_pp}` : "—",
              ])}
            />
          </Panel>
        </>
      )}
    </div>
  );
};
