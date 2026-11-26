/**
 * Presentation model for Ask: turns the SSE trace (parsed → plan → step → subgraph → token →
 * citations → final) into plain-language plan steps, readable tables, an automatically chosen
 * chart, a deterministic graph layout and numbered footnotes. Nothing here changes the data:
 * values are formatted for reading and every identifier is replaced by its name.
 */
import { displayName, kindFromId, orgName, plural, shortOrg, subjectName } from "./names";

export type Row = Record<string, unknown>;

export interface TraceStep {
  step: number;
  tool: string;
  args?: Record<string, any>;
  rows: Row[];
  row_count?: number;
  note?: string;
  paper_ids?: string[];
  source_kind?: string;
  empty?: boolean;
  error?: string;
  purpose?: string;
}

export interface LinkedEntity {
  text?: string;
  entity_type?: string | null;
  id?: string | null;
  name?: string | null;
  paper_count?: number;
  kind_choices?: Array<{ id: string; label: string; name: string; paper_count?: number }>;
  alternatives?: Array<{ id: string; label: string; name: string; paper_count?: number }>;
}

export interface SubgraphData {
  nodes: Array<{ id: string; label?: string; name?: string; hop?: number }>;
  edges: Array<{ source: string; target: string; relation?: string; support_count?: number; hop?: number }>;
}

export interface NamedEntity {
  name: string;
  label: string | null;
}

/* ---------------------------------------------------------------------------------------- */
/* Names                                                                                     */
/* ---------------------------------------------------------------------------------------- */

const str = (x: unknown): string => (typeof x === "string" ? x : x == null ? "" : String(x));
const num = (x: unknown): number | null => (typeof x === "number" && Number.isFinite(x) ? x : null);

/** Every id → name we can learn from the trace, so no raw id ever reaches the screen. */
export function buildNameIndex(linked: LinkedEntity[], steps: TraceStep[], subgraph?: SubgraphData | null): Map<string, NamedEntity> {
  const idx = new Map<string, NamedEntity>();
  const put = (id: unknown, name: unknown, label?: unknown) => {
    const i = str(id);
    const n = str(name);
    if (!i || !n || idx.has(i)) return;
    const l = str(label) || kindFromId(i);
    idx.set(i, { name: displayName(n, l), label: l });
  };
  for (const l of linked) {
    put(l.id, l.name, l.entity_type);
    for (const a of l.alternatives || []) put(a.id, a.name, a.label);
    for (const a of l.kind_choices || []) put(a.id, a.name, a.label);
  }
  for (const n of subgraph?.nodes || []) put(n.id, n.name, n.label);
  for (const s of steps) {
    for (const r of s.rows || []) {
      put(r.id, r.name, r.label);
      put(r.neighbor_id, r.neighbor_name, r.neighbor_label);
      put(r.entity_id, r.entity_name, "Organization");
      put(r.group_key, r.label, null);
      put(r.community_id, r.title, "Community");
    }
  }
  return idx;
}

export function nameOf(idx: Map<string, NamedEntity>, id: unknown, fallback = "this entity"): string {
  const i = str(id);
  return idx.get(i)?.name || fallback;
}

/* ---------------------------------------------------------------------------------------- */
/* Plan steps in plain language                                                              */
/* ---------------------------------------------------------------------------------------- */

const LABEL_PLURAL: Record<string, string> = {
  Organization: "organizations",
  Researcher: "researchers",
  Method: "methods",
  Task: "tasks",
  Dataset: "datasets",
  Topic: "topics",
  Paper: "papers",
};
const NETWORK_WORD: Record<string, string> = {
  N1: "co-authorship network",
  N2: "organization collaboration network",
  N3: "citation network",
  N4: "full knowledge graph",
};

function subjectFromFilters(f: Record<string, any> | undefined, idx: Map<string, NamedEntity>): string | null {
  if (!f) return null;
  for (const k of ["method_id", "task_id", "dataset_id", "topic_id", "subject_id"]) {
    if (typeof f[k] === "string") return nameOf(idx, f[k], "the subject").toLowerCase();
  }
  return null;
}

/** Parse the share-growth note: "37 organization(s) qualified (27 excluded …); showing top 15". */
function shareGrowthResult(note: string | undefined, rowCount: number): string {
  const q = note?.match(/(\d+) organi[sz]ation\(s\) qualified/);
  const top = note?.match(/showing top (\d+)/);
  if (q) return `${q[1]} organizations had enough papers; ${top ? top[1] : rowCount} grew the most`;
  return `${plural(rowCount, "organization")} compared`;
}

export interface PlainStep {
  key: string;
  title: string;
  result?: string;
  state: "pending" | "active" | "done" | "error";
  stepNumber?: number;
}

export function describeStep(tool: string, args: Record<string, any> = {}, idx: Map<string, NamedEntity>, mode?: string): string {
  const f = (args.filters || {}) as Record<string, any>;
  const targets: string[] = Array.isArray(f.target_labels) ? f.target_labels : [];
  const tgt = targets.length ? targets.map((t) => LABEL_PLURAL[t] || `${t.toLowerCase()}s`).join(" and ") : "connected entities";
  const preds: string[] = Array.isArray(args.predicates) ? args.predicates : [];
  const center = nameOf(idx, args.node_id, "the starting point");
  switch (tool) {
    case "find":
      return `Look up “${str(args.text) || "the name"}” in the graph`;
    case "neighbors":
      if (f.include_cooccurrence) return `Find ${tgt} that appear in the same papers as ${center.toLowerCase() === center ? center : center}`;
      if (preds.includes("COAUTHORED_WITH")) return `Find researchers who co-authored with ${center}`;
      if (preds.includes("COLLABORATED_WITH")) return `Find organizations that co-authored with ${center}`;
      return `Follow ${center}'s links to ${tgt}`;
    case "path":
      return `Find the shortest connection between ${nameOf(idx, args.source_id, "the first")} and ${nameOf(idx, args.target_id, "the second")}`;
    case "papers": {
      const s = subjectFromFilters(f, idx);
      return s ? `Find papers on ${s}${f.year ? ` from ${f.year}` : ""}` : "Find the matching papers";
    }
    case "aggregate": {
      const s = subjectFromFilters(f, idx) || (Array.isArray(args.entity_ids) && args.entity_ids.length === 1 ? nameOf(idx, args.entity_ids[0], "the subject").toLowerCase() : "the subject");
      if (args.metric === "share_growth" || args.by === "organization_year") {
        const y = f.after_year || 2022;
        return `Compare each organization's share of ${s} papers up to ${y} and after`;
      }
      if (args.by === "year") return args.metric === "share" || args.metric === "paper_share" ? `Work out ${s}'s share of papers each year` : `Count ${s} papers each year`;
      return `Count ${s} papers by ${str(args.by) || "group"}`;
    }
    case "rank": {
      const scope = args.scope ? nameOf(idx, args.scope, str(args.scope).split(":").pop() || "the subject") : null;
      const who = args.network === "N1" ? "researchers" : "organizations";
      if (scope && (args.measure === "lift" || args.measure === "ppr")) return `Rank ${who} by how concentrated their work is on ${scope.toLowerCase()}`;
      if (scope) return `Rank ${who} working on ${scope.toLowerCase()}`;
      return `Rank ${who} by influence in the ${NETWORK_WORD[str(args.network)] || "network"}`;
    }
    case "community":
      return `Find the research community around ${nameOf(idx, args.node_or_community_id, "this entity")}`;
    case "community_report":
      return mode === "global" ? "Read the summaries of the research communities" : "Read the community report";
    case "local_search":
      return "Gather what the graph says about the subject";
    case "trend": {
      const kind = str(args.subject_or_kind);
      if (["Method", "Task", "Dataset", "Topic"].includes(kind)) {
        const cls = args.trend_class ? `${args.trend_class} ` : "";
        return `Rank ${cls}${LABEL_PLURAL[kind]} by how fast their share of papers grew, 2021 to 2025`;
      }
      return `Look up ${nameOf(idx, kind, "the subject")}'s share of papers, 2021 to 2025`;
    }
    default:
      return "Run a graph query";
  }
}

