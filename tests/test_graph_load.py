"""Loader query text, batching, idempotency and target guards (release plan Phase 1, item 2).

These tests use an in-memory fake session; they cannot show Neo4j accepts the Cypher.
The integration run against a real server is recorded in the work log.
"""

import math
import re
from collections import Counter
from pathlib import Path

import pytest

from scientific_network.contracts import GraphArtifact, NodeLabel, Relation
from scientific_network.graph import load
from scientific_network.graph.schema import RELATIONSHIPS

ROOT = Path(__file__).resolve().parents[1]
QUALITY = ROOT / "configs/quality-release-v1.yaml"


class FakeResult:
    def __init__(self, value=None):
        self.value = value

    def consume(self):
        return None

    def single(self):
        return {"n": self.value}


class FakeTx:
    def __init__(self, store):
        self.store = store

    def run(self, statement, **params):
        store = self.store
        store.statements.append((statement, params))
        if statement.startswith("UNWIND"):
            rows = params["rows"]
            store.row_batches.append(len(rows))
            merge_node = re.search(r"MERGE \(n:(\w+) \{id: row\.id\}\)", statement)
            merge_edge = re.search(r"MERGE \(a\)-\[r:(\w+) \{edge_id: row\.edge_id\}\]->\(b\)", statement)
            if merge_node:
                store.nodes.setdefault(merge_node[1], set()).update(row["id"] for row in rows)
            elif merge_edge and merge_edge[1] != store.drop_relation:
                store.edges.setdefault(merge_edge[1], set()).update(row["edge_id"] for row in rows)
            return FakeResult()
        if "RETURN count(n) AS n" in statement and "n.id IN $ids" in statement:
            label = re.search(r"MATCH \(n:(\w+)\)", statement)[1]
            clash = store.foreign.get(label, set()) & set(params["ids"])
            return FakeResult(len(clash))
        node_count = re.search(r"MATCH \(n:(\w+) \{project", statement)
        if node_count:
            return FakeResult(len(store.nodes.get(node_count[1], set())))
        edge_count = re.search(r"MATCH \(\)-\[r:(\w+)\]->\(\)", statement)
        return FakeResult(len(store.edges.get(edge_count[1], set())))


class FakeSession:
    """Behaves like a MERGE-only store: re-writing the same IDs adds nothing."""

    def __init__(self):
        self.statements: list[tuple[str, dict]] = []
        self.row_batches: list[int] = []
        self.nodes: dict[str, set] = {}
        self.edges: dict[str, set] = {}
        self.foreign: dict[str, set] = {}
        self.drop_relation: str | None = None

    def execute_write(self, fn, *args, **kwargs):
        return fn(FakeTx(self), *args, **kwargs)

    execute_read = execute_write


def test_every_relation_statement_uses_the_labels_from_the_schema():
    for relation in Relation:
        spec = RELATIONSHIPS[relation]
        text = load.relation_statement(relation)
        assert f"MATCH (a:{spec.source.value} {{id: row.left" in text
        assert f"MATCH (b:{spec.target.value} {{id: row.right" in text
        assert f"MERGE (a)-[r:{relation.value} {{edge_id: row.edge_id}}]->(b)" in text
        assert "project: $project, graph_version: $version" in text


def test_no_generated_statement_matches_an_unlabeled_node(graph):
    session = FakeSession()
    load.import_graph(session, graph, batch_size=4)
    assert session.statements
    for statement, _ in session.statements:
        for variable in re.findall(r"MATCH \((\w*)", statement):
            assert re.search(rf"MATCH \({variable}:\w+", statement) or variable == "", statement
        assert "MATCH (n)" not in statement and "MATCH (n {" not in statement


def test_rows_are_written_in_bounded_batches_each_in_its_own_transaction(graph):
    session = FakeSession()
    result = load.import_graph(session, graph, batch_size=4)
    assert session.row_batches and max(session.row_batches) <= 4
    nodes = Counter(n.label for n in graph.nodes)
    relations = Counter(e.relation for e in graph.edges)
    expected = sum(math.ceil(n / 4) for n in nodes.values()) + sum(math.ceil(n / 4) for n in relations.values())
    assert result["transactions"] == len(session.row_batches) == expected
    assert result["batch_size"] == 4


