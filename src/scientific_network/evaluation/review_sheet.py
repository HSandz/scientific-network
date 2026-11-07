"""Reviewer context columns and a self-contained HTML sheet for the edge audit (D040, plan section 5).

``SheetContext`` turns each sampled edge into plain strings and links that a reviewer
needs to judge it. It reads these optional graph properties and leaves anything absent
blank, so the same code serves synthetic fixtures and the release graph:

* Paper node: ``official_url``, ``pdf_url``, ``doi``, ``openalex_id``, ``year``.
* Researcher node: ``orcid``, ``openalex_id`` (or an ``researcher:openalex:A...`` ID).
* Organization node: ``ror``, ``openalex_id`` (or an ``organization:I...`` ID).
* Topic node: ``definition``.
* AUTHORED edge: ``byline_position``, ``roster_name``.
* AFFILIATED_WITH edge: ``raw_affiliation_strings``.
* Evidence: ``excerpt`` and, for derived edges, ``support_paper_ids``.

The HTML sheet is one static file with no external resources. A reviewer picks their
letter, records a decision per assigned edge, and exports a CSV in the exact format
``score-edge-audit`` reads. Answers are kept in the browser's local storage.
"""

from collections import defaultdict
import html
import json
import re

from scientific_network.contracts import Edge, GraphArtifact, Relation as R

ERROR_CATEGORIES = (
    "wrong_identity", "wrong_affiliation", "wrong_citation", "wrong_topic", "unverifiable", "other",
)

CORRECT_WHEN = {
    R.AUTHORED: "The person is on the official byline at that position, and the OpenAlex author page shows no obvious merge of different people.",
    R.AFFILIATED_WITH: "The paper's PDF lists that author at that organization.",
    R.PUBLISHED_IN: "The official page lists the paper in that venue and year.",
    R.CITES: "The citing paper's reference list contains the cited paper.",
    R.HAS_TOPIC: "The topic is a substantive topic of the paper.",
    R.SUBTOPIC_OF: "The hierarchy matches the taxonomy.",
    R.COAUTHORED_WITH: "Both people are on that paper's byline.",
    R.COLLABORATED_WITH: "Two distinct authors are at the two organizations on that paper.",
    R.RESEARCHES_TOPIC: "The person authored both papers and both papers have the topic.",
    R.CONTRIBUTES_TO_TOPIC: "Each paper has the topic and an author affiliated with the organization.",
}
# How many supporting papers to show for derived edges (plan section 5).
SUPPORT_SHOWN = {R.COAUTHORED_WITH: 1, R.COLLABORATED_WITH: 1, R.RESEARCHES_TOPIC: 2, R.CONTRIBUTES_TO_TOPIC: 3}

CONTEXT_FIELDS = [
    "relation", "is_overlap", "source_id", "source_name", "target_id", "target_name",
    "official_page_url", "pdf_url", "doi_url", "openalex_work_url", "openalex_entity_url",
    "also_show", "correct_when",
]

_OPENALEX_ID = re.compile(r"^[AIWSCPF]\d+$", re.IGNORECASE)


def _web_url(value) -> str:
    text = str(value or "").strip()
    return text if text.startswith(("https://", "http://")) else ""


def _doi_url(value) -> str:
    text = str(value or "").strip()
    for prefix in ("https://doi.org/", "http://doi.org/", "https://dx.doi.org/", "doi:"):
        if text.lower().startswith(prefix):
            text = text[len(prefix):]
    return f"https://doi.org/{text}" if text else ""


def _openalex_url(*candidates) -> str:
    for candidate in candidates:
        segment = re.split(r"[:/]", str(candidate or "").strip())[-1]
        if _OPENALEX_ID.match(segment):
            return f"https://openalex.org/{segment[0].upper()}{segment[1:]}"
    return ""


def _as_list(value) -> list[str]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            return [value] if value else []
    return [str(item) for item in value] if isinstance(value, list) else []


