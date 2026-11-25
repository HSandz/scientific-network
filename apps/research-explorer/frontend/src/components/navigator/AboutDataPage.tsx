import React from "react";
import { useQuery } from "@tanstack/react-query";
import { navigatorApi } from "../../lib/navigatorApi";
import { Panel, Table, pct } from "../analytics/DashboardPrimitives";

export const AboutDataPage: React.FC = () => {
  const { data, isLoading, error } = useQuery({
    queryKey: ["nav-about-data"],
    queryFn: ({ signal }) => navigatorApi.getAboutData(signal),
  });

  const d: any = data || {};
  const versions = d.versions || {};
  const counts = d.counts || {};
  const e4 = d.e4_v3_quality || {};
  const runtime = d.runtime_model || {};

  const e4Axes: Array<[string, any]> = [
    ["PART_OF kept edges", e4.part_of?.kept_edges],
    ["MEMBER_OF", e4.member_of?.decided_only],
    ["Linking v3", e4.link?.decided_or_all || e4.link],
    ["APPLIED_TO single paper", e4.applied_to_single_paper?.shown_paper_supports_the_relation],
  ];
  const e4Rows = e4Axes
    .filter(([, metric]) => metric && typeof metric === "object")
    .map(([name, metric]) => [
      String(name),
      metric.estimate !== undefined ? pct(metric.estimate, 1) : "—",
      metric.low !== undefined && metric.high !== undefined
        ? `[${pct(metric.low, 1)}, ${pct(metric.high, 1)}]`
        : "—",
      metric.k !== undefined && metric.n !== undefined ? `${metric.k}/${metric.n}` : "—",
    ]);

  return (
    <div data-testid="page-about-data" className="p-4 sm:p-6 space-y-4 overflow-y-auto h-full">
      <div className="ledger-panel p-4">
        <h1 className="text-lg font-semibold text-ink">About the Data, Quality Audit & Provenance</h1>
        <p className="text-xs text-muted mt-1">{d.ai_assessment_disclosure}</p>
      </div>

      {isLoading && <p role="status" className="text-sm text-muted">Loading provenance…</p>}
      {error && <p role="alert" className="text-sm text-[var(--negative)]">{String(error)}</p>}

      {data && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Panel title="Graph & Pipeline Versions">
            <dl className="grid grid-cols-2 gap-2 text-xs">
              <dt className="text-muted">Frozen Base Graph (v4)</dt>
              <dd className="font-mono">{versions.v4_base}</dd>
              <dt className="text-muted">Enriched Graph (v5 / v3 enrichment)</dt>
              <dd className="font-mono">{versions.v5_enriched}</dd>
              <dt className="text-muted">Enriched SHA-256</dt>
              <dd className="font-mono truncate">{versions.v5_sha256}</dd>
              <dt className="text-muted">SNA Config</dt>
              <dd className="font-mono">{versions.analysis}</dd>
              <dt className="text-muted">GraphRAG Index</dt>
              <dd className="font-mono">{versions.rag}</dd>
              <dt className="text-muted">SLM Runtime</dt>
              <dd>{runtime.model_id}</dd>
              <dt className="text-muted">Embeddings</dt>
              <dd className="font-mono">{runtime.embeddings}</dd>
            </dl>
          </Panel>

          <Panel title="Enriched Graph v5 Inventory">
            <dl className="grid grid-cols-2 gap-2 text-xs tabular-nums">
              <dt className="text-muted">Total Nodes</dt>
              <dd className="font-semibold">{counts.total?.nodes?.toLocaleString()}</dd>
              <dt className="text-muted">Total Edges</dt>
              <dd className="font-semibold">{counts.total?.edges?.toLocaleString()}</dd>
              <dt className="text-muted">Base v4 Nodes / Edges</dt>
              <dd>{counts.v4_layer?.nodes?.toLocaleString()} / {counts.v4_layer?.edges?.toLocaleString()}</dd>
              <dt className="text-muted">Enrichment Nodes / Edges</dt>
              <dd>{counts.enrichment_layer?.nodes?.toLocaleString()} / {counts.enrichment_layer?.edges?.toLocaleString()}</dd>
              <dt className="text-muted">Evidence Records</dt>
              <dd>{counts.total?.evidence?.toLocaleString()}</dd>
            </dl>
          </Panel>

          <Panel title="E4 Quality Evaluation (AI-Assessed, Wilson 95% CI)">
            <p className="text-xs text-muted mb-2">
              Wilson 95% confidence intervals measure sampling variance only and exclude AI-evaluator error.
            </p>
            <Table
              label="E4 evaluation intervals"
              headers={["Axis", "Primary Estimate", "Wilson 95% CI", "k / n"]}
              rows={e4Rows}
            />
          </Panel>

          <Panel title="GraphRAG & Corpus Scope">
            <p className="text-xs text-muted leading-relaxed">
              Corpus: 13,617 AAAI and IJCAI main-track papers (2021–2025) from frozen roster v10. Precomputed S1–S3 and trend tables
              serve sub-second views; GraphRAG community reports, entity descriptions, and annotated abstract chunks power Ask.
            </p>
            {d.rag_reports && Object.keys(d.rag_reports).length > 0 && (
              <p className="text-xs font-mono text-ink mt-2">
                Reports stats: {JSON.stringify({ ok: (d.rag_reports.succeeded_first_try || 0) + (d.rag_reports.succeeded_retry || 0), dropped: d.rag_reports.dropped })}
              </p>
            )}
          </Panel>
        </div>
      )}
    </div>
  );
};
