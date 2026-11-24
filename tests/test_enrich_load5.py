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
