"""Source acquisition for enrichment (specification §4.1, E1).

Every fetched document is stored once, immutable, content-addressed under
``data/raw/enrichment-v1/`` (ignored by git) and registered in a manifest row with URL,
request parameters, retrieval time, revision ID where the source has one, and SHA-256.
Requests are rate-limited and sent with a generic User-Agent (no personal contact data).
"""

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import re
import time

import httpx

USER_AGENT = "scientific-network-coursework/0.1 (academic research project; Wikimedia API etiquette followed)"
WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"
WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
_ROR = re.compile(r"([0-9a-z]{9})$")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass
class RawStore:
    """Content-addressed store plus an append-only manifest of fetches."""

    root: Path
    manifest: Path
    _known: dict[str, dict] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.manifest.parent.mkdir(parents=True, exist_ok=True)
        if self.manifest.exists():
            with self.manifest.open(encoding="utf-8") as handle:  # iterate by "\n" only; splitlines() also splits on U+2028
                for line in handle:
                    if line.strip():
                        row = json.loads(line)
                        self._known[row["request_key"]] = row

    def lookup(self, request_key: str) -> dict | None:
        return self._known.get(request_key)

    def read(self, row: dict) -> bytes:
        return (self.root / row["sha256"][:2] / f"{row['sha256']}.json").read_bytes()

    def put(self, request_key: str, url: str, params: dict, body: bytes, *, source: str,
            revision: dict | None = None) -> dict:
        digest = sha256_bytes(body)
        path = self.root / digest[:2] / f"{digest}.json"
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
        row = {"request_key": request_key, "source": source, "url": url, "params": params,
               "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "sha256": digest, "bytes": len(body),
               "revisions": revision or {}}
        with self.manifest.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
        self._known[request_key] = row
        return row


class Fetcher:
    def __init__(self, store: RawStore, *, min_interval: float = 1.0, transport: httpx.BaseTransport | None = None,
                 sleep=time.sleep):
        self.store = store
        self.min_interval = min_interval
        self._last = 0.0
        self._sleep = sleep
        self._http = httpx.Client(headers={"User-Agent": USER_AGENT, "Accept": "application/json"}, timeout=120,
                                  transport=transport, follow_redirects=True)

    def _wait(self) -> None:
        gap = self.min_interval - (time.monotonic() - self._last)
        if gap > 0:
            self._sleep(gap)
        self._last = time.monotonic()

    def get(self, source: str, url: str, params: dict, *, revision_of=None) -> tuple[dict, dict]:
        key = hashlib.sha256(json.dumps([url, sorted(params.items())], sort_keys=True).encode()).hexdigest()
        cached = self.store.lookup(key)
        if cached is not None:
            return json.loads(self.store.read(cached)), cached
        for attempt in range(4):
            self._wait()
            try:
                response = self._http.get(url, params=params)
            except httpx.TimeoutException:
                self._sleep(5 * (attempt + 1))
                continue
            if response.status_code in (429, 503):
                self._sleep(float(response.headers.get("retry-after", 5 * (attempt + 1))))
                continue
            response.raise_for_status()
            try:
                payload = json.loads(response.content)
            except json.JSONDecodeError:  # truncated body: transient, fetch again
                self._sleep(3 * (attempt + 1))
                continue
            break
        else:
            raise RuntimeError(f"{source}: repeated throttling, timeouts or malformed JSON for {url}")
        body = response.content
        revision = revision_of(payload) if revision_of else None
        return payload, self.store.put(key, url, params, body, source=source, revision=revision)


def ror_id(value: str | None) -> str | None:
    if not value:
        return None
    match = _ROR.search(value.strip().lower())
    return match.group(1) if match else None


CORE_QUERY = """
SELECT ?ror ?item ?itemLabel ?itemDescription ?enwiki ?website ?inception ?countryLabel ?oa WHERE {
  VALUES ?ror { %s }
  ?item wdt:P6782 ?ror .
  OPTIONAL { ?item wdt:P856 ?website }
  OPTIONAL { ?item wdt:P571 ?inception }
  OPTIONAL { ?item wdt:P17 ?country }
  OPTIONAL { ?item wdt:P10283 ?oa }
  OPTIONAL { ?enwiki schema:about ?item ; schema:isPartOf <https://en.wikipedia.org/> }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en" . }
}
"""
TYPES_QUERY = """
SELECT ?item ?typeLabel WHERE {
  VALUES ?ror { %s }
  ?item wdt:P6782 ?ror ; wdt:P31 ?type .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en" . }
}
"""
PARENTS_QUERY = """
SELECT ?item ?parent ?parentLabel ?prop WHERE {
  VALUES ?ror { %s }
  ?item wdt:P6782 ?ror .
  { ?item wdt:P749 ?parent . BIND("P749" AS ?prop) } UNION { ?item wdt:P361 ?parent . BIND("P361" AS ?prop) }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en" . }
}
"""


