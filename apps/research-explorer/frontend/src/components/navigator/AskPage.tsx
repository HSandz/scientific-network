import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AskMethodNote } from "./methodNotes";
import { MethodDrawer } from "../ui/primitives";
import { useQuery } from "@tanstack/react-query";
import { navigatorApi } from "../../lib/navigatorApi";
import { navigate, pathFor, useRoute } from "../../lib/router";
import { newId, titleFor, useConversations, type StoredTurn } from "../../lib/conversations";
import {
  buildGraph,
  buildNameIndex,
  buildTables,
  chooseChart,
  describeResult,
  describeStep,
  followUps,
  footnoteAnswer,
  recognisedText,
  type Block,
  type PlainStep,
} from "../../lib/askModel";
import { displayName, orgName } from "../../lib/names";
import type { AskDemoItem } from "../../types/navigator";
import { Icon } from "../shell/icons";
import { EvidencePanel, type EvidenceData, type EvidenceTab } from "../ask/EvidencePanel";
import { turnFromResult, useAskTurn, type AskMode, type TurnView } from "../ask/useAskTurn";

/* ---------- Starter questions grouped by intent (from the scripted demos) ---------- */
const INTENTS: Array<{ name: string; icon: string; items: Array<[string, string]> }> = [
  { name: "Trends", icon: "trends", items: [["demo-02-rising-methods-diffusion-orgs", "Ranks methods by growth"]] },
  {
    name: "Groups",
    icon: "groups",
    items: [
      ["demo-01-worked-example", "Follows collaborations, then compares shares"],
      ["demo-05-causal-lift", "Ranks organizations by specialisation"],
    ],
  },
  {
    name: "Connections",
    icon: "network",
    items: [
      ["demo-03-method-task-cooccurrence", "Walks from a method to tasks and datasets"],
      ["demo-04-researcher-path", "Finds how two researchers are connected"],
    ],
  },
  {
    name: "Overview",
    icon: "pulse",
    items: [
      ["pulse", "Opens the overview"],
      ["demo-06-global-communities", "Reads the summaries of every research community"],
      ["demo-07-local-gnn", "Gathers what the graph says about one subject"],
    ],
  },
];

const MODEL_LINE = "Written by a 4-billion-parameter language model from the graph";

function toStored(t: TurnView): StoredTurn {
  return {
    id: t.id,
    question: t.question,
    mode: t.mode,
    askedAt: new Date().toISOString(),
    elapsedSeconds: t.elapsedSeconds,
    result: t.result,
    error: t.error,
  };
}

/* ---------- Derived view of one turn ---------- */
interface TurnModel {
  plainSteps: PlainStep[];
  executedCount: number;
  blocks: Block[];
  evidence: EvidenceData;
  follow: string[];
}

