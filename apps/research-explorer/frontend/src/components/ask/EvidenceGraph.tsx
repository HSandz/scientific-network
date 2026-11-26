import React, { useMemo, useState } from "react";
import type { GraphModel, GNode } from "../../lib/askModel";
import { cssVar, readPalette } from "../../lib/thermal";
import { navigate, pathFor } from "../../lib/router";
import { kindFromId } from "../../lib/names";
import { ENTITY_VAR, EntityDot } from "../ui/primitives";

const hue = (n: GNode) => ENTITY_VAR[n.label] || "var(--org)";

function targetFor(id: string): string | null {
  const k = kindFromId(id);
  if (!k) return null;
  if (["Method", "Task", "Dataset", "Topic"].includes(k)) return pathFor("topics", id);
  if (k === "Organization") return pathFor("groups", id);
  if (k === "Researcher" || k === "Paper") return pathFor("node", id);
  return null;
}

/**
 * The orchestrated moment: a deterministic, labelled layout revealed hop by hop as the plan
 * steps finish. Nodes fade in and links draw in; with reduced motion everything appears at once.
 */
export const EvidenceGraph: React.FC<{ model: GraphModel; revealed: number; done: boolean }> = ({ model, revealed, done }) => {
  const [hover, setHover] = useState<GNode | null>(null);
  const p = readPalette();
  const heat = p.heat;
  const faint = cssVar("--decor");
  const surface = cssVar("--surface");
  const shown = done ? 99 : revealed;
  const maxW = useMemo(() => Math.max(1, ...model.edges.map((e) => e.weight)), [model]);
  const funnel = model.mode === "funnel";
  const hopText = shown >= model.steps ? "Complete walk" : shown <= 0 ? "Starting point" : `Step ${shown} of ${model.steps}`;

  return (
    <div className="ev-graph">
      <p className="ev-caption">{model.caption}</p>
      <div className="hopbar" aria-hidden="true">
        {Array.from({ length: model.steps + 1 }, (_, i) => (
          <i key={i} className={i <= shown ? "on" : ""} />
        ))}
        <span>{hopText}</span>
      </div>
      <div className="graph-wrap">
        <svg
          viewBox={`0 0 ${model.width} ${model.height}`}
          role="img"
          aria-label={`Graph of ${model.nodes.length} entities and ${model.edges.length} links. ${model.caption}`}
          data-testid="ask-subgraph"
          data-graph-mode={model.mode}
          data-graph-nodes={model.nodes.length}
          data-graph-revealed={Math.min(shown, model.steps)}
          style={{ minWidth: 520 }}
        >
          <g>
            {model.edges.map((e) => {
              const on = e.reveal <= shown;
              const len = Math.hypot(e.target.x - e.source.x, e.target.y - e.source.y);
              const accent = e.accent;
              return (
                <line
                  key={e.id}
                  x1={e.source.x}
                  y1={e.source.y}
                  x2={e.target.x}
                  y2={e.target.y}
                  stroke={accent ? heat : faint}
                  strokeOpacity={accent ? 0.8 : funnel ? (e.target.highlight ? 0.4 : 0.22) : 0.5}
                  strokeWidth={1 + 3 * Math.sqrt(e.weight / maxW)}
                  strokeDasharray={len}
                  strokeDashoffset={on ? 0 : len}
                  className="ev-edge"
                >
                  <title>{e.title}</title>
                </line>
              );
            })}
          </g>
          <g>
            {model.nodes.map((n, i) => {
              const on = n.reveal <= shown;
              const go = targetFor(n.id);
              const lp = n.labelPos;
              return (
                <g
                  key={n.id}
                  transform={`translate(${n.x},${n.y})`}
                  className="ev-node"
                  style={{ opacity: on ? 1 : 0, transitionDelay: on && !done ? `${Math.min(i, 30) * 18}ms` : "0ms" }}
                  onMouseEnter={() => setHover(n)}
                  onMouseLeave={() => setHover(null)}
                  onFocus={() => setHover(n)}
                  onBlur={() => setHover(null)}
                  tabIndex={on && go ? 0 : -1}
                  role={go ? "link" : undefined}
                  aria-label={go ? `${n.name}, ${n.label}` : undefined}
                  onClick={() => go && navigate(go)}
                  onKeyDown={(e) => {
                    if (go && (e.key === "Enter" || e.key === " ")) {
                      e.preventDefault();
                      navigate(go);
                    }
                  }}
                >
                  <circle r={n.r} fill={hue(n)} stroke={n.highlight ? heat : surface} strokeWidth={n.highlight ? 3 : 1.5} />
                  {n.showLabel && lp && (
                    <text className={`node-label${n.strong ? " strong" : ""}`} x={lp.dx} y={lp.dy} textAnchor={lp.anchor}>
                      {lp.lines ? (
                        lp.lines.map((ln, k) => (
                          <tspan key={k} x={lp.dx} dy={k ? 16 : 0}>
                            {ln}
                          </tspan>
                        ))
                      ) : (
                        <>
                          {n.short}
                          {n.value ? `  ${n.value}` : ""}
                        </>
                      )}
                    </text>
                  )}
                  <title>{n.name}</title>
                </g>
              );
            })}
          </g>
        </svg>
        {hover && (
          <div className="graph-tip" role="status">
            {hover.name}
            {hover.value ? `: ${hover.highlight ? `share ${hover.value.startsWith("−") ? "down" : "up"} ${hover.value.replace(/^[+−]/, "")} points` : hover.value}` : ""}
          </div>
        )}
      </div>
      <div className="g-legend">
        {model.legend.filter((l, i, all) => all.findIndex((x) => x.kind === l.kind) === i).map((l) =>
          l.ring ? (
            <span key="ring">
              <span className="ring-swatch" />
              {l.label}
            </span>
          ) : (
            <span key={l.kind}>
              <EntityDot kind={l.kind} />
              {l.label}
            </span>
          ),
        )}
      </div>
    </div>
  );
};

export const EmptyGraphArt: React.FC = () => (
  <svg viewBox="0 0 120 80" aria-hidden="true" className="ev-empty-art">
    <g stroke="var(--rule)" strokeWidth="1.5">
      <line x1="20" y1="40" x2="60" y2="20" />
      <line x1="60" y1="20" x2="100" y2="34" />
      <line x1="60" y1="20" x2="64" y2="62" />
      <line x1="20" y1="40" x2="64" y2="62" />
    </g>
    <g fill="var(--surface)" stroke="var(--decor)" strokeWidth="1.5">
      <circle cx="20" cy="40" r="6" />
      <circle cx="60" cy="20" r="8" />
      <circle cx="100" cy="34" r="5" />
      <circle cx="64" cy="62" r="5" />
    </g>
  </svg>
);