def _join(parts) -> str:
    return "; ".join(part for part in parts if part)


def _clip(text: str, limit: int = 700) -> str:
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


class SheetContext:
    def __init__(self, graph: GraphArtifact):
        self.nodes = {node.id: node for node in graph.nodes}
        self.evidence = {item.id: item for item in graph.evidence}
        self.edges = {(e.relation, e.source_id, e.target_id): e for e in graph.edges}
        self.pair_papers: dict[tuple[str, str], set[str]] = defaultdict(set)
        self.paper_observations = defaultdict(list)
        for observation in graph.affiliation_observations:
            self.pair_papers[(observation.researcher_id, observation.organization_id)].add(observation.paper_id)
            self.paper_observations[observation.paper_id].append(observation)

    def _name(self, identifier: str) -> str:
        node = self.nodes.get(identifier)
        return node.name if node else identifier

    def _prop(self, identifier: str, key: str):
        node = self.nodes.get(identifier)
        return node.properties.get(key) if node else None

    def _support_papers(self, edge: Edge) -> list[str]:
        papers = {p for ref in edge.evidence_ids if ref in self.evidence for p in self.evidence[ref].support_paper_ids}
        return sorted(papers)

    def papers_for(self, edge: Edge) -> list[str]:
        relation = edge.relation
        if relation == R.AUTHORED:
            return [edge.target_id]
        if relation in (R.PUBLISHED_IN, R.CITES, R.HAS_TOPIC):
            return [edge.source_id]
        if relation == R.AFFILIATED_WITH:
            return sorted(self.pair_papers.get((edge.source_id, edge.target_id), set()))[:3]
        if relation in SUPPORT_SHOWN:
            return self._support_papers(edge)[: SUPPORT_SHOWN[relation]]
        return []

    def paper_links(self, paper_id: str) -> list[tuple[str, str]]:
        links = [
            ("Official page", _web_url(self._prop(paper_id, "official_url"))),
            ("PDF", _web_url(self._prop(paper_id, "pdf_url"))),
            ("DOI", _doi_url(self._prop(paper_id, "doi"))),
            ("OpenAlex work", _openalex_url(self._prop(paper_id, "openalex_id"))),
        ]
        return [(label, url) for label, url in links if url]

    def entity_links(self, edge: Edge) -> list[tuple[str, str]]:
        ids = {
            R.AUTHORED: [edge.source_id], R.AFFILIATED_WITH: [edge.source_id, edge.target_id],
            R.COAUTHORED_WITH: [edge.source_id, edge.target_id], R.COLLABORATED_WITH: [edge.source_id, edge.target_id],
            R.RESEARCHES_TOPIC: [edge.source_id], R.CONTRIBUTES_TO_TOPIC: [edge.source_id],
        }.get(edge.relation, [])
        links = []
        for identifier in ids:
            node = self.nodes.get(identifier)
            if node is None:
                continue
            url = _openalex_url(node.properties.get("openalex_id"), identifier)
            if url:
                links.append((f"OpenAlex: {node.name}", url))
        return links

    def _title(self, paper_id: str) -> str:
        year = self._prop(paper_id, "year")
        return f"{self._name(paper_id)} ({year})" if year else self._name(paper_id)

    def _excerpt(self, edge: Edge) -> str:
        for ref in edge.evidence_ids:
            item = self.evidence.get(ref)
            if item is not None and item.excerpt:
                return item.excerpt
        return ""

    def _raw_affiliations(self, researcher_id: str, organization_id: str) -> list[str]:
        edge = self.edges.get((R.AFFILIATED_WITH, researcher_id, organization_id))
        return _as_list(edge.properties.get("raw_affiliation_strings")) if edge else []

    def also_show(self, edge: Edge, papers: list[str]) -> str:
        r, props = edge.relation, edge.properties
        source, target = self._name(edge.source_id), self._name(edge.target_id)
        if r == R.AUTHORED:
            position = props.get("byline_position")
            return _join([
                f"byline position {position}" if position else "", f"roster name: {props['roster_name']}" if props.get("roster_name") else "",
                f"OpenAlex name: {source}", f"ORCID: {self._prop(edge.source_id, 'orcid')}" if self._prop(edge.source_id, "orcid") else "",
                f"paper: {self._title(edge.target_id)}",
            ])
        if r == R.AFFILIATED_WITH:
            raw = " | ".join(self._raw_affiliations(edge.source_id, edge.target_id))
            return _join([
                f"supporting papers: {len(self.pair_papers.get((edge.source_id, edge.target_id), ()))}",
                f"raw affiliation: {raw}" if raw else "", f"organization: {target}",
                "papers shown: " + " | ".join(self._title(p) for p in papers) if papers else "",
            ])
        if r == R.PUBLISHED_IN:
            return _join([f"paper: {self._title(edge.source_id)}", f"venue: {target}"])
        if r == R.CITES:
            return _join([f"citing paper: {self._title(edge.source_id)}", f"cited paper: {self._title(edge.target_id)}"])
        if r == R.HAS_TOPIC:
            definition = self._prop(edge.target_id, "definition")
            return _join([
                f"title: {source}", f"excerpt: {self._excerpt(edge)}" if self._excerpt(edge) else "",
                f"topic: {target}", f"definition: {definition}" if definition else "",
            ])
        if r == R.SUBTOPIC_OF:
            return _join([f"leaf topic: {source}", f"parent topic: {target}"])
        if r == R.COAUTHORED_WITH:
            return _join([f"people: {source} and {target}", "supporting paper: " + " | ".join(self._title(p) for p in papers)])
        if r == R.COLLABORATED_WITH:
            people = []
            for paper in papers:
                for obs in self.paper_observations.get(paper, []):
                    if obs.organization_id in (edge.source_id, edge.target_id):
                        raw = " / ".join(self._raw_affiliations(obs.researcher_id, obs.organization_id))
                        people.append(f"{self._name(obs.researcher_id)} at {self._name(obs.organization_id)}" + (f" (raw: {raw})" if raw else ""))
            return _join([f"organizations: {source} and {target}", "supporting paper: " + " | ".join(self._title(p) for p in papers),
                          "authors: " + " | ".join(people) if people else ""])
        topic_papers = " | ".join(self._title(p) for p in papers)
        kind = "person" if r == R.RESEARCHES_TOPIC else "organization"
        return _join([f"{kind}: {source}", f"topic: {target}", f"supporting papers: {topic_papers}" if topic_papers else ""])

    def describe(self, edge: Edge) -> tuple[dict, list[dict]]:
        """Return the flat CSV context columns and the full link list for one edge."""
        papers = self.papers_for(edge)
        first_links = dict(self.paper_links(papers[0])) if papers else {}
        entity = self.entity_links(edge)
        fields = {
            "relation": edge.relation.value,
            "source_id": edge.source_id, "source_name": self._name(edge.source_id),
            "target_id": edge.target_id, "target_name": self._name(edge.target_id),
            "official_page_url": first_links.get("Official page", ""), "pdf_url": first_links.get("PDF", ""),
            "doi_url": first_links.get("DOI", ""), "openalex_work_url": first_links.get("OpenAlex work", ""),
            "openalex_entity_url": " ".join(url for _, url in entity),
            "also_show": _clip(self.also_show(edge, papers)),
            "correct_when": CORRECT_WHEN[edge.relation],
        }
        links = []
        for index, paper in enumerate(papers):
            suffix = f" (paper {index + 1})" if len(papers) > 1 else ""
            links.extend({"label": label + suffix, "url": url} for label, url in self.paper_links(paper))
        links.extend({"label": label, "url": url} for label, url in entity)
        return fields, links


