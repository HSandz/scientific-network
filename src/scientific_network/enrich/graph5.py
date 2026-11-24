"""v5-enriched graph: the frozen v4 graph plus the enrichment layer (specification §4.4, D042).

The v4 nodes, edges, evidence and affiliation observations are carried over byte-for-byte in meaning:
``validate_enriched`` compares a canonical hash of the v4 layer with the one recorded at build time and
runs the frozen v4 structural validator on it. The enrichment layer adds the labels ``Method``, ``Task``
and ``Dataset``, seven predicates, parent-only Organization nodes (``source: wikidata_parent``,
``is_core: false``) and property additions on existing nodes (``node_enrichments``), none of which
changes a v4 node.
"""

import json
from collections import Counter, defaultdict
from hashlib import sha256

from scientific_network.enrich.relations import edge_id

ENRICH_LABELS = ("Method", "Task", "Dataset")
RELATION_SPEC = {  # relation -> (source labels, target labels, evidence kind)
    "USES_METHOD": ({"Paper"}, {"Method"}, "extracted"),
    "ADDRESSES_TASK": ({"Paper"}, {"Task"}, "extracted"),
    "USES_DATASET": ({"Paper"}, {"Dataset"}, "extracted"),
    "APPLIED_TO": ({"Method"}, {"Task"}, "extracted"),
    "EVALUATED_ON": ({"Method", "Task"}, {"Dataset"}, "extracted"),
    "PART_OF": ({"Organization"}, {"Organization"}, "wikidata"),
    "RELATED_TO": ({"Method", "Task"}, {"Method", "Task"}, "aggregated"),
}
MIN_SUPPORT = {"APPLIED_TO": 2, "EVALUATED_ON": 2, "RELATED_TO": 3}
SCHEMA_VERSION = "0.2.0-enrichment"
V4_EVIDENCE_KINDS = ("observed", "inferred_topic", "curated_taxonomy", "derived")
V4_LAYER_KEYS = ("nodes", "edges", "evidence", "affiliation_observations")


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def v4_layer_sha256(graph: dict) -> str:
    digest = sha256()
    for key in V4_LAYER_KEYS:
        digest.update(key.encode())
        for item in graph.get(key, []):
            digest.update(canonical(item))
    return digest.hexdigest()


def build_enriched_graph(base: dict, enrichment: dict, *, base_file_sha256: str, enrichment_version: str) -> dict:
    """Combine the v4 graph dict with ``enrichment`` = {nodes, edges, evidence, node_enrichments}."""
    layer_sha = v4_layer_sha256(base)
    payload = sha256(layer_sha.encode() + canonical([enrichment["nodes"], enrichment["edges"]])).hexdigest()[:12]
    version = f"enriched-{payload}"
    edges = [{**e, "graph_version": version} for e in enrichment["edges"]]
    # edge IDs do not contain the graph version, so they stay valid after the version is stamped
    return {
        "schema_version": SCHEMA_VERSION, "graph_version": version, "base_graph_version": base["graph_version"],
        "base_graph_file_sha256": base_file_sha256, "base_layer_sha256": layer_sha, "enrichment_version": enrichment_version,
        "is_synthetic": False,
        "nodes": base["nodes"] + enrichment["nodes"], "edges": base["edges"] + edges,
        "evidence": base["evidence"] + enrichment["evidence"],
        "affiliation_observations": base["affiliation_observations"],
        "node_enrichments": enrichment.get("node_enrichments", {}),
    }


def split_layers(graph: dict) -> tuple[dict, dict]:
    """(v4 layer as a v4-shaped dict, enrichment layer)."""
    base_version = graph["base_graph_version"]
    enrich_labels = set(ENRICH_LABELS)
    v4_nodes = [n for n in graph["nodes"] if n["label"] in set(("Researcher", "Organization", "Paper", "Topic", "Venue"))
                and not (n.get("properties") or {}).get("source") == "wikidata_parent"]
    v4_edges = [e for e in graph["edges"] if e.get("graph_version") == base_version]
    v4_ids = {e["id"] for e in graph["evidence"] if e.get("kind") in V4_EVIDENCE_KINDS}
    base = {"schema_version": "0.1.0", "graph_version": base_version, "is_synthetic": False, "nodes": v4_nodes, "edges": v4_edges,
            "evidence": [e for e in graph["evidence"] if e["id"] in v4_ids],
            "affiliation_observations": graph["affiliation_observations"]}
    enrich = {"nodes": [n for n in graph["nodes"] if n["label"] in enrich_labels or (n.get("properties") or {}).get("source") == "wikidata_parent"],
              "edges": [e for e in graph["edges"] if e["relation"] in RELATION_SPEC],
              "evidence": [e for e in graph["evidence"] if e["id"] not in v4_ids]}
    return base, enrich


def node_id_for(node: dict) -> str:
    from scientific_network.enrich.entities import entity_id
    props = node.get("properties") or {}
    if props.get("linked") and props.get("wikidata_qid"):
        return f"{node['label'].lower()}:{props['wikidata_qid']}"
    return entity_id(node["label"], props.get("key", ""))


