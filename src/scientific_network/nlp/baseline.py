"""Uncalibrated phrase baseline with literal title/abstract spans and abstention."""

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re

from scientific_network.collect.storage import SourceCache, digest, read_config, write_bytes, write_json
from scientific_network.contracts import GraphArtifact, Node, Edge, EvidenceRecord
from scientific_network.graph.schema import edge_id
from scientific_network.graph.materialize import materialize
from scientific_network.graph.validate import validate_graph, graph_counts


METHOD = "literal-phrase-baseline-v2-text-provenance"


def predict(text: str, taxonomy: dict) -> tuple[list[dict], str]:
    candidates = []
    for topic in taxonomy["leaves"]:
        matches = []
        for phrase in topic["synonyms"]:
            pattern = r"(?<!\w)" + re.escape(phrase).replace(r"\ ", r"\s+") + r"(?!\w)"
            match = re.search(pattern, text, re.I)
            if match:
                matches.append(match)
        if matches:
            match = min(matches, key=lambda m: (m.start(), -len(m.group())))
            candidates.append({"topic_id": topic["id"], "start": match.start(), "end": match.end(), "excerpt": match.group()})
    if not candidates:
        return [], "abstain_no_supported_phrase"
    if len(candidates) > taxonomy["annotation"]["max_labels"]:
        return [], "abstain_too_many_candidate_labels"
    return candidates, "phrase_baseline_unvalidated"


def classify(input_path: Path, config_path: Path, quality_path: Path, output: Path, cache_path: Path) -> dict:
    graph = GraphArtifact.model_validate_json(input_path.read_bytes())
    if any(e.relation in {"HAS_TOPIC", "SUBTOPIC_OF"} for e in graph.edges):
        raise ValueError("classify expects a base graph without topic assignments")
    taxonomy, quality = read_config(config_path), read_config(quality_path)
    graph.graph_version = "pilot-topic-" + digest(METHOD.encode() + input_path.read_bytes() + config_path.read_bytes() + quality_path.read_bytes())[:12]
    for e in graph.edges:
        e.graph_version = graph.graph_version
    taxonomy_bytes = config_path.read_bytes()
    taxonomy_hash = digest(taxonomy_bytes)
    taxonomy_record_path = cache_path / "requests" / f"taxonomy-{taxonomy_hash}.json"
    write_bytes(cache_path / "objects" / taxonomy_hash, taxonomy_bytes)
    if not taxonomy_record_path.exists():
        write_json(taxonomy_record_path, {"retrieved_at": datetime.now(timezone.utc).isoformat()})
    retrieved = json.loads(taxonomy_record_path.read_text())["retrieved_at"]
    source_url = "https://ai-research-network-plan.hazy-tern-8113.chatgpt.site"
    for topic in taxonomy["parents"] + taxonomy["leaves"]:
        level = "leaf" if "parent_id" in topic else "parent"
        graph.nodes.append(Node(id=topic["id"], label="Topic", name=topic["name"],
            properties={"level": level, "taxonomy_version": taxonomy["version"],
                "definition": topic.get("definition", "Parent grouping"), "taxonomy_status": taxonomy["status"]}))
        if level == "leaf":
            identifier = edge_id("SUBTOPIC_OF", topic["id"], topic["parent_id"])
            evidence_id = "evidence:taxonomy:" + digest(f"{taxonomy_hash}|{topic['id']}".encode())
            graph.evidence.append(EvidenceRecord(id=evidence_id, kind="curated_taxonomy", source_url=source_url,
                retrieved_at=retrieved, raw_sha256=taxonomy_hash,
                source_locator=f"{config_path}#leaves[id={topic['id']}]"))
            graph.edges.append(Edge(edge_id=identifier, relation="SUBTOPIC_OF", source_id=topic["id"],
                target_id=topic["parent_id"], evidence_kind="curated_taxonomy", evidence_ids=[evidence_id],
                method_version=taxonomy["version"], graph_version=graph.graph_version, validation_status="accepted"))
    by_evidence = {e.id: e for e in graph.evidence}
    by_venue_edge = {e.source_id: e for e in graph.edges if e.relation == "PUBLISHED_IN"}
    decisions = []
    for paper in graph.nodes:
        if paper.label != "Paper" or paper.properties.get("is_core") is not True:
            continue
        text = paper.name + "\n" + paper.properties.get("abstract", "")
        predictions, reason = predict(text, taxonomy)
        decisions.append({"paper_id": paper.id, "decision": reason, "labels": predictions})
        base = by_evidence[paper.properties.get("topic_text_evidence_id", by_venue_edge[paper.id].evidence_ids[0])]
        for prediction in predictions:
            if text[prediction["start"]:prediction["end"]] != prediction["excerpt"]:
                raise ValueError("topic evidence is not a literal input span")
            identifier = edge_id("HAS_TOPIC", paper.id, prediction["topic_id"])
            evidence_id = "evidence:topic:" + identifier.removeprefix("edge:")
            graph.evidence.append(EvidenceRecord(id=evidence_id, kind="inferred_topic", source_url=base.source_url,
                retrieved_at=base.retrieved_at, raw_sha256=base.raw_sha256,
                source_locator=f"{base.source_locator};normalized_title+abstract[{prediction['start']}:{prediction['end']}]", excerpt=prediction["excerpt"]))
            graph.edges.append(Edge(edge_id=identifier, relation="HAS_TOPIC", source_id=paper.id,
                target_id=prediction["topic_id"], evidence_kind="inferred_topic", evidence_ids=[evidence_id],
                method_version=METHOD, graph_version=graph.graph_version,
                validation_status="accepted", properties={"evaluation_status": "uncalibrated_baseline"}))
    graph = materialize(graph, quality["derived"]["researcher_topic_min_distinct_papers"],
        quality["derived"]["organization_topic_min_distinct_papers"])
    errors = validate_graph(graph, require_derived=True,
        researcher_min=quality["derived"]["researcher_topic_min_distinct_papers"],
        organization_min=quality["derived"]["organization_topic_min_distinct_papers"])
    if errors:
        raise ValueError("topic graph failed structure: " + "; ".join(errors[:5]))
    graph.nodes.sort(key=lambda n: n.id)
    write_json(output, json.loads(graph.model_dump_json()))
    write_json(output.with_suffix(".topics.json"), decisions)
    summary = {"stage": "classify", "graph_version": graph.graph_version,
        "input_sha256": digest(input_path.read_bytes()), "taxonomy_sha256": taxonomy_hash,
        "counts": graph_counts(graph), "paper_decisions": dict(Counter(d["decision"] for d in decisions)),
        "semantic_accuracy": "not_measured", "method": "uncalibrated_phrase_baseline", "release_eligible": False}
    write_json(output.with_suffix(".summary.json"), summary)
    return summary
