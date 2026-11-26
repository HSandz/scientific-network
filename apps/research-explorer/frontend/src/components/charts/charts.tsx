import React, { useMemo, useState } from "react";
import { cellColor, cssVar, fmtPct, readPalette, thermal, withAlpha } from "../../lib/thermal";
import { EntityDot } from "../ui/primitives";

/**
 * Small chart kit drawn with SVG and HTML, so labels stay sharp, wrap where needed and keep
 * at least 12 px on phones. Every chart carries data-chart-* attributes that tests read to
 * check that data was drawn.
 */

export interface LineSeries {
  name: string;
  values: number[];
  /** Momentum strength in [-1, 1] for the thermal colour; omit for graphite. */
  t?: number;
  emphasis?: boolean;
}

function niceStep(raw: number): number {
  if (raw <= 0) return 1;
  const p = 10 ** Math.floor(Math.log10(raw));
  const m = raw / p;
  return (m <= 1 ? 1 : m <= 2 ? 2 : m <= 2.5 ? 2.5 : m <= 5 ? 5 : 10) * p;
}
/** Clean axis: a nice step and a maximum that is a whole number of steps. */
function axis(maxVal: number, n = 4): { max: number; ticks: number[] } {
  const step = niceStep(Math.max(maxVal, 1e-9) / n);
  const max = Math.ceil(maxVal / step - 1e-9) * step || step;
  const ticks: number[] = [];
  for (let v = 0; v <= max + step / 2; v += step) ticks.push(+v.toFixed(6));
  return { max, ticks };
}
function tickLabel(v: number, unit: "pct" | "count"): string {
  const s = Number.isInteger(v) ? String(v) : v.toFixed(v < 1 ? (v * 10 === Math.round(v * 10) ? 1 : 2) : 1);
  return unit === "pct" ? `${s}%` : Number(s).toLocaleString("en");
}

/** Monotone cubic path (Fritsch–Carlson), so a smooth line never overshoots a data point. */
function monotonePath(pts: Array<[number, number]>): string {
  if (pts.length < 2) return pts.length ? `M${pts[0][0]},${pts[0][1]}` : "";
  const n = pts.length;
  const dx: number[] = [], dy: number[] = [], m: number[] = [];
  for (let i = 0; i < n - 1; i++) {
    dx.push(pts[i + 1][0] - pts[i][0]);
    dy.push(pts[i + 1][1] - pts[i][1]);
    m.push(dy[i] / dx[i]);
  }
  const t: number[] = [m[0]];
  for (let i = 1; i < n - 1; i++) t.push(m[i - 1] * m[i] <= 0 ? 0 : (3 * (dx[i - 1] + dx[i])) / ((2 * dx[i] + dx[i - 1]) / m[i - 1] + (dx[i] + 2 * dx[i - 1]) / m[i]));
  t.push(m[n - 2]);
  let d = `M${pts[0][0]},${pts[0][1]}`;
  for (let i = 0; i < n - 1; i++) {
    const h = dx[i] / 3;
    d += ` C${pts[i][0] + h},${pts[i][1] + h * t[i]} ${pts[i + 1][0] - h},${pts[i + 1][1] - h * t[i + 1]} ${pts[i + 1][0]},${pts[i + 1][1]}`;
  }
  return d;
}

/** De-collide end labels vertically within [top, bottom] with a minimum gap. */
function spread<T extends { y: number }>(items: T[], gap: number, top: number, bottom: number): T[] {
  const s = [...items].sort((a, b) => a.y - b.y);
  for (let i = 1; i < s.length; i++) if (s[i].y - s[i - 1].y < gap) s[i].y = s[i - 1].y + gap;
  const over = s.length ? s[s.length - 1].y - bottom : 0;
  if (over > 0) s.forEach((x) => (x.y -= over));
  for (let i = s.length - 2; i >= 0; i--) if (s[i + 1].y - s[i].y < gap) s[i].y = s[i + 1].y - gap;
  if (s.length && s[0].y < top) {
    const d = top - s[0].y;
    s.forEach((x) => (x.y += d));
  }
  return s;
}

