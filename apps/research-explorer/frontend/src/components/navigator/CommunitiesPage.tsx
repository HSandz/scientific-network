import React, { useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { navigatorApi } from "../../lib/navigatorApi";
import { navigate, pathFor } from "../../lib/router";
import { orgName, plural } from "../../lib/names";
import { readPalette, thermal } from "../../lib/thermal";
import { cleanCommunityRefs } from "../../lib/askModel";
import { clusterLabel, clusterMomentum, clusterTitle, topTerms } from "../../lib/communityModel";
import { paperMeta, usePapers } from "../../lib/usePapers";
import { MIN_RESEARCHER_PAPERS } from "../../config/display";
import type { CommunityNodeItem } from "../../types/navigator";
import { EntityDot, ErrorLine, LoadingLine, MethodDrawer, PageHead, Section } from "../ui/primitives";
import { Icon } from "../shell/icons";
import { ClusterMap } from "./ClusterMap";

interface CommunitiesPageProps {
  /** From the path; opens the side panel. */
  selectedCommunityId: string | null;
  onSelectCommunity: (cid: string) => void;
  onOpenNode360: (id: string) => void;
}

type Source = "research_L1" | "research_L0" | "N1" | "N2";
const SOURCES: Array<{ id: Source; label: string; unit: string }> = [
  { id: "research_L1", label: "Research areas", unit: "papers" },
  { id: "research_L0", label: "Narrower areas", unit: "papers" },
  { id: "N1", label: "Co-author clusters", unit: "researchers" },
  { id: "N2", label: "Organization clusters", unit: "organizations" },
];
const MAP_LIMIT = 24;

const sourceOf = (cid: string | null): Source | null => {
  if (!cid) return null;
  if (cid.startsWith("research:L1")) return "research_L1";
  if (cid.startsWith("research:")) return "research_L0";
  return cid.startsWith("N2") ? "N2" : "N1";
};

const MapMethodNote: React.FC<{ n2Note?: string }> = ({ n2Note }) => (
  <>
    <p>
      Clusters were found with the Leiden community-detection method. <b>Research areas</b> and <b>narrower areas</b> group topics, methods, tasks and datasets that appear in the same
      papers. <b>Co-author clusters</b> group researchers in the co-authorship network and <b>organization clusters</b> group organizations in the collaboration network.
    </p>
    <p>
      <b>Circle size</b> is the number of papers for research areas, and the number of members for the other two.
    </p>
    <p>
      <b>Colour and left-to-right position</b> (research areas only) compare the cluster's share of all papers in 2024–2025 with its share in 2021–2022. This is a display measure for
      this map; the analysis does not assign trend classes to clusters. The other two kinds have no yearly counts, so they are grey. Vertical position has no meaning.
    </p>
    <p>Cluster names and reports written by a language model are marked AI-generated. Where a cluster has no readable name, its most characteristic terms are shown.</p>
    {n2Note && <p>{n2Note}</p>}
    <p className="muted">Subject labels were extracted from paper text and checked by an AI reviewer (AI-assessed), not by human annotators.</p>
  </>
);

const Panel: React.FC<{ cid: string; onClose: () => void; onOpenNode360: (id: string) => void }> = ({ cid, onClose, onOpenNode360 }) => {
  const [showMembers, setShowMembers] = useState(false);
  const q = useQuery({ queryKey: ["nav-community-detail", cid], queryFn: ({ signal }) => navigatorApi.getCommunityDetail(cid, signal) });
  const members = useQuery({ queryKey: ["nav-community-members", cid], queryFn: () => navigatorApi.getCommunityMembers(cid, { limit: 60 }), enabled: showMembers });
  const d: CommunityNodeItem | undefined = q.data;
  const findings = d?.key_findings || [];
  const sourceIds = [...new Set(findings.flatMap((f) => (f.paper_ids || []).slice(0, 2)))];
  const topPapers = (d?.top_papers || []).slice(0, 5);
  const meta = usePapers([...sourceIds, ...topPapers.map((x) => x.id)]);
  const heading = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    setShowMembers(false);
  }, [cid]);
  useEffect(() => {
    if (d) heading.current?.focus({ preventScroll: true });
  }, [d?.community_id]);

  const terms = (d?.dominant_topics || []) as Array<any>;
  const rising = terms.filter((t) => typeof t === "object" && t.label === "Method" && (t.trend_class === "rising" || t.trend_class === "emerging"));

  return (
    <aside className="map-panel" aria-label="Cluster details" data-testid="community-panel" onKeyDown={(e) => e.key === "Escape" && onClose()}>
      <button type="button" className="icon-btn panel-close" aria-label="Close cluster details" onClick={onClose}>
        <Icon name="close" size={19} />
      </button>
      {q.isLoading && <LoadingLine />}
      {q.isError && <ErrorLine error={q.error} onRetry={() => q.refetch()} />}
      {d && (
        <>
          <h2 ref={heading} tabIndex={-1}>
            {clusterTitle(d)}
          </h2>
          <p className="muted">
            {d.paper_count ? `${plural(d.paper_count, "paper")}, ` : ""}
            {plural(d.size, d.source === "N1" ? "researcher" : d.source === "N2" ? "organization" : "linked subject")}
          </p>

          <h3>What it is about</h3>
          {d.summary ? (
            <>
              <p className="prose prose-sm">{cleanCommunityRefs(d.summary)}</p>
              {findings.length > 0 && (
                <ul className="findings">
                  {findings.map((f, i) => (
                    <li key={i}>
                      {cleanCommunityRefs(f.claim)}
                      {(f.paper_ids || []).slice(0, 2).map((pid) => (
                        <button
                          key={pid}
                          type="button"
                          className="fnref"
                          onClick={() => onOpenNode360(pid)}
                          title={meta.data?.[pid]?.title || "Open the paper"}
                          aria-label={`Source ${sourceIds.indexOf(pid) + 1}: ${meta.data?.[pid]?.title || "paper"}`}
                        >
                          {sourceIds.indexOf(pid) + 1}
                        </button>
                      ))}
                    </li>
                  ))}
                </ul>
              )}
              {sourceIds.length > 0 && (
                <ol className="sources">
                  {sourceIds.map((pid) => (
                    <li key={pid} className="paper-ref">
                      <button type="button" className="t paperlink" onClick={() => onOpenNode360(pid)}>
                        {meta.data?.[pid]?.title || "Loading title…"}
                      </button>
                      <span className="meta">{paperMeta(meta.data?.[pid])}</span>
                    </li>
                  ))}
                </ol>
              )}
              <p className="note">{d.ai_generated_label || "AI-generated from graph data"}.</p>
            </>
          ) : (
            <p className="note">No written report for this cluster. Its most characteristic terms are {topTerms(d, 5) || "not recorded"}.</p>
          )}

          {terms.length > 0 && (
            <div className="chips">
              {terms.slice(0, 6).map((t, i) =>
                typeof t === "object" ? (
                  <button key={t.id} type="button" className="echip" onClick={() => navigate(pathFor("topics", t.id))}>
                    <EntityDot kind={t.label} />
                    {t.name} <span className="c">{t.papers}</span>
                  </button>
                ) : (
                  <span key={i} className="echip echip-static">
                    {String(t)}
                  </span>
                ),
              )}
            </div>
          )}

          {(d.top_orgs?.length || 0) > 0 && (
            <>
              <h3>Leading groups</h3>
              <ul className="plain-list">
                {d.top_orgs!.map((o) => (
                  <li key={o.id}>
                    <button type="button" className="rowlink" onClick={() => navigate(pathFor("groups", o.id))}>
                      {orgName(o.name)}
                    </button>
                    {o.papers != null && <span className="muted">{plural(o.papers, "paper")}</span>}
                  </li>
                ))}
              </ul>
            </>
          )}
          {d.label_organization && (
            <>
              <h3>Characteristic organizations</h3>
              <p>{d.label_organization.split(";").map((x) => orgName(x.trim())).slice(0, 5).join(", ")}</p>
            </>
          )}

          {d.top_people && (
            <>
              <h3>Leading people</h3>
              {d.top_people.length ? (
                <ul className="plain-list">
                  {d.top_people.map((r) => (
                    <li key={r.id}>
                      <button type="button" className="rowlink" onClick={() => onOpenNode360(r.id)}>
                        {r.name}
                      </button>
                      <span className="muted">{plural(r.papers, "paper")}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="note">No researcher has {MIN_RESEARCHER_PAPERS} or more papers in this cluster.</p>
              )}
            </>
          )}
          {(d.hubs?.length || 0) > 0 && (
            <>
              <h3>Most central people</h3>
              <p>{d.hubs!.slice(0, 5).join(", ")}</p>
              {(d.brokers?.length || 0) > 0 && (
                <>
                  <h3>People who connect it to other clusters</h3>
                  <p>{d.brokers!.slice(0, 5).join(", ")}</p>
                </>
              )}
            </>
          )}

          {rising.length > 0 && (
            <>
              <h3>Rising methods in it</h3>
              <div className="chips">
                {rising.map((t) => (
                  <button key={t.id} type="button" className="echip" onClick={() => navigate(pathFor("topics", t.id))}>
                    <EntityDot kind="Method" />
                    {t.name}
                  </button>
                ))}
              </div>
            </>
          )}

          {topPapers.length > 0 && (
            <>
              <h3>Papers</h3>
              <ul className="plain-list plain-list-stack">
                {topPapers.map((x) => (
                  <li key={x.id} className="paper-ref">
                    <button type="button" className="t paperlink" onClick={() => onOpenNode360(x.id)}>
                      {x.title}
                    </button>
                    <span className="meta">{paperMeta(meta.data?.[x.id]) || x.year}</span>
                  </li>
                ))}
              </ul>
            </>
          )}

          <h3>Members</h3>
          {!showMembers ? (
            <button type="button" className="chip-btn" data-testid="expand-community-members" onClick={() => setShowMembers(true)}>
              Show members ({d.size.toLocaleString("en")})
            </button>
          ) : (
            <div data-testid="community-members-panel">
              {members.isLoading && <LoadingLine />}
              {members.data && (
                <>
                  <p className="muted">
                    Showing {members.data.members.length} of {members.data.total.toLocaleString("en")}.
                  </p>
                  <div className="chips">
                    {members.data.members.map((m) => (
                      <button key={m.id} type="button" className="echip" onClick={() => onOpenNode360(m.id)}>
                        <EntityDot kind={m.label} />
                        {m.label === "Organization" ? orgName(m.name) : m.name}
                      </button>
                    ))}
                  </div>
                </>
              )}
            </div>
          )}
        </>
      )}
    </aside>
  );
};

export const CommunitiesPage: React.FC<CommunitiesPageProps> = ({ selectedCommunityId, onSelectCommunity, onOpenNode360 }) => {
  const [source, setSource] = useState<Source>(sourceOf(selectedCommunityId) || "research_L1");
  const [search, setSearch] = useState("");

  // A link to a cluster of another kind switches the map to that kind.
  useEffect(() => {
    const s = sourceOf(selectedCommunityId);
    if (s) setSource(s);
  }, [selectedCommunityId]);

  const list = useQuery({
    queryKey: ["nav-communities", source, search],
    queryFn: ({ signal }) => navigatorApi.listCommunities({ source, q: search, limit: 80 }, signal),
    placeholderData: (prev) => prev,
  });
  const pulse = useQuery({ queryKey: ["nav-pulse"], queryFn: ({ signal }) => navigatorApi.getPulse(signal), staleTime: 600_000 });

  const info = SOURCES.find((s) => s.id === source)!;
  const research = source.startsWith("research");
  const p = readPalette();
  const items = useMemo(() => {
    const totals = pulse.data?.year_totals || {};
    return (list.data?.supernodes || [])
      .filter((n) => n.source === source)
      .map((n) => {
        const mom = research ? clusterMomentum(n.papers_by_year, totals) : null;
        return {
          id: n.community_id,
          label: clusterLabel(n),
          title: clusterTitle(n),
          size: research ? n.paper_count || 0 : n.size,
          t: mom?.t ?? 0,
          change: mom?.words || "",
        };
      })
      .sort((a, b) => b.size - a.size);
  }, [list.data, pulse.data, source, research]);
  const shown = items.slice(0, MAP_LIMIT);
  const rising = (list.data?.rising_researchers || []).filter((r) => r.recent_papers >= MIN_RESEARCHER_PAPERS).slice(0, 15);

  return (
    <div data-testid="page-communities">
      <PageHead title="Map of research clusters" sub="Groups of subjects, people and organizations that belong together. Select one to read about it." />
      <div className="controls">
        <div className="seg seg-wrap" role="group" aria-label="Kind of cluster">
          {SOURCES.map((s) => (
            <button
              key={s.id}
              type="button"
              aria-pressed={source === s.id}
              onClick={() => {
                setSource(s.id);
                if (selectedCommunityId) navigate(pathFor("map"));
              }}
            >
              {s.label}
            </button>
          ))}
        </div>
        <label className="control control-grow">
          <span className="sr-only">Filter clusters</span>
          <input className="field-input" type="search" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Filter by name or term…" />
        </label>
        <MethodDrawer testId="map-how">
          <MapMethodNote n2Note={source === "N2" ? list.data?.n2_resolution_note : undefined} />
        </MethodDrawer>
      </div>
      {list.isLoading && <LoadingLine />}
      {list.isError && <ErrorLine error={list.error} onRetry={() => list.refetch()} />}

      <div className={`map-layout ${selectedCommunityId ? "has-panel" : ""}`}>
        <div className="map-main">
          {list.data && (
            <>
              <div className="map-legend">
                {research ? (
                  <>
                    <span>Cooling</span>
                    <span className="scale" aria-hidden="true" />
                    <span>Heating</span>
                  </>
                ) : null}
                <span>
                  Circle size shows {info.unit}. {items.length > shown.length ? `The ${shown.length} largest of ${items.length} are on the map; all are listed below.` : ""}
                </span>
              </div>
              {shown.length ? (
                <ClusterMap
                  items={shown}
                  positioned={research}
                  selected={selectedCommunityId}
                  unit={info.unit}
                  colorOf={(t) => (research ? thermal(t, p) : p.neutral)}
                  onSelect={onSelectCommunity}
                />
              ) : (
                <p className="note">No cluster matches that filter.</p>
              )}
              <details className="map-all">
                <summary>All {items.length} clusters as a list</summary>
                <ul className="plain-list">
                  {items.map((it) => (
                    <li key={it.id}>
                      <button type="button" className="rowlink" onClick={() => onSelectCommunity(it.id)}>
                        {it.title}
                      </button>
                      <span className="muted">
                        {it.size.toLocaleString("en")} {info.unit}
                        {it.change ? `, ${it.change}` : ""}
                      </span>
                    </li>
                  ))}
                </ul>
              </details>
            </>
          )}
        </div>
        {selectedCommunityId && <Panel cid={selectedCommunityId} onClose={() => navigate(pathFor("map"))} onOpenNode360={onOpenNode360} />}
      </div>

      {source === "N1" && rising.length > 0 && (
        <Section id="rising-people" title="Rising researchers" hint={`At least ${MIN_RESEARCHER_PAPERS} papers in 2024–2025, compared with 2021–2022.`}>
          <div className="table-scroll">
            <table className="data">
              <thead>
                <tr>
                  <th>Researcher</th>
                  <th className="num">Papers 2024–2025</th>
                  <th className="num">Papers 2021–2022</th>
                  <th>Cluster</th>
                </tr>
              </thead>
              <tbody>
                {rising.map((r) => (
                  <tr key={r.id}>
                    <td>
                      <button type="button" className="rowlink" onClick={() => onOpenNode360(r.id)}>
                        {r.name}
                      </button>
                    </td>
                    <td className="num">{r.recent_papers}</td>
                    <td className="num">{r.new_entrant ? "none (new)" : r.base_papers}</td>
                    <td>
                      <button type="button" className="textlink" onClick={() => onSelectCommunity(`N1:${r.community}`)}>
                        Open cluster
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>
      )}
    </div>
  );
};
