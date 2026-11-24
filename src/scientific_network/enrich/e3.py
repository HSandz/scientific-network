"""Phase 2-4 orchestration: link entities, build the enrichment layer, assemble and validate v5-enriched."""

import json
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path

from scientific_network.enrich.finalize import finalize_entities
from scientific_network.enrich.graph5 import build_enriched_graph, enriched_counts, validate_enriched
from scientific_network.enrich.k1 import read_jsonl, write_jsonl
from scientific_network.enrich.link import apply_threshold, fetch_page_links, link_entities
from scientific_network.enrich.relations import (entity_relation_edges, paper_entity_edges, part_of_edges, related_to_edges)
from scientific_network.enrich.sources import Fetcher, RawStore


def run_link_entities(e2_dir: Path, texts_path: Path, raw_dir: Path, manifest: Path, output_dir: Path, *, threshold: float,
                      device: str = "cuda", min_interval: float = 0.5) -> dict:
    nodes = read_jsonl(e2_dir / "entities.jsonl")
    texts = {r["id"]: r["text"] for r in read_jsonl(texts_path)}
    support: dict[tuple[str, str], list[str]] = defaultdict(list)
    key_to_node = {(n["type"], k): n["id"] for n in nodes for k in n["keys"]}
    for m in read_jsonl(e2_dir / "mentions.jsonl"):
        node = key_to_node.get((m["type"], m["key"])) if m["status"] == "kept" else None
        if node and len(support[node]) < 3 and m["paper_id"] not in support[node]:
            support[node].append(m["paper_id"])
    titles = {n["id"]: [texts[p].split("\n")[0] for p in support[n["id"]]] for n in nodes}
    fetcher = Fetcher(RawStore(raw_dir, manifest), min_interval=min_interval)
    output_dir.mkdir(parents=True, exist_ok=True)
    all_links = link_entities(nodes, titles, fetcher, output_dir, device=device)
    write_jsonl(output_dir / "links-all.jsonl", all_links)
    accepted = apply_threshold(all_links, threshold=threshold)
    write_jsonl(output_dir / "links.jsonl", accepted)
    linked_titles = sorted({a["wikipedia_title"] for a in accepted if a["linked"]})
    page_links = fetch_page_links(fetcher, linked_titles)
    (output_dir / "page-links.json").write_text(json.dumps({t: sorted(v) for t, v in page_links.items()}, ensure_ascii=False))
    by_type = Counter(n["type"] for n in nodes)
    linked_by_type = Counter(n["type"] for n, a in zip(nodes, accepted) if a["linked"])
    report = {"nodes_before_link_merge": len(nodes), "linked": sum(a["linked"] for a in accepted), "link_threshold": threshold,
              "linked_by_type": dict(linked_by_type), "nodes_by_type": dict(by_type), "pages_with_links_fetched": len(linked_titles)}
    return report


def organization_enrichment(matches: dict, wikipedia: dict, org_ids: set[str]) -> tuple[dict, dict]:
    """Property additions for v4 organizations plus parent-only Organization nodes (never counted as core)."""
    additions, parents = {}, {}
    qid_to_org = {m["qid"]: org for org, m in matches.items() if org in org_ids}
    for org, match in sorted(matches.items()):
        if org not in org_ids:
            continue
        page = wikipedia.get((match.get("enwiki") or "").rsplit("/wiki/", 1)[-1].replace("_", " "))
        props = {"wikidata_qid": match["qid"], "wikidata_description": match.get("description"), "wikidata_types": match.get("types", []),
                 "wikidata_country": match.get("country"), "wikidata_inception": match.get("inception"), "wikidata_websites": match.get("websites", [])}
        if page:
            props.update({"wikipedia_url": page["url"], "wikipedia_revision_id": page["revision_id"], "wikipedia_page_id": page["page_id"]})
        additions[org] = {k: v for k, v in props.items() if v not in (None, [], "")}
        for parent in match["parents"]:
            if parent["qid"] not in qid_to_org:
                parents.setdefault(parent["qid"], {"id": f"organization:wikidata:{parent['qid']}", "label": "Organization", "name": parent["label"],
                                                   "properties": {"source": "wikidata_parent", "is_core": False, "wikidata_qid": parent["qid"],
                                                                  "layer": "enrichment"}})
    return additions, parents


def frozen_v4_validator(quality_config: Path):
    """The frozen v4 structural validator, applied unchanged to the v4 layer of the enriched graph."""
    import yaml
    from scientific_network.contracts import GraphArtifact
    from scientific_network.graph.validate import validate_graph
    config = yaml.safe_load(quality_config.read_text(encoding="utf-8"))
    derived = config.get("derived", {})

    def check(base: dict) -> list[str]:
        return validate_graph(GraphArtifact.model_validate(base), max_topic_labels=config.get("topics", {}).get("max_labels_per_paper", 3),
                              researcher_min=derived.get("researcher_topic_min_distinct_papers", 2),
                              organization_min=derived.get("organization_topic_min_distinct_papers", 3))
    return check


