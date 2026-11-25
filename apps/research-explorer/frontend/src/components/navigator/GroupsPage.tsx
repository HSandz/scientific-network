import React, { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { navigatorApi } from "../../lib/navigatorApi";
import { useExplorerStore } from "../../stores/useExplorerStore";
import { Panel, Table } from "../analytics/DashboardPrimitives";
import { EChartBox } from "../analytics/EChartBox";
import { MetricTooltip } from "./MetricTooltip";

interface GroupsPageProps {
  selectedGroupId: string | null;
  onSelectGroup: (id: string) => void;
  onOpenNode360: (id: string) => void;
}

export const GroupsPage: React.FC<GroupsPageProps> = ({ selectedGroupId, onSelectGroup, onOpenNode360 }) => {
  const darkMode = useExplorerStore((s) => s.darkMode);
  const [sector, setSector] = useState("");
  const [country, setCountry] = useState("");
  const [notableOnly, setNotableOnly] = useState(false);
  const [search, setSearch] = useState("");

  const axisColor = darkMode ? "#b0b0b0" : "#504f4c";

  const groupsQuery = useQuery({
    queryKey: ["nav-groups", sector, country, notableOnly, search],
    queryFn: ({ signal }) =>
      navigatorApi.listGroups({ sector, country, notable_only: notableOnly, q: search, limit: 60 }, signal),
  });

  const activeGroupId = selectedGroupId || groupsQuery.data?.organizations[0]?.id || "organization:I19820366";

  const detailQuery = useQuery({
    queryKey: ["nav-group-detail", activeGroupId],
    queryFn: ({ signal }) => navigatorApi.getGroupDetail(activeGroupId, signal),
    enabled: Boolean(activeGroupId),
  });

  const matrixOption = useMemo(() => {
    const m = groupsQuery.data?.matrix;
    if (!m || !m.organizations.length || !m.topics.length) return null;
    const orgIdx = new Map(m.organizations.map((o, i) => [o, i]));
    const topIdx = new Map(m.topics.map((t, i) => [t, i]));
    const pts: Array<[number, number, number]> = [];
    let maxRca = 2;
    m.cells.forEach((c) => {
      const yi = orgIdx.get(c.organization_name);
      const xi = topIdx.get(c.subject_name);
      if (yi !== undefined && xi !== undefined) {
        const val = Number(c.rca.toFixed(2));
        if (val > maxRca) maxRca = Math.min(8, val);
        pts.push([xi, yi, val]);
      }
    });
    return {
      tooltip: {
        formatter: (p: { value: [number, number, number] }) =>
          `${m.organizations[p.value[1]]} × ${m.topics[p.value[0]]}: RCA ${p.value[2]}`,
      },
      grid: { top: 10, left: 190, right: 20, bottom: 75 },
      xAxis: { type: "category", data: m.topics.map((t) => t.slice(0, 18)), axisLabel: { rotate: 32, fontSize: 10, color: axisColor } },
      yAxis: { type: "category", data: m.organizations.map((o) => o.slice(0, 26)), inverse: true, axisLabel: { fontSize: 10, color: axisColor } },
      visualMap: {
        min: 0,
        max: maxRca,
        show: false,
        inRange: {
          color: darkMode ? ["#1f2937", "#b45309", "#fbbf24"] : ["#fef3c7", "#f59e0b", "#92400e"],
        },
      },
      series: [{ type: "heatmap", data: pts }],
    };
  }, [groupsQuery.data, axisColor, darkMode]);

  const g = groupsQuery.data;
  const gd = detailQuery.data;

  return (
    <div data-testid="page-groups" className="p-4 sm:p-6 space-y-4 overflow-y-auto h-full">
      <div className="ledger-panel p-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold text-ink">Research Organizations & Institutional Groups</h1>
          <p className="text-xs text-muted mt-0.5">{g?.government_exclusion_note}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <select aria-label="Filter by sector" value={sector} onChange={(e) => setSector(e.target.value)} className="ledger-input h-8 px-2">
            <option value="">All sectors</option>
            {(g?.sectors || []).map((s) => <option key={s.name} value={s.name}>{s.name} ({s.count})</option>)}
          </select>
          <select aria-label="Filter by country" value={country} onChange={(e) => setCountry(e.target.value)} className="ledger-input h-8 px-2">
            <option value="">All countries</option>
            {(g?.countries || []).map((c) => <option key={c.code} value={c.code}>{c.code} ({c.count})</option>)}
          </select>
          <label className="inline-flex items-center gap-1.5 cursor-pointer">
            <input type="checkbox" checked={notableOnly} onChange={(e) => setNotableOnly(e.target.checked)} />
            <span>Notable only</span>
          </label>
          <input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Filter organization…"
            aria-label="Filter organizations"
            className="ledger-input h-8 px-2.5 w-44"
          />
        </div>
      </div>

      {g && (
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
          <div className="xl:col-span-2 space-y-4">
            {matrixOption && (
              <Panel title="Organization × Topic Specialization Matrix (RCA)">
                <div className="text-xs text-muted mb-2">
                  <MetricTooltip
                    label="Revealed Comparative Advantage (RCA)"
                    definition={g.metric_definitions?.rca?.definition || "Group topic share divided by global topic share."}
                    denominator={g.metric_definitions?.rca?.denominator}
                    network={g.metric_definitions?.rca?.network}
                  />
                </div>
                <EChartBox option={matrixOption} label="Organization by topic RCA heatmap" height={340} />
              </Panel>
            )}

            <Panel title={`Organizations (${g.total_organizations.toLocaleString()} matched)`}>
              <Table
                label="Organizations list"
                headers={["Organization", "Sector", "Country", "Papers", "Researchers", "Notable"]}
                rows={g.organizations.map((o) => [
                  <button key={o.id} type="button" onClick={() => onSelectGroup(o.id)} className="text-[var(--accent)] hover:underline text-left">
                    {o.name}
                  </button>,
                  o.sector,
                  o.country_code || "—",
                  o.papers.toLocaleString(),
                  o.researchers.toLocaleString(),
                  o.notable ? "Yes" : "No",
                ])}
              />
            </Panel>

            <Panel title="Organization-Anchored Communities & Parent Roll-Up">
              <p className="text-xs text-muted mb-2">
                Clusters ≥100 researchers are badged <strong>large</strong>; duplicate institution names are disambiguated by dominant topic.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                <div>
                  <h4 className="font-semibold mb-1.5">Organization-Anchored Communities</h4>
                  <ul className="space-y-1 max-h-60 overflow-y-auto pr-1">
                    {g.org_anchored_communities.slice(0, 20).map((c) => (
                      <li key={c.community} className="flex items-center justify-between gap-2 border-b border-rule pb-1">
                        <button type="button" onClick={() => onSelectGroup(c.organization_id)} className="text-left hover:underline truncate">
                          {c.display_name}
                        </button>
                        <span className="shrink-0 tabular-nums">
                          {c.members}
                          {c.size_tier === "large" && (
                            <span className="ml-1 px-1 py-0.5 rounded bg-raised text-[10px] font-semibold">large</span>
                          )}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h4 className="font-semibold mb-1.5">Non-Government Parent Roll-Up</h4>
                  <ul className="space-y-1 max-h-60 overflow-y-auto pr-1">
                    {g.rollup.slice(0, 20).map((r) => (
                      <li key={r.parent} className="flex items-center justify-between gap-2 border-b border-rule pb-1">
                        <span className="truncate">{r.parent_name}</span>
                        <span className="shrink-0 text-muted tabular-nums">
                          {r.child_organizations} units · {r.papers} papers
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </Panel>
          </div>

          <div className="space-y-4">
            <Panel title={String(gd?.profile?.name || "Organization Profile")}>
              {gd ? (
                <div className="space-y-3 text-xs">
                  <div className="flex flex-wrap gap-2">
                    <span className="px-2 py-0.5 rounded bg-raised">Sector: {String(gd.profile.sector || "—")}</span>
                    <span className="px-2 py-0.5 rounded bg-raised">Country: {String(gd.profile.country_code || "—")}</span>
                    <button type="button" onClick={() => onOpenNode360(activeGroupId)} className="px-2 py-0.5 rounded border border-control hover:bg-raised">
                      Open Node 360 →
                    </button>
                  </div>
                  {gd.description && (
                    <div className="p-2 rounded bg-ground border border-rule space-y-1">
                      <span className="text-[10px] uppercase tracking-wide text-faint block">
                        {gd.description.provenance_label || "Graph profile"}
                      </span>
                      <p className="text-ink">{gd.description.description}</p>
                      {gd.description.wikipedia_url && (
                        <p className="text-[10px] text-faint">
                          <a href={gd.description.wikipedia_url} target="_blank" rel="noreferrer" className="text-[var(--accent)] hover:underline">
                            Wikipedia source (rev {gd.description.wikipedia_revision_id ?? "—"})
                          </a>{" "}
                          · CC BY-SA 4.0
                        </p>
                      )}
                    </div>
                  )}
                  <div>
                    <h4 className="font-semibold mb-1">Top Topic Specializations (RCA & Entry Year)</h4>
                    <ul className="space-y-1">
                      {gd.specializations.slice(0, 8).map((sp) => (
                        <li key={sp.subject} className="flex justify-between border-b border-rule pb-0.5 tabular-nums">
                          <span className="truncate">{sp.subject_name}</span>
                          <span className="shrink-0 text-muted">
                            RCA {sp.rca.toFixed(2)} · from {sp.first_active_year || "—"}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  {gd.partners.length > 0 && (
                    <div>
                      <h4 className="font-semibold mb-1">Top Collaborating Organizations</h4>
                      <ul className="space-y-1">
                        {gd.partners.slice(0, 6).map((p) => (
                          <li key={p.id} className="flex justify-between">
                            <button type="button" onClick={() => onSelectGroup(p.id)} className="text-[var(--accent)] hover:underline truncate">
                              {p.name}
                            </button>
                            <span className="tabular-nums text-muted">{p.papers} papers</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-xs text-muted">Select an organization to inspect its profile.</p>
              )}
            </Panel>
          </div>
        </div>
      )}
    </div>
  );
};
