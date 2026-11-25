from scientific_network.enrich.cooccurrence import CooccurrenceIndex, distribution


def fixture():
    nodes = [{"id": f"paper:{i}", "label": "Paper", "name": f"P{i}", "properties": {"year": 2020 + i}} for i in range(1, 5)]
    nodes += [{"id": "method:gnn", "label": "Method", "name": "GNN", "properties": {}},
              {"id": "method:cnn", "label": "Method", "name": "CNN", "properties": {}},
              {"id": "task:nc", "label": "Task", "name": "node classification", "properties": {}},
              {"id": "task:seg", "label": "Task", "name": "segmentation", "properties": {}},
              {"id": "dataset:cora", "label": "Dataset", "name": "Cora", "properties": {}}]
    def edge(relation, paper, target, status="accepted"):
        return {"relation": relation, "source_id": f"paper:{paper}", "target_id": target, "validation_status": status}
    edges = [edge("USES_METHOD", 1, "method:gnn"), edge("ADDRESSES_TASK", 1, "task:nc"), edge("USES_DATASET", 1, "dataset:cora"),
             edge("USES_METHOD", 2, "method:gnn"), edge("ADDRESSES_TASK", 2, "task:nc"),
             edge("USES_METHOD", 3, "method:gnn"), edge("ADDRESSES_TASK", 3, "task:seg"),
             edge("USES_METHOD", 4, "method:cnn"), edge("ADDRESSES_TASK", 4, "task:nc", status="rejected"),
             {"relation": "APPLIED_TO", "source_id": "method:cnn", "target_id": "task:seg", "validation_status": "accepted"}]
    return CooccurrenceIndex(nodes, edges)


def test_partners_count_distinct_shared_papers_with_years_and_evidence():
    rows = fixture().partners("method:gnn", "Task")
    assert [(r["name"], r["shared_papers"]) for r in rows] == [("node classification", 2), ("segmentation", 1)]
    assert rows[0]["paper_ids"] == ["paper:1", "paper:2"] and rows[0]["years"] == [2021, 2022]
    assert fixture().partners("method:gnn", "Task", min_papers=2)[0]["entity_id"] == "task:nc"


def test_only_paper_level_accepted_edges_count_and_entity_edges_are_ignored():
    index = fixture()
    assert index.partners("method:cnn", "Task") == []  # rejected edge and the APPLIED_TO edge are not evidence
    assert [r["name"] for r in index.partners("task:nc", "Method")] == ["GNN"]
    assert index.partners("method:gnn", "Dataset")[0]["shared_papers"] == 1


def test_distribution_reports_thresholds_and_partner_availability():
    report = distribution(fixture())
    mt = report["by_type_pair"]["Method-Task"]
    assert mt["pairs_at_least"] == {"1": 2, "2": 1, "3": 0, "5": 0}
    assert mt["top_pairs"][0]["shared_papers"] == 2 and mt["top_pairs"][0]["a"] == "GNN"
    assert report["entities_with_a_partner_at_2_papers"]["Method_with_a_Task"] == {"count": 1, "of": 2}
    assert report["entities_with_a_partner_at_1_paper"]["Task_with_a_Method"] == {"count": 2, "of": 2}
