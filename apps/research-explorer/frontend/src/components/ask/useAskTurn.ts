import { useCallback, useEffect, useRef, useState } from "react";
import { navigatorApi } from "../../lib/navigatorApi";
import type { AskCitationsEvent, AskResult } from "../../types/navigator";
import type { LinkedEntity, SubgraphData, TraceStep } from "../../lib/askModel";

export type AskMode = "auto" | "local" | "global";

export interface TurnView {
  id: string;
  question: string;
  mode: AskMode;
  status: "running" | "done" | "error" | "ambiguous";
  stage: string | null;
  fromCache: boolean;
  parsed: Record<string, any> | null;
  linked: LinkedEntity[];
  plan: Array<{ tool: string; args: Record<string, any>; purpose?: string }> | null;
  planArrived: boolean;
  steps: TraceStep[];
  subgraph: SubgraphData | null;
  answer: string;
  answerDone: boolean;
  evidence: AskCitationsEvent;
  result: AskResult | null;
  error: string | null;
  startedAt: number;
  elapsedSeconds: number | null;
  restored: boolean;
}

export function emptyTurn(id: string, question: string, mode: AskMode): TurnView {
  return {
    id,
    question,
    mode,
    status: "running",
    stage: "parsing",
    fromCache: false,
    parsed: null,
    linked: [],
    plan: null,
    planArrived: false,
    steps: [],
    subgraph: null,
    answer: "",
    answerDone: false,
    evidence: {},
    result: null,
    error: null,
    startedAt: performance.now(),
    elapsedSeconds: null,
    restored: false,
  };
}

/** A finished turn rebuilt from a stored or cached result (no replay animation). */
export function turnFromResult(id: string, question: string, mode: AskMode, result: AskResult | null, elapsed?: number | null, error?: string | null): TurnView {
  const t = emptyTurn(id, question, mode);
  if (!result) return { ...t, status: error ? "error" : "done", error: error || null, restored: true, answerDone: true, elapsedSeconds: elapsed ?? null };
  const linked = Array.isArray(result.linked) ? (result.linked as unknown as LinkedEntity[]) : [];
  return {
    ...t,
    status: result.ambiguous?.length && !result.steps?.length ? "ambiguous" : "done",
    stage: null,
    fromCache: !!result.from_cache,
    parsed: ((result as any).parsed as Record<string, any>) || null,
    linked,
    plan: (result.plan as any) || [],
    planArrived: true,
    steps: (result.steps as unknown as TraceStep[]) || [],
    subgraph: (result.subgraph as SubgraphData) || null,
    answer: result.answer || "",
    answerDone: true,
    evidence: { citations: result.citations, result_papers: result.result_papers, paper_ids: result.paper_ids, evidence_labelling: result.evidence_labelling },
    result,
    elapsedSeconds: elapsed ?? (result as any).latency_s ?? null,
    restored: true,
  };
}

const reducedMotion = () => typeof window !== "undefined" && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

type QueuedEvent = { type: string; data: any };

/**
 * Runs one question over the SSE stream and exposes a TurnView that updates as events arrive.
 * Cached demo answers arrive all at once; they are paced on the client (one plan step at a time,
 * then the answer typed out) so the hop-by-hop reveal reads the same as a live run. With
 * prefers-reduced-motion everything is shown at once.
 */
