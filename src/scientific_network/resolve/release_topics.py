"""Build release graph v2 with frozen embedding topics (D040 Phase 5)."""

from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from scientific_network.collect.storage import read_config, read_jsonl, write_bytes, write_json
from scientific_network.contracts import Edge, EvidenceRecord, GraphArtifact
from scientific_network.graph.materialize import materialize
from scientific_network.graph.schema import edge_id
from scientific_network.graph.validate import graph_counts, validate_graph
from scientific_network.nlp.embeddings import load_sentence_model, predict_topics
from scientific_network.resolve.release import METHOD_VERSION as GRAPH_V1_METHOD, _roster_evidence, _work_evidence


def _digest(*parts: str) -> str:
    return hashlib.sha256("\0".join(parts).encode("utf-8")).hexdigest()


def build_release_graph_v2(
    graph_v1_path: Path,
    works_path: Path,
    taxonomy_path: Path,
    quality_path: Path,
    output_dir: Path,
    summary_path: Path,
    *,
    model=None,
) -> dict:
    """Replace v1 topic edges, recompute derivations, validate, and write a new graph."""
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError("release graph v2 output directory is not empty; use a new versioned directory")
    taxonomy = read_config(taxonomy_path)
    quality = read_config(quality_path)
    if taxonomy.get("status") != "frozen":
        raise ValueError("release graph v2 requires a frozen topic config")
    model_config = taxonomy.get("model", {})
    thresholds = model_config.get("thresholds") or {}
    tau, delta = thresholds.get("tau"), thresholds.get("delta")
    if not isinstance(tau, (int, float)) or not isinstance(delta, (int, float)):
        raise ValueError("frozen topic config requires numeric tau and delta")
    if taxonomy.get("test_manifest") is None:
        raise ValueError("frozen topic config must identify its reserved test manifest")
    topic_test_path = Path(taxonomy["test_manifest"])
    topic_test_bytes = topic_test_path.read_bytes()
    topic_test_rows = [json.loads(line) for line in topic_test_bytes.splitlines() if line.strip()]
    if len(topic_test_rows) != 50 or len({row.get("paper_id") for row in topic_test_rows}) != 50:
        raise ValueError("frozen topic test manifest must contain 50 unique papers")
    calibration = taxonomy.get("calibration") or {}
    if calibration.get("topic_test_sha256") != hashlib.sha256(topic_test_bytes).hexdigest():
        raise ValueError("frozen taxonomy calibration does not bind to the current topic test manifest")
    if calibration.get("tau") != tau or calibration.get("delta") != delta:
        raise ValueError("frozen taxonomy thresholds differ from the development calibration record")

    graph_raw = graph_v1_path.read_bytes()
    graph_v1 = GraphArtifact.model_validate_json(graph_raw)
    if graph_v1.is_synthetic:
        raise ValueError("synthetic graphs cannot be used to build release graph v2")
    if not graph_v1.graph_version.startswith("release-"):
        raise ValueError("graph v1 input does not have a release graph version")
    rows = read_jsonl(works_path)
    works_hash = hashlib.sha256(works_path.read_bytes()).hexdigest()
    if calibration.get("works_sha256") != works_hash:
        raise ValueError("frozen taxonomy calibration does not bind to the current works input")
    paper_nodes = {node.id for node in graph_v1.nodes if node.label == "Paper" and node.properties.get("is_core") is True}
    work_ids = {row["paper_id"] for row in rows}
    if paper_nodes != work_ids:
        raise ValueError("graph v1 core-paper IDs do not exactly match the works input")
    inputs = {
        "graph_v1_sha256": hashlib.sha256(graph_raw).hexdigest(),
        "works_sha256": works_hash,
        "taxonomy_sha256": hashlib.sha256(taxonomy_path.read_bytes()).hexdigest(),
        "quality_sha256": hashlib.sha256(quality_path.read_bytes()).hexdigest(),
        "topic_test_sha256": hashlib.sha256(topic_test_bytes).hexdigest(),
    }
    method_version = "release-embedding-topics-v1"
    construction_version = "release-embedding-graph-taxonomy-sync-v2"
    graph_version = "release-" + _digest(construction_version, method_version, graph_v1.graph_version, *inputs.values())[:12]
    if model is None:
        model = load_sentence_model(taxonomy)
    documents = [{
        "paper_id": row["paper_id"], "title": row["roster"]["title"],
        "abstract": (row.get("openalex") or {}).get("abstract") if row["match"]["status"] == "matched" else None,
    } for row in rows]
    predictions = predict_topics(documents, taxonomy, model, tau=float(tau), delta=float(delta),
                                 batch_size=int(model_config.get("batch_size", 64)))
    prediction_by_id = {row["paper_id"]: row for row in predictions}

    nodes = []
    for node in graph_v1.nodes:
        if node.label == "Paper":
            prediction = prediction_by_id[node.id]
            properties = {**node.properties, "topic_text": "title_and_abstract" if prediction["text_source"] == "abstract" else "title_only"}
            nodes.append(node.model_copy(update={"properties": properties}))
        else:
            nodes.append(node)

    edges = []
    for edge in graph_v1.edges:
        if edge.relation == "HAS_TOPIC" or edge.evidence_kind == "derived":
            continue
        edges.append(edge.model_copy(update={"graph_version": graph_version}))
    evidence_by_id = {
        record.id: record for record in graph_v1.evidence
        if record.kind not in {"inferred_topic", "derived"}
    }
    topic_decisions = Counter()
    topic_by_venue_year: dict[str, dict[str, Counter]] = defaultdict(lambda: defaultdict(Counter))
    for row in rows:
        paper_id = row["paper_id"]
        document_result = prediction_by_id[paper_id]
        topic_decisions[document_result["decision"]] += 1
        year_counts = topic_by_venue_year[row["venue_id"]][str(row["year"])]
        year_counts["eligible"] += 1
        year_counts["labeled"] += bool(document_result["predictions"])
        base = _work_evidence(row) if row["match"]["status"] == "matched" else _roster_evidence(row)
        for prediction in document_result["predictions"]:
            identifier = edge_id("HAS_TOPIC", paper_id, prediction["topic_id"])
            evidence_id = "evidence:topic:" + identifier.removeprefix("edge:")
            source_locator = f"{base.source_locator};{prediction['text_source']}[{prediction['start']}:{prediction['end']}]"
            evidence_by_id[evidence_id] = EvidenceRecord(
                id=evidence_id, kind="inferred_topic", source_url=base.source_url,
                retrieved_at=base.retrieved_at, raw_sha256=base.raw_sha256,
                source_locator=source_locator, excerpt=prediction["excerpt"],
            )
            edges.append(Edge(
                edge_id=identifier, relation="HAS_TOPIC", source_id=paper_id,
                target_id=prediction["topic_id"], evidence_kind="inferred_topic",
                evidence_ids=[evidence_id], method_version=method_version,
                graph_version=graph_version, validation_status="accepted",
                properties={
                    "cosine_similarity": prediction["similarity"],
                    "threshold_tau": float(tau), "margin_delta": float(delta),
                    "text_source": prediction["text_source"],
                    "evaluation_status": "human_review_pending",
                },
            ))

    graph = GraphArtifact(
        graph_version=graph_version, is_synthetic=False, nodes=sorted(nodes, key=lambda item: item.id),
        edges=sorted(edges, key=lambda item: item.edge_id),
        evidence=sorted(evidence_by_id.values(), key=lambda item: item.id),
        affiliation_observations=graph_v1.affiliation_observations,
    )
    from scientific_network.resolve.release_taxonomy import synchronize_taxonomy, validate_taxonomy
    graph = synchronize_taxonomy(graph, taxonomy_path, graph_version)
    taxonomy_errors = validate_taxonomy(graph, taxonomy_path)
    if taxonomy_errors:
        raise ValueError("; ".join(taxonomy_errors))
    researcher_min = quality["derived"]["researcher_topic_min_distinct_papers"]
    organization_min = quality["derived"]["organization_topic_min_distinct_papers"]
    graph = materialize(graph, researcher_min, organization_min)
    errors = validate_graph(
        graph, max_topic_labels=quality["topics"]["max_labels_per_paper"], require_derived=True,
        researcher_min=researcher_min, organization_min=organization_min,
    )
    if errors:
        raise ValueError("release graph v2 failed structural validation: " + "; ".join(errors[:5]))

    output_dir.mkdir(parents=True, exist_ok=True)
    graph_path = output_dir / "graph.json"
    write_bytes(graph_path, (graph.model_dump_json() + "\n").encode("utf-8"))
    counts = graph_counts(graph)
    summary = {
        "stage": "release-topic-graph", "method_version": method_version,
        "base_graph_method_version": GRAPH_V1_METHOD,
        "construction_version": construction_version, "taxonomy_validation": "passed",
        "model": {key: model_config.get(key) for key in ("name", "revision", "device")},
        "thresholds": {"tau": float(tau), "delta": float(delta)},
        "development_calibration": {
            key: calibration.get(key) for key in (
                "target_coverage", "observed_coverage", "development_papers", "sample_seed", "sample_size",
            )
        },
        "graph_v1_version": graph_v1.graph_version, "graph_version": graph_version,
        "inputs_sha256": inputs, "graph_sha256": hashlib.sha256(graph_path.read_bytes()).hexdigest(),
        "counts": json.loads(json.dumps(counts, default=str)),
        "coverage": {
            "eligible_papers": len(rows),
            "papers_with_abstract": sum(bool((row.get("openalex") or {}).get("abstract")) for row in rows if row["match"]["status"] == "matched"),
            "papers_topic_labeled": topic_decisions["labeled"],
            "papers_topic_abstained": topic_decisions["abstain"],
            "topic_coverage": topic_decisions["labeled"] / len(rows) if rows else 0.0,
            "topic_labeled_by_venue_year": {
                venue: {year: dict(sorted(values.items())) for year, values in sorted(years.items())}
                for venue, years in sorted(topic_by_venue_year.items())
            },
        },
        "topic_decisions": dict(sorted(topic_decisions.items())),
        "structural_validation": "passed", "semantic_accuracy": "not_measured",
        "test_predictions_computed_after_classifier_freeze": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    write_json(summary_path, summary)
    return summary
