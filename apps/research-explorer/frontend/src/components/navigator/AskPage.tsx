import React, { useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { navigatorApi } from "../../lib/navigatorApi";
import { AskResult } from "../../types/navigator";
import { Panel } from "../analytics/DashboardPrimitives";

interface AskPageProps {
  onOpenNode360: (id: string) => void;
}

type SgNode = { id: string; label?: string; name?: string; hop?: number };
type SgEdge = { source: string; target: string; relation?: string; support_count?: number; hop?: number };

function renderBoldInline(text: string): React.ReactNode {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((p, idx) =>
    p.startsWith("**") && p.endsWith("**") && p.length > 4 ? (
      <strong key={idx} className="font-semibold text-ink">
        {p.slice(2, -2)}
      </strong>
    ) : (
      <React.Fragment key={idx}>{p}</React.Fragment>
    ),
  );
}

const FormattedAnswer: React.FC<{ text: string }> = ({ text }) => {
  const lines = text.split("\n");
  return (
    <div data-testid="ask-answer-text" className="text-sm text-ink space-y-1.5 leading-relaxed">
      {lines.map((raw, idx) => {
        const line = raw.trim();
        if (!line) return <div key={idx} className="h-1" />;
        const bulletMatch = line.match(/^(?:[-*]|\d+\.)\s+(.*)$/);
        if (bulletMatch) {
          return (
            <div key={idx} className="flex items-start gap-2 pl-2">
              <span className="text-muted select-none">•</span>
              <span className="min-w-0 flex-1">{renderBoldInline(bulletMatch[1])}</span>
            </div>
          );
        }
        return <p key={idx}>{renderBoldInline(line)}</p>;
      })}
    </div>
  );
};

export const AskPage: React.FC<AskPageProps> = ({ onOpenNode360 }) => {
  const [question, setQuestion] = useState("");
  const [mode, setMode] = useState<"auto" | "local" | "global">("auto");
  const [useCache, setUseCache] = useState(true);
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState("");
  const [streamedText, setStreamedText] = useState("");
  const [liveLinked, setLiveLinked] = useState<Array<Record<string, unknown>>>([]);
  const [livePlan, setLivePlan] = useState<Array<{ tool: string; args: Record<string, unknown>; purpose?: string }>>([]);
  const [liveSteps, setLiveSteps] = useState<Array<Record<string, unknown>>>([]);
  const [liveSubgraph, setLiveSubgraph] = useState<{ nodes: SgNode[]; edges: SgEdge[] }>({ nodes: [], edges: [] });
  const [liveCitations, setLiveCitations] = useState<string[]>([]);
  const [result, setResult] = useState<AskResult | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [activeHop, setActiveHop] = useState<number | "all">("all");
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const demosQuery = useQuery({
    queryKey: ["nav-ask-demos"],
    queryFn: ({ signal }) => navigatorApi.getAskDemos(signal),
  });

  const runQuestion = async (
    qText: string,
    qMode: "auto" | "local" | "global" = mode,
    qCache: boolean = useCache,
    overrides?: Record<string, string>,
  ) => {
    const trimmed = qText.trim();
    if (!trimmed) return;
    abortRef.current?.abort();
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    setLoading(true);
    setErrorMsg(null);
    setStatusMsg("Parsing question…");
    setStreamedText("");
    setLiveLinked([]);
    setLivePlan([]);
    setLiveSteps([]);
    setLiveSubgraph({ nodes: [], edges: [] });
    setLiveCitations([]);
    setResult(null);
    setActiveHop("all");
    setHoveredNodeId(null);

    await navigatorApi.askStream(
      { question: trimmed, mode: qMode, use_cache: qCache, resolved_overrides: overrides },
      {
        onStatus: (d) => setStatusMsg(`${String(d.stage || "running")} (${String(d.mode || qMode)})`),
        onParsed: (d) => {
          if (Array.isArray(d.linked)) setLiveLinked(d.linked);
        },
        onPlan: (d) => setLivePlan((d.plan as Array<{ tool: string; args: Record<string, unknown>; purpose?: string }>) || []),
        onStep: (d) => setLiveSteps((prev) => [...prev, d]),
        onSubgraph: (sg) =>
          setLiveSubgraph({
            nodes: sg.nodes || [],
            edges: sg.edges || [],
          }),
        onToken: (d) => setStreamedText((prev) => prev + (d.text || "")),
        onCitations: (c) => setLiveCitations(c.paper_ids || []),
        onAmbiguous: (res) => {
          setResult(res as unknown as AskResult);
          setStatusMsg("Disambiguation required");
          setLoading(false);
        },
        onFinal: (res) => {
          setResult(res);
          setStreamedText(res.answer || "");
          setStatusMsg(res.from_cache ? "Served from scripted demo cache" : "Completed");
          setLoading(false);
        },
        onError: (err) => {
          setErrorMsg(err);
          setLoading(false);
        },
      },
      ctrl.signal,
    );
    setLoading(false);
  };

  const activeSubgraph = result?.subgraph || liveSubgraph;

  const shownSubgraph = useMemo(() => {
    const sg = activeSubgraph || { nodes: [], edges: [] };
    const edges =
      activeHop === "all" ? sg.edges : sg.edges.filter((e) => (e.hop ?? 1) <= activeHop);
    const keepIds = new Set<string>();
    edges.forEach((e) => {
      keepIds.add(e.source);
      keepIds.add(e.target);
    });
    const nodes =
      activeHop === "all"
        ? sg.nodes.slice(0, 26)
        : sg.nodes.filter((n) => (n.hop ?? 0) <= activeHop || keepIds.has(n.id)).slice(0, 26);
    return { nodes, edges: edges.slice(0, 40) };
  }, [activeSubgraph, activeHop]);

  // Concentric-by-hop + deterministic force-repulsion layout on 600x400 SVG canvas
  const sgLayout = useMemo(() => {
    const nodes = shownSubgraph.nodes;
    if (!nodes.length) return [];
    const W = 600;
    const H = 400;
    const cx = W / 2;
    const cy = H / 2;

    const byHop = new Map<number, SgNode[]>();
    nodes.forEach((nd, idx) => {
      const h = idx === 0 ? 0 : Math.max(1, Math.min(3, Number(nd.hop ?? 1)));
      const arr = byHop.get(h) || [];
      arr.push(nd);
      byHop.set(h, arr);
    });

    const pos = new Map<string, { x: number; y: number }>();
    const sortedHops = Array.from(byHop.keys()).sort((a, b) => a - b);
    sortedHops.forEach((h, ringIdx) => {
      const arr = byHop.get(h) || [];
      const radius = arr.length === 1 && ringIdx === 0 ? 0 : 75 + ringIdx * 72;
      arr.forEach((nd, i) => {
        const ang = (2 * Math.PI * i) / Math.max(arr.length, 1) - Math.PI / 2 + ringIdx * 0.35;
        pos.set(nd.id, {
          x: cx + radius * Math.cos(ang),
          y: cy + radius * Math.sin(ang) * 0.85,
        });
      });
    });

    // Repulsion + edge attraction + bounds clamp
    const ids = nodes.map((n) => n.id);
    for (let iter = 0; iter < 60; iter++) {
      for (let i = 0; i < ids.length; i++) {
        for (let j = i + 1; j < ids.length; j++) {
          const p1 = pos.get(ids[i])!;
          const p2 = pos.get(ids[j])!;
          const dx = p2.x - p1.x;
          const dy = p2.y - p1.y;
          const dist = Math.hypot(dx, dy) || 0.1;
          const minDist = 52;
          if (dist < minDist) {
            const push = ((minDist - dist) / dist) * 0.45;
            p1.x -= dx * push;
            p1.y -= dy * push;
            p2.x += dx * push;
            p2.y += dy * push;
          }
        }
      }
      for (const e of shownSubgraph.edges) {
        const ps = pos.get(e.source);
        const pt = pos.get(e.target);
        if (!ps || !pt) continue;
        const dx = pt.x - ps.x;
        const dy = pt.y - ps.y;
        const dist = Math.hypot(dx, dy) || 1;
        if (dist > 130) {
          const pull = ((dist - 130) / dist) * 0.05;
          ps.x += dx * pull;
          ps.y += dy * pull;
          pt.x -= dx * pull;
          pt.y -= dy * pull;
        }
      }
      for (const id of ids) {
        const p = pos.get(id)!;
        p.x = Math.max(42, Math.min(W - 42, p.x));
        p.y = Math.max(32, Math.min(H - 32, p.y));
      }
    }

    return nodes.map((node) => {
      const p = pos.get(node.id)!;
      return { node, x: p.x, y: p.y };
    });
  }, [shownSubgraph]);

  const sgCoord = useMemo(
    () => new Map(sgLayout.map((item) => [item.node.id, { x: item.x, y: item.y }])),
    [sgLayout],
  );

  // Label all nodes when <= 10; when crowded (> 10), label ONLY the primary anchor + hovered/focused node
  const visibleLabelIds = useMemo(() => {
    const ids = new Set<string>();
    if (sgLayout.length <= 10) {
      sgLayout.forEach((it) => ids.add(it.node.id));
    } else if (sgLayout[0]) {
      ids.add(sgLayout[0].node.id);
    }
    if (hoveredNodeId) ids.add(hoveredNodeId);
    return ids;
  }, [sgLayout, hoveredNodeId]);

  const plan = result?.plan?.length ? result.plan : livePlan;
  const steps = result?.steps?.length ? result.steps : liveSteps;
  const citations = result?.citations?.length ? result.citations : liveCitations;
  const linkedList = Array.isArray(result?.linked) ? result.linked : liveLinked;

  return (
    <div data-testid="page-ask" className="p-4 sm:p-6 space-y-4 overflow-y-auto h-full">
      <div className="ledger-panel p-4 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h1 className="text-lg font-semibold text-ink">Ask the Research Graph (GraphRAG + Multi-Hop)</h1>
            <p className="text-xs text-muted">
              The SLM plans over a closed 9-tool read-only set; every number, entity, and paper ID in the answer is verified against retrieved tool outputs.
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs">
            <div role="group" aria-label="Retrieval mode" className="ledger-segmented">
              {(["auto", "local", "global"] as const).map((m) => (
                <button key={m} type="button" data-active={mode === m} onClick={() => setMode(m)}>
                  {m.charAt(0).toUpperCase() + m.slice(1)}
                </button>
              ))}
            </div>
            <label className="inline-flex items-center gap-1 cursor-pointer">
              <input type="checkbox" checked={useCache} onChange={(e) => setUseCache(e.target.checked)} />
              <span>Use demo cache</span>
            </label>
          </div>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            void runQuestion(question);
          }}
          className="flex gap-2"
        >
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a multi-hop, trend, or corpus question…"
            aria-label="Ask research question"
            data-testid="ask-input"
            className="ledger-input flex-1 h-9 px-3 text-sm"
          />
          <button
            type="submit"
            disabled={loading}
            data-testid="ask-submit"
            className="ledger-btn h-9 px-4 text-xs font-medium bg-[var(--primary)] text-[var(--primary-ink)]"
          >
            {loading ? "Running…" : "Ask"}
          </button>
        </form>

        <div className="flex flex-wrap gap-1.5 text-xs">
          {(demosQuery.data?.demos || []).map((d) => (
            <button
              key={d.demo_id}
              type="button"
              data-testid={`demo-btn-${d.demo_id}`}
              onClick={() => {
                setQuestion(d.question);
                setMode(d.mode as "auto" | "local" | "global");
                void runQuestion(d.question, d.mode as "auto" | "local" | "global", useCache);
              }}
              className="px-2 py-1 rounded border border-border hover:bg-raised text-left"
              title={d.question}
            >
              {d.title}
            </button>
          ))}
        </div>
      </div>

      {errorMsg && <p role="alert" className="text-sm text-[var(--negative)] px-1">{errorMsg}</p>}
      {statusMsg && <p role="status" className="text-xs text-muted px-1">{statusMsg}</p>}

      {result?.ambiguous && result.ambiguous.length > 0 && (
        <Panel title="Same-Name Entity Disambiguation Required">
          {result.ambiguous.map((amb) => (
            <div key={amb.slot} className="space-y-1 text-xs mb-2">
              <p className="text-muted">Multiple researchers match &ldquo;{amb.query}&rdquo;. Pick one to re-run without merging identities:</p>
              <div className="flex flex-wrap gap-1.5">
                {amb.candidates.map((c) => (
                  <button
                    key={c.id}
                    type="button"
                    onClick={() => void runQuestion(question, mode, false, { [amb.slot]: c.id })}
                    className="px-2 py-1 rounded border border-control hover:bg-raised"
                  >
                    {c.name} <span className="font-mono text-[10px] text-faint">({c.id})</span>
                  </button>
                ))}
              </div>
            </div>
          ))}
        </Panel>
      )}

      {(streamedText || result || steps.length > 0 || plan.length > 0 || linkedList.length > 0) && (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          <div className="space-y-4">
            <Panel title="Grounded Answer">
              <div className="flex flex-wrap items-center gap-2 text-[11px] mb-2">
                <span className="px-2 py-0.5 rounded bg-raised font-medium">
                  {result?.ai_generated_label || "AI-generated from graph data"}
                </span>
                {result?.faithfulness && (
                  <span
                    data-testid="faithfulness-badge"
                    className={`px-2 py-0.5 rounded font-medium ${
                      result.faithfulness.passed
                        ? "bg-[var(--pill-positive-bg)] text-[var(--pill-positive-ink)]"
                        : "bg-[var(--pill-warning-bg)] text-[var(--pill-warning-ink)]"
                    }`}
                  >
                    Faithfulness: {result.faithfulness.passed ? "Verified" : `Warnings (${result.faithfulness.errors.length})`}
                  </span>
                )}
              </div>
              {streamedText ? (
                <FormattedAnswer text={streamedText} />
              ) : (
                <p data-testid="ask-answer-text" className="text-sm text-muted">
                  Executing graph steps before grounded synthesis…
                </p>
              )}
              {citations.length > 0 && (
                <div data-testid="ask-citations" className="mt-3 pt-2 border-t border-rule text-xs">
                  <span className="font-semibold mr-2">Cited Papers:</span>
                  {citations.map((pid) => (
                    <button
                      key={pid}
                      type="button"
                      onClick={() => onOpenNode360(pid)}
                      className="inline-block mr-1.5 mb-1 px-1.5 py-0.5 rounded border border-border font-mono text-[11px] text-[var(--accent)] hover:bg-raised"
                    >
                      {pid}
                    </button>
                  ))}
                </div>
              )}
            </Panel>

            <Panel title={`Reasoning Trace (${plan.length} planned · ${steps.length} executed)`}>
              {linkedList.length > 0 && (
                <div className="mb-2 flex flex-wrap gap-1.5 text-[11px]">
                  <span className="text-muted">Linked:</span>
                  {linkedList.map((lk: Record<string, unknown>, idx) => (
                    <span key={idx} className="px-1.5 py-0.5 rounded bg-ground border border-rule font-mono">
                      {String(lk.name || lk.text)} ({String(lk.id || "unlinked")})
                    </span>
                  ))}
                </div>
              )}
              <div data-testid="ask-trace" className="space-y-2.5 text-xs max-h-96 overflow-y-auto">
                {steps.map((st: Record<string, unknown>, i) => (
                  <div key={i} className="p-2.5 rounded border border-border bg-ground space-y-1">
                    <div className="flex justify-between font-mono text-[11px]">
                      <span className="font-semibold">Step {i + 1}: {String(st.tool)}</span>
                      <span className="text-muted">{Array.isArray(st.rows) ? `${st.rows.length} rows` : ""}</span>
                    </div>
                    <div className="text-[11px] text-faint font-mono truncate">{JSON.stringify(st.args || {})}</div>
                    {Boolean(st.note) && <div className="text-[11px] text-muted">{String(st.note)}</div>}
                    {Array.isArray(st.rows) && st.rows.length > 0 && (
                      <pre className="text-[11px] overflow-x-auto bg-surface p-1.5 rounded border border-rule max-h-32">
                        {JSON.stringify(st.rows.slice(0, 5), null, 1)}
                      </pre>
                    )}
                  </div>
                ))}
              </div>
            </Panel>
          </div>

          <Panel title="Highlighted Retrieval Subgraph (Hop-by-Hop)">
            <div className="flex flex-wrap items-center justify-between gap-2 mb-2 text-xs">
              <div className="flex flex-wrap items-center gap-1.5">
                <button
                  type="button"
                  onClick={() => setActiveHop("all")}
                  className={`px-2 py-0.5 rounded border ${activeHop === "all" ? "bg-raised border-control" : "border-border"}`}
                >
                  All Hops
                </button>
                {[1, 2, 3].map((h) => (
                  <button
                    key={h}
                    type="button"
                    onClick={() => setActiveHop(h)}
                    className={`px-2 py-0.5 rounded border ${activeHop === h ? "bg-raised border-control" : "border-border"}`}
                  >
                    Up to Hop {h}
                  </button>
                ))}
              </div>
              {sgLayout.length > 10 && (
                <span className="text-[11px] text-faint">Hover or focus any node to read its label</span>
              )}
            </div>
            <div data-testid="ask-subgraph" className="border border-rule rounded bg-ground p-2">
              {sgLayout.length === 0 ? (
                <p className="text-xs text-muted p-4">No subgraph edges returned for this trace.</p>
              ) : (
                <svg viewBox="0 0 600 400" className="w-full max-h-[380px]" role="img" aria-label="Ask union subgraph">
                  {shownSubgraph.edges.map((e, idx) => {
                    const s = sgCoord.get(e.source);
                    const t = sgCoord.get(e.target);
                    if (!s || !t) return null;
                    return (
                      <line
                        key={idx}
                        x1={s.x}
                        y1={s.y}
                        x2={t.x}
                        y2={t.y}
                        stroke="var(--accent)"
                        strokeWidth={1.4}
                        strokeOpacity={0.55}
                      />
                    );
                  })}
                  {sgLayout.map(({ node, x, y }) => {
                    const isHovered = hoveredNodeId === node.id;
                    const isAnchor = (node.hop ?? 1) === 1 && sgLayout.length > 10 && node.id === sgLayout[0]?.node.id;
                    return (
                      <g
                        key={node.id}
                        role="button"
                        tabIndex={0}
                        aria-label={`${node.name || node.id} (hop ${node.hop ?? 1})`}
                        onMouseEnter={() => setHoveredNodeId(node.id)}
                        onMouseLeave={() => setHoveredNodeId(null)}
                        onFocus={() => setHoveredNodeId(node.id)}
                        onBlur={() => setHoveredNodeId(null)}
                        onClick={() => onOpenNode360(node.id)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter" || e.key === " ") {
                            e.preventDefault();
                            onOpenNode360(node.id);
                          }
                        }}
                        className="cursor-pointer focus:outline-none"
                      >
                        <circle
                          cx={x}
                          cy={y}
                          r={isAnchor || isHovered ? 11 : 8}
                          fill={isHovered ? "var(--positive)" : "#1d5fbf"}
                          stroke="var(--surface)"
                          strokeWidth={1.6}
                        />
                      </g>
                    );
                  })}
                  {sgLayout
                    .filter(({ node }) => visibleLabelIds.has(node.id))
                    .map(({ node, x, y }) => {
                      const label = (node.name || node.id).slice(0, 26);
                      const w = Math.min(180, label.length * 6 + 12);
                      const lx = Math.max(6, Math.min(600 - w - 6, x - w / 2));
                      const ly = y + 14 > 376 ? y - 28 : y + 12;
                      return (
                        <g key={`lbl-${node.id}`} pointerEvents="none">
                          <rect x={lx} y={ly} width={w} height={17} rx={4} fill="var(--surface)" fillOpacity={0.92} stroke="var(--border)" />
                          <text x={lx + w / 2} y={ly + 12} textAnchor="middle" fontSize="9.5" fill="var(--text)">
                            {label}
                          </text>
                        </g>
                      );
                    })}
                </svg>
              )}
            </div>
          </Panel>
        </div>
      )}
    </div>
  );
};