export function useAskTurn(onFinished: (turn: TurnView) => void) {
  const [turn, setTurn] = useState<TurnView | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const queue = useRef<QueuedEvent[]>([]);
  const pumping = useRef(false);
  const timer = useRef<number | null>(null);
  const turnRef = useRef<TurnView | null>(null);
  const finishedCb = useRef(onFinished);
  finishedCb.current = onFinished;

  const update = useCallback((fn: (t: TurnView) => TurnView) => {
    setTurn((prev) => {
      if (!prev) return prev;
      const next = fn(prev);
      turnRef.current = next;
      return next;
    });
  }, []);

  const apply = useCallback(
    (ev: QueuedEvent) => {
      const d = ev.data || {};
      switch (ev.type) {
        case "status":
          update((t) => ({ ...t, stage: String(d.stage || t.stage), fromCache: t.fromCache || d.stage === "cached" }));
          break;
        case "parsed":
          update((t) => ({ ...t, parsed: d.parsed || t.parsed, linked: Array.isArray(d.linked) ? d.linked : t.linked }));
          break;
        case "plan":
          update((t) => ({ ...t, plan: Array.isArray(d.plan) ? d.plan : [], planArrived: true, linked: Array.isArray(d.linked) && d.linked.length ? d.linked : t.linked }));
          break;
        case "step":
          update((t) => ({ ...t, planArrived: true, steps: [...t.steps.filter((s) => s.step !== d.step), d as TraceStep].sort((a, b) => a.step - b.step) }));
          break;
        case "subgraph":
          update((t) => ({ ...t, subgraph: { nodes: d.nodes || [], edges: d.edges || [] } }));
          break;
        case "token":
          update((t) => ({ ...t, stage: "writing", answer: t.answer + (d.text || "") }));
          break;
        case "citations":
          update((t) => ({ ...t, evidence: d || {} }));
          break;
        case "ambiguous":
          update((t) => {
            const res = d as AskResult;
            return { ...t, status: "ambiguous", stage: null, result: res, answer: res.answer || "", answerDone: true, elapsedSeconds: (performance.now() - t.startedAt) / 1000 };
          });
          break;
        case "final":
          update((t) => {
            const res = d as AskResult;
            const done: TurnView = {
              ...t,
              status: res.ambiguous?.length && !res.steps?.length ? "ambiguous" : "done",
              stage: null,
              result: res,
              answer: res.answer || t.answer,
              answerDone: true,
              steps: (res.steps as unknown as TraceStep[])?.length ? (res.steps as unknown as TraceStep[]) : t.steps,
              plan: (res.plan as any)?.length ? (res.plan as any) : t.plan,
              subgraph: (res.subgraph as SubgraphData) || t.subgraph,
              linked: Array.isArray(res.linked) && (res.linked as unknown[]).length ? (res.linked as unknown as LinkedEntity[]) : t.linked,
              evidence: { citations: res.citations, result_papers: res.result_papers, paper_ids: res.paper_ids, evidence_labelling: res.evidence_labelling },
              fromCache: !!res.from_cache || t.fromCache,
              elapsedSeconds: (performance.now() - t.startedAt) / 1000,
            };
            queueMicrotask(() => finishedCb.current(done));
            return done;
          });
          break;
        case "error":
          update((t) => {
            const failed: TurnView = { ...t, status: "error", stage: null, error: String(d.error || d || "Something went wrong."), answerDone: true, elapsedSeconds: (performance.now() - t.startedAt) / 1000 };
            queueMicrotask(() => finishedCb.current(failed));
            return failed;
          });
          break;
      }
    },
    [update],
  );

  const delayFor = useCallback((ev: QueuedEvent): number => {
    const t = turnRef.current;
    if (reducedMotion()) return 0;
    const cached = t?.fromCache;
    if (ev.type === "token") return 22;
    if (!cached) return 0;
    if (ev.type === "plan") return 450;
    if (ev.type === "step") return 800;
    if (ev.type === "citations" || ev.type === "final") return 120;
    return 0;
  }, []);

  const pump = useCallback(() => {
    if (pumping.current) return;
    pumping.current = true;
    const next = () => {
      const ev = queue.current.shift();
      if (!ev) {
        pumping.current = false;
        return;
      }
      // Token chunks are split further so the answer types out word by word.
      if (ev.type === "token" && !reducedMotion()) {
        const words = String(ev.data?.text || "").split(/(?<=\s)/);
        if (words.length > 3) {
          const chunks: QueuedEvent[] = [];
          for (let i = 0; i < words.length; i += 3) chunks.push({ type: "token", data: { text: words.slice(i, i + 3).join("") } });
          queue.current.unshift(...chunks);
          next();
          return;
        }
      }
      const wait = delayFor(ev);
      const run = () => {
        apply(ev);
        next();
      };
      if (wait) timer.current = window.setTimeout(run, wait);
      else run();
    };
    next();
  }, [apply, delayFor]);

  const enqueue = useCallback(
    (type: string, data: any) => {
      // The cached flag must be known before pacing decisions, so status is applied at once.
      if (type === "status") {
        apply({ type, data });
        return;
      }
      queue.current.push({ type, data });
      pump();
    },
    [apply, pump],
  );

  const stop = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    queue.current = [];
    if (timer.current) window.clearTimeout(timer.current);
    pumping.current = false;
  }, []);

  const run = useCallback(
    async (id: string, question: string, mode: AskMode, useCache: boolean, overrides?: Record<string, string>) => {
      stop();
      const t = emptyTurn(id, question, mode);
      turnRef.current = t;
      setTurn(t);
      const ctrl = new AbortController();
      abortRef.current = ctrl;
      try {
        await navigatorApi.askStream(
          { question, mode, use_cache: useCache, resolved_overrides: overrides },
          {
            onStatus: (d) => enqueue("status", d),
            onParsed: (d) => enqueue("parsed", d),
            onPlan: (d) => enqueue("plan", d),
            onStep: (d) => enqueue("step", d),
            onSubgraph: (d) => enqueue("subgraph", d),
            onToken: (d) => enqueue("token", d),
            onCitations: (d) => enqueue("citations", d),
            onAmbiguous: (d) => enqueue("ambiguous", d),
            onFinal: (d) => enqueue("final", d),
            onError: (e) => enqueue("error", { error: e }),
          },
          ctrl.signal,
        );
      } catch (e) {
        if (ctrl.signal.aborted) return;
        enqueue("error", { error: e instanceof Error ? e.message : String(e) });
      }
    },
    [enqueue, stop],
  );

  const show = useCallback(
    (t: TurnView | null) => {
      stop();
      turnRef.current = t;
      setTurn(t);
    },
    [stop],
  );

  useEffect(() => stop, [stop]);

  return { turn, run, show, stop };
}