# --- HTML sheet ---------------------------------------------------------------------------------

_LOGIC_JS = r"""
function csvCell(value) {
  const text = value === null || value === undefined ? '' : String(value);
  return /[",\r\n]/.test(text) ? '"' + text.replace(/"/g, '""') + '"' : text;
}
function isoLocal(date) {
  const pad = (n) => String(n).padStart(2, '0');
  const offset = -date.getTimezoneOffset();
  const sign = offset >= 0 ? '+' : '-';
  const abs = Math.abs(offset);
  return date.getFullYear() + '-' + pad(date.getMonth() + 1) + '-' + pad(date.getDate()) + 'T' +
    pad(date.getHours()) + ':' + pad(date.getMinutes()) + ':' + pad(date.getSeconds()) +
    sign + pad(Math.floor(abs / 60)) + ':' + pad(abs % 60);
}
function answerKey(reviewer, edgeId) { return reviewer + '|' + edgeId; }
function answerComplete(answer) {
  if (!answer || !answer.decision) return false;
  if (answer.decision === 'correct') return true;
  return Boolean(answer.category && answer.reason && answer.reason.trim());
}
function buildCsv(fields, rows, answers, reviewer) {
  const lines = [fields.map(csvCell).join(',')];
  let exported = 0;
  for (const row of rows) {
    if (row.review.reviewer_id !== reviewer) continue;
    const answer = answers[answerKey(reviewer, row.review.edge_id)];
    if (!answerComplete(answer)) continue;
    const correct = answer.decision === 'correct';
    const record = Object.assign({}, row.review, {
      reviewer_id: reviewer, decision: answer.decision,
      error_category: correct ? '' : answer.category, reason: correct ? '' : answer.reason.trim(),
      reviewed_at: answer.at,
    });
    lines.push(fields.map((field) => csvCell(record[field])).join(','));
    exported += 1;
  }
  return { csv: lines.join('\r\n') + '\r\n', exported: exported };
}
"""

