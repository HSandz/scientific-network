import React, { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { navigatorApi } from "../../lib/navigatorApi";
import { Panel, pct } from "../analytics/DashboardPrimitives";
import { EChartBox } from "../analytics/EChartBox";
import { MetricTooltip } from "./MetricTooltip";

interface SubjectPageProps {
  subjectId: string | null;
  onSelectSubject: (id: string) => void;
  onOpenGroup: (orgId: string) => void;
  onOpenCommunity: (cid: string) => void;
  onOpenNode360: (nodeId: string) => void;
}

export const SubjectPage: React.FC<SubjectPageProps> = ({
  subjectId,
  onSelectSubject,
  onOpenGroup,
  onOpenCommunity,
  onOpenNode360,
}) => {
  const [search, setSearch] = useState("");
  const activeId = subjectId || "method:Q3621696";

  const listQuery = useQuery({
    queryKey: ["nav-subjects", search],
    queryFn: ({ signal }) => navigatorApi.listSubjects({ q: search, limit: 30 }, signal),
  });

  const detailQuery = useQuery({
    queryKey: ["nav-subject-detail", activeId],
    queryFn: ({ signal }) => navigatorApi.getSubjectDetail(activeId, signal),
    enabled: Boolean(activeId),
  });

  const trendOption = useMemo(() => {
    const pts = detailQuery.data?.trend?.yearly || [];
    return {
      tooltip: { trigger: "axis" },
      grid: { top: 20, left: 48, right: 16, bottom: 26 },
      xAxis: { type: "category", data: pts.map((p) => String(p.year)) },
      yAxis: {
        type: "value",
        axisLabel: { formatter: (v: number) => `${(v * 100).toFixed(1)}%` },
      },
      series: [
        {
          name: "Share",
          type: "line",
          smooth: true,
          data: pts.map((p) => Number(p.share.toFixed(4))),
        },
      ],
    };
  }, [detailQuery.data]);

  const d = detailQuery.data;

  return (
    <div data-testid="page-subjects" className="p-4 sm:p-6 space-y-4 overflow-y-auto h-full">
      <div className="ledger-panel p-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold text-ink">{d?.name || "Topic / Method / Task / Dataset"}</h1>
          <p className="text-xs text-muted mt-0.5">
            {d?.kind || "Subject"} · Classification: {d?.classification_note || "descriptive (p <= 0.10 per subject, no multiple-testing correction)"}
            {d?.display_aliases?.length ? ` · Display aliases: ${d.display_aliases.join(", ")}` : ""}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Find subject or alias…"
            aria-label="Find topic, method, task or dataset"
            className="ledger-input h-8 px-2.5 text-xs w-52"
          />
          <select
            aria-label="Choose subject"
            value={activeId}
            onChange={(e) => onSelectSubject(e.target.value)}
            className="ledger-input h-8 px-2 text-xs max-w-xs"
          >
            {(listQuery.data?.items || []).map((it) => (
              <option key={it.id} value={it.id}>
                [{it.kind}] {it.name} ({it.total_papers})
              </option>
            ))}
          </select>
        </div>
      </div>

      {detailQuery.isLoading && <p role="status" className="text-sm text-muted">Loading subject profile…</p>}
      {detailQuery.error && <p role="alert" className="text-sm text-[var(--negative)]">{String(detailQuery.error)}</p>}

      {d && (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <Panel title="Annual Share & Descriptive Trend">
              {d.trend ? (
                <>
                  <div className="text-xs text-muted mb-2 flex flex-wrap gap-3">
                    <span>Class: <strong className="text-ink">{d.trend.class}</strong></span>
                    <span>Total papers: <strong className="text-ink">{d.trend.total_papers.toLocaleString()}</strong></span>
                    <span>Recent share: <strong className="text-ink">{pct(d.trend.recent_share, 2)}</strong></span>
                  </div>
                  <EChartBox option={trendOption} label="Subject annual share chart" height={210} />
                </>
              ) : (
                <p className="text-xs text-muted">No trend series recorded.</p>
              )}
            </Panel>

            <Panel title="Summary">
              {d.summary ? (
                <div className="space-y-2 text-xs">
                  <span className="inline-block px-2 py-0.5 rounded bg-raised text-ink font-medium">
                    {d.summary.label}
                  </span>
                  <p className="text-ink leading-relaxed">{d.summary.text}</p>
                  {d.summary.findings.length > 0 && (
                    <ul className="list-disc pl-4 space-y-1 text-muted">
                      {d.summary.findings.map((f, i) => (
                        <li key={i}>
                          {f.claim}{" "}
                          {f.paper_ids.slice(0, 3).map((pid) => (
                            <button
                              key={pid}
                              type="button"
                              onClick={() => onOpenNode360(pid)}
                              className="font-mono text-[11px] text-[var(--accent)] hover:underline mr-1"
                            >
                              [{pid}]
                            </button>
                          ))}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              ) : (
                <p className="text-xs text-muted">No summary generated for this subject yet.</p>
              )}
            </Panel>

            <Panel title="Related Entities & Communities">
              <div className="space-y-2 text-xs">
                {[["Methods", d.related_methods], ["Tasks", d.related_tasks], ["Datasets", d.related_datasets]].map(([lbl, items]) => (
                  <div key={String(lbl)}>
                    <span className="font-medium text-muted">{String(lbl)}: </span>
                    {(items as Array<{ id: string; name: string }>).length === 0 ? (
                      <span className="text-faint">None precomputed</span>
                    ) : (
                      (items as Array<{ id: string; name: string }>).slice(0, 6).map((x) => (
                        <button
                          key={x.id}
                          type="button"
                          onClick={() => onOpenNode360(x.id)}
                          className="inline-block mr-1.5 mb-1 px-1.5 py-0.5 rounded border border-border hover:bg-raised"
                        >
                          {x.name}
                        </button>
                      ))
                    )}
                  </div>
                ))}
                {d.communities.length > 0 && (
                  <div className="pt-1 border-t border-rule">
                    <span className="font-medium text-muted block mb-1">GraphRAG Communities:</span>
                    {d.communities.slice(0, 4).map((c) => (
                      <button
                        key={c.community_id}
                        type="button"
                        onClick={() => onOpenCommunity(c.community_id)}
                        className="block text-left text-[var(--accent)] hover:underline truncate max-w-full"
                      >
                        {c.community_id}: {c.title}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </Panel>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Panel title="Specialized Organizations (Ranked by PPR Lift)">
              <div className="text-xs text-muted mb-2">
                <MetricTooltip
                  label="PPR Lift & RCA"
                  definition={d.metric_definitions?.ppr_lift?.definition || "Topic PPR / global PPR"}
                  denominator={d.metric_definitions?.ppr_lift?.denominator}
                  network={d.metric_definitions?.ppr_lift?.network}
                  graphVersion={d.metric_definitions?.ppr_lift?.graph_version}
                />
                {d.filter_notes?.Organization ? ` · ${d.filter_notes.Organization}` : ""}
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead>
                    <tr className="border-b border-border text-muted">
                      <th className="p-1.5">Organization</th>
                      <th className="p-1.5">Lift</th>
                      <th className="p-1.5">RCA</th>
                      <th className="p-1.5">Raw PPR</th>
                      <th className="p-1.5">Papers</th>
                    </tr>
                  </thead>
                  <tbody>
                    {d.top_organizations.slice(0, 12).map((o) => (
                      <tr key={o.id} className="border-t border-rule">
                        <td className="p-1.5">
                          <button type="button" onClick={() => onOpenGroup(o.id)} className="text-[var(--accent)] hover:underline text-left">
                            {o.name}
                          </button>
                        </td>
                        <td className="p-1.5 tabular-nums font-medium">{o.lift?.toFixed(2) ?? "—"}</td>
                        <td className="p-1.5 tabular-nums">{o.rca?.toFixed(2) ?? "—"}</td>
                        <td className="p-1.5 tabular-nums text-muted">{(o.ppr_score ?? o.score ?? 0).toExponential(2)}</td>
                        <td className="p-1.5 tabular-nums">{o.subject_papers ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Panel>

            <Panel title="Key Researchers (by PPR Lift) & Most-Cited Corpus Papers">
              <div className="overflow-x-auto mb-3">
                <table className="w-full text-xs text-left">
                  <thead>
                    <tr className="border-b border-border text-muted">
                      <th className="p-1.5">Researcher</th>
                      <th className="p-1.5">Lift</th>
                      <th className="p-1.5">Raw PPR</th>
                      <th className="p-1.5">Papers</th>
                    </tr>
                  </thead>
                  <tbody>
                    {d.top_researchers.slice(0, 8).map((r) => (
                      <tr key={r.id} className="border-t border-rule">
                        <td className="p-1.5">
                          <button type="button" onClick={() => onOpenNode360(r.id)} className="text-[var(--accent)] hover:underline text-left">
                            {r.name}
                          </button>
                        </td>
                        <td className="p-1.5 tabular-nums font-medium">{r.lift?.toFixed(2) ?? "—"}</td>
                        <td className="p-1.5 tabular-nums text-muted">{(r.ppr_score ?? 0).toExponential(2)}</td>
                        <td className="p-1.5 tabular-nums">{r.subject_papers ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {d.most_cited_papers.length > 0 && (
                <div className="border-t border-border pt-2">
                  <h4 className="text-xs font-semibold mb-1.5">Most-Cited Papers (Within-Corpus CITES)</h4>
                  <ul className="space-y-1 text-xs">
                    {d.most_cited_papers.slice(0, 6).map((p) => (
                      <li key={p.paper_id} className="flex items-start justify-between gap-2">
                        <button type="button" onClick={() => onOpenNode360(p.paper_id)} className="text-left hover:underline text-ink">
                          {p.title} ({p.year}, {p.venue})
                        </button>
                        <span className="shrink-0 tabular-nums text-muted">{p.in_corpus_citations} cites</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </Panel>
          </div>
        </>
      )}
    </div>
  );
};
