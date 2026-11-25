import pytest

from scientific_network.enrich.load5 import check_enriched_target, edge_groups, edge_statement
from test_enrich_graph5 import build


def test_only_port_7690_is_accepted_for_the_enriched_graph():
    check_enriched_target("bolt://localhost:7690")
    for uri in ("bolt://localhost:7689", "bolt://localhost:7687", "bolt://localhost"):
        with pytest.raises(ValueError, match="7690"):
            check_enriched_target(uri)


def test_edges_are_grouped_by_endpoint_labels_and_use_labeled_lookups():
    groups = edge_groups(build())
    assert {k for k in groups} == {("USES_METHOD", "Paper", "Method"), ("ADDRESSES_TASK", "Paper", "Task"), ("APPLIED_TO", "Method", "Task")}
    statement = edge_statement("APPLIED_TO", "Method", "Task")
    assert "MATCH (a:Method {id: row.left})" in statement and "MERGE (a)-[r:APPLIED_TO" in statement


import re

from scientific_network.enrich.load5 import find_stale_enrichment, remove_stale_enrichment


class FakeSession:
    """In-memory stand-in for a Neo4j session: interprets only the statements the stale-layer functions issue."""

    def __init__(self, nodes, edges):
        self.nodes, self.edges, self.statements = nodes, edges, []

    def _matching_nodes(self, statement, version):
        label = re.search(r"MATCH \(n:(\w+)\)", statement).group(1)
        parent_only = "n.source = 'wikidata_parent'" in statement
        return [n for n in self.nodes if label in n["labels"] and n.get("graph_version", "") != version and (not parent_only or n.get("source") == "wikidata_parent")]

    def _matching_edges(self, statement, version):
        rel = re.search(r"\[r:(\w+)\]", statement).group(1)
        return [e for e in self.edges if e["type"] == rel and e.get("graph_version", "") != version]

    def execute_read(self, fn, statement, params):
        self.statements.append(statement)
        if "MATCH (n:" in statement:
            return len(self._matching_nodes(statement, params["version"]))
        return len(self._matching_edges(statement, params["version"]))

    def execute_write(self, fn, statement, params):
        self.statements.append(statement)
        assert "LIMIT $limit" in statement                                   # always batched
        if "DETACH DELETE" in statement:
            hit = self._matching_nodes(statement, params["version"])[: params["limit"]]
            self.nodes = [n for n in self.nodes if not any(n is h for h in hit)]
            gone = {id(h) for h in hit}
            self.edges = [e for e in self.edges if id(e["a"]) not in gone and id(e["b"]) not in gone]
            return len(hit)
        hit = self._matching_edges(statement, params["version"])[: params["limit"]]
        self.edges = [e for e in self.edges if not any(e is h for h in hit)]
        return len(hit)


def database_with_stale_layer():
    paper = {"labels": {"Paper"}, "graph_version": "release-v4", "id": "p1"}
    v4_org = {"labels": {"Organization"}, "graph_version": "release-v4", "id": "o1"}          # a v4 organization: never enrichment
    old_method = {"labels": {"Method"}, "graph_version": "enriched-old", "id": "m1"}
    old_parent = {"labels": {"Organization"}, "graph_version": "enriched-old", "source": "wikidata_parent", "id": "o2"}
    new_task = {"labels": {"Task"}, "graph_version": "enriched-new", "id": "t1"}              # the layer being loaded: kept
    edges = [{"type": "AUTHORED", "graph_version": "release-v4", "a": paper, "b": paper},
             {"type": "AFFILIATED_WITH", "graph_version": "release-v4", "a": paper, "b": v4_org},
             {"type": "USES_METHOD", "graph_version": "enriched-old", "a": paper, "b": old_method},
             {"type": "PART_OF", "graph_version": "enriched-old", "a": v4_org, "b": old_parent},
             {"type": "ADDRESSES_TASK", "graph_version": "enriched-new", "a": paper, "b": new_task}]
    return FakeSession([paper, v4_org, old_method, old_parent, new_task], edges)


def test_stale_layer_is_detected_by_version_and_v4_items_are_not_counted():
    session = database_with_stale_layer()
    stale = find_stale_enrichment(session, "enriched-new")
    assert stale == {"nodes": {"Method": 1, "Organization": 1}, "edges": {"USES_METHOD": 1, "PART_OF": 1}}
    assert find_stale_enrichment(session, "enriched-old")["nodes"] == {"Task": 1}      # the other way round, the new layer is the stale one
    clean = FakeSession([n for n in session.nodes if n["id"] in ("p1", "o1", "t1")], [e for e in session.edges if e["graph_version"] != "enriched-old"])
    assert find_stale_enrichment(clean, "enriched-new") == {"nodes": {}, "edges": {}}


def test_replace_deletes_only_the_stale_enrichment_layer_in_batches():
    session = database_with_stale_layer()
    removed = remove_stale_enrichment(session, "enriched-new", batch_size=1)
    assert removed == {"nodes": {"Method": 1, "Organization": 1}, "edges": {"USES_METHOD": 1, "PART_OF": 1}}
    assert sorted(n["id"] for n in session.nodes) == ["o1", "p1", "t1"]                 # v4 paper, v4 organization and the new layer survive
    assert sorted(e["type"] for e in session.edges) == ["ADDRESSES_TASK", "AFFILIATED_WITH", "AUTHORED"]
    assert not any(re.search(r"\b(Paper|Researcher|Topic|Venue)\b|AUTHORED|AFFILIATED_WITH|CITES", s) for s in session.statements if "DELETE" in s)
    assert all("LIMIT $limit" in s for s in session.statements if "DELETE" in s)


def test_loader_refuses_a_stale_layer_without_the_flag_and_an_existing_report_path(tmp_path, monkeypatch):
    from scientific_network.enrich import load5
    graph_path = tmp_path / "graph.json"
    import json
    graph = build()
    graph_path.write_text(json.dumps(graph))
    existing = tmp_path / "report.json"
    existing.write_text("{}")
    with pytest.raises(ValueError, match="choose a new report path.*report.json"):
        load5.build(graph_path, existing)
    session = database_with_stale_layer()

    class Driver:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def verify_connectivity(self): pass
        def session(self, database=None): return self

    class Ctx(FakeSession):
        def __enter__(self): return self
        def __exit__(self, *a): return False

    ctx = Ctx(session.nodes, session.edges)
    ctx.execute_write = lambda fn, statement, params: (_ for _ in ()).throw(AssertionError("must not write before refusing"))
    driver = Driver()
    driver.session = lambda database=None: ctx
    monkeypatch.setenv("NEO4J_PASSWORD", "x")
    monkeypatch.setenv("NEO4J_URI", "bolt://localhost:7690")
    monkeypatch.setattr(load5.GraphDatabase, "driver", lambda *a, **k: driver)
    monkeypatch.setattr(load5, "load_dotenv", lambda **k: None)
    import types
    monkeypatch.setattr(load5, "GraphArtifact", types.SimpleNamespace(model_validate=lambda base: base))   # the fixture's tiny base graph is not a full v4 artifact
    with pytest.raises(ValueError, match="another graph version.*Nothing was written.*--replace-enrichment"):
        load5.build(graph_path, tmp_path / "new.json")
