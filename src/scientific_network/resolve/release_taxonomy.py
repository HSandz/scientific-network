"""Synchronize release taxonomy and correct frozen metadata without inference."""

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

from scientific_network.collect.storage import read_config, write_bytes, write_json
from scientific_network.contracts import Edge, EvidenceRecord, GraphArtifact, Node
from scientific_network.graph.schema import edge_id
from scientific_network.graph.validate import graph_counts, validate_graph
from scientific_network.resolve.release import TAXONOMY_SOURCE_URL

CORRECTION_METHOD = "release-taxonomy-metadata-correction-v1"


def taxonomy_components(taxonomy_path: Path, graph_version: str, retrieved_at: str):
    """Construct every taxonomy claim from the same frozen source bytes."""
    taxonomy = read_config(taxonomy_path)
    if taxonomy.get("status") != "frozen":
        raise ValueError("release taxonomy must be frozen")
    digest = sha256(taxonomy_path.read_bytes()).hexdigest()
    nodes, edges, evidence = [], [], []
    for group, level in (("parents", "parent"), ("leaves", "leaf")):
        for topic in taxonomy[group]:
            properties = {key: value for key, value in topic.items() if key not in {"id", "name"}}
            properties.update(level=level, taxonomy_version=taxonomy["version"],
                              taxonomy_status=taxonomy["status"],
                              definition=topic.get("definition", "Parent grouping"))
            nodes.append(Node(id=topic["id"], label="Topic", name=topic["name"], properties=properties))
            if level == "leaf":
                record = EvidenceRecord(
                    id="evidence:taxonomy:" + sha256(f"{digest}\0{topic['id']}".encode()).hexdigest()[:24],
                    kind="curated_taxonomy", source_url=TAXONOMY_SOURCE_URL,
                    retrieved_at=retrieved_at, raw_sha256=digest,
                    source_locator=f"{taxonomy_path}#leaves[id={topic['id']}]",
                )
                evidence.append(record)
                edges.append(Edge(
                    edge_id=edge_id("SUBTOPIC_OF", topic["id"], topic["parent_id"]),
                    relation="SUBTOPIC_OF", source_id=topic["id"], target_id=topic["parent_id"],
                    evidence_kind="curated_taxonomy", evidence_ids=[record.id],
                    method_version=taxonomy["version"], graph_version=graph_version,
                    validation_status="accepted",
                ))
    return nodes, edges, evidence


def synchronize_taxonomy(graph: GraphArtifact, taxonomy_path: Path, graph_version: str) -> GraphArtifact:
    # Source-read time is carried forward to keep this metadata correction deterministic.
    timestamps = [r.retrieved_at for r in graph.evidence if r.kind == "curated_taxonomy"]
    if not timestamps:
        raise ValueError("input graph lacks taxonomy source-read provenance")
    nodes, edges, evidence = taxonomy_components(taxonomy_path, graph_version, min(timestamps))
    return graph.model_copy(update={
        "graph_version": graph_version,
        "nodes": sorted([n for n in graph.nodes if n.label != "Topic"] + nodes, key=lambda n: n.id),
        "edges": sorted([e.model_copy(update={"graph_version": graph_version}) for e in graph.edges
                         if e.relation != "SUBTOPIC_OF"] + edges, key=lambda e: e.edge_id),
        "evidence": sorted([r for r in graph.evidence if r.kind != "curated_taxonomy"] + evidence,
                           key=lambda r: r.id),
    })


def validate_taxonomy(graph: GraphArtifact, taxonomy_path: Path) -> list[str]:
    """Semantic/provenance check beyond structural validation; compare source content."""
    records = [r for r in graph.evidence if r.kind == "curated_taxonomy"]
    if not records:
        return ["taxonomy evidence missing"]
    expected = taxonomy_components(taxonomy_path, graph.graph_version, min(r.retrieved_at for r in records))
    actual = ([n for n in graph.nodes if n.label == "Topic"],
              [e for e in graph.edges if e.relation == "SUBTOPIC_OF"], records)
    errors = []
    for label, given, wanted in zip(("nodes", "hierarchy", "evidence"), actual, expected):
        key = (lambda item: item.edge_id) if label == "hierarchy" else (lambda item: item.id)
        # Evidence timestamps may differ between source reads; content and locators may not.
        def content(item):
            return item.model_dump(mode="json", exclude={"retrieved_at"} if label == "evidence" else set())
        if [content(i) for i in sorted(given, key=key)] != [content(i) for i in sorted(wanted, key=key)]:
            errors.append(f"taxonomy {label} differ from frozen source config")
    return errors


