"""Source-wide conflict withholding and frozen-prediction correction regressions."""

from hashlib import sha256
import json
from pathlib import Path

import pytest

from scientific_network.contracts import GraphArtifact
from scientific_network.graph.validate import validate_graph
from scientific_network.resolve.release_identity import (
    collect_identity_evidence, correct_release_identity, identity_invariants, valid_orcid,
)
from scientific_network.resolve.release_taxonomy import synchronize_taxonomy
from test_release_graph import QUALITY, authorship, build, edges, inst, row

TAXONOMY = Path(__file__).resolve().parents[1] / "configs/topics-release-v1.yaml"

ONE, TWO = "0000-0002-1825-0097", "0000-0001-5109-3700"


def with_orcids(person, *, singular=None, observed=None):
    result = authorship(person, "Ann One", [inst("I1")], orcid=singular)
    if observed is not None:
        result["author"]["observed_orcids"] = observed
    return result


@pytest.mark.parametrize("value,expected", [
    (ONE, ONE), (f" https://orcid.org/{ONE}/ ", ONE), (f"http://orcid.org/{ONE}", ONE),
    ("0000-0002-1825-0098", None), (f"garbage {ONE}", None), (f"{ONE}?x=1", None),
    (None, None), ([], None), (123, None), ("", None),
])
def test_whole_value_and_checksum_required(value, expected):
    assert valid_orcid(value) == expected


@pytest.mark.parametrize("authorships", [
    [with_orcids("A1", observed=[ONE, TWO])],
    [with_orcids("A1", singular=ONE, observed=[TWO])],
    [with_orcids("A1", observed=[ONE]), with_orcids("A1", observed=[TWO])],
])
def test_all_orcid_fields_union_across_all_matched_works(authorships):
    rows = [row(index, ["Ann One"], [item]) for index, item in enumerate(authorships, 1)]
    result = collect_identity_evidence(rows)
    assert result["withheld"] == {"A1": "author_id_conflicting_orcids"}
    assert result["review"][0]["orcids"] == sorted([ONE, TWO])
    records = result["review"][0]["source_observations"]
    assert all(r["raw_sha256"] == "b" * 64 and "#results[0]" in r["source_locator"] for r in records)
    assert all("/authorships/0/author/" in r["field_locator"] for r in records)
    assert {r["normalized_orcid"] for r in records} == {ONE, TWO}
    # This pass is independent of name compatibility and whether a position was previously accepted.
    rows[-1]["roster"]["authors"] = ["Incompatible Other"]
    assert collect_identity_evidence(rows)["withheld"] == result["withheld"]


def test_equivalent_duplicates_missing_ids_names_and_unmatched_work_do_not_make_conflicts():
    a = with_orcids("A1", singular=ONE, observed=[ONE, f"https://orcid.org/{ONE}"])
    rows = [row(1, ["Ann One"], [a]), row(2, ["Ann One"], [with_orcids("A1")]),
            row(3, ["Ann One"], [with_orcids("A2", singular=TWO)]),
            row(4, ["Ann One"], [], status="review")]
    result = collect_identity_evidence(rows)
    assert result["withheld"] == {}
    assert result["orcids"] == {"A1": {ONE}, "A2": {TWO}}
    assert result["counts"]["matched_author_ids"] == 2


@pytest.mark.parametrize("field,value", [
    ("orcid", "bad"), ("orcid", f"prefix {ONE}"), ("orcid", "0000-0002-1825-0098"),
    ("orcid", 2), ("orcid", []), ("observed_orcids", ONE), ("observed_orcids", {}),
    ("observed_orcids", [None]), ("observed_orcids", [ONE, "bad"]),
])
def test_malformed_nonempty_identity_evidence_withheld_globally(field, value):
    item = with_orcids("A1")
    item["author"][field] = value
    result = collect_identity_evidence([row(1, ["Ann One"], [item]),
                                        row(2, ["Ann One"], [with_orcids("A1", singular=ONE)])])
    assert result["withheld"] == {"A1": "author_id_malformed_orcid"}
    assert result["review"][0]["has_malformed_evidence"]
    assert any(r["status"] == "malformed" for r in result["review"][0]["source_observations"])


def test_builder_uses_global_array_conflicts_and_keeps_same_name_distinct(tmp_path):
    rows = [row(1, ["Ann One", "Ann One"], [with_orcids("A1", observed=[ONE, TWO]), with_orcids("A2")]),
            row(2, ["Ann One"], [with_orcids("A1")])]
    graph, summary, queue = build(tmp_path, rows)
    assert {n.id for n in graph.nodes if n.label == "Researcher"} == {"researcher:openalex:A2"}
    assert len(edges(graph, "AUTHORED")) == 1 and len(graph.affiliation_observations) == 1
    assert summary["coverage"]["author_positions_accepted"] == 1
    assert any(q["kind"] == "author_id_conflicting_orcids" and q["source_observations"] for q in queue)


