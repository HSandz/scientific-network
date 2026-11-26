import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { navigatorApi } from "../../lib/navigatorApi";
import { navigate, pathFor } from "../../lib/router";
import { subjectName, orgName } from "../../lib/names";
import { fmtPct, readPalette, rowHue } from "../../lib/thermal";
import { displayMomentum, MIN_ORG_PAPERS, momentumSentence, MOMENTUM_WORD } from "../../config/display";
import { HeatCells } from "../charts/charts";
import { BarTrack, EntityDot, ErrorLine, InfoPopover, LoadingLine, MethodDrawer, MomentumChip, PageHead, Section } from "../ui/primitives";
import { Icon } from "../shell/icons";
import { TrendsMethodNote } from "./methodNotes";
import type { PulseStripRow } from "../../types/navigator";

const STARTERS = [
  "Which organizations collaborating with Tsinghua University increased their share of large-language-model papers after 2022?",
  "Which methods grew fastest as a share of AAAI and IJCAI papers from 2021 to 2025?",
  "Which tasks co-occur most with diffusion models, and what datasets are used with diffusion models?",
];

function band(cls: string) {
  return cls === "stable" ? 0 : cls === "declining" ? -1 : 1;
}

function joinNames(names: string[]): string {
  if (names.length <= 1) return names[0] || "";
  return `${names.slice(0, -1).join(", ")} and ${names[names.length - 1]}`;
}

/** One plain sentence from the data: the two fastest-heating and the two fastest-cooling subjects. */
export function pulseHeadline(strip: PulseStripRow[]): string {
  const heat = strip.filter((s) => s.class === "rising" || s.class === "emerging").slice(0, 2);
  const cool = strip
    .filter((s) => s.class === "declining")
    .slice(0, 2)
    .map((s) => subjectName(s.name, s.kind));
  const h = heat.map((s, i) => (i === 0 ? subjectName(s.name, s.kind) : subjectName(s.name, s.kind).replace(/^[A-Z](?=[a-z])/, (c) => c.toLowerCase())));
  const parts: string[] = [];
  if (h.length) parts.push(`${joinNames(h)} ${h.length > 1 ? "are" : "is"} heating fastest.`);
  if (cool.length) parts.push(`${joinNames(cool.map((c, i) => (i === 0 ? c : c.replace(/^[A-Z](?=[a-z])/, (x) => x.toLowerCase()))))} ${cool.length > 1 ? "are" : "is"} cooling.`);
  return parts.join(" ");
}

const StripRow: React.FC<{ s: PulseStripRow; years: string[] }> = ({ s, years }) => {
  const p = readPalette();
  const hue = rowHue(s.t, p);
  const disp = displayMomentum(s.class, s.share);
  const first = s.share[0] * 100;
  const last = s.share[s.share.length - 1] * 100;
  const name = subjectName(s.name, s.kind);
  const sentence = momentumSentence(s.class, s.share);
  return (
    <button
      type="button"
      className="strip-row"
      onClick={() => navigate(pathFor("topics", s.id))}
      aria-label={`${name}, ${s.kind.toLowerCase()}. ${sentence}.`}
      data-testid="strip-row"
    >
      <span className="s-name">
        <EntityDot kind={s.kind} />
        <span>{name}</span>
      </span>
      <HeatCells shares={s.share.map((x) => x * 100)} hue={hue} years={years} papers={s.papers} />
      <span className="s-label">
        <MomentumChip cls={s.class} t={s.t} label={MOMENTUM_WORD[disp]} title={sentence} />
      </span>
      <span className="s-change">
        <span className="from">{fmtPct(first)}</span> → <b>{fmtPct(last)}</b>
      </span>
    </button>
  );
};

