import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { navigatorApi } from "../../lib/navigatorApi";
import { navigate, pathFor } from "../../lib/router";
import { orgName, plural, subjectName } from "../../lib/names";
import { paperMeta, usePapers } from "../../lib/usePapers";
import { MIN_ORG_PAPERS } from "../../config/display";
import type { GroupDetailResponse, GroupsResponse } from "../../types/navigator";
import { BarTrack, CopyIdButton, EntityDot, ErrorLine, InfoPopover, LoadingLine, MethodDrawer, PageHead, Section } from "../ui/primitives";
import { GroupMatrix } from "./GroupMatrix";

interface GroupsPageProps {
  /** From the path; on wide screens the largest organization is shown when empty. */
  selectedGroupId: string | null;
  onSelectGroup: (id: string) => void;
  onOpenNode360: (id: string) => void;
}

const regionNames = typeof Intl !== "undefined" && "DisplayNames" in Intl ? new Intl.DisplayNames(["en"], { type: "region" }) : null;
export function countryName(code: string | null | undefined): string {
  if (!code) return "";
  try {
    return regionNames?.of(code) || code;
  } catch {
    return code;
  }
}
const sectorWord = (s: string) => (s === "unknown" ? "Not classified" : s.charAt(0).toUpperCase() + s.slice(1));
const PAGE = 40;

const GroupsMethodNote: React.FC<{ exclusion?: string }> = ({ exclusion }) => (
  <>
    <p>
      An organization's papers are the AAAI and IJCAI 2021–2025 main-track papers where an author listed it as an affiliation on that paper. Current profiles are never used as past
      affiliations.
    </p>
    <p>
      <b>Specialisation</b> compares the share of an organization's papers on a subject with the share across all papers. 3× means three times the average. Organizations need at least{" "}
      {MIN_ORG_PAPERS} papers on a subject before it counts as a specialisation.
    </p>
    <p>
      <b>Notable</b> marks organizations with enough papers to compare, as set by the analysis. <b>Organization type</b> is the type recorded in Wikidata and can look odd, for example
      "government" for a national academy.
    </p>
    {exclusion && <p>{exclusion}</p>}
    <p className="muted">Subject labels were extracted from paper text and checked by an AI reviewer (AI-assessed), not by human annotators.</p>
  </>
);

