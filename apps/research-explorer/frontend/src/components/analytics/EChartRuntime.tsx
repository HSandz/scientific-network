import React, { useEffect, useRef, useState } from "react";
import * as echarts from "echarts/core";
import { BarChart, LineChart, HeatmapChart } from "echarts/charts";
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
}
export interface EChartBoxProps {
  option: EChartsCoreOption;
  label: string;
  onClick?: (data: ChartClick) => void;
  height?: number;
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
    const observer = new IntersectionObserver(
      ([entry]) => setActive(entry.isIntersecting),
      { rootMargin: "200px" },
    );
    if (el.current) observer.observe(el.current);
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
    const apply = (initial: boolean) => {
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
    };
  }, [active]);
  useEffect(() => {
    chart.current?.setOption(option, {
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
