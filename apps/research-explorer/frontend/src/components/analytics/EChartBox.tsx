import React, { Suspense, useEffect, useRef, useState } from "react";
import type { EChartBoxProps } from "./EChartRuntime";
export type { ChartClick } from "./EChartRuntime";
const Runtime = React.lazy(() =>
  import("./EChartRuntime").then((m) => ({ default: m.EChartRuntime })),
);
/** Load the chart engine only when a real chart approaches the viewport. */
export const EChartBox: React.FC<EChartBoxProps> = (props) => {
  const ref = useRef<HTMLDivElement>(null);
  const [ready, setReady] = useState(false);
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setReady(true);
          observer.disconnect();
        }
      },
      { rootMargin: "300px" },
    );
    if (ref.current) observer.observe(ref.current);
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