def test_default_batch_size_is_five_thousand_rows():
    assert load.BATCH_SIZE == 5000
    assert [len(chunk) for chunk in load.batched(list(range(12_001)), load.BATCH_SIZE)] == [5000, 5000, 2001]
    with pytest.raises(ValueError):
        list(load.batched([1], 0))


def test_import_reconciles_counts_and_replay_changes_nothing(graph):
    session = FakeSession()
    first = load.import_graph(session, graph, batch_size=3)
    assert first["nodes_before"] == 0
    assert first["nodes_after"] == len(graph.nodes)
    assert first["edges_after"] == len(graph.edges)
    assert first["edges_by_relation"] == {r.value: n for r, n in Counter(e.relation for e in graph.edges).items()}
    assert first["nodes_by_label"] == {l.value: Counter(n.label for n in graph.nodes).get(l, 0) for l in NodeLabel}
    second = load.import_graph(session, graph, batch_size=3)
    assert second["nodes_before"] == first["nodes_after"]
    assert (second["nodes_after"], second["edges_after"]) == (first["nodes_after"], first["edges_after"])
    assert second["edges_by_relation"] == first["edges_by_relation"]


def test_count_mismatch_names_the_relation_and_is_not_reported_as_success(graph):
    session = FakeSession()
    session.drop_relation = "CITES"
    with pytest.raises(ValueError, match=r"counts disagree.*CITES: stored 0 != canonical 2"):
        load.import_graph(session, graph)


def test_foreign_ids_are_refused_before_any_write(graph):
    session = FakeSession()
    session.foreign["Paper"] = {"paper:p1"}
    with pytest.raises(ValueError, match="another graph/version"):
        load.import_graph(session, graph)
    assert session.row_batches == []


def _as_release(graph: GraphArtifact, version: str = "release-0123456789ab") -> GraphArtifact:
    payload = graph.model_dump(mode="json")
    payload["graph_version"], payload["is_synthetic"] = version, False
    for edge in payload["edges"]:
        edge["graph_version"] = version
    return GraphArtifact.model_validate(payload)


@pytest.mark.parametrize("uri,release,allowed", [
    ("bolt://localhost:7689", True, True),
    ("bolt://127.0.0.1:7689", True, True),
    ("bolt://localhost:7687", True, False),
    ("bolt://localhost:7688", True, False),
    ("bolt://localhost", True, False),
    ("not a uri", True, False),
    ("bolt://localhost:7689", False, False),
    ("bolt://localhost:7687", False, True),
    ("bolt://localhost:7699", False, True),
])
def test_release_graphs_may_only_target_the_isolated_service(graph, uri, release, allowed):
    candidate = _as_release(graph) if release else graph
    if allowed:
        load.check_target(uri, candidate)
    else:
        with pytest.raises(ValueError, match="neo4j-five-year|reserved for the release graph"):
            load.check_target(uri, candidate)


def test_build_refuses_a_release_graph_aimed_at_the_pilot_uri_before_connecting(tmp_path, monkeypatch, graph):
    def unexpected_connection(*args, **kwargs):
        raise AssertionError("must not connect when the target is wrong")

    monkeypatch.setattr(load.GraphDatabase, "driver", unexpected_connection)
    monkeypatch.setenv("NEO4J_PASSWORD", "test-password")
    monkeypatch.setenv("NEO4J_URI", "bolt://localhost:7687")
    graph_path = tmp_path / "graph.json"
    graph_path.write_text(_as_release(graph).model_dump_json())
    with pytest.raises(ValueError, match="neo4j-five-year"):
        load.build(graph_path, tmp_path / "report.json", QUALITY)
    assert not (tmp_path / "report.json").exists()
