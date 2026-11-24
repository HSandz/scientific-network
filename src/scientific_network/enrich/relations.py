"""E3: paper-to-entity edges and entity-to-entity relations from verified mentions (specification §4.3).

Edge IDs are deterministic from (relation, source, target, method version). Every edge records the
supporting paper IDs and where in each paper the support sits (character offsets and sentence
index into the title+abstract text), never the abstract text itself (docs/source-policy.md).
"""

from collections import defaultdict
from hashlib import sha256
from itertools import combinations

PAPER_RELATION = {"Method": "USES_METHOD", "Task": "ADDRESSES_TASK", "Dataset": "USES_DATASET"}


def edge_id(relation: str, source: str, target: str, method_version: str) -> str:
    return "edge:" + sha256(f"{relation}\0{source}\0{target}\0{method_version}".encode()).hexdigest()


def evidence_id(kind: str, *parts: str) -> str:
    return f"evidence:{kind}:" + sha256("\0".join(parts).encode()).hexdigest()[:24]


def node_lookup(nodes: list[dict]) -> dict[tuple[str, str], str]:
    """(type, normalized key) -> node id, covering every surface key merged into a node."""
    return {(n["type"], key): n["id"] for n in nodes for key in n["keys"]}


def paper_entity_edges(mentions: list[dict], lookup: dict, texts: dict[str, str], *, method_version: str,
                       graph_version: str) -> tuple[list[dict], list[dict]]:
    """USES_METHOD / ADDRESSES_TASK / USES_DATASET: one edge per (paper, entity); evidence per mention span."""
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for m in mentions:
        if m["status"] != "kept":
            continue
        node = lookup.get((m["type"], m["key"]))
        if node is not None:
            grouped[(m["paper_id"], node)].append(m)
    edges, evidence = [], []
    for (paper_id, node), found in sorted(grouped.items()):
        best = max(found, key=lambda m: (m["confidence"], -m["start"]))
        entity_type = best["type"]
        ev = {"id": evidence_id("extracted", paper_id, node, str(best["start"]), str(best["end"])), "kind": "extracted",
              "paper_id": paper_id, "source": "openalex_abstract_or_title", "text_sha256": sha256(texts[paper_id].encode()).hexdigest(),
              "start": best["start"], "end": best["end"], "sentence": best["sentence"], "surface": best["text"],
              "confidence": best["confidence"], "extractor": best["extractor"], "retyped_from": best["retyped_from"],
              "in_encoder_baseline": any(m["in_encoder_baseline"] for m in found)}
        evidence.append(ev)
        edges.append({"edge_id": edge_id(PAPER_RELATION[entity_type], paper_id, node, method_version),
                      "relation": PAPER_RELATION[entity_type], "source_id": paper_id, "target_id": node,
                      "evidence_kind": "extracted", "evidence_ids": [ev["id"]], "method_version": method_version,
                      "graph_version": graph_version, "validation_status": "accepted",
                      "properties": {"support_count": 1, "n_mentions": sum(m["n_mentions"] for m in found),
                                     "confidence": best["confidence"], "sentence": best["sentence"]}})
    return edges, evidence


def entity_relation_edges(paper_relations: list[dict], lookup: dict, mentions: list[dict], texts: dict[str, str], *,
                          min_papers: dict[str, int], method_version: str, graph_version: str) -> tuple[list[dict], list[dict], dict]:
    """APPLIED_TO and EVALUATED_ON, kept when at least ``min_papers[relation]`` distinct papers support the pair."""
    spans = {(m["paper_id"], m["type"], m["key"]): m for m in mentions if m["status"] == "kept"}
    support: dict[tuple[str, str, str], dict[str, dict]] = defaultdict(dict)
    for rel in paper_relations:
        head = lookup.get((rel["head_type"], rel["head_key"]))
        tail = lookup.get((rel["tail_type"], rel["tail_key"]))
        if head is None or tail is None or head == tail:
            continue
        support[(rel["relation"], head, tail)].setdefault(rel["paper_id"], rel)
    edges, evidence = [], []
    dropped_below = 0
    for (relation, head, tail), by_paper in sorted(support.items()):
        if len(by_paper) < min_papers[relation]:
            dropped_below += 1
            continue
        ev_ids = []
        for paper_id, rel in sorted(by_paper.items()):
            h = spans[(paper_id, rel["head_type"], rel["head_key"])]
            t = spans[(paper_id, rel["tail_type"], rel["tail_key"])]
            ev = {"id": evidence_id("extracted", paper_id, relation, head, tail), "kind": "extracted", "paper_id": paper_id,
                  "source": "openalex_abstract_or_title", "text_sha256": sha256(texts[paper_id].encode()).hexdigest(),
                  "head_span": [h["start"], h["end"]], "tail_span": [t["start"], t["end"]],
                  "head_sentence": rel["head_sentence"], "tail_sentence": rel["tail_sentence"],
                  "same_sentence": rel["same_sentence"], "extractor": h["extractor"]}
            evidence.append(ev)
            ev_ids.append(ev["id"])
        papers = sorted(by_paper)
        edges.append({"edge_id": edge_id(relation, head, tail, method_version), "relation": relation, "source_id": head,
                      "target_id": tail, "evidence_kind": "extracted", "evidence_ids": ev_ids, "method_version": method_version,
                      "graph_version": graph_version, "validation_status": "accepted",
                      "properties": {"support_count": len(papers), "support_paper_ids": papers,
                                     "same_sentence_papers": sum(1 for r in by_paper.values() if r["same_sentence"])}})
    return edges, evidence, {"pairs_seen": len(support), "pairs_below_threshold": dropped_below}


