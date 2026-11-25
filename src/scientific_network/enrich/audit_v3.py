"""E4 v3 audit (D042 amendment 2026-11-25): fresh items only, four axes, every item judged by A and B, adjudicated by a non-Claude C.

Axes: PART_OF v3 kept edges (50), MEMBER_OF (up to 30, excluding the 30 v2-audited pairs), linking v3 (up to 100) and single-paper
same-sentence APPLIED_TO (up to 100). Every axis excludes every item already audited or used in any development or informational
sample. The sample and packets are written and hashed before any judgement.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path

from scientific_network.enrich.audit_v2 import PROPERTY_LABELS, excluded_pairs, pair_of
from scientific_network.enrich.k1 import read_jsonl
from scientific_network.enrich.quality import (TYPES, draw, item_id, load_answers, precision, relation_precision, write_packets)
from scientific_network.enrich.v3 import AUDIT_SEED_V3, applied_to_candidates, relation_items_for, seen_papers

PART_OF_SIZE, MEMBER_OF_SIZE, LINK_SIZE, APPLIED_SIZE = 50, 30, 100, 100
SHARD = 80


def org_pair_items(graph: dict, edge_ids: list[str], axis: str, prefix: str) -> dict:
    """PART_OF or MEMBER_OF items: the two organizations, their Wikidata descriptions, the statement(s) and the parent's classes."""
    nodes = {n["id"]: n for n in graph["nodes"]}
    extra = graph.get("node_enrichments", {})
    evidence = {e["id"]: e for e in graph["evidence"]}
    edges = {e["edge_id"]: e for e in graph["edges"]}
    items = {}
    for edge_id in edge_ids:
        e = edges[edge_id]
        child, parent = nodes[e["source_id"]], nodes[e["target_id"]]
        evs = [evidence[r] for r in e["evidence_ids"]]
        items[item_id(prefix, edge_id)] = {
            "item_id": item_id(prefix, edge_id), "axis": axis, "organization": child["name"],
            "organization_description": (extra.get(child["id"]) or {}).get("wikidata_description"), "organization_qid": evs[0]["wikidata_item"],
            "parent": parent["name"], "parent_description": (extra.get(parent["id"]) or {}).get("wikidata_description"), "parent_qid": evs[0]["parent_item"],
            "parent_instance_of": evs[0].get("parent_instance_of", []),
            "wikidata_statements": [{"property": ev["property"], "property_label": PROPERTY_LABELS.get(ev["property"], ev["property"]),
                                     "statement": f"{ev['wikidata_item']} {ev['property']} {ev['parent_item']}", "statement_item_url": ev["source_url"],
                                     "raw_response_sha256": ev.get("raw_sha256"), "retrieved_at": ev.get("retrieved_at")} for ev in evs]}
    return items


def link_items_v3(graph: dict, texts: dict[str, str], leads: dict[str, str], node_ids: list[str]) -> dict:
    papers_of: dict[str, list[str]] = defaultdict(list)
    for e in graph["edges"]:
        if e["relation"] in ("USES_METHOD", "ADDRESSES_TASK", "USES_DATASET"):
            papers_of[e["target_id"]].append(e["source_id"])
    nodes = {n["id"]: n for n in graph["nodes"]}
    items = {}
    for node_id in node_ids:
        n = nodes[node_id]
        titles = [texts[p].split("\n")[0] for p in sorted(papers_of[node_id])[:3]]
        items[item_id("link", node_id)] = {"item_id": item_id("link", node_id), "axis": "link", "entity": n["name"], "type": n["label"],
                                           "example_paper_titles": titles, "wikipedia_title": n["properties"]["wikipedia_title"],
                                           "wikipedia_lead": leads.get(n["properties"]["wikipedia_title"], "")[:500]}
    return items


def _rows(path: Path) -> list[dict]:
    return read_jsonl(path) if path.exists() else []