export function describeResult(step: TraceStep, idx: Map<string, NamedEntity>): string {
  const n = step.row_count ?? step.rows.length;
  if (step.error) return "This step failed";
  if (step.empty || n === 0) return "No matching records";
  const f = (step.args?.filters || {}) as Record<string, any>;
  switch (step.tool) {
    case "find":
      return plural(n, "match", "matches");
    case "neighbors": {
      const t = Array.isArray(f.target_labels) && f.target_labels.length === 1 ? LABEL_PLURAL[f.target_labels[0]] : null;
      const preds: string[] = Array.isArray(step.args?.predicates) ? step.args!.predicates : [];
      if (preds.includes("COLLABORATED_WITH")) return `${plural(n, "collaborator")} found`;
      if (preds.includes("COAUTHORED_WITH")) return `${plural(n, "co-author")} found`;
      return `${n.toLocaleString("en")} ${t || "connections"} found`;
    }
    case "path":
      return `Connected in ${plural(n, "step")}`;
    case "papers":
      return `${plural(n, "paper")} found`;
    case "aggregate":
      if (step.args?.metric === "share_growth" || step.args?.by === "organization_year") return shareGrowthResult(step.note, step.rows.length);
      return `${plural(n, step.args?.by === "year" ? "year" : "group")} counted`;
    case "rank":
      return `${plural(n, step.args?.network === "N1" ? "researcher" : "organization")} ranked`;
    case "trend":
      return n === 1 ? "Trend found" : `${n} ${step.args?.trend_class ? `are ${step.args.trend_class}` : "subjects ranked"}`;
    case "community_report": {
      const m = step.note?.match(/over (\d+) community reports/);
      return m ? `${m[1]} community summaries read, ${plural(n, "finding")} kept` : `${plural(n, "finding")}`;
    }
    case "local_search":
      return `${plural(n, "record")} gathered`;
    default:
      return plural(n, "row");
  }
  void idx;
}

export function recognisedText(linked: LinkedEntity[], parsed: Record<string, any> | null | undefined): string {
  const names = linked
    .filter((l) => l.name || l.text)
    .filter((l) => l.id)
    .map((l) => `${displayName(l.name || l.text || "", l.entity_type)} (${(l.entity_type || "name").toLowerCase()})`);
  const after = parsed?.after_year || parsed?.filters?.after_year;
  const year = parsed?.year || parsed?.filters?.year;
  const parts = [...names];
  if (after) parts.push(`after ${after}`);
  else if (year) parts.push(`in ${year}`);
  return parts.length ? `Recognised ${parts.join(", ")}` : "No specific names; answering from the whole graph";
}

/* ---------------------------------------------------------------------------------------- */
/* Tables                                                                                    */
/* ---------------------------------------------------------------------------------------- */

export type CellFormat = "text" | "int" | "pct" | "pp" | "x" | "pctYear" | "score";
export interface TableColumn {
  key: string;
  label: string;
  format: CellFormat;
  numeric?: boolean;
}
export interface StepTable {
  step: number;
  title: string;
  columns: TableColumn[];
  rows: Array<Record<string, unknown>>;
  /** Paper ids behind each row, if any (for footnotes). */
  rowPapers: Array<string[]>;
  /** Entity id behind each row, for links. */
  rowIds: Array<string | null>;
  totalRows: number;
}

export function formatCell(v: unknown, f: CellFormat): string {
  const n = num(v);
  switch (f) {
    case "int":
      return n == null ? str(v) : n.toLocaleString("en");
    case "pct":
      return n == null ? str(v) : `${(n * 100).toFixed(1)}%`;
    case "pp":
      return n == null ? str(v) : `${n >= 0 ? "+" : "−"}${Math.abs(n * 100).toFixed(1)} points`;
    case "x":
      return n == null ? str(v) : `${n.toFixed(1)}×`;
    case "pctYear":
      return n == null ? str(v) : `${n >= 0 ? "+" : "−"}${Math.abs(n * 100).toFixed(0)}% a year`;
    case "score":
      return n == null ? str(v) : n < 0.01 ? n.toExponential(1) : n.toFixed(3);
    default:
      return str(v);
  }
}

const RELATION_WORD: Record<string, string> = {
  AUTHORED: "wrote",
  COAUTHORED_WITH: "co-authored with",
  AFFILIATED_WITH: "is affiliated with",
  COLLABORATED_WITH: "collaborated with",
  CITES: "cites",
  PUBLISHED_IN: "published in",
  HAS_TOPIC: "is about",
  USES_METHOD: "uses",
  ADDRESSES_TASK: "addresses",
  USES_DATASET: "uses",
  APPLIED_TO: "is applied to",
  EVALUATED_ON: "is evaluated on",
  COOCCURS_IN_PAPERS: "appears with",
};

function neighborRows(s: TraceStep, idx: Map<string, NamedEntity>): Row[] {
  // One row per neighbour, keeping the strongest link.
  const best = new Map<string, Row>();
  for (const r of s.rows) {
    const id = str(r.neighbor_id) || (str(r.source_id) === str(r.center_id) ? str(r.target_id) : str(r.source_id));
    if (!id) continue;
    const prev = best.get(id);
    if (!prev || (num(r.support_count) || 0) > (num(prev.support_count) || 0)) best.set(id, { ...r, _id: id });
  }
  return [...best.values()]
    .sort((a, b) => (num(b.support_count) || 0) - (num(a.support_count) || 0))
    .map((r): Row => ({ ...r, _name: str(r.neighbor_name) ? displayName(str(r.neighbor_name), str(r.neighbor_label)) : nameOf(idx, r._id, "Unnamed") }));
}