def part_of_edges(matches: dict, org_ids: set[str], parent_nodes: dict[str, dict], fetch_rows: dict[str, dict], *,
                  method_version: str, graph_version: str) -> tuple[list[dict], list[dict]]:
    """PART_OF from Wikidata P749 (parent organization) and P361 (part of) between organizations."""
    qid_to_org = {m["qid"]: org for org, m in matches.items() if org in org_ids}
    edges, evidence = [], []
    for org, match in sorted(matches.items()):
        if org not in org_ids:
            continue
        for parent in match["parents"]:
            target = qid_to_org.get(parent["qid"]) or parent_nodes[parent["qid"]]["id"]
            if target == org:
                continue
            ev = {"id": evidence_id("wikidata", org, parent["property"], parent["qid"]), "kind": "wikidata",
                  "source_url": f"https://www.wikidata.org/wiki/{match['qid']}", "wikidata_item": match["qid"],
                  "property": parent["property"], "parent_item": parent["qid"], "source": "wikidata_sparql",
                  "retrieved_at": fetch_rows.get("retrieved_at"), "raw_sha256": fetch_rows.get("sha256")}
            evidence.append(ev)
            edges.append({"edge_id": edge_id("PART_OF", org, target, method_version), "relation": "PART_OF", "source_id": org,
                          "target_id": target, "evidence_kind": "wikidata", "evidence_ids": [ev["id"]],
                          "method_version": method_version, "graph_version": graph_version, "validation_status": "accepted",
                          "properties": {"wikidata_property": parent["property"], "parent_in_v4": target in org_ids}})
    # a pair stated by both P749 and P361 is one edge with both pieces of evidence
    merged: dict[str, dict] = {}
    for e in edges:
        slot = merged.setdefault(e["edge_id"], e)
        if slot is not e:
            slot["evidence_ids"].extend(e["evidence_ids"])
            slot["properties"]["wikidata_property"] = "P361+P749"
    return list(merged.values()), evidence


def related_to_edges(linked: dict[str, str], page_links: dict[str, set[str]], paper_entities: dict[str, set[str]], *,
                     min_papers: int, method_version: str, graph_version: str) -> tuple[list[dict], list[dict], dict]:
    """RELATED_TO between two linked Method/Task nodes: a Wikipedia link in either direction and >= min_papers shared papers.

    ``linked`` maps node id -> Wikipedia title; ``page_links`` maps title -> titles it links to;
    ``paper_entities`` maps paper id -> node ids. Orientation: source id < target id.
    """
    by_title = {title: node for node, title in linked.items()}
    candidate_pairs = set()
    for node, title in linked.items():
        for target_title in page_links.get(title, ()):
            other = by_title.get(target_title)
            if other and other != node:
                candidate_pairs.add(tuple(sorted((node, other))))
    cooc: dict[tuple[str, str], list[str]] = defaultdict(list)
    wanted = {n for pair in candidate_pairs for n in pair}
    for paper, nodes in sorted(paper_entities.items()):
        for pair in combinations(sorted(nodes & wanted), 2):
            if pair in candidate_pairs:
                cooc[pair].append(paper)
    edges, evidence = [], []
    for pair, papers in sorted(cooc.items()):
        if len(papers) < min_papers:
            continue
        a, b = pair
        directions = [d for d, (x, y) in (("a_links_b", (a, b)), ("b_links_a", (b, a)))
                      if linked[y] in page_links.get(linked[x], ())]
        ev = {"id": evidence_id("wikipedia", a, b), "kind": "wikipedia", "source": "wikipedia_links",
              "titles": [linked[a], linked[b]], "directions": directions}
        evidence.append(ev)
        edges.append({"edge_id": edge_id("RELATED_TO", a, b, method_version), "relation": "RELATED_TO", "source_id": a, "target_id": b,
                      "evidence_kind": "aggregated", "evidence_ids": [ev["id"]], "method_version": method_version,
                      "graph_version": graph_version, "validation_status": "accepted",
                      "properties": {"support_count": len(papers), "support_paper_ids": papers, "wikipedia_link": directions}})
    return edges, evidence, {"linked_pairs_with_wikipedia_link": len(candidate_pairs), "pairs_with_enough_papers": len(edges)}
