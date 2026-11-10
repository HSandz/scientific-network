import React, { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { explorerApi } from "../../lib/api";
import { getThemeTokens } from "../../lib/colors";
import {
  bridgeRanks,
  ccdfPoints,
  componentHistogram,
  sectorCells,
  topicCells,
  TopicRow,
} from "../../lib/analytics";
import { useExplorerStore } from "../../stores/useExplorerStore";
import { GraphSummaryResponse } from "../../types/explorer";
import { EChartBox } from "./EChartBox";

const fmt = (n: unknown) =>
  typeof n === "number" ? n.toLocaleString() : "Unavailable";
const pct = (n: unknown, digits = 2) =>
  typeof n === "number" ? `${(n * 100).toFixed(digits)}%` : "Unavailable";
const Table: React.FC<{
  headers: string[];
  rows: React.ReactNode[][];
  label: string;
}> = ({ headers, rows, label }) => (
  <details className="mt-3 text-xs">
    <summary className="cursor-pointer py-2">
      {label} · data & keyboard actions ({rows.length} rows)
    </summary>
    <div className="overflow-auto max-h-96">
      <table className="w-full text-left">
        <caption className="sr-only">{label}</caption>
        <thead>
          <tr>
            {headers.map((h) => (
              <th key={h} className="p-2 font-medium text-muted">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-t border-border">
              {r.map((v, j) => (
                <td key={j} className="p-2 tabular-nums">
                  {v}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  </details>
);
const Panel: React.FC<{ title: string; children: React.ReactNode }> = ({
  title,
  children,
}) => (
  <section className="ledger-panel p-4 sm:p-5 min-w-0">
    <h2 className="text-sm font-semibold mb-2">{title}</h2>
    {children}
  </section>
);

export const AnalyticsView: React.FC<{
  summary?: GraphSummaryResponse;
  onFocusNodeInGraph: (id: string, name?: string) => void;
}> = ({ summary, onFocusNodeInGraph }) => {
  const {
    darkMode,
    analyticsSection: section,
    setViewMode,
    updateFilters,
    resetFilters,
    setWorkspaceTab,
    setCompareModalOpen,
    selectNode,
  } = useExplorerStore();
  const [venue, setVenue] = useState("venue:aaai"),
    [topic, setTopic] = useState(""),
    [yearMin, setYearMin] = useState(2021),
    [yearMax, setYearMax] = useState(2025);
  const [family, setFamily] = useState("");
  const [community, setCommunity] = useState("");
  const query = useQuery({
    queryKey: ["analytics-overview"],
    queryFn: ({ signal }) => explorerApi.getAnalyticsOverview(signal),
    staleTime: 300_000,
  });
  const data = query.data as Record<string, any> | undefined;
  const tokens = getThemeTokens(darkMode);
  const chart = useMemo(
    () => ({
      tooltip: { trigger: "item" },
      grid: { top: 35, left: 58, right: 20, bottom: 65 },
      textStyle: { color: tokens.chartAxis },
      xAxis: {
        type: "category",
        axisLabel: { color: tokens.chartAxis, fontSize: 12 },
      },
      yAxis: {
        type: "value",
        axisLabel: { color: tokens.chartAxis },
        splitLine: { lineStyle: { color: tokens.chartGrid } },
      },
      color: [tokens.chartPrimarySeries, tokens.chartSecondarySeries],
      legend: { textStyle: { color: tokens.chartAxis } },
    }),
    [darkMode],
  );
  const button = (id: string, name?: string) => (
    <button
      className="underline underline-offset-2 text-left"
      onClick={() => onFocusNodeInGraph(id, name)}
    >
      {name || id}
    </button>
  );
  const topics: TopicRow[] = data?.topic_shares_by_year_venue?.rows || [];
  const families: { topic_id: string; family_id: string; family: string }[] =
    data?.explorer_derived?.topic_families || [];
  const cells = useMemo(
    () =>
      topicCells(topics, venue, yearMin, yearMax, topic).filter(
        (r) =>
          !family ||
          families.some(
            (f) => f.family_id === family && f.topic_id === r.topic_id,
          ),
      ),
    [topics, venue, yearMin, yearMax, topic, family, families],
  );
  const topicNames = [...new Set(cells.map((r) => r.topic))];
  const years = [...new Set(cells.map((r) => r.year))].sort();
  const openCell = (r: TopicRow) => {
    setViewMode("heterogeneous");
    resetFilters();
    updateFilters({
      preset: "researcher_paper_topic",
      topicId: r.topic_id,
      venue: r.venue_id,
      yearMin: r.year,
      yearMax: r.year,
      limit: 120,
    });
    selectNode(r.topic_id, r.topic);
    setWorkspaceTab("graph");
  };
  if (query.isLoading)
    return (
      <p role="status" className="p-5">
        Loading frozen analytics…
      </p>
    );
  if (query.isError || !data || !data.graph_version || !data.projections)
    return (
      <div role="alert" className="p-5">
        Analytics unavailable:{" "}
        {query.error instanceof Error
          ? query.error.message
          : "incomplete artifact"}
        .{" "}
        <button className="ledger-btn" onClick={() => query.refetch()}>
          Retry
        </button>
      </div>
    );
  const q = summary?.quality || data.quality;
  const base = data.projections.researcher_collaboration,
    strict = data.robustness?.strict_projections?.researcher_collaboration;
  const sensitivity = data.robustness?.per_projection?.researcher_collaboration;
  const bridges = data.bridge_researchers?.top_researchers || [];
  const names = new Map<string, string>(
    bridges.map((b: any) => [b.researcher_id, b.researcher]),
  );
  const ranks = bridgeRanks(
    base?.top_betweenness || [],
    strict?.top_betweenness || [],
  );
  const profiles =
    data.bridge_researchers?.community_topic_profiles_top_20_by_size || [];
  const profile =
    profiles.find((p: any) => p.community_id === community) || profiles[0];
  const histogram = componentHistogram(base?.component_sizes || []);
  const mixing = sectorCells(data.sector_mixing?.matrix || []);
  const annual = data.annual_counts?.rows || [];
  const cited = data.cited_papers?.top_by_in_degree || [];
  const pairs = data.academia_industry_pairs || [];
  const derived = data.explorer_derived;
  const change = [...new Set(cells.map((r) => r.topic_id))].map((id) => {
    const rows = cells
      .filter((r) => r.topic_id === id)
      .sort((a, b) => a.year - b.year);
    const first = rows[0],
      last = rows[rows.length - 1];
    return {
      first,
      last,
      delta:
        100 *
        (last.share_of_fractional_topic_mass -
          first.share_of_fractional_topic_mass),
    };
  });
  return (
    <div
      data-testid="analytics-view"
      className="flex-1 overflow-y-auto p-3 sm:p-5 space-y-4 text-ink"
    >
      <div className="flex flex-wrap justify-between gap-2 items-center">
        <h1 className="text-lg font-semibold">Explore findings</h1>
        <span className="text-xs text-muted">
          {data.graph_version} · {data.analysis_method_version}
        </span>
      </div>
      <nav aria-label="Analytical sections" className="flex flex-wrap gap-1">
        {[
          ["robustness", "Evidence sensitivity"],
          ["topics", "Topic evolution"],
          ["communities", "Components & communities"],
          ["sectors", "Academia–industry"],
          ["trajectories", "Citations & annual metrics"],
        ].map(([id, label]) => (
          <button
            key={id}
            aria-pressed={section === id}
            className={`ledger-btn px-3 py-2 text-xs ${section === id ? "bg-raised" : ""}`}
            onClick={() => useExplorerStore.setState({ analyticsSection: id })}
          >
            {label}
          </button>
        ))}
      </nav>
      <section className="ledger-kpis">
        {[
          ["Domain nodes", summary?.total_nodes],
          ["Accepted relationships", summary?.total_edges],
          ["Core factual edges (R1–R4)", summary?.unique_core_factual_edges],
          ["Resolved researchers", summary?.resolved_core_researchers],
        ].map(([label, n]) => (
          <div key={String(label)} className="ledger-kpi">
            <div className="text-xs text-muted">{label}</div>
            <div className="text-xl tabular-nums">{fmt(n)}</div>
          </div>
        ))}
      </section>
      <section
        data-testid="quality-audit-panel"
        aria-label="Scientific quality and coverage audit"
        className="ledger-panel p-3 text-xs space-y-2"
      >
        <div className="grid sm:grid-cols-3 gap-3">
          <div data-testid="quality-card-edge-precision">
            <strong>
              AI-assessed edge precision: {pct(q?.edge_precision)}
            </strong>
            <p>
              {fmt(q?.edge_precision_correct)} / {fmt(q?.edge_precision_total)}{" "}
              correct · Wilson 95% CI {pct(q?.edge_precision_wilson_lower)}–
              {pct(q?.edge_precision_wilson_upper)} ·{" "}
              {q?.edge_precision_status || "Unavailable"}
            </p>
          </div>
          <div data-testid="quality-card-affiliation">
            <strong>
              Affiliation coverage: {pct(q?.affiliation_coverage)}
            </strong>
            <p>
              {fmt(q?.affiliation_positions_resolved)} /{" "}
              {fmt(q?.affiliation_positions_eligible)} matched-work authorship
              positions · Target {pct(q?.affiliation_target)} ·{" "}
              {q?.affiliation_status || "Unavailable"}
            </p>
          </div>
          <div data-testid="quality-card-topic">
            <strong>Topic coverage {pct(q?.topic_coverage)} ≠ accuracy</strong>
            <p>
              Precision {pct(q?.topic_precision)} (
              {fmt(q?.topic_precision_true_positive)} /{" "}
              {fmt(q?.topic_precision_predicted_labels)} weighted labels) ·
              Historical micro-F1{" "}
              {q?.topic_embedding_micro_f1?.toFixed(4) ?? "Unavailable"} vs{" "}
              {q?.topic_phrase_baseline_f1?.toFixed(4) ?? "Unavailable"} phrase
              baseline
            </p>
            <p>
              {fmt(q?.topic_papers_labeled)} / {fmt(q?.topic_papers_eligible)}{" "}
              labeled papers
            </p>
          </div>
        </div>
        <p className="text-muted">
          No independent human validation; reviewer independence and verified
          course accuracy not established. Wilson intervals exclude evaluator
          error. Inferred topics are provisional. Unknown affiliations/sectors
          do not imply absent collaboration.
        </p>
      </section>
      {section === "robustness" && (
        <>
          <Panel title="Which bridge claims survive repeated-paper evidence?">
            <p className="text-sm mb-3">
              {pct(sensitivity?.edge_retention_fraction)} of coauthorship edges
              survive the frozen strict filter. The top-20 bridge overlap is{" "}
              {fmt(sensitivity?.centralities?.betweenness?.overlap_count)}/20.
            </p>
            {strict && sensitivity ? (
              <>
                <EChartBox
                  label="Base versus strict researcher connectivity"
                  option={{
                    ...chart,
                    xAxis: {
                      ...chart.xAxis,
                      data: ["Base", "Strict ≥2 papers"],
                    },
                    yAxis: {
                      ...chart.yAxis,
                      name: "Largest component (%)",
                      max: 100,
                    },
                    series: [
                      {
                        name: "Largest component share",
                        type: "bar",
                        data: [
                          100 * sensitivity.largest_component_share_base,
                          100 * sensitivity.largest_component_share_strict,
                        ],
                      },
                    ],
                  }}
                />
                <Table
                  label="Connectivity"
                  headers={[
                    "Projection",
                    "Researchers",
                    "Edges",
                    "Largest component",
                    "Components",
                    "Isolates",
                  ]}
                  rows={[
                    [
                      "Corrected base",
                      fmt(base.node_count),
                      fmt(base.edge_count),
                      `${fmt(base.component_sizes?.[0])} (${pct(sensitivity.largest_component_share_base)})`,
                      fmt(base.component_sizes?.length),
                      fmt(base.isolate_count),
                    ],
                    [
                      "Frozen strict",
                      fmt(strict.node_count),
                      fmt(strict.edge_count),
                      `${fmt(strict.weak_or_undirected_component_sizes?.[0])} (${pct(sensitivity.largest_component_share_strict)})`,
                      fmt(strict.weak_or_undirected_component_sizes?.length),
                      fmt(strict.isolate_count),
                    ],
                  ]}
                />
                <div className="flex flex-wrap gap-2 mt-3">
                  <button
                    className="ledger-btn px-3 py-2 text-xs"
                    onClick={() => {
                      setViewMode("researchers");
                      resetFilters();
                      updateFilters({ minSupport: 2, minWeight: 0 });
                      setWorkspaceTab("graph");
                    }}
                  >
                    Inspect repeated co-publications →
                  </button>
                  <button
                    className="ledger-btn px-3 py-2 text-xs"
                    onClick={() => {
                      setViewMode("researchers");
                      resetFilters();
                      updateFilters({ minSupport: 1, minWeight: 0 });
                      setWorkspaceTab("graph");
                    }}
                  >
                    Inspect base collaboration →
                  </button>
                </div>
              </>
            ) : (
              <p role="status">
                Strict summaries unavailable in this runtime artifact. Operator
                must prepare a new versioned artifact directory; no successful
                comparison inferred.
              </p>
            )}
            <details className="text-xs mt-3">
              <summary className="cursor-pointer py-2">
                Method & limitations
              </summary>
              <p>
                Frozen minimum support = 2 distinct core papers; same researcher
                denominator including isolates. Approximate weighted betweenness
                uses 256 pivots, inverse positive fractional strength as
                distance, random seed 20261101. Louvain NetworkX, seed 17,
                resolution 0.8. Rankings describe structural position, never
                researcher quality. Historical 73.6% largest component belongs
                to a different frozen graph, not a UI filter. The historical
                blanket strict filter mechanically removes CITES/HAS_TOPIC; this
                UI applies repeated-paper filtering only to collaboration
                predicates.
              </p>
            </details>
          </Panel>
          <Panel title="Top-20 bridge ranking stability (base ↔ strict)">
            <p className="text-xs text-muted">
              Outside top 20 is not a zero centrality. Each stable ID opens its
              collaboration graph and paper evidence.
            </p>
            <Table
              label="Bridge ranking comparison"
              headers={["Researcher / stable ID", "Base rank", "Strict rank"]}
              rows={ranks.map((r) => [
                button(r.id, names.get(r.id)),
                r.base ?? "Outside top 20",
                r.strict ?? "Outside top 20",
              ])}
            />
            <div className="grid sm:grid-cols-2 gap-2 mt-3">
              {bridges.slice(0, 6).map((b: any) => (
                <div key={b.researcher_id} className="text-xs py-2">
                  {button(b.researcher_id, b.researcher)} ·{" "}
                  {b.betweenness.toFixed(6)}
                  <p className="text-muted">
                    {b.community_id} · {fmt(b.community_member_count)} members
                  </p>
                </div>
              ))}
            </div>
          </Panel>
        </>
      )}
      {section === "topics" && (
        <Panel title="Which inferred topics changed by venue and year?">
          <div className="flex flex-wrap gap-3 text-xs mb-3">
            <label>
              Venue
              <select
                aria-label="Topic venue"
                value={venue}
                onChange={(e) => setVenue(e.target.value)}
                className="ledger-input ml-2"
              >
                <option value="venue:aaai">AAAI</option>
                <option value="venue:ijcai">IJCAI</option>
              </select>
            </label>
            <label>
              Family
              <select
                aria-label="Topic family"
                value={family}
                onChange={(e) => setFamily(e.target.value)}
                className="ledger-input ml-2"
              >
                <option value="">All families</option>
                {[
                  ...new Map(
                    families.map((f) => [f.family_id, f.family]),
                  ).entries(),
                ].map(([id, name]) => (
                  <option key={id} value={id}>
                    {name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Topic
              <select
                aria-label="Topic selection"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                className="ledger-input ml-2 max-w-52"
              >
                <option value="">All inferred leaves</option>
                {[
                  ...new Map(
                    topics.map((r) => [r.topic_id, r.topic]),
                  ).entries(),
                ].map(([id, name]) => (
                  <option key={id} value={id}>
                    {name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              From
              <input
                aria-label="Topic first year"
                type="number"
                min="2021"
                max={yearMax}
                value={yearMin}
                onChange={(e) =>
                  setYearMin(Math.max(2021, Math.min(yearMax, +e.target.value)))
                }
                className="ledger-input w-20 ml-2"
              />
            </label>
            <label>
              Through
              <input
                aria-label="Topic last year"
                type="number"
                min={yearMin}
                max="2025"
                value={yearMax}
                onChange={(e) =>
                  setYearMax(Math.min(2025, Math.max(yearMin, +e.target.value)))
                }
                className="ledger-input w-20 ml-2"
              />
            </label>
          </div>
          <p className="text-xs text-muted">
            Each labeled paper contributes 1/k to each of its k labels;
            fractional mass / labeled papers defines prevalence. Coverage
            includes abstentions; prevalence and percentage-point change are not
            accuracy or causal growth. Click a cell or use its data-table button
            for a bounded, illustrative paper-topic graph.
          </p>
          <EChartBox
            label="Year by inferred topic share"
            height={Math.max(300, topicNames.length * 27 + 100)}
            onClick={(p) => {
              const r = cells[p.dataIndex];
              if (r) openCell(r);
            }}
            option={{
              ...chart,
              grid: {
                top: 20,
                left: 15,
                right: 15,
                bottom: 60,
                containLabel: true,
              },
              xAxis: { type: "category", data: years },
              yAxis: {
                type: "category",
                data: topicNames,
                axisLabel: {
                  color: tokens.chartAxis,
                  width: 180,
                  overflow: "truncate",
                },
              },
              visualMap: {
                min: 0,
                max: Math.max(
                  0,
                  ...cells.map((r) => r.share_of_fractional_topic_mass * 100),
                ),
                orient: "horizontal",
                left: "center",
                bottom: 0,
                inRange: { color: tokens.heatmapScale },
                textStyle: { color: tokens.chartAxis },
              },
              series: [
                {
                  type: "heatmap",
                  data: cells.map((r) => [
                    years.indexOf(r.year),
                    topicNames.indexOf(r.topic),
                    100 * r.share_of_fractional_topic_mass,
                  ]),
                  label: {
                    show: !!topic,
                    formatter: (p: any) => `${p.value[2].toFixed(1)}%`,
                  },
                },
              ],
            }}
          />
          <Table
            label="Topic cells and filtered graphs"
            headers={[
              "Year",
              "Topic / graph",
              "Raw count",
              "Fractional count",
              "Labeled / all papers",
              "Coverage",
              "Share",
              "Abstentions",
            ]}
            rows={cells.map((r) => [
              r.year,
              <button
                className="underline text-left"
                onClick={() => openCell(r)}
              >
                {r.topic} → papers
              </button>,
              r.paper_count,
              r.fractional_paper_count.toFixed(3),
              `${r.labeled_paper_count} / ${r.all_core_paper_count}`,
              pct(r.topic_label_coverage),
              pct(r.share_of_fractional_topic_mass),
              r.all_core_paper_count - r.labeled_paper_count,
            ])}
          />
          {topic && (
            <EChartBox
              label="Selected topic comparison by venue"
              option={{
                ...chart,
                tooltip: { trigger: "axis" },
                legend: { textStyle: { color: tokens.chartAxis } },
                xAxis: { ...chart.xAxis, data: years },
                yAxis: { ...chart.yAxis, name: "Share of labeled papers (%)" },
                series: ["venue:aaai", "venue:ijcai"].map((vid) => ({
                  type: "line",
                  name: vid === "venue:aaai" ? "AAAI" : "IJCAI",
                  data: years.map((year) => {
                    const r = topics.find(
                      (r) =>
                        r.topic_id === topic &&
                        r.venue_id === vid &&
                        r.year === year,
                    );
                    return r ? 100 * r.share_of_fractional_topic_mass : null;
                  }),
                })),
              }}
            />
          )}
          <Table
            label="Prevalence change in selected venue"
            headers={[
              "Topic",
              "First year/share",
              "Last year/share",
              "Percentage-point change",
            ]}
            rows={change.map((r) => [
              r.first.topic,
              `${r.first.year}: ${pct(r.first.share_of_fractional_topic_mass)}`,
              `${r.last.year}: ${pct(r.last.share_of_fractional_topic_mass)}`,
              `${r.delta >= 0 ? "+" : ""}${r.delta.toFixed(2)} pp`,
            ])}
          />
        </Panel>
      )}
      {section === "communities" && (
        <div className="grid lg:grid-cols-2 gap-4">
          <Panel title="Connected components, including isolates">
            <p className="text-xs text-muted">
              {fmt(base?.component_sizes?.length)} components /{" "}
              {fmt(base?.node_count)} researchers; {fmt(base?.isolate_count)}{" "}
              isolates. A component differs from a Louvain community. Size
              histogram includes the full tail.
            </p>
            <EChartBox
              label="Component size distribution"
              option={{
                ...chart,
                xAxis: {
                  ...chart.xAxis,
                  type: "log",
                  name: "Researchers per component",
                  min: 1,
                },
                yAxis: {
                  ...chart.yAxis,
                  type: "log",
                  name: "Components",
                  min: 1,
                },
                series: [{ type: "line", data: histogram }],
              }}
            />
            <Table
              label="Component distribution"
              headers={["Size", "Components"]}
              rows={histogram.map((r) => r)}
            />
            <Table
              label="Largest component representatives"
              headers={[
                "Component stable membership ID",
                "Size",
                "Representative collaboration neighborhood",
              ]}
              rows={(derived?.component_examples || []).map((c: any) => [
                c.component_id,
                c.size,
                button(c.representative_id, c.representative),
              ])}
            />
            <p className="text-xs text-muted">
              Representative = highest accepted coauthor degree, stable-ID
              tie-break. Its bounded neighborhood is illustrative of that
              component; it does not display every member.
            </p>
          </Panel>
          <Panel title="What do frozen researcher communities study?">
            <label className="text-xs">
              Community
              <select
                aria-label="Community profile"
                className="ledger-input w-full my-2"
                value={profile?.community_id || ""}
                onChange={(e) => setCommunity(e.target.value)}
              >
                {profiles.map((p: any) => (
                  <option key={p.community_id} value={p.community_id}>
                    {p.community_id} · {p.member_count} researchers
                  </option>
                ))}
              </select>
            </label>
            {profile && (
              <>
                <p className="text-xs">
                  {fmt(profile.paper_count)} distinct papers;{" "}
                  {fmt(profile.topic_labeled_paper_count)} labeled papers. Only
                  the stored top five topics are available. Not in stored
                  profile ≠ zero.
                </p>
                <EChartBox
                  label="Community inferred topic portfolio"
                  option={{
                    ...chart,
                    grid: {
                      left: 15,
                      right: 15,
                      top: 20,
                      bottom: 80,
                      containLabel: true,
                    },
                    xAxis: {
                      ...chart.xAxis,
                      data: profile.top_topics.map((t: any) => t.topic),
                      axisLabel: {
                        color: tokens.chartAxis,
                        rotate: 25,
                        width: 100,
                        overflow: "truncate",
                      },
                    },
                    yAxis: { ...chart.yAxis, name: "Fractional mass (%)" },
                    series: [
                      {
                        type: "bar",
                        data: profile.top_topics.map(
                          (t: any) => 100 * t.share_of_fractional_topic_mass,
                        ),
                      },
                    ],
                  }}
                />
                <button
                  className="ledger-btn px-3 py-2 text-xs"
                  onClick={() => {
                    setViewMode("researchers");
                    updateFilters({ communityId: profile.community_id });
                    setWorkspaceTab("graph");
                  }}
                >
                  Open representative community graph →
                </button>
                <Table
                  label="Stored community topic profile"
                  headers={[
                    "Inferred topic",
                    "Distinct papers",
                    "Fractional share",
                  ]}
                  rows={profile.top_topics.map((t: any) => [
                    t.topic,
                    t.paper_count,
                    pct(t.share_of_fractional_topic_mass),
                  ])}
                />
              </>
            )}
            <p className="text-xs text-muted mt-3">
              Louvain NetworkX seed 17, resolution 0.8. IDs are run-specific and
              unstable across graph versions. Community paper sets may overlap;
              do not sum as unique corpus papers.
            </p>
          </Panel>
        </div>
      )}
      {section === "sectors" && (
        <>
          <Panel title="Academia–industry co-publication, including unknown sectors">
            <p className="text-xs text-muted">
              Symmetric organization-pair × core-paper support matrix. A pair is
              counted once per supporting paper; cells are neither unique pairs
              nor unique papers. Unknown means missing sector evidence.
              Co-publication establishes neither funding, contracts nor
              employment.
            </p>
            <EChartBox
              label="Sector pair-paper supports"
              option={{
                ...chart,
                grid: { left: 90, right: 15, top: 10, bottom: 80 },
                xAxis: {
                  type: "category",
                  data: mixing.sectors,
                  axisLabel: { color: tokens.chartAxis, rotate: 25 },
                },
                yAxis: {
                  type: "category",
                  data: mixing.sectors,
                  axisLabel: { color: tokens.chartAxis },
                },
                visualMap: {
                  min: 0,
                  max: mixing.max,
                  orient: "horizontal",
                  left: "center",
                  bottom: 0,
                  inRange: { color: tokens.heatmapScale },
                  textStyle: { color: tokens.chartAxis },
                },
                series: [
                  {
                    type: "heatmap",
                    data: mixing.cells,
                    label: { show: true, color: tokens.chartInkSeries },
                  },
                ],
              }}
            />
            <Table
              label="Sector mixing"
              headers={["Sector A", "Sector B", "Pair-paper supports"]}
              rows={(data.sector_mixing?.matrix || []).map((r: any) => [
                r.row_sector,
                r.column_sector,
                r.pair_paper_support_count,
              ])}
            />
          </Panel>
          <Panel title="Repeated cross-sector topic pairs">
            <div className="grid md:grid-cols-2 gap-4">
              {pairs.map((p: any, i: number) => (
                <div key={i} className="text-xs border-t border-border py-3">
                  <strong>
                    {p.academia_organization} ↔ {p.industry_organization}
                  </strong>
                  <p>
                    {p.topic}: {p.supported_paper_count} distinct supporting
                    papers
                  </p>
                  <button
                    className="ledger-btn px-3 py-2 mt-2"
                    onClick={() =>
                      setCompareModalOpen(
                        true,
                        p.academia_organization_id,
                        p.industry_organization_id,
                      )
                    }
                  >
                    Compare portfolios & supporting papers
                  </button>
                </div>
              ))}
            </div>
          </Panel>
        </>
      )}
      {section === "trajectories" && (
        <>
          <Panel title="Annual corpus and collaboration metrics">
            <p className="text-xs text-muted">
              Separate scales retain actual counts. New coauthor pair = an
              accepted pair counted in its earliest supported core-paper year;
              not all pairs active that year. Annual active researcher sets
              overlap and must not be summed.
            </p>
            <div className="grid lg:grid-cols-3 gap-3">
              {[
                ["Core papers", "paper_count"],
                ["Active researchers", "active_researcher_count"],
                ["New coauthor pairs", "new_collaboration_pair_count"],
              ].map(([title, key]) => (
                <div key={key}>
                  <h3 className="text-xs mt-3">{title}</h3>
                  <EChartBox
                    label={title}
                    height={240}
                    option={{
                      ...chart,
                      xAxis: {
                        ...chart.xAxis,
                        data: annual.map((r: any) => r.year),
                      },
                      series: [
                        { type: "bar", data: annual.map((r: any) => r[key]) },
                      ],
                    }}
                  />
                </div>
              ))}
            </div>
            <Table
              label="Annual metrics"
              headers={[
                "Year",
                "Core papers",
                "Active researchers",
                "New coauthor pairs",
              ]}
              rows={annual.map((r: any) => [
                r.year,
                r.paper_count,
                r.active_researcher_count,
                r.new_collaboration_pair_count,
              ])}
            />
          </Panel>
          <Panel title="Researcher coauthor degree CCDF, complete tail">
            <p className="text-xs text-muted">
              Numerical degree x-axis; logarithmic researcher-count y-axis.
              Includes {fmt(base?.isolate_count)} isolates /{" "}
              {fmt(data.researcher_degree_ccdf?.node_denominator)} researchers.
              Unique coauthor degree is specific to this projection.
            </p>
            <EChartBox
              label="Complete researcher degree CCDF"
              option={{
                ...chart,
                xAxis: {
                  ...chart.xAxis,
                  type: "value",
                  name: "Coauthor degree",
                },
                yAxis: {
                  ...chart.yAxis,
                  type: "log",
                  min: 1,
                  name: "Researchers ≥ k",
                },
                series: [
                  {
                    type: "line",
                    showSymbol: false,
                    data: ccdfPoints(data.researcher_degree_ccdf?.rows || []),
                  },
                ],
              }}
            />
            <Table
              label="Complete CCDF"
              headers={["Degree k", "Researchers ≥ k", "Fraction ≥ k"]}
              rows={(data.researcher_degree_ccdf?.rows || []).map((r: any) => [
                r.degree,
                r.researcher_count_at_least,
                pct(r.fraction_at_least),
              ])}
            />
          </Panel>
          <Panel title="Citation cohorts: compare papers within venue and conference year">
            <p className="text-xs text-muted">
              Exploratory empirical CDF of within-corpus incoming citations.
              Percentile = fraction of same-venue/year papers with in-degree ≤
              this paper, including ties and uncited papers. This controls
              cohort membership only, not reference coverage or exposure. No
              prediction or independent evaluation.
            </p>
            {derived ? (
              <>
                <Table
                  label="Citation cohort distributions"
                  headers={[
                    "Venue",
                    "Year",
                    "All cohort papers",
                    "Uncited",
                    "In-degree: paper counts",
                  ]}
                  rows={derived.citation_cohorts.map((r: any) => [
                    r.venue_id,
                    r.year,
                    r.paper_denominator,
                    r.zero_in_degree_count,
                    r.distribution
                      .map((d: any) => `${d.in_degree}: ${d.paper_count}`)
                      .join("; "),
                  ])}
                />
                <Table
                  label="Within-cohort citation leaders"
                  headers={[
                    "Paper / evidence",
                    "Venue",
                    "Year",
                    "Incoming citations",
                    "Cohort N",
                    "Empirical percentile",
                  ]}
                  rows={derived.cohort_leaders.map((p: any) => [
                    <button
                      className="underline text-left"
                      onClick={() => {
                        setViewMode("citations");
                        onFocusNodeInGraph(p.paper_id, p.title);
                      }}
                    >
                      {p.title}
                    </button>,
                    p.venue_id,
                    p.year,
                    p.in_degree,
                    p.cohort_paper_denominator,
                    pct(p.empirical_percentile_including_ties),
                  ])}
                />
              </>
            ) : (
              <p className="text-xs">
                Exploratory cohort artifact unavailable.
              </p>
            )}
          </Panel>
          <Panel title="Organization collaboration persistence by supported paper year">
            <p className="text-xs text-muted">
              Top 25 accepted organization pairs, sorted by distinct full-period
              R8 evidence paper support then edge ID. Active years count
              observed co-publication years; zero years do not prove a
              partnership ceased. Topic counts overlap for multilabel papers.
              Exploratory selection, not a preregistered test.
            </p>
            {derived ? (
              <Table
                label="Pair persistence, inferred topics and evidence"
                headers={[
                  "Pair / provenance",
                  "Distinct papers",
                  "Active years",
                  "2021–2025 paper counts",
                  "Inferred topic support",
                ]}
                rows={derived.organization_pair_persistence.map((p: any) => [
                  <button
                    className="underline text-left"
                    onClick={() => {
                      setCompareModalOpen(true, p.source_id, p.target_id);
                    }}
                  >
                    {p.source} ↔ {p.target}
                  </button>,
                  p.distinct_support_papers,
                  p.active_year_count,
                  p.by_year
                    .map((y: any) => `${y.year}: ${y.distinct_support_papers}`)
                    .join(" · "),
                  p.inferred_topics
                    .map((t: any) => `${t.topic}: ${t.distinct_support_papers}`)
                    .join("; "),
                ])}
              />
            ) : (
              <p className="text-xs">Persistence artifact unavailable.</p>
            )}
          </Panel>
          <Panel title="Citations within the release corpus">
            <p className="text-xs text-muted">
              Citing → cited, both endpoints AAAI/IJCAI 2021–2025. Counts are
              not global influence or future impact; older papers have more
              exposure.
            </p>
            <Table
              label="Top within-corpus cited papers"
              headers={["Paper / graph", "Year", "In-degree", "PageRank"]}
              rows={cited.map((p: any) => [
                <button
                  className="underline text-left"
                  onClick={() => {
                    setViewMode("citations");
                    onFocusNodeInGraph(p.paper_id, p.title);
                  }}
                >
                  {p.title}
                </button>,
                p.year,
                p.in_degree,
                p.pagerank,
              ])}
            />
          </Panel>
        </>
      )}
      <details className="text-xs text-muted">
        <summary className="cursor-pointer py-2">
          Artifact provenance and limitations
        </summary>
        <pre className="whitespace-pre-wrap break-all">
          {JSON.stringify(
            {
              analysis: data.provenance,
              exploratory: derived
                ? {
                    method: derived.method_version,
                    graph_sha256: derived.graph_sha256,
                    config_sha256: derived.config_sha256,
                    definitions: derived.definitions,
                  }
                : "Unavailable",
            },
            null,
            2,
          )}
        </pre>
        {(data.limitations || []).map((s: string) => (
          <p key={s}>{s}</p>
        ))}
      </details>
    </div>
  );
};