export function buildTables(steps: TraceStep[], idx: Map<string, NamedEntity>): StepTable[] {
  const out: StepTable[] = [];
  for (const s of steps) {
    if (!s.rows?.length) continue;
    const f = (s.args?.filters || {}) as Record<string, any>;
    const base = { step: s.step, totalRows: s.row_count ?? s.rows.length };
    if (s.tool === "neighbors") {
      const rows = neighborRows(s, idx);
      const lbl = Array.isArray(f.target_labels) && f.target_labels.length === 1 ? f.target_labels[0] : "Entity";
      const isCo = rows.some((r) => r.relation === "COOCCURS_IN_PAPERS") || f.include_cooccurrence;
      out.push({
        ...base,
        title: describeStep(s.tool, s.args, idx).replace(/^Find /, "").replace(/^./, (c) => c.toUpperCase()),
        columns: [
          { key: "name", label: lbl === "Entity" ? "Name" : lbl, format: "text" },
          ...(rows.some((r) => r.neighbor_sector) ? [{ key: "sector", label: "Sector", format: "text" as const }] : []),
          { key: "shared", label: "Shared papers", format: "int", numeric: true },
          ...(isCo ? [{ key: "link", label: "Link", format: "text" as const }] : []),
        ],
        rows: rows.map((r) => ({
          name: r._name,
          sector: str(r.neighbor_sector),
          shared: num(r.support_count),
          link: r.relation === "COOCCURS_IN_PAPERS" ? "same paper" : "stated in a paper",
        })),
        rowPapers: rows.map((r) => (Array.isArray(r.paper_ids) ? (r.paper_ids as string[]) : Array.isArray(r.support_paper_ids) ? (r.support_paper_ids as string[]) : [])),
        rowIds: rows.map((r) => str(r._id) || null),
      });
    } else if (s.tool === "aggregate" && (s.args?.metric === "share_growth" || s.args?.by === "organization_year")) {
      const y = f.after_year || 2022;
      const preShare = Object.keys(s.rows[0]).find((k) => /^pre_.*_share$/.test(k)) || "pre_share";
      const postShare = Object.keys(s.rows[0]).find((k) => /^post_.*_share$/.test(k)) || "post_share";
      out.push({
        ...base,
        title: `Share of ${subjectFromFilters(f, idx) || "subject"} papers, up to ${y} and after`,
        columns: [
          { key: "name", label: "Organization", format: "text" },
          { key: "pre", label: `Up to ${y}`, format: "text", numeric: true },
          { key: "post", label: `After ${y}`, format: "text", numeric: true },
          { key: "share", label: "Share after", format: "pct", numeric: true },
          { key: "change", label: "Change", format: "pp", numeric: true },
        ],
        rows: s.rows.map((r) => ({
          name: orgName(str(r.entity_name)),
          pre: r.pre_papers,
          post: r.post_papers,
          share: r[postShare],
          change: r.share_delta,
          _pre: r[preShare],
        })),
        rowPapers: s.rows.map((r) => (Array.isArray(r.paper_ids) ? (r.paper_ids as string[]) : [])),
        rowIds: s.rows.map((r) => str(r.entity_id) || null),
      });
    } else if (s.tool === "aggregate") {
      const byYear = s.args?.by === "year";
      out.push({
        ...base,
        title: describeStep(s.tool, s.args, idx).replace(/^(Count|Work out) /, "").replace(/^./, (c) => c.toUpperCase()),
        columns: [
          { key: "name", label: byYear ? "Year" : "Name", format: "text" },
          { key: "papers", label: "Papers", format: "int", numeric: true },
          ...(s.rows.some((r) => num(r.share) != null) ? [{ key: "share", label: "Share of papers", format: "pct" as const, numeric: true }] : []),
        ],
        rows: s.rows.map((r) => ({ name: byYear ? str(r.label || r.group_key) : displayName(str(r.label), kindFromId(str(r.group_key))), papers: r.paper_count, share: r.share })),
        rowPapers: s.rows.map((r) => (Array.isArray(r.paper_ids) ? (r.paper_ids as string[]) : [])),
        rowIds: s.rows.map((r) => (byYear ? null : str(r.group_key) || null)),
      });
    } else if (s.tool === "rank") {
      const lift = s.rows.some((r) => num(r.lift) != null);
      const scope = s.args?.scope ? nameOf(idx, s.args.scope, "the subject").toLowerCase() : null;
      out.push({
        ...base,
        title: lift && scope ? `Organizations most specialised in ${scope}` : describeStep(s.tool, s.args, idx).replace(/^Rank /, "").replace(/^./, (c) => c.toUpperCase()),
        columns: lift
          ? [
              { key: "name", label: s.args?.network === "N1" ? "Researcher" : "Organization", format: "text" },
              { key: "lift", label: "Specialisation", format: "x", numeric: true },
              { key: "subject", label: "Papers on the subject", format: "int", numeric: true },
              { key: "total", label: "All papers", format: "int", numeric: true },
            ]
          : [
              { key: "name", label: "Name", format: "text" },
              { key: "score", label: "Influence score", format: "score", numeric: true },
              ...(s.rows.some((r) => num(r.degree) != null) ? [{ key: "degree", label: "Direct links", format: "int" as const, numeric: true }] : []),
            ],
        rows: s.rows.map((r) => ({
          name: displayName(str(r.name), str(r.label) || kindFromId(str(r.id))),
          lift: r.lift,
          subject: r.subject_papers,
          total: r.total_papers,
          score: r.pagerank ?? r.score ?? r.ppr_score,
          degree: r.degree,
        })),
        rowPapers: s.rows.map(() => []),
        rowIds: s.rows.map((r) => str(r.id) || null),
      });
    } else if (s.tool === "trend") {
      out.push({
        ...base,
        title: s.rows.length > 1 ? `${s.args?.trend_class ? `${String(s.args.trend_class)[0].toUpperCase()}${String(s.args.trend_class).slice(1)} ` : ""}${LABEL_PLURAL[str(s.rows[0].kind)] || "subjects"}` : "Share of papers by year",
        columns: [
          { key: "name", label: str(s.rows[0].kind) || "Subject", format: "text" },
          { key: "papers", label: "Papers", format: "int", numeric: true },
          { key: "s21", label: "Share 2021", format: "pct", numeric: true },
          { key: "s25", label: "Share 2025", format: "pct", numeric: true },
          { key: "cagr", label: "Growth", format: "pctYear", numeric: true },
        ],
        rows: s.rows.map((r) => {
          const sh = (r.share_by_year || {}) as Record<string, number>;
          return { name: subjectName(str(r.name), str(r.kind)), papers: r.total_papers, s21: sh["2021"], s25: sh["2025"], cagr: r.cagr_of_share_2021_2025 };
        }),
        rowPapers: s.rows.map(() => []),
        rowIds: s.rows.map((r) => str(r.id) || null),
      });
    } else if (s.tool === "papers") {
      out.push({
        ...base,
        title: "Papers",
        columns: [
          { key: "name", label: "Title", format: "text" },
          { key: "year", label: "Year", format: "text", numeric: true },
          { key: "cited", label: "Cited here", format: "int", numeric: true },
        ],
        rows: s.rows.map((r) => ({ name: str(r.title), year: r.year, cited: r.in_citations })),
        rowPapers: s.rows.map((r) => [str(r.id)]),
        rowIds: s.rows.map((r) => str(r.id) || null),
      });
    } else if (s.tool === "path") {
      out.push({
        ...base,
        title: "The connection, link by link",
        columns: [
          { key: "from", label: "From", format: "text" },
          { key: "link", label: "Link", format: "text" },
          { key: "to", label: "To", format: "text" },
        ],
        rows: s.rows.map((r) => ({ from: nameOf(idx, r.source, "Unnamed"), link: RELATION_WORD[str(r.relation)] || str(r.relation).toLowerCase().replace(/_/g, " "), to: nameOf(idx, r.target, "Unnamed") })),
        rowPapers: s.rows.map(() => []),
        rowIds: s.rows.map(() => null),
      });
    } else if (s.tool === "find") {
      out.push({
        ...base,
        title: "Matches",
        columns: [
          { key: "name", label: "Name", format: "text" },
          { key: "kind", label: "Type", format: "text" },
        ],
        rows: s.rows.map((r) => ({ name: displayName(str(r.name), str(r.label)), kind: str(r.label) })),
        rowPapers: s.rows.map(() => []),
        rowIds: s.rows.map((r) => str(r.id) || null),
      });
    } else if (s.tool === "community_report") {
      out.push({
        ...base,
        title: "Findings from the community summaries",
        columns: [{ key: "name", label: "Finding", format: "text" }],
        rows: s.rows.filter((r) => r.claim).map((r) => ({ name: cleanCommunityRefs(str(r.claim)) })),
        rowPapers: s.rows.filter((r) => r.claim).map((r) => (Array.isArray(r.paper_ids) ? (r.paper_ids as string[]) : [])),
        rowIds: s.rows.filter((r) => r.claim).map(() => null),
      });
    }
  }
  return out;
}

