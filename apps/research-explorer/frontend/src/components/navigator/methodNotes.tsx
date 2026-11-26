import React from "react";
import { MIN_ORG_PAPERS, MIN_RESEARCHER_PAPERS, GREW_RATIO, MIN_CHANGE_POINTS } from "../../config/display";

/** Plain-language caveats: "a share is a share of all papers" etc. come from the analysis summary. */
function Caveats({ caveats }: { caveats?: string[] }) {
  if (!caveats?.length) return null;
  return (
    <>
      <h3>Limits</h3>
      <ul>
        {caveats.map((c) => (
          <li key={c}>{c.replace(/human_review_pending \/ /, "")}</li>
        ))}
      </ul>
    </>
  );
}

export const TrendsMethodNote: React.FC<{ yearTotals?: Record<string, number | null>; caveats?: string[]; extra?: React.ReactNode }> = ({ yearTotals, caveats, extra }) => {
  const yt = yearTotals ? Object.entries(yearTotals).filter(([, v]) => v) : [];
  return (
    <>
      <p>
        Each subject's share is the number of papers that mention it in a year, divided by all AAAI and IJCAI main-track papers that year
        {yt.length ? ` (${yt[0][1]!.toLocaleString("en")} in ${yt[0][0]} rising to ${yt[yt.length - 1][1]!.toLocaleString("en")} in ${yt[yt.length - 1][0]})` : ""}. Shares correct for the conferences growing; raw counts do not.
      </p>
      <h3>Momentum</h3>
      <ul>
        <li>
          <b>Rising</b> or <b>Declining</b>: the share's straight-line trend over five years is clearly up or down (p ≤ 0.10 per subject, with no correction for testing many subjects).
        </li>
        <li>
          <b>Emerging</b>: barely present before 2023, then established.
        </li>
        <li>
          <b>Stable</b>: no clear trend. When a stable subject's share still moved by at least {MIN_CHANGE_POINTS} points and by a factor of {GREW_RATIO}, it is labelled <b>Grew, not consistently</b> or{" "}
          <b>Fell, not consistently</b>. That label is wording only; the analysis class stays Stable.
        </li>
      </ul>
      {extra && (
        <>
          <h3>Which subjects are shown</h3>
          {extra}
        </>
      )}
      <Caveats
        caveats={
          caveats || [
            "Only two venues (AAAI and IJCAI) are covered, so a trend is a trend in these proceedings, not in the field.",
            "Method, task and dataset labels were extracted from paper text and exist for only part of the papers, so shares are lower bounds.",
          ]
        }
      />
      <p className="muted">Extraction quality was checked by an AI reviewer (AI-assessed), not by human annotators. Intervals on About cover sampling error only.</p>
    </>
  );
};

export const TopicMethodNote: React.FC<{ source?: string | null; caveats?: string[] }> = ({ source, caveats }) => (
  <>
    <p>
      Share of papers is papers mentioning the subject divided by all papers that year. Leading groups are ranked by specialisation: how concentrated an organization's work is on this
      subject compared with all papers.{" "}
      {source === "precomputed" || source === "on_demand"
        ? "Here it is computed from a random walk on the full knowledge graph that restarts at this subject's papers, divided by each organization's overall importance (personalised PageRank lift)."
        : "Here it is the organization's share of papers on the subject divided by the share across all papers (relative concentration)."}
    </p>
    <p>
      Organizations with fewer than {MIN_ORG_PAPERS} papers on the subject, and researchers with fewer than {MIN_RESEARCHER_PAPERS}, are not ranked.
    </p>
    <h3>Related subjects</h3>
    <p>Counted from papers that mention both subjects. Two or more shared papers are needed to appear.</p>
    <h3>Top papers</h3>
    <p>Ordered by how often other papers in these proceedings cite them, which favours older papers.</p>
    <Caveats caveats={caveats} />
    <p className="muted">Extraction quality was checked by an AI reviewer (AI-assessed), not by human annotators.</p>
  </>
);
