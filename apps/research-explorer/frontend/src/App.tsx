import React, { useEffect, useLayoutEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AppShell } from "./components/shell/AppShell";
import { explorerApi } from "./lib/api";
import { exploreFocusHandler, queueExploreFocus } from "./lib/exploreBridge";
import {
  currentRoute,
  linkClick,
  navigate,
  normalizeLegacyUrl,
  parsePath,
  pathFor,
  pathForTab,
  tabForRoute,
  useRoute,
  type Route,
} from "./lib/router";
import { useExplorerStore } from "./stores/useExplorerStore";
import type { WorkspaceTab } from "./types/explorer";

const ExplorePage = React.lazy(() => import("./components/explore/ExplorePage").then((m) => ({ default: m.ExplorePage })));
const AnalyticsView = React.lazy(() => import("./components/analytics/AnalyticsView").then((m) => ({ default: m.AnalyticsView })));
const PulsePage = React.lazy(() => import("./components/navigator/PulsePage").then((m) => ({ default: m.PulsePage })));
const TrendsPage = React.lazy(() => import("./components/navigator/TrendsPage").then((m) => ({ default: m.TrendsPage })));
const SubjectPage = React.lazy(() => import("./components/navigator/SubjectPage").then((m) => ({ default: m.SubjectPage })));
const GroupsPage = React.lazy(() => import("./components/navigator/GroupsPage").then((m) => ({ default: m.GroupsPage })));
const CommunitiesPage = React.lazy(() => import("./components/navigator/CommunitiesPage").then((m) => ({ default: m.CommunitiesPage })));
const NetworkSciencePage = React.lazy(() => import("./components/navigator/NetworkSciencePage").then((m) => ({ default: m.NetworkSciencePage })));
const AskPage = React.lazy(() => import("./components/navigator/AskPage").then((m) => ({ default: m.AskPage })));
const Node360Page = React.lazy(() => import("./components/navigator/Node360Page").then((m) => ({ default: m.Node360Page })));
const AboutDataPage = React.lazy(() => import("./components/navigator/AboutDataPage").then((m) => ({ default: m.AboutDataPage })));
const SearchCommandModal = React.lazy(() => import("./components/search/SearchCommandModal").then((m) => ({ default: m.SearchCommandModal })));
const NavigatorSearchModal = React.lazy(() => import("./components/search/NavigatorSearchModal").then((m) => ({ default: m.NavigatorSearchModal })));
const CaveatsModal = React.lazy(() => import("./components/modals/CaveatsModal").then((m) => ({ default: m.CaveatsModal })));

/** Network has two views: the enriched graph's network science and the frozen v4 release analysis. */
const NetworkViews: React.FC<{ current: "enriched" | "release" }> = ({ current }) => (
  <nav className={`network-views ${current === "release" ? "network-views--bleed" : ""}`} aria-label="Network views">
    <div className="seg">
      {(
        [
          ["enriched", "Enriched graph", pathFor("network")],
          ["release", "Release graph (v4) analysis", pathFor("network", "release")],
        ] as const
      ).map(([key, label, href]) => (
        <a
          key={key}
          href={href}
          aria-current={current === key ? "page" : undefined}
          aria-pressed={current === key}
          data-testid={`network-view-${key}`}
          onClick={(e) => linkClick(e, href)}
        >
          {label}
        </a>
      ))}
    </div>
  </nav>
);

const EXPLORE_TABS = new Set<WorkspaceTab>(["graph", "table"]);

/** Apply a route to the store: page tab plus the selected subject, group, community or node. */
function applyRouteToStore(r: Route) {
  const s = useExplorerStore.getState();
  const tab = tabForRoute(r);
  const patch: Partial<ReturnType<typeof useExplorerStore.getState>> = {};
  if (r.page === "topics" && r.param !== s.selectedSubjectId && r.param) patch.selectedSubjectId = r.param;
  if (r.page === "groups" && r.param !== s.selectedGroupId) patch.selectedGroupId = r.param;
  if (r.page === "map" && r.param !== s.selectedCommunityId) patch.selectedCommunityId = r.param;
  if (r.page === "node" && r.param && r.param !== s.node360Id) patch.node360Id = r.param;
  if (Object.keys(patch).length) useExplorerStore.setState(patch);
  if (s.workspaceTab !== tab) s.setWorkspaceTab(tab);
}

