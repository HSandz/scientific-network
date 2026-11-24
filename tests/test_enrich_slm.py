import json

import httpx

from scientific_network.enrich.candidates import merge_entities, merge_relations
from scientific_network.enrich.slm import slm_extract, slm_verify
from scientific_network.rag.llm import LLMClient, LLMConfig

TEXT = "Graph Mixing\nWe propose GraphMix, a graph neural network (GNN) method for link prediction, tested on Cora."


def client(replies):
    queue = list(replies)

    def handler(request):
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(queue.pop(0))}, "finish_reason": "stop"}],
                                         "usage": {"prompt_tokens": 100, "completion_tokens": 20}})
    return LLMClient(LLMConfig(base_url="http://fake/v1", model="m"), transport=httpx.MockTransport(handler))


def test_extract_drops_spans_not_in_text_and_bad_relations():
    reply = {"entities": [{"text": "GraphMix", "type": "Method"}, {"text": "link prediction", "type": "Task"},
                          {"text": "Cora", "type": "Dataset"}, {"text": "ImageNet", "type": "Dataset"},
                          {"text": "graphmix", "type": "Method"}],
             "relations": [{"head": "GraphMix", "relation": "APPLIED_TO", "tail": "link prediction"},
                           {"head": "Cora", "relation": "APPLIED_TO", "tail": "GraphMix"},
                           {"head": "GraphMix", "relation": "EVALUATED_ON", "tail": "ImageNet"}]}
    out = slm_extract(client([reply]), TEXT)
    assert [e["text"] for e in out["entities"]] == ["GraphMix", "link prediction", "Cora"]
    assert out["dropped"] == [{"type": "Dataset", "text": "ImageNet", "reason": "not_in_text"}]
    assert out["relations"] == [{"head": "GraphMix", "relation": "APPLIED_TO", "tail": "link prediction"}]


def letters(replies):
    queue = list(replies)

    def handler(request):
        return httpx.Response(200, json={"choices": [{"message": {"content": queue.pop(0)}, "finish_reason": "stop"}],
                                         "usage": {"prompt_tokens": 100, "completion_tokens": 1}})
    return LLMClient(LLMConfig(base_url="http://fake/v1", model="m"), transport=httpx.MockTransport(handler))


def test_pointwise_verify_keeps_retypes_drops_and_checks_relations():
    cands = [{"id": 1, "text": "GraphMix", "type": "Method"}, {"id": 2, "text": "graph neural network", "type": "Task"},
             {"id": 3, "text": "method", "type": "Method"}, {"id": 4, "text": "Cora", "type": "Dataset"},
             {"id": 5, "text": "link prediction", "type": "Task"}]
    rels = [{"head": "GraphMix", "relation": "EVALUATED_ON", "tail": "Cora"},
            {"head": "GraphMix", "relation": "APPLIED_TO", "tail": "link prediction"},
            {"head": "method", "relation": "APPLIED_TO", "tail": "link prediction"}]
    # entity letters: K, M (retype to Method), X, K, garbage; only the first relation has two kept endpoints: K
    out = slm_verify(letters(["K", "M", "X", "K", "?? hmm", "K"]), TEXT, cands, rels)
    kept = {e["text"]: e for e in out["entities"]}
    assert set(kept) == {"GraphMix", "graph neural network", "Cora"} and kept["graph neural network"]["retyped_from"] == "Task"
    assert {d["text"]: d["reason"] for d in out["dropped"]} == {"method": "slm_drop", "link prediction": "no_decision"}
    assert out["relations"] == [{"head": "GraphMix", "relation": "EVALUATED_ON", "tail": "Cora"}]
    assert out["completion_tokens"] == 6


def test_invalid_json_after_retry_is_reported_not_raised():
    bad = client([{"entities": "x"}, {"entities": "y"}])
    out = slm_extract(bad, TEXT)
    assert out["valid"] is False and out["entities"] == []


def test_candidate_merge_dedupes_filters_and_expands_acronyms():
    record = {"entities": [
        {"text": "GNN", "label": "method", "start": 50, "end": 53, "score": 0.9},
        {"text": "graph neural network", "label": "method", "start": 30, "end": 50, "score": 0.7},
        {"text": "method", "label": "method", "start": 60, "end": 66, "score": 0.9},
        {"text": "link prediction", "label": "task", "start": 70, "end": 85, "score": 0.8},
        {"text": "Cora", "label": "dataset", "start": 90, "end": 94, "score": 0.2}],
        "relations": [{"head": "GNN", "relation": "applied_to", "tail": "link prediction", "score": 0.8},
                      {"head": "GNN", "relation": "applied_to", "tail": "link prediction", "score": 0.7},
                      {"head": "link prediction", "relation": "applied_to", "tail": "GNN", "score": 0.9}]}
    entities = merge_entities(record, TEXT, threshold=0.5)
    assert [(e["type"], e["text"]) for e in entities] == [("Method", "graph neural network"), ("Task", "link prediction")]
    assert len(entities[0]["mentions"]) == 2
    relations = merge_relations(record, entities, TEXT, threshold=0.5)
    assert relations == [{"head": "graph neural network", "relation": "APPLIED_TO", "tail": "link prediction", "score": 0.8}]


def test_parse_decisions_tolerates_formats_and_keeps_first():
    from scientific_network.enrich.slm import parse_decisions
    assert parse_decisions("1:K 2:X, 3 = m\n4) T 1:X") == {1: "K", 2: "X", 3: "M", 4: "T"}
    assert parse_decisions("no decisions here") == {}


def test_batch_verify_two_calls_and_relation_filter():
    from scientific_network.enrich.slm import slm_verify_batch
    cands = [{"id": 1, "text": "GraphMix", "type": "Method"}, {"id": 2, "text": "link prediction", "type": "Task"},
             {"id": 3, "text": "method", "type": "Method"}]
    rels = [{"head": "GraphMix", "relation": "APPLIED_TO", "tail": "link prediction"},
            {"head": "method", "relation": "APPLIED_TO", "tail": "link prediction"}]
    out = slm_verify_batch(letters(["1:K 2:K 3:X", "1:K"]), TEXT, cands, rels)
    assert [e["text"] for e in out["entities"]] == ["GraphMix", "link prediction"]
    assert out["dropped"][0]["reason"] == "slm_drop" and out["relations"] == [rels[0]]
    assert slm_verify_batch(letters([]), TEXT, [], [])["entities"] == []


def test_generative_relations_use_entity_ids_and_endpoint_types():
    from scientific_network.enrich.slm import slm_relations
    entities = [{"id": 1, "text": "GraphMix", "type": "Method"}, {"id": 2, "text": "link prediction", "type": "Task"},
                {"id": 3, "text": "Cora", "type": "Dataset"}]
    reply = {"relations": [{"head": 1, "relation": "APPLIED_TO", "tail": 2}, {"head": 1, "relation": "APPLIED_TO", "tail": 2},
                           {"head": 3, "relation": "EVALUATED_ON", "tail": 1}, {"head": 1, "relation": "EVALUATED_ON", "tail": 3},
                           {"head": 9, "relation": "APPLIED_TO", "tail": 2}]}
    rels, _p, _c = slm_relations(client([reply]), TEXT, entities, [])
    assert rels == [{"head": "GraphMix", "relation": "APPLIED_TO", "tail": "link prediction"},
                    {"head": "GraphMix", "relation": "EVALUATED_ON", "tail": "Cora"}]
    assert slm_relations(client([]), TEXT, [entities[2]], []) == ([], 0, 0)