function modelFor(t: TurnView): TurnModel {
  const idx = buildNameIndex(t.linked, t.steps, t.subgraph);
  const planned = t.plan?.length ? t.plan.map((p, i) => ({ tool: p.tool, args: p.args || {}, step: i + 1 })) : t.steps.map((s) => ({ tool: s.tool, args: s.args || {}, step: s.step }));
  const plainSteps: PlainStep[] = [];
  const understood = t.planArrived || t.steps.length > 0 || t.status !== "running";
  plainSteps.push({ key: "read", title: "Read the question and find the names it mentions", result: understood ? recognisedText(t.linked, t.parsed) : undefined, state: understood ? "done" : "active" });
  let prevDone = understood;
  for (const p of planned) {
    const ex = t.steps.find((s) => s.step === p.step);
    const state: PlainStep["state"] = ex ? (ex.error ? "error" : "done") : prevDone && t.status === "running" ? "active" : "pending";
    plainSteps.push({ key: `s${p.step}`, title: describeStep(p.tool, p.args, idx, t.mode), result: ex ? describeResult(ex, idx) : undefined, state, stepNumber: p.step });
    prevDone = !!ex;
  }
  if (!planned.length && t.status === "running" && (t.stage === "global_map_reduce" || t.stage === "local_retrieve")) {
    plainSteps.push({ key: "retrieve", title: t.stage === "global_map_reduce" ? "Read the summaries of the research communities" : "Gather what the graph says about the subject", state: "active" });
    prevDone = false;
  }
  const passed = t.result?.faithfulness?.passed;
  if (t.status !== "ambiguous") {
    plainSteps.push({
      key: "write",
      title: "Write the answer and check every number against the results",
      result: t.result ? (passed ? "All numbers matched" : "Some statements did not match the data") : undefined,
      state: t.result ? (passed ? "done" : "error") : prevDone && t.status === "running" && (planned.length > 0 || t.steps.length > 0) ? "active" : t.status === "error" ? "error" : "pending",
    });
  }
  const tables = buildTables(t.steps, idx);
  const resultPapers = (t.evidence.result_papers || []).map((r) => ({ step: r.step, paper_ids: r.paper_ids }));
  const { blocks, footnotes } = footnoteAnswer(t.answer, plainSteps, tables, resultPapers);
  // Direct citations from the evidence labeller that the text did not reference inline.
  const citedIds = footnotes.flatMap((f) => f.papers);
  const resultIds = [...new Set([...(t.evidence.result_papers || []).flatMap((r) => r.paper_ids), ...(t.evidence.citations || []).map((c) => c.paper_id)])];
  const graph = buildGraph(t.steps, t.linked, t.subgraph, idx);
  const chart = chooseChart(t.steps, tables, idx);
  const graphEmptyReason =
    t.mode === "global" || t.steps.some((s) => s.tool === "community_report")
      ? "This answer was written from summaries of research communities, so there is no walk through the graph to draw. The Papers tab lists the sources."
      : t.steps.length
        ? "This answer came from one ranked table, so there is no path through the graph to draw. The chart and table show the result."
        : t.status === "running"
          ? "The graph walk appears here as each step finishes."
          : "No graph for this answer.";
  return {
    plainSteps,
    executedCount: t.steps.length,
    blocks,
    follow: t.status === "done" ? followUps(t.question, t.linked, t.steps) : [],
    evidence: {
      graph,
      graphEmptyReason,
      revealed: t.planArrived || t.steps.length ? t.steps.length : -1,
      done: t.status !== "running",
      chart,
      tables,
      footnotes,
      resultPaperIds: resultIds,
      citedPaperIds: citedIds,
    },
  };
}

/* ---------- Answer rendering ---------- */
const AnswerBlocks: React.FC<{ blocks: Block[]; streaming: boolean; onFootnote: (n: number) => void }> = ({ blocks, streaming, onFootnote }) => {
  const out: React.ReactNode[] = [];
  let list: React.ReactNode[] = [];
  const flush = (k: number) => {
    if (list.length) {
      out.push(<ul key={`ul${k}`}>{list}</ul>);
      list = [];
    }
  };
  const renderSegs = (b: Block) =>
    b.segs.map((s, i) =>
      typeof s === "string" ? (
        <React.Fragment key={i}>{s}</React.Fragment>
      ) : "fn" in s ? (
        <button key={i} type="button" className="fn" aria-label={`Source ${s.fn}`} onClick={() => onFootnote(s.fn)} data-testid="answer-footnote">
          {s.fn}
        </button>
      ) : (
        <strong key={i}>{s.strong}</strong>
      ),
    );
  blocks.forEach((b, i) => {
    if (b.type === "li") list.push(<li key={i}>{renderSegs(b)}</li>);
    else {
      flush(i);
      out.push(<p key={i}>{renderSegs(b)}</p>);
    }
  });
  flush(blocks.length);
  return (
    <div className="answer" data-testid="ask-answer-text">
      {out}
      {streaming && <span className="caret" aria-hidden="true" />}
    </div>
  );
};

