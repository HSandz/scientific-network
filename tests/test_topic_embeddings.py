"""Pure tests for embedding threshold rules and cited excerpt offsets."""

import numpy as np
import pytest
import hashlib
import json

from scientific_network.nlp.embeddings import (
    calibrate_topic_thresholds, load_development_documents, predict_topics,
    select_labels, split_sentences,
)


LEAVES = [
    {"id": "topic:graph", "name": "Graph learning", "definition": "Methods on graphs."},
    {"id": "topic:vision", "name": "Computer vision", "definition": "Methods for images."},
    {"id": "topic:other", "name": "Other topic", "definition": "Other methods."},
    {"id": "topic:fourth", "name": "Fourth topic", "definition": "Fourth methods."},
]


def test_select_labels_abstains_and_caps_supported_close_labels():
    assert select_labels([0.4, 0.39, 0.2, 0.1], LEAVES, tau=0.5, delta=0.2) == []
    selected = select_labels([0.81, 0.8, 0.78, 0.79], LEAVES, tau=0.75, delta=0.05)
    assert [row["topic_id"] for row in selected] == ["topic:graph", "topic:vision", "topic:fourth"]
    with pytest.raises(ValueError, match="tau"):
        select_labels([0.8] * 4, LEAVES, tau=float("nan"), delta=0.1)


def test_split_sentences_preserves_exact_source_offsets():
    text = "First sentence.  Second sentence!\nThird?"
    parts = split_sentences(text)
    assert [sentence for sentence, _, _ in parts] == ["First sentence.", "Second sentence!", "Third?"]
    assert all(text[start:end] == sentence for sentence, start, end in parts)


class FakeEncoder:
    def encode(self, texts, **kwargs):
        vectors = []
        for text in texts:
            if text.startswith("Graph learning"):
                vectors.append([1.0, 0.0])
            elif text.startswith("Computer vision"):
                vectors.append([0.0, 1.0])
            elif text.startswith("Other topic") or text.startswith("Fourth topic"):
                vectors.append([-1.0, 0.0] if text.startswith("Other topic") else [0.0, -1.0])
            elif text.startswith("Research about both"):
                vectors.append([0.8, 0.79])
            elif text == "A graph neural network." or text == "Graph title":
                vectors.append([1.0, 0.0])
            elif text == "Images are analyzed.":
                vectors.append([0.0, 1.0])
            elif text.startswith("Unrelated subject"):
                vectors.append([0.0, 0.0])
            else:
                vectors.append([-1.0, 0.0])
        vectors = np.asarray(vectors, dtype=np.float32)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        return np.divide(vectors, norms, out=np.zeros_like(vectors), where=norms != 0)


def test_predict_topics_uses_abstract_or_title_excerpt_and_abstains():
    taxonomy = {"leaves": LEAVES}
    documents = [
        {"paper_id": "paper:both", "title": "Research about both", "abstract": "A graph neural network. Images are analyzed."},
        {"paper_id": "paper:title", "title": "Graph title", "abstract": None},
        {"paper_id": "paper:abstain", "title": "Unrelated subject", "abstract": "No matching evidence."},
    ]
    output = predict_topics(documents, taxonomy, FakeEncoder(), tau=0.7, delta=0.02, batch_size=2)
    both, title, abstain = output
    assert [p["topic_id"] for p in both["predictions"]] == ["topic:graph", "topic:vision"]
    assert both["predictions"][0]["excerpt"] == "A graph neural network."
    assert both["predictions"][1]["excerpt"] == "Images are analyzed."
    assert all(p["text_source"] == "abstract" for p in both["predictions"])
    assert title["text_source"] == "title" and title["predictions"][0]["excerpt"] == "Graph title"
    assert title["predictions"][0]["start"] == 0 and title["predictions"][0]["end"] == len("Graph title")
    assert abstain["decision"] == "abstain" and abstain["predictions"] == []


