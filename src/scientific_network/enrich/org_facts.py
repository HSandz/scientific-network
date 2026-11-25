"""Enrichment v2: Wikidata facts about PART_OF children and parents (instance-of, qualifiers, reverse statements).

Everything goes through the cached, rate-limited ``Fetcher`` into the v2 raw store (``data/raw/enrichment-v2``), so
the v1 raw store and manifest stay unchanged. Facts are data only: no rule is applied here (see ``part_of_rule``).
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from scientific_network.enrich.sources import WIKIDATA_SPARQL, Fetcher

STATEMENT_PROPERTIES = ("P749", "P361", "P355", "P527")
TYPES_QUERY = """
SELECT ?item ?cls ?clsLabel WHERE {
  VALUES ?item { %s }
  ?item wdt:P31 ?cls .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en" . }
}
"""
STATEMENTS_QUERY = """
SELECT ?item ?target ?rank ?start ?end WHERE {
  VALUES ?item { %s }
  ?item p:%s ?st . ?st ps:%s ?target . ?st wikibase:rank ?rank .
  OPTIONAL { ?st pq:P580 ?start } OPTIONAL { ?st pq:P582 ?end }
}
"""  # one query per property: the four-way UNION with the label service timed out (HTTP 504) on Wikidata
SUPERCLASS_QUERY = """
SELECT ?cls ?sup ?supLabel WHERE {
  VALUES ?cls { %s }
  ?cls wdt:P279 ?sup .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en" . }
}
"""


def qid(uri: str) -> str:
    return uri.rsplit("/", 1)[-1]


def _values(ids: list[str]) -> str:
    return " ".join(f"wd:{i}" for i in ids)


def _run(fetcher: Fetcher, query: str, ids: list[str], batch: int, *, prop: str | None = None) -> list[dict]:
    rows = []
    for start in range(0, len(ids), batch):
        chunk = ids[start:start + batch]
        payload, _row = fetcher.get("wikidata_sparql", WIKIDATA_SPARQL, {"query": (query % (_values(chunk), prop, prop)) if prop else (query % _values(chunk)), "format": "json"})
        rows.extend(payload["results"]["bindings"])
    return rows


def fetch_org_facts(fetcher: Fetcher, qids: list[str], *, superclass_depth: int = 3, batch: int = 40) -> dict:
    """Instance-of classes, class superclasses (depth-limited), and P749/P361/P355/P527 statements with qualifiers.

    Returns {"types": {item: {class: label}}, "statements": {item: [{prop, target, rank, start, end}]},
    "superclasses": {class: {superclass: label}}, "class_labels": {class: label}}.
    """
    qids = sorted(set(qids))
    types: dict[str, dict[str, str]] = defaultdict(dict)
    class_labels: dict[str, str] = {}
    for b in _run(fetcher, TYPES_QUERY, qids, batch):
        cls = qid(b["cls"]["value"])
        label = (b.get("clsLabel") or {}).get("value", cls)
        types[qid(b["item"]["value"])][cls] = label
        class_labels[cls] = label
    statements: dict[str, list[dict]] = defaultdict(list)
    for prop in STATEMENT_PROPERTIES:
        for b in _run(fetcher, STATEMENTS_QUERY, qids, batch, prop=prop):
            item = qid(b["item"]["value"])
            row = {"prop": prop, "target": qid(b["target"]["value"]), "rank": qid(b["rank"]["value"]).replace("Rank", "").lower(),
                   "start": (b.get("start") or {}).get("value"), "end": (b.get("end") or {}).get("value")}
            if row not in statements[item]:
                statements[item].append(row)
    superclasses: dict[str, dict[str, str]] = defaultdict(dict)
    frontier = sorted(class_labels)
    seen = set(frontier)
    for _depth in range(superclass_depth):
        found = []
        for b in _run(fetcher, SUPERCLASS_QUERY, frontier, batch):
            cls, sup = qid(b["cls"]["value"]), qid(b["sup"]["value"])
            label = (b.get("supLabel") or {}).get("value", sup)
            superclasses[cls][sup] = label
            class_labels[sup] = label
            if sup not in seen:
                seen.add(sup)
                found.append(sup)
        frontier = sorted(found)
        if not frontier:
            break
    return {"items": len(qids), "superclass_depth": superclass_depth, "types": {k: v for k, v in sorted(types.items())},
            "statements": {k: v for k, v in sorted(statements.items())},
            "superclasses": {k: v for k, v in sorted(superclasses.items())}, "class_labels": dict(sorted(class_labels.items()))}


def collect_part_of_qids(graph: dict) -> list[str]:
    """Child and parent QIDs of every PART_OF edge in a graph (from the Wikidata evidence records)."""
    evidence = {e["id"]: e for e in graph["evidence"]}
    out = set()
    for edge in graph["edges"]:
        if edge["relation"] == "PART_OF":
            for ref in edge["evidence_ids"]:
                out.update((evidence[ref]["wikidata_item"], evidence[ref]["parent_item"]))
    return sorted(out)


def write_facts(facts: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(facts, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
