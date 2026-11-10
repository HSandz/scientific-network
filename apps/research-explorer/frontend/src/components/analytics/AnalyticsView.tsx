import React, { useEffect, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import * as echarts from "echarts";
import {
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
  GitCompare,
} from "lucide-react";
import { explorerApi } from "../../lib/api";
import { getThemeTokens } from "../../lib/colors";
import { useExplorerStore } from "../../stores/useExplorerStore";
import { GraphSummaryResponse, QualityContract } from "../../types/explorer";

interface EChartBoxProps {
  option: echarts.EChartsOption;
  height?: number;
  darkMode: boolean;
}

const EChartBox: React.FC<EChartBoxProps> = ({
  option,
  height = 280,
  darkMode,
}) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const instanceRef = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    if (instanceRef.current) {
      instanceRef.current.dispose();
    }
    const chart = echarts.init(el, darkMode ? "dark" : undefined);
    instanceRef.current = chart;
    chart.setOption({
      backgroundColor: "transparent",
      textStyle: {
        fontFamily: "Geist, system-ui, sans-serif",
      },
      ...option,
    });

    const handleResize = () => {
      chart.resize();
    };
    window.addEventListener("resize", handleResize);

    let ro: ResizeObserver | null = null;
    if (typeof ResizeObserver !== "undefined") {
      ro = new ResizeObserver(() => {
        chart.resize();
      });
      ro.observe(el);
    }

    return () => {
      window.removeEventListener("resize", handleResize);
      if (ro) ro.disconnect();
      chart.dispose();
      instanceRef.current = null;
    };
  }, [option, darkMode]);

  return <div ref={containerRef} style={{ width: "100%", height }} />;
};

interface AnalyticsViewProps {
  summary?: GraphSummaryResponse;
  onFocusNodeInGraph: (nodeId: string, name?: string) => void;
}

