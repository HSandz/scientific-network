import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { navigatorApi } from "../../lib/navigatorApi";
import { AppLink, EntityDot, ErrorLine, InfoPopover, LoadingLine, MethodDrawer, PageHead, Section } from "../ui/primitives";
import { LineChart } from "../charts/charts";
import { orgName } from "../../lib/names";
import { linkClick, pathFor } from "../../lib/router";
import { DegreePlot, PathHistogram } from "./networkFigures";

interface NetworkSciencePageProps {
  onOpenNode360: (id: string) => void;
  /** The frozen release (v4) sections that have no counterpart in the enriched graph. */
  releaseSections?: React.ReactNode;
}

type Net = "N1" | "N2" | "N3" | "N4";
const NETS: Record<Net, { name: string; noun: string; one: string; what: string }> = {
  N1: { name: "Co-authorship", noun: "researchers", one: "researcher", what: "researchers, linked when they wrote a paper together" },
  N2: { name: "Organization collaboration", noun: "organizations", one: "organization", what: "organizations, linked when their researchers wrote a paper together" },
  N3: { name: "Citations between papers", noun: "papers", one: "paper", what: "papers, linked when one cites another" },
  N4: { name: "Full knowledge graph", noun: "nodes", one: "node", what: "papers, researchers, organizations and subjects with all their links" },
};
const SW_NETS: Net[] = ["N1", "N2", "N4"];
const MEASURES: Record<string, string> = {
  degree: "Number of links",
  strength: "Weighted links",
  betweenness: "Bridging (betweenness)",
  eigenvector: "Links to well-linked nodes (eigenvector)",
};

const num = (v: unknown, d = 0) => (typeof v === "number" ? v.toLocaleString("en", { minimumFractionDigits: d, maximumFractionDigits: d }) : "–");
const small = (v: unknown) => (typeof v === "number" ? (v < 0.001 ? v.toFixed(4) : v < 0.1 ? v.toFixed(3) : v.toFixed(2)) : "–");

const NetworkMethodNote: React.FC<{ clustering?: string; config?: string; graph?: string }> = ({ clustering, config, graph }) => (
  <>
    <p>
      A network is a <b>small world</b> when its nodes form much tighter groups than chance would give, while the average number of steps between two nodes stays close to a random
      network's. Each network is compared with two kinds of random network: one that keeps every node's number of links and shuffles who links to whom, and one with the same number of
      nodes and links placed at random.
    </p>
    <p>
      The rule was fixed before measuring: the score must be above 1 for every random replicate, and the average path must be no more than twice the random network's. Path lengths and
      clustering are measured on the main connected part of each network.
    </p>
    {clustering && <p>Clustering: {clustering}</p>}
    <h3>Central nodes</h3>
    <p>
      Rankings use PageRank (damping 0.85). The score shown is how many times the average node's value a node receives. Citation rankings use only citations between papers in this
      collection and are fragile because few such links exist.
    </p>
    <p className="muted">
      Analysis {config} on graph {graph}. Entity extraction was checked by an AI reviewer (AI-assessed), not by human annotators.
    </p>
  </>
);