/** "Community N1:87 focuses on …" → "A co-authorship community focuses on …" (no raw ids). */
export function cleanCommunityRefs(text: string): string {
  const word = (net: string) =>
    ({ N1: "a co-authorship community", N2: "an organization collaboration community", research: "a research community", L0: "a research community", L1: "a research community" } as Record<string, string>)[net] ||
    "a research community";
  const head = text.match(/^\*\*(?:Research )?[Cc]ommunity (?:research:)?(N1|N2|L0|L1):\d+(?::\d+)?\*\*:?\s*(?:[Ff]ocuses|[Ff]ocused) on (.*)$/);
  if (head) {
    const w = word(head[1]);
    return `${w.charAt(0).toUpperCase()}${w.slice(1)} focused on ${head[2]}`;
  }
  return text
    .replace(/^(?:Research )?[Cc]ommunity (?:research:)?(?:N1|N2|L0|L1):\d+(?::\d+)?:\s*/, "")
    .replace(/\b(?:[Tt]he |[Aa] )?(?:[Rr]esearch )?[Cc]ommunity (research:)?(N1|N2|L0|L1):\d+(?::\d+)?/g, (_m, _p, net) => word(net))
    .replace(/\b(?:research:)?(?:L0|L1|N1|N2):\d+(?::\d+)?\b/g, "")
    .replace(/^a /, "A ")
    .replace(/^an /, "An ")
    .replace(/\(\s*\)/g, "")
    .replace(/\s{2,}/g, " ");
}

/* ---------------------------------------------------------------------------------------- */
/* Chart choice                                                                              */
/* ---------------------------------------------------------------------------------------- */

export type ChartSpec =
  | { kind: "lines"; caption: string; years: string[]; series: Array<{ name: string; values: number[]; weight: number }>; unit: "pct" | "count" }
  | { kind: "bars"; caption: string; panels: Array<{ title?: string; dotKind?: string; unit: CellFormat; items: Array<{ name: string; value: number; note?: string }> }> }
  | { kind: "dumbbell"; caption: string; before: string; after: string; items: Array<{ name: string; from: number; to: number }> }
  | { kind: "none"; reason: string };

const YEARS = ["2021", "2022", "2023", "2024", "2025"];

