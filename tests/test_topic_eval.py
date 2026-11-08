"""Topic review scoring uses all assigned judgments and keeps overlap visible."""

import csv
from hashlib import sha256
import json
from pathlib import Path

import pytest
import yaml

from scientific_network.contracts import Edge, GraphArtifact, Node
from scientific_network.evaluation.topic_eval import (
    _agreement,
    _read_topic_labels,
    _score_annotations,
    score_topic_review,
)
from scientific_network.evaluation.topic_review import FIELDS, assign_topic_reviewers


def test_paper_normalized_topic_metrics_weight_overlap_judgments_and_abstentions():
    annotations = [
        ("paper:shared", {"topic:a"}, 0.5),
        ("paper:shared", set(), 0.5),
        ("paper:single", set(), 1.0),
    ]
    predictions = {
        "paper:shared": {"topic:a"},
        "paper:single": {"topic:b"},
    }

    result = _score_annotations(annotations, predictions, ["topic:a", "topic:b"])

    assert result["annotation_rows"] == 3
    assert result["effective_paper_weight"] == 2.0
    assert result["micro"] == {
        "true_positive": 0.5,
        "false_positive": 1.5,
        "false_negative": 0.0,
        "precision": 0.25,
        "recall": 1.0,
        "f1": 0.4,
    }
    assert result["per_label"]["topic:a"]["gold_support"] == 0.5
    assert result["per_label"]["topic:b"]["gold_support"] == 0.0


def test_topic_agreement_is_computed_only_on_overlap():
    labels_a = {"paper:1": {"topic:a"}, "paper:2": set()}
    labels_b = {"paper:1": {"topic:a"}, "paper:2": {"topic:b"}}

    result = _agreement(["paper:1", "paper:2"], labels_a, labels_b, ["topic:a", "topic:b"])

    assert result["overlap_paper_count"] == 2
    assert result["exact_set_agreement_count"] == 1
    assert result["exact_set_agreement_fraction"] == 0.5
    assert result["mean_jaccard"] == 0.5
    assert result["per_topic"]["topic:a"]["cohen_kappa"] == 1.0


def test_empty_topic_set_requires_an_explicit_review_note(tmp_path):
    master_row = {
        "paper_id": "paper:1", "venue_id": "venue:aaai", "year": "2025",
        "title": "Title", "abstract": "Abstract", "topic_catalog": "[]",
        "label_1": "", "label_2": "", "label_3": "", "labeler": "", "notes": "",
    }
    packet = tmp_path / "review.csv"
    with packet.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerow({**master_row, "labeler": "A"})

    with pytest.raises(ValueError, match="explain an empty label set"):
        _read_topic_labels(
            packet,
            reviewer="A",
            expected_ids={"paper:1"},
            master_rows={"paper:1": master_row},
            allowed_topics={"topic:a"},
        )


