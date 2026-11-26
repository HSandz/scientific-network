/**
 * Minimal path router for the Navigator shell.
 *
 * Pages are linkable and the back button works through the History API. The Explorer keeps
 * its own query-string view spec (`?v=2&view=…`, `?mode=…`), so Explore URLs carry both a
 * path and the Explorer's search parameters. Legacy single-page URLs (`/?tab=trends`,
 * `/?mode=researchers`, `/?view=…`) are mapped to the new paths on load.
 */
import { useSyncExternalStore } from "react";
import type { WorkspaceTab } from "../types/explorer";

export type PageKey =
  | "pulse"
  | "ask"
  | "trends"
  | "topics"
  | "groups"
  | "map"
  | "network"
  | "explore"
  | "node"
  | "about";

export interface Route {
  page: PageKey;
  /** Path parameter: conversation, subject, group, community, node id, or a sub-view. */
  param: string | null;
  path: string;
  search: string;
}

const ROUTE_EVENT = "rtn:navigate";

function decode(s: string | undefined): string | null {
  if (!s) return null;
  try {
    return decodeURIComponent(s);
  } catch {
    return s;
  }
}

export function parsePath(pathname: string, search = ""): Route {
  const parts = pathname.replace(/^\/+|\/+$/g, "").split("/");
  const head = parts[0] || "";
  const rest = parts.length > 1 ? decode(parts.slice(1).join("/")) : null;
  const known: Record<string, PageKey> = {
    "": "pulse",
    pulse: "pulse",
    ask: "ask",
    trends: "trends",
    topics: "topics",
    groups: "groups",
    map: "map",
    network: "network",
    explore: "explore",
    node: "node",
    about: "about",
  };
  const page = known[head] ?? "pulse";
  return { page, param: page === "pulse" ? null : rest, path: pathname, search };
}

export function pathFor(page: PageKey, param?: string | null): string {
  const base = page === "pulse" ? "/" : `/${page}`;
  if (!param) return base;
  // Keep ":" readable in ids such as method:Q3621696; encode everything else that needs it.
  return `${base}/${encodeURIComponent(param).replace(/%3A/gi, ":")}`;
}

/** Map an old `?tab=` value (or explorer-only parameters) to a new path. */
export function legacyTabToPath(tab: string | null, ids: { subject?: string | null; group?: string | null; community?: string | null; node?: string | null } = {}): string | null {
  switch (tab) {
    case "graph":
      return "/explore";
    case "table":
      return "/explore/table";
    case "analytics":
      return "/network/release";
    case "trends":
      return "/trends";
    case "subjects":
      return ids.subject ? pathFor("topics", ids.subject) : "/topics";
    case "groups":
      return ids.group ? pathFor("groups", ids.group) : "/groups";
    case "communities":
      return ids.community ? pathFor("map", ids.community) : "/map";
    case "network":
      return "/network";
    case "ask":
      return "/ask";
    case "node360":
      return ids.node ? pathFor("node", ids.node) : "/node";
    case "about":
      return "/about";
    case "pulse":
      return "/";
    default:
      return null;
  }
}

/**
 * On first load, rewrite legacy root URLs to the new paths (replaceState, so Back still works).
 * Explorer parameters stay in the query string for the Explorer's own hydration.
 */
export function normalizeLegacyUrl(): void {
  if (typeof window === "undefined") return;
  const { pathname, search, hash } = window.location;
  if (pathname !== "/" && pathname !== "") return;
  const sp = new URLSearchParams(search);
  const tab = sp.get("tab");
  let target: string | null = null;
  if (tab) {
    target = legacyTabToPath(tab);
    sp.delete("tab");
  } else if (sp.has("view")) {
    try {
      const v = JSON.parse(sp.get("view") || "{}");
      target = legacyTabToPath(typeof v.workspaceTab === "string" ? v.workspaceTab : "graph") || "/explore";
    } catch {
      target = "/explore";
    }
  } else if (["mode", "node", "edge", "scope", "center", "preset", "layout", "edge_filter"].some((k) => sp.has(k))) {
    target = "/explore";
  }
  if (!target) return;
  const isExplore = target.startsWith("/explore") || target.startsWith("/network/release");
  const qs = isExplore ? sp.toString() : "";
  window.history.replaceState(window.history.state, "", `${target}${qs ? `?${qs}` : ""}${hash}`);
}

function snapshot(): string {
  if (typeof window === "undefined") return "/";
  return `${window.location.pathname}${window.location.search}`;
}

function subscribe(cb: () => void): () => void {
  window.addEventListener("popstate", cb);
  window.addEventListener(ROUTE_EVENT, cb);
  return () => {
    window.removeEventListener("popstate", cb);
    window.removeEventListener(ROUTE_EVENT, cb);
  };
}

let cachedKey = "";
let cachedRoute: Route = parsePath("/");

export function currentRoute(): Route {
  const key = snapshot();
  if (key !== cachedKey) {
    cachedKey = key;
    cachedRoute = parsePath(window.location.pathname, window.location.search);
  }
  return cachedRoute;
}

export function useRoute(): Route {
  useSyncExternalStore(subscribe, snapshot, () => "/");
  return currentRoute();
}

export function navigate(to: string, opts: { replace?: boolean; keepScroll?: boolean } = {}): void {
  if (typeof window === "undefined") return;
  const cur = snapshot();
  if (to === cur) return;
  if (opts.replace) window.history.replaceState(null, "", to);
  else window.history.pushState(null, "", to);
  window.dispatchEvent(new Event(ROUTE_EVENT));
  if (!opts.keepScroll) {
    document.getElementById("main-content")?.scrollTo?.({ top: 0 });
    window.scrollTo?.({ top: 0 });
  }
}

/** Anchor click handler: left-click without modifiers navigates in-app, others open normally. */
export function linkClick(e: React.MouseEvent<HTMLAnchorElement>, to: string): void {
  if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
  e.preventDefault();
  navigate(to);
}

/** Store tab for each page, so the Explorer's internal tab logic keeps working. */
export function tabForRoute(r: Route): WorkspaceTab {
  switch (r.page) {
    case "pulse":
      return "pulse";
    case "ask":
      return "ask";
    case "trends":
      return "trends";
    case "topics":
      return "subjects";
    case "groups":
      return "groups";
    case "map":
      return "communities";
    case "network":
      return r.param === "release" ? "analytics" : "network";
    case "explore":
      return r.param === "table" ? "table" : "graph";
    case "node":
      return "node360";
    case "about":
      return "about";
  }
}

/** Path for a store tab (used when Explorer code calls setWorkspaceTab directly). */
export function pathForTab(
  tab: WorkspaceTab,
  ids: { subject?: string | null; group?: string | null; community?: string | null; node?: string | null },
): string {
  return legacyTabToPath(tab, ids) || "/";
}
