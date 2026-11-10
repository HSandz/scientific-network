import React, { useEffect, useRef } from "react";
import * as echarts from "echarts/core";
import { BarChart, LineChart, HeatmapChart } from "echarts/charts";
import {
  GridComponent,
  TooltipComponent,
  VisualMapComponent,
  LegendComponent,
  AriaComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
echarts.use([
  BarChart,
  LineChart,
  HeatmapChart,
  GridComponent,
  TooltipComponent,
  VisualMapComponent,
  LegendComponent,
  AriaComponent,
  CanvasRenderer,
]);
export const EChartBox: React.FC<{
  option: any;
  label: string;
  onClick?: (data: any) => void;
  height?: number;
}> = ({ option, label, onClick, height = 300 }) => {
  const el = useRef<HTMLDivElement>(null),
    chart = useRef<echarts.ECharts | null>(null),
    click = useRef(onClick);
  click.current = onClick;
  useEffect(() => {
    if (!el.current) return;
    const instance = echarts.init(el.current);
    chart.current = instance;
    instance.on("click", (p: any) => click.current?.(p));
    const ro = new ResizeObserver(() => instance.resize());
    ro.observe(el.current);
    return () => {
      ro.disconnect();
      instance.dispose();
      chart.current = null;
    };
  }, []);
  useEffect(() => {
    const reduced = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    chart.current?.setOption(
      {
        backgroundColor: "transparent",
        textStyle: { fontFamily: "Geist, system-ui, sans-serif" },
        aria: { enabled: true },
        ...option,
        animation: !reduced,
        animationDuration: 250,
        animationDurationUpdate: 150,
      },
      { notMerge: true, lazyUpdate: true },
    );
  }, [option]);
  return (
    <div
      role="img"
      aria-label={`${label}. Exact values and keyboard actions in the data table below.`}
      ref={el}
      style={{ width: "100%", height }}
    />
  );
};