def test_development_loader_excludes_all_existing_and_new_test_versions_before_returning_text(tmp_path):
    def write_jsonl(name, rows):
        path = tmp_path / name
        path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        return path

    roster = write_jsonl("roster.jsonl", [
        {"paper_id": "paper:ijcai:2021:test", "venue_id": "venue:ijcai", "year": 2021, "status": "included", "title": "reserved IJCAI"},
        {"paper_id": "paper:ijcai:2021:version", "venue_id": "venue:ijcai", "year": 2021, "status": "included", "title": "reserved IJCAI version"},
        {"paper_id": "paper:aaai:2021:test", "venue_id": "venue:aaai", "year": 2021, "status": "included", "title": "reserved AAAI"},
        {"paper_id": "paper:aaai:2021:version", "venue_id": "venue:aaai", "year": 2021, "status": "included", "title": "reserved AAAI version"},
        {"paper_id": "paper:aaai:2022:dev", "venue_id": "venue:aaai", "year": 2022, "status": "included", "title": "development paper"},
    ])
    membership = write_jsonl("membership.jsonl", [
        {"paper_id": "paper:ijcai:2021:test", "venue_id": "venue:ijcai", "split": "test", "leakage_group": "ij-test"},
        {"paper_id": "paper:ijcai:2021:version", "venue_id": "venue:ijcai", "split": "pool", "leakage_group": "ij-test"},
    ])
    leakage = write_jsonl("leakage.jsonl", [
        {"paper_id": "paper:ijcai:2021:test", "candidate_paper_ids": ["paper:ijcai:2021:test", "paper:ijcai:2021:version"]},
        {"paper_id": "paper:aaai:2021:test", "candidate_paper_ids": ["paper:aaai:2021:test", "paper:aaai:2021:version"]},
    ])
    source_hashes = {
        "roster_sha256": hashlib.sha256(roster.read_bytes()).hexdigest(),
        "membership_sha256": hashlib.sha256(membership.read_bytes()).hexdigest(),
        "leakage_sha256": hashlib.sha256(leakage.read_bytes()).hexdigest(),
    }
    topic_test = write_jsonl("topic-test.jsonl", [{
        "paper_id": "paper:aaai:2021:test", "heldout_paper_ids": ["paper:aaai:2021:test", "paper:aaai:2021:version"],
        **source_hashes,
    }])
    paper_rows = [json.loads(line) for line in roster.read_text().splitlines()]
    works = write_jsonl("works.jsonl", [
        {"paper_id": row["paper_id"], "roster": {"title": row["title"]}, "venue_id": row["venue_id"], "year": row["year"],
         "match": {"status": "matched"}, "openalex": {"abstract": "secret " + row["title"]}}
        for row in paper_rows
    ])

    documents, report = load_development_documents(works, roster, membership, leakage, topic_test)
    assert [row["paper_id"] for row in documents] == ["paper:aaai:2022:dev"]
    assert all("reserved" not in row["title"] and "reserved" not in str(row["abstract"]) for row in documents)
    assert report["eligible_release_papers"] == 5
    assert report["existing_reserved_test_papers"] == 1
    assert report["development_papers"] == 1


def test_calibration_is_development_only_and_reports_coverage_and_delta_sweep():
    documents = [
        {"paper_id": f"paper:dev:{index}", "title": "Research about both", "abstract": "A graph neural network."}
        for index in range(10)
    ]
    result = calibrate_topic_thresholds(
        documents, {"leaves": LEAVES}, FakeEncoder(), target_coverage=0.85,
        seed=20261108, sample_size=3, batch_size=4,
    )
    assert result["development_papers"] == 10
    assert result["target_coverage"] == 0.85 and -1 <= result["tau"] <= 1
    assert 0.8 <= result["observed_coverage"] <= 1
    assert len(result["delta_sweep"]) >= 3 and len(result["development_sample"]) == 3
    assert result["test_predictions_computed"] is False
    assert all(row["paper_id"].startswith("paper:dev:") for row in result["development_sample"])