export function chooseChart(steps: TraceStep[], tables: StepTable[], idx: Map<string, NamedEntity>): ChartSpec {
  const withRows = steps.filter((s) => s.rows?.length);
  if (!withRows.length) return { kind: "none", reason: "There is no table of numbers behind this answer, so there is nothing to chart." };
  const last = withRows[withRows.length - 1];
  const f = (last.args?.filters || {}) as Record<string, any>;

  if (last.tool === "trend" && last.rows.some((r) => r.share_by_year)) {
    const rows = last.rows.slice(0, 8);
    const series = rows.map((r) => {
      const sh = (r.share_by_year || {}) as Record<string, number>;
      return { name: subjectName(str(r.name), str(r.kind)), values: YEARS.map((y) => (sh[y] || 0) * 100), weight: num(r.cagr_of_share_2021_2025) || num(r.slope_of_share) || 0 };
    });
    return {
      kind: "lines",
      caption: rows.length > 1 ? `Share of all papers each year for the ${rows.length} ${LABEL_PLURAL[str(last.rows[0].kind)] || "subjects"} in the answer.` : `Share of all papers each year.`,
      years: YEARS,
      series,
      unit: "pct",
    };
  }
  if (last.tool === "aggregate" && last.args?.by === "year") {
    const share = last.rows.some((r) => num(r.share) != null);
    const subj = subjectFromFilters(f, idx) || (Array.isArray(last.args?.entity_ids) ? nameOf(idx, last.args!.entity_ids[0], "Subject") : "Subject");
    return {
      kind: "lines",
      caption: share ? `${capital(subj)}: share of all papers each year.` : `${capital(subj)}: papers each year.`,
      years: last.rows.map((r) => str(r.label || r.group_key)),
      series: [{ name: capital(subj), values: last.rows.map((r) => (share ? (num(r.share) || 0) * 100 : num(r.paper_count) || 0)), weight: 1 }],
      unit: share ? "pct" : "count",
    };
  }
  if (last.tool === "aggregate" && (last.args?.metric === "share_growth" || last.args?.by === "organization_year")) {
    const t = tables.find((x) => x.step === last.step);
    if (t) {
      const y = f.after_year || 2022;
      const subj = subjectFromFilters(f, idx) || "the subject";
      const allZero = t.rows.every((r) => !num(r._pre));
      if (allZero) {
        const vals = t.rows.map((r) => num(r.share) || 0);
        return {
          kind: "bars",
          caption: `Share of each organization's papers that are about ${subj}, after ${y}. None of the ${t.rows.length} had such a paper up to ${y}, so the share after ${y} is the whole change: ${(Math.min(...vals) * 100).toFixed(1)}% to ${(Math.max(...vals) * 100).toFixed(1)}%.`,
          panels: [{ unit: "pct", items: t.rows.map((r) => ({ name: str(r.name), value: num(r.share) || 0, note: str(r.post) })) }],
        };
      }
      return {
        kind: "dumbbell",
        caption: `Share of each organization's papers that are about ${subj}, up to ${y} and after.`,
        before: `Up to ${y}`,
        after: `After ${y}`,
        items: t.rows.map((r) => ({ name: str(r.name), from: num(r._pre) || 0, to: num(r.share) || 0 })),
      };
    }
  }
  if (last.tool === "rank") {
    const t = tables.find((x) => x.step === last.step);
    if (t) {
      const lift = t.columns.some((c) => c.key === "lift");
      const scope = last.args?.scope ? nameOf(idx, last.args.scope, "the subject").toLowerCase() : null;
      return {
        kind: "bars",
        caption: lift && scope ? `Specialisation in ${scope}: how many times more of the organization's work is on it than average.` : "Influence score in the network.",
        panels: [{ unit: lift ? "x" : "score", items: t.rows.slice(0, 12).map((r) => ({ name: str(r.name), value: num(lift ? r.lift : r.score) || 0 })) }],
      };
    }
  }
  const nbTables = tables.filter((t) => withRows.find((s) => s.step === t.step && s.tool === "neighbors"));
  if (nbTables.length) {
    const center = nameOf(idx, withRows.find((s) => s.tool === "neighbors")?.args?.node_id, "the subject");
    return {
      kind: "bars",
      caption: nbTables.length > 1 ? `Shared papers with ${center.toLowerCase()}, by ${nbTables.map((t) => t.columns[0].label.toLowerCase()).join(" and by ")}.` : `Shared papers with ${center}.`,
      panels: nbTables.map((t) => ({
        title: nbTables.length > 1 ? `${t.columns[0].label}s` : undefined,
        dotKind: t.columns[0].label,
        unit: "int" as const,
        items: t.rows.slice(0, 10).map((r) => ({ name: str(r.name), value: num(r.shared) || 0 })),
      })),
    };
  }
  if (last.tool === "aggregate") {
    const t = tables.find((x) => x.step === last.step);
    if (t) return { kind: "bars", caption: "Papers per group.", panels: [{ unit: "int", items: t.rows.slice(0, 12).map((r) => ({ name: str(r.name), value: num(r.papers) || 0 })) }] };
  }
  if (last.tool === "community_report" || last.tool === "local_search")
    return { kind: "none", reason: "This answer was written from community summaries and descriptions, not from one table of numbers, so there is no chart. The Papers tab lists the sources." };
  return { kind: "none", reason: "This result has no numbers to chart. The Table tab shows every row." };
}

function capital(s: string) {
  return s ? s[0].toUpperCase() + s.slice(1) : s;
}

/* ---------------------------------------------------------------------------------------- */
/* Graph layout                                                                              */
/* ---------------------------------------------------------------------------------------- */

export interface GNode {
  id: string;
  name: string;
  short: string;
  label: string;
  x: number;
  y: number;
  r: number;
  /** Plan step that brings this node in (0 = the starting point). */
  reveal: number;
  highlight?: boolean;
  value?: string;
  labelPos?: { dx: number; dy: number; anchor: "start" | "middle" | "end"; lines?: string[] };
  strong?: boolean;
  showLabel: boolean;
}
export interface GEdge {
  id: string;
  source: GNode;
  target: GNode;
  weight: number;
  reveal: number;
  accent?: boolean;
  title: string;
}
export interface GraphModel {
  mode: "funnel" | "bowtie" | "fan" | "path" | "layered";
  width: number;
  height: number;
  nodes: GNode[];
  edges: GEdge[];
  caption: string;
  legend: Array<{ kind: string; label: string; ring?: boolean }>;
  steps: number;
}

const MAX_SIDE = 18;

function wrap2(name: string, max = 16): string[] {
  if (name.length <= max) return [name];
  const words = name.split(" ");
  let a = "";
  let i = 0;
  while (i < words.length && (a + " " + words[i]).trim().length <= max) a = (a + " " + words[i++]).trim();
  if (!a) return [name.slice(0, max - 1) + "…"];
  const b = words.slice(i).join(" ");
  return [a, b.length > max + 2 ? b.slice(0, max + 1) + "…" : b];
}

function short(name: string, label: string, max = 34): string {
  const s = label === "Organization" ? shortOrg(name) : name;
  return s.length > max ? `${s.slice(0, max - 1)}…` : s;
}

