import React, { useEffect, useRef, useState } from "react";
import { useExplorerStore } from "../../stores/useExplorerStore";
import { useConversations } from "../../lib/conversations";
import { linkClick, navigate, pathFor, type PageKey, type Route } from "../../lib/router";
import { BrandMark, Icon } from "./icons";

const NAV: Array<[PageKey, string]> = [
  ["pulse", "Pulse"],
  ["ask", "Ask"],
  ["trends", "Trends"],
  ["topics", "Topics"],
  ["groups", "Groups"],
  ["map", "Map"],
  ["network", "Network"],
  ["explore", "Explore"],
];
const MOBILE_TABS: Array<[PageKey, string]> = [
  ["pulse", "Pulse"],
  ["ask", "Ask"],
  ["trends", "Trends"],
  ["topics", "Topics"],
  ["groups", "Groups"],
];
const MORE: Array<[PageKey, string]> = [
  ["map", "Map"],
  ["network", "Network"],
  ["explore", "Explore"],
  ["about", "About"],
];

interface AppShellProps {
  route: Route;
  /** Ask and Explore fill the viewport and manage their own scrolling. */
  fullBleed: boolean;
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({ route, fullBleed, children }) => {
  const darkMode = useExplorerStore((s) => s.darkMode);
  const toggleDarkMode = useExplorerStore((s) => s.toggleDarkMode);
  const setSearchModalOpen = useExplorerStore((s) => s.setSearchModalOpen);
  const conversations = useConversations((s) => s.conversations);
  const [moreOpen, setMoreOpen] = useState(false);
  const moreRef = useRef<HTMLDivElement>(null);
  // A node profile belongs to no rail item, so none is marked as current there.
  const active: PageKey = route.page;

  useEffect(() => setMoreOpen(false), [route.path]);
  useEffect(() => {
    if (!moreOpen) return;
    const onDown = (e: MouseEvent) => {
      if (moreRef.current && !moreRef.current.contains(e.target as Node)) setMoreOpen(false);
    };
    // Menu keyboard pattern: focus moves in on open, arrows cycle, Escape returns to the button.
    const items = () => Array.from(moreRef.current?.querySelectorAll<HTMLElement>('[role="menuitem"]') || []);
    items()[0]?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setMoreOpen(false);
        moreRef.current?.querySelector<HTMLElement>('[data-testid="tabbar-more"]')?.focus();
        return;
      }
      if (e.key !== "ArrowDown" && e.key !== "ArrowUp") return;
      const list = items();
      const at = list.indexOf(document.activeElement as HTMLElement);
      e.preventDefault();
      list[(at + (e.key === "ArrowDown" ? 1 : -1) + list.length) % list.length]?.focus();
    };
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [moreOpen]);

  const recent = conversations.slice(0, 6);
  const activeConversation = route.page === "ask" ? route.param : null;

  const navItem = (key: PageKey, label: string) => {
    const href = pathFor(key);
    return (
      <a
        key={key}
        href={href}
        onClick={(e) => linkClick(e, href)}
        className="nav-item"
        data-testid={`nav-${key}`}
        title={label}
        aria-current={active === key ? "page" : undefined}
      >
        <Icon name={key} />
        <span>{label}</span>
      </a>
    );
  };

  return (
    <div className={route.page === "explore" ? "app-shell app-shell--tool" : "app-shell"}>
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <nav className="rail" aria-label="Main">
        <a className="brand" href="/" onClick={(e) => linkClick(e, "/")}>
          <BrandMark />
          <span className="brand-name">Research Trend Navigator</span>
        </a>
        {NAV.map(([key, label]) => (
          <React.Fragment key={key}>
            {navItem(key, label)}
            {key === "ask" && route.page === "ask" && recent.length > 0 && (
              <div className="history" aria-label="Recent conversations" role="group">
                <div className="history-title">Recent conversations</div>
                {recent.map((c) => {
                  const href = pathFor("ask", c.id);
                  return (
                    <a
                      key={c.id}
                      href={href}
                      onClick={(e) => linkClick(e, href)}
                      title={c.turns[0]?.question || c.title}
                      aria-current={activeConversation === c.id ? "true" : undefined}
                      data-testid="rail-conversation"
                    >
                      {c.title}
                    </a>
                  );
                })}
              </div>
            )}
          </React.Fragment>
        ))}
        <div className="rail-spacer" />
        {navItem("about", "About")}
      </nav>

      <div className="shell-main">
        <header className="topbar">
          <button
            type="button"
            className="search-trigger"
            onClick={() => setSearchModalOpen(true)}
            data-testid="open-global-search"
            aria-label="Search topics, methods, groups and people"
            aria-keyshortcuts="Control+K Meta+K /"
          >
            <Icon name="search" size={18} strokeWidth={1.8} />
            <span className="search-placeholder">Search topics, methods, groups, people…</span>
            <kbd aria-hidden="true">⌘K</kbd>
          </button>
          <div className="topbar-spacer" />
          <button
            type="button"
            className="icon-btn"
            onClick={toggleDarkMode}
            data-testid="theme-toggle"
            aria-label={darkMode ? "Switch to light theme" : "Switch to dark theme"}
            title={darkMode ? "Switch to light theme" : "Switch to dark theme"}
          >
            <Icon name={darkMode ? "sun" : "moon"} size={19} strokeWidth={1.7} />
          </button>
        </header>

        <main
          id="main-content"
          tabIndex={-1}
          className={fullBleed ? "main-content main-content--bleed" : "main-content"}
        >
          {children}
        </main>
      </div>

      <nav className="tabbar" aria-label="Main">
        {MOBILE_TABS.map(([key, label]) => {
          const href = pathFor(key);
          return (
            <a
              key={key}
              href={href}
              onClick={(e) => linkClick(e, href)}
              aria-current={active === key ? "page" : undefined}
              data-testid={`tabbar-${key}`}
            >
              <Icon name={key} size={22} />
              <span>{label}</span>
            </a>
          );
        })}
        <div ref={moreRef} className="tabbar-more">
          <button
            type="button"
            aria-expanded={moreOpen}
            aria-haspopup="menu"
            aria-controls="more-sheet"
            aria-current={MORE.some(([k]) => k === active) ? "page" : undefined}
            onClick={() => setMoreOpen((v) => !v)}
            data-testid="tabbar-more"
          >
            <Icon name="more" size={22} />
            <span>More</span>
          </button>
          {moreOpen && (
            <div className="more-sheet" id="more-sheet" role="menu">
              {MORE.map(([key, label]) => (
                <button
                  key={key}
                  type="button"
                  role="menuitem"
                  onClick={() => {
                    setMoreOpen(false);
                    navigate(pathFor(key));
                  }}
                  aria-current={active === key ? "page" : undefined}
                >
                  <Icon name={key} />
                  <span>{label}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </nav>
    </div>
  );
};