def _canonical(value) -> str:
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def compare_correction(old: GraphArtifact, new: GraphArtifact) -> dict:
    """Fail closed on every non-taxonomy change, including prediction evidence/weights."""
    def invariant(graph):
        return {
            "entity_identities": sorted((n.id, n.label) for n in graph.nodes),
            "non_topic_nodes": [n.model_dump(mode="json") for n in sorted(graph.nodes, key=lambda n: n.id) if n.label != "Topic"],
            "semantic_edges": sorted((e.edge_id, e.relation, e.source_id, e.target_id) for e in graph.edges),
            "non_taxonomy_edges": [e.model_dump(mode="json", exclude={"graph_version"}) for e in sorted(graph.edges, key=lambda e: e.edge_id)
                                   if e.relation != "SUBTOPIC_OF"],
            "non_taxonomy_evidence": [r.model_dump(mode="json") for r in sorted(graph.evidence, key=lambda r: r.id)
                                      if r.kind != "curated_taxonomy"],
            "affiliation_observations": [r.model_dump(mode="json") for r in graph.affiliation_observations],
        }
    before, after = invariant(old), invariant(new)
    digests = {}
    for key in before:
        a, b = _canonical(before[key]), _canonical(after[key])
        if a != b:
            raise ValueError(f"unintended taxonomy correction difference: {key}")
        digests[key] = {"before_sha256": a, "after_sha256": b, "equal": True}
    if any(e.graph_version != new.graph_version for e in new.edges) or new.graph_version == old.graph_version:
        raise ValueError("correction must create a new identity and stamp every edge")
    old_topics = {n.id: n for n in old.nodes if n.label == "Topic"}
    return {
        "status": "preserved", "invariants": digests,
        "nodes": len(new.nodes), "edges": len(new.edges),
        "relations": dict(sorted(Counter(e.relation for e in new.edges).items())),
        "changed_topic_node_ids": [n.id for n in new.nodes if n.label == "Topic" and n != old_topics[n.id]],
        "intended_changes": ["Topic source properties, version and status", "taxonomy evidence IDs, hashes and locators",
                             "SUBTOPIC_OF provenance", "every edge graph_version"],
        "predictions_excerpts_scores_core_facts_support_sets_counts_weights": "byte-equivalent canonical content",
    }


def correct_release_taxonomy(input_path: Path, taxonomy_path: Path, quality_path: Path,
                             source_summary_path: Path, source_freeze_path: Path,
                             output_dir: Path, summary_path: Path) -> dict:
    """Create a new release graph from frozen predictions; never load a model."""
    if output_dir.exists() or output_dir.is_symlink() or summary_path.exists() or summary_path.is_symlink():
        raise ValueError("correction outputs must use unused versioned paths")
    sources = {"source_graph": input_path, "taxonomy": taxonomy_path, "quality": quality_path,
               "source_summary": source_summary_path, "source_freeze": source_freeze_path}
    hashes = {key: sha256(path.read_bytes()).hexdigest() for key, path in sources.items()}
    freeze = json.loads(source_freeze_path.read_bytes())
    summary = json.loads(source_summary_path.read_bytes())
    if hashes["source_graph"] != freeze["graph_sha256"] or hashes["source_graph"] != summary["graph_sha256"]:
        raise ValueError("source graph differs from frozen graph/summary")
    for path, key in ((taxonomy_path, "taxonomy"), (quality_path, "quality")):
        if freeze["config_hashes"].get(str(path)) != hashes[key]:
            raise ValueError("correction cannot change frozen classifier or quality config")
    old = GraphArtifact.model_validate_json(input_path.read_bytes())
    if old.is_synthetic or old.graph_version != freeze["graph_version"]:
        raise ValueError("correction requires the frozen real release graph")
    version = "release-" + _canonical([CORRECTION_METHOD, hashes])[:12]
    graph = synchronize_taxonomy(old, taxonomy_path, version)
    preservation = compare_correction(old, graph)
    quality = read_config(quality_path)
    errors = validate_taxonomy(graph, taxonomy_path) + validate_graph(
        graph, require_derived=True, max_topic_labels=quality["topics"]["max_labels_per_paper"],
        researcher_min=quality["derived"]["researcher_topic_min_distinct_papers"],
        organization_min=quality["derived"]["organization_topic_min_distinct_papers"])
    if errors:
        raise ValueError("corrected graph validation failed: " + "; ".join(errors[:10]))
    output_dir.mkdir(parents=True)
    graph_path = output_dir / "graph.json"
    write_bytes(graph_path, (graph.model_dump_json() + "\n").encode())
    result = {
        **summary, "stage": "release-taxonomy-correction", "method_version": CORRECTION_METHOD,
        "topic_classifier_method_version": summary["method_version"],
        "graph_version": version, "graph_sha256": sha256(graph_path.read_bytes()).hexdigest(),
        "correction_inputs": {key: {"path": str(sources[key]), "sha256": value} for key, value in hashes.items()},
        "supersedes_graph_version": old.graph_version, "preservation": preservation,
        "counts": graph_counts(graph), "structural_validation": "passed", "taxonomy_validation": "passed",
        "computation": "deterministic metadata correction; no model inference; coverage/calibration carried forward unchanged",
    }
    # The source timestamp describes the original inference, not this correction.
    result["source_created_at"] = result.pop("created_at", None)
    write_json(summary_path, result)
    return result