const Profile: React.FC<{ d: GroupDetailResponse; id: string; onSelectGroup: (id: string) => void; onOpenNode360: (id: string) => void }> = ({ d, id, onSelectGroup, onOpenNode360 }) => {
  const p = d.profile as Record<string, any>;
  const name = orgName(String(p.name || id));
  const specs = d.specializations.filter((s) => s.group_papers_in_subject >= MIN_ORG_PAPERS).slice(0, 10);
  const maxSpec = Math.max(...specs.map((s) => s.rca), 0.0001);
  const partners = d.partners.slice(0, 8);
  const maxPartner = Math.max(...partners.map((x) => x.papers), 1);
  const wiki = d.description && d.description.source_kind === "wikipedia" ? d.description : null;
  const papers = d.top_papers.slice(0, 6);
  const meta = usePapers(papers.map((x) => x.paper_id));
  const parents = ((p.parents as Array<{ id: string | null; name: string | null }>) || []).filter((x) => x?.id && x.name);
  const country = countryName(p.country_code as string);
  const anchored = (d.org_anchored_communities as Array<{ community: string; members: number; display_name: string }>) || [];

  return (
    <article className="org-profile" data-testid="group-profile">
      <header className="profile-head">
        <div className="topic-kind">
          <EntityDot kind="Organization" />
          <span>Organization{country ? ` in ${country}` : ""}</span>
        </div>
        <h2>{name}</h2>
        {specs.length > 0 && <p className="sub">Most concentrated on {specs.slice(0, 2).map((s) => subjectName(s.subject_name, s.kind).replace(/^[A-Z](?=[a-z])/, (c) => c.toLowerCase())).join(" and ")}.</p>}
      </header>
      <dl className="stats">
        <div>
          <dt>Papers</dt>
          <dd>{p.papers != null ? Number(p.papers).toLocaleString("en") : "Not recorded"}</dd>
        </div>
        <div>
          <dt>Researchers</dt>
          <dd>{p.researchers != null ? Number(p.researchers).toLocaleString("en") : "Not recorded"}</dd>
        </div>
        {d.paper_rank != null && (
          <div>
            <dt>Rank by papers</dt>
            <dd>
              {d.paper_rank.toLocaleString("en")} <small>of {d.ranked_organizations.toLocaleString("en")}</small>
            </dd>
          </div>
        )}
      </dl>

      <Section id="spec" title="Top specialisations">
        <p className="hint">
          Subjects this organization works on more than average.
          <InfoPopover label="What is specialisation?">
            <p>
              <b>Specialisation</b> compares the share of this organization's papers on a subject with the share across all papers. 3× means three times the average. A subject needs at
              least {MIN_ORG_PAPERS} of the organization's papers to be listed.
            </p>
          </InfoPopover>
        </p>
        {specs.length ? (
          <ol className="leadlist" data-chart-label="Organization specialisations" data-chart-rendered="true" data-chart-point-count={specs.length}>
            {specs.map((s) => (
              <li key={s.subject}>
                <div>
                  <button type="button" className="rowlink" onClick={() => navigate(pathFor("topics", s.subject))}>
                    <EntityDot kind={s.kind} /> {subjectName(s.subject_name, s.kind)}
                  </button>
                  <small>
                    {plural(s.group_papers_in_subject, "paper")}
                    {s.first_active_year ? `, first in ${s.first_active_year}` : ""}
                  </small>
                </div>
                <BarTrack value={s.rca} max={maxSpec} />
                <b className="spec">{s.rca.toFixed(1)}×</b>
              </li>
            ))}
          </ol>
        ) : (
          <p className="note">No subject reaches {MIN_ORG_PAPERS} papers, so no specialisation is shown.</p>
        )}
      </Section>

      {partners.length > 0 && (
        <Section id="partners" title="Closest partners" hint="Organizations that share the most papers with it.">
          <ol className="leadlist" data-chart-label="Organization partners" data-chart-rendered="true" data-chart-point-count={partners.length}>
            {partners.map((x) => (
              <li key={x.id}>
                <div>
                  <button type="button" className="rowlink" onClick={() => onSelectGroup(x.id)}>
                    {orgName(x.name)}
                  </button>
                  <small>{countryName(x.country_code)}</small>
                </div>
                <BarTrack value={x.papers} max={maxPartner} />
                <b className="spec">{x.papers.toLocaleString("en")}</b>
              </li>
            ))}
          </ol>
        </Section>
      )}

      {wiki && (
        <Section id="about-org" title="About">
          <p className="prose">{wiki.description}</p>
          <p className="note">
            From{" "}
            <a className="textlink" href={wiki.wikipedia_url || undefined} target="_blank" rel="noreferrer">
              Wikipedia
            </a>
            {wiki.wikipedia_revision_id ? ` (revision ${wiki.wikipedia_revision_id})` : ""}, licensed CC BY-SA 4.0.
          </p>
        </Section>
      )}

      {papers.length > 0 && (
        <Section id="org-papers" title="Recent papers">
          <ol className="toppapers">
            {papers.map((x) => (
              <li key={x.paper_id} className="paper-ref">
                <button type="button" className="t paperlink" onClick={() => onOpenNode360(x.paper_id)}>
                  {x.title}
                </button>
                <span className="meta">{paperMeta(meta.data?.[x.paper_id]) || `${x.venue || ""} ${x.year}`}</span>
              </li>
            ))}
          </ol>
        </Section>
      )}

      {(d.child_units.length > 0 || anchored.length > 0) && (
        <Section id="units" title="Units and research clusters">
          {d.child_units.length > 0 && (
            <div className="chips">
              {d.child_units.slice(0, 12).map((c) => (
                <button key={c.id} type="button" className="echip" onClick={() => onSelectGroup(c.id)}>
                  <EntityDot kind="Organization" />
                  {orgName(c.name)}
                </button>
              ))}
              {d.child_units.length > 12 && <span className="note-inline">and {d.child_units.length - 12} more units</span>}
            </div>
          )}
          {anchored.length > 0 && (
            <ul className="plain-list">
              {anchored.map((c) => (
                <li key={c.community}>
                  <button type="button" className="rowlink" onClick={() => navigate(pathFor("map", `N1:${c.community}`))}>
                    Co-author cluster: {c.display_name}
                  </button>{" "}
                  <span className="muted">{plural(c.members, "researcher")}</span>
                </li>
              ))}
            </ul>
          )}
        </Section>
      )}

      <details className="all-data">
        <summary>Details</summary>
        <dl className="kv">
          <dt>Wikidata type</dt>
          <dd>Wikidata type: {p.sector && p.sector !== "unknown" ? String(p.sector) : "not recorded"}</dd>
          {parents.length > 0 && (
            <>
              <dt>Part of</dt>
              <dd>
                {parents.map((x) => (
                  <button key={x.id!} type="button" className="chip-btn" onClick={() => onSelectGroup(x.id!)}>
                    {orgName(x.name!)}
                  </button>
                ))}
              </dd>
            </>
          )}
          {p.wikidata_qid && (
            <>
              <dt>Wikidata</dt>
              <dd>
                <a className="textlink" href={`https://www.wikidata.org/wiki/${p.wikidata_qid}`} target="_blank" rel="noreferrer">
                  {String(p.wikidata_qid)}
                </a>
              </dd>
            </>
          )}
          {p.wikipedia_url && (
            <>
              <dt>Wikipedia</dt>
              <dd>
                <a className="textlink" href={String(p.wikipedia_url)} target="_blank" rel="noreferrer">
                  Article
                </a>
              </dd>
            </>
          )}
          {d.description && !wiki && (
            <>
              <dt>{d.description.provenance_label || "Graph profile"}</dt>
              <dd>{d.description.description}</dd>
            </>
          )}
        </dl>
        <CopyIdButton id={id} />
      </details>
    </article>
  );
};

