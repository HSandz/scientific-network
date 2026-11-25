import React, { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { navigatorApi } from "../../lib/navigatorApi";
import { Panel, Table } from "../analytics/DashboardPrimitives";
import { EChartBox } from "../analytics/EChartBox";

interface Node360PageProps {
  nodeId: string | null;
  onSelectNode: (id: string) => void;
}

export const Node360Page: React.FC<Node360PageProps> = ({ nodeId, onSelectNode }) => {
  const [searchText, setSearchText] = useState("");
  const activeId = nodeId || "method:Q3621696";

  const searchQuery = useQuery({
    queryKey: ["nav-node360-search", searchText],
    queryFn: () => navigatorApi.searchEnriched({ q: searchText, limit: 20 }),
    enabled: searchText.trim().length >= 2,
  });

  const detailQuery = useQuery({
    queryKey: ["nav-node360", activeId],
    queryFn: ({ signal }) => navigatorApi.getNode360(activeId, signal),
    enabled: Boolean(activeId),
  });

  const d: any = detailQuery.data;

  const sparkOption = useMemo(() => {
    const sp: Array<{ year: number; papers: number }> = d?.sparkline || [];
    return {
      tooltip: { trigger: "axis" },
      grid: { top: 14, left: 36, right: 12, bottom: 24 },
      xAxis: { type: "category", data: sp.map((x) => String(x.year)) },
      yAxis: { type: "value" },
      series: [{ type: "bar", name: "Papers", data: sp.map((x) => x.papers) }],
    };
  }, [d]);

  return (
    <div data-testid="page-node360" className="p-4 sm:p-6 space-y-4 overflow-y-auto h-full">
      <div className="ledger-panel p-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold text-ink">{d?.name || activeId}</h1>
          <p className="text-xs text-muted font-mono">
            {d?.label || "Entity"} · {activeId}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <input
            type="search"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            placeholder="Search any label (Method, Task, Researcher…)…"
            aria-label="Search Node 360 entities"
            className="ledger-input h-8 px-2.5 w-64"
          />
          {searchQuery.data && searchQuery.data.results.length > 0 && (
            <select
              aria-label="Pick matched entity"
              onChange={(e) => e.target.value && onSelectNode(e.target.value)}
              defaultValue=""
              className="ledger-input h-8 px-2 max-w-xs"
            >
              <option value="">Select match ({searchQuery.data.results.length})…</option>
              {searchQuery.data.results.map((r) => (
                <option key={r.id} value={r.id}>
                  [{r.label}] {r.name}
                </option>
              ))}
            </select>
          )}
        </div>
      </div>

      {detailQuery.isLoading && <p role="status" className="text-sm text-muted">Loading Node 360…</p>}
      {detailQuery.error && <p role="alert" className="text-sm text-[var(--negative)]">{String(detailQuery.error)}</p>}

      {d && (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <Panel title="Properties & Enrichment">
              {d.description && (
                <div className="mb-3 p-2.5 rounded bg-ground border border-rule text-xs">
                  <span className="inline-block px-1.5 py-0.5 rounded bg-raised font-medium mb-1">
                    {d.description.label}
                  </span>
                  <p className="text-ink leading-relaxed">{d.description.text}</p>
                </div>
              )}
              <dl className="grid grid-cols-2 gap-1.5 text-xs">
                {Object.entries(d.properties || {})
                  .slice(0, 14)
                  .map(([k, v]) => (
                    <React.Fragment key={k}>
                      <dt className="text-muted font-mono truncate">{k}</dt>
                      <dd className="text-ink truncate">{typeof v === "object" ? JSON.stringify(v) : String(v)}</dd>
                    </React.Fragment>
                  ))}
              </dl>
            </Panel>

            <Panel title="Centrality & Ranking Metrics">
              {Object.keys(d.metrics || {}).length === 0 ? (
                <p className="text-xs text-muted">Not in top-20 summary rankings (live neighbor count: {(d.neighbors || []).length}).</p>
              ) : (
                <div className="space-y-2 text-xs">
                  {Object.entries(d.metrics).map(([net, m]: [string, any]) => (
                    <div key={net} className="p-2 rounded bg-ground border border-rule tabular-nums">
                      <span className="font-semibold">{net}</span> · Rank #{m.rank ?? "—"} · PageRank{" "}
                      {typeof m.pagerank === "number" ? m.pagerank.toExponential(2) : "—"} · Degree {m.degree ?? "—"}
                    </div>
                  ))}
                </div>
              )}
            </Panel>

            <Panel title="Yearly Activity Sparkline (2021–2025)">
              {d.sparkline && d.sparkline.length > 0 ? (
                <EChartBox option={sparkOption} label="Node 2021-2025 activity sparkline" height={190} />
              ) : (
                <p className="text-xs text-muted">No temporal paper series available for this node offline.</p>
              )}
            </Panel>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Panel title={`Neighborhood (${(d.neighbors || []).length})`}>
              <Table
                label="Node neighbors"
                headers={["Relation", "Direction", "Neighbor", "Label", "Evidence / Support"]}
                rows={(d.neighbors || []).map((nb: any) => [
                  nb.relation,
                  nb.outgoing ? "out" : "in",
                  <button key={nb.id} type="button" onClick={() => onSelectNode(nb.id)} className="text-[var(--accent)] hover:underline text-left">
                    {nb.name || nb.id}
                  </button>,
                  nb.label,
                  `${nb.evidence_kind || "—"} (${nb.support_count ?? 1})`,
                ])}
              />
            </Panel>

            <Panel title={`Linked Papers (${(d.papers || []).length})`}>
              <Table
                label="Linked papers"
                headers={["Paper", "Year", "Venue"]}
                rows={(d.papers || []).map((p: any) => [
                  <button key={p.paper_id} type="button" onClick={() => onSelectNode(p.paper_id)} className="text-[var(--accent)] hover:underline text-left">
                    {p.title || p.paper_id}
                  </button>,
                  p.year ?? "—",
                  p.venue ?? "—",
                ])}
              />
            </Panel>
          </div>
        </>
      )}
    </div>
  );
};