def validate_enriched(graph: dict, *, base_validator=None) -> list[str]:
    """Structural checks for the enrichment layer and for the integrity of the v4 layer. Not a semantic accuracy claim."""
    errors: list[str] = []
    if graph.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"unexpected schema_version {graph.get('schema_version')!r}")
    base, enrich = split_layers(graph)
    if v4_layer_sha256(base) != graph.get("base_layer_sha256"):
        errors.append("v4 layer differs from the base layer recorded at build time")
    if base_validator is not None:
        errors.extend(f"v4 layer: {e}" for e in base_validator(base))
    for kind, items, key in (("node", graph["nodes"], "id"), ("edge", graph["edges"], "edge_id"), ("evidence", graph["evidence"], "id")):
        errors.extend(f"duplicate {kind} ID: {k}" for k, c in Counter(i[key] for i in items).items() if c > 1)
    nodes = {n["id"]: n for n in graph["nodes"]}
    evidence = {e["id"]: e for e in graph["evidence"]}
    version, method_versions = graph["graph_version"], set()
    paper_counts: Counter[str] = Counter()
    for node in enrich["nodes"]:
        props = node.get("properties") or {}
        if node["label"] in ENRICH_LABELS:
            if node["id"] != node_id_for(node):
                errors.append(f"{node['id']}: ID is not the deterministic ID for its type and QID/name")
            if props.get("paper_count", 0) < 3:
                errors.append(f"{node['id']}: fewer than 3 supporting papers")
            if bool(props.get("linked")) != bool(props.get("wikidata_qid")):
                errors.append(f"{node['id']}: linked flag and wikidata_qid disagree")
        elif props.get("source") != "wikidata_parent" or props.get("is_core") is not False:
            errors.append(f"{node['id']}: added Organization must be a non-core wikidata_parent node")
    papers_by_edge: dict[str, set[str]] = defaultdict(set)
    for edge in enrich["edges"]:
        spec = RELATION_SPEC[edge["relation"]]
        source, target = nodes.get(edge["source_id"]), nodes.get(edge["target_id"])
        if source is None or target is None:
            errors.append(f"{edge['edge_id']}: dangling endpoint")
            continue
        if source["label"] not in spec[0] or target["label"] not in spec[1]:
            errors.append(f"{edge['edge_id']}: {edge['relation']} endpoints {source['label']}->{target['label']} not allowed")
        if edge["evidence_kind"] != spec[2]:
            errors.append(f"{edge['edge_id']}: evidence kind {edge['evidence_kind']} != {spec[2]}")
        if edge["edge_id"] != edge_id(edge["relation"], edge["source_id"], edge["target_id"], edge["method_version"]):
            errors.append(f"{edge['edge_id']}: edge ID is not deterministic")
        if edge["graph_version"] != version or edge.get("validation_status") != "accepted":
            errors.append(f"{edge['edge_id']}: graph version or status")
        method_versions.add(edge["method_version"])
        if not edge["evidence_ids"] or any(r not in evidence for r in edge["evidence_ids"]):
            errors.append(f"{edge['edge_id']}: evidence missing or unresolved")
        props = edge.get("properties", {})
        minimum = MIN_SUPPORT.get(edge["relation"])
        if minimum and (props.get("support_count", 0) < minimum or len(props.get("support_paper_ids", [])) != props.get("support_count")):
            errors.append(f"{edge['edge_id']}: support below {minimum} papers or inconsistent")
        if edge["relation"] in ("USES_METHOD", "ADDRESSES_TASK", "USES_DATASET"):
            paper_counts[edge["target_id"]] += 1
            if source["label"] == "Paper" and not (source.get("properties") or {}).get("is_core"):
                errors.append(f"{edge['edge_id']}: source paper is not a core paper")
            if any(evidence[r].get("paper_id") != edge["source_id"] for r in edge["evidence_ids"] if r in evidence):
                errors.append(f"{edge['edge_id']}: evidence is from another paper")
        if edge["relation"] in ("APPLIED_TO", "EVALUATED_ON"):
            papers_by_edge[edge["edge_id"]] = set(props.get("support_paper_ids", []))
            if any(evidence[r].get("paper_id") not in papers_by_edge[edge["edge_id"]] for r in edge["evidence_ids"] if r in evidence):
                errors.append(f"{edge['edge_id']}: evidence paper not in support list")
    for node in enrich["nodes"]:
        if node["label"] in ENRICH_LABELS and paper_counts[node["id"]] != (node.get("properties") or {}).get("paper_count"):
            errors.append(f"{node['id']}: paper_count {node['properties'].get('paper_count')} != {paper_counts[node['id']]} paper edges")
    for node_id in graph.get("node_enrichments", {}):
        if node_id not in nodes or nodes[node_id]["label"] != "Organization":
            errors.append(f"node_enrichments target {node_id} is not an Organization")
    if len(method_versions) > 1:
        errors.append(f"several method versions in one build: {sorted(method_versions)}")
    return errors


def enriched_counts(graph: dict) -> dict:
    """v4 layer, enrichment layer by evidence kind, and totals, reported separately."""
    base, enrich = split_layers(graph)
    return {
        "v4_layer": {"nodes": len(base["nodes"]), "edges": len(base["edges"]),
                     "nodes_by_label": dict(Counter(n["label"] for n in base["nodes"])),
                     "edges_by_relation": dict(Counter(e["relation"] for e in base["edges"]))},
        "enrichment_layer": {"nodes": len(enrich["nodes"]), "edges": len(enrich["edges"]),
                             "nodes_by_label": dict(Counter(n["label"] for n in enrich["nodes"])),
                             "edges_by_relation": dict(Counter(e["relation"] for e in enrich["edges"])),
                             "edges_by_evidence_kind": dict(Counter(e["evidence_kind"] for e in enrich["edges"])),
                             "linked_entities": sum(1 for n in enrich["nodes"] if (n.get("properties") or {}).get("linked")),
                             "organizations_enriched": len(graph.get("node_enrichments", {}))},
        "total": {"nodes": len(graph["nodes"]), "edges": len(graph["edges"]), "evidence": len(graph["evidence"])},
    }