/** The path the store currently describes, or null when the route already matches it. */
function pathFromStore(r: Route): string | null {
  const s = useExplorerStore.getState();
  const tab = s.workspaceTab;
  if (tabForRoute(r) === tab) {
    // Same page: follow id changes made inside a page (openSubject, openGroup, …).
    if (tab === "subjects" && s.selectedSubjectId && s.selectedSubjectId !== r.param) return pathFor("topics", s.selectedSubjectId);
    if (tab === "groups" && (s.selectedGroupId || null) !== (r.param || null)) return pathFor("groups", s.selectedGroupId);
    if (tab === "communities" && (s.selectedCommunityId || null) !== (r.param || null)) return pathFor("map", s.selectedCommunityId);
    if (tab === "node360" && s.node360Id && s.node360Id !== r.param) return pathFor("node", s.node360Id);
    return null;
  }
  if (tab === "pulse") return "/";
  const path = pathForTab(tab, {
    subject: s.selectedSubjectId,
    group: s.selectedGroupId,
    community: s.selectedCommunityId,
    node: s.node360Id,
  });
  // Moving between Explore sub-views keeps the Explorer's query string.
  if (EXPLORE_TABS.has(tab) && r.page === "explore") return `${path}${r.search}`;
  return path;
}

let booted = false;
function bootOnce() {
  if (booted) return;
  booted = true;
  normalizeLegacyUrl();
  useExplorerStore.getState().hydrateFromUrl();
  applyRouteToStore(parsePath(window.location.pathname, window.location.search));
}