def freeze_v3(*, graph_path: Path, texts_path: Path, link_dir: Path, v1_graph_path: Path, v1_sample_path: Path, v2_graph_path: Path, v2_sample_path: Path,
              dev_label_files: list[Path], link_dev_labels: Path, applied_dev_sample: Path, applied_informational: Path, config_path: Path,
              out_dir: Path, seed: int = AUDIT_SEED_V3) -> dict:
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    v1_graph = json.loads(v1_graph_path.read_text(encoding="utf-8"))
    v1_sample = json.loads(v1_sample_path.read_text(encoding="utf-8"))
    v2_graph = json.loads(v2_graph_path.read_text(encoding="utf-8"))
    v2_sample = json.loads(v2_sample_path.read_text(encoding="utf-8"))
    texts = {r["id"]: r["text"] for r in read_jsonl(texts_path)}
    leads = {r["id"]: r["text"] for r in read_jsonl(link_dir / "link-leads.jsonl")}
    nodes = {n["id"]: n for n in graph["nodes"]}

    # --- organization axes: pairs seen in v1 audit, v1/v2 development samples and the v2 MEMBER_OF audit
    seen = excluded_pairs(v1_graph, v1_sample, dev_label_files)
    v2_edges = {e["edge_id"]: e for e in v2_graph["edges"]}
    v2_audited = {pair_of(v2_edges[i]) for i in v2_sample["axes"]["member_of"]["MEMBER_OF"]}
    seen_pairs = seen["v1_audited"] | seen["development_labeled"] | v2_audited
    part_pool = {e["edge_id"]: e for e in graph["edges"] if e["relation"] == "PART_OF" and pair_of(e) not in seen_pairs}
    member_pool = {e["edge_id"]: e for e in graph["edges"] if e["relation"] == "MEMBER_OF" and pair_of(e) not in seen_pairs}
    part_ids = draw(sorted(part_pool), PART_OF_SIZE, seed, "part_of_v3")
    member_ids = draw(sorted(member_pool), MEMBER_OF_SIZE, seed, "member_of_v3")

    # --- linking: linked entities not in the v1 link audit or the link development sample (by node ID or Wikipedia page)
    v1_nodes = {n["id"]: n for n in v1_graph["nodes"]}
    seen_nodes = set(v1_sample["link_sample"]["link"]) | {r["node_id"] for r in _rows(link_dev_labels)}
    seen_titles = {(v1_nodes[i]["properties"].get("wikipedia_title")) for i in v1_sample["link_sample"]["link"] if i in v1_nodes} | {r["wikipedia_title"] for r in _rows(link_dev_labels)}
    link_pool = [n["id"] for n in graph["nodes"] if n["label"] in TYPES and n["properties"].get("linked") and n["id"] not in seen_nodes
                 and n["properties"].get("wikipedia_title") not in seen_titles]
    link_ids = draw(sorted(link_pool), LINK_SIZE, seed, "link_v3")

    # --- single-paper APPLIED_TO: not the development 40, not the 30 informational items (their papers are excluded too)
    dev = json.loads(applied_dev_sample.read_text(encoding="utf-8"))
    informational = _rows(applied_informational)
    dev_edges = set(dev["edge_ids"])
    candidates = applied_to_candidates(graph)
    used_papers = {c["paper_id"] for c in candidates if c["edge_id"] in dev_edges} | {r["paper_id"] for r in informational}
    applied_pool = {c["edge_id"]: c for c in candidates if c["edge_id"] not in dev_edges and c["paper_id"] not in used_papers}
    applied_ids = draw(sorted(applied_pool), APPLIED_SIZE, seed, "applied_to_v3")

    items = {**org_pair_items(graph, part_ids, "part_of", "part"), **org_pair_items(graph, member_ids, "member_of", "member"),
             **link_items_v3(graph, texts, leads, link_ids), **relation_items_for(graph, texts, applied_ids)}
    assignments = {i: ["A", "B"] for i in items}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "answers").mkdir(exist_ok=True)
    packets = write_packets(items, assignments, [], out_dir, shard_size=SHARD)
    sample = {"seed": seed, "graph_version": graph["graph_version"], "graph_sha256": sha256(graph_path.read_bytes()).hexdigest(),
              "config_sha256": sha256(config_path.read_bytes()).hexdigest(),
              "axes": {"part_of": {"edge_ids": part_ids, "population": sum(e["relation"] == "PART_OF" for e in graph["edges"]), "pool_after_exclusion": len(part_pool), "requested": PART_OF_SIZE},
                       "member_of": {"edge_ids": member_ids, "population": sum(e["relation"] == "MEMBER_OF" for e in graph["edges"]), "pool_after_exclusion": len(member_pool), "requested": MEMBER_OF_SIZE},
                       "link": {"node_ids": link_ids, "population": sum(1 for n in graph["nodes"] if n["label"] in TYPES and n["properties"].get("linked")), "pool_after_exclusion": len(link_pool), "requested": LINK_SIZE},
                       "applied_to_single_paper": {"edge_ids": applied_ids, "population": len(candidates), "pool_after_exclusion": len(applied_pool), "requested": APPLIED_SIZE,
                                                   "excluded": {"development_edges": len(dev_edges), "informational_items": len(informational), "papers_of_those": len(used_papers)}}},
              "excluded_pairs": {"v1_audited": len(seen["v1_audited"]), "development_labeled": len(seen["development_labeled"]), "v2_audited_member_of": len(v2_audited)},
              "excluded_link_nodes": len(seen_nodes), "unchanged_axes_not_reaudited": ["entities", "paper_edges", "RELATED_TO", "EVALUATED_ON single-paper (27 audited in v2)", "APPLIED_TO (two or more papers)"],
              "assignments": assignments, "item_axes": dict(Counter(i["axis"] for i in items.values())), "items_total": len(items)}
    sample_path, items_path = out_dir / "sample.json", out_dir / "items.json"
    sample_path.write_text(json.dumps(sample, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    items_path.write_text(json.dumps(items, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    receipt = {"frozen": True, "purpose": "E4 v3 AI-assessed audit sample, written before any judgement", "sample_sha256": sha256(sample_path.read_bytes()).hexdigest(),
               "items_sha256": sha256(items_path.read_bytes()).hexdigest(),
               "packets": [{k: v for k, v in p.items() if k != "path"} | {"file": Path(p["path"]).name} for p in packets],
               "graph_version": graph["graph_version"], "seed": seed, "config_sha256": sample["config_sha256"]}
    (out_dir / "freeze-receipt.json").write_text(json.dumps(receipt, indent=1, sort_keys=True), encoding="utf-8")
    return receipt
