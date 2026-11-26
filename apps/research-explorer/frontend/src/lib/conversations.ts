/**
 * Ask conversation history, kept in this browser's localStorage only.
 * Each conversation holds its turns (question plus the final answer payload) so a reload or
 * a link to /ask/<id> restores the answer and its evidence without re-running the model.
 */
import { create } from "zustand";
import type { AskResult } from "../types/navigator";

export interface StoredTurn {
  id: string;
  question: string;
  mode: "auto" | "local" | "global";
  askedAt: string;
  /** Seconds from send to final event, measured in the browser. */
  elapsedSeconds?: number | null;
  result: AskResult | null;
  error?: string | null;
}

export interface Conversation {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  turns: StoredTurn[];
}

const KEY = "rtn-conversations-v1";
const MAX_CONVERSATIONS = 20;
const MAX_ROWS_PER_STEP = 60;

function load(): Conversation[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = JSON.parse(window.localStorage.getItem(KEY) || "[]");
    return Array.isArray(raw) ? raw.filter((c) => c && typeof c.id === "string" && Array.isArray(c.turns)) : [];
  } catch {
    return [];
  }
}

/** Trim bulky trace rows so twenty conversations fit comfortably in localStorage. */
function compact(result: AskResult | null): AskResult | null {
  if (!result) return result;
  return {
    ...result,
    steps: (result.steps || []).map((s) => ({ ...s, rows: (s.rows || []).slice(0, MAX_ROWS_PER_STEP) })),
  };
}

function persist(list: Conversation[]) {
  if (typeof window === "undefined") return;
  let out = list.slice(0, MAX_CONVERSATIONS);
  for (let attempt = 0; attempt < 4; attempt++) {
    try {
      window.localStorage.setItem(KEY, JSON.stringify(out));
      return;
    } catch {
      out = out.slice(0, Math.max(1, Math.floor(out.length / 2)));
    }
  }
}

export function newId(prefix = "c"): string {
  return `${prefix}${Date.now().toString(36)}${Math.random().toString(36).slice(2, 7)}`;
}

/** A short, sentence-case title from the question. */
export function titleFor(question: string): string {
  const q = question.trim().replace(/\s+/g, " ").replace(/\?$/, "");
  return q.length > 60 ? `${q.slice(0, 57).trimEnd()}…` : q;
}

interface ConversationState {
  conversations: Conversation[];
  upsertTurn: (conversationId: string, turn: StoredTurn, title?: string) => void;
  remove: (conversationId: string) => void;
  clear: () => void;
}

export const useConversations = create<ConversationState>((set, get) => ({
  conversations: load(),
  upsertTurn: (conversationId, turn, title) => {
    const now = new Date().toISOString();
    const list = get().conversations.slice();
    const idx = list.findIndex((c) => c.id === conversationId);
    const stored = { ...turn, result: compact(turn.result) };
    if (idx === -1) {
      list.unshift({ id: conversationId, title: title || titleFor(turn.question), createdAt: now, updatedAt: now, turns: [stored] });
    } else {
      const c = list[idx];
      const tIdx = c.turns.findIndex((t) => t.id === turn.id);
      const turns = c.turns.slice();
      if (tIdx === -1) turns.push(stored);
      else turns[tIdx] = stored;
      list.splice(idx, 1);
      list.unshift({ ...c, turns, updatedAt: now });
    }
    persist(list);
    set({ conversations: list.slice(0, MAX_CONVERSATIONS) });
  },
  remove: (conversationId) => {
    const list = get().conversations.filter((c) => c.id !== conversationId);
    persist(list);
    set({ conversations: list });
  },
  clear: () => {
    persist([]);
    set({ conversations: [] });
  },
}));