def _qid(uri: str) -> str:
    return uri.rsplit("/", 1)[-1]


def parse_org_bindings(core: dict, types: dict | None = None, parents: dict | None = None) -> list[dict]:
    """Merge the three SPARQL result sets into one row per Wikidata item (multi-valued fields kept as lists)."""
    rows: dict[str, dict] = {}
    for binding in core["results"]["bindings"]:
        def val(name):
            return binding[name]["value"] if name in binding else None
        qid = _qid(val("item"))
        row = rows.setdefault(qid, {"ror": val("ror"), "qid": qid, "label": val("itemLabel"),
                                    "description": val("itemDescription"), "enwiki": val("enwiki"), "websites": [],
                                    "inception": val("inception"), "country": val("countryLabel"),
                                    "openalex_ids": [], "types": [], "parents": []})
        for field, key in (("websites", "website"), ("openalex_ids", "oa")):
            if val(key) and val(key) not in row[field]:
                row[field].append(val(key))
    for binding in (types or {"results": {"bindings": []}})["results"]["bindings"]:
        qid = _qid(binding["item"]["value"])
        label = binding.get("typeLabel", {}).get("value")
        if qid in rows and label and label not in rows[qid]["types"]:
            rows[qid]["types"].append(label)
    for binding in (parents or {"results": {"bindings": []}})["results"]["bindings"]:
        if "parent" not in binding or "prop" not in binding:
            continue
        qid = _qid(binding["item"]["value"])
        parent = {"qid": _qid(binding["parent"]["value"]), "label": binding.get("parentLabel", {}).get("value"),
                  "property": binding["prop"]["value"]}
        if qid in rows and parent not in rows[qid]["parents"]:
            rows[qid]["parents"].append(parent)
    return list(rows.values())


def fetch_org_wikidata(fetcher: Fetcher, orgs: list[dict], *, batch: int = 40) -> dict:
    """``orgs``: [{id, ror, openalex_id}]. Returns matches keyed by organization id plus counts."""
    by_ror: dict[str, list[dict]] = {}
    for org in orgs:
        key = ror_id(org.get("ror"))
        if key:
            by_ror.setdefault(key, []).append(org)
    keys = sorted(by_ror)
    found: dict[str, list[dict]] = {}
    for start in range(0, len(keys), batch):
        chunk = keys[start:start + batch]
        values = " ".join(f'"{k}"' for k in chunk)
        results = [fetcher.get("wikidata_sparql", WIKIDATA_SPARQL, {"query": q % values, "format": "json"})[0]
                   for q in (CORE_QUERY, TYPES_QUERY, PARENTS_QUERY)]
        for row in parse_org_bindings(*results):
            found.setdefault(row["ror"], []).append(row)
    matches, conflicts = {}, []
    for ror, orgs_for_ror in by_ror.items():
        rows = found.get(ror, [])
        if len(rows) > 1:
            conflicts.append({"ror": ror, "qids": sorted({r["qid"] for r in rows})})
            continue
        if rows:
            for org in orgs_for_ror:
                matches[org["id"]] = rows[0]
    return {"matches": matches, "conflicts": conflicts, "orgs_with_ror": sum(len(v) for v in by_ror.values()),
            "orgs_total": len(orgs)}


# ---------------------------------------------------------------------------
# Wikipedia (lead section and infobox of linked pages only)

_INFOBOX_START = re.compile(r"\{\{\s*infobox", re.IGNORECASE)


def _strip_markup(value: str) -> str:
    value = re.sub(r"<ref[^>]*?/>|<ref[^>]*?>.*?</ref>", "", value, flags=re.DOTALL)
    value = re.sub(r"<!--.*?-->", "", value, flags=re.DOTALL)
    value = re.sub(r"\{\{[^{}]*\}\}", lambda m: " ".join(p for p in m.group(0)[2:-2].split("|")[1:2]), value)
    value = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", value)
    value = re.sub(r"'''?|<[^>]+>", "", value)
    return " ".join(value.split())