_APP_JS = r"""
(function () {
  const DATA = JSON.parse(document.getElementById('sheet-data').textContent);
  const STORE = 'edge-audit-answers:' + DATA.meta.audit_id;
  let answers = {};
  let storageOk = true;
  try { answers = JSON.parse(localStorage.getItem(STORE) || '{}') || {}; } catch (e) { storageOk = false; answers = {}; }
  function save() { try { localStorage.setItem(STORE, JSON.stringify(answers)); } catch (e) { storageOk = false; } }
  const $ = (id) => document.getElementById(id);
  const reviewerSelect = $('reviewer'), filterSelect = $('filter'), list = $('list'), progress = $('progress');

  function el(tag, attrs, children) {
    const node = document.createElement(tag);
    for (const [key, value] of Object.entries(attrs || {})) {
      if (key === 'text') node.textContent = value; else if (key === 'class') node.className = value; else node.setAttribute(key, value);
    }
    for (const child of children || []) node.appendChild(child);
    return node;
  }
  function mine() { return DATA.rows.filter((row) => row.review.reviewer_id === reviewerSelect.value); }
  function updateProgress() {
    const rows = mine();
    const done = rows.filter((row) => answerComplete(answers[answerKey(reviewerSelect.value, row.review.edge_id)])).length;
    progress.textContent = reviewerSelect.value ? done + ' of ' + rows.length + ' complete' + (storageOk ? '' : ' (browser storage unavailable: export often)') : '';
  }
  function card(row, index) {
    const reviewer = reviewerSelect.value, id = row.review.edge_id, key = answerKey(reviewer, id);
    const entry = answers[key] || {};
    const c = row.context;
    const links = el('p', { class: 'links' }, row.links.map((link) => {
      const a = el('a', { text: link.label, target: '_blank', rel: 'noopener noreferrer' });
      if (/^https?:\/\//.test(link.url)) a.setAttribute('href', link.url);
      return a;
    }));
    const category = el('select', { 'aria-label': 'Error category' }, [el('option', { value: '', text: 'error category…' })]
      .concat(DATA.meta.error_categories.map((name) => el('option', { value: name, text: name.replace(/_/g, ' ') }))));
    const reason = el('textarea', { rows: '2', placeholder: 'What is wrong, or what could not be verified (required)', 'aria-label': 'Reason' });
    const issue = el('div', { class: 'issue' }, [category, reason]);
    category.value = entry.category || ''; reason.value = entry.reason || '';
    function sync() {
      issue.hidden = !entry.decision || entry.decision === 'correct';
      card_.classList.toggle('done', answerComplete(entry));
      updateProgress();
    }
    function commit() { entry.at = isoLocal(new Date()); answers[key] = entry; save(); sync(); }
    const radios = ['correct', 'incorrect', 'unverifiable'].map((value) => {
      const input = el('input', { type: 'radio', name: 'decision-' + index, value: value });
      input.checked = entry.decision === value;
      input.addEventListener('change', () => { entry.decision = value; commit(); });
      return el('label', { class: 'choice ' + value }, [input, document.createTextNode(' ' + value)]);
    });
    category.addEventListener('change', () => { entry.category = category.value; commit(); });
    reason.addEventListener('input', () => { entry.reason = reason.value; commit(); });
    const badges = [el('span', { class: 'badge', text: c.relation })];
    if (c.is_overlap === 'true') badges.push(el('span', { class: 'badge overlap', text: 'also reviewed by the other reviewer: decide independently' }));
    const card_ = el('article', { class: 'card' }, [
      el('header', {}, [el('span', { class: 'num', text: '#' + (index + 1) })].concat(badges)),
      el('h2', { text: c.source_name + '  →  ' + c.target_name }),
      links,
      el('p', { class: 'also', text: c.also_show }),
      el('p', { class: 'when' }, [el('strong', { text: 'Correct when: ' }), document.createTextNode(c.correct_when)]),
      el('div', { class: 'decide' }, radios),
      issue,
      el('p', { class: 'id', text: id }),
    ]);
    sync();
    return card_;
  }
  function render() {
    list.textContent = '';
    if (!reviewerSelect.value) { list.appendChild(el('p', { class: 'empty', text: 'Choose your reviewer letter to begin.' })); updateProgress(); return; }
    const rows = mine();
    rows.forEach((row, index) => {
      const complete = answerComplete(answers[answerKey(reviewerSelect.value, row.review.edge_id)]);
      if (filterSelect.value === 'open' && complete) return;
      list.appendChild(card(row, index));
    });
    updateProgress();
  }
  DATA.meta.reviewer_ids.forEach((letter) => reviewerSelect.appendChild(el('option', { value: letter, text: letter })));
  try { reviewerSelect.value = localStorage.getItem(STORE + ':reviewer') || ''; } catch (e) { /* ignore */ }
  const fromHash = /reviewer=([^&]+)/.exec(location.hash || '');
  if (fromHash && DATA.meta.reviewer_ids.indexOf(decodeURIComponent(fromHash[1])) >= 0) reviewerSelect.value = decodeURIComponent(fromHash[1]);
  reviewerSelect.addEventListener('change', () => { try { localStorage.setItem(STORE + ':reviewer', reviewerSelect.value); } catch (e) { /* ignore */ } render(); });
  filterSelect.addEventListener('change', render);
  $('export').addEventListener('click', () => {
    const reviewer = reviewerSelect.value;
    if (!reviewer) { alert('Choose your reviewer letter first.'); return; }
    const built = buildCsv(DATA.fields, DATA.rows, answers, reviewer);
    const total = mine().length;
    if (built.exported < total && !confirm(built.exported + ' of ' + total + ' edges are complete. Export only the completed ones?')) return;
    const blob = new Blob([built.csv], { type: 'text/csv;charset=utf-8' });
    const link = el('a', { href: URL.createObjectURL(blob), download: 'edge-review-' + reviewer + '.csv' });
    document.body.appendChild(link); link.click(); link.remove();
  });
  render();
})();
"""

