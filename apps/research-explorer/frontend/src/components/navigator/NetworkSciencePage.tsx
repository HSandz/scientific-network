import React, { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { navigatorApi } from "../../lib/navigatorApi";
import { Panel, Table } from "../analytics/DashboardPrimitives";
import { EChartBox } from "../analytics/EChartBox";
import { MetricTooltip } from "./MetricTooltip";

interface NetworkSciencePageProps {
  onOpenNode360: (id: string) => void;
}

export const NetworkSciencePage: React.FC<NetworkSciencePageProps> = ({ onOpenNode360 }) => {
  const [rankNet, setRankNet] = useState<"N1" | "N2" | "N3" | "N4">("N1");
  const { data, isLoading, error } = useQuery({
    queryKey: ["nav-network-science"],
    queryFn: ({ signal }) => navigatorApi.getNetworkScience(signal),
  });

  const swNetworks = (data?.smallworld as { networks?: Record<string, any> } | undefined)?.networks || {};
  const evo = (data?.evolution as Record<string, Array<{ year: number | string; L: number; C: number; lcc_nodes: number }>> | undefined) || {};
  const degTail = (data?.degree_tail as Record<string, { alpha?: number; degree_counts?: Record<string, number>; statement?: string }> | undefined) || {};
  const ranking = (data?.ranking as Record<string, any> | undefined) || {};
  const defs = (data?.metric_definitions as Record<string, any> | undefined) || {};

  const histOption = useMemo(() => {
    const n1Hist = swNetworks.N1?.real?.histogram || {};
    const keys = Object.keys(n1Hist).sort((a, b) => Number(a) - Number(b));
    return {
      tooltip: { trigger: "axis" },
      grid: { top: 20, left: 56, right: 16, bottom: 30 },
      xAxis: { type: "category", data: keys, name: "Path length" },
      yAxis: { type: "value", name: "Pairs" },
      series: [{ type: "bar", name: "N1 shortest-path pairs", data: keys.map((k) => n1Hist[k]) }],
    };
  }, [swNetworks]);

  const evoOption = useMemo(() => {
    const rows = evo.N1 || [];
    return {
      tooltip: { trigger: "axis" },
      legend: { bottom: 0, textStyle: { fontSize: 11 } },
      grid: { top: 20, left: 48, right: 48, bottom: 42 },
      xAxis: { type: "category", data: rows.map((r) => String(r.year)) },
      yAxis: [
        { type: "value", name: "L" },
        { type: "value", name: "C (LCC)", min: 0.7, max: 0.9 },
      ],
      series: [
        { name: "N1 L", type: "line", data: rows.map((r) => Number(r.L?.toFixed(3))) },
        { name: "N1 C", type: "line", yAxisIndex: 1, data: rows.map((r) => Number(r.C?.toFixed(4))) },
      ],
    };
  }, [evo]);

  const rankBlock = ranking[rankNet] || {};
  const topRows = Array.isArray(rankBlock.top)
    ? rankBlock.top
    : Object.entries(rankBlock.top || {}).flatMap(([lbl, arr]) =>
        (Array.isArray(arr) ? arr.slice(0, 3) : []).map((x: any) => ({ ...x, label: lbl })),
      );

  return (
    <div data-testid="page-network-science" className="p-4 sm:p-6 space-y-4 overflow-y-auto h-full">
      <div className="ledger-panel p-4">
        <h1 className="text-lg font-semibold text-ink">Network Science (S1 Small-World · S2 Centrality · S3 Communities)</h1>
        <p className="text-xs text-muted mt-0.5">
          Config: <span className="font-mono">{String(data?.config_version || "analysis-final-exam-v2")}</span> · Clustering:{" "}
          {String(data?.clustering_definition || "igraph average local clustering, mode='zero', on the LCC")}
        </p>
      </div>

      {isLoading && <p role="status" className="text-sm text-muted">Loading S1–S3 metrics…</p>}
      {error && <p role="alert" className="text-sm text-[var(--negative)]">{String(error)}</p>}

      {data && (
        <>
          <Panel title="S1: Small-World Analysis Against Both Null Baselines">
            <div className="text-xs text-muted mb-2">
              <MetricTooltip
                label="Small-world formula & σ"
                definition={defs.small_world_sigma?.definition || "(C / C_rand) / (L / L_rand)"}
                denominator={defs.small_world_sigma?.denominator}
                network={defs.small_world_sigma?.network}
              />
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead>
                  <tr className="border-b border-border text-muted">
                    <th className="p-2">Network</th>
                    <th className="p-2">LCC Nodes / Edges</th>
                    <th className="p-2">L</th>
                    <th className="p-2">C (LCC)</th>
                    <th className="p-2">σ (ER)</th>
                    <th className="p-2">σ (Rewired)</th>
                    <th className="p-2">Decision</th>
                  </tr>
                </thead>
                <tbody>
                  {["N1", "N2", "N4"].map((nk) => {
                    const nw = swNetworks[nk];
                    if (!nw) return null;
                    return (
                      <tr key={nk} className="border-t border-rule tabular-nums">
                        <td className="p-2 font-medium">{nk}</td>
                        <td className="p-2">{nw.lcc_nodes?.toLocaleString()} / {nw.lcc_edges?.toLocaleString()}</td>
                        <td className="p-2">{nw.real?.L?.toFixed(3)}</td>
                        <td className="p-2">{nw.real?.clustering?.average_local?.toFixed(4)}</td>
                        <td className="p-2">{nw.baselines?.erdos_renyi_gnm?.sigma_from_means?.toFixed(2)}</td>
                        <td className="p-2">{nw.baselines?.degree_preserving_rewiring?.sigma_from_means?.toFixed(2)}</td>
                        <td className="p-2">{nw.decision?.statement}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </Panel>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Panel title="N1 Shortest-Path Distribution (Exact LCC)">
              <EChartBox option={histOption} label="N1 path length histogram" height={260} />
            </Panel>
            <Panel title="N1 Temporal Evolution (2021–2025 Cumulative vs 2025)">
              <EChartBox option={evoOption} label="N1 L and C evolution chart" height={260} />
              {degTail.N1?.statement && (
                <p className="text-[11px] text-muted mt-2">Degree tail (N1): {degTail.N1.statement}</p>
              )}
            </Panel>
          </div>

          <Panel title="S2: PageRank & Centrality Comparison">
            <div className="flex flex-wrap items-center justify-between gap-2 mb-3 text-xs">
              <div className="ledger-segmented" role="group" aria-label="Ranking network">
                {(["N1", "N2", "N3", "N4"] as const).map((nk) => (
                  <button key={nk} type="button" data-active={rankNet === nk} onClick={() => setRankNet(nk)}>
                    {nk}
                  </button>
                ))}
              </div>
              {rankBlock.sparsity_note && (
                <span className="text-[var(--warning)]">{rankBlock.sparsity_note}</span>
              )}
            </div>

            {rankBlock.comparison_with_pagerank && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-3 text-xs">
                {Object.entries(rankBlock.comparison_with_pagerank).map(([metric, stats]: [string, any]) => (
                  <div key={metric} className="p-2 rounded bg-ground border border-rule tabular-nums">
                    <span className="font-medium block">{metric} vs PageRank</span>
                    <span className="text-muted">Spearman ρ: {typeof stats?.spearman === "number" ? stats.spearman.toFixed(3) : "—"}</span>
                    <span className="block text-faint">Top-20 overlap: {stats?.top20_overlap ?? "—"}</span>
                  </div>
                ))}
              </div>
            )}

            <Table
              label={`${rankNet} top ranked nodes`}
              headers={["Rank", "Name", "Label", "PageRank", "Degree", rankNet === "N3" ? "In-Corpus Cites" : "Community"]}
              rows={topRows.map((r: any, idx: number) => [
                r.rank ?? idx + 1,
                <button key={r.id || idx} type="button" onClick={() => r.id && onOpenNode360(r.id)} className="text-[var(--accent)] hover:underline text-left">
                  {r.name || r.id}
                </button>,
                r.label || "—",
                typeof r.pagerank === "number" ? r.pagerank.toExponential(2) : "—",
                r.degree ?? "—",
                rankNet === "N3" ? (r.in_corpus_citations ?? 0) : (r.community ?? "—"),
              ])}
            />
          </Panel>
        </>
      )}
    </div>
  );
};
