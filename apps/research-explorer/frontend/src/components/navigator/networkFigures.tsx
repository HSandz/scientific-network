import React from "react";
import { useWidth } from "../charts/charts";

/** How many pairs sit at each shortest-path length. */
export const PathHistogram: React.FC<{ histogram: Record<string, number>; mean?: number }> = ({ histogram, mean }) => {
  const [ref, W] = useWidth(720);
  const keys = Object.keys(histogram)
    .map(Number)
    .sort((a, b) => a - b);
  const total = keys.reduce((a, k) => a + histogram[String(k)], 0) || 1;
  const shares = keys.map((k) => histogram[String(k)] / total);
  const max = Math.max(...shares, 0.0001);
  const H = 250;
  const m = { t: 22, r: 4, b: 40, l: 4 };
  const bw = (W - m.l - m.r) / Math.max(keys.length, 1);
  const labelEvery = bw < 22 ? 4 : bw < 34 ? 2 : 1;
  const peak = shares.indexOf(max);
  return (
    <figure ref={ref} className="chart" data-chart-label="Path length distribution" data-chart-rendered="true" data-chart-point-count={keys.length}>
      <svg viewBox={`0 0 ${W} ${H}`} className="chart-svg" role="img" aria-label={`Share of pairs by number of steps: ${keys.map((k, i) => `${k} steps ${(shares[i] * 100).toFixed(1)}%`).join(", ")}`}>
        {keys.map((k, i) => {
          const h = (shares[i] / max) * (H - m.t - m.b);
          return (
            <g key={k}>
              <rect x={m.l + i * bw + 1} y={H - m.b - h} width={Math.max(1, bw - 3)} height={h} rx={2} fill="var(--ink)" fillOpacity={i === peak ? 0.85 : 0.45}>
                <title>{`${k} steps: ${(shares[i] * 100).toFixed(2)}% of pairs`}</title>
              </rect>
              {i === peak && (
                <text x={m.l + i * bw + bw / 2} y={H - m.b - h - 7} textAnchor="middle" fontSize={13} fontWeight={700} fill="var(--ink)">
                  {(shares[i] * 100).toFixed(0)}%
                </text>
              )}
              {(k % labelEvery === 0 || labelEvery === 1) && (
                <text x={m.l + i * bw + bw / 2} y={H - m.b + 17} textAnchor="middle" fontSize={12} fill="var(--muted)">
                  {k}
                </text>
              )}
            </g>
          );
        })}
        <text x={W / 2} y={H - 4} textAnchor="middle" fontSize={13} fill="var(--muted)">
          Steps between two researchers{mean ? ` (average ${mean.toFixed(1)})` : ""}
        </text>
      </svg>
    </figure>
  );
};

const nice = (v: number) => (v >= 1000 ? `${v / 1000}k` : String(v));

/** Degree distribution on logarithmic axes: how many nodes have how many links. */
export const DegreePlot: React.FC<{ counts: Record<string, number>; noun: string }> = ({ counts, noun }) => {
  const [ref, W] = useWidth(720);
  const pts = Object.entries(counts)
    .map(([k, c]) => [Number(k), Number(c)] as const)
    .filter(([k, c]) => k > 0 && c > 0)
    .sort((a, b) => a[0] - b[0]);
  const H = 270;
  const m = { t: 12, r: 14, b: 40, l: 44 };
  const decades = (v: number) => Math.max(1, Math.ceil(Math.log10(Math.max(v, 1)) - 1e-9));
  const dx = decades(Math.max(...pts.map((p) => p[0]), 1));
  const dy = decades(Math.max(...pts.map((p) => p[1]), 1));
  const x = (k: number) => m.l + (Math.log10(k) / dx) * (W - m.l - m.r);
  const y = (c: number) => H - m.b - (Math.log10(c) / dy) * (H - m.t - m.b);
  return (
    <figure ref={ref} className="chart" data-chart-label="Degree distribution" data-chart-rendered="true" data-chart-point-count={pts.length}>
      <svg viewBox={`0 0 ${W} ${H}`} className="chart-svg" role="img" aria-label={`Number of ${noun} by number of links, on logarithmic axes. ${pts.length} points.`}>
        {Array.from({ length: dy + 1 }, (_, i) => (
          <g key={`y${i}`}>
            <line x1={m.l} x2={W - m.r} y1={y(10 ** i)} y2={y(10 ** i)} stroke="var(--rule)" strokeDasharray={i ? "2 4" : undefined} />
            <text x={m.l - 8} y={y(10 ** i) + 4} textAnchor="end" fontSize={12} fill="var(--muted)">
              {nice(10 ** i)}
            </text>
          </g>
        ))}
        {Array.from({ length: dx + 1 }, (_, i) => (
          <text key={`x${i}`} x={x(10 ** i)} y={H - m.b + 17} textAnchor="middle" fontSize={12} fill="var(--muted)">
            {nice(10 ** i)}
          </text>
        ))}
        {pts.map(([k, c]) => (
          <circle key={k} cx={x(k)} cy={y(c)} r={3} fill="var(--ink)" fillOpacity={0.6}>
            <title>{`${c} ${noun} have ${k} links`}</title>
          </circle>
        ))}
        <text x={(W + m.l) / 2} y={H - 4} textAnchor="middle" fontSize={13} fill="var(--muted)">
          Links per node (log scale); height is the number of {noun} (log scale)
        </text>
      </svg>
    </figure>
  );
};
