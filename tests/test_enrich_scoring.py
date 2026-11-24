from scientific_network.enrich.scoring import score_entities, score_relations
from scientific_network.enrich.textutil import acronym_map, jaccard, normalize, paper_text, split_sentences

TEXT = ("Graph Mixing\nWe use a graph neural network (GNN) for link prediction. "
        "GNN models are tested on Cora. Next, we train graph neural networks.")


def test_normalize_and_jaccard():
    assert normalize("The Graph Neural Networks") == "graph neural network"
    assert jaccard("graph neural network", "Graph Neural Networks") == 1.0
    assert jaccard("link prediction", "node classification") == 0.0
    assert 0.5 <= jaccard("offline reinforcement learning", "reinforcement learning") < 1.0


def test_acronym_expansion_requires_matching_initials():
    mapping = acronym_map(TEXT)
    assert mapping["gnn"] == "graph neural network"
    assert acronym_map("We study the cat (BAZ) problem.") == {}


def test_sentences_cover_title_and_body():
    spans = split_sentences(paper_text("Title here", "First one. Second one."))
    assert [paper_text("Title here", "First one. Second one.")[a:b] for a, b in spans] == ["Title here", "First one.", "Second one."]


def test_entity_scoring_is_type_aware_lenient_and_strict():
    labels = [{"paper_id": "p", "methods": ["graph neural network"], "tasks": ["link prediction"], "datasets": ["Cora"], "relations": []}]
    texts = {"p": TEXT}
    pred = {"p": [("Method", "GNN"), ("Task", "link prediction task"), ("Dataset", "Cora"), ("Method", "Cora")]}
    lenient = score_entities(pred, labels, texts)
    assert lenient["Method"]["tp"] == 1 and lenient["Task"]["tp"] == 1 and lenient["Dataset"]["tp"] == 1
    assert lenient["Method"]["predicted"] == 2  # same string typed Method is a false positive
    strict = score_entities(pred, labels, texts, strict=True)
    assert strict["Task"]["tp"] == 0 and strict["Method"]["tp"] == 1


def test_relation_scoring_needs_both_endpoints_and_type():
    labels = [{"paper_id": "p", "methods": [], "tasks": [], "datasets": [],
               "relations": [{"head": "graph neural network", "relation": "APPLIED_TO", "tail": "link prediction"}]}]
    texts = {"p": TEXT}
    good = score_relations({"p": [("GNN", "APPLIED_TO", "link prediction")]}, labels, texts)
    assert good["micro"]["tp"] == 1
    wrong_type = score_relations({"p": [("GNN", "EVALUATED_ON", "link prediction")]}, labels, texts)
    assert wrong_type["micro"]["tp"] == 0
    wrong_tail = score_relations({"p": [("GNN", "APPLIED_TO", "Cora")]}, labels, texts)
    assert wrong_tail["micro"]["tp"] == 0


def test_stemmer_handles_es_and_ies_plurals_and_keeps_ss_us_is_endings():
    from scientific_network.enrich.textutil import acronym_map, normalize
    assert normalize("Gaussian Processes") == normalize("Gaussian Process") == "gaussian process"
    assert normalize("Markov Decision Processes") == "markov decision process"
    assert normalize("policies") == "policy" and normalize("classes") == "class" and normalize("searches") == "search"
    assert normalize("bias") == "bias" and normalize("series") == "series" and normalize("analysis") == "analysis"
    assert normalize("graph neural networks") == "graph neural network"
    assert acronym_map("We use 3D Gaussian Splatting (3DGS) for rendering.")["3dgs"] == "3D Gaussian Splatting"