export function buildGraph(
  steps: TraceStep[],
  linked: LinkedEntity[],
  subgraph: SubgraphData | null | undefined,
  idx: Map<string, NamedEntity>,
): GraphModel | null {
  const nb = steps.filter((s) => s.tool === "neighbors" && s.rows?.length);
  const sg = steps.find((s) => s.tool === "aggregate" && (s.args?.metric === "share_growth" || s.args?.by === "organization_year") && s.rows?.length);
  const pathStep = steps.find((s) => s.tool === "path" && s.rows?.length);
  const rankStep = steps.find((s) => s.tool === "rank" && s.rows?.length && s.args?.scope);

  /* Funnel: collaborators of X, the ones that grew ringed and linked to the subject. */
  if (nb.length && sg) {
    const W = 600;
    const H = 560;
    const centerId = str(nb[0].args?.node_id);
    const subjId = Object.entries((sg.args?.filters || {}) as Record<string, any>).find(([k]) => /_id$/.test(k))?.[1] as string | undefined;
    const growRows = [...sg.rows].sort((a, b) => (num(b.share_delta) || 0) - (num(a.share_delta) || 0)).slice(0, MAX_SIDE);
    const growIds = new Set(growRows.map((r) => str(r.entity_id)));
    const nRows = neighborRows(nb[0], idx);
    const supportOf = new Map(nRows.map((r) => [str(r._id), num(r.support_count) || 1]));
    const restRows = nRows.filter((r) => !growIds.has(str(r._id))).slice(0, 20);
    const center: GNode = { id: centerId, name: nameOf(idx, centerId, "Start"), short: "", label: idx.get(centerId)?.label || "Organization", x: 34, y: H / 2, r: 14, reveal: 0, showLabel: true, strong: true };
    center.short = short(center.name, center.label, 40);
    center.labelPos = { dx: -center.r, dy: -center.r - 10, anchor: "start" };
    const nodes: GNode[] = [center];
    const edges: GEdge[] = [];
    const maxDelta = Math.max(...growRows.map((r) => num(r.share_delta) || 0), 0.0001);
    growRows.forEach((r, i) => {
      const id = str(r.entity_id);
      const name = orgName(str(r.entity_name));
      const d = num(r.share_delta) || 0;
      const n: GNode = {
        id,
        name,
        short: short(name, "Organization", 46),
        label: "Organization",
        x: 432,
        y: growRows.length > 1 ? 28 + (i * (H - 56)) / (growRows.length - 1) : H / 2,
        r: 5 + 5 * Math.sqrt(d / maxDelta),
        reveal: 1,
        highlight: true,
        value: `${d >= 0 ? "+" : "−"}${Math.abs(d * 100).toFixed(1)}`,
        showLabel: true,
      };
      n.labelPos = { dx: -(n.r + 8), dy: 4.5, anchor: "end" };
      nodes.push(n);
      edges.push({ id: `${centerId}-${id}`, source: center, target: n, weight: supportOf.get(id) || 1, reveal: 1, title: `${center.name} and ${name}` });
    });
    restRows.forEach((r, i) => {
      const n: GNode = {
        id: str(r._id),
        name: str(r._name),
        short: short(str(r._name), "Organization"),
        label: "Organization",
        x: 74 + (i % 3) * 16 + ((i * 37) % 9),
        y: 30 + (i * (H - 60)) / Math.max(1, restRows.length - 1),
        r: 3.5,
        reveal: 1,
        showLabel: false,
      };
      nodes.push(n);
      edges.push({ id: `${centerId}-${n.id}`, source: center, target: n, weight: num(r.support_count) || 1, reveal: 1, title: `${center.name} and ${n.name}: ${num(r.support_count) || 0} shared papers` });
    });
    if (subjId) {
      const sname = nameOf(idx, subjId, "Subject");
      const s: GNode = { id: subjId, name: sname, short: sname, label: idx.get(subjId)?.label || kindFromId(subjId) || "Method", x: 572, y: H / 2, r: 14, reveal: 2, showLabel: true, strong: true };
      s.labelPos = { dx: s.r, dy: -s.r - 26, anchor: "end", lines: wrap2(sname, 16) };
      nodes.push(s);
      growRows.forEach((r) => {
        const n = nodes.find((x) => x.id === str(r.entity_id))!;
        edges.push({ id: `${n.id}-${subjId}`, source: n, target: s, weight: num(r.post_gt_2022_subject_papers) || num(r.post_subject_papers) || 1, reveal: 2, accent: true, title: `${n.name}: ${str(r.post_papers)} papers after` });
      });
    }
    const subjWord = subjId ? nameOf(idx, subjId, "the subject").toLowerCase() : "the subject";
    return {
      mode: "funnel",
      width: W,
      height: H,
      nodes,
      edges,
      steps: 2,
      caption: `${center.name} and its strongest collaborators. The ${growRows.length} that grew their share of ${subjWord} papers are ringed and linked to the subject.`,
      legend: [
        { kind: center.label, label: center.label },
        ...(subjId ? [{ kind: idx.get(subjId)?.label || "Method", label: idx.get(subjId)?.label || "Method" }] : []),
        { kind: "ring", label: "Share grew", ring: true },
      ],
    };
  }

  /* Bow tie / fan: one subject in the middle, neighbours by kind on each side. */
  if (nb.length) {
    const centerId = str(nb[0].args?.node_id) || str(nb[0].rows[0]?.center_id);
    const groups = new Map<string, Row[]>();
    nb.forEach((s) => {
      const rows = neighborRows(s, idx);
      for (const r of rows) {
        const lab = str(r.neighbor_label) || idx.get(str(r._id))?.label || ((s.args?.filters || {}) as any).target_labels?.[0] || "Entity";
        if (!groups.has(lab)) groups.set(lab, []);
        const g = groups.get(lab)!;
        if (!g.find((x) => x._id === r._id)) g.push({ ...r, _step: s.step });
      }
    });
    const cols = [...groups.entries()].slice(0, 2).map(([lab, rows]) => [lab, rows.slice(0, MAX_SIDE)] as const);
    const W = 600;
    const maxLen = Math.max(...cols.map(([, r]) => r.length));
    const H = Math.max(360, maxLen * 27 + 40);
    const centerLabel = idx.get(centerId)?.label || kindFromId(centerId) || "Method";
    const two = cols.length === 2;
    const center: GNode = { id: centerId, name: nameOf(idx, centerId, "Subject"), short: "", label: centerLabel, x: two ? W / 2 : 120, y: H / 2, r: 13, reveal: 0, showLabel: true, strong: true };
    center.short = short(center.name, centerLabel, 28);
    center.labelPos = { dx: 0, dy: center.r + 19, anchor: "middle" };
    const nodes: GNode[] = [center];
    const edges: GEdge[] = [];
    const maxW = Math.max(1, ...cols.flatMap(([, r]) => r.map((x) => num(x.support_count) || 1)));
    const stepOrder = nb.map((s) => s.step);
    cols.forEach(([lab, rows], k) => {
      const x = two ? (k ? 392 : 208) : 330;
      rows.forEach((r, i) => {
        const n: GNode = {
          id: str(r._id),
          name: str(r._name),
          short: short(str(r._name), lab, 30),
          label: lab,
          x,
          y: H / 2 + (i - (rows.length - 1) / 2) * 27,
          r: 4.5 + 2.5 * Math.sqrt((num(r.support_count) || 1) / maxW),
          reveal: Math.max(1, stepOrder.indexOf(num(r._step) || nb[0].step) + 1),
          showLabel: true,
        };
        const left = two && k === 0;
        n.labelPos = { dx: left ? -(n.r + 7) : n.r + 7, dy: 4.5, anchor: left ? "end" : "start" };
        nodes.push(n);
        edges.push({ id: `${centerId}-${n.id}`, source: center, target: n, weight: num(r.support_count) || 1, reveal: n.reveal, title: `${center.name} and ${n.name}: ${num(r.support_count) || 0} shared papers` });
      });
    });
    const kinds = cols.map(([lab]) => LABEL_PLURAL[lab] || "entities");
    return {
      mode: two ? "bowtie" : "fan",
      width: W,
      height: H,
      nodes,
      edges,
      steps: nb.length,
      caption: `${center.name} and the ${kinds.join(" and ")} linked to it. Thicker lines mean more shared papers.`,
      legend: [{ kind: centerLabel, label: centerLabel }, ...cols.map(([lab]) => ({ kind: lab, label: lab }))],
    };
  }

  /* Fan for a ranking scoped to a subject: the subject on the left, ranked groups on the right. */
  if (rankStep) {
    const W = 600;
    const rows = rankStep.rows.slice(0, 15);
    const H = Math.max(360, rows.length * 30 + 40);
    const sid = str(rankStep.args?.scope);
    const center: GNode = { id: sid, name: nameOf(idx, sid, "Subject"), short: "", label: idx.get(sid)?.label || kindFromId(sid) || "Topic", x: 90, y: H / 2, r: 13, reveal: 0, showLabel: true, strong: true };
    center.short = short(center.name, center.label, 22);
    center.labelPos = { dx: 0, dy: center.r + 19, anchor: "middle" };
    const nodes: GNode[] = [center];
    const edges: GEdge[] = [];
    const max = Math.max(...rows.map((r) => num(r.lift) || num(r.score) || 0), 0.0001);
    rows.forEach((r, i) => {
      const v = num(r.lift) ?? num(r.score) ?? 0;
      const name = displayName(str(r.name), str(r.label) || "Organization");
      const n: GNode = {
        id: str(r.id),
        name,
        short: short(name, "Organization", 42),
        label: str(r.label) || "Organization",
        x: 300,
        y: H / 2 + (i - (rows.length - 1) / 2) * 30,
        r: 4 + 6 * Math.sqrt(v / max),
        reveal: 1,
        value: num(r.lift) != null ? `${v.toFixed(1)}×` : undefined,
        showLabel: true,
      };
      n.labelPos = { dx: n.r + 8, dy: 4.5, anchor: "start" };
      nodes.push(n);
      edges.push({ id: `${sid}-${n.id}`, source: center, target: n, weight: num(r.subject_papers) || 1, reveal: 1, title: `${name}: ${num(r.subject_papers) ?? "?"} papers on the subject` });
    });
    return {
      mode: "fan",
      width: W,
      height: H,
      nodes,
      edges,
      steps: 1,
      caption: `${center.name} and the groups most concentrated on it. Bigger dots mean stronger specialisation.`,
      legend: [{ kind: center.label, label: center.label }, { kind: "Organization", label: "Organization" }],
    };
  }

  /* Path: a straight chain. */
  if (pathStep) {
    const ids: string[] = [];
    pathStep.rows.forEach((r) => {
      if (!ids.includes(str(r.source))) ids.push(str(r.source));
      if (!ids.includes(str(r.target))) ids.push(str(r.target));
    });
    const W = 600;
    const H = Math.max(200, ids.length * 70);
    const nodes: GNode[] = ids.map((id, i) => {
      const name = nameOf(idx, id, "Unnamed");
      const lab = idx.get(id)?.label || kindFromId(id) || "Entity";
      const n: GNode = { id, name, short: short(name, lab, 40), label: lab, x: 200, y: 40 + i * ((H - 80) / Math.max(1, ids.length - 1)), r: i === 0 || i === ids.length - 1 ? 12 : 8, reveal: i === 0 ? 0 : 1, showLabel: true, strong: i === 0 || i === ids.length - 1 };
      n.labelPos = { dx: n.r + 10, dy: 5, anchor: "start" };
      return n;
    });
    const byId = new Map(nodes.map((n) => [n.id, n]));
    const edges: GEdge[] = pathStep.rows.map((r, i) => ({
      id: `p${i}`,
      source: byId.get(str(r.source))!,
      target: byId.get(str(r.target))!,
      weight: num(r.support_count) || 1,
      reveal: 1,
      title: `${nameOf(idx, r.source)} ${RELATION_WORD[str(r.relation)] || "is linked to"} ${nameOf(idx, r.target)}`,
    }));
    return { mode: "path", width: W, height: H, nodes, edges, steps: 1, caption: `The shortest connection found, link by link.`, legend: [...new Set(nodes.map((n) => n.label))].map((k) => ({ kind: k, label: k })) };
  }

  /* Layered: whatever subgraph came back, by hop. */
  if (subgraph?.nodes?.length) {
    const sgNodes = subgraph.nodes.filter((n) => !String(n.id).startsWith("paper:")).slice(0, 24);
    const papers = subgraph.nodes.filter((n) => String(n.id).startsWith("paper:")).slice(0, 8);
    const all = [...sgNodes, ...papers];
    if (all.length < 2) return null;
    const linkedIds = new Set(linked.map((l) => l.id).filter(Boolean) as string[]);
    const layer = (n: (typeof all)[number]) => (linkedIds.has(n.id) ? 0 : String(n.id).startsWith("paper:") ? 2 : 1);
    const cols = [0, 1, 2].map((h) => all.filter((n) => layer(n) === h));
    const W = 600;
    const H = Math.max(320, Math.max(...cols.map((c) => c.length)) * 28 + 40);
    const xs = [70, 300, 470];
    const nodes: GNode[] = [];
    cols.forEach((col, h) =>
      col.forEach((n, i) => {
        const lab = n.label || kindFromId(n.id) || "Entity";
        const name = displayName(n.name || nameOf(idx, n.id, "Unnamed"), lab);
        const g: GNode = { id: n.id, name, short: short(name, lab, h === 2 ? 26 : 30), label: lab, x: xs[h], y: H / 2 + (i - (col.length - 1) / 2) * 28, r: h === 0 ? 11 : 5.5, reveal: h === 0 ? 0 : 1, showLabel: true, strong: h === 0 };
        g.labelPos = h === 0 ? { dx: 0, dy: g.r + 18, anchor: "middle" } : { dx: g.r + 7, dy: 4.5, anchor: "start" };
        nodes.push(g);
      }),
    );
    const byId = new Map(nodes.map((n) => [n.id, n]));
    const edges: GEdge[] = subgraph.edges
      .filter((e) => byId.has(e.source) && byId.has(e.target))
      .slice(0, 60)
      .map((e, i) => ({ id: `e${i}`, source: byId.get(e.source)!, target: byId.get(e.target)!, weight: e.support_count || 1, reveal: 1, title: `${byId.get(e.source)!.name} ${RELATION_WORD[e.relation || ""] || "is linked to"} ${byId.get(e.target)!.name}` }));
    return { mode: "layered", width: W, height: H, nodes, edges, steps: 1, caption: "The part of the graph the answer was read from.", legend: [...new Set(nodes.map((n) => n.label))].map((k) => ({ kind: k, label: k })) };
  }
  return null;
}

