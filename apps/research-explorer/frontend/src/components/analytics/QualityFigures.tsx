import React from "react";
import type { QualityContract } from "../../types/explorer";
import { Panel, pct, fmt } from "./DashboardPrimitives";
function Measure({
  label,
  value,
  target,
  note,
}: {
  label: string;
  value?: number;
  target?: number;
  note: string;
}) {
  const below =
    typeof value === "number" && typeof target === "number" && value < target;
  return (
    <div className="quality-measure">
      <div className="flex justify-between gap-3 text-sm">
        <span>{label}</span>
        <strong className="num">{pct(value)}</strong>
      </div>
      <div
        className="quality-track"
        role="img"
        aria-label={`${label}: ${pct(value)}${target != null ? `; target ${pct(target)}` : ""}`}
      >
        {value != null && (
          <span
            className={below ? "quality-fill below" : "quality-fill"}
            style={{ width: `${Math.max(0, Math.min(100, value * 100))}%` }}
          />
        )}
        {target != null && <i style={{ left: `${target * 100}%` }} />}
      </div>
      <p className={`text-xs mt-2 ${below ? "text-warning" : "text-muted"}`}>
        {target != null && (
          <>
            Target {pct(target, 0)} · {value == null ? "Value unavailable" : below ? "Below target" : "Target met"}
            .{" "}
          </>
        )}
        {note}
      </p>
    </div>
  );
}
export const QualityFigures: React.FC<{ quality?: QualityContract }> = ({
  quality: q,
}) => {
  const lo = q?.edge_precision_wilson_lower,
    hi = q?.edge_precision_wilson_upper,
    point = q?.edge_precision;
  const x = (v: number) => 42 + v * 400;
  return (
    <div className="analytics-grid">
      <Panel title="Coverage and topic precision">
        <Measure
          label="Affiliation coverage"
          value={q?.affiliation_coverage}
          target={q?.affiliation_target}
          note="Matched-work authorship positions."
        />
        <Measure
          label="Topic coverage"
          value={q?.topic_coverage}
          target={q?.topic_coverage_target}
          note="Labeled core papers; coverage ≠ accuracy."
        />
        <Measure
          label="Historical topic precision"
          value={q?.topic_precision}
          target={q?.topic_precision_target}
          note="Weighted labels against AI references."
        />
      </Panel>
      <Panel title="AI-assessed edge precision and uncertainty">
        <p className="text-3xl num mb-1">
          {pct(point)}{" "}
          <span className="text-sm text-muted">
            {fmt(q?.edge_precision_correct)}/{fmt(q?.edge_precision_total)}{" "}
            correct
          </span>
        </p>
        <p className="text-sm text-muted">
          Wilson 95% interval {pct(lo)}–{pct(hi)}
        </p>
        {lo != null && hi != null && point != null && (
          <svg
            viewBox="0 0 480 100"
            className="w-full my-3"
            role="img"
            aria-label={`AI-assessed precision ${pct(point)}, Wilson 95% interval ${pct(lo)} to ${pct(hi)}. Percentage axis from 0 to 100.`}
          >
            <line x1="42" x2="442" y1="60" y2="60" stroke="var(--control)" />
            {[0, 0.25, 0.5, 0.75, 1].map((v) => (
              <g key={v}>
                <line
                  x1={x(v)}
                  x2={x(v)}
                  y1="56"
                  y2="64"
                  stroke="var(--control)"
                />
                <text
                  x={x(v)}
                  y="84"
                  textAnchor="middle"
                  fill="var(--muted)"
                  fontSize="12"
                >
                  {v * 100}%
                </text>
              </g>
            ))}
            <line
              x1={x(lo)}
              x2={x(hi)}
              y1="35"
              y2="35"
              stroke="var(--accent)"
              strokeWidth="4"
            />
            {[lo, hi].map((v) => (
              <line
                key={v}
                x1={x(v)}
                x2={x(v)}
                y1="26"
                y2="44"
                stroke="var(--accent)"
                strokeWidth="2"
              />
            ))}
            <circle cx={x(point)} cy="35" r="5" fill="var(--accent)" />
          </svg>
        )}
        <p className="text-xs text-muted">
          AI-assessed only. No independent human validation. Wilson intervals
          describe sampling uncertainty and exclude evaluator error.
        </p>
      </Panel>
      <Panel title="Historical topic methods: micro-F1">
        <p className="text-sm text-muted mb-3">
          Agreement with reused AI references; this is historical evaluation,
          not a new independent test.
        </p>
        {[
          ["Embedding method", q?.topic_embedding_micro_f1],
          ["Phrase baseline", q?.topic_phrase_baseline_f1],
        ].map(([label, value]) => (
          <div className="quality-measure" key={String(label)}>
            <div className="flex justify-between text-sm">
              <span>{label}</span>
              <strong className="num">
                {typeof value === "number" ? value.toFixed(4) : "Unavailable"}
              </strong>
            </div>
            <div
              className="quality-track"
              role="img"
              aria-label={`${label} micro-F1 ${value ?? "unavailable"}, scale 0 to 1`}
            >
              <span
                className="quality-fill"
                style={{
                  width: `${typeof value === "number" ? value * 100 : 0}%`,
                  opacity: label === "Phrase baseline" ? 0.5 : 1,
                }}
              />
            </div>
          </div>
        ))}
        <p className="text-xs text-muted">
          Micro-F1 scale: 0–1. Exposed references and shared source dependence
          limit interpretation.
        </p>
      </Panel>
      <Panel title="Read the evidence with its limits">
        <p className="text-sm leading-relaxed">
          The edge audit and the topic evaluation assess different claims.
          Failed affiliation coverage and topic-precision targets remain
          visible.
        </p>
        <p className="text-sm text-muted mt-3">
          Independent human validation, evaluator independence and verified
          course accuracy are not established. Inferred topics are provisional;
          missing affiliation evidence means unknown.
        </p>
      </Panel>
    </div>
  );
};