def parse_infobox(wikitext: str) -> dict:
    """Return ``{template, fields}`` for the first infobox in wikitext, or an empty dict."""
    match = _INFOBOX_START.search(wikitext)
    if not match:
        return {}
    depth, index, end = 0, match.start(), None
    while index < len(wikitext) - 1:
        pair = wikitext[index:index + 2]
        if pair == "{{":
            depth += 1
            index += 2
        elif pair == "}}":
            depth -= 1
            index += 2
            if depth == 0:
                end = index
                break
        else:
            index += 1
    body = wikitext[match.start() + 2:(end - 2) if end else len(wikitext)]
    parts, current, depth = [], [], 0
    for ch_index, ch in enumerate(body):
        if body[ch_index:ch_index + 2] in ("{{", "[["):
            depth += 1
        elif body[ch_index:ch_index + 2] in ("}}", "]]"):
            depth -= 1
        if ch == "|" and depth <= 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    parts.append("".join(current))
    fields = {}
    for part in parts[1:]:
        if "=" in part:
            key, value = part.split("=", 1)
            cleaned = _strip_markup(value)
            if key.strip() and cleaned:
                fields[key.strip().lower()] = cleaned[:300]
    return {"template": _strip_markup(parts[0]).lower(), "fields": fields}


def wikipedia_title(url_or_title: str) -> str:
    title = url_or_title.rsplit("/wiki/", 1)[-1]
    return title.replace("_", " ")


def fetch_wikipedia(fetcher: Fetcher, titles: list[str], *, batch: int = 20) -> dict[str, dict]:
    """Lead extract, page and revision IDs, and infobox for each title (redirects resolved)."""
    pages: dict[str, dict] = {}
    titles = sorted(set(titles))
    for start in range(0, len(titles), batch):
        chunk = titles[start:start + batch]
        base = {"action": "query", "format": "json", "formatversion": "2", "redirects": "1", "titles": "|".join(chunk)}
        lead, lead_row = fetcher.get("wikipedia_lead", WIKIPEDIA_API,
                                     {**base, "prop": "extracts|revisions|pageprops", "exintro": "1", "explaintext": "1",
                                      "exlimit": "max", "rvprop": "ids|timestamp", "rvslots": "main"})
        wiki, wiki_row = fetcher.get("wikipedia_wikitext", WIKIPEDIA_API,
                                     {**base, "prop": "revisions", "rvprop": "content", "rvslots": "main", "rvsection": "0"})
        wikitext = {p["pageid"]: p["revisions"][0]["slots"]["main"]["content"]
                    for p in wiki["query"]["pages"] if p.get("revisions")}
        renamed = {}
        for entry in lead["query"].get("redirects", []) + lead["query"].get("normalized", []):
            renamed[entry["from"]] = entry["to"]
        for page in lead["query"]["pages"]:
            if page.get("missing") or "pageid" not in page:
                continue
            revision = (page.get("revisions") or [{}])[0]
            record = {"title": page["title"], "page_id": page["pageid"], "revision_id": revision.get("revid"),
                      "revision_timestamp": revision.get("timestamp"),
                      "wikibase_item": (page.get("pageprops") or {}).get("wikibase_item"),
                      "lead": page.get("extract", ""), "infobox": parse_infobox(wikitext.get(page["pageid"], "")),
                      "url": "https://en.wikipedia.org/wiki/" + page["title"].replace(" ", "_"),
                      "lead_sha256": lead_row["sha256"], "wikitext_sha256": wiki_row["sha256"],
                      "retrieved_at": lead_row["retrieved_at"], "licence": "CC BY-SA 4.0"}
            pages[page["title"]] = record
            for original, target in renamed.items():
                if target == page["title"] or renamed.get(target) == page["title"]:
                    pages[original] = record
    return pages


# ---------------------------------------------------------------------------
# Phase 1 driver and the E1 source manifest

def load_v4_organizations(graph_path: Path) -> list[dict]:
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    return [{"id": n["id"], "name": n["name"], "ror": n["properties"].get("ror"),
             "openalex_id": n["properties"].get("openalex_id"), "country_code": n["properties"].get("country_code"),
             "sector": n["properties"].get("sector")} for n in graph["nodes"] if n["label"] == "Organization"]