export const PulsePage: React.FC = () => {
  const pulse = useQuery({ queryKey: ["nav-pulse"], queryFn: ({ signal }) => navigatorApi.getPulse(signal), staleTime: 600_000 });
  const [q, setQ] = useState("");
  const data = pulse.data;
  const years = (data?.years || [2021, 2022, 2023, 2024, 2025]).map(String);
  const sw = data?.smallworld;

  return (
    <div className="view" data-testid="page-pulse">
      <PageHead
        title="What's heating up in AI research"
        sub="AAAI and IJCAI, 2021–2025"
        lede={data ? <span data-testid="pulse-headline">{pulseHeadline(data.strip)}</span> : undefined}
      />
      {pulse.isLoading && <LoadingLine />}
      {pulse.isError && <ErrorLine error={pulse.error} onRetry={() => pulse.refetch()} />}
      {data && (
        <>
          <div className="pulse-grid">
            <section className="strip" aria-labelledby="strip-h" data-testid="thermal-strip" data-chart-label="Pulse thermal strip" data-chart-rendered="true" data-chart-point-count={data.strip.length * 5}>
              <h2 className="sr-only" id="strip-h">
                Subjects by momentum
              </h2>
              <div className="strip-head" aria-hidden="true">
                <span>Subject</span>
                {years.map((y) => (
                  <span key={y} className="yr" data-short={`’${y.slice(2)}`}>
                    {y}
                  </span>
                ))}
                <span className="lab">Momentum</span>
                <span className="r">Share of papers</span>
              </div>
              {data.strip.map((s, i) => (
                <React.Fragment key={s.id}>
                  {i > 0 && band(s.class) !== band(data.strip[i - 1].class) && <div className="strip-divider" aria-hidden="true" />}
                  <StripRow s={s} years={years} />
                </React.Fragment>
              ))}
              <div className="strip-legend">
                <span>Cooling</span>
                <span className="scale" aria-hidden="true" />
                <span>Heating</span>
                <span>Darker cell means a larger share that year.</span>
                <span className="strip-legend-end">
                  <MethodDrawer testId="pulse-how">
                    <TrendsMethodNote yearTotals={data.year_totals} caveats={data.caveats} extra={<p>{data.selection_rule}</p>} />
                  </MethodDrawer>
                </span>
              </div>
            </section>
            <aside className="side">
              <section className="askbox" aria-labelledby="ab-h">
                <h2 id="ab-h">Ask the graph</h2>
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    if (q.trim()) navigate(`${pathFor("ask")}?q=${encodeURIComponent(q.trim())}`);
                  }}
                >
                  <label className="sr-only" htmlFor="pulse-ask">
                    Your question
                  </label>
                  <input id="pulse-ask" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Ask a question…" data-testid="pulse-ask-input" />
                  <button className="send" aria-label="Ask" type="submit">
                    <Icon name="send" size={18} strokeWidth={2} />
                  </button>
                </form>
                <div className="starters">
                  {STARTERS.map((s) => (
                    <button key={s} type="button" className="starter" onClick={() => navigate(`${pathFor("ask")}?q=${encodeURIComponent(s)}`)}>
                      {s}
                    </button>
                  ))}
                </div>
              </section>
              {sw && (
                <section className="smallworld" aria-labelledby="sw-h" data-testid="pulse-smallworld">
                  <h2 id="sw-h">Is it a small world?</h2>
                  <p className="yes">{sw.holds ? "Yes." : "Not quite."}</p>
                  <p>
                    Co-authors form tight clusters, yet any two researchers in the main network are about {Math.round(sw.L || 0)} steps apart. Against shuffled networks of the same size that scores{" "}
                    {Math.round(sw.sigma_rewired || 0).toLocaleString("en")} on the small-world test, where anything above 1 counts.
                  </p>
                  <a
                    className="textlink"
                    href={pathFor("network")}
                    onClick={(e) => {
                      e.preventDefault();
                      navigate(pathFor("network"));
                    }}
                  >
                    See the network
                  </a>
                </section>
              )}
            </aside>
          </div>

          <Section
            id="leaders"
            title="Who leads the rising topics"
            hint={
              <>
                The three organizations most concentrated on each subject, compared with their overall output.
                <InfoPopover label="What is specialisation?">
                  <p>
                    <b>Specialisation</b> compares how much of an organization's work is on a subject with how much of all papers are. 3× means three times the average.
                  </p>
                  <p>Only organizations with at least {data.thresholds.min_org_papers || MIN_ORG_PAPERS} papers on the subject are ranked, so one-off papers do not lead.</p>
                </InfoPopover>
              </>
            }
          >
            <div className="leaders">
              {data.leaders.map((l) => {
                const max = Math.max(...l.organizations.map((o) => o.specialisation), 0.0001);
                return (
                  <button key={l.id} type="button" className="leader" onClick={() => navigate(pathFor("topics", l.id))} data-testid="leader-card">
                    <h3>{subjectName(l.name, l.kind)}</h3>
                    {l.organizations.length ? (
                      <ol>
                        {l.organizations.map((o) => (
                          <li key={o.id}>
                            <div>{orgName(o.name)}</div>
                            <div className="val">
                              {o.specialisation.toFixed(1)}× average, {o.subject_papers} papers
                            </div>
                            <BarTrack value={o.specialisation} max={max} />
                          </li>
                        ))}
                      </ol>
                    ) : (
                      <p className="val">No organization has {data.thresholds.min_org_papers} or more papers on it yet.</p>
                    )}
                  </button>
                );
              })}
            </div>
          </Section>
        </>
      )}
    </div>
  );
};
