import React from "react";
import { useQuery } from "@tanstack/react-query";
import { navigatorApi } from "../../lib/navigatorApi";
import { navigate, pathFor } from "../../lib/router";
import { displayName, orgName, plural, subjectName } from "../../lib/names";
import { paperMeta, usePapers } from "../../lib/usePapers";
import { fmtPct, momentumT } from "../../lib/thermal";
import { displayMomentum, momentumSentence, MOMENTUM_WORD } from "../../config/display";
import { useExplorerStore } from "../../stores/useExplorerStore";
import type { NodeProfileResponse } from "../../types/navigator";
import { CopyIdButton, EntityDot, ErrorLine, LoadingLine, MomentumChip, PageHead, Section } from "../ui/primitives";
import { countryName } from "./GroupsPage";
import { YearBars } from "./YearBars";

interface Node360PageProps {
  nodeId: string | null;
  onSelectNode: (id: string) => void;
  onShowInExplore: (id: string, name?: string) => void;
}

const SUBJECTS = ["Topic", "Method", "Task", "Dataset"];
const EXPLORABLE = ["Researcher", "Organization", "Paper"];

/** Plain headings for each relation, read from this node's side: [outgoing, incoming]. */
const RELATIONS: Record<string, [string, string]> = {
  AUTHORED: ["Papers written", "Authors"],
  AFFILIATED_WITH: ["Affiliations", "Affiliated researchers"],
  PUBLISHED_IN: ["Published in", "Papers published here"],
  CITES: ["Cites", "Cited by"],
  HAS_TOPIC: ["Topics", "Papers on this topic"],
  SUBTOPIC_OF: ["Part of the topic", "Narrower topics"],
  COAUTHORED_WITH: ["Co-authors", "Co-authors"],
  COLLABORATED_WITH: ["Collaborating organizations", "Collaborating organizations"],
  RESEARCHES_TOPIC: ["Researches", "Researchers on this topic"],
  CONTRIBUTES_TO_TOPIC: ["Contributes to", "Contributing organizations"],
  USES_METHOD: ["Methods used", "Papers using it"],
  ADDRESSES_TASK: ["Tasks addressed", "Papers addressing it"],
  USES_DATASET: ["Datasets used", "Papers using it"],
  PART_OF: ["Part of", "Units"],
};
const heading = (relation: string, outgoing: boolean) => RELATIONS[relation]?.[outgoing ? 0 : 1] || relation.replace(/_/g, " ").toLowerCase();

const HOW_KNOWN: Record<string, string> = {
  observed: "Recorded in publication data",
  extracted: "Extracted from paper text by a language model (AI-generated)",
  inferred_topic: "Topic assigned automatically",
  curated_taxonomy: "Fixed topic hierarchy",
  derived: "Counted from other links",
  alignment: "Matched to an external record",
};
const howKnown = (kind: string | null) => (kind ? HOW_KNOWN[kind] || kind.replace(/_/g, " ") : "Not recorded");

const nameOf = (label: string, name: string) => (label === "Organization" ? orgName(name) : SUBJECTS.includes(label) ? subjectName(name, label) : name);

const RANK_SCOPE: Record<string, string> = {
  N1: "in the co-authorship network",
  N2: "in organization collaboration",
  N3: "in citations between papers",
  N4: "in the full knowledge graph",
};

function describe(d: NodeProfileResponse, papers: number, authors: string): string {
  const props = d.properties as Record<string, any>;
  if (d.label === "Researcher") {
    const orgs = d.neighbors.filter((n) => n.relation === "AFFILIATED_WITH" && n.name).map((n) => orgName(n.name!));
    return `Researcher${orgs.length ? ` who has listed ${orgs.slice(0, 2).join(" and ")}${orgs.length > 2 ? " among others" : ""}` : ""}.`;
  }
  if (d.label === "Paper") return authors || (props.year ? `Paper from ${props.year}.` : "Paper.");
  if (d.label === "Organization") return `Organization${props.country_code ? ` in ${countryName(String(props.country_code))}` : ""}.`;
  if (SUBJECTS.includes(d.label)) return `${d.label} mentioned in ${plural(papers, "paper")}.`;
  return `${d.label}.`;
}

