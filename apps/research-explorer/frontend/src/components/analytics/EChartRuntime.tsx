import React, { useEffect, useRef, useState } from "react";
import * as echarts from "echarts/core";
import { BarChart, LineChart, HeatmapChart, ScatterChart } from "echarts/charts";
import {
  GridComponent,
  TooltipComponent,
  VisualMapContinuousComponent,
  LegendPlainComponent,
  AriaComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import type { EChartsCoreOption } from "echarts/core";
echarts.use([
  BarChart,
  LineChart,
  HeatmapChart,
  ScatterChart,
  GridComponent,
  TooltipComponent,
  VisualMapContinuousComponent,
  LegendPlainComponent,
  AriaComponent,
  CanvasRenderer,
]);

export interface ChartClick {
  dataIndex: number;
  seriesIndex: number;
  value: unknown;
  data?: unknown;
}
export interface EChartBoxProps {
  option: EChartsCoreOption;
  label: string;
  onClick?: (data: ChartClick) => void;
  height?: number;
}

function countChartPoints(opt: EChartsCoreOption): { seriesCount: number; pointCount: number } {
  const raw = (opt as { series?: unknown }).series;
  const arr = Array.isArray(raw) ? raw : raw ? [raw] : [];
  let pointCount = 0;
  for (const s of arr) {
    if (s && typeof s === "object" && Array.isArray((s as { data?: unknown[] }).data)) {
      pointCount += (s as { data: unknown[] }).data.length;
    }
  }
  return { seriesCount: arr.length, pointCount };
}

export const EChartRuntime: React.FC<EChartBoxProps> = ({
  option,
  label,
  onClick,
  height = 300,
}) => {
  const el = useRef<HTMLDivElement>(null);
  const chart = useRef<echarts.ECharts | null>(null);
  const click = useRef(onClick);
  const latest = useRef(option);
  const entered = useRef(false);
  const [active, setActive] = useState(false);
  click.current = onClick;
  latest.current = option;

  useEffect(() => {
    const node = el.current;
    if (!node) return;
    const rect = node.getBoundingClientRect();
    const vh = window.innerHeight || 900;
    if (rect.top <= vh + 200 && rect.bottom >= -200) {
      setActive(true);
    }
    const observer = new IntersectionObserver(
      ([entry]) => setActive(entry.isIntersecting),
      { rootMargin: "200px" },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const node = el.current;
    if (!node || !active) return;
    const instance = echarts.init(node);
    chart.current = instance;
    if (import.meta.env.DEV)
      (node as HTMLDivElement & { __chart?: echarts.ECharts }).__chart =
        instance;
    node.dataset.chartGeneration = String(
      Number(node.dataset.chartGeneration || 0) + 1,
    );
    node.dataset.chartActive = "true";
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const markStats = (opt: EChartsCoreOption) => {
      const { seriesCount, pointCount } = countChartPoints(opt);
      node.dataset.chartSeriesCount = String(seriesCount);
      node.dataset.chartPointCount = String(pointCount);
      node.dataset.chartRendered = "false";
    };
    instance.on("finished", () => {
      node.dataset.chartRendered = "true";
    });
    const apply = (initial: boolean) => {
      markStats(latest.current);
      node.dataset.animation = media.matches ? "reduced" : "enabled";
      node.dataset.entranceDuration = String(
        !media.matches && initial && !entered.current ? 600 : 0,
      );
      instance.setOption({
        backgroundColor: "transparent",
        textStyle: { fontFamily: "Geist, system-ui, sans-serif" },
        aria: { enabled: true },
        ...latest.current,
        animation: !media.matches,
        animationDuration: initial && !entered.current ? 600 : 0,
        animationDurationUpdate: media.matches ? 0 : 300,
        animationEasing: "cubicOut",
        animationEasingUpdate: "cubicOut",
      });
    };
    apply(true);
    entered.current = true;
    instance.on("click", (p) => click.current?.(p as unknown as ChartClick));
    let frame = 0;
    const ro = new ResizeObserver(() => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => instance.resize());
    });
    ro.observe(node);
    const onMotion = () => apply(false);
    media.addEventListener("change", onMotion);
    return () => {
      cancelAnimationFrame(frame);
      ro.disconnect();
      media.removeEventListener("change", onMotion);
      instance.dispose();
      if (import.meta.env.DEV)
        delete (node as HTMLDivElement & { __chart?: echarts.ECharts }).__chart;
      chart.current = null;
      node.dataset.chartActive = "false";
      node.dataset.chartRendered = "false";
    };
  }, [active]);

  useEffect(() => {
    const node = el.current;
    if (!chart.current || !node) return;
    const { seriesCount, pointCount } = countChartPoints(option);
    node.dataset.chartSeriesCount = String(seriesCount);
    node.dataset.chartPointCount = String(pointCount);
    node.dataset.chartRendered = "false";
    chart.current.setOption(option, {
      replaceMerge: ["series", "xAxis", "yAxis", "visualMap"],
      lazyUpdate: true,
    });
  }, [option]);

  return (
    <div
      role="img"
      aria-label={`${label}. Exact values and keyboard actions in the data table below.`}
      className="analytics-chart"
      data-chart-label={label}
      ref={el}
      style={{ width: "100%", height }}
    />
  );
};
