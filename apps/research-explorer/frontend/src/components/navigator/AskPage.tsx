import React, { useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { navigatorApi } from "../../lib/navigatorApi";
import { AskResult } from "../../types/navigator";
import { Panel } from "../analytics/DashboardPrimitives";

interface AskPageProps {
  onOpenNode360: (id: string) => void;
}

export const AskPage: React.FC<AskPageProps> = ({ onOpenNode360 }) => {
  const [question, setQuestion] = useState("");
  const [mode, setMode] = useState<"auto" | "local" | "global">("auto");
  const [useCache, setUseCache] = useState(true);
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState("");
  const [streamedText, setStreamedText] = useState("");
  const [livePlan, setLivePlan] = useState<Array<{ tool: string; args: Record<string, unknown>; purpose?: string }>>([]);
  const [liveSteps, setLiveSteps] = useState<Array<Record<string, unknown>>>([]);
  const [result, setResult] = useState<AskResult | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [activeHop, setActiveHop] = useState<number | "all">("all");
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
    setStatusMsg("Starting…");
    setStreamedText("");
    setLivePlan([]);
    setLiveSteps([]);
    setResult(null);
    setActiveHop("all");

    await navigatorApi.askStream(
      { question: trimmed, mode: qMode, use_cache: qCache, resolved_overrides: overrides },
      {
        onStatus: (d) => setStatusMsg(`${String(d.stage || "running")} (${String(d.mode || qMode)})`),
        onPlan: (d) => setLivePlan((d.plan as any[]) || []),
        onStep: (d) => setLiveSteps((prev) => [...prev, d]),
        onToken: (d) => setStreamedText((prev) => prev + (d.text || "")),
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

  const shownSubgraph = useMemo(() => {
    const sg = result?.subgraph || { nodes: [], edges: [] };
    const edges =
      activeHop === "all" ? sg.edges : sg.edges.filter((e) => (e.hop ?? 1) <= activeHop);
    const keepIds = new Set<string>();
    edges.forEach((e) => {
      keepIds.add(e.source);
      keepIds.add(e.target);
    });
    const nodes =
      activeHop === "all"
        ? sg.nodes.slice(0, 24)
        : sg.nodes.filter((n) => (n.hop ?? 0) <= activeHop || keepIds.has(n.id)).slice(0, 24);
    return { nodes, edges: edges.slice(0, 32) };
  }, [result, activeHop]);

  // Lay out highlighted subgraph deterministically on SVG
  const sgLayout = useMemo(() => {
    const n = Math.max(shownSubgraph.nodes.length, 1);
    return shownSubgraph.nodes.map((node, i) => {
      const ang = (2 * Math.PI * i) / n - Math.PI / 2;
      return {
        node,
        x: 230 + 145 * Math.cos(ang),
        y: 160 + 105 * Math.sin(ang),
      };
    });
  }, [shownSubgraph]);

  const sgCoord = useMemo(
    () => new Map(sgLayout.map((item) => [item.node.id, { x: item.x, y: item.y }])),
    [sgLayout],
  );

  const plan = result?.plan || livePlan;
  const steps = result?.steps || liveSteps;

  return (
    <div data-testid="page-ask" className="p-4 sm:p-6 space-y-4 overflow-y-auto h-full">
      <div className="ledger-panel p-4 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h1 className="text-lg font-semibold text-ink">Ask the Research Graph (GraphRAG + Multi-Hop)</h1>
            <p className="text-xs text-muted">
              The SLM plans over a closed 9-tool read-only set; every number in the answer is verified against retrieved tool outputs.
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

      {(streamedText || result || steps.length > 0) && (
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
                    className="px-2 py-0.5 rounded bg-raised font-medium"
                  >
                    Faithfulness: {result.faithfulness.passed ? "Verified" : `Warnings (${result.faithfulness.errors.length})`}
                  </span>
                )}
              </div>
              <p data-testid="ask-answer-text" className="text-sm text-ink whitespace-pre-wrap leading-relaxed">
                {streamedText || "Waiting for grounded synthesis…"}
              </p>
              {result?.citations && result.citations.length > 0 && (
                <div data-testid="ask-citations" className="mt-3 pt-2 border-t border-rule text-xs">
                  <span className="font-semibold mr-2">Cited Papers:</span>
                  {result.citations.map((pid) => (
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
              <div data-testid="ask-trace" className="space-y-2.5 text-xs max-h-96 overflow-y-auto">
                {steps.map((st: any, i) => (
                  <div key={i} className="p-2.5 rounded border border-border bg-ground space-y-1">
                    <div className="flex justify-between font-mono text-[11px]">
                      <span className="font-semibold">Step {i + 1}: {st.tool}</span>
                      <span className="text-muted">{Array.isArray(st.rows) ? `${st.rows.length} rows` : ""}</span>
                    </div>
                    <div className="text-[11px] text-faint font-mono truncate">{JSON.stringify(st.args || {})}</div>
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
            <div className="flex flex-wrap items-center gap-1.5 mb-2 text-xs">
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
            <div data-testid="ask-subgraph" className="border border-rule rounded bg-ground p-2">
              {sgLayout.length === 0 ? (
                <p className="text-xs text-muted p-4">No subgraph edges returned for this trace.</p>
              ) : (
                <svg viewBox="0 0 460 320" className="w-full max-h-[340px]" role="img" aria-label="Ask union subgraph">
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
                        strokeWidth={1.6}
                        strokeOpacity={0.7}
                      />
                    );
                  })}
                  {sgLayout.map(({ node, x, y }) => (
                    <g
                      key={node.id}
                      role="button"
                      tabIndex={0}
                      onClick={() => onOpenNode360(node.id)}
                      className="cursor-pointer"
                    >
                      <circle cx={x} cy={y} r={10} fill="#1d5fbf" stroke="var(--surface)" strokeWidth={1.5} />
                      <text x={x} y={y + 20} textAnchor="middle" fontSize="9" fill="var(--text)">
                        {(node.name || node.id).slice(0, 20)}
                      </text>
                    </g>
                  ))}
                </svg>
              )}
            </div>
          </Panel>
        </div>
      )}
    </div>
  );
};
