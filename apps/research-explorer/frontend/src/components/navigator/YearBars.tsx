import React from "react";

/** A few yearly counts as labelled columns. */
export const YearBars: React.FC<{ label: string; data: Array<{ year: number; papers: number }> }> = ({ label, data }) => {
  const max = Math.max(1, ...data.map((d) => d.papers));
  return (
    <figure className="yearbars" data-chart-label={label} data-chart-rendered="true" data-chart-point-count={data.length}>
      <ol aria-label={label}>
        {data.map((d) => (
          <li key={d.year}>
            <b>{d.papers.toLocaleString("en")}</b>
            <span className="col" aria-hidden="true">
              <i style={{ height: `${(d.papers / max) * 100}%` }} />
            </span>
            <span className="yr">{d.year}</span>
          </li>
        ))}
      </ol>
    </figure>
  );
};
