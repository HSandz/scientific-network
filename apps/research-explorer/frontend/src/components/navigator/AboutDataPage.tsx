import React from "react";
import { useQuery } from "@tanstack/react-query";
import { navigatorApi } from "../../lib/navigatorApi";
import { Panel, Table, pct } from "../analytics/DashboardPrimitives";
import { MetricTooltip } from "./MetricTooltip";

const SYS_LABELS: Record<string, string> = {
  S1_slm_only: "S1 · SLM alone (no retrieval)",
  S2_vector_rag: "S2 · Vector RAG (top-10 abstract chunks)",
  S3_graphrag: "S3 · GraphRAG (local & global)",
  S4_multihop: "S4 · Full multi-hop (auto)",
};

function fmtScoreCi(entry: any): string {
  if (!entry || typeof entry.mean_score !== "number") return "—";
  const ci = entry.bootstrap_95_ci;
  return ci && ci.length === 2
    ? `${entry.mean_score.toFixed(4)} [${Number(ci[0]).toFixed(4)}, ${Number(ci[1]).toFixed(4)}]`
    : entry.mean_score.toFixed(4);
}

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
            <div className="text-xs text-muted mb-2 flex flex-wrap items-center gap-2">
              <MetricTooltip
                label="Wilson 95% CI"
                definition="Two-sided 95% Wilson binomial score interval capturing sampling uncertainty only; excludes AI-evaluator error."
                network="enriched-cb371912e308"
              />
              <span>· AI-assessed (no human gold validation)</span>
            </div>
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

          {d.qa_eval_v1 && (
            <div className="lg:col-span-2 space-y-4">
              <Panel title={`QA Benchmark Comparison (${d.qa_eval_v1.protocol_version}, 69 Kept Test Questions)`}>
                <div className="space-y-3">
                  <div className="p-2.5 rounded bg-ground border border-rule text-xs space-y-1">
                    <p className="font-semibold text-ink">AI-Assessed & Statistical Caveats</p>
                    <p className="text-muted">{d.qa_eval_v1.ai_assessed_disclosure}</p>
                    <p className="text-muted">{d.qa_eval_v1.evaluator_independence_disclosure}</p>
                    <p className="text-muted">{d.qa_eval_v1.coverage_and_extraction_caveats}</p>
                  </div>

                  <div className="text-xs text-muted flex flex-wrap items-center gap-3">
                    <MetricTooltip
                      label="Unified Factual Scoring & Bootstrap 95% CI"
                      definition="Identical text-to-graph-ID resolver (exact ID -> alias -> MiniLM cosine >= 0.80) computing set-F1 / exact match across S1–S4 with 2,000-resample seeded bootstrap 95% CIs."
                    />
                    <MetricTooltip
                      label="Automatic Faithfulness"
                      definition="Fraction of responses whose numbers, bracketed citations, and named entities are verified present in the retrieved trace/excerpts."
                    />
                  </div>

                  <Table
                    label="QA factual accuracy comparison"
                    headers={["System", "Hop 1 (14)", "Hop 2 (22)", "Hop 3 (18)", "Overall Factual (54)", "Mean Latency"]}
                    rows={["S1_slm_only", "S2_vector_rag", "S3_graphrag", "S4_multihop"].map((s) => {
                      const bh = d.qa_eval_v1.factual?.[s]?.by_hop || {};
                      return [
                        SYS_LABELS[s] || s,
                        fmtScoreCi(bh["1"]),
                        fmtScoreCi(bh["2"]),
                        fmtScoreCi(bh["3"]),
                        fmtScoreCi(bh["factual_overall"]),
                        bh["factual_overall"]?.mean_latency_s !== undefined ? `${bh["factual_overall"].mean_latency_s}s` : "—",
                      ];
                    })}
                  />

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 pt-2">
                    <div>
                      <h4 className="text-xs font-semibold mb-1.5">Faithfulness & AI-Assessed Citation Validity (95% Wilson CI)</h4>
                      <Table
                        label="Faithfulness and citation validity"
                        headers={["System", "Automatic Faithfulness", "Citation Validity (AI-assessed)"]}
                        rows={["S1_slm_only", "S2_vector_rag", "S3_graphrag", "S4_multihop"].map((s) => {
                          const f = d.qa_eval_v1.factual?.[s]?.overall_faithfulness || {};
                          const c = d.qa_eval_v1.citation_validity_ai_assessed?.by_system?.[s] || {};
                          const fStr =
                            f.status === "not_applicable"
                              ? "N/A (no retrieval trace)"
                              : f.total
                                ? `${f.passed}/${f.total} (${pct(f.rate, 1)})`
                                : "—";
                          const cStr =
                            c.total > 0
                              ? `${c.supported}/${c.total} (${pct(c.rate, 1)} [${pct(c.wilson_95_ci?.[0] || 0, 1)}, ${pct(c.wilson_95_ci?.[1] || 0, 1)}])`
                              : "0 citations emitted";
                          return [SYS_LABELS[s] || s, fStr, cStr];
                        })}
                      />
                      <p className="text-[11px] text-muted mt-1">
                        Citation A–B Cohen&apos;s κ (AI-assessed):{" "}
                        <span className="font-mono">{d.qa_eval_v1.citation_validity_ai_assessed?.cohens_kappa_ab ?? "—"}</span> · S4 attaches graph-level paper IDs without abstract text, explaining lower single-abstract support vs S2.
                      </p>
                    </div>

                    <div>
                      <h4 className="text-xs font-semibold mb-1.5">AI-Assessed Global Pairwise (15 Questions, AB+BA = 180 Items)</h4>
                      <Table
                        label="Global pairwise comparison"
                        headers={["System", "Wins / Ties / Losses", "Win Rate", "Position-Consistent"]}
                        rows={["S1_slm_only", "S2_vector_rag", "S3_graphrag", "S4_multihop"].map((s) => {
                          const p = d.qa_eval_v1.global_pairwise_ai_assessed?.by_system?.[s] || {};
                          return [
                            SYS_LABELS[s] || s,
                            p.total_appearances ? `${p.wins} / ${p.ties} / ${p.losses}` : "—",
                            typeof p.win_rate === "number" ? pct(p.win_rate, 1) : "—",
                            typeof p.position_consistent_win_rate === "number"
                              ? `${p.position_consistent_wins} (${pct(p.position_consistent_win_rate, 1)})`
                              : "—",
                          ];
                        })}
                      />
                      <p className="text-[11px] text-muted mt-1">
                        Pairwise A–B Cohen&apos;s κ (AI-assessed):{" "}
                        <span className="font-mono">{d.qa_eval_v1.global_pairwise_ai_assessed?.cohens_kappa_ab ?? "—"}</span> · Position-inconsistent pairs:{" "}
                        {d.qa_eval_v1.global_pairwise_ai_assessed?.position_inconsistent_pairs ?? "—"} / {d.qa_eval_v1.global_pairwise_ai_assessed?.total_unordered_pairs ?? "—"}.
                      </p>
                    </div>
                  </div>
                </div>
              </Panel>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