/* ---------------------------------------------------------------------------------------- */
/* Footnotes                                                                                 */
/* ---------------------------------------------------------------------------------------- */

export interface Footnote {
  n: number;
  kind: "step" | "row" | "paper";
  label: string;
  step?: number;
  papers: string[];
}
export type Seg = string | { fn: number } | { strong: string };
export interface Block {
  type: "p" | "li";
  segs: Seg[];
}

const REF_RE = /(\s?\[steps?\s+[0-9,\sand&–-]+\]|\s?\[paper:[^\]]+\])/g;

/**
 * Split the answer into paragraphs and list items, and turn `[step N]` and `[paper:…]`
 * references into numbered footnotes. List items whose name matches a result row get a
 * footnote with that row's papers.
 */
export function footnoteAnswer(
  answer: string,
  plainSteps: Array<{ stepNumber?: number; title: string }>,
  tables: StepTable[],
  resultPapers: Array<{ step: number; paper_ids: string[] }>,
): { blocks: Block[]; footnotes: Footnote[] } {
  const footnotes: Footnote[] = [];
  const stepFn = new Map<number, number>();
  const paperFn = new Map<string, number>();
  const rowFn = new Map<string, number>();
  const rowPapers = new Map<string, string[]>();
  for (const t of tables)
    t.rows.forEach((r, i) => {
      const nm = str(r.name).toLowerCase();
      if (nm && t.rowPapers[i]?.length && !rowPapers.has(nm)) rowPapers.set(nm, t.rowPapers[i]);
    });

  const addStep = (n: number) => {
    if (stepFn.has(n)) return stepFn.get(n)!;
    const ps = plainSteps.find((p) => p.stepNumber === n);
    const fn = footnotes.length + 1;
    footnotes.push({ n: fn, kind: "step", step: n, label: `Step ${n}: ${ps ? ps.title.charAt(0).toLowerCase() + ps.title.slice(1) : "a step of the plan"}`, papers: resultPapers.find((r) => r.step === n)?.paper_ids?.slice(0, 3) || [] });
    stepFn.set(n, fn);
    return fn;
  };
  const addPaper = (pid: string) => {
    if (paperFn.has(pid)) return paperFn.get(pid)!;
    const fn = footnotes.length + 1;
    footnotes.push({ n: fn, kind: "paper", label: "Paper", papers: [pid] });
    paperFn.set(pid, fn);
    return fn;
  };
  const addRow = (name: string) => {
    const key = name.toLowerCase();
    if (rowFn.has(key)) return rowFn.get(key)!;
    const fn = footnotes.length + 1;
    footnotes.push({ n: fn, kind: "row", label: name, papers: rowPapers.get(key)!.slice(0, 3) });
    rowFn.set(key, fn);
    return fn;
  };

  const blocks: Block[] = [];
  const lines = answer.replace(/\r/g, "").split("\n");
  for (const raw of lines) {
    const line = raw.trim();
    if (!line) continue;
    const li = line.match(/^(?:[-*•]|\d+[.)])\s+(.*)$/);
    let text = (li ? li[1] : line).replace(/^Name:\s*/, "");
    text = cleanCommunityRefs(text);
    const segs: Seg[] = [];
    const parts = text.split(REF_RE);
    for (const part of parts) {
      if (!part) continue;
      const stepM = part.match(/\[steps?\s+([0-9,\sand&–-]+)\]/);
      const paperM = part.match(/\[(paper:[^\]]+)\]/);
      if (stepM) {
        for (const nStr of stepM[1].match(/\d+/g) || []) segs.push({ fn: addStep(Number(nStr)) });
      } else if (paperM) {
        for (const pid of paperM[1].split(/\s*[,;]\s*/)) if (pid.startsWith("paper:")) segs.push({ fn: addPaper(pid) });
      } else {
        // **bold** → strong; keep the rest as text
        part.split(/(\*\*[^*]+\*\*)/g).forEach((p) => {
          if (!p) return;
          if (p.startsWith("**") && p.endsWith("**")) segs.push({ strong: p.slice(2, -2) });
          else segs.push(p);
        });
      }
    }
    if (li) {
      const head = text.split(":")[0].replace(/\*\*/g, "").trim();
      if (head && rowPapers.has(head.toLowerCase()) && !segs.some((s) => typeof s === "object" && "fn" in s)) segs.push({ fn: addRow(head) });
    }
    blocks.push({ type: li ? "li" : "p", segs });
  }
  return { blocks, footnotes };
}