def make_frozen_source(tmp_path):
    rows = []
    for n in range(1, 4):
        rows.append(row(n, ["Ann One", "Bo Two", "Cy Three"], [
            authorship("A1", "Ann One", [inst("I1"), inst("I2")], orcid=ONE),
            authorship("A2", "Bo Two", [inst("I2")]),
            authorship("A3", "Cy Three", [inst("I3")]),
        ], refs=["W1"] if n != 1 else []))
    # Distinct same-name identity without ORCID remains accepted and keeps I1 supported.
    rows.append(row(4, ["Ann One"], [authorship("A4", "Ann One", [inst("I1")])]))
    old, summary, _ = build(tmp_path, rows)
    old = synchronize_taxonomy(old, TAXONOMY, old.graph_version)
    # Represent the historical omission: graph accepted A1 before noticing arrays.
    rows[0]["openalex"]["authorships"][0]["author"]["observed_orcids"] = [ONE, TWO]
    works = tmp_path / "works.jsonl"
    works.write_text("".join(json.dumps(r) + "\n" for r in rows))
    source = tmp_path / "frozen-graph.json"
    source.write_text(old.model_dump_json() + "\n")
    summary.update(graph_version=old.graph_version, graph_sha256=sha256(source.read_bytes()).hexdigest())
    summary_path = tmp_path / "source-summary.json"
    summary_path.write_text(json.dumps(summary))
    frozen = {"graph_version": old.graph_version, "graph_sha256": summary["graph_sha256"],
              "source_inputs": {"works": {"sha256": sha256(works.read_bytes()).hexdigest()}},
              "correction_summary": {"sha256": sha256(summary_path.read_bytes()).hexdigest()},
              "config_hashes": {str(p): sha256(p.read_bytes()).hexdigest() for p in (TAXONOMY, QUALITY)}}
    freeze_path = tmp_path / "source-freeze.json"
    freeze_path.write_text(json.dumps(frozen))
    protocol = tmp_path / "correction-protocol.yaml"
    protocol.write_text("version: synthetic-test-correction\n")
    return old, (works, source, TAXONOMY, QUALITY, summary_path, freeze_path, protocol)


def test_correction_preserves_topics_and_papers_recomputes_all_support(tmp_path, monkeypatch):
    old, inputs = make_frozen_source(tmp_path)
    hashes = {p: sha256(p.read_bytes()).hexdigest() for p in inputs}
    monkeypatch.setattr("scientific_network.resolve.release_topics.predict_topics",
                        lambda *a, **k: pytest.fail("identity correction invoked inference"))
    result = correct_release_identity(*inputs, tmp_path / "v4", tmp_path / "summary-v4.json", tmp_path / "freeze-v4.json")
    new = GraphArtifact.model_validate_json((tmp_path / "v4/graph.json").read_bytes())
    assert all(sha256(p.read_bytes()).hexdigest() == digest for p, digest in hashes.items())
    assert not any(n.id == "researcher:openalex:A1" for n in new.nodes)
    assert any(n.id == "researcher:openalex:A4" for n in new.nodes)
    assert not any(o.researcher_id.endswith(":A1") for o in new.affiliation_observations)
    assert len(new.affiliation_observations) == 7
    assert result["coverage"]["author_positions"] == 10
    assert result["coverage"]["author_positions_accepted"] == 7
    assert result["coverage"]["identity_correction_removed_authorships"] == 3
    assert result["coverage"]["author_paper_affiliation_coverage"] == .7
    assert {n.id for n in new.nodes if n.label == "Organization"} == {"organization:I1", "organization:I2", "organization:I3"}
    # Official k=3 remains the denominator after one person is withheld.
    coauthored = edges(new, "COAUTHORED_WITH")
    assert len(coauthored) == 1 and coauthored[0].properties == {"support_count": 3, "fractional_weight": 1.5}
    collaboration = edges(new, "COLLABORATED_WITH")
    assert len(collaboration) == 1 and collaboration[0].properties == {"support_count": 3, "fractional_weight": 3.0}
    assert len(edges(new, "RESEARCHES_TOPIC")) == 2 and len(edges(new, "CONTRIBUTES_TO_TOPIC")) == 2
    assert validate_graph(new, require_derived=True) == []
    assert identity_invariants(old, new) == result["preservation"]
    changes = [json.loads(line) for line in (tmp_path / "v4/changes.jsonl").read_text().splitlines()]
    manifest = json.loads((tmp_path / "v4/change-manifest.json").read_bytes())
    assert len(changes) == manifest["change_ledger"]["rows"]
    changed_evidence = [c for c in changes if c["collection"] == "evidence" and c["change"] == "changed"]
    assert changed_evidence and any(c["before"]["support_edge_ids"] != c["after"]["support_edge_ids"] for c in changed_evidence)
    changed_edges = [c for c in changes if c["collection"] == "edges" and c["change"] == "changed"]
    assert any(c["before"]["properties"]["fractional_weight"] != c["after"]["properties"]["fractional_weight"] for c in changed_edges)
    assert manifest["graph_version_restamp"]["edge_count"] == len(new.edges)
    freeze = json.loads((tmp_path / "freeze-v4.json").read_bytes())
    assert freeze["graph_sha256"] == sha256((tmp_path / "v4/graph.json").read_bytes()).hexdigest()
    assert freeze["audit_status"].startswith("not_started")
    again = correct_release_identity(*inputs, tmp_path / "again", tmp_path / "again-summary.json", tmp_path / "again-freeze.json")
    assert again["graph_version"] == result["graph_version"]
    assert (tmp_path / "again/graph.json").read_bytes() == (tmp_path / "v4/graph.json").read_bytes()