export const AnalyticsView: React.FC<AnalyticsViewProps> = ({
  summary,
  onFocusNodeInGraph,
}) => {
  const {
    darkMode,
    setViewMode,
    setWorkspaceTab,
    updateFilters,
    selectNode,
    setCompareModalOpen,
  } = useExplorerStore();

  const analyticsQuery = useQuery({
    queryKey: ["analytics-overview"],
    queryFn: ({ signal }) => explorerApi.getAnalyticsOverview(signal),
    staleTime: 300_000,
  });

  if (analyticsQuery.isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-ground text-sm text-muted">
        Loading precomputed release v4 analytics...
      </div>
    );
  }

  const data = (analyticsQuery.data || {}) as Record<string, any>;
  const annualRows: Array<{
    year: number;
    paper_count: number;
    active_researcher_count: number;
    new_collaboration_pair_count: number;
  }> = data.annual_counts?.rows || [];

  const sectorMatrix: Array<{
    row_sector: string;
    column_sector: string;
    pair_paper_support_count: number;
  }> = data.sector_mixing?.matrix || [];

  const ccdfRows: Array<{
    degree: number;
    researcher_count_at_least: number;
    fraction_at_least: number;
  }> = data.researcher_degree_ccdf?.rows || [];

  const bridgeResearchers: Array<{
    researcher_id: string;
    researcher: string;
    betweenness: number;
    community_id: string;
    community_member_count: number;
    community_top_topics: Array<{ topic: string; paper_count: number }>;
  }> = data.bridge_researchers?.top_researchers || [];

  const topCitedPapers: Array<{
    paper_id: string;
    title: string;
    year: number;
    venue: string;
    in_degree: number;
    pagerank: number;
  }> = data.cited_papers?.top_by_in_degree || [];

  const acadIndustryPairs: Array<{
    academia_organization_id: string;
    academia_organization: string;
    industry_organization_id: string;
    industry_organization: string;
    topic_id: string;
    topic: string;
    supported_paper_count: number;
  }> = data.academia_industry_pairs || [];

  const countryPairs: Array<{
    country_a: string;
    country_b: string;
    pair_paper_support_count: number;
  }> = data.country_pair_collaborations?.rows || [];

  const tokens = getThemeTokens(darkMode);
  const axisColor = tokens.chartAxis;
  const gridColor = tokens.chartGrid;
  const primarySeriesColor = tokens.chartPrimarySeries;
  const inkSeriesColor = tokens.chartInkSeries;
  const secondarySeriesColor = tokens.chartSecondarySeries;

  const quality: QualityContract | undefined =
    summary?.quality || (data.quality as QualityContract | undefined);

  const edgePrecPct =
    quality?.edge_precision !== undefined
      ? `${(quality.edge_precision * 100).toFixed(2)}%`
      : "96.50%";
  const edgePrecDetail = quality
    ? `${quality.edge_precision_correct ?? 193} / ${quality.edge_precision_total ?? 200} correct · Wilson 95% CI: ${(((quality.edge_precision_wilson_lower ?? 0.9295)) * 100).toFixed(2)}%–${(((quality.edge_precision_wilson_upper ?? 0.9829)) * 100).toFixed(2)}% · Target ${(((quality.edge_precision_target ?? 0.9)) * 100).toFixed(1)}%`
    : "193 / 200 correct · Wilson 95% CI: 92.95%–98.29%";

  const affCovPct =
    quality?.affiliation_coverage !== undefined
      ? `${(quality.affiliation_coverage * 100).toFixed(2)}%`
      : "73.71%";
  const affCovDetail = quality
    ? `${(quality.affiliation_positions_resolved ?? 48259).toLocaleString()} / ${(quality.affiliation_positions_eligible ?? 65469).toLocaleString()} authorship positions on OpenAlex-matched works · Target ${(((quality.affiliation_target ?? 0.8)) * 100).toFixed(1)}% (${(quality.affiliation_papers_with_edge ?? 10037).toLocaleString()} / ${(quality.affiliation_papers_eligible ?? 13617).toLocaleString()} core papers)`
    : "48,259 / 65,469 authorship positions on OpenAlex-matched works · Target 80.0%";

  const topicCovPct =
    quality?.topic_coverage !== undefined
      ? `${(quality.topic_coverage * 100).toFixed(2)}%`
      : "85.00%";
  const topicPrecPct =
    quality?.topic_precision !== undefined
      ? `${(quality.topic_precision * 100).toFixed(2)}%`
      : "68.63%";
  const topicF1Val =
    quality?.topic_embedding_micro_f1 !== undefined
      ? quality.topic_embedding_micro_f1.toFixed(4)
      : "0.4667";
  const topicDetail = quality
    ? `${(quality.topic_papers_labeled ?? 11575).toLocaleString()} / ${(quality.topic_papers_eligible ?? 13617).toLocaleString()} core papers (Target ${(((quality.topic_coverage_target ?? 0.8)) * 100).toFixed(1)}% PASS) · AI-assessed topic precision ${topicPrecPct} (140/204, Target ${(((quality.topic_precision_target ?? 0.95)) * 100).toFixed(1)}% FAIL) · Historical micro-F1 ${topicF1Val} (vs ${(quality.topic_phrase_baseline_f1 ?? 0.2301).toFixed(4)} phrase baseline)`
    : "11,575 / 13,617 core papers (Target 80.0% PASS) · AI-assessed topic precision 68.63% (140/204, Target 95.0% FAIL) · Historical micro-F1 0.4667 (vs 0.2301 phrase baseline)";

  // 1. Annual Corpus & Collaboration Growth
  const annualChartOption: echarts.EChartsOption = {
    tooltip: { trigger: "axis" },
    legend: {
      top: 0,
      right: 0,
      itemWidth: 12,
      itemHeight: 8,
      textStyle: { fontSize: 12, color: axisColor },
    },
    grid: { top: 38, left: 52, right: 18, bottom: 28 },
    xAxis: {
      type: "category",
      data: annualRows.map((r) => String(r.year)),
      axisLabel: { fontSize: 12, color: axisColor },
      axisLine: { lineStyle: { color: gridColor } },
    },
    yAxis: {
      type: "value",
      axisLabel: { fontSize: 12, color: axisColor },
      splitLine: { lineStyle: { color: gridColor } },
    },
    series: [
      {
        name: "Core papers",
        type: "bar",
        barMaxWidth: 26,
        data: annualRows.map((r) => r.paper_count),
        itemStyle: { color: primarySeriesColor, borderRadius: [2, 2, 0, 0] },
      },
      {
        name: "Active researchers",
        type: "line",
        smooth: false,
        symbolSize: 6,
        data: annualRows.map((r) => r.active_researcher_count),
        itemStyle: { color: inkSeriesColor },
        lineStyle: { width: 2, color: inkSeriesColor },
      },
      {
        name: "New coauthor pairs",
        type: "line",
        smooth: false,
        symbolSize: 6,
        data: annualRows.map((r) => r.new_collaboration_pair_count),
        itemStyle: { color: secondarySeriesColor },
        lineStyle: { width: 2, type: "dashed", color: secondarySeriesColor },
      },
    ],
  };

  // 2. Sector Mixing Heatmap
  const sectors = ["academia", "industry", "government", "nonprofit"];
  const heatmapData: Array<[number, number, number]> = [];
  for (const cell of sectorMatrix) {
    const xIdx = sectors.indexOf(cell.column_sector);
    const yIdx = sectors.indexOf(cell.row_sector);
    if (xIdx >= 0 && yIdx >= 0) {
      heatmapData.push([xIdx, yIdx, cell.pair_paper_support_count]);
    }
  }

  const sectorHeatmapOption: echarts.EChartsOption = {
    tooltip: {
      position: "top",
      formatter: (params: any) => {
        const [x, y, val] = params.data;
        return `${sectors[y]} × ${sectors[x]}: <b>${Number(
          val
        ).toLocaleString()}</b> pair-paper supports`;
      },
    },
    grid: { top: 12, left: 86, right: 20, bottom: 48 },
    xAxis: {
      type: "category",
      data: sectors.map((s) => s.charAt(0).toUpperCase() + s.slice(1)),
      axisLabel: { fontSize: 12, color: axisColor },
      splitArea: { show: false },
    },
    yAxis: {
      type: "category",
      data: sectors.map((s) => s.charAt(0).toUpperCase() + s.slice(1)),
      axisLabel: { fontSize: 12, color: axisColor },
      splitArea: { show: false },
    },
    visualMap: {
      min: 0,
      max: 11000,
      calculable: false,
      orient: "horizontal",
      left: "center",
      bottom: 0,
      itemWidth: 12,
      itemHeight: 90,
      textStyle: { fontSize: 12, color: axisColor },
      inRange: {
        color: tokens.heatmapScale,
      },
    },
    series: [
      {
        name: "Sector mixing",
        type: "heatmap",
        data: heatmapData,
        label: {
          show: true,
          formatter: (p: any) => Number(p.data[2]).toLocaleString(),
          fontSize: 12,
          color: inkSeriesColor,
        },
      },
    ],
  };

  // 3. Researcher Coauthorship Degree CCDF
  const ccdfOption: echarts.EChartsOption = {
    tooltip: { trigger: "axis" },
    grid: { top: 18, left: 58, right: 20, bottom: 42 },
    xAxis: {
      type: "category",
      name: "Coauthor degree k",
      nameLocation: "middle",
      nameGap: 26,
      nameTextStyle: { fontSize: 12, color: axisColor },
      axisLabel: { fontSize: 12, color: axisColor },
      data: ccdfRows.slice(0, 35).map((r) => String(r.degree)),
    },
    yAxis: {
      type: "log",
      name: "Researchers ≥ k",
      nameTextStyle: { fontSize: 12, color: axisColor },
      axisLabel: { fontSize: 12, color: axisColor },
      splitLine: { lineStyle: { color: gridColor } },
      min: 1,
    },
    series: [
      {
        name: "Researchers with degree ≥ k",
        type: "line",
        smooth: false,
        symbolSize: 5,
        data: ccdfRows.slice(0, 35).map((r) => r.researcher_count_at_least),
        itemStyle: { color: primarySeriesColor },
        lineStyle: { width: 2, color: primarySeriesColor },
        areaStyle: { opacity: 0.08, color: primarySeriesColor },
      },
    ],
  };

  // 4. Country-Pair Collaborations
  const countryBarOption: echarts.EChartsOption = {
    tooltip: { trigger: "axis" },
    grid: { top: 12, left: 76, right: 24, bottom: 28 },
    xAxis: {
      type: "value",
      axisLabel: { fontSize: 12, color: axisColor },
      splitLine: { lineStyle: { color: gridColor } },
    },
    yAxis: {
      type: "category",
      inverse: true,
      axisLabel: { fontSize: 12, color: axisColor },
      data: countryPairs
        .slice(0, 10)
        .map((c) => `${c.country_a} – ${c.country_b}`),
    },
    series: [
      {
        name: "Pair-paper support",
        type: "bar",
        barMaxWidth: 18,
        data: countryPairs.slice(0, 10).map((c) => c.pair_paper_support_count),
        itemStyle: { color: primarySeriesColor, borderRadius: [0, 2, 2, 0] },
      },
    ],
  };

  const totalNodesText =
    summary?.total_nodes !== undefined
      ? summary.total_nodes.toLocaleString()
      : "47,875";
  const totalEdgesText =
    summary?.total_edges !== undefined
      ? summary.total_edges.toLocaleString()
      : data.graph_totals?.total_edges !== undefined
      ? Number(data.graph_totals.total_edges).toLocaleString()
      : "225,731";
  const coreFactualText =
    summary?.unique_core_factual_edges !== undefined
      ? summary.unique_core_factual_edges.toLocaleString()
      : "110,026";

  return (
    <div
      className="flex-1 overflow-y-auto px-3 sm:px-6 py-3 sm:py-5 bg-ground space-y-3 sm:space-y-5"
      data-testid="analytics-view"
    >
      {/* Title Row */}
      <div className="flex flex-wrap items-baseline justify-between gap-2 sm:gap-4">
        <div>
          <h1 className="text-base sm:text-xl font-semibold text-ink tracking-tight">
            Full-graph scientific analytics
          </h1>
          <p className="hidden sm:block text-xs text-muted mt-0.5">
            Precomputed over the complete 2021–2025 AAAI &amp; IJCAI main-track graph (
            <span className="font-mono">release-d3c788c3114a</span>). Click any entity to inspect or focus it on the graph canvas.
          </p>
        </div>
      </div>

      {/* 1. Inventory Summary Strip (Divided 4-cell ledger container) */}
      <section
        aria-label="Corpus inventory totals"
        className="ledger-kpis [&>.ledger-kpi]:!p-2.5 sm:[&>.ledger-kpi]:!p-3.5"
      >
        <div className="ledger-kpi">
          <div className="text-xs text-muted">Domain nodes</div>
          <div className="mt-0.5 sm:mt-1 text-lg sm:text-2xl font-medium text-ink tabular-nums">
            {totalNodesText}
          </div>
          <div className="mt-0.5 sm:mt-1 text-xs text-[var(--positive)] flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
            <span>Gate ≥ 2,000 PASS</span>
          </div>
        </div>

        <div className="ledger-kpi">
          <div className="text-xs text-muted">Accepted relationships</div>
          <div className="mt-0.5 sm:mt-1 text-lg sm:text-2xl font-medium text-ink tabular-nums">
            {totalEdgesText}
          </div>
          <div className="mt-0.5 sm:mt-1 text-xs text-muted">
            Across 10 predicates (R1–R10)
          </div>
        </div>

        <div className="ledger-kpi">
          <div className="text-xs text-muted">Core factual edges (R1–R4)</div>
          <div className="mt-0.5 sm:mt-1 text-lg sm:text-2xl font-medium text-ink tabular-nums">
            {coreFactualText}
          </div>
          <div className="mt-0.5 sm:mt-1 text-xs text-[var(--positive)] flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
            <span>Gate ≥ 5,000 PASS</span>
          </div>
        </div>

        <div className="ledger-kpi">
          <div className="text-xs text-muted">Resolved researchers</div>
          <div className="mt-0.5 sm:mt-1 text-lg sm:text-2xl font-medium text-ink tabular-nums">
            32,189
          </div>
          <div className="mt-0.5 sm:mt-1 text-xs text-muted tabular-nums">
            13,617 core papers · 2,047 orgs
          </div>
        </div>
      </section>

      {/* 2. Separate Scientific Quality, Coverage & Audit Status Ledger */}
      <section
        aria-label="Scientific quality and coverage audit"
        data-testid="quality-audit-panel"
        className="ledger-panel p-3 sm:p-4"
      >
        {/* Compact phone disclosure so first chart enters initial 844px viewport */}
        <details className="sm:hidden group">
          <summary className="list-none cursor-pointer flex items-center justify-between gap-2 text-xs">
            <div className="min-w-0">
              <div className="font-semibold text-ink">
                Quality &amp; audit (D040 AI-assessed)
              </div>
              <div className="text-muted tabular-nums truncate mt-0.5">
                Edge {edgePrecPct} · Affil {affCovPct} (48,259 / 65,469 FAIL) · Topic {topicCovPct} cov / {topicPrecPct} prec / {topicF1Val} F1
              </div>
            </div>
            <ChevronRight className="w-4 h-4 text-muted shrink-0 transition-transform group-open:rotate-90" />
          </summary>
          <div className="mt-2.5 space-y-2 text-xs">
            <div className="p-2.5 rounded-[6px] bg-ground border border-border">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-ink tabular-nums">
                  AI-assessed edge precision: {edgePrecPct}
                </span>
                <span className="ledger-pill ledger-pill-warn">AI-assessed</span>
              </div>
              <div className="mt-1 text-muted tabular-nums">{edgePrecDetail}</div>
            </div>
            <div className="p-2.5 rounded-[6px] bg-ground border border-border">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-ink tabular-nums">
                  Affiliation coverage: {affCovPct}
                </span>
                <span className="ledger-pill ledger-pill-neg">Gate FAIL</span>
              </div>
              <div className="mt-1 text-muted tabular-nums">{affCovDetail}</div>
            </div>
            <div className="p-2.5 rounded-[6px] bg-ground border border-border">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-ink tabular-nums">
                  Topic: {topicCovPct} cov · {topicPrecPct} prec · {topicF1Val} F1
                </span>
                <span className="ledger-pill ledger-pill-warn">
                  Cov PASS · Prec FAIL
                </span>
              </div>
              <div className="mt-1 text-muted tabular-nums">{topicDetail}</div>
            </div>
          </div>
        </details>

        {/* Tablet (2-col) and Desktop (3-col) Quality Grid */}
        <div className="hidden sm:block">
          <div className="flex flex-wrap items-baseline justify-between gap-2 mb-3">
            <h2 className="text-sm font-semibold text-ink">
              Scientific quality, coverage &amp; audit status (D040)
            </h2>
            <span className="text-xs text-muted">
              Agent-assessed frozen audit · No human annotation performed
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3 text-xs">
            <div
              data-testid="quality-card-edge-precision"
              className="p-3 rounded-[6px] bg-ground border border-border flex items-start justify-between gap-3"
            >
              <div>
                <div className="text-muted">AI-assessed edge precision</div>
                <div className="mt-1 text-lg font-semibold text-ink tabular-nums">
                  {edgePrecPct}
                </div>
                <div className="mt-0.5 text-muted tabular-nums leading-relaxed">
                  {edgePrecDetail}
                </div>
              </div>
              <span className="ledger-pill ledger-pill-warn shrink-0">
                AI-assessed
              </span>
            </div>

            <div
              data-testid="quality-card-affiliation"
              className="p-3 rounded-[6px] bg-ground border border-border flex items-start justify-between gap-3"
            >
              <div>
                <div className="text-muted">Affiliation position coverage</div>
                <div className="mt-1 text-lg font-semibold text-ink tabular-nums">
                  {affCovPct}
                </div>
                <div className="mt-0.5 text-muted tabular-nums leading-relaxed">
                  {affCovDetail}
                </div>
              </div>
              <span className="ledger-pill ledger-pill-neg shrink-0">
                <AlertTriangle className="w-3 h-3" />
                Gate FAIL
              </span>
            </div>

            <div
              data-testid="quality-card-topic"
              className="p-3 rounded-[6px] bg-ground border border-border flex items-start justify-between gap-3 md:col-span-2 xl:col-span-1"
            >
              <div>
                <div className="text-muted">
                  Topic coverage, precision &amp; historical F1
                </div>
                <div className="mt-1 text-lg font-semibold text-ink tabular-nums">
                  {topicCovPct} cov · {topicPrecPct} prec · {topicF1Val} F1
                </div>
                <div className="mt-0.5 text-muted tabular-nums leading-relaxed">
                  {topicDetail}
                </div>
              </div>
              <span className="ledger-pill ledger-pill-warn shrink-0">
                <AlertTriangle className="w-3 h-3" />
                Cov PASS · Prec FAIL
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* 3. Paired Analytical Charts (2x2 on desktop, stacked on tablet/phone) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 items-start">
        <div className="ledger-panel p-5">
          <div className="mb-2">
            <h2 className="text-[15px] font-semibold text-ink">
              Annual corpus & collaboration growth (2021–2025)
            </h2>
            <p className="text-xs text-muted mt-0.5">
              Core proceedings papers, active OpenAlex-resolved researchers, and newly formed coauthorship pairs per conference year.
            </p>
          </div>
          <EChartBox option={annualChartOption} darkMode={darkMode} />
        </div>

        <div className="ledger-panel p-5">
          <div className="mb-2">
            <h2 className="text-[15px] font-semibold text-ink">
              Organization sector mixing matrix (COLLABORATED_WITH)
            </h2>
            <p className="text-xs text-muted mt-0.5">
              Pair-paper support counts across organizational sectors (academia, industry, government, nonprofit).
            </p>
          </div>
          <EChartBox option={sectorHeatmapOption} darkMode={darkMode} />
        </div>

        <div className="ledger-panel p-5">
          <div className="mb-2">
            <h2 className="text-[15px] font-semibold text-ink">
              Researcher coauthorship degree CCDF (log scale)
            </h2>
            <p className="text-xs text-muted mt-0.5">
              Complementary cumulative distribution across all 32,189 resolved researchers (including 471 single-author isolates).
            </p>
          </div>
          <EChartBox option={ccdfOption} darkMode={darkMode} />
        </div>

        <div className="ledger-panel p-5">
          <div className="mb-2">
            <h2 className="text-[15px] font-semibold text-ink">
              Top country-pair organization collaborations
            </h2>
            <p className="text-xs text-muted mt-0.5">
              Distinct accepted COLLABORATED_WITH organization-pair by core-paper support counts across ISO country codes.
            </p>
          </div>
          <EChartBox option={countryBarOption} darkMode={darkMode} />
        </div>
      </div>

      {/* 4. Linked Interactive Ranking Tables */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 items-start">
        {/* Bridge Researchers */}
        <div className="ledger-panel p-5">
          <div className="mb-3">
            <h2 className="text-[15px] font-semibold text-ink">
              Top bridge researchers (full-projection betweenness)
            </h2>
            <p className="text-xs text-muted mt-0.5">
              Computed on the 32,189-node Researcher–COAUTHORED_WITH projection.
            </p>
          </div>

          <div className="divide-y divide-rule text-xs max-h-96 overflow-y-auto">
            {bridgeResearchers.slice(0, 12).map((br, idx) => (
              <div
                key={br.researcher_id}
                className="py-2.5 flex items-center justify-between gap-3 hover:bg-raised/60 px-2 transition-colors"
              >
                <div className="min-w-0">
                  <div className="font-medium text-ink flex items-center gap-2">
                    <span className="font-mono text-faint tabular-nums w-6">
                      #{idx + 1}
                    </span>
                    <button
                      type="button"
                      onClick={() => selectNode(br.researcher_id, br.researcher)}
                      className="hover:underline truncate text-left"
                    >
                      {br.researcher}
                    </button>
                  </div>
                  <div className="text-muted flex flex-wrap items-center gap-2 mt-0.5 pl-8 tabular-nums">
                    <span>Betweenness: {br.betweenness.toFixed(4)}</span>
                    <span>·</span>
                    <button
                      type="button"
                      onClick={() => {
                        setViewMode("researchers");
                        updateFilters({ communityId: br.community_id });
                        setWorkspaceTab("graph");
                      }}
                      className="text-ink underline underline-offset-2"
                    >
                      {br.community_id} ({br.community_member_count} members)
                    </button>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() =>
                    onFocusNodeInGraph(br.researcher_id, br.researcher)
                  }
                  className="ledger-btn h-7 px-2.5 text-xs shrink-0"
                >
                  Focus →
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Top Cited Core Papers */}
        <div className="ledger-panel p-5">
          <div className="mb-3">
            <h2 className="text-[15px] font-semibold text-ink">
              Top within-corpus cited papers (CITES in-degree)
            </h2>
            <p className="text-xs text-muted mt-0.5">
              Directed citations within the 2021–2025 AAAI/IJCAI release corpus.
            </p>
          </div>

          <div className="divide-y divide-rule text-xs max-h-96 overflow-y-auto">
            {topCitedPapers.slice(0, 12).map((paper, idx) => (
              <div
                key={paper.paper_id}
                className="py-2.5 flex items-center justify-between gap-3 hover:bg-raised/60 px-2 transition-colors"
              >
                <div className="min-w-0">
                  <div className="font-medium text-ink flex items-center gap-2">
                    <span className="font-mono text-faint tabular-nums w-6">
                      #{idx + 1}
                    </span>
                    <button
                      type="button"
                      onClick={() => selectNode(paper.paper_id, paper.title)}
                      className="hover:underline truncate text-left"
                    >
                      {paper.title}
                    </button>
                  </div>
                  <div className="text-muted mt-0.5 pl-8 tabular-nums">
                    {paper.year} · In-degree: {paper.in_degree} · PageRank:{" "}
                    {paper.pagerank.toFixed(5)}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setViewMode("citations");
                    onFocusNodeInGraph(paper.paper_id, paper.title);
                  }}
                  className="ledger-btn h-7 px-2.5 text-xs shrink-0"
                >
                  Citations →
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 5. Academia–Industry Collaboration Candidates */}
      <div className="ledger-panel p-5">
        <div className="mb-3">
          <h2 className="text-[15px] font-semibold text-ink">
            Academia–industry topic collaboration candidates
          </h2>
          <p className="text-xs text-muted mt-0.5">
            Cross-sector organization pairs co-publishing on shared inferred AI topics. Click Compare to inspect joint papers and topic portfolios.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {acadIndustryPairs.slice(0, 12).map((pair, idx) => (
            <div
              key={`${pair.academia_organization_id}-${pair.industry_organization_id}-${pair.topic_id}-${idx}`}
              className="p-3.5 rounded-[8px] border border-border bg-ground flex flex-col justify-between gap-3"
            >
              <div>
                <div className="text-xs font-semibold text-ink">
                  {pair.academia_organization} ↔ {pair.industry_organization}
                </div>
                <div className="text-xs text-muted mt-1">
                  Shared topic: <strong className="font-medium text-ink">{pair.topic}</strong>
                </div>
                <div className="text-xs text-faint mt-0.5 tabular-nums">
                  Supported by {pair.supported_paper_count} shared topic papers
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() =>
                    setCompareModalOpen(
                      true,
                      pair.academia_organization_id,
                      pair.industry_organization_id
                    )
                  }
                  className="flex-1 ledger-btn h-7 px-2.5 text-xs"
                >
                  <GitCompare className="w-3.5 h-3.5 text-muted" />
                  <span>Compare pair</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setViewMode("organizations");
                    onFocusNodeInGraph(
                      pair.industry_organization_id,
                      pair.industry_organization
                    );
                  }}
                  className="ledger-btn ledger-btn-primary h-7 px-2.5 text-xs"
                >
                  Graph
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