/* ---------------------------------------------------------------------------------------- */
/* Follow-up questions                                                                       */
/* ---------------------------------------------------------------------------------------- */

export function followUps(question: string, linked: LinkedEntity[], steps: TraceStep[]): string[] {
  const q = question.toLowerCase();
  const out: string[] = [];
  const add = (s: string) => {
    if (!out.includes(s) && s.toLowerCase() !== q) out.push(s);
  };
  const subj = linked.find((l) => l.id && ["Method", "Task", "Dataset", "Topic"].includes(l.entity_type || ""));
  const org = linked.find((l) => l.id && l.entity_type === "Organization");
  if (subj) {
    const nm = displayName(subj.name || subj.text || "", subj.entity_type).toLowerCase();
    const verb = subj.entity_type === "Task" ? "address" : subj.entity_type === "Dataset" ? "use" : subj.entity_type === "Topic" ? "are about" : "use";
    if (!/speciali[sz]e/.test(q)) add(`Which organizations specialize most in ${nm} by lift?`);
    if (!/five organizations authored/.test(q)) add(`Which five organizations authored the most papers that ${verb} ${nm}?`);
    if (subj.entity_type === "Method" && !/datasets/.test(q)) add(`Which datasets are used in papers that apply ${nm}?`);
    if (subj.entity_type === "Task" && !/methods/.test(q)) add(`Which methods are applied to ${nm}?`);
  }
  if (org) {
    const nm = displayName(org.name || org.text || "", "Organization");
    add(`Which five organizations does ${nm} collaborate with most often, by number of joint papers?`);
  }
  if (steps.some((s) => s.tool === "trend")) {
    add("Which methods are declining as a share of papers from 2021 to 2025?");
    add("Which tasks grew fastest as a share of papers from 2021 to 2025?");
  }
  if (!out.length) {
    add("Which methods grew fastest as a share of AAAI and IJCAI papers from 2021 to 2025?");
    add("What are the main research communities in the enriched AAAI and IJCAI 2021-2025 knowledge graph?");
  }
  return out.slice(0, 3);
}