/* ---------- One turn in the conversation ---------- */
const Turn: React.FC<{
  turn: TurnView;
  model: TurnModel;
  selected: boolean;
  latency: number | null;
  onFootnote: (n: number) => void;
  onAsk: (q: string, overrides?: Record<string, string>) => void;
  onSelect: () => void;
  onShowEvidence: () => void;
}> = ({ turn, model, selected, latency, onFootnote, onAsk, onSelect, onShowEvidence }) => {
  const running = turn.status === "running";
  const [open, setOpen] = useState(true);
  const [tick, setTick] = useState(0);
  useEffect(() => {
    if (!running) {
      setOpen(false);
      return;
    }
    setOpen(true);
    const id = window.setInterval(() => setTick((n) => n + 1), 100);
    return () => window.clearInterval(id);
  }, [running]);
  void tick;
  const elapsed = running ? (performance.now() - turn.startedAt) / 1000 : turn.elapsedSeconds;
  const visibleSteps = model.plainSteps.filter((s) => s.state !== "pending");
  const passed = turn.result?.faithfulness?.passed;
  const errors = turn.result?.faithfulness?.errors || [];
  const kindChoices = turn.linked.filter((l) => Array.isArray(l.kind_choices) && l.kind_choices.length);
  const ambiguous = turn.result?.ambiguous || [];
  const shownLatency = latency ?? elapsed;

  return (
    <article className={`turn ${selected ? "is-selected" : ""}`} aria-label={`Question: ${turn.question}`} onFocus={onSelect} onClick={onSelect} data-testid="ask-turn">
      <div className="msg-user">{turn.question}</div>

      {turn.status !== "error" || visibleSteps.length > 1 ? (
        <div className={`plan ${open ? "" : "collapsed"}`} data-testid="ask-trace">
          <button type="button" className="plan-title" aria-expanded={open} onClick={() => setOpen((v) => !v)}>
            <span>Plan</span>
            <span className="elapsed">
              {running ? `${(elapsed || 0).toFixed(1)} s` : turn.status === "ambiguous" ? "needs a choice" : `${model.plainSteps.length} steps, ${model.plainSteps.every((s) => s.state === "done") ? "all done" : "finished with a warning"}`}
            </span>
            <Icon name="chevronDown" size={16} strokeWidth={2} className="chev" />
          </button>
          {open && (
            <ol>
              {visibleSteps.map((s) => (
                <li key={s.key} id={s.stepNumber ? `ask-step-${turn.id}-${s.stepNumber}` : undefined} data-state={s.state} tabIndex={-1}>
                  {s.state === "active" ? (
                    <span className="st spin" role="img" aria-label="Working" />
                  ) : s.state === "error" ? (
                    <Icon name="warning" size={18} className="st st-warn" title="Needs attention" />
                  ) : (
                    <Icon name="check" size={18} strokeWidth={2.2} className="st" title="Done" />
                  )}
                  <div>
                    <div className="t">{s.title}</div>
                    {s.result && <div className="res">{s.result}</div>}
                  </div>
                </li>
              ))}
            </ol>
          )}
        </div>
      ) : null}

      {turn.status === "ambiguous" && ambiguous.length > 0 && (
        <div className="choice" role="group" aria-label="Which one did you mean?">
          {ambiguous.map((a) => (
            <div key={a.slot}>
              <p>
                More than one researcher is called <b>{a.query}</b>. Which one do you mean?
              </p>
              <div className="chips">
                {a.candidates.map((c: any) => (
                  <button key={c.id} type="button" className="chip-btn" onClick={() => onAsk(turn.question, { [a.slot]: c.id })} title={c.id}>
                    {c.name}
                    {Array.isArray(c.affiliations) && c.affiliations.length ? `, ${c.affiliations.slice(0, 2).map((x: string) => orgName(x)).join(" and ")}` : ""}
                    {typeof c.paper_count === "number" ? `, ${c.paper_count} ${c.paper_count === 1 ? "paper" : "papers"}` : ""}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {turn.answer && turn.status !== "ambiguous" && <AnswerBlocks blocks={model.blocks} streaming={!turn.answerDone} onFootnote={onFootnote} />}

      {turn.status === "error" && (
        <div className="checkline is-warn" role="alert">
          <Icon name="warning" size={18} />
          <span>
            The answer could not be finished: {turn.error || "the request failed"}. Try again, or turn on recorded answers in the settings next to the box below.
          </span>
        </div>
      )}

      {turn.result && turn.status === "done" && (
        <>
          {passed ? (
            <div className="checkline" data-testid="faithfulness-badge" data-passed="true">
              <Icon name="shield" size={18} strokeWidth={2} />
              <span>
                Every number is checked against the retrieved data. {MODEL_LINE}
                {shownLatency != null ? `, ${shownLatency.toFixed(1)} s` : ""}.{turn.fromCache ? " This is a recorded answer." : ""}
              </span>
            </div>
          ) : (
            <div className="checkline is-warn" data-testid="faithfulness-badge" data-passed="false" role="alert">
              <Icon name="warning" size={18} />
              <span>
                Some statements could not be matched to the retrieved data, so read this answer against the Table tab.
                {errors.length > 0 && (
                  <details>
                    <summary>What did not match</summary>
                    <ul>
                      {errors.slice(0, 6).map((e, i) => (
                        <li key={i}>{e.replace(/^entity /, "Name ").replace(/ not in trace$/, " is not in the retrieved data")}</li>
                      ))}
                    </ul>
                  </details>
                )}
              </span>
            </div>
          )}
          <MethodDrawer testId="ask-how">
            <AskMethodNote />
          </MethodDrawer>
          {kindChoices.map((l) => (
            <p className="kind-note" key={l.text}>
              Read “{l.text}” as {l.entity_type ? `a ${l.entity_type.toLowerCase()}` : "a subject"}
              {typeof l.paper_count === "number" ? ` (${l.paper_count} papers)` : ""}.{" "}
              {l.kind_choices!.map((c) => (
                <button key={c.id} type="button" className="textlink" data-testid="ask-kind-choice" onClick={() => onAsk(turn.question, { [String(l.text)]: c.id })}>
                  Use the {c.label.toLowerCase()} instead{typeof c.paper_count === "number" ? ` (${c.paper_count})` : ""}
                </button>
              ))}
            </p>
          ))}
          {model.follow.length > 0 && (
            <div className="chips" aria-label="Follow-up questions" role="group">
              {model.follow.map((f) => (
                <button key={f} type="button" className="chip-btn" onClick={() => onAsk(f)} data-testid="ask-followup">
                  {f}
                </button>
              ))}
            </div>
          )}
          <button type="button" className="chip-btn mobile-ev-toggle" onClick={onShowEvidence}>
            See the evidence
          </button>
        </>
      )}
    </article>
  );
};

/* ---------- Welcome ---------- */
const Welcome: React.FC<{ demos: AskDemoItem[]; onDemo: (d: AskDemoItem) => void }> = ({ demos, onDemo }) => (
  <div className="welcome">
    <h1>What would you like to know?</h1>
    <p>
      Ask about AAAI and IJCAI papers from 2021 to 2025. A small language model plans the steps, reads the knowledge graph, and writes an answer whose numbers are checked against the data.
    </p>
    <div className="intent-groups">
      {INTENTS.map((g) => (
        <div className="intent" key={g.name}>
          <h2>
            <Icon name={g.icon} size={18} strokeWidth={1.7} />
            {g.name}
          </h2>
          {g.items.map(([id, hint]) => {
            if (id === "pulse")
              return (
                <button key={id} type="button" className="card-btn" onClick={() => navigate("/")}>
                  What's heating up across all subjects?
                  <small>{hint}</small>
                </button>
              );
            const d = demos.find((x) => x.demo_id === id);
            if (!d) return null;
            return (
              <button key={id} type="button" className="card-btn" onClick={() => onDemo(d)} data-testid={`demo-btn-${id}`}>
                {d.question}
                <small>{hint}</small>
              </button>
            );
          })}
        </div>
      ))}
    </div>
  </div>
);

/* ---------- Page ---------- */
export const AskPage: React.FC<{ onOpenNode360?: (id: string) => void }> = () => {
  const route = useRoute();
  const convId = route.page === "ask" ? route.param : null;
  const conversations = useConversations((s) => s.conversations);
  const upsertTurn = useConversations((s) => s.upsertTurn);
  const demosQuery = useQuery({ queryKey: ["nav-ask-demos"], queryFn: ({ signal }) => navigatorApi.getAskDemos(signal), staleTime: 300_000 });
  const demos = demosQuery.data?.demos || [];

  const [mode, setMode] = useState<AskMode>("auto");
  const [useCache, setUseCache] = useState(true);
  const [input, setInput] = useState("");
  const [advOpen, setAdvOpen] = useState(false);
  const [tab, setTab] = useState<EvidenceTab>("Graph");
  const [tabTouched, setTabTouched] = useState(false);
  const [selectedTurnId, setSelectedTurnId] = useState<string | null>(null);
  const [flashFn, setFlashFn] = useState<number | null>(null);
  const [announce, setAnnounce] = useState("");
  const liveConv = useRef<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const evRef = useRef<HTMLDivElement>(null);
  const textRef = useRef<HTMLTextAreaElement>(null);
  const advRef = useRef<HTMLDivElement>(null);

  const onFinished = useCallback(
    (t: TurnView) => {
      if (liveConv.current) upsertTurn(liveConv.current, toStored(t));
      setAnnounce(t.status === "error" ? "The answer could not be finished." : t.status === "ambiguous" ? "The question needs a choice." : "The answer is ready.");
    },
    [upsertTurn],
  );
  const { turn: live, run, stop } = useAskTurn(onFinished);

  const conversation = conversations.find((c) => c.id === convId) || null;
  const turns: TurnView[] = useMemo(() => {
    const stored = conversation?.turns || [];
    const list = stored.map((st) => (live && live.id === st.id ? live : turnFromResult(st.id, st.question, st.mode, st.result, st.elapsedSeconds, st.error || (st.result ? null : "the question was interrupted"))));
    if (live && liveConv.current === convId && !stored.some((s) => s.id === live.id)) list.push(live);
    return list;
  }, [conversation, live, convId]);
  const models = useMemo(() => turns.map(modelFor), [turns]);

  // Leaving a conversation stops a run that belongs to another one.
  useEffect(() => {
    if (live && liveConv.current && liveConv.current !== convId && live.status === "running") stop();
    setSelectedTurnId(null);
    setTabTouched(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [convId]);

  const selectedIndex = Math.max(0, selectedTurnId ? turns.findIndex((t) => t.id === selectedTurnId) : turns.length - 1);
  const selected = turns[selectedIndex] || null;
  const selModel = selected ? models[selectedIndex] : null;

  // Default tab: the graph when there is one, otherwise the chart, otherwise the table.
  useEffect(() => {
    if (!selModel || tabTouched) return;
    const ev = selModel.evidence;
    setTab(ev.graph ? "Graph" : ev.chart.kind !== "none" ? "Chart" : ev.tables.length ? "Table" : "Papers");
  }, [selModel?.evidence.graph, selModel?.evidence.chart.kind, selModel?.evidence.tables.length, tabTouched, selModel]);

  // Keep the newest content in view while streaming.
  useEffect(() => {
    if (!live || live.status !== "running") return;
    const el = scrollRef.current;
    if (el && el.scrollHeight - el.scrollTop - el.clientHeight < 240) el.scrollTop = el.scrollHeight;
  }, [live?.answer, live?.steps.length, live]);

  useEffect(() => {
    if (!live) return;
    if (live.status === "running") setAnnounce(live.steps.length ? `Step ${live.steps.length} done` : live.planArrived ? "Plan ready" : "Reading the question");
  }, [live?.steps.length, live?.planArrived, live?.status, live]);

  const latencyFor = (t: TurnView): number | null => {
    if (!t.fromCache) return t.elapsedSeconds;
    const d = demos.find((x) => x.question.trim().toLowerCase() === t.question.trim().toLowerCase());
    return d?.latency_seconds ?? (t.result as any)?.latency_s ?? null;
  };

  const ask = useCallback(
    (question: string, opts: { mode?: AskMode; overrides?: Record<string, string> } = {}) => {
      const q = question.trim();
      if (!q) return;
      let cid = convId;
      if (!cid || !conversation) {
        cid = newId("c");
      }
      const tid = newId("t");
      const m = opts.mode || mode;
      liveConv.current = cid;
      upsertTurn(cid, { id: tid, question: q, mode: m, askedAt: new Date().toISOString(), result: null, elapsedSeconds: null }, titleFor(q));
      if (cid !== convId) navigate(pathFor("ask", cid));
      setSelectedTurnId(tid);
      setTabTouched(false);
      setInput("");
      void run(tid, q, m, opts.overrides ? false : useCache, opts.overrides);
      requestAnimationFrame(() => {
        const el = scrollRef.current;
        if (el) el.scrollTop = el.scrollHeight;
      });
    },
    [convId, conversation, mode, run, upsertTurn, useCache],
  );

  // /ask?q=… (from search) asks once.
  const askedFromQuery = useRef(false);
  useEffect(() => {
    if (askedFromQuery.current) return;
    const q = new URLSearchParams(window.location.search).get("q");
    if (q && !convId) {
      askedFromQuery.current = true;
      window.history.replaceState(null, "", "/ask");
      ask(q);
    }
  }, [ask, convId]);

  // Close the settings menu on outside click or Escape.
  useEffect(() => {
    if (!advOpen) return;
    const down = (e: MouseEvent) => {
      if (advRef.current && !advRef.current.contains(e.target as Node)) setAdvOpen(false);
    };
    const key = (e: KeyboardEvent) => {
      if (e.key === "Escape") setAdvOpen(false);
    };
    document.addEventListener("mousedown", down);
    document.addEventListener("keydown", key);
    return () => {
      document.removeEventListener("mousedown", down);
      document.removeEventListener("keydown", key);
    };
  }, [advOpen]);

  const openFootnote = (turnId: string, n: number) => {
    setSelectedTurnId(turnId);
    setTab("Papers");
    setTabTouched(true);
    setFlashFn(null);
    requestAnimationFrame(() => setFlashFn(n));
    if (window.matchMedia("(max-width: 1000px)").matches) evRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const running = live?.status === "running" && liveConv.current === convId;
  const hasTurns = turns.length > 0;

  return (
    <div className="ask" data-testid="page-ask">
      <section className="convo" aria-label="Conversation">
        <div className="convo-scroll" ref={scrollRef}>
          <p className="sr-only" aria-live="polite">
            {announce}
          </p>
          {!hasTurns ? (
            demosQuery.isLoading ? (
              <p className="loading-line">
                <span className="spin" aria-hidden="true" />
                Loading…
              </p>
            ) : (
              <Welcome demos={demos} onDemo={(d) => ask(d.question, { mode: d.mode as AskMode })} />
            )
          ) : (
            turns.map((t, i) => (
              <Turn
                key={t.id}
                turn={t}
                model={models[i]}
                selected={i === selectedIndex && turns.length > 1}
                latency={latencyFor(t)}
                onFootnote={(n) => openFootnote(t.id, n)}
                onAsk={(q, overrides) => ask(q, { overrides })}
                onSelect={() => setSelectedTurnId(t.id)}
                onShowEvidence={() => {
                  setSelectedTurnId(t.id);
                  evRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
                }}
              />
            ))
          )}
        </div>
        <div className="composer">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              ask(input);
            }}
          >
            <label className="sr-only" htmlFor="ask-input">
              Your question
            </label>
            <textarea
              id="ask-input"
              ref={textRef}
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  ask(input);
                }
              }}
              placeholder={hasTurns ? "Ask a follow-up…" : "Ask about topics, groups or connections…"}
              data-testid="ask-input"
            />
            <button type="submit" className="send" aria-label="Send" disabled={!input.trim() || running} data-testid="ask-submit">
              <Icon name="send" size={18} strokeWidth={2} />
            </button>
            <div ref={advRef} className="adv-wrap">
              <button type="button" className="icon-btn" aria-label="Answer settings" aria-expanded={advOpen} aria-controls="adv-menu" onClick={() => setAdvOpen((v) => !v)} data-testid="ask-settings">
                <Icon name="sliders" size={19} strokeWidth={1.7} />
              </button>
              {advOpen && (
                <div className="adv-menu" id="adv-menu" role="dialog" aria-label="Answer settings">
                  <fieldset>
                    <legend>How to search</legend>
                    <div className="seg" role="radiogroup" aria-label="How to search">
                      {(["auto", "local", "global"] as AskMode[]).map((m) => (
                        <label key={m}>
                          <input type="radio" name="ask-mode" value={m} checked={mode === m} onChange={() => setMode(m)} />
                          <span>{m === "auto" ? "Auto" : m === "local" ? "Local" : "Global"}</span>
                        </label>
                      ))}
                    </div>
                    <p className="small-note">Auto picks for you. Local follows links from the names in the question. Global reads summaries of whole research communities.</p>
                  </fieldset>
                  <div className="toggle-row">
                    <label htmlFor="ask-cache">Use cached demo answers</label>
                    <input id="ask-cache" type="checkbox" checked={useCache} onChange={(e) => setUseCache(e.target.checked)} data-testid="ask-use-cache" />
                  </div>
                  <p className="small-note">Plays recorded runs of the starter questions, so they work without the language model.</p>
                </div>
              )}
            </div>
          </form>
        </div>
      </section>
      <div ref={evRef} className="evidence-wrap">
        <EvidencePanel
          data={selModel && selected?.status !== "ambiguous" ? selModel.evidence : null}
          tab={tab}
          onTab={(t) => {
            setTab(t);
            setTabTouched(true);
          }}
          flashFootnote={flashFn}
        />
      </div>
    </div>
  );
};

// Names used by tests and other pages.
export { displayName };