const Directory: React.FC<{
  data?: GroupsResponse;
  activeId: string | null;
  onSelect: (id: string) => void;
  onMore: () => void;
  shown: number;
}> = ({ data, activeId, onSelect, onMore, shown }) => (
  <>
    {data && <p className="note">{plural(data.total_organizations, "organization")}, largest first.</p>}
    <ul className="org-list" aria-label="Organizations">
      {data?.organizations.map((o) => (
        <li key={o.id}>
          <button type="button" aria-current={activeId === o.id ? "true" : undefined} onClick={() => onSelect(o.id)} data-testid="org-row">
            <span>{orgName(o.name)}</span>
            <small>
              {countryName(o.country_code)}
              {o.country_code ? ", " : ""}
              {plural(o.papers, "paper")}
            </small>
          </button>
        </li>
      ))}
    </ul>
    {data && data.total_organizations > data.organizations.length && shown < 200 && (
      <button type="button" className="quiet-btn" onClick={onMore}>
        Show more
      </button>
    )}
  </>
);

export const GroupsPage: React.FC<GroupsPageProps> = ({ selectedGroupId, onSelectGroup, onOpenNode360 }) => {
  const [view, setView] = useState<"directory" | "matrix">("directory");
  const [sector, setSector] = useState("");
  const [country, setCountry] = useState("");
  const [notableOnly, setNotableOnly] = useState(false);
  const [search, setSearch] = useState("");
  const [limit, setLimit] = useState(PAGE);

  const list = useQuery({
    queryKey: ["nav-groups", sector, country, notableOnly, search, limit],
    queryFn: ({ signal }) => navigatorApi.listGroups({ sector, country, notable_only: notableOnly, q: search, limit }, signal),
    placeholderData: (prev) => prev,
  });
  const activeId = selectedGroupId || list.data?.organizations[0]?.id || null;
  const detail = useQuery({
    queryKey: ["nav-group-detail", activeId],
    queryFn: ({ signal }) => navigatorApi.getGroupDetail(activeId!, signal),
    enabled: Boolean(activeId) && view === "directory",
  });
  const g = list.data;
  const pick = (id: string) => {
    setView("directory");
    onSelectGroup(id);
  };

  return (
    <div data-testid="page-groups">
      <PageHead title="Groups" sub="Which organizations work on what, and with whom" />
      <div className="controls">
        <div className="seg" role="group" aria-label="View">
          <button type="button" aria-pressed={view === "directory"} onClick={() => setView("directory")}>
            Organizations
          </button>
          <button type="button" aria-pressed={view === "matrix"} onClick={() => setView("matrix")} data-testid="groups-matrix-tab">
            Topic matrix
          </button>
        </div>
        <label className="control control-grow">
          <span className="sr-only">Search organizations</span>
          <input
            className="field-input"
            type="search"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setLimit(PAGE);
            }}
            placeholder="Search organizations…"
            data-testid="groups-search"
          />
        </label>
        <label className="control">
          <span className="sr-only">Country</span>
          <select className="field-input" value={country} onChange={(e) => setCountry(e.target.value)}>
            <option value="">All countries</option>
            {g?.countries.map((c) => (
              <option key={c.code} value={c.code}>
                {countryName(c.code)} ({c.count})
              </option>
            ))}
          </select>
        </label>
        <label className="control">
          <span className="sr-only">Organization type in Wikidata</span>
          <select className="field-input" value={sector} onChange={(e) => setSector(e.target.value)}>
            <option value="">All Wikidata types</option>
            {g?.sectors.map((s) => (
              <option key={s.name} value={s.name}>
                {sectorWord(s.name)} ({s.count})
              </option>
            ))}
          </select>
        </label>
        <label className="check">
          <input type="checkbox" checked={notableOnly} onChange={(e) => setNotableOnly(e.target.checked)} />
          Notable only
        </label>
        <MethodDrawer testId="groups-how">
          <GroupsMethodNote exclusion={g?.government_exclusion_note} />
        </MethodDrawer>
      </div>
      {list.isLoading && <LoadingLine />}
      {list.isError && <ErrorLine error={list.error} onRetry={() => list.refetch()} />}

      {view === "directory" ? (
        <div className={`groups-layout ${selectedGroupId ? "has-selection" : ""}`}>
          <aside className="groups-list">
            <Directory data={g} activeId={activeId} onSelect={pick} shown={limit} onMore={() => setLimit((n) => n + PAGE)} />
          </aside>
          <div className="groups-detail">
            <button type="button" className="textlink back-link groups-back" onClick={() => navigate(pathFor("groups"))}>
              ‹ All organizations
            </button>
            {detail.isLoading && <LoadingLine />}
            {detail.isError && <ErrorLine error={detail.error} onRetry={() => detail.refetch()} />}
            {detail.data && activeId && <Profile key={activeId} id={activeId} d={detail.data} onSelectGroup={pick} onOpenNode360={onOpenNode360} />}
            {g && !activeId && <p className="note">No organization matches these filters.</p>}
          </div>
        </div>
      ) : (
        g && <GroupMatrix data={g} onSelectGroup={pick} />
      )}
    </div>
  );
};
