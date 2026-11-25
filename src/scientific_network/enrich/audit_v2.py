"""E4 v2 audit: fresh samples for the axes that changed in enrichment v2 (D042 amendment 2026-11-25).

Changed axes: the new single-paper same-sentence ``EVALUATED_ON`` edges (all of them) and the new ``MEMBER_OF`` predicate (a fresh
sample that excludes every v1-audited pair and every development-labeled pair). Axes whose rule was not adopted (PART_OF, single-paper
``APPLIED_TO``, the link guard) are not re-audited; their v1 figures are carried over and labeled as such. Both A and B judge every item
because each axis has 50 or fewer items; adjudicator C decides disagreements. The sample and packets are written and hashed before any
judgement.
"""

from __future__ import annotations

import json
from collections import Counter
from hashlib import sha256
from pathlib import Path

from scientific_network.enrich.k1 import read_jsonl
from scientific_network.enrich.quality import (draw, final_verdict, item_id, load_answers, precision, relation_precision, support_text, write_packets)

AUDIT_SEED = 2026112502
PROPERTY_LABELS = {"P749": "parent organization", "P361": "part of"}
MEMBER_OF_SIZE = 30


def pair_of(edge: dict) -> tuple[str, str]:
    return edge["source_id"], edge["target_id"]


def excluded_pairs(v1_graph: dict, audit_sample: dict, dev_label_files: list[Path]) -> dict[str, set[tuple[str, str]]]:
    """Organization pairs already seen: the 50 v1-audited PART_OF edges and the development-labeled PART_OF / MEMBER_OF candidates."""
    by_id = {e["edge_id"]: e for e in v1_graph["edges"] if e["relation"] == "PART_OF"}
    audited = {pair_of(by_id[i]) for i in audit_sample["part_of_sample"]["PART_OF"]}
    dev = set()
    for path in dev_label_files:
        for row in read_jsonl(path):
            dev.add(pair_of(by_id[row["edge_id"]]))
    return {"v1_audited": audited, "development_labeled": dev}


def single_paper_evaluated_on_items(graph: dict, texts: dict[str, str]) -> tuple[dict, list[str]]:
    nodes = {n["id"]: n for n in graph["nodes"]}
    evidence = {e["id"]: e for e in graph["evidence"]}
    items, edge_ids = {}, []
    for e in graph["edges"]:
        if e["relation"] == "EVALUATED_ON" and e["properties"].get("support_rule") == "single_paper_same_sentence":
            ev = evidence[e["evidence_ids"][0]]
            edge_ids.append(e["edge_id"])
            items[item_id("rel", e["edge_id"])] = {
                "item_id": item_id("rel", e["edge_id"]), "axis": "relation", "relation": "EVALUATED_ON",
                "head": f"{nodes[e['source_id']]['name']} ({nodes[e['source_id']]['label']})",
                "tail": f"{nodes[e['target_id']]['name']} ({nodes[e['target_id']]['label']})",
                "papers": [support_text(texts, ev["paper_id"], [ev["head_span"], ev["tail_span"]])]}
    return items, sorted(edge_ids)


def member_of_items(graph: dict, excluded: dict[str, set], seed: int, size: int) -> tuple[dict, dict]:
    nodes = {n["id"]: n for n in graph["nodes"]}
    extra = graph.get("node_enrichments", {})
    evidence = {e["id"]: e for e in graph["evidence"]}
    all_edges = {e["edge_id"]: e for e in graph["edges"] if e["relation"] == "MEMBER_OF"}
    seen = excluded["v1_audited"] | excluded["development_labeled"]
    pool = {i: e for i, e in all_edges.items() if pair_of(e) not in seen}
    chosen = draw(sorted(pool), size, seed, "member_of")
    items = {}
    for edge_id in chosen:
        e = pool[edge_id]
        ev = evidence[e["evidence_ids"][0]]
        child, parent = nodes[e["source_id"]], nodes[e["target_id"]]
        items[item_id("member", edge_id)] = {
            "item_id": item_id("member", edge_id), "axis": "member_of", "organization": child["name"],
            "organization_description": (extra.get(child["id"]) or {}).get("wikidata_description"), "organization_qid": ev["wikidata_item"],
            "parent": parent["name"], "parent_description": (extra.get(parent["id"]) or {}).get("wikidata_description"), "parent_qid": ev["parent_item"],
            "parent_instance_of": ev["parent_instance_of"],
            "wikidata_statement": {"property": ev["property"], "property_label": PROPERTY_LABELS[ev["property"]],
                                   "statement": f"{ev['wikidata_item']} {ev['property']} {ev['parent_item']}",
                                   "statement_item_url": ev["source_url"], "raw_response_sha256": ev["raw_sha256"], "retrieved_at": ev["retrieved_at"]}}
    return items, {"MEMBER_OF": chosen, "population": len(all_edges), "excluded_v1_audited_pairs": len(excluded["v1_audited"]),
                   "excluded_development_pairs": len(excluded["development_labeled"]), "pool_after_exclusion": len(pool)}