export const LineChart: React.FC<{
  label: string;
  years: string[];
  series: LineSeries[];
  unit: "pct" | "count";
  /** Single-series hero chart: area fill and value labels on every point. */
  hero?: boolean;
  height?: number;
  endLabels?: boolean;
}> = ({ label, years, series, unit, hero = false, height, endLabels = true }) => {
  const [hover, setHover] = useState<number | null>(null);
  const p = readPalette();
  const ink = cssVar("--ink"), muted = cssVar("--muted"), rule = cssVar("--rule"), paper = cssVar("--paper");
  const W = hero ? 1000 : 680;
  const H = height || (hero ? 330 : 400);
  const labelW = endLabels && !hero && series.length > 1 ? 250 : hero ? 70 : 40;
  const m = { t: hero ? 34 : 18, r: labelW, b: 36, l: hero ? 52 : 52 };
  const { max, ticks } = axis(Math.max(0.0001, ...series.flatMap((s) => s.values)) * 1.04, 4);
  const x = (i: number) => m.l + (years.length > 1 ? (i * (W - m.l - m.r)) / (years.length - 1) : (W - m.l - m.r) / 2);
  const y = (v: number) => H - m.b - (v / max) * (H - m.t - m.b);
  const fmt = (v: number, d = 1) => (unit === "pct" ? fmtPct(v, d) : Math.round(v).toLocaleString("en"));
  const colorOf = (s: LineSeries) => (s.t == null ? ink : thermal(s.t, p));
  const ends = spread(
    series.map((s, i) => ({ i, y: y(s.values[s.values.length - 1] || 0) + 4, s })),
    17,
    m.t,
    H - m.b,
  );
  const points = series.reduce((a, s) => a + s.values.length, 0);
  return (
    <figure
      className="chart"
      data-chart-label={label}
      data-chart-rendered="true"
      data-chart-active="true"
      data-chart-series-count={series.length}
      data-chart-point-count={points}
    >
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`${label}: ${series.map((s) => `${s.name} ${years.map((yr, i) => `${yr} ${fmt(s.values[i], 2)}`).join(", ")}`).join("; ")}`} className="chart-svg" style={{ minWidth: hero ? 520 : 560 }}>
        {ticks.map((t) => (
          <g key={t}>
            <line x1={m.l} x2={W - m.r} y1={y(t)} y2={y(t)} stroke={rule} strokeDasharray={t === 0 ? undefined : "2 4"} />
            <text x={m.l - 10} y={y(t) + 4} textAnchor="end" fill={muted} fontSize={hero ? 15 : 14}>
              {tickLabel(t, unit)}
            </text>
          </g>
        ))}
        {years.map((yr, i) => (
          <text key={yr} x={x(i)} y={H - 10} textAnchor="middle" fill={muted} fontSize={hero ? 15 : 14}>
            {yr}
          </text>
        ))}
        {hero &&
          series.map((s, k) => (
            <path key={`a${k}`} d={`${monotonePath(s.values.map((v, i) => [x(i), y(v)]))} L${x(s.values.length - 1)},${y(0)} L${x(0)},${y(0)} Z`} fill={withAlpha(colorOf(s), 0.13)} />
          ))}
        {series.map((s, k) => (
          <path
            key={k}
            d={monotonePath(s.values.map((v, i) => [x(i), y(v)]))}
            fill="none"
            stroke={colorOf(s)}
            strokeWidth={hero ? 3.5 : s.emphasis || k === 0 ? 3 : 2}
            strokeOpacity={hover == null || hover === k ? 1 : 0.25}
            strokeLinecap="round"
          />
        ))}
        {(hero || series.length === 1) &&
          series.map((s, k) =>
            s.values.map((v, i) => (
              <g key={`${k}-${i}`}>
                <circle cx={x(i)} cy={y(v)} r={5} fill={paper} stroke={colorOf(s)} strokeWidth={2.5} />
                <text x={x(i)} y={y(v) - 14} textAnchor="middle" fontSize={hero ? 15 : 14} fontWeight={i === s.values.length - 1 ? 700 : 400} fill={i === s.values.length - 1 ? ink : muted}>
                  {fmt(v)}
                </text>
              </g>
            )),
          )}
        {endLabels &&
          !hero &&
          series.length > 1 &&
          ends.map(({ i, y: ly, s }) => (
            <text
              key={i}
              x={W - m.r + 10}
              y={ly}
              fontSize={14}
              fill={ink}
              fontWeight={s.emphasis || i === 0 ? 700 : 400}
              onMouseEnter={() => setHover(i)}
              onMouseLeave={() => setHover(null)}
              style={{ cursor: "default" }}
            >
              {s.name.length > 30 ? `${s.name.slice(0, 29)}…` : s.name} {fmt(s.values[s.values.length - 1], 1)}
            </text>
          ))}
      </svg>
    </figure>
  );
};