const Profile: React.FC<{ d: NodeProfileResponse; onSelectNode: (id: string) => void; onShowInExplore: (id: string, name?: string) => void }> = ({ d, onSelectNode, onShowInExplore }) => {
  const props = d.properties as Record<string, any>;
  const isPaper = d.label === "Paper";
  const own = usePapers(isPaper ? [d.id] : []);
  const paper = own.data?.[d.id];
  const listed = d.papers.slice(0, 8);
  const listedMeta = usePapers(listed.map((p) => p.paper_id));
  const yearly = isPaper ? [] : d.sparkline;
  const total = d.trend?.total_papers ?? yearly.reduce((a, b) => a + b.papers, 0);
  const name = nameOf(d.label, displayName(d.name, d.label));

  const best = Object.entries(d.metrics || {})
    .filter(([, m]) => typeof m.rank === "number")
    .sort(([a], [b]) => a.localeCompare(b))[0];
  const shares = d.trend?.yearly.map((y) => y.share) || [];

  const groups = new Map<string, NodeProfileResponse["neighbors"]>();
  for (const n of d.neighbors) {
    // The Papers section already lists this node's papers.
    if (listed.length > 0 && n.label === "Paper") continue;
    const key = heading(n.relation, n.outgoing);
    groups.set(key, [...(groups.get(key) || []), n]);
  }
  const evidence = new Map<string, number>();
  d.neighbors.forEach((n) => evidence.set(n.evidence_kind || "", (evidence.get(n.evidence_kind || "") || 0) + 1));
  const link = typeof props.official_url === "string" ? props.official_url : null;
  const detailPage = SUBJECTS.includes(d.label) ? pathFor("topics", d.id) : d.label === "Organization" ? pathFor("groups", d.id) : null;
  const authorLine = paper ? paperMeta(paper) : "";

  return (
    <article>
      <header className="profile-head">
        <div className="topic-kind">
          <EntityDot kind={d.label} />
          <span>{d.label}</span>
          {d.trend && <MomentumChip cls={d.trend.class} t={momentumT(d.trend.slope_of_share, Math.abs(d.trend.slope_of_share) || 1, d.trend.class)} label={MOMENTUM_WORD[displayMomentum(d.trend.class, shares)]} title={momentumSentence(d.trend.class, shares)} />}
        </div>
        <h1 className={isPaper ? "paper-title" : ""} data-testid="node-name">
          {name}
        </h1>
        <p className="sub">{describe(d, total, authorLine)}</p>
        <div className="profile-actions">
          {detailPage && (
            <button type="button" className="chip-btn" onClick={() => navigate(detailPage)}>
              {d.label === "Organization" ? "Open the organization profile" : "Open the full topic page"}
            </button>
          )}
          {link && (
            <a className="chip-btn" href={link} target="_blank" rel="noreferrer">
              Read at the publisher
            </a>
          )}
          {EXPLORABLE.includes(d.label) && (
            <button type="button" className="chip-btn" onClick={() => onShowInExplore(d.id, d.name)}>
              Show in Explore
            </button>
          )}
        </div>
      </header>

      <dl className="stats">
        {isPaper ? (
          <>
            {props.year && (
              <div>
                <dt>Year</dt>
                <dd>{String(props.year)}</dd>
              </div>
            )}
            {paper && (
              <>
                <div>
                  <dt>Authors</dt>
                  <dd>{paper.n_authors}</dd>
                </div>
                <div>
                  <dt>Citations from these proceedings</dt>
                  <dd>{paper.in_corpus_citations}</dd>
                </div>
              </>
            )}
          </>
        ) : (
          d.activity_basis !== "unavailable" &&
          total > 0 && (
            <div>
              <dt>Papers</dt>
              <dd>{total.toLocaleString("en")}</dd>
            </div>
          )
        )}
        {best && (
          <div>
            <dt>Influence rank {RANK_SCOPE[best[0]] || ""}</dt>
            <dd>{best[1].rank!.toLocaleString("en")}</dd>
          </div>
        )}
        {d.trend && shares.length > 1 && (
          <div>
            <dt>Share of papers, {d.trend.yearly[0].year} to {d.trend.yearly[shares.length - 1].year}</dt>
            <dd>
              {fmtPct(shares[0] * 100)} → {fmtPct(shares[shares.length - 1] * 100)}
            </dd>
          </div>
        )}
      </dl>

      {yearly.some((y) => y.papers > 0) && (
        <Section id="activity" title="Activity" hint={d.activity_basis === "paper_affiliation" ? "Papers each year on which an author listed this organization." : "Papers each year."}>
          <YearBars label="Papers per year" data={yearly} />
        </Section>
      )}

      {d.description && d.description.source_kind !== "template_from_graph_metadata" && (
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

      {listed.length > 0 && (
        <Section id="papers" title="Papers" hint={total > listed.length ? `${listed.length} of ${total.toLocaleString("en")}.` : undefined}>
          <ol className="toppapers">
            {listed.map((p) => (
              <li key={p.paper_id} className="paper-ref">
                <button type="button" className="t paperlink" onClick={() => onSelectNode(p.paper_id)}>
                  {p.title}
                </button>
                <span className="meta">{paperMeta(listedMeta.data?.[p.paper_id]) || `${p.venue || ""} ${p.year || ""}`}</span>
              </li>
            ))}
          </ol>
        </Section>
      )}

      {groups.size > 0 && (
        <Section id="connections" title="Connections" hint={d.neighbors.length >= 45 ? "The first 45 connections. Explore shows more." : undefined}>
          {[...groups.entries()].map(([title, rows]) => (
            <div key={title} className="chipset">
              <h3>{title}</h3>
              <div className="chips">
                {rows.map((n, i) => (
                  <button key={`${n.id}-${i}`} type="button" className="echip echip-long" onClick={() => onSelectNode(n.id)} data-testid="node-connection">
                    <EntityDot kind={n.label} />
                    <span>{nameOf(n.label, n.name || displayName(n.id, n.label))}</span>
                  </button>
                ))}
              </div>
            </div>
          ))}
        </Section>
      )}

      {d.neighbors.length > 0 && (
        <Section id="evidence" title="How these connections are known">
          <ul className="plain-list">
            {[...evidence.entries()].map(([kind, n]) => (
              <li key={kind}>
                <span>{howKnown(kind || null)}</span>
                <span className="muted">{plural(n, "connection")}</span>
              </li>
            ))}
          </ul>
          <details className="map-all">
            <summary>Evidence for each connection</summary>
            <div className="table-scroll">
              <table className="data">
                <thead>
                  <tr>
                    <th>Connection</th>
                    <th>To</th>
                    <th>How it is known</th>
                    <th className="num">Supporting papers</th>
                  </tr>
                </thead>
                <tbody>
                  {d.neighbors.map((n, i) => (
                    <tr key={`${n.id}-${i}`}>
                      <td>{heading(n.relation, n.outgoing)}</td>
                      <td>{nameOf(n.label, n.name || displayName(n.id, n.label))}</td>
                      <td>{howKnown(n.evidence_kind)}</td>
                      <td className="num">{n.support_count ?? "–"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
        </Section>
      )}

      <details className="all-data" data-testid="node-all-data">
        <summary>All data</summary>
        <dl className="kv">
          {Object.entries(props)
            .filter(([k]) => k !== "_label")
            .map(([k, v]) => (
              <React.Fragment key={k}>
                <dt>{k}</dt>
                <dd>{typeof v === "object" ? JSON.stringify(v) : String(v)}</dd>
              </React.Fragment>
            ))}
          {Object.entries(d.metrics || {}).map(([net, m]) => (
            <React.Fragment key={net}>
              <dt>Ranking {RANK_SCOPE[net] || net}</dt>
              <dd>{JSON.stringify(m)}</dd>
            </React.Fragment>
          ))}
          {d.description?.source_kind === "template_from_graph_metadata" && (
            <>
              <dt>{d.description.label}</dt>
              <dd>{d.description.text}</dd>
            </>
          )}
        </dl>
        <CopyIdButton id={d.id} />
      </details>
    </article>
  );
};

export const Node360Page: React.FC<Node360PageProps> = ({ nodeId, onSelectNode, onShowInExplore }) => {
  const setSearchModalOpen = useExplorerStore((s) => s.setSearchModalOpen);
  const q = useQuery({
    queryKey: ["nav-node360", nodeId],
    queryFn: ({ signal }) => navigatorApi.getNode360(nodeId!, signal),
    enabled: Boolean(nodeId),
  });
  return (
    <div data-testid="page-node360">
      {!nodeId ? (
        <>
          <PageHead title="Profiles" sub="Every paper, researcher, organization and subject has one." />
          <p>
            <button type="button" className="chip-btn" onClick={() => setSearchModalOpen(true)}>
              Search for one
            </button>
          </p>
        </>
      ) : (
        <>
          {q.isLoading && <LoadingLine />}
          {q.isError && <ErrorLine error={q.error} onRetry={() => q.refetch()} />}
          {q.data && <Profile key={q.data.id} d={q.data} onSelectNode={onSelectNode} onShowInExplore={onShowInExplore} />}
        </>
      )}
    </div>
  );
};
