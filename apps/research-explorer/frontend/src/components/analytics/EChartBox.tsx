import React, { Suspense, useEffect, useRef, useState } from "react";
import type { EChartBoxProps } from "./EChartRuntime";
export type { ChartClick } from "./EChartRuntime";
const Runtime = React.lazy(() =>
  import("./EChartRuntime").then((m) => ({ default: m.EChartRuntime })),
);
/** Load the chart engine when a real chart is in or near the viewport. */
export const EChartBox: React.FC<EChartBoxProps> = (props) => {
  const ref = useRef<HTMLDivElement>(null);
  const [ready, setReady] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const vh = window.innerHeight || 900;
    if (rect.top <= vh + 300 && rect.bottom >= -300) {
      setReady(true);
      return;
    }
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setReady(true);
          observer.disconnect();
        }
      },
      { rootMargin: "300px" },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);
  return (
    <div ref={ref} style={{ minHeight: props.height || 300 }}>
      {ready && (
        <Suspense
          fallback={
            <p role="status" className="text-xs text-muted p-4">
              Loading {props.label.toLowerCase()}…
            </p>
          }
        >
          <Runtime {...props} />
        </Suspense>
      )}
    </div>
  );
};