def test_frozen_topic_evaluator_compares_both_graphs_with_paper_normalized_labels(tmp_path):
    paper_rows = [
        {"paper_id": f"paper:aaai:{index}", "venue_id": "venue:aaai"}
        for index in range(20)
    ] + [
        {"paper_id": f"paper:ijcai:{index}", "venue_id": "venue:ijcai"}
        for index in range(30)
    ]
    test_path = tmp_path / "topic-test.jsonl"
    test_path.write_text(
        "".join(json.dumps({"paper_id": row["paper_id"], "seed": 20261108}) + "\n" for row in paper_rows),
        encoding="utf-8",
    )
    topic_ids = [f"topic:{index}" for index in range(16)]
    catalog = [{"id": topic_id, "name": topic_id, "definition": "Definition"} for topic_id in topic_ids]
    taxonomy_path = tmp_path / "taxonomy.yaml"
    taxonomy_path.write_text(yaml.safe_dump({
        "status": "frozen",
        "calibration": {"topic_test_sha256": sha256(test_path.read_bytes()).hexdigest()},
        "leaves": catalog,
    }), encoding="utf-8")
    catalog_json = json.dumps(catalog, ensure_ascii=False, separators=(",", ":"))
    master_path = tmp_path / "master.csv"
    master_rows = [
        {"paper_id": row["paper_id"], "venue_id": row["venue_id"], "year": "2025",
         "title": "Title", "abstract": "Abstract", "topic_catalog": catalog_json,
         "label_1": "", "label_2": "", "label_3": "", "labeler": "", "notes": ""}
        for row in paper_rows
    ]
    with master_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(master_rows)
    master_by_id = {row["paper_id"]: row for row in master_rows}

    allocation = assign_topic_reviewers(paper_rows, seed=20261108)
    review_paths = {}
    blank_sheet_metadata = {}
    for reviewer in ("A", "B"):
        blank_path = tmp_path / f"blank-{reviewer}.csv"
        blank_html_path = tmp_path / f"blank-{reviewer}.html"
        completed_path = tmp_path / f"completed-{reviewer}.csv"
        assigned_ids = allocation["reviewer_paper_ids"][reviewer]
        blank_rows = [{**master_by_id[paper_id], "labeler": reviewer} for paper_id in assigned_ids]
        completed_rows = [
            {**row, "label_1": "topic:0", "labeler": reviewer, "notes": ""}
            for row in blank_rows
        ]
        for path, rows in ((blank_path, blank_rows), (completed_path, completed_rows)):
            with path.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=FIELDS)
                writer.writeheader()
                writer.writerows(rows)
        blank_sheet_metadata[reviewer] = {"csv": {"path": str(blank_path), "sha256": sha256(blank_path.read_bytes()).hexdigest()}}
        blank_html_path.write_text("<html>prediction-blind</html>", encoding="utf-8")
        blank_sheet_metadata[reviewer]["html"] = {
            "path": str(blank_html_path), "sha256": sha256(blank_html_path.read_bytes()).hexdigest()
        }
        review_paths[reviewer] = completed_path

    allocation_path = tmp_path / "allocation.json"
    allocation_doc = {
        "assignment_method_version": "d040-topic-review-allocation-v1",
        "predictions_included": False,
        "paper_count": 50,
        "reviewer_paper_ids": allocation["reviewer_paper_ids"],
        "assignments_per_reviewer": {"A": 30, "B": 30},
        "overlap_paper_ids": allocation["overlap_paper_ids"],
        "venue_counts": allocation["venue_counts"],
        "master_sheet": {"sha256": sha256(master_path.read_bytes()).hexdigest()},
        "topic_test_manifest": {"sha256": sha256(test_path.read_bytes()).hexdigest()},
        "taxonomy": {"sha256": sha256(taxonomy_path.read_bytes()).hexdigest()},
        "reviewer_sheets": blank_sheet_metadata,
    }
    allocation_path.write_text(json.dumps(allocation_doc), encoding="utf-8")

    paper_nodes = [Node(id=row["paper_id"], label="Paper", name=row["paper_id"]) for row in paper_rows]
    topic_nodes = [Node(id=topic_id, label="Topic", name=topic_id) for topic_id in topic_ids]

    def make_graph(version: str, predicted_ids: set[str], method: str) -> Path:
        nodes = paper_nodes + topic_nodes
        edges = [
            Edge(edge_id=f"edge:{version}:{paper_id}", relation="HAS_TOPIC", source_id=paper_id,
                 target_id="topic:0", evidence_kind="inferred_topic", evidence_ids=["evidence:1"],
                 method_version=method, graph_version=version, validation_status="accepted")
            for paper_id in sorted(predicted_ids)
        ]
        path = tmp_path / f"{version}.json"
        path.write_text(GraphArtifact(
            graph_version=version, is_synthetic=False, nodes=nodes, edges=edges, evidence=[]
        ).model_dump_json(), encoding="utf-8")
        return path

    all_papers = {row["paper_id"] for row in paper_rows}
    graph_v1_path = make_graph("graph-v1", all_papers, "phrase-v1")
    embedding_ids = {row["paper_id"] for index, row in enumerate(paper_rows) if index < 45}
    graph_v2_path = make_graph("graph-v2", embedding_ids, "embedding-v1")
    graph_v2_summary_path = tmp_path / "graph-v2-summary.json"
    graph_v2_summary_path.write_text(json.dumps({
        "graph_v1_version": "graph-v1",
        "graph_version": "graph-v2",
        "graph_sha256": sha256(graph_v2_path.read_bytes()).hexdigest(),
        "inputs_sha256": {"graph_v1_sha256": sha256(graph_v1_path.read_bytes()).hexdigest()},
    }), encoding="utf-8")
    freeze_path = tmp_path / "freeze.json"
    freeze_path.write_text(json.dumps({
        "graph_version": "graph-v2",
        "graph_sha256": sha256(graph_v2_path.read_bytes()).hexdigest(),
        "topic_test_manifest_sha256": sha256(test_path.read_bytes()).hexdigest(),
        "config_hashes": {"configs/topics-release-v1.yaml": sha256(taxonomy_path.read_bytes()).hexdigest()},
        "review_packet": {"topic_review_assignment": {
            "allocation_manifest": {"sha256": sha256(allocation_path.read_bytes()).hexdigest()},
            "reviewer_sheets": blank_sheet_metadata,
        }},
    }), encoding="utf-8")

    output = tmp_path / "topic-eval.json"
    result = score_topic_review(
        graph_v1_path, graph_v2_path, test_path, taxonomy_path, allocation_path,
        master_path, review_paths["A"], review_paths["B"], freeze_path,
        graph_v2_summary_path, output,
    )

    assert result["status"] == "scored_pending_release_edge_audit"
    assert result["reviewer_assignment"] == {"A": 30, "B": 30, "overlap": 10, "union": 50}
    assert result["weighting"]["effective_paper_weight"] == 50.0
    assert result["reviewer_agreement_on_overlap"]["exact_set_agreement_fraction"] == 1.0
    assert result["models"]["phrase_baseline"]["paper_normalized_review_metrics"]["micro"]["f1"] == 1.0
    embedding = result["models"]["embedding_classifier"]
    assert embedding["test_paper_coverage"]["coverage_fraction"] == 0.9
    assert embedding["paper_normalized_review_metrics"]["micro"]["recall"] == 0.9
    assert output.is_file()