def freeze_v2(*, graph_path: Path, texts_path: Path, v1_graph_path: Path, v1_sample_path: Path, dev_label_files: list[Path], config_path: Path,
              out_dir: Path, seed: int = AUDIT_SEED) -> dict:
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    v1_graph = json.loads(v1_graph_path.read_text(encoding="utf-8"))
    v1_sample = json.loads(v1_sample_path.read_text(encoding="utf-8"))
    texts = {r["id"]: r["text"] for r in read_jsonl(texts_path)}
    rel_items, rel_ids = single_paper_evaluated_on_items(graph, texts)
    mem_items, mem_sample = member_of_items(graph, excluded_pairs(v1_graph, v1_sample, dev_label_files), seed, MEMBER_OF_SIZE)
    items = {**rel_items, **mem_items}
    assignments = {i: ["A", "B"] for i in items}  # every axis has 50 or fewer items: A and B both judge all of them
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "answers").mkdir(exist_ok=True)
    packets = write_packets(items, assignments, [], out_dir, shard_size=120)
    sample = {"seed": seed, "graph_version": graph["graph_version"], "graph_sha256": sha256(graph_path.read_bytes()).hexdigest(),
              "config_sha256": sha256(config_path.read_bytes()).hexdigest(), "base_v1_graph_sha256": sha256(v1_graph_path.read_bytes()).hexdigest(),
              "axes": {"evaluated_on_single_paper": {"edge_ids": rel_ids, "population": len(rel_ids), "sampled": len(rel_ids),
                                                     "note": "all new single-paper same-sentence EVALUATED_ON edges"},
                       "member_of": mem_sample},
              "unchanged_axes_not_reaudited": ["entities", "paper_edges", "APPLIED_TO (two or more papers)", "RELATED_TO", "PART_OF (rule not adopted)", "linking (guard not adopted)"],
              "assignments": assignments, "item_axes": dict(Counter(i["axis"] for i in items.values())), "items_total": len(items)}
    sample_path = out_dir / "sample.json"
    sample_path.write_text(json.dumps(sample, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    items_path = out_dir / "items.json"
    items_path.write_text(json.dumps(items, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    receipt = {"frozen": True, "purpose": "E4 v2 AI-assessed audit sample, written before any judgement",
               "sample_sha256": sha256(sample_path.read_bytes()).hexdigest(), "items_sha256": sha256(items_path.read_bytes()).hexdigest(),
               "packets": [{k: v for k, v in p.items() if k != "path"} | {"file": Path(p["path"]).name} for p in packets],
               "graph_version": graph["graph_version"], "seed": seed, "config_sha256": sample["config_sha256"]}
    (out_dir / "freeze-receipt.json").write_text(json.dumps(receipt, indent=1, sort_keys=True), encoding="utf-8")
    return receipt


def score_v2(audit_dir: Path) -> dict:
    sample = json.loads((audit_dir / "sample.json").read_text(encoding="utf-8"))
    receipt = json.loads((audit_dir / "freeze-receipt.json").read_text(encoding="utf-8"))
    if sha256((audit_dir / "sample.json").read_bytes()).hexdigest() != receipt["sample_sha256"]:
        raise ValueError("sample.json differs from the frozen receipt")
    items = json.loads((audit_dir / "items.json").read_text(encoding="utf-8"))
    judged, _ = load_answers(audit_dir / "answers")
    rel_ids = [item_id("rel", e) for e in sample["axes"]["evaluated_on_single_paper"]["edge_ids"]]
    mem_ids = [item_id("member", e) for e in sample["axes"]["member_of"]["MEMBER_OF"]]
    relation = relation_precision({"ids": {"same_sentence": rel_ids}, "population": {"same_sentence": len(rel_ids)}}, judged, items)
    pairs = [(judged[i]["A"]["verdict"], judged[i]["B"]["verdict"]) for i in items if i in judged and "A" in judged[i] and "B" in judged[i]]
    from scientific_network.evaluation.edge_audit import cohens_kappa
    kappa = cohens_kappa(pairs)
    return {"evaluated_on_single_paper": {"shown_paper_supports_the_relation": relation["strata"]["same_sentence"]["every_shown_paper_supports"],
                                           "unclear": relation["strata"]["same_sentence"]["unclear"],
                                           "sensitivity_unclear_as_incorrect": relation["strata"]["same_sentence"]["sensitivity_unclear_as_incorrect"],
                                           "sampled": len(rel_ids), "population": len(rel_ids)},
            "member_of": precision(mem_ids, judged) | {"population": sample["axes"]["member_of"]["population"]},
            "agreement": {"items_judged_by_both": len(pairs), "observed_agreement": round(sum(a == b for a, b in pairs) / len(pairs), 4) if pairs else None,
                          "cohens_kappa": None if kappa is None else round(kappa, 4)},
            "channel_c_items": sum(1 for i in items if i in judged and "C" in judged[i]),
            "items_answered": sum(1 for i in items if i in judged), "items_frozen": len(items)}