def abstract_counts(works_path: Path) -> dict:
    total = with_abstract = 0
    with works_path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            work = json.loads(line)
            total += 1
            if ((work.get("openalex") or {}).get("abstract") or "").strip():
                with_abstract += 1
    return {"papers": total, "with_abstract": with_abstract, "title_only": total - with_abstract}


def acquire_organization_sources(graph_path: Path, works_path: Path, raw_dir: Path, manifest_path: Path,
                                 output_dir: Path, report_path: Path, *, min_interval: float = 1.0,
                                 transport: httpx.BaseTransport | None = None) -> dict:
    fetcher = Fetcher(RawStore(raw_dir, manifest_path), min_interval=min_interval, transport=transport)
    orgs = load_v4_organizations(graph_path)
    wikidata = fetch_org_wikidata(fetcher, orgs)
    by_id = {o["id"]: o for o in orgs}
    linked, openalex_agree, openalex_disagree = {}, 0, 0
    for org_id, row in wikidata["matches"].items():
        if row["openalex_ids"]:
            if by_id[org_id]["openalex_id"] in {x.rsplit("/", 1)[-1] for x in row["openalex_ids"]}:
                openalex_agree += 1
            else:
                openalex_disagree += 1
        if row["enwiki"]:
            linked[org_id] = wikipedia_title(row["enwiki"])
    pages = fetch_wikipedia(fetcher, sorted(set(linked.values())))
    wiki_out = {org_id: pages[title]["url"] for org_id, title in linked.items() if title in pages}
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "org-wikidata.json").write_text(json.dumps(wikidata, indent=1, sort_keys=True, ensure_ascii=False) + "\n")
    (output_dir / "org-wikipedia.json").write_text(json.dumps(pages, indent=1, sort_keys=True, ensure_ascii=False) + "\n")
    with manifest_path.open(encoding="utf-8") as handle:
        manifest_rows = [json.loads(line) for line in handle if line.strip()]
    sectors = {}
    for org_id in wikidata["matches"]:
        sectors[by_id[org_id].get("sector") or "unknown"] = sectors.get(by_id[org_id].get("sector") or "unknown", 0) + 1
    report = {
        "report_version": "enrichment-sources-v1",
        "retrieved_with": {"user_agent": USER_AGENT, "min_interval_seconds": min_interval},
        "sources": {
            "openalex_abstracts": {**abstract_counts(works_path), "path": str(works_path),
                                   "licence": "CC0 (OpenAlex); redistribution of abstract text not assumed, see docs/source-policy.md",
                                   "selection": "all core papers; papers without an abstract use the title only"},
            "wikidata_organizations": {"organizations": len(orgs), "with_ror": wikidata["orgs_with_ror"],
                                       "matched_by_ror": len(wikidata["matches"]), "ror_conflicts": len(wikidata["conflicts"]),
                                       "openalex_id_agrees": openalex_agree, "openalex_id_disagrees": openalex_disagree,
                                       "matched_by_sector": sectors, "licence": "CC0",
                                       "selection": "v4 organizations with a ROR ID, matched on Wikidata P6782 only; no name matching"},
            "wikipedia_organization_pages": {"pages": len(pages), "orgs_linked": len(wiki_out), "licence": "CC BY-SA 4.0",
                                             "selection": "English Wikipedia lead section and infobox of pages linked from a matched Wikidata item; revision ID stored"},
            "wikidata_researchers": {"status": "not_run", "reason": "optional; exact ORCID/OpenAlex-ID matches only if time allows"},
            "news_blogs": {"status": "not_run", "reason": "stretch source, only after M3"},
        },
        "fetches": {"rows": len(manifest_rows), "by_source": dict(sorted(
            {s: sum(1 for r in manifest_rows if r["source"] == s) for s in {r["source"] for r in manifest_rows}}.items())),
            "manifest": str(manifest_path), "raw_dir": str(raw_dir)},
        "rules": "Every fetched document is stored once, immutable, with URL, parameters, retrieval time, revision ID and SHA-256.",
        "publication_default": "IDs, offsets and spans; Wikipedia text is CC BY-SA and is not republished wholesale",
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report
