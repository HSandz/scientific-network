import React from "react";
import { useQuery } from "@tanstack/react-query";
import { navigatorApi } from "../../lib/navigatorApi";
import { navigate, pathFor } from "../../lib/router";
import { communityTitle, orgName, subjectName } from "../../lib/names";
import { fmtPct, momentumT } from "../../lib/thermal";
import { cleanCommunityRefs } from "../../lib/askModel";
import { paperMeta, usePapers } from "../../lib/usePapers";
import { displayMomentum, MIN_RESEARCHER_PAPERS, momentumSentence, MOMENTUM_WORD } from "../../config/display";
import type { SubjectDetailResponse } from "../../types/navigator";
import { LineChart } from "../charts/charts";
import { AppLink, BarTrack, EntityDot, ErrorLine, InfoPopover, LoadingLine, MethodDrawer, MomentumChip, Section } from "../ui/primitives";
import { TopicMethodNote } from "./methodNotes";
import { TopicsIndex } from "./TopicsIndex";

interface SubjectPageProps {
  /** null shows the index of all topics, methods, tasks and datasets. */
  subjectId: string | null;
  onSelectSubject: (id: string) => void;
  onOpenGroup: (orgId: string) => void;
  onOpenCommunity: (cid: string) => void;
  onOpenNode360: (nodeId: string) => void;
}

const KIND_PLURAL: Record<string, string> = { Method: "Methods", Task: "Tasks", Dataset: "Datasets" };

const lower = (s: string) => s.replace(/^[A-Z](?=[a-z])/, (c) => c.toLowerCase());
const isPlural = (name: string) => /(?:[^siu])s$/.test(name);

/** One sentence that answers "what is happening to this subject?" from its yearly shares. */
function heroSentence(name: string, kind: string, cls: string, shares: number[], fastest: boolean): string {
  const a = fmtPct(shares[0] * 100);
  const b = fmtPct(shares[shares.length - 1] * 100);
  const many = isPlural(name);
  const is = many ? "are" : "is";
  const has = many ? "have" : "has";
  const range = `${a} → ${b} of papers`;
  switch (displayMomentum(cls, shares)) {
    case "rising":
      return fastest ? `${name} ${is} the fastest-rising ${kind.toLowerCase()}: ${range}` : `${name} ${is} rising: ${range}`;
    case "emerging":
      return fastest ? `${name} ${is} the fastest-emerging ${kind.toLowerCase()}: ${range}` : `${name} ${has} emerged: ${range}`;
    case "declining":
      return `${name} ${is} cooling: ${range}`;
    case "grew-unsteady":
      return `${name} grew from ${a} to ${b} of papers, but not consistently`;
    case "fell-unsteady":
      return `${name} fell from ${a} to ${b} of papers, but not consistently`;
    default:
      return `${name} ${has} no clear trend: ${range}`;
  }
}

function aliasesOf(d: SubjectDetailResponse): string[] {
  const own = new Set([d.name.toLowerCase(), subjectName(d.name, d.kind).toLowerCase()]);
  return d.display_aliases.filter((a) => !own.has(a.toLowerCase()));
}

/** Related subjects with shared-paper counts when the live graph supplies them. */
function relatedSets(d: SubjectDetailResponse) {
  // The name's own acronym (for example "LLMs") is not shown as a related subject.
  const acronym = d.name.match(/\(([^)]+)\)\s*$/)?.[1]?.toLowerCase();
  const own = new Set([d.name.toLowerCase(), ...d.display_aliases.map((a) => a.toLowerCase()), ...(acronym ? [acronym] : [])]);
  return (["Method", "Task", "Dataset"] as const)
    .map((kind) => {
      const fallback = { Method: d.related_methods, Task: d.related_tasks, Dataset: d.related_datasets }[kind];
      const rows: Array<{ id: string; name: string; co_papers?: number }> = d.co_mentions ? d.co_mentions[kind] : fallback;
      return { kind, rows: rows.filter((r) => r.id !== d.id && !own.has(r.name.toLowerCase())).slice(0, 8) };
    })
    .filter((s) => s.rows.length);
}