def test_unsupported_orgs_removed_and_zero_authorship_paper_metadata_preserved(tmp_path):
    old, inputs = make_frozen_source(tmp_path)
    # A4 is also withheld, leaving I1 with no support. Make its only paper all withheld.
    rows = [json.loads(line) for line in inputs[0].read_text().splitlines()]
    rows[-1]["openalex"]["authorships"][0]["author"]["observed_orcids"] = ["malformed"]
    inputs[0].write_text("".join(json.dumps(r) + "\n" for r in rows))
    freeze = json.loads(inputs[5].read_bytes())
    freeze["source_inputs"]["works"]["sha256"] = sha256(inputs[0].read_bytes()).hexdigest()
    inputs[5].write_text(json.dumps(freeze))
    result = correct_release_identity(*inputs, tmp_path / "v4", tmp_path / "summary.json", tmp_path / "freeze.json")
    new = GraphArtifact.model_validate_json((tmp_path / "v4/graph.json").read_bytes())
    assert not any(n.id == "organization:I1" for n in new.nodes)
    assert result["coverage"]["papers_without_accepted_authorship"] == 1
    old_papers = {n.id: n for n in old.nodes if n.label == "Paper"}
    for node in new.nodes:
        if node.label == "Paper":
            expected = old_papers[node.id].model_dump(mode="json")
            actual = node.model_dump(mode="json")
            if node.id == rows[-1]["paper_id"]:
                assert actual["properties"].pop("unresolved_author_reason") == "identity_correction:all_authorships_withheld"
            assert actual == expected
    assert all(n.properties["official_author_count"] == 3 for n in new.nodes if n.label == "Paper" and n.id != rows[-1]["paper_id"])


@pytest.mark.parametrize("destination", ["directory", "summary", "freeze", "dangling_symlink"])
def test_refuses_used_paths_including_dangling_symlinks(tmp_path, destination):
    _, inputs = make_frozen_source(tmp_path)
    out, summary, freeze = tmp_path / "v4", tmp_path / "new-summary.json", tmp_path / "new-freeze.json"
    if destination == "directory":
        out.mkdir()
    elif destination == "summary":
        summary.write_text("protected")
    elif destination == "freeze":
        freeze.write_text("protected")
    else:
        out.symlink_to(tmp_path / "missing")
    with pytest.raises(ValueError, match="unused versioned"):
        correct_release_identity(*inputs, out, summary, freeze)


@pytest.mark.parametrize("which", ["works", "summary", "quality"])
def test_frozen_input_hash_bindings_fail_before_outputs(tmp_path, which):
    _, inputs = make_frozen_source(tmp_path)
    if which == "quality":
        freeze = json.loads(inputs[5].read_bytes())
        freeze["config_hashes"][str(QUALITY)] = "f" * 64
        inputs[5].write_text(json.dumps(freeze))
    else:
        path = inputs[0 if which == "works" else 4]
        path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="differs from frozen"):
        correct_release_identity(*inputs, tmp_path / "v4", tmp_path / "s.json", tmp_path / "f.json")
    assert not (tmp_path / "v4").exists()


def test_preservation_checker_rejects_prediction_or_official_denominator_changes(tmp_path):
    old, inputs = make_frozen_source(tmp_path)
    for kind in ("score", "denominator", "excerpt"):
        new = old.model_copy(deep=True, update={"graph_version": "release-new"})
        for e in new.edges:
            e.graph_version = new.graph_version
        if kind == "score":
            edges(new, "HAS_TOPIC")[0].properties["score"] = .99
        elif kind == "denominator":
            next(n for n in new.nodes if n.label == "Paper").properties["official_author_count"] = 20
        else:
            next(e for e in new.evidence if e.kind == "inferred_topic").excerpt = "changed"
        with pytest.raises(ValueError, match="protected claims"):
            identity_invariants(old, new)
