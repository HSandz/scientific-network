import React from "react";
import { EChartBox } from "./EChartBox";
import { Table, pct, fmt } from "./DashboardPrimitives";
import { useExplorerStore } from "../../stores/useExplorerStore";
import { getThemeTokens } from "../../lib/colors";
import { bridgeRanks } from "../../lib/analytics";

export function useFigureTheme() {
  return getThemeTokens(useExplorerStore((s) => s.darkMode));
}
export interface BarRow {
  id: string;
  name: string;
  value: number;
}
export const RankedBars: React.FC<{
  label: string;
  rows: BarRow[];
  unit: string;
  onOpen?: (index: number) => void;
  signed?: boolean;
  selectedIndex?: number;
}> = ({ label, rows, unit, onOpen, signed, selectedIndex }) => {
  const t = useFigureTheme();
  if (!rows.length)
    return (
      <p className="text-sm text-muted py-4" role="status">
        No measured values available for {label.toLowerCase()}.
      </p>
    );
  return (
    <EChartBox
      label={label}
      height={Math.max(240, rows.length * 30 + 95)}
      onClick={onOpen ? (p) => onOpen(p.dataIndex) : undefined}
      option={{
        media: [
          {
            query: { maxWidth: 400 },
            option: { yAxis: { axisLabel: { width: 110 } } },
          },
        ],
        grid: { left: 12, right: 55, top: 24, bottom: 40, containLabel: true },
        tooltip: {
          trigger: "axis",
          axisPointer: { type: "shadow" },
          valueFormatter: (v: number) =>
            `${v.toLocaleString(undefined, { maximumFractionDigits: 2 })} ${unit}`,
        },
        xAxis: {
          type: "value",
          name: unit,
          nameLocation: "middle",
          nameGap: 28,
          axisLabel: { color: t.chartAxis },
          splitLine: { lineStyle: { color: t.chartGrid } },
        },
        yAxis: {
          type: "category",
          inverse: true,
          data: rows.map((r) => r.name),
          axisLabel: {
            color: t.chartAxis,
            width: 145,
            overflow: "truncate",
            fontSize: 12,
          },
        },
        series: [
          {
            type: "bar",
            barMaxWidth: 18,
            data: rows.map((r, i) => ({
              value: r.value,
              itemStyle: {
                opacity:
                  selectedIndex == null || selectedIndex === i ? 1 : 0.45,
                color:
                  signed && r.value < 0
                    ? t.chartSecondarySeries
                    : t.chartPrimarySeries,
              },
            })),
            label: {
              show: true,
              position: "right",
              color: t.chartAxis,
              formatter: (p: { value: number }) =>
                p.value.toLocaleString(undefined, { maximumFractionDigits: 2 }),
            },
          },
        ],
      }}
    />
  );
};
export const BridgeMatrix: React.FC<{
  ranks: ReturnType<typeof bridgeRanks>;
  names: Map<string, string>;
  onOpen: (id: string, name?: string) => void;
}> = ({ ranks, names, onOpen }) => (
  <>
    <div
      className="bridge-matrix mt-4"
      role="group"
      aria-label="Leading bridge rank comparison"
    >
      <div className="bridge-matrix-head text-xs text-muted">
        <span>Researcher</span>
        <span>Base rank</span>
        <span>Strict rank</span>
      </div>
      {ranks
        .filter(
          (r) =>
            (r.base != null && r.base <= 3) ||
            (r.strict != null && r.strict <= 3),
        )
        .map((r) => (
          <div key={r.id} className="bridge-matrix-row text-xs">
            <button
              className="underline truncate text-left"
              title={names.get(r.id) || r.id}
              onClick={() => onOpen(r.id, names.get(r.id))}
            >
              {names.get(r.id) || r.id.split(":").at(-1)}
            </button>
            {[r.base, r.strict].map((rank, i) => (
              <span
                key={i}
                className="rank-cell num"
                style={
                  rank == null
                    ? undefined
                    : {
                        background: `color-mix(in srgb, var(--accent) ${Math.round(12 + (21 - rank) * 1.8)}%, var(--surface))`,
                      }
                }
              >
                {rank == null ? "Outside 20" : `#${rank}`}
              </span>
            ))}
          </div>
        ))}
    </div>
    <p className="text-xs text-muted mt-3">
      Top three in each stored list shown here; expand the comparison table for
      all researchers. Shading encodes rank 1–20 within each list. An absent
      rank means outside the stored shortlist; no rank or score is imputed.
    </p>
  </>
);
export const RobustnessCounts: React.FC<{
  base: {
    node_count: number;
    edge_count: number;
    isolate_count: number;
    component_sizes: number[];
  };
  strict: {
    node_count: number;
    edge_count: number;
    isolate_count: number;
    weak_or_undirected_component_sizes: number[];
  };
}> = ({ base, strict }) => (
  <div className="grid gap-3 mt-4">
    {[
      ["Accepted edges", base.edge_count, strict.edge_count],
      ["Isolates", base.isolate_count, strict.isolate_count],
      [
        "Components",
        base.component_sizes?.length,
        strict.weak_or_undirected_component_sizes?.length,
      ],
    ].map(([title, a, b]) => (
      <div key={String(title)}>
        <p className="text-xs font-medium">{title}</p>
        <div className="grid grid-cols-2 gap-3">
          {[
            ["Base", a],
            ["Strict", b],
          ].map(([name, v]) => (
            <div key={String(name)} className="mt-2 text-xs">
              <div className="flex justify-between">
                <span>{name}</span>
                <span className="num">{fmt(v)}</span>
              </div>
              <div className="quality-track">
                <span
                  className="quality-fill"
                  style={{
                    width: `${(Number(v) / Math.max(Number(a), Number(b), 1)) * 100}%`,
                    opacity: name === "Base" ? 1 : 0.5,
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    ))}
    <p className="text-xs text-muted">
      Separate count scales per metric. Both networks retain{" "}
      {fmt(base.node_count)} researchers, including isolates.
    </p>
  </div>
);
