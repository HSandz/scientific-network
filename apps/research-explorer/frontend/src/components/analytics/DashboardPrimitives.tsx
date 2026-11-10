import React from "react";
export const fmt = (n: unknown) =>
  typeof n === "number" ? n.toLocaleString() : "Unavailable";
export const pct = (n: unknown, digits = 2) =>
  typeof n === "number" ? `${(n * 100).toFixed(digits)}%` : "Unavailable";
export const Table: React.FC<{
  headers: string[];
  rows: React.ReactNode[][];
  label: string;
}> = ({ headers, rows, label }) => (
  <details className="mt-3 text-xs">
    <summary className="cursor-pointer py-2">
      {label} · data & keyboard actions ({rows.length} rows)
    </summary>
    <div className="overflow-auto max-h-96">
      <table className="w-full text-left">
        <caption className="sr-only">{label}</caption>
        <thead>
          <tr>
            {headers.map((h) => (
              <th key={h} className="p-2 font-medium text-muted">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-t border-border">
              {r.map((v, j) => (
                <td key={j} className="p-2 tabular-nums">
                  {v}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  </details>
);
export const Panel: React.FC<{ title: string; children: React.ReactNode }> = ({
  title,
  children,
}) => (
  <section className="ledger-panel p-4 sm:p-5 min-w-0 analytics-panel">
    <h3 className="text-base font-semibold mb-3">{title}</h3>
    {children}
  </section>
);