const Detail: React.FC<{ d: SubjectDetailResponse; onSelectSubject: (id: string) => void; onOpenGroup: (id: string) => void; onOpenCommunity: (id: string) => void; onOpenNode360: (id: string) => void }> = ({
  d,
  onSelectSubject,
  onOpenGroup,
  onOpenCommunity,
  onOpenNode360,
}) => {
  const kind = d.kind;
  const name = subjectName(d.name, kind);
  const trend = d.trend;
  const yearly = trend?.yearly || [];
  const shares = yearly.map((y) => y.share);

  // The slope scale and the "fastest" claim come from the same leaderboards the Trends page shows.
  const board = useQuery({
    queryKey: ["nav-trends", kind, "all", "2021-2025", ""],
    queryFn: ({ signal }) => navigatorApi.getTrends({ kind: kind as "Method", venue: "all", period: "2021-2025", q: "", limit: 200 }, signal),
    staleTime: 600_000,
    enabled: Boolean(trend),
  });
  const maxSlope = Math.max(Math.abs(trend?.slope_of_share || 0), ...(board.data?.items || []).map((r) => Math.abs(r.slope_of_share)), 0.000001);
  const t = trend ? momentumT(trend.slope_of_share, maxSlope, trend.class) : 0;
  const heating = board.data ? [...board.data.leaderboards.rising, ...board.data.leaderboards.emerging].sort((a, b) => b.slope_of_share - a.slope_of_share) : [];
  const fastest = heating[0]?.id === d.id;

  const papers = d.most_cited_papers.slice(0, 5);
  // Each paper cited by the community report is listed, and numbered, once.
  const reportPaperIds = [...new Set((d.summary?.source_community_id ? d.summary.findings : []).flatMap((f) => f.paper_ids.slice(0, 2)))];
  const meta = usePapers([...papers.map((x) => x.paper_id), ...reportPaperIds]);
  const related = relatedSets(d);
  const groups = d.leading_groups;
  const maxSpec = Math.max(...groups.map((g) => g.specialisation), 0.0001);
  const researchers = d.researcher_evidence;
  const aliases = aliasesOf(d);
  const lastYear = yearly[yearly.length - 1];

  /* "In brief": sentences written from the counts on this page, each footnoted to its source. */
  const topMethod = related.find((s) => s.kind === "Method")?.rows[0];
  const topTask = related.find((s) => s.kind === "Task")?.rows[0];
  const cite = papers[0];
  const together = [topMethod && `the method ${lower(subjectName(topMethod.name, "Method"))}`, topTask && `the task ${lower(subjectName(topTask.name, "Task"))}`].filter(Boolean);

  return (
    <article>
      <AppLink to="/topics" className="textlink back-link">
        ‹ All topics
      </AppLink>
      <header className="topic-hero">
        <div className="topic-kind">
          <EntityDot kind={kind} />
          <span>{kind}</span>
          {trend && <MomentumChip cls={trend.class} t={t} label={MOMENTUM_WORD[displayMomentum(trend.class, shares)]} title={momentumSentence(trend.class, shares)} />}
        </div>
        <h1 data-testid="topic-headline">{trend && shares.length ? heroSentence(name, kind, trend.class, shares, fastest) : name}</h1>
        <p className="sub">
          {trend ? (
            <>
              {trend.total_papers.toLocaleString("en")} papers in AAAI and IJCAI, 2021–2025.{lastYear ? ` ${lastYear.papers.toLocaleString("en")} of them appeared in ${lastYear.year}.` : ""}
            </>
          ) : (
            "Too few papers for a yearly trend."
          )}
          {aliases.length ? ` Also written as ${aliases.slice(0, 3).join(", ")}.` : ""}
        </p>
      </header>

      {trend && (
        <div className="topic-chart">
          <LineChart label="Subject annual share chart" years={yearly.map((y) => String(y.year))} unit="pct" hero series={[{ name, values: shares.map((x) => x * 100), t }]} />
          <div className="chart-foot chart-foot-start">
            <span>Share of all papers each year</span>
            <MethodDrawer testId="topic-how">
              <TopicMethodNote source={d.ppr_source} />
            </MethodDrawer>
          </div>
        </div>
      )}

      <div className="topic-columns">
        <Section id="groups" title="Leading groups">
          <p className="hint">
            Organizations most concentrated on this subject.
            <InfoPopover label="How are groups ranked?" testId="groups-info">
              <p>
                <b>Specialisation</b> compares the share of an organization's papers on this subject with the share across all papers. 3× means three times the average.
              </p>
              <p>
                Organizations need at least {d.min_org_papers} papers on the subject to be ranked. Researchers need at least {researchers?.min_papers || MIN_RESEARCHER_PAPERS}.
              </p>
            </InfoPopover>
          </p>
          {groups.length ? (
            <ol className="leadlist" data-chart-label="Leading groups specialisation" data-chart-rendered="true" data-chart-point-count={groups.length}>
              {groups.map((g) => (
                <li key={g.id}>
                  <div>
                    <button type="button" className="rowlink" onClick={() => onOpenGroup(g.id)}>
                      {orgName(g.name)}
                    </button>
                    <small>
                      {g.subject_papers} of {g.total_papers.toLocaleString("en")} papers
                    </small>
                  </div>
                  <BarTrack value={g.specialisation} max={maxSpec} />
                  <b className="spec">{g.specialisation.toFixed(1)}×</b>
                </li>
              ))}
            </ol>
          ) : (
            <p className="note">No organization has {d.min_org_papers} or more papers on this subject, so none are ranked.</p>
          )}
          {researchers &&
            (researchers.ranked.length ? (
              <div className="researchers" data-testid="topic-researchers">
                <h3>Researchers with {researchers.min_papers} or more papers on it</h3>
                <div className="chips">
                  {researchers.ranked.map((r) => (
                    <button key={r.id} type="button" className="echip" onClick={() => onOpenNode360(r.id)}>
                      <EntityDot kind="Researcher" />
                      {r.name} <span className="c">{r.subject_papers}</span>
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <p className="note" data-testid="topic-researchers">
                No researcher has {researchers.min_papers} or more papers on this subject yet (the most is {researchers.max_papers}), so individuals are not ranked.
              </p>
            ))}
        </Section>

        <Section id="together" title="Often found together" hint={`Subjects that share papers with ${lower(name)}.`}>
          {related.length ? (
            related.map((set) => (
              <div key={set.kind} className="chipset">
                <h3>
                  <EntityDot kind={set.kind} />
                  {KIND_PLURAL[set.kind]}
                </h3>
                <div className="chips">
                  {set.rows.map((r) => (
                    <button key={r.id} type="button" className="echip" onClick={() => onSelectSubject(r.id)} title={r.co_papers ? `${r.co_papers} shared papers` : undefined}>
                      <EntityDot kind={set.kind} />
                      {subjectName(r.name, set.kind)}
                      {r.co_papers ? <span className="c">{r.co_papers}</span> : null}
                    </button>
                  ))}
                </div>
              </div>
            ))
          ) : (
            <p className="note">No other subject shares two or more papers with it.</p>
          )}
        </Section>
      </div>

      {trend && (
        <Section id="brief" title="In brief">
          <p className="prose" data-testid="topic-brief">
            {name} {isPlural(name) ? "appear" : "appears"} in {trend.total_papers.toLocaleString("en")} papers across the five years
            {lastYear ? `, and ${lastYear.papers.toLocaleString("en")} of them are from ${lastYear.year}` : ""}.
            <sup>
              <a href="#cite-1">1</a>
            </sup>
            {together.length ? ` The subjects that most often share a paper with ${isPlural(name) ? "them" : "it"} are ${together.join(" and ")}.` : ""}
            {groups[0] ? ` The most specialised group is ${orgName(groups[0].name)}, with ${groups[0].subject_papers} of its ${groups[0].total_papers.toLocaleString("en")} papers on the subject.` : ""}
            {cite && cite.in_corpus_citations > 0 ? (
              <>
                {" "}
                The most-cited paper on it inside these proceedings is “{cite.title}”.
                <sup>
                  <a href="#cite-2">2</a>
                </sup>
              </>
            ) : null}
          </p>
          <ol className="sources">
            <li id="cite-1">
              <b>Yearly paper counts</b>
              <span className="meta">{yearly.map((y) => `${y.year}: ${y.papers}`).join(", ")}</span>
            </li>
            {cite && cite.in_corpus_citations > 0 && (
              <li id="cite-2" className="paper-ref">
                <button type="button" className="t paperlink" onClick={() => onOpenNode360(cite.paper_id)}>
                  {cite.title}
                </button>
                <span className="meta">{paperMeta(meta.data?.[cite.paper_id]) || `${cite.venue || ""} ${cite.year}`}</span>
              </li>
            )}
          </ol>
          <p className="note">Written from the counts on this page, not by a language model.</p>
        </Section>
      )}

      {d.description && (
        <Section id="what" title="What it is">
          <p className="prose">{d.description.text}</p>
          <p className="note">
            {d.description.source_kind === "wikipedia" ? (
              <>
                From{" "}
                <a className="textlink" href={d.description.wikipedia_url || undefined} target="_blank" rel="noreferrer">
                  Wikipedia
                </a>
                {d.description.wikipedia_revision_id ? ` (revision ${d.description.wikipedia_revision_id})` : ""}, licensed {d.description.license || "CC BY-SA 4.0"}.
              </>
            ) : (
              `${d.description.label}. AI-generated text can be wrong.`
            )}
          </p>
        </Section>
      )}

      {d.summary?.source_community_id && (
        <Section id="community" title="The research community around it" hint="A report written by a language model about the group of papers and people that includes this subject. It covers more than the subject itself.">
          <p className="prose">{cleanCommunityRefs(d.summary.text)}</p>
          {d.summary.findings.length > 0 && (
            <ul className="findings">
              {d.summary.findings.map((f, i) => (
                <li key={i}>
                  {cleanCommunityRefs(f.claim)}
                  {f.paper_ids.slice(0, 2).map((pid) => (
                    <button
                      key={pid}
                      type="button"
                      className="fnref"
                      onClick={() => onOpenNode360(pid)}
                      title={meta.data?.[pid]?.title || "Open the paper"}
                      aria-label={`Source ${reportPaperIds.indexOf(pid) + 1}: ${meta.data?.[pid]?.title || "paper"}`}
                    >
                      {reportPaperIds.indexOf(pid) + 1}
                    </button>
                  ))}
                </li>
              ))}
            </ul>
          )}
          {reportPaperIds.length > 0 && (
            <ol className="sources">
              {reportPaperIds.map((pid) => (
                <li key={pid} className="paper-ref">
                  <button type="button" className="t paperlink" onClick={() => onOpenNode360(pid)}>
                    {meta.data?.[pid]?.title || "Loading title…"}
                  </button>
                  <span className="meta">{paperMeta(meta.data?.[pid])}</span>
                </li>
              ))}
            </ol>
          )}
          <p className="note">{d.summary.label}.</p>
          {d.communities.some((c) => communityTitle(c.title)) && (
            <div className="chips">
              {d.communities
                .filter((c) => communityTitle(c.title))
                .slice(0, 4)
                .map((c) => (
                  <button key={c.community_id} type="button" className="chip-btn" onClick={() => onOpenCommunity(c.community_id)}>
                    {communityTitle(c.title)}
                  </button>
                ))}
            </div>
          )}
        </Section>
      )}

      {papers.length > 0 && (
        <Section id="papers" title="Top papers" hint="Ordered by citations from other papers in these proceedings.">
          <ol className="toppapers">
            {papers.map((x) => (
              <li key={x.paper_id} className="paper-ref">
                <button type="button" className="t paperlink" onClick={() => onOpenNode360(x.paper_id)}>
                  {x.title}
                </button>
                <span className="meta">
                  {paperMeta(meta.data?.[x.paper_id]) || `${x.venue || ""} ${x.year}`}. Cited {x.in_corpus_citations} {x.in_corpus_citations === 1 ? "time" : "times"} in these proceedings.
                </span>
              </li>
            ))}
          </ol>
        </Section>
      )}
    </article>
  );
};

export const SubjectPage: React.FC<SubjectPageProps> = ({ subjectId, ...nav }) => {
  const q = useQuery({
    queryKey: ["nav-subject-detail", subjectId],
    queryFn: ({ signal }) => navigatorApi.getSubjectDetail(subjectId!, signal),
    enabled: Boolean(subjectId),
  });
  return (
    <div data-testid="page-subjects">
      {!subjectId ? (
        <TopicsIndex onSelect={(id) => navigate(pathFor("topics", id))} />
      ) : (
        <>
          {q.isLoading && <LoadingLine />}
          {q.isError && <ErrorLine error={q.error} onRetry={() => q.refetch()} />}
          {q.data && <Detail key={q.data.id} d={q.data} {...nav} />}
        </>
      )}
    </div>
  );
};