_CSS = """
:root{--bg:#fafaf7;--fg:#1d2327;--muted:#5d6670;--card:#fff;--line:#d9dde1;--accent:#1b5fa8;--ok:#1d7a46;--bad:#a3262a;--warn:#8a5a00}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#15181b;--fg:#e6e8ea;--muted:#9aa4ad;--card:#1d2226;--line:#333b42;--accent:#6aa9ec;--ok:#53c184;--bad:#ef7a7e;--warn:#e0b04f}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
.top{position:sticky;top:0;z-index:2;background:var(--bg);border-bottom:1px solid var(--line);padding:12px 16px}
.top h1{margin:0 0 4px;font-size:18px}.meta{margin:0 0 8px;color:var(--muted);font-size:13px;overflow-wrap:anywhere}
.bar{display:flex;flex-wrap:wrap;gap:12px;align-items:center}.bar select,.bar button{font:inherit;padding:6px 10px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--fg)}
.bar button{background:var(--accent);color:#fff;border-color:var(--accent);cursor:pointer}#progress{color:var(--muted)}
main{max-width:860px;margin:0 auto;padding:16px}.empty{color:var(--muted)}
.card{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--line);border-radius:8px;padding:12px 14px;margin:0 0 14px}
.card.done{border-left-color:var(--ok)}.card header{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.num{color:var(--muted);font-variant-numeric:tabular-nums}.badge{font-size:12px;padding:1px 8px;border-radius:99px;border:1px solid var(--line)}
.badge.overlap{border-color:var(--warn);color:var(--warn)}.card h2{margin:8px 0 6px;font-size:16px;overflow-wrap:anywhere}
.links{display:flex;flex-wrap:wrap;gap:6px 14px;margin:6px 0}.links a{color:var(--accent)}.also,.when{margin:6px 0;overflow-wrap:anywhere}.when{color:var(--muted)}
.decide{display:flex;flex-wrap:wrap;gap:8px 18px;margin:10px 0 4px}.choice{cursor:pointer}.choice.correct{color:var(--ok)}.choice.incorrect{color:var(--bad)}.choice.unverifiable{color:var(--warn)}
.issue{display:flex;flex-direction:column;gap:6px;margin:6px 0}.issue[hidden]{display:none}.issue select,.issue textarea{font:inherit;padding:6px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg);width:100%}
.id{margin:6px 0 0;font:11px ui-monospace,monospace;color:var(--muted);overflow-wrap:anywhere}
"""


