import React, { useLayoutEffect, useMemo, useRef, useState } from "react";

export interface ClusterItem {
  id: string;
  label: string;
  title: string;
  size: number;
  /** Display momentum in [-1, 1]. */
  t: number;
  change: string;
}

const LABEL_W = 138;
const LINE = 16;

function wrap(text: string, chars = 19, max = 3): string[] {
  const out: string[] = [];
  let line = "";
  for (const w of text.split(/\s+/)) {
    if (line && `${line} ${w}`.length > chars) {
      out.push(line);
      line = w;
    } else line = line ? `${line} ${w}` : w;
  }
  if (line) out.push(line);
  if (out.length > max) return [...out.slice(0, max - 1), `${out[max - 1].slice(0, chars - 1)}…`];
  return out;
}

interface Placed extends ClusterItem {
  x: number;
  y: number;
  r: number;
  lines: string[];
  w: number;
  h: number;
}

/**
 * Deterministic labelled bubble layout. Largest first; each takes the free spot closest to its
 * wanted position, so labels never overlap. With `positioned`, horizontal position follows t.
 */
function layout(items: ClusterItem[], width: number, positioned: boolean): { nodes: Placed[]; height: number } {
  const maxSize = Math.max(1, ...items.map((i) => i.size));
  const rMax = width < 620 ? 36 : 54;
  const ts = items.map((i) => i.t);
  const lo = Math.min(-0.25, ...ts);
  const hi = Math.max(0.25, ...ts);
  const nodes: Placed[] = [];
  for (const it of items) {
    const r = 10 + (rMax - 10) * Math.sqrt(it.size / maxSize);
    const lines = wrap(it.label);
    const w = Math.max(2 * r, LABEL_W) + 6;
    const h = 2 * r + lines.length * LINE + 14;
    const minX = w / 2;
    const maxX = Math.max(minX, width - w / 2);
    const wantX = positioned ? minX + ((it.t - lo) / (hi - lo)) * (maxX - minX) : width / 2;
    let best: { x: number; y: number; cost: number } | null = null;
    for (let dy = 0; dy <= 2400 && (!best || dy < best.cost); dy += 12) {
      for (const sy of dy ? [-1, 1] : [1]) {
        for (let dx = 0; dx <= width; dx += 14) {
          for (const sx of dx ? [-1, 1] : [1]) {
            const x = Math.max(minX, Math.min(maxX, wantX + sx * dx));
            const y = sy * dy;
            // Moving sideways costs more when horizontal position carries meaning.
            const cost = dy + dx * (positioned ? 2.2 : 0.6);
            if (best && cost >= best.cost) continue;
            const clash = nodes.some((n) => Math.abs(n.x - x) < (n.w + w) / 2 && y - h / 2 < n.y + n.h / 2 && y + h / 2 > n.y - n.h / 2);
            if (!clash) best = { x, y, cost };
          }
        }
      }
    }
    nodes.push({ ...it, x: best?.x ?? wantX, y: best?.y ?? 0, r, lines, w, h });
  }
  const top = Math.min(...nodes.map((n) => n.y - n.h / 2));
  const bottom = Math.max(...nodes.map((n) => n.y + n.h / 2));
  nodes.forEach((n) => (n.y -= top - 6));
  return { nodes, height: bottom - top + 12 };
}

export const ClusterMap: React.FC<{
  items: ClusterItem[];
  positioned: boolean;
  selected: string | null;
  unit: string;
  colorOf: (t: number) => string;
  onSelect: (id: string) => void;
}> = ({ items, positioned, selected, unit, colorOf, onSelect }) => {
  const ref = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(900);
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    const read = () => el.clientWidth && setWidth(Math.max(300, el.clientWidth));
    read();
    const ro = new ResizeObserver(read);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  const { nodes, height } = useMemo(() => layout(items, width, positioned), [items, width, positioned]);

  return (
    <div ref={ref} className="cluster-map" data-chart-label="Cluster map" data-chart-rendered="true" data-chart-point-count={nodes.length}>
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} role="group" aria-label={`Map of ${nodes.length} clusters`}>
        {nodes.map((n) => {
          const on = n.id === selected;
          const cy = n.y - n.h / 2 + n.r + 4;
          return (
            <g
              key={n.id}
              role="button"
              tabIndex={0}
              aria-pressed={on}
              aria-label={`${n.title}, ${n.size.toLocaleString("en")} ${unit}${n.change ? `, ${n.change}` : ""}`}
              data-testid={`supernode-${n.id}`}
              className="cluster"
              onClick={() => onSelect(n.id)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  onSelect(n.id);
                }
              }}
            >
              <title>{`${n.title}\n${n.size.toLocaleString("en")} ${unit}${n.change ? `, ${n.change}` : ""}`}</title>
              <circle cx={n.x} cy={cy} r={n.r} fill={colorOf(n.t)} fillOpacity={on ? 1 : 0.86} stroke={on ? "var(--ink)" : "var(--surface)"} strokeWidth={on ? 3 : 1.5} />
              <text x={n.x} y={cy + n.r + 16} textAnchor="middle">
                {n.lines.map((l, i) => (
                  <tspan key={i} x={n.x} dy={i ? LINE : 0}>
                    {l}
                  </tspan>
                ))}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
};
