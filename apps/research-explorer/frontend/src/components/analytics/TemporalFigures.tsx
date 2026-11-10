import React, { useState } from "react";
import { EChartBox } from "./EChartBox";
import { RankedBars, useFigureTheme } from "./RankedFigures";
import { Table, pct } from "./DashboardPrimitives";
import {
  cohortCdf,
  type CitationCohort,
  type TopicRow,
  topicChanges,
} from "../../lib/analytics";
export interface PersistencePair {
  source_id: string;
  target_id: string;
  source: string;
  target: string;
  distinct_support_papers: number;
  active_year_count: number;
  by_year: { year: number; distinct_support_papers: number }[];
}
const shortVenue = (id: string) => id.split(":").at(-1)?.toUpperCase();
export const PersistenceFigures: React.FC<{
  pairs: PersistencePair[];
  onOpen: (pair: PersistencePair) => void;
}> = ({ pairs, onOpen }) => {
  const t = useFigureTheme();
  const years = [2021, 2022, 2023, 2024, 2025];
  const visible = pairs.slice(0, 12);
  return (
    <>
      <RankedBars
        label="Leading organization co-publication pairs"
        unit="distinct papers"
        rows={visible.map((p, i) => ({
          id: String(i),
          name: `${p.source} ↔ ${p.target}`,
          value: p.distinct_support_papers,
        }))}
        onOpen={(i) => onOpen(visible[i])}
      />
      <h4 className="text-sm font-medium mt-4">
        Supported activity by year · top 25 pairs
      </h4>
      {!pairs.length ? (
        <p className="text-sm text-muted py-4">
          Persistence artifact unavailable.
        </p>
      ) : (
        <EChartBox
          label="Organization pair-by-year persistence"
          height={Math.max(300, pairs.length * 28 + 100)}
          onClick={(p) => onOpen(pairs[Math.floor(p.dataIndex / years.length)])}
          option={{
            grid: {
              left: 12,
              right: 20,
              top: 20,
              bottom: 70,
              containLabel: true,
            },
            xAxis: {
              type: "category",
              data: years,
              axisLabel: { color: t.chartAxis },
            },
            yAxis: {
              type: "category",
              inverse: true,
              data: pairs.map((p) => `${p.source} ↔ ${p.target}`),
              axisLabel: {
                color: t.chartAxis,
                width: 170,
                overflow: "truncate",
                fontSize: 11,
              },
            },
            tooltip: {
              formatter: (p: { value: number[] }) => {
                const [x, y, n] = p.value;
                return `${years[x]} · Pair ${y + 1}<br/>${n == null ? "Unavailable" : n + " distinct supporting papers"}`;
              },
            },
            visualMap: {
              min: 0,
              max: Math.max(
                1,
                ...pairs.flatMap((p) =>
                  p.by_year.map((y) => y.distinct_support_papers),
                ),
              ),
              orient: "horizontal",
              left: "center",
              bottom: 0,
              inRange: { color: t.heatmapScale },
              textStyle: { color: t.chartAxis },
            },
            series: [
              {
                type: "heatmap",
                data: pairs.flatMap((p, y) =>
                  years.map((year, x) => [
                    x,
                    y,
                    p.by_year.find((v) => v.year === year)
                      ?.distinct_support_papers ?? null,
                  ]),
                ),
                label: {
                  show: true,
                  color: t.chartInkSeries,
                  formatter: (p: { value: number[] }) =>
                    p.value[2] == null ? "—" : String(p.value[2]),
                },
              },
            ],
          }}
        />
      )}
      <p className="text-xs text-muted mt-3">
        Counts describe observed support by year, not a continuous formal
        partnership. Missing years are unavailable, not inferred zero.
      </p>
    </>
  );
};
export const TopicChangeFigures: React.FC<{
  changes: ReturnType<typeof topicChanges>;
  topics: TopicRow[];
  topic: string;
  years: number[];
  onOpen: (row: TopicRow) => void;
}> = ({ changes, topics, topic, years, onOpen }) => {
  const t = useFigureTheme();
  const [comparison, setComparison] = useState("");
  const selected = topic || comparison || changes[0]?.first.topic_id || "";
  const names = [
    ...new Map(topics.map((r) => [r.topic_id, r.topic])).entries(),
  ];
  const decreasing = [...changes].reverse().find((r) => r.delta < 0),
    increasing = changes.find((r) => r.delta > 0);
  const persistent = [...changes].sort(
    (a, b) =>
      Math.min(
        b.first.share_of_fractional_topic_mass,
        b.last.share_of_fractional_topic_mass,
      ) -
      Math.min(
        a.first.share_of_fractional_topic_mass,
        a.last.share_of_fractional_topic_mass,
      ),
  )[0];
  return (
    <div className="analytics-grid mt-5">
      <div>
        <h3 className="text-base font-semibold">
          First-to-last selected year change
        </h3>
        <p className="text-xs text-muted mt-2">
          Percentage points in fractional prevalence; both selected endpoints
          must be observed.
        </p>
        <RankedBars
          label="Topic fractional prevalence change"
          unit="percentage points"
          signed
          rows={changes.map((c) => ({
            id: c.first.topic_id,
            name: c.first.topic,
            value: c.delta,
          }))}
          onOpen={(i) => onOpen(changes[i].last)}
        />
        <p className="text-sm mt-3">
          {increasing && (
            <>
              Largest increase: <strong>{increasing.first.topic}</strong> (+
              {increasing.delta.toFixed(2)} pp).{" "}
            </>
          )}
          {decreasing && (
            <>
              Largest decrease: <strong>{decreasing.first.topic}</strong> (
              {decreasing.delta.toFixed(2)} pp).{" "}
            </>
          )}
          {persistent && (
            <>
              Highest minimum endpoint share:{" "}
              <strong>{persistent.first.topic}</strong>.
            </>
          )}
        </p>
      </div>
      <div>
        <h3 className="text-base font-semibold">Compare venues</h3>
        <label className="text-xs block mt-3">
          Comparison topic
          <select
            aria-label="Venue comparison topic"
            className="ledger-input w-full mt-2"
            value={selected}
            onChange={(e) => setComparison(e.target.value)}
            disabled={!!topic}
          >
            {names.map(([id, name]) => (
              <option key={id} value={id}>
                {name}
              </option>
            ))}
          </select>
        </label>
        <EChartBox
          label="Selected topic comparison by venue"
          option={{
            grid: {
              left: 12,
              right: 24,
              top: 50,
              bottom: 45,
              containLabel: true,
            },
            tooltip: {
              trigger: "axis",
              valueFormatter: (v: number) => `${v.toFixed(2)}%`,
            },
            legend: { textStyle: { color: t.chartAxis } },
            xAxis: {
              type: "category",
              data: years,
              axisLabel: { color: t.chartAxis },
            },
            yAxis: {
              type: "value",
              name: "Fractional prevalence (%)",
              nameTextStyle: { align: "left" },
              axisLabel: { color: t.chartAxis },
              splitLine: { lineStyle: { color: t.chartGrid } },
            },
            series: ["venue:aaai", "venue:ijcai"].map((id, i) => ({
              name: shortVenue(id),
              type: "line",
              connectNulls: false,
              lineStyle: { width: 2 },
              itemStyle: {
                color: i ? t.chartSecondarySeries : t.chartPrimarySeries,
              },
              data: years.map((year) => {
                const r = topics.find(
                  (r) =>
                    r.topic_id === selected &&
                    r.venue_id === id &&
                    r.year === year,
                );
                return r ? 100 * r.share_of_fractional_topic_mass : null;
              }),
            })),
          }}
        />
        <Table
          label="Venue comparison values"
          headers={["Venue", "Year", "Topic / graph", "Fractional prevalence"]}
          rows={topics
            .filter((r) => r.topic_id === selected && years.includes(r.year))
            .map((r) => [
              shortVenue(r.venue_id),
              r.year,
              <button className="underline" onClick={() => onOpen(r)}>
                {r.topic}
              </button>,
              pct(r.share_of_fractional_topic_mass),
            ])}
        />
      </div>
    </div>
  );
};
export interface CohortLeader {
  paper_id: string;
  title: string;
  venue_id: string;
  year: number;
  in_degree: number;
  cohort_paper_denominator: number;
  empirical_percentile_including_ties: number;
}
export const CitationFigures: React.FC<{
  cohorts: CitationCohort[];
  leaders: CohortLeader[];
  onOpen: (p: CohortLeader) => void;
}> = ({ cohorts, leaders, onOpen }) => {
  const t = useFigureTheme();
  const [selected, setSelected] = useState("");
  const key = (c: { venue_id: string; year: number }) =>
    `${shortVenue(c.venue_id)} ${c.year}`;
  const cohort = cohorts.find((c) => key(c) === selected) || cohorts[0];
  const within = cohort
    ? leaders.filter(
        (p) => p.venue_id === cohort.venue_id && p.year === cohort.year,
      )
    : [];
  return (
    <>
      <RankedBars
        label="Uncited share by venue/year cohort"
        unit="% of cohort papers"
        rows={cohorts
          .filter((c) => c.paper_denominator > 0)
          .map((c) => ({
            id: key(c),
            name: key(c),
            value: (100 * c.zero_in_degree_count) / c.paper_denominator,
          }))}
      />
      <label className="text-xs block mt-4">
        Citation distribution cohort
        <select
          aria-label="Citation distribution cohort"
          className="ledger-input ml-2 max-w-full"
          value={cohort ? key(cohort) : ""}
          onChange={(e) => setSelected(e.target.value)}
        >
          {cohorts.map((c) => (
            <option key={key(c)}>{key(c)}</option>
          ))}
        </select>
      </label>
      {cohort && (
        <EChartBox
          label="Within-cohort incoming citation distribution"
          option={{
            grid: {
              top: 45,
              left: 12,
              right: 24,
              bottom: 50,
              containLabel: true,
            },
            tooltip: {
              trigger: "axis",
              valueFormatter: (v: number) => `${v.toFixed(2)}% of cohort`,
            },
            xAxis: {
              type: "value",
              name: "Incoming in-corpus citations",
              nameLocation: "middle",
              nameGap: 32,
              axisLabel: { color: t.chartAxis },
            },
            yAxis: {
              type: "value",
              max: 100,
              name: "Cumulative papers (%)",
              nameTextStyle: { align: "left" },
              axisLabel: { color: t.chartAxis },
              splitLine: { lineStyle: { color: t.chartGrid } },
            },
            series: [
              {
                type: "line",
                step: "end",
                showSymbol: false,
                data: cohortCdf(cohort),
                itemStyle: { color: t.chartPrimarySeries },
              },
            ],
          }}
        />
      )}
      <h4 className="text-sm font-medium mt-4">
        Within-cohort citation leaders {cohort ? `· ${key(cohort)}` : ""}
      </h4>
      <RankedBars
        label="Within-cohort paper citation ranking"
        unit="incoming citations"
        rows={within.map((p) => ({
          id: p.paper_id,
          name: p.title,
          value: p.in_degree,
        }))}
        onOpen={(i) => onOpen(within[i])}
      />
      <Table
        label="Selected cohort leaders and evidence"
        headers={[
          "Paper / evidence",
          "Incoming citations",
          "Cohort N",
          "Empirical percentile",
        ]}
        rows={within.map((p) => [
          <button className="underline text-left" onClick={() => onOpen(p)}>
            {p.title}
          </button>,
          p.in_degree,
          p.cohort_paper_denominator,
          pct(p.empirical_percentile_including_ties),
        ])}
      />
    </>
  );
};
