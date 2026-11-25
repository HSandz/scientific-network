import React, { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { navigatorApi } from "../../lib/navigatorApi";
import { CommunityNodeItem } from "../../types/navigator";
import { Panel, Table } from "../analytics/DashboardPrimitives";

interface CommunitiesPageProps {
  selectedCommunityId: string | null;
  onSelectCommunity: (cid: string) => void;
  onOpenNode360: (id: string) => void;
}

const SOURCES: Array<{ id: "research_L1" | "research_L0" | "N1" | "N2"; label: string }> = [
  { id: "research_L1", label: "Research L1 (Macro)" },
  { id: "research_L0", label: "Research L0 (Leaves)" },
  { id: "N1", label: "N1 Researchers (S3)" },
  { id: "N2", label: "N2 Organizations (S3)" },
];

export const CommunitiesPage: React.FC<CommunitiesPageProps> = ({
  selectedCommunityId,
  onSelectCommunity,
  onOpenNode360,
}) => {
  const [source, setSource] = useState<"research_L1" | "research_L0" | "N1" | "N2">("research_L1");
  const [search, setSearch] = useState("");
  const [expandedCid, setExpandedCid] = useState<string | null>(null);

  const listQuery = useQuery({
    queryKey: ["nav-communities", source, search],
    queryFn: ({ signal }) => navigatorApi.listCommunities({ source, q: search, limit: 80 }, signal),
  });

  const activeCid =
    selectedCommunityId || listQuery.data?.supernodes[0]?.community_id || "research:L1:1";

  const detailQuery = useQuery({
    queryKey: ["nav-community-detail", activeCid],
    queryFn: ({ signal }) => navigatorApi.getCommunityDetail(activeCid, signal),
    enabled: Boolean(activeCid),
  });

  const membersQuery = useQuery({
    queryKey: ["nav-community-members", expandedCid],
    queryFn: () => navigatorApi.getCommunityMembers(expandedCid!, { limit: 40 }),
    enabled: Boolean(expandedCid),
  });

  // Deterministic circular/level coordinates for super-node SVG canvas
  const layoutNodes = useMemo(() => {
    const nodes = (listQuery.data?.supernodes || []).slice(0, 36);
    const n = Math.max(nodes.length, 1);
    const maxSize = Math.max(...nodes.map((x) => x.size), 1);
    return nodes.map((node, idx) => {
      const angle = (2 * Math.PI * idx) / n - Math.PI / 2;
      const ring = 140 + (idx % 2) * 38;
      const cx = 260 + ring * Math.cos(angle);
      const cy = 200 + ring * Math.sin(angle);
      const radius = 12 + Math.round(Math.sqrt(node.size / maxSize) * 18);
      return { node, cx, cy, radius };
    });
  }, [listQuery.data]);

  const coordById = useMemo(
    () => new Map(layoutNodes.map((item) => [item.node.community_id, { cx: item.cx, cy: item.cy }])),
    [layoutNodes],
  );

  const detail: CommunityNodeItem | undefined = detailQuery.data;

  return (
    <div data-testid="page-communities" className="p-4 sm:p-6 space-y-4 overflow-y-auto h-full">
      <div className="ledger-panel p-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold text-ink">Communities & GraphRAG Super-Nodes</h1>
          <p className="text-xs text-muted mt-0.5">
            {listQuery.data?.n2_resolution_note || "Hierarchical Leiden super-nodes sized by membership and colored by level."}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <div role="group" aria-label="Community source" className="ledger-segmented">
            {SOURCES.map((s) => (
              <button
                key={s.id}
                type="button"
                data-active={source === s.id}
                onClick={() => {
                  setSource(s.id);
                  setExpandedCid(null);
                }}
              >
                {s.label}
              </button>
            ))}
          </div>
          <input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Filter title or topic…"
            aria-label="Filter communities"
            className="ledger-input h-8 px-2.5 w-44"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="xl:col-span-2 space-y-4">
          <Panel title="Community Super-Node Map (Click Node to Open Report · Expand to Inspect Members)">
            <div className="border border-rule rounded bg-ground p-2">
              <svg viewBox="0 0 520 400" className="w-full max-h-[380px]" role="img" aria-label="Community super-node map">
                {(listQuery.data?.edges || []).map((e, i) => {
                  const s = coordById.get(e.source);
                  const t = coordById.get(e.target);
                  if (!s || !t) return null;
                  return (
                    <line
                      key={i}
                      x1={s.cx}
                      y1={s.cy}
                      x2={t.cx}
                      y2={t.cy}
                      stroke="var(--border)"
                      strokeWidth={Math.min(3, 0.8 + e.weight * 0.5)}
                      strokeOpacity={0.7}
                    />
                  );
                })}
                {layoutNodes.map(({ node, cx, cy, radius }) => {
                  const selected = node.community_id === activeCid;
                  const fill = node.level === 1 ? "#1d5fbf" : "#2a8c6a";
                  return (
                    <g
                      key={node.community_id}
                      role="button"
                      tabIndex={0}
                      aria-label={`${node.community_id} ${node.title} (${node.size} members)`}
                      onClick={() => onSelectCommunity(node.community_id)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          e.preventDefault();
                          onSelectCommunity(node.community_id);
                        }
                      }}
                      className="cursor-pointer focus:outline-none"
                    >
                      <circle
                        cx={cx}
                        cy={cy}
                        r={radius}
                        fill={fill}
                        fillOpacity={selected ? 0.95 : 0.72}
                        stroke={selected ? "var(--text)" : "var(--surface)"}
                        strokeWidth={selected ? 2.5 : 1.2}
                      />
                      <text
                        x={cx}
                        y={cy + 3}
                        textAnchor="middle"
                        fontSize="8"
                        fill="#ffffff"
                        pointerEvents="none"
                      >
                        {node.size}
                      </text>
                    </g>
                  );
                })}
              </svg>
            </div>
            <div className="mt-3 flex flex-wrap gap-1.5 text-xs">
              {(listQuery.data?.supernodes || []).slice(0, 18).map((n) => (
                <button
                  key={n.community_id}
                  type="button"
                  data-testid={`supernode-${n.community_id}`}
                  onClick={() => onSelectCommunity(n.community_id)}
                  className={`px-2 py-1 rounded border text-left ${
                    n.community_id === activeCid ? "border-[var(--accent)] bg-raised font-medium" : "border-border hover:bg-raised"
                  }`}
                >
                  <span className="font-mono text-[11px]">{n.community_id}</span> · {n.title.slice(0, 30)} ({n.size})
                </button>
              ))}
            </div>
          </Panel>

          <Panel title="Rising Researchers (2024–2025 vs 2021–2022)">
            <Table
              label="Rising researchers"
              headers={["Researcher", "Community", "Recent Papers", "Base Papers", "Share Ratio", "New Entrant"]}
              rows={(listQuery.data?.rising_researchers || []).map((r) => [
                <button key={r.id} type="button" onClick={() => onOpenNode360(r.id)} className="text-[var(--accent)] hover:underline text-left">
                  {r.name}
                </button>,
                `N1:${r.community}`,
                r.recent_papers,
                r.base_papers,
                r.share_ratio.toFixed(2),
                r.new_entrant ? "Yes" : "No",
              ])}
            />
          </Panel>
        </div>

        <div className="space-y-4">
          <Panel title={detail?.title || activeCid}>
            {detail ? (
              <div className="space-y-3 text-xs">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-mono px-1.5 py-0.5 rounded bg-raised">{detail.community_id}</span>
                  <span>Level {detail.level}</span>
                  <span>· {detail.size.toLocaleString()} members</span>
                  {detail.centrality_rating !== null && detail.centrality_rating !== undefined && (
                    <span>· Centrality {detail.centrality_rating}/10</span>
                  )}
                </div>

                {detail.ai_generated_label && (
                  <span className="inline-block px-2 py-0.5 rounded bg-raised font-medium">
                    {detail.ai_generated_label}
                  </span>
                )}

                {detail.summary ? (
                  <p className="text-ink leading-relaxed">{detail.summary}</p>
                ) : (
                  <p className="text-muted">No LLM report stored for this community size/partition.</p>
                )}

                {detail.key_findings && detail.key_findings.length > 0 && (
                  <div>
                    <h4 className="font-semibold mb-1">Key Findings & Citations</h4>
                    <ul className="list-disc pl-4 space-y-1 text-muted">
                      {detail.key_findings.map((kf, i) => (
                        <li key={i}>
                          {kf.claim}{" "}
                          {(kf.paper_ids || []).slice(0, 3).map((pid) => (
                            <button
                              key={pid}
                              type="button"
                              onClick={() => onOpenNode360(pid)}
                              className="font-mono text-[11px] text-[var(--accent)] hover:underline mr-1"
                            >
                              [{pid}]
                            </button>
                          ))}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {detail.hubs && detail.hubs.length > 0 && (
                  <div>
                    <h4 className="font-semibold mb-1">Hubs & Brokers</h4>
                    <p className="text-muted"><strong>Hubs:</strong> {detail.hubs.slice(0, 5).join(", ")}</p>
                    {detail.brokers && detail.brokers.length > 0 && (
                      <p className="text-muted"><strong>Brokers (participation):</strong> {detail.brokers.slice(0, 5).join(", ")}</p>
                    )}
                  </div>
                )}

                <div className="pt-2 border-t border-rule">
                  <button
                    type="button"
                    data-testid="expand-community-members"
                    onClick={() => setExpandedCid(detail.community_id)}
                    className="ledger-btn h-8 px-3 text-xs"
                  >
                    Expand members ({detail.size})
                  </button>
                </div>

                {expandedCid === detail.community_id && membersQuery.data && (
                  <div data-testid="community-members-panel" className="pt-2 border-t border-rule">
                    <h4 className="font-semibold mb-1">
                      Expanded Members ({membersQuery.data.members.length} of {membersQuery.data.total})
                    </h4>
                    <ul className="max-h-52 overflow-y-auto space-y-1">
                      {membersQuery.data.members.map((m) => (
                        <li key={m.id} className="flex justify-between gap-2 border-b border-rule pb-0.5">
                          <button type="button" onClick={() => onOpenNode360(m.id)} className="text-[var(--accent)] hover:underline truncate text-left">
                            {m.name}
                          </button>
                          <span className="text-faint shrink-0">{m.label}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-xs text-muted">Select a community super-node.</p>
            )}
          </Panel>
        </div>
      </div>
    </div>
  );
};