export const NetworkSciencePage: React.FC<NetworkSciencePageProps> = ({ onOpenNode360, releaseSections }) => {
  const [net, setNet] = useState<Net>("N1");
  const [rankNet, setRankNet] = useState<Net>("N1");
  const [kind, setKind] = useState("Researcher");
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["nav-network-science"],
    queryFn: ({ signal }) => navigatorApi.getNetworkScience(signal),
  });

  const sw = ((data?.smallworld as any)?.networks || {}) as Record<string, any>;
  const evo = (data?.evolution || {}) as Record<string, Array<{ year: number; L: number; C: number }>>;
  const tails = (data?.degree_tail || {}) as Record<string, { degree_counts?: Record<string, number>; power_law_claim_allowed?: boolean }>;
  const ranking = (data?.ranking || {}) as Record<string, any>;
  const cur = sw[net];
  const er = cur?.baselines?.erdos_renyi_gnm;
  const rw = cur?.baselines?.degree_preserving_rewiring;
  const holds = Boolean(cur?.decision?.small_world_holds);
  const n1 = sw.N1;
  // The artifact ends each series with a summary entry that has no year.
  const rows = (evo[net] || []).filter((r) => typeof r.year === "number" && typeof r.L === "number" && typeof r.C === "number");

  const rankBlock = ranking[rankNet] || {};
  const byKind = rankBlock.top && !Array.isArray(rankBlock.top) ? (rankBlock.top as Record<string, any[]>) : null;
  const topRows: any[] = (byKind ? byKind[kind] || [] : rankBlock.top || []).slice(0, 15);

  return (
    <div data-testid="page-network-science">
      <PageHead
        title="Is it a small world?"
        sub="How researchers, organizations and papers are connected"
        lede={
          n1 ? (
            <span data-testid="network-verdict">
              {n1.decision?.small_world_holds ? "Yes. " : "Not quite. "}
              Researchers form tight circles of co-authors, yet two researchers in the main network are on average only {num(n1.real?.L, 1)} steps apart.
            </span>
          ) : undefined
        }
      />
      {isLoading && <LoadingLine />}
      {error ? <ErrorLine error={error} onRetry={() => refetch()} /> : null}

      {data && cur && (
        <>
          <div className="controls">
            <div className="seg seg-wrap" role="group" aria-label="Network">
              {SW_NETS.map((k) => (
                <button key={k} type="button" aria-pressed={net === k} onClick={() => setNet(k)} data-testid={`network-${k}`}>
                  {NETS[k].name}
                </button>
              ))}
            </div>
            <MethodDrawer testId="network-how">
              <NetworkMethodNote clustering={data.clustering_definition as string} config={data.config_version as string} graph={data.graph_version as string} />
            </MethodDrawer>
          </div>

          <Section id="evidence" title={`${NETS[net].name}: ${holds ? "a small world" : "not a small world"}`} hint={`A network of ${NETS[net].what}.`}>
            <div className="table-scroll">
              <table className="data evidence-table">
                <thead>
                  <tr>
                    <th>Measure</th>
                    <th className="num">This network</th>
                    <th className="num">Shuffled, same links per node</th>
                    <th className="num">Random, same size</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <th scope="row">
                      How often two neighbours are also linked
                      <InfoPopover label="Clustering C">
                        <p>
                          <b>Clustering coefficient C</b>: for each node, the share of pairs of its neighbours that are linked to each other, averaged over nodes. Between 0 and 1.
                        </p>
                      </InfoPopover>
                    </th>
                    <td className="num big">{small(cur.real?.clustering?.average_local)}</td>
                    <td className="num">{small(rw?.C_rand_mean)}</td>
                    <td className="num">{small(er?.C_rand_mean)}</td>
                  </tr>
                  <tr>
                    <th scope="row">
                      Average steps between two nodes
                      <InfoPopover label="Path length L">
                        <p>
                          <b>Average shortest path length L</b>: the fewest links needed to get from one node to another, averaged over all connected pairs.
                        </p>
                      </InfoPopover>
                    </th>
                    <td className="num big">{num(cur.real?.L, 2)}</td>
                    <td className="num">{num(rw?.L_rand_mean, 2)}</td>
                    <td className="num">{num(er?.L_rand_mean, 2)}</td>
                  </tr>
                  <tr>
                    <th scope="row">
                      Small-world score against each baseline
                      <InfoPopover label="Small-world score σ">
                        <p>
                          <b>σ = (C ÷ C of the random network) ÷ (L ÷ L of the random network)</b>. Above 1 means more clustered than random for its path length.
                        </p>
                      </InfoPopover>
                    </th>
                    <td className="num">–</td>
                    <td className="num big">{num(rw?.sigma_from_means)}</td>
                    <td className="num big">{num(er?.sigma_from_means)}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p className="note">
              The main connected part holds {num(cur.lcc_nodes)} of {num(cur.full_nodes)} {NETS[net].noun} ({num((cur.lcc_share_of_nodes || 0) * 100)}%). Paths are{" "}
              {num(rw?.L_over_L_rand, 1)} times as long as in the shuffled network, within the limit of 2. The longest shortest path is {num(cur.real?.diameter)} steps.
            </p>
          </Section>

          <div className="two-lists">
            <Section id="paths" title="Steps between pairs">
              <PathHistogram histogram={cur.real?.histogram || {}} mean={cur.real?.L} />
            </Section>
            <Section id="degree" title="Links per node">
              {tails[net]?.degree_counts ? (
                <>
                  <DegreePlot counts={tails[net].degree_counts!} noun={NETS[net].noun} />
                  <p className="note">
                    {tails[net].power_law_claim_allowed
                      ? "A power law fits the tail under the declared test."
                      : "A few nodes have far more links than most. The declared test does not support calling this a power law."}
                  </p>
                </>
              ) : (
                <p className="note">The degree distribution was not computed for this network.</p>
              )}
            </Section>
          </div>

          {rows.length > 0 && (
            <Section id="evolution" title="How it changed" hint="Each year includes all papers up to and including that year.">
              <div className="two-lists">
                <div>
                  <h3>Average steps between two nodes</h3>
                  <LineChart label="Path length by year" unit="plain" years={rows.map((r) => String(r.year))} series={[{ name: "Average steps", values: rows.map((r) => r.L) }]} height={230} />
                </div>
                <div>
                  <h3>How often two neighbours are linked</h3>
                  <LineChart label="Clustering by year" unit="plain" years={rows.map((r) => String(r.year))} series={[{ name: "Clustering", values: rows.map((r) => r.C) }]} height={230} />
                </div>
              </div>
              {net === "N1" && <p className="note">In 2021 the main connected part was still small, so its path length is not comparable with later years.</p>}
            </Section>
          )}

          <Section id="central" title="Who is central" hint="Ranked by PageRank. The score is the node's value as a multiple of the average node's.">
            <div className="controls">
              <div className="seg seg-wrap" role="group" aria-label="Ranking network">
                {(Object.keys(NETS) as Net[]).map((k) => (
                  <button key={k} type="button" aria-pressed={rankNet === k} onClick={() => setRankNet(k)} data-testid={`rank-${k}`}>
                    {NETS[k].name}
                  </button>
                ))}
              </div>
              {byKind && (
                <label className="control">
                  <span className="sr-only">Kind of node</span>
                  <select className="field-input" value={kind} onChange={(e) => setKind(e.target.value)}>
                    {Object.keys(byKind).map((k) => (
                      <option key={k} value={k}>
                        {k}
                      </option>
                    ))}
                  </select>
                </label>
              )}
            </div>
            {rankNet === "N3" && <p className="note">Few papers here cite one another, so this ranking is fragile. Read it next to the citation counts.</p>}
            <div className="table-scroll">
              <table className="data" data-chart-label="Centrality ranking" data-chart-rendered="true" data-chart-point-count={topRows.length}>
                <thead>
                  <tr>
                    <th className="num">Rank</th>
                    <th>Name</th>
                    <th className="num">Score</th>
                    <th className="num">Links</th>
                    {rankNet === "N3" && <th className="num">Citations here</th>}
                  </tr>
                </thead>
                <tbody>
                  {topRows.map((r, i) => (
                    <tr key={r.id || i}>
                      <td className="num">{i + 1}</td>
                      <td>
                        <button type="button" className="rowlink" onClick={() => r.id && onOpenNode360(r.id)}>
                          <EntityDot kind={r.label || kind} /> {r.label === "Organization" ? orgName(r.name) : r.name}
                        </button>
                      </td>
                      <td className="num">{typeof r.pagerank === "number" && rankBlock.nodes ? `${num(r.pagerank * rankBlock.nodes, 1)}×` : "–"}</td>
                      <td className="num">{num(r.degree)}</td>
                      {rankNet === "N3" && <td className="num">{num(r.in_corpus_citations ?? 0)}</td>}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {rankBlock.comparison_with_pagerank && (
              <details className="map-all">
                <summary>Do other measures of importance agree?</summary>
                <div className="table-scroll">
                  <table className="data">
                    <thead>
                      <tr>
                        <th>Measure compared with PageRank</th>
                        <th className="num">Rank agreement (Spearman, 1 is identical)</th>
                        <th className="num">Shared among the top 20</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(rankBlock.comparison_with_pagerank as Record<string, any>).map(([m, v]) => (
                        <tr key={m}>
                          <th scope="row">{MEASURES[m] || m}</th>
                          <td className="num">{typeof v?.spearman === "number" ? v.spearman.toFixed(2) : "Not computed"}</td>
                          <td className="num">{v?.top20_overlap ?? "Not computed"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </details>
            )}
          </Section>

          <p className="note">
            The communities inside these networks are on the{" "}
            <a className="textlink" href={pathFor("map")} onClick={(e) => linkClick(e, pathFor("map"))}>
              Map
            </a>
            .
          </p>
        </>
      )}

      {releaseSections && (
        <Section
          id="release-checks"
          title="Checks on the frozen release graph (v4)"
          hint="Analyses that exist only for the earlier release graph, which has no extracted methods, tasks or datasets: how far collaboration results survive stricter evidence, how academia and industry work together, and citation patterns."
          testId="network-release-checks"
        >
          <AppLink to={pathFor("network", "release")} className="textlink" >
            Open the full v4 release report
          </AppLink>
          <div className="release-embed">{releaseSections}</div>
        </Section>
      )}
    </div>
  );
};