export const App: React.FC = () => {
  bootOnce();
  const route = useRoute();
  const searchModalOpen = useExplorerStore((s) => s.searchModalOpen);
  const caveatsModalOpen = useExplorerStore((s) => s.caveatsModalOpen);
  const pathFinderOpen = useExplorerStore((s) => s.pathFinderOpen);
  const compareModalOpen = useExplorerStore((s) => s.compareModalOpen);
  const darkMode = useExplorerStore((s) => s.darkMode);
  const node360Id = useExplorerStore((s) => s.node360Id);
  const selectedSubjectId = useExplorerStore((s) => s.selectedSubjectId);
  const selectedGroupId = useExplorerStore((s) => s.selectedGroupId);
  const selectedCommunityId = useExplorerStore((s) => s.selectedCommunityId);
  const openSubject = useExplorerStore((s) => s.openSubject);
  const openGroup = useExplorerStore((s) => s.openGroup);
  const openCommunity = useExplorerStore((s) => s.openCommunity);
  const openNode360 = useExplorerStore((s) => s.openNode360);
  const shellRef = useRef<HTMLDivElement>(null);
  const [, force] = useState(0);
  const anyModalOpen = searchModalOpen || pathFinderOpen || compareModalOpen || caveatsModalOpen;

  // Development-only instrumentation for correctness/performance regression checks.
  if (import.meta.env.DEV) (window as any).__explorerStore = useExplorerStore;

  useEffect(() => {
    document.documentElement.classList.toggle("dark", darkMode);
    force((n) => n + 1); // charts read colours from CSS variables
  }, [darkMode]);

  // Route → store on every navigation (Back and Forward included).
  useLayoutEffect(() => {
    applyRouteToStore(route);
  }, [route]);

  // Store → route: pages and Explorer code still call openSubject / setWorkspaceTab.
  useEffect(
    () =>
      useExplorerStore.subscribe((s, prev) => {
        if (
          s.workspaceTab === prev.workspaceTab &&
          s.selectedSubjectId === prev.selectedSubjectId &&
          s.selectedGroupId === prev.selectedGroupId &&
          s.selectedCommunityId === prev.selectedCommunityId &&
          s.node360Id === prev.node360Id
        )
          return;
        const next = pathFromStore(currentRoute());
        if (next) navigate(next);
      }),
    [],
  );

  // ⌘K / Ctrl+K and "/" open search anywhere.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const t = e.target as HTMLElement | null;
      const typing = t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.tagName === "SELECT" || t.isContentEditable);
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        useExplorerStore.getState().setSearchModalOpen(true);
      } else if (!anyModalOpen && !typing && e.key === "/") {
        e.preventDefault();
        useExplorerStore.getState().setSearchModalOpen(true);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [anyModalOpen]);

  // Background inert while a dialog is open.
  useEffect(() => {
    const el = shellRef.current;
    if (!el) return;
    if (anyModalOpen) {
      el.setAttribute("inert", "");
      el.setAttribute("aria-hidden", "true");
    } else {
      el.removeAttribute("inert");
      el.removeAttribute("aria-hidden");
    }
  }, [anyModalOpen]);

  // Move focus to the page on navigation so keyboard and screen-reader users land on content.
  const lastPath = useRef<string | null>(null);
  useEffect(() => {
    const key = `${route.page}/${route.param || ""}`;
    const prev = lastPath.current;
    lastPath.current = key;
    if (prev === null || prev === key) return;
    if (route.page === "ask" || route.page === "explore") return;
    document.getElementById("main-content")?.focus({ preventScroll: true });
  }, [route.page, route.param]);

  const summaryQuery = useQuery({
    queryKey: ["graph-summary"],
    queryFn: () => explorerApi.getSummary(),
    staleTime: 300_000,
  });

  const isExplore = route.page === "explore";
  const isRelease = route.page === "network" && route.param === "release";
  const fullBleed = route.page === "ask" || isExplore || isRelease;

  const fallback = <p role="status" className="loading-line view">Loading…</p>;

  let page: React.ReactNode;
  switch (route.page) {
    case "pulse":
      page = <PulsePage />;
      break;
    case "ask":
      page = <AskPage onOpenNode360={openNode360} />;
      break;
    case "trends":
      page = <div className="view"><TrendsPage onOpenSubject={openSubject} /></div>;
      break;
    case "topics":
      page = (
        <div className="view">
          <SubjectPage
            subjectId={route.param}
            onSelectSubject={openSubject}
            onOpenGroup={openGroup}
            onOpenCommunity={openCommunity}
            onOpenNode360={openNode360}
          />
        </div>
      );
      break;
    case "groups":
      page = <div className="view"><GroupsPage selectedGroupId={selectedGroupId} onSelectGroup={openGroup} onOpenNode360={openNode360} /></div>;
      break;
    case "map":
      page = <div className="view"><CommunitiesPage selectedCommunityId={selectedCommunityId} onSelectCommunity={openCommunity} onOpenNode360={openNode360} /></div>;
      break;
    case "network":
      page = isRelease ? (
        <div className="release-wrap">
        <NetworkViews current="release" />
        <AnalyticsView
          summary={summaryQuery.data}
          onFocusNodeInGraph={(id, name) => {
            const state = useExplorerStore.getState();
            state.setViewMode(id.startsWith("researcher:") ? "researchers" : id.startsWith("organization:") ? "organizations" : "citations");
            state.resetFilters();
            state.setEdgeFilterMode("all");
            queueExploreFocus({ nodeId: id, name, replace: true });
            state.setWorkspaceTab("graph");
          }}
        />
        </div>
      ) : (
        <div className="view">
          <NetworkViews current="enriched" />
          <NetworkSciencePage onOpenNode360={openNode360} />
        </div>
      );
      break;
    case "explore":
      page = <ExplorePage />;
      break;
    case "node":
      page = <div className="view"><Node360Page nodeId={node360Id} onSelectNode={openNode360} /></div>;
      break;
    case "about":
      page = <div className="view"><AboutDataPage /></div>;
      break;
  }

  return (
    <>
      <div ref={shellRef} data-testid="workspace-shell" className="contents">
        <AppShell route={route} fullBleed={fullBleed}>
          <React.Suspense fallback={fallback}>{page}</React.Suspense>
        </AppShell>
      </div>
      <React.Suspense fallback={null}>
        {searchModalOpen &&
          (isExplore ? (
            <SearchCommandModal onFocusNodeInGraph={(id, name) => exploreFocusHandler()?.(id, name)} />
          ) : (
            <NavigatorSearchModal />
          ))}
        {caveatsModalOpen && <CaveatsModal summary={summaryQuery.data} />}
      </React.Suspense>
    </>
  );
};