def run_build_enrichment(e2_dir: Path, link_dir: Path, texts_path: Path, org_wikidata: Path, org_wikipedia: Path, base_graph_path: Path,
                         fetch_manifest: Path, output_dir: Path, config: dict, *, quality_config: Path | None = None) -> dict:
    version = config["config_version"]
    min_papers = config["node_threshold_papers"]
    texts = {r["id"]: r["text"] for r in read_jsonl(texts_path)}
    mentions = read_jsonl(e2_dir / "mentions.jsonl")
    pre_nodes = read_jsonl(e2_dir / "entities.jsonl")
    links = {l["id"]: l for l in read_jsonl(link_dir / "links.jsonl")}
    pairs = json.loads((e2_dir / "merge-map.json").read_text())["pairs"]
    embedding_merge = {(t, a): (t, b) for t, a, b in pairs}
    final = finalize_entities(mentions, embedding_merge, pre_nodes, links, min_papers=min_papers, enrichment_version=version)
    lookup, entity_nodes = final["lookup"], final["nodes"]
    graph_version = "pending"
    paper_edges, paper_ev = paper_entity_edges(mentions, lookup, texts, method_version=version, graph_version=graph_version)
    rel_edges, rel_ev, rel_stats = entity_relation_edges(
        read_jsonl(e2_dir / "paper-relations.jsonl"), lookup, mentions, texts,
        min_papers={"APPLIED_TO": config["relation_thresholds"]["applied_to_min_papers"],
                    "EVALUATED_ON": config["relation_thresholds"]["evaluated_on_min_papers"]},
        method_version=version, graph_version=graph_version)
    base = json.loads(base_graph_path.read_text(encoding="utf-8"))
    org_ids = {n["id"] for n in base["nodes"] if n["label"] == "Organization"}
    wikidata = json.loads(org_wikidata.read_text())
    wikipedia = json.loads(org_wikipedia.read_text())
    additions, parent_nodes = organization_enrichment(wikidata["matches"], wikipedia.get("pages", wikipedia), org_ids)
    sparql = []
    with fetch_manifest.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row["source"] == "wikidata_sparql":
                    sparql.append(row)
    fetch_rows = {"retrieved_at": max((r["retrieved_at"] for r in sparql), default=None),
                  "sha256": sha256("".join(sorted(r["sha256"] for r in sparql)).encode()).hexdigest()}
    part_edges, part_ev = part_of_edges(wikidata["matches"], org_ids, parent_nodes, fetch_rows, method_version=version, graph_version=graph_version)
    used_parents = {e["target_id"] for e in part_edges}
    parent_list = sorted((p for p in parent_nodes.values() if p["id"] in used_parents), key=lambda n: n["id"])
    page_links = {t: set(v) for t, v in json.loads((link_dir / "page-links.json").read_text()).items()}
    linked = {n["id"]: n["properties"]["wikipedia_title"] for n in entity_nodes if n["properties"]["linked"] and n["label"] in ("Method", "Task")}
    paper_entities: dict[str, set[str]] = defaultdict(set)
    for e in paper_edges:
        paper_entities[e["source_id"]].add(e["target_id"])
    related_edges, related_ev, related_stats = related_to_edges(linked, page_links, paper_entities, min_papers=config["relation_thresholds"]["related_to_min_cooccurring_papers"],
                                                                method_version=version, graph_version=graph_version)
    enrichment = {"nodes": entity_nodes + parent_list, "edges": paper_edges + rel_edges + part_edges + related_edges,
                  "evidence": paper_ev + rel_ev + part_ev + related_ev, "node_enrichments": additions}
    graph = build_enriched_graph(base, enrichment, base_file_sha256=sha256(base_graph_path.read_bytes()).hexdigest(), enrichment_version=version)
    output_dir.mkdir(parents=True, exist_ok=True)
    graph_path = output_dir / "graph.json"
    graph_path.write_text(json.dumps(graph, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    errors = validate_enriched(graph, base_validator=frozen_v4_validator(quality_config) if quality_config else None)
    summary = {"graph_version": graph["graph_version"], "base_graph_version": graph["base_graph_version"], "enrichment_version": version,
               "graph_sha256": sha256(graph_path.read_bytes()).hexdigest(), "base_graph_file_sha256": graph["base_graph_file_sha256"],
               "counts": enriched_counts(graph), "relation_stats": {**rel_stats, **related_stats},
               "nodes_below_threshold_after_merge": final["below_threshold"], "validation": {"scope": "structural_only", "errors": errors[:50], "error_count": len(errors),
               "status": "failed" if errors else "passed"}, "semantic_accuracy": "not_measured_by_validation"}
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False, sort_keys=True) + "\n")
    return summary