export interface BarItem {
  name: string;
  value: number;
  note?: string;
  kind?: string;
  href?: string;
  onClick?: () => void;
}

export const BarList: React.FC<{
  label: string;
  items: BarItem[];
  format: (v: number) => string;
  title?: React.ReactNode;
  max?: number;
}> = ({ label, items, format, title, max }) => {
  const top = max ?? Math.max(0.000001, ...items.map((i) => i.value));
  return (
    <figure className="barlist" data-chart-label={label} data-chart-rendered="true" data-chart-active="true" data-chart-series-count={1} data-chart-point-count={items.length}>
      {title && <figcaption className="barlist-title">{title}</figcaption>}
      <ol aria-label={label}>
        {items.map((it, i) => {
          const body = (
            <>
              <span className="barlist-name">
                {it.kind && <EntityDot kind={it.kind} />}
                <span>{it.name}</span>
                {it.note && <small>{it.note}</small>}
              </span>
              <span className="barlist-track" aria-hidden="true">
                <span className="barlist-bar" style={{ width: `${Math.max(1.5, (it.value / top) * 100)}%` }} />
              </span>
              <span className="barlist-value">{format(it.value)}</span>
            </>
          );
          return (
            <li key={`${it.name}-${i}`}>
              {it.onClick ? (
                <button type="button" className="barlist-row is-link" onClick={it.onClick}>
                  {body}
                </button>
              ) : (
                <div className="barlist-row">{body}</div>
              )}
            </li>
          );
        })}
      </ol>
    </figure>
  );
};

export const Dumbbell: React.FC<{ label: string; before: string; after: string; items: Array<{ name: string; from: number; to: number }> }> = ({ label, before, after, items }) => {
  const max = Math.max(0.000001, ...items.flatMap((i) => [i.from, i.to]));
  const p = readPalette();
  return (
    <figure className="dumbbell" data-chart-label={label} data-chart-rendered="true" data-chart-active="true" data-chart-series-count={2} data-chart-point-count={items.length * 2}>
      <div className="dumbbell-legend">
        <span>
          <i style={{ background: p.neutral }} /> {before}
        </span>
        <span>
          <i style={{ background: p.heat }} /> {after}
        </span>
      </div>
      <ol>
        {items.map((it) => {
          const a = (it.from / max) * 100;
          const b = (it.to / max) * 100;
          const up = it.to >= it.from;
          return (
            <li key={it.name}>
              <span className="barlist-name">{it.name}</span>
              <span className="dumbbell-track" aria-hidden="true">
                <span className="dumbbell-span" style={{ left: `${Math.min(a, b)}%`, width: `${Math.abs(b - a)}%`, background: up ? withAlpha(p.heat, 0.5) : withAlpha(p.cool, 0.5) }} />
                <span className="dumbbell-dot" style={{ left: `${a}%`, background: p.neutral }} />
                <span className="dumbbell-dot" style={{ left: `${b}%`, background: up ? p.heat : p.cool }} />
              </span>
              <span className="barlist-value">
                {(it.from * 100).toFixed(1)}% → <b>{(it.to * 100).toFixed(1)}%</b>
              </span>
            </li>
          );
        })}
      </ol>
    </figure>
  );
};

/** Five-cell heat strip for one subject (Pulse and Trends). */
export const HeatCells: React.FC<{ shares: number[]; hue: string; years: string[]; papers?: number[]; size?: "lg" | "sm" }> = ({ shares, hue, years, papers, size = "lg" }) => {
  const max = Math.max(...shares, 0);
  const p = readPalette();
  return (
    <>
      {shares.map((v, i) => {
        const k = max ? 0.1 + 0.9 * (v / max) : 0;
        return (
          <span
            key={years[i]}
            className={`cell cell-${size}`}
            style={{ background: cellColorCached(hue, k, p) }}
            title={`${years[i]}: ${fmtPct(v, 2)} of papers${papers ? ` (${papers[i]})` : ""}`}
          />
        );
      })}
    </>
  );
};

const cellCache = new Map<string, string>();
function cellColorCached(hue: string, k: number, p: ReturnType<typeof readPalette>): string {
  const key = `${hue}|${k.toFixed(3)}|${p.dark}|${p.paper}`;
  let c = cellCache.get(key);
  if (!c) {
    c = cellColor(hue, k, p);
    cellCache.set(key, c);
  }
  return c;
}

export function useStableYears(): string[] {
  return useMemo(() => ["2021", "2022", "2023", "2024", "2025"], []);
}