def render_html(meta: dict, fields: list[str], rows: list[dict]) -> str:
    """``rows`` are ``{"review": <full CSV row>, "context": <context fields>, "links": [...]}``."""
    payload = {"meta": {**meta, "error_categories": list(ERROR_CATEGORIES)}, "fields": fields, "rows": rows}
    data = json.dumps(payload, ensure_ascii=True, separators=(",", ":")).replace("<", "\\u003c")
    note = (
        "Decide each edge from the linked sources, not from the system's output. Unverifiable counts as incorrect. "
        "Answers are saved in this browser; use Export to download your CSV and send it back."
    )
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        "<title>Edge audit review sheet</title><style>" + _CSS + "</style></head><body>"
        '<div class="top"><h1>Edge audit review sheet</h1>'
        f'<p class="meta">graph {html.escape(meta["graph_version"])} · audit {html.escape(meta["audit_id"])} · {note}</p>'
        '<div class="bar"><label>Reviewer <select id="reviewer"><option value="">choose…</option></select></label>'
        '<label>Show <select id="filter"><option value="all">all edges</option><option value="open">not yet complete</option></select></label>'
        '<span id="progress"></span><button id="export" type="button">Export my reviews (CSV)</button></div></div>'
        '<main id="list"></main>'
        '<script id="sheet-data" type="application/json">' + data + "</script>"
        '<script id="logic">' + _LOGIC_JS + "</script>"
        '<script id="app">' + _APP_JS + "</script></body></html>"
    )
