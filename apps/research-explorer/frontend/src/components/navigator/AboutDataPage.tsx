import React from "react";
import { useQuery } from "@tanstack/react-query";
import { navigatorApi } from "../../lib/navigatorApi";
import { ORG_ATTRIBUTION_NOTE } from "./methodNotes";
import { CopyIdButton, ErrorLine, LoadingLine, PageHead, Section } from "../ui/primitives";

const SYSTEMS: Array<[string, string]> = [
  ["S1_slm_only", "Language model alone"],
  ["S2_vector_rag", "Search over abstracts"],
  ["S3_graphrag", "GraphRAG"],
  ["S4_multihop", "Multi-hop graph search (used by Ask)"],
];

const pct = (v: unknown, digits = 1) => (typeof v === "number" ? `${(v * 100).toFixed(digits)}%` : "–");
const range = (low: unknown, high: unknown, digits = 1) => (typeof low === "number" && typeof high === "number" ? `${(low * 100).toFixed(digits)} to ${pct(high, digits)}` : "–");
const score = (v: unknown) => (typeof v === "number" ? v.toFixed(2) : "–");
const count = (v: unknown) => (typeof v === "number" ? v.toLocaleString("en") : "–");

/** A table that scrolls sideways on narrow screens. The first column names the row. */
const Figures: React.FC<{ caption: string; head: string[]; rows: React.ReactNode[][] }> = ({ caption, head, rows }) => (
  <div className="table-scroll" tabIndex={0} role="region" aria-label={caption}>
    <table className="data figures">
      <caption>{caption}</caption>
      <thead>
        <tr>
          {head.map((h, i) => (
            <th key={h} className={i ? "num" : ""}>
              {h}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((r, i) => (
          <tr key={i}>
            {r.map((c, j) => (j ? <td key={j} className="num">{c}</td> : <th key={j} scope="row">{c}</th>))}
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

const Sub: React.FC<{ main: React.ReactNode; sub: React.ReactNode }> = ({ main, sub }) => (
  <>
    {main}
    <span className="cell-sub">{sub}</span>
  </>
);

export const AboutDataPage: React.FC<{ releaseQuality?: React.ReactNode }> = ({ releaseQuality }) => {
  const q = useQuery({ queryKey: ["nav-about-data"], queryFn: ({ signal }) => navigatorApi.getAboutData(signal) });
  const d: any = q.data;

  return (
    <div data-testid="page-about-data" className="about">
      <PageHead title="About the data" sub="Where it comes from, how good it is, and what you may reuse" />
      {q.isLoading && <LoadingLine />}
      {q.isError && <ErrorLine error={q.error} onRetry={() => q.refetch()} />}
      {d && <Body d={d} releaseQuality={releaseQuality} />}
    </div>
  );
};

const Body: React.FC<{ d: any; releaseQuality?: React.ReactNode }> = ({ d, releaseQuality }) => {
  const v = d.versions || {};
  const c = d.counts || {};
  const e4 = d.e4_v3_quality || {};
  const qa = d.qa_eval_v1;
  const run = d.runtime_model || {};
  const reports = d.rag_reports || {};

  const e4Rows: Array<[string, any]> = [
    ["Entities linked to Wikipedia or Wikidata", e4.link],
    ["“Part of” links that were kept", e4.part_of],
    ["Organization “member of” links", e4.member_of],
    ["“Applied to” links shown by one paper", e4.applied_to_single_paper?.shown_paper_supports_the_relation],
  ];
  const e4Sensitivity: any[] = [e4.link, e4.part_of, e4.member_of, e4.applied_to_single_paper].map((x) => x?.sensitivity_unclear_as_incorrect);

  const supp = qa?.supplementary_literature_precision;
  const cites = qa?.citation_validity_ai_assessed;
  const pairs = qa?.global_pairwise_ai_assessed;

  return (
    <>
      <p className="prose lede-note" data-testid="about-ai-statement">
        {d.ai_assessment_disclosure}
      </p>

      <Section id="sources" title="Sources">
        <p className="prose">
          The collection is 13,617 main-track papers from AAAI and IJCAI, 2021 to 2025. Paper lists come from the official proceedings pages. Authors, affiliations and citations come from OpenAlex; organization records from ROR and Wikidata; some
          descriptions from English Wikipedia. Methods, tasks and datasets were extracted from paper text by a language model. Other conferences and other years are not covered.
        </p>
        <p className="prose">Coverage is incomplete: not every authorship has an affiliation, and topic labels are often wrong. The measured figures are under the quality of the frozen release, below.</p>
      </Section>

      <Section id="versions" title="Versions" hint="Quote these to reproduce a figure." testId="about-versions">
        <dl className="kv">
          <dt>Graph used here</dt>
          <dd className="hash">{v.v5_enriched}</dd>
          <dt>Graph file SHA-256</dt>
          <dd className="hash">
            {v.v5_sha256 || "–"} {v.v5_sha256 && <CopyIdButton id={v.v5_sha256} label="Copy" />}
          </dd>
          <dt>Frozen release it builds on</dt>
          <dd className="hash">{v.v4_base}</dd>
          <dt>Network analysis</dt>
          <dd className="hash">{v.analysis}</dd>
          <dt>Search index for Ask</dt>
          <dd className="hash">{v.rag}</dd>
          <dt>Language model</dt>
          <dd>
            {run.model_id}, run locally at temperature {run.temperature}
          </dd>
          <dt>Embedding model</dt>
          <dd>{run.embeddings}</dd>
        </dl>
        <Figures
          caption="Size of the graph"
          head={["Layer", "Entities", "Connections"]}
          rows={[
            ["Publication records (frozen release)", count(c.v4_layer?.nodes), count(c.v4_layer?.edges)],
            ["Added from paper text and external records", count(c.enrichment_layer?.nodes), count(c.enrichment_layer?.edges)],
            ["Total", count(c.total?.nodes), count(c.total?.edges)],
          ]}
        />
      </Section>

      <Section id="quality" title="How accurate the added facts are" hint="Samples judged by AI evaluators, not by people. Intervals are 95% Wilson intervals: they cover sampling error, not evaluator error." testId="about-quality">
        <Figures
          caption="Added facts judged correct"
          head={["What was checked", "Correct, of those decided", "95% interval", "If unclear counts as wrong"]}
          rows={e4Rows.map(([label, m], i) => {
            const s = e4Sensitivity[i];
            return [label, m ? <Sub main={pct(m.estimate)} sub={`${m.k} of ${m.n}`} /> : "–", m ? range(m.low, m.high) : "–", s ? <Sub main={pct(s.estimate)} sub={`${s.k} of ${s.n}`} /> : "–"];
          })}
        />
        {e4.pooled_agreement && (
          <p className="note">
            Two evaluators agreed on {pct(e4.pooled_agreement.observed_agreement)} of {e4.pooled_agreement.items_judged_by_both} items (Cohen’s κ {score(e4.pooled_agreement.cohens_kappa)}); a third decided the {e4.pooled_agreement.disputes_sent_to_c} disputes.
          </p>
        )}
        {releaseQuality && (
          <details className="map-all" data-testid="about-release-quality">
            <summary>Quality of the frozen release the graph builds on</summary>
            {releaseQuality}
          </details>
        )}
      </Section>

      {qa && (
        <Section id="benchmark" title="How well Ask answers" testId="about-benchmark">
          <p className="prose">
            <b>The main score measures agreement with the graph, not truth.</b> Reference answers were computed from the graph itself, so a system that reads the graph has an advantage, and a correct answer taken from abstracts can score zero. The test has
            69 questions; 54 have factual answers.
          </p>
          <p className="prose">{ORG_ATTRIBUTION_NOTE}</p>
          <Figures
            caption="Agreement with the graph on factual questions (0 to 1)"
            head={["System", "1 step (14)", "2 steps (22)", "3 steps (18)", "All 54", "Mean time"]}
            rows={SYSTEMS.map(([id, label]) => {
              const by = qa.factual?.[id]?.by_hop || {};
              const cell = (m: any) => (m ? <Sub main={score(m.mean_score)} sub={m.bootstrap_95_ci ? `${score(m.bootstrap_95_ci[0])} to ${score(m.bootstrap_95_ci[1])}` : ""} /> : "–");
              return [label, cell(by["1"]), cell(by["2"]), cell(by["3"]), cell(by.factual_overall), typeof by.factual_overall?.mean_latency_s === "number" ? `${by.factual_overall.mean_latency_s.toFixed(1)} s` : "–"];
            })}
          />
          <p className="note">The small figures are 95% bootstrap intervals.</p>
          <Figures
            caption="Checks on the answers themselves"
            head={["System", "Passed automatic grounding check", "Citations that support the sentence", "Won in side-by-side judging"]}
            rows={SYSTEMS.map(([id, label]) => {
              const f = qa.factual?.[id]?.overall_faithfulness || {};
              const cv = cites?.by_system?.[id] || {};
              const p = pairs?.by_system?.[id] || {};
              return [
                label,
                f.status === "not_applicable" ? "Does not apply" : f.total ? <Sub main={pct(f.rate)} sub={`${f.passed} of ${f.total}`} /> : "–",
                cv.total ? <Sub main={pct(cv.rate)} sub={`${cv.supported} of ${cv.total}, interval ${range(cv.wilson_95_ci?.[0], cv.wilson_95_ci?.[1])}`} /> : "No citations given",
                p.total_appearances ? <Sub main={pct(p.win_rate)} sub={`${p.wins} won, ${p.ties} tied, ${p.losses} lost`} /> : "–",
              ];
            })}
          />
          <p className="note">
            The grounding check tests that numbers, citations and names appear in what was retrieved. Citation support and side-by-side wins are AI-assessed (agreement between evaluators: κ {score(cites?.cohens_kappa_ab)} and {score(pairs?.cohens_kappa_ab)}).
            Multi-hop search cites papers found through the graph without reading their abstracts, so fewer of its citations support the sentence on their own.
          </p>

          {supp && (
            <>
              <h3>Supplementary check against the literature</h3>
              <p className="prose">
                Added after the test was run, and it does not replace the scores above. AI evaluators asked whether each listed item is a correct answer supported by the papers shown with it.
              </p>
              <Figures
                caption="Listed items supported by the literature shown"
                head={["System", "Supported", "95% interval", "Leaving out unclear"]}
                rows={SYSTEMS.filter(([id]) => supp.by_system?.[id]).map(([id, label]) => {
                  const a = supp.by_system[id].literature_supported_precision;
                  const b = supp.by_system[id].excluding_unclear;
                  return [label, <Sub main={pct(a.rate)} sub={`${a.yes} of ${a.total}`} />, range(a.wilson_95_ci?.[0], a.wilson_95_ci?.[1]), <Sub main={pct(b.rate)} sub={`${b.yes} of ${b.total}`} />];
                })}
              />
            </>
          )}

          <details className="map-all">
            <summary>Who judged, and other limits</summary>
            <p className="prose">{qa.coverage_and_extraction_caveats}</p>
            <p className="prose">{qa.ai_assessed_disclosure}</p>
            <p className="prose">{qa.evaluator_independence_disclosure}</p>
            {supp?.evaluators && (
              <p className="prose">
                Supplementary check: evaluator A was a {supp.evaluators.A}; B a {supp.evaluators.B}. {supp.evaluators.C}
              </p>
            )}
            {qa.scorer_hashseed_sensitivity && (
              <p className="prose">
                The scorer’s name matching depends on a random seed. Re-scoring the saved answers with {qa.scorer_hashseed_sensitivity.seeds?.length} seeds moves the multi-hop score between{" "}
                {score(qa.scorer_hashseed_sensitivity.factual_overall?.S4_multihop?.min)} and {score(qa.scorer_hashseed_sensitivity.factual_overall?.S4_multihop?.max)}
                {qa.scorer_hashseed_sensitivity.ranking_stable_across_seeds ? "; the ranking of the four systems does not change" : ""}. No system was run again.
              </p>
            )}
            <p className="note">
              Protocol {qa.protocol_version}, code commit <span className="hash">{String(qa.code_commit || "").slice(0, 12)}</span>, model revision <span className="hash">{String(qa.llm_hf_revision || "").slice(0, 12)}</span>.
            </p>
          </details>
        </Section>
      )}

      {reports.attempted && (
        <Section id="summaries" title="AI-written community summaries">
          <p className="prose">
            The language model wrote summaries for {count((reports.succeeded_first_try || 0) + (reports.succeeded_retry || 0))} of {count(reports.attempted)} communities. {count(reports.dropped)} were dropped because they contained numbers that were not in the
            input. The summaries are AI-generated from graph data and can still be wrong.
          </p>
        </Section>
      )}

      <Section id="licences" title="Licences">
        <ul className="plain-list licences">
          <li>
            <span>Code</span>
            <span>MIT</span>
          </li>
          <li>
            <span>Data produced by this project, including AI-generated text</span>
            <span>CC BY 4.0</span>
          </li>
          <li>
            <span>OpenAlex, ROR and Wikidata records</span>
            <span>CC0 1.0</span>
          </li>
          <li>
            <span>Wikipedia excerpts, with attribution and share-alike</span>
            <span>CC BY-SA 4.0</span>
          </li>
        </ul>
        <p className="note">
          Conference proceedings supply bibliographic facts and links; no PDFs are redistributed. Full terms are in{" "}
          <a className="textlink" href="https://github.com/HSandz/scientific-network/blob/main/LICENSE-DATA.md" target="_blank" rel="noreferrer">
            the data licence file
          </a>
          .
        </p>
      </Section>
    </>
  );
};
