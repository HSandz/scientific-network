import React, { useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { navigatorApi } from "../../lib/navigatorApi";
import { useModalDialog } from "../../lib/useModalDialog";
import { displayName, subjectName } from "../../lib/names";
import { navigate, pathFor } from "../../lib/router";
import { useExplorerStore } from "../../stores/useExplorerStore";
import { EntityDot } from "../ui/primitives";
import { Icon } from "../shell/icons";

interface Hit {
  key: string;
  name: string;
  kind: string;
  detail?: string;
  go: string;
}

const KIND_WORD: Record<string, string> = {
  Method: "Method",
  Task: "Task",
  Dataset: "Dataset",
  Topic: "Topic",
  Organization: "Organization",
  Researcher: "Researcher",
  Paper: "Paper",
};

function targetFor(id: string, label: string): string {
  if (["Method", "Task", "Dataset", "Topic"].includes(label)) return pathFor("topics", id);
  if (label === "Organization") return pathFor("groups", id);
  return pathFor("node", id);
}

/**
 * Global search for the Navigator pages: subjects (methods, tasks, datasets, topics),
 * organizations, researchers and papers in the enriched graph. Each hit opens its page.
 */
export const NavigatorSearchModal: React.FC = () => {
  const open = useExplorerStore((s) => s.searchModalOpen);
  const setOpen = useExplorerStore((s) => s.setSearchModalOpen);
  const [query, setQuery] = useState("");
  const [debounced, setDebounced] = useState("");
  const [active, setActive] = useState(0);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const dialogRef = useModalDialog({ isOpen: open, onClose: () => setOpen(false), initialFocusRef: inputRef });

  useEffect(() => {
    if (open) {
      setQuery("");
      setDebounced("");
      setActive(0);
    }
  }, [open]);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(query.trim()), 140);
    return () => clearTimeout(t);
  }, [query]);

  const subjects = useQuery({
    queryKey: ["nav-search-subjects", debounced],
    queryFn: ({ signal }) => navigatorApi.listSubjects({ q: debounced || undefined, limit: debounced ? 8 : 6 }, signal),
    enabled: open,
    staleTime: 60_000,
  });
  const entities = useQuery({
    queryKey: ["nav-search-entities", debounced],
    queryFn: () => navigatorApi.searchEnriched({ q: debounced, limit: 12 }),
    enabled: open && debounced.length >= 2,
    staleTime: 60_000,
  });

  const hits: Hit[] = useMemo(() => {
    const out: Hit[] = [];
    for (const s of subjects.data?.items || []) {
      out.push({
        key: s.id,
        name: subjectName(s.name, s.kind),
        kind: s.kind,
        detail: `${s.total_papers.toLocaleString("en")} papers`,
        go: pathFor("topics", s.id),
      });
    }
    const seen = new Set(out.map((h) => h.key));
    for (const e of entities.data?.results || []) {
      if (seen.has(e.id) || ["Method", "Task", "Dataset", "Topic"].includes(e.label)) continue;
      out.push({
        key: e.id,
        name: displayName(e.name, e.label),
        kind: e.label,
        detail: e.label === "Paper" && e.year ? String(e.year) : undefined,
        go: targetFor(e.id, e.label),
      });
    }
    return out.slice(0, 14);
  }, [subjects.data, entities.data]);

  useEffect(() => setActive(0), [debounced, hits.length]);

  const choose = (h: Hit) => {
    setOpen(false);
    navigate(h.go);
  };
  const askInstead = () => {
    setOpen(false);
    navigate(`${pathFor("ask")}?q=${encodeURIComponent(query.trim())}`);
  };

  if (!open) return null;
  const loading = subjects.isFetching || entities.isFetching;
  const listId = "nav-search-results";

  return (
    <div className="search-backdrop" onClick={() => setOpen(false)} data-testid="search-modal-backdrop">
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="nav-search-heading"
        tabIndex={-1}
        className="search-dialog"
        onClick={(e) => e.stopPropagation()}
        data-testid="search-modal"
      >
        <h2 id="nav-search-heading" className="sr-only">
          Search topics, methods, groups and people
        </h2>
        <div className="search-dialog-input">
          <Icon name="search" size={18} strokeWidth={1.8} />
          <input
            ref={inputRef}
            type="text"
            role="combobox"
            aria-expanded={hits.length > 0}
            aria-controls={listId}
            aria-activedescendant={hits[active] ? `nav-hit-${active}` : undefined}
            aria-autocomplete="list"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "ArrowDown") {
                e.preventDefault();
                setActive((a) => Math.min(hits.length - 1, a + 1));
              } else if (e.key === "ArrowUp") {
                e.preventDefault();
                setActive((a) => Math.max(0, a - 1));
              } else if (e.key === "Enter") {
                e.preventDefault();
                if (hits[active]) choose(hits[active]);
                else if (query.trim()) askInstead();
              }
            }}
            placeholder="Search topics, methods, groups, people…"
            data-testid="global-search-input"
          />
          <button type="button" className="quiet-btn" onClick={() => setOpen(false)} aria-label="Close search" data-testid="close-search-modal">
            Esc
          </button>
        </div>
        <ul id={listId} role="listbox" className="search-hits" aria-label="Results">
          {!debounced && <li className="search-hint">Popular subjects</li>}
          {hits.map((h, i) => (
            <li
              key={h.key}
              id={`nav-hit-${i}`}
              role="option"
              aria-selected={i === active}
              className={i === active ? "is-active" : ""}
              onMouseEnter={() => setActive(i)}
              onMouseDown={(e) => {
                e.preventDefault();
                choose(h);
              }}
              data-testid="search-hit"
            >
              <EntityDot kind={h.kind} />
              <span className="search-hit-name">{h.name}</span>
              {h.detail && <span className="search-hit-detail">{h.detail}</span>}
              <span className="search-hit-kind">{KIND_WORD[h.kind] || h.kind}</span>
            </li>
          ))}
          {debounced && !loading && hits.length === 0 && (
            <li className="search-hint">Nothing matches “{debounced}”. Try a method such as diffusion models, or ask it as a question.</li>
          )}
        </ul>
        <div className="search-foot">
          {query.trim() ? (
            <button type="button" className="textlink" onClick={askInstead}>
              Ask “{query.trim().slice(0, 60)}”
            </button>
          ) : (
            <span className="muted">Type a name, or press Enter to ask it as a question.</span>
          )}
          {loading && <span className="spin" aria-label="Searching" />}
        </div>
      </div>
    </div>
  );
};
