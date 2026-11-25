import React, { useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { navigatorApi } from "../../lib/navigatorApi";
import { AskCitation, AskCitationsEvent, AskResult, AskResultPapers } from "../../types/navigator";
import { Panel } from "../analytics/DashboardPrimitives";
import { MetricTooltip } from "./MetricTooltip";

interface AskPageProps {
  onOpenNode360: (id: string) => void;
}

type SgNode = { id: string; label?: string; name?: string; hop?: number };
type SgEdge = { source: string; target: string; relation?: string; support_count?: number; hop?: number };

type RefHandlers = { onStep: (n: number) => void; onPaper: (id: string) => void };

const PAPER_ID_SRC = "paper:(?:aaai|ijcai):\\d{4}:[A-Za-z0-9_.-]*[A-Za-z0-9_-]";
const INLINE_REF_RE = new RegExp(`(\\[steps? [0-9, ]+\\]|\\[${PAPER_ID_SRC}(?:\\s*[,;]\\s*${PAPER_ID_SRC})*\\])`, "g");

/** Render inline `[step N]` references (aggregate claims) and `[paper:…]` citations as chips. */
function renderRefs(text: string, keyBase: string, h?: RefHandlers): React.ReactNode {
  if (!h) return text;
  const parts = text.split(INLINE_REF_RE);
  return parts.map((p, idx) => {
    const stepMatch = p.match(/^\[steps? ([0-9, ]+)\]$/);
    if (stepMatch) {
      const nums = stepMatch[1].split(/[ ,]+/).filter(Boolean).map(Number);
      return (
        <React.Fragment key={`${keyBase}-${idx}`}>
          {nums.map((n) => (
            <button
              key={n}
              type="button"
              data-testid="answer-step-ref"
              onClick={() => h.onStep(n)}
              title={`Aggregate claim computed by trace step ${n}; its example papers are listed under "Papers in this result".`}
              className="mx-0.5 px-1 rounded border border-border font-mono text-[11px] text-muted hover:bg-raised"
            >
              step {n}
            </button>
          ))}
        </React.Fragment>
      );
    }
    if (p.startsWith("[paper:") && p.endsWith("]")) {
      const ids = p.slice(1, -1).split(/\s*[,;]\s*/).filter(Boolean);
      return (
        <React.Fragment key={`${keyBase}-${idx}`}>
          {ids.map((pid) => (
            <button
              key={pid}
              type="button"
              data-testid="answer-citation-ref"
              onClick={() => h.onPaper(pid)}
              title="Citation: this paper is returned as its own row or abstract excerpt and the sentence is about it."
              className="mx-0.5 px-1 rounded border border-border font-mono text-[11px] text-[var(--accent)] hover:bg-raised"
            >
              {pid}
            </button>
          ))}
        </React.Fragment>
      );
    }
    return <React.Fragment key={`${keyBase}-${idx}`}>{p}</React.Fragment>;
  });
}

function renderBoldInline(text: string, h?: RefHandlers): React.ReactNode {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((p, idx) =>
    p.startsWith("**") && p.endsWith("**") && p.length > 4 ? (
      <strong key={idx} className="font-semibold text-ink">
        {renderRefs(p.slice(2, -2), `b${idx}`, h)}
      </strong>
    ) : (
      <React.Fragment key={idx}>{renderRefs(p, `t${idx}`, h)}</React.Fragment>
    ),
  );
}

const FormattedAnswer: React.FC<{ text: string; refs?: RefHandlers }> = ({ text, refs }) => {
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
              <span className="min-w-0 flex-1">{renderBoldInline(bulletMatch[1], refs)}</span>
            </div>
          );
        }
        return <p key={idx}>{renderBoldInline(line, refs)}</p>;
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
  const [liveEvidence, setLiveEvidence] = useState<AskCitationsEvent>({});
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
    setLiveEvidence({});
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
        onCitations: (c) => setLiveEvidence(c || {}),
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
  const citations: AskCitation[] = (result?.evidence_labelling ? result.citations : liveEvidence.citations) || [];
  const resultPapers: AskResultPapers[] =
    (result?.evidence_labelling ? result.result_papers : liveEvidence.result_papers) || [];
  const refHandlers: RefHandlers = {
    onStep: (n) => {
      const el = document.getElementById(`ask-step-${n}`);
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "nearest" });
        el.focus({ preventScroll: true });
      }
    },
    onPaper: onOpenNode360,
  };
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
                  <>
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
                    <MetricTooltip
                      label="Faithfulness check"
                      definition="Verifies every number, bracketed paper/entity ID, and named entity in the answer appears verbatim in the retrieved graph trace."
                    />
                  </>
                )}
              </div>
              {streamedText ? (
                <FormattedAnswer text={streamedText} refs={refHandlers} />
              ) : (
                <p data-testid="ask-answer-text" className="text-sm text-muted">
                  Executing graph steps before grounded synthesis…
                </p>
              )}
              {(citations.length > 0 || resultPapers.length > 0) && (
                <div className="mt-3 pt-2 border-t border-rule text-xs space-y-2">
                  <div data-testid="ask-citations">
                    <div className="flex items-center gap-1 mb-1">
                      <span className="font-semibold">Citations</span>
                      <span className="text-muted">({citations.length})</span>
                      <MetricTooltip
                        label="Citation"
                        definition="A specific paper supporting a specific sentence: the trace returns that paper as its own row (papers tool) or as an abstract excerpt (local search). Aggregate claims (counts, shares, rankings) point to their trace step instead."
                      />
                    </div>
                    {citations.length === 0 ? (
                      <p data-testid="ask-citations-empty" className="text-muted">
                        No sentence cites a single paper: the claims are aggregates over the graph, and each points to the trace step that computed it.
                      </p>
                    ) : (
                      <ul className="space-y-1">
                        {citations.map((c, i) => (
                          <li key={`${c.paper_id}-${i}`} data-testid="ask-citation-item" className="flex items-start gap-2">
                            <button
                              type="button"
                              onClick={() => onOpenNode360(c.paper_id)}
                              className="shrink-0 px-1.5 py-0.5 rounded border border-border font-mono text-[11px] text-[var(--accent)] hover:bg-raised"
                            >
                              {c.paper_id}
                            </button>
                            <span className="text-muted min-w-0">supports: &ldquo;{c.sentence}&rdquo;</span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                  {resultPapers.length > 0 && (
                    <div data-testid="ask-result-papers">
                      <div className="flex items-center gap-1 mb-1">
                        <span className="font-semibold">Papers in this result</span>
                        <MetricTooltip
                          label="Papers in this result"
                          definition="Example papers behind a step's count or list, returned with the graph rows. They illustrate the result; a single paper's abstract usually does not state the aggregate claim, so they are not shown as citations."
                        />
                      </div>
                      {resultPapers.map((rp) => (
                        <div key={rp.step} data-testid="ask-result-papers-step" className="mb-1">
                          <button
                            type="button"
                            onClick={() => refHandlers.onStep(rp.step)}
                            className="mr-1.5 text-muted underline decoration-dotted"
                          >
                            Step {rp.step}
                            {rp.tool ? ` · ${rp.tool}` : ""} · {rp.paper_ids.length} example paper{rp.paper_ids.length === 1 ? "" : "s"}
                          </button>
                          {rp.paper_ids.slice(0, 8).map((pid) => (
                            <button
                              key={pid}
                              type="button"
                              onClick={() => onOpenNode360(pid)}
                              className="inline-block mr-1.5 mb-1 px-1.5 py-0.5 rounded border border-border font-mono text-[11px] text-[var(--accent)] hover:bg-raised"
                            >
                              {pid}
                            </button>
                          ))}
                          {rp.paper_ids.length > 8 && (
                            <span className="text-faint">+{rp.paper_ids.length - 8} more</span>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
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
                  <div
                    key={i}
                    id={`ask-step-${Number(st.step ?? i + 1)}`}
                    tabIndex={-1}
                    data-testid="ask-trace-step"
                    className="p-2.5 rounded border border-border bg-ground space-y-1 focus:outline focus:outline-1 focus:outline-[var(--accent)]"
                  >
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
